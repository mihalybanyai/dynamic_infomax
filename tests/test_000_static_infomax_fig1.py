"""Tests for spec 000 — static infomax prior, Mattingly Fig 1 reproduction.

One test per acceptance criterion (T1-T9 in spec §4 post-F13/F15
revisions) plus one cross-cutting self-consistency test
(`test_mi_fkl_self_consistency`) added per red-team F1. Properties are
asserted against the stubs in `src/infomax/`, which currently raise
`NotImplementedError`; the tests therefore fail meaningfully against
the absent implementation per the `derive-test-suite` skill, step 5.

Status:
    - Spec sections all `reviewed` except §4 (revised under F13/F15
      to add T8 reflection symmetry and T9 continuum scaling).
    - Stubs in `src/infomax/` match spec §3 signatures.
    - Test refinements from red-team review of tests applied per
      `tests/test_000_static_infomax_fig1-redteam.md`:
        - F1: independent MI/f_KL re-derivation (`test_mi_fkl_self_consistency`)
        - F5: T5 tighter tolerance, nearest-neighbour matching, mass agreement
        - F6: T6 also pins history[0] (MI of uniform prior) and history[-1]
        - F8: T1 also asserts direct prior masses at boundary cells
        - F10: T2 off-support tolerance now relative
        - F11: subsumed by F1's consistency test

Randomness: BA is fully deterministic (uniform init, deterministic
likelihood matrix, deterministic fixed-point updates), so no
`np.random.Generator` is threaded through the API — see
manage-randomness skill rule 7. If a test ever needs randomness (e.g.,
a perturbation-stability check that turns out to be useful), it will
construct its own generator with a hardcoded literal seed per rule 3.
"""
from __future__ import annotations

import numpy as np
import pytest

from infomax.atoms import count_support, extract_atoms
from infomax.ba import blahut_arimoto
from infomax.jeffreys import jeffreys_bernoulli_cdf
from infomax.likelihood import binomial_log_likelihood, cell_centred_grid


# ---------------------------------------------------------------------------
# Constants (spec §3.1, §3.6, §4)
# ---------------------------------------------------------------------------

DEFAULT_N_THETA: int = 1000
"""Headline grid resolution per spec §3.1."""

M_SWEEP: tuple[int, ...] = (1, 2, 3, 4, 5, 10, 20, 50, 100)
"""Sample budgets covered by the m-sweep per spec §3.6."""

N_THETA_GRID_INVARIANCE: tuple[int, ...] = (200, 1000, 2000)
"""Grid resolutions compared in T5 per spec §4."""

T5_M_VALUES: tuple[int, ...] = (1, 2, 5, 10)
"""m values used in the T5 grid-invariance check per spec §4."""

T9_N_THETA_VALUES: tuple[int, ...] = (100, 1000, 10000)
"""Grid resolutions used in T9 continuum-scaling check per spec §4 (F15)."""

K_UPPER_FLOOR: float = 1e-12
"""Hard floor used by T3 to count support cells, per spec §4 (F4 revision)."""


# ---------------------------------------------------------------------------
# Test-local helpers
# ---------------------------------------------------------------------------


def _binary_entropy_nats(p: float | np.ndarray) -> float | np.ndarray:
    """H(p) = -p log p - (1-p) log(1-p), in nats; defined on p in (0, 1)."""
    return -p * np.log(p) - (1.0 - p) * np.log(1.0 - p)


def _mi_ref_m1(n_theta: int) -> float:
    """T1 reference value (spec §4): MI_ref(N_θ) = log 2 − H(1/(2 N_θ))."""
    theta_lo = 1.0 / (2 * n_theta)
    return float(np.log(2.0) - _binary_entropy_nats(theta_lo))


def _compute_marginal_x(masses: np.ndarray, log_likelihood: np.ndarray) -> np.ndarray:
    """p(x) = Σ_i masses[i] * exp(log_likelihood[i, x]). Shape (n_x,)."""
    return masses @ np.exp(log_likelihood)


def _compute_fkl_and_mi(
    masses: np.ndarray, log_likelihood: np.ndarray
) -> tuple[np.ndarray, float]:
    """Independent recomputation of (f_KL vector, MI scalar) from a prior.

    f_KL[i] = Σ_x p(x|θ_i) * (log p(x|θ_i) − log p(x))
    MI      = Σ_i masses[i] * f_KL[i]

    Used by F1's consistency test and by F6 (MI of uniform prior).
    """
    p_x = _compute_marginal_x(masses, log_likelihood)
    P = np.exp(log_likelihood)
    f_kl = np.einsum("ix,ix->i", P, log_likelihood - np.log(p_x))
    mi = float(masses @ f_kl)
    return f_kl, mi


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


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


def test_t1_m1_closed_form(theta_grid: np.ndarray, n_theta: int) -> None:
    """T1 — m=1 closed form (on the grid).

    Spec §1.5, §4. With m=1, BA must converge to two atoms at the first
    and last grid cells, mass 1/2 each, with MI matching the analytic
    two-atom MI evaluated on the grid:

        MI_ref(N_θ) = log 2 − H(1/(2 N_θ))

    Tolerances: centroids within 0.5/N_θ, masses within 1e-6 of 0.5, MI
    within 1e-6 nats of MI_ref. The continuum optimum (atoms at 0 and 1
    with MI = log 2) is the N_θ → ∞ limit; we test the on-grid analogue
    per DC-1.

    Per red-team F8: also asserts the prior masses *directly* (not just
    via the §3.5 atom-extraction heuristic).
    """
    log_lik = binomial_log_likelihood(theta_grid, m=1)
    result = blahut_arimoto(log_lik, theta_grid)

    atoms = sorted(extract_atoms(result.prior), key=lambda a: a.theta)
    assert len(atoms) == 2, f"expected K=2, got {len(atoms)}"

    theta_lo_expected = theta_grid[0]
    theta_hi_expected = theta_grid[-1]
    half_cell = 0.5 / n_theta
    assert abs(atoms[0].theta - theta_lo_expected) < half_cell
    assert abs(atoms[1].theta - theta_hi_expected) < half_cell

    assert abs(atoms[0].mass - 0.5) < 1e-6
    assert abs(atoms[1].mass - 0.5) < 1e-6

    assert abs(result.mi - _mi_ref_m1(n_theta)) < 1e-6

    # F8: direct prior-mass checks. The two boundary cells should each
    # carry ≈ 0.5; all interior cells should be at numerical noise.
    masses = result.prior.masses()
    assert abs(masses[0] - 0.5) < 1e-6, f"boundary cell 0 mass = {masses[0]}"
    assert abs(masses[-1] - 0.5) < 1e-6, f"boundary cell -1 mass = {masses[-1]}"
    max_interior = float(np.max(masses[1:-1]))
    assert max_interior < 1e-10, f"max interior mass = {max_interior:.3e} (expected < 1e-10)"


def test_t2_fkl_flatness_on_support(
    theta_grid: np.ndarray, log_likelihood: np.ndarray, m: int, n_theta: int
) -> None:
    """T2 — f_KL flatness on support.

    Spec §1.3, §4. KKT condition for the MI-maximising prior:

        on support (p_i > p_thresh):  f_KL(theta_i) = MI*  (rel. tol. 1e-3)
        off support:                   f_KL(theta_i) ≤ MI*  (scaled slack)

    Parametrised across the full m-sweep.

    Per red-team F10: off-support slack is now relative
    (`abs(MI*) * 1e-8 + 1e-12`) rather than a hardcoded 1e-10, so the
    asymmetry between on- and off-support tolerances goes away.
    """
    result = blahut_arimoto(log_likelihood, theta_grid)
    p_thresh = 1.0 / (10 * n_theta)
    masses = result.prior.masses()
    on_support = masses > p_thresh

    assert np.any(on_support), "no support cells detected — BA likely did not converge"
    rel_err = np.abs(result.f_kl[on_support] - result.mi) / max(abs(result.mi), 1e-300)
    assert np.all(rel_err < 1e-3), (
        f"f_KL flatness violated on support: max rel_err = {rel_err.max():.3e}"
    )

    fp_slack = abs(result.mi) * 1e-8 + 1e-12
    off_support_violations = result.f_kl[~on_support] - result.mi
    assert np.all(off_support_violations <= fp_slack), (
        f"f_KL > MI off support: max violation = {off_support_violations.max():.3e} "
        f"(slack {fp_slack:.3e})"
    )


def test_t3_capacity_bound(
    theta_grid: np.ndarray, log_likelihood: np.ndarray, m: int
) -> None:
    """T3 — Capacity bound (decoupled from §3.5).

    Spec §4 (F4 revision). `K_upper = #{i : p_i > 1e-12}` is a
    permissive grid-cell count off the converged prior — strictly an
    upper bound on the true atom count, so the bound `MI* ≤ log K_upper`
    holds whenever the math holds. Independent of the §3.5
    atom-extraction heuristic.
    """
    result = blahut_arimoto(log_likelihood, theta_grid)
    k_upper = count_support(result.prior, floor=K_UPPER_FLOOR)
    assert k_upper >= 1, "no support cells above the K_upper floor"
    assert result.mi <= np.log(k_upper) + 1e-10, (
        f"capacity bound violated: MI* = {result.mi:.6f}, "
        f"log K_upper = {np.log(k_upper):.6f}, K_upper = {k_upper}"
    )


def test_t4_converges_to_jeffreys(theta_grid: np.ndarray) -> None:
    """T4 — Convergence to Jeffreys (qualitative), m=100 only.

    Spec §1.5, §4. The CDF of the converged atom-mass distribution (step
    function with K jumps of height λ_a at the atom centroids) is
    compared against the Jeffreys CDF F_J(θ) = (2/π) arcsin(√θ). KS
    distance must be < 0.05 — generous; the discreteness floor is
    ~ 1/(2 K(m)) ~ 5e-3 at K ≈ 100. Convergence rate across the m-sweep
    lives in the report (§5), not as a hard assertion.
    """
    log_lik = binomial_log_likelihood(theta_grid, m=100)
    result = blahut_arimoto(log_lik, theta_grid)

    atoms = sorted(extract_atoms(result.prior), key=lambda a: a.theta)
    thetas = np.array([a.theta for a in atoms])
    masses = np.array([a.mass for a in atoms])

    cdf_atoms = np.cumsum(masses)
    cdf_jeffreys = jeffreys_bernoulli_cdf(thetas)
    ks_distance = float(np.max(np.abs(cdf_atoms - cdf_jeffreys)))

    assert ks_distance < 0.05, f"KS distance to Jeffreys CDF = {ks_distance:.4f}"


@pytest.mark.parametrize("m_val", T5_M_VALUES)
def test_t5_grid_invariance_of_atoms(m_val: int) -> None:
    """T5 — Grid invariance of atom locations.

    Spec §3.1, §4. For m ∈ {1, 2, 5, 10} and N_θ ∈ {200, 1000, 2000}:
    detected atom counts agree across grids, atom centroids agree to
    within `max(1/N_θ)` (F5 tightening from 3× to 1×), matching is
    nearest-neighbour (not zip-by-index), and atom masses also agree
    across grids to ~1e-3 absolute.
    """
    centroid_sets: dict[int, np.ndarray] = {}
    mass_sets: dict[int, np.ndarray] = {}
    for n in N_THETA_GRID_INVARIANCE:
        grid = cell_centred_grid(n)
        log_lik = binomial_log_likelihood(grid, m_val)
        result = blahut_arimoto(log_lik, grid)
        atoms = sorted(extract_atoms(result.prior), key=lambda a: a.theta)
        centroid_sets[n] = np.array([a.theta for a in atoms])
        mass_sets[n] = np.array([a.mass for a in atoms])

    counts = {n: len(c) for n, c in centroid_sets.items()}
    assert len(set(counts.values())) == 1, (
        f"detected atom counts differ across grids: {counts}"
    )

    # F5: tighter tolerance + nearest-neighbour matching + mass agreement.
    centroid_tol = max(1.0 / n for n in N_THETA_GRID_INVARIANCE)
    mass_tol = 1e-3
    reference_n = N_THETA_GRID_INVARIANCE[0]
    ref_centroids = centroid_sets[reference_n]
    ref_masses = mass_sets[reference_n]
    for n in N_THETA_GRID_INVARIANCE[1:]:
        other_centroids = centroid_sets[n]
        other_masses = mass_sets[n]
        for ref_theta, ref_mass in zip(ref_centroids, ref_masses):
            distances = np.abs(other_centroids - ref_theta)
            nn_idx = int(np.argmin(distances))
            nn_dist = float(distances[nn_idx])
            mass_diff = abs(other_masses[nn_idx] - ref_mass)
            assert nn_dist < centroid_tol, (
                f"atom centroid mismatch at m={m_val}, N_θ={reference_n}→{n}: "
                f"ref θ={ref_theta:.6f}, nearest in grid {n} at distance "
                f"{nn_dist:.6f} (tol {centroid_tol:.6f})"
            )
            assert mass_diff < mass_tol, (
                f"atom mass mismatch at m={m_val}, N_θ={reference_n}→{n}, "
                f"θ ≈ {ref_theta:.4f}: |Δmass| = {mass_diff:.3e} (tol {mass_tol:.3e})"
            )


def test_t6_ba_monotonicity(
    theta_grid: np.ndarray, log_likelihood: np.ndarray, m: int, n_theta: int
) -> None:
    """T6 — BA monotonicity.

    Spec §1.4, §4. I_τ is non-decreasing across BA iterations, up to
    a floating-point slack of 1e-10 per step. Direct check of the
    Blahut/Arimoto convergence guarantee.

    Per red-team F6: also pins both endpoints of the history. `history[0]`
    must equal the MI under the uniform prior (independently recomputed
    from the likelihood matrix); `history[-1]` must equal `result.mi`.
    Together these prevent fabricated monotone-but-arbitrary histories.
    """
    result = blahut_arimoto(log_likelihood, theta_grid)
    history = np.asarray(result.mi_history, dtype=float)
    assert history.size >= 2, "mi_history too short to test monotonicity"
    diffs = np.diff(history)
    min_step = float(diffs.min())
    assert min_step >= -1e-10, (
        f"BA not monotone: minimum step Δ = {min_step:.3e} (slack 1e-10)"
    )

    # F6: history endpoints
    uniform_masses = np.full(n_theta, 1.0 / n_theta)
    _, mi_uniform = _compute_fkl_and_mi(uniform_masses, log_likelihood)
    assert abs(history[0] - mi_uniform) < 1e-12, (
        f"history[0] = {history[0]:.6e} ≠ MI under uniform = {mi_uniform:.6e}"
    )
    assert abs(history[-1] - result.mi) < 1e-12, (
        f"history[-1] = {history[-1]:.6e} ≠ result.mi = {result.mi:.6e}"
    )


def test_t7_degenerate_likelihood(theta_grid: np.ndarray, n_theta: int) -> None:
    """T7 — Algorithmic sanity on a degenerate case.

    Spec §4. With a θ-independent likelihood (uniform p(x|θ) for all θ),
    the channel learns nothing: MI* = 0, f_KL ≡ 0, and the converged
    prior equals the uniform initialisation. Cheap structural check on
    the BA loop and on the f_KL computation.
    """
    n_x = 5
    log_lik = np.full((n_theta, n_x), -np.log(n_x))
    result = blahut_arimoto(log_lik, theta_grid)

    assert abs(result.mi) < 1e-12, f"MI ≠ 0 for degenerate likelihood: {result.mi}"
    max_abs_fkl = float(np.max(np.abs(result.f_kl)))
    assert max_abs_fkl < 1e-12, f"f_KL not identically 0: max|f_KL| = {max_abs_fkl:.3e}"
    masses = result.prior.masses()
    assert np.allclose(masses, 1.0 / n_theta, atol=1e-12), (
        "prior drifted from uniform under a θ-independent likelihood"
    )


def test_t8_reflection_symmetry(
    theta_grid: np.ndarray, log_likelihood: np.ndarray, m: int
) -> None:
    """T8 — Reflection symmetry (added per red-team F13).

    Spec §4. The Bernoulli likelihood satisfies p(x | θ) = p(m−x | 1−θ),
    making the MI objective invariant under θ ↔ 1−θ. The optimal prior
    inherits the symmetry: p*(θ_i) = p*(θ_{N_θ−1−i}). A wrong
    implementation that breaks symmetry (asymmetric update bug,
    accumulated numerical drift) passes T1's per-side checks but fails
    here.
    """
    result = blahut_arimoto(log_likelihood, theta_grid)
    masses = result.prior.masses()
    assert np.allclose(masses, masses[::-1], atol=1e-8), (
        f"prior not θ↔1−θ symmetric: max|p_i − p_{{N-1-i}}| = "
        f"{float(np.max(np.abs(masses - masses[::-1]))):.3e}"
    )


@pytest.mark.parametrize("n_theta_val", T9_N_THETA_VALUES)
def test_t9_t1_continuum_scaling(n_theta_val: int) -> None:
    """T9 — Continuum scaling of the T1 deficit (added per red-team F15).

    Spec §4. As N_θ grows, MI_ref(N_θ) → log 2; the deficit
    `log 2 − MI_ref(N_θ)` scales like `(log N_θ) / N_θ` (leading order
    of H(1/(2 N_θ)) for small p). Asserts the ratio
    `deficit · N_θ / log(N_θ)` stays in [0.1, 10] across the sweep.
    Catches an implementation that hard-codes MI_ref or silently
    drops the cell-centred convention.
    """
    grid = cell_centred_grid(n_theta_val)
    log_lik = binomial_log_likelihood(grid, m=1)
    result = blahut_arimoto(log_lik, grid)
    deficit = np.log(2.0) - result.mi
    expected_scale = np.log(n_theta_val) / n_theta_val
    ratio = deficit / expected_scale
    assert 0.1 < ratio < 10.0, (
        f"T1 deficit scaling off at N_θ={n_theta_val}: "
        f"deficit={deficit:.3e}, expected ~ (log N_θ)/N_θ = {expected_scale:.3e}, "
        f"ratio = {ratio:.3f}"
    )


# ---------------------------------------------------------------------------
# Cross-cutting self-consistency (red-team F1, F11)
# ---------------------------------------------------------------------------


def test_mi_fkl_self_consistency(
    theta_grid: np.ndarray, log_likelihood: np.ndarray, m: int
) -> None:
    """F1 — `result.mi` and `result.f_kl` must match independent recomputation.

    Spec §1.2, §1.3 define MI and f_KL in terms of the prior and the
    likelihood. A correct BA must return values that match what those
    formulas yield when applied to the *returned* prior. Catches:

      - Stale `mi` or `f_kl` reported from an earlier iterate (also F11).
      - Hard-coded or fabricated values.
      - Off-by-one bugs where one of the three is computed against a
        different prior than the other two.

    Tolerance is ~1e-12 since recomputation uses the same precision and
    the same arithmetic structure as the loop.
    """
    result = blahut_arimoto(log_likelihood, theta_grid)
    masses = result.prior.masses()
    f_kl_indep, mi_indep = _compute_fkl_and_mi(masses, log_likelihood)
    assert abs(result.mi - mi_indep) < 1e-12, (
        f"result.mi = {result.mi:.12f}, independent MI = {mi_indep:.12f}"
    )
    assert np.allclose(result.f_kl, f_kl_indep, atol=1e-12), (
        f"result.f_kl differs from independent recomputation: "
        f"max|Δ| = {float(np.max(np.abs(result.f_kl - f_kl_indep))):.3e}"
    )
