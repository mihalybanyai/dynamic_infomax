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

CHEAP_TWIN = {**CHEAP, "sigma": 0.2, "N": 4}
"""The cheap cell's twin (§5.4, F9): the same `sigma_eff = 0.1` at `N = 4`, where `sigma`
and `sigma_eff` differ."""

CONE_BASE_TWIN = {**CONE_BASE, "sigma": 2.0, "N": 4}
"""The cone base cell's twin (§5.4, F9): `sigma_eff = 1` at `N = 4`."""

CHEAP_CELLS = {"N=1": CHEAP, "twin": CHEAP_TWIN}
"""Parametrisation over the cheap cell and its twin."""

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

# T12's tolerances and cells, fixed by spec §5.5 before the fixtures exist (F7); the
# fixtures carry values and metadata only. Auto-chosen in the spec; MB to confirm.
T12_SIGMA: float = 0.1
T12_YMAP = dict(D=3, n_states=10, rtol_y=1e-10, rtol_fim=1e-8)
T12_PSTAR = dict(N=1, atom_fisher=0.5, weight_atol=0.02, I_atol=0.01, B_atol=0.2)
T12_CAPACITY = dict(D=2, N=(1, 2, 4), atol=0.01)
T12_MUTUAL = dict(D=2, levels=(0.1, 0.3, 0.5, 0.7, 0.9), atol=0.005)
T12_TRANSTRUM = dict(D=2, N=1, cloud=2000, ks_p=1e-3, edge_width=0.02, edge_sigmas=4.0)
T12_SPREAD_SHARE: float = 0.25
"""A fixture fails T12 if a recorded Julia run-to-run spread exceeds this share of its tolerance."""


def cheap_model(**overrides) -> Model:
    """The cheap cell's model, with any knob overridden."""
    return build_model(**{**CHEAP, **overrides})


def cone_model(D: int, **overrides) -> Model:
    """The hypercone's base cell at dimension `D`, with any knob overridden."""
    return build_model(D=D, **{**CONE_BASE, **overrides})


def agree_mc(a: float, b: float, *errors: float, k: float = MC_SIGMAS) -> bool:
    """True when `a` and `b` agree within `k` combined standard errors."""
    return abs(a - b) <= k * float(np.sqrt(np.sum(np.square(errors))))


def paired_mcse(a: np.ndarray, b: np.ndarray) -> float:
    """The Monte-Carlo error of `mean(a) - mean(b)` when `a` and `b` share their draws:
    the standard error of the per-draw differences (§4.4)."""
    d = np.asarray(a, dtype=float) - np.asarray(b, dtype=float)
    return float(np.std(d, ddof=1) / np.sqrt(d.size))


def log_mean_exp_with_error(log_w: np.ndarray) -> tuple[float, float]:
    """`log mean(exp(log_w))` and its delta-method standard error, in nats: the brute-force
    Monte-Carlo marginal of F4 and F6."""
    log_w = np.asarray(log_w, dtype=float)
    top = log_w.max()
    w = np.exp(log_w - top)
    return float(top + np.log(w.mean())), float(w.std(ddof=1) / (w.mean() * np.sqrt(w.size)))


def cheap_model_at(cell: dict, **overrides) -> Model:
    """A model at one of `CHEAP_CELLS`' cells, with any knob overridden."""
    return build_model(**{**cell, **overrides})


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
