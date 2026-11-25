"""The capacity prior `p*` and its mis-budgeted copies (spec 002 §4.2).

Blahut–Arimoto on a candidate set placed by Fisher distance (points at most 0.5 Fisher
lengths apart at `sigma_eff`, seeded with the faces of `Theta`); beyond the sets'
reach, AtomicPriors.jl through `juliacall` (OQ-1), which is not installed here, so the
atomic path raises.

The candidate set (DD-C1) is a Poisson-disk net in prediction space, in noise units:
every pair of candidates is at least `spacing/2` apart, and Bridson's growth step
proposes new points between `spacing/2` and `spacing` from an existing one, so
neighbours lie at most `spacing` apart. The faces of `Theta` are covered first, lowest
dimension first (vertices, edges, ...), so that `p*`'s atoms on the faces are available
exactly; the interior is grown last. Proposals are drawn in a face's own coordinates
with the step scaled by the local Fisher metric. The construction is deterministic
(fixed seed), since `build_pstar` takes no generator (`skills/manage-randomness.md`, rule 7).
"""
from __future__ import annotations

import dataclasses
from dataclasses import dataclass
from itertools import product

import numpy as np
from scipy.spatial import cKDTree

from infomax.capacity import GaussianObjective, _newton, solve_capacity
from infomax.mixture import kl_to_mixture
from infomax.models import Model
from infomax.priors002 import DiscretePrior

NET_SEED: int = 20260601
"""Seed of the candidate-net construction (a fixed constant of the algorithm)."""


@dataclass(frozen=True)
class PStarResult:
    """A `p*` build: the prior, the capacity `C_N` (nats) and how it was built."""

    prior: DiscretePrior
    capacity: float
    candidates: np.ndarray
    masses: np.ndarray
    method: str  # "candidates" or "atomic"
    budget: float
    support_residual: float = 0.0


# ---------------------------------------------------------------------------
# Faces of Theta
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class _Face:
    """A face of `Theta`: `theta = base + P phi`, `phi` in its own domain."""

    dim: int
    base: np.ndarray  # (D,)
    P: np.ndarray  # (D, dim)
    lo: float | np.ndarray
    hi: float | np.ndarray
    ordered: bool

    def theta(self, phi: np.ndarray) -> np.ndarray:
        return self.base + phi @ self.P.T

    def inside(self, phi: np.ndarray) -> np.ndarray:
        ok = np.all((phi >= self.lo) & (phi <= self.hi), axis=-1)
        if self.ordered and self.dim > 1:
            ok &= np.all(np.diff(phi, axis=-1) >= 0.0, axis=-1)
        return ok

    def sample(self, n: int, rng: np.random.Generator) -> np.ndarray:
        lo = np.broadcast_to(np.asarray(self.lo, float), (self.dim,))
        hi = np.broadcast_to(np.asarray(self.hi, float), (self.dim,))
        phi = lo + (hi - lo) * rng.uniform(size=(n, self.dim))
        if self.ordered:
            phi = np.sort(phi, axis=-1)
        return phi


def _compositions(D: int):
    """Compositions of `D` into consecutive blocks (sizes)."""
    for cuts in product([0, 1], repeat=D - 1):
        sizes, run = [], 1
        for c in cuts:
            if c:
                sizes.append(run)
                run = 1
            else:
                run += 1
        sizes.append(run)
        yield sizes


def _faces(model: Model) -> list[_Face]:
    D = model.D
    lo = np.asarray(model.box.low, float)
    hi = np.asarray(model.box.high, float)
    faces: list[_Face] = []
    if model.box.ordered:
        a, b = float(lo[0]), float(hi[0])
        for sizes in _compositions(D):
            k = len(sizes)
            for pin_lo, pin_hi in product([False, True], repeat=2):
                if k == 1 and pin_lo and pin_hi:
                    continue
                base = np.zeros(D)
                free_blocks = []
                start = 0
                for bi, size in enumerate(sizes):
                    sl = slice(start, start + size)
                    if bi == 0 and pin_lo:
                        base[sl] = a
                    elif bi == k - 1 and pin_hi:
                        base[sl] = b
                    else:
                        free_blocks.append(sl)
                    start += size
                P = np.zeros((D, len(free_blocks)))
                for j, sl in enumerate(free_blocks):
                    P[sl, j] = 1.0
                faces.append(_Face(len(free_blocks), base, P, a, b, True))
    else:
        for choice in product([0, 1, 2], repeat=D):  # 0 = free, 1 = at low, 2 = at high
            free = [d for d in range(D) if choice[d] == 0]
            base = np.array([0.0 if choice[d] == 0 else (lo[d] if choice[d] == 1 else hi[d]) for d in range(D)])
            P = np.zeros((D, len(free)))
            for j, d in enumerate(free):
                P[d, j] = 1.0
            faces.append(_Face(len(free), base, P, lo[free], hi[free], False))
    faces.sort(key=lambda f: f.dim)
    return faces


# ---------------------------------------------------------------------------
# The Poisson-disk net
# ---------------------------------------------------------------------------


class _Net:
    """Accepted points in prediction space (noise units), with a KD-tree plus a buffer."""

    def __init__(self, r: float) -> None:
        self.r = r
        self.Y: list[np.ndarray] = []
        self.theta: list[np.ndarray] = []
        self._tree = None
        self._tree_n = 0

    def _rebuild(self):
        if self.Y:
            self._tree = cKDTree(np.array(self.Y))
            self._tree_n = len(self.Y)

    def far(self, Yp: np.ndarray) -> np.ndarray:
        """True where a point is at least `r` from every accepted point."""
        ok = np.ones(Yp.shape[0], dtype=bool)
        if self._tree is not None:
            d, _ = self._tree.query(Yp, k=1, distance_upper_bound=self.r)
            ok &= ~np.isfinite(d)
        if len(self.Y) > self._tree_n:
            buf = np.array(self.Y[self._tree_n :])
            d2 = ((Yp[:, None, :] - buf[None, :, :]) ** 2).sum(-1)
            ok &= np.all(d2 >= self.r**2, axis=1)
        return ok

    def add(self, Yp: np.ndarray, th: np.ndarray) -> None:
        self.Y.extend(Yp)
        self.theta.extend(th)
        if len(self.Y) - self._tree_n > 256:
            self._rebuild()

    def __len__(self) -> int:
        return len(self.Y)


def _grow_face(model: Model, face: _Face, net: _Net, s: float, rng: np.random.Generator, *, k: int = 24, max_points: int) -> None:
    r = net.r
    if face.dim == 0:
        th = face.base[None, :]
        Yp = model.y(th) / s
        if net.far(Yp)[0]:
            net.add(Yp, th)
        return
    span = np.broadcast_to(np.asarray(face.hi, float) - np.asarray(face.lo, float), (face.dim,))
    reg = np.diag((2.0 * r / np.maximum(span, 1e-12)) ** 2)
    seeds = face.sample(16, rng)
    active: list[np.ndarray] = []
    for phi in seeds:
        th = face.theta(phi[None, :])
        Yp = model.y(th) / s
        if net.far(Yp)[0]:
            net.add(Yp, th)
            active.append(phi)
    while active:
        if len(net) > max_points:
            raise RuntimeError(f"candidate set passes {max_points} points: the cell goes to the atomic path (§4.2)")
        batch = np.array(active[-128:])
        del active[-128:]
        B = batch.shape[0]
        Jth = model.jacobian(face.theta(batch))  # (B, m_out, D)
        Jphi = Jth @ face.P / s
        G = np.swapaxes(Jphi, -1, -2) @ Jphi + reg
        L = np.linalg.cholesky(G)
        dirs = rng.standard_normal((B, k, face.dim))
        dirs /= np.linalg.norm(dirs, axis=-1, keepdims=True)
        rad = r * (1.0 + rng.uniform(size=(B, k, 1)))
        z = dirs * rad  # Fisher-unit steps
        # solve L^T delta = z for each proposal
        LT = np.swapaxes(L, -1, -2)
        delta = np.linalg.solve(LT[:, None, :, :], z[..., None])[..., 0]
        prop = (batch[:, None, :] + delta).reshape(-1, face.dim)
        owner = np.repeat(np.arange(B), k)
        ok = face.inside(prop)
        prop, owner = prop[ok], owner[ok]
        if prop.size == 0:
            continue
        th = face.theta(prop)
        Yp = model.y(th) / s
        far = net.far(Yp)
        prop, owner, th, Yp = prop[far], owner[far], th[far], Yp[far]
        if prop.size == 0:
            continue
        # greedy acceptance within the batch
        accepted = []
        acc_Y = np.empty((0, Yp.shape[1]))
        for i in range(prop.shape[0]):
            if acc_Y.shape[0] and np.min(((acc_Y - Yp[i]) ** 2).sum(-1)) < r**2:
                continue
            accepted.append(i)
            acc_Y = np.vstack([acc_Y, Yp[i]])
        accepted = np.array(accepted, dtype=int)
        net.add(Yp[accepted], th[accepted])
        active.extend(prop[accepted])
        # owners that produced a new point stay active for another round
        for o in np.unique(owner[accepted]):
            active.append(batch[o])


def candidate_set(model: Model, spacing: float = 0.5, *, max_points: int = 10**6) -> np.ndarray:
    """Candidate states at most `spacing` Fisher lengths apart at `sigma_eff` (§4.2, F9).

    Seeded with the faces of `Theta`; shape (n, D).
    """
    s = model.sigma_eff
    rng = np.random.default_rng(NET_SEED)
    net = _Net(0.5 * spacing)
    for face in _faces(model):
        _grow_face(model, face, net, s, rng, max_points=max_points)
    theta = np.array(net.theta)
    return theta


# ---------------------------------------------------------------------------
# Atoms
# ---------------------------------------------------------------------------


def merge_atoms(Yhat: np.ndarray, theta: np.ndarray, masses: np.ndarray, *, link: float = 0.75, floor: float = 1e-10):
    """Clusters of supported candidates whose predictions lie within `link` noise units of
    each other (single linkage; neighbours in the net are at most 0.5 apart) become one atom
    with the cluster's total mass, placed at its heaviest member (DD-C2; spec 000's runs of
    adjacent cells, in `D` dimensions). The heaviest member, unlike a centroid, stays on
    the net and on its face of `Theta`, where `p*` puts atoms."""
    keep = np.flatnonzero(masses > floor)
    if keep.size == 0:
        raise ValueError("no supported candidates")
    tree = cKDTree(Yhat[keep])
    pairs = tree.query_pairs(r=link, output_type="ndarray")
    parent = np.arange(keep.size)

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    for a, b in pairs:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb
    roots = np.array([find(i) for i in range(keep.size)])
    atoms, weights = [], []
    for root in np.unique(roots):
        members = keep[roots == root]
        w = masses[members]
        atoms.append(theta[members[np.argmax(w)]])
        weights.append(w.sum())
    return np.array(atoms), np.array(weights)


# ---------------------------------------------------------------------------
# The build
# ---------------------------------------------------------------------------


def _channel(model: Model, budget: float, literal_nfold: bool):
    """The prediction map and noise of the budget-`budget` channel: the `sigma_eff`
    reduction, or the literal `N`-fold channel `theta -> X_{1:N}` (T7c)."""
    if literal_nfold:
        n = int(round(budget))
        if n != budget or n < 1:
            raise ValueError("the literal N-fold channel needs an integer budget >= 1")
        return (lambda th: np.tile(model.y(th), n)), model.sigma
    return model.y, model.sigma / np.sqrt(budget)


def _initial_support(Yhat: np.ndarray, radius: float = 1.25, max_size: int = 1500) -> np.ndarray:
    """A thinned subset of the candidates (greedy, every point within `radius` noise units)."""
    while True:
        tree = cKDTree(Yhat)
        covered = np.zeros(Yhat.shape[0], dtype=bool)
        chosen = []
        for i in range(Yhat.shape[0]):
            if covered[i]:
                continue
            chosen.append(i)
            covered[tree.query_ball_point(Yhat[i], r=radius)] = True
        if len(chosen) <= max_size:
            return np.array(chosen, dtype=int)
        radius *= 1.3


def build_pstar(
    model: Model,
    *,
    budget: float | None = None,
    spacing: float = 0.5,
    candidates: np.ndarray | None = None,
    method: str = "auto",
    literal_nfold: bool = False,
    tol: float = 1e-8,
) -> PStarResult:
    """`p*` of the budget-`budget` channel (default: the model's `N`), at `sigma/sqrt(budget)`.

    `budget != model.N` gives the mis-budgeted `p*_M` (§2.2). `candidates` overrides the
    candidate set, so two builds can share one (T16(c), T19(a)). `literal_nfold=True`
    builds the explicit `N`-fold channel instead of the `sigma_eff` reduction (T7c).
    """
    M = float(model.N if budget is None else budget)
    if method == "atomic":
        raise NotImplementedError("the atomic path needs AtomicPriors.jl through juliacall (OQ-1), not installed")
    from infomax.priors002 import _model_key

    # the reduced build depends on sigma and the budget only through sigma / sqrt(budget),
    # so the cheap cell's p*_10N and its twin's p*_40 share one build
    noise = (float(model.sigma), M) if literal_nfold else (round(float(model.sigma / np.sqrt(M)), 14),)
    key = (
        _model_key(model), noise, float(spacing), method, bool(literal_nfold), float(tol),
        None if candidates is None else np.asarray(candidates, dtype=float).tobytes(),
    )
    hit = _BUILD_CACHE.get(key)
    if hit is not None:
        return hit if hit.budget == M else dataclasses.replace(hit, budget=M)
    result = _build_pstar(model, M, spacing, candidates, literal_nfold, tol)
    if len(_BUILD_CACHE) > 64:
        _BUILD_CACHE.clear()
    _BUILD_CACHE[key] = result
    return result


_BUILD_CACHE: dict = {}
"""Builds are deterministic functions of their arguments, so a repeated build (the same
cell in several tests, or `p*` and its copies in each `build_cast`) reuses the result."""


def _build_pstar(model: Model, M: float, spacing: float, candidates, literal_nfold: bool, tol: float) -> PStarResult:
    model_b = model.at_budget(M)
    cands = candidate_set(model_b, spacing) if candidates is None else np.asarray(candidates, dtype=float)
    ymap, s = _channel(model, M, literal_nfold)
    Y = ymap(cands)
    obj = GaussianObjective(Y, s)
    fast = None if Y.shape[1] == 1 else GaussianObjective(Y, s, fast=True)
    initial = None if cands.shape[0] <= 600 else _initial_support(Y / s)
    sol = solve_capacity(obj, fast=fast, initial=initial, tol=tol)
    # The prior is the converged candidate-set solution itself (DD-C2): merging adjacent
    # supported candidates into one atom moves mass by up to a net spacing and breaks the
    # equalizer by several 1e-2 nats; `merge_atoms` gives the atoms for reporting.
    keep = sol.masses > 0
    prior = DiscretePrior(f"p*[{M:g}]", cands[keep], sol.masses[keep])
    capacity = float(sol.value)
    return PStarResult(
        prior=prior, capacity=capacity, candidates=cands, masses=sol.masses, method="candidates", budget=M,
        support_residual=sol.support_residual,
    )
