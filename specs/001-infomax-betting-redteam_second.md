# Red-team review of 001-infomax-betting

Reviewer: red-team sub-agent
Date: 2026-05-30
Spec version: 8292233 (commit 829223355edd56ad5a4e6b4fdaf6d7bd9cd2e731)

## Summary

The mathematical core of this spec is, on the whole, sound: I checked the
Kelly growth identity (1.3.2)–(1.3.3), the binomial data-average collapse
(§9.1), the q-average moment identification (§9.2), the Part-2 loss-term
moment difference (§9.4), the moment-matched Beta inversion (§9.5), the
oracle digamma log-moment identities (§4.3), and the per-prior posterior
formulas (§1.6), and verified the headline closed forms `V̄₁` (1.4.4) and
`V̄₂` (1.5.2) numerically against independent Monte-Carlo — all match. The
Thorp (2006) Fig. 1 eye-test reference was confirmed against the actual PDF
(`g(f) = p log(1+f) + q log(1−f)`, peak `log 2 − H_B(p)`, zero at `f=0`,
divergence at the edges — exactly as the spec claims). The reused spec-000
machinery (`blahut_arimoto`, `GridPrior`, cell-centred grid, Jeffreys =
`Beta(½,½)`, `p*` discreteness) is cross-referenced correctly. The one
serious problem is a single test (T12) that asserts a *false* exact
identity: it conflates "the agent's prior matches nature's marginal `q`"
with "the agent knows the realized `θ`", and a correct implementation will
fail it by ~0.04–0.14 nats. Beyond that, there is one overstated
test-coverage cross-reference and a few low-severity loose statements and a
diagram annotation issue. With T12 fixed (and the §1.6 coverage claim
corrected), the spec is ready for downstream implementation; the derivations
do not need rework.

## Findings

### F1: T12 asserts a false exact identity — a matched prior is not the oracle [severity: high]

**Location**: §3.3 table P12 (line 911) and §3.4 T12 description (lines
1087–1094); relies on §1.10 (oracle) and §1.4 (`V̄₁`).

**Concern**: T12 claims that for `q = Beta(1,1)` (uniform nature) and the
uniform prior `p_U`, `V̄₁(p_U, n, q) = log 2 − E_q[H_B(θ)]` exactly, to atol
`1e-10`, "because the agent is perfectly matched to nature and must achieve
the oracle bound exactly." This is wrong. The right-hand side is the
*oracle* value (eq. 1.10.1), which is realized only by a bettor who believes
`π̂ = θ` — i.e. who already knows the realized coin bias. The agent using
`p_U` bets `π̂ = μ̂_n(p_U, h) = (1+h)/(n+2)`, the posterior *mean*, which is
a shrunken function of the heads count and is never equal to `θ` for a
continuous `q`. Matching nature's *marginal* `q` removes prior
misspecification but does not remove posterior *uncertainty*; the Bayesian
still pays a strictly positive penalty `E_q D_KL(θ ‖ μ̂_n) > 0` at every
finite `n`.

I evaluated both sides directly from the spec's own formula (1.4.4):

| n | `V̄₁(p_U, n, uniform)` | oracle `log2 − E_q[H_B]` | gap |
|---|---|---|---|
| 1 | 0.056633 | 0.193147 | −0.1365 |
| 2 | 0.087208 | 0.193147 | −0.1059 |
| 5 | 0.129383 | 0.193147 | −0.0638 |
| 10 | 0.154599 | 0.193147 | −0.0385 |

The gap is 7–9 orders of magnitude larger than the asserted `1e-10`
tolerance and only vanishes as `n → ∞` (consistent with §1.10's `n → ∞`
limit claim, which *is* correct). A correct implementation of `V̄₁` will
therefore *fail* T12; the danger is that an implementer "fixes" a correct
`V̄₁` to pass this test, or distrusts it. This is exactly the
belief-vs-truth conflation the spec's own Kelly tutorial flags as red-team
failure mode #1 (`tutorials/math/kelly.md`, lines 255–263). Note T12 is also
billed as "the one point where both are computable in closed form" and as
the exact check that catches a systematic offset a `4·MCSE` tolerance would
absorb — so its incorrectness removes the only claimed *exact*-value guard
on `V̄₁`.

**What would resolve it**: Replace T12 with an exact check that is actually
true. Options: (a) check the matched-belief identity `g̅(π,π) = log2 − H_B(π)`
already covered by T3, extended to confirm `V̄₁`'s `log 2` additive constant;
(b) compute `V̄₁(p_U, n, q)` for a fixed simple `q` two algebraically
independent ways (e.g. the moment-sum form 1.4.4 versus a direct
`Σ_h Binom · g̅` evaluation with closed-form Beta moments) and assert
equality to `1e-12`; (c) keep an oracle comparison but assert the correct
relation `V̄₁ < oracle` with a *non-zero* gap, and check the gap's `n→∞`
decay (which overlaps T6). In all cases delete the false "uniform prior is
the oracle" sentence and the `= log2 − E_q[H_B(θ)]` equality from §3.3/§3.4.

> M: I agree that T12 is wrong. Given T3 and T6, is there any added value that could we salvaged in T12, or should it just be dropped?

> C: Deferred — not edited this pass (you asked a question, so per the
> workflow I bring an opinion back to chat before touching §3.3/§3.4). My
> recommendation (full reasoning in the 2026-05-30 chat reply): T3 and T6
> do *not* cover T12's niche — T3 checks only the `kelly.py` atom
> `g̅(π,π)`, T6 checks only the *relative* `n→∞` trend, and T2a's MC
> tolerance (`4·MCSE`) can absorb a small systematic offset. T12 was the
> only *exact* (machine-precision) pin on the *assembled* `V̄₁` level, so
> I'd repurpose rather than drop it: replace the false "uniform prior is
> the oracle" identity with an exact two-independent-ways check of
> `V̄₁(p_U, n, Beta(1,1))` (eq. (1.4.4) vs. a direct
> `Σ_h Binom·g̅` evaluation with closed-form Beta moments, atol 1e-12).
> Awaiting your stage-3b decision before editing.

---

### F2: §1.6 overstates T2a's coverage — `V̄₁` for the discrete `p*` is never end-to-end MC-tested [severity: medium]

**Location**: §1.6 coverage note (lines 369–378), against §3.3 P2a (line
900) / P2b (line 901).

**Concern**: §1.6 states that the discrete posterior weights (1.6.3) and the
discrete mean/pattern (1.6.4) are "consumed inside `V̄` (for `p*`) by **T2a /
T2b**." But T2a (P2a) is parametrised *only* on `p_J` ("`p_J` on H3, n=5,
K=2") — a Beta prior. T2a never runs `p*`. So the specific end-to-end path
"discrete posterior mean (1.6.4) → moment-weighted `V̄₁` (1.4.4)" for `p*` is
not directly validated against Monte-Carlo anywhere. The cross-reference is
factually incorrect for T2a. (The discrete *mean* is checked against the
Beta mean by T4, and the discrete posterior is checked by T13; and T2b does
exercise the discrete path end-to-end for `p*` in `V̄₂`. So the gap is the
narrow combination {discrete `p*`, Part 1, `V̄₁`}, with adjacent coverage
elsewhere — but the §1.6 claim that T2a covers it is simply false.)

**What would resolve it**: Either (a) add `p*` (and ideally `p_U`) to the
T2a parametrisation so `V̄₁` is MC-validated for the discrete prior, mirroring
T2b's "all four priors" design — this is the clean fix; or (b) if T2a is left
Beta-only, correct §1.6's sentence to state that the discrete `p*` path in
`V̄₁` is covered *indirectly* (T4 for the mean, T13 for the posterior, T2b
for the same discrete machinery inside `V̄₂`), not by T2a.

> M: yes, let's just add all four priors to T2a

> C: Applied (= first-report F3). §3.3 P2a and §3.4 T2a now parametrise
> over all four priors `{p_J, p_U, p_MM, p*}` (H3, n=5, K=2), MC-validating
> the discrete-`p*` `V̄₁` path end-to-end; this makes the §1.6 coverage
> claim accurate (no §1.6 edit needed). `p_MM` is in the test only to
> exercise the Beta branch — §2.5's Part-1 comparison set is still
> `{p*, p_J, p_U}`. §3 flipped to draft; revision-log entry added
> (Correction).

---

### F3: §1.8 precondition "`σ²` strictly inside `(0, ¼)`" is not the existence condition for general mean [severity: low]

**Location**: §1.8 (lines 401–402), eq. (1.8.1).

**Concern**: §1.8 introduces `moment_match_beta` "given a prior `p̃` … with
mean `μ` and variance `σ²` strictly inside `(0, ¼)`." The actual existence
condition for a valid Beta (`ν > 0`) is `σ² < μ(1−μ)`, which the spec states
correctly two paragraphs down (and which `moment_match_beta` enforces, per
§2.2 / T9). For `μ ≠ ½`, `μ(1−μ) < ¼`, so "`σ² ∈ (0, ¼)`" is necessary but
**not sufficient**: e.g. `μ = 0.1, σ² = 0.2` satisfies `σ² < ¼` yet
`σ² > μ(1−μ) = 0.09`, giving `ν < 0`. The framing happens to be harmless in
this spec's *only* use (`p̃ = p*_n` is reflection-symmetric, so `μ = ½` and
`μ(1−μ) = ¼`), but `moment_match_beta(mean, variance)` takes an arbitrary
mean, and the `(0, ¼)` lead-in could mislead a reader into thinking that is
the admissibility region.

**What would resolve it**: Replace "strictly inside `(0, ¼)`" with "with
`0 < σ² < μ(1−μ)`" (and optionally note that for the symmetric `p*_n`,
`μ = ½` so this reduces to `σ² < ¼`).

> M: let's make the suggested replacement

> C: Applied. §1.8's opening precondition "variance `σ²` strictly inside
> `(0, ¼)`" replaced with the actual existence condition
> `0 < σ² < μ(1−μ)`, noting `σ² ∈ (0, ¼)` alone is necessary but not
> sufficient for general `μ`, and that it reduces to `σ² < ¼` for the
> symmetric `p*_n`. §1 flipped to draft; revision-log entry added
> (Correction).

---

### F4: Generative-model diagram marks the `k₊` future bet outcomes as observed [severity: low]

**Location**: Generative model prose (lines 113–120) vs
`diagrams/001-infomax-betting-pgm.py` (lines 33–34, 55–65) and the rendered
SVG.

**Concern**: The inner plate is labelled `n + k₊` and (per the `.py`
docstring, lines 14–15) covers "the `n` observations fed to the agent plus
the `k₊` future tosses the bet is on", and the single `x` node it contains
is `observed=True`. But the `k₊` future tosses are the *bet outcomes* — they
are realized by nature *after* the agent commits its bet and are exactly what
the agent does **not** see when forming `π̂`. Collapsing the `n` observed
training tosses and the `k₊` unobserved bet outcomes into one `observed` node
misrepresents the conditioning structure (the agent conditions on `X_{1:n}`
only; cf. §0, §1.4–§1.5). The prose §generative-model line 118 also says
"`n` Bernoulli observations plus the bet outcomes", which reads as if the
outcomes are observations.

**What would resolve it**: Either split the inner plate into an observed
`n`-plate (`X_{1:n}`) and a separate (unshaded) `k₊`-plate for the bet
outcomes, or drop the `k₊` from the inner plate entirely (the bet outcomes
are integrated out analytically and need not appear), and reword the prose so
"observations" denotes only `X_{1:n}`.

> M: this is always an issue where any kind of action is involved, that observabiliy is not a general property of variables, some are observable before the decision, some after. I wouldn't sweat it in this case, let's just note in the text that the graphical model denotes observability at any point.

> C: Applied (= first-report F5). Added a prose note to the
> Generative-model section that the shaded node denotes observability *at
> some point* in the generative model, not the agent's decision-time
> conditioning set (the `k₊` bet-outcome tosses are observed only after
> the bet and never conditioned on). No diagram change, per your
> instruction. Generative model flipped to draft; revision-log entry
> added (Clarification).

---

### F5: `|ω|` (Hamming weight) is used in eq. (1.6.4) without definition [severity: low]

**Location**: §1.6 eq. (1.6.4), second line (line 360).

**Concern**: The general discrete pattern formula is written
`r̂_n(p*, h, ω) = Σ_a θ_a^{|ω|}(1−θ_a)^{k₊−|ω|} · π'_a(h)`. For this to be the
correct predictive probability of a pattern `ω`, `|ω|` must denote the number
of heads (Hamming weight) of `ω`, and `k₊ − |ω|` the number of tails — but
`|ω|` is never defined in §1.1 or §1.6. Elsewhere `|·|` is not introduced.
Since the headline runs fix `ω = 1^{k₊}` (`|ω| = k₊`), this never bites in
practice, but the general formula (kept in the spec for the DC-2 extension)
is ambiguous as written.

**What would resolve it**: Add "where `|ω|` is the number of 1s (heads) in
the pattern `ω`" to the §1.1 symbol table or inline at (1.6.4).

> M: ok add the clarification

> C: Applied. Defined `|ω|` inline at eq. (1.6.4): the Hamming weight —
> the number of 1s (heads) in `ω`, so `k₊ − |ω|` is the number of 0s
> (tails); for the all-heads headline pattern `|ω| = k₊`. §1 flipped to
> draft; revision-log entry added (Clarification).

## What the spec gets right

The derivations are the strong part and should not be disturbed when fixing
the findings above. The Kelly growth identity (1.3.3) has the correct sign
and the correct *forward* KL direction (truth ‖ belief); the binomial
collapse (§9.1), the `q`-average moment substitution (§9.2, §9.4), and the
moment-matched Beta inversion (§9.5) are algebraically correct; the closed
forms `V̄₁` (1.4.4) and `V̄₂` (1.5.2) reproduce independent Monte-Carlo to
within sampling error for all cases I tried, including the error-prone Part-2
loss-term cancellation `M_{h,n−h} − M_{h+k₊,n−h}`. The §4.3 digamma Beta
log-moment identities are exact to machine precision. The oracle upper bound
(T5), the `n→∞` oracle limit (T6), and the reflection symmetry (T7) all
follow from the math as written, and the oracle is correctly characterized as
an unachievable diagnostic ceiling (§1.10), not an agent strategy. The Thorp
(2006) Fig. 1 eye-test reference is accurate. The moment notation `M_{r,s}`
and its `(r,s)` index conventions are used consistently across §1.4, §1.5,
§2.4, and §9, and the `k_n → h_n` rename is propagated cleanly.
