"""The NML pushforward `p_proj` (spec 002 §4.2, OQ-6).

A port of AtomicPriors.jl's `transtrum`: an ensemble Markov chain on `x` targets
`p_NML(x) ∝ max_theta p(x|theta)`, and the maximum-likelihood `theta-hat` of each
retained step forms the cloud.

The projection (DD-P1) is a batched, box-constrained Levenberg–Marquardt least-squares
fit of `y(theta)` to `x`, started from the nearest points of a Fisher-spaced seed set
(the candidate net of `infomax.pstar`, faces included) and from a walker's previous
estimate. In exp-decay it runs on the unordered cube, which the map's permutation
symmetry makes equivalent, and sorts the result into the ordered `Theta`. The chain is
the affine-invariant stretch move of emcee (Goodman & Weare 2010) [recalled], the
sampler `transtrum` calls through KissMCMC [read: `resources/AtomicPriors.jl/src/max/sample.jl`].
"""
from __future__ import annotations

import numpy as np
from scipy.spatial import cKDTree

from infomax.mixture import log_normal_iso
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
    returns the fits and their squared residuals."""
    lo, hi = np.asarray(model.box.low, float), np.asarray(model.box.high, float)
    th = np.clip(theta0.copy(), lo, hi)
    r = model.y(th) - x
    cost = np.sum(r * r, axis=1)
    lam = np.full(th.shape[0], 1e-3)
    D = th.shape[1]
    for _ in range(iters):
        J = model.jacobian(th)  # (n, m, D)
        g = np.einsum("nmd,nm->nd", J, r)
        # coordinates at a bound with the gradient pushing outward are held
        hold = ((th <= lo + 1e-15) & (g > 0)) | ((th >= hi - 1e-15) & (g < 0))
        JtJ = np.einsum("nmd,nme->nde", J, J)
        diag = np.einsum("ndd->nd", JtJ)
        A = JtJ + (lam[:, None] * (diag + 1e-12))[:, :, None] * np.eye(D)[None]
        H = hold.astype(float)
        A = A * (1.0 - H)[:, :, None] * (1.0 - H)[:, None, :] + np.eye(D)[None] * H[:, :, None]
        rhs = -g * (1.0 - H)
        step = np.linalg.solve(A, rhs[..., None])[..., 0]
        th_new = np.clip(th + step, lo, hi)
        r_new = model.y(th_new) - x
        c_new = np.sum(r_new * r_new, axis=1)
        better = c_new < cost
        th = np.where(better[:, None], th_new, th)
        r = np.where(better[:, None], r_new, r)
        cost = np.where(better, c_new, cost)
        lam = np.where(better, lam * 0.3, lam * 10.0)
        if np.all(lam > 1e8):
            break
    return th, cost


def mle_project(model: Model, x: np.ndarray, *, previous: np.ndarray | None = None) -> np.ndarray:
    """The maximum-likelihood state for data `x` within `Theta`, at `sigma_eff`."""
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
    best_th, best_c = None, None
    for th0 in starts:
        th, c = _lm(model, x, th0)
        if best_th is None:
            best_th, best_c = th, c
        else:
            better = c < best_c
            best_th = np.where(better[:, None], th, best_th)
            best_c = np.where(better, c, best_c)
    if model.box.ordered:
        best_th = np.sort(best_th, axis=-1)
    return best_th


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


def build_pproj(
    model: Model,
    n_samples: int,
    rng: np.random.Generator,
    *,
    n_walkers: int = 64,
    burn: int = 1000,
    a: float = 2.0,
) -> CloudPrior:
    """`p_proj` as a cloud of `n_samples` maximum-likelihood estimates (§4.2)."""
    m = model.m_out
    if n_walkers % 2:
        n_walkers += 1
    theta0 = model.box.sample_uniform(n_walkers, rng)
    X = model.y(theta0)  # walkers start on the manifold
    logp, TH = _log_nml_unnorm(model, X, previous=theta0)
    half = n_walkers // 2
    n_keep = int(np.ceil(n_samples / n_walkers))
    kept = []
    for step in range(burn + n_keep):
        for first in (0, 1):
            sl_k = slice(0, half) if first == 0 else slice(half, n_walkers)
            sl_c = slice(half, n_walkers) if first == 0 else slice(0, half)
            Xk, Xc = X[sl_k], X[sl_c]
            partner = Xc[rng.integers(0, half, size=half)]
            z = ((a - 1.0) * rng.uniform(size=half) + 1.0) ** 2 / a
            prop = partner + z[:, None] * (Xk - partner)
            lp_prop, th_prop = _log_nml_unnorm(model, prop, previous=TH[sl_k])
            log_acc = (m - 1) * np.log(z) + lp_prop - logp[sl_k]
            acc = np.log(rng.uniform(size=half)) < log_acc
            idx = np.arange(n_walkers)[sl_k][acc]
            X[idx] = prop[acc]
            logp[idx] = lp_prop[acc]
            TH[idx] = th_prop[acc]
        if step >= burn:
            kept.append(TH.copy())
    cloud = np.concatenate(kept, axis=0)[:n_samples]
    return CloudPrior("p_proj", cloud)
