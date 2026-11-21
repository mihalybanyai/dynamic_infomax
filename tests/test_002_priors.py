"""Spec 002 tests: building the priors (P3, P4, P7b, P11, P15, P16, P19, P23).

specs/002-foreign-q-prediction.md §4.2 and §5.2 (T3, T4, T7b, T11, T15, T16, T19, T23).
These check the constructions, never which prior wins (§2.4). Stubs raise
`NotImplementedError` until the implementation exists.
"""
from __future__ import annotations

import numpy as np
import pytest
import scipy.stats

from infomax.jeffreys import build_jeffreys
from infomax.plat import build_plat, conditional_divergence
from infomax.plognormal import build_pln, build_pln_star
from infomax.pproj import build_pproj, mle_project, nml_log_normaliser
from infomax.pref import build_pref, build_uniform
from infomax.pstar import build_pstar
from infomax.score import mutual_information, per_state_redundancy, score_cell
from spec002_common import (
    EQUALIZER_SLACK,
    INFO_SLACK,
    S_Q_TEST,
    agree_mc,
    cheap_model,
    cone_model,
)


# ---------------------------------------------------------------------------
# P3 / T3 — p*'s equalizer
# ---------------------------------------------------------------------------


def test_t3_pstar_equalizer():
    """T3: `b(theta) = R_N^theta(p*) - C_N` is about zero on `supp p*` and at most zero off
    it, at candidates and at random states off the candidate set; `I_{p*} = C_N`.

    A unit test of the solver (§3.1, §4.2), not of any result.
    """
    rng = np.random.default_rng(20261130)
    model = cheap_model()
    res = build_pstar(model)
    b_atoms = per_state_redundancy(res.prior, model, res.prior.atoms, rng=rng) - res.capacity
    assert np.max(np.abs(b_atoms)) <= EQUALIZER_SLACK
    b_candidates = per_state_redundancy(res.prior, model, res.candidates, rng=rng) - res.capacity
    assert np.max(b_candidates) <= EQUALIZER_SLACK
    off_set = model.box.sample_uniform(256, rng)
    b_off = per_state_redundancy(res.prior, model, off_set, rng=rng) - res.capacity
    assert np.max(b_off) <= EQUALIZER_SLACK, "the candidate set's capacity gap is too large"
    np.testing.assert_allclose(mutual_information(res.prior, model, rng=rng), res.capacity, rtol=1e-3)


# ---------------------------------------------------------------------------
# P4 / T4 — Jeffreys
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("family", ["exp_decay", "hypercone"])
def test_t4_jeffreys_normalises(family):
    """T4: `p_J ∝ sqrt(det g)` integrates to one on `Theta` (checked against `p_U` by Monte
    Carlo: `E_U[p_J / p_U] = 1`), and its density follows `sqrt(det g)` (§4.2)."""
    rng = np.random.default_rng(20261131)
    model = cheap_model(D=2) if family == "exp_decay" else cone_model(4)
    p_J, p_U = build_jeffreys(model), build_uniform(model)
    theta = model.box.sample_uniform(200_000, rng)
    ratio = np.exp(p_J.log_density(theta) - p_U.log_density(theta))
    assert abs(ratio.mean() - 1.0) <= 4 * ratio.std() / np.sqrt(ratio.size)
    log_vol = 0.5 * np.log(np.linalg.det(model.fim(theta[:20])))
    diff = p_J.log_density(theta[:20]) - log_vol
    np.testing.assert_allclose(diff, diff[0], rtol=0, atol=1e-8)


def test_t4_jeffreys_normaliser_converges_on_whole_manifold():
    """T4: in exp-decay the normaliser over the whole manifold converges as the quadrature
    is refined (F8: normalisability there is a [guess] this checks)."""
    model = cheap_model(D=2)
    coarse = build_jeffreys(model, quadrature_points=200).log_normaliser
    fine = build_jeffreys(model, quadrature_points=400).log_normaliser
    assert np.isfinite(fine)
    assert abs(fine - coarse) <= 1e-3


def test_t4_jeffreys_cone_marginal():
    """T4: in the cone Jeffreys' `theta_1`-marginal is `∝ theta_1^(D-1)` on `[0, W]`, i.e.
    its CDF is `(theta_1 / W)^D` (§1.2, §9.2). Catches a wrong determinant or swapped axes."""
    rng = np.random.default_rng(20261132)
    D = 6
    model = cone_model(D)
    theta1 = build_jeffreys(model).sample(5000, rng)[:, 0]
    p = scipy.stats.kstest(theta1, lambda t: (np.clip(t, 0, model.W) / model.W) ** D).pvalue
    assert p > 1e-3


# ---------------------------------------------------------------------------
# P7b / T7b — p*'s two paths agree
# ---------------------------------------------------------------------------


@pytest.mark.slow
def test_t7b_pstar_method_agreement():
    """T7(b): where both the candidate-set and the atomic path run, their `R_N^q` agree
    within Monte-Carlo and solver tolerance (§4.2, OQ-1). Needs AtomicPriors.jl."""
    model = cheap_model()
    sets = build_pstar(model, method="candidates")
    atomic = build_pstar(model, method="atomic")
    np.testing.assert_allclose(sets.capacity, atomic.capacity, rtol=1e-3)
    rng = np.random.default_rng(20261133)
    p_U = build_uniform(model)
    cell = score_cell(model, {"sets": sets.prior, "atomic": atomic.prior}, ("own", p_U), S_q=S_Q_TEST, rng=rng)
    assert agree_mc(cell.R_mean["sets"], cell.R_mean["atomic"], cell.R_mcse["sets"], cell.R_mcse["atomic"])


# ---------------------------------------------------------------------------
# P11 / T11 — p_proj
# ---------------------------------------------------------------------------


def test_t11_pproj_normaliser_is_finite():
    """T11: `p_NML ∝ max_theta p(x|theta)` has a finite normaliser on the compact manifold (§4.2)."""
    rng = np.random.default_rng(20261134)
    assert np.isfinite(nml_log_normaliser(cheap_model(), rng))


def test_t11_pproj_projection_recovers_mle():
    """T11: the projection recovers a known `theta-hat` from `x` placed near the manifold.

    Data a hundredth of a noise unit from `y(theta)` have their maximum-likelihood state
    within a small fraction of the noise of `theta`'s prediction."""
    rng = np.random.default_rng(20261135)
    model = cheap_model()
    theta = np.sort(rng.uniform(0.2, 0.8, size=(10, 2)), axis=-1)
    x = model.y(theta) + 0.01 * model.sigma_eff * rng.standard_normal((10, model.m_out))
    theta_hat = mle_project(model, x)
    dist = np.linalg.norm(model.y(theta_hat) - model.y(theta), axis=-1) / model.sigma_eff
    assert np.max(dist) <= 0.05


def test_t11_pproj_information_below_capacity():
    """T11: `I_{p_proj} <= I_{p*} = C_N`, since `p*` maximises the information (§4.2, m11)."""
    rng = np.random.default_rng(20261136)
    model = cheap_model()
    cap = build_pstar(model).capacity
    i_proj = mutual_information(build_pproj(model, 2000, rng), model, rng=rng)
    assert i_proj <= cap + INFO_SLACK


# ---------------------------------------------------------------------------
# P15 / T15 — p_ref
# ---------------------------------------------------------------------------


def test_t15a_cone_schur_complement():
    """T15(a): in the hypercone the information left for `theta_1` once the cross-section is
    accounted for is `sigma_eff^-2` everywhere ([^3-schur])."""
    rng = np.random.default_rng(20261137)
    model = cone_model(5)
    for theta in model.box.sample_uniform(20, rng):
        if theta[0] < 1.0:
            continue
        g = model.fim(theta)
        schur = g[0, 0] - g[0, 1:] @ np.linalg.solve(g[1:, 1:], g[1:, 0])
        np.testing.assert_allclose(schur, model.sigma_eff**-2, rtol=1e-8)


@pytest.mark.parametrize("taper", [1.0, 0.0])
def test_t15b_c_cone_pref_is_uniform(taper):
    """T15(b), (c): in the cone `p_ref = p_U` pointwise; with the taper off also `= p_J` (§3.5)."""
    rng = np.random.default_rng(20261138)
    model = cone_model(4, taper=taper)
    theta = model.box.sample_uniform(100, rng)
    p_ref, p_U = build_pref(model), build_uniform(model)
    np.testing.assert_allclose(p_ref.log_density(theta), p_U.log_density(theta), rtol=1e-8)
    if taper == 0.0:
        np.testing.assert_allclose(build_jeffreys(model).log_density(theta), p_U.log_density(theta), rtol=1e-6)


def test_t15d_exp_decay_rankings_normalise_and_differ():
    """T15(d): in exp-decay each ranking's `p_ref` normalises, and the slowest-first,
    fastest-first and (at `D = 2`) stiffest-first priors differ pairwise (§3.5, OQ-8)."""
    rng = np.random.default_rng(20261139)
    model = cheap_model(D=2)
    theta = model.box.sample_uniform(100_000, rng)
    log_u = build_uniform(model).log_density(theta)
    dens = {}
    for ranking in ("slowest", "fastest", "stiffest"):
        log_p = build_pref(model, ranking).log_density(theta)
        ratio = np.exp(log_p - log_u)
        assert abs(ratio.mean() - 1.0) <= 4 * ratio.std() / np.sqrt(ratio.size)
        dens[ranking] = log_p
    for a, b in (("slowest", "fastest"), ("slowest", "stiffest"), ("fastest", "stiffest")):
        assert np.max(np.abs(dens[a] - dens[b])) > 1e-2, f"{a} and {b} give the same prior"


def test_t15e_stiffest_ranking_ignores_transversal():
    """T15(e): at `D = 2` the stiffest-first `p_ref` does not depend on the transversal from
    which its coordinate is traced (`[^4-stiff]`: a reference prior ignores how its
    interest parameter is labelled)."""
    rng = np.random.default_rng(20261140)
    model = cheap_model(D=2)
    theta = model.box.sample_uniform(200, rng)
    a = build_pref(model, "stiffest", transversal=np.array([[0.1, 0.9], [0.9, 0.95]]))
    b = build_pref(model, "stiffest", transversal=np.array([[0.05, 0.5], [0.5, 0.99]]))
    np.testing.assert_allclose(a.log_density(theta), b.log_density(theta), rtol=1e-3)


# ---------------------------------------------------------------------------
# P16 / T16 — p_lat
# ---------------------------------------------------------------------------


def test_t16a_b_plat_conditional_equalizer_and_bounds():
    """T16(a), (b): at convergence `f^(N+1) - f^(N)` is within tolerance of the conditional
    capacity on `supp p_lat` and below it elsewhere; the two-sided bound of §4.2 closes."""
    model = cheap_model()
    res = build_plat(model)
    on_support = conditional_divergence(res, model, res.prior.atoms[res.prior.weights > 1e-8])
    assert np.max(np.abs(on_support - res.conditional_capacity)) <= EQUALIZER_SLACK
    rng = np.random.default_rng(20261141)
    off = conditional_divergence(res, model, model.box.sample_uniform(256, rng))
    assert np.max(off) <= res.conditional_capacity + EQUALIZER_SLACK
    assert res.upper_bound - res.lower_bound <= 1e-6 + 1e-12
    assert res.lower_bound <= res.conditional_capacity <= res.upper_bound


def test_t16c_plat_at_zero_budget_is_pstar():
    """T16(c): at `N = 0`, `p_lat` maximises `I(Theta; X_1)`, so it equals `p*` at budget 1
    on the same candidate set. Catches swapped noise levels or a wrong difference."""
    model1 = cheap_model(N=1)
    pstar = build_pstar(model1)
    plat0 = build_plat(cheap_model(N=0), candidates=pstar.candidates)
    np.testing.assert_allclose(plat0.prior.weights, pstar.masses, atol=1e-4)


# ---------------------------------------------------------------------------
# P19 / T19 — mis-budgeted p*
# ---------------------------------------------------------------------------


def test_t19a_b_misbudgeted_is_pstar_of_its_budget():
    """T19(a), (b): `p*_M` built at `sigma / sqrt(M)` equals `p*` built for budget `M` (same
    path and candidate set), and scored at budget `M` its `R` matches `p*`'s (§2.2)."""
    M = 4
    model_N, model_M = cheap_model(N=1), cheap_model(N=M)
    own = build_pstar(model_M)
    mis = build_pstar(model_N, budget=M, candidates=own.candidates)
    np.testing.assert_allclose(mis.masses, own.masses, atol=1e-8)
    rng = np.random.default_rng(20261142)
    p_U = build_uniform(model_M)
    cell = score_cell(model_M, {"mis": mis.prior, "own": own.prior}, ("own", p_U), S_q=S_Q_TEST, rng=rng)
    np.testing.assert_allclose(cell.R_mean["mis"], cell.R_mean["own"], atol=1e-10)


def test_t19c_misbudget_worst_case_exceeds_capacity():
    """T19(c): in the 1-D bounded channel of Fisher length 3 at `N = 1` (the note's §3.1),
    the worst-case per-state redundancy of `p*_M` at budget `N` is at least `C_N`, with
    equality only at `M = N`. Only `N = 1` lies in the two-atom regime (m12)."""
    W = 50.0
    sigma = W / 3.0
    grid = np.linspace(0.0, W, 401)[:, None]
    budgets = (1, 4, 16, 64)
    for N in budgets:
        model = cone_model(1, sigma=sigma, N=N)
        C_N = build_pstar(model).capacity
        for M in budgets:
            prior = build_pstar(model, budget=M).prior
            worst = np.max(per_state_redundancy(prior, model, grid))
            if M == N:
                np.testing.assert_allclose(worst, C_N, atol=EQUALIZER_SLACK)
            else:
                assert worst > C_N + EQUALIZER_SLACK, f"N={N}, M={M}"


# ---------------------------------------------------------------------------
# P23 / T23 — p_LN^*
# ---------------------------------------------------------------------------


def test_t23_tuned_lognormal_information_order():
    """T23(a): `I_{p_LN} <= I_{p_LN^*} <= C_N` (§4.2): the search starts from A&M's (0, 1)
    and `p*` maximises the information. Catches a search that did not run."""
    model = cheap_model()
    tuned = build_pln_star(model, np.random.default_rng(20261143))
    i_ln = mutual_information(build_pln(model), model, rng=np.random.default_rng(20261144))
    i_star = mutual_information(tuned.prior, model, rng=np.random.default_rng(20261144))
    cap = build_pstar(model).capacity
    assert i_ln <= i_star + INFO_SLACK
    assert i_star <= cap + INFO_SLACK


def test_t23_tuned_lognormal_is_a_local_maximum():
    """T23(b): at the returned `(theta_bar, tau)`, `I` does not increase along a small step in
    either parameter (common random numbers). Catches `I` estimated at the wrong noise."""
    model = cheap_model()
    tuned = build_pln_star(model, np.random.default_rng(20261145))

    def info(theta_bar, tau):
        return mutual_information(build_pln(model, theta_bar, tau), model, rng=np.random.default_rng(20261146))

    best = info(tuned.theta_bar, tuned.tau)
    for d_bar, d_tau in ((0.1, 0), (-0.1, 0), (0, 0.1), (0, -0.1)):
        assert info(tuned.theta_bar + d_bar, tuned.tau + d_tau) <= best + INFO_SLACK
