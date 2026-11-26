"""Spec 002 tests: external references (P9, P12, P18).

specs/002-foreign-q-prediction.md §5.2 (T9, T12, T18) and §5.5. T9 reproduces A&M's
prior-side result; T12 compares with frozen AtomicPriors.jl values; T18 compares
`p_lat` with Tanaka's closed form. Stubs raise `NotImplementedError` until the
implementation exists; T12 also fails until the fixtures are generated. Regenerated after
the test red-team (`tests/test_002_foreign_q_prediction-redteam.md`: F2, F7).

T12's fixtures live in `tests/fixtures/atomicpriors/` and are written at dev time by
`tests/fixtures/atomicpriors/generate.jl` (§5.5; written with the implementation). Each
JSON file holds the values below and their metadata: `atomicpriors_commit`,
`julia_version`, `seed`, the cell (`sigma`, `D`, `N`, the number of states or the cloud
size), `coordinates` (`"xi"`, sorted), and `spread`, each estimated value's spread over two
Julia seeds. It holds no tolerances: §5.5 fixes them, and `spec002_common.py` pins them, so
the bar is set before the reference is computed (F7).
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest
import scipy.stats

from infomax.jeffreys import build_jeffreys
from infomax.models import binomial_model
from infomax.plat import build_plat
from infomax.pproj import build_pproj
from infomax.priors002 import DiscretePrior
from infomax.pstar import build_pstar
from infomax.score import bias_pressure, mutual_information
from spec002_common import (
    D_SWEEP_GRID,
    INFO_SLACK,
    T12_CAPACITY,
    T12_MUTUAL,
    T12_PSTAR,
    T12_SIGMA,
    T12_ATOMIC,
    T12_SPREAD_SHARE,
    T12_TRANSTRUM,
    T12_YMAP,
    cheap_model,
)

FIXTURES = Path(__file__).parent / "fixtures" / "atomicpriors"


def _fixture(name: str, *, D: int, N: int = 1) -> dict:
    """Load a fixture and assert its metadata before any value is trusted (§5.5, F7)."""
    path = FIXTURES / f"{name}.json"
    if not path.exists():
        pytest.fail(f"missing fixture {path}: generate it with tests/fixtures/atomicpriors/generate.jl (§5.5)")
    fx = json.loads(path.read_text())
    for key in ("atomicpriors_commit", "julia_version", "seed"):
        assert fx.get(key), f"{name}: no {key}"
    assert fx["sigma"] == T12_SIGMA, f"{name}: sigma {fx['sigma']}, §5.5 fixes {T12_SIGMA}"
    assert fx["D"] == D and fx["N"] == N, f"{name}: cell (D, N) = ({fx['D']}, {fx['N']}), expected ({D}, {N})"
    assert fx["coordinates"] == "xi", f"{name}: coordinates {fx['coordinates']}"
    return fx


def _spread_ok(fx: dict, key: str, tol: float) -> None:
    """The reference's own run-to-run spread must be small against the tolerance (§5.5)."""
    assert fx["spread"][key] <= T12_SPREAD_SHARE * tol, f"Julia's spread in {key} is too large for the tolerance"


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
    """T12(a): exp-decay's `y` and metric at 10 states drawn on the ordered `Theta` at
    `D = 3` match AtomicPriors.jl's `yexp`, whose compact coordinate is this spec's `xi`
    (§5.5), to the relative tolerances §5.5 fixes. Asserted first: the bridge."""
    fx = _fixture("ymap", D=T12_YMAP["D"])
    xi = np.array(fx["xi"])
    assert xi.shape == (T12_YMAP["n_states"], T12_YMAP["D"])
    model = cheap_model(D=T12_YMAP["D"], sigma=T12_SIGMA)
    np.testing.assert_allclose(model.y(xi), np.array(fx["y"]), rtol=T12_YMAP["rtol_y"])
    np.testing.assert_allclose(model.fim(xi), np.array(fx["fim"]), rtol=T12_YMAP["rtol_fim"])


@pytest.mark.parametrize("D", [2, 3])
def test_t12b_pstar_matches_atomicpriors(D):
    """T12(b): `p*` at exp-decay, `sigma = 0.1`, `N = 1`, against AtomicPriors.jl (§5.5):
    `I_{p*}` to 0.01 nats; `B(p*)` to 0.2 nats; and the cross-equalizer, the Python `p*`'s
    bias pressure within 0.05 nats of zero at every reference atom. The capacity-achieving
    mixture is unique while the prior need not be, so every optimal prior's atoms lie where
    any other's bias pressure vanishes; atoms and weights are not compared one to one
    (MB, 2026-11-25: the candidate set's unmerged atoms outnumber Julia's continuous ones
    about two to one, at any merge radius)."""
    tol = T12_PSTAR
    fx = _fixture(f"pstar_D{D}", D=D, N=tol["N"])
    for key, t in (("I", tol["I_atol"]), ("B", tol["B_atol"])):
        _spread_ok(fx, key, t)
    model = cheap_model(D=D, sigma=T12_SIGMA)
    res = build_pstar(model)
    np.testing.assert_allclose(res.capacity, fx["I"], atol=tol["I_atol"])
    ref_atoms = np.array(fx["atoms"])
    assert ref_atoms.ndim == 2 and ref_atoms.shape[1] == D and len(ref_atoms) >= 2
    b_at_ref = bias_pressure(res.prior, model, ref_atoms, rng=np.random.default_rng(20261203))
    worst = int(np.argmax(np.abs(b_at_ref)))
    assert np.abs(b_at_ref[worst]) <= tol["cross_atol"], ("cross-equalizer", ref_atoms[worst], b_at_ref[worst])
    B = np.max(bias_pressure(res.prior, model, res.candidates))
    np.testing.assert_allclose(B, fx["B"], atol=tol["B_atol"])


@pytest.mark.parametrize("N", T12_CAPACITY["N"])
def test_t12c_capacity_at_reduced_noise(N):
    """T12(c): `C_N` at `sigma_eff = sigma / sqrt(N)`, `N = 2, 4`, `D = 2`, matches
    AtomicPriors.jl's `p*` recipe of (b) run at the same reduced noise, to 0.01 nats: an
    external check of the capacity solver where `p*` has more atoms (§5.5). The reduction
    itself is checked by T7(c) and the twin cells; `repeat` builds the `N`-fold channel of a
    discrete-outcome likelihood and cannot run on 26-dimensional Gaussian data."""
    fx = _fixture(f"capacity_N{N}", D=T12_CAPACITY["D"], N=N)
    _spread_ok(fx, "C_N", T12_CAPACITY["atol"])
    model = cheap_model(D=T12_CAPACITY["D"], N=N, sigma=T12_SIGMA)
    np.testing.assert_allclose(build_pstar(model).capacity, fx["C_N"], atol=T12_CAPACITY["atol"])


def test_t12d_mutual_information_of_a_fixed_prior():
    """T12(d): `I` of the fixed prior of §5.5, the 15 ordered points of
    `{0.1, 0.3, 0.5, 0.7, 0.9}^2` with equal weights, matches AtomicPriors.jl's `mutual` to
    0.005 nats."""
    fx = _fixture("mutual_fixed", D=T12_MUTUAL["D"])
    _spread_ok(fx, "I", T12_MUTUAL["atol"])
    levels = T12_MUTUAL["levels"]
    want_atoms = np.array([(a, b) for a in levels for b in levels if a <= b])
    atoms, weights = np.array(fx["atoms"]), np.array(fx["weights"])
    np.testing.assert_allclose(atoms, want_atoms, rtol=0, atol=1e-15)
    np.testing.assert_allclose(weights, 1 / 15, rtol=1e-12)
    model = cheap_model(D=T12_MUTUAL["D"], sigma=T12_SIGMA)
    prior = DiscretePrior("fixed", atoms, weights)
    np.testing.assert_allclose(mutual_information(prior, model), fx["I"], atol=T12_MUTUAL["atol"])


def _edge_fractions(z: np.ndarray, width: float, w: np.ndarray | None = None) -> np.ndarray:
    """Weighted fractions of a cloud within `width` in `xi` of each edge: coinciding rates,
    `xi = 0` (a rate decaying at once) and `xi = 1` (a rate never decaying)."""
    w = np.full(len(z), 1.0 / len(z)) if w is None else w
    return np.array([
        w @ (np.abs(z[:, 1] - z[:, 0]) < width),
        w @ (z[:, 0] < width),
        w @ (z[:, 1] > 1 - width),
    ])


def _weighted_ks_p(xa: np.ndarray, wa: np.ndarray, xb: np.ndarray, wb: np.ndarray) -> float:
    """Two-sample KS p-value for weighted samples, each at its effective size."""
    grid = np.concatenate([xa, xb])
    Fa = np.array([wa @ (xa <= g) for g in grid])
    Fb = np.array([wb @ (xb <= g) for g in grid])
    na, nb = 1.0 / np.sum(wa**2), 1.0 / np.sum(wb**2)
    return float(scipy.stats.kstwo.sf(np.max(np.abs(Fa - Fb)), int(na * nb / (na + nb))))


def test_t12e_pproj_port_matches_transtrum():
    """T12(e): the sampler's weighted cloud of `theta-hat` matches `transtrum`'s at
    exp-decay, `D = 2`, `sigma = 0.1`, on the whole manifold (§5.5). `generate.jl` maps
    `transtrum`'s cloud to sorted `xi` and re-fits each point tightly. A two-sample KS test
    per coordinate at `p > 1e-3`, each cloud at its effective size, and the mass within 0.02
    of each edge (coinciding rates, `xi = 0`, `xi = 1`) within four binomial standard errors
    at those sizes; and two independent starts of the sampler, from Jeffreys and from
    `p_U`, also agree (OQ-6)."""
    tol = T12_TRANSTRUM
    fx = _fixture("transtrum", D=tol["D"], N=tol["N"])
    ref = np.array(fx["theta_hat"])
    assert ref.shape == (tol["cloud"], tol["D"]) and np.all(np.diff(ref, axis=1) >= 0)
    w_ref = np.full(len(ref), 1.0 / len(ref))
    model = cheap_model(D=tol["D"], sigma=T12_SIGMA)
    a = build_pproj(model, np.random.default_rng(20261201))
    b = build_pproj(model, np.random.default_rng(20261202), first="uniform")
    for j in range(tol["D"]):
        assert _weighted_ks_p(a.atoms[:, j], a.weights, ref[:, j], w_ref) > tol["ks_p"]
        assert _weighted_ks_p(a.atoms[:, j], a.weights, b.atoms[:, j], b.weights) > tol["ks_p"]
    width = tol["edge_width"]
    got, want = _edge_fractions(a.atoms, width, a.weights), _edge_fractions(ref, width)
    other = _edge_fractions(b.atoms, width, b.weights)
    for k in range(3):
        se = np.hypot(np.sqrt(got[k] * (1 - got[k]) / a.ess), np.sqrt(want[k] * (1 - want[k]) / len(ref)))
        assert abs(got[k] - want[k]) <= tol["edge_sigmas"] * se + 1e-12, ("edge vs transtrum", k, got[k], want[k])
        se_ab = np.hypot(np.sqrt(got[k] * (1 - got[k]) / a.ess), np.sqrt(other[k] * (1 - other[k]) / b.ess))
        assert abs(got[k] - other[k]) <= tol["edge_sigmas"] * se_ab + 1e-12, ("edge, two starts", k, got[k], other[k])


@pytest.mark.slow
@pytest.mark.parametrize("D", T12_ATOMIC["D"])
def test_t12f_atomic_path_not_below_atomicpriors(D):
    """T12(f): at A&M's `D in {5, 7}`, exp-decay, `sigma = 0.1`, `N = 1`, the atomic path's
    `I_{p*}` is at least AtomicPriors.jl's minus 0.01 nats (§5.5(f)). One-sided: `p*`
    maximises `I`, and the reference optimises a kernel bound, so it is a floor, not the
    value; at `D = 5` the atomic path exceeded it by 0.027 nats (2026-11-26). Also checks
    that the pool's last round leaves no violation above the solver's tolerance."""
    tol = T12_ATOMIC
    fx = _fixture(f"pstar_D{D}", D=D, N=tol["N"])
    _spread_ok(fx, "I", tol["I_floor"])
    model = cheap_model(D=D, sigma=T12_SIGMA)
    res = build_pstar(model, method="atomic")
    assert res.method == "atomic"
    assert res.capacity >= fx["I"] - tol["I_floor"], (res.capacity, fx["I"])
    assert res.max_violation <= 2e-3, res.max_violation


# ---------------------------------------------------------------------------
# P18 / T18 — p_lat against Tanaka's closed form
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("n_points", [11, 101])
def test_t18_plat_matches_tanaka(n_points):
    """T18: one Bernoulli observation, one to predict: the latent information prior puts
    3/10 on `theta = 0` and on `theta = 1` and 2/5 on `theta = 1/2` [Tanaka 2014, Thm 4].
    A grid containing these points has the same optimum, and the conditional information is
    `log(5/4)` (`[^5-tanaka]`). Run through `build_plat` on the binomial model (§5.2, §5.3),
    so the reference reaches the same update as the Gaussian build (F2). Catches a wrong
    difference of divergences, or a stopping rule that halts short of the optimum."""
    grid = np.linspace(0.0, 1.0, n_points)
    res = build_plat(binomial_model(N=1, M=1), M=1, candidates=grid[:, None], tol=1e-10)
    order = np.argsort(res.prior.atoms[:, 0])
    np.testing.assert_allclose(res.prior.atoms[order, 0], grid, atol=1e-15)
    expected = np.zeros(n_points)
    expected[0], expected[-1], expected[n_points // 2] = 0.3, 0.3, 0.4
    np.testing.assert_allclose(res.prior.weights[order], expected, atol=1e-4)
    np.testing.assert_allclose(res.conditional_capacity, np.log(5 / 4), atol=1e-6)
