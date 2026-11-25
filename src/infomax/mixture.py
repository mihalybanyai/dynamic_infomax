"""Gaussian-mixture machinery shared by spec 002's priors, solvers and scores.

Spec: specs/002-foreign-q-prediction.md §4.2 (the per-cell divergence of the
Blahut–Arimoto solvers), §4.4 (exact mixture marginals and predictives) and §4.5
(per-state redundancy). New in spec 002; not used by spec 000.

Two things live here.

1. **Mixture log densities.** `mixture_logpdf(x, Y, logw, s)` is
   `log sum_j w_j N(x; Y_j, s^2 1)`, evaluated in log space and in chunks.

2. **The per-state divergence** `f(y_0) = D_KL(N(y_0, s^2 1) || sum_j w_j N(Y_j, s^2 1))`.
   With `x = y_0 + s z` and `delta_j = (Y_j - y_0)/s`,
   `f = E_z[-log sum_j w_j exp(-|delta_j|^2/2 + z . delta_j)]`, which depends on `z` only
   through its projection on the span of the nearby `delta_j`. The expectation is taken
   over that span (design decision DD-K1): Gauss–Hermite nodes when the span is
   one-dimensional, otherwise a scrambled Sobol point set in the span's first
   coordinates, with antithetic pairs. Atoms farther than `CUTOFF` noise units are
   dropped (their terms are below `exp(-CUTOFF^2/2 + 3 CUTOFF)` at three-sigma `z`).
   The estimator is deterministic for a fixed `seed`, so the solvers that use it are
   deterministic (`skills/manage-randomness.md`, rule 7).
"""
from __future__ import annotations

from functools import lru_cache

import numpy as np
import scipy.special
import scipy.stats
from scipy.spatial import cKDTree

CUTOFF: float = 8.0
"""Neighbour radius, in noise units, of the per-state divergence (DD-K1): an atom 8 noise
units away contributes at most `exp(-8)` of the dominant term at a three-sigma `z`."""

N_MIN_NEIGHBOURS: int = 6
"""The divergence of a state far from every atom still uses its nearest atoms."""

DEFAULT_NQ: int = 512
"""Sobol points per state (doubled by the antithetic pairs) in the accurate estimator."""

FIXED_SEED: int = 20261125
"""Scramble seed of the deterministic point set used when no generator is passed."""

N_GH: int = 96
"""Gauss–Hermite nodes when the neighbours' span is one-dimensional."""


# ---------------------------------------------------------------------------
# Mixture log densities
# ---------------------------------------------------------------------------


def log_normal_iso(x: np.ndarray, mean: np.ndarray, s: float) -> np.ndarray:
    """`log N(x; mean, s^2 1)` over the last axis, broadcasting."""
    d = np.asarray(x, dtype=float) - np.asarray(mean, dtype=float)
    m = d.shape[-1]
    return -0.5 * np.sum(d * d, axis=-1) / s**2 - 0.5 * m * np.log(2.0 * np.pi * s**2)


def sq_dists(x: np.ndarray, Y: np.ndarray) -> np.ndarray:
    """Squared Euclidean distances, shape (n, k), from the expansion `|x|^2 - 2 x.Y + |Y|^2`,
    corrected by a direct evaluation where the expansion loses precision."""
    x = np.asarray(x, dtype=float)
    Y = np.asarray(Y, dtype=float)
    xx = np.einsum("ij,ij->i", x, x)
    yy = np.einsum("ij,ij->i", Y, Y)
    d2 = xx[:, None] - 2.0 * (x @ Y.T) + yy[None, :]
    np.maximum(d2, 0.0, out=d2)
    scale = xx[:, None] + yy[None, :]
    bad = d2 < 1e-6 * scale
    if np.any(bad):
        ii, jj = np.nonzero(bad)
        diff = x[ii] - Y[jj]
        d2[ii, jj] = np.einsum("ij,ij->i", diff, diff)
    return d2


def mixture_logpdf(
    x: np.ndarray, Y: np.ndarray, logw: np.ndarray, s: float, *, chunk: int = 2_000_000
) -> np.ndarray:
    """`log sum_j w_j N(x_i; Y_j, s^2 1)` for each row `x_i`, shape (n,)."""
    x = np.atleast_2d(np.asarray(x, dtype=float))
    Y = np.atleast_2d(np.asarray(Y, dtype=float))
    logw = np.asarray(logw, dtype=float)
    keep = np.isfinite(logw)
    Y, logw = Y[keep], logw[keep]
    m = x.shape[-1]
    const = -0.5 * m * np.log(2.0 * np.pi * s**2)
    out = np.empty(x.shape[0])
    rows = max(1, chunk // max(1, Y.shape[0]))
    for a in range(0, x.shape[0], rows):
        d2 = sq_dists(x[a : a + rows], Y)
        out[a : a + rows] = scipy.special.logsumexp(logw[None, :] - 0.5 * d2 / s**2, axis=1)
    return out + const


def posterior_weights(x: np.ndarray, Y: np.ndarray, logw: np.ndarray, s: float) -> np.ndarray:
    """Posterior weights over the atoms `Y` given data `x` at noise `s`, shape (n, k)."""
    x = np.atleast_2d(np.asarray(x, dtype=float))
    lw = np.asarray(logw, dtype=float)[None, :] - 0.5 * sq_dists(x, Y) / s**2
    lw -= scipy.special.logsumexp(lw, axis=1, keepdims=True)
    return np.exp(lw)


# ---------------------------------------------------------------------------
# Quadrature points for the per-state divergence
# ---------------------------------------------------------------------------


@lru_cache(maxsize=32)
def _sobol_normals(n_q: int, dim: int, seed: int) -> np.ndarray:
    """A scrambled Sobol set of `n_q` points in `dim` dimensions, mapped to N(0, 1)."""
    sob = scipy.stats.qmc.Sobol(d=dim, scramble=True, seed=seed)
    u = sob.random(n_q)
    u = np.clip(u, 1e-12, 1 - 1e-12)
    z = scipy.stats.norm.ppf(u)
    z.setflags(write=False)
    return z


@lru_cache(maxsize=4)
def _gauss_hermite(n: int) -> tuple[np.ndarray, np.ndarray]:
    t, w = np.polynomial.hermite.hermgauss(n)
    z = np.sqrt(2.0) * t
    om = w / np.sqrt(np.pi)
    z.setflags(write=False)
    om.setflags(write=False)
    return z, om


def _seed_from(rng: np.random.Generator | None) -> int:
    if rng is None:
        return FIXED_SEED
    return int(rng.integers(0, 2**31 - 1))


# ---------------------------------------------------------------------------
# The per-state divergence and its Jacobian
# ---------------------------------------------------------------------------


GH_TOP: dict[int, int] = {1: 64, 2: 28, 3: 12}
"""Gauss–Hermite nodes per direction when the leading span has 1, 2 or 3 directions:
about 2e-4 nats of error at the cheap cell (DD-K1)."""

GH_TOP_FAST: dict[int, int] = {1: 32, 2: 12, 3: 6}
"""The fast objective's rule: about 3e-3 nats, eight times cheaper."""

RES_REL: float = 1e-3
"""Residual directions below this share of the leading singular value are dropped."""

TOP_REL: float = 0.03
"""A direction of the neighbours' span is leading when its singular value exceeds this
share of the largest (DD-K1); the others enter through the second-order correction."""


def _gh_tensor(k: int, top: dict | None = None) -> tuple[np.ndarray, np.ndarray]:
    z1, w1 = _gauss_hermite((GH_TOP if top is None else top)[k])
    mesh = np.meshgrid(*([np.arange(z1.size)] * k), indexing="ij")
    idx = np.stack([g.ravel() for g in mesh], axis=-1)
    return z1[idx], np.prod(w1[idx], axis=1)


class KernelTable:
    """Per-state quadrature tables for the per-state divergence `f_i` (DD-K1).

    States `Y0` (n, m) and atoms `Y` (K, m) are in data units; `s` is the noise. For
    each state the atoms within `CUTOFF` noise units (and at least the nearest
    `N_MIN_NEIGHBOURS`) enter; `idx[i]` lists them, padded with `-1`. With
    `c_ij = (Y_j - Y0_i)/s` split into its components on the leading directions of their
    span (`c_top`) and on the rest (`c_res`),
    `f_i = sum_k omega_ik [-log sum_j w_j exp(-|c_ij|^2/2 + z_k . c_top_ij) - V_ik/2]`, where
    `z_k` are Gauss–Hermite nodes on the leading directions and `V_ik` is the variance of
    `c_res` under the posterior over neighbours at node `k`: the second-order term of the
    expectation over the residual directions. `method="sobol"` instead uses a scrambled
    Sobol set over the whole span (`n_q` points, antithetic).
    """

    def __init__(
        self,
        Y0: np.ndarray,
        Y: np.ndarray,
        s: float,
        *,
        n_q: int = DEFAULT_NQ,
        seed: int = FIXED_SEED,
        cutoff: float = CUTOFF,
        tree: cKDTree | None = None,
        dtype=None,
        method: str = "gh",
        gh_top: dict | None = None,
    ) -> None:
        Y0 = np.atleast_2d(np.asarray(Y0, dtype=float)) / s
        Yh = np.atleast_2d(np.asarray(Y, dtype=float)) / s
        n, m = Y0.shape
        K = Yh.shape[0]
        tree = cKDTree(Yh) if tree is None else tree
        near = tree.query_ball_point(Y0, r=cutoff)
        k_min = min(N_MIN_NEIGHBOURS, K)
        _, nearest = tree.query(Y0, k=k_min)
        nearest = np.atleast_2d(nearest).reshape(n, k_min)
        lists = []
        for i in range(n):
            lst = set(near[i])
            lst.update(int(j) for j in nearest[i])
            lists.append(np.array(sorted(lst), dtype=int))
        jmax = max(len(lst) for lst in lists)
        dtype = np.float64 if dtype is None else dtype
        self.dtype = dtype
        per_state = []
        for i in range(n):
            js = lists[i]
            delta = Yh[js] - Y0[i]
            d2 = np.einsum("ij,ij->i", delta, delta)
            if m == 1:
                z, om = _gauss_hermite(N_GH)
                per_state.append((js, -0.5 * d2[None, :] + z[:, None] * delta[None, :, 0], om, None))
                continue
            big = d2 > 1e-24
            if not np.any(big):
                per_state.append((js, np.tile(-0.5 * d2[None, :], (1, 1)), np.ones(1), None))
                continue
            _, sv, vt = np.linalg.svd(delta[big], full_matrices=False)
            # residual directions below RES_REL of the leading one move each exponent by
            # under RES_REL * CUTOFF noise units and are dropped (DD-K1)
            rank = int(np.sum(sv > (1e-10 if method == "sobol" else RES_REL) * sv[0]))
            Q = vt[:rank].T
            c = delta @ Q
            if method == "sobol":
                u = _sobol_normals(n_q, m, seed)[:, :rank]
                proj = u @ c.T
                E_i = -0.5 * d2[None, :] + np.concatenate([proj, -proj], axis=0)
                per_state.append((js, E_i, np.full(E_i.shape[0], 1.0 / E_i.shape[0]), None))
                continue
            k_top = int(min(3, np.sum(sv[:rank] > TOP_REL * sv[0])))
            z, om = _gh_tensor(k_top, gh_top)
            E_i = -0.5 * d2[None, :] + z @ c[:, :k_top].T
            c_res = c[:, k_top:] if rank > k_top else None
            per_state.append((js, E_i, om, c_res))
        n_nodes = max(p[1].shape[0] for p in per_state)
        k_res = max((p[3].shape[1] if p[3] is not None else 0) for p in per_state)
        E = np.full((n, n_nodes, jmax), -np.inf, dtype=dtype)
        omega = np.zeros((n, n_nodes))
        idx = np.full((n, jmax), -1, dtype=int)
        C = np.zeros((n, jmax, k_res)) if k_res else None
        for i, (js, E_i, om, c_res) in enumerate(per_state):
            idx[i, : js.size] = js
            E[i, : E_i.shape[0], : js.size] = E_i
            if E_i.shape[0] < n_nodes:  # padded nodes: finite, weight 0
                E[i, E_i.shape[0] :, 0] = 0.0
            omega[i, : om.size] = om
            if c_res is not None:
                C[i, : js.size, : c_res.shape[1]] = c_res
        self.E = E
        self.idx = idx
        self.omega = omega
        self.C = C
        self.n_states = n
        self.n_atoms = K

    def _lse_post(self, logw: np.ndarray, need_post: bool):
        lw = np.where(self.idx >= 0, np.asarray(logw, dtype=float)[np.maximum(self.idx, 0)], -np.inf)
        a = self.E + lw[:, None, :].astype(self.dtype)
        mx = np.max(a, axis=2, keepdims=True)
        mx = np.where(np.isfinite(mx), mx, 0.0)
        ex = np.exp(a - mx)
        tot = np.sum(ex, axis=2)
        with np.errstate(divide="ignore"):
            lse = np.log(tot.astype(float)) + mx[..., 0].astype(float)
        post = ex / np.maximum(tot, np.finfo(self.dtype).tiny)[..., None] if (need_post or self.C is not None) else None
        if post is not None:
            post = np.where(np.isfinite(post), post, 0.0)
        return lse, post

    def _correction(self, post) -> np.ndarray:
        if self.C is None:
            return 0.0
        sq = np.einsum("ikj,ij->ik", post, np.sum(self.C**2, axis=2))
        mean = np.einsum("ikj,ijr->ikr", post, self.C)
        return 0.5 * (sq - np.sum(mean**2, axis=2))

    def f(self, logw: np.ndarray) -> np.ndarray:
        """Per-state divergence for log weights `logw` over the atoms (`-inf` allowed)."""
        lse, post = self._lse_post(logw, False)
        term = np.where(self.omega > 0, lse + self._correction(post), 0.0)
        return -np.sum(self.omega * term, axis=1)

    def f_and_jacobian(self, w: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        """`f` and `df_i/dw_l`, shape (n_states, n_atoms), for weights `w` (not logs); the
        Jacobian omits the derivative of the second-order correction."""
        w = np.asarray(w, dtype=float)
        with np.errstate(divide="ignore"):
            logw = np.log(w)
        lse, post = self._lse_post(logw, True)
        term = np.where(self.omega > 0, lse + self._correction(post), 0.0)
        f = -np.sum(self.omega * term, axis=1)
        lse_safe = np.where(self.omega > 0, lse, 0.0)
        ratio = np.exp(self.E - lse_safe[:, :, None].astype(self.dtype))  # p_j / m at the nodes
        dJ = -np.einsum("ik,ikj->ij", self.omega.astype(self.dtype), ratio).astype(float)
        jac = np.zeros((self.n_states, self.n_atoms))
        rows = np.repeat(np.arange(self.n_states), self.idx.shape[1])
        cols = self.idx.ravel()
        ok = cols >= 0
        np.add.at(jac, (rows[ok], cols[ok]), dJ.ravel()[ok])
        return f, jac


def kl_to_mixture(
    Y0: np.ndarray,
    Y: np.ndarray,
    logw: np.ndarray,
    s: float,
    *,
    n_q: int = DEFAULT_NQ,
    seed: int = FIXED_SEED,
    chunk: int = 128,
    method: str = "gh",
) -> np.ndarray:
    """`D_KL(N(y_0, s^2 1) || sum_j w_j N(Y_j, s^2 1))` for each row `y_0` of `Y0`."""
    Y0 = np.atleast_2d(np.asarray(Y0, dtype=float))
    Y = np.atleast_2d(np.asarray(Y, dtype=float))
    logw = np.asarray(logw, dtype=float)
    keep = np.isfinite(logw)
    Yk, lw = Y[keep], logw[keep]
    tree = cKDTree(Yk / s)
    out = np.empty(Y0.shape[0])
    for a in range(0, Y0.shape[0], chunk):
        table = KernelTable(Y0[a : a + chunk], Yk, s, n_q=n_q, seed=seed, tree=tree, method=method)
        out[a : a + chunk] = table.f(lw)
    return out


def elk_divergence(Y0: np.ndarray, Y: np.ndarray, logw: np.ndarray, s: float) -> np.ndarray:
    """A&M's kernel approximation (App. A.2, ELK with `sqrt(2) sigma`) of the per-state
    divergence, up to a constant: `-log sum_j w_j exp(-|y_0 - Y_j|^2 / (4 s^2))`. Used
    only to warm-start the solvers (DD-K2)."""
    d2 = sq_dists(np.atleast_2d(Y0), np.atleast_2d(Y))
    return -scipy.special.logsumexp(np.asarray(logw)[None, :] - d2 / (4.0 * s**2), axis=1)
