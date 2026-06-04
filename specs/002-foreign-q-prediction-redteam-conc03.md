# Conceptual red-team review of spec 002 — Foreign-q prediction (held-out predictive log-loss in ribbon geometry)

Reviewer: red-team sub-agent
Reviewer model (declared identity): Claude Opus 4.7
Effort tier: Max (human-set; not machine-verified)
Roster verified: 2026-06-04
Date: 2026-06-04
Spec version: 8f89b25

## Summary

The spec is well-structured and the §0–§3 narrative is clearly written; the central
construction (compensation identity → `D(m_q‖m_π)` is the only prior-dependent term)
is correct and load-bearing, and the falsification structure (§2.4, §3.6) is honest
about what cannot be asserted. The geometry block in §1.2 is unusually clean. Where
the spec is thinnest is in the single guarantee that licenses the case for transfer
(§3.1): the bound `R_N^q(p*) ≤ C_N` quietly switches between two distinct objects —
the single-observation capacity prior defined in §1.1 and the N-fold capacity, with
no proof that either implies the other. The §3.2 "average-case asymmetry" then leans
on (i) a non-rigorous step that drops a subtraction (`I_q^{(1)} − I_{p_J} = o(d)`)
under an unstated `d_eff = O(1)` assumption, and (ii) an appeal to Quinn's
"truth-between-atoms" replies that are arguments about posterior accuracy under
self-sampling, not bounds on the foreign-`q` marginal mismatch `D(m_q‖m_{p*})` the
score actually depends on. §3.4's "infomax vs MDL" framing also conflates a
*code* (NML, on data) with a *prior* (`p_proj`, the MLE pushforward), which lets the
"siblings" rhetoric carry more weight than the underlying mathematics. None of these
sinks the experiment — they would shrink to caveats with the right hedging — but as
written they would not survive a tough review. Section 0 and §2 are mostly fine
modulo F8/F9.

## Findings

### F1: §3.1 capacity bound mixes single-observation `p*` with N-fold capacity `C_N` [severity: high]

**Location**: §3.1, eq. (3.1.1); definition of `p*` in §1.1.

**Concern**: §1.1 defines `p* = argmax_π I(Θ;X)` where `X` is a *single*
observation (consistent with the equalizer / Bernoulli-channel treatment in
`tutorials/math/redundancy-capacity.md` and A&M's procedure, which optimises
mutual information for the channel at one noise scale `σ`). The single-observation
equalizer then gives `D(p(x|θ)‖m_{p*}(x)) ≤ C` for every `θ`, equality on
`supp(p*)`. But (3.1.1) writes the *N-fold* version
`R_N^q(p*) = 𝔼_q D(p(X_{1:N}|θ)‖m_{p*}(X_{1:N})) ≤ max_θ D(p(X_{1:N}|θ)‖m_{p*}(X_{1:N})) = C_N`,
where (a) `m_{p*}(X_{1:N}) = ∫ ∏_i p(x_i|θ) p*(dθ)` is *not* the product
`∏_i m_{p*}(x_i)` and (b) `C_N = sup_π I(Θ;X_{1:N})` is the N-fold capacity,
achieved (per `redundancy-capacity.md`'s worked Bernoulli) by a *different* prior
than the single-x `p*` — at `n=1` `p* = ½δ_0+½δ_1` (2 atoms), at `n=2`
`p*_2 = 0.441δ_0 + 0.118δ_{1/2} + 0.441δ_1` (3 atoms). The single-x equalizer
neither implies the N-fold KL is bounded by `C_N` nor that the maximum is attained
at any particular value. The whole §3.1 "one real guarantee" — the load-bearing
half of the case for transfer — therefore does not follow from the cited
equalizer/KL-center argument. The 2026-06-03 conc01-stage-3b log entry already
distinguishes `C_N` from A&M's single-σ `I⋆`, but does not redefine `p*` as the
N-fold capacity prior, leaving the gap open.

**What would resolve it**: either (i) redefine `p*` in §1.1 as the N-fold capacity
prior `p*_N := argmax_π I(Θ;X_{1:N})` for the budget `N` in this spec (and note
that for i.i.d. observations equivalent to single observation at `σ/√N` per A&M
§2.1, so A&M's procedure does compute the right object); or (ii) replace `C_N` in
(3.1.1) with the explicit bound that *does* follow from the single-x equalizer,
e.g. `D(p(X_{1:N}|θ)‖∏_i m_{p*}(x_i)) ≤ N·C` for `θ ∈ supp(p*)` (product mixture,
not Bayes mixture), and explain why that bound still licenses the "capacity
ceiling" rhetoric. Either route requires explicitly distinguishing the
single-observation capacity prior from the N-fold one and stating which is used
throughout.

---

### F2: §3.2 — the `I_q^{(1)} − I_{p_J} = o(d)` step requires an unstated `d_eff = O(1)` assumption [severity: high]

**Location**: §3.2, the paragraph deriving `D(m_q‖m_{p_J}) = Ω(d) − o(d)` via eq. (3.2.1).

**Concern**: The spec writes "both `I_q^{(1)}` and `I_{p_J}` are bounded by the
single-observation *resolvable* complexity `C_1 = O(d_eff)`, which does not grow
with nominal `d` … so `I_q^{(1)} − I_{p_J} = o(d)`". Two independent flaws:

1. *The boundedness-of-each-term step is too weak.* From `|I_q^{(1)}|, |I_{p_J}| ≤
   C_1`, the *difference* satisfies `|I_q^{(1)} − I_{p_J}| ≤ 2 C_1`. The
   conclusion `= o(d)` therefore requires `C_1 = o(d)`, i.e. `d_eff = o(d)` in
   nominal `d`. This is plausible for hyperribbon-geometry models at fixed σ (the
   stiff-direction spectrum is a few directions regardless of `d`, A&M Fig. 2 /
   Quinn Fig. 1), but it is *not stated as an assumption*. The argument as
   written reads as if `o(d)` follows from boundedness alone; it does not.

2. *Even with `d_eff = O(1)`, `I_{p_J}` can fall well below `I_q^{(1)}`.* A&M
   Fig. 5 shows `I_{p_J} < 1` bit at `d = 26` in the exp-decay model while
   `I_{p*} ≈ 4` bits — and for a cooperative `q = m_{p*}`, `I_q^{(1)} = I_{p*}`,
   making the gap `I_q^{(1)} − I_{p_J} = Θ(d_eff)`. So the subtracted term is
   not "negligible" — it could *cancel* a constant-multiplied
   `B(p_J) = O(d)` numerator at intermediate `d`. The argument only works once
   `B(p_J) ≫ d_eff · log L` is empirically established, which is exactly what A&M
   measure but not what the inequality `I_q^{(1)} − I_{p_J} = o(d)` says.

**What would resolve it**: state the assumption "for sloppy hyperribbon models at
fixed σ, `d_eff = O(1)` in nominal `d` (A&M Fig. 2, Quinn §2)" explicitly. Replace
the `I_q^{(1)} − I_{p_J} = o(d)` step with `|I_q^{(1)} − I_{p_J}| ≤ 2 C_1 = O(1)`
under that assumption, so the resulting inequality reads `D(m_q‖m_{p_J}) = Ω(d) −
O(1)` and is honest about needing the explicit `Ω(d) ≫ O(1)` separation. Or
equivalently, point at A&M's empirical `B(p_J) > 500` bits as the quantitative
ground rather than presenting the chain as a derivation.

---

### F3: §3.2 — Quinn's discreteness replies do not bound the foreign-`q` marginal mismatch [severity: high]

**Location**: §3.2, the closing paragraph: "Quinn et al. also dispatch the
discreteness objection that a *discrete* `p*` must mis-predict … Both bound
`p*`'s discretisation penalty at `O(1)` **without** leaning on A&M's
self-sampling".

**Concern**: The "discretisation penalty" the foreign-`q` score charges is the
*marginal mismatch* `D(m_q‖m_{p*})` in (2.1.2). Quinn's three replies
(`resources/quinn.pdf` p. 28) are:

1. "Eventually" implies more data, ruled out by the prior depending on `N`;
2. Along a relevant direction, discretization is no worse than truncating to a
   sensible number of digits, *given error bars*;
3. Along an irrelevant direction, placing weight at an extreme value is what
   *effective theories* do (QED: ignoring all other couplings is fine because
   they're irrelevant to the experiment).

None of these is a bound on `D(m_q‖m_{p*})` for a *foreign* `q`. (1) is a defence
against an objection that assumes future updating; (2) is about *posterior
accuracy* (truncating an inferred `θ`), not predictive marginals; (3) is about
*effective-theory irrelevance under the model's own predictions*, not about a
mismatched `q` placing data in atom gaps. The spec then immediately writes,
correctly in the next sentence, that `D(m_q‖m_{p*}) = O(1)` is "asserted, not
shown, and left to the experiment" — but this contradicts the prior claim that
"both bound `p*`'s discretisation penalty at `O(1)`". The Quinn replies do *not*
provide a bound; the spec needs to choose one of the two readings and stop
straddling them.

**What would resolve it**: drop the "both bound … at `O(1)`" sentence (or
restrict it to *self-sampled* `x ∼ p*`, where it is true by the equalizer), and
let the subsequent honest concession ("asserted, not shown") stand on its own.
Equivalently: state explicitly that Quinn's replies bound the *self-consistent*
posterior bias but say nothing about `D(m_q‖m_{p*})` for arbitrary `q`, and that
the §3.2 case for transfer therefore rests on an experimental (not theoretical)
hypothesis.

---

### F4: §3.4 — the "NML / MDL" framing conflates a code (`p_NML(x)`) with the prior `p_proj(θ)` [severity: medium]

**Location**: §3.4 bullet "**NML / MDL — `p_proj`**" and the "siblings" paragraph
that follows.

**Concern**: The Shtarkov/Rissanen pointwise-regret minimiser is `p_NML(x) =
max_θ p(x|θ)/Z`, a distribution over *data*. It minimises
`max_x[log max_θ p(x|θ) − log q(x)]`. The object `p_proj(θ)` defined immediately
afterwards is the *MLE pushforward* of `p_NML` (A&M App. A.3, Quinn §5.2,
nml-mdl.md §4); it is a prior. `p_proj` does *not* itself solve the pointwise
minimax problem and is *not* the MDL universal code. The spec's tutorial
`nml-mdl.md` itself states "NML is not a Bayes mixture. No prior makes
`m_π = p_NML` exactly at finite `n`; the two universal codes agree only
asymptotically. `p_proj` is the MLE-pushforward of `p_NML`, a prior — not
`p_NML` itself, and not a mixture of the family." The spec §3.4 elides this
distinction when it writes "The two solve the *same* universal-coding problem
under different regret notions — `p*` the worst-case **expected** redundancy …,
NML the worst-case **pointwise** regret"; the "two" implicitly includes `p_proj`,
but `p_proj` solves *neither* — it is a heuristic prior that *approximates* `p*`
empirically (Quinn Fig. 12), through a route motivated by NML on the data side.
The "siblings, not approximation" framing is therefore a rhetorical upgrade that
the mathematics does not deliver. The "essentially **unique** resolution
adaptation" claim — finite-σ near-coincidence in hyperribbon geometry — is also
just Quinn Fig. 12 empirically, not a theorem.

**What would resolve it**: clarify the trichotomy `p* | p_NML | p_proj`: `p*`
solves min-max-expected redundancy and is a prior; `p_NML` solves
min-max-pointwise regret and is a code over data; `p_proj` is the MLE pushforward
of `p_NML` and is a prior, but solves *neither* minimax exactly. Then the §3.4
argument becomes "two budget-dependent universal-coding objects, with `p_proj`
the MDL-motivated heuristic prior that approximates `p*` well in hyperribbon
geometry (Quinn Fig. 12)". This is honest about `p_proj` being an empirical
sibling, not a theoretically-equal one, and it preserves the spec's
"capacity-vs-MDL" framing without overclaiming the equivalence.

---

### F5: §3.4 — "Jeffreys is the σ→0 limit of both" misses A&M's own boundary caveat [severity: medium]

**Location**: §3.4 ("Jeffreys is the `σ→0` (infinite-budget) limit of both") and
the "Why they coincide here" paragraph.

**Concern**: A&M §2.1 explicitly says "`p*(θ)` approaches a continuum at any
interior point, it remains discrete at Fisher distances ∼1 from the boundary"
and "the worst-case bias pressure detects this; hence, the maximum for Jeffreys
prior does not approach that for the optimal prior: `B_J ↛ 0`. However, since
mutual information is dominated by the interior in this limit, we expect the
values for `p_J(θ)` and `p*(θ)` to agree in the limit: `I_J − I* → 0`." So `p*
→ p_J` is true *in the interior, in mutual information*, but the boundary atoms
persist and `B(p_J)` does not tend to zero. The same caveat applies to
`p_proj` — its halo on convex boundaries persists at small σ in a different way.
The spec's blanket "Jeffreys is the σ→0 limit of both" overstates a result that
is more subtle (and the spec actually needs this subtlety: §3.4's "Adversarial
to `p_proj`, benign for `p*`" corner — the persistent boundary halo of `p_proj`
— exists precisely *because* convergence to Jeffreys is not uniform).

**What would resolve it**: add the qualifier "in the interior" (or "in mutual
information"), and note that boundary atoms / boundary halos persist at finite
Fisher distance from the boundary, which is in fact what produces the §3.4
"corner 1" contrastive case. Cross-reference A&M's Fig. 2 caveat.

---

### F6: §1.2 / §3.1 — "competitor worst-case bias `O(d)`" overgeneralised from two model-specific data points [severity: medium]

**Location**: §0 ("`O(d)` competitor bias vs `O(1)` for `p*`"); §1.2 ("competitor
bias `O(d)` vs `p*`'s `O(1)`"); §3.1 ("`B(p_J)` *grows with dimension* (`>500`
bits at `d=26` in the exp-decay model … `≈55` bits in the hypercone)"); §3.2
("`B(p_J) = max_θ b_{p_J} = O(d)`").

**Concern**: A&M's actual evidence for `B(p_J)` growth is *two model-specific
data points* — exp-decay (>500 bits at d=26) and hypercone (~55 bits at d=26).
These are not the same growth rate. A naive linear extrapolation would imply
`O(d)` for exp-decay and `O(d log d)`-ish for hypercone (the hypercone derivation
in A&M App. A.1 gives `B ~ const · d` analytically but the spec doesn't track
the constant). Asserting `B(p_J) = O(d)` *and* `Ω(d)` (lower bound) as a generic
hyperribbon fact requires either a theorem (none is cited) or a careful empirical
qualification ("in the exp-decay model up to d=26"). The asymmetry claim
`O(d) vs O(1)` reads as universal but is two model-specific empirical
observations from one paper; the order constants matter at finite `d` (compare
exp-decay 500 vs hypercone 55), and "Ω(d)" as a lower bound is in fact unstated
in A&M.

**What would resolve it**: replace `O(d)` and `Ω(d)` with empirical
characterisations: "A&M observe `B(p_J)` growing rapidly with `d` (e.g. >500 bits
at d=26 in exp-decay, ~55 bits at d=26 in the hypercone — App. A.1 derives
roughly linear growth in d for the hypercone)". Make clear this is empirical
for the models we use, not a theorem about hyperribbons in general. Drop the
`Ω(d)` lower bound or replace it with the actual hypercone closed form `B ~ (d−1)`.

---

### F7: §2.4 — flat co-volume does not screen all uniform-vs-Jeffreys differences [severity: medium]

**Location**: §2.4 negative-control / T2 description and §4.1.3 constant-cross-section cone.

**Concern**: The spec says "flat co-volume ⇒ `R(p_J) = R(p_U)` within MC error,
at every `d`. That identity is the hard screen (T2)". The reasoning: with
constant `√det g`, Jeffreys *equals* uniform on `Θ`. This is exactly right *as
long as the parameter box `Θ` itself is the same for both priors*. But spec
constructs the constant-cross-section cone as the hypercone with `r(θ_1) = r_0`
(taper switched off). In the hypercone family, `θ_1 ∈ [0, L]` and
`θ_μ ∈ [0, 1]`. With `r(θ_1) = r_0`, `√det g` is constant on this box, and
`p_J = p_U` algebraically. Good. But the test as stated, `|R(p_J) − R(p_U)| <
3·MCSE`, is then *trivially zero* up to RNG noise: if the same Monte-Carlo
samples are used for both priors (common random numbers), `R(p_J) − R(p_U) ≡ 0`
exactly, not just `< 3·MCSE`. If independent samples are used, MCSE for the
*difference* is `√2` times MCSE of each, but the test would be passing/failing
on RNG seeds, not on any property of the marginal estimator. The test is "broken
Jeffreys-construction" if and only if `p_J` is computed *numerically* from the
FIM (and could fail to equal `p_U` due to quadrature error). The spec should
either say "the Jeffreys construction is built from a *numerical* FIM evaluation
and grid quadrature, so `p_J` may differ from `p_U` even with constant `√det g`;
T2 checks this numerical pipeline", or explicitly use common random numbers
and assert exact agreement. As written, the test's status is ambiguous.

**What would resolve it**: specify whether T2 uses common random numbers
(in which case assert exact equality, not within MCSE), and clarify that T2 is
testing the *numerical pipeline* (FIM eval → quadrature normalisation → mixture
marginal) for inadvertent inequalities, not the analytic identity.

---

### F8: §0 — "dominated by the prior matched to nature (its own pullback) *by theorem*" overclaims uniqueness [severity: low]

**Location**: §0 paragraph 3: "under a strictly proper score `p*` is dominated
by the prior matched to nature (its own pullback) *by theorem* (the compensation
identity, §2.1)".

**Concern**: The compensation identity says `R_N^q(π) = I_q + D(m_q‖m_π)`,
minimised when `m_π = m_q`. The minimising *condition* is on the *marginal*; any
prior whose Bayes mixture equals `m_q` is optimal. In an overparametrised /
sloppy model (the regime this spec lives in), many distinct priors can produce
the same data marginal — the *equivalence class of priors* with `m_π = m_q` may
be large. The phrase "the prior matched to nature (its own pullback)" suggests
uniqueness, and "by theorem" promotes a Bayes-mixture-matching condition to a
prior-matching one. §2.3 actually gets this right: "the prior whose marginal
matches that `q_c`". §0 should match §2.3 — strictly proper guarantees
optimality of the data marginal, not the prior.

**What would resolve it**: replace "the prior matched to nature (its own
pullback)" with "any prior whose Bayes mixture matches nature's marginal
(e.g. `q` itself in identifiable models)". Cross-link to §2.3, which already
has the right wording.

---

### F9: §1.1 — `b(θ)` definition does not name its dependence on the prior [severity: low]

**Location**: §1.1 notation table, row `b(θ)`.

**Concern**: The entry reads `b(θ) = D(p(x|θ)‖m_π) − I(Θ;X)`. Both `m_π` and
`I(Θ;X)` depend on a choice of prior `π`; A&M Eq. 5 defines `b(θ)` *for a fixed
prior*, and the value `b_π(θ)` is what's reported in their figures. The notation
`b(θ)` (no `π` subscript) is therefore implicitly π-dependent. §3.2 then writes
`b_{p_J}(θ)` and `𝔼_q b_{p_J}` with the subscript made explicit — but the table
in §1.1 lets it be implicit, and earlier sections (§0, §2.4) use `b(θ)` without
qualification. This is minor but means the reader who looks up the symbol in
§1.1 sees an ambiguity.

**What would resolve it**: change the table entry to `b_π(θ) := D(p(x|θ)‖m_π) −
I_π(Θ;X)` for a given agent prior `π`, with a one-line note that `b(θ)` is
shorthand when `π` is fixed by context.

---

## What the spec gets right

The compensation-identity decomposition `R_N^q(π) = I_q^{(N)} + D(m_q‖m_π)` and
its derivation in §9.1 are clean and correct; the three-redundancy disambiguation
table in §2.1 is one of the clearest statements in the literature of why "infomax
minimax" and "minimise foreign-q redundancy" do not coincide. The §2.3 distinction
between per-cell pullback and c-averaged `q̄` is correct and is exactly the kind of
result that is easy to elide. The hypercone closed form derivation in §9.2 has the
right structure, sign convention is now honest (mode vs mean, `(d−1)/x` is leading
not exact), and the numerical check at d=26, x=10 (mean ≈ 2.08 vs leading 2.5)
that I independently confirmed agrees with the spec's claim. The geometry block in
§1.2 successfully threads the hyperribbon / hypercone / exp-decay / constant
cross-section caricature-vs-realisation relationship, and the §3.5 "what would
sink it" list is unusually candid about the failure modes the experiment must rule
out — including the `q̄` ceiling and the requirement to include `p_proj` in the
competitor set for clean attribution.
