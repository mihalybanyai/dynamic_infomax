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
review.** The two-sided bound of `p_lat` is affected the same way: T16(b) holds it to
`1e-6` in 1-D and to this `1e-3` beyond (MB, 2026-11-26).

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

**DD-Q4 — Continuous priors beyond the grids.** (`sampled.py`; `build_jeffreys`, `build_pln`,
`build_uniform`.) Spec §4.2, §4.4 and OQ-13. Exp-decay `p_J` from `D = 4`, and `p_U` and
`p_LN` above `D = 5`, are `SampledPrior`s: weighted clouds of 20000 draws in ordered `xi`,
with a normalised log density.
- *Jeffreys' sampler.* Adaptive importance sampling in unordered log decay times. Round 0
  draws Student-t log times (3 degrees of freedom, location 0.8, scale 1.5); later rounds
  draw from Scott-bandwidth Gaussian kernels around the previous weighted cloud, with 10% of
  round 0's law. Each round has 8000 draws. It stops once `log Z` varies by less than 0.02
  nats over three rounds, and a last round of 20000 draws gives the cloud, `log_normaliser`
  and its standard error. A last round below half the adaptive rounds' median effective
  sample share is redrawn, at most three times; then the build raises. Seed
  `SAMPLED_SEED + D`. A build that stays collapsed or ends below `JEFFREYS_ANNEAL_BELOW = 2%`
  anneals instead (`_anneal_jeffreys`). It tempers 20000 first-law particles in
  `u = (theta_(1), log gaps)` toward Jeffreys, keeping 80% effective per step, with 10
  random-walk moves per step; `log Z` is the sum of the steps' log mean incremental weights.
  `anneal=True` forces it. Round 0 was `N(0.8, 1.5²)` until 2026-11-26. Toward slow rates
  Jeffreys' density in log time falls only exponentially, so the normal's tails could not
  bound the weights (*Testing notes*).
- *Results* (t first law). `log Z` was 0.828 ± 0.007 at `D = 4`, −4.063 ± 0.010 at `D = 5` and
  −19.394 ± 0.025 at `D = 7`, against brute force's 0.842 ± 0.001, −4.067 ± 0.002 and
  −19.388 ± 0.010. It builds in 20–40 s. `I(p_J)` at `D = 7` was 1.72 bits (1.73 and 1.77
  under two other seeds), against A&M's 1.71. The effective sample share is about 53% at
  `D = 4`, 31% at `D = 5` and 7.5–8% at `D = 7`.
- *Marginals* (OQ-14). `_lmn` routes: the weighted cloud's mixture where the cloud weighted
  by the likelihood keeps at least `N0_THIN = 300` effective draws, `per_point_log_marginal`
  elsewhere. Both `log_marginal` and `log_predictive` come through `_lmn`. The per-point
  estimate works in unordered log decay times. Modes come from L-BFGS from the three
  best-explaining cloud draws, keeping the best state seen, with a Powell polish when
  L-BFGS ends worse. Each mode gets a finite-difference Laplace scale. The proposal is a
  Student-t core (5 degrees of freedom, scale 1.5) plus a wide part (scale 3, 20%),
  symmetrised over permutations within blocks of near-equal mode coordinates (at most 7!).
  It takes 1000 draws per point, seeded by the point's bytes. `variant=1` (3 degrees of
  freedom, core 2) is T4's second version. Above `D = 5` it warns, and it warns when fewer
  than 20 draws are effective. `cloud()` gives the plain cloud, which screens in
  `worst_case_bias_pressure`.
- *Annealed* (`annealed_log_marginal`). Where the bell-shaped estimate keeps fewer than
  `ANNEAL_BELOW = 50` effective draws, `_lmn` uses a sequential Monte Carlo sampler. 2000
  particles are resampled from the cloud. The likelihood's power climbs in steps that keep
  80% of the particles effective, each followed by systematic resampling and 10 random-walk
  Metropolis moves; the scale follows the particles' covariance and adapts to about 25%
  accepted. `log m` is the sum of the steps' log mean incremental weights. The coordinates
  are ordered log decay times as `u = (theta_(1), log gaps)`. Seeded by the point's bytes;
  `replicate` gives an independent run. About 1.2 s per point at `D = 5`, with 10–30 steps.
- *Superseded.* `kernel_log_marginal`: Gaussian kernels around up to 200 likelihood-weighted
  cloud draws, 20% defensive kernel density, 1000 draws. Its centres come from the cloud, so
  at thin states it misses the posterior. It is kept for the thin-states figure. Before it,
  a Gaussian at the tight fit with covariance `(g + 100 I)^-1` reached 1% effective sample
  size, and two such proposals differed by 3–4 nats.

**DD-P1 — The maximum-likelihood projection.** (`pproj.mle_project`.) A batched,
box-constrained Levenberg–Marquardt fit, started from the three nearest points of a
Fisher-spaced seed net (`candidate_set` at spacing 1) and, optionally, from a previous
estimate. In exp-decay it runs on the unordered cube (the map is permutation-symmetric) and
sorts the result. In the 1-D cone the projection is the clip.

Each fit stops once a step lowers its cost by less than `1e-12` of it, or its damping
passes `1e6`; all starting points of a batch run as one array. That took `p_proj`'s build at
the cheap cell from 44 s to 12 s, mostly by removing Python overhead.

`tight=True` then polishes each fit by bounded least squares (`scipy.optimize.least_squares`,
`xtol = ftol = gtol = 1e-15`). It is needed because along sloppy directions the likelihood
is nearly flat, and the default stopping rule fires there early. On the same 3000 data
points, the default fits put 0.335 of the cloud on coinciding rates and `transtrum`'s 0.287;
polished from both, they gave 0.31 and 0.30, and met on 99% of points (2026-11-26). Raising
the iteration cap does not help: the cost rule, not the cap, stops the fit. The polish runs
only in the sampler's last round (DD-P3), since earlier rounds only shape the proposal.
A fit within `1e-12` of the range from a bound is snapped onto it, since the polish can
stop at `xi = 3e-20` instead of 0. Without the snap, T12(e)'s KS test read the cloud's
point mass on a face as off the face and failed at `p = 1e-12`, while every quantile
agreed with `transtrum`'s within 0.01.

**DD-P2 — The NML normaliser.** (`pproj.nml_log_normaliser`.) Importance sampling from
`p_U`'s marginal at 1.25 times the noise, with the delta-method error of `log Z`.

**DD-P3 — The sampler.** (`pproj.build_pproj`.) Adaptive importance sampling, as spec
§4.2 and OQ-6 fix it: cold starts from 8000 Jeffreys draws (or `p_U`'s, `first="uniform"`,
for an independent second start), warm starts from a given cloud with 2000 draws per round,
10% of the first atoms as the defensive part, rounds until the effective sample size is at
least 85% twice in a row (2 to 12), then a tight round. The result is a weighted
`CloudPrior` carrying `ess`, `ess_fraction`, `rounds` and `warm`. A warm start whose last
round falls below 85% repeats cold; a cold start that ends below it warns. Warm-start atoms
are clipped into the new cell's `Θ`, so a cloud from the whole manifold can seed the window
box.

It replaces a stretch-move chain (`a = 2`, 64 walkers, 1000 burn-in steps, every step kept).
That chain held about ten independent points per 2000-point cloud, by its autocorrelation
time of about 200 steps at the cheap cell (*Testing notes*, T12(e)).

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

**DD-A1 — The atomic path.** (`pstar._build_pstar_atomic`, `build_pstar(method="atomic")`.)
The adaptive pool of spec §4.2. Each round: `400 D` states on random faces, without listing
them (the cone has `3^D`), and `200 D` interior states. In the ordered `Θ`, rates fall into
consecutive blocks with each gap cut with probability 0.3, the end blocks pinned with
probability 0.3 each. Otherwise each coordinate sits at a bound with probability ½. The
current support and four moves of each atom join them: jitter at 0.3%, 1% and 3% of the
range, and one coordinate snapped to a bound or onto its neighbouring rate. The pool is
thinned to `POOL_SEPARATION = 0.25` noise units, keeping the support, and solved by
`solve_capacity` from the support. It stops at the first round, from the third on, that
adds no atom and raises `C` by less than `1e-4` nats (at most 15 rounds). The pool's draws
use `NET_SEED + 1`, so builds are deterministic. `method="auto"` falls back to it when the
candidate set passes `10^6` points. The result records `rounds` and `max_violation`, the
largest `f − C` over the last pool (§6.1).

Thinning matters: without it the first round at `D = 2` took 20 minutes, since near-duplicate
states stall the Newton step (DD-S1); with it the build takes 2–3 minutes. At `D = 2` the pool
gave `C = 3.0980` nats against the candidate set's 3.0979 (98 atoms, 9 rounds). At `D = 4` it
gave 3.2890 against 3.2886. At `D = 5` it gave 3.3254 ± 0.0013 nats by direct Monte Carlo,
against AtomicPriors.jl's 3.2987 ± 0.0018 (2026-11-26). The hypercone's face states are
untested.

**DD-A2 — Exp-decay `p_ref` beyond `D = 2`.** Not implemented yet (the coverage table
asks for `D ≤ 4`): `build_pref` raises `NotImplementedError` at `D ≥ 3`.

**DD-J1 — The fixtures' Julia environment.** (`tests/fixtures/atomicpriors/Project.toml`,
`Manifest.toml`.) AtomicPriors.jl is unregistered and `resources/AtomicPriors.jl` is
gitignored, so the environment takes it from upstream at its only commit, `0dfd103`
(2022-02-27); the local copy is identical apart from upstream's CI folder. Two pins keep it
working on Julia 1.13:

- *LineSearches `7.0 - 7.4`.* LineSearches 7.5.1 declares NLSolversBase 7 but calls
  NLSolversBase 8's `value_gradient!`, which returns a tuple; 7.6.0 and later declare 8
  correctly. AtomicPriors' ForwardDiff 0.10 holds NLSolversBase at 7, so the resolver picks
  7.5.1, and every `optim!` call fails. LineSearches is a direct dependency only to carry
  this bound.
- *One thread.* AtomicPriors sizes per-thread buffers by `Threads.nthreads()` and indexes
  them by `threadid()`. Since Julia 1.12, `--threads=N` and a plain `julia` add an
  interactive thread, so `threadid()` can exceed `nthreads()`. `generate.jl` refuses to run
  unless `--threads=1`, which also makes each seed's output independent of the machine.

**DD-J2 — `transtrum`'s log-rate cap.** (`generate.jl`, `ylograte`.) `transtrum` fits in the
unbounded coordinate `theta = log k`, where `y_t = mean exp(-e^theta t)`. For
`theta >= log 746 ≈ 6.6`, `y` and its derivative are already exactly 0 in Float64 (`t >= 1`);
above `log(floatmax) ≈ 709.78`, `exp` overflows and the derivative becomes `-t·∞·0 = NaN`.
Levenberg–Marquardt does step there, and Julia's LU then refuses the matrix. `generate.jl`
caps `theta` at 700 inside the map. Below the cap every value and Jacobian is unchanged bit
for bit (checked at `theta = 0.3, 5, 6.7, 699, 705`); above it the NaN becomes its limit, 0.
Any other NaN still raises, and every value `generate.jl` writes is checked finite. With the
cap, the mutual information of `transtrum`'s cloud agrees with AtomicPriors' separate
`transtrum_exp` within 0.04 nats over three seeds (times `1:2`, AtomicPriors' own test).

**DD-J3 — Which AtomicPriors routines produce each fixture.** (`generate.jl`.) §5.5 names
`mutual` and `optim!`/`nlopt!` over `mutual`, but `mutual` needs an explicit grid over the
data, which 26 dimensions rule out. The fixtures use AtomicPriors' Gaussian routines instead,
as its own documentation does for exp-decay [read: `resources/AtomicPriors.jl/docs/basic.jl`]:

- `p*`: `nlopt!` on the kernel bound `ekern` at `σ√2`, from 200 Sobol atoms. The optimum
  barely depends on the start: from 100, 150 or 200 atoms, with or without a restart, `I` is
  3.093–3.094 nats at `D = 2`. Each atom is sorted onto the ordered `Θ`, since `y` is
  symmetric in the rates and `nlopt!` returns permuted copies of one atom. Then atoms whose
  predictions lie within `0.1σ` merge, since `nlopt!`'s own `unique` merges only to 5
  digits. Merging before sorting averaged `(0.97, 0)` and `(0, 0.97)` into `(0.48, 0.48)`,
  which cost 0.04 nats and left a face with `b = 1.08` nats; the first generated fixture had
  that bug. `nlopt!` stops once an iteration changes `ekern` by less than 1e-8 nats; with no
  tolerance it has no stopping rule, and at T12(c)'s `N = 4` (400 starting atoms) it ran for
  over 4 hours. T12(c) starts from 200 atoms at `N = 2` and 400 at `N = 4`, since the atoms
  grow like `N^(D/2)`.
- `I` (b, d): Monte Carlo, `mcarlo`, 10⁶ draws for `p*` and 4·10⁶ for the fixed prior.
- `B` (b): `fcarlo` minus `I`, maximised over an ordered grid in `xi`, faces included (step
  1/50 at `D = 2`, 1/20 at `D = 3`), in two stages: 2000 draws per state, then 2·10⁵ for the
  top 20.
- `transtrum` (e): 200 walkers (at least the data dimension plus 2 are needed), each seed
  starting them from its own `randn` draw. Every 1600th step of each walker is kept, and
  2000 points are drawn from what remains. The fraction of the cloud with coinciding rates
  (`|xi_2 − xi_1| < 0.02`) fell as the chains lengthened, until it stopped:

  | Walkers, step kept, start | Coinciding-rates fraction (two seeds) |
  |---|---|
  | 60, every 10th or 100th, Sobol | 0.46–0.69 |
  | 200 or 400, every 100th or 200th, Sobol | 0.45–0.53 |
  | 200, every 400th, Sobol | 0.33, 0.34 |
  | 200, every 1600th, Sobol | 0.27, 0.25 |
  | 200, every 1600th, random | 0.27, 0.25 |
  | 200, every 6400th, random | 0.27, 0.27 |

  The other two edges agree as well at 1600 and 6400 (`xi = 0`: 0.14–0.16; `xi = 1`:
  0.20–0.23). With Sobol starts the two seeds share their walkers' starting points, so
  their agreement within a row said nothing about convergence; with random starts it does.
  A chain keeping every 1600th step takes about 20 minutes. `generate.jl` then re-fits each
  of the 2000 kept points from its data point. It uses LsqFit at `x_tol = g_tol = 1e-15`,
  from `transtrum`'s own estimate and two random log-rates, and keeps the smallest
  residual (spec §5.5(e)). `transtrum`'s fits, like ours, stop early along flat ridges
  (DD-P1).
  The emcee walkers move through the 26-dimensional data space, while the target is a thin
  tube around the 2-dimensional model surface. The old Python port of the same chain did
  need chains this long, which is why spec §4.2 replaced it (DD-P3).

- `pstar_highD` (f): `nlopt!` on `ekern` from 100 Sobol atoms at `D = 5, 7`, about twice the
  54–57 atoms the optimum keeps, with `I` by `mcarlo`. It is a floor for `I_{p*}`, not its
  value, since `ekern`'s optimum fell 0.027 nats short of the atomic path at `D = 5`; T12(f)
  is one-sided.

Each estimate is the mean over two seeds, and their difference is the recorded spread.
`ekern`'s optimum is A&M's `p*`, not necessarily the exact capacity prior. T12(b) measures
the gap between the two.

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
- **T7(a), the fine-grid reference.** `test_t7a_continuous_quadrature_matches_a_fine_atom_sum`
  built its reference from density values at the midpoints of a 400 x 400 grid in `xi`,
  with the diagonal cells at full weight. Against a converged reference (exact cell masses,
  1600 x 1600), that reference was off by 2.5e-3 nats for `p_U` and 3.8e-2 for `p_LN`, while
  the code's quadrature was off by 2.4e-5 and 2.1e-4. The diagonal cells straddle the
  ordered region and carry half their area; midpoints misjudge `p_LN`'s spike at `xi -> 0`
  (DD-Q2). Resolved (MB, 2026-11-26): the test gives product laws exact cell masses from
  closed-form per-rate CDFs written in the test, the diagonal cells their ordered half at
  its centroid. All three priors pass at 1e-3.
- **`p_J`'s exp-decay grid loses mass at `D ≥ 4`.** Brute force over 2·10⁶ uniform ordered
  draws gives `log ∫ √det g`, which the grid (DD-Q1) underestimates. It misses 0.0% of the
  mass at `D = 2`, 0.2% at `D = 3`, 5.0% at `D = 4` and 24% at `D = 5`. The node weights are
  renormalised, so the grid stood for a distorted Jeffreys. At `D = 5`, two rates within 0.02
  of each other carried 1.3% of its mass against 5.5% in truth, and a rate near instant decay
  carried 0.87 against 0.68. Resolved (MB, 2026-11-26): `p_J` is sampled from `D = 4`
  (DD-Q4, OQ-13). The eye test's `D = 4, 5` rows were redrawn with it.
- **T12, AtomicPriors.jl fixtures.** Generated by `tests/fixtures/atomicpriors/generate.jl`
  (DD-J1–J3) on 2026-11-25. T12(a) and T12(d) pass.
- **T12(c), `C_N` through `repeat`.** `repeat` builds the `N`-fold channel of a
  discrete-outcome likelihood matrix, and exp-decay's data are 26-dimensional Gaussian, so
  §5.5(c) could not run as written. Resolved (MB, 2026-11-25): (c) runs (b)'s recipe at
  `sigma/sqrt(N)` for `N = 2, 4`, an external check of the capacity solver at lower noise.
  The reduction itself is covered by spec §4.4, T7(c) and the twin cells. Stacking `N`
  copies of the data was set aside: `ekern` sees only `‖Δy‖²/σ²`, where `N` copies are
  exactly `σ/√N`.
- **T12(e), the `p_proj` port had not mixed.** Against `transtrum`'s converged cloud (DD-J3),
  the old port's two chains (2000 points) put 0.70 and 0.63 of their mass on coinciding
  rates, against 0.255, and 0.25 and 0.12 exactly at `xi_1 = 0`, against 0.07. They also
  disagreed with each other. Resolved (MB, 2026-11-26): spec §4.2 and OQ-6 replace the
  chain with adaptive importance sampling (DD-P3), and `transtrum`'s points are re-fitted
  tightly (DD-J3). T12(e) now compares weighted clouds at their effective sizes, and checks
  two independent starts (Jeffreys and `p_U`), not two chains. It passes against the
  re-fitted fixture (2026-11-26). The re-fit moved 1.3–1.4% of `transtrum`'s coordinates
  by more than 1e-3, and its coinciding-rates fraction from 0.255 to 0.260.
- **T12(b), atom matching.** The candidate set's unmerged atoms (DD-C2) outnumber Julia's
  continuous ones about two to one, and merged counts only follow the merge radius.
  Resolved (MB, 2026-11-25): atoms are compared through the cross-equalizer, the Python
  `p*`'s bias pressure within 0.05 nats of zero at every Julia atom (largest seen: 0.024 at
  `D = 3`). That value is above the solver's 1e-3 stopping threshold (DD-S1): either
  Monte-Carlo noise or a location between candidates.
- **T14(a), `p_LN` and `p_LN^*` samplers.** The test integrated each density on its own
  600-point midpoint grid and required the total to be 1 within `5e-3`. For the
  log-normals it got 0.972 and 0.914, because midpoints miss the density's integrable spike
  at `xi -> 0` (the mechanism of T7(a), DD-Q2). The true mass of `xi_1 < 1/600` is 6.2% and
  12%. Loosening the total would not have helped: against the renormalised grid CDF the KS
  test gives p = 9e-5 and 1e-31. Resolved (MB, 2026-11-26): the product laws (`p_U`,
  `p_LN`, `p_LN^*`) are checked against closed forms written in the test
  (`spec002_common.per_rate_law`, shared with T7(a)). `log_density` matches
  `log 2 + sum log h` pointwise, and the draws' `xi_1` follow `1 - (1 - H)^2` (KS p = 0.85,
  0.64, 0.64). The two log-normals' p-values coincide because their draws are one monotone
  map of the same normals. `p_J` and the `p_ref`s keep the grid. The test runs in about
  40 s, not slow; spec §5.1's marker is removed.
- **T21(a), `mass_near`'s precondition.** The test moves 10 atoms by 0.01 in `xi` and
  required every moved state to keep some atom within one noise unit (`want > 0`). Near
  `xi = 1` a move of 0.01 is up to about 3 noise units at `N = 4`, and two states landed 2.51
  and 1.07 units from their own atom, with no atom in reach. `mass_near` itself matched
  the test's sum to 4e-16, exact zeros included. Resolved (MB, 2026-11-26): the states are
  kept, since they cover 0, 1 and 2 atoms in reach. The precondition now asks for at least
  one state with no mass, one with some, and none with all of it. The docstring had the
  direction backwards: an understated mass, not an overstated one, loosens the bound.
- **T16(b), the two-sided bound at the cheap cell.** It closed to 9.3e-4 nats against the
  test's `1e-6`. That is DD-S1's stopping rule: beyond 1-D, violations below 1e-3 are not
  chased. Resolved (MB, 2026-11-26): `1e-6` in 1-D, where the divergences are exact, and
  `1e-3` at the cheap cell (`PLAT_GAP_EXACT`, `PLAT_GAP_QUADRATURE`; spec §5.2). There (b)
  checks only that the solve ended by its own rule. It follows DD-S1, still open.
- **Jeffreys' sampler collapsed at `D = 7`** (extended eye test). `I(p_J)` came out 1.52
  bits against A&M's 1.71. Under two other seeds the build gave 1.73 and 1.71 bits with
  7–8% effective draws. Drawing `theta` from one healthy build and the marginal from
  another gave the same `I`, so a cloud does not flatter itself. The default seed's last
  round had collapsed (adaptive rounds 7–9%): one draw with a log decay time near 10 took
  about 5000 times the mean weight, leaving 15 effective draws, with `log Z` −19.10 ± 0.26
  against brute force's −19.39 ± 0.01. T4's three-standard-error check would have passed
  it. Resolved (MB, 2026-11-26): a Student-t first law and a last-round guard (DD-Q4). T4
  adds `D = 7` and a 1% floor on the effective share.
- **Sampled priors at thin states (OQ-14; implemented, open for Jeffreys from `D = 5`).** The extended eye test's upper `B` edge
  for `p_LN` at `D = 7` was 416 bits, against A&M's 45–50. At `D = 5`, where `p_LN` still has
  its exact grid, the `D = 7` path on the eye test's 1533 states gave `B` = 114 nats, against
  the grid's 44. At the no-decay corner the per-state divergence was 46 nats by the grid, 121
  by the per-point estimate and 234 by the plain cloud. Over the 20 states that set `B` the
  per-point estimate overshot by a median of 10 and up to 75 nats, with an effective share
  near 0.001 everywhere. Its two kernel variants agree (T4) because both take their centres
  from the cloud. At `D = 3` the plain cloud overshot `p_LN` by 54 nats near the corner and
  about 4 on faces with a fast and slow rate, and `p_J` by 0.15–0.28. The scores
  (`score.log_marginal`) use the plain cloud everywhere; the per-point estimate runs only
  inside `worst_case_bias_pressure`. New test,
  `test_t7a_sampled_marginal_matches_the_grid_at_thin_states`: at `D = 3`, within 0.1 nats of
  the grid at five thin states and a typical one. The grid agrees there with one of half its
  cell length within 0.03 nats, but not at the corner itself (0.11–0.16), which is left out.
  It fails for both priors until OQ-14 is resolved (2026-11-26).
- **OQ-14's per-point estimate, tested** (2026-11-26).
  - *`D = 3`, against a grid of half the default cell length.* The estimate is within
    0.011 nats (`p_LN`) and 0.034 (`p_J`, at the exact corner) at seven states, with
    18–47% of its draws effective. The routed marginal is within 0.02 nats everywhere. The
    thin-state test passes.
  - *`D = 5`, `p_LN` against its exact grid on the eye test's 1533 states.* `B` is 43.3
    nats against 44.2. Over the 20 states that set it, the routed `log m` is within 0.03
    nats at the median and 0.41 at worst.
  - *`D = 5`, Jeffreys (no exact reference).* At the corner, coincident, mixed and typical
    states, 7–33% of draws are effective and the two variants agree within 0.02 nats on
    average. On the face with one instantly decaying and four non-decaying rates, 0.1% are
    effective, and the variants differ by 0.8 nats on average and 17 at worst.
  - *`D = 7`.* For Jeffreys, 0.1–1% of draws are effective at faces, and the variants
    differ by 0.2–0.9 nats.
  - *Two other tries, set aside.* Ordered log decay times with log gaps remove the
    relabelling sum: 0.06–0.4 s per point at `D = 7`, against 2.9 s. But they were worse at
    `D = 3` (0.09–0.18 nats at interior states, 4% effective) and no better for Jeffreys at
    `D = 7`. Covariances from the likelihood's Gauss–Newton term plus the cloud's spread, or
    from the curvature floored at the prior's precision, did not help either. In the four
    directions the data leave free, the posterior is Jeffreys' own conditional, which is far
    from Gaussian there. The next candidate is annealed importance sampling from the cloud.
  - *A bug on the way.* At `D = 7`, L-BFGS stepped onto states where Jeffreys' density is
    zero in double precision (rates rounding to `xi = 1` and coinciding) and stopped there.
    scipy returned that last point, not the best one, so the estimate was `-inf`. The search
    now keeps the best state seen, is bounded to log decay times in `[-8, 35]`, and polishes
    with Powell when L-BFGS ends worse.
- **The annealed estimate** (OQ-14, 2026-11-26). With its first settings (1000 particles,
  50% kept per step, 5 moves) it took 9–19 steps. Runs differed by 0.2–0.6 nats per datum,
  and against `p_LN`'s exact grid at `D = 5` it was 0.1–0.3 nats low. Six settings were
  measured on the grid at two faces and on run agreement at Jeffreys' `D = 7` corner. With
  2000 particles, 80% and 10 moves: grid error at the fast-and-slow face 0.003 ± 0.05 nats,
  run spread 0.06–0.08, 1.2 s per point. At the exact `D = 5` corner every setting sat 0.32
  above the grid, and the bell-shaped estimate agreed with it; the grid also fell short at
  the exact corner at `D = 3`. At `D = 7`, at Jeffreys' corner, runs differed by 2.5–14 nats
  under every setting. Hand-over: at `D = 5`, data where the bell-shaped estimate kept 5% or
  more agreed with the annealed one within 0.05 nats (16 of 16 at the corner for both
  priors). Below 5% it was off by 0.9–2.6 nats on Jeffreys' faces, or returned `-inf`.
- **Jeffreys' density in double precision** (2026-11-26). Against 80-digit decimal
  arithmetic, the direct `slogdet(J^T J)` was off by up to 43 nats at `D = 7`, 95 at `D = 9`
  and 260 at `D = 11` at near-corner and near-coincident states, and non-finite at 3 of 12
  states at `D = 5`. It was already 3.7e-4 nats off at typical states at `D = 4`. That is
  where the per-point marginal works, so the `D = 7` instabilities may come from it.
  `_log_sqrt_det_g` now uses `_log_sqrt_det_g_newton` for equally spaced times: the
  Jacobian is `diag(t/D) V diag(xi^(t_0-1))`, with `V` Vandermonde in `z = xi^c`. Its Newton
  factorisation `V = P Omega` gives `det Omega = prod (z_j - z_i)` exactly, and `P`'s entries
  are complete homogeneous symmetric polynomials with non-negative terms. Error at most
  8e-12 (`D = 5`), 1.4e-9 (`D = 7`), 5.8e-7 (`D = 9`), 5.7e-5 (`D = 11`) and 3.2 (`D = 13`).
  It takes 1.1 s per 10^5 states at `D = 11`. Test:
  `test_t4_jeffreys_density_matches_high_precision`.
- **Jeffreys to `D = 11`** (2026-11-26, on the corrected density).
  - *Importance sampling.* Effective share 53% (`D = 4`), 31% (5), 7.7% (7), 1.2% (9) and
    0.09–0.20% (11, three seeds). `log Z` matches brute force at `D = 4`–9. At `D = 11`
    brute force keeps 8 effective draws and is no reference.
  - *Annealed build.* At `D = 9`, `log Z` = −42.053 (importance sampling: −42.044 ± 0.064). At
    `D = 11`, three seeds gave −72.089, −72.137 and −72.147, each in 69–78 s, with about 19,940
    distinct particles of 20,000. Its reported error, 0.011, ignores the steps' correlation;
    the seeds spread by 0.06. `I(p_J)` from the clouds was 1.37 bits at `D = 9` and
    1.09–1.12 at `D = 11`, against A&M's ≈ 1.19 (digitised, ±0.05).
  - *Faces at `D = 5, 7`, corrected density.* The bell-shaped estimate kept 21–33% effective
    at the corner, near the corner, the fast-and-slow faces and the coincident state.
    Bell-shaped minus annealed was −0.04 to +0.003 nats on average. Two annealed runs
    differed by at most 0.06 nats on average and 0.38 at worst. The forward–backward bracket
    was at most 0.04 nats wide on average and 0.15 at worst. The annealed estimate took 3–4.5
    s per point at faces at `D = 7`.
  - *Stability against A&M's `I(p_J)`* (16384 draws, Monte-Carlo error about 0.01 bits).
    Importance-sampled against annealed: 1.690 vs 1.695 bits at `D = 7` (`log Z` −19.361 for
    both), and 1.329 vs 1.351 at `D = 9` (240 effective draws for importance sampling). At
    `D = 11`, 10 moves per step gave 1.072 bits and 50 gave 1.077, taking 75 vs 246 s. Ours is
    below A&M's by 0.01, 0.02 and 0.11 bits at `D = 5, 7, 11`. Two methods agree and more
    mixing changes nothing, so the build is not the cause. A&M's side (precision or sampler at
    `d = 11`) cannot be checked from the paper.
- **The annealed estimate at `D = 11`** (2026-11-26, 6 data per state). For `p_LN` at the
  corner, two runs differ by 0.05 nats on average and 0.12 at worst, with a bracket about
  0.01 wide. For Jeffreys at the corner, near it and on the fast-and-slow face, they differ by
  0.37–0.60 nats on average and up to 1.9, while each run's bracket stays under 0.12: the moves
  do not equilibrate there, so the bracket understates the error. The bell-shaped estimate
  keeps 0.1–0.5% effective and hands every point over. About 10 s per point (Jeffreys) and
  2.7 s (`p_LN`), 36–48 steps. That is adequate for the eye test's `B` at `D = 11` (about 170
  nats, read on a log scale), not for gaps between priors at `D = 11`.
- **First fast-suite run** (`762eae0`, 18.5 min): 140 passed, 17 failed: the T12 fixtures
  (8), T13(d) (2), T7(a) (2), T14(a) log-normals (2), T21(a) `mass_near`, T16(b) at the
  cheap cell, and T7(c), a bug in the batched kernel tables (two-dimensional data have two
  singular directions, not three), fixed after the run.
- **Third fast-suite run** (`0483d5b` plus the new `p_proj` sampler, T12(e) deselected while
  its fixture was re-fitted; 35 min with other jobs running): 149 passed, 6 failed. They are
  the same open test-side issues as in the second run. T12(e) then passed on its own.
- **Second fast-suite run** (`8f0ab36` plus the uncommitted T12 changes, T12 deselected while
  its fixtures were regenerating; 23.5 min): 143 passed, 6 failed. Every failure is one of the
  open test-side issues above: T7(a) (2), T14(a) log-normals (2), T21(a) `mass_near`, T16(b)
  at the cheap cell. T7(c)'s fix holds, and T11, suspected of Monte-Carlo noise, passes.
