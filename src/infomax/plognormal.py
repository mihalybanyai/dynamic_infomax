"""The log-normal priors `p_LN` and `p_LN^*`, exp-decay only (spec 002 §4.2, OQ-3).

`p_LN`: each log decay time normal with `(theta_bar, tau) = (0, 1)`, as A&M, sorted.
`p_LN^*`: the member of the same family whose `(theta_bar, tau)` maximise
`I_pi(Theta; X_{1:N})`, found by Nelder–Mead with common random numbers. Stubs until the
implementation stage.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import scipy.stats

from infomax.models import Model


def _theta_xi(xi):
    xi = np.asarray(xi, dtype=float)
    with np.errstate(divide="ignore"):
        return -np.log(-np.log(xi))


def build_pln(model: Model, theta_bar: float = 0.0, tau: float = 1.0):
    """`p_LN` with the given parameters (A&M's are the default).

    Each log decay time `theta_mu = -log(-log xi_mu)` is `N(theta_bar, tau^2)`, sorted: an
    `ExpDecayProductPrior` with per-rate density `h(xi) = phi_tau(theta) / (xi (-log xi))`.
    On the matched box each rate's law is truncated to the box and renormalised."""
    from infomax.priors002 import ExpDecayProductPrior, log_diff_ndtr

    if model.family != "exp_decay":
        raise ValueError("p_LN is carried in exp-decay only (§4.2)")
    if not tau > 0:
        raise ValueError("tau must be positive")
    lo, hi = float(model.box.low[0]), float(model.box.high[0])
    z_lo = -np.inf if lo <= 0 else (_theta_xi(lo) - theta_bar) / tau
    z_hi = np.inf if hi >= 1 else (_theta_xi(hi) - theta_bar) / tau
    log_mass = float(log_diff_ndtr(np.array(z_hi), np.array(z_lo)))

    def log_h(xi):
        xi = np.asarray(xi, dtype=float)
        with np.errstate(divide="ignore", invalid="ignore"):
            th = _theta_xi(xi)
            val = scipy.stats.norm.logpdf(th, theta_bar, tau) - np.log(xi) - np.log(-np.log(xi)) - log_mass
        return np.where(np.isfinite(val), val, -np.inf)

    def log_H_interval(a, b):
        za = np.where(np.asarray(a) <= 0, -np.inf, (_theta_xi(np.maximum(a, 1e-300)) - theta_bar) / tau)
        zb = np.where(np.asarray(b) >= 1, np.inf, (_theta_xi(np.minimum(b, 1 - 1e-16)) - theta_bar) / tau)
        return log_diff_ndtr(zb, za) - log_mass

    def sampler(n, rng):
        z = rng.standard_normal((n, model.D))
        if np.isfinite(z_lo) or np.isfinite(z_hi):
            u = scipy.stats.norm.cdf(z)
            p_lo, p_hi = scipy.stats.norm.cdf(z_lo), scipy.stats.norm.cdf(z_hi)
            z = scipy.stats.norm.ppf(p_lo + (p_hi - p_lo) * u)
        th = np.sort(theta_bar + tau * z, axis=-1)
        return np.exp(-np.exp(-th))

    def inv_H(a, b, u):
        za = np.where(np.asarray(a) <= 0, -np.inf, (_theta_xi(np.maximum(a, 1e-300)) - theta_bar) / tau)
        zb = np.where(np.asarray(b) >= 1, np.inf, (_theta_xi(np.minimum(b, 1 - 1e-16)) - theta_bar) / tau)
        # quantiles in the tail-stable direction: the survival side for positive z
        pa, pb = scipy.stats.norm.cdf(za), scipy.stats.norm.cdf(zb)
        z = scipy.stats.norm.ppf(pa + (pb - pa) * u)
        sa, sb = scipy.stats.norm.sf(za), scipy.stats.norm.sf(zb)
        z_sf = scipy.stats.norm.isf(sa - (sa - sb) * u)
        z = np.where(np.broadcast_to(za, z.shape) > 0, z_sf, z)
        return np.exp(-np.exp(-(theta_bar + tau * z)))

    prior = ExpDecayProductPrior("p_LN", model, log_h, log_H_interval, sampler, inv_H=inv_H)
    prior.theta_bar, prior.tau = float(theta_bar), float(tau)
    return prior


@dataclass(frozen=True)
class TunedLogNormal:
    """`p_LN^*` and the information it reaches."""

    prior: object
    theta_bar: float
    tau: float
    information: float


def build_pln_star(model: Model, rng: np.random.Generator, *, n: int = 4096) -> TunedLogNormal:
    """`p_LN^*`, the budget-tuned log-normal (§4.2).

    Nelder–Mead over `(theta_bar, log tau)` from A&M's `(0, 1)`, maximising the Monte-Carlo
    information of `infomax.score.mutual_information` with common random numbers: one
    generator state, drawn once from `rng`, is reused for every trial, so the objective is
    a smooth function of the parameters (DD-L1)."""
    import scipy.optimize

    from infomax.score import mutual_information

    seed = int(rng.integers(0, 2**63 - 1))

    def neg_info(params):
        bar, log_tau = params
        prior = build_pln(model, bar, float(np.exp(log_tau)))
        return -mutual_information(prior, model, rng=np.random.default_rng(seed), n=n)

    res = scipy.optimize.minimize(
        neg_info, x0=np.array([0.0, 0.0]), method="Nelder-Mead",
        options={"xatol": 1e-3, "fatol": 1e-5, "initial_simplex": np.array([[0.0, 0.0], [0.5, 0.0], [0.0, 0.5]]), "maxiter": 200},
    )
    bar, tau = float(res.x[0]), float(np.exp(res.x[1]))
    prior = build_pln(model, bar, tau)
    prior.name = "p_LN^*"
    return TunedLogNormal(prior=prior, theta_bar=bar, tau=tau, information=float(-res.fun))
