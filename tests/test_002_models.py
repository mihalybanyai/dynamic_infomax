"""Spec 002 tests: the model families (property P13; test T13).

specs/002-foreign-q-prediction.md §4.1 and §5.2 (T13). Stubs in `src/infomax/models.py`
raise `NotImplementedError`, so every test fails until the implementation exists
(`skills/derive-test-suite.md`, step 6). Regenerated after the test red-team
(`tests/test_002_foreign_q_prediction-redteam.md`: F1, F7, F9, m3).
"""
from __future__ import annotations

import numpy as np
import pytest

from infomax.models import build_model, warp_vertex
from infomax.pstar import candidate_set
from spec002_common import (
    CHEAP,
    CHEAP_TWIN,
    CONE_BASE,
    CONE_BASE_TWIN,
    CURVATURE_CELL,
    cheap_model,
    cone_model,
)

TIMES = np.linspace(1.0, 5.0, 26)
"""A&M's observation times (§4.1), written out so the map's known values are independent."""


def _finite_difference_jacobian(f, theta: np.ndarray, h: float = 1e-6) -> np.ndarray:
    """Central-difference Jacobian of `f` at one point; shape (m_out, D)."""
    cols = []
    for i in range(theta.size):
        e = np.zeros_like(theta)
        e[i] = h
        cols.append((f(theta + e) - f(theta - e)) / (2 * h))
    return np.stack(cols, axis=-1)


def _smoothstep(s: np.ndarray) -> np.ndarray:
    """§4.1's ramp `S(s) = 3s^2 - 2s^3`, written out in the test."""
    s = np.clip(s, 0.0, 1.0)
    return 3 * s**2 - 2 * s**3


def _angle_from_lateral_edge(w: np.ndarray) -> np.ndarray:
    """Angle between `w` (rows) and the lateral edge's direction `-e_1` (§4.1)."""
    return np.arccos(-w[..., 0] / np.linalg.norm(w, axis=-1))


def _states_inside_the_ball(model, v, rho, rng, n=60):
    """Interior states of the curvature cell whose prediction lies inside the warped ball,
    away from `v` and from the faces, so that central differences stay in `Theta`."""
    W = model.W
    theta = np.column_stack([W - rng.uniform(0.01, 0.4, n), rng.uniform(0.01, 0.4, n), rng.uniform(0.05, 0.95, n)])
    u = np.linalg.norm(model.y(theta) - v, axis=-1)
    return theta[(u > 0.01) & (u < rho - 0.01)]


# ---------------------------------------------------------------------------
# T13(a) — the metric
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "cell, D, knobs",
    [
        (CHEAP, 3, {}),
        (CHEAP_TWIN, 3, {}),
        (CONE_BASE, 4, {"falloff": 0.5}),
        (CONE_BASE_TWIN, 4, {"falloff": 0.5}),
        (CONE_BASE, 3, {"taper": 0.0}),
    ],
    ids=["exp-decay", "exp-decay-twin", "cone", "cone-twin", "constant-cross-section"],
)
def test_t13a_metric_matches_finite_differences(cell, D, knobs):
    """T13(a): the metric of §4.1 is (1.2.1), `J^T J / sigma_eff^2`, at random states.

    The reference uses the cell's own `sigma` and `N`, never `model.sigma_eff`, and the
    twins have `N = 4`, where `sigma` and `sigma_eff` differ (F9). Catches a wrong closed
    form (§9.3 in exp-decay), a slip in `sigma_eff`, or a knob wired to the wrong axis.
    """
    rng = np.random.default_rng(20261121)
    model = build_model(**{**cell, **knobs, "D": D})
    sigma_eff = cell["sigma"] / np.sqrt(cell["N"])
    for theta in model.box.sample_uniform(5, rng):
        J = _finite_difference_jacobian(model.y, theta)
        np.testing.assert_allclose(model.fim(theta), J.T @ J / sigma_eff**2, rtol=1e-5, atol=1e-8)


@pytest.mark.parametrize("kappa", [0.5, 0.25])
def test_t13a_metric_with_curvature_matches_finite_differences(kappa):
    """T13(a): with the curvature knob on, the metric inside the warped ball is still
    `J^T J / sigma_eff^2` of the warped map (§4.1; F1). `v` itself is excluded, since the
    warp is not differentiable there."""
    rng = np.random.default_rng(20261127)
    model = build_model(D=3, **CURVATURE_CELL, curvature=kappa)
    v = np.array([model.W, 0.0, 0.0])
    sigma_eff = CURVATURE_CELL["sigma"] / np.sqrt(CURVATURE_CELL["N"])
    states = _states_inside_the_ball(model, v, 5 * sigma_eff, rng)
    assert len(states) >= 10
    for theta in states[:10]:
        J = _finite_difference_jacobian(model.y, theta)
        np.testing.assert_allclose(model.fim(theta), J.T @ J / sigma_eff**2, rtol=1e-4, atol=1e-6)


# ---------------------------------------------------------------------------
# T13(b) — exp-decay's map and parameter set
# ---------------------------------------------------------------------------


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


def test_t13b_exp_decay_map_known_values():
    """T13(b): known values of exp-decay's map at the 26 times in `[1, 5]` (§4.1; F7): with
    every rate equal, `y(a, ..., a) = a^t`; and `y(0, 1) = 1/2`, one component decayed at
    once and one never. Pins the `1/D` amplitudes and the times, which T12(a) checks only
    against a fixture."""
    for D in (2, 3):
        model = cheap_model(D=D)
        for a in (0.2, 0.5, 0.9):
            np.testing.assert_allclose(model.y(np.full((1, D), a))[0], a**TIMES, rtol=1e-13)
    np.testing.assert_allclose(cheap_model(D=2).y(np.array([[0.0, 1.0]]))[0], np.full(26, 0.5), rtol=1e-14)


def test_t13b_matched_box_is_the_window():
    """T13(b): the matched box is the window's range in `xi`, decay times 1 to 5 (§4.1, OQ-9)."""
    model = cheap_model(D=2, box="matched")
    np.testing.assert_allclose(model.box.low, np.exp(-1.0), rtol=1e-12)
    np.testing.assert_allclose(model.box.high, np.exp(-0.2), rtol=1e-12)


# ---------------------------------------------------------------------------
# T13(c) — the hypercone's co-volume and widths
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("cell", [CONE_BASE, CONE_BASE_TWIN], ids=["N=1", "twin"])
@pytest.mark.parametrize("falloff", [1.0, 0.5, 0.1])
def test_t13c_hypercone_covolume_and_widths(falloff, cell):
    """T13(c): in the hypercone `sqrt(det g) / theta_1^(D-1)` is constant over `Theta` for
    every fall-off, so Jeffreys does not depend on it, and the cross-section's widths are
    `r phi^(mu-2) sqrt(N) / sigma` (§1.2, §4.1), with `sigma` and `N` taken from the cell,
    at `N = 1` and at the twin `N = 4` (F9)."""
    rng = np.random.default_rng(20261123)
    D = 5
    model = build_model(D=D, **{**cell, "falloff": falloff})
    theta = model.box.sample_uniform(50, rng)
    theta = theta[theta[:, 0] > 1.0]  # away from the tip, where both sides vanish
    g = model.fim(theta)
    ratio = np.sqrt(np.linalg.det(g)) / theta[:, 0] ** (D - 1)
    np.testing.assert_allclose(ratio, ratio[0], rtol=1e-6)
    r = theta[:, 0] / cell["W"]
    expected = r[:, None] * falloff ** np.arange(D - 1) * np.sqrt(cell["N"]) / cell["sigma"]
    widths = np.sqrt(np.diagonal(g, axis1=-2, axis2=-1)[:, 1:])
    np.testing.assert_allclose(widths, expected, rtol=1e-8)


def test_t13c_constant_cross_section_has_flat_volume():
    """T13(c), family 3: with the taper off, `sqrt(det g)` is constant (§4.1), which T2 relies on."""
    rng = np.random.default_rng(20261124)
    model = cone_model(4, taper=0.0)
    vol = np.sqrt(np.linalg.det(model.fim(model.box.sample_uniform(30, rng))))
    np.testing.assert_allclose(vol, vol[0], rtol=1e-10)


# ---------------------------------------------------------------------------
# T13(d) — the curvature knob
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("kappa", [0.5, 0.25])
def test_t13d_vertex_warp(kappa):
    """T13(d): the vertex warp alone is one-to-one (positive Jacobian determinant), the
    identity outside the ball of radius `rho` around `v`, keeps each point in the
    half-plane spanned by `-e_1` and its own `e_perp`, and gives the angle `kappa pi / 2`
    between the lateral edge and the base face at every `u <= rho/2` (§4.1, OQ-12; m3)."""
    rng = np.random.default_rng(20261125)
    D, rho = 3, 0.5
    v = np.array([5.0, 0.0, 0.0])
    pts = v + rng.uniform([-1.0, 0.0, 0.0], [0.0, 1.0, 0.05], size=(200, D))
    warped = warp_vertex(pts, v, kappa, rho)
    outside = np.linalg.norm(pts - v, axis=-1) >= rho
    np.testing.assert_array_equal(warped[outside], pts[outside])
    inside = pts[~outside & (np.linalg.norm(pts - v, axis=-1) > 1e-3)]
    for p in inside:
        J = _finite_difference_jacobian(lambda z: warp_vertex(z[None, :], v, kappa, rho)[0], p)
        assert np.linalg.det(J) > 0
    # The base face (beta = pi/2) along e_2 maps to the direction at kappa*pi/2 from -e_1,
    # with no e_3 component and with its distance from v kept.
    u = np.array([0.02, 0.1, 0.2, 0.25])  # all at most rho/2 = 0.25
    base = v + u[:, None] * np.array([0.0, 1.0, 0.0])
    w = warp_vertex(base, v, kappa, rho) - v
    np.testing.assert_allclose(_angle_from_lateral_edge(w), kappa * np.pi / 2, rtol=1e-6)
    np.testing.assert_allclose(np.linalg.norm(w, axis=-1), u, rtol=1e-12)
    np.testing.assert_allclose(w[:, 2], 0.0, atol=1e-15)


@pytest.mark.parametrize("kappa", [0.5, 0.25])
def test_t13d_curvature_knob_through_the_model(kappa):
    """T13(d) through `build_model` (F1): the curvature cell's map is the warped cone.

    On the base face the angle from the lateral edge is `kappa pi/2` for `u < rho/2` and
    `kappa(u) pi/2` with `kappa(u) = kappa + (1 - kappa) S(2u/rho - 1)` for
    `rho/2 < u < rho`, `S` the smoothstep of §4.1; the map is continuous across `u = rho`;
    outside `rho = 5 sigma_eff` of `v` the map and `sqrt(det g)` equal the `kappa = 1`
    model's; and `sqrt(det g) > 0` on the candidate set, `v` itself excluded. A knob that is
    ignored, a ball of the wrong radius, a warp around the wrong vertex or one that jumps
    at `rho` fails here.
    """
    rng = np.random.default_rng(20261129)
    model = build_model(D=3, **CURVATURE_CELL, curvature=kappa)
    flat = build_model(D=3, **CURVATURE_CELL, curvature=1.0)
    W = CURVATURE_CELL["W"]
    rho = 5 * CURVATURE_CELL["sigma"] / np.sqrt(CURVATURE_CELL["N"])
    v = np.array([W, 0.0, 0.0])
    np.testing.assert_allclose(model.y(np.array([[W, 0.0, 0.0]]))[0], v, atol=1e-14)
    # The base face: theta = (W, s, 0) lies at distance s from v along e_2 before the warp.
    s = np.array([0.05, 0.1, 0.2, 0.24, 0.3, 0.375, 0.45])  # rho = 0.5: four below rho/2, three between
    w = model.y(np.column_stack([np.full_like(s, W), s, np.zeros_like(s)])) - v
    k_of_u = kappa + (1 - kappa) * _smoothstep(2 * s / rho - 1)
    np.testing.assert_allclose(_angle_from_lateral_edge(w), k_of_u * np.pi / 2, rtol=1e-6)
    np.testing.assert_allclose(np.linalg.norm(w, axis=-1), s, rtol=1e-12)
    np.testing.assert_allclose(w[:, 2], 0.0, atol=1e-14)
    # Continuity across u = rho.
    edge = model.y(np.array([[W, rho - 1e-6, 0.0], [W, rho + 1e-6, 0.0]]))
    assert np.linalg.norm(edge[1] - edge[0]) <= 1e-5
    # Outside the ball nothing changes.
    theta = model.box.sample_uniform(400, rng)
    far = np.linalg.norm(flat.y(theta) - v, axis=-1) > rho + 1e-9
    assert far.sum() >= 100
    np.testing.assert_allclose(model.y(theta[far]), flat.y(theta[far]), rtol=1e-12, atol=1e-14)
    vol, vol_flat = np.sqrt(np.linalg.det(model.fim(theta[far]))), np.sqrt(np.linalg.det(flat.fim(theta[far])))
    np.testing.assert_allclose(vol, vol_flat, rtol=1e-8)
    # The metric stays non-degenerate on the candidate set, v excluded.
    cands = candidate_set(model)
    cands = cands[np.linalg.norm(model.y(cands) - v, axis=-1) > 1e-9]
    dets = np.linalg.det(model.fim(cands))
    assert np.all(np.isfinite(dets)) and np.all(dets > 0)


def test_t13d_curvature_off_is_identity():
    """T13(d): at `kappa = 1` the warp changes nothing, so the base cell's cone is A&M's (§4.1)."""
    rng = np.random.default_rng(20261126)
    bent = build_model(D=3, **CURVATURE_CELL, curvature=1.0)
    theta = bent.box.sample_uniform(40, rng)
    r = theta[:, 0] / bent.W
    unwarped = np.column_stack([theta[:, 0], r * theta[:, 1], r * bent.falloff * theta[:, 2]])
    np.testing.assert_allclose(bent.y(theta), unwarped, rtol=1e-12, atol=1e-14)
