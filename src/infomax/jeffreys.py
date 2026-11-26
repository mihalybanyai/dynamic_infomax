"""Closed-form Jeffreys prior for the Bernoulli model.

Spec: specs/000-static-infomax-fig1.md §1.5. p_J(theta) is the m -> infinity
limit of the MI-maximising prior; used as a qualitative comparison target
(test T4).
"""
from __future__ import annotations

import numpy as np


def jeffreys_bernoulli_pdf(theta: np.ndarray) -> np.ndarray:
    """p_J(theta) = 1 / (pi * sqrt(theta * (1 - theta))) on (0, 1)."""
    theta = np.asarray(theta, dtype=np.float64)
    return 1.0 / (np.pi * np.sqrt(theta * (1.0 - theta)))


def jeffreys_bernoulli_cdf(theta: np.ndarray) -> np.ndarray:
    """CDF of the Jeffreys prior on the Bernoulli.

    Closed form: F_J(theta) = (2/pi) * arcsin(sqrt(theta)) on [0, 1].
    Used for the K-S test in T4.
    """
    theta = np.asarray(theta, dtype=np.float64)
    return (2.0 / np.pi) * np.arcsin(np.sqrt(np.clip(theta, 0.0, 1.0)))


# ---------------------------------------------------------------------------
# Spec 002 (appended; the spec-000 functions above are unchanged)
# ---------------------------------------------------------------------------


def build_jeffreys(model, *, quadrature_points: int | None = None):
    """`p_J ∝ sqrt(det g)` on `Theta`, in `D` dimensions (spec 002 §4.2).

    Hypercone, curvature off: `sqrt(det g) ∝ r(theta_1)^(D-1)` with a uniform
    cross-section (the Schur complement of `[^3-schur]` is `sigma^-2` for every taper), so
    `p_J` is a `ConeProductPrior` whose `theta_1`-law is `r^(D-1)` normalised by
    Gauss–Legendre quadrature (closed form `D theta_1^(D-1) / W^D` with the taper on).
    Exp-decay, and the cone with curvature: `sqrt(det g)` on a quadrature grid, normalised
    with `quadrature_points` nodes per axis, exposed as `log_normaliser` (in `xi` for
    exp-decay), and sampled by rejection on the grid. Extended precision above `D ≈ 12` is
    not available on this path (OQ-1). Exp-decay from `D = 4` (unless `quadrature_points`
    asks for the grid): adaptive importance sampling (`infomax.sampled`, §4.2, OQ-13), since
    the grid loses Jeffreys' mass where rates nearly coincide.
    """
    import scipy.special

    from infomax.sampled import JEFFREYS_SAMPLED_FROM_D, build_sampled_jeffreys

    if model.family == "exp_decay" and model.D >= JEFFREYS_SAMPLED_FROM_D and quadrature_points is None:
        return build_sampled_jeffreys(model)

    from infomax.priors002 import ConeProductPrior, GridPrior002
    from infomax.quadrature import cone_theta1_rule

    if model.family == "hypercone" and model.curvature == 1.0:
        D, W = model.D, model.W
        if model.taper == 1.0:
            log_c = np.log(D) - D * np.log(W)

            def log_pdf1(t):
                t = np.asarray(t, dtype=float)
                with np.errstate(divide="ignore"):
                    return log_c + (D - 1) * np.log(t) if D > 1 else np.full(t.shape, -np.log(W))

            def sample1(n, rng):
                return W * rng.uniform(size=n) ** (1.0 / D)
        else:
            t, w = cone_theta1_rule(W, W / 400.0)
            log_norm = float(scipy.special.logsumexp(np.log(w) + (D - 1) * np.log(model.taper_r(t))))
            t_grid = np.linspace(0.0, W, 20001)
            pdf = np.exp((D - 1) * np.log(model.taper_r(t_grid)) - log_norm)
            cdf = np.concatenate([[0.0], np.cumsum(0.5 * (pdf[1:] + pdf[:-1]) * np.diff(t_grid))])
            cdf /= cdf[-1]

            def log_pdf1(t):
                with np.errstate(divide="ignore"):
                    return (D - 1) * np.log(model.taper_r(np.asarray(t, float))) - log_norm

            def sample1(n, rng):
                return np.interp(rng.uniform(size=n), cdf, t_grid)

        return ConeProductPrior("p_J", model, log_pdf1, sample1)

    if model.D > 8:
        raise NotImplementedError("Jeffreys above D = 8 needs extended precision (AtomicPriors.jl, OQ-1)")

    def log_root_det(theta):
        g = model.fim(theta)
        sign, logdet = np.linalg.slogdet(g)
        return np.where(sign > 0, 0.5 * logdet, -np.inf)

    return GridPrior002("p_J", model, log_root_det, normaliser_points=quadrature_points)
