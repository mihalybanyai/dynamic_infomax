"""Spec 002 tests: the scores, floors and controls (P1, P7a, P7c, P8, P17, P20).

specs/002-foreign-q-prediction.md §2.1, §2.5, §4.4 and §5.2 (T1, T7a, T7c, T8, T17, T20).
They pin what the scores mean, never their signs (§2.4). Stubs raise
`NotImplementedError` until the implementation exists.
"""
from __future__ import annotations

import numpy as np

from infomax.jeffreys import build_jeffreys
from infomax.priors002 import DiscretePrior
from infomax.pref import build_uniform
from infomax.pstar import build_pstar
from infomax.qfamily import build_qbar
from infomax.score import log_marginal, marginal_mismatch, matched_floor, score_cell
from spec002_common import MC_SIGMAS, S_Q_TEST, agree_mc, build_cast, cheap_model, cone_model


def test_t1_redundancy_decomposition():
    """T1: `R_N^q(pi)` estimated directly by (2.1.1) equals `I_q + D_KL(m_q || m_pi)`, each
    estimated separately (2.1.2). The tightest check that the score means what §2.1 says."""
    model = cheap_model()
    p_U, p_J = build_uniform(model), build_jeffreys(model)
    nature = ("own", p_U)
    cell = score_cell(model, {"p_J": p_J}, nature, S_q=S_Q_TEST, rng=np.random.default_rng(20261160))
    floor, floor_se = matched_floor(model, nature, S_q=S_Q_TEST, rng=np.random.default_rng(20261161))
    mis, mis_se = marginal_mismatch(model, nature, p_J, S_q=S_Q_TEST, rng=np.random.default_rng(20261162))
    assert agree_mc(cell.R_mean["p_J"], floor + mis, cell.R_mcse["p_J"], floor_se, mis_se)


def test_t7a_discrete_marginal_is_the_atom_sum():
    """T7(a): for a discrete prior, `log m_pi(xbar)` is the exact atom sum
    `logsumexp_a [log w_a + log N(xbar; y(theta_a), sigma_eff^2)]` (§4.4)."""
    rng = np.random.default_rng(20261163)
    model = cheap_model()
    atoms = np.sort(rng.uniform(0, 1, size=(7, 2)), axis=-1)
    weights = rng.dirichlet(np.ones(7))
    prior = DiscretePrior("toy", atoms, weights)
    xbar = model.y(atoms[:3]) + model.sigma_eff * rng.standard_normal((3, model.m_out))
    d2 = ((xbar[:, None, :] - model.y(atoms)[None, :, :]) ** 2).sum(-1)
    log_n = -d2 / (2 * model.sigma_eff**2) - 0.5 * model.m_out * np.log(2 * np.pi * model.sigma_eff**2)
    expected = np.logaddexp.reduce(np.log(weights)[None, :] + log_n, axis=1)
    np.testing.assert_allclose(log_marginal(prior, model, xbar, method="atoms"), expected, rtol=1e-12)


def test_t7a_continuous_quadrature_matches_a_fine_atom_sum():
    """T7(a): a coarse continuous prior's quadrature agrees with the atom sum of the same
    prior placed on a fine grid of `Theta` (a shared support)."""
    rng = np.random.default_rng(20261164)
    model = cheap_model()
    p_U = build_uniform(model)
    g = (np.arange(400) + 0.5) / 400
    a, b = np.meshgrid(g, g, indexing="ij")
    grid = np.column_stack([a.ravel(), b.ravel()])
    grid = grid[grid[:, 0] <= grid[:, 1]]
    weights = np.exp(p_U.log_density(grid))
    fine = DiscretePrior("p_U on a grid", grid, weights / weights.sum())
    xbar = model.y(model.box.sample_uniform(10, rng)) + model.sigma_eff * rng.standard_normal((10, model.m_out))
    np.testing.assert_allclose(
        log_marginal(p_U, model, xbar, method="quadrature"), log_marginal(fine, model, xbar, method="atoms"), atol=1e-3
    )


def test_t7c_budget_through_the_noise():
    """T7(c): at small `(D, N)`, `p*` and `R_N^q` built at `sigma_eff` agree with those from
    the literal channel `theta -> X_{1:N}` (§4). With T12(c), this pins the construction
    that the guarantee of §3.1 rests on."""
    model = cone_model(1, sigma=10.0, N=2)
    reduced = build_pstar(model)
    literal = build_pstar(model, literal_nfold=True, candidates=reduced.candidates)
    np.testing.assert_allclose(literal.capacity, reduced.capacity, rtol=1e-3)
    np.testing.assert_allclose(literal.masses, reduced.masses, atol=1e-3)
    p_U = build_uniform(model)
    a = score_cell(model, {"p*": reduced.prior}, ("own", p_U), S_q=S_Q_TEST, rng=np.random.default_rng(20261165))
    b = score_cell(model, {"p*": reduced.prior}, ("own", p_U), S_q=S_Q_TEST, rng=np.random.default_rng(20261165), literal_nfold=True)
    assert agree_mc(a.R_mean["p*"], b.R_mean["p*"], a.R_mcse["p*"], b.R_mcse["p*"])


def test_t8_floors_and_matched_prior():
    """T8(a): per nature, `R_N^q(pi) >= I_q >= 0` for every prior, and likewise for `r_N`
    with the conditional floor; the matched prior's mismatch is zero (§2.1, §2.5)."""
    model = cheap_model()
    cast = build_cast(model, np.random.default_rng(20261166))
    cell = score_cell(model, cast, ("own", cast["p_U"]), S_q=S_Q_TEST, rng=np.random.default_rng(20261167))
    assert cell.floor_R >= 0 and cell.floor_r >= 0
    for name in cast:
        assert cell.R_mean[name] >= cell.floor_R - MC_SIGMAS * cell.R_mcse[name]
        assert cell.r_mean[name] >= cell.floor_r - MC_SIGMAS * cell.r_mcse[name]
    np.testing.assert_allclose(cell.mismatch_R["p_U"], 0.0, atol=1e-12)


def test_t8_qbar_wins_the_row_average_and_splits_the_mean():
    """T8(b), (c): among fixed priors the row-averaged score is smallest for `q̄`; and each
    prior's mean mismatch equals `q̄`'s mean mismatch plus `D_KL(m_q̄ || m_pi)` (`[^2-qbar]`).
    `q̄` need not win per row; this is not asserted."""
    model = cheap_model()
    cast = build_cast(model, np.random.default_rng(20261168))
    rows = [("own", prior) for prior in cast.values()]
    qbar = build_qbar(rows)
    priors = {**cast, "q̄": qbar}
    cells = [score_cell(model, priors, row, S_q=S_Q_TEST, rng=np.random.default_rng(20261169)) for row in rows]
    mean_R = {n: np.mean([c.R_mean[n] for c in cells]) for n in priors}
    se_R = {n: np.sqrt(np.sum([c.R_mcse[n] ** 2 for c in cells])) / len(cells) for n in priors}
    for n in cast:
        assert mean_R["q̄"] <= mean_R[n] + MC_SIGMAS * np.hypot(se_R["q̄"], se_R[n])
    mean_mis = {n: np.mean([c.mismatch_R[n] for c in cells]) for n in priors}
    for n in cast:
        to_qbar, to_qbar_se = marginal_mismatch(model, ("own", qbar), cast[n], S_q=S_Q_TEST, rng=np.random.default_rng(20261170))
        assert agree_mc(mean_mis[n], mean_mis["q̄"] + to_qbar, se_R[n], se_R["q̄"], to_qbar_se)


def test_t17_one_step_score():
    """T17: (a) under common random numbers `r_N^q(pi)` from (2.1.5) matches
    `R_{N+1}^q(pi) - R_N^q(pi)`; (b) `r_N^q(pi)` equals the conditional floor plus the
    expected posterior-predictive mismatch of (2.1.6). Catches `x'` drawn at `sigma_eff`
    instead of `sigma`, or a prior predictive in place of the posterior predictive."""
    N = 2
    model_N, model_N1 = cheap_model(N=N), cheap_model(N=N + 1)
    p_J = build_jeffreys(model_N)
    nature = ("own", build_uniform(model_N))
    a = score_cell(model_N, {"p_J": p_J}, nature, S_q=S_Q_TEST, rng=np.random.default_rng(20261171))
    b = score_cell(model_N1, {"p_J": p_J}, nature, S_q=S_Q_TEST, rng=np.random.default_rng(20261171))
    assert agree_mc(a.r_mean["p_J"], b.R_mean["p_J"] - a.R_mean["p_J"], a.r_mcse["p_J"], a.R_mcse["p_J"], b.R_mcse["p_J"])
    floor, floor_se = matched_floor(model_N, nature, S_q=S_Q_TEST, rng=np.random.default_rng(20261172), score="r")
    mis, mis_se = marginal_mismatch(model_N, nature, p_J, S_q=S_Q_TEST, rng=np.random.default_rng(20261173), score="r")
    assert agree_mc(a.r_mean["p_J"], floor + mis, a.r_mcse["p_J"], floor_se, mis_se)


def test_t20_round_robin_mismatches_are_non_negative():
    """T20: in each prior's own world, no other prior's mismatch is negative beyond
    Monte-Carlo error, on either score. Each estimates a KL divergence, so a negative value
    is a bug: a sampler that does not draw from the prior whose mixture is evaluated, or a
    mixture that does not normalise (§2.5)."""
    model = cheap_model()
    cast = build_cast(model, np.random.default_rng(20261174))
    for own, prior in cast.items():
        cell = score_cell(model, cast, ("own", prior), S_q=S_Q_TEST, rng=np.random.default_rng(20261175))
        for name in cast:
            assert cell.mismatch_R[name] >= -MC_SIGMAS * cell.R_mcse[name], (own, name, "R")
            assert cell.mismatch_r[name] >= -MC_SIGMAS * cell.r_mcse[name], (own, name, "r")
