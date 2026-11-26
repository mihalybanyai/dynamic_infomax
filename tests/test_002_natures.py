"""Spec 002 tests: the natures (property P14; test T14).

specs/002-foreign-q-prediction.md §2.3, §4.3 and §5.2 (T14): round robin, nested natures
(question 3) and stress natures, their laws, labels and floors, and `q̄`. Stubs raise
`NotImplementedError` until the implementation exists. Regenerated after the test
red-team (`tests/test_002_foreign_q_prediction-redteam.md`: F3, F4, F15, m4, m5, m6).
"""
from __future__ import annotations

import numpy as np
import pytest
import scipy.stats

from infomax.jeffreys import build_jeffreys
from infomax.models import build_model, submodel
from infomax.plognormal import build_pln, build_pln_star
from infomax.pref import build_pref, build_uniform
from infomax.qfamily import D_MAX, build_qbar, cell_rows, nature_log_marginal, sample_nature, submodel_floor
from infomax.score import score_cell
from spec002_common import (
    CURVATURE_CELL,
    MC_SIGMAS,
    PRODUCT_LAWS,
    build_cast,
    cheap_model,
    cone_model,
    log_mean_exp_with_error,
    log_time_from_xi,
    per_rate_law,
    xi_from_log_time,
)


def _assert_independent_uniform_cross_section(cross: np.ndarray) -> None:
    """Each cross-section coordinate is uniform on `[0, 1]` (KS, Bonferroni over the
    coordinates) and no two are correlated beyond four standard errors (m4). Pooling the
    coordinates, as before, passed draws with every coordinate equal."""
    n, k = cross.shape
    for j in range(k):
        assert scipy.stats.kstest(cross[:, j], scipy.stats.uniform(0, 1).cdf).pvalue > 1e-3 / k, j
    if k > 1:
        corr = np.corrcoef(cross, rowvar=False)
        assert np.max(np.abs(corr[np.triu_indices(k, 1)])) <= 4 / np.sqrt(n)


# ---------------------------------------------------------------------------
# T14(a) — the round robin's samplers
# ---------------------------------------------------------------------------


def test_t14a_round_robin_draws_come_from_the_prior():
    """T14: a round-robin row draws from its prior's own sampler, under the cell's seed, and
    every draw carries one label per nature, different between natures (§4.3, §6.3; m5)."""
    model = cheap_model()
    p_U, p_J = build_uniform(model), build_jeffreys(model)
    theta, labels = sample_nature(model, ("own", p_U), 500, np.random.default_rng(20261150))
    np.testing.assert_array_equal(theta, p_U.sample(500, np.random.default_rng(20261150)))
    assert labels.shape == (500,) and len(set(labels)) == 1
    _, labels_J = sample_nature(model, ("own", p_J), 10, np.random.default_rng(20261157))
    _, labels_few = sample_nature(model, ("nested", "few_rates"), 10, np.random.default_rng(20261158))
    assert len({labels[0], labels_J[0], labels_few[0]}) == 3, "two natures share a label"


def _continuous_prior(model, name: str):
    """The cheap cell's continuous priors by name (§2.2)."""
    if name == "p_U":
        return build_uniform(model)
    if name == "p_J":
        return build_jeffreys(model)
    if name == "p_LN":
        return build_pln(model)
    if name == "p_LN^*":
        return build_pln_star(model, np.random.default_rng(20261159)).prior
    return build_pref(model, name.removeprefix("p_ref[").removesuffix("]"))


@pytest.mark.parametrize(
    "name", ["p_U", "p_J", "p_LN", "p_LN^*", "p_ref[slowest]", "p_ref[fastest]", "p_ref[stiffest]"]
)
def test_t14a_samplers_match_their_densities(name):
    """T14 (F3): at the cheap cell each continuous prior's sampler, which draws its
    round-robin row, follows its own density: a KS test of the draws' `xi_1`. A sampler that
    drifts from its own mixture is otherwise seen only by T20, and only when the drift moves
    it toward another prior. For the product laws, `log_density` equals the closed-form
    `log 2 + log h(xi_1) + log h(xi_2)` pointwise, and `xi_1`, the smaller of two i.i.d.
    rates, has the CDF `1 - (1 - H)^2` (`per_rate_law`). A midpoint grid misses 3% and 9%
    of the log-normals' mass, in their integrable spike at `xi -> 0` (MB, 2026-11-26). For
    the other priors, the reference is the marginal of `log_density`, integrated over
    `xi_2 >= xi_1` on a fine midpoint grid of the ordered triangle."""
    model = cheap_model(D=2)
    prior = _continuous_prior(model, name)
    draws = prior.sample(4000, np.random.default_rng(20261160))[:, 0]
    if name in PRODUCT_LAWS:
        H, log_h = per_rate_law(name, prior)
        xi = np.array([[1e-4, 0.5], [0.05, 0.99], [0.1, 0.3], [0.2, 0.9], [0.5, 0.6]])
        np.testing.assert_allclose(prior.log_density(xi), np.log(2.0) + log_h(xi).sum(-1), atol=1e-8)
        assert scipy.stats.kstest(draws, lambda x: 1.0 - (1.0 - H(x)) ** 2).pvalue > 1e-3
    else:
        n = 600
        g = (np.arange(n) + 0.5) / n
        a, b = np.meshgrid(g, g, indexing="ij")
        keep = a <= b
        dens = np.zeros((n, n))
        dens[keep] = np.exp(prior.log_density(np.column_stack([a[keep], b[keep]])))
        marginal = dens.sum(axis=1) / n
        edges = np.linspace(0.0, 1.0, n + 1)
        cdf = np.concatenate([[0.0], np.cumsum(marginal) / n])
        np.testing.assert_allclose(cdf[-1], 1.0, atol=5e-3)
        assert scipy.stats.kstest(draws, lambda x: np.interp(x, edges, cdf / cdf[-1])).pvalue > 1e-3


# ---------------------------------------------------------------------------
# T14(b)–(d) — nested natures
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("half, lo, hi", [("thin", 0.0, 25.0), ("thick", 25.0, 50.0)])
def test_t14b_nested_cone_laws(half, lo, hi):
    """T14: a nested hypercone nature lives at `D_max = 26` with fall-off below 1: `theta_1`
    uniform on its half, each cross-section coordinate uniform on `[0, 1]` and independent
    of the others (§2.3, §4.3; m4)."""
    rng = np.random.default_rng(20261151)
    model_max = cone_model(D_MAX, falloff=0.5)
    theta, _ = sample_nature(model_max, ("nested", half), 4000, rng)
    assert theta.shape == (4000, D_MAX)
    assert scipy.stats.kstest(theta[:, 0], scipy.stats.uniform(lo, hi - lo).cdf).pvalue > 1e-3
    _assert_independent_uniform_cross_section(theta[:, 1:])


def test_t14c_agent_fixes_ignored_coordinates_at_centre():
    """T14: the agent of dimension `D` frees the first `D` coordinates and fixes the rest at
    `1/2`, the box's centre; its predictions live in the same data space (§2.3, §4.3)."""
    rng = np.random.default_rng(20261152)
    model_max = cone_model(D_MAX, falloff=0.5)
    agent = submodel(model_max, 3)
    free = agent.box.sample_uniform(20, rng)
    full = np.concatenate([free, np.full((20, D_MAX - 3), 0.5)], axis=-1)
    np.testing.assert_allclose(agent.y(free), model_max.y(full), rtol=1e-14)
    assert agent.m_out == model_max.m_out


def test_t14d_few_rates_share_one_rate_in_the_window():
    """T14: the few-rates nature at `D_0 = 1` gives every component the same rate, with the
    log decay time uniform over the window `[0, log 5]` (§4.3, OQ-2)."""
    rng = np.random.default_rng(20261153)
    model = cheap_model(D=4)
    xi, _ = sample_nature(model, ("nested", "few_rates"), 3000, rng)
    np.testing.assert_allclose(xi, xi[:, :1].repeat(4, axis=1), rtol=0, atol=0)
    log_time = log_time_from_xi(xi[:, 0])
    assert scipy.stats.kstest(log_time, scipy.stats.uniform(0, np.log(5)).cdf).pvalue > 1e-3


# ---------------------------------------------------------------------------
# T14(e) — stress natures
# ---------------------------------------------------------------------------


def _vertex_face_pieces(W: float, phi: float, rho: float, n: int = 2000):
    """The `theta`-area and the distances from `v` of the three face pieces within `rho` of
    `v` at `D = 3` (§4.3), on a fine midpoint grid of each face's own coordinates. The warp
    keeps distances from `v`, so the pieces are those of the unwarped cone."""
    s = (np.arange(n) + 0.5) / n
    pieces = {}
    t2, t3 = np.meshgrid(s, s, indexing="ij")  # base face theta_1 = W, where r = 1
    u = np.sqrt(t2**2 + (phi * t3) ** 2)
    pieces["base"] = (np.sum(u <= rho) / n**2, np.sort(u[u <= rho]))
    t1 = W - rho * s  # only theta_1 >= W - rho can lie within rho of v
    a, b = np.meshgrid(t1, s, indexing="ij")
    for face, u in (
        ("theta_2=0", np.sqrt((W - a) ** 2 + (a * phi * b / W) ** 2)),
        ("theta_3=0", np.sqrt((W - a) ** 2 + (a * b / W) ** 2)),
    ):
        pieces[face] = (np.sum(u <= rho) * rho / n**2, np.sort(u[u <= rho]))
    return pieces


def test_t14e_vertex_nature_lies_on_faces_near_v():
    """T14: every draw of the sharpened-vertex nature lies on a face that meets the warped
    vertex `v` and within `rho = 5 sigma_eff` of it in prediction space (§4.3)."""
    rng = np.random.default_rng(20261154)
    model = build_model(D=3, **CURVATURE_CELL, curvature=0.5)
    theta, _ = sample_nature(model, ("stress", "vertex"), 2000, rng)
    v = np.array([model.W, 0.0, 0.0])
    on_face = np.isclose(theta[:, 0], model.W) | np.isclose(theta[:, 1:], 0.0).any(axis=1)
    assert on_face.all()
    assert np.all(np.linalg.norm(model.y(theta) - v, axis=-1) <= 5 * model.sigma_eff + 1e-12)


def test_t14e_vertex_nature_is_uniform_by_area():
    """T14 (F15): the sharpened-vertex nature is uniform by area in `theta` on its three face
    pieces (§4.3): each face's share of the draws matches its share of the area (chi-squared
    test), and on each face the distance from `v` follows its law under area-uniform
    sampling (KS). A sampler that returns `v` every time, or uses one face only, fails."""
    W, phi = CURVATURE_CELL["W"], CURVATURE_CELL["falloff"]
    rho = 5 * CURVATURE_CELL["sigma"] / np.sqrt(CURVATURE_CELL["N"])
    model = build_model(D=3, **CURVATURE_CELL, curvature=0.5)
    theta, _ = sample_nature(model, ("stress", "vertex"), 6000, np.random.default_rng(20261161))
    u = np.linalg.norm(model.y(theta) - np.array([W, 0.0, 0.0]), axis=-1)
    on_base = np.isclose(theta[:, 0], W)
    on_t2 = ~on_base & np.isclose(theta[:, 1], 0.0)
    on_t3 = ~on_base & ~on_t2 & np.isclose(theta[:, 2], 0.0)
    pieces = _vertex_face_pieces(W, phi, rho)
    masks = {"base": on_base, "theta_2=0": on_t2, "theta_3=0": on_t3}
    areas = np.array([pieces[f][0] for f in masks])
    observed = np.array([masks[f].sum() for f in masks])
    assert observed.sum() == len(theta)
    assert scipy.stats.chisquare(observed, areas / areas.sum() * observed.sum()).pvalue > 1e-3
    for face, mask in masks.items():
        law = pieces[face][1]
        cdf = lambda x, law=law: np.searchsorted(law, x, side="right") / law.size
        assert scipy.stats.kstest(u[mask], cdf).pvalue > 1e-3, face


def test_t14e_interior_nature_is_truncated_normal():
    """T14: the smooth interior's `theta_1` is normal with mean `W/2` and standard deviation
    `7.5 sigma_eff`, truncated to `[0, W]`; each cross-section coordinate is uniform and
    independent of the others (§4.3; m4)."""
    rng = np.random.default_rng(20261155)
    model = cone_model(4)
    theta, _ = sample_nature(model, ("stress", "interior"), 5000, rng)
    s = 7.5 * model.sigma_eff
    law = scipy.stats.truncnorm((0 - model.W / 2) / s, (model.W - model.W / 2) / s, loc=model.W / 2, scale=s)
    assert scipy.stats.kstest(theta[:, 0], law.cdf).pvalue > 1e-3
    _assert_independent_uniform_cross_section(theta[:, 1:])


# ---------------------------------------------------------------------------
# T14(f) — q̄ and a cell's rows
# ---------------------------------------------------------------------------


def test_t14f_qbar_is_the_average_of_the_rows():
    """T14: `q̄`'s data marginal is the equal-weight average of the rows' marginals (§2.5,
    §4.2), and the cell's own list of rows leaves `q̄` out (m6): it is a ceiling, not a
    nature."""
    rng = np.random.default_rng(20261156)
    model = cheap_model()
    rows = [("own", build_uniform(model)), ("nested", "few_rates")]
    qbar = build_qbar(rows)
    xbar = model.y(model.box.sample_uniform(50, rng)) + model.sigma_eff * rng.standard_normal((50, model.m_out))
    each = np.stack([nature_log_marginal(model, row, xbar) for row in rows])
    expected = np.logaddexp.reduce(each, axis=0) - np.log(len(rows))
    np.testing.assert_allclose(qbar.log_marginal(model, xbar), expected, rtol=1e-10)
    cast = build_cast(model, np.random.default_rng(20261162))
    listed = cell_rows(model, {**cast, "q̄": qbar})
    assert all(not (kind == "own" and arg is qbar) for kind, arg in listed), "q̄ is listed as a row"
    owns = {id(arg) for kind, arg in listed if kind == "own"}
    assert owns == {id(prior) for prior in cast.values()}, "every prior of the cast has its own world"


# ---------------------------------------------------------------------------
# T14(g)–(i) — question 3's floors and scoring (F4)
# ---------------------------------------------------------------------------


def _draw_nature_in_the_test(name: str, n: int, rng: np.random.Generator):
    """`theta ~ q` drawn in the test from §4.3's laws, independent of `sample_nature`, with
    the model the nature lives in."""
    if name in ("thin", "thick"):
        model = cone_model(D_MAX, falloff=0.5)
        lo = 0.0 if name == "thin" else model.W / 2
        theta = np.column_stack([rng.uniform(lo, lo + model.W / 2, n), rng.uniform(0, 1, (n, D_MAX - 1))])
        return model, ("nested", name), theta
    if name == "few_rates":
        model = cheap_model(D=2)
        xi = xi_from_log_time(rng.uniform(0.0, np.log(5.0), n))
        return model, ("nested", "few_rates"), np.column_stack([xi, xi])
    model = cone_model(6)
    s = 7.5 * model.sigma_eff
    t1 = scipy.stats.truncnorm(-model.W / 2 / s, model.W / 2 / s, loc=model.W / 2, scale=s).rvs(n, random_state=rng)
    return model, ("stress", "interior"), np.column_stack([t1, rng.uniform(0, 1, (n, 5))])


@pytest.mark.parametrize("name", ["thin", "thick", "few_rates", "interior"])
def test_t14g_nature_marginals_match_brute_force(name):
    """T14 (F4): a row's floor rests on `log m_q(xbar)`, which §4.3 computes as a
    low-dimensional integral. At three `xbar`, it matches brute-force Monte Carlo over 10^6
    states drawn in the test, `log mean_j N(xbar; y(theta_j), sigma_eff^2)`, within four of
    the Monte Carlo's own standard errors (about 0.003 nats). Catches a floor off by any
    constant, wrong widths in the cross-section integral, or the wrong noise."""
    rng = np.random.default_rng(20261163)
    model, nature, theta = _draw_nature_in_the_test(name, 1_000_000, rng)
    s2 = model.sigma_eff**2
    xbar = model.y(theta[:3]) + model.sigma_eff * rng.standard_normal((3, model.m_out))
    got = nature_log_marginal(model, nature, xbar)
    for i, xb in enumerate(xbar):
        log_w = np.concatenate([
            -0.5 * ((xb - model.y(chunk)) ** 2).sum(-1) / s2 for chunk in np.array_split(theta, 10)
        ]) - 0.5 * model.m_out * np.log(2 * np.pi * s2)
        want, se = log_mean_exp_with_error(log_w)
        assert abs(got[i] - want) <= MC_SIGMAS * se + 1e-9, (name, i, got[i], want, se)


def test_t14h_submodel_floor_is_the_projection_loss():
    """T14 (F4): the submodel's own floor is `N ||y(theta) - y(theta^(D))||^2 / (2 sigma^2)`,
    with `theta^(D)` the state whose ignored coordinates are set to `1/2` (§4.3), at
    `N = 4` so that `sigma` and `sigma_eff` differ. Written out in the test."""
    rng = np.random.default_rng(20261164)
    model_max = cone_model(D_MAX, falloff=0.5, N=4)
    _, _, theta = _draw_nature_in_the_test("thick", 50, rng)
    for D in (2, 5):
        fixed = theta.copy()
        fixed[:, D:] = 0.5
        want = 4 * ((model_max.y(theta) - model_max.y(fixed)) ** 2).sum(-1) / (2 * 1.0**2)
        np.testing.assert_allclose(submodel_floor(model_max, D, theta), want, rtol=1e-12)


def test_t14i_nested_cell_is_one_nature_for_every_agent():
    """T14 (F4): a nested nature is defined once, at `D_max`, and scored by agents of every
    `D` (§2.3). Scored through `score_cell` by submodel agents at `D = 2` and `D = 4` under
    one seed, the nature's draws and its floor are the same; the submodel floor is not; and
    each agent's score is at least the floor (T8(a)). A nature redrawn in each agent's own
    dimension, the drift §2.3 removed, fails."""
    model_max = cone_model(D_MAX, falloff=0.5)
    cells = {}
    for D in (2, 4):
        agent = submodel(model_max, D)
        cells[D] = score_cell(
            agent,
            {"p_U": build_uniform(agent)},
            ("nested", "thick"),
            S_q=200,
            rng=np.random.default_rng(20261165),
            nature_model=model_max,
        )
    a, b = cells[2], cells[4]
    assert a.theta.shape == (200, D_MAX)
    np.testing.assert_array_equal(a.theta, b.theta)
    np.testing.assert_allclose(a.floor_R, b.floor_R, rtol=1e-12)
    assert a.floor_sub is not None and b.floor_sub is not None and a.floor_sub != b.floor_sub
    for cell in cells.values():
        assert cell.R_mean["p_U"] >= cell.floor_R - MC_SIGMAS * cell.mismatch_R_mcse["p_U"]
