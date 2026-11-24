# Red-team review of the spec 002 test suite

Reviewer: red-team sub-agent
Reviewer model (declared identity): Claude Opus 5.5 (`claude-opus-5-5`)
Effort tier: max (set at spawn by the main agent; not verifiable here)
Roster verified: 2026-11-21
Date: 2026-11-21
Spec version: cf4df6e (HEAD, the commit that derived the suite and last touched the spec)
Artefact: `tests/test_002_{models,priors,natures,scores,diagnostics,references,pipeline}.py`,
with `tests/spec002_common.py` and `tests/eye_test_002_foreign_q_prediction.py`
Spec: `specs/002-foreign-q-prediction.md`

Numbers marked *computed by the reviewer* come from throwaway scripts (scipy quadrature;
a 300 × 300 grid approximation of the exp-decay cheap cell). They are not committed.

## Summary

The suite follows §5's property table closely and has some sharp known-answer tests:
T7(a)'s discrete atom sum, T18's Tanaka weights, T19(c)'s mis-budget design, the cone's
closed-form map and widths, and the KS checks of the natures' laws. Most of the machinery
that produces the spec's numbers, though, is checked only for internal consistency.

**Tolerances from the code under test.** Many tolerances come from the code under test:
every Monte-Carlo agreement uses the implementation's own error bars. T12, the only
external anchor for exp-decay, takes its tolerances and even its cells from fixture files
that will be written along with the implementation.

**Identities and self-comparisons.** Several tests are identities of the estimators
(T1, T8(c), T17(b)), or compare an output with itself (T22(a)). The one real check of the
one-step score, T17(a), has a tolerance larger than `r_N` itself. In my simulation of its
cell, `r_N ≡ 0` passes, and so does `x′` drawn at `σ_eff`.

**Where the suite is thinnest.** The work is thinnest where the spec is newest:
- `p_lat` at `N ≥ 1`: no reference reaches the Gaussian build, and every test runs at
  `N ≤ 1`, where `σ_eff = σ`.
- Question 3's nested natures: the floors, the submodel floor and the `D`-agent scoring
  path are untested, and two slow tests call nested natures in a model of the wrong
  dimension.
- The curvature knob: never applied through `build_model`.
- The privileged-information priors in exp-decay: `p_LN` and `p_ref` are never compared
  with their definitions.

**What slips through.** Wrong implementations that pass include:
- a one-step score of zero;
- a Gaussian `p_lat` that never leaves its initialisation;
- a curvature knob that does nothing;
- a `p_ref` that is any normalised density;
- nested floors off by any constant;
- a Monte-Carlo error twenty times too large, which turns most of the Monte-Carlo
  agreement tests into near-tautologies.

As it stands, the suite cannot gate an implementation. The fixes are mostly cheap: known
answers in the 1-D Gaussian channel and the small-`D` hypercone, the cheap cell rerun at
`N = 4`, and tolerances pinned in the suite.

## Findings

### F1: The curvature knob is never applied through the model [severity: high]

**Test**: `test_t13d_vertex_warp`, `test_t13d_curvature_off_is_identity`,
`test_t14e_vertex_nature_lies_on_faces_near_v`; missing: `build_model` with `κ < 1`.

**Concern**: T13(d) calls `warp_vertex` directly, on hand-made points with `ρ = 0.5`. It
exercises `build_model` only at `κ = 1`. The one test that builds a model with `κ = ½`,
T14(e), checks faces in `θ` and `‖y(θ) − v‖ ≤ ρ`. Both are invariant under the warp, which
by construction preserves the distance `u` from `v` (§4.1: it "changes neither `u` nor
`ê_⊥`").

So a `build_model` that ignores `curvature` passes every test. So does one that warps with
a `ρ` other than `5σ_eff`, or around the wrong vertex. The `κ ∈ {½, ¼}` cells would then
run on the unwarped cone, and the axis on which `p*` and `p_proj` are expected to differ
(§1.2, §3.4) would read "a sharpened vertex does not hurt `p_proj`".

Separately, T13(d) passes a warp that applies `κ` throughout `u < ρ` and jumps to the
identity at `u = ρ`. That warp is one-to-one and has a positive Jacobian at every interior
point, but it tears the manifold at `ρ`, which §4.1's smooth rise from `ρ/2` to `ρ` rules
out. The Jacobian is probed only by finite differences with a `1e-6` step, at random
interior points.

`p_ref` with curvature on (Berger–Bernardo by quadrature, §4.2's coverage table) has no
test.

**What would resolve it**: Test the knob through `build_model(D=3, **CURVATURE_CELL,
curvature=κ)` for `κ ∈ {½, ¼}`:
- on the base face at `u < ρ/2`, the angle between `y(θ) − v` and `−e_1` is `κπ/2`;
- `y` and `√det fim` equal the `κ = 1` model's outside `5σ_eff` of `v = y(W, 0, …, 0)`;
- `y` is continuous across `u = ρ`, by comparing points at `ρ ± 1e-6`;
- `√det fim > 0` on the candidate set.

Add `p_ref` at `κ = ½`: it normalises, and it equals `p_U` on cross-sections that miss
the ball.

> M: let's add these tests

> C: Agreed; tests only. T13(d) gains checks through `build_model(D=3, **CURVATURE_CELL,
> curvature=κ)`, `κ ∈ {½, ¼}`: the base face leaves `v` at angle `κπ/2` for `u < ρ/2`; for
> `ρ/2 < u < ρ` its angle follows `κ(u) = κ + (1 − κ) S(2u/ρ − 1)`, the smoothstep pinned in
> 48bef96; `y` is continuous across `u = ρ` (points at `ρ ± 1e-6`); outside `5σ_eff` of `v`,
> `y` and `√det fim` equal the `κ = 1` model's; and `√det fim > 0` on the candidate set,
> `v` itself excluded, since the warp is not differentiable there. T13(a)'s
> finite-difference check of the metric gains a curvature model, at states inside the
> ball. T15 gains `p_ref` at `κ = ½`: it normalises, and on cross-sections that miss the
> ball it is *proportional* to `p_U`, with one constant ratio. The finding says "equals",
> but the warp changes the normaliser.

---

### F2: The Gaussian `p_lat` has no reference, and is tested only where `σ_eff = σ` [severity: high]

**Test**: `test_t16a_b_plat_conditional_equalizer_and_bounds`,
`test_t16c_plat_at_zero_budget_is_pstar`; missing: `build_plat` at `N ≥ 2`, and the 1-D
bounded channel.

**Concern**: T16(a, b) compare `build_plat`'s output only with quantities the same code
reports: `conditional_divergence`, `conditional_capacity`, `lower_bound` and
`upper_bound`. Suppose `f^(N+1)` and `f^(N)` are computed at the same noise. Then
`f^(N+1) − f^(N) ≡ 0`, Blahut–Arimoto never moves from its uniform start, every divergence
is 0, the capacity and both bounds are 0, and all four assertions hold.

T16(c) runs at `N = 0`. There the pseudocode skips the `f^(N)` term
(`if model.N > 0 else 0.0`), so the subtraction is never evaluated. T16(c) also passes
outright if `build_plat` handles `N = 0` by calling `build_pstar`, as its docstring
describes.

T18 and the Komaki eye test go through `build_plat_binomial`, a separate function in
`plat.py`, so no reference reaches the Gaussian build.

Every `p_lat` test runs at `N ≤ 1`. At `N = 1`, `σ_eff = σ`, so consider a build that
writes `s1 = σ_eff/√(N+1)` where §4.2 needs `σ/√(N+1)`. It gets `s1` right at exactly that
cell, and wrong at every other point of the sweep's `N` axis, `N ∈ {2, 4, 8}`.

§5.4 prescribes T16 "at `N ∈ {0, 1, 4}` in the 1-D bounded channel and at the cheap cell".
The suite has neither the 1-D channel nor `N = 4`.

**What would resolve it**:
- Run T16 as §5.4 says, at `N ∈ {1, 4}`, in the 1-D cone of Fisher length 3.
- Check the build against an objective computed on a different path:
  - `res.conditional_capacity` should equal `mutual_information(prior)` at budget `N + 1`
    minus the same at budget `N`.
  - That difference should be at least as large as the same difference for `p*` and for
    `p_U`.
- Add a reference for the Gaussian build. On a 3- to 5-point grid in the 1-D channel,
  maximise `I(Θ; X̄_{N+1}) − I(Θ; X̄_N)` over the simplex with scipy (each term is a 1-D
  quadrature), and compare the weights to `1e-4`. Alternatively, route T18 through
  `build_plat`'s own Blahut–Arimoto core.

> M: let's add these tests

> C: Agreed; tests and stubs. T16(a)–(c) run where §5.4 puts them: `N ∈ {0, 1, 4}` in the
> 1-D cone with `W/σ = 3`, and at the cheap cell. T16 gains: `conditional_capacity` equals
> `mutual_information` of `res.prior` at budget `N + 1` minus the same at `N`; that
> difference is at least as large for `p_lat` as for `p*` and `p_U`; and a reference for
> the Gaussian build: in the 1-D cone, on a 3- and a 5-point grid, the test maximises
> `I(Θ; X̄_{N+1}) − I(Θ; X̄_N)` over the simplex with scipy (concave in the weights, §4.2),
> each term by 1-D quadrature, and compares the weights to `1e-4`. T18 and the Komaki eye
> test call `build_plat` on a binomial model, as §5.2 (T18) and §5.3 already say, so they
> exercise the Gaussian build's update: the separate `build_plat_binomial` stub goes, and
> `models.py` gains a binomial-model stub.

---

### F3: The privileged-information priors and the round robin's samplers are not checked against their definitions [severity: high]

**Test**: `test_t4_jeffreys_normalises`, `test_t15d_exp_decay_rankings_normalise_and_differ`,
`test_t15e_stiffest_ranking_ignores_transversal`, `eye_test_002_foreign_q_prediction.py`;
missing: `p_LN`'s law and density, `p_U`'s normaliser, and the samplers of `p_U`, `p_LN`,
`p_LN^*`, `p_ref` and exp-decay's `p_J`.

**Concern**:
- **`p_LN`.** A&M's prior (each log decay time `N(0, 1)`, sorted) is never compared with
  its definition. A `p_LN` normal in `ξ` instead of `θ` passes. So does a density in `ξ`
  that omits the Jacobian `dθ/dξ = 1/(ξ(−log ξ))`, which only T20 could notice, and only if
  another prior's mixture happens to lie closer to the true law. T23 needs only `I`, which
  §4.2 estimates from draws. The helper `xi_from_log_time` in `spec002_common.py` is never
  called. The eye test plots `p*` and `p_J` only, though A&M's Fig. 5 also plots the
  log-normal.
- **`p_ref` in exp-decay.** It is checked only to normalise and to differ pairwise. Any
  three distinct normalised densities pass, Jeffreys among them, and so does
  slowest-first swapped with fastest-first. T15(e) passes if `build_pref` ignores
  `transversal`.
- **Normalisation.** Every normalisation check is relative to `p_U`: T4 tests
  `E_U[p_J/p_U] = 1` and T15(d) tests `E_U[p_ref/p_U] = 1`. `p_U`'s absolute density is
  never asserted. So `p_U`, `p_J` and `p_ref` can all be off by one common factor and
  pass. For example, all three normalised over the cube `[0, 1]^D` rather than the ordered
  region give half the true density at `D = 2`. That matters wherever a density is used
  directly: importance sampling and Bennett's method for `m_π` (§4.4), and `p_ref`'s
  construction.
- **Samplers.** Each round-robin row is drawn from its prior's sampler (T14(a)). Only
  `p_J`'s `θ_1`-marginal in the cone is checked against a law (T4). Unchecked: the
  cross-section of those draws, exp-decay's Jeffreys sampler, and the samplers of `p_U`,
  `p_LN`, `p_LN^*` and `p_ref`. T20 notices a sampler that drifts from its own mixture
  only when the drift brings it nearer some other prior's mixture.

**What would resolve it**:
- **`p_LN`.** Run a KS test of `log_time_from_xi` of `p_LN`'s sorted draws against the
  order statistics of `N(0, 1)`. Check `p_LN.log_density` against the change-of-variables
  formula at a few `ξ`.
- **`p_ref` at `D = 2`.** Compute a known answer in the test. Slowest first has
  `ψ = ξ_2` and `λ = ξ_1`. `g_11` depends on `ξ_1` alone, so the conditional Jeffreys
  factor and the Schur factor of `[^3-schur]` reduce to nested 1-D quadratures. The same
  holds for fastest first, with `ψ = ξ_1`. Compare each ranking with its own reference at
  a few points; that also pins the labels.
- **T15(e).** Assert that the traced `ψ` differs between the two transversals.
- **`p_U`.** Assert `log p_U = log D!` on the ordered unit cube, and `−log W` in the cone.
- **Samplers.** For each continuous prior at the cheap cell, KS-test a 1-D marginal of the
  draws against the marginal of its own `log_density`, by quadrature.
- **Eye test.** Add `p_LN` to the eye test.

> M: let's do these tests

> C: Agreed; tests, and the spec's eye test (§5.3, §5.3.1). Tests: `p_LN`'s draws, mapped
> by `log_time_from_xi`, pass a KS test against the order statistics of `N(0, 1)`, and
> `p_LN.log_density` matches the change of variables from `θ` to `ξ` (factor
> `1/(ξ(−log ξ))`) at a few `ξ`. At `D = 2` the test computes each ranking's `p_ref` from
> `[^3-schur]` by nested 1-D quadratures (`g_11` depends on `ξ_1` alone) and compares it
> with `build_pref` at a few points, which also pins the labels. T15(e) asserts that the
> traced coordinate differs between the two transversals. Absolute normalisation:
> `log p_U = log D!` on exp-decay's ordered `Θ`, and `−log W` in the cone. Samplers: at
> the cheap cell, a KS test of one 1-D marginal of each continuous prior's draws against
> the marginal of its own `log_density`, by quadrature. Spec: §5.3 adds `p_LN` to the eye
> test. A&M's Fig. 5 plots it [read: A&M Fig. 5]: its `I` stays near 3 bits for `D ≤ 3`,
> below Jeffreys', and falls more slowly, crossing Jeffreys between `D = 3` and 5. The
> acceptance adds `I_{p*} ≥ I_{p_LN}` at every `D`, by `p*`'s optimality.

---

### F4: Question 3's machinery is untested, and two slow tests call nested natures in a model of the wrong dimension [severity: high]

**Test**: missing: `nature_log_marginal` for nested and stress natures, `submodel_floor`,
and `score_cell` with a submodel agent against the `D_max` nature;
`test_t21b_insurance_inequality`, `test_t22c_covered_fraction_matches_the_interval`,
`test_t8_floors_and_matched_prior`.

**Concern**: Question 3 (§2.3) reads each prior's loss against `D` on natures that live
once, at `D_max = 26`, beside the submodel's own floor. T14(b) pins the nature's law at
`D_max`, and T14(c) the submodel's map. Nothing tests the rest:
- the floor's marginal `m_q` (§4.3: an integral over `θ_1` with per-coordinate
  normal-CDF differences, or over the shared rate for few rates). T14(f) only averages it
  without checking it.
- `submodel_floor` (`qfamily.py`), which no test calls.
- `score_cell` scoring a `D`-agent's priors on `x̄` drawn from the `D_max` model.

T8(a)'s `R ≥ I_q`, the first guard on a floor, runs only in `p_U`'s world. So these pass:
a nested floor off by any constant, a submodel floor with the wrong `N` or `σ`, and an
agent scored against a nature redrawn in its own `D`-model.

That last one is the drift §2.3 and `[^2-fixed]` removed, and T21(b) and T22(c) invite it.
They call `("nested", "thin"/"thick")` with `cone_model(6)`, although `sample_nature`
documents that for these natures "`model` is the `D_max` model". An implementation that
makes those slow tests pass by defining the halves in any model's own dimension is the
per-`D` nature the spec rejects.

The stress natures' floors are untested too: the interior's, by the same `θ_1` integral,
and the vertex's, by quadrature.

**What would resolve it**:
- Check `nature_log_marginal` against brute-force Monte Carlo over `θ ∼ q`,
  `log mean_j p(x̄|θ_j)`, at a few `x̄`, for thin, thick, few rates and interior.
- Check `submodel_floor` against `N‖y(θ) − y(θ^{(D)})‖²/(2σ²)` computed in the test, at
  `N = 4`.
- Score one nested cell through `score_cell` with
  `agent = submodel(cone_model(26, falloff=0.5), D)`. Assert that the nature's draws, and
  so its floor, are the same at every `D` under one seed.
- Rewrite T21(b) and T22(c) on submodel agents, or on round-robin and stress natures.
- Extend T8(a) to every nature of the cheap cell and of one cone cell.

> M: how expensive is the brute force MC? which option makes more sense for T21(b) and T22(c)? The rest seems reasonable.

> C: Resolved in chat; MB chose round-robin and stress natures for T21(b) and T22(c).
> Cost: brute-force Monte Carlo over `θ ∼ q`, 10⁶ draws, takes about 0.3 s per `x̄` with
> a standard error of 0.0025–0.005 nats (measured on the thin and thick halves at
> `D_max = 26`, `σ_eff ∈ {1, ½}`, and on few rates at the cheap cell), so it runs in the
> fast suite. Why not submodel agents: (3.2.3) assumes `R_N^θ(p*) ≤ C_N`, which holds only
> at states in the agent's own model, so a `D = 6` agent facing a nested nature could fail
> T21(b) without a bug. Tests: `nature_log_marginal` against that Monte Carlo at three `x̄`
> for thin, thick, few rates and interior, within 4 of the test's standard errors;
> `submodel_floor` against `N‖y(θ) − y(θ^{(D)})‖²/(2σ²)` at `N = 4`; one nested cell
> through `score_cell` with the agent `submodel(cone_model(26, falloff=0.5), D)`, asserting
> that the nature's draws and floor are the same at every `D` under one seed; T21(b) on the
> own worlds of `p*`, `p_J` and `p_U` and the interior stress nature, at `D = 6`; T22(c) on
> `p_U`'s own world and the interior stress nature, with the expected mass in closed form
> (`(W − θ_lo)/W`, and normal distribution functions); T8(a) on every nature of the cheap
> cell and of one cone cell. Spec: §5.2's T21(b) holds "on every nature in the agent's own
> model"; §3.2 states that (3.2.3) is guaranteed for those natures only; §6.1's insurance
> figure marks nested natures scored by a smaller agent as outside that guarantee.

---

### F5: Monte-Carlo errors come from the code under test and are never checked [severity: high]

**Test**: missing; the tolerances of `test_t1_redundancy_decomposition`,
`test_t7b_pstar_method_agreement`, `test_t7c_budget_through_the_noise`,
`test_t8_floors_and_matched_prior`, `test_t8_qbar_wins_the_row_average_and_splits_the_mean`,
`test_t17_one_step_score`, `test_t20_round_robin_mismatches_are_non_negative` and
`test_t21b_insurance_inequality`.

**Concern**: Every Monte-Carlo agreement and inequality in the suite takes its tolerance
from errors the implementation reports: `R_mcse`, `r_mcse`, `floor_se` and `mis_se`. No
test checks them.

Suppose the MCSE is computed as the standard deviation of the draws, without the division
by `√S_q`. At `S_q = 400` it is then twenty times too large. T1's and T17's acceptance
windows grow to several nats, T20's floor drops to about −5 nats, and the tests above pass
almost any estimate.

The same errors decide §3.7's verdict ("beyond Monte-Carlo error"), the beyond-the-cap
label, and §5.4's rule for raising `S_q`. The spec reports every gap with its error. That
error, of a difference under common random numbers, is untested too.

**What would resolve it**:
- Assert `R_mcse[π] = std(draws_R[π], ddof=1)/√S_q`, and the same for `r`. `CellScores`
  already exposes the draws.
- For `matched_floor` and `marginal_mismatch`, compare the reported error with the spread
  of the estimate over about 20 seeds.
- Check that a gap's error comes from per-draw differences. For `p*` against `p*_{10N}`
  it should be much smaller than the root-sum-square of the two scores' errors.

> M: we should do these

> C: Agreed; tests, and one sentence of spec (§4.4). Tests: `R_mcse[π] =
> std(draws_R[π], ddof=1)/√S_q`, and the same for `r`; the errors that `matched_floor` and
> `marginal_mismatch` report agree within a factor of 2 with each estimate's spread over 20
> seeds (slow); and the error of `p*`'s gap to `p*_{10N}` is the MCSE of the per-draw
> differences, well below the root-sum-square of the two scores' errors. Spec: §4.4 says
> how a gap's error is computed (a cell's priors share its draws, so the error of a
> difference is the MCSE of the per-draw differences). It now says only "MCSE of each",
> and §3.7's verdict rests on gaps.

---

### F6: The score's level is never checked against an independent value [severity: high]

**Test**: `test_t1_redundancy_decomposition`,
`test_t7a_continuous_quadrature_matches_a_fine_atom_sum`,
`test_t8_qbar_wins_the_row_average_and_splits_the_mean` (part c),
`test_t17_one_step_score` (part b); missing: marginals of continuous and cloud priors
other than the flat `p_U`, and the tapered hypercone's marginals.

**Concern**:
- **T1 is an identity.** T1 estimates three quantities: `E[log p(x̄|θ) − log m_π]`,
  `E[log p(x̄|θ) − log m_q]` and `E_{m_q}[log m_q − log m_π]`. It checks that the first is
  the sum of the other two. By linearity that holds for any functions standing in for
  `log m_π`, `log m_q` and `log p`. So it passes for a mixture at the wrong noise, for a
  quadrature that drops the prior density, and for an oracle term with the wrong
  normaliser. It only checks that three estimators draw the same `(θ, x̄)`. Its docstring
  calls it "the tightest check that the score means what §2.1 says", which is more than an
  identity can check.
- **T8(c) and T17(b) are identities too.** T8(c) is the same identity taken across rows:
  it holds for any `log m_q̄`, provided `q̄`'s sampler is the row mixture. T17(b) is its
  one-step version.
- **The only independent anchors for `log m_π` are in T7(a).** For discrete priors it uses
  an exact atom sum, which is good. For continuous priors it uses only the flat `p_U`,
  which passes a quadrature that ignores the prior density, since that density is
  constant.
- **Nothing else checks the marginals.** Nothing checks `m_{p_J}`, `m_{p_LN}`, `m_{p_ref}`
  or `p_proj`'s cloud mixture. No fast test scores the tapered hypercone at `D > 1`.
  T2 runs with the taper off, where `p_J = p_U` share one integral, so an error in the
  cone's cross-section integral (§4.3: normal-CDF differences with widths `r φ^{μ−2}`)
  cancels there. T7(c) is at `D = 1`. So a cone marginal with the wrong widths passes the
  fast suite.

**What would resolve it**: Add known answers computed in the test:
1. In the 1-D cone at `σ = W/3`: `R_N^q(π)` for `q = p_U` and `π ∈ {p_U, two atoms at 0
   and W}`, by deterministic quadrature, against `score_cell` within its MCSE (checked as
   in F5).
2. In the tapered cone at `D = 4` to 6: `log m_{p_J}(x̄)` and `log m_{p_U}(x̄)` at a few
   `x̄`, against brute-force Monte Carlo over `θ`, to `1e-3`. For Jeffreys,
   `θ_1 = W·U^{1/D}` and the cross-section is uniform.
3. T7(a)'s continuous case for `p_J` and `p_LN`, not only for `p_U`.

Keep T1, T8(c) and T17(b) as consistency checks, and say so in their docstrings.

> M: these changes sound very reasonable

> C: Agreed; tests, and §5.2's description of T1. Tests: (1) a known answer in the 1-D cone
> at `σ = W/3`: `R_N^q(π)` for `q = p_U` and `π ∈ {p_U, two atoms at 0 and W}` by
> deterministic quadrature in the test, against `score_cell` within its MCSE (checked by
> F5); (2) in the tapered cone at `D = 4` and 6, `log m_{p_J}(x̄)` and `log m_{p_U}(x̄)` at a
> few `x̄` against brute-force Monte Carlo over `θ` (Jeffreys drawn as `θ_1 = W U^{1/D}`,
> cross-section uniform), within 4 of the test's own standard errors rather than the
> finding's `1e-3`: 10⁶ draws give about 0.003 nats in 0.3 s per `x̄` (measured at
> `D_max = 26`; see F4), and `1e-3` would take 10⁸; (3) T7(a)'s continuous case for `p_J`
> and `p_LN`, not only `p_U`. T1, T8(c) and T17(b) stay, with docstrings calling them
> consistency checks. Spec: §5.2 drops "the tightest check that the score means what §2.1
> says" from T1, an identity of its estimators, and names (1) as T1's anchor.

---

### F7: T12's tolerances and cells live in fixture files written with the implementation [severity: high]

**Test**: `test_t12a_exp_decay_map_and_metric`, `test_t12b_pstar_matches_atomicpriors`,
`test_t12c_capacity_through_repeat`, `test_t12d_mutual_information_of_a_fixed_prior`,
`test_t12e_pproj_port_matches_transtrum`.

**Concern**: T12 is the suite's only external anchor for five things:
- the exp-decay map: T13(a, b) check only finite-difference consistency and permutation
  symmetry, so nothing else pins the `1/D` amplitudes or the 26 times in `[1, 5]`;
- `p*`'s actual capacity: T3 checks only its equalizer;
- `C_N` at `N > 1` in exp-decay;
- the mutual-information estimator;
- `p_proj`'s law (F14).

Yet every tolerance is read from the JSON: `tol`, `atom_tol`, `weight_tol`, `B_tol`,
`edge_width` and `edge_tol`. So is every cell: `σ`, `D`, the number of states, and the size
of `transtrum`'s cloud, which sets the KS tests' power. The JSON is written by
`generate.jl`, which, per the commit and the test file's header, comes with the
implementation.

So the suite as reviewed fixes no bar. A fixture at another `σ`, a cloud of 50 points, or
`tol = 0.1` lets T12 pass for a wrong map or a wrong prior, and nothing in the tests would
show it.

Two smaller gaps in T12(e):
- It checks only the coinciding-rates edge, not "rates outside the window" (spec T12(e)).
- `transtrum` runs in the unclamped log-rate parametrisation
  (`resources/AtomicPriors.jl/src/max/sample.jl`, `_transtrum`: "expected an unclamped
  prior!"). So `generate.jl` must map `θ̂` to sorted `ξ`, contrary to §5.5's "no change of
  variables beyond sorting the rates". A failure from that mismatch invites loosening
  `edge_tol`.

**What would resolve it**:
- Pin the tolerances and cells in `spec002_common.py`, from §5.5.
- Assert the fixture's metadata: `σ = 0.1`, `D`, `N`, at least 10 states, the cloud size,
  the coordinate system, and the provenance fields.
- Add an in-suite known answer for the exp-decay map: `y(ξ = (a, …, a)) = a^t` and
  `y(0, 1) = ½`, at the 26 times.
- Add the edge masses near `ξ = 0` and `ξ = 1` to T12(e).

> M: we should add these

> C: Agreed; tests, and spec §5.5. Spec: `generate.jl` no longer writes tolerances; §5.5
> fixes the tolerances and the cells (values proposed in Stage 3b, flagged auto-chosen),
> and `spec002_common.py` pins them; the JSON holds values and metadata only. §5.5's bridge
> is corrected for (e): `transtrum` needs the unclamped log-rate coordinate [read:
> `resources/AtomicPriors.jl/src/max/sample.jl`, `_transtrum`: "expected an unclamped
> prior!"], Julia's `θ = log k`, so `generate.jl` maps the cloud to sorted
> `ξ = exp(−exp θ)`; (a)–(d) use the compact `ξ` and need only sorting. Tests: T12 asserts
> each fixture's metadata before its values (`σ = 0.1`, `D`, `N`, at least 10 states, the
> cloud size, the coordinate system, the AtomicPriors commit, the Julia version, the seed);
> T13(b) gains the in-suite known answers `y(a, …, a) = a^t` and `y(0, 1) = ½` at the 26
> times; T12(e) adds the mass near `ξ = 0` and near `ξ = 1` (rates outside the window) to
> the coinciding-rates edge.

---

### F8: T17's tolerance is larger than the one-step score it checks [severity: high]

**Test**: `test_t17_one_step_score`.

**Concern**: T17(a) accepts `r_N` within `4·√(se_r² + se_{R_N}² + se_{R_{N+1}}²)` of
`R_{N+1} − R_N`, treating the three estimates as independent. Under the common random
numbers the test sets up, `R_N` and `R_{N+1}` are almost perfectly correlated.

I simulated the test's cell: exp-decay, `D = 2`, `σ = 0.1`, `N = 2`, nature `p_U`, a grid
approximation of `p_J`, `S_q = 400`, three seeds (computed by the reviewer):

| Quantity | Value |
|---|---|
| `R_N` | ≈ 3.5, error 0.06 |
| `R_{N+1} − R_N` | ≈ 0.32, error under CRN 0.005 |
| `r_N` | 0.26–0.41 |
| T17(a)'s tolerance | 0.35–0.38 nats |

The tolerance is larger than `r_N` itself. `r_N ≡ 0` passes for all three seeds, and so
does `x′` drawn and scored at `σ_eff` instead of `σ` (`r ≈ 0.48–0.67`). That is the bug
the docstring says the test catches.

T17(b) is an identity of the estimators (F6). So the one-step score, one of the spec's two
scores, is effectively untested. The posterior predictive `log_predictive` has no direct
test, though for a discrete prior §4.4 gives it as an exact atom sum.

**What would resolve it**:
- Add T7(a)'s analogue for the posterior predictive. For a `DiscretePrior` at `N = 4`,
  compare `log_predictive` with
  `logsumexp_a[log w_a + log N(x̄; y_a, σ_eff²) + log N(x′; y_a, σ²)] − log m(x̄)`. That
  pins both noise levels exactly.
- In T17(a), use the error of the CRN difference `R_{N+1} − R_N`, not the root-sum-square
  of the two scores' errors. In my runs that brings the tolerance to about 0.14, which
  rejects both bugs, though one seed only barely.
- Raise `S_q` until the error is under a tenth of `r_N`.

> M: let's do these

> C: Agreed; tests only, plus one check of my own. (1) T7(a)'s analogue for the posterior
> predictive: for a `DiscretePrior` at `N = 4`, `log_predictive` equals the finding's exact
> atom sum. (2) T17(a)'s tolerance is the error of the per-draw difference `R_{N+1} − R_N`
> under common random numbers, and the test asserts that this error is below a tenth of
> `r_N`, which also checks that the two runs share their draws; `S_q` is raised until it
> is. (3) Added: per draw, with `x̄_{N+1} = (N x̄_N + x′)/(N + 1)`,
> `log_predictive(x′ | x̄_N) = log m_{N+1}(x̄_{N+1}) − log m_N(x̄_N)
> − (m/2) log(2πσ²(N+1)/N) − N‖x′ − x̄_N‖²/(2(N+1)σ²)`, each marginal at its own noise
> `σ/√n`. It holds for any prior, continuous ones by quadrature, to numerical precision
> (checked on a discrete prior: 4e-15 over 200 draws), so it pins both noise levels with
> no Monte-Carlo slack. T17(b) stays as a consistency check (F6).

---

### F9: The noise-dependent pieces are tested only at `N ≤ 1`, so `σ` and `σ_eff` are interchangeable there [severity: medium]

**Test**: `test_t13a_metric_matches_finite_differences`,
`test_t13c_hypercone_covolume_and_widths`, `test_t15a_cone_schur_complement`,
`test_t21a_mass_bound`, `test_t22a_split_terms_vanish_on_the_diagonal`,
`test_t23_tuned_lognormal_is_a_local_maximum`; missing: §2.1's invariance of `R_N` in
`σ/√N`.

**Concern**: The cheap cell and the cone base cell have `N = 1`, where `σ_eff = σ`. Any
confusion between `σ` and `σ_eff` is therefore invisible in:
- the Fisher metric and the widths (T13, T15(a));
- the radius of `A(θ)` in `mass_near` (T21(a));
- `p_LN^*`'s objective (T23);
- the noise of the moment-matched predictive (T22(a));
- the candidate set's Fisher spacing.

T13(a) is doubly blind: it compares `fim` with `J^T J / model.sigma_eff**2`, using the
model's own `sigma_eff`. Three docstrings claim checks their tests cannot make: T13(a) ("a
slip in `sigma_eff`"), T21(a) ("a wrong `sigma / sqrt(N)`") and T23(b) ("`I` estimated at
the wrong noise"). The tests at `N > 1` (T7(c), T12(c), T17, T19) cover `p*`'s build and
`R`, not these pieces.

Nor does the suite test the spec's own invariance (§2.1): `R_N` depends on `σ` and `N`
only through `σ/√N`, and `r_N` does not. That check is cheap and strong. It would catch,
among other things, a score that draws `x̄` at `σ`.

**What would resolve it**: Rerun the cheap-cell tests at `(σ, N) = (0.2, 4)`. That keeps
`σ_eff = 0.1`, and so the same priors. Write T13(a)'s reference as `σ/√N`. Add the
invariance check: `score_cell` at `(0.1, 1)` and at `(0.2, 4)`, with the same priors and
seed, gives identical `R` arrays and different `r` arrays.

> M: yes, do these

> C: Agreed; tests, and §5.4's list of cells. Tests: the tests of the noise-dependent
> pieces (T13(a, c), T15(a), T21(a), T22(a), T23 and the candidate set's spacing) also run
> at a twin of their cell with the same `σ_eff` and `N = 4`: `(σ, N) = (0.2, 4)` for the
> cheap cell, `(2, 4)` for the cone's base cell. T13(a)'s reference is written from the
> cell's `σ` and `N`, not from `model.sigma_eff`. New: §2.1's invariance, `score_cell` at
> `(0.1, 1)` and `(0.2, 4)` with the same priors and seed gives the same `R` per draw to
> floating-point precision and a different `r`. The docstrings of T13(a), T21(a) and
> T23(b), which claim a `σ_eff` check, then hold. Spec: §5.4 names the twin cells.

---

### F10: The row summaries of §2.4 have no test [severity: medium]

**Test**: missing: `gap_J`, `gap_pi`, `gap_pair`, `gap_budget` with `gap_coarse` and
`gap_fine`, `gap_tune`, `delta_R_pref`, `relatives_world`, the exchange, and the trend on
the cast present at every `D`.

**Concern**: These summaries are machinery, not results. §3.7's verdict reads off `gap_J`
and its error, and `gap_pi` "stands beside it". Unlike `beyond_cap` (T22(b)) and the
failure map (T22(e)), none of them is unit-tested. Footnote `[^2-max]` records that
`gap_pi` was once specified as `min δS`, the gap to the *worst* privileged-information
prior.

Wrong implementations that pass:
- a `gap_pi` with that same error;
- a `gap_pi` that keeps a privileged-information prior in the minimum in its own world,
  which §2.4 excludes;
- one that drops a `p_ref` ranking;
- an exchange with its sign flipped;
- a `relatives_world` flag that omits `p_LN^*`.

**What would resolve it**: Add toy-dict unit tests in the style of T22(e):
- a row where choosing min or max changes `gap_pi`;
- `p_LN`'s own world, where excluding `p_LN` changes it;
- exp-decay with two `p_ref` rankings;
- the exchange's antisymmetry;
- `gap_budget = max(gap_coarse, gap_fine)`;
- `relatives_world` true for exactly `p*_{N/10}`, `p*_{10N}`, `p_lat`, `p_proj` and
  `p_LN^*`.

> M: ok let's add the tests for these functions, as per the chat about this

> C: Agreed, after the chat explanation of the row summaries; tests and stubs. Hand-made
> score tables with known answers, in the style of T22(e), no sampling: `gap_J` is not
> formed in Jeffreys' own world; `gap_pi` takes the best (lowest-scoring)
> privileged-information prior on a row where min and max differ, leaves the row's own
> prior out in `p_LN`'s world, and counts both `p_ref` rankings in exp-decay;
> `gap_budget = max(gap_coarse, gap_fine)`; `gap_pair`, `gap_tune` and `delta_R_pref`
> against hand-computed values; the exchange is antisymmetric, with §2.4's sign on one
> hand-made pair; `relatives_world` is true for exactly `p*_{N/10}`, `p*_{10N}`, `p_lat`,
> `p_proj` and `p_LN^*`; and the every-`D` trend drops a prior missing at one `D`. The row
> summaries and the report-time readings (exchange, trends) get stubs in `diagnostics.py`
> for the tests to call.

---

### F11: The §3.3 split is checked on its formula only, and T22(a) compares a predictive with itself [severity: medium]

**Test**: `test_t5_gaussian_kl_split_matches_numeric_kl`,
`test_t5_gaussian_kl_split_vanishes_when_matched`,
`test_t22a_split_terms_vanish_on_the_diagonal`.

**Concern**:
- **T22(a).** It passes `moment_matched_predictive`'s `(μ, Σ)` as both arguments of
  `gaussian_kl_split`. That is zero for any `(μ, Σ)`, so the test passes even when
  `moment_matched_predictive` returns zeros and the identity. It never touches the
  diagnostic's pipeline: the row's matched predictive, other rows, other priors. §5.4
  places T22 "over all rows of that cell".
- **T5.** It checks only the half-sum of the two terms. A split that swaps them passes both
  T5 tests, as does one that computes the shift with `Σ_q^{-1}` and folds the difference
  into the spread. Yet which term carries a prior's mismatch is the diagnostic's whole
  content (§3.3).
- **`moment_matched_predictive`.** It is never compared with its definition. For a
  discrete prior that is mean `Σ_a w_a(x̄) y(θ_a)` and covariance `σ²𝟙 + Cov[y]`. Its noise
  term must be `σ`, the noise of `x′`, which `N = 1` hides (F9).

**What would resolve it**:
- In T5, add a pure-shift case (`Σ_π = Σ_q`: spread 0, shift the Mahalanobis distance)
  and a pure-spread case (`μ_π = μ_q`: shift 0).
- Test `moment_matched_predictive` at `N = 4` for a one-atom prior, which gives
  `(y(θ_a), σ²𝟙)`, and for a two-atom prior, against the explicit posterior weights.
- Make T22(a) read the cell's `mean_shift` and `spread_mismatch` for the own prior over
  every row of the cheap cell. Assert both are nonzero for a prior that is away.

> M: let's do these

> C: Agreed; tests only. T5 gains a pure-shift case (`Σ_π = Σ_q`: spread 0, shift the
> Mahalanobis distance) and a pure-spread case (`μ_π = μ_q`: shift 0), so a split that
> swaps or mixes the two terms fails. `moment_matched_predictive` is tested at `N = 4`: a
> one-atom prior gives `(y(θ_a), σ²𝟙)`, and a two-atom prior gives the mean and covariance
> under its posterior weights, computed in the test, with noise `σ`, not `σ_eff`. T22(a)
> reads the cell's `mean_shift` and `spread_mismatch` over every row of the cheap cell:
> both vanish for each prior on its own row and are nonzero for a prior that is away.

---

### F12: T6 passes the leading-order formula itself, and the mode [severity: medium]

**Test**: `test_t6_hypercone_jeffreys_deviation`,
`test_t6_hypercone_jeffreys_mode_is_the_exact_root`.

**Concern**: The tolerance is the full size of the first neglected term, `(D − 1)²/x_1³`.
A `hypercone_jeffreys_mean` that returns `x_1 + (D − 1)/x_1` has zero error and passes at
every `D`. So does one that returns the mode. Each column below is that function's error
against `(D − 1)/x_1`, by quadrature, computed by the reviewer:

| `D` | true mean | mode | tolerance |
|---|---|---|---|
| 6 | 0.0187 | 0.0228 | 0.025 |
| 11 | 0.0773 | 0.0839 | 0.1 |
| 26 | 0.4185 | 0.4289 | 0.625 |

The docstring quotes the computed deviations (0.019, 0.077, 0.418) but does not assert
them. T6(iii) compares the closed-form mode with that same closed form.

**What would resolve it**: Assert the departure from `(D − 1)/x_1` against the quadrature
values above, to `1e-3`, or compute the mean in the test with `scipy.integrate.quad` to
`1e-6`. Either separates the mean from the mode, which differ by 0.004 at `D = 6`. For the
mode, check that the derivative of `−½(x_1 − θ)² + (D − 1) log θ` vanishes there, and that
it is a maximum.

> M: let's implement the suggestion

> C: Agreed; tests only. T6 computes Jeffreys' posterior mean in the test with
> `scipy.integrate.quad` and compares `hypercone_jeffreys_mean` with it to `1e-6`. The
> departures from `(D − 1)/x_1` are −0.0187, −0.0773 and −0.4185 at `D = 6, 11, 26`
> (reproduced here by quadrature), against −0.0228, −0.0839 and −0.4289 for the mode, so
> the test separates the two. T6(iii) checks the mode by the derivative of
> `−½(x_1 − θ)² + (D − 1) log θ` vanishing there with a negative second derivative,
> instead of by its own closed form.

---

### F13: T10 builds the cast once [severity: medium]

**Test**: `test_t10_seed_determinism`.

**Concern**: P10 says that two runs with one seed give identical score arrays. The test
builds the cast once and checks only that `score_cell` is deterministic. It cannot see a
builder that draws from global state: `p_proj`'s ensemble chain, `p_LN^*`'s
common-random-number search, or the Julia path, whose RNG the spec plans to seed for T10
(revision log, 2026-06-06).

Nor can it see a `score_cell` that ignores its `rng` and uses a fixed internal seed. That
passes T10, but every cell then gets the same stream, contrary to §4.4's one child stream
per cell, and the cells' Monte-Carlo errors become correlated. Floors and mismatches are
not compared either.

**What would resolve it**: Inside the test, build the cast twice from the same seed, and
compare score arrays, floors and mismatches. Assert that a different seed changes
`draws_R`.

> M: yes, good suggestion.

> C: Agreed; tests only. T10 builds the cast twice from the same seed inside the test,
> and compares the score arrays, floors and mismatches bit for bit; a different seed must
> change `draws_R`.

---

### F14: `p_proj`'s law is checked only by T12(e) [severity: medium]

**Test**: `test_t11_pproj_normaliser_is_finite`, `test_t11_pproj_projection_recovers_mle`,
`test_t11_pproj_information_below_capacity`.

**Concern**: Each of the three T11 tests is weak:
- **Normaliser.** Any finite number passes, including 0.
- **Information.** Any prior passes, given a correct estimator, since `p*` maximises `I`.
  A point mass gives `I = 0 ≤ C_N`.
- **Projection.** It places data 0.01 noise units from the manifold. The case that makes
  NML what it is never comes up: data in the halo outside a convex boundary, projecting
  onto a face. So an unconstrained least-squares fit in `ξ` that leaves `[0, 1]` passes, as
  does one that returns unsorted `ξ`.

So a `build_pproj` that returns draws of `p_U` passes T11, T8, T10 and T20. Only T12(e)
could tell, and its tolerances are set by the fixture (F7). §5.4 runs T11 "over the
`D`-sweep"; the suite runs it at `D = 2` only.

The 1-D bounded channel has a closed form. `Z = 1 + W/(σ_eff√(2π))`, which is 2.197 at
`W = 50`, `σ = 50/3`, checked by quadrature (computed by the reviewer). `p_proj` is then
Quinn's slab-and-spike: mass `1/(2Z) = 0.228` at each end, and a uniform slab between.

**What would resolve it**: In `cone_model(1, sigma=50/3)`, assert:
- `nml_log_normaliser = log 2.197`, within MC error;
- the cloud's fractions at exactly 0 and exactly `W` are each 0.228, within a binomial
  error inflated for autocorrelation;
- the interior is KS-uniform;
- `mle_project` of `x < 0` and of `x > W` returns the endpoints.

In exp-decay, project data from beyond the manifold and assert that `θ̂` lies on a face
inside the ordered box (coinciding `ξ`, or `ξ ∈ {0, 1}`). Run T11 over `D_SWEEP_GRID`.

> M: yes, do these

> C: Agreed; tests only. In `cone_model(1, sigma=50/3)`: `nml_log_normaliser` equals
> `log(1 + W/(σ√(2π))) = log 2.197` within its Monte-Carlo error (the closed form is ½ for
> each tail plus `W/(σ√(2π))` for the slab); the cloud's fractions at exactly 0 and at
> exactly `W` are each `1/(2Z) = 0.228`, within a binomial error inflated by the chain's
> autocorrelation (batch means); the interior is KS-uniform; `mle_project` maps `x < 0` and
> `x > W` to the endpoints. In exp-decay, data placed beyond the manifold project to a face
> of the ordered box (coinciding `ξ`, or `ξ ∈ {0, 1}`), sorted. T11 runs over
> `D_SWEEP_GRID`, as §5.4 says.

---

### F15: The sharpened-vertex nature is checked for support, not law [severity: medium]

**Test**: `test_t14e_vertex_nature_lies_on_faces_near_v`.

**Concern**: §4.3 defines this nature as `θ` uniform, by area in `θ`, on the parts of the
base face and of the lateral faces `θ_μ = 0` that lie within `ρ` of `v`. The test checks
only that each draw lies on some such face, within `ρ`. A sampler that returns
`v = (W, 0, 0)` for every draw passes, as does one that uses only the base face. This is
the stress nature aimed at `p_proj` (§2.3, §3.4), so its law decides what the pairwise
gaps there measure. Its floor is untested (F4), and the test is blind to the warp (F1).

**What would resolve it**: Assert each face's share of the draws against the ratio of the
faces' `θ`-areas within `ρ`, which the test can compute at `D = 3`. On each face, KS-test
a 1-D statistic, such as the distance from `v`, against its law under area-uniform
sampling.

> M: sounds reasonable

> C: Agreed; tests only. At `D = 3` the test computes the `θ`-areas of the three face
> pieces within `ρ` of `v` (the base face and the lateral faces `θ_2 = 0` and `θ_3 = 0`;
> the warp keeps distances from `v`, so the pieces are those of the unwarped cone), and
> checks each face's share of the draws against them with a χ² test. On each face, the
> distance from `v` passes a KS test against its law under area-uniform sampling, computed
> in the test.

---

### F16: The eye test, run as shipped, cannot expose a wrong model [severity: medium]

**Test**: `eye_test_002_foreign_q_prediction.py`.

**Concern**: By default the script runs `D ∈ {1, 2, 3, 4}`. There, the spec's acceptance
criteria, `I_{p*} ≥ I_{p_J}` and `B(p*) ≈ 0 ≤ B(p_J)`, "hold by `p*`'s optimality"
(§5.3). They hold for any self-consistent channel, so a wrong map or metric passes too.

The features that would expose a wrong metric or a mis-normalised Jeffreys are `p*` flat
while Jeffreys falls, and `B(p_J)` rising. They appear only on the range extended toward
`D = 26`, which needs `--extended` and Julia.

Other gaps:
- The figure has no reference overlay, so review is qualitative.
- It omits `p_LN`, which A&M's Fig. 5 plots and nothing else checks (F3).
- Its Komaki panel uses `build_plat_binomial`, so the Gaussian `p_lat` has no eye test
  either (F2).

**What would resolve it**: Make approval require the `--extended` run, and say so in the
script's printout. Overlay A&M's Fig. 5 values at the computed `D`, read off the published
figure. Add `p_LN`, and a Gaussian `p_lat` against `D`.

> M: the eye test should be simple and fairly quick. Would it be so with the extended run? On the other hand we should be as close to the reference figures as possible.

> C: Resolved in chat. MB: nothing expensive in the eye test, so no `D = 26`. Spec (§5.3,
> §5.3.1) and the script: the default run, `D ≤ 4` on the candidate-set path, is the quick
> smoke check. Approval needs one extended run at A&M's own `D ∈ {5, 7, 11}` (through
> AtomicPriors.jl, OQ-1); it saves its numbers beside the figure, so the figure redraws
> without recomputing, and the printout says approval needs it. These `D` already show
> the features that expose a wrong metric: `I_{p_J}` falls from about 3.2 to 1.2 bits
> between `D = 3` and 11 while `I_{p*}` stays near 4.8, and `B(p_J)` rises from about 10
> to over 100 bits [read: A&M Fig. 5]. Both panels overlay A&M's points at
> `D ∈ {1, 2, 3, 5, 7, 11}`, digitised from the published figure by eye and tagged so.
> `p_LN` joins the figure (F3); the Komaki panel goes through `build_plat` (F2). No
> Gaussian `p_lat` panel, against the finding: it has no published figure, and
> `skills/write-math-spec.md` does not anchor an eye test on an unknown shape; F2's
> reference covers it. The first extended run is timed, and §5.3 records the time.

## Minor

- m1 — `test_t4_jeffreys_normaliser_converges_on_whole_manifold` — It passes if
  `quadrature_points` is ignored, since coarse then equals fine. In `ξ`, `√det g` is a
  bounded polynomial on a compact set, so finiteness is automatic. — Compare
  `log_normaliser` with an independent `scipy` `dblquad` over the ordered triangle at
  `D = 2`.
- m2 — `test_t7c_budget_through_the_noise` — It compares two code paths of the
  implementation, at one `D = 1` cell. A `literal_nfold` flag that reduces internally to
  `σ_eff` passes. — Compute the two-fold per-state KL in the test, by explicit Monte
  Carlo over `(x_1, x_2)`, and compare it with `per_state_redundancy`.
- m3 — `test_t13d_vertex_warp` — It checks the angle at a single `u`. It never checks that
  the image stays in `span(e_1, ê_⊥)` (§4.1: the warp "changes neither `u` nor `ê_⊥`"). —
  Assert that a base point along `e_2` maps with zero `e_3` component. Check the angle at
  several `u ≤ ρ/2`.
- m4 — `test_t14b_nested_cone_laws`, `test_t14e_interior_nature_is_truncated_normal` —
  The cross-section is KS-tested pooled across coordinates, which checks the marginal
  only. Draws with all cross-section coordinates equal pass. — KS-test per coordinate,
  and check that pairwise correlations are near 0.
- m5 — `test_t14a_round_robin_draws_come_from_the_prior` — It checks that labels are
  constant within a row, not that they differ between natures. One label shared by every
  nature passes, which breaks §6.3's re-split by nature. — Sample two natures and assert
  that their labels differ.
- m6 — `test_t14f_qbar_is_the_average_of_the_rows` — It checks "not itself a row" by
  object identity against the test's own two-element list, so the check cannot fail. —
  Assert that the cell's enumeration of rows excludes `q̄`.
- m7 — `test_t20_round_robin_mismatches_are_non_negative`,
  `test_t8_floors_and_matched_prior`,
  `test_t8_qbar_wins_the_row_average_and_splits_the_mean` — The slack is a multiple of the
  score's error, not of the mismatch's. The two are close for `p_J` against `p_U` (0.059
  and 0.052 nats, computed by the reviewer). For near-identical priors, such as `p*` and
  `p*_{10N}`, the mismatch's error can be far smaller, so the check is looser than it
  reads. — Use the mismatch errors that §6.3 requires.
- m8 — `test_t21a_mass_bound` — The test is one-sided. A `per_state_redundancy` that
  understates the loss passes, and so does a `mass_near` that understates the mass.
  `mass_near` is never compared with its definition. §5.4 places T21 in the hypercone at
  `D ∈ {6, 11, 26}`; the test runs at exp-decay's cheap cell. — Add a discrete-prior case
  at `N = 4` where `π(A(θ))` is a known sum of weights.
- m9 — `test_t21c_jeffreys_cone_loss_formula` — It exercises two helpers with the Jeffreys
  marginal hard-coded, not `build_jeffreys` or `per_state_redundancy`, so it cannot catch
  the pipeline errors spec T21 names. At `D = 6` the second-order term (at most 0.006
  nats) is below `rtol = 1e-2`: the uncorrected formula is off by 0.25–0.28 %. Only
  `D = 11` pins it, at `θ_1 = 40` and 45, by 1.08 % and 1.71 % against 1 % (computed by
  the reviewer). — Add `per_state_redundancy(p_J, cone_model(D), θ)` ≥ the relevant-datum
  divergence, minus MC error (dropping data cannot raise a KL), and tighten `rtol` to
  `2e-3`.
- m10 — `test_t22b_beyond_cap_label` — It tests the label as a pure function only.
  `capacity_gap` in `diagnostics.py` is never called, and spec T22(b)'s "`C_N` equals
  `p*`'s largest per-state divergence" is not asserted, so a capacity gap of 0 passes and
  makes the label too permissive. — Test `capacity_gap` against T3's largest `b_off`, and
  assert that the capacity equals the largest per-state divergence over the candidates.
- m11 — `test_t22e_failure_map_coordinates` — In both cases, the mapped prior's own
  mismatch is never the smallest among the priors that are away, so an implementation
  that forgets to exclude it passes. `r_N`'s conditional capacity and a nested row, which
  has no own prior, are not covered. — Add a case that maps `p_LN` (best rival 1.0,
  gap −0.6), and one with `own_prior=None`.
- m12 — `test_t22d_joint_width_ratio_is_recorded` — The spec has the ratio only recorded,
  which the test follows. But `joint_width2`, which feeds `mismatch_vs_D.png` and
  `joint_width.png`, has no test at all, though in the cones it is closed form. — Assert,
  at `r = 1`, the sum of `(φ^{μ−2}√N/σ)²` over the sub-resolution directions.
- m13 — `test_t23_tuned_lognormal_information_order` — A search that never moves returns
  `(0, 1)`. Under the shared seed, `i_ln` and `i_star` are then equal, so (a) passes,
  despite the docstring's "Catches a search that did not run". Only (b) can catch it, and
  only if `(0, 1)` lies more than about half a step (0.05) from a stationary point. —
  Assert that the information rises from `(0, 1)` by more than MC error.
- m14 — spec §4.2 (outside this review's scope) — "As `τ` grows the family tends to
  `p_U`" is false. With `θ` the log decay time and `ξ = exp(−e^{−θ})`, a wide normal in
  `θ` sends `ξ` to 0 or 1, so the law tends to `½δ_0 + ½δ_1` for fixed `θ̄`; `p_U` is a
  Gumbel law in `θ`. T23 does not depend on the claim. — Correct the sentence in §4.2.

## What the test suite gets right

It never asserts a result (§2.4), and it says so where a quantity is only recorded (T22(d)).
Where it has a reference, the reference is exact and sharp:
- T7(a)'s discrete marginal reproduces the atom sum, including the full Gaussian
  normalisation.
- T18's Tanaka weights (3/10, 2/5, 3/10) and `log(5/4)` are right on both grids;
  re-derived by the reviewer.
- T19(c)'s choice of Fisher length 3 at `N = 1` is clever. If `σ_eff` is computed the
  wrong way round, every mis-budgeted `p*` collapses into the same two-atom prior, and the
  strict inequality fails.
- T13(c) and the `κ = 1` half of T13(d) pin the cone's map and widths in closed form.
- T4's cone KS test and T14's KS tests pin the laws of Jeffreys' `θ_1`-marginal and of the
  nested, few-rates and interior natures.
- T14(c) pins the submodel's fixed coordinates.
- T22(b)'s cases straddle the threshold on both sides.

Seeds are literal, and the `slow` marker keeps the default run cheap. The fixes above
should give the consistency checks external anchors, not replace them.
