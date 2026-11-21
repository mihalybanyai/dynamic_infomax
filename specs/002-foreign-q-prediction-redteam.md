# Red-team review of specs/002-foreign-q-prediction.md

Reviewer: red-team sub-agent
Reviewer model (declared identity): Claude Opus 5.5
Effort tier: max (set at spawn by the main agent; not verifiable here)
Roster verified: 2026-11-20
Date: 2026-11-20
Spec version: 00c3746 (HEAD; the spec file is unmodified in the working tree)

## Summary

The scoring core holds. The compensation identities (2.1.2) and (2.1.6), the cap (3.1.1),
the mass bound (3.2.1), the insurance inequality (3.2.3) and the derivations of §9 check
out. The `[read: …]` claims I traced to A&M, Mattingly et al., Quinn et al., Komaki and
Fogel & Feder say what the spec says they say. The spec is thinnest at two points: where
it turns the table into a verdict (§3.7), and where it builds the controls meant to make
that verdict non-trivial. The rules for setting cells aside are defined inconsistently
across sections. They are applied to the one-step score, where their justification fails,
and on one reading they declare "supported" in a row that a deployable prior wins. The
rotation knob, the cones' only route to a failing coordinate prior, leaves `p_U` within
0.02 nats of `p_ref`, so the cones read as either refuted by construction or a contest
with Jeffreys alone. Several "fixed" natures are not fixed in data space. The whole cast
exists only on the grid (exp-decay `D ≤ 4`), with cells too coarse for `p*`'s atoms over
much of the σ and `N` sweep. Not ready for test derivation until F1, F2 and the §0.1
mismatches of F3 are settled; F4–F9 can be fixed alongside.

Numbers marked *computed* are the reviewer's own (scripts in the session scratchpad, not
committed). The settings are stated with each number so it can be reproduced.

## Findings

### F1: The rotation knob cannot make `p_U` fail, so the cones' ranking tiers collapse [severity: high]

**Location**: §1.2 (*Rotation* bullet), §3.5 (tier 2, "Computable"), §4.1 (family 2 and
`build_model`), §4.2 (`p_ref` in the cones), §4.3 (hypercone natures), §5.4
(`α ∈ {0, π/8, π/4}`), T15(c), §3.7 (the cones' reading).

**Concern**: The knob rotates the `(θ_1, θ_2)` plane of the box
`Θ = [0, W] × [0, 1]^{D−1}`; `theta_box = cone_box(D, W)` whatever the rotation. Take
`s = (Qθ)_1` as the relevant coordinate. Every slice `{θ ∈ Θ : s = const}` has the same
volume except within `sin α` of the two ends of the `s` range. So `p_U`'s marginal on `s`
is flat apart from end ramps of width 0.38 (π/8) or 0.71 (π/4), both below one Fisher
length at the base σ = 1. Both priors are uniform on each slice.

*Computed* (`W = 50`): KL(`p_ref`‖`p_U`) on `s` is 0.008 nats at π/8 and 0.019 at π/4.
By data processing this also bounds KL(`m_{p_ref}`‖`m_{p_U}`), so their mixtures are
nearly identical. Jeffreys' marginal on `s` is `∝ A(s)|s|^{D−1}`, unchanged in shape.

The consequences:

- Rotation moves no prior between tiers. §3.5's "coordinate priors such as `p_U` inherit
  a tilt" holds only on the ramps, and T15(c) ("`p_U`'s is not [flat]") passes on them
  alone.
- The knob's purpose in the source note, "to make uniform-θ and log-normal genuine
  competitors that also fail" (`notes/prediction_objective_for_priors.md` §6.3), is not
  met. By §1.2's own sentence, every cone result stays "a win over Jeffreys alone".
- §3.7's cone reading is self-contradictory. A loss to `p_ref` is "the expected control
  result", yet "`p*` is read against the other deployable priors". Those include `p_U`,
  which equals `p_ref` at α = 0 (§3.5, T15(b)) and lies within 0.02 nats of it under
  rotation.
  - If `p_U` counts, the cones are refuted by construction. §3.5 already reports from
    the reduced cone that "a prior flat in the relevant coordinate beats `p*_N` on
    natures uniform in it or confined to the thin end".
  - If `p_U` does not count, only `p_J` is left, and its cells are mostly set aside
    (F5).

Two smaller points:

- "In the cone's own coordinates, before any rotation" (§4.3) is ambiguous. If it means
  `Qθ`, the fixed natures leave the model manifold once α exceeds about `2/W` rad,
  because `Q(Θ)` reaches `(Qθ)_2 ≈ θ_1 sin α`.
- `s` ranges over `[−sin α, W cos α]`. The negative end is a mirrored sliver with negative
  taper.

**What would resolve it**:

- Give the cones a coordinate prior that does fail along the relevant direction: either a
  non-linear relevant coordinate (`p_U` uniform in `log θ_1`, as exp-decay's log-rates
  are), or a box whose extent along the rotated relevant direction is comparable to its
  cross-section.
- Pre-state a minimum KL(`p_ref`‖`p_U`) of several nats, and assert it in T15(c).
- State whether `p_U` enters the cones' verdict.
- State the coordinates in which the hypercone natures live.

> M: the rotation knob, or any kind of coordinate transform on the uniform is not actually useful - it can make the uniform fail tautologically, but we don't care about that. Let's keep the uniform and other coordinate-dependent priors as privileged-information competitors, so they will be good when the true coordinates come with the task description, but we note that they can be arbitrarily bad when thy don't. Simplifying the spec wherever possible is good anyways. 

> C: Agreed. The rotation knob is dropped (§1.2, §4.1, §4.2, §4.3, P13, P15, T13(d),
> T15(c), §5.4, §6.3). The cones then have no computable-ranking case, so §3.5 keeps the
> handed-over case (the cones) and the unavailable one (exp-decay), and names the
> computable case in one line as not run. `p_U`, `p_LN` and `p_ref` are recast as
> privileged-information priors: good when the task supplies the coordinates or the
> ranking, arbitrarily bad when it does not. No coordinate transform is used to make them
> fail (§1.2, §2.2, §3.2, §3.5). §3.7 reads the cones against Jeffreys, with
> `p_U = p_ref` as a reference point (see F3(b)). To apply in the spec (Stage 3b).

---

### F2: The ½-nat "at home" rule makes the §3.7 verdict ill-defined, and on one reading wrong [severity: high]

**Location**: §2.3 (*Stress natures*: "a win at a mismatch below ½ nat is a home win and
is not counted"); §2.4 (Δ_S: "In a deployable prior's own world that prior is left out of
the minimum"); §2.5 ("Near home"); §3.7 (*Home wins*; "beats every deployable prior that
is away"); §4.5 (the marks, "on that score"); §6.3 (`gap_best`, "over the deployable
priors other than the row's own").

**Concern**:

(a) *Two comparison sets.* §2.4 and §6.3 drop only the row's own prior from Δ_S's minimum.
§3.7 calls every prior with mismatch below ½ nat "at home", and compares `p*` only with
the deployable priors "that are away". Illustration: a fixed-spectrum row with `p_LN` at
0.4 nats, `p*` at 1.0 and `p_ref` at 1.5. Under §3.7 this row is "supported"; under §2.4
and §6.3, Δ_S(`p*`) = +0.6, "refuted". The §3.7 reading declares support in a row where a
deployable prior predicts better than `p*`.

(b) *Non-monotone in `p*`'s quality.* A row in which `p*` itself comes within ½ nat of
nature cannot count for it, however large the competitors' losses. The threshold is
applied to point estimates with no Monte-Carlo band. The spec's own preview has `p*` at
0.51 nats on the cone's uniform nature (`notes/budget-value-of-information.md` §4).

(c) *The one-step score.* §4.5 applies the rule "on that score", that is, to `r_N` as
well. The justification, that ½ nat is the KL between two `N`-fold predictions one Fisher
length apart, holds for `R_N`. For `x′` (one observation at noise σ) the same offset costs
`1/(2N)` nats. The one-step mismatch is the per-observation increment of the cumulative
mismatch (fn. `[^2-onestep]`), and it shrinks with `N`.

*Computed* in the reduced cone (relevant datum, `D = 26`, `W = 50`, σ = 1). This setup
reproduces the note's cumulative 18.65 and 20.98 to within 0.04.

| Nature | Jeffreys' cumulative mismatch | Jeffreys' one-step mismatch |
|---|---|---|
| uniform | 18.6–20.9 nats over `N = 1–16` | 0.89, 0.40, 0.24, 0.064 nats at `N = 1, 2, 3, 8` |
| thin end | 58 nats at `N = 8` | 0.29 nats at `N = 8` |

So for `N ≥ 2`, Jeffreys is "at home" on `r_N` in a row where it is 20 nats away, and
`p_lat`'s home-score verdict consists mostly of set-aside cells.

(d) *Relatives' worlds.* "Near home" is defined only by the threshold. The round robin
includes worlds built by `p*`'s own construction at other budgets (`p*_{N/10}`,
`p*_{10N}`), and worlds of priors with the same objective or approximating `p*` (`p_lat`,
`p_proj`, `p_LN^*`). None is "chosen independently of the agent's prior", which is §0.2's
definition of foreign, yet §3.7's round-robin verdict counts them.

**What would resolve it**:

- Define "at home" structurally: the diagonal plus each prior's declared relatives. Use
  the same comparison set in §2.4, §3.7 and §6.3.
- If a proximity rule stays, make it "this row is not a test when its best prior is within
  the threshold" rather than "drop that prior from the minimum". Require the
  classification to hold beyond Monte-Carlo error.
- Derive a separate threshold for `r_N`, or drop the rule there.
- Report the round-robin verdict separately for the worlds of deployable priors and for
  the worlds of budget-dependent relatives.

> M: drop any thresholding everywhere. for each prior, report a heatmap where axes are breadth and best rival's mismatch, as per the chat about this. This would be in addition to the full result matrix, as a visual aid to draw conclusions. Again, simplicity is good.

> C: Agreed (chat). Every threshold goes, the ½-nat home rule included (§2.3, §2.5,
> §3.7, §4.5, T22(a), `at_home` in §6.3); (c) is resolved by dropping it on both scores.
> One comparison set throughout, §2.4's: only the row's own prior is left out. The worlds
> of `p*`'s relatives (`p*_{N/10}`, `p*_{10N}`, `p_lat`, `p_proj`, `p_LN^*`) are reported
> as a group of their own (d). New figure in §6.1, beside the full table: per prior and
> score, one point per row at breadth `I_q/C_N` against the best rival's mismatch (the
> smallest mismatch among the other priors away in that row), coloured by the prior's
> signed gap to that rival; each fixed nature's points joined into a track across `D`;
> relatives' worlds marked. To apply in the spec (Stage 3b).

---

### F3: The body and the §0.1 human summary disagree on five points [severity: medium]

**Location**: §0.1 against §0.2, §3.2 (*Scope*), §3.5, §3.6 point 5 and §3.7.

**Concern**: Where each side stands (no wording proposed for §0.1):

(a) *Belief prior.* §0.1's last point: note whether *any* budget-conscious prior seems
reasonable "as a belief prior" in a novel scenario. Body:

- §0.2 says the spec is "not 'is `p*` a good epistemic prior'".
- §3.7 states a verdict for `p*` (and `p_lat`) only, and counts `p*`'s lead as supported
  only if `p_proj`, `p_lat` and `p_LN^*` do *not* share it. A shared lead, which §0.1
  would read as evidence for budget-consciousness, weakens the body's case for `p*`.
- No verdict is defined for the principle.

> M: yeah, this is a bit all over the place, reflecting different stages of the spec's development. However, saying that it's not about p* being a good epistemic prior is flat out wrong, as the fact that with privileged information (knowing how to match nature's mixture in advance) it can be beaten is uninteresting - the question is exactly if it's a good deployable epistemic prior in complex/realistic enough problems or not. And indeed not all of the text agrees about the importance of other budget-conscious priors, I see the goal of the spec being primarily about assessing p*, and secondarily about assessing the budget principle. All text should be easy enough to smooth out this way.

> C: Agreed; the body changes and §0.1 stands. §0.2 drops "not 'is `p*` a good epistemic
> prior'": the question is whether `p*` is a good deployable belief prior in problems
> where privileged information is unavailable. The aims are stated once, in §0.2 and the
> §2 opening: first `p*`, then the budget principle. §3.7 gives a verdict per
> budget-conscious prior, `p*` first. A lead that several of them share counts for the
> principle, and the pairwise gaps decide whether it is `p*`'s own (§2.4, §3.6 point 2,
> §3.7). To apply in the spec (Stage 3b).

(b) *Constructing uniform and reference priors.* §0.1 point 4: in complex scenarios a
uniform or reference prior "is not in general possible to construct, at least not in a
parametrisation-independent way". Body:

- `p_U` is built on every model. `p_ref` is built in closed form in the cones and once
  per ranking in exp-decay.
- The obstacle the body names is an unavailable ranking (§3.5), not parametrisation
  dependence.
- §3.2 says "No case is made against `p_U` or `p_ref`".
- `p_U`'s parametrisation is never varied in exp-decay (log-rates only), and the cones'
  rotation does not vary it in effect (F1).

  > M: again, the text may be a bit all over the place, but p_U is constructible in the sense that you can construct any mathematical object by saying it's the number 4, and not caring if it doesn't end up being that. What 3.2 is trying to say is that p_U and p_ref are privileged-information priors, so they are just points of reference (ha), instead of equal-footing competitors. The wording could be smoother I guess. And the practical side of this is resolved by the resolution of F1.

  > C: Agreed; the body changes. §2.2, §3.2 and §3.5 describe `p_U`, `p_LN` and `p_ref` as
  > privileged-information priors, which take their coordinates or ranking from the task:
  > reference points, not equal-footing competitors. F1 removes the coordinate
  > transforms. MB accepted in chat ("Yes, all"): §2.4's gap splits into the gap to
  > Jeffreys, the one deployable prior that needs nothing beyond the likelihood, on which
  > the verdict of §3.7 rests, and the gap to the best privileged-information prior,
  > reported as what the task's coordinates or ranking would buy (§2.4, §3.7, §6.3).
  > To apply in the spec (Stage 3b).

(c) *RL and Bayesian inference.* §0.1 point 2: no principle "is offered by either RL or
Bayesian inference". Body: the ranked reference prior, a Bayesian construction, is
presented as a budget-free route that may "do the job" (§3.5, §3.6 point 5). RL does not
appear in the body.

> M: ok that's weird, the reference prior is not a Bayesian construction but an information-theoretic one, innit?

> C: Chat. Explained: both. The reference prior maximises the information the data give
> about `θ`, in the limit of infinitely many repetitions [read: Bernardo 2005, preprint
> pp. 15–16]: an information-theoretic criterion, proposed within Bayesian statistics
> because coherence alone does not fix the prior. It is `p*`'s criterion at infinite
> budget, plus a ranking, so it does not contradict §0.1 point 2. MB accepted ("Yes,
> all"): §3.5 states this in its core text, not only in `[^3-lineage]`; RL stays in §0.1.
> To apply in the spec (Stage 3b).

(d) *Betting.* §0.1 point 1 names Kelly betting games. Outside §0.1, betting appears only
in references to spec 001; the body never states log-loss's link to betting.

> M: reworded 0.1 slightly, not elaborating on the connection to betting is fine otherwise, but maybe it's worth a footnote

> C: Agreed. A footnote at the first use of `R_N` (§2.1) states the link: under log-loss,
> `R_N` is the shortfall in log-wealth of a Kelly bettor who bets with `m_π` against one
> who knows `θ` [recalled: Cover & Thomas, ch. 6; spec 001]. MB's rewording of §0.1
> point 1 is in the working tree. To apply in the spec (Stage 3b).

(e) *A body point missing from §0.1.* The "decisive comparison" is `p*` against `p_ref`
under at least two rankings in exp-decay, with the cones as a control in which ranking is
free (§3.5, §3.7).

> M: yeah in the light of everything above we definitely shouldn't say this is the decisive comparison. 

> C: Agreed. "Decisive comparison" goes wherever it appears (§3.5, §3.7 and elsewhere).
> `p*` against `p_ref` is one comparison among the others, against a
> privileged-information reference point (F3(b)). To apply in the spec (Stage 3b).

**What would resolve it**: The human decides which side changes. Work that depends on (a),
such as a verdict for budget-consciousness as a principle, waits for that decision.

---

### F4: Most "fixed" natures are not fixed in data space, so question 3 is not isolated [severity: medium]

**Location**: §2.3 (question 3, "while nature stays fixed"; *Fixed natures*;
`[^2-fixed]`); §4.3; §3.7 (*Fixed natures*); §6.1 (`spectrum_width.png`).

**Concern**:

(a) *Cones.* `D` is also the data dimension (`y ∈ ℝ^D`), so a cone nature generates data
in every added coordinate, and its floor and data law change with `D`. In the base cell
the added coordinates are sub-resolution. In the σ < 1 and `N > 1` cells, the
cross-section is resolved beyond `θ_1 = Wσ/√N` (§1.2), and each added coordinate carries
information about nature's state. A Gaussian-input bound gives up to 0.42 nats per
coordinate at the base for σ/√N = 0.25 (reviewer's estimate).

(b) *Fixed spectrum, discretisation.* Placing the rates at quantiles makes the data law
depend on `D`. *Computed* at `c = 0.8`, `w = 1`, σ = 0.1, one observation:
`‖y_D − y_26‖/σ` is 0.95, 0.50 and 0.31 at `D = 2, 3, 4` (×√N at budget `N`).

(c) *Fixed spectrum, clipping.* *Computed* over the stated laws of `c` and `w`, clipping
to the box puts on average 28% of the rates on the faces of the matched box (45% at
`w = 1`, 70% at `w = 2`), and 33% in the wide box at `w = 2`. Clipped rates coincide, so
the large-`w` end is an edge nature. "At large `w` it is the bulk kind" (§4.3,
`[^2-fixed]`, OQ-2) is false, and `spectrum_width.png`'s run from edge to bulk folds back.

(d) *Few rates.* This is the only row whose data law is exactly `D`-free. On it §3.7
counts only the trend, because "a level lead is expected there from the geometry". The
same geometry predicts the trend:

- Each added component adds a direction in which the `D_0 = 1` nature sits on a face of
  the ordered `Θ`.
- `p*` keeps atoms there.
- Smooth priors' mass within resolution of that face shrinks with `D` [guess: settled by
  computing `−log π(A(θ))` on that row for `p_U` and `p_J` across `D`].

**What would resolve it**:

- Ask question 3 only of natures whose data law does not depend on `D`: few rates with
  `D_0 | D`, and spectra built as exact `D_0`-rate mixtures. Otherwise report each fixed
  nature's own drift, KL(`m_q^{(D)}`‖`m_q^{(D′)}`), beside the trends.
- Take quantiles of the law truncated to the box, or limit `c` and `w` so that clipping
  is negligible, and record the clipped fraction per draw.
- State what the few-rates trend can show, given (d).

> M: rewrite it in such a way that there are a lot of unresolvable dims to begin with (also unresolvable together), and all models receive privileged info about which to ignore, and as this privileged info is supplied less, they get worse (or not), and the underlying nature doesn't change. Fixed spectrum can be left out of this.

> C: Agreed (chat). Question 3 is rebuilt on nested models (§2.3, §4.3, §5, §6). Nature
> lives once in the largest model, `D_max = 26`, with one fixed law. The agent's model
> frees the first `D` directions and fixes the rest at a reference value, so less
> privileged information means larger `D`; the data space, the oracle and the floor never
> change. The ignored directions must be jointly irrelevant, `Σ_{μ>D} L_μ² ≪ 1`, so in
> the hypercone question 3 runs at fall-off `φ < 1`. Each curve is shown beside the
> submodel's own floor: an oracle that knows `θ` but fixes the ignored directions. In
> exp-decay the few-rates nature is already nested: every model with `D ≥ D_0`
> components represents it exactly, and `D_0` is the privileged information. The fixed
> spectrum leaves the spec (MB accepted in chat, "Yes, all"), so (b) and (c) lapse; its
> bulk role is filled by `p_U`'s and `p_LN`'s own worlds. To apply in the spec (Stage 3b).

---

### F5: "Settled by theorem" sets aside the empirical fact the theorem needs [severity: medium]

**Location**: §2.3 (*Reading the table*), §3.7 (*Cells settled by theorem*), §4.5, T22(b).

**Concern**:

- (3.1.1) gives only the implication: if `R_N^q(π) > C_N`, then `p*` wins. Whether a
  deployable prior exceeds `C_N` in a row is the co-volume result the spec measures. It
  is also where the insurance that §3.6 point 4 calls "`p*`'s case" pays out.
- For the verdict, which uses the best deployable prior, the rule bites in rows where
  every away deployable prior exceeds `C_N`, that is, where transfer is strongest.
- Every off-diagonal cell of `p*`'s own world is settled, since there `R = C_N +` the
  mismatch. Yet §3.7's round-robin verdict uses "the exchange with each deployable prior",
  which needs exactly those cells.
- *Computed* in the reduced cone at `D = 26`, `N = 1`: Jeffreys exceeds `C_N = 4.02` on
  the uniform row (mismatch 18.6) and on the thick half (mismatch 4.87 plus a floor of
  about 1.8, about 6.7 nats; relevant datum only). Only its own corner stays live. If
  `p_U` is left out (F1), the cone verdict against Jeffreys is confined to that corner.
- The marks compare a point estimate with the grid's `C_N`. That is the capacity of the
  grid-restricted channel, not of `Θ`, and the grid `p*`'s per-state redundancy off the
  grid can exceed it (F9).

**What would resolve it**:

- Report settled rows under their own label, as evidence for the insurance reading.
  Exclude them only from claims about an average-case lead within the cap.
- State that the exchange uses all cells.
- Mark a cell settled only when `R − C_N` exceeds its Monte-Carlo error plus the grid's
  capacity gap (the maximum of `R_N^θ(p*) − C_N` over off-grid states).

> M: yes: do not exclude cells, also as per F2, labeling them as theorem-driven is a good idea, they can show up on the results that way (also as per the chat about this). Inclusion of the MC error is a good idea

> C: Agreed (chat). No cell is set aside (§2.3, §3.7, §4.5, T22(b)). A cell where a
> prior's redundancy exceeds `C_N` is labelled "beyond the cap": `p*`'s win there is
> guaranteed by (3.1.1), and the size of the loss is the finding. Such cells sit above
> the line `C_N(1 − x)` on F2's map. A claim that `p*` leads within the cap is stated over
> the other cells, and the exchange uses every cell. The label requires `R − C_N` to
> exceed its Monte-Carlo error plus the capacity gap of the candidate set (the largest
> `R_N^θ(p*) − C_N` over states off it). To apply in the spec (Stage 3b).

---

### F6: The `p_proj`-adversarial corner runs outside hyperribbon geometry [severity: medium]

**Location**: §3.4 (*Where they part*: "both reachable by tuning the hyperribbon … with
no new model"), §4.1 (curvature knob), §5.4 (curvature cells at σ = 0.1, `W = 5`).

**Concern**:

- The warped ball (`ρ = 5σ_eff`) must lie inside the base face, which is 1 wide. So
  `σ_eff ≤ 0.2`, and each cross-section direction at the base is at least 5 Fisher
  lengths wide.
- In the chosen cells it is 10, and the cross-section is resolved beyond `θ_1 = 0.5` of 5.
  Over 90% of its axis the model has no sloppy direction.
- So `p*` against `p_proj`, which §0.2 calls "the sharpest question", is measured at the
  vertex of a regular model, not in the geometry that §3.4 says makes it reachable.

**What would resolve it**: Restate §3.4's claim for the cells as run. Alternatively, put
the warp where the cross-section is sub-resolution: a smaller ρ with a stated halo
argument, or fall-off `φ < 1` so that only the first cross-section direction is resolved.

> M: well it is a question, if it's the sharpest, I'm not sure. p_proj is a conceptual cousin of p*, so deciding between the two is interesting, but as empiricism is so hard to begin with, not the most pressing maybe. But we should be as consistent as we can nevertheless, but I don't quite understand the proposed solution here. Can't we just choose a parametrisation that works better?

> C: Chat. Explained: a reparametrisation moves neither `p*` nor `p_proj`; the geometry
> has to change. The vertex must be visible to the data, with the faces that meet there
> wider than the noise, while the other directions stay sloppy. MB accepted ("Yes,
> all"): the curvature cells run at fall-off `φ = 0.05` besides `σ = 0.1` and `W = 5`.
> The first cross-section direction is then resolved (about 10 Fisher lengths at the
> base) and holds the vertex, while the rest stay jointly irrelevant (`Σ L_μ² ≈ 0.25`,
> about 0.03 nats). §3.4's claim is restated for these cells (§3.4, §4.1, §5.4), and
> §0.2's "the sharpest question" becomes a plainer description of `p_proj` as `p*`'s
> conceptual cousin. To apply in the spec (Stage 3b).

---

### F7: In exp-decay, `p_ref` keeps conditional Jeffreys on the unranked rates [severity: medium]

**Location**: §3.5 (the ordering route; "Their volume therefore never tilts it");
`[^3-schur]`; §4.2 (`p_ref` in exp-decay: "the ranked quantity as the relevant coordinate
and the other rates as the rest").

**Concern**:

- The two-group Berger–Bernardo formula gives the rest the conditional Jeffreys density
  `j(θ_⊥|θ_1)`.
- In the cones `j` is uniform, because `√det g_⊥⊥ ∝ r^{D−1}` is constant on the
  cross-section.
- In exp-decay the rest is itself a sloppy block of `D − 1` rates. There `j` is Jeffreys
  on that block: the measure whose co-volume bias the spec tests. A&M report bias pressure
  of about 10 bits already in a 2-D exp-decay model [read: A&M §2.1, Fig. 1].
- At `D = 3` and `D = 4`, `p_ref` therefore takes the ordering route for one coordinate
  only. The "decisive comparison" (§3.5, §3.7) pits `p*` against a prior that is partly
  Jeffreys.

**What would resolve it**: Rank every rate, as a one-at-a-time sequential reference prior
in which each conditional is a 1-D reference prior [recalled: Berger & Bernardo's
ordered-group construction; settled by reading Berger, Bernardo & Sun 2009 on several
groups]. Otherwise, state that the two-group version keeps conditional-Jeffreys bias in
the rest, and read `δR(p*, p_ref)` with that in mind.

> M: again, calling this the decisive comparison is a relic of the past, should be removed. Otherwise, this does not seem to be a problem really? Why is it bad that p_ref shares a lot with p_J here? Stating it is of course good.

> C: Agreed. "Decisive" goes (F3(e)). Otherwise no defect: §3.5 and §4.2 state that in
> exp-decay the two-group `p_ref` ranks one order statistic and keeps conditional
> Jeffreys on the other rates, so `δR(p*, p_ref)` compares `p*` with a prior that is
> partly Jeffreys. No sequential construction. To apply in the spec (Stage 3b).

---

### F8: The wide box's slow face is a resolvable artificial edge [severity: medium]

**Location**: §4.1 ("so a rate can leave the window on either side"), OQ-9, §4.2
(`p_proj`, MLE "within `Θ`").

**Concern**: *Computed* at σ = 0.1, `N = 1`, holding the other rates fixed:

| Face of the wide box | Distance to the natural edge, in noise units |
|---|---|
| slow, `θ = 3` (decay time 20), to `k → 0` | `7.5/D`: 7.5, 3.7, 1.9 at `D = 1, 2, 4`; more at the sweep's smaller `σ_eff` |
| slow, all rates at `θ = 3`, to "never gives way" | 7.5 at every `D` |
| fast, `θ = −1` | `0.87/D` |

So on the slow side the box face, not the window, makes the edge. This has three
consequences:

- §0's "honest" corner is outside the model.
- `p*` and `p_proj` will put atoms and point masses on an artificial face.
- The matched-versus-wide control (OQ-9) does not isolate rates that leave the window.

**What would resolve it**: Extend the slow side until its face is well below one noise
unit from `k = 0` at the sweep's smallest `σ_eff`. For one component that means
`θ_max ≈ 6.3` at `σ_eff = 0.1` and `θ_max ≈ 7.3` at 0.035 (reviewer's estimate, from
`‖k·t‖/σ_eff ≤ 0.3`). Alternatively, use A&M's compact coordinate
`φ_μ = e^{−k_μ} ∈ [0, 1]` [read: A&M App. A.5].

> M: both solutions seem fine to me. We previously decided against A&M's construction here, and I'm not actually sure why.

> C: Chat. Explained: OQ-9 set aside the unbounded range because uniform in log-rate is
> improper on `ℝ^D` and a grid needs a cut-off anyway. After F1 neither holds: `p_U` can
> be uniform in A&M's compact coordinate `φ_μ = e^{−k_μ} ∈ [0, 1]`, where it is proper
> (an exponential law on each rate, `k ∼ Exp(1)`), and candidate sets on `[0, 1]^D` need
> no cut-off. MB accepted ("Yes, all"): exp-decay's `Θ` is the ordered part of
> `[0, 1]^D` in `φ` (written `ξ` in the spec, where `φ` is the fall-off), so the box is the whole manifold and has no artificial faces at any
> `σ_eff`. `p_U` is uniform in `φ`; `p_LN` stays A&M's normal law in `θ` on `ℝ`; the
> matched-box control becomes the window's range in `φ`, `[e^{−1}, e^{−1/5}]`; §5.5's
> bridge to AtomicPriors.jl, whose `yexp` already uses `e^{−k}` on `[0, 1]`, needs no
> change of variables (§1.1, §1.2, §4.1, §4.2, §4.3, §5.5, OQ-9, and the geometry
> figure's panel (d)). Jeffreys' normalisability on the whole manifold stays a `[guess]`,
> checked by T4. To apply in the spec (Stage 3b).

---

### F9: The full cast, at adequate resolution, exists only in a corner of the sweep [severity: medium]

**Location**: §4.2 (construction of `p_lat`, `p_ref` and `p_J`); §5.4 (*Dimension*,
*Grid resolution*); §5.5 ("`p_lat` has no fixture"); §2.4 (Δ_S over
`{p_J, p_U, p_LN, p_ref}`).

**Concern**:

(a) *Cast.*

- `p_lat` is grid-only, since AtomicPriors.jl "has no conditional objective". So is
  `p_ref` in exp-decay (quadrature on the ordered grid).
- `p_J` is "normalised over `Θ` by quadrature". Beyond `D ≈ 12` its determinant needs
  more than double precision (§0's own footnote; A&M App. A.5). AtomicPriors.jl's BigFloat
  and Vandermonde routines (`src/mod/ymap.jl`) are not used.
- So the whole cast exists only on the grid, which in exp-decay means `D ≤ 4`. The
  decisive comparison against `p_ref` runs at `D ∈ {2, 3, 4}`, the range A&M's scores
  still prefer (`d ≤ 3`) [read: A&M §3], not the high-`D` regime of the title.
- Nothing says how Δ_S, the round robin and `q̄` are formed when `p_ref` or `p_lat` is
  missing. Dropping `p_ref` from Δ_S's minimum above `D = 4` shifts `p*`'s gap in its
  favour exactly where the trend in `D` is read.

(b) *Resolution.* "`G` well above `√N` resolves `p*`'s atom spacing" is spec 000's
Bernoulli rule. *Computed* along the stiffest direction at σ = 0.1 (median to 90th
percentile over uniform ordered `θ`), the exp-decay cells span:

| `D` | `G` | Cell width in Fisher lengths |
|---|---|---|
| 2 | 50 | 0.69–0.88 |
| 3 | 30 | 0.93–1.14 |
| 4 | 20 | 1.19–1.45 |

These widths double at σ = 0.05 and grow 2.8-fold at `N = 8`. Compare an atom spacing of
about 2.5, and §5.4's own hypercone rule of five cells per spacing (0.5 Fisher lengths
per cell). The hypercone grid keeps two cells per cross-section axis only up to `D ≈ 14`
(`100·2^{D−1} < 10^6`). T3 checks the equalizer on grid cells only.

**What would resolve it**:

- Add a table of which priors are built for which (model, `D`). Define Δ_S, the round
  robin and `q̄` on the cast common to each `D`.
- Set `G` per cell from a Fisher-length rule: at most 0.5 per cell along the stiffest
  direction at that cell's `σ_eff`. Where that is infeasible, route the cell to the atomic
  path.
- Evaluate T3 at off-grid states.
- Route Jeffreys through extended precision, or cap its `D`.

> M: let's do these

> C: Agreed (chat). (1) A coverage table in §4 says which priors are built for which
> model and `D`. §2.4's gaps, the round robin and `q̄` are formed on the cast common to
> each `D`, and each trend in `D` is shown twice: with the full cast up to `D = 4`, and
> with the cast present at every `D`. (2) The priors built by Blahut–Arimoto use a
> candidate set placed by Fisher distance instead of the uniform grid: spacing at most 0.5
> Fisher lengths at the cell's `σ_eff`, from AtomicPriors.jl's `mitchell` sampler seeded
> with the faces of `Θ`. Where that is infeasible, the cell goes to the atomic path. (3)
> T3 checks the equalizer at states off the candidate set. (4) Jeffreys uses
> AtomicPriors.jl's extended-precision or near-Vandermonde routines (`src/mod/ymap.jl`).
> `p_lat` goes beyond the grid only if AtomicPriors.jl gains its conditional objective;
> otherwise the table says where it stops. To apply in the spec (Stage 3b).

## Minor

- m1 — §0.2 against the §2 opening — §0 names `p_proj` and `p_lat` beside `p*` but never `p_LN^*`, which §2 counts as the fourth budget-dependent protagonist — §0 is `reviewed`, so this is for the human's next pass.

> M: add it

> C: Agreed. §0.2 names `p_LN^*` with the other budget-conscious priors. To apply in the spec (Stage 3b).

- m2 — `[^0-matched]`, §1.2 (*Ordered rates*, pull saturation, *Fall-off*), the §2.2 table (`p_proj`), `[^2-fixed]`, `[^3-slab]`, §3.4 item 1 — the `[read: …]` tags cite `redteam-conc04`, a review that red-teams may not open. The underlying sources do say what is claimed: A&M Fig. 1 caption; Mattingly p. 1763, fn. ∥; A&M App. A.1; Quinn §5.2 ("zero-dimensional points usually have finite weight"); `cone_pstar.out` (3.75) — cite them directly, and show `[^0-matched]`'s deconvolution argument or tag it `[recalled]`.

> M: cite directly

> C: Agreed. Each tag cites the original source, after checking that it says what is
> claimed; `[^0-matched]`'s argument is shown or tagged `[recalled]`. To apply in the spec (Stage 3b).

- m3 — §2.2, *Too coarse* — "4.4 nats at budget 16" comes from the reduced cone at σ = 1, `N = 16`, where §1.2 says the cross-section is resolved beyond `W/4` and the reduced model ignores what those data say about `θ_1` (note §3.3, *Limits*) — flag the number as outside the reduced model's range, or recompute it.

> M: can we recompute it?

> C: Chat. MB accepted ("Yes, all") a re-run with `σ = 8` and `W = 400`. Not applied in
> Stage 3b. On reading the note's script (`cone_misbudget.py`), that scaling keeps the
> cross-section below resolution at every budget, so no direction crosses resolution
> between budgets 1 and 16, and the effect the number measures vanishes by construction:
> the re-run would not recompute it. The number is the reduced model's `4.82` minus the
> hidden coordinates' own score, `0.39` (`cone_misbudget_full.py`). Raised again with MB;
> open.

- m4 — §2.2, mixing bound — "at most `log(1/w_k)` worse … on every nature" holds for `R_N`, not for `r_N` — add "on `R_N`".

> M: yes

> C: Agreed. §2.2 adds "on `R_N`". To apply in the spec (Stage 3b).

- m5 — §3.3 — "exact … in the limit where `y(θ)` is linear and the prior flat over the posterior's extent": in that limit both posteriors coincide and the mismatch is zero — call the split a heuristic wherever the mismatch is non-zero.

> M: isn't it already applied by saying it's not exact there?

> C: Chat. Explained: the text implies exactness for smooth priors, but in the limit it
> names any two such priors give the same predictive, so there is nothing to split. MB
> accepted ("Yes, all"): §3.3 says the split is exact for a linear model with Gaussian
> prior and nature, which the cast does not contain, and a heuristic for every prior here.
> To apply in the spec (Stage 3b).

- m6 — §1.1 and §3.2 against §9.4 — `A(θ)` is described as "within one Fisher length", and §1.1 defines Fisher length as a path length `∫ds`, but §9.4 uses Euclidean distance in prediction space — use §9.4's wording throughout.

> M: why is that wording better?

> C: Chat. Explained: the bound needs predictions close in data space, since two
> predictions differ in KL by `N‖Δy‖²/(2σ²)`, a straight-line distance; a Fisher length
> is a path length along the manifold, never shorter, which gives a looser bound and, on
> a folded manifold, misses states whose predictions are close. MB accepted ("Yes,
> all"): §1.1, §3.2 and §4.5 use §9.4's wording. To apply in the spec (Stage 3b).

- m7 — `[^4-stiff]` — "stiffest" is an eigenvector of the coordinate matrix `g(θ)`, so it depends on the Euclidean structure of `θ` (log-rates) and is undefined where the top eigenvalues cross — state it as a choice.

> M: yeah ok

> C: Agreed. `[^4-stiff]` states that "stiffest" depends on the Euclidean structure of
> the log-rate coordinates and is undefined where the top eigenvalues cross: a choice, and
> a coordinate-dependent ranking. To apply in the spec (Stage 3b).

- m8 — §4.2 (`p_proj`) and T12(e) — the experiment uses the boxed port (MLE within `Θ`), but T12(e) checks only the unboxed one — add a check of the boxed port (see also F8).

> M: add it

> C: Agreed; resolved through F8. With A&M's compact coordinate the box is the whole
> manifold, so the boxed and unboxed ports coincide and T12(e) covers both. T12 also
> checks that two independent chains give the same cloud in a two-sample test.
> To apply in the spec (Stage 3b).

- m9 — T2 — "`R(p_J) − R(p_U) = 0` exactly" cannot hold when `p_J` is normalised by quadrature — state a tolerance.

> M: of course nothing ever is zero numerically - choose a reasonable tolaerance

> C: Agreed. T2 asserts `|R(p_J) − R(p_U)| ≤ 10^{-6}` nats under common random numbers,
> about ten times the error of the normalising quadrature (auto-chosen; please confirm).
> To apply in the spec (Stage 3b).

- m10 — T6 — "within `3(D−1)²/x_1³`, about 0.6 at `D = 26`": `3(D−1)²/x_1³ = 1.875`, and 0.6 is `(D−1)²/x_1³`. *Computed*: |mean deviation − `(D−1)/x_1`| = 0.418, 0.077 and 0.019 at `D = 26, 11, 6` — pick one tolerance.

> M: which is the principled pick here?

> C: Chat. Explained: `(D−1)²/x_1³`, the first term the expansion neglects; the mode's
> exact root has exactly `−(D−1)²/x_1³` as its next term. Claude checked the reviewer's
> deviations by quadrature: 0.019, 0.077 and 0.418 at `D = 6, 11, 26`, against bounds of
> 0.025, 0.1 and 0.625. MB accepted ("Yes, all"): T6 uses that tolerance. To apply in the spec (Stage 3b).

- m11 — T11 — asserts that `I_{p_proj}` "tracks" `I_{p*}`, a literature result on `ℝ^D` (Quinn Fig. 12), with no tolerance and on the box — give a tolerance and a box caveat, or move it to the report.

> M: does checking a monotonic relationship only make sense here?

> C: Chat. Explained: what holds by theorem is `I_{p_proj} ≤ I_{p*} = C_N`; "tracks
> `I_{p*}`, far above Jeffreys" is a published result on `ℝ^D` (Quinn Fig. 12). MB
> accepted ("Yes, all"): T11 asserts the inequality, and the tracking moves to the
> report's A&M reproduction figure. To apply in the spec (Stage 3b).

- m12 — T19(c) — "equality only at `M = N`" fails if two budgets both lie in the two-atom regime (`L ≲ 3.3`), where `p*_M = p*_N` — pin the channel length; the note's `L = 3` at `N = 1` is safe.

> M: ok

> C: Agreed. T19(c) pins the channel length at `L = 3` Fisher lengths at `N = 1`, as the
> note does, so only `N = 1` lies in the two-atom regime. To apply in the spec (Stage 3b).

- m13 — §5.3, acceptance — "`I_{p_J}` falls" is asserted for `D ∈ {1, …, 4}`, but A&M state only that `p*` is flat "once `d > 3`" and that Jeffreys declines with `d` toward 26 [read: A&M §2.2] — state the expected shape for the `D` actually run.

> M: do we actually know this?

> C: Chat. Explained: no. A&M say `p*` captures the same information "once d > 3" and
> that the scores "prefer models with d ≤ 3" [read: A&M §2.2, text on Fig. 5], so on
> `D ≤ 4` Jeffreys may still be rising. MB accepted ("Yes, all"): on the grid range the
> eye test accepts what holds by theorem, `I_{p*} ≥ I_{p_J}` and `B(p*) ≈ 0 ≤ B(p_J)`;
> the shape (`p*` flat, Jeffreys falling) is accepted only on the range extended toward
> `D = 26` (§5.3). To apply in the spec (Stage 3b).

- m14 — §9.5 — the validity condition `θ_1 ≫ Dσ/√N` fails at both check points (`θ_1 ≈ 41` at `D = 26`; `θ_1 ≈ 43 < D = 100`, where the correction is 2.6 nats) — call the agreement empirical outside the stated range.

> M: I actually have no idea what the significance of this is

> C: Chat. Explained: low. (3.2.2) holds only for `θ_1 ≫ Dσ/√N`, and the check points at
> `D = 26` and `100` violate it, so agreement there is luck rather than a check of the
> derivation, and a mismatch would fail the test for the wrong reason. MB accepted ("Yes,
> all"): T21(c) is asserted at `D ∈ {6, 11}`, and §9.5 reports `D = 26` and `100` as
> observed agreement. To apply in the spec (Stage 3b).

## What the spec gets right

The spec reduces every comparison to a mismatch of marginals or posterior predictives
(2.1.2, 2.1.6), and declares the table, not a winner, to be the result. That is the right
answer to the spec-001 failure, and it should survive every fix. So should the per-cell
marking idea (the rules need fixing, not the idea), the controls (the constant
cross-section of T2, the `q̄` ceiling, the non-negative diagonal of T20) and the insurance
inequality (3.2.3).

Checked and sound:

- the derivations of §2.1, §3.2 and §9, including the second-order term of §9.5;
- the Schur complement `σ^{-2}`;
- the concavity behind `p_lat`;
- T18's Tanaka prior, which satisfies the conditional equalizer: `max_θ f = log(5/4)` on
  `[0, 1]`;
- the A&M, Mattingly, Quinn, Komaki and Fogel & Feder claims, read against the PDFs in
  `resources/`;
- the reduced-cone numbers, which reproduce (18.63 and 20.94 against the note's 18.65 and
  20.98).
