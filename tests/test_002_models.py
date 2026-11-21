"""Spec 002 tests: the model families (property P13; test T13).

specs/002-foreign-q-prediction.md §4.1 and §5.2 (T13). Stubs in `src/infomax/models.py`
raise `NotImplementedError`, so every test fails until the implementation exists
(`skills/derive-test-suite.md`, step 6).
"""
from __future__ import annotations

import numpy as np
import pytest

from infomax.models import build_model, warp_vertex
from spec002_common import CURVATURE_CELL, cheap_model, cone_model


def _finite_difference_jacobian(f, theta: np.ndarray, h: float = 1e-6) -> np.ndarray:
    """Central-difference Jacobian of `f` at one point; shape (m_out, D)."""
    cols = []
    for i in range(theta.size):
        e = np.zeros_like(theta)
        e[i] = h
        cols.append((f(theta + e) - f(theta - e)) / (2 * h))
    return np.stack(cols, axis=-1)


@pytest.mark.parametrize(
    "family, D, knobs",
    [("exp_decay", 3, {}), ("hypercone", 4, {"falloff": 0.5}), ("hypercone", 3, {"taper": 0.0})],
)
def test_t13a_metric_matches_finite_differences(family, D, knobs):
    """T13(a): the metric of §4.1 is (1.2.1), `J^T J / sigma_eff^2`, at random states.

    Catches a wrong closed form (§9.3 in exp-decay), a slip in `sigma_eff`, or a knob
    wired to the wrong axis.
    """
    rng = np.random.default_rng(20261121)
    model = cheap_model(D=D, **knobs) if family == "exp_decay" else cone_model(D, **knobs)
    for theta in model.box.sample_uniform(5, rng):
        J = _finite_difference_jacobian(model.y, theta)
        np.testing.assert_allclose(model.fim(theta), J.T @ J / model.sigma_eff**2, rtol=1e-5, atol=1e-8)


def test_t13b_exp_decay_symmetry_and_ordered_theta():
    """T13(b): exp-decay's map is unchanged by permuting the rates, and `Theta` holds only
    ordered `xi` in `[0, 1]^D`: the whole manifold, its limits included (§4.1)."""
    rng = np.random.default_rng(20261122)
    model = cheap_model(D=4)
    xi = np.sort(rng.uniform(0.0, 1.0, size=(20, 4)), axis=-1)
    permuted = xi[:, ::-1]
    np.testing.assert_allclose(model.y(xi), model.y(permuted), rtol=0, atol=1e-14)
    assert model.box.contains(xi).all()
    assert not model.box.contains(permuted).any()
    corners = np.array([[0.0, 0.0, 1.0, 1.0], [0.0, 0.0, 0.0, 0.0], [1.0, 1.0, 1.0, 1.0]])
    assert model.box.contains(corners).all(), "the manifold's limits belong to Theta"
    assert not model.box.contains(np.array([[0.2, 0.3, 0.4, 1.2]])).any()


def test_t13b_matched_box_is_the_window():
    """T13(b): the matched box is the window's range in `xi`, decay times 1 to 5 (§4.1, OQ-9)."""
    model = cheap_model(D=2, box="matched")
    np.testing.assert_allclose(model.box.low, np.exp(-1.0), rtol=1e-12)
    np.testing.assert_allclose(model.box.high, np.exp(-0.2), rtol=1e-12)


@pytest.mark.parametrize("falloff", [1.0, 0.5, 0.1])
def test_t13c_hypercone_covolume_and_widths(falloff):
    """T13(c): in the hypercone `sqrt(det g) / theta_1^(D-1)` is constant over `Theta` for
    every fall-off, so Jeffreys does not depend on it, and the cross-section's widths are
    `r phi^(mu-2) sqrt(N) / sigma` (§1.2, §4.1)."""
    rng = np.random.default_rng(20261123)
    D = 5
    model = cone_model(D, falloff=falloff)
    theta = model.box.sample_uniform(50, rng)
    theta = theta[theta[:, 0] > 1.0]  # away from the tip, where both sides vanish
    g = model.fim(theta)
    ratio = np.sqrt(np.linalg.det(g)) / theta[:, 0] ** (D - 1)
    np.testing.assert_allclose(ratio, ratio[0], rtol=1e-6)
    r = theta[:, 0] / model.W
    expected = r[:, None] * falloff ** np.arange(D - 1) * np.sqrt(model.N) / model.sigma
    widths = np.sqrt(np.diagonal(g, axis1=-2, axis2=-1)[:, 1:])
    np.testing.assert_allclose(widths, expected, rtol=1e-8)


def test_t13c_constant_cross_section_has_flat_volume():
    """T13(c), family 3: with the taper off, `sqrt(det g)` is constant (§4.1), which T2 relies on."""
    rng = np.random.default_rng(20261124)
    model = cone_model(4, taper=0.0)
    vol = np.sqrt(np.linalg.det(model.fim(model.box.sample_uniform(30, rng))))
    np.testing.assert_allclose(vol, vol[0], rtol=1e-10)


@pytest.mark.parametrize("kappa", [0.5, 0.25])
def test_t13d_vertex_warp(kappa):
    """T13(d): the vertex warp is one-to-one (positive Jacobian determinant), the identity
    outside the ball of radius `rho` around `v`, and gives the angle `kappa pi / 2`
    between the lateral edge and the base face at `v` (§4.1, OQ-12)."""
    rng = np.random.default_rng(20261125)
    D, rho = 3, 0.5
    v = np.array([5.0, 0.0, 0.0])
    # Points of the manifold near the vertex: theta_1 below W, cross-section non-negative.
    pts = v + rng.uniform([-1.0, 0.0, 0.0], [0.0, 1.0, 0.05], size=(200, D))
    warped = warp_vertex(pts, v, kappa, rho)
    outside = np.linalg.norm(pts - v, axis=-1) >= rho
    np.testing.assert_array_equal(warped[outside], pts[outside])
    inside = pts[~outside & (np.linalg.norm(pts - v, axis=-1) > 1e-3)]
    for p in inside:
        J = _finite_difference_jacobian(lambda z: warp_vertex(z[None, :], v, kappa, rho)[0], p)
        assert np.linalg.det(J) > 0
    # The base face (beta = pi/2) maps to the direction at angle kappa*pi/2 from -e_1.
    u = 0.1 * rho
    base_point = v + u * np.array([0.0, 1.0, 0.0])
    w = warp_vertex(base_point[None, :], v, kappa, rho)[0] - v
    angle = np.arccos(np.dot(w, [-1.0, 0.0, 0.0]) / np.linalg.norm(w))
    np.testing.assert_allclose(angle, kappa * np.pi / 2, rtol=1e-6)
    np.testing.assert_allclose(np.linalg.norm(w), u, rtol=1e-12)


def test_t13d_curvature_off_is_identity():
    """T13(d): at `kappa = 1` the warp changes nothing, so the base cell's cone is A&M's (§4.1)."""
    rng = np.random.default_rng(20261126)
    bent = build_model(D=3, **CURVATURE_CELL, curvature=1.0)
    theta = bent.box.sample_uniform(40, rng)
    r = theta[:, 0] / bent.W
    unwarped = np.column_stack([theta[:, 0], r * theta[:, 1], r * bent.falloff * theta[:, 2]])
    np.testing.assert_allclose(bent.y(theta), unwarped, rtol=1e-12, atol=1e-14)
