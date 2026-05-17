# Red-team review of test_000_static_infomax_fig1

Reviewer: red-team sub-agent
Date: 2026-05-17
Test file version: c0f5fe124f2440fba0c99eb9637255f353e29b6f
Spec version reviewed against: 245fa2b139520041294d6da314b9a19f5b171c55

## Summary

The suite covers all seven of the spec's named acceptance criteria with at least
one test apiece, and a few of the tests (T1, T2, T6, T7) are genuinely tight.
The weak area is everything that depends on the §3.5 atom-extraction heuristic
(T4, T5) and everything that relies on test-internal callers reading fields of
the returned object without re-validating them (T2, T3, T6). A wrong
implementation that (a) returns a converged `prior` but supplies a fabricated
`mi`, `f_kl`, or `mi_history` consistent with that `prior`, or (b) returns
atoms whose masses do not actually correspond to the prior, would slip past
several tests. The most exploitable single gap is the absence of any
independent check that `result.mi` equals `Σ p_i f_KL_i` computed from
`result.prior` and the likelihood — every test consumes `result.mi` and
`result.f_kl` as ground truth. There is also no direct check that BA actually
attains the *maximum* (only that it is monotone and that f_KL is flat on its
own reported support) — a stationary but suboptimal fixed point would pass
T2/T3/T6 trivially.

## Findings

### F1: No independent check that `result.mi` equals the MI of `result.prior` [severity: high]

**Test**: missing (covers T2, T3, T4, T6)

**Concern**: Every test consumes `result.mi`, `result.f_kl`, and
`result.prior` as if they are mutually consistent. A wrong implementation that
returns the converged prior correctly but reports a stale, fabricated, or
hard-coded `mi` (e.g. `mi = log(2)` constant for all m, or `mi = 0`, or `mi`
computed against the *previous* iterate) will sail through T2 (flatness is
checked against the reported `mi`, not the true one), T3 (`MI* ≤ log K_upper`
is easier to satisfy if MI is under-reported), and T6 (a fabricated monotone
sequence passes). Likewise nothing checks `result.f_kl` equals
`D_KL[p(·|θ_i) ‖ p_x]` re-computed from `result.prior` and the
likelihood matrix.

**What would resolve it**: add a standalone test that re-computes
`p_x = Σ_i p_i exp(logP[i, x])`, `f_kl_i = Σ_x p(x|θ_i)[logP[i,x] − log p_x[x]]`,
and `mi = Σ_i p_i f_kl_i` from `result.prior` and the cached likelihood, and
asserts equality with `result.mi`, `result.f_kl` to ~1e-12. Run across the
m-sweep.

---

### F2: No check that BA reaches the *global* MI, only that it is monotone and self-consistent [severity: high]

**Test**: missing (would close gaps in T2, T6)

**Concern**: The spec's T1 pins the optimum only at m = 1. At every other m,
the only "optimality" tests are T2 (flatness on whatever support BA settled
on) and T3 (the trivial bound `MI ≤ log K_upper`). A wrong implementation that
returns a *degenerate stationary point* — e.g. collapses to a single atom on
the first non-zero cell — satisfies T2 (one-cell support is trivially flat
because `f_KL` is a scalar there) and T3 (`log K_upper ≥ MI`) and T6
(monotone by virtue of being constant), yet the MI is much lower than the
true capacity. The spec's own §1.4 note that "mass strictly zero stays zero"
makes this a realistic failure mode if the BA loop is implemented wrongly
(e.g. a bug that masks out small cells too early).

**What would resolve it**: at each m in the sweep, assert a known lower bound
on MI* — e.g., for m=2 compute the analytic two-atom MI at θ ∈ {¼, ¾} or
{0, 1}-cell-centred and assert `result.mi ≥` that; or run BA from two
different initialisations and assert agreement of `mi` to ~1e-6. Even a
simple "MI* grows with m" monotonicity across the sweep would catch a stuck-
at-one-atom bug.

---

### F3: T2 flatness check is satisfied by collapse to a single support cell [severity: high]

**Test**: `test_t2_fkl_flatness_on_support`

**Concern**: The on-support set is defined by `masses > p_thresh = 1/(10 N_θ)`
which for the spec's default is 1e-4. If a wrong BA collapses the prior onto
a single cell (mass 1.0 on one cell), then `on_support` has one element, the
flatness check `|f_KL[on_support] − mi| / |mi| < 1e-3` is trivially satisfied
(only one entry, and `mi = p_i f_KL_i = f_KL_i` for that one cell, so the
difference is identically zero modulo float error), and the off-support
condition holds because the single-atom marginal makes f_KL non-positive
elsewhere on uniformly chosen cells. The test passes with arbitrarily small
MI.

**What would resolve it**: assert `on_support.sum() >= K_expected_lower(m)`
where `K_expected_lower(m)` is at least 2 for m ≥ 1 (and ideally a tighter
known bound for larger m). Alternatively, recompute `f_KL` independently
(see F1) and require flatness against the *true* MI.

---

### F4: T4 does not actually test convergence to Jeffreys — only that one specific stair-step CDF lies near the Jeffreys CDF at the atom locations [severity: high]

**Test**: `test_t4_converges_to_jeffreys`

**Concern**: Two compounding problems.
(1) `cdf_atoms = np.cumsum(masses)` evaluated only *at the atom locations*
gives the right-continuous CDF at the jump points, but never at any θ between
atoms. The Jeffreys CDF can be visited only at K ≈ 100 sample points, which
hides the true KS distance — which is achieved between jumps where the step
CDF lags maximally below the continuous CDF. The test therefore allows much
larger true KS distances than 0.05.
(2) Worse: many wrong "discrete approximations to Jeffreys" will pass. For
example, returning *the Jeffreys prior itself on the grid* (the m → ∞ limit,
no atom structure) would yield atom centroids and a step CDF that match
Jeffreys essentially exactly, despite being the wrong answer for finite m.
The test as written rewards "looks like Jeffreys" without independently
verifying that the prior is the MI-maximiser at m = 100.

**What would resolve it**: (a) evaluate KS distance on a dense θ grid using
the true step CDF, not at atom positions; (b) add a sanity check that the
prior at m = 100 is *not* the on-grid Jeffreys prior (e.g. `K << N_θ`, or
that mass concentrates onto a small number of disjoint runs), so that
"return Jeffreys" cannot win.

---

### F5: T5 silently ignores mismatches when atom counts differ [severity: high]

**Test**: `test_t5_grid_invariance_of_atoms`

**Concern**: The centroid comparison loop uses `zip(reference_centroids,
centroid_sets[n])`. If atom counts differ, `zip` truncates and the earlier
`len(set(counts.values())) == 1` assert would fail — *unless* the wrong
implementation produces equal atom counts that are themselves wrong. In that
case the centroids get pair-up by index order with no atom-correspondence
logic; for symmetric problems (θ ↔ 1−θ in the Bernoulli case) the symmetric
pairings will coincide even if atom positions are off, because both grids
will report atoms in the same sorted order. The "3 × max(1/N_θ)" tolerance is
~1.5e-2 — wide enough to mask substantive drift, since the centroid spacing
itself is O(1/√m) ≈ 0.32 at m=10.

**What would resolve it**: use a stricter tolerance scaled to the smaller of
the grid spacings (e.g. `max(1/N_θ)` not `3×`), and assert each atom
matching by nearest-neighbour distance rather than by index. Also assert
that atom masses agree across grids (currently only positions are checked).

---

### F6: T6 monotonicity does not constrain *what* `mi_history` contains [severity: high]

**Test**: `test_t6_ba_monotonicity`

**Concern**: The test asserts only that `np.diff(history).min() >= -1e-10`.
A wrong implementation that returns `mi_history = [0.0, 0.0]`, or
`[constant, constant, ..., constant]`, or any monotone sequence unrelated
to actual BA iterates, passes trivially. Combined with F1, nothing ties
`mi_history[-1]` to `result.mi` or to the true MI of `result.prior`.

**What would resolve it**: also assert `history[0]` equals the MI of the
uniform initial prior (computable in closed form: MI of channel under
uniform input — for Bernoulli at m=1 this is 1 − log 2 ≈ 0.3068 nats, etc.),
and assert `history[-1] == result.mi` to high precision. Optionally assert
strict increase for the first several steps from uniform.

---

### F7: T7 has a uniform-likelihood symmetry that masks many wrong implementations [severity: medium]

**Test**: `test_t7_degenerate_likelihood`

**Concern**: A θ-independent likelihood is the maximally symmetric input:
every cell has identical `f_KL_i`, so *any* normalised prior satisfies the
KKT condition with `mi = 0`. The masses check (`np.allclose(masses,
1/n_theta)`) does pin the prior to uniform — that's fine — but the BA step
itself is the identity on the uniform initialisation, so a wrong
implementation that *just returns the input prior unchanged whenever any
trivial condition is met* (an "early-out / identity" bug) will pass. There
is no test that exercises a non-uniform initial state, so an identity-on-
uniform implementation is indistinguishable here from a correct one.

**What would resolve it**: add a variant that perturbs the initial prior
(if the API allows) and asserts BA *restores* uniformity, or use a
likelihood that is θ-independent only on a subset, so the wrong-but-trivial
implementation cannot get away.

---

### F8: T1 mass tolerance is not actually tight enough to detect a small constant offset [severity: medium]

**Test**: `test_t1_m1_closed_form`

**Concern**: The atom mass returned by `extract_atoms` is `Σ_{i ∈ run} p_i`
summed over the run, but the spec's §3.5 defines a *run* as adjacent cells
above `p_thresh`. If an off-by-one or rounding bug leaks tiny mass into
adjacent cells just below `p_thresh`, the reported `mass` ≈ 0.5 − ε passes
`< 1e-6`, while the *true* prior mass at the boundary is e.g. 0.49 with
0.01 leaked into the interior — a substantial qualitative error. Likewise
the centroid tolerance `0.5/N_θ = 5e-4` matches half a cell, which is fine
for the "atom is at the first cell" assertion but cannot distinguish "atom
on first cell with 1e-7 leak" from "atom split between cells 0 and 1".

**What would resolve it**: also assert `result.prior.masses()[0]` and
`[-1]` are each within 1e-6 of 0.5, and that all other masses are below
~1e-10. This checks the prior directly rather than the extractor output.

---

### F9: T3 capacity bound is trivially loose [severity: medium]

**Test**: `test_t3_capacity_bound`

**Concern**: The spec correctly identifies T3 as a *permissive* bound, but
the test does not exploit any of the slack. With `floor = 1e-12`, every
non-zero cell counts; an implementation that smears the prior over many
cells will trivially satisfy `MI ≤ log K_upper`. For example, returning the
uniform prior on all `N_θ = 1000` cells gives `log K_upper ≈ 6.9`, which
exceeds the true MI* at any m ≤ 100 (capped at `log(m+1)` and in practice
much less). The test therefore detects only very pathological violations.

**What would resolve it**: keep T3 as a sanity check, but add a companion
assertion `result.mi <= np.log(m + 1) + 1e-10` (channel-capacity upper
bound — output alphabet size). This catches MI values that are simply
fabricated to be large.

---

### F10: Off-support check in T2 uses absolute 1e-10 tolerance, not relative [severity: medium]

**Test**: `test_t2_fkl_flatness_on_support`

**Concern**: For large m, `MI*` is O(log m) and `f_KL` values are similarly
sized. A bug that lets `f_KL > MI*` by a small *relative* amount (say 1e-8
relative, which on `MI ≈ 3` is 3e-8) would fail the test. Conversely, the
1e-10 tolerance is so tight that the test will fail spuriously on legitimate
float64 noise at larger m — the implementation may then be tempted to add a
sloppy slack. Asymmetric tolerance treatment between on-support (relative
1e-3) and off-support (absolute 1e-10) is inconsistent.

**What would resolve it**: use a relative or scaled tolerance off-support
(e.g. `abs(mi) * 1e-8 + 1e-12`).

---

### F11: No test that `result.f_kl` matches the f_KL at the *converged* prior, not at some earlier iterate [severity: medium]

**Test**: missing

**Concern**: The spec's §3.4 pseudocode computes `f_KL_i` *before* the BA
update, so a literal implementation returns `f_KL` at the iterate just
*before* the final step, not at `result.prior`. T2 silently accepts this
because the prior changes very little near convergence, but the test cannot
distinguish "f_KL is consistent with the returned prior" from "f_KL is
consistent with the previous prior". With aggressive early stopping
(`ε_I = 1e-10`) this is harmless; with looser convergence it could mask a
half-converged result.

**What would resolve it**: re-compute `f_KL` from `result.prior` and the
likelihood (see F1) and require equality.

---

### F12: T4 does not pin the *number* of atoms at m=100 [severity: medium]

**Test**: `test_t4_converges_to_jeffreys`

**Concern**: Mattingly Fig 1 / Fig 3C predicts K(m) growing roughly like
√m, so at m=100 K should be on the order of a couple dozen. The test does
not check K at all (it just sorts and accumulates whatever atoms the
extractor returned). A wrong implementation reporting, say, K = 2 (atoms
at boundary cells) would have `cumsum(masses) = [0.5, 1.0]` against
`F_J(thetas) ≈ [F_J(θ_lo), 1 − F_J(θ_lo)]` — likely failing KS by a wide
margin, *but* an implementation that returns K = 1000 with masses
proportional to the on-grid Jeffreys prior will pass (see F4). The test
neither rules out under-atomising nor over-atomising.

**What would resolve it**: assert `K_lower ≤ K ≤ K_upper` at m=100, with
bounds taken from Mattingly's tabulated value (~25 atoms at m=100) plus
generous slack.

---

### F13: No test for permutation/reflection symmetry of the optimum [severity: medium]

**Test**: missing (implied by the math, not in spec's T-list)

**Concern**: The Bernoulli likelihood is symmetric under θ ↔ 1−θ
(equivalently x ↔ m−x), and so is the MI objective. The optimal prior
satisfies `p*(θ) = p*(1−θ)`. None of the tests check this — even at m=1
T1 checks each boundary atom independently, not that they are reflections
of each other. A wrong implementation that breaks symmetry (e.g. asymmetric
update bug, or numerical drift accumulated over iterations) can pass T1's
component checks while producing an asymmetric prior at other m.

**What would resolve it**: at each m in the sweep, assert `result.prior`
satisfies pointwise symmetry under the reversal `i → N_θ−1−i` to ~1e-8.

---

### F14: Likelihood is not exercised against an analytic reference [severity: low]

**Test**: missing

**Concern**: `binomial_log_likelihood` is the foundation for every other
test, but no test compares it to `scipy.stats.binom.logpmf` (or hand
arithmetic) on a small example. A bug here (e.g. log(1-θ) replaced by
log θ) would propagate silently into every other test, where it might or
might not cause failures depending on the symmetry of the affected test.
This is the kind of bug T7 cannot catch (uniform-likelihood symmetry
again).

**What would resolve it**: a 5-line test asserting
`binomial_log_likelihood(np.array([0.3]), m=3)[0]` matches the hand-computed
log-pmf values for x ∈ {0,1,2,3}.

---

### F15: T1 known-answer is on-grid only; continuum log 2 sanity check absent [severity: low]

**Test**: `test_t1_m1_closed_form`

**Concern**: DC-1 motivates testing the on-grid MI_ref rather than `log 2`.
That's correct. But there is no scaling check that `MI_ref → log 2` as N_θ
grows, which would catch an implementation that hard-codes MI_ref (or that
silently fails to use the cell-centred convention). Cheap to add.

**What would resolve it**: parametrise T1 over N_θ ∈ {100, 1000, 10000} and
assert `(log 2 − result.mi)` shrinks like `~(log N_θ)/N_θ`.

---

### F16: T6 does not exercise convergence from a non-uniform initial state [severity: low]

**Test**: `test_t6_ba_monotonicity`

**Concern**: BA's monotonicity guarantee is global, not just from uniform.
If the API allows a custom initial prior (it doesn't appear to in the
current stubs, but the spec leaves room), monotonicity from a perturbed
start is the more discriminating test. Low severity because the current
API forecloses it.

**What would resolve it**: if the API gains an `init=` argument, add a
perturbed-start variant.

## What the test suite gets right

T1 is genuinely sharp — the on-grid analytic reference is the right move
post-F1, and the centroid + mass + MI triple is hard to fake. T7's
prior-equals-uniform assert (to atol 1e-12) is tight. T2's KKT structure
(flatness on, dominance off) is exactly the right invariant to assert from
the spec. The fixture-based parametrisation over the full m-sweep means
many tests get free coverage at every m, and the imports cleanly mirror
the spec's §6 layout so adding the missing checks (F1, F2, F11, F13, F14)
will be straightforward additions rather than rewrites. The decision to
test KKT (T2) rather than asymptotic convergence rate is the right
trade-off for a Fig-1 reproduction.
