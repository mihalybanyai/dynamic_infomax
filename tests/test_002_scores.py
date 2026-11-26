"""Spec 002 tests: the scores, floors and controls (P1, P7a, P7c, P8, P17, P20).

specs/002-foreign-q-prediction.md §2.1, §2.5, §4.4 and §5.2 (T1, T7a, T7c, T8, T17, T20).
They pin what the scores mean, never their signs (§2.4). Stubs raise
`NotImplementedError` until the implementation exists. Regenerated after the test
red-team (`tests/test_002_foreign_q_prediction-redteam.md`: F5, F6, F8, F9, m2, m7).
"""
from __future__ import annotations

import numpy as np
import pytest
import scipy.integrate
import scipy.stats

from infomax.diagnostics import row_summaries
from infomax.jeffreys import build_jeffreys
from infomax.plognormal import build_pln
from infomax.priors002 import DiscretePrior
from infomax.pref import build_uniform
from infomax.pstar import build_pstar
from infomax.qfamily import build_qbar, cell_rows
from infomax.score import (
    log_marginal,
    marginal_mismatch,
    matched_floor,
    per_state_redundancy,
    score_cell,
)
from spec002_common import (
    CHEAP_TWIN,
    MC_SIGMAS,
    PRODUCT_LAWS,
    S_Q_TEST,
    agree_mc,
    build_cast,
    cheap_model,
    cheap_model_at,
    cone_model,
    log_mean_exp_with_error,
    paired_mcse,
    per_rate_law,
)

W_CONE = 50.0


def _log_normal_iso(x: np.ndarray, mean: np.ndarray, var: float) -> np.ndarray:
    """`log N(x; mean, var 1)`, isotropic, over the last axis."""
    return -0.5 * ((x - mean) ** 2).sum(-1) / var - 0.5 * x.shape[-1] * np.log(2 * np.pi * var)


# ---------------------------------------------------------------------------
# P1 / T1 — the cumulative score: consistency, a known answer, its errors
# ---------------------------------------------------------------------------


def test_t1_redundancy_decomposition():
    """T1: `R_N^q(pi)` estimated directly by (2.1.1) equals `I_q + D_KL(m_q || m_pi)`, each
    estimated separately (2.1.2). A consistency check of the three estimators: (2.1.2) holds
    for any functions standing in for the marginals, so it cannot show that they are right
    (F6). T1(b) anchors the score's level."""
    model = cheap_model()
    p_U, p_J = build_uniform(model), build_jeffreys(model)
    nature = ("own", p_U)
    cell = score_cell(model, {"p_J": p_J}, nature, S_q=S_Q_TEST, rng=np.random.default_rng(20261160))
    floor, floor_se = matched_floor(model, nature, S_q=S_Q_TEST, rng=np.random.default_rng(20261161))
    mis, mis_se = marginal_mismatch(model, nature, p_J, S_q=S_Q_TEST, rng=np.random.default_rng(20261162))
    assert agree_mc(cell.R_mean["p_J"], floor + mis, cell.R_mcse["p_J"], floor_se, mis_se)


def _one_d_cone_scores(s: float, W: float) -> dict:
    """`R_N^q(pi)` in the 1-D cone of noise `s` for `q = p_U`, by quadrature, for `pi = p_U`
    and for two atoms at 0 and `W`. `m_q` is written with survival functions on the right
    half so that it stays positive in double precision out to ten noise units."""
    norm = scipy.stats.norm

    def m_q(x):
        left = norm.cdf(x / s) - norm.cdf((x - W) / s)
        right = norm.sf((x - W) / s) - norm.sf(x / s)
        return (left if x < W / 2 else right) / W

    m_two = lambda x: 0.5 * (norm.pdf(x, 0.0, s) + norm.pdf(x, W, s))
    lo, hi = -10 * s, W + 10 * s
    oracle = -0.5 * np.log(2 * np.pi * np.e * s**2)
    cross = lambda log_m: scipy.integrate.quad(lambda x: m_q(x) * log_m(x), lo, hi, points=[0, W / 2, W], limit=400)[0]
    return {"p_U": oracle - cross(lambda x: np.log(m_q(x))), "two": oracle - cross(lambda x: np.log(m_two(x)))}


def test_t1b_score_matches_quadrature_in_the_1d_cone():
    """T1(b) (F6): a known answer. In the 1-D cone at `sigma = W/3`, with nature `q = p_U`,
    `R_N^q(pi) = -1/2 log(2 pi e sigma^2) - ∫ m_q log m_pi`, where
    `m_q(x) = [Phi(x/sigma) - Phi((x - W)/sigma)] / W`. The test computes it by deterministic
    quadrature for `pi = p_U` and for two atoms at 0 and `W`, and `score_cell` matches both
    within its error (which T1(c) checks). A mixture at the wrong noise, a quadrature that
    drops the prior density, or an oracle term with the wrong normaliser fails."""
    model = cone_model(1, sigma=W_CONE / 3.0)
    p_U = build_uniform(model)
    two = DiscretePrior("two atoms", np.array([[0.0], [W_CONE]]), np.array([0.5, 0.5]))
    want = _one_d_cone_scores(W_CONE / 3.0, W_CONE)
    cell = score_cell(model, {"p_U": p_U, "two": two}, ("own", p_U), S_q=2000, rng=np.random.default_rng(20261166))
    for name, value in want.items():
        assert agree_mc(cell.R_mean[name], value, cell.R_mcse[name]), (name, cell.R_mean[name], value)


def test_t1c_mcse_is_the_standard_error_of_the_draws():
    """T1(c) (F5): the reported Monte-Carlo errors are the standard errors of the per-draw
    scores, `std(draws, ddof=1) / sqrt(S_q)`. Every agreement test takes its tolerance from
    them; an error twenty times too large (the standard deviation, without `sqrt(S_q)`)
    would turn those tests into near-tautologies."""
    model = cheap_model()
    p_U = build_uniform(model)
    priors = {"p_J": build_jeffreys(model), "p_U": p_U}
    cell = score_cell(model, priors, ("own", p_U), S_q=S_Q_TEST, rng=np.random.default_rng(20261167))
    for name in priors:
        for draws, se in ((cell.draws_R[name], cell.R_mcse[name]), (cell.draws_r[name], cell.r_mcse[name])):
            assert draws.shape == (S_Q_TEST,)
            np.testing.assert_allclose(se, np.std(draws, ddof=1) / np.sqrt(S_Q_TEST), rtol=1e-10)


@pytest.mark.slow
def test_t1d_floor_and_mismatch_errors_match_their_spread():
    """T1(d) (F5): the errors that `matched_floor` and `marginal_mismatch` report agree,
    within a factor of 2, with the spread of each estimate over 20 seeds."""
    model = cheap_model()
    p_U, p_J = build_uniform(model), build_jeffreys(model)
    nature = ("own", p_U)
    for estimator in (
        lambda rng: matched_floor(model, nature, S_q=S_Q_TEST, rng=rng),
        lambda rng: marginal_mismatch(model, nature, p_J, S_q=S_Q_TEST, rng=rng),
    ):
        runs = np.array([estimator(np.random.default_rng(20261300 + k)) for k in range(20)])
        ratio = runs[:, 1].mean() / runs[:, 0].std(ddof=1)
        assert 0.5 <= ratio <= 2.0, ratio


def test_t1e_gap_error_comes_from_per_draw_differences():
    """T1(e) (F5; §4.4, "Errors of differences"): a cell's priors share its draws, so the
    error of a gap is the standard error of the per-draw differences. For `p*` against
    `p*_{10N}` it equals `paired_mcse` of their draws and lies well below the root-sum-square
    of the two scores' errors, which would make §3.7's verdict needlessly blunt."""
    model = cheap_model()
    p_U = build_uniform(model)
    priors = {"p*": build_pstar(model).prior, "p*_10N": build_pstar(model, budget=10 * model.N).prior}
    cell = score_cell(model, priors, ("own", p_U), S_q=S_Q_TEST, rng=np.random.default_rng(20261168))
    est, err = row_summaries(cell.draws_R, cell.draws_r, own_prior="p_U").gap_fine["R"]
    np.testing.assert_allclose(est, cell.R_mean["p*"] - cell.R_mean["p*_10N"], rtol=1e-10, atol=1e-12)
    np.testing.assert_allclose(err, paired_mcse(cell.draws_R["p*"], cell.draws_R["p*_10N"]), rtol=1e-10)
    assert err < 0.5 * np.hypot(cell.R_mcse["p*"], cell.R_mcse["p*_10N"])


# ---------------------------------------------------------------------------
# P7a / T7a — the marginal and the predictive
# ---------------------------------------------------------------------------


def test_t7a_discrete_marginal_is_the_atom_sum():
    """T7(a): for a discrete prior, `log m_pi(xbar)` is the exact atom sum
    `logsumexp_a [log w_a + log N(xbar; y(theta_a), sigma_eff^2)]` (§4.4)."""
    rng = np.random.default_rng(20261163)
    model = cheap_model()
    atoms = np.sort(rng.uniform(0, 1, size=(7, 2)), axis=-1)
    weights = rng.dirichlet(np.ones(7))
    prior = DiscretePrior("toy", atoms, weights)
    xbar = model.y(atoms[:3]) + model.sigma_eff * rng.standard_normal((3, model.m_out))
    log_n = _log_normal_iso(xbar[:, None, :], model.y(atoms)[None, :, :], model.sigma_eff**2)
    expected = np.logaddexp.reduce(np.log(weights)[None, :] + log_n, axis=1)
    np.testing.assert_allclose(log_marginal(prior, model, xbar, method="atoms"), expected, rtol=1e-12)


def test_t7a_discrete_predictive_is_the_atom_sum():
    """T7(a) for the posterior predictive (F8): for a discrete prior at `N = 4`,
    `log m_pi(x' | xbar) = logsumexp_a [log w_a + log N(xbar; y_a, sigma^2/N)
    + log N(x'; y_a, sigma^2)] - log m_pi(xbar)` (§4.4), with the two noises from the cell,
    not from the model. Pins both noise levels exactly."""
    rng = np.random.default_rng(20261169)
    sigma, N = CHEAP_TWIN["sigma"], CHEAP_TWIN["N"]
    model = cheap_model_at(CHEAP_TWIN)
    atoms = np.sort(rng.uniform(0, 1, size=(7, 2)), axis=-1)
    weights = rng.dirichlet(np.ones(7))
    prior = DiscretePrior("toy", atoms, weights)
    y = model.y(atoms)
    xbar = y[:3] + sigma / np.sqrt(N) * rng.standard_normal((3, model.m_out))
    x_prime = y[:3] + sigma * rng.standard_normal((3, model.m_out))
    joint = np.log(weights) + _log_normal_iso(xbar[:, None], y[None], sigma**2 / N)
    expected = np.logaddexp.reduce(joint + _log_normal_iso(x_prime[:, None], y[None], sigma**2), axis=1)
    expected -= np.logaddexp.reduce(joint, axis=1)
    np.testing.assert_allclose(prior.log_predictive(model, x_prime, xbar), expected, rtol=1e-12)


def _fine_grid_prior(name: str, prior, G: int = 400) -> DiscretePrior:
    """`prior` on a `G x G` grid of `xi`-cells over the ordered triangle. A product law gets
    each cell's exact mass from its closed-form per-rate CDF (`per_rate_law`):
    `2 dF_1 dF_2` off the diagonal, and on
    it the ordered half of the cell, `dF^2`, with the atom at that half's centroid. Midpoint
    densities misjudge `p_LN`'s integrable spike at `xi -> 0` by 4e-2 nats, and full-weight
    diagonal cells put twice the mass on coinciding rates (2.5e-3 nats for `p_U`; MB,
    2026-11-26). `p_J` is not a product law and keeps midpoint densities; it vanishes on the
    diagonal."""
    e = np.linspace(0.0, 1.0, G + 1)
    mid = 0.5 * (e[:-1] + e[1:])
    i, j = np.meshgrid(np.arange(G), np.arange(G), indexing="ij")
    keep = i <= j
    i, j = i[keep], j[keep]
    if name not in PRODUCT_LAWS:
        grid = np.column_stack([mid[i], mid[j]])
        weights = np.exp(prior.log_density(grid))
        return DiscretePrior(f"{name} on a grid", grid, weights / weights.sum())
    F = per_rate_law(name, prior)[0](e)
    F[0], F[-1] = 0.0, 1.0
    dF = np.diff(F)
    weights = np.where(i < j, 2.0 * dF[i] * dF[j], dF[i] ** 2)
    lo, width = e[i], e[i + 1] - e[i]
    grid = np.column_stack([np.where(i < j, mid[i], lo + width / 3), np.where(i < j, mid[j], lo + 2 * width / 3)])
    return DiscretePrior(f"{name} on a grid", grid, weights / weights.sum())


@pytest.mark.parametrize("name", ["p_U", "p_J", "p_LN"])
def test_t7a_continuous_quadrature_matches_a_fine_atom_sum(name):
    """T7(a): a continuous prior's quadrature agrees with the atom sum of the same prior
    placed on a fine grid of `Theta` (a shared support), for `p_J` and `p_LN` as well as the
    flat `p_U` (F6), so a quadrature that drops the prior's density fails. The grid's cells
    carry exact masses for the product laws (`_fine_grid_prior`)."""
    rng = np.random.default_rng(20261164)
    model = cheap_model()
    prior = {"p_U": build_uniform, "p_J": build_jeffreys, "p_LN": build_pln}[name](model)
    fine = _fine_grid_prior(name, prior)
    xbar = model.y(prior.sample(10, rng)) + model.sigma_eff * rng.standard_normal((10, model.m_out))
    np.testing.assert_allclose(
        log_marginal(prior, model, xbar, method="quadrature"), log_marginal(fine, model, xbar, method="atoms"), atol=1e-3
    )


THIN_STATES_D3 = {
    "near corner": [0.97, 0.97, 0.97],
    "fast and slow": [0.0, 1.0, 1.0],
    "near fast and slow": [0.02, 1.0, 1.0],
    "coincident": [0.5, 0.5, 0.5],
    "mixed faces": [0.0, 0.5, 1.0],
    "typical": [0.3, 0.6, 0.8],
}
"""Exp-decay states at `D = 3` where a 20000-draw cloud is thin, and one where it is not.
At each, the default grid agrees with one of half its cell length (0.3 noise units) within
0.03 nats on the mean `log m`. The no-decay corner `(1, 1, 1)` is left out: there the two
grids differ by 0.11 (`p_LN`) and 0.16 (`p_J`) nats (2026-11-26)."""


@pytest.mark.parametrize("name", ["p_LN", "p_J"])
def test_t7a_sampled_marginal_matches_the_grid_at_thin_states(name):
    """T7(a) (§4.4, OQ-13): a continuous prior carried as a sampled cloud (`SampledPrior`, the
    path of `p_J` from `D = 4` and of the product laws above `D = 5`) gives the same `log m` as
    the grid where both exist, including where the prior is thin. At `D = 3` both run. At each
    state of `THIN_STATES_D3`, over 64 draws of `x`, the mean of `log m` from the sampled
    prior's `log_marginal`, the path the scores use, agrees with the grid's within 0.1 nats,
    T4's bar for marginals. A cloud has no draws where the prior's mass is below about
    `1/20000`, so its mixture there underestimates `m`. At `D = 5` the per-point estimate
    overstated `p_LN`'s per-state divergence by a median of 10 nats and up to 75 at face
    states, and the plain cloud by up to 188 (MB, 2026-11-26)."""
    from infomax.sampled import build_sampled_jeffreys, sampled_from

    model = cheap_model(D=3)
    s = model.sigma_eff
    grid = {"p_LN": build_pln, "p_J": build_jeffreys}[name](model)
    assert not hasattr(grid, "refined_log_marginal"), "at D = 3 the reference must be the grid"
    sampled = sampled_from(grid, model, name) if name == "p_LN" else build_sampled_jeffreys(model)
    off = {}
    for k, (label, theta) in enumerate(THIN_STATES_D3.items()):
        y = model.y(np.asarray(theta, dtype=float)[None])[0]
        x = y + s * np.random.default_rng(20261230 + k).standard_normal((64, y.size))
        off[label] = float(np.mean(log_marginal(grid, model, x) - log_marginal(sampled, model, x)))
    assert all(abs(v) <= 0.1 for v in off.values()), off


@pytest.mark.parametrize("name", ["p_J", "p_U"])
@pytest.mark.parametrize("D", [4, 6])
def test_t7a_tapered_cone_marginal_matches_brute_force(D, name):
    """T7(a) (F6): in the tapered hypercone at `D = 4` and 6, `log m_pi(xbar)` for Jeffreys and
    the uniform prior matches brute-force Monte Carlo over 10^6 states drawn in the test
    (Jeffreys as `theta_1 = W U^(1/D)`, §9.2, with a uniform cross-section) within four of
    the Monte Carlo's own standard errors. No fast test scored the tapered cone at `D > 1`,
    so a cone marginal with the wrong widths passed."""
    rng = np.random.default_rng(20261170)
    model = cone_model(D)
    prior = build_jeffreys(model) if name == "p_J" else build_uniform(model)
    n = 1_000_000
    u = rng.uniform(size=n)
    theta1 = W_CONE * u ** (1.0 / D) if name == "p_J" else W_CONE * u
    theta = np.column_stack([theta1, rng.uniform(0, 1, (n, D - 1))])
    xbar = model.y(theta[:3]) + model.sigma_eff * rng.standard_normal((3, model.m_out))
    got = log_marginal(prior, model, xbar)
    for i, xb in enumerate(xbar):
        log_w = np.concatenate([_log_normal_iso(xb, model.y(c), model.sigma_eff**2) for c in np.array_split(theta, 10)])
        want, se = log_mean_exp_with_error(log_w)
        assert abs(got[i] - want) <= MC_SIGMAS * se + 1e-9, (i, got[i], want, se)


# ---------------------------------------------------------------------------
# P7c / T7c — the budget through the noise
# ---------------------------------------------------------------------------


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


def test_t7c_two_fold_divergence_by_explicit_monte_carlo():
    """T7(c) (m2): the per-state divergence of the literal two-fold channel, computed in the
    test by Monte Carlo over `(x_1, x_2)`, `E[log p(x_1, x_2|theta) - log sum_a w_a
    p(x_1|a) p(x_2|a)]`, matches `per_state_redundancy` at `sigma_eff`. Unlike comparing two
    code paths of the implementation, this passes no `literal_nfold` flag that might reduce
    internally."""
    rng = np.random.default_rng(20261171)
    sigma, N = 10.0, 2
    model = cone_model(1, sigma=sigma, N=N)
    prior = build_pstar(model).prior
    a, w = prior.atoms[:, 0], prior.weights
    n = 200_000
    for theta in (5.0, 25.0, 45.0):
        x = theta + sigma * rng.standard_normal((n, 2))
        log_like = scipy.stats.norm.logpdf(x, theta, sigma).sum(-1)
        log_mix = np.logaddexp.reduce(np.log(w) + scipy.stats.norm.logpdf(x[:, :, None], a, sigma).sum(1), axis=-1)
        d = log_like - log_mix
        want, se = d.mean(), d.std(ddof=1) / np.sqrt(n)
        got = per_state_redundancy(prior, model, np.array([[theta]]), rng=np.random.default_rng(20261172), n_x=65536)[0]
        assert abs(got - want) <= MC_SIGMAS * np.hypot(se, d.std() / np.sqrt(65536)), (theta, got, want)


# ---------------------------------------------------------------------------
# P8 / T8 — floors and the ceiling
# ---------------------------------------------------------------------------


def _check_floors(cell, cast: dict, own: str | None) -> None:
    """T8(a) on one row: floors non-negative, every prior at or above them within its
    mismatch's own error (m7), and the row's own prior at zero mismatch."""
    assert cell.floor_R >= 0 and cell.floor_r >= 0
    for name in cast:
        assert cell.R_mean[name] >= cell.floor_R - MC_SIGMAS * cell.mismatch_R_mcse[name], name
        assert cell.r_mean[name] >= cell.floor_r - MC_SIGMAS * cell.mismatch_r_mcse[name], name
    if own is not None:
        np.testing.assert_allclose(cell.mismatch_R[own], 0.0, atol=1e-12)
        np.testing.assert_allclose(cell.mismatch_r[own], 0.0, atol=1e-12)


def test_t8_floors_and_matched_prior():
    """T8(a): per nature, `R_N^q(pi) >= I_q >= 0` for every prior, and likewise for `r_N`
    with the conditional floor; the matched prior's mismatch is zero (§2.1, §2.5). The slack
    is the mismatch's own error, from per-draw differences, not the score's (m7)."""
    model = cheap_model()
    cast = build_cast(model, np.random.default_rng(20261173))
    cell = score_cell(model, cast, ("own", cast["p_U"]), S_q=S_Q_TEST, rng=np.random.default_rng(20261174))
    _check_floors(cell, cast, "p_U")


@pytest.mark.slow
@pytest.mark.parametrize("where", ["cheap", "cone"])
def test_t8_floors_on_every_row(where):
    """T8(a) (F4): the floors hold on every row of the cheap cell and of one cone cell,
    nested and stress natures included, not only in `p_U`'s world, which was the first and
    only guard on a nested floor."""
    model = cheap_model() if where == "cheap" else cone_model(4)
    cast = build_cast(model, np.random.default_rng(20261175))
    names = {id(p): n for n, p in cast.items()}
    for k, row in enumerate(cell_rows(model, cast)):
        cell = score_cell(model, cast, row, S_q=S_Q_TEST, rng=np.random.default_rng(20261400 + k))
        own = names[id(row[1])] if row[0] == "own" else None
        _check_floors(cell, cast, own)


def test_t8_qbar_wins_the_row_average_and_splits_the_mean():
    """T8(b), (c): among fixed priors the row-averaged score is smallest for `q̄`; and each
    prior's mean mismatch equals `q̄`'s mean mismatch plus `D_KL(m_q̄ || m_pi)` (`[^2-qbar]`).
    (c) is a consistency check: it holds for any `log m_q̄` once `q̄`'s sampler is the row
    mixture (F6). `q̄` need not win per row; this is not asserted."""
    model = cheap_model()
    cast = build_cast(model, np.random.default_rng(20261176))
    rows = [("own", prior) for prior in cast.values()]
    qbar = build_qbar(rows)
    priors = {**cast, "q̄": qbar}
    cells = [score_cell(model, priors, row, S_q=S_Q_TEST, rng=np.random.default_rng(20261177)) for row in rows]
    mean_R = {n: np.mean([c.R_mean[n] for c in cells]) for n in priors}
    se_R = {n: np.sqrt(np.sum([c.R_mcse[n] ** 2 for c in cells])) / len(cells) for n in priors}
    for n in cast:
        assert mean_R["q̄"] <= mean_R[n] + MC_SIGMAS * np.hypot(se_R["q̄"], se_R[n])
    mean_mis = {n: np.mean([c.mismatch_R[n] for c in cells]) for n in priors}
    se_mis = {n: np.sqrt(np.sum([c.mismatch_R_mcse[n] ** 2 for c in cells])) / len(cells) for n in priors}
    for n in cast:
        to_qbar, to_qbar_se = marginal_mismatch(model, ("own", qbar), cast[n], S_q=S_Q_TEST, rng=np.random.default_rng(20261178))
        assert agree_mc(mean_mis[n], mean_mis["q̄"] + to_qbar, se_mis[n], se_mis["q̄"], to_qbar_se)


# ---------------------------------------------------------------------------
# P17 / T17 — the one-step score
# ---------------------------------------------------------------------------


def test_t17_one_step_score():
    """T17: (a) under common random numbers `r_N^q(pi)` from (2.1.5) matches
    `R_{N+1}^q(pi) - R_N^q(pi)` (F8). The tolerance is the error of the per-draw
    differences, and the error of `R_{N+1} - R_N` must be below a tenth of `r_N`, which also
    checks that the two runs share their draws; `S_q = 2000` makes it so. (b) `r_N^q(pi)`
    equals the conditional floor plus the expected posterior-predictive mismatch of (2.1.6),
    a consistency check (F6). T17(c) pins the noise levels exactly."""
    N, S_q = 2, 2000
    model_N, model_N1 = cheap_model(N=N), cheap_model(N=N + 1)
    p_J = build_jeffreys(model_N)
    nature = ("own", build_uniform(model_N))
    a = score_cell(model_N, {"p_J": p_J}, nature, S_q=S_q, rng=np.random.default_rng(20261179))
    b = score_cell(model_N1, {"p_J": p_J}, nature, S_q=S_q, rng=np.random.default_rng(20261179))
    dR = b.draws_R["p_J"] - a.draws_R["p_J"]
    assert dR.std(ddof=1) / np.sqrt(S_q) < 0.1 * abs(a.r_mean["p_J"]), "the two runs do not share their draws"
    assert abs(a.r_mean["p_J"] - dR.mean()) <= MC_SIGMAS * paired_mcse(a.draws_r["p_J"], dR)
    floor, floor_se = matched_floor(model_N, nature, S_q=S_Q_TEST, rng=np.random.default_rng(20261180), score="r")
    mis, mis_se = marginal_mismatch(model_N, nature, p_J, S_q=S_Q_TEST, rng=np.random.default_rng(20261181), score="r")
    assert agree_mc(a.r_mean["p_J"], floor + mis, a.r_mcse["p_J"], floor_se, mis_se)


@pytest.mark.parametrize("which", ["discrete", "p_J"])
def test_t17c_predictive_is_the_ratio_of_marginals(which):
    """T17(c) (F8): per draw, with `xbar_{N+1} = (N xbar_N + x') / (N + 1)`,
    `log m(x' | xbar_N) = log m_{N+1}(xbar_{N+1}) - log m_N(xbar_N)
    - (m/2) log(2 pi sigma^2 (N+1)/N) - N ||x' - xbar_N||^2 / (2 (N+1) sigma^2)`,
    each marginal at its own noise `sigma / sqrt(n)` (the sufficiency factors of §4.4 in
    closed form; checked on a discrete prior to 4e-15 when the decision was taken). It holds
    for any prior, so it pins both noise levels with no Monte-Carlo slack: `x'` drawn or
    scored at `sigma_eff` fails. Tolerance `1e-10` for atoms, `1e-4` for Jeffreys'
    quadrature (auto-chosen)."""
    rng = np.random.default_rng(20261182)
    sigma, N = 0.1, 4
    model_N, model_N1 = cheap_model(N=N), cheap_model(N=N + 1)
    if which == "discrete":
        atoms = np.sort(rng.uniform(0, 1, size=(7, 2)), axis=-1)
        prior, tol = DiscretePrior("toy", atoms, rng.dirichlet(np.ones(7))), 1e-10
    else:
        prior, tol = build_jeffreys(model_N), 1e-4
    y = model_N.y(model_N.box.sample_uniform(20, rng))
    m = model_N.m_out
    xbar = y + sigma / np.sqrt(N) * rng.standard_normal(y.shape)
    x_prime = y + sigma * rng.standard_normal(y.shape)
    xbar1 = (N * xbar + x_prime) / (N + 1)
    want = (
        log_marginal(prior, model_N1, xbar1)
        - log_marginal(prior, model_N, xbar)
        - 0.5 * m * np.log(2 * np.pi * sigma**2 * (N + 1) / N)
        - N * ((x_prime - xbar) ** 2).sum(-1) / (2 * (N + 1) * sigma**2)
    )
    np.testing.assert_allclose(prior.log_predictive(model_N, x_prime, xbar), want, rtol=0, atol=tol)


def test_t17d_cumulative_score_depends_on_sigma_over_root_N_only():
    """§2.1's invariance (F9): `R_N` depends on `sigma` and `N` only through `sigma/sqrt(N)`,
    while `r_N` does not. Scored with the same priors and seed at the cheap cell
    `(0.1, 1)` and its twin `(0.2, 4)`, the per-draw `R` arrays are identical and the `r`
    arrays differ. Catches a score that draws `xbar` at `sigma`."""
    model_1, model_4 = cheap_model(), cheap_model_at(CHEAP_TWIN)
    p_U = build_uniform(model_1)
    priors = {"p_J": build_jeffreys(model_1), "p*": build_pstar(model_1).prior}
    a = score_cell(model_1, priors, ("own", p_U), S_q=S_Q_TEST, rng=np.random.default_rng(20261183))
    b = score_cell(model_4, priors, ("own", p_U), S_q=S_Q_TEST, rng=np.random.default_rng(20261183))
    for name in priors:
        np.testing.assert_allclose(a.draws_R[name], b.draws_R[name], rtol=1e-12, atol=1e-12)
        assert np.max(np.abs(a.draws_r[name] - b.draws_r[name])) > 1e-3, name


# ---------------------------------------------------------------------------
# P20 / T20 — the round robin
# ---------------------------------------------------------------------------


def test_t20_round_robin_mismatches_are_non_negative():
    """T20: in each prior's own world, no other prior's mismatch is negative beyond its own
    Monte-Carlo error (m7), on either score. Each estimates a KL divergence, so a negative
    value is a bug: a sampler that does not draw from the prior whose mixture is evaluated,
    or a mixture that does not normalise (§2.5)."""
    model = cheap_model()
    cast = build_cast(model, np.random.default_rng(20261184))
    for own, prior in cast.items():
        cell = score_cell(model, cast, ("own", prior), S_q=S_Q_TEST, rng=np.random.default_rng(20261185))
        for name in cast:
            assert cell.mismatch_R[name] >= -MC_SIGMAS * cell.mismatch_R_mcse[name], (own, name, "R")
            assert cell.mismatch_r[name] >= -MC_SIGMAS * cell.mismatch_r_mcse[name], (own, name, "r")
