# Red-team review of 000-static-infomax-fig1

Reviewer: red-team sub-agent
Date: 2026-05-17
Spec version: 6d895ba436a411fd8d0dbb2fdc94059c65d85571

## Summary

The spec is structurally sound and faithfully captures Mattingly et al. 2018's
Bernoulli example and the standard Blahut–Arimoto recipe. The math statement,
optimality condition, and BA update are correctly transcribed. However the
implementation contract has at least one numerically wrong test tolerance that
will block T1 with the spec's own default grid, the pseudocode in §3.4 has an
off-by-one variable-existence bug, and several claims about uniqueness, support
discreteness, and "monotonic convergence" lean on properties that hold only in
the continuous setting the algorithm does not use. Two qualitative-test
thresholds (T3, T4) interact badly with the heuristic atom extractor of §3.5 in
a way the spec does not address. Findings: **3 high, 5 medium, 4 low.**

## Findings

### F1: T1 tolerance is inconsistent with the cell-centred grid it mandates [severity: high]

**Location**: §4, test T1 ("MI* within 0.001 nats of log 2"), in combination
with §3.1 (default `N_θ = 1000`, cell-centred) and DC-1.

**Concern**: With the cell-centred convention the extreme cells sit at
`θ ≈ 1/(2 N_θ) = 5e-4` and `1 − 5e-4`. The best two-atom prior placeable on the
grid is `½` at each extreme cell. A direct calculation (verified numerically)
gives `MI = (1−θ_1) log((1−θ_1)/0.5) + θ_1 log(θ_1/0.5) ≈ 0.68885` nats at
`N_θ = 1000`. The deficit from `log 2 ≈ 0.69315` is `≈ 4.3e-3` nats — over
four times the asserted `1e-3` tolerance. The leading deficit scales like
`θ_1 log(1/θ_1) = O(N_θ^{-1} log N_θ)`, so the test as written will fail at all
of `N_θ ∈ {200, 500, 1000, 2000}` (the deficit at `N_θ = 2000` is still
`≈ 2.3e-3`). The spec author appears to have confused the analytic
optimum (which lives on θ ∈ {0,1}, not representable on this grid) with what
BA can actually achieve on the grid it is given.

**What would resolve it**: Either (a) relax the T1 tolerance to e.g.
`(2/N_θ) log(2 N_θ)` nats and document the scaling, or (b) switch to a grid
that includes the endpoints (and handle the 0·log0 / log0 limits explicitly in
the likelihood code), or (c) compare against the analytic two-atom MI evaluated
*at the actual grid cell positions* rather than against `log 2`. Whichever
choice is made, DC-1 should be promoted from an aside to a numerical
prediction.

> M: good catch. let's use suggestion (c), evaluate the analytic solution on the grid, and compare to that. Does this resolves DC-1?

> C: T1 rewritten in §4 of the spec to compare against `MI_ref = log 2 − H(1/(2 N_θ))` with tolerances tightened to 1e-6. The DC-1 follow-up question (whether this fix resolves DC-1 entirely) is deferred to the discussion phase.

> C [follow-up]: DC-1 kept as-is per reviewer's decision; no further spec edit beyond the T1 fix above. DC-1 remains the standing caveat that the cell-centred grid never includes θ = 0 or θ = 1 exactly; tests work with the on-grid analogues as T1 now does.

---

### F2: §3.4 pseudocode references `I_{τ−1}` at τ = 0 [severity: low]

**Location**: §3.4, BA loop pseudocode.

**Concern**: The convergence check `|I_τ − I_{τ−1}| < ε_I` is evaluated inside
the loop, but `I_{τ−1}` is undefined on the first iteration. There is also no
initialisation shown. Minor, but it is exactly the kind of thing that gets
copy-pasted into the implementation.

**What would resolve it**: Initialise `I_prev = −∞` before the loop, or guard
the test with `τ ≥ 1`. (`τ_min = 10` happens to mask the bug but only because
`τ_min > 1`.)

> M: let's just add `I_prev = −∞`

> C: Added `I_prev ← −∞` before the loop in §3.4 and explicit `I_prev ← I_τ` update at end-of-step; removed the `I_{τ−1}` reference.
---

### F3: §3.4 pseudocode does not match the §1.4 update [severity: medium]

**Location**: §3.4 vs §1.4.

**Concern**: §1.4 defines the update with `exp(f_KL(θ; p_τ))` and a partition
function `Z_τ = Σ_θ exp(f_KL(θ; p_τ)) · p_τ(θ)`. The §3.4 pseudocode writes
`p_new ← exp(f_KL_i) · p_i; p_new ← p_new / Σ p_new`, which is fine
mathematically but uses log-domain operations nowhere despite §3.2 insisting
"we work in log-space where possible". For the m values in the sweep (up to
100) `f_KL` is bounded by `log(m+1) ≈ 4.6` nats, so `exp(f_KL)` is small
enough to avoid overflow — but the spec should either drop the log-space
claim or rewrite the BA step as
`log p_new ← f_KL_i + log p_i; p_new ← softmax(log p_new)` so that the
mantra in §3.2 is actually followed in the BA step (which is the only place
overflow could realistically bite at larger m).

**What would resolve it**: Add a log-space variant of the BA step in §3.4,
or remove the log-space promise from §3.2.

> M: let's use the log-space variant of the BA step

> C: BA step in §3.4 rewritten as `log_p_new = f_KL + log_p; log_p_new −= logsumexp(log_p_new)`; `p ← exp(log_p)` materialised at each step for downstream uses (computing `p_x`, `I_τ`).

---

### F4: T3 ("capacity bound MI* ≤ log K") is checked against the *detected* K, not the true K [severity: high]

**Location**: §4, test T3; depends on §3.5 atom extraction.

**Concern**: The bound `MI ≤ log K` from Mattingly Fig 3C is a statement about
the *true* number of support atoms of `p*`. The spec uses the heuristic of
§3.5 (threshold `1/(10 N_θ)` then group adjacent runs) to *detect* K. Two
failure modes:
  (i) The threshold drops a real low-weight atom, so detected `K < K_true`
      and `log K < log K_true` can fall below `MI*`, giving a spurious test
      failure.
  (ii) Adjacent-cell grouping at coarse `N_θ` can *merge* two true atoms that
      happen to land in neighbouring cells, again under-counting K.
Either failure mode invalidates the test without invalidating the
implementation. The asymmetric direction (an upper bound on MI in terms of a
quantity that can only shrink as detection becomes more conservative) is the
wrong way around.

**What would resolve it**: State T3 against an upper bound on the true atom
count (e.g. count *any* cell with `p_i > 0` after a hard floor of, say,
`1e-12`), or use a much smaller `p_thresh`, or replace the test with the
direct algebraic check `MI* ≤ log(#{i : p*_i > 1e−12})`.

> M: it's not very clear to me what makes sense here. maybe if the test fails, there should be an additional quantification of how likely is it to have failed because of such an undercounting? please advise.

> C: Adopted the structural fix instead of the failure-quantification path: §4 T3 now asserts `MI* ≤ log K_upper + tol` where `K_upper = #{i : p*_i > 1e-12}` is a permissive grid-cell count direct off the converged prior (no atom-extraction heuristic in the loop). This is an honest mathematical bound — `K_upper ≥ K_true` by construction, so the bound holds whenever the math holds. The §3.5 extractor is unchanged and still drives the figure and the results table.

---

### F5: T4's KS test against the continuous Jeffreys CDF at m=100 is not justified [severity: medium]

**Location**: §4, test T4; §1.5 second bullet.

**Concern**: The number of atoms at `m = 100` is, by Mattingly's own scaling
`K ∼ L^{1/ζ}` with `L = π √m ≈ 31.4` and `ζ ≈ 3/4`, on the order of
`K ∼ 31.4^{4/3} ≈ 99` atoms. The supremum gap between a step function with K
jumps and a continuous CDF is at least `1/(2K) ≈ 5e-3` *even when atoms are
placed optimally at the Jeffreys quantiles*. The asserted KS threshold `0.05`
is plausible but the spec does not show this — and at the smaller m values
that are still in the sweep (e.g. m=20 with K≈10), the same test against the
same threshold would clearly fail. The spec should either justify the choice
of threshold from first principles or note explicitly that T4 is m=100-only by
design.

Separately, §1.5 says the "empirical histogram of atom locations weighted by
λ_a" should approach `p_J`. A set of atoms is not a histogram, and one cannot
compare it pointwise to a density. The CDF formulation in T4 is the right
one; §1.5 prose should be made consistent with it.

**What would resolve it**: Replace the "histogram" sentence with a CDF/quantile
statement, and either tighten T4 to "m = 100 only" or compute the predicted
KS-distance floor `~ 1/(2K(m))` and use it as the per-m tolerance.

> M: do make the language consistent. otherwise it seems to me that instead of KS test at the m=100 endpoint one would want to quantify the rate of convergence to the Jeffreys as m increases. I realise that this is harder to quantify, and would basically only work as a visual sanity check. So maybe keep the test for just m=100, and then include the rest as a convergence plot in the report. 

> C: §1.5's second bullet rewritten in CDF terms (no more "histogram"), with an explicit note that the KS floor `~ 1/(2 K(m))` makes the assertion m=100-only. T4 itself unchanged. §5 gained item 3: a convergence plot of KS distance vs m with the discreteness floor overlaid, framed as a visual sanity check not a hard assertion.

---

### F6: Uniqueness claim in §1.2 is unjustified [severity: medium]

**Location**: §1.2 ("the maximum is unique modulo the discreteness of the
grid").

**Concern**: `I(Θ; X)` is concave in `p`, but not strictly concave in general:
distinct grid distributions can produce the same channel output distribution
`p(x)` (this is exactly what happens when two grid cells are close enough
that their likelihood columns are nearly collinear, which is the regime where
"atoms" form). The optimum *value* is unique but the optimum *p\** is not in
general — BA from different initialisations may land on different mass
distributions with the same support cluster. The spec uses uniqueness
implicitly in T5 (asserting grid-to-grid atom-centroid agreement); without
strict concavity that test can fail for reasons unrelated to the
implementation being wrong.

**What would resolve it**: State that the optimum *value* `MI*` is unique and
the *output marginal* `p*(x)` is unique, but the input prior is unique only on
its support (Csiszár 1974). Then T5 should compare per-atom *output* marginals
or the support set, not centroids of mass within runs.

> M: to me this seems like a thing that can't really cause any issues. Probably worth clarifying the language though.

> C: §1.2's uniqueness sentence reworded: the maximum *value* `MI*` and the optimal output marginal `p*(x)` are unique; the prior `p*(θ)` is unique only on its support. Added a one-line guidance for cross-grid comparisons (support- or marginal-based, not pointwise mass).

---

### F7: Discreteness argument quietly switches from discrete θ to continuous θ [severity: medium]

**Location**: §1.3, final paragraph ("In the continuous setting, the
analyticity of `f_KL − MI` in θ implies the support of `p*` is a finite set
of points").

**Concern**: §1.2 sets up the problem on a discrete grid (`Σ_θ`, `Δ(Θ)`
= simplex of PMFs over the grid). The analyticity argument requires `f_KL` to
be analytic in θ on a connected open subset of ℂ — true for the continuous
Bernoulli problem, not even meaningful on a finite grid. The spec then folds
the continuous result back into the grid claim ("on a fine grid the 'atoms'
appear as one or a few adjacent grid bins"). This is the only justification
the spec gives for expecting clusters in the first place, and it is logically
shaky: on a grid, *any* maximiser is automatically "discrete" trivially. The
real content — that the *continuous* optimum has finite support and the grid
optimum tracks it — should be stated as an assumption (grid is fine enough to
resolve atom spacing) rather than smuggled in.

**What would resolve it**: Add one sentence: "We assume `N_θ` is large enough
that the continuous optimum's atom spacing `~1/√m` is resolved, i.e.
`N_θ ≫ √m`. Under this assumption the grid maximiser's mass clusters track
the continuous atoms to within one cell." Note this then justifies `N_θ ≥
1000` for `m ≤ 100`.

> M: ok, worth clarifying the language. does not seem to me to cause a technical issue though.

> C: §1.3 final paragraph extended: the fineness assumption `N_θ ≫ √m` is now stated explicitly (from Mattingly's atom-spacing scaling), with the note that `N_θ = 1000` covers `m ≤ 100`.

---

### F8: §3.3 `update` signature is incompatible with BA [severity: medium]

**Location**: §3.3, `Prior` protocol.

**Concern**: The signature `def update(self, fKL: ndarray) -> "Prior"` takes
only `fKL` and returns a Prior. But the BA update needs *both* the previous
mass vector and `fKL` (it computes `p_τ · exp(fKL) / Z`). If `update` is a
method on `self`, the previous masses come from `self.masses()` — fine.
However, for the future `AtomicPrior` (atoms at `(θ_a, λ_a)`), `fKL` evaluated
on the grid is not the right input: you need `fKL(θ_a)` at the atom positions,
which differ from the grid. The protocol therefore does not actually abstract
over the two prior types it claims to support, and the §3.3 promise that
`AtomicPrior` "plugs in behind the same interface without rewriting downstream
code" will not survive contact with §S5 of the supplementary (which uses
gradients `∂MI/∂θ_a` and `∂MI/∂λ_a`, not a BA step). This is the kind of
abstraction that looks fine until you write the second implementation.

**What would resolve it**: Either make `update` take a callable `fKL_fn :
ndarray[θ] -> ndarray[θ]` and let each Prior subclass query it at its own
support, or split the protocol into a "BA-updatable" interface (for grid) and
a "gradient-updatable" interface (for atoms). Be honest that these are
different optimisers, not one optimiser with two backends.

> M: if it's possible, I'd not have two optimisers at this point. So if we can make the interface compatible with all prior types via a callable fKL_fn, let's do that

> C: §3.3 `Prior` protocol changed: `expected_data` takes a `log_likelihood_fn`, `updated` takes an `f_kl_fn`. Each `Prior` queries the callable on its own support — no grid-shaped buffer is baked into the interface. The section also acknowledges that the per-subclass `updated()` step is a different algorithm under the hood (BA for grid, gradient for atoms, SMC for particles); the interface unifies the protocol but not the algorithm. The src/infomax/prior.py stub is now stale; it will be re-aligned at the next implementation step (§3 is back to draft).

---

### F9: "the marginal `p(x) = Σ_θ p(x|θ) p(θ)` (the *expected data*)" is unusual terminology [severity: low]

**Location**: §1.2.

**Concern**: "Expected data" usually means `E[X]` (a value), not the marginal
distribution `p(x)` (a distribution). Mattingly uses "expected data" loosely
too (e.g. in §S1) but the spec is ostensibly self-contained. A reader from
information theory will read "expected data" as "mean of X" and be confused
when it is then summed over.

**What would resolve it**: Call it "marginal distribution of X under the
current prior" or "data marginal". Reserve "expected data" for `E[X]`.

> M: I'm fine with the "expected data" notion, leave it as is

> C: No spec change. Finding dismissed per reviewer's note; the terminology stays in §1.2.

---

### F10: T6 monotonicity tolerance is asymmetric with the convergence threshold [severity: low]

**Location**: §4, T6 vs §3.4 default `ε_I = 1e-10`.

**Concern**: T6 allows "floating-point slack `1e-12` per step". But
`ε_I = 1e-10` is the *stopping* threshold; the per-step changes near
convergence can be down at `1e-11` or `1e-12`, comparable to the asserted
slack. Without specifying whether the per-step slack is absolute or relative,
or whether it accumulates across the (potentially 5000) iterations, T6 can
trigger spurious failures from FP noise that have nothing to do with BA being
broken. With float64 summation over `N_θ = 1000` terms, per-step rounding
error in `I_τ` is realistically `~ 1e-14 · max|f_KL| · N_θ ~ 1e-10`, which
already exceeds the asserted tolerance.

**What would resolve it**: Either widen the per-step slack (`1e-10` absolute
or `1e-12` relative to `|I_τ|`), or change T6 to check that any per-step
decrease is bounded by a multiple of machine epsilon times `MI*`.

> M: this seems like minor issue, setting the per-step slack to 1e-10 seems fine to me if that's better for numerical reasons

> C: §4 T6 slack widened from 1e-12 to 1e-10 per step, with a one-line note tying it to the realistic float64 rounding budget for `Σ` over `N_θ = 1000` terms of `|f_KL| ≲ log(m+1)`.

---

### F11: "Bernardo's reference prior in this limit is the Jeffreys prior" omits regularity conditions [severity: low]

**Location**: §1.5, second bullet.

**Concern**: The "benign assumptions" (Mattingly's phrasing, citing Clarke
& Barron) under which the reference prior reduces to Jeffreys include
asymptotic normality of the posterior, a compact parameter space, and bounded
KL information rate. These all happen to hold for Bernoulli but the spec
should not present the equivalence as a general fact — it's a theorem with
preconditions, and several spec readers (a multi-parameter case is planned for
spec 002) will inherit the mistake.

**What would resolve it**: One sentence: "for regular models satisfying the
Clarke–Barron conditions (asymptotic normality, compactness, finite Fisher
information), Bernardo's reference prior converges to Jeffreys as m → ∞;
Bernoulli on [0,1] satisfies these."

> M: it would be even better to state what kind of model families will satisfy these criteria. Can we say this? If not, then let's just indeed state what the red team suggested.

> C: Applied the proposed wording in §1.5: the regularity conditions for Bernardo → Jeffreys (compact parameter space, identifiable parametrisation, continuous positive-definite Fisher information) are now stated, with positive (regular exponential families on a compact parameter space, including Bernoulli) and negative (parameter-dependent support, singular Fisher, non-compact parameter spaces) examples. Clarke & Barron (1994), DOI 10.1016/0378-3758(94)90153-8, added to §9 References.

---

### F12: The diagram does not match §1.1's "one random variable over {0,…,m}" framing [severity: low]

**Location**: `diagrams/000-static-infomax-fig1-pgm.{py,svg}` + §1.1 + revision
log.

**Concern**: The revision log says the node was renamed `x_i → x` and the
plate label became `m`, "no change to the underlying generative model". But
the plate still encloses a single observed node `x`, which by plate
conventions means `m` i.i.d. copies of `x`. §1.1 then explicitly says "there
is no need to enumerate sequences in `{0,1}^m`" and works only with the
sufficient statistic — i.e. there is *not* a plate of m i.i.d. observations
in the model the rest of the spec uses; there is a single `Binomial(m, θ)`
draw. The plate is therefore misleading: a reader following the diagram will
write a different likelihood than the one in §1.1 (Bernoulli per flip vs
Binomial of the count). The pre-refactor `x_i` inside an `i = 1, …, m` plate
was actually the correct picture for the Bernoulli generative story; the
post-refactor diagram is neither the Bernoulli nor the Binomial picture.

**What would resolve it**: Either revert the diagram to `x_i` with plate
`i = 1, …, m` (matches the prose "each of the m observed flips is i.i.d.
Bernoulli(θ)") and add one line of text saying "we work with the sufficient
statistic for computation", or remove the plate entirely and add a single
node labelled `x ∈ {0,…,m}` with edge labelled `Binomial(m, θ)`. The current
intermediate state is wrong under plate semantics.

> M: this doesn't seem true to me. I have never actually seen the index variable notation for plates that the first version had, and I thought that omitting it will keep it semantically unchanged. What is the reference for this plate sematics?  

> C: No spec or diagram change. The bare-`x`-in-plate-with-corner-`m` convention IS the standard plate convention and means `m` i.i.d. copies of `x` — the same as the indexed `x_i` with corner `i = 1, …, m` form. References for the convention: Buntine (1994), *JAIR* 2:159–225 (original plate notation); Koller & Friedman (2009), *Probabilistic Graphical Models* §6.4 "Plate Models"; Bishop (2006), *PRML* §8.1; the PyMC and daft documentation both routinely use the bare-`x` form. The redteam was technically right that a plate around bare `x` denotes replication, and wrong to call the current diagram "neither Bernoulli nor Binomial": it IS the Bernoulli plate model. The spec's caption already states that computation uses the sufficient statistic. Finding dismissed.

## What the spec gets right

The mathematical statement (likelihood, MI objective, KKT support condition,
BA fixed-point) is correctly transcribed from Mattingly and the BA references;
sign conventions, base-e logs, and the `f_KL` definition are all consistent
internally. The cell-centred grid motivation (avoiding `log 0` at the
endpoints) is sound and the DC-1 caveat is correctly flagged even if the
numerical consequence is mis-quantified in T1. The test list T1–T7 covers the
right phenomena (closed-form benchmark, KKT flatness, capacity bound,
Jeffreys limit, grid invariance, monotonicity, degenerate-channel sanity);
the issues are in tolerances and detection coupling, not in the choice of
tests. The scope discipline (single parameter, BA only, atom-refinement
deferred) is clean and the deferred-choice register makes the limits explicit.
