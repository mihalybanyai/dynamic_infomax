"""The two scores of spec 002 and their pieces (§2.1, §4.4).

`R_N` is the cumulative redundancy (2.1.1), estimated from one draw of the sufficient
statistic `xbar`; `r_N` is the one-step excess log-loss on `x'` at noise `sigma` (2.1.5).

Common random numbers (§4.4). A cell draws, in this order, the nature's `theta`, then
standard normals `e1` and `e2`, and sets `xbar = y + sigma_eff e1`, `x' = y + sigma e2`.
Every prior is scored on the same draws, so the error of a difference is the standard
error of the per-draw differences; and two cells that differ only in `N` (or `sigma` at
fixed `sigma_eff`) share their `theta`, `e1` and `e2` (T17, §2.1's invariance).
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from infomax.mixture import kl_to_mixture, log_normal_iso, mixture_logpdf
from infomax.models import Model
from infomax.priors002 import CloudPrior, DiscretePrior


@dataclass(frozen=True)
class CellScores:
    """One cell's scores per prior, with Monte-Carlo errors, floors and mismatches (§4.4).

    Dict keys are prior names. `draws_R` and `draws_r` hold the per-draw arrays. The
    errors of mismatches come from per-draw differences (§4.4, "Errors of differences").
    `theta` and `labels` are the nature's draws and their labels (§4.3). `floor_sub` is the
    submodel's own floor for a nested hypercone nature, `None` otherwise. `mean_shift` and
    `spread_mismatch` are the two terms of (3.3.1) per prior, averaged over draws (§4.5).
    """

    R_mean: dict
    R_mcse: dict
    r_mean: dict
    r_mcse: dict
    floor_R: float
    floor_r: float
    mismatch_R: dict
    mismatch_r: dict
    draws_R: dict
    draws_r: dict
    mismatch_R_mcse: dict | None = None
    mismatch_r_mcse: dict | None = None
    theta: np.ndarray | None = None
    labels: np.ndarray | None = None
    floor_sub: float | None = None
    mean_shift: dict | None = None
    spread_mismatch: dict | None = None


def _mcse(d: np.ndarray) -> float:
    d = np.asarray(d, dtype=float)
    return float(np.std(d, ddof=1) / np.sqrt(d.size))


def _draw(model: Model, nature_model: Model, nature: tuple, S_q: int, rng: np.random.Generator, literal_nfold: bool):
    from infomax.qfamily import sample_nature

    theta, labels = sample_nature(nature_model, nature, S_q, rng)
    y = nature_model.y(theta)
    m = y.shape[1]
    if literal_nfold:
        n = int(round(model.N))
        X = y[:, None, :] + model.sigma * rng.standard_normal((S_q, n, m))
        e2 = rng.standard_normal((S_q, m))
        return theta, labels, y, X, y + model.sigma * e2
    e1 = rng.standard_normal((S_q, m))
    e2 = rng.standard_normal((S_q, m))
    return theta, labels, y, y + model.sigma_eff * e1, y + model.sigma * e2


def _literal_log_marginal(prior, model: Model, X: np.ndarray) -> np.ndarray:
    """`log m_pi(X_{1:N})` of the literal `N`-fold channel: the explicit product over the
    `N` observations for a discrete prior; for others, `log m_pi(xbar)` plus the exact
    sufficiency factor `log p(X | xbar)` (§4.4), which is the same for every prior."""
    if not isinstance(prior, DiscretePrior):
        n = X.shape[1]
        xbar = X.mean(axis=1)
        log_fact = np.sum(log_normal_iso(X, xbar[:, None, :], model.sigma), axis=1) - log_normal_iso(xbar, xbar, model.sigma / np.sqrt(n))
        return prior.log_marginal(model, xbar) + log_fact
    keep = prior.weights > 0
    n = X.shape[1]
    Ya = np.tile(model.y(prior.atoms[keep]), n)
    return mixture_logpdf(X.reshape(X.shape[0], -1), Ya, prior.log_weights[keep], model.sigma)


def score_cell(
    model: Model,
    priors: dict,
    nature: tuple,
    *,
    S_q: int,
    rng: np.random.Generator,
    literal_nfold: bool = False,
    nature_model: Model | None = None,
    scores: tuple[str, ...] = ("R", "r"),
) -> CellScores:
    """Score every prior in `priors` on one cell, under common random numbers (§4.4).

    `model` is the agent's model. For a nested hypercone nature, `nature_model` is the
    `D_max` cone the nature lives in (§2.3); the agent's predictions share its data space.
    `scores=("R",)` skips the one-step score: no predictive is evaluated, and the `r` fields
    are empty dicts with `floor_r` NaN. The draws, `x'` included, are the same either way, so
    `R` is identical whichever scores are asked for (experiment 002, tier 0).
    """
    from infomax.diagnostics import gaussian_kl_split
    from infomax.qfamily import nature_prior, submodel_floor

    nm = model if nature_model is None else nature_model
    theta, labels, y, xbar, x_prime = _draw(model, nm, nature, S_q, rng, literal_nfold)
    s_eff = model.sigma_eff
    if literal_nfold:
        X = xbar
        log_p_x = np.sum(log_normal_iso(X, y[:, None, :], model.sigma), axis=1)
        xbar = X.mean(axis=1)
    else:
        log_p_x = log_normal_iso(xbar, y, s_eff)
    log_p_xp = log_normal_iso(x_prime, y, model.sigma)

    want_r = "r" in scores
    cache: dict = {}

    def marg(obj, mdl):
        key = id(obj)
        if key not in cache:
            if literal_nfold:
                lm = _literal_log_marginal(obj, mdl, X)
            else:
                lm = obj.log_marginal(mdl, xbar)
            cache[key] = (lm, obj.log_predictive(mdl, x_prime, xbar) if want_r else None)
        return cache[key]

    q_obj = nature_prior(nm, nature)
    q_m, q_p = marg(q_obj, nm) if nature[0] != "own" else marg(nature[1], model)
    floor_draws_R = log_p_x - q_m
    floor_draws_r = log_p_xp - q_p if want_r else None

    out = {k: {} for k in ("R_mean", "R_mcse", "r_mean", "r_mcse", "mm_R", "mm_r", "mm_R_se", "mm_r_se", "dR", "dr")}
    for name, prior in priors.items():
        lm, lp = marg(prior, model)
        dR = log_p_x - lm
        out["dR"][name] = dR
        out["R_mean"][name], out["R_mcse"][name] = float(dR.mean()), _mcse(dR)
        mR = q_m - lm
        out["mm_R"][name], out["mm_R_se"][name] = float(mR.mean()), _mcse(mR)
        if want_r:
            dr, mr = log_p_xp - lp, q_p - lp
            out["dr"][name] = dr
            out["r_mean"][name], out["r_mcse"][name] = float(dr.mean()), _mcse(dr)
            out["mm_r"][name], out["mm_r_se"][name] = float(mr.mean()), _mcse(mr)

    # §3.3's split, against the row's matched predictive
    shift, spread = {}, {}
    try:
        q_obj_m = nature[1] if nature[0] == "own" else q_obj
        mu_q, S_q_cov = q_obj_m.posterior_predictive_moments(nm if nature[0] != "own" else model, xbar)
        mom = {}
        for name, prior in priors.items():
            key = id(prior)
            if key not in mom:
                mom[key] = (mu_q, S_q_cov) if prior is q_obj_m else prior.posterior_predictive_moments(model, xbar)
            mu_p, S_p = mom[key]
            a = np.empty(xbar.shape[0])
            b = np.empty(xbar.shape[0])
            for i in range(xbar.shape[0]):
                a[i], b[i] = gaussian_kl_split(mu_q[i], S_q_cov[i], mu_p[i], S_p[i])
            shift[name], spread[name] = float(a.mean()), float(b.mean())
    except NotImplementedError:
        shift, spread = None, None

    floor_sub = None
    if nature[0] == "nested" and nm.family == "hypercone" and model.fixed is not None:
        floor_sub = float(np.mean(submodel_floor(nm, model.D, theta)))

    return CellScores(
        R_mean=out["R_mean"], R_mcse=out["R_mcse"], r_mean=out["r_mean"], r_mcse=out["r_mcse"],
        floor_R=float(floor_draws_R.mean()), floor_r=float(floor_draws_r.mean()) if want_r else float("nan"),
        mismatch_R=out["mm_R"], mismatch_r=out["mm_r"], draws_R=out["dR"], draws_r=out["dr"],
        mismatch_R_mcse=out["mm_R_se"], mismatch_r_mcse=out["mm_r_se"], theta=theta, labels=labels,
        floor_sub=floor_sub, mean_shift=shift, spread_mismatch=spread,
    )


def log_marginal(prior, model: Model, xbar: np.ndarray, *, method: str = "auto") -> np.ndarray:
    """`log m_pi(xbar)`: an exact sum for discrete priors, quadrature or importance
    sampling for continuous ones (`method` in {"auto", "atoms", "quadrature"})."""
    if method == "atoms" and not isinstance(prior, DiscretePrior):
        raise ValueError("method='atoms' needs a discrete prior")
    if method == "quadrature" and isinstance(prior, DiscretePrior):
        raise ValueError("method='quadrature' needs a continuous prior")
    return prior.log_marginal(model, xbar)


def matched_floor(model: Model, nature: tuple, *, S_q: int, rng: np.random.Generator, score: str = "R") -> tuple[float, float]:
    """Nature's own information, `I_q` (or the conditional one for `score="r"`), with its error."""
    from infomax.qfamily import nature_prior

    theta, _, y, xbar, x_prime = _draw(model, model, nature, S_q, rng, False)
    q = nature_prior(model, nature)
    if score == "R":
        d = log_normal_iso(xbar, y, model.sigma_eff) - q.log_marginal(model, xbar)
    else:
        d = log_normal_iso(x_prime, y, model.sigma) - q.log_predictive(model, x_prime, xbar)
    return float(d.mean()), _mcse(d)


def marginal_mismatch(model: Model, nature: tuple, prior, *, S_q: int, rng: np.random.Generator, score: str = "R") -> tuple[float, float]:
    """`D_KL(m_q || m_pi)` (or the posterior-predictive mismatch of (2.1.6)), with its error."""
    from infomax.qfamily import nature_prior

    theta, _, y, xbar, x_prime = _draw(model, model, nature, S_q, rng, False)
    q = nature_prior(model, nature)
    if score == "R":
        d = q.log_marginal(model, xbar) - prior.log_marginal(model, xbar)
    else:
        d = q.log_predictive(model, x_prime, xbar) - prior.log_predictive(model, x_prime, xbar)
    return float(d.mean()), _mcse(d)


def per_state_redundancy(prior, model: Model, theta: np.ndarray, *, rng: np.random.Generator | None = None, n_x: int = 64) -> np.ndarray:
    """`R_N^theta(pi) = D_KL(p(xbar|theta) || m_pi)` per state (§3.2, §4.5).

    Discrete priors (and clouds): the deterministic quadrature of `infomax.mixture`
    (Gauss–Hermite in the span of the nearby atoms; exact in 1-D), whatever `n_x` and
    `rng` (DD-K1). Continuous priors: Monte Carlo over `n_x` draws of `xbar` per state."""
    theta = np.atleast_2d(np.asarray(theta, dtype=float))
    s = model.sigma_eff
    Yt = model.y(theta)
    if isinstance(prior, DiscretePrior):
        keep = prior.weights > 0
        return kl_to_mixture(Yt, model.y(prior.atoms[keep]), prior.log_weights[keep], s)
    rng = np.random.default_rng(20261125) if rng is None else rng
    out = np.empty(theta.shape[0])
    for i in range(theta.shape[0]):
        e = rng.standard_normal((n_x, Yt.shape[1]))
        x = Yt[i] + s * e
        out[i] = float(np.mean(log_normal_iso(x, Yt[i], s) - prior.log_marginal(model, x)))
    return out


def _entropy_1d(prior, model: Model, s: float) -> float:
    """`I = H(m) - H(noise)` for one-dimensional data, by a fine trapezoid in `x`."""
    if isinstance(prior, DiscretePrior):
        keep = prior.weights > 0
        y = model.y(prior.atoms[keep])[:, 0]
    else:
        theta, _ = prior.nodes(model, s) if not hasattr(prior, "_theta1_rule") else (np.array([[0.0], [model.W]]), None)
        y = model.y(theta)[:, 0]
    x = np.linspace(y.min() - 12 * s, y.max() + 12 * s, 40001)[:, None]
    lm = prior._lmn(model, x, s)
    dens = np.exp(lm)
    h = -np.trapezoid(dens * lm, x[:, 0])
    return float(h - 0.5 * np.log(2 * np.pi * np.e * s**2))


def mutual_information(prior, model: Model, *, rng: np.random.Generator | None = None, n: int = 4096) -> float:
    """`I_pi(Theta; X_{1:N})` in nats, at `sigma_eff`.

    One-dimensional data: deterministic, `H(m) - H(noise)` by quadrature. Discrete priors
    with at most 600 atoms: `sum_a w_a f(theta_a)` with the deterministic per-state
    divergence. Larger clouds and continuous priors: Monte Carlo over `n` draws of
    `(theta, xbar)`, `theta` from the prior's own sampler (common random numbers for a
    fixed `rng` state)."""
    s = model.sigma_eff
    if model.m_out == 1:
        return _entropy_1d(prior, model, s)
    if isinstance(prior, DiscretePrior) and not isinstance(prior, CloudPrior) and int(np.sum(prior.weights > 0)) <= 600:
        keep = prior.weights > 0
        Ya = model.y(prior.atoms[keep])
        return float(prior.weights[keep] @ kl_to_mixture(Ya, Ya, prior.log_weights[keep], s))
    rng = np.random.default_rng(20261125) if rng is None else rng
    theta = prior.sample(n, rng)
    y = model.y(theta)
    x = y + s * rng.standard_normal(y.shape)
    return float(np.mean(log_normal_iso(x, y, s) - prior.log_marginal(model, x)))


def bias_pressure(prior, model: Model, theta: np.ndarray, *, rng: np.random.Generator | None = None) -> np.ndarray:
    """A&M's bias pressure `b(theta) = D_KL(p(x|theta) || m_pi) - I_pi`, single observation."""
    return per_state_redundancy(prior, model, theta, rng=rng) - mutual_information(prior, model, rng=rng)
