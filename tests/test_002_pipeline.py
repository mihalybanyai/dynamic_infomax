"""Spec 002 tests: pipeline checks (P2, P10).

specs/002-foreign-q-prediction.md §5.2 (T2, T10). T2 is the negative control: with no
co-volume gradient, Jeffreys and uniform coincide and must score the same. T10 pins
determinism. Stubs raise `NotImplementedError` until the implementation exists. Regenerated after the test
red-team (`tests/test_002_foreign_q_prediction-redteam.md`: F13).
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
    """T10: two runs with the same seed give bit-identical results (`skills/manage-randomness.md`),
    the cast's builders included (F13): the cast is built twice from one seed, so a builder
    that draws from global state (`p_proj`'s chain, `p_LN^*`'s search) fails, and score
    arrays, floors and mismatches are compared. A different seed must change the draws, so a
    `score_cell` that ignores its `rng` for a fixed internal seed fails too."""
    model = cheap_model()

    def run(cast_seed: int, cell_seed: int):
        cast = build_cast(model, np.random.default_rng(cast_seed))
        return cast, score_cell(model, cast, ("own", cast["p_U"]), S_q=S_Q_TEST, rng=np.random.default_rng(cell_seed))

    cast, a = run(20261196, 20261197)
    _, b = run(20261196, 20261197)
    assert a.floor_R == b.floor_R and a.floor_r == b.floor_r
    for name in cast:
        np.testing.assert_array_equal(a.draws_R[name], b.draws_R[name])
        np.testing.assert_array_equal(a.draws_r[name], b.draws_r[name])
        assert a.mismatch_R[name] == b.mismatch_R[name] and a.mismatch_r[name] == b.mismatch_r[name]
    _, c = run(20261196, 20261198)
    assert not np.array_equal(a.draws_R["p_J"], c.draws_R["p_J"]), "the cell ignores its seed"


def test_t10_scoring_R_alone_leaves_R_unchanged():
    """T10 (experiment 002, tier 0): scoring `R_N` alone (`scores=("R",)`) gives bit-identical
    `R` draws, floors and mismatches to scoring both, since the draws, `x'` included, are the
    same; the one-step fields are then empty. And a sampled prior's memo of thin points
    changes no number: at `D = 3`, near the no-decay corner, `log m` asked for again, after
    the predictive has asked for it too, equals a fresh prior's (§4.4, OQ-14)."""
    from infomax.plognormal import build_pln
    from infomax.sampled import sampled_from

    model = cheap_model()
    priors = {"p_U": build_uniform(model), "p_J": build_jeffreys(model)}
    both = score_cell(model, priors, ("own", priors["p_U"]), S_q=100, rng=np.random.default_rng(20261340))
    only = score_cell(model, priors, ("own", priors["p_U"]), S_q=100, rng=np.random.default_rng(20261340), scores=("R",))
    assert both.floor_R == only.floor_R and np.isnan(only.floor_r)
    for name in priors:
        np.testing.assert_array_equal(both.draws_R[name], only.draws_R[name])
        assert both.mismatch_R[name] == only.mismatch_R[name]
    assert only.draws_r == {} and only.r_mean == {}

    m3 = cheap_model(D=3)
    grid = build_pln(m3)
    y = m3.y(np.full((1, 3), 0.97))[0]
    x = y + m3.sigma_eff * np.random.default_rng(20261341).standard_normal((4, y.size))
    x_prime = y + m3.sigma * np.random.default_rng(20261342).standard_normal((4, y.size))
    cloud = sampled_from(grid, m3, "p_LN")
    first = cloud.log_marginal(m3, x)
    cloud.log_predictive(m3, x_prime, x)
    again = cloud.log_marginal(m3, x)
    fresh = sampled_from(grid, m3, "p_LN").log_marginal(m3, x)
    np.testing.assert_array_equal(first, again)
    np.testing.assert_array_equal(first, fresh)
