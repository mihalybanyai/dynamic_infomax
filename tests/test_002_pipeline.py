"""Spec 002 tests: pipeline checks (P2, P10).

specs/002-foreign-q-prediction.md §5.2 (T2, T10). T2 is the negative control: with no
co-volume gradient, Jeffreys and uniform coincide and must score the same. T10 pins
determinism. Stubs raise `NotImplementedError` until the implementation exists.
"""
from __future__ import annotations

import numpy as np
import pytest

from infomax.jeffreys import build_jeffreys
from infomax.pref import build_uniform
from infomax.score import score_cell
from spec002_common import D_SWEEP_GRID, S_Q_TEST, T2_TOL, build_cast, cheap_model, cone_model


@pytest.mark.parametrize("D", D_SWEEP_GRID)
def test_t2_pipeline_pJ_equals_pU(D):
    """T2: in the constant cross-section `p_J = p_U` pointwise, which exercises the metric,
    the quadrature and the normalisation; then, under common random numbers,
    `|R(p_J) - R(p_U)| <= 1e-6` nats, so any larger difference is a bug (§4.1, m9). `p*`'s
    gaps are recorded by the experiment, not asserted: on the bounded relevant axis it is
    discrete and can win by an edge effect unrelated to the co-volume."""
    rng = np.random.default_rng(20261195)
    model = cone_model(D, taper=0.0)
    p_J, p_U = build_jeffreys(model), build_uniform(model)
    theta = model.box.sample_uniform(200, rng)
    np.testing.assert_allclose(p_J.log_density(theta), p_U.log_density(theta), rtol=1e-6)
    cell = score_cell(model, {"p_J": p_J, "p_U": p_U}, ("own", p_U), S_q=S_Q_TEST, rng=rng)
    assert abs(cell.R_mean["p_J"] - cell.R_mean["p_U"]) <= T2_TOL


def test_t10_seed_determinism():
    """T10: two runs with the same seed give bit-identical score arrays
    (`skills/manage-randomness.md`)."""
    model = cheap_model()
    cast = build_cast(model, np.random.default_rng(20261196))
    nature = ("own", cast["p_U"])
    a = score_cell(model, cast, nature, S_q=S_Q_TEST, rng=np.random.default_rng(20261197))
    b = score_cell(model, cast, nature, S_q=S_Q_TEST, rng=np.random.default_rng(20261197))
    for name in cast:
        np.testing.assert_array_equal(a.draws_R[name], b.draws_R[name])
        np.testing.assert_array_equal(a.draws_r[name], b.draws_r[name])
