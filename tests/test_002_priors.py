"""Spec 002 tests: building the priors (P3, P4, P7b, P11, P15, P16, P19, P23).

specs/002-foreign-q-prediction.md §4.2 and §5.2 (T3, T4, T7b, T11, T15, T16, T19, T23).
These check the constructions, never which prior wins (§2.4). Stubs raise
`NotImplementedError` until the implementation exists. Regenerated after the test
red-team (`tests/test_002_foreign_q_prediction-redteam.md`: F1, F2, F3, F9, F14, m1, m13).
"""
from __future__ import annotations

import math

import numpy as np
import pytest
import scipy.integrate
import scipy.optimize
import scipy.stats

from infomax.jeffreys import build_jeffreys
from infomax.models import build_model
from infomax.plat import build_plat, conditional_divergence
from infomax.plognormal import build_pln, build_pln_star
from infomax.pproj import build_pproj, mle_project, nml_log_normaliser
from infomax.pref import build_pref, build_uniform, ranking_coordinate
from infomax.pstar import build_pstar
from infomax.score import mutual_information, per_state_redundancy, score_cell
from spec002_common import (
    CHEAP_CELLS,
    CONE_BASE,
    CONE_BASE_TWIN,
    CURVATURE_CELL,
    D_SWEEP_GRID,
    EQUALIZER_SLACK,
    INFO_SLACK,
    MC_SIGMAS,
    S_Q_TEST,
    agree_mc,
    cheap_model,
    cheap_model_at,
    cone_model,
    log_time_from_xi,
)

TIMES = np.linspace(1.0, 5.0, 26)
W_CONE = 50.0
SIGMA_1D = W_CONE / 3.0
"""The 1-D cone of Fisher length 3 at `N = 1` (§5.4's 1-D bounded channel)."""


def _cone_1d(N: int):
    """The 1-D cone `y = theta_1` on `[0, 50]` at `sigma = 50/3` and budget `N`."""
    return cone_model(1, sigma=SIGMA_1D, N=N)


def _exp_decay_metric_parts(x1: float, x2: float, sigma: float = 0.1, D: int = 2):
    """`g_11, g_12, g_22` of exp-decay at `D = 2` in `xi`, written out from (1.2.1) with
    `J_t,mu = t xi_mu^(t-1) / D` (§9.3), independent of `Model.fim`."""
    a = TIMES * x1 ** (TIMES - 1) / D
    b = TIMES * x2 ** (TIMES - 1) / D
    return a @ a / sigma**2, a @ b / sigma**2, b @ b / sigma**2


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
# P4 / T4 — Jeffreys, and the uniform prior's absolute density
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("family", ["exp_decay", "hypercone"])
def test_t4_jeffreys_normalises(family):
    """T4: `p_J ∝ sqrt(det g)` integrates to one on `Theta` (checked against `p_U` by Monte
    Carlo: `E_U[p_J / p_U] = 1`), and its density follows `sqrt(det g)` (§4.2). `p_U`'s own
    density is pinned absolutely by `test_t4_uniform_density_is_absolute`."""
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
    """T4: in exp-decay the normaliser over the whole manifold is stable as the quadrature
    is refined. (Finiteness is not in question: in `xi`, `sqrt(det g)` is a bounded
    polynomial on a compact set; m1.)"""
    model = cheap_model(D=2)
    coarse = build_jeffreys(model, quadrature_points=200).log_normaliser
    fine = build_jeffreys(model, quadrature_points=400).log_normaliser
    assert np.isfinite(fine)
    assert abs(fine - coarse) <= 1e-3


def test_t4_jeffreys_normaliser_matches_an_independent_quadrature():
    """T4 (m1): at `D = 2` in exp-decay, `log V_g = log ∫ sqrt(det g) dxi` over the ordered
    triangle, by `scipy.integrate.dblquad` on the metric written out in the test, equals
    `build_jeffreys(...).log_normaliser`. Catches a quadrature that ignores its own
    refinement, which the convergence test cannot."""
    model = cheap_model(D=2)

    def sqrt_det(x1, x2):
        g11, g12, g22 = _exp_decay_metric_parts(x1, x2)
        return math.sqrt(max(g11 * g22 - g12 * g12, 0.0))

    V, _ = scipy.integrate.dblquad(lambda x1, x2: sqrt_det(x1, x2), 0.0, 1.0, 0.0, lambda x2: x2, epsabs=0, epsrel=1e-9)
    np.testing.assert_allclose(build_jeffreys(model).log_normaliser, np.log(V), atol=1e-4)


def test_t4_uniform_density_is_absolute():
    """T4 (F3): `p_U` is normalised absolutely, not only relative to itself: `log p_U = log D!`
    on exp-decay's ordered unit cube, whose volume is `1/D!`, and `-log W` in the cone. A
    `p_U`, `p_J` and `p_ref` off by one common factor (say, normalised over the unordered
    cube) pass every relative check and fail here."""
    rng = np.random.default_rng(20261147)
    for D in (2, 3):
        model = cheap_model(D=D)
        theta = model.box.sample_uniform(50, rng)
        np.testing.assert_allclose(build_uniform(model).log_density(theta), np.log(math.factorial(D)), atol=1e-12)
    cone = cone_model(4)
    theta = cone.box.sample_uniform(50, rng)
    np.testing.assert_allclose(build_uniform(cone).log_density(theta), -np.log(W_CONE), atol=1e-12)


@pytest.mark.slow
@pytest.mark.parametrize("D", [4, 5])
def test_t4_sampled_jeffreys_normaliser_matches_brute_force(D):
    """T4 (§5.2, OQ-13): from `D = 4`, exp-decay's `p_J` is sampled by adaptive importance
    sampling; its `log Z` over ordered `xi` agrees with brute force over `2e6` uniform ordered
    draws within three combined standard errors. Brute force: `log Z = log mean sqrt(det g)
    - log D!`. Catches a wrong Jacobian of the log-time coordinates or a lost `D!`."""
    import math

    from infomax.sampled import _log_sqrt_det_g

    model = cheap_model(D=D)
    p_J = build_jeffreys(model)
    assert hasattr(p_J, "refined_log_marginal"), "p_J should be the sampled prior from D = 4"
    rng = np.random.default_rng(20261205)
    lv = np.concatenate([_log_sqrt_det_g(model, np.sort(rng.uniform(size=(100_000, D)), axis=-1)) for _ in range(20)])
    r = np.exp(lv - lv.max())
    log_z = lv.max() + np.log(r.mean()) - math.lgamma(D + 1)
    se = r.std() / (r.mean() * np.sqrt(r.size))
    assert abs(p_J.log_normaliser - log_z) <= 3 * np.hypot(se, p_J.log_normaliser_se), (p_J.log_normaliser, log_z, se)


@pytest.mark.slow
def test_t4_pointwise_marginals_agree():
    """T4 (§5.2, §4.4): at `D = 5`, at a typical and a face-adjacent state, the per-point
    marginal's two variants (full and diagonal kernels) agree within 0.1 nats on the mean
    `log m` over 16 draws of `x` from the state. Catches a proposal whose density is
    mis-evaluated, since two different proposals then disagree."""
    model = cheap_model(D=5)
    p_J = build_jeffreys(model)
    rng = np.random.default_rng(20261206)
    typical = p_J.sample(1, rng)[0]
    face = np.sort(np.concatenate([[1e-4], rng.uniform(size=4)]))
    for state in (typical, face):
        y = model.y(state[None])[0]
        x = y + model.sigma_eff * rng.standard_normal((16, model.m_out))
        a, ess_a = p_J.refined_log_marginal(model, x, rng, kernel="full")
        b, ess_b = p_J.refined_log_marginal(model, x, rng, kernel="diagonal")
        assert abs(a.mean() - b.mean()) <= 0.1, (state, a.mean(), b.mean(), ess_a.min(), ess_b.min())


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
    within Monte-Carlo and solver tolerance (§4.2, OQ-1). The atomic path is the adaptive
    pool on the same solver."""
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


def test_t11_nml_normaliser_in_the_1d_cone():
    """T11 (F14): in the 1-D cone the NML normaliser has a closed form,
    `Z = 1/2 + W/(sigma sqrt(2 pi)) + 1/2`: each tail beyond an end contributes half a
    Gaussian, the slab between them `W/(sigma sqrt(2 pi))`. At `W/sigma = 3`, `Z = 2.197`.
    Any finite number passed the old check; this pins the value within its error."""
    model = _cone_1d(1)
    log_Z, se = nml_log_normaliser(model, np.random.default_rng(20261134))
    expected = np.log(1.0 + W_CONE / (SIGMA_1D * np.sqrt(2 * np.pi)))
    np.testing.assert_allclose(expected, np.log(2.197), atol=5e-4)
    assert abs(log_Z - expected) <= MC_SIGMAS * se + 1e-12


def test_t11_pproj_cloud_is_slab_and_spike_in_the_1d_cone():
    """T11 (F14): `p_proj` in the 1-D cone is Quinn's slab and spike: data beyond either end
    project onto it, so each end carries `1/(2Z) = 0.228` of the cloud, and the slab between
    is uniform (§3.4, §4.2). The cloud is weighted (importance sampling, OQ-6), so the
    ends' weighted fractions are checked within four binomial standard errors at the
    cloud's effective sample size, and the slab by a weighted KS statistic at that size. A
    `build_pproj` that returns draws of `p_U` has no mass at the ends and fails."""
    model = _cone_1d(1)
    cloud = build_pproj(model, np.random.default_rng(20261135))
    atoms, w, n_eff = cloud.atoms[:, 0], cloud.weights, cloud.ess
    Z = 1.0 + W_CONE / (SIGMA_1D * np.sqrt(2 * np.pi))
    for end in (0.0, W_CONE):
        p = w @ np.isclose(atoms, end, rtol=0, atol=1e-12)
        se = np.sqrt(p * (1 - p) / n_eff)
        assert abs(p - 1 / (2 * Z)) <= MC_SIGMAS * se, f"end {end}"
    inside = (atoms > 1e-12) & (atoms < W_CONE - 1e-12)
    xs, ws = atoms[inside], w[inside] / w[inside].sum()
    order = np.argsort(xs)
    ecdf = np.cumsum(ws[order])
    u = xs[order] / W_CONE
    ks = max(np.max(np.abs(ecdf - u)), np.max(np.abs(ecdf - ws[order] - u)))
    n_in = 1.0 / np.sum(ws**2)
    assert scipy.stats.kstwo.sf(ks, int(n_in)) > 1e-3


def test_t11_projection_maps_outside_data_to_the_endpoints():
    """T11 (F14): in the 1-D cone the maximum-likelihood state of data beyond either end is
    that end, and of data between them the data itself (§4.2)."""
    model = _cone_1d(1)
    x = np.array([[-30.0], [-0.5], [10.0], [49.0], [50.5], [80.0]])
    np.testing.assert_allclose(mle_project(model, x)[:, 0], [0.0, 0.0, 10.0, 49.0, 50.0, 50.0], atol=1e-8)


@pytest.mark.parametrize("D", D_SWEEP_GRID)
def test_t11_pproj_projection_recovers_mle(D):
    """T11: the projection recovers a known `theta-hat` from `x` placed near the manifold,
    over the `D`-sweep (§5.4).

    Data a hundredth of a noise unit from `y(theta)` have their maximum-likelihood state
    within a small fraction of the noise of `theta`'s prediction."""
    rng = np.random.default_rng(20261136)
    model = cheap_model(D=D)
    theta = np.sort(rng.uniform(0.2, 0.8, size=(10, D)), axis=-1)
    x = model.y(theta) + 0.01 * model.sigma_eff * rng.standard_normal((10, model.m_out))
    theta_hat = mle_project(model, x)
    dist = np.linalg.norm(model.y(theta_hat) - model.y(theta), axis=-1) / model.sigma_eff
    assert np.max(dist) <= 0.05


def test_t11_projection_of_data_beyond_the_manifold_lands_on_a_face():
    """T11 (F14): data outside the manifold project onto its boundary, inside the ordered
    `Theta` (§4.2). Every `y_t` lies in `[0, 1]`, so `x = 1.2` at every time projects to
    `xi = (1, 1)` and `x = -0.2` to `xi = (0, 0)`; data far off at random land sorted and
    in `[0, 1]^2`. An unconstrained fit that leaves `[0, 1]`, or returns unsorted `xi`,
    fails."""
    rng = np.random.default_rng(20261148)
    model = cheap_model(D=2)
    np.testing.assert_allclose(mle_project(model, np.full((1, 26), 1.2))[0], [1.0, 1.0], atol=1e-6)
    np.testing.assert_allclose(mle_project(model, np.full((1, 26), -0.2))[0], [0.0, 0.0], atol=1e-6)
    theta = model.box.sample_uniform(20, rng)
    x = model.y(theta) + 5 * model.sigma_eff * rng.standard_normal((20, model.m_out))
    theta_hat = mle_project(model, x)
    assert model.box.contains(theta_hat).all()
    assert np.all(np.diff(theta_hat, axis=-1) >= 0)


@pytest.mark.parametrize("D", D_SWEEP_GRID)
def test_t11_pproj_information_below_capacity(D):
    """T11: `I_{p_proj} <= I_{p*} = C_N`, since `p*` maximises the information (§4.2, m11),
    over the `D`-sweep (§5.4). Any prior passes this given a correct estimator; the
    slab-and-spike test above pins `p_proj`'s law."""
    rng = np.random.default_rng(20261137)
    model = cheap_model(D=D)
    cap = build_pstar(model).capacity
    i_proj = mutual_information(build_pproj(model, rng), model, rng=rng)
    assert i_proj <= cap + INFO_SLACK


# ---------------------------------------------------------------------------
# P15 / T15 — p_ref
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("cell", [CONE_BASE, CONE_BASE_TWIN], ids=["N=1", "twin"])
def test_t15a_cone_schur_complement(cell):
    """T15(a): in the hypercone the information left for `theta_1` once the cross-section is
    accounted for is `N / sigma^2` everywhere ([^3-schur]), with `sigma` and `N` from the
    cell, at `N = 1` and at the twin `N = 4` (F9)."""
    rng = np.random.default_rng(20261138)
    model = build_model(D=5, **cell)
    for theta in model.box.sample_uniform(20, rng):
        if theta[0] < 1.0:
            continue
        g = model.fim(theta)
        schur = g[0, 0] - g[0, 1:] @ np.linalg.solve(g[1:, 1:], g[1:, 0])
        np.testing.assert_allclose(schur, cell["N"] / cell["sigma"] ** 2, rtol=1e-8)


@pytest.mark.parametrize("taper", [1.0, 0.0])
def test_t15b_c_cone_pref_is_uniform(taper):
    """T15(b), (c): in the cone `p_ref = p_U` pointwise; with the taper off also `= p_J` (§3.5)."""
    rng = np.random.default_rng(20261157)
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


def _berger_bernardo_log_density(x1: float, x2: float, ranking: str) -> float:
    """`log p_ref` at `D = 2` in exp-decay, up to a constant, from the formula of
    `[^3-schur]` by nested 1-D quadratures. Slowest first ranks `xi_2` (`psi`) with
    `lambda = xi_1` on `[0, psi]`; fastest first ranks `xi_1` with `lambda = xi_2` on
    `[psi, 1]`. `g_11` depends on `xi_1` alone and `g_22` on `xi_2` alone, so the conditional
    Jeffreys factor is one-dimensional."""
    quad = lambda f, a, b: scipy.integrate.quad(f, a, b, limit=400, epsabs=1e-10, epsrel=1e-8)[0]
    if ranking == "slowest":
        psi, lam = x2, x1
        root_g = lambda t: math.sqrt(_exp_decay_metric_parts(t, psi)[0])
        lo, hi = 0.0, psi

        def half_log_schur(t):
            g11, g12, g22 = _exp_decay_metric_parts(t, psi)
            return 0.5 * math.log(max(g22 - g12 * g12 / g11, 1e-300))
    else:
        psi, lam = x1, x2
        root_g = lambda t: math.sqrt(_exp_decay_metric_parts(psi, t)[2])
        lo, hi = psi, 1.0

        def half_log_schur(t):
            g11, g12, g22 = _exp_decay_metric_parts(psi, t)
            return 0.5 * math.log(max(g11 - g12 * g12 / g22, 1e-300))

    norm = quad(root_g, lo, hi)
    log_marginal = quad(lambda t: root_g(t) / norm * half_log_schur(t), lo, hi)
    return math.log(root_g(lam)) - math.log(norm) + log_marginal


@pytest.mark.parametrize("ranking", ["slowest", "fastest"])
def test_t15d_exp_decay_pref_matches_the_berger_bernardo_formula(ranking):
    """T15(d) (F3): at `D = 2` each ranking's `p_ref` follows the Berger–Bernardo formula of
    `[^3-schur]`, computed in the test by nested quadratures, at a few states. Log-density
    differences are compared, so the normaliser (pinned by the test above and by `p_U`'s
    absolute density) drops out. Any normalised density, Jeffreys among them, passed the
    normalise-and-differ check; this also pins which ranking is which. Tolerance 5e-3
    (auto-chosen)."""
    model = cheap_model(D=2)
    pts = np.array([[0.2, 0.6], [0.4, 0.8], [0.5, 0.9], [0.3, 0.5], [0.1, 0.95]])
    want = np.array([_berger_bernardo_log_density(a, b, ranking) for a, b in pts])
    got = build_pref(model, ranking).log_density(pts)
    np.testing.assert_allclose(got - got[0], want - want[0], atol=5e-3)


def test_t15e_stiffest_ranking_ignores_transversal():
    """T15(e): at `D = 2` the stiffest-first `p_ref` does not depend on the transversal from
    which its coordinate is traced (`[^4-stiff]`: a reference prior ignores how its
    interest parameter is labelled), while the traced coordinate itself does (F3), so a
    build that ignores `transversal` fails."""
    rng = np.random.default_rng(20261140)
    model = cheap_model(D=2)
    theta = model.box.sample_uniform(200, rng)
    t_a = np.array([[0.1, 0.9], [0.9, 0.95]])
    t_b = np.array([[0.05, 0.5], [0.5, 0.99]])
    a = build_pref(model, "stiffest", transversal=t_a)
    b = build_pref(model, "stiffest", transversal=t_b)
    np.testing.assert_allclose(a.log_density(theta), b.log_density(theta), rtol=1e-3)
    psi_a = ranking_coordinate(model, "stiffest", theta, transversal=t_a)
    psi_b = ranking_coordinate(model, "stiffest", theta, transversal=t_b)
    assert np.max(np.abs(psi_a - psi_b)) > 1e-3, "the traced coordinate ignores the transversal"


def test_t15f_cone_pref_with_curvature():
    """T15 (F1): with the curvature knob on, the cone's `p_ref` comes from the Berger–Bernardo
    formula by quadrature (§4.2). It normalises, and on cross-sections that miss the warped
    ball (`theta_1 < W - rho`) it is proportional to `p_U` with one constant ratio: the
    geometry there is the unwarped cone's, but the normaliser is not."""
    rng = np.random.default_rng(20261141)
    model = build_model(D=3, **CURVATURE_CELL, curvature=0.5)
    rho = 5 * CURVATURE_CELL["sigma"] / np.sqrt(CURVATURE_CELL["N"])
    p_ref, p_U = build_pref(model), build_uniform(model)
    theta = model.box.sample_uniform(200_000, rng)
    ratio = np.exp(p_ref.log_density(theta) - p_U.log_density(theta))
    assert abs(ratio.mean() - 1.0) <= 4 * ratio.std() / np.sqrt(ratio.size)
    away = theta[theta[:, 0] < CURVATURE_CELL["W"] - rho][:500]
    log_ratio = p_ref.log_density(away) - p_U.log_density(away)
    np.testing.assert_allclose(log_ratio, log_ratio[0], atol=1e-6)


# ---------------------------------------------------------------------------
# P16 / T16 — p_lat
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("where, N", [("cone-1d", 1), ("cone-1d", 4), ("cheap", 1)])
def test_t16a_b_plat_conditional_equalizer_and_bounds(where, N):
    """T16(a), (b): at convergence `f^(N+1) - f^(N)` is within tolerance of the conditional
    capacity on `supp p_lat` and below it elsewhere; the two-sided bound of §4.2 closes.
    Run where §5.4 puts it (F2): the 1-D bounded channel at `N = 1` and `N = 4`, where
    `sigma_eff != sigma`, and the cheap cell. These compare the build with numbers it
    reports; T16(d) and T16(e) compare it with independent ones."""
    model = _cone_1d(N) if where == "cone-1d" else cheap_model(N=N)
    res = build_plat(model)
    on_support = conditional_divergence(res, model, res.prior.atoms[res.prior.weights > 1e-8])
    assert np.max(np.abs(on_support - res.conditional_capacity)) <= EQUALIZER_SLACK
    rng = np.random.default_rng(20261142)
    off = conditional_divergence(res, model, model.box.sample_uniform(256, rng))
    assert np.max(off) <= res.conditional_capacity + EQUALIZER_SLACK
    assert res.upper_bound - res.lower_bound <= 1e-6 + 1e-12
    assert res.lower_bound <= res.conditional_capacity <= res.upper_bound


@pytest.mark.parametrize("where", ["cone-1d", "cheap"])
def test_t16c_plat_at_zero_budget_is_pstar(where):
    """T16(c): at `N = 0`, `p_lat` maximises `I(Theta; X_1)`, so it equals `p*` at budget 1
    on the same candidate set. Catches swapped noise levels. It cannot see the `f^(N)` term,
    which is absent at `N = 0`; T16(d), (e) do."""
    model1 = _cone_1d(1) if where == "cone-1d" else cheap_model(N=1)
    model0 = _cone_1d(0) if where == "cone-1d" else cheap_model(N=0)
    pstar = build_pstar(model1)
    plat0 = build_plat(model0, candidates=pstar.candidates)
    np.testing.assert_allclose(plat0.prior.weights, pstar.masses, atol=1e-4)


@pytest.mark.parametrize("N", [1, 4])
def test_t16d_conditional_capacity_is_a_difference_of_informations(N):
    """T16(d) (F2): the conditional capacity equals `I(Theta; X_{1:N+1}) - I(Theta; X_{1:N})`
    of `p_lat`, each information computed by `mutual_information` at its own budget, and
    that difference is at least as large as `p*`'s and `p_U`'s (§4.2). A build that uses one
    noise for both terms reports zero everywhere and fails."""
    model_N, model_N1 = _cone_1d(N), _cone_1d(N + 1)
    res = build_plat(model_N)
    rng = lambda: np.random.default_rng(20261143)

    def gain(prior):
        return mutual_information(prior, model_N1, rng=rng()) - mutual_information(prior, model_N, rng=rng())

    np.testing.assert_allclose(gain(res.prior), res.conditional_capacity, atol=INFO_SLACK)
    assert res.conditional_capacity > 1e-3
    for other in (build_pstar(model_N).prior, build_uniform(model_N)):
        assert gain(other) <= res.conditional_capacity + INFO_SLACK


def _information_on_grid(weights: np.ndarray, atoms: np.ndarray, s: float) -> float:
    """`I(Theta; X)` in nats for a 1-D Gaussian channel of noise `s` and a discrete prior:
    the mixture's entropy, by a fine trapezoid rule, minus the noise's."""
    x = np.linspace(atoms.min() - 10 * s, atoms.max() + 10 * s, 40001)
    dens = (weights[:, None] * np.exp(-0.5 * ((x[None, :] - atoms[:, None]) / s) ** 2)).sum(0) / (s * np.sqrt(2 * np.pi))
    h = -np.trapezoid(np.where(dens > 0, dens * np.log(np.maximum(dens, 1e-300)), 0.0), x)
    return float(h - 0.5 * np.log(2 * np.pi * np.e * s**2))


@pytest.mark.parametrize("n_points", [3, 5])
@pytest.mark.parametrize("N", [1, 4])
def test_t16e_gaussian_plat_matches_a_direct_maximisation(N, n_points):
    """T16(e) (F2): a reference for the Gaussian build. In the 1-D cone, on a grid of 3 or 5
    states, the test maximises `I(Theta; Xbar_{N+1}) - I(Theta; Xbar_N)` over the simplex
    with scipy, each information by 1-D quadrature at noise `sigma/sqrt(n)`; the objective
    is concave in the weights [read: Komaki 2011 §4], so the optimum is global. `build_plat`
    on the same grid gives the same weights to `1e-4`."""
    atoms = np.linspace(0.0, W_CONE, n_points)
    s_N, s_N1 = SIGMA_1D / np.sqrt(N), SIGMA_1D / np.sqrt(N + 1)

    def neg_gain(w):
        w = np.clip(w, 0.0, None)
        w = w / w.sum()
        return -(_information_on_grid(w, atoms, s_N1) - _information_on_grid(w, atoms, s_N))

    out = scipy.optimize.minimize(
        neg_gain,
        np.full(n_points, 1.0 / n_points),
        method="SLSQP",
        bounds=[(0.0, 1.0)] * n_points,
        constraints=[{"type": "eq", "fun": lambda w: w.sum() - 1.0}],
        options={"ftol": 1e-14, "maxiter": 500},
    )
    assert out.success
    res = build_plat(_cone_1d(N), candidates=atoms[:, None], tol=1e-10)
    order = np.argsort(res.prior.atoms[:, 0])
    np.testing.assert_allclose(res.prior.atoms[order, 0], atoms, atol=1e-12)
    np.testing.assert_allclose(res.prior.weights[order], out.x / out.x.sum(), atol=1e-4)
    np.testing.assert_allclose(res.conditional_capacity, -out.fun, atol=1e-6)


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
    rng = np.random.default_rng(20261144)
    p_U = build_uniform(model_M)
    cell = score_cell(model_M, {"mis": mis.prior, "own": own.prior}, ("own", p_U), S_q=S_Q_TEST, rng=rng)
    np.testing.assert_allclose(cell.R_mean["mis"], cell.R_mean["own"], atol=1e-10)


def test_t19c_misbudget_worst_case_exceeds_capacity():
    """T19(c): in the 1-D bounded channel of Fisher length 3 at `N = 1` (the note's §3.1),
    the worst-case per-state redundancy of `p*_M` at budget `N` is at least `C_N`, with
    equality only at `M = N`. Only `N = 1` lies in the two-atom regime (m12)."""
    grid = np.linspace(0.0, W_CONE, 401)[:, None]
    budgets = (1, 4, 16, 64)
    for N in budgets:
        model = _cone_1d(N)
        C_N = build_pstar(model).capacity
        for M in budgets:
            prior = build_pstar(model, budget=M).prior
            worst = np.max(per_state_redundancy(prior, model, grid))
            if M == N:
                np.testing.assert_allclose(worst, C_N, atol=EQUALIZER_SLACK)
            else:
                assert worst > C_N + EQUALIZER_SLACK, f"N={N}, M={M}"


# ---------------------------------------------------------------------------
# P23 / T23 — p_LN and p_LN^*
# ---------------------------------------------------------------------------


def test_t23_lognormal_is_as_defined():
    """§4.2 (F3): `p_LN` is A&M's prior: each log decay time `N(0, 1)`, sorted. At `D = 2` its
    draws, mapped to log decay times, follow the order statistics of two standard normals
    (CDFs `1 - (1 - Phi)^2` and `Phi^2`), and its density in `xi` is the change of
    variables, `log 2 + sum_mu [log phi(theta_mu) - log xi_mu - log(-log xi_mu)]`. A
    log-normal in `xi`, or a density without the factor `d theta / d xi`, fails."""
    rng = np.random.default_rng(20261145)
    model = cheap_model(D=2)
    p_LN = build_pln(model)
    theta = log_time_from_xi(p_LN.sample(4000, rng))
    Phi = scipy.stats.norm.cdf
    assert scipy.stats.kstest(theta[:, 0], lambda t: 1 - (1 - Phi(t)) ** 2).pvalue > 1e-3
    assert scipy.stats.kstest(theta[:, 1], lambda t: Phi(t) ** 2).pvalue > 1e-3
    xi = np.array([[0.1, 0.3], [0.2, 0.9], [0.5, 0.6], [0.05, 0.99]])
    t = log_time_from_xi(xi)
    want = np.log(2.0) + (scipy.stats.norm.logpdf(t) - np.log(xi) - np.log(-np.log(xi))).sum(-1)
    np.testing.assert_allclose(p_LN.log_density(xi), want, atol=1e-8)


@pytest.mark.parametrize("cell", list(CHEAP_CELLS.values()), ids=list(CHEAP_CELLS))
def test_t23_tuned_lognormal_information_order(cell):
    """T23(a): `I_{p_LN} <= I_{p_LN^*} <= C_N` (§4.2), at the cheap cell and its twin (F9).
    The search must also move: under common random numbers over five seeds, the information
    rises from A&M's `(0, 1)` by more than four standard errors (m13). That `(0, 1)` is not
    already a stationary point at this cell is a [guess], settled by the first run."""
    model = cheap_model_at(cell)
    tuned = build_pln_star(model, np.random.default_rng(20261210))
    rises = []
    for seed in (20261211, 20261212, 20261213, 20261214, 20261215):
        i_ln = mutual_information(build_pln(model), model, rng=np.random.default_rng(seed))
        i_star = mutual_information(tuned.prior, model, rng=np.random.default_rng(seed))
        assert i_ln <= i_star + INFO_SLACK
        rises.append(i_star - i_ln)
    rises = np.array(rises)
    assert rises.mean() > MC_SIGMAS * rises.std(ddof=1) / np.sqrt(rises.size), "the search did not move"
    assert tuned.information <= build_pstar(model).capacity + INFO_SLACK


@pytest.mark.parametrize("cell", list(CHEAP_CELLS.values()), ids=list(CHEAP_CELLS))
def test_t23_tuned_lognormal_is_a_local_maximum(cell):
    """T23(b): at the returned `(theta_bar, tau)`, `I` does not increase along a small step in
    either parameter (common random numbers), at the cheap cell and its twin (F9). Catches
    `I` estimated at the wrong noise."""
    model = cheap_model_at(cell)
    tuned = build_pln_star(model, np.random.default_rng(20261216))

    def info(theta_bar, tau):
        return mutual_information(build_pln(model, theta_bar, tau), model, rng=np.random.default_rng(20261217))

    best = info(tuned.theta_bar, tuned.tau)
    for d_bar, d_tau in ((0.1, 0), (-0.1, 0), (0, 0.1), (0, -0.1)):
        assert info(tuned.theta_bar + d_bar, tuned.tau + d_tau) <= best + INFO_SLACK
