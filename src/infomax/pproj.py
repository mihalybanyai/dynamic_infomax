"""The NML pushforward `p_proj` (spec 002 §4.2, OQ-6).

Adaptive importance sampling. Each round draws `theta` from a proposal made of atoms, adds
noise at `sigma_eff`, fits the maximum-likelihood `theta-hat(x)` within `Theta`, and weights
the draw by `p(x | theta-hat(x)) / m_q(x)`; the proposal's mixture `m_q` is a finite sum, so
the weights are exact. The first proposal is the draws of a broad prior (Jeffreys, or `p_U`
for an independent second start) used as atoms; each later one is the previous round's
weighted cloud, mixed with 10% of those first atoms so that no weight is unbounded. The fit
supplies the faces' mass: data beyond a face project onto it, so the next proposal has atoms
there. A warm start (`start=`, a neighbouring cell's cloud) changes only the cost, since the
weights make every cloud consistent for `p_proj` whatever its proposal. The last round uses
tight fits: along sloppy directions the likelihood is nearly flat and the default fit's
stopping rule moves `theta-hat` (DD-P1). The result is a weighted `CloudPrior`.

The projection (DD-P1) is a batched, box-constrained Levenberg–Marquardt least-squares
fit of `y(theta)` to `x`, started from the nearest points of a Fisher-spaced seed set
(the candidate net of `infomax.pstar`, faces included) and, optionally, from a previous
estimate. In exp-decay it runs on the unordered cube, which the map's permutation
symmetry makes equivalent, and sorts the result into the ordered `Theta`. `tight=True`
polishes each fit by bounded least squares at `1e-15` tolerances.
"""
from __future__ import annotations

import numpy as np
from scipy.spatial import cKDTree

import warnings

from infomax.mixture import log_normal_iso, mixture_logpdf
from infomax.models import Model
from infomax.priors002 import CloudPrior

_SEED_CACHE: dict = {}


def _seed_bank(model: Model):
    from infomax.priors002 import _model_key
    from infomax.pstar import candidate_set

    key = (_model_key(model), round(model.sigma_eff, 14))
    hit = _SEED_CACHE.get(key)
    if hit is None:
        theta = candidate_set(model, spacing=1.0)
        Y = model.y(theta)
        hit = (theta, cKDTree(Y / model.sigma_eff))
        if len(_SEED_CACHE) > 16:
            _SEED_CACHE.clear()
        _SEED_CACHE[key] = hit
    return hit


def _lm(model: Model, x: np.ndarray, theta0: np.ndarray, *, iters: int = 40) -> tuple[np.ndarray, np.ndarray]:
    """Box-constrained Levenberg–Marquardt from each row of `theta0` toward each row of `x`;
    returns the fits and their squared residuals. A row stops once a step lowers its cost
    by less than `1e-12` of it, or its damping passes `1e6` (no step helps)."""
    lo, hi = np.asarray(model.box.low, float), np.asarray(model.box.high, float)
    th = np.clip(theta0.copy(), lo, hi)
    r = model.y(th) - x
    cost = np.sum(r * r, axis=1)
    lam = np.full(th.shape[0], 1e-3)
    D = th.shape[1]
    eye = np.eye(D)[None]
    act = np.arange(th.shape[0])
    for _ in range(iters):
        if act.size == 0:
            break
        ta, ra, xa = th[act], r[act], x[act]
        J = model.jacobian(ta)  # (n, m, D)
        g = np.einsum("nmd,nm->nd", J, ra)
        # coordinates at a bound with the gradient pushing outward are held
        hold = ((ta <= lo + 1e-15) & (g > 0)) | ((ta >= hi - 1e-15) & (g < 0))
        JtJ = np.einsum("nmd,nme->nde", J, J)
        diag = np.einsum("ndd->nd", JtJ)
        ridge = 1e-12 * np.maximum(diag.max(axis=1), 1e-300)
        A = JtJ + (lam[act][:, None] * diag + ridge[:, None])[:, :, None] * eye
        H = hold.astype(float)
        A = A * (1.0 - H)[:, :, None] * (1.0 - H)[:, None, :] + eye * H[:, :, None]
        step = np.linalg.solve(A, (-g * (1.0 - H))[..., None])[..., 0]
        th_new = np.clip(ta + step, lo, hi)
        r_new = model.y(th_new) - xa
        c_new = np.sum(r_new * r_new, axis=1)
        c_old = cost[act]
        better = c_new < c_old
        th[act] = np.where(better[:, None], th_new, ta)
        r[act] = np.where(better[:, None], r_new, ra)
        cost[act] = np.where(better, c_new, c_old)
        lam_a = np.where(better, np.maximum(lam[act] * 0.3, 1e-9), lam[act] * 10.0)
        lam[act] = lam_a
        done = (better & (c_old - c_new <= 1e-12 * c_old)) | (lam_a > 1e6)
        act = act[~done]
    return th, cost


def _polish(model: Model, x: np.ndarray, theta: np.ndarray) -> np.ndarray:
    """Each fit polished by bounded least squares at `1e-15` tolerances (DD-P1)."""
    from scipy.optimize import least_squares

    lo, hi = np.asarray(model.box.low, float), np.asarray(model.box.high, float)
    out = np.empty_like(theta)
    for i in range(x.shape[0]):
        res = least_squares(
            lambda t: model.y(t[None])[0] - x[i], np.clip(theta[i], lo, hi), bounds=(lo, hi),
            jac=lambda t: model.jacobian(t[None])[0], xtol=1e-15, ftol=1e-15, gtol=1e-15,
            max_nfev=2000, method="trf",
        )
        out[i] = res.x
    return out


def mle_project(model: Model, x: np.ndarray, *, previous: np.ndarray | None = None, tight: bool = False) -> np.ndarray:
    """The maximum-likelihood state for data `x` within `Theta`, at `sigma_eff`; `tight`
    polishes each fit (DD-P1)."""
    x = np.atleast_2d(np.asarray(x, dtype=float))
    n = x.shape[0]
    if model.family == "hypercone" and model.D == 1 and model.D_full == 1 and model.curvature == 1.0:
        return np.clip(x[:, :1], 0.0, model.W)
    seeds, tree = _seed_bank(model)
    k = min(3, seeds.shape[0])
    _, nn = tree.query(x / model.sigma_eff, k=k)
    nn = np.atleast_2d(nn).reshape(n, k)
    starts = [seeds[nn[:, j]] for j in range(k)]
    if previous is not None:
        starts.append(np.asarray(previous, dtype=float))
    # all starting points in one batch
    th, c = _lm(model, np.tile(x, (len(starts), 1)), np.concatenate(starts))
    th = th.reshape(len(starts), n, -1)
    c = c.reshape(len(starts), n)
    best = th[np.argmin(c, axis=0), np.arange(n)]
    if tight:
        best = _polish(model, x, best)
    # a fit that reaches a face lies on it exactly: snap values within 1e-12 of the range
    # (the polish can stop at 1e-20 instead of 0)
    lo, hi = np.asarray(model.box.low, float), np.asarray(model.box.high, float)
    eps = 1e-12 * (hi - lo)
    best = np.where(best - lo < eps, lo, np.where(hi - best < eps, hi, best))
    if model.box.ordered:
        best = np.sort(best, axis=-1)
    return best


def _log_nml_unnorm(model: Model, x: np.ndarray, previous=None):
    th = mle_project(model, x, previous=previous)
    return log_normal_iso(x, model.y(th), model.sigma_eff), th


def nml_log_normaliser(model: Model, rng: np.random.Generator, *, n: int = 4096) -> tuple[float, float]:
    """`log ∫ max_theta p(x|theta) dx` at `sigma_eff`, with its Monte-Carlo error (T11).

    Importance sampling from `p_U`'s marginal at 1.25 times the noise (DD-P2):
    `Z = E_q[max_theta p(x|theta) / q(x)]`, with the delta-method error of `log Z`."""
    from infomax.pref import build_uniform

    s = model.sigma_eff
    p_U = build_uniform(model)
    theta = p_U.sample(n, rng)
    lam = 1.25
    x = model.y(theta) + lam * s * rng.standard_normal((n, model.m_out))
    log_q = p_U._lmn(model, x, lam * s)
    log_f, _ = _log_nml_unnorm(model, x)
    lr = log_f - log_q
    top = lr.max()
    r = np.exp(lr - top)
    mean = r.mean()
    return float(top + np.log(mean)), float(r.std(ddof=1) / (mean * np.sqrt(n)))


def _first_prior(model: Model, first: str):
    if first == "jeffreys":
        from infomax.jeffreys import build_jeffreys

        return build_jeffreys(model)
    if first == "uniform":
        from infomax.pref import build_uniform

        return build_uniform(model)
    raise ValueError(f"unknown first proposal {first!r}")


def _is_round(model, atoms, w, base, alpha, n, rng, tight):
    """One round: draw from the proposal `(1 - alpha) * cloud + alpha * base`, fit, weight."""
    s = model.sigma_eff
    theta0 = atoms[rng.choice(atoms.shape[0], size=n, p=w)]
    from_base = rng.uniform(size=n) < alpha
    theta0[from_base] = base[rng.integers(0, base.shape[0], size=int(from_base.sum()))]
    x = model.y(theta0) + s * rng.standard_normal((n, model.m_out))
    keep = w > 0
    log_cloud = mixture_logpdf(x, model.y(atoms[keep]), np.log(w[keep]), s)
    log_base = mixture_logpdf(x, model.y(base), np.full(base.shape[0], -np.log(base.shape[0])), s)
    log_q = np.logaddexp(np.log1p(-alpha) + log_cloud, np.log(alpha) + log_base)
    theta_hat = mle_project(model, x, tight=tight)
    log_w = log_normal_iso(x, model.y(theta_hat), s) - log_q
    wt = np.exp(log_w - log_w.max())
    wt /= wt.sum()
    return theta_hat, wt, float(1.0 / np.sum(wt**2) / n)


def build_pproj(
    model: Model,
    rng: np.random.Generator,
    *,
    start: CloudPrior | None = None,
    first: str = "jeffreys",
    n_cold: int = 8000,
    n_warm: int = 2000,
    alpha: float = 0.1,
    ess_ok: float = 0.85,
    max_rounds: int = 12,
) -> CloudPrior:
    """`p_proj` as a weighted cloud of maximum-likelihood estimates (§4.2, OQ-6).

    Cold start (`start=None`): `n_cold` draws of the `first` prior ("jeffreys" or
    "uniform") are the first and the defensive proposal. Warm start: a neighbouring cell's
    cloud is the first proposal, with `n_warm` draws per round, its atoms clipped into this
    model's `Theta`. Rounds continue until the effective sample size reaches `ess_ok` in two
    consecutive rounds (at least two rounds, at most `max_rounds`); a last round with tight
    fits gives the cloud. A warm start whose last round falls below `ess_ok` repeats cold.
    The returned prior carries `ess` (as a fraction of the draws in `ess_fraction`),
    `rounds` and `warm`."""
    n = n_cold if start is None else n_warm
    base = _first_prior(model, first).sample(n, rng)
    if start is None:
        atoms, w = base, np.full(n, 1.0 / n)
    else:
        lo, hi = np.asarray(model.box.low, float), np.asarray(model.box.high, float)
        atoms = np.clip(np.asarray(start.atoms, dtype=float), lo, hi)
        if model.box.ordered:
            atoms = np.sort(atoms, axis=-1)
        w = np.asarray(start.weights, dtype=float)
    ok, rounds = 0, 0
    for rnd in range(max_rounds):
        atoms, w, ess = _is_round(model, atoms, w, base, alpha, n, rng, tight=False)
        rounds += 1
        ok = ok + 1 if ess >= ess_ok else 0
        if rnd >= 1 and ok >= 2:
            break
    atoms, w, ess = _is_round(model, atoms, w, base, alpha, n, rng, tight=True)
    rounds += 1
    if ess < ess_ok and start is not None:
        return build_pproj(model, rng, first=first, n_cold=n_cold, alpha=alpha, ess_ok=ess_ok, max_rounds=max_rounds)
    if ess < ess_ok:
        warnings.warn(f"p_proj: effective sample size {ess:.2f} of the draws, below {ess_ok}", RuntimeWarning, stacklevel=2)
    cloud = CloudPrior("p_proj", atoms, w)
    cloud.ess_fraction, cloud.rounds, cloud.warm = ess, rounds, start is not None
    return cloud
