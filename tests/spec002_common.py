"""Shared setup for spec 002's tests (specs/002-foreign-q-prediction.md §5).

Not collected by pytest (no `test_` prefix). It holds the cells and tolerances several
test files share, and a builder for the cast present in a cell. Seeds stay literal in
each test (`skills/manage-randomness.md`, rule 3).
"""
from __future__ import annotations

import numpy as np

from infomax.jeffreys import build_jeffreys
from infomax.models import Model, build_model
from infomax.plat import build_plat
from infomax.plognormal import build_pln, build_pln_star
from infomax.pproj import build_pproj
from infomax.pref import build_pref, build_uniform
from infomax.pstar import build_pstar

# ---------------------------------------------------------------------------
# Cells (spec §5.4)
# ---------------------------------------------------------------------------

CHEAP = dict(family="exp_decay", D=2, m=26, sigma=0.1, N=1)
"""The cheap cell of §5.4: exp-decay, `D = 2`, `sigma = 0.1`, `N = 1`."""

CONE_BASE = dict(family="hypercone", m=26, sigma=1.0, N=1, W=50.0)
"""The hypercone's base cell (§5.4): `sigma = 1`, `W = 50`, taper on, `kappa = 1`."""

CURVATURE_CELL = dict(family="hypercone", m=26, sigma=0.1, N=1, W=5.0, falloff=0.05)
"""The curvature cells (§5.4): `sigma = 0.1`, `W = 5`, fall-off 0.05."""

D_SWEEP_GRID: tuple[int, ...] = (1, 2, 3, 4)
"""The `D`-sweep on the candidate-set path (§5.4, §5.3)."""

S_Q_TEST: int = 400
"""Draws per cell in the unit tests; the experiment uses 500 to 2000 (§5.4)."""

# ---------------------------------------------------------------------------
# Tolerances (auto-chosen at test derivation; the test red-team reviews them)
# ---------------------------------------------------------------------------

MC_SIGMAS: float = 4.0
"""Two Monte-Carlo estimates agree when they differ by less than this many combined
standard errors."""

EQUALIZER_SLACK: float = 1e-2
"""T3/T16: nats by which a per-state divergence may exceed the capacity off the support."""

T2_TOL: float = 1e-6
"""T2: `|R(p_J) - R(p_U)|` in nats, about ten times the normalising quadrature's error."""

INFO_SLACK: float = 1e-3
"""Nats of solver slack in inequalities between information values (T9, T11, T23)."""


def cheap_model(**overrides) -> Model:
    """The cheap cell's model, with any knob overridden."""
    return build_model(**{**CHEAP, **overrides})


def cone_model(D: int, **overrides) -> Model:
    """The hypercone's base cell at dimension `D`, with any knob overridden."""
    return build_model(D=D, **{**CONE_BASE, **overrides})


def agree_mc(a: float, b: float, *errors: float, k: float = MC_SIGMAS) -> bool:
    """True when `a` and `b` agree within `k` combined standard errors."""
    return abs(a - b) <= k * float(np.sqrt(np.sum(np.square(errors))))


def xi_from_log_time(theta: np.ndarray) -> np.ndarray:
    """Exp-decay: A&M's compact coordinate from the log decay time, `xi = exp(-exp(-theta))`."""
    return np.exp(-np.exp(-np.asarray(theta, dtype=float)))


def log_time_from_xi(xi: np.ndarray) -> np.ndarray:
    """Inverse of `xi_from_log_time`: `theta = -log(-log xi)`."""
    return -np.log(-np.log(np.asarray(xi, dtype=float)))


def build_cast(model: Model, rng: np.random.Generator) -> dict:
    """The cast of §2.2 present in `model`'s cell, keyed by name (coverage table, §4.2).

    `q̄` is not included: it is formed from the rows (§4.2).
    """
    cast = {
        "p*": build_pstar(model).prior,
        "p*_N/10": build_pstar(model, budget=model.N / 10).prior,
        "p*_10N": build_pstar(model, budget=10 * model.N).prior,
        "p_lat": build_plat(model).prior,
        "p_proj": build_pproj(model, 2000, rng),
        "p_J": build_jeffreys(model),
        "p_U": build_uniform(model),
    }
    if model.family == "exp_decay":
        cast["p_LN"] = build_pln(model)
        cast["p_LN^*"] = build_pln_star(model, rng).prior
        rankings = ("slowest", "fastest", "stiffest") if model.D == 2 else ("slowest", "fastest")
        for ranking in rankings:
            cast[f"p_ref[{ranking}]"] = build_pref(model, ranking)
    else:
        cast["p_ref"] = build_pref(model)
    return cast
