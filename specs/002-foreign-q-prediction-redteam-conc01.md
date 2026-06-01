# Conceptual red-team review of 002-foreign-q-prediction

Reviewer: red-team sub-agent
Date: 2026-06-01
Spec version: ef253d9 + uncommitted working-tree changes (reviewing on-disk version)

## Summary

The spec is conceptually careful in the places it most needs to be: it does not
assert the headline sign, it correctly identifies that the only prior-dependent term
in the score is the data-marginal mismatch `D(m_q‖m_π)` (the compensation identity in
§9.1 is correct, verified), the Gaussian KL split in §9.4 is algebraically right
(verified numerically), the hypercone deviation magnitude `(d−1)/x` in §9.2 is right
(verified), and the three-redundancy disambiguation in §2.1 is the correct way to
defuse the "max vs min" worry. The author also draws the `p*`/`p_proj`/Jeffreys
budget-dependence picture accurately against both in-repo tutorials and the source
papers. The work is thinnest at two load-bearing joints. First, the **negative
control** (§2.4 / T2) — the spec's primary falsification screen — rests on a claim
that is false under the spec's own machinery: "flat co-volume ⇒ `p*`=`p_J`=`p_U`"
ignores that the *bounded* relevant coordinate carries a Smith-type boundary
discreteness, so the capacity prior is not uniform even with constant `√det g`. That
makes the control unable to do its stated job and is the most serious issue. Second,
several statements about *which* object minimises the score, and about *how* the
bias mechanism transfers to the data-marginal KL, are stated more tightly than they
are true (the per-`q` minimiser is the pullback, not `q̄`; the `b(θ)→D(m_q‖m_π)`
bridge is asserted, not derived). These are fixable with scope/wording changes but
should be fixed before any code is written, because T2 and the §3.2 heuristic are
exactly what the experiment is built around. Recommend substantive revision of §2.4
and tightening of §2.1/§3.2 before the sections go to `reviewed`.

## Findings

### F1: The negative control's "flat co-volume ⇒ everyone ties" is false — `p*` ≠ `p_U` on a bounded flat channel [severity: high]

**Location**: §2.4 (Negative control bullet); propagated to §4.1.3, §5 P2/T2.

**Concern**: §2.4 asserts that in the constant-cross-section cone "`√det g` is
constant, `b(θ)≡0` ... `R_N^q(p*) = R_N^q(p_J) = R_N^q(p_U)` within Monte-Carlo
error, at every `d`", and makes this the falsification screen: "If `p*` 'wins' here,
the result is an artefact." The step `√det g` constant ⇒ `b(θ)≡0` is wrong. `b(θ)≡0`
for the uniform prior requires the *full* equalizer `D(p(·|θ)‖m_{p_U}) = C` constant
over `θ`, i.e. a **homogeneous** channel with no special points. But the relevant
coordinate is a *bounded* interval `θ_1∈[0,L]` with Gaussian likelihood, and a
bounded flat Gaussian-mean channel is precisely the inhomogeneous,
constraint-bounded case whose capacity-achieving prior is **discrete**, not uniform
(Smith 1971 — cited approvingly in `tutorials/math/redundancy-capacity.md`:
"inhomogeneity + a constraint ⇒ discrete even with continuous output"). The
boundaries at `0` and `L` break homogeneity exactly as the `{0,1}` endpoints do for
the Bernoulli channel in that same tutorial.

I verified this numerically for a 1-D bounded Gaussian channel `θ∈[0,L]`,
`x∼𝒩(θ,σ²)`, `L=5`, `σ=1`: the per-`θ` redundancy `r(θ)=D(p(·|θ)‖m_{p_U})` is **not**
flat — it is `≈0.28` nats in the interior and rises to `≈1.19` nats at each boundary
(an excess of `≈0.9` nats). So `b_{p_U}(θ)≢0`, uniform is not capacity-achieving,
`m_{p*}≠m_{p_U}`, and the three priors will **not** tie within MC error even with
constant `√det g`. Worse, the discrepancy is concentrated at the boundary, which is
exactly where the non-cooperative `q` (§4.3, "thin end") puts mass — so a discrete
`p*` that places atoms at the boundary (as Smith's theory predicts) will *genuinely
win* on the negative-control model for reasons that have nothing to do with
co-volume. The control therefore cannot distinguish a real co-volume effect from a
generic bounded-channel edge effect: it will either flag a correct `p*` solver as an
artefact, or pass a "win" that is an edge artefact, defeating its stated purpose. The
effect is `d`-independent (it lives on `θ_1`), so it is present "at every `d`", not
only asymptotically.

**What would resolve it**: State the true null condition. Everyone ties only when the
channel is homogeneous on the relevant coordinate — e.g. make `θ_1` periodic
(a circle/torus, the von Mises case the tutorial gives as the continuous-optimum
example), or take `L→∞` / restrict the scored `q` to the deep interior so boundary
redundancy is negligible relative to MCSE, and demonstrate the residual edge excess
is below MCSE in the chosen design. Alternatively, keep the bounded cone but redefine
the control's pass condition to compare against the *capacity* prior of that flat
bounded channel (which is discrete) rather than against uniform, so the screen tests
"no co-volume gradient ⇒ no co-volume advantage" rather than the stronger and false
"⇒ uniform is optimal."

---

### F2: "`R_N^q ≥ 0`, reached only by a predictor matching nature" misstates the floor [severity: medium]

**Location**: §2.1, the "Lower `R` is better" paragraph (line ~166).

**Concern**: The score is defined as `R_N^q(π) = I_q^{(N)} + D(m_q‖m_π)` (eq. 2.1.2),
and §2.3/§9.1 correctly call `I_q^{(N)}` the *matched floor*, which is strictly
positive (it is `𝔼_{θ∼q}D(p(X_{1:N}|θ)‖m_q) ~ (d/2)log N > 0` whenever `q` carries
real uncertainty in `θ`). But the headline definition says "`R_N^q(π) ≥ 0`, reached
only by a predictor matching nature." A predictor matching nature (`m_π=m_q`) sets
`D(m_q‖m_π)=0` and reaches `R_N^q = I_q^{(N)}`, which is **not** `0`. The value `0`
is unreachable in this setting (it needs `I_q=0`, i.e. no latent uncertainty). So the
sentence conflates the trivial bound `R≥0` with the operative floor `R≥I_q^{(N)}>0`,
and the "reached only by a predictor matching nature" clause attaches to the wrong
number. This directly contradicts §2.3 and §9.1 two paragraphs later.

**What would resolve it**: Change to "`R_N^q(π) ≥ I_q^{(N)} ≥ 0`; the floor
`I_q^{(N)}` (not `0`) is reached only by a predictor matching nature's marginal,
`m_π=m_q`." This is what §2.3 already says.

---

### F3: The per-`q` score's minimiser is the pullback of `q`, not `q̄` [severity: medium]

**Location**: §2.1 three-redundancy table, row 3 ("the matched prior `q̄`, **not**
`p*`"); restated in §0 (line ~41, "`p*` is dominated by the matched prior `q̄` *by
theorem* (the compensation identity)").

**Concern**: Row 3 defines the score for a *single* foreign nature as
`R_N^q(π) = 𝔼_{θ∼q} r_θ(π) = I_q^{(N)} + D(m_q‖m_π)` and names its minimiser
"the matched prior `q̄`." By eq. (2.1.2) the minimiser of *this* quantity over priors
is whatever prior makes `m_π = m_q` — the **pullback of that specific `q`** — not
`q̄ = 𝔼_c[q]`. `q̄` minimises only the **`c`-averaged** score `𝔼_c R_N^{q_c}`, as §2.3
states correctly and carefully ("Per cell ... not by `q̄`. Across the `c`-sweep ...
`q̄`"). So the §2.1 table cell and the §0 sentence ("`p*` is dominated by the matched
prior `q̄` by theorem") both attribute to a per-`q` object a property that holds only
for the `c`-average. As written, the central conceptual table and the Context both
mis-identify the score's minimiser, which is exactly the object the reader is being
taught to track.

**What would resolve it**: In row 3 and in §0, replace "`q̄`" with "the prior matched
to `q` (its own pullback)"; add a parenthetical "(across the `c`-sweep, the single
fixed minimiser is `q̄`; see §2.3)" so the table is consistent with §2.3 rather than
contradicting it.

---

### F4: The bias→marginal-mismatch bridge in §3.2 is a non sequitur as written [severity: medium]

**Location**: §3.2, "most of `q`'s mass falls where `b_{p_J}(θ)>0` is large, so
`D(m_q‖m_{p_J})` inflates with `d` while `D(m_q‖m_{p*})` stays `O(1)`."

**Concern**: `b(θ) = D(p(x|θ)‖m_{p_J}) − I_{p_J}` is a property of the agent's
*single-observation* mixture mismatch *at the point `θ`*; `D(m_q‖m_π)` is a KL
between *data marginals* of the whole sample. The spec slides from "`b` is large on
`q`'s support" to "`D(m_q‖m_{p_J})` inflates" as if one implies the other, but it does
not directly. The actual relation is `𝔼_{θ∼q} b(θ) = I_q^{(1)} − I_{p_J} +
D(m_q‖m_{p_J})` (from `𝔼_{θ∼q}D(p(x|θ)‖m_{p_J}) = I_q^{(1)} + D(m_q‖m_{p_J})` and the
definition of `b`). So large `𝔼_q b` bounds `D(m_q‖m_{p_J})` only after subtracting
`I_q^{(1)} − I_{p_J}`, and the claim that the `b`-growth survives that subtraction
(rather than being cancelled) is an **unstated assumption**. The `O(1)` claim for
`D(m_q‖m_{p*})` is likewise asserted, not shown (it is fine to leave it as the open
empirical question per §2.2, but then it should not appear inside a sentence phrased
as a deduction). The paragraph also leans on vague qualifiers — "any `q` whose
predictions are spread over distinguishable outcomes (**the natural notion** of a
nature that explores the resolvable behaviours)" — that hide precisely the condition
under which the bridge holds.

**What would resolve it**: Either (a) write the one-line algebra `𝔼_q b(θ) =
I_q^{(1)} − I_{p_J} + D(m_q‖m_{p_J})` and state the assumption that `I_q^{(1)} −
I_{p_J}` is `o(d)` on the relevant `q`, so the `O(d)` growth of `𝔼_q b` does transfer
to `D(m_q‖m_{p_J})`; or (b) demote the sentence to an explicitly heuristic
expectation ("we *expect*", not "so ... inflates") and name "spread over
distinguishable outcomes" as a precise condition on `q` rather than "the natural
notion."

---

### F5: §3.1 conflates A&M's fixed-`σ` mutual information `I⋆` with the `N`-fold capacity `C_N` and a `log N` rate [severity: medium]

**Location**: §3.1, "`C_N` tracks only the **resolvable** complexity
(`~ (d_eff/2)·log N`, roughly flat in nominal `d` — A&M Fig. 5)."

**Concern**: Three distinct objects are merged. (i) Bound (3.1.1) uses
`C_N = max_θ D(p(X_{1:N}|θ)‖m_{p*})`, the capacity of the `N`-fold channel. (ii) A&M
Fig. 5 plots `I⋆(X;Θ)` and `B = max_θ b(θ)` as a function of **`d`** at a *single
fixed* noise `σ`/data — there is no `N`-axis and no `log N` scaling in Fig. 5 at all.
(iii) The `(d_eff/2)·log N` rate is the Clarke–Barron/Rissanen *budget* term, a
statement about the `N`→∞ asymptotics, not what Fig. 5 shows. So citing "A&M Fig. 5"
for "`C_N ~ (d_eff/2)·log N`" attaches an `N`-scaling claim to a figure that holds
`N` fixed. What Fig. 5 *does* support is the weaker and correct claim that `I⋆` is
roughly flat in *nominal* `d` once `d>3`; the `log N` rate needs Clarke–Barron, which
the spec cites elsewhere (§3.4) but not here. The numerical anchor ">500 bits at
`d=26`" is from A&M's **exp-decay** model (their §3.3), not the hypercone (whose `B`
is `≈55` bits) — fine since exp-decay is the primary model, but worth pinning.

**What would resolve it**: Split the citation: attribute "roughly flat in nominal `d`"
to A&M Fig. 5, and "`~(d_eff/2)·log N`" to Clarke–Barron 1990 / Rissanen 1996 (already
in §8). State that `C_N` is the `N`-fold capacity, distinct from A&M's single-`σ`
`I⋆`, and note the `>500` bits figure is the exp-decay model.

---

### F6: §9.2 conflates mode with mean, the leading term is loose, and the A&M sign is silently reconciled [severity: low]

**Location**: §9.2 (eqs. 9.2.1–9.2.2); cited by §3.2, §5 T6.

**Concern**: (a) Eq. (9.2.1) finds the stationary point of the log-posterior, i.e. the
**mode** `θ_1 ≈ x + (d−1)/x`, but (9.2.2) reports it as the **mean**
`⟨θ_1⟩_{p_J(θ_1|x)}`. For a skewed posterior these differ; numerically (`x=10`,
`L=50`) the mean−`x` is `+0.48, +0.92, +2.08` for `d=6,11,26` while `(d−1)/x =
0.5, 1.0, 2.5` — so the `(d−1)/x` leading term is already off by `~17%` at `d=26`,
i.e. the `O(x^{-3})` remainder is not negligible at the `(d,x)` the spec proposes to
test (T6 uses `d=26, x≈10`). (b) The spec writes `Δ = |⟨θ_1⟩ − x|` with the posterior
mean **above** `x` (toward the thick end), which is what the algebra gives and is
correct; but A&M Appendix A.1 publishes `Δ = x − ⟨θ_1⟩ = (d−1)/x`, i.e. mean **below**
`x`. The magnitudes agree and the spec's absolute value hides the sign clash, but the
two cannot both be the signed deviation — A&M's signed formula appears to have a sign
slip, and the spec should note that it takes the magnitude rather than silently
inheriting A&M's sign.

**What would resolve it**: Say "mode (= mean to leading order)" and add the
mean-vs-mode caveat; widen the T6 tolerance or move the test to larger `x` where
`(d−1)/x` is actually leading-order; and add a one-line footnote that the spec reports
`|⟨θ_1⟩−x|` and that A&M's signed `x−⟨θ_1⟩` has the opposite sign.

---

### F7: §3.3 mislabels the Bayes predictive's uncertainty as "miscalibration" the proper score "charges" [severity: low]

**Location**: §3.3 ("every Bayes predictive is *over-dispersed* ... a proper score
charges that miscalibration"); §9.4 calibration term.

**Concern**: `Σ_π = σ²I + Cov_π[y(θ)|X_{1:N}] ⪰ σ²I` is correct, but calling the
resulting positive calibration term a "miscalibration" the score "charges" is a
conceptual slip. The Bayes posterior-predictive is **correctly** propagating residual
uncertainty about `θ`; it is not miscalibrated against the data marginal it predicts.
The positive KL `D(𝒩(y(θ),σ²I)‖𝒩(μ_π,Σ_π))` is *oracle-relative* excess loss (the
oracle knows `θ` and pays `σ²I` spread), which is the redundancy the spec is measuring
— not evidence of a calibration defect in `m_π`. Framing the term as the score
"charging miscalibration" risks reading a correct predictive as doing something wrong.
Separately, "calibration is `O(σ²)`" labels a *dimensionless* (nat-valued) KL term
with a `σ²` order; what is meant is that `Cov_π[y|X] = O(σ²)`, making the calibration
term `O(1)` in `Cov/σ²` units — the wording should be tightened.

**What would resolve it**: Reword to "the calibration term is the oracle-relative cost
of the predictive's residual posterior spread — invisible to the centre-only `Δ`,
charged by a proper score." Replace "`O(σ²)`" with "`Cov_π[y|X]=O(σ²)`, so the
calibration term is bounded independent of `d`."

---

### F8: Vague-word and minor-notation flags [severity: low]

**Location**: §1.1 (`p_LN` row); §2.1; §3.2; §3.4.

**Concern**: (a) §1.1 calls `p_LN` "Log-normal in `θ`", but a Gaussian density in `θ`
is log-normal in the *rate* `k_μ=e^{−θ_μ}`, not in `θ`; A&M's own Eq. 10 text says
"log-normal in each decay rate `k_μ`, that is, normal in terms of `θ`." The label
should read "normal in `θ` (log-normal in `k`)". (Also note A&M write `k_μ=e^{θμ}` in
the log-normal passage vs `k_μ=e^{−θμ}` in Eq. 6; the spec uses `e^{−θμ}` throughout
— internally consistent, but a reader cross-checking A&M will hit the discrepancy.)
(b) Several load-bearing steps lean on the flagged hedge-words the brief asks to
surface: "the **natural** notion of a nature that explores the resolvable behaviours"
(§3.2), "resolution-adaptation is essentially **unique**" (§3.4), "**clearly** has
much more weight" (inherited from A&M in §9.2 context), "the **obvious** objection"
(§3.2). Each marks a place where a condition is asserted rather than stated. The §3.4
"essentially unique" in particular is the crux of the `p*`≈`p_proj` claim and deserves
the explicit qualifier the `nml-mdl.md` tutorial gives ("in hyperribbon geometry").

**What would resolve it**: Fix the `p_LN` label; for each hedge-word, either name the
precise condition or mark the statement explicitly as a heuristic expectation.

## What the spec gets right

The mathematical spine is sound and should be preserved while addressing the above.
The compensation identity (§9.1) and its consequence that the only prior-dependent
term is `D(m_q‖m_π)` (eq. 2.1.2) are correct and cleanly derived; the Gaussian
bias/calibration split (eq. 9.4.1) checks out numerically to machine precision; the
hypercone deviation *magnitude* `(d−1)/x` (§9.2) is right; the prequential
chain-rule form of `R_N` (§2.1) is the correct held-out reading; the three-redundancy
table correctly resolves the "infomax maximises, we minimise" worry by separating the
three objects and noting the row-1/row-2 saddle. The `p*`/`p_proj`/Jeffreys
budget-dependence framing (§3.4) matches both in-repo tutorials and the source papers,
the worst-case ceiling `R_N^q(p*) ≤ C_N` (3.1.1) is a genuine and correctly-stated
guarantee, and the §2.2/§3.5/§3.6 refusal to assert the headline sign — together with
the `p_proj`-in-the-lineup requirement for clean attribution — is exactly the right
epistemic posture. Fixing F1–F4 should not require touching any of this.
