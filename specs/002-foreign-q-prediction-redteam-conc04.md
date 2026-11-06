# Conceptual red-team review of spec 002 — Foreign-q prediction

Reviewer: red-team sub-agent
Reviewer model (declared identity): Claude Opus 5.5
Effort tier: max (set at spawn by the main agent; not verifiable here)
Roster verified: 2026-11-06
Date: 2026-11-06
Spec version: e6e577a (the working tree differs only in the status table, which now marks §0–§3 reviewed)
Scope: §0–§3 and the files they reference

## Summary

**Claim:** the scoring core of §0–§3 is sound, but the nature family and the verdict rule
do not yet make a foreign-`q` test (F1, F8). **To decide:** how to rebuild the tilt
family's negative branch, and which cells count as tests, before §4–§5 are built on them.
The compensation identities, the per-nature floor against the sweep-average ceiling and the
capacity cap are correct, and nearly every `[read]` tag I checked says what the spec
claims. The work is thinnest where the design meets the geometry. The tilt family's `t < 0`
branch is built from the zeros of `√det g`, which is where `p*` keeps its weight, so the
natures expected to favour `p*` most are close to its own world, and the verdict rule
neither sees this nor sets aside the cells a competitor wins by construction. The
equal-width hypercone, used as the analytic caricature and as the control where ranking is
free, lacks the geometric fall-off that keeps `p*`'s side `D`-independent: under the spec's
own definitions `p*`'s posterior deviation, calibration term and capacity all grow with `D`
there (F5). §3.3's "bias term" is mostly posterior spread (F7), and the decisive exp-decay
comparator `p_ref` is undefined in these sections and constrained by an unstated
permutation symmetry (F4). F1 and F8 block the algorithm and tests; the other findings are
revisions of §0–§3 text that can proceed alongside.

## Findings

### F1: The tilt family's negative branch approaches `p*`'s own world [severity: high]

**Location**: §2.3 (tilt family); §0 ("passes through several priors' own worlds"); §2.5
(own-world points of the tilt axis); §3.7 (the self-sampling screen).

**Concern**: *Aims not achieved.* For `t < 0`, `q_t ∝ (√det g)^t` moves its mass to where
`√det g` is small, and in both families that is where `p*` puts its weight.

- *Exp-decay.* With equal shares, two components with equal rates have identical Jacobian
  columns, so `√det g = 0` on every coincidence hyperplane `θ_μ = θ_ν` inside the box `Θ`;
  it is also small on the faces where a rate leaves the observation window. These are the
  manifold's lower-dimensional edges: A&M equate an edge's dimension with the FIM's rank
  there [read: A&M Fig. 2 caption]. At small budget all of `p*`'s weight is on 0- and
  1-dimensional edges [read: A&M §2.1, Fig. 2], and its first new atoms appear on the edge
  `k_1 = k_2` [read: Mattingly p. 1763]. For `D = m`, `√det g` is `Π_{μ<ν}|φ_μ − φ_ν|` up to
  a positive factor [read: A&M App. A.5]. Near the line where all prices coincide, its
  `D(D−1)/2` vanishing factors against a `(D−1)`-dimensional transverse volume make `q_t`
  non-normalisable for every `t ≤ −2/D` (−0.08 at `D = 26`). Below that, the floor `ε_g`
  (OQ-2) decides the nature, not `t`. As `ε_g → 0`, nature collapses onto "honest up to a
  price", an edge `p*` weights.
- *Hypercone.* The `θ_1`-marginal `∝ θ_1^{t(D−1)}` is non-normalisable for
  `t ≤ −1/(D−1)` (−0.04 at `D = 26`). The branch therefore collapses onto the tip, where
  `p*` keeps atoms (tip-to-base weight ratio 0.074 at `D = 26` [read: cone_pstar.out]).
- A floor set high enough to prevent the collapse would instead make `q_t ∝ ε_g^t` flat
  wherever `√det g` is below it. At `D = 26`, where `√det g` spans tens of orders of
  magnitude [read: Quinn §5.1], that is plausibly most of the box, which is close to `p_U`'s
  world [guess].

The note that §2.3 cites for its natures drew exactly this for the `√det g` family. It
concluded that the family "runs from Jeffreys' own world toward `p*`'s" and that "a
protagonist win near c=1 is partly self-served" [read: notes/q-family-visualisation.md,
"What they show", "B: Fisher-weighted"]. The spec kept the construction and dropped the
caveat: §0, §2.3 and §2.5 name only `t = 1` and `t = 0` as own-world points. Yet `t < 0` is
where the spec expects `p*` to do best: the thin end, where Jeffreys' `Δ` is largest
(§1.2).

- Where every deployable prior exceeds `C_N` there, §3.7 already sets the cell aside as
  settled by theorem, so the branch tests nothing.
- Where the best deployable prior stays below `C_N`, a `p*` lead is partly self-served:
  the failure that sank spec 001.

§3.7's screen ("leads only near its self-sampling control") cannot catch this, because
"near" has no measure and the branch is not recognised as near. Settled by: per `t`, the
`q_t`-mass within one Fisher length of `supp p*`, or `D_KL(m_{q_t}‖m_{p*})` set against the
same quantity for each deployable prior.

**What would resolve it**:
- In §2.3 and §2.5, name the `t < 0` end as close to `p*`'s world (and to the edge-heavy
  `p_proj`'s).
- Give every nature a measured foreignness coordinate, for instance `D_KL(m_q‖m_π)` for
  each prior `π` of the cast, and report §2.4's summaries against it.
- Define "near" in §3.7 as a threshold on that coordinate (see F8).
- Either keep `t` above the normalisable bound (`−1/(D−1)` in the cone, `−2/D` in exp-decay
  at `D = m`), or replace the negative branch with a nature not built from `√det g`'s
  zeros, and declare its lean.

---

### F2: The case for transfer is made against Jeffreys; the verdict is taken against the best deployable prior [severity: medium]

**Location**: §0 ("Why transfer could hold"); §2.1 (paragraph after the redundancy table);
§3.2.

**Concern**: *Conceptual confusion; aims.* §0 says the deployable priors' bias "grows with
the number of parameters `D`", and §2.1 calls their mismatch "the co-volume bias". But the
deployable set contains two priors without that bias:
- `p_ref`, built so that the irrelevant volume "never tilts" the relevant direction
  (§3.5);
- `p_U`, which §1.2's table lists as unbiased in the axis-aligned cone ("Jeffreys only").
  Its bias in exp-decay is `[guess]` (§3.1).

The case of §3.1–§3.2 is made for `p_J` alone: (3.2.1) is written for `p_J`. The verdict
(§2.4, §3.7), however, is taken against the minimum over `{p_J, p_U, p_LN, p_ref}`. For the
comparison §3.5 calls decisive, exp-decay against `p_ref`, §3 offers no argument for `p*`
beyond the ranking being unavailable.

**What would resolve it**: State the asymmetry as `p*` against `p_J` (and `p_LN` [read: A&M
§2.2]). Say in §0 and §3 that no case is made against `p_U` and `p_ref`, and that against
`p_ref` in exp-decay the expectation rests only on §3.5's "unavailable" ranking. Or supply
the missing argument.

---

### F3: The mis-budget comparison contradicts its example and its cited evidence [severity: medium]

**Location**: §0 ("Second protagonist", last sentence); [^0-motives] ("More evidence, and
circumstances"); §2.2 ("Mis-budgeted `p*`").

**Concern**: *Conceptual confusion.*
- (a) The example sets the budget by expected exposure ("how much one will see of them ...
  the flatmate for a year"). On that definition the flatmate-observer's `p*_{10N}` is
  correctly budgeted for its horizon. Scoring it at `N` (`Δ^{bud}`) therefore asks what a
  long-horizon prior costs before the horizon is reached. It does not ask what knowing the
  budget is worth: this observer knows its budget, and on the score that budget defines,
  `R_{10N}`, `p*_{10N}` is the minimax prior.
- (b) §2.2 says "a wrong resolution costs on both sides (note §3)", and that the too-coarse
  loss grows "linearly in `N/M`". The cited note's high-`D` result is the opposite on both
  natures it tested: "the *coarser* prior wins at every budget tested" [read:
  notes/budget-value-of-information.md §3.3]. "Both sides" holds only in the worst case and
  in 1-D (that note's §3.1).
- (c) The example placed under "Too fine (`M > N`)", `p*_1` beating `p*_{16}` at budget
  16, has `M < N`. It shows the too-coarse prior beating the correctly budgeted one.

**What would resolve it**:
- Either make the flatmate-observer genuinely mis-budgeted (it expects a year; the flatmate
  leaves after `N` encounters), or say that `Δ^{bud}` at `N` measures the short-run cost of
  a long-horizon prior.
- Restate §2.2 as: "in the worst case a wrong resolution costs on both sides; on the
  natures computed in the cone, too coarse wins".
- Move the `p*_1`/`p*_{16}` example under "too coarse".

---

### F4: Exp-decay's permutation symmetry is unstated, and three claims depend on it [severity: medium]

**Location**: [^0-motives] ("Handing over the ranking"); [^0-matched]; §1.1 (`Θ` "a compact
box"); §3.5 (item 3 and the paragraph after it); §3.7.

**Concern**: *Unstated assumption.* With equal shares `a_μ = 1/D` on a box, `y(θ)` is
invariant under permuting the `θ_μ`, so the model is not identifiable. A&M impose
`k_1 ≥ k_2` [read: A&M Fig. 1 caption]. Mattingly et al. point out that swapping two rates
leaves the data unchanged, so the model is singular unless the rates are ordered [read:
Mattingly p. 1763, footnote]. §0–§3 never say so, and the following depend on it:
- (a) [^0-matched] attributes the non-uniqueness of matching priors to sloppiness. But
  Gaussian convolution is injective on measures (the Gaussian's Fourier transform has no
  zeros), so `m_π = m_q` if and only if `y_#π = y_#q`. In any identifiable model, however
  sloppy, the class is a single prior. Here it is larger only because of the symmetry (and
  the cone's tip).
- (b) The decisive comparison is against `p_ref` "built from at least two of the OQ-8
  candidate rankings" (§3.5, §3.7). Under the symmetry, any two coordinate orderings give
  priors that are permutations of each other, and they score identically on §2.3's natures,
  which are all symmetric. A candidate must therefore rank something that breaks the
  symmetry, such as an order statistic like "the slowest rate", which amounts to
  reparametrising to the ordered cone. A direction that varies across `Θ` counts as a
  ranking in the Berger–Bernardo construction only if it integrates to a coordinate. §0–§3
  define neither, so the decisive comparator exists only as OQ-8 (§7).
- (c) [^0-motives] says that if the story named the motive that matters ("only conscience
  counts"), "the reference prior with that motive first would remove the bias". The
  likelihood cannot tell conscience from habit (same share, same form), so "that motive
  first" ranks an arbitrary coordinate. What makes a motive matter is its price, and the
  price is part of nature.
- (d) The zeros of `√det g` on the coincidence hyperplanes are what F1 turns on.

**What would resolve it**:
- State the symmetry in §1.2, or restrict `Θ` to the ordered cone as A&M and Mattingly do.
- Correct the reason given in [^0-matched].
- In §3.5, say what `p_ref` ranks in exp-decay, and check that the candidate rankings give
  distinct priors after symmetrisation.
- Rewrite "handing over the ranking" with unequal shares, or present it as information
  about `θ` rather than a ranking.

---

### F5: The equal-width hypercone breaks `p*`'s `D`-independence [severity: medium]

**Location**: §1.2 (square hypercone; three-families table); also §0 ("stays roughly flat
as `D` grows"), §3.2 ("which `m_{p*}` respects"), §3.3 ("its calibration term is `O(1)`,
independent of nominal `D`"), [^3-typical], §3.4 ("They nearly agree on our models"), and
§3.5 and §3.7 (the cones as "the control where ranking is free").

**Concern**: *Unstated assumption; notation drift.* The glossary defines a hyperribbon by
widths that "fall off roughly geometrically"; the square hypercone's `D − 1` sub-resolution
widths are all equal. The spec draws the consequence once: `C_1` grows linearly, from 4.02
to 11.25 nats between `D = 26` and 100 (§3.1, §3.2 point 1). Its other `D`-independence
claims for `p*` fail in this model too, by its own definitions:
- *`Δ`.* §1.1 defines `Δ` as A&M's full deviation (Eq. 9). Every cone figure (§1.2,
  [^1-pstar-bias], §9.2, following A&M App. A.1) is only its `θ_1` component. Take the
  reduced cone at `θ_1 = 40`, with nature uniform on the cross-section, at `D = 26`:
  - the full `Δ` is 1.67 for Jeffreys and 1.17 for `p*`, not 0.62 and 0.10;
  - `p*`'s grows like `√(D−1)`, reaching 2.34 at `D = 100`[^check];
  - the reason is that, for any prior symmetric on the cross-section, the posterior means
    in the sub-resolution directions sit mid-section while the MLE sits on its faces.
- *Calibration (§3.3).* In §3.3's own Gaussian approximation and at the same point,
  `p*`'s calibration term is 0.21 nats at `D = 26` and 0.85 at `D = 100`. That is linear in
  `D` and about six times Jeffreys' (0.03 and 0.15)[^check]: two-atom cross-sections spread
  the predictive more than uniform ones.
- *[^3-typical].* The distance from a datum to the nearest cross-section corner grows like
  `√(D−1)`, not `O(1)`.
- *§3.4.* The evidence for near-coincidence of `p*` and `p_proj` is mutual information in
  sum-of-exponentials [read: Quinn Fig. 12]. The q-family note estimates that `p_proj`
  tilts about ten orders of magnitude toward the base in the `D = 26` cone [read:
  notes/q-family-visualisation.md, "B′ drawn", tagged guess there].
- *Budget.* The one-relevant-direction split holds only while `σ/√N ≥ 1`; A&M fix
  `σ = 1`. The cross-section's Fisher width is `r√N/σ`, so at `N = 16` everything beyond
  `θ_1 = 12.5` is resolvable, and `p*_N`'s own thick-end tilt grows with `N` [read: budget
  note §3.3].

So a loss of `p*` to `p_ref` in the cone, which §3.7 reads as "the expected control result",
may come from this equal-width artefact rather than from ranking being free [guess].
Settled by: the same comparison in a cone with geometric widths.

[^check]: Reviewer's check, not in the repo. It uses the reduced cone of `cone_pstar.py`
    with the sub-resolution coordinates added: Jeffreys uniform on the cross-section,
    `p*` on equiprobable corners, the MLE clipped to the cross-section, 4000 draws. It
    reproduces `cone_pstar.py`'s `θ_1` deviations (0.62 and 0.09).

**What would resolve it**:
- Restrict the claims in §0, §3.2 (A&M's invariance), §3.3, [^3-typical] and §3.4 to
  geometric widths.
- Say in §1.1 and §1.2 that the cone's `Δ` is its `θ_1` component.
- Add A&M's geometric-width cone (widths `L, 1, L^{−1}, …`) as the analytic caricature and
  the ranking-free control. A&M state that it leaves Jeffreys' effective prior and `Δ`
  unchanged [read: A&M App. A.1]. Keep the equal-width cone as a stress case.
- State the budget range over which the cone has one relevant direction.

---

### F6: The hypercone's "explicit" asymmetry adds a deviation to a divergence, and uses `Δ = (D−1)/x` outside its range [severity: medium]

**Location**: §1.2 (square hypercone paragraph: "largest at the thin end, where a foreign
`q` can place data"); §3.2 ("In the hypercone the asymmetry is explicit"); §9.2.

**Concern**: *Conceptual confusion; math.*
- (a) The sentence "`p*` pays ≈0 on self-sampled data, which lands on its atoms, but
  `O(1)` plus `D_KL(m_q‖m_{p*})` on data in the gaps" adds a posterior deviation (noise
  units) to a divergence (nats). No single reading of "pays" makes it true:
  - if "pays" means redundancy, `p*`'s on its own data is `C_N` (equalizer, §3.1), not 0;
  - if it means mismatch, that is 0 on its own data by definition, so "plus `D_KL`" counts
    it twice;
  - if it means `Δ`, on its own data `p*`'s deviations are mostly shorter than its atom
    spacing [read: A&M Fig. 4 caption], which is `O(1)`, not ≈0.

  Weighing this against Jeffreys' `Δ` ("whether that net favours `p*`") compares
  incommensurable quantities.
- (b) `Δ = (D−1)/x` is A&M's expansion for `1 ≪ x ≪ L` [read: A&M App. A.1], and §9.2
  states that it needs `x² ≫ 4(D−1)`. The core uses it exactly where that condition fails.
  At the thin end the true deviation saturates near `√(D−1)`: it is 3.75 at `x = 3`,
  `D = 26`, against `(D−1)/x = 8.33` [read: cone_pstar.out]. The validity condition that
  the thin-end claim needs appears only in §9.2, which hides load-bearing content in the
  apparatus.

**What would resolve it**: Make the hypercone comparison in one currency, per-state
redundancy or mismatch; the budget note §4 already gives reduced-cone numbers for both. In
§1.2 and §3.2, use §9.2's exact root, or state the range of `(D−1)/x` wherever it is used.

---

### F7: §3.3's "bias term" is mostly posterior spread [severity: medium]

**Location**: §3.3, (3.3.1) and the two paragraphs after it.

**Concern**: *Conceptual confusion.* The bias term
`(μ_π − y(θ))ᵀ Σ_π^{−1} (μ_π − y(θ))` is centred on the realised truth. Take the matched
prior `π = q`, and let `c_i` be the eigenvalues of the posterior covariance. Its expected
bias term is `E_X tr(Σ_q^{−1} Cov_q[y|X]) = Σ_i c_i/(σ² + c_i) > 0`: pure spread, no bias.
Consequences:
- The "unavoidable cost of not knowing `θ`", which §3.3 assigns to the calibration term,
  sits in both terms.
- The bias term is a held-out analogue of A&M's `Δ` only where the prior-induced shift
  dominates the posterior spread. That holds for Jeffreys at large `D`, but not for `p*`,
  the protagonist.
- The "`O(σ)`" gap between `y(θ_true)` and `y(θ̂_x)` is of the same order as `p*`'s `Δ`.

As written, "The bias term decides the contest" and the §6 diagnostic built on it would
report spread as bias.

**What would resolve it**: Decompose the prior-dependent part of (2.1.6),
`D_KL(m_q(·|X)‖m_π(·|X))`, instead of `D_KL(p(·|θ)‖m_π(·|X))`. In the same Gaussian
approximation it splits into two terms, both zero for the matched prior:
- a mean-shift term `(μ_π − μ_q)ᵀ Σ_π^{−1} (μ_π − μ_q)`, which is the right held-out
  analogue of `Δ`;
- a covariance-mismatch term `tr(Σ_π^{−1} Σ_q) − m + log(det Σ_π / det Σ_q)`.

---

### F8: The verdict rule sets aside cells `p*` wins by theorem, but not cells it loses by construction [severity: medium]

**Location**: §3.7; §2.5.

**Concern**: *Aims not achieved; vague claim.* By (2.1.2), wherever nature is a deployable
prior, that prior attains the floor. This happens at:
- `t = 1`, for `p_J`;
- `t = 0`, for `p_U`, and for `p_ref` in the axis-aligned cone;
- each deployable prior's self-sampling control.

In those cells `Δ_{R_N}(p*) ≥ 0`, and likewise `Δ_{r_N}(p*) ≥ 0`, by construction. §3.7
excludes cells in which every deployable prior exceeds `C_N`, but not these. Its "refuted
where `p*` ties or loses" therefore fires there, and by continuity near them, whatever
happens elsewhere. Three phrases are also undefined:
- "Supported ... across the tilt family" can never hold if it means "for every `t`".
- If it means "wherever", no rule says which map supports or refutes the expectation.
- "Leads only near its self-sampling control" has no measure of nearness.

**What would resolve it**:
- Define the test cells symmetrically: mark as controls the cells settled in either
  direction, both those where `p*` wins under the cap `C_N` and those where a deployable
  prior is matched (`D_KL(m_q‖m_π) ≈ 0`).
- State the verdict per region of the tilt axis, with the controls marked.
- Define "near" by F1's foreignness coordinate.

## Minor

- m1 — §0, §1.1, §2.1 (text after the table), §3.7 — `p_lat`'s minimaxity is stated without
  the finite-outcome qualifier that §2.2 gives, and "The same reading applies to `p_lat` on
  `r_N`" relies on a by-theorem cap that is unproven for Gaussian data [read: Komaki 2011
  §4] — qualify each.
- m2 — [^0-motives] — Jeffreys is called "the only weighting that does not depend on how
  prices are measured", but maximum-information priors keep reparametrisation invariance
  too [read: Quinn §5.1], as do `p_proj` and reference priors — say "the only local,
  budget-free one".
- m3 — [^0-motives], §1.1, §2.2, §2.3, [^1-uniform] — linear-reader breaks: Fisher
  volume, width, Fisher length and `Θ` are used before §1; OQ-8, OQ-2 and T9 have no
  pointer at first use; "cooperativeness axis" is never defined — link or define.
- m4 — §1.1 and throughout — *Symbol choice* clashes: `t` is both tilt and observation
  time (the letter rule 3 cites); `q` is nature and, in §3.4, a code over data; `G` is
  grid resolution and the Gumbel function; `L` is Fisher length and the cone's `θ_1` range
  (both in [^1-pstar-bias]); `ν` is the nature and an index in `g_{μν}`; `S` is a score and
  Berger–Bernardo's `S`; `r_θ(π)` is a cumulative loss beside the one-step `r_N`; `x` is a
  vector and, in §1.2 and §9.2, a scalar; §0 writes `n` for `N`; `ω` and `w` are a rule-5
  pair — rename.
- m5 — §1.1 — Fisher length, relevance and co-volume are defined at noise `σ` but used at
  budget `N` ([^0-motives], §2.3, §3.3) — state the budget in the definitions.
- m6 — §1.1 and §2.2 tables, §3.4 — `p*` is listed "Discrete"/"yes", while
  [^1-discrete] supports only "usually" in multi-`D`. For vector Gaussian channels with
  ball-shaped input sets the optimum lies on finitely many spheres [recalled: Shamai &
  Bar-David 1995; Dytso et al. 2019], which is relevant to the curved-boundary variants.
  Conversely, `p_proj` is listed "no" although it gives finite weight to zero-dimensional
  points [read: Quinn §5.2], and §3.4 says the boundary "keeps both discrete" — align the
  labels.
- m7 — §1.2, (1.2.3) — `V_⊥` is one global number (a product of end-to-end widths),
  whereas the mechanism needs the local co-volume whose gradient tilts Jeffreys, as the
  glossary defines it. `V_g ≈ Π L_μ` is off by a factor `D` in the hypercone itself
  (`V_g = L/D` against `Π L_μ = L`, at `σ = 1`). Jeffreys weights Fisher (prediction-space)
  volume, not "parameter-space volume", which is what `p_U` weights — define `V_⊥` locally
  and fix the wording.
- m8 — §1.2 — "Each load-bearing claim reduces to `g(θ)` and its gradient" is false for the
  `p*`/`p_proj` contrast of §3.4, which turns on the noise halo, an extrinsic property of
  the boundary that `g` does not encode — qualify.
- m9 — §2.3 — a stress nature "varying on scales below one Fisher length" varies invisibly
  to every score, since `m_q` sees `q` only through the likelihood — say "smooth on the
  atom-spacing scale", as §3.4 does.
- m10 — §2.4 — "the gap to the ceiling, `S(π) − S(q̄)`" is reported per nature, where `q̄`
  is not the floor (§2.5) and the gap can be negative — per nature, report the mismatch
  `S − I_q`, and report the `q̄` gap on the sweep average only.
- m11 — §2.4, §3.7 — in exp-decay the minimum defining `Δ_S(π)` runs over one `p_ref` per
  OQ-8 ranking — say whether it is taken per ranking or over rankings (the latter picks a
  ranking per cell, which no deployable agent can do).
- m12 — §3.2 — "Jeffreys' excess log-loss is 18.65 nats against `p*`'s 0.51": these are
  `x_1` mismatches `D_KL(m_q‖m_π)` [read: jeffreys_vs_pstar.py docstring], not §2.1's
  excess over the oracle, which is at least `I_q` (about 2.5 nats on this nature) —
  relabel.
- m13 — §3.2, assumption 2 — it is called "the precise content" but states no checkable
  condition. One candidate is `E_q b_{p_J} ≥ κ·B(p_J)` with `κ > 0` independent of `D`.
  The condition must fail at `t = 1`, since a prior's bias pressure averages to zero under
  that prior [read: A&M Fig. 4 caption] — state one.
- m14 — §3.4 — "nearly the same prior and nearly the same mutual information [read: Quinn
  §5.1, Fig. 12]" overstates the source: Fig. 12 shows only mutual information, in
  sum-of-exponentials; Quinn's p♯ has full support while `p*` is discrete; and "essentially
  unique" is not in the source. Reason 1 (the `(D/2) log N` asymptotics) is the
  all-resolved regime the spec is far from, and "their one structural difference" omits
  the MLE pushforward — qualify.
- m15 — §3.5, item 2 — the Rosedahl, Serota & Ashby numbers concern human learners, not
  the priors scored, and fail the necessity test in the core — move them to `empirics/` or
  a footnote.
- m16 — §3.6, points 1–2 — "merely re-derives A&M" is wrong: A&M neither tested uniform
  ([^1-uniform]) nor scored a foreign `q` (§0). "`I_{p_J} < C` can let a smooth prior beat
  `p*`" does not follow as written; the operative fact is that `p*`'s per-state redundancy
  is `C_N` on its support, while a near-matched prior pays about `I_q` — rewrite both.
- m17 — §2.1, §2.2, §2.5, §3.4 — under §0's "hereafter *the note*"
  (prediction_objective_for_priors.md), "note §3" (§2.2, twice) and "note §5.3" (§2.5)
  point to sections that do not hold the claims; they are budget-value-of-information.md
  §3 and infomax_two_hats_and_directions.md §5.3. "note §1.2, §4" (§2.1) is ambiguous.
  `redundancy-capacity.md` and `nml-mdl.md` lack their `tutorials/math/` path — fix the
  pointers.
- m18 — [^3-lineage], §2.1, §3.1, §3.4, [^0-motives] — provenance: "not read" is not an
  epistemic tag (use `[recalled]` or `[CITATION NEEDED]`); Topsøe 1979, Kemperman 1974,
  Haussler 1997, Shtarkov 1987, Rissanen 1996 and Grünwald 2007 are untagged; and "would
  remove the bias with no budget at all" (exp-decay) is a `[guess]` stated as fact — tag
  each.

## What the spec gets right

- The prior-dependence of both scores is reduced exactly to a mismatch, of marginals or of
  posterior predictives ((2.1.2), (2.1.6)).
- The per-nature floor is kept apart from the sweep-average ceiling (§2.5).
- (3.1.1) is separated, as the one theorem, from the heuristic, and the cells it settles
  are excluded from the verdict (§3.7).
- The provenance mostly holds. The `[read]` tags I checked against A&M, Quinn, Mattingly,
  Komaki and Fogel & Feder say what is claimed, and the motives table reproduces digit for
  digit from `jeffreys_pull.out`.
- Declaring no winner and testing only the machinery (§2.4) is the right guard; the fixes
  for F1 and F8 should keep it.
