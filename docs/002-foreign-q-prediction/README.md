# Spec 002 — Foreign-`q` prediction: implementation notes

User-facing documentation for the code that implements
[`specs/002-foreign-q-prediction.md`](../../specs/002-foreign-q-prediction.md) (§4): the
models, the cast of priors, the natures, the two scores and the diagnostics, in
`src/infomax/`. The test suite is `tests/test_002_*.py`; the codegen audit trail is
[`experiments/002-foreign-q-prediction/CODEGEN_LOG.md`](../../experiments/002-foreign-q-prediction/CODEGEN_LOG.md).
The call graph and the data-flow diagram are added at stage 4 of `workflows/implement-spec.md`.

## Modules

| Module | Spec | Holds |
|---|---|---|
| `models.py` | §4.1 | the three families, `Theta`, the vertex warp, submodels, the binomial model |
| `mixture.py` (new) | §4.2, §4.4 | Gaussian-mixture log densities; the per-state divergence `D_KL(p(.|theta) || m_pi)` |
| `quadrature.py` (new) | §4.4, §5.4 | exp-decay's ordered grids; the cone's `theta_1` rule |
| `priors002.py` | §2.2, §4.4 | the prior interface: discrete, cloud, grid and cone-product priors |
| `capacity.py` (new) | §4.2 | the solver for `p*` and `p_lat` on a candidate set |
| `ba.py` | §4.6 | spec 000's loop, now also with an injected per-cell divergence |
| `pstar.py`, `plat.py`, `pproj.py`, `pref.py`, `plognormal.py`, `jeffreys.py` | §4.2 | the cast |
| `qfamily.py` | §4.3 | the natures, `q̄`, a cell's rows |
| `score.py` | §2.1, §4.4 | `score_cell`, floors, mismatches, per-state redundancy, information |
| `diagnostics.py` | §2.4, §3.2, §3.3, §4.5 | the split (3.3.1), the cap label, failure maps, row summaries, widths |

Three modules are new beyond the list in spec §4.6: `mixture.py`, `quadrature.py` and
`capacity.py`. They hold machinery that several of §4.6's modules share.

## Design decisions

Choices the spec does not fix, in the order a reader meets them. Each names the code
that carries it.

**DD-M1 — The constant cross-section's scale, and taper values between 0 and 1.**
(`models.R0`, `Model.taper_r`.) The spec writes `r = r_0` for the taper off but gives no
value, and lists a taper of `0.5` ("onset") without a map. Chosen: `r_0 = 1`, the cone's
base cross-section carried along the whole axis, and
`r(theta_1) = (1 - taper) r_0 + taper theta_1 / W` in between. Taper 1 and 0 are the
spec's two maps; 0.5 is a frustum.

**DD-M2 — The warped metric.** (`models._warp_jacobian`.) Inside the warped ball the
Jacobian of `warp_vertex` is taken by central differences (step `1e-7`) and composed
with the cone's analytic Jacobian. Outside the ball the analytic Jacobian is used
unchanged, so `sqrt(det g)` there is exact.

**DD-M3 — The warp keeps its radius under a change of budget.** (`Model.warp_radius`,
`Model.at_budget`.) `rho = 5 sigma_eff` is fixed when the cell's model is built. A
mis-budgeted `p*` is built on the same geometry at another noise.

**DD-K1 — The per-state divergence.** (`mixture.KernelTable`.) `p*`'s equalizer test
(T3) needs `D_KL(N(y_0, s^2) || sum_j w_j N(y_j, s^2))` to about `1e-3` nats at thousands
of states. Plain Monte Carlo at the spec's `J = 64` draws is far from that, and scrambled
Sobol is off by 2e-3 at 1024 points. The integrand depends on the noise only through its
projection onto the span of the nearby atoms, and that span is effectively two- or
three-dimensional at the cheap cell (singular values 1, 0.2–0.7, 0.05–0.1, then ≤ 0.015).
So the expectation is a Gauss–Hermite tensor product on the leading one to three
directions (48, 20² or 10³ nodes), plus the exact second-order term of the remaining
directions: `-1/2` times the variance of their components under the posterior over
neighbours. Directions below `1e-3` of the leading one are dropped. Atoms more than 8
noise units away are dropped too: their terms are below `e^-8` of the dominant one even
at a three-sigma noise draw. In one dimension it is plain Gauss–Hermite (96 nodes).
Against the mean of two 32 768-point Sobol estimates the error is at most 3.4e-4 nats over
406 states (1.8e-4 with 64, 28, 12 nodes at twice the cost). The estimator is
deterministic, so `per_state_redundancy` of a discrete prior ignores `rng` and `n_x`. A
cheaper rule (32, 12², 6³ nodes, about 3e-3 nats) serves as the solver's fast objective.
The derivation is in `tutorials/math/quadrature.md` §4.

**DD-K3 — Compiled kernels (numba).** (`mixture._divergence_kernel`, `mixture._rows_lse`.)
The divergence above and the mixture log-density are fused, multi-core loops compiled by
numba. The divergence's exponents `-d2/2 + z . c_top` are formed on the fly from compact
per-state data, never stored as a (states x nodes x neighbours) array. A cheap-cell `p*`
build fell from 47 s to 8.4 s; together with DD-K1's smaller rule, the divergence kernel
is about 17 times faster than the numpy version. The capacity found is unchanged
(3.09792 against 3.09795 nats).

**DD-K2 — Warm start by A&M's kernel approximation.** (`mixture.elk_divergence`.) The
solver's first Blahut–Arimoto pass runs on `-log sum_j w_j exp(-|y_i - y_j|^2 / 4 s^2)`
(A&M App. A.2, `sigma sqrt 2`), on a thinned subset of the candidates (every candidate
within 1.25 noise units). Only the starting support comes from it.

**DD-C1 — The candidate set.** (`pstar.candidate_set`.) The spec cites AtomicPriors.jl's
`mitchell` sampler for a net with points at most 0.5 Fisher lengths apart, seeded with the
faces of `Theta`. Implemented as a Poisson-disk net (Bridson's algorithm) in prediction
space, in noise units. Candidates are at least `spacing/2` apart, and new points are
proposed at `spacing/2` to `spacing` from an existing one, with the step scaled by the
local metric of the face. Every face of `Theta` is grown, lowest dimension first
(vertices, edges, ..., interior). In exp-decay the faces are the coincidences of rates and
the rates at 0 or ∞; in the cone they are each coordinate at either end of its range.
The seed is fixed (`pstar.NET_SEED`), so the net is a deterministic function of the model.
Sizes at spacing 0.5: 10 candidates in the 1-D cone of Fisher length 3, and 1624 at the
cheap cell (Fisher volume 147). The cone's tip (`theta_1 = 0`) is a candidate, and
`det g = 0` there (see *Testing notes*, T13(d)).

**DD-C2 — Atoms of `p*`.** (`pstar.merge_atoms`.) Supported candidates whose predictions
lie within 1 noise unit of each other (single linkage) merge into one atom. It sits at
their mass-weighted centroid in `theta` (a convex combination, so it stays ordered and in
the box). The weights are then re-solved on the merged atoms, and `C_N` is the
information of that prior. This is spec 000's runs of adjacent cells, in `D` dimensions.
`PStarResult.masses` keeps the unmerged weights over the candidates, which T16(c) and
T19(a) compare.

**DD-S1 — The solver.** (`capacity.solve_capacity`.) Spec 000's overrelaxed
Blahut–Arimoto loop (its per-cell divergence injected, §4.6) converges far too slowly to
the `1e-3` level on ~100-atom, 26-dimensional problems. It is kept as the warm start, and
the fixed point is finished by:

1. projected Newton ascent on `I(w) = sum w_i f_i(w)` over the active set. The model is
   `f` and the symmetrised Jacobian `df/dw` (the information's Hessian
   `-∫ p_i p_l / m`, negative semi-definite), damped Levenberg–Marquardt-style, with an
   Armijo line search, so `I` never falls. A weight driven to zero leaves the support if
   its `f` is below `lambda = sum w f`. Atoms may enter with weight 0.
2. a sweep over every candidate. The Jensen bound `-log sum_j w_j e^{-d_j^2/2} >= f`
   clears most of them, the fast objective screens the rest, and the accurate objective
   decides. The strongest violators (`f_c > lambda + add_tol`) join, at most 32 per round
   and at least 2 noise units apart: many adjacent zero-weight candidates at once make
   the Newton system near-singular.

The Newton step's damping has a floor of `1e-5` of the Hessian's scale (`capacity.MU_FLOOR`).
With near-duplicate candidates the system is near-singular, and at `1e-8`, rounding-level
differences in the divergences (`1e-14`) sent the steps in different directions and the
solve stalled. At the cheap cell `1e-5` was the fastest robust floor: 6.8 s, against 9.3 s
at `1e-6`, and 16.8 s with a residual of 2e-3 at `1e-4`. `p_lat`'s objective, a difference of two divergences, keeps the light damping (`1e-10`)
it was tuned with: at `1e-5` its solve stalled and took 990 s instead of 51 s. Adding more
than 32 violators per round was tried and made `p*_{10N}` slower (795 s against 340 s): its support grew to 1669
atoms, many near zero, and Newton stopped converging.

Tolerances. With one-dimensional data or a binomial channel the divergences are exact,
and the stopping rule is the spec's `tol`. Beyond one dimension, near-duplicate
candidates make the split of an atom's mass between neighbours ill-determined and
immaterial to `I`. So violations below `1e-3` nats are not chased, and the equalizer on
the support is accepted at `2e-3` nats once `I` has stopped rising (`< 1e-7` per round).
At the cheap cell this gives `C_N = 3.09795` nats (A&M: 4.47 bits = 3.10 nats). An
independent 8192-point Sobol estimate puts the support within `[-3e-4, +1.3e-4]` of
`C_N`, and every candidate below `C_N + 1e-3`. The solve takes 35 s. **This is a
deviation from the build's `tol = 1e-8` default (spec §4.2 pseudocode) and needs your
review.** The two-sided bound of `p_lat` (T16(b), `1e-6`) is affected the same way.

**DD-Q1 — Exp-decay quadrature.** (`quadrature.exp_decay_grid`.) In `xi` the diagonal of
the metric is separable and the same on every axis. Each axis is cut into cells of equal
arc length: 0.3 noise units at `D ≤ 2` and 0.6 beyond. Each cell has two Gauss–Legendre
nodes per axis. Cells with tied indices are the ordered region's boundary: each holds
`1/g!` of its box, and its nodes are sorted into the ordered region. One node per cell is
not used. In a tied cell the sorted single node lies on the diagonal, where Jeffreys'
density vanishes, so the cell's mass is lost: at `D = 4` that cost 0.16 nats in per-state
divergences against 0.06 for two nodes at the same cost. Measured per-state errors (spread
after the mean, which cancels in `b`): 2e-4 (`D = 2`), 7.5e-4 (`p_LN`, `D = 3`),
2.4e-3 (`p_J`, `D = 3`), 2.7e-4 (`p_LN`, `D = 4`) and 6e-2 nats (`p_J`, `D = 4`, against a
reference that may itself be unconverged). Jeffreys is the hard case at `D ≥ 3`: its
density vanishes on every coincidence face. The spec's `G` per axis (50, 30, 20) is
replaced by this resolution rule, which is finer where the metric is large. Grids are
coarsened until they hold at most 2 million nodes.

**DD-Q2 — Normalised quadrature weights, and exact cell masses for product laws.**
(`priors002.ContinuousPrior.nodes`, `ExpDecayProductPrior`.) Every continuous prior's
node weights are normalised to sum to one, so every mixture is a proper distribution.
`p_U`, `p_LN` and `p_LN^*` are i.i.d. per rate before ordering. Their grid cells carry
their exact masses `D!/prod g! prod_mu [H(b_mu) - H(a_mu)]`, because `p_LN`'s density in
`xi` has an integrable spike at `xi -> 0`, which node values misjudge by about 20% in the
first cell.

**DD-Q3 — Sampling grid priors.** (`priors002.grid_rejection_sample`.) Exact rejection
sampling. A cell is proposed in proportion to its volume times the largest density at its
nodes, a point is drawn uniformly in its part of `Theta`, and it is accepted with
probability `f / (4 f_max)`.

**DD-P1 — The maximum-likelihood projection.** (`pproj.mle_project`.) A batched,
box-constrained Levenberg–Marquardt fit, started from the three nearest points of a
Fisher-spaced seed net (`candidate_set` at spacing 1) and, in the chain, from the
walker's previous estimate. In exp-decay it runs on the unordered cube (the map is
permutation-symmetric) and sorts the result. In the 1-D cone the projection is the clip.

Each fit stops once a step lowers its cost by less than `1e-12` of it, or its damping
passes `1e6`; all starting points of a batch run as one array. That took `p_proj`'s build at
the cheap cell from 44 s to 12 s, mostly by removing Python overhead.

**DD-P2 — The NML normaliser.** (`pproj.nml_log_normaliser`.) Importance sampling from
`p_U`'s marginal at 1.25 times the noise, with the delta-method error of `log Z`.

**DD-P3 — The chain.** (`pproj.build_pproj`.) Goodman–Weare's stretch move (`a = 2`),
two half-ensembles, `n_walkers = 64`, `burn = 1000`, and every walker's estimate kept at
every step after burn-in (no thinning). This follows the spec's defaults; T12(e), which
would check it against `transtrum`, needs Julia (*Testing notes*).

**DD-R1 — Stiffest first at `D = 2`.** (`pref._StiffestField`, `pref.ranking_coordinate`.)
The Berger–Bernardo prior in coordinates (`psi`, arc length) is rewritten free of
labels: `p_ref / p_J ∝ n(theta) / (L(psi) G(psi))`. Here `n = |d psi|_{g^-1}`, `L` is the
curve's Fisher length and `G` the Fisher-length geometric mean of `n` along it, so any
relabelling of `psi` cancels. Along a curve, `n` follows from the integrating factor `a`
of the sloppy direction's normal covector, `d log a / ds = v_1 · grad phi` (`phi` the
stiff eigenvector's angle, in log decay times), and `n = a / sqrt(lambda_1)`. Curves are
traced in log decay times on `[-4, 9]` (beyond it a rate is frozen or gone at every
observation time). They are seeded on the diagonal and on three lines inside the domain,
and the field is interpolated linearly in log decay times. So the density does not
depend on the transversal by construction (T15(e) then checks the relabelling, not a
numerical coincidence). The transversal enters `ranking_coordinate`: a curve's label is
where it crosses the transversal segment in `xi`. A curve that misses the segment gets the
parameter of the segment's point closest to it. That fallback is not a coordinate in the
strict sense, and the spec does not say what the transversal must cross.

**DD-R2 — The warped cone's `p_ref`.** (`pref._cone_pref_with_curvature`.) Each
cross-section is integrated by Gauss–Legendre at the `theta_1` nodes of the cone rule.
The normaliser and the exponent are interpolated in `theta_1`, the normaliser as its
smooth remainder after removing `(D-1) log r(theta_1)`, which is singular at the tip.

**DD-L1 — `p_LN^*`'s search.** (`plognormal.build_pln_star`.) Nelder–Mead over
`(theta_bar, log tau)` from A&M's `(0, 1)`. The information is the Monte Carlo of
`score.mutual_information` (4096 draws, the marginal by quadrature), with one seed drawn
once from `rng` and reused for every trial. The objective is then a smooth function of
the parameters (common random numbers, §4.2).

**DD-N1 — Natures as priors.** (`qfamily.nature_prior`.) Each nature is an object with
the cast's interface. The cone's halves and interior are `ConeProductPrior`s, so their
floors use the closed-form cross-section integral of §4.3. Few rates uses Gauss–Legendre
in the shared log decay time. The vertex nature uses quadrature and rejection sampling on
the boxes that bound each face piece within `rho` of `v`. Draws are labelled
`own:<prior>`, `nested:<name>` or `stress:<name>`.

**DD-SC1 — Common random numbers and the predictive.** (`score.score_cell`,
`PriorBase.log_predictive`.) A cell draws `theta`, then `e1`, then `e2`, and sets
`xbar = y + sigma_eff e1`, `x' = y + sigma e2`. Cells that differ only in `N` (or in
`sigma` at fixed `sigma_eff`) therefore share their draws (T17, §2.1's invariance). The
posterior predictive is computed for every prior from two marginals by the identity in
`priors002`'s docstring (T17(c)).

**DD-SC2 — Information estimates.** (`score.mutual_information`.) With one-dimensional
data, deterministic `H(m) - H(noise)` on a fine `x` grid. Discrete priors with at most 600
atoms use `sum w f` with DD-K1's estimator. Larger clouds and continuous priors use Monte
Carlo over 4096 draws from the prior's own sampler.

**DD-E1 — The eye test's bias-pressure band.** (`diagnostics.worst_case_bias_pressure`;
spec §5.3, §5.3.1 as revised 2026-11-25.) A&M's `B = max_theta b(theta)` does not say over
which states it runs. At `D = 1` Jeffreys' `b` is about 0 in the interior (median −0.04
bits) and about 1.3–1.4 bits on the faces `xi = 0` and `xi = 1`, where half the noise
falls off the manifold. The figure therefore draws a band, from the maximum over 2000 draws
from the prior itself to the maximum over `p*`'s candidate set, faces included. Each is
found in two stages. First `b` on the states thinned to two Fisher lengths (64 draws of
`x`), then the states within one Fisher length of the 16 best re-evaluated with 512 draws
(at most 64 states). Over `D ≤ 3` the band contains every A&M point except Jeffreys' at
`D = 1` (0.15 bits against 1.37–1.43).

A first band, from states at least one Fisher length from every face, was dropped. It is
empty at `D ≥ 3`: every candidate lies within 0.58 (`D = 3`) or 0.39 (`D = 4`) noise units
of a face, because the irrelevant directions are thinner than the noise.

**DD-S2 — Builds are memoised within a process.** (`pstar._BUILD_CACHE`,
`plat._BUILD_CACHE`.) `p*` and `p_lat` are deterministic functions of their arguments, so
a repeated build (`build_cast` in many tests, `p*` and its copies) returns the stored
result. `p*`'s key uses the effective noise `sigma/sqrt(budget)`, on which the reduced
build alone depends, so the cheap cell's `p*_{10N}` and its twin's `p*_{40}` share one build.
The memo lives in memory only; a cache that survives the process is left for later, when
the code is stable.

**DD-A1 — The atomic path.** (`pstar.build_pstar(method="atomic")`.) AtomicPriors.jl
through `juliacall` (OQ-1) needs Julia, which is not installed. The path raises
`NotImplementedError`. `D_switch` is unset, and every build uses candidate sets.

**DD-A2 — Exp-decay `p_ref` beyond `D = 2`.** Not implemented yet (the coverage table
asks for `D ≤ 4`): `build_pref` raises `NotImplementedError` at `D ≥ 3`.

## Testing notes

Opened at the first run of the suite (stage 3, run as a debugging aid before the eye test
is approved, at the human's request).

- **T13(d), the cone's tip.** `test_t13d_curvature_knob_through_the_model` required
  `det g > 0` on the whole candidate set, `v` excluded. The tip `theta_1 = 0` is a vertex
  of `Theta`, and the net includes it (DD-C1). There `det g ∝ theta_1^(D-1) = 0` exactly,
  so both `kappa` cases failed, each at that one candidate, 5 from `v` and far outside the
  warp. Resolved (MB, 2026-11-25): the check runs on the candidates within `rho` of `v`
  only, where the warp acts; spec §5.2's "on the grid" now says so. The tip stays in the
  net, since `p*` may put an atom there.
- **T12, AtomicPriors.jl fixtures.** `tests/fixtures/atomicpriors/` does not exist:
  generating it needs Julia (§5.5), so T12(a)–(e) fail at "missing fixture".
- **T14(a), `p_LN` and `p_LN^*` samplers.** The test integrates each density on its own
  600-point midpoint grid and requires the total to be 1 within `5e-3`. For the
  log-normals it gets 0.972, because midpoints miss the density's integrable spike at
  `xi -> 0` (the mechanism of T7(a), DD-Q2). The densities are exact in closed form (T23
  checks `p_LN`'s to `1e-8`). Open: integrate the test's marginal in the CDF, or loosen it.
- **First fast-suite run** (`762eae0`, 18.5 min): 140 passed, 17 failed: the T12 fixtures
  (8), T13(d) (2), T7(a) (2), T14(a) log-normals (2), T21(a) `mass_near`, T16(b) at the
  cheap cell, and T7(c), a bug in the batched kernel tables (two-dimensional data have two
  singular directions, not three), fixed after the run.
