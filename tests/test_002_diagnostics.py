"""Spec 002 tests: closed forms and diagnostics (P5, P6, P21, P22).

specs/002-foreign-q-prediction.md §2.4, §3.2, §3.3, §4.5, §9 and §5.2 (T5, T6, T21, T22).
Stubs raise `NotImplementedError` until the implementation exists. Regenerated after the
test red-team (`tests/test_002_foreign_q_prediction-redteam.md`: F4, F9, F10, F11, F12,
m8, m9, m10, m11, m12).
"""
from __future__ import annotations

import math

import numpy as np
import pytest
import scipy.integrate
import scipy.stats

from infomax.diagnostics import (
    RELATIVES,
    beyond_cap,
    capacity_gap,
    cast_present_at_every_D,
    covered_fraction,
    exchange,
    failure_map_point,
    gaussian_kl_split,
    hypercone_jeffreys_mean,
    hypercone_jeffreys_mode,
    jeffreys_cone_loss,
    joint_width2,
    joint_width_ratio,
    mass_near,
    moment_matched_predictive,
    relevant_datum_divergence,
    row_summaries,
)
from infomax.jeffreys import build_jeffreys
from infomax.priors002 import DiscretePrior
from infomax.pref import build_uniform
from infomax.pstar import build_pstar
from infomax.qfamily import cell_rows
from infomax.score import per_state_redundancy, score_cell
from spec002_common import (
    CHEAP_CELLS,
    EQUALIZER_SLACK,
    MC_SIGMAS,
    S_Q_TEST,
    build_cast,
    cheap_model,
    cheap_model_at,
    cone_model,
)

W_CONE = 50.0


# ---------------------------------------------------------------------------
# P5 / T5 — the Gaussian split (3.3.1)
# ---------------------------------------------------------------------------


def _random_spd(rng, m):
    A = rng.normal(size=(m, m))
    return A @ A.T + 0.5 * np.eye(m)


def test_t5_gaussian_kl_split_matches_numeric_kl():
    """T5: for random Gaussians, half the sum of (3.3.1)'s two terms matches a Monte-Carlo
    `D_KL(N_q || N_pi)`. Catches a sign or trace error in the decomposition; which term is
    which is pinned by the pure cases below."""
    rng = np.random.default_rng(20261180)
    m = 2
    for _ in range(5):
        mu_q, mu_pi = rng.normal(size=m), rng.normal(size=m)
        S_q, S_pi = _random_spd(rng, m), _random_spd(rng, m)
        shift, spread = gaussian_kl_split(mu_q, S_q, mu_pi, S_pi)
        x = rng.multivariate_normal(mu_q, S_q, size=400_000)

        def logpdf(x, mu, S):
            d = x - mu
            return -0.5 * np.einsum("ni,ij,nj->n", d, np.linalg.inv(S), d) - 0.5 * np.log(np.linalg.det(2 * np.pi * S))

        llr = logpdf(x, mu_q, S_q) - logpdf(x, mu_pi, S_pi)
        assert abs(0.5 * (shift + spread) - llr.mean()) <= 4 * llr.std() / np.sqrt(llr.size)


def test_t5_gaussian_kl_split_vanishes_when_matched():
    """T5: both terms of (3.3.1) are zero at `(mu_pi, Sigma_pi) = (mu_q, Sigma_q)` (§3.3)."""
    mu, S = np.array([0.3, -1.0]), np.array([[2.0, 0.3], [0.3, 1.0]])
    shift, spread = gaussian_kl_split(mu, S, mu, S)
    assert abs(shift) <= 1e-12 and abs(spread) <= 1e-12


def test_t5_pure_shift_and_pure_spread():
    """T5 (F11): with equal covariances the spread term is zero and the shift is the
    Mahalanobis distance `(mu_pi - mu_q)^T Sigma^-1 (mu_pi - mu_q)`; with equal means the
    shift is zero and the spread is `tr(Sigma_pi^-1 Sigma_q) - m + log det Sigma_pi /
    det Sigma_q`. Which term carries a prior's mismatch is the diagnostic's whole content
    (§3.3), so a split that swaps or mixes the terms fails here."""
    rng = np.random.default_rng(20261186)
    m = 3
    S, S_pi = _random_spd(rng, m), _random_spd(rng, m)
    mu_q, mu_pi = rng.normal(size=m), rng.normal(size=m)
    shift, spread = gaussian_kl_split(mu_q, S, mu_pi, S)
    d = mu_pi - mu_q
    np.testing.assert_allclose(shift, d @ np.linalg.solve(S, d), rtol=1e-12)
    assert abs(spread) <= 1e-12
    shift, spread = gaussian_kl_split(mu_q, S, mu_q, S_pi)
    assert abs(shift) <= 1e-12
    want = np.trace(np.linalg.solve(S_pi, S)) - m + np.log(np.linalg.det(S_pi) / np.linalg.det(S))
    np.testing.assert_allclose(spread, want, rtol=1e-12)


# ---------------------------------------------------------------------------
# P6 / T6 — the hypercone deviation (9.2.2)
# ---------------------------------------------------------------------------


def _jeffreys_posterior_mean_by_quadrature(x1: float, D: int, W: float) -> float:
    """Jeffreys' posterior mean of `theta_1` in the hypercone at noise 1: the prior
    `∝ theta_1^(D-1)` on `[0, W]` times `exp(-(x1 - theta_1)^2 / 2)`, by `scipy.integrate.quad`."""
    shift = (D - 1) * math.log(x1 + (D - 1) / x1)
    f = lambda t, k: t**k * math.exp((D - 1) * math.log(t) - 0.5 * (x1 - t) ** 2 - shift) if t > 0 else 0.0
    opts = dict(points=[x1], limit=400, epsabs=0, epsrel=1e-13)
    return scipy.integrate.quad(lambda t: f(t, 1), 0, W, **opts)[0] / scipy.integrate.quad(lambda t: f(t, 0), 0, W, **opts)[0]


@pytest.mark.parametrize("D, departure", [(6, -0.0187), (11, -0.0773), (26, -0.4185)])
def test_t6_hypercone_jeffreys_deviation(D, departure):
    """T6 (F12): Jeffreys' posterior mean of `theta_1` at `x_1 = 10` (`W = 50`, noise 1, as
    A&M) lies toward the thick end and matches the mean computed in the test by quadrature
    to `1e-6`. Its departure from the leading order `(D - 1)/x_1` is about −0.0187, −0.0773
    and −0.4185 at `D = 6, 11, 26` (§9.2). The old tolerance, the whole first neglected
    term, passed the leading-order formula itself and the mode."""
    x1 = 10.0
    want = _jeffreys_posterior_mean_by_quadrature(x1, D, W_CONE)
    got = hypercone_jeffreys_mean(x1, D, W_CONE)
    assert got > x1, "the pull is toward the thick end"
    np.testing.assert_allclose(got, want, atol=1e-6)
    np.testing.assert_allclose((want - x1) - (D - 1) / x1, departure, atol=1e-3)


@pytest.mark.parametrize("D", [6, 11, 26])
def test_t6_hypercone_jeffreys_mode_is_the_exact_root(D):
    """T6(iii) (F12): the mode is where the log posterior `-(x_1 - theta)^2/2 + (D - 1) log
    theta` is stationary with negative curvature (9.2.1), checked by its derivative rather
    than by the closed form it is computed from, and it differs from the mean."""
    x1 = 10.0
    mode = hypercone_jeffreys_mode(x1, D)
    assert abs((x1 - mode) + (D - 1) / mode) <= 1e-10
    assert -1.0 - (D - 1) / mode**2 < 0
    assert abs(_jeffreys_posterior_mean_by_quadrature(x1, D, W_CONE) - mode) > 1e-3


# ---------------------------------------------------------------------------
# P21 / T21 — the mass bound, the insurance inequality, Jeffreys' loss
# ---------------------------------------------------------------------------


def _check_mass_bound(model, priors, rng) -> None:
    theta = model.box.sample_uniform(30, rng)
    for name, prior in priors.items():
        loss = per_state_redundancy(prior, model, theta, rng=rng, n_x=256)
        bound = -np.log(mass_near(prior, model, theta)) + 0.5
        assert np.all(loss <= bound + 0.05), name


@pytest.mark.parametrize("cell", list(CHEAP_CELLS.values()), ids=list(CHEAP_CELLS))
def test_t21a_mass_bound(cell):
    """T21(a): at sampled states, for every prior, `R_N^theta(pi) <= -log pi(A(theta)) + 1/2`
    (3.2.1), with a small Monte-Carlo slack, at the cheap cell and its twin (F9). It cannot
    fail when correct, and it is one-sided: `mass_near` is pinned separately below."""
    model = cheap_model_at(cell)
    priors = {"p*": build_pstar(model).prior, "p_J": build_jeffreys(model), "p_U": build_uniform(model)}
    _check_mass_bound(model, priors, np.random.default_rng(20261188))


@pytest.mark.slow
@pytest.mark.parametrize("D", [6, 11, 26])
def test_t21a_mass_bound_in_the_hypercone(D):
    """T21(a) where §5.4 puts it (m8): in the hypercone at `D in {6, 11, 26}`."""
    model = cone_model(D)
    priors = {"p*": build_pstar(model).prior, "p_J": build_jeffreys(model), "p_U": build_uniform(model)}
    _check_mass_bound(model, priors, np.random.default_rng(20261189))


def test_t21a_mass_near_is_a_sum_of_weights():
    """T21(a) (m8): for a discrete prior `pi(A(theta))` is the total weight of the atoms whose
    predictions lie within one noise unit of `y(theta)` at budget `N`,
    `sqrt(N) ||y(theta_a) - y(theta)|| / sigma <= 1` (§1.1), here at `N = 4`, computed in the
    test. A `mass_near` that understates the mass would loosen the bound unseen; one that
    overstates it is caught at the states with no atom within reach. The states are atoms
    moved by 0.01 in `xi`, up to about 3 noise units near `xi = 1`, so some leave their own
    atom's reach: the precondition asks only for both kinds of state (MB, 2026-11-26)."""
    rng = np.random.default_rng(20261190)
    sigma, N = 0.1, 4
    model = cheap_model(N=N)
    atoms = np.sort(rng.uniform(0, 1, size=(40, 2)), axis=-1)
    weights = rng.dirichlet(np.ones(40))
    prior = DiscretePrior("toy", atoms, weights)
    theta = atoms[:10] + 0.01 * rng.standard_normal((10, 2))
    theta = np.sort(np.clip(theta, 0, 1), axis=-1)
    dist = np.linalg.norm(model.y(atoms)[None] - model.y(theta)[:, None], axis=-1) * np.sqrt(N) / sigma
    want = (weights[None] * (dist <= 1.0)).sum(-1)
    assert np.any(want == 0) and np.any(want > 0) and np.all(want < 1)
    np.testing.assert_allclose(mass_near(prior, model, theta), want, rtol=1e-12)


@pytest.mark.slow
@pytest.mark.parametrize("nature", ["own:p*", "own:p_J", "own:p_U", "stress:interior"])
def test_t21b_insurance_inequality(nature):
    """T21(b) (F4): in the hypercone the two sides of (3.2.3) are ordered as stated on every
    nature inside the agent's model, the round robin and the interior stress nature (§3.2).
    The hypercone's nested natures, scored by a smaller agent, put `theta` outside the
    agent's `Theta`, where `p*`'s cap does not hold, so (3.2.3) is not asserted there."""
    rng = np.random.default_rng(20261191)
    model = cone_model(6, falloff=0.5)
    pstar = build_pstar(model)
    p_J = build_jeffreys(model)
    kind, arg = nature.split(":")
    row = (kind, {"p*": pstar.prior, "p_J": p_J, "p_U": build_uniform(model)}[arg]) if kind == "own" else (kind, arg)
    cell = score_cell(model, {"p*": pstar.prior, "p_J": p_J}, row, S_q=S_Q_TEST, rng=rng)
    loss_J = per_state_redundancy(p_J, model, cell.theta[:200], rng=rng, n_x=64)
    covered = loss_J <= pstar.capacity
    rhs = np.mean(np.where(covered, 0.0, loss_J - pstar.capacity)) - pstar.capacity * covered.mean()
    lhs = cell.R_mean["p_J"] - cell.R_mean["p*"]
    lhs_se = np.std(cell.draws_R["p_J"] - cell.draws_R["p*"], ddof=1) / np.sqrt(S_Q_TEST)
    assert lhs >= rhs - MC_SIGMAS * lhs_se


@pytest.mark.parametrize("D", [6, 11])
def test_t21c_jeffreys_cone_loss_formula(D):
    """T21(c): in the hypercone, where `theta_1 >> D sigma / sqrt(N)`, the divergence between
    the laws of the relevant datum under `theta` and under `p_J` matches (3.2.2) with the
    correction of §9.5, to `2e-3` (m9: at `D = 6` the uncorrected formula is off by
    0.25–0.28 %, so `1e-2` could not tell). At `D = 26` and `100` the agreement is only
    observed (§9.5, m14)."""
    theta1 = np.array([35.0, 40.0, 45.0])
    numeric = relevant_datum_divergence(theta1, D, W=W_CONE, sigma=1.0, N=1)
    formula = jeffreys_cone_loss(theta1, D, W=W_CONE, sigma=1.0, N=1, second_order=True)
    np.testing.assert_allclose(numeric, formula, rtol=2e-3)


@pytest.mark.parametrize("D", [6, 11])
def test_t21c_full_loss_exceeds_the_relevant_datum_divergence(D):
    """T21(c) through the pipeline (m9): Jeffreys' per-state loss on the full data, by
    `per_state_redundancy` with `build_jeffreys`, is at least the relevant datum's divergence,
    since dropping data cannot raise a KL divergence; four seeds give its error. The helpers
    above hard-code Jeffreys' marginal, so they could not see a pipeline error."""
    model = cone_model(D)
    p_J = build_jeffreys(model)
    theta1 = np.array([35.0, 40.0, 45.0])
    theta = np.column_stack([theta1, np.full((3, D - 1), 0.5)])
    runs = np.array([per_state_redundancy(p_J, model, theta, rng=np.random.default_rng(20261192 + k), n_x=1024) for k in range(4)])
    full, se = runs.mean(0), runs.std(0, ddof=1) / 2.0
    relevant = relevant_datum_divergence(theta1, D, W=W_CONE, sigma=1.0, N=1)
    assert np.all(full >= relevant - MC_SIGMAS * se - 1e-9), (full, relevant, se)


# ---------------------------------------------------------------------------
# P22 / T22 — the diagnostics of §4.5
# ---------------------------------------------------------------------------


def test_t22a_moment_matched_predictive_is_as_defined():
    """§3.3, §4.5 (F11): the moment-matched predictive of a discrete prior after `xbar` has
    mean `sum_a w_a(xbar) y(theta_a)` and covariance `sigma^2 1 + Cov_w[y]`, with posterior
    weights `w_a ∝ lambda_a N(xbar; y_a, sigma^2/N)` and the noise of `x'`, `sigma`, not
    `sigma_eff`. At `N = 4`, so that the two differ: one atom gives `(y(theta_a), sigma^2 1)`;
    two atoms give the weights computed in the test."""
    rng = np.random.default_rng(20261187)
    sigma, N = 0.1, 4
    model = cheap_model(N=N)
    m = model.m_out
    one = DiscretePrior("one", np.array([[0.3, 0.7]]), np.array([1.0]))
    xbar = model.y(np.array([[0.3, 0.7]]))[0] + sigma / np.sqrt(N) * rng.standard_normal(m)
    mu, S = moment_matched_predictive(one, model, xbar)
    np.testing.assert_allclose(mu, model.y(np.array([[0.3, 0.7]]))[0], rtol=1e-12)
    np.testing.assert_allclose(S, sigma**2 * np.eye(m), rtol=1e-12, atol=1e-15)
    atoms, lam = np.array([[0.2, 0.5], [0.4, 0.6]]), np.array([0.3, 0.7])
    y = model.y(atoms)
    xbar = 0.5 * (y[0] + y[1]) + sigma / np.sqrt(N) * rng.standard_normal(m)
    log_w = np.log(lam) - 0.5 * ((xbar - y) ** 2).sum(-1) * N / sigma**2
    w = np.exp(log_w - log_w.max())
    w /= w.sum()
    mean = w @ y
    cov = sigma**2 * np.eye(m) + ((y - mean).T * w) @ (y - mean)
    mu, S = moment_matched_predictive(DiscretePrior("two", atoms, lam), model, xbar)
    np.testing.assert_allclose(mu, mean, rtol=1e-10)
    np.testing.assert_allclose(S, cov, rtol=1e-10, atol=1e-14)


def _check_split_on_row(cell, cast: dict, own: str | None) -> None:
    for name in cast:
        shift, spread = cell.mean_shift[name], cell.spread_mismatch[name]
        assert shift >= -1e-12 and spread >= -1e-12, name
        if name == own:
            assert abs(shift) <= 1e-10 and abs(spread) <= 1e-10, name
        elif own is not None:
            assert shift + spread > 1e-8, f"{name} is away from {own}'s world, yet its split vanishes"


def test_t22a_split_terms_vanish_on_the_diagonal():
    """T22(a) (F11): the cell's own `mean_shift` and `spread_mismatch` (3.3.1) vanish for each
    prior in its own world and not for a prior that is away. In `p_U`'s world at the cheap
    cell; the slow test below covers every row and the twin. The old test fed one Gaussian
    to both sides of the split, so it could not fail."""
    model = cheap_model()
    cast = build_cast(model, np.random.default_rng(20261193))
    cell = score_cell(model, cast, ("own", cast["p_U"]), S_q=S_Q_TEST, rng=np.random.default_rng(20261194))
    _check_split_on_row(cell, cast, "p_U")


@pytest.mark.slow
@pytest.mark.parametrize("cell_def", list(CHEAP_CELLS.values()), ids=list(CHEAP_CELLS))
def test_t22a_split_on_every_row(cell_def):
    """T22(a) over every row of the cheap cell and of its twin, where the predictive's noise
    `sigma` differs from `sigma_eff` (F9, F11; §5.4 places T22 over all rows)."""
    model = cheap_model_at(cell_def)
    cast = build_cast(model, np.random.default_rng(20261195))
    names = {id(p): n for n, p in cast.items()}
    for k, row in enumerate(cell_rows(model, cast)):
        cell = score_cell(model, cast, row, S_q=S_Q_TEST, rng=np.random.default_rng(20261500 + k))
        _check_split_on_row(cell, cast, names[id(row[1])] if row[0] == "own" else None)


@pytest.mark.parametrize(
    "R, se, C_N, gap, expected",
    [(5.0, 0.1, 4.0, 0.2, True), (4.25, 0.1, 4.0, 0.2, False), (3.0, 0.1, 4.0, 0.2, False), (4.31, 0.1, 4.0, 0.2, True)],
)
def test_t22b_beyond_cap_label(R, se, C_N, gap, expected):
    """T22(b): a cell is beyond the cap exactly when `R - C_N` exceeds its Monte-Carlo error
    plus the candidate set's capacity gap (§3.7, §4.5, F5). No other mark is made."""
    assert beyond_cap(R, se, C_N, gap) is expected


def test_t22b_capacity_gap_and_capacity():
    """T22(b) (m10): the capacity gap is the largest `R_N^theta(p*) - C_N` over states off the
    candidate set (T3), checked on the same states and stream; and `C_N` is `p*`'s largest
    per-state divergence over the candidates. A capacity gap of 0 would make the label too
    permissive."""
    model = cheap_model()
    res = build_pstar(model)
    off = model.box.sample_uniform(256, np.random.default_rng(20261196))
    gap = capacity_gap(res, model, np.random.default_rng(20261197), states=off)
    b_off = per_state_redundancy(res.prior, model, off, rng=np.random.default_rng(20261197)) - res.capacity
    np.testing.assert_allclose(gap, np.max(b_off), atol=EQUALIZER_SLACK)
    on_candidates = per_state_redundancy(res.prior, model, res.candidates, rng=np.random.default_rng(20261198))
    np.testing.assert_allclose(res.capacity, np.max(on_candidates), atol=EQUALIZER_SLACK)


@pytest.mark.slow
@pytest.mark.parametrize("which", ["own:p_U", "stress:interior"])
def test_t22c_covered_fraction_matches_the_interval(which):
    """T22(c) (F4): in the hypercone, `covered_J` from `K` draws matches the nature's mass on
    the `theta_1`-interval where Jeffreys' per-state loss is at most `C_N` (§3.2, §4.5), on
    natures inside the agent's model whose mass there is closed form: `(W - lo)/W` in `p_U`'s
    world, and the truncated normal's in the interior's."""
    rng = np.random.default_rng(20261199)
    model = cone_model(6, falloff=0.5)
    C_N = build_pstar(model).capacity
    p_J = build_jeffreys(model)
    grid = np.column_stack([np.linspace(0.5, W_CONE, 200), np.full((200, 5), 0.5)])
    covered_theta1 = grid[per_state_redundancy(p_J, model, grid, rng=rng, n_x=256) <= C_N, 0]
    lo = covered_theta1.min() if covered_theta1.size else W_CONE
    if which == "own:p_U":
        nature, expected = ("own", build_uniform(model)), (W_CONE - lo) / W_CONE
    else:
        s = 7.5 * model.sigma_eff
        law = scipy.stats.truncnorm(-W_CONE / 2 / s, W_CONE / 2 / s, loc=W_CONE / 2, scale=s)
        nature, expected = ("stress", "interior"), float(law.sf(lo))
    got = covered_fraction(model, nature, C_N, rng, K=200, J=64)
    assert abs(got - expected) <= 4 * np.sqrt(expected * (1 - expected) / 200) + 0.02


def test_t22d_joint_width_ratio_is_recorded():
    """T22(d): at `D = 2` in exp-decay the proxy and geodesic widths are both computed and
    their ratio recorded; it is not asserted, only required to be finite and positive (a
    ratio outside [1/2, 2] is flagged in the report, §4.5)."""
    rng = np.random.default_rng(20261185)
    model = cheap_model(D=2)
    ratio = joint_width_ratio(model, model.box.sample_uniform(20, rng))
    assert np.all(np.isfinite(ratio)) and np.all(ratio > 0)


def test_t22d_joint_width_in_the_cone_is_closed_form():
    """T22(d) (m12): in the cones `joint_width2` is closed form (§4.5): the largest
    `sum_mu L_mu^2` over the directions below resolution, with widths
    `r phi^(mu-2) sqrt(N)/sigma`. At `sigma = 2`, `phi = 1/2`, `D = 5`, every width is below 1
    at the base `r = 1`, where the sum is largest: `sum_k (phi^k / 2)^2` for `k = 0..3`."""
    model = cone_model(5, falloff=0.5, sigma=2.0)
    want = sum((0.5**k / 2.0) ** 2 for k in range(4))
    np.testing.assert_allclose(joint_width2(model), want, rtol=1e-6)


def test_t22e_failure_map_coordinates():
    """§2.4, §4.5: a row's point on a prior's failure map is at breadth `floor / C_N` and at
    the best rival's mismatch, the smallest among the *other* priors that are away in the
    row (the row's own prior excluded), coloured by the signed gap to that rival (m11 adds
    the cases where the mapped prior itself would otherwise be the smallest, a nested row
    with no own prior, and `r_N` read against its conditional capacity)."""
    mismatch = {"p_U": 0.0, "p*": 1.0, "p_J": 2.5, "p_LN": 0.4}
    pt = failure_map_point(mismatch, "p_J", own_prior="p_U", floor=1.0, capacity=4.0)
    assert pt.breadth == pytest.approx(0.25)
    assert pt.best_rival == pytest.approx(0.4)
    assert pt.gap_to_rival == pytest.approx(2.1)
    own = failure_map_point(mismatch, "p_U", own_prior="p_U", floor=1.0, capacity=4.0)
    assert own.best_rival == pytest.approx(0.4) and own.gap_to_rival == pytest.approx(-0.4)
    self_excluded = failure_map_point(mismatch, "p_LN", own_prior="p_U", floor=1.0, capacity=4.0)
    assert self_excluded.best_rival == pytest.approx(1.0) and self_excluded.gap_to_rival == pytest.approx(-0.6)
    nested = failure_map_point({"p*": 1.2, "p_J": 2.0, "p_U": 0.7}, "p*", own_prior=None, floor=2.0, capacity=5.0)
    assert nested.breadth == pytest.approx(0.4)
    assert nested.best_rival == pytest.approx(0.7) and nested.gap_to_rival == pytest.approx(0.5)
    one_step = failure_map_point({"p*": 0.05, "p_J": 0.2, "p_U": 0.0}, "p_J", own_prior="p_U", floor=0.03, capacity=0.12)
    assert one_step.breadth == pytest.approx(0.25)
    assert one_step.best_rival == pytest.approx(0.05) and one_step.gap_to_rival == pytest.approx(0.15)


# ---------------------------------------------------------------------------
# P22 / T22(f) — the row summaries and readings of §2.4 (F10)
# ---------------------------------------------------------------------------

ROW_R = {
    "p*": 2.0, "p_lat": 2.2, "p_proj": 1.9, "p_LN^*": 2.4, "p*_N/10": 2.3, "p*_10N": 1.7,
    "p_J": 2.6, "p_U": 1.0, "p_LN": 3.0, "p_ref[slowest]": 1.5, "p_ref[fastest]": 1.2,
}
"""A hand-made exp-decay row, in nats; `r` is a tenth of it, so the two scores are told apart."""


def _summaries(scores: dict, own: str | None):
    draws_R = {n: np.full(10, v) for n, v in scores.items()}
    draws_r = {n: np.full(10, v / 10) for n, v in scores.items()}
    return row_summaries(draws_R, draws_r, own_prior=own)


def test_t22f_gap_to_jeffreys_and_to_the_privileged_priors():
    """T22(f) (F10; §2.4): `gap_J = S(pi) - S(p_J)`, not formed in Jeffreys' own world;
    `gap_pi = S(pi) - min S(pi')` over `p_U`, `p_LN` and every `p_ref` ranking, the *best*
    privileged-information prior (`[^2-max]`: the max is the old error), leaving the row's
    own prior out."""
    s = _summaries(ROW_R, None)
    assert s.gap_J["p*"]["R"] == pytest.approx((-0.6, 0.0))
    assert s.gap_J["p*"]["r"] == pytest.approx((-0.06, 0.0))
    assert s.gap_pi["p*"]["R"][0] == pytest.approx(1.0)  # against p_U, the smallest; the max gives -1.0
    in_pU = _summaries(ROW_R, "p_U")
    assert in_pU.gap_pi["p*"]["R"][0] == pytest.approx(0.8)  # p_U left out; fastest-first p_ref, not slowest
    in_pLN = _summaries({**ROW_R, "p_LN": 0.0}, "p_LN")
    assert in_pLN.gap_pi["p*"]["R"][0] == pytest.approx(1.0)  # p_LN left out in its own world
    in_pJ = _summaries(ROW_R, "p_J")
    assert all(pi not in in_pJ.gap_J for pi in ("p*", "p_lat", "p_proj", "p_LN^*"))


def test_t22f_budget_tuning_pairs_and_ranking():
    """T22(f) (F10; §2.4): `gap_budget = S(p*) - min_M S(p*_M) = max(gap_coarse, gap_fine)`;
    `gap_tune = S(p_LN^*) - S(p_LN)`; the protagonist pairs; and `delta_R_pref = R(p*) -
    R(p_ref)` once per ranking in exp-decay, once in the cones."""
    s = _summaries(ROW_R, None)
    assert s.gap_coarse["R"][0] == pytest.approx(-0.3)
    assert s.gap_fine["R"][0] == pytest.approx(0.3)
    assert s.gap_budget["R"][0] == pytest.approx(0.3)
    assert s.gap_budget["r"][0] == pytest.approx(0.03)
    assert s.gap_tune["R"][0] == pytest.approx(-0.6)
    for pair, value in ((("p*", "p_lat"), -0.2), (("p*", "p_proj"), 0.1), (("p_lat", "p_proj"), 0.3), (("p*", "p_LN^*"), -0.4)):
        assert s.gap_pair[pair]["R"][0] == pytest.approx(value), pair
    assert s.delta_R_pref["slowest"][0] == pytest.approx(0.5)
    assert s.delta_R_pref["fastest"][0] == pytest.approx(0.8)
    cone_row = {"p*": 2.0, "p_lat": 2.2, "p_proj": 1.9, "p*_N/10": 2.3, "p*_10N": 1.7, "p_J": 2.6, "p_U": 1.0, "p_ref": 1.0}
    cone = _summaries(cone_row, None)
    assert cone.delta_R_pref["p_ref"][0] == pytest.approx(1.0)
    assert not cone.gap_tune


def test_t22f_relatives_world():
    """T22(f) (F10): `relatives_world` is true in the own worlds of exactly `p*_{N/10}`,
    `p*_{10N}`, `p_lat`, `p_proj` and `p_LN^*`, and false elsewhere, nested rows included."""
    assert set(RELATIVES) == {"p*_N/10", "p*_10N", "p_lat", "p_proj", "p_LN^*"}
    for own in ROW_R:
        assert _summaries(ROW_R, own).relatives_world is (own in RELATIVES), own
    assert _summaries(ROW_R, None).relatives_world is False


def test_t22f_exchange_and_the_cast_present_at_every_D():
    """§2.4's other readings (F10): the exchange is what `a` loses in `b`'s world minus what
    `b` loses in `a`'s, negative when `a` loses less away, and antisymmetric; a trend in `D`
    is also read on the priors present at every `D`."""
    mismatch = {"p*": {"p*": 0.0, "p_J": 0.7}, "p_J": {"p*": 0.3, "p_J": 0.0}}
    assert exchange(mismatch, "p*", "p_J") == pytest.approx(-0.4)
    assert exchange(mismatch, "p_J", "p*") == pytest.approx(0.4)
    cast_by_D = {1: {"p*", "p_J", "p_LN"}, 2: {"p*", "p_J"}, 3: {"p*", "p_J", "p_LN"}}
    assert cast_present_at_every_D(cast_by_D) == {"p*", "p_J"}
