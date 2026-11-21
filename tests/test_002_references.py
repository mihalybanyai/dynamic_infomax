"""Spec 002 tests: external references (P9, P12, P18).

specs/002-foreign-q-prediction.md §5.2 (T9, T12, T18) and §5.5. T9 reproduces A&M's
prior-side result; T12 compares with frozen AtomicPriors.jl values; T18 compares
`p_lat` with Tanaka's closed form. Stubs raise `NotImplementedError` until the
implementation exists; T12 also fails until the fixtures are generated.

T12's fixtures live in `tests/fixtures/atomicpriors/` and are written at dev time by
`tests/fixtures/atomicpriors/generate.jl` (§5.5; written with the implementation). Each
JSON file holds the values below plus the AtomicPriors commit, the Julia version, the
seed and a tolerance `tol`.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest
import scipy.stats

from infomax.jeffreys import build_jeffreys
from infomax.plat import build_plat_binomial
from infomax.pproj import build_pproj
from infomax.priors002 import DiscretePrior
from infomax.pstar import build_pstar
from infomax.score import bias_pressure, mutual_information
from spec002_common import D_SWEEP_GRID, INFO_SLACK, cheap_model

FIXTURES = Path(__file__).parent / "fixtures" / "atomicpriors"


def _fixture(name: str) -> dict:
    path = FIXTURES / f"{name}.json"
    if not path.exists():
        pytest.fail(f"missing fixture {path}: generate it with tests/fixtures/atomicpriors/generate.jl (§5.5)")
    return json.loads(path.read_text())


# ---------------------------------------------------------------------------
# P9 / T9 — A&M's prior side (Fig. 5)
# ---------------------------------------------------------------------------


@pytest.mark.slow
@pytest.mark.parametrize("D", D_SWEEP_GRID)
def test_t9_am_prior_side_dominance(D):
    """T9: at every `D` of the sweep, `I_{p*} >= I_{p_J}` and `B(p*) <= B(p_J)`, A&M's
    established result (Fig. 5), checked before any foreign nature is scored. Both hold by
    `p*`'s optimality, so they are machinery checks, not results."""
    rng = np.random.default_rng(20261190)
    model = cheap_model(D=D)
    pstar = build_pstar(model)
    p_J = build_jeffreys(model)
    assert pstar.capacity >= mutual_information(p_J, model, rng=rng) - INFO_SLACK
    states = pstar.candidates
    B_star = np.max(bias_pressure(pstar.prior, model, states, rng=rng))
    B_J = np.max(bias_pressure(p_J, model, states, rng=rng))
    assert B_star <= B_J + INFO_SLACK


# ---------------------------------------------------------------------------
# P12 / T12 — AtomicPriors.jl references
# ---------------------------------------------------------------------------


def test_t12a_exp_decay_map_and_metric():
    """T12(a): exp-decay's `y` and metric at about ten sampled states match AtomicPriors.jl's
    `yexp`, whose coordinate is this spec's `xi` (§5.5). Asserted first: the bridge."""
    fx = _fixture("ymap")
    model = cheap_model(D=len(fx["xi"][0]), sigma=fx["sigma"])
    xi = np.array(fx["xi"])
    np.testing.assert_allclose(model.y(xi), np.array(fx["y"]), rtol=fx["tol"])
    np.testing.assert_allclose(model.fim(xi), np.array(fx["fim"]), rtol=fx["tol"])


@pytest.mark.parametrize("D", [2, 3])
def test_t12b_pstar_matches_atomicpriors(D):
    """T12(b): `p*`'s atoms and weights up to relabelling, `I_{p*}` and `B(p*)` at exp-decay,
    `sigma = 0.1`, match the frozen values (§5.5)."""
    fx = _fixture(f"pstar_D{D}")
    model = cheap_model(D=D, sigma=fx["sigma"])
    res = build_pstar(model)
    np.testing.assert_allclose(res.capacity, fx["I"], rtol=fx["tol"])
    ref_atoms, ref_w = np.array(fx["atoms"]), np.array(fx["weights"])
    big = res.prior.weights > 1e-3
    got = res.prior.atoms[big]
    order_got, order_ref = np.lexsort(got.T[::-1]), np.lexsort(ref_atoms.T[::-1])
    np.testing.assert_allclose(got[order_got], ref_atoms[order_ref], atol=fx["atom_tol"])
    np.testing.assert_allclose(res.prior.weights[big][order_got], ref_w[order_ref], atol=fx["weight_tol"])
    B = np.max(bias_pressure(res.prior, model, res.candidates))
    np.testing.assert_allclose(B, fx["B"], atol=fx["B_tol"])


@pytest.mark.parametrize("N", [1, 2, 4])
def test_t12c_capacity_through_repeat(N):
    """T12(c): `C_N` from AtomicPriors.jl's literal `N`-fold channel (`repeat`, `mutual`)
    matches the `sigma_eff` build: the independent check that the reduction is right."""
    fx = _fixture("capacity_repeat")
    model = cheap_model(D=2, N=N, sigma=fx["sigma"])
    np.testing.assert_allclose(build_pstar(model).capacity, fx["C_N"][str(N)], rtol=fx["tol"])


def test_t12d_mutual_information_of_a_fixed_prior():
    """T12(d): `I` of a fixed grid prior matches AtomicPriors.jl's `mutual`."""
    fx = _fixture("mutual_fixed")
    model = cheap_model(D=len(fx["atoms"][0]), sigma=fx["sigma"])
    prior = DiscretePrior("fixed", np.array(fx["atoms"]), np.array(fx["weights"]))
    np.testing.assert_allclose(mutual_information(prior, model), fx["I"], rtol=fx["tol"])


def test_t12e_pproj_port_matches_transtrum():
    """T12(e): the port's cloud of `theta-hat` matches `transtrum`'s at exp-decay, `D = 2`,
    `sigma = 0.1`, on the whole manifold: a two-sample test per coordinate, and the mass near
    the edges (coinciding rates, rates outside the window), where mixing is least certain.
    Two independent chains of the port also agree (m8)."""
    fx = _fixture("transtrum")
    model = cheap_model(D=2, sigma=fx["sigma"])
    ref = np.array(fx["theta_hat"])
    a = build_pproj(model, ref.shape[0], np.random.default_rng(20261191)).atoms
    b = build_pproj(model, ref.shape[0], np.random.default_rng(20261192)).atoms
    for j in range(2):
        assert scipy.stats.ks_2samp(a[:, j], ref[:, j]).pvalue > 1e-3
        assert scipy.stats.ks_2samp(a[:, j], b[:, j]).pvalue > 1e-3
    near_edge = lambda z: np.mean(np.abs(z[:, 1] - z[:, 0]) < fx["edge_width"])
    assert abs(near_edge(a) - near_edge(ref)) <= fx["edge_tol"]


# ---------------------------------------------------------------------------
# P18 / T18 — p_lat against Tanaka's closed form
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("n_points", [11, 101])
def test_t18_plat_matches_tanaka(n_points):
    """T18: one Bernoulli observation, one to predict: the latent information prior puts
    3/10 on `theta = 0` and on `theta = 1` and 2/5 on `theta = 1/2` [Tanaka 2014, Thm 4].
    A grid containing these points has the same optimum, and the conditional information is
    `log(5/4)` (`[^5-tanaka]`). Catches a wrong difference of divergences, or a stopping rule
    that halts short of the optimum."""
    grid = np.linspace(0.0, 1.0, n_points)
    res = build_plat_binomial(grid, N=1, M=1)
    expected = np.zeros(n_points)
    expected[0], expected[-1], expected[n_points // 2] = 0.3, 0.3, 0.4
    np.testing.assert_allclose(res.weights, expected, atol=1e-4)
    np.testing.assert_allclose(res.conditional_information, np.log(5 / 4), atol=1e-6)
