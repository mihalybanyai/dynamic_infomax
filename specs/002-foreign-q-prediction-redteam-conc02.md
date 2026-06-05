# Conceptual red-team review of spec 002 — Foreign-q prediction (held-out predictive log-loss in ribbon geometry)

Reviewer: red-team sub-agent
Reviewer model (declared identity): Claude Opus 4.8
Effort tier: Max (human-set; not machine-verified)
Roster verified: 2026-06-04
Date: 2026-06-04
Spec version: 8e534de (template said `3c4a6d6`; `git rev-parse --short HEAD` returns **8e534de** — the template hash is stale, confirm which is intended)

## Summary

The spec is in good shape and visibly battle-hardened: the conc01 round already caught the
big conceptual traps (the `q̄`-vs-pullback minimiser confusion, the `b→D(m_q‖m_{p_J})`
non-sequitur, the negative-control `p*≠p_U` error, the A&M sign slip, the calibration-term
framing), and the surviving §0–3 math I could check is correct — the compensation identity
(9.1.1), the rearrangement (3.2.1), the Gaussian KL split (9.4.1), the prequential chain-rule
decomposition, the `m_{𝔼_c[q]} = 𝔼_c[m_q]` linearity behind §2.3, and the negative-control
`p_J = p_U` claim all hold as written. The author is admirably explicit about what is *proven*
versus *asserted* (the `O(1)` half of the asymmetry is repeatedly flagged as experiment-deferred).
The work is thinnest at one seam the prior round did not close: the symbol `p*` (and the capacity
`C`) is **defined single-shot at nominal `σ` in §1.1** but **used as the `N`-fold capacity
achiever in §3.1**, where the spec's sole real guarantee lives — as literally defined, the
guarantee (3.1.1) does not follow, and the bridge (sufficiency: `N` i.i.d. obs ≡ one obs at
`σ/√N`) is never stated where it is needed. There is also a figure-vs-text contradiction the F1
fix introduced (the geometry panel (c) still says "every prior ties," which §2.4 now explicitly
denies). Both are fixable with localized edits; neither sinks the design. With the `p*`/`C`
budget-channel definition reconciled and the figure corrected, §0–3 are ready for downstream
work. The remaining items are smaller over-claims and attribution slips.

## Findings

### F1: `p*` and capacity `C` are defined single-shot in §1.1 but used as the `N`-fold capacity achiever in the §3.1 guarantee [severity: medium]

**Location**: §1.1 (table rows `p*`, `I(Θ;X)`, `C`); §3.1 eq. (3.1.1) and surrounding; cross-tension with §2.1 table row 2 and §3.4 ("`p*`'s σ-dependence is the atom count ~√N").

**Concern**: §1.1 defines `p* = argmax_π I(Θ;X)` with `I(Θ;X) = 𝔼_π D_KL(p(x|θ)‖m_π)` — a
**single observation** `x ∼ 𝒩(y(θ),σ²I)` at the nominal noise `σ` — and `C = sup_π I(Θ;X)`
likewise single-shot. §4.2 then builds `p*` by BA on the single-`x` functional `f_KL(θ) =
D(p(x|θ)‖m_π)`, again at nominal `σ`, with no mention of `N`. But the spec's *one real
guarantee*, eq. (3.1.1), is the **`N`-fold** statement
`R_N^q(p*) = 𝔼_q D_KL(p(X_{1:N}|θ)‖m_{p*}) ≤ max_θ D_KL(p(X_{1:N}|θ)‖m_{p*}) = C_N`. The final
equality (the equalizer bound `D(p(X_{1:N}|θ)‖m_{p*}) ≤ C_N` for *every* `θ`) holds **only if
`p*` is the capacity-achieving prior of the `N`-fold channel** `θ → X_{1:N}`. The single-shot
`argmax_π I` of §1.1 is *not* in general the `N`-fold capacity achiever (the atom count grows
like `√N`, per §3.4 itself), so as the symbols are literally defined, (3.1.1) does not follow.
The intended fix is clearly the sufficiency bridge stated for `σ` in §1.1 (line 91: `N` i.i.d.
obs ≡ one obs at `σ/√N`) — under it, `p*` built at the *effective* noise `σ/√N` is the `N`-fold
achiever and the bound holds — but this bridge is never invoked where (3.1.1) lives, and §1.1 /
§4.2 pin `p*` at the *nominal* `σ`, so the spec is internally inconsistent about whether `p*` is
single-shot or budget-`N`. The same slip sits under §2.1's table row 2 (`argmin_π R_N^{max} =
p*` "by duality" — true for the `N`-fold achiever, not automatically for the single-shot one).
Conc01's F5 sharpened the *attribution* of `C_N` but left the *definition of the prior `p*`*
single-shot.

**What would resolve it**: State once (in §1.1 or at the head of §3.1) that `p*` denotes the
capacity-achieving prior of the **budget-`N` channel** — equivalently the single-observation
achiever at effective noise `σ/√N` — and that `C ≡ C_N` is that channel's capacity; then invoke
sufficiency (`D(p(X_{1:N}|θ)‖m_{p*}) = D(p(x̄|θ)‖m_{p*})`, `x̄ ∼ 𝒩(y(θ),σ²/N)`) at (3.1.1) so the
equalizer applies to the object actually being bounded. Make §4.2 build `p*` at the same
effective noise (or say explicitly that `σ` there *is* the effective budget noise).

> M: this issue was corrected in another red team pass (conc03, F1)

> C: Confirmed — no action needed. §1.1 was redefined to `p* = argmax_π I(Θ;X_{1:N})` (budget-`N` capacity prior, `C ≡ C_N`) in the conc03 F1 round (2026-06-05), with the single-observation `I(Θ;X_1)` kept distinct for `b_π(θ)`. This finding is already resolved.

---

### F2: Geometry figure panel (c) ("every prior ties") contradicts the post-F1 §2.4 text [severity: medium]

**Location**: `diagrams/002-foreign-q-prediction-geometry.svg`, panel (c) label "every prior
ties (control T2, §2.4)"; embedded in §1.2 ("The model geometry"); contradicts §2.4 first
bullet (lines ~484–494).

**Concern**: Conc01's F1 fix rewrote the negative control so that the hard screen is now only
`p_J = p_U ⇒ R(p_J) = R(p_U)`, and §2.4 states in bold that **`p*` is *not* expected to tie**
on the flat model ("a `p*` 'win' on the flat model is **not** by itself an artefact … `p*` can
genuinely beat the uniform priors at the non-cooperative end" by a bounded-channel edge effect).
The geometry figure embedded in §1.2 was not updated: panel (c) still asserts "**every prior
ties**." A reader who meets the negative control first in the figure (which is the stated purpose
of putting the geometry block before the conceptual red-team) will absorb the exact claim conc01
corrected as false. Because the negative control is load-bearing for the falsification structure,
the figure actively misleads about what T2 screens.

**What would resolve it**: Regenerate the figure with panel (c) relabelled to match §2.4 — e.g.
"`p_J = p_U` here (hard screen T2); `p*` may still win by an edge effect (diagnostic, §6)" — or
at minimum drop the universal "every prior ties." Re-run
`diagrams/002-foreign-q-prediction-geometry.py`.

> M: section 2.4 has been rewritten in another red team pass (conc03, F7), so we should just drop that text from the figure

> C: Applied (conc02 pass). Dropped "every prior ties (control T2, §2.4)" from panel (c) of `diagrams/002-foreign-q-prediction-geometry.svg`; SVG regenerated via `uv run`, docstring updated. **One thing to flag:** the same panel also still asserted `b(θ) ≡ 0` — the exact claim conc01 removed from the prose but left in the figure — so while regenerating I corrected it to the true consequence `p_J = p_U`; the panel now reads "pipeline check T2 (`p*` need not tie)", matching the conc03-F7 §2.4 rewrite. You only asked to drop the "every prior ties" text, so say if you'd rather I leave the second label blank than carry the corrected note. Revision-log entry added (Correction).

---

### F3: §0 presents the `O(d)`-vs-`O(1)` asymmetry as established fact / "derived," but §3.2 flags the `O(1)` half as merely asserted [severity: medium]

**Location**: §0 lines 55–58 ("`p*` … pays … a penalty that does *not* grow with dimension") and
line 65–66 ("The quantitative form of the asymmetry (`O(d)` competitor bias vs `O(1)` for `p*`)
is **derived** in §3.2"); against §3.2 lines 563–564.

**Concern**: §3.2 is explicit that only the *competitor* half is argued: `D(m_q‖m_{p_J}) = Ω(d)`
follows (given the named `𝔼_q b_{p_J} = Ω(d)` hypothesis) from (3.2.1), but
"`D(m_q‖m_{p*})` is *expected* to stay `O(1)` — **asserted, not shown, and left to the
experiment**." §0 states the `p*` side as a flat fact ("a penalty that does *not* grow with
dimension") and calls the whole asymmetry "**derived** in §3.2." Neither is accurate: the `O(1)`
`p*` side is unproven by the spec's own account, and what §3.2 *derives* is one inequality
(the competitor's mismatch growth) plus a pointwise hypercone deviation `Δ = (d−1)/x` — not the
`O(1)` cap on `p*`'s marginal mismatch that the contest (2.1.3) actually turns on. §0 thus
over-states the epistemic status of the central claim of the spec, exactly the kind of
"unstated headline" the spec elsewhere (line 60–66) congratulates itself on avoiding.

**What would resolve it**: In §0, downgrade "a penalty that does *not* grow with dimension" to
the expectation it is (e.g. "a penalty *expected* to stay bounded in dimension, which the
experiment tests"), and change "is **derived** in §3.2" to "is *argued* (competitor side) and
*conjectured* (`p*` side) in §3.2," matching §3.2's own hedging.

> M: this section has been rewritten in another red team pass (conc03, F2). Do you think this problem still exists?

---

### F4: §3.3 calls the bias term "exactly A&M's quantity, up to weighting," but it also differs in reference point (truth vs MLE) [severity: low]

**Location**: §3.3 ("The **bias term** is a precision-weighted `Δ²` — *exactly A&M's quantity*,
up to weighting"); §9.4 (same phrasing); reconciled only later in §4 (lines 735–739).

**Concern**: A&M's `Δ` (Eq. 9, verified in `resources/abbott_machta.pdf` p. 6) is
`(1/σ)|y(θ̂_x) − ⟨y(θ)⟩_x|` — posterior mean of `y` minus the **MLE** `y(θ̂_x)`. The §9.4 bias
term is `(μ_π − y(θ))^⊤ Σ_π^{-1}(μ_π − y(θ))` with `μ_π = ⟨y⟩` and reference `y(θ_true)`. These
differ in **two** ways, not one: (i) the precision weighting `Σ_π^{-1}` vs A&M's `(1/σ²)I`, and
(ii) the reference point — **truth** `y(θ_true)` here vs **MLE** `y(θ̂_x)` in A&M. §4 (lines
735–739) correctly notes the reference-point change ("A&M's `Δ` uses the in-sample MLE; the
held-out bias term uses `y(θ_true)`"), so the spec knows about (ii) — but §3.3/§9.4, the places
that make the "exactly A&M's quantity, up to weighting" claim, mention only the weighting. For
held-out data with `θ̂_{x'} ≈` projection of `x'`, the MLE and the truth differ by `O(σ)`, so
the two "bias terms" are not equal even up to weighting. The claim that the proper score
"*contains* A&M's `Δ`" is therefore slightly too strong as stated locally.

**What would resolve it**: In §3.3/§9.4, change "up to weighting" to "up to weighting **and the
reference point (truth vs in-sample MLE; see §4)**," or soften "exactly A&M's quantity" to "the
held-out analogue of A&M's `Δ`." A one-clause cross-reference to the §4 caveat suffices.

> M: first of all, 9.4 is unnecessary, let's have that one equation and the rest of the info all there in 3.3 and delete 9.4. Otherwise this is a bit hard to evaluate for me, but seems vaguely correct?

> C: Merge applied (conc02 pass): the Gaussian KL is now inline in §3.3 as **eq. (3.3.1)** and **§9.4 is deleted**; all references updated (`(9.4.1)→(3.3.1)` in §4 ×2, P5, T5; the dead §9.4 link dropped). The finding's *other* half — whether "exactly A&M's quantity, up to weighting" should also flag the reference-point difference (held-out **truth** `y(θ_true)` vs A&M's in-sample **MLE** `y(θ̂_x)`) — I'm bringing back to you in chat (you flagged it "seems vaguely correct?"), so §3.3's wording on that point is unchanged for now. Revision-log entry added (Clarification).

> C: (follow-up) Confirmed correct and applied. §3.3 now reads "the **held-out analogue** of A&M's quantity, up to the precision weighting *and* the reference point (truth `y(θ_true)` here vs A&M's in-sample MLE `y(θ̂_x)`, differing by `O(σ)`; see §4)", and "*contains* the held-out analogue of A&M's `Δ`". Second revision-log entry added (Clarification).

---

### F5: §3.1 supports a property of the `N`-fold capacity `C_N` by citing A&M Fig. 5, which plots the single-`σ` `I⋆` [severity: low]

**Location**: §3.1 lines 528–531 ("`C_N` — the capacity of the `N`-fold channel, **distinct
from** A&M's single-`σ` mutual information `I⋆` — … roughly flat in *nominal* `d` once `d>3`
(**A&M Fig. 5**)").

**Concern**: The sentence asserts `C_N ≠ I⋆` and, in the same clause, cites A&M Fig. 5 for
`C_N`'s flatness in nominal `d`. But Fig. 5 (verified, `resources/abbott_machta.pdf` pp. 6–7)
plots `I(X;Θ)` under `p*` at the single fixed `σ = 0.1` — i.e. `I⋆`, the very object the sentence
says `C_N` is distinct from. The flatness of `C_N` in nominal `d` is genuinely *inherited* from
the saturation of `d_eff` (and hence of `I⋆`), so the conclusion is defensible, but the citation
is to the wrong object: a figure about `I⋆` is offered as direct evidence for a property of a
quantity declared different from `I⋆`, with the inheritance step unstated. This is a residue of
the conc01 F5 split-attribution that did not fully land.

**What would resolve it**: Add the missing half-sentence — e.g. "`C_N` is flat in nominal `d`
because both `C_N` and `I⋆` are governed by the saturating resolvable dimension `d_eff` (A&M
Fig. 5 shows the saturation for `I⋆`)" — so Fig. 5 supports `I⋆`'s saturation and the text, not
the figure, carries `C_N`'s inheritance of it.

> M: seems correct. Agree?

> C: Agree, applied (conc02 pass). The conclusion (`C_N` flat in nominal `d`) holds, but Fig. 5 plots the single-`σ` `I⋆`, not `C_N`. Added the inheritance step in §3.1: both `C_N` and `I⋆` are governed by the saturating `d_eff`, whose saturation Fig. 5 shows *for `I⋆`* — so the figure now supports `I⋆` and the text carries `C_N`'s inheritance. Revision-log entry added (Clarification).

---

### F6: "No fixed non-infomax prior has this [capacity cap]" is shown only for `p_J`, asserted for `p_U`/`p_LN` [severity: low]

**Location**: §3.1 lines 524–528 ("So `p*`'s foreign-`q` redundancy is capped at capacity … No
fixed non-infomax prior has this: by A&M's own score a prior's worst-case redundancy is
`I_π + B(π)` … and `B(p_J)` *grows with dimension*").

**Concern**: The universal claim ("**No** fixed non-infomax prior has [a `d`-controlled
worst-case ceiling]") is justified only via `B(p_J) = O(d)` (A&M's Jeffreys result). The
identity `max_θ D = I_π + B(π)` is correct for any `π`, but the spec gives the `O(d)` growth
only for `p_J`. For `p_U` and `p_LN` it is asserted, not shown; A&M show `p_LN` "also suffers a
decline … with increasing `d`" empirically (p. 7) but do not establish an `Ω(d)` worst-case
redundancy for it, and `p_U` on a compact box has a finite worst case whose `d`-growth the spec
does not argue. The headline statistic (§2.2) is the gap to the **best** deployable competitor,
so whether *every* deployable prior has an `O(d)` worst case matters for the "no fixed prior has
this" rhetoric.

**What would resolve it**: Restrict the claim to "the deployable priors A&M study (Jeffreys, and
empirically log-normal) show worst-case redundancy growing with `d`," or add a one-line argument
/ citation that `p_U` and `p_LN` inherit the same co-volume growth on the hyperribbon.

> M: seems ok to make this change

> C: Applied (conc02 pass). §3.1's "No fixed non-infomax prior has this" → "The deployable priors lack it (shown for Jeffreys, and empirically for log-normal — A&M p. 7; `p_U`/`p_LN` taken to inherit the same co-volume growth on the hyperribbon, not separately proven)". Revision-log entry added (Clarification).

---

### F7: "the atom spacing *is* the resolution" is imprecise given the spec's own `≈2` Fisher-length spacing [severity: low]

**Location**: §3.2 lines 568–570 ("along a **relevant** direction the atom spacing *is* the
resolution, so the error is no worse than rounding `θ` to its resolved precision"); against §1.2
line 253 and the revision log (BA-verified interior spacing `~2.5`, not 1).

**Concern**: The spec elsewhere (and `notes/infomax_two_hats_and_directions.md` §7.4, per the
revision log) establishes that `p*`'s interior atoms sit `≈2`–`2.5` Fisher lengths apart, *not*
at the unit resolution. "The atom spacing *is* the resolution" therefore conflates two scales
that differ by a factor `~2`. The `O(1)` conclusion (bounded discretisation penalty) is
unaffected — rounding to atoms an `O(1)` spacing apart still gives `O(1)` bias — but the equality
"spacing = resolution" is the same loose phrasing the revision log flagged ("`≈1` Fisher length
apart" was corrected to `O(1)` elsewhere) and missed here.

**What would resolve it**: Replace "the atom spacing *is* the resolution" with "the atom spacing
is `O(1)` resolutions," consistent with the `≈2` correction applied in §1.2 and §3.3.

> M: correct, apply

> C: Applied (conc02 pass). §3.2 "the atom spacing *is* the resolution" → "the atom spacing **is `O(1)` resolutions**", consistent with the BA-verified `≈2` interior spacing corrected elsewhere (§1.2/§3.3). The `O(1)` discretisation conclusion is unchanged. Revision-log entry added (Clarification).

## What the spec gets right

The core machinery is sound and should be preserved. The three-redundancy disambiguation in §2.1
(self-consistent MI / worst-case minimax / foreign-`q` average) is the right way to dissolve the
"why would a max-MI object minimise a loss" worry, and the compensation-identity decomposition
(2.1.2)/(9.1.1) reducing all prior-dependence to `D(m_q‖m_π)` is correct and is the spec's best
idea. The §2.3 `q̄`-ceiling argument is right (and rests on the genuine linearity
`m_{𝔼_c[q]} = 𝔼_c[m_q]`), the negative-control `p_J = p_U` identity under constant `√det g` is
correct, the prequential chain-rule rewrite of `R_N` is correct, the Gaussian bias/calibration
split (9.4.1) is algebraically right, and the §9.2 handling of A&M's sign slip (taking the
magnitude, relabelling mode vs mean, widening the tolerance at the marginal expansion point) is
careful and correct against the source. The honesty about asserted-vs-proven (the `O(1)` `p*`
side, the `𝔼_q b = Ω(d)` hypothesis named as the sole `q`-dependent assumption) is exactly what a
spec at this stage should do — the F3 fix is about importing that honesty back into §0, not about
changing the argument. Do not let the F1 reconciliation of `p*`/`C` disturb the (correct)
single-observation definitions used for `b(θ)` and the §3.2 `N=1` identity (3.2.1), which
legitimately live at `N=1`.
