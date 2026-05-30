# Red-team review of 001-infomax-betting

Reviewer: red-team sub-agent
Date: 2026-05-30
Spec version: 8292233 (commit 829223355edd56ad5a4e6b4fdaf6d7bd9cd2e731)

## Summary

The spec's load-bearing mathematics is sound. I checked the Kelly KL
decomposition (1.3.3), the Part-1 and Part-2 closed forms (1.4.4 / 1.5.2)
against independent Monte-Carlo, the digamma Beta log-moment identities
(§4.3), the moment-matched Beta inversion (1.8.1 / §9.5), the Part-2
loss-term moment difference and its non-negativity claim, and the oracle
upper bound (§1.10): all hold, numerically and analytically. The reused
spec-000 machinery (`blahut_arimoto`, `cell_centred_grid`,
`binomial_log_likelihood`, `GridPrior.masses`) matches the calls made in
§2.4, and the Kelly tutorial's identities agree with §1.3. There are **no
high-severity (result-invalidating) errors**. The flaws that exist are
real but bounded: the most consequential is that the justification for
excluding `n = 1` from Part 2 (that `p_MM` is undefined because
`σ² = μ(1−μ)`) is *false for the grid object the code actually uses* — on
the cell-centred grid `p*_1`'s variance is strictly below the bound, so
`p_MM` exists and `moment_match_beta` would not raise, undercutting the
stated reason and the T9 guard. Beyond that, the cell-enumeration of §2.6
is under-specified for Part-1 (crossing it with `k_plus_sweep`), one
discrete code path is not exercised by the Monte-Carlo tests it is claimed
to be, and the §9 Derivations section carries a systematic
section/equation numbering collision (everything internal is labelled
"§10/eq-10.x" while the section ships as §9). The spec is close to
ready for downstream work; the n=1/`p_MM` reasoning and the §2.6
enumeration should be tightened before implementation, and the numbering
collision cleaned up so cross-references resolve.

## Findings

### F1: The `n = 1` / `p_MM`-undefined justification is false for the grid object the code uses [severity: medium]

**Location**: §1.8 (final paragraph), §2.5 (first bullet of the `n` sweep
rationale), §3.3 P9 / §3.4 T9.

**Concern**: §1.8 states "for `n = 1`, `p*_1 = ½(δ_0 + δ_1)` with
`σ² = μ(1−μ) = ¼` and `ν = 0` — `p_MM` is undefined in that degenerate
case." §2.5 and DC-4 repeat this as *the* reason Part 2 excludes `n = 1`,
and T9 claims to "guard the `n = 1` exclusion … the case where the bound
is exactly saturated." But §1.2 / §2.3 are explicit that this spec uses
the **raw cell-centred grid masses** of the BA output, with no atom
extraction, and spec 000 §3.1 / T1 place the `n = 1` atoms at the first
and last *cell centres* `θ = 1/(2G)` and `1 − 1/(2G)`, **not** at `0` and
`1`. On that grid object (G = 1000):

```
μ = 0.5, σ² = 0.2495, μ(1−μ) = 0.25  ⇒  σ² < μ(1−μ) strictly,
ν = μ(1−μ)/σ² − 1 ≈ 0.0020 > 0,  α = β ≈ 0.0010.
```

So `p_MM` *is* well-defined for the grid `p*_1`, and
`moment_match_beta` would **not** raise (`variance < mean(1−mean)` holds).
The continuum identity `σ² = ¼` only holds for the idealised `{δ_0, δ_1}`,
which the code never constructs. Consequently (a) the stated reason for
the `n = 1` exclusion is wrong, and (b) T9's claim that it "guards the
`n = 1` exclusion … where the bound is exactly saturated" describes a
condition that does not occur on the grid — at `n = 1` the matched Beta
would be returned (an extreme, near-degenerate U-shape), not rejected.
A closely related imprecision in §1.8: "`p*_n` is multi-atom for all
`n ≥ 2` … so `σ² < μ(1−μ) strictly`" — multi-atomicity alone does not
imply the strict bound (a 2-atom prior on `{0,1}` is multi-atom yet
saturates it); the operative condition is "support not contained in
`{0,1}`", which holds for `n ≥ 2` only because the atoms are interior.

**What would resolve it**: Restate the `n = 1` exclusion on its
*independently sufficient* grounds (it is the trivially extreme,
analytically understood boundary case, per §2.5's second bullet and OQ-4)
and drop the claim that `p_MM` is undefined there. If a hard guard is
still wanted, either (i) test `moment_match_beta` rejection on the
true-continuum `½(δ_0+δ_1)` inputs explicitly (and note the grid object
does not hit it), or (ii) add a separate guard that excludes `n = 1` from
Part 2 by design rather than relying on a `ValueError` that will not fire.
Fix the "multi-atom ⇒ strict bound" wording to "interior support ⇒ strict
bound".

---

### F2: Part-1 cell enumeration is under-specified against `k_plus_sweep` [severity: medium]

**Location**: §2.6 (the `enumerate_cells(...)` call), with §2.4
(`for each (n, k_plus, hyperprior, K) cell`) and §2.2
(`BettingCell.k_plus: int | None  # None for Part 1`).

**Concern**: §2.6 calls
`enumerate_cells(parts={1, 2}, n_sweep={2,3,5,10,20}, k_plus_sweep={2,3,5},
hyperpriors={H1,H2,H3}, K_sweep={1,2,3})`, passing `k_plus_sweep` for
*both* parts in a single call. Part-1 cells carry `k_plus = None` and
their `V̄₁` does not depend on `k_plus`. The spec never states whether
Part-1 cells are emitted **once** (with `k_plus = None`) or **crossed
with the three `k_plus` values** (yielding three identical-`V̄₁`
duplicates per `(n, 𝓗, K)`). This matters concretely because:
(a) the cell *count* and ordering feed the per-cell `rng.spawn` of §2.6,
so the ambiguity changes which RNG stream each cell gets and therefore
every Part-1 result; and (b) T11 freezes the enumerated
`(cell, stream_seed)` list — but the spec gives the reader no way to
predict what that list should contain for Part 1, so the snapshot cannot
be reviewed for correctness, only diffed against itself.

**What would resolve it**: State explicitly that Part-1 cells are emitted
once with `k_plus = None` (i.e. `k_plus_sweep` is iterated only for
`part = 2`), and that the lexicographic ordering of §2.6 treats
`k_plus = None` as a single value sorting before/after the integers.
Pin this in the `enumerate_cells` contract so T11's snapshot is
predictable from the spec.

---

### F3: The discrete `p*` path inside `V̄₁` is not exercised by the Monte-Carlo test it is credited to [severity: medium]

**Location**: §1.6 (test-coverage paragraph) vs §3.3 P2a / §3.4 T2a.

**Concern**: §1.6 claims the discrete posterior formulas (1.6.3)/(1.6.4)
are "consumed inside `V̄` (for `p*`) by **T2a / T2b**". But P2a pins T2a
to a single configuration — "`p_J` on H3, `n = 5, K = 2`" — i.e. T2a runs
only the **Beta** prior, never `p*`. T2b *does* run all four priors
(including `p*`) but is **Part 2 only** (`V̄₂`). So the discrete `p*`
posterior-mean path *inside `V̄₁`* (Part 1) is never checked against an
independent Monte-Carlo reference. It is checked algebraically — T13
(log-space vs naïve Bayes) and T4 (discrete vs Beta mean) validate the
`μ̂_n(p*, ·)` array, and `V̄₁` is then a deterministic finite sum of that
array against closed-form moments — so this is a *coverage gap*, not a
demonstrated bug. But the spec's own claim that T2a covers `p*` inside
`V̄₁` is inaccurate, and an error confined to the way the discrete `μ̂`
array is *assembled into* `V̄₁` (e.g. a wrong moment index used only on
the `p*` branch) would slip past every MC check.

**What would resolve it**: Either add `p*` to T2a's parametrisation (one
extra Monte-Carlo cell), or correct §1.6 to state that the discrete-`p*`
`V̄₁` path is covered by composition (T13/T4 on the mean array + T2a on
the Beta `V̄₁` assembler) rather than by T2a directly, and note the
residual assumption that the `V̄₁` summation code is prior-agnostic.

---

### F4: §9 Derivations — systematic section/equation numbering collision [severity: low]

**Location**: §9 (Derivations) throughout — equation tags, internal prose
references, and the Revision-log narration.

**Concern**: The Derivations section ships as **§9** (References is §8),
and §1 correctly cross-references it as "§9.1 … §9.5". But everything
*inside* §9 is numbered as if it were §10: the equation tags are
`\tag{10.1.1}`, `\tag{10.2.1}`, `\tag{10.3.1}`, `\tag{10.4.1}`,
`\tag{10.5.1}` (etc.), the in-section prose refers to "(10.1.2)",
"(10.1.3)", "(10.5.2)", and the Revision-log entry for 2026-05-29 narrates
"a new **§10 Derivations** was inserted after §9 References … Revision log
moved §10 → §11" — a layout that does not match the shipped file
(References = §8, Derivations = §9, Revision log = §10). A reader chasing
"the steps are in §9.1" lands in a section whose own equations are all
labelled 10.x, and the §4.4 / §1 pointers to "§10.1–§10.5" (lines ~1697,
1710, 1715, 1719, 1730) point at a section number that does not exist.

**What would resolve it**: Pick one numbering and apply it consistently —
either renumber the section to §10 (and fix the §1 cross-refs that say
"§9.x") or, more simply, renumber the equation tags and internal
references from `10.x.y` to `9.x.y` and correct the Revision-log prose to
describe the actual §8/§9/§10 layout.

---

### F5: Generative-model diagram marks the future bet tosses as "observed" [severity: low]

**Location**: `diagrams/001-infomax-betting-pgm.{py,svg}` and the
§Generative-model prose ("`n` Bernoulli observations plus the bet
outcomes").

**Concern**: The inner plate is labelled `n + k_+` and its single node
`x` is rendered `observed=True`. But the `k_+` post-training tosses are
the **bet target**: the agent bets *before* they are realised and never
conditions on them (they are integrated out analytically, §1.5). Folding
the `n` conditioned-on training tosses and the `k_+` unobserved bet tosses
into one plate under a single shaded/"observed" node conflates two roles
the rest of the spec is careful to separate (e.g. the §1.10 oracle
discussion, and §0's insistence that the agent "observes only `X_{1:n}`").
The prose frames the diagram as nature's model, where every draw is
realised — but even then, "observed" in PGM convention denotes
conditioning, which does not apply to the bet tosses. This mirrors the
spec-000 F12 plate discussion but is more load-bearing here because `k_+`
is a first-class experimental axis.

**What would resolve it**: Either split the inner plate into an
`n`-observed plate and a `k_+` bet-target plate (the latter unshaded), or
keep one plate but add a caption sentence stating that only the `n`
training tosses are conditioned on and the `k_+` tosses are the
integrated-out bet target — making the "observed" shading a
nature-realises-all convention, not an agent-conditions-on-all claim.

---

### F6: Minor wording/units imprecisions [severity: low]

**Location**: §1.1 ("Bits are obtained at report time via `log 2`");
§1.5 ("non-negative **by construction**").

**Concern**: Two small items, neither affecting a result.
(1) §1.1 says bits are obtained "via `log 2`" — the operation is
*division* by `log 2`; "via `log 2`" is ambiguous (could read as
multiplication). Spec 000 §1.2 states it correctly ("dividing by
`log 2`"); align the wording.
(2) §1.5 calls `M_{h,n−h}(q) − M_{h+k₊,n−h}(q) ≥ 0` "non-negative **by
construction** (each term is a probability against a non-negative
integrand)". The conclusion is correct (the difference equals
`E_q[θ^h(1−θ)^{n−h}(1−θ^{k₊})]`, whose integrand is `≥ 0` on `[0,1]` — I
verified this numerically), but "by construction" hand-waves the actual
reason, which is that the *difference* equals a single expectation of a
non-negative integrand, not that "each term is a probability". As written
the parenthetical justifies the wrong thing (two separately-non-negative
terms whose difference need not be non-negative).

**What would resolve it**: (1) change "via `log 2`" to "by dividing by
`log 2`". (2) replace the parenthetical with the actual one-liner: the
difference is `E_q[θ^h(1−θ)^{n−h}(1−θ^{k₊})]` and `1 − θ^{k₊} ≥ 0` on
`[0,1]`, so the integrand is non-negative.

## What the spec gets right

The mathematical core is correct and well cross-referenced, and these
parts should be preserved as-is while the findings above are addressed.
The Kelly identity (1.3.3) uses forward KL `D_KL(Bernoulli(π_true) ‖
Bernoulli(π̂))` with the truth in the first slot, exactly as the tutorial
prescribes; the Part-1 and Part-2 closed forms (1.4.4 / 1.5.2) reproduce
independent Monte-Carlo to within MC error; the binomial data-average and
`q`-average collapses (§9.1–§9.4) are step-for-step valid; the digamma
Beta log-moment identities for the Part-1 oracle (§4.3) are exact; the
method-of-moments Beta inversion (1.8.1 / §9.5) is correct and its
`ν > 0 ⇔ σ² < μ(1−μ)` condition is right; the oracle upper bound (§1.10,
T5) follows pointwise from per-`h` Kelly optimality and survives the
`q`-average; and the reused spec-000 API calls (`blahut_arimoto`,
`cell_centred_grid`, `binomial_log_likelihood`, `GridPrior.masses`) all
match the actual signatures. The log-space numerical-stability treatment
(§1.7, §2.4) and the test suite's separation of correctness checks
(MC references, oracle bounds, analytic limits) from the open headline
question are both well judged.
