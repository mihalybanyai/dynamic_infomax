"""The capacity solver behind `p*` and `p_lat` on a candidate set (spec 002 §4.2).

Spec: specs/002-foreign-q-prediction.md §4.2 ("Blahut–Arimoto on a candidate set ...
reusing spec 000's loop"; the `p_lat` update; the two-sided stopping bound). New in
spec 002.

The fixed point sought is the Blahut–Arimoto one: weights `w` on the candidates with the
per-state objective `f_i(w)` equal to its average `lambda = sum_i w_i f_i` on the support
and at most `lambda` off it. For `p*`, `f_i` is the divergence
`D_KL(p(.|theta_i) || m_w)`; for `p_lat` it is the difference of two such divergences at
budgets `N + M` and `N` (§4.2). The solver (design decision DD-S1) runs

1. spec 000's overrelaxed Blahut–Arimoto loop (`infomax.ba.blahut_arimoto`, with the
   per-cell divergence injected as a callable, §4.6) as a warm start, on a cheap
   objective over a subset of the candidates;
2. an active-set Newton method on the fixed-point equations `f_i(w) = lambda` (`i` in the
   support), `sum w = 1`, with the accurate objective; atoms whose weight is driven to zero
   leave the support;
3. a sweep over every candidate: those with `f_c > lambda + add_tol` join the support,
   and steps 2–3 repeat until none does.

At the end `max_c f_c - lambda`, the Csiszár gap over the candidates, is below `add_tol`.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import scipy.special
import scipy.stats
from scipy.spatial import cKDTree

from infomax.ba import blahut_arimoto
from infomax.mixture import DEFAULT_NQ, FIXED_SEED, GH_TOP_FAST, KernelTable, elk_divergence


# ---------------------------------------------------------------------------
# Objectives
# ---------------------------------------------------------------------------


class GaussianObjective:
    """`f_i(w) = D_KL(N(Y_i, s^2 1) || sum_j w_j N(Y_j, s^2 1))` over candidate predictions `Y`."""

    def __init__(self, Y: np.ndarray, s: float, *, n_q: int = DEFAULT_NQ, seed: int = FIXED_SEED, fast: bool = False) -> None:
        self.Y = np.atleast_2d(np.asarray(Y, dtype=float))
        self.s = float(s)
        self.n_q = n_q
        self.seed = seed
        self.n = self.Y.shape[0]
        self.one_d = self.Y.shape[1] == 1
        self.dtype = np.float32 if (fast and not self.one_d) else np.float64
        self.precision = 0.0 if self.dtype == np.float64 else 2e-7  # float32 for the fast objective (DD-K1)
        self.gh_top = GH_TOP_FAST if fast else None
        self._cache: dict = {}

    def _table(self, states: np.ndarray, atoms: np.ndarray) -> KernelTable:
        key = (states.tobytes(), atoms.tobytes())
        hit = self._cache.get(key)
        if hit is None:
            if len(self._cache) > 8:
                self._cache.clear()
            hit = KernelTable(self.Y[states], self.Y[atoms], self.s, n_q=self.n_q, seed=self.seed, dtype=self.dtype, gh_top=self.gh_top)
            self._cache[key] = hit
        return hit

    def f_and_jac(self, S: np.ndarray, w: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        return self._table(S, S).f_and_jacobian(w)

    def f_S(self, S: np.ndarray, w: np.ndarray) -> np.ndarray:
        with np.errstate(divide="ignore"):
            return self._table(S, S).f(np.log(w))

    def f(self, states: np.ndarray, S: np.ndarray, w: np.ndarray, *, chunk: int = 256) -> np.ndarray:
        with np.errstate(divide="ignore"):
            lw = np.log(w)
        out = np.empty(states.size)
        for a in range(0, states.size, chunk):
            st = states[a : a + chunk]
            table = KernelTable(self.Y[st], self.Y[S], self.s, n_q=self.n_q, seed=self.seed, dtype=self.dtype, gh_top=self.gh_top)
            out[a : a + chunk] = table.f(lw)
        return out

    def cheap_f(self, S: np.ndarray, w: np.ndarray) -> np.ndarray:
        """Warm-start objective: exact in 1-D, A&M's kernel approximation otherwise (DD-K2)."""
        if self.one_d:
            return self.f_and_jac(S, w)[0]
        with np.errstate(divide="ignore"):
            lw = np.log(w)
        return elk_divergence(self.Y[S], self.Y[S], lw, self.s)

    def upper_bound(self, states: np.ndarray, S: np.ndarray, w: np.ndarray) -> np.ndarray:
        """`-log sum_j w_j exp(-|Y_c - Y_j|^2 / 2 s^2) >= f_c` (Jensen), to skip candidates."""
        with np.errstate(divide="ignore"):
            lw = np.log(w)
        tree = cKDTree(self.Y[S] / self.s)
        k = min(32, S.size)
        d, j = tree.query(self.Y[states] / self.s, k=k)
        d, j = np.atleast_2d(d).reshape(states.size, k), np.atleast_2d(j).reshape(states.size, k)
        return -scipy.special.logsumexp(lw[j] - 0.5 * d**2, axis=1)


class DifferenceObjective:
    """`f^(a) - f^(b)`: the `p_lat` update's difference of divergences at two noises (§4.2).
    `b = None` stands for budget 0, whose divergence is 0."""

    def __init__(self, a, b=None) -> None:
        self.a, self.b = a, b
        self.n = a.n
        self.one_d = getattr(a, "one_d", True)
        # with no second term the objective is exactly `a`, on exactly `a`'s path (T16(c))
        self.precision = getattr(a, "precision", 0.0) * (1 if b is None else 2)
        if b is None and hasattr(a, "upper_bound"):
            self.upper_bound = a.upper_bound

    def f_and_jac(self, S, w):
        fa, ja = self.a.f_and_jac(S, w)
        if self.b is None:
            return fa, ja
        fb, jb = self.b.f_and_jac(S, w)
        return fa - fb, ja - jb

    def f(self, states, S, w, **kw):
        out = self.a.f(states, S, w, **kw)
        return out if self.b is None else out - self.b.f(states, S, w, **kw)

    def f_S(self, S, w):
        out = self.a.f_S(S, w)
        return out if self.b is None else out - self.b.f_S(S, w)

    def cheap_f(self, S, w):
        out = self.a.cheap_f(S, w)
        return out if self.b is None else out - self.b.cheap_f(S, w)

    def upper_bound(self, states, S, w):
        return None


class BinomialObjective:
    """Binomial divergences `D_KL(Bin(n, theta_i) || sum_j w_j Bin(n, theta_j))`, exact."""

    def __init__(self, theta: np.ndarray, n: int) -> None:
        theta = np.asarray(theta, dtype=float).reshape(-1)
        k = np.arange(n + 1)
        with np.errstate(divide="ignore"):
            self.L = scipy.stats.binom.logpmf(k[None, :], n, theta[:, None])  # (n_cand, n+1)
        self.P = np.exp(self.L)
        self.n = theta.size
        self.one_d = True

    def _parts(self, states, S, w):
        px = w @ self.P[S]
        with np.errstate(divide="ignore", invalid="ignore"):
            logpx = np.log(px)
            f = np.sum(np.where(self.P[states] > 0, self.P[states] * (self.L[states] - logpx), 0.0), axis=1)
        return f, px

    def f_and_jac(self, S, w):
        f, px = self._parts(S, S, w)
        with np.errstate(divide="ignore", invalid="ignore"):
            ratio = np.where(px > 0, self.P[S] / px, 0.0)  # (|S|, n+1)
        jac = -self.P[S] @ ratio.T
        return f, jac

    def f(self, states, S, w, **kw):
        return self._parts(states, S, w)[0]

    def f_S(self, S, w):
        return self._parts(S, S, w)[0]

    def cheap_f(self, S, w):
        return self._parts(S, S, w)[0]

    def upper_bound(self, states, S, w):
        return None


# ---------------------------------------------------------------------------
# The solver
# ---------------------------------------------------------------------------


@dataclass
class CapacitySolution:
    """Weights over every candidate, the value `lambda = sum w f`, and the objective at
    every candidate (the two sides of the stopping bound are `lambda` and `max f`)."""

    masses: np.ndarray
    value: float
    f_all: np.ndarray
    n_outer: int
    support_residual: float = 0.0


MU_FLOOR = 1e-5
"""Floor of the Newton step's Levenberg–Marquardt damping, relative to the Hessian's scale
(DD-S1). With near-duplicate candidates the system is near-singular; at a floor of `1e-8`
rounding-level differences in the divergences sent the steps in different directions and
the solve stalled. `1e-5` was the fastest robust value at the cheap cell (`1e-6`: 9.3 s,
`1e-5`: 6.8 s, `1e-4`: 16.8 s and a residual of 2e-3)."""


def _newton(obj, S: np.ndarray, w: np.ndarray, *, tol: float, max_iter: int = 40):
    """Projected Newton ascent on `I(w) = sum_i w_i f_i(w)` over the simplex (DD-S1).

    The model is `f` for the gradient (constant shifts do not matter on the simplex) and
    the symmetrised Jacobian `(J + J^T)/2`, minus a Levenberg–Marquardt shift so that it is
    negative definite: the Hessian of the information is `-∫ p_i p_l / m <= 0`. Steps are
    taken by an Armijo line search on `I`, so `I` never falls. A step that drives a weight
    to zero stops at the boundary, and that atom leaves the support if its `f` lies below
    `lambda = sum w f`. Atoms may enter with weight 0. Stops when
    `max_S |f_i - lambda| < tol` (floored at the objective's precision) or `I` stalls."""
    S = S.copy()
    w = np.asarray(w, dtype=float).copy()
    prec = getattr(obj, "precision", 0.0)
    tol = max(tol, prec)
    f, J = obj.f_and_jac(S, w)
    I = float(w @ f)
    mu = MU_FLOOR
    stall = 0
    for _ in range(max_iter):
        lam = float(w @ f)
        out = (w <= 1e-300) & (f <= lam)
        if np.any(out) and np.sum(~out) >= 1:
            S, w = S[~out], w[~out]
            f, J = obj.f_and_jac(S, w)
            lam = float(w @ f)
        active = w > 1e-300
        if float(np.max(np.abs(f[active] - lam))) < tol and not np.any(f[~active] > lam + tol):
            break
        k = S.size
        H = 0.5 * (J + J.T)
        scale = max(1e-300, float(np.max(np.abs(np.diag(H)))))
        free = np.ones(k, dtype=bool)
        for _rep in range(3):
            idx = np.flatnonzero(free)
            kf = idx.size
            A = np.zeros((kf + 1, kf + 1))
            A[:kf, :kf] = H[np.ix_(idx, idx)] - mu * scale * np.eye(kf)
            A[:kf, kf] = 1.0
            A[kf, :kf] = 1.0
            rhs = np.concatenate([-(f[idx] - lam), [0.0]])
            try:
                sol = np.linalg.solve(A, rhs)[:kf]
            except np.linalg.LinAlgError:
                sol = np.linalg.lstsq(A, rhs, rcond=1e-14)[0][:kf]
            dw = np.zeros(k)
            dw[idx] = sol
            pinned = (w <= 1e-300) & (dw < 0)
            if not np.any(pinned):
                break
            free &= ~pinned  # atoms at zero that the step would push negative stay at zero
        dw[(w <= 1e-300) & (dw < 0)] = 0.0
        slope = float(f @ dw)
        if slope <= 0:  # not an ascent direction: fall back to the projected gradient
            dw = f - lam
            dw[(w <= 1e-300) & (dw < 0)] = 0.0
            dw -= np.where(dw != 0, 1.0, 0.0) * dw.sum() / max(1, np.count_nonzero(dw))
            slope = float(f @ dw)
            if slope <= 0:
                break
        neg = dw < 0
        if np.any(neg):
            ratios = np.full(k, np.inf)
            ratios[neg] = -w[neg] / dw[neg]
            a_max = float(np.min(ratios))
            if a_max <= 0:
                break
        else:
            a_max = np.inf
        alpha = min(1.0, a_max)
        improved = False
        for _ls in range(40):
            w_try = np.maximum(w + alpha * dw, 0.0)
            w_try /= w_try.sum()
            f_try = obj.f_S(S, w_try)
            I_try = float(w_try @ f_try)
            if I_try >= I + 1e-6 * alpha * slope or (alpha == a_max and I_try >= I):
                improved = True
                break
            alpha *= 0.5
        if not improved:
            mu = min(mu * 100.0, 1e2)
            stall += 1
            if stall >= 4:
                break
            continue
        stall = 0
        mu = max(mu / 10.0, MU_FLOOR)
        gain = I_try - I
        w = w_try
        lam = float(w @ f_try)
        # an atom at zero stays free only while its f exceeds lambda
        drop = (w <= 1e-300) & (f_try <= lam)
        dropped = bool(np.any(drop) and np.sum(~drop) >= 1)
        if dropped:
            S, w = S[~drop], w[~drop] / w[~drop].sum()
        f, J = obj.f_and_jac(S, w)
        I = float(w @ f)
        if not dropped and gain < 1e-15 * max(1.0, abs(I)):
            break
    lam = float(w @ f)
    return S, w, lam, f


def _separated(obj, order: np.ndarray, *, min_sep: float, cap: int) -> np.ndarray:
    """The strongest violators, at least `min_sep` noise units apart, at most `cap`."""
    Y = getattr(obj, "Y", None)
    if Y is None and hasattr(obj, "a"):
        Y = getattr(obj.a, "Y", None)
    if Y is None:
        return order[:cap]
    s = obj.s if hasattr(obj, "s") else obj.a.s
    chosen = []
    for i in order:
        if all(np.sum((Y[i] - Y[j]) ** 2) >= (min_sep * s) ** 2 for j in chosen):
            chosen.append(i)
            if len(chosen) >= cap:
                break
    return np.array(chosen, dtype=int)


def _ba_on(obj, S: np.ndarray, w: np.ndarray, *, cheap: bool, iters: int, eps: float = 1e-10) -> np.ndarray:
    """Spec 000's overrelaxed Blahut–Arimoto loop with the per-cell divergence injected."""
    fn = (lambda p: obj.cheap_f(S, p)) if cheap else (lambda p: obj.f_S(S, p))
    init = np.maximum(w, 1e-12 * max(w.max(), 1e-300))
    res = blahut_arimoto(f_kl=fn, n_cells=S.size, init=init / init.sum(), eps_i=eps, tau_min=2, tau_max=iters)
    return res.prior.masses()


def solve_capacity(
    obj,
    *,
    fast=None,
    initial: np.ndarray | None = None,
    tol: float = 1e-8,
    add_tol: float | None = None,
    max_outer: int = 80,
    ba_iters: int = 400,
    keep_threshold: float = 1e-6,
) -> CapacitySolution:
    """Maximise over weights on `obj`'s candidates (DD-S1); `initial` is an optional
    starting support (candidate indices), by default every candidate. `fast`, if given, is
    a cheaper version of `obj` (fewer quadrature points) used to reach the neighbourhood
    of the fixed point and to screen the candidate sweep."""
    fast = obj if fast is None else fast
    n = obj.n
    add_tol = tol if add_tol is None else add_tol
    support_tol = add_tol
    if not getattr(obj, "one_d", True):
        # quadrature-based divergences beyond 1-D (DD-S1): violations below 1e-3 nats are
        # not chased, and the equalizer on the support is accepted at 2e-3 nats once the
        # information has stopped rising (near-duplicate candidates make the last digits
        # of the split between them ill-determined and irrelevant to I)
        add_tol = max(add_tol, 1e-3)
        support_tol = 2e-3
        max_outer = min(max_outer, 12)
    lam_prev = -np.inf
    final_resid = np.inf
    S = np.arange(n) if initial is None else np.unique(np.asarray(initial, dtype=int))
    w = np.full(S.size, 1.0 / S.size)
    # 1. warm start on the cheap objective
    w = _ba_on(obj, S, w, cheap=True, iters=ba_iters)
    keep = w > keep_threshold * w.max()
    S, w = S[keep], w[keep] / w[keep].sum()
    f_all = None
    lam = 0.0
    # 2a. accurate-enough BA steps and Newton on the fast objective
    w = _ba_on(fast, S, w, cheap=False, iters=40)
    keep = w > 1e-14
    S, w = S[keep], w[keep] / w[keep].sum()
    if fast is not obj:
        S, w, _, _ = _newton(fast, S, w, tol=1e-6)
    for outer in range(max_outer):
        # 2b. Newton on the fixed-point equations of the accurate objective
        tol_round = 0.1 * add_tol
        S, w, lam, f_S = _newton(obj, S, w, tol=tol_round)
        for _again in range(2):
            act = w > 0
            if float(np.max(np.abs(f_S[act] - lam))) <= support_tol:
                break
            w = _ba_on(obj, S, w, cheap=False, iters=30)
            S, w, lam, f_S = _newton(obj, S, w, tol=tol_round)
        # 3. sweep every candidate: the Jensen bound first, then the fast objective, then
        # the accurate one only where a violation is still possible
        f_all = np.full(n, -np.inf)
        f_all[S] = f_S
        others = np.setdiff1d(np.arange(n), S)
        if others.size:
            ub = obj.upper_bound(others, S, w)
            if ub is None:
                check = others
                if fast is not obj:
                    f_fast = fast.f(others, S, w)
                    f_all[others] = f_fast
                    check = others[f_fast > lam + add_tol - 0.02]
                if check.size:
                    f_all[check] = obj.f(check, S, w)
            else:
                f_all[others] = ub
                check = others[ub > lam + add_tol]
                if check.size and fast is not obj:
                    f_fast = fast.f(check, S, w)
                    f_all[check] = f_fast
                    check = check[f_fast > lam + add_tol - 0.02]
                if check.size:
                    f_all[check] = obj.f(check, S, w)
        viol = np.setdiff1d(np.flatnonzero(f_all > lam + add_tol), S)
        act = w > 0
        resid = float(np.max(np.abs(f_S[act] - lam)))
        final_resid = resid
        support_ok = resid <= max(add_tol, 10 * getattr(obj, "precision", 0.0)) or (
            resid <= support_tol and lam - lam_prev < 1e-7
        )
        lam_prev = lam
        if viol.size == 0 and support_ok:
            break
        if viol.size == 0:
            # Newton stalled on the support: a few BA steps there, then Newton again
            w = _ba_on(obj, S, w, cheap=False, iters=50)
            keep = w > 1e-14
            S, w = S[keep], w[keep] / w[keep].sum()
            continue
        order = viol[np.argsort(-f_all[viol])]
        add = _separated(obj, order, min_sep=2.0, cap=32)
        S = np.concatenate([S, add])
        w = np.concatenate([w, np.zeros(add.size)])
        w /= w.sum()
        srt = np.argsort(S)
        S, w = S[srt], w[srt]
    masses = np.zeros(n)
    masses[S] = w
    return CapacitySolution(masses=masses, value=lam, f_all=f_all, n_outer=outer + 1,
                            support_residual=final_resid)
