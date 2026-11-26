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

**DD-Q4 — Continuous priors beyond the grids.** (`sampled.py`; `build_jeffreys`, `build_pln`,
`build_uniform`.) Spec §4.2, §4.4 and OQ-13. Exp-decay `p_J` from `D = 4`, and `p_U` and
`p_LN` above `D = 5`, are `SampledPrior`s: weighted clouds of 20000 draws in ordered `xi`,
with a normalised log density.
- *Jeffreys' sampler.* Adaptive importance sampling in unordered log decay times. Round 0
  draws `N(0.8, 1.5²)` log times; later rounds draw from Scott-bandwidth Gaussian kernels
  around the previous weighted cloud, with 10% of round 0's law. Each round has 8000 draws.
  It stops once `log Z` varies by less than 0.02 nats over three rounds, and a last round of
  20000 draws gives the cloud, `log_normaliser` and its standard error. Seed
  `SAMPLED_SEED + D`.
- *Results.* `log Z` was 0.8466 ± 0.0065 at `D = 4` and −4.0597 ± 0.0103 at `D = 5`, against
  brute force's 0.8411 ± 0.0013 and −4.0646 ± 0.0022. It builds in 20–25 s. `I(p_J)` at
  `D = 5` was 2.300 bits, against A&M's 2.29. The sampler's effective sample size levels off
  near 32% of a round at `D = 5` and 8% at `D = 7`; a better proposal is open.
- *Marginals.* The weighted cloud's mixture by default. `refined_log_marginal` gives a
  per-point estimate: up to 200 posterior centres resampled from the likelihood-weighted
  cloud, full-covariance or diagonal kernels, 20% defensive kernel density of the cloud,
  1000 draws, and each point's effective sample size. `worst_case_bias_pressure` screens
  with the cloud and refines the 20 highest states per point, with 64 draws each.
- *First attempt.* A Gaussian at the tight fit, with covariance `(g + 100 I)^-1`, reached
  1% effective sample size, and two such proposals differed by 3–4 nats.

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
- **T7(a), the fine-grid reference.** `test_t7a_continuous_quadrature_matches_a_fine_atom_sum`
  built its reference from density values at the midpoints of a 400 x 400 grid in `xi`,
  with the diagonal cells at full weight. Against a converged reference (exact cell masses,
  1600 x 1600), that reference was off by 2.5e-3 nats for `p_U` and 3.8e-2 for `p_LN`, while
  the code's quadrature was off by 2.4e-5 and 2.1e-4. The diagonal cells straddle the
  ordered region and carry half their area; midpoints misjudge `p_LN`'s spike at `xi -> 0`
  (DD-Q2). Resolved (MB, 2026-11-26): the test gives product laws exact cell masses from
  closed-form per-rate CDFs written in the test, the diagonal cells their ordered half at
  its centroid. All three priors pass at 1e-3.
- **`p_J`'s exp-decay grid loses mass at `D ≥ 4` (open).** Brute force over 2·10⁶ uniform
  ordered draws gives `log ∫ √det g`, which the grid (DD-Q1) underestimates. It misses 0.0%
  of the mass at `D = 2`, 0.2% at `D = 3`, 5.0% at `D = 4` and 24% at `D = 5`. An adaptive
  importance sampler agreed with brute force at `D = 5` (−4.0674 against −4.0646 ± 0.0022).
  The node weights are renormalised, so the grid prior is a distorted Jeffreys, not an
  unnormalised one. At `D = 5`, near-coincident rates (two within 0.02) carry 1.3% of its
  mass, against 5.5% in truth; a rate near instant decay (`xi_1 < 0.05`) carries 0.87,
  against 0.68 (2026-11-26). The eye test's `I(p_J)` at `D = 4, 5` still sits within 0.03
  bits of A&M. Its `B` band and the sweep's `p_J` scores at `D ≥ 4` rest on the distorted
  prior.
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
- **T14(a), `p_LN` and `p_LN^*` samplers.** The test integrates each density on its own
  600-point midpoint grid and requires the total to be 1 within `5e-3`. For the
  log-normals it gets 0.972, because midpoints miss the density's integrable spike at
  `xi -> 0` (the mechanism of T7(a), DD-Q2). The densities are exact in closed form (T23
  checks `p_LN`'s to `1e-8`). Open: integrate the test's marginal in the CDF, or loosen it.
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
