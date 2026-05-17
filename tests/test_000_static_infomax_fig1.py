"""Tests for spec 000 — static infomax prior, Mattingly Fig 1 reproduction.

This file is currently scaffolding only. Per skills/write-math-spec.md the
status-table gating allows test scaffolding once Setup and Objective are
reviewed; full property assertions follow once Derivation is reviewed and
implementation follows once Algorithm is reviewed. All sections of spec 000
are now reviewed, but we are progressing stepwise: scaffolding first.

Each test below corresponds to one acceptance criterion (T1-T7) in spec
§4. The bodies are intentionally `pytest.skip(...)`; they will be filled
in in the next step.

The BA loop is fully deterministic (uniform init, deterministic likelihood
matrix, deterministic fixed-point updates), so no `np.random.Generator`
is threaded through the API — see manage-randomness skill rule 7. If a
test ever needs randomness (e.g., for a perturbation-stability check
that turns out to be useful), it will construct its own generator with a
hardcoded literal seed per rule 3.
"""
from __future__ import annotations

import numpy as np
import pytest

from infomax.likelihood import binomial_log_likelihood, cell_centred_grid


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

DEFAULT_N_THETA: int = 1000
"""Headline grid resolution per spec §3.1."""

M_SWEEP: tuple[int, ...] = (1, 2, 3, 4, 5, 10, 20, 50, 100)
"""Sample budgets covered by the m-sweep per spec §3.6."""

N_THETA_SWEEP: tuple[int, ...] = (200, 500, 1000, 2000)
"""Grid resolutions used for the grid-invariance check (T5) per spec §3.1."""


@pytest.fixture
def n_theta() -> int:
    """Default grid resolution for tests that don't sweep it explicitly."""
    return DEFAULT_N_THETA


@pytest.fixture
def theta_grid(n_theta: int) -> np.ndarray:
    """Cell-centred uniform grid on [0, 1] (spec §3.1)."""
    return cell_centred_grid(n_theta)


@pytest.fixture(params=M_SWEEP, ids=lambda m: f"m={m}")
def m(request: pytest.FixtureRequest) -> int:
    """Sample budget; parametrised across the full m-sweep (spec §3.6)."""
    return request.param


@pytest.fixture
def log_likelihood(theta_grid: np.ndarray, m: int) -> np.ndarray:
    """Precomputed log p(x|theta, m), shape (n_theta, m+1) (spec §3.2)."""
    return binomial_log_likelihood(theta_grid, m)


# ---------------------------------------------------------------------------
# Acceptance criteria — spec §4
# ---------------------------------------------------------------------------


def test_t1_m1_closed_form() -> None:
    """T1 — m=1 closed form.

    Spec §1.5, §4. With m=1, BA must converge to p* = 1/2 delta(0) + 1/2
    delta(1), MI* = log 2 nats. Atom centroids within 2/n_theta of {0, 1},
    masses within 0.01 of 1/2 each, MI within 0.001 nats of log 2.
    """
    pytest.skip("property tests pending — scaffolding only")


def test_t2_fkl_flatness_on_support() -> None:
    """T2 — f_KL flatness on support.

    Spec §1.3, §4. At every grid cell with mass > p_thresh, f_KL agrees
    with the achieved MI to within rel. tol. 1e-3; off-support cells
    satisfy f_KL <= MI (no positive violations beyond fp slack).

    Parametrised across the full m-sweep.
    """
    pytest.skip("property tests pending — scaffolding only")


def test_t3_capacity_bound() -> None:
    """T3 — Capacity bound MI* <= log K.

    Spec §4 (Mattingly Fig 3C bound). Parametrised across the m-sweep.
    """
    pytest.skip("property tests pending — scaffolding only")


def test_t4_converges_to_jeffreys() -> None:
    """T4 — Convergence to Jeffreys (qualitative).

    Spec §1.5, §4. At m=100, the mass-weighted CDF of p* agrees with
    the Jeffreys CDF in Kolmogorov-Smirnov distance below 0.05.
    """
    pytest.skip("property tests pending — scaffolding only")


def test_t5_grid_invariance_of_atoms() -> None:
    """T5 — Grid invariance of atom locations.

    Spec §3.1, §4. For m in {1, 2, 5, 10} and n_theta in {200, 1000, 2000},
    detected atom counts agree and centroids agree across grids to within
    3 * max(1/n_theta) of each other. Pins atoms as a property of the
    problem, not the discretisation.
    """
    pytest.skip("property tests pending — scaffolding only")


def test_t6_ba_monotonicity() -> None:
    """T6 — BA monotonicity.

    Spec §1.4, §4. I_tau is non-decreasing across BA iterations, up to
    floating-point slack 1e-12 per step. Direct check of the Blahut /
    Arimoto convergence guarantee.
    """
    pytest.skip("property tests pending — scaffolding only")


def test_t7_degenerate_likelihood() -> None:
    """T7 — Algorithmic sanity on a degenerate case.

    Spec §4. If p(x|theta) is theta-independent ("experiment that learns
    nothing"), MI* = 0, f_KL identically zero, and p* equals the uniform
    initialisation. Cheap structural check on the BA loop.
    """
    pytest.skip("property tests pending — scaffolding only")
