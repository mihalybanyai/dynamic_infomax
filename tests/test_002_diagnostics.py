"""Spec 002 tests: closed forms and diagnostics (P5, P6, P21, P22).

specs/002-foreign-q-prediction.md §3.2, §3.3, §4.5, §9 and §5.2 (T5, T6, T21, T22). Stubs
raise `NotImplementedError` until the implementation exists.
"""
from __future__ import annotations

import numpy as np
import pytest

from infomax.diagnostics import (
    beyond_cap,
    covered_fraction,
    failure_map_point,
    gaussian_kl_split,
    hypercone_jeffreys_mean,
    hypercone_jeffreys_mode,
    jeffreys_cone_loss,
    joint_width_ratio,
    mass_near,
    moment_matched_predictive,
    relevant_datum_divergence,
)
from infomax.jeffreys import build_jeffreys
from infomax.pref import build_uniform
from infomax.pstar import build_pstar
from infomax.qfamily import sample_nature
from infomax.score import per_state_redundancy, score_cell
from spec002_common import S_Q_TEST, agree_mc, cheap_model, cone_model


# ---------------------------------------------------------------------------
# P5 / T5 — the Gaussian split (3.3.1)
# ---------------------------------------------------------------------------


def test_t5_gaussian_kl_split_matches_numeric_kl():
    """T5: for random Gaussians, half the sum of (3.3.1)'s two terms matches a Monte-Carlo
    `D_KL(N_q || N_pi)`. Catches a sign or trace error in the decomposition."""
    rng = np.random.default_rng(20261180)
    m = 2
    for _ in range(5):
        mu_q, mu_pi = rng.normal(size=m), rng.normal(size=m)
        A, B = rng.normal(size=(m, m)), rng.normal(size=(m, m))
        S_q, S_pi = A @ A.T + 0.5 * np.eye(m), B @ B.T + 0.5 * np.eye(m)
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


# ---------------------------------------------------------------------------
# P6 / T6 — the hypercone deviation (9.2.2)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("D", [6, 11, 26])
def test_t6_hypercone_jeffreys_deviation(D):
    """T6: Jeffreys' posterior mean of `theta_1` at `x_1 = 10` (W = 50, noise 1, as A&M) lies
    toward the thick end, and its deviation matches `(D-1)/x_1` within `(D-1)^2/x_1^3`, the
    first neglected order (§9.2, m10). Computed deviations: 0.019, 0.077, 0.418."""
    x1, W = 10.0, 50.0
    mean = hypercone_jeffreys_mean(x1, D, W)
    assert mean > x1, "the pull is toward the thick end"
    assert abs((mean - x1) - (D - 1) / x1) <= (D - 1) ** 2 / x1**3


@pytest.mark.parametrize("D", [6, 11, 26])
def test_t6_hypercone_jeffreys_mode_is_the_exact_root(D):
    """T6(iii): the closed-form mode equals the positive root of
    `theta_1^2 - x_1 theta_1 - (D-1) = 0` (9.2.1)."""
    x1 = 10.0
    root = 0.5 * (x1 + np.sqrt(x1**2 + 4 * (D - 1)))
    np.testing.assert_allclose(hypercone_jeffreys_mode(x1, D), root, rtol=1e-12)


# ---------------------------------------------------------------------------
# P21 / T21 — the mass bound, the insurance inequality, Jeffreys' loss
# ---------------------------------------------------------------------------


def test_t21a_mass_bound():
    """T21(a): at sampled states, for every prior, `R_N^theta(pi) <= -log pi(A(theta)) + 1/2`
    (3.2.1). Both sides are recorded elsewhere; here only the bound is asserted, with a small
    Monte-Carlo slack. It cannot fail when correct; it catches a mis-normalised mixture or a
    wrong `sigma / sqrt(N)`."""
    rng = np.random.default_rng(20261181)
    model = cheap_model()
    priors = {"p*": build_pstar(model).prior, "p_J": build_jeffreys(model), "p_U": build_uniform(model)}
    theta = model.box.sample_uniform(30, rng)
    for name, prior in priors.items():
        loss = per_state_redundancy(prior, model, theta, rng=rng, n_x=256)
        bound = -np.log(mass_near(prior, model, theta)) + 0.5
        assert np.all(loss <= bound + 0.05), name


@pytest.mark.slow
@pytest.mark.parametrize("nature", [("nested", "thin"), ("nested", "thick"), ("stress", "interior")])
def test_t21b_insurance_inequality(nature):
    """T21(b): in the hypercone the two sides of (3.2.3) are ordered as stated on every
    nature: `R(p_J) - R(p*)` is at least the excess of Jeffreys' per-state loss over `C_N`
    outside its covered set, minus `C_N` times the nature's mass on that set."""
    rng = np.random.default_rng(20261182)
    model = cone_model(6, falloff=0.5)
    pstar = build_pstar(model)
    p_J = build_jeffreys(model)
    cell = score_cell(model, {"p*": pstar.prior, "p_J": p_J}, nature, S_q=S_Q_TEST, rng=rng)
    theta, _ = sample_nature(model, nature, 200, rng)
    loss_J = per_state_redundancy(p_J, model, theta, rng=rng, n_x=64)
    covered = loss_J <= pstar.capacity
    rhs = np.mean(np.where(covered, 0.0, loss_J - pstar.capacity)) - pstar.capacity * covered.mean()
    lhs = cell.R_mean["p_J"] - cell.R_mean["p*"]
    assert lhs >= rhs - 4 * np.hypot(cell.R_mcse["p_J"], cell.R_mcse["p*"])


@pytest.mark.parametrize("D", [6, 11])
def test_t21c_jeffreys_cone_loss_formula(D):
    """T21(c): in the hypercone, where `theta_1 >> D sigma / sqrt(N)`, the divergence between
    the laws of the relevant datum under `theta` and under `p_J` matches (3.2.2) with the
    correction of §9.5. At `D = 26` and `100` the agreement is only observed (§9.5, m14)."""
    theta1 = np.array([35.0, 40.0, 45.0])
    numeric = relevant_datum_divergence(theta1, D, W=50.0, sigma=1.0, N=1)
    formula = jeffreys_cone_loss(theta1, D, W=50.0, sigma=1.0, N=1, second_order=True)
    np.testing.assert_allclose(numeric, formula, rtol=1e-2)


# ---------------------------------------------------------------------------
# P22 / T22 — the diagnostics of §4.5
# ---------------------------------------------------------------------------


def test_t22a_split_terms_vanish_on_the_diagonal():
    """T22(a): in a prior's own world, both terms of (3.3.1) vanish for that prior: its
    moment-matched predictive is the matched one (§3.3, §4.5)."""
    rng = np.random.default_rng(20261183)
    model = cheap_model()
    p_U = build_uniform(model)
    xbar = model.y(model.box.sample_uniform(5, rng)) + model.sigma_eff * rng.standard_normal((5, model.m_out))
    for xb in xbar:
        mu, S = moment_matched_predictive(p_U, model, xb)
        shift, spread = gaussian_kl_split(mu, S, mu, S)
        assert abs(shift) <= 1e-12 and abs(spread) <= 1e-12


@pytest.mark.parametrize(
    "R, se, C_N, gap, expected",
    [(5.0, 0.1, 4.0, 0.2, True), (4.25, 0.1, 4.0, 0.2, False), (3.0, 0.1, 4.0, 0.2, False), (4.31, 0.1, 4.0, 0.2, True)],
)
def test_t22b_beyond_cap_label(R, se, C_N, gap, expected):
    """T22(b): a cell is beyond the cap exactly when `R - C_N` exceeds its Monte-Carlo error
    plus the candidate set's capacity gap (§3.7, §4.5, F5). No other mark is made."""
    assert beyond_cap(R, se, C_N, gap) is expected


def test_t22e_failure_map_coordinates():
    """§2.4, §4.5: a row's point on a prior's failure map is at breadth `floor / C_N` and at
    the best rival's mismatch, the smallest among the *other* priors that are away in the
    row (the row's own prior excluded), coloured by the signed gap to that rival."""
    mismatch = {"p_U": 0.0, "p*": 1.0, "p_J": 2.5, "p_LN": 0.4}
    pt = failure_map_point(mismatch, "p_J", own_prior="p_U", floor=1.0, capacity=4.0)
    assert pt.breadth == pytest.approx(0.25)
    assert pt.best_rival == pytest.approx(0.4)
    assert pt.gap_to_rival == pytest.approx(2.1)
    own = failure_map_point(mismatch, "p_U", own_prior="p_U", floor=1.0, capacity=4.0)
    assert own.best_rival == pytest.approx(0.4) and own.gap_to_rival == pytest.approx(-0.4)


@pytest.mark.slow
def test_t22c_covered_fraction_matches_the_interval():
    """T22(c): in the hypercone, `covered_J` from `K` draws matches the nature's mass on the
    `theta_1`-interval where Jeffreys' per-state loss is at most `C_N` (§3.2, §4.5)."""
    rng = np.random.default_rng(20261184)
    model = cone_model(6, falloff=0.5)
    C_N = build_pstar(model).capacity
    p_J = build_jeffreys(model)
    grid = np.column_stack([np.linspace(0.5, model.W, 200), np.full((200, 5), 0.5)])
    covered_theta1 = grid[per_state_redundancy(p_J, model, grid, rng=rng, n_x=256) <= C_N, 0]
    lo = covered_theta1.min() if covered_theta1.size else model.W
    nature = ("nested", "thick")
    theta, _ = sample_nature(model, nature, 20_000, rng)
    expected = np.mean(theta[:, 0] >= lo)
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
