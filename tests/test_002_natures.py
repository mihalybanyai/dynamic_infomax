"""Spec 002 tests: the natures (property P14; test T14).

specs/002-foreign-q-prediction.md §2.3, §4.3 and §5.2 (T14): round robin, nested natures
(question 3) and stress natures, their labels, and `q̄`. Stubs raise
`NotImplementedError` until the implementation exists.
"""
from __future__ import annotations

import numpy as np
import pytest
import scipy.stats

from infomax.models import build_model, submodel
from infomax.pref import build_uniform
from infomax.qfamily import D_MAX, build_qbar, nature_log_marginal, sample_nature
from spec002_common import CURVATURE_CELL, cheap_model, cone_model, log_time_from_xi


def test_t14a_round_robin_draws_come_from_the_prior():
    """T14: a round-robin row draws from its prior's own sampler, under the cell's seed (§4.3)."""
    model = cheap_model()
    p_U = build_uniform(model)
    theta, labels = sample_nature(model, ("own", p_U), 500, np.random.default_rng(20261150))
    np.testing.assert_array_equal(theta, p_U.sample(500, np.random.default_rng(20261150)))
    assert labels.shape == (500,) and len(set(labels)) == 1


@pytest.mark.parametrize("half, lo, hi", [("thin", 0.0, 25.0), ("thick", 25.0, 50.0)])
def test_t14b_nested_cone_laws(half, lo, hi):
    """T14: a nested hypercone nature lives at `D_max = 26` with fall-off below 1: `theta_1`
    uniform on its half, the cross-section uniform on `[0, 1]` (§2.3, §4.3)."""
    rng = np.random.default_rng(20261151)
    model_max = cone_model(D_MAX, falloff=0.5)
    theta, _ = sample_nature(model_max, ("nested", half), 4000, rng)
    assert theta.shape == (4000, D_MAX)
    assert scipy.stats.kstest(theta[:, 0], scipy.stats.uniform(lo, hi - lo).cdf).pvalue > 1e-3
    assert scipy.stats.kstest(theta[:, 1:].ravel(), scipy.stats.uniform(0, 1).cdf).pvalue > 1e-3


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


def test_t14e_interior_nature_is_truncated_normal():
    """T14: the smooth interior's `theta_1` is normal with mean `W/2` and standard deviation
    `7.5 sigma_eff`, truncated to `[0, W]`; its cross-section is uniform (§4.3)."""
    rng = np.random.default_rng(20261155)
    model = cone_model(4)
    theta, _ = sample_nature(model, ("stress", "interior"), 5000, rng)
    s = 7.5 * model.sigma_eff
    law = scipy.stats.truncnorm((0 - model.W / 2) / s, (model.W - model.W / 2) / s, loc=model.W / 2, scale=s)
    assert scipy.stats.kstest(theta[:, 0], law.cdf).pvalue > 1e-3
    assert scipy.stats.kstest(theta[:, 1:].ravel(), scipy.stats.uniform(0, 1).cdf).pvalue > 1e-3


def test_t14f_qbar_is_the_average_of_the_rows():
    """T14: `q̄`'s data marginal is the equal-weight average of the rows' marginals, and it
    is not itself one of the rows (§2.5, §4.2)."""
    rng = np.random.default_rng(20261156)
    model = cheap_model()
    rows = [("own", build_uniform(model)), ("nested", "few_rates")]
    qbar = build_qbar(rows)
    xbar = model.y(model.box.sample_uniform(50, rng)) + model.sigma_eff * rng.standard_normal((50, model.m_out))
    each = np.stack([nature_log_marginal(model, row, xbar) for row in rows])
    expected = np.logaddexp.reduce(each, axis=0) - np.log(len(rows))
    np.testing.assert_allclose(qbar.log_marginal(model, xbar), expected, rtol=1e-10)
    assert len(rows) == 2 and all(row[1] is not qbar for row in rows)
