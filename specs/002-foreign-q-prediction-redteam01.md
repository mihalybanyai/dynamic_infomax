# Red-team review of 002-foreign-q-prediction

Reviewer: red-team sub-agent
Reviewer model (declared identity): Claude Fable 5 (claude-fable-5)
Effort tier: Max (human-set; not machine-verified)
Roster verified: 2026-06-11
Date: 2026-06-11
Spec version: fc5677a

Note on provenance: a predecessor run of this same pass was killed before
writing anything; its transcript was salvaged per protocol. Its thinking
content is redacted, so no drafted findings could be recovered verbatim; its
visible leads (a T6 tolerance factor, the §4.5/§5.4 transplants from spec 000,
and how AtomicPriors samples the projected prior) were re-verified
independently here and appear below as F17, F9, and F2 respectively. All
numerical verifications quoted below were re-run in this session.

## Summary

The conceptual layer of this spec (§0–§3, §9) is in good shape: the
redundancy/compensation-identity scoring architecture is correctly derived,
the three-redundancies disambiguation genuinely dissolves the max-vs-min
confusion, the q̄-ceiling logic is right, and the readings of Abbott & Machta
check out in detail — including the spec's claim that A&M's Appendix A.1
carries a sign slip (verified: they write Δ = x − ⟨θ₁⟩ = (d−1)/x while their
own premise forces ⟨θ₁⟩ > x) and its numeric claim that the leading term 2.5
overshoots the true deviation 2.08 (verified by quadrature). The thin layer is
the draft §4–§6 algorithm/test machinery, where the two constructions that
carry the headline are wrong as written: the headline statistic is a min/max
inversion that reduces the falsification structure to "p* beats Jeffreys"
(the exact failure mode §3.5 and OQ-5 disqualify), and the pinned p_proj
sampler does not sample p_proj — it under-weights precisely the boundary
halos that define the co-protagonist, by a factor of ~π, in a way no test in
the suite would catch. Around these sit a cluster of medium gaps — an
undefined curvature knob, unpinned parameter boxes, an unstated exchange
symmetry in the realism model, BA convergence machinery incompatible with an
estimated f_KL, no high-d estimator story for anything except p*, a vacuous
grid-resolution rule, and a deconfounding axis the design note demands but the
spec drops. §0–§3 need only wording-level fixes; §4–§6 need substantive
revision before implementation starts.

## Findings

### F1: The headline statistic is inverted — `min_{π'} ΔR(p*,π')` measures the gap to the WORST competitor, not the best [severity: high]

**Location**: §2.2 (definition), §2.4 (sign-of-advantage screen), §3.6
(falsification), §5.1 headline row, §6.1 `transfer_vs_c.png`, §6.3
`delta_R_best`.

**Concern**: Eq. (2.1.3) defines `ΔR(π,π') = R(π) − R(π')`. The "best
deployable competitor" is the π' with the smallest `R(π')`, so the gap from
`p*` to the best competitor is `R(p*) − min_{π'} R(π') = max_{π'} ΔR(p*,π')`.
The spec instead takes `min_{π'} ΔR(p*,π') = R(p*) − max_{π'} R(π')` — the gap
to the worst competitor — and §6.3 makes the semantics unambiguous:
`delta_R_best = min_{π'∈{p_J,p_U,p_LN,p_proj}} (R[p*] − R[π'])`. Consequence:
the reported "win" condition `min ΔR < 0` is satisfied whenever `p*` beats ANY
single competitor. Jeffreys is in the set and is catastrophic in high d (A&M:
B > 500 bits at d=26), so in the high-d cells the condition holds essentially
always — regardless of whether `p_proj` or `p_LN` beats `p*`. The §2.4 screen
("does the win persist to c→1") and the §3.6 falsification ("refuted if `p*`
ties or loses to the best resolution-adapted prior") cannot detect the
failure they are written to detect; the experiment's headline reduces to
"`p*` beats Jeffreys", which §3.5(2) and OQ-5 explicitly identify as merely
re-deriving A&M. (Secondary: §2.2's competitor set still reads
`{p_J, p_U, p_LN}` while §5.1/§6.1/§6.3 use the four-way set with `p_proj` —
the OQ-5 resolution was not propagated to the defining sentence.)

**What would resolve it**: change to `max_{π'} ΔR(p*,π') < 0` (equivalently
`R(p*) < min_{π'} R(π')`) at all six sites; rename `delta_R_best`
consistently; include `p_proj` in §2.2's set; keep per-competitor ΔR columns
so the report can show which competitor is binding per cell.

---

### F2: §4.2 `build_pproj` does not sample `p_proj` — the convolution sampler under-weights exactly the boundary halos that define the co-protagonist [severity: high]

**Location**: §4.2 (`build_pproj` pseudocode and the bullet "For Gaussian
noise p_NML is a band of width σ_eff around the manifold Y, so the sampler
draws x near Y and projects to its MLE"); §7 OQ-6 (marked RESOLVED); §5.2 T11.

**Concern**: A&M App. A.3 defines `p_proj(θ) = ∫dx p_NML(x) δ(θ − θ̂(x))`,
the MLE pushforward of `x ~ p_NML ∝ max_θ p(x|θ)`. The spec's pinned sampler
draws θ uniform-by-area on Y, adds Gaussian noise, and MLE-projects — i.e. it
pushes forward `Unif(Y) ⊛ N(0, σ_eff²I)`, which is not `p_NML`. The two agree
in the flat interior but diverge at boundaries. Verified in closed form and
numerically for Y = [0,L] (codimension 0): the NML pushforward has endpoint
spikes of mass `σ√(π/2)/(L+σ√(2π))` each, while the convolution sampler gives
`σ/(√(2π)L)` — a factor → π too small (measured ratio 2.81 at L=10, σ=0.5),
plus a depleted half-density boundary layer where the NML pushforward stays
uniform up to the edge; codim-2 corner spikes are off by ~π². The resulting
predictive `log m_{p_proj}(x̄)` at edge-region data shifts by +0.5 to +0.7
nats (measured) — the same order as the ΔR effects the experiment reads.
This lands exactly on the spec's most novel axis: §3.4's corner-1 contrast
("NML over-weights the halo-collecting vertex; p* is unmoved") is the feature
the broken sampler suppresses, so the `pstar_vs_pproj` figure would measure a
strawman. Both primary sources sample `p_NML` directly instead: AtomicPriors
`src/max/sample.jl` ("samples from p^NML(x) using emcee", per-x MLE
optimisation) and Quinn §5.2 ("computed efficiently by sampling pNML(x) using
Monte Carlo methods"). No test catches the discrepancy: T11 checks Z < ∞, the
interior-dominated MI ordering `I_pproj ≈ I_p* ≫ I_pJ`, and MLE recovery from
a synthetic x — none constrains boundary mass — and §5.5's frozen fixtures
(a)–(d) contain no p_proj fixture.

**What would resolve it**: sample `x ~ p_NML` directly (MCMC/emcee with per-x
`min_θ ‖x − y(θ)‖²` as in AtomicPriors; or exact inverse-CDF sampling in the
codim-0 hypercone, where p_NML is uniform-inside + Gaussian-halo), or
importance-reweight the convolution cloud by `p_NML(x)/[Unif(Y)⊛N](x)`; add a
boundary-spike-mass assertion to T11 against the exact 1-D closed form above,
or an AtomicPriors `transtrum` fixture to T12.

---

### F3: The curvature knob — "the one axis on which p* and p_proj provably differ" — is never defined, and nothing is proven [severity: medium]

**Location**: §1.2 ("the one axis on which `p*` and `p_proj` provably
differ"); §4.1.2 (same claim, and `sharpen_vertex(base, curvature)` with no
definition); §5.2 T13; §5.4 (curvature ∈ {moderate, sharp}).

**Concern**: (a) no mathematical definition of the vertex-sharpening map
exists anywhere — not the transform, not which vertex, not what "sharpness"
measures — so the §4.1 families are under-specified, T13 ("the curvature knob
sharpens the named convex vertex") has no testable content, and the §6.1
`pstar_vs_pproj` sweep runs over an undefined axis. (b) "provably differ"
overstates the spec's own §3.4, which derives the corner contrast
heuristically and states "Neither corner's winner is analytic"; no proof that
the two priors differ on this axis, in any quantified sense, is given or
cited. Both gaps sit on the axis that §3.4/§6 present as the spec's most
distinctive measurement.

**What would resolve it**: define the map (e.g. a boundary reparametrisation
with a stated effect on the vertex's exterior solid angle or curvature radius
relative to σ_eff), give numeric values for {moderate, sharp}, and either
prove the halo-mass difference (the codim-0 corner mass is computable in
closed form — cf. F2's spike calculation) or downgrade "provably" to
"structurally expected".

---

### F4: §3.3's "calibration term is O(1), independent of nominal d" is false in the spec's own controlled model [severity: medium]

**Location**: §3.3 ("its calibration term is `O(1)` — bounded, independent of
nominal `d` — and a smooth well-specified prior is the same order. So
calibration modulates ... but does not decide").

**Concern**: the calibration term of (3.3.1) sums per-output-direction costs
`½[1/(1+c_μ) − 1 + log(1+c_μ)]` with `c_μ = Var_post[y_μ]/σ²`. Along an
unresolvable direction of Fisher width ℓ_μ ≤ 1 the posterior keeps ~the full
width: c_μ ≈ ℓ_μ²/4 for p*'s two-corner posterior, ℓ_μ²/12 for a smooth
prior's. The sum is O(1) only if Σ_μ ℓ_μ⁴ converges — true for a geometric
hyperribbon spectrum (exp-decay), false for the hypercone, where all d−1
irrelevant widths are equal (A&M A.1): there the term grows linearly in d
(≈0.29 nats for p* at d=26 with ℓ=1) and the p*-minus-smooth calibration gap
is ≈0.27 nats and Θ(d) — anti-p*, and of the same order as plausible headline
ΔR values in the marginal cells (the interior-q, non-cooperative corner)
where the §2.4 sign is read. "The bias term is what decides the contest" is
therefore unsupported exactly where the controlled model is supposed to make
the contest clean.

**What would resolve it**: state the geometric-spectrum condition
(Σℓ_μ⁴ < ∞) under which the O(1) claim holds; for the hypercone either bound
the p*-vs-smooth calibration gap explicitly (it is computable) or report the
§3.3 split per cell so a calibration-driven sign flip is visible rather than
assumed away.

---

### F5: Model constants that every prior depends on are never pinned — exp-decay parameter box, hypercone L, r0, curvature values [severity: medium]

**Location**: §1.1 ("Θ a compact box (per model, §4.1)"); §4.1 (no box given
for exp-decay; L and r0 symbolic; `parameter_box(family, d)` undefined);
§5.4 (no box, L, or r0 in the sweep; curvature only {moderate, sharp}).

**Concern**: everything except Jeffreys changes with the box: p_U is uniform
on it, p_LN is truncated by it, p* atom counts scale with box/σ_eff, the NML
normaliser Z is finite only because of it (T11 asserts exactly this), and the
§3.1 ceiling C_N is a box property. A&M provide no box to inherit for
exp-decay — they effectively work on θ ∈ ℝ^d, compactifying via
φ = e^(−exp θ) ∈ [0,1] in their App. A.5 — so "per model, §4.1" points at a
choice that was never made. The hypercone's L is used as if pinned (T6 says
"e.g. L=50"; §9.2 quotes A&M's L=50) but is not in §5.4, and r0 for the
control likewise. Every reported number in §6 moves with these choices.

**What would resolve it**: pin (family, d) → box in §4.1 with a stated
rationale (e.g. the box that reproduces A&M's Fig. 5 setting), pin L and r0,
give numeric curvature values, and record all of them in the §6.3 cell key.

---

### F6: Exp-decay's exchange symmetry (a_μ = 1/d) is never mentioned — non-identifiability, d!-fold atom redundancy on the grid, ill-defined MLE projection and atom fixtures [severity: medium]

**Location**: §4.1.1; §4.2 (grid-BA, `mle_project`); §5.5 fixture (b); §6.3
(`pstar_n_atoms`).

**Concern**: with equal weights a_μ = 1/d, y(θ) is invariant under permuting
the θ coordinates. Hence: (i) θ is non-identifiable (every prediction has d!
preimages); (ii) grid-BA on the full box solves the same problem d! times —
the optimal grid prior spreads each effective atom across d! symmetric copies
(24 at d=4), wasting grid resolution and making `pstar_n_atoms` and any
atom-position artefact meaningless without a fundamental-domain convention;
(iii) T12b's "up to label permutation" quotients atom indices but not the
coordinate permutation within each atom — the Julia optimiser and Python
grid-BA can return different sector representatives and fail the fixture
spuriously; (iv) `mle_project` (used by `build_pproj` and the q-family
pullback) must pick among d! minimisers — unspecified, and the choice
determines every θ-space artefact. The score itself depends only on y, so the
headline survives; several specified tests and outputs do not.

**What would resolve it**: state the symmetry; restrict Θ to the sorted
fundamental domain θ_1 ≤ … ≤ θ_d or canonicalise (sort) after every θ-valued
operation; define T12b comparisons after canonicalisation.

---

### F7: Grid-BA keeps spec-000's exact-arithmetic convergence machinery (tol=1e-8, Csiszár gap, "BA is deterministic") on top of an estimated f_KL that cannot support it [severity: medium]

**Location**: §4.2 `build_pstar_gridBA` (`tol=1e-8`, `mc_x=4096`, "A&M App.
A.2 kernel estimate (or MC over x)"); §4.4 "Randomness" ("BA itself is
deterministic"); §5.2 T3.

**Concern**: spec-000's `ba.py` stops on the Csiszár gap with exact
finite-output arithmetic (code default eps_i = 1e-12). Spec 002 injects an
estimated f_KL. (a) The MC option at mc_x = 4096 has a per-cell noise floor of
~0.02–0.05 nats: `tol=1e-8` is unreachable, the fixed-point iteration becomes
an unanalysed stochastic approximation, and "BA itself is deterministic" is
false unless the x-draws are fixed across iterations (unstated; T10's
bit-identical requirement hangs on this). (b) The kernel option (A&M Eq. (A1))
is deterministic but biased — a zeroth-order Taylor expansion with the
σ′ = √2σ patch, which A&M use for L-BFGS *gradients* precisely because MC
fails near the flat optimum — so the BA fixed point shifts by the bias, and
T3's equalizer slack ("up to numerical slack") and T7b's "solver tolerance"
have no stated link to that bias. As written the pseudocode either cannot
converge as specified or converges to a biased object with unquantified
tolerances.

**What would resolve it**: pin the estimator (kernel with σ′ = √2σ), replace
the stopping rule with one compatible with estimation error (relative-MI
change plus gap-above-estimated-bias), state the expected f_KL bias/noise and
derive T3/T7b slacks from it; if MC is kept, fix and seed the x-sample set
across iterations and amend §4.4's determinism claim.

---

### F8: The d > d_switch path specifies an estimator only for p* — m_π for the continuous priors, V_g, and B = max_θ b at d ≈ 26 have no stated method [severity: medium]

**Location**: §4.2 (p_J "normalised over Θ by grid quadrature"); §4.4
("grid quadrature over Θ for small d", Bennett/IS only for far-from-mass x̄);
§5.3 eye test ("extend toward A&M's d ≤ 26"); §7 OQ-1 (delegates only p* to
Julia).

**Concern**: every cell and sample needs `log m_π(x̄)` for p_J, p_U, p_LN, q̄
— a d-dimensional integral whose grid quadrature is impossible beyond the
spec's own d=4 cap (10^6 cells, §5.4) — plus the Jeffreys normaliser V_g (a
d-dim integral of √det g) and the eye-test/T9 quantity B = max_θ b (a global
optimisation with a per-θ KL estimate). A&M's App. A.5 reports that det g for
exp-decay is so badly conditioned in high d that they needed the exact
Vandermonde formula (valid only at d = m), emcee sampling, and ~30-step
Bennett bridging for b(θ). The spec gestures at "Bennett's method / importance
sampling" for one corner case and otherwise says nothing; the bias/MCSE of an
importance-sampled log-marginal would be the dominant error of the headline at
exactly the d that motivates the spec, and no test pins the continuous-prior
marginal estimator beyond small-d quadrature agreement (T7a).

**What would resolve it**: specify the high-d estimators (Vandermonde-based
Jeffreys sampling at d = m as in A&M A.5; Bennett bridging for log m_π; the
optimiser for B), their error model, and a pinning test (e.g. a linear
Gaussian-manifold cell where m_π is closed-form at any d); or explicitly cap
the experiment's claims at the d the small-d machinery covers.

---

### F9: §5.4's grid rule "G ≫ √(budget)" transplants spec 000's criterion with the wrong quantity — vacuous as stated, and the chosen G under-resolves long relevant axes [severity: medium]

**Location**: §5.4 "Grid resolution G" ("G ≫ √(budget) resolves the ~√n atom
spacing (spec 000 §1.3)").

**Concern**: spec 000 §1.3's rule is grid-count ≫ atom-count; the Bernoulli
atom count is ~√m only because the total Fisher length there is L = π√m. The
correct transplant is per-axis: G_axis ≫ (per-axis Fisher length)/2.5 =
(box_length/σ_eff)/2.5 (the BA-verified ~2.5 spacing the spec itself cites).
Read as written, budget = N ∈ {1..8} gives √N ≤ 2.8 — satisfied by any G and
unrelated to the real requirement. Concretely, a hypercone with A&M's L=50
box at σ_eff = 0.1 has relevant-axis Fisher length 500 → ~200 atoms versus
G ∈ {20..50} cells: under-resolved several-fold even before the "≫". The rule
also applies one G to all axes although the relevant axis is up to ~50× longer
in Fisher units than the irrelevant ones. The §5.4 refinement check
(G ∈ {20,30,50}) cannot reveal this if all three values are below the
requirement.

**What would resolve it**: restate the criterion as
G_axis ≫ L_axis(σ_eff)/2.5 per axis, allow anisotropic grids, recompute the
defaults from the pinned boxes (F5), and run the refinement check on a cell
with a long relevant axis.

---

### F10: The spec drops the design note's deconfounding requirement — no sloppiness-at-fixed-d axis, and d reinstated as "the dimension being stressed" [severity: medium]

**Location**: §5.4 dimension sweep ("higher d show the trend toward A&M's
dramatic d≥11"); §1.1 (d: "the dimension being stressed"); §5.3 (extend
toward d ≤ 26); contrast `notes/prediction_objective_for_priors.md` §6
("Dimension is not the axis"; §6.2 axis 2: sweep scale-hierarchy depth AT
FIXED d — "A&M never do this (their d-sweep silently deepens the spectrum,
since exp-decay eigenvalues ∝10^{-d})").

**Concern**: the note this spec formalises identifies the exp-decay d-sweep
as confounded (raising d simultaneously deepens the width spectrum) and
prescribes a spectrum-depth knob at fixed d as the deconfounded axis. The
spec carries taper/rotation/curvature knobs but no spectrum-depth knob, runs
the headline figures "per d"/"vs d" (§6.1), and never acknowledges the
departure. Any §6 conclusion of the form "the asymmetry grows with d" — the
§0 framing — inherits the confound the project's own note documents; the
hypercone d-sweep is similarly confounded (more irrelevant directions and a
steeper co-volume gradient at once).

**What would resolve it**: add the note's axis (e.g. hypercone with
per-direction widths ℓ_μ = ℓ₀ρ^μ, sweeping ρ at fixed d; or exp-decay with
tapered a_μ at fixed d), or state explicitly that this spec stresses d in
A&M's confounded sense and defers the dimension-vs-spectrum attribution, with
§6's report wording adjusted to match.

---

### F11: §0 "spec 001 scored it ... and found it loses" — the 001 experiment was never run [severity: low]

**Location**: §0, first sentence.

**Concern**: `experiments/` contains only `000-static-fig1`; spec 001 has no
report and no executed run. The "found it loses to smooth priors" verdict is
the third red-team report's F1 analysis (a computed win-rate table over the
spec's hyperpriors) plus the two-hats note's diagnosis ("p* essentially never
beats Jeffreys/uniform at the spec's Kelly game" — an analysis of the design,
not an experimental outcome). As written, §0 claims an empirical result that
does not exist as an artefact, in the sentence motivating this spec.

**What would resolve it**: attribute precisely — spec 001's design was shown
analytically (in its third red-team review and the two-hats note) to make p*
lose across its hyperpriors; the experiment itself was not run.

---

### F12: Two wrong citation pinpoints into A&M [severity: low]

**Location**: §3.1 (">500 bits at d=26 in the exp-decay model — A&M §3.3");
§3.2 ("d_eff = O(1) in nominal d — A&M Fig. 2, Quinn §2").

**Concern**: (a) A&M has no §3.3 — its numbered subsections end at §2.3; the
">500 bits / <1 bit / Δ>20σ at d=26" sentence is in §3 "Discussion" (journal
p. 10). The §10 revision log shows this pinpoint was added as a red-team fix
(conc01 F5), so the wrong pin is now load-bearing attribution. (b) A&M Fig. 2
shows d_eff vs σ at fixed d=4 (with d_eff → d as σ → 0 — if anything,
evidence that d_eff tracks nominal d in the asymptotic limit); the saturation
of I⋆ in nominal d at fixed σ is Fig. 5, which §3.1 cites correctly for the
same fact. Citing Fig. 2 for "d_eff = O(1) in nominal d" points the §3.2
bridge's one named assumption at the wrong figure.

**What would resolve it**: cite "A&M §3 (Discussion), p. 10" for the 500-bit
figure; cite Fig. 5 (and Quinn §2) for the d_eff saturation, keeping Fig. 2
only for d_eff's definition.

---

### F13: "Its pedigree is MDL, left uncited by A&M/Quinn" — false for Quinn [severity: low]

**Location**: §3.4, `p_proj` bullet, last sentence.

**Concern**: Quinn et al. §5.2 attaches a footnote to p_NML stating it "is
also used, independently, in a non-Bayesian approach to model selection by
minimum description length [93, 94]", with [93] = Myung, Navarro & Pitt,
"Model selection by normalized maximum likelihood" and [94] = Grünwald &
Roos, "Minimum description length revisited". The claim holds for A&M's App.
A.3 (no MDL citation there) but not for Quinn; the spec uses the alleged
omission rhetorically (this spec as the supplier of the missing pedigree).

**What would resolve it**: "left uncited by A&M; Quinn footnotes the MDL
connection for p_NML but does not develop the prior's MDL reading" — or drop
the clause.

---

### F14: §4.2 still labels p_LN "log-normal in θ" — the error conc01 F8a corrected in §1.1 [severity: low]

**Location**: §4.2 ("`p_LN` — **log-normal** in `θ` (A&M Eq. 10)"); cf. §1.1
("Normal in `θ` (log-normal in the rate `k_μ=e^{-θ_μ}`)").

**Concern**: A&M Eq. 10 is normal in θ, log-normal in the rate k. The §1.1
table was corrected per the revision log, but §4.2's construction bullet
retains the old wrong label, so the spec contradicts itself about what p_LN
is.

**What would resolve it**: align §4.2 with §1.1.

---

### F15: §4.3's "fixed scaffold" prejudges the q-family the companion note recommends against, and q̄'s c-measure is unpinned [severity: low]

**Location**: §4.3 (`sample_q(model, pstar, c, n, rng)`; "q_non: mass on the
thin end and in the gaps between pstar's atoms"; "q̄ ... marginalised over
the c-grid"); §7 OQ-2; cf. `notes/q-family-visualisation.md`.

**Concern**: OQ-2 is open, but the "fixed" scaffold hardwires the
p*-dependent atom-anchored (A) family into the sampler signature and
comments — the family the companion note recommends only as a diagnostic
because "its circularity (nature ≔ smoothed/gapped p*) is the kind of thing a
referee would flag as rigging", recommending geometry-relative (B) for c. If
the human picks B+C, the scaffold and T14 change too, so "only the two anchor
distributions await a human choice" is not true as stated. Separately,
`q̄ = 𝔼_c[q]` requires a measure over c; "marginalised over the c-grid" makes
the reference ceiling (and T8(b)'s optimum) depend on the arbitrary 5-point
sweep grid without saying so.

**What would resolve it**: make the sampler anchor-agnostic (anchors as
injected distributions; pstar passed only to the (A)-diagnostic); pin q̄'s
c-measure explicitly (e.g. uniform on the swept c-grid, stated as a
definition).

---

### F16: T2's "R(p_J) − R(p_U) ≡ 0 exactly (no MCSE)" is unimplementable as stated [severity: low]

**Location**: §5.1 P2; §5.2 T2.

**Concern**: the test first asserts the constructions agree "to numerical
tolerance" (FIM → √det g → quadrature normalisation vs exact uniform), then
asserts the scored difference is exactly zero under common random numbers.
The numerically built p_J differs from p_U at tolerance level (the det of a
numerically evaluated FIM is not exactly constant), so the mixtures differ in
the last ulps and the R difference is small-but-nonzero: the "exactly ≡ 0, any
nonzero difference is a pipeline bug" criterion fails on correct code — or
forces the test to score the same array twice, which tests nothing.

**What would resolve it**: assert |R(p_J) − R(p_U)| ≤ (construction tolerance
propagated through the mixture), or split the test: construction agreement
with tolerance, plus a CRN-plumbing check on two literally identical mass
arrays.

---

### F17: T6's tolerance formula contradicts its own quoted value (spurious factor 3) [severity: low]

**Location**: §5.2 T6 ("within `~3·(d−1)²/x³` (≈0.6 at `d=26, x≈10` ...)");
cf. §9.2.

**Concern**: 3(d−1)²/x³ = 1.875 at d=26, x=10 — not ≈0.6; the quoted 0.6
corresponds to (d−1)²/x³ = 0.625, the next-order coefficient of the mode
expansion θ̂ = x + (d−1)/x − (d−1)²/x³ + …. The true mean deviation is 2.0815
(verified by quadrature; spec's own §9.2 quotes ≈2.08), so the leading-term
error 0.419 passes under either reading — but an implementer cannot tell
which tolerance is normative (1.875 is slack enough to mask a real sign-free
bug of ~0.7; 0.625 is the meaningful bound). Secondary: T6 does not say which
posterior is constructed — the reduced 1-D `e^{−(x−θ₁)²/2}θ₁^{d−1}` of
(9.2.1), or the full d-dim hypercone posterior, which differs by O(dθ₁/L²)
coupling through r(θ₁).

**What would resolve it**: drop the factor 3 (or restate the number as ≈1.9),
and state explicitly that T6 builds the reduced 1-D posterior (or budget the
coupling correction if it builds the full one).

---

### F18: T8(a)'s "per-cell minimum attained by the matched prior" is untestable with the §4.4 lineup, and the floor assertions lack MCSE slack [severity: low]

**Location**: §5.2 T8(a); §4.4 step 2.

**Concern**: no prior in {p*, p_J, p_U, p_LN, p_proj, q̄} is matched to the
cell's q_c (q̄ matches only the c-average), so the "minimum attained by the
prior matched to that q_c" clause has nothing to evaluate unless π = q_c is
added per cell (it is available — q_c is known and m_{q_c} is already
estimated for I_q). Separately, T8 states hard inequalities R ≥ I_q ≥ 0 on MC
estimates; for a nearly-matched prior the estimated gap D(m_q‖m_π) ≈ 0 goes
negative with ~50% probability, so the test is flaky by construction (T1, by
contrast, specifies "within combined MCSE").

**What would resolve it**: add π = q_c per cell and assert its R is the
per-cell minimum within MCSE; phrase all T8 inequalities with MCSE slack.

---

### F19: §5.4 runs T9/T11 "over the full d-sweep" — requiring p* at d > d_switch inside the Julia-free test suite [severity: low]

**Location**: §5.4 test-suite subset; §5.5 / OQ-7 ("the test suite never
imports Julia"); OQ-1.

**Concern**: T9 needs I_{p*}(d) and B_{p*}(d), and T11 needs I_{p*}(d),
across the d-sweep; for d > d_switch these exist only via juliacall. Either
the suite imports Julia (contradicting §5.5/OQ-7) or "full d-sweep" silently
means the grid-BA-feasible range (contradicting §5.4's words).

**What would resolve it**: scope T9/T11 to d ≤ d_switch in §5.4, moving the
high-d halves to the experiment script/report, or add frozen high-d fixtures.

---

### F20: T12b freezes p* atom positions/weights across two different optimisers — against spec 000's own uniqueness caution and grid quantisation [severity: low]

**Location**: §5.5 fixture (b); §5.2 T12; cf. spec 000 §1.2.

**Concern**: spec 000 §1.2 (which this spec reuses) warns that the optimal
prior is unique only in its output marginal and that cross-run comparisons
must use supports/marginals, "not pointwise mass over θ". T12b nonetheless
compares Python grid-BA atoms (constrained to grid points, spacing box/G;
one continuous atom's weight splits across adjacent bins) against Julia's
continuous L-BFGS atoms "up to label permutation" at a recorded tolerance.
Positions can only agree to ~half a grid cell — macroscopic at G = 20–50 —
so the fixture either fails spuriously or needs slack so wide it stops
testing; F6's permutation symmetry compounds it.

**What would resolve it**: freeze the optimiser-independent quantities
(I_{p*}, B_{p*}, C_N, and m_{p*} at probe x-points); if atom geometry must be
compared, use a transport distance with grid-scale tolerance after F6
canonicalisation.

---

### F21: §6.3 drops the per-sample R_s arrays that the promised q-subset analysis needs [severity: low]

**Location**: §6.3 ("Computed but **not persisted**: per-sample `R_s` arrays
... so ... a `q`-subset analysis can re-key off it"); §4.3 ("reported
per-sample so results can be subset by `q`-shape"); §4.4 step 3.

**Concern**: subsetting results by q-shape post hoc requires joining
per-sample scores to per-sample q parameters; persisting only q-metadata and
cell-level means makes the promised re-keyed analysis impossible without a
full re-run.

**What would resolve it**: persist per-sample (R_s per π, shape tag) next to
`q_metadata.jsonl` (≤2000 rows per cell), or persist per-shape conditional
means/MCSEs per cell.

## What the spec gets right

The scoring architecture is correct and carefully derived: (9.1.1), the
(3.2.1) bridge identity, and the (3.3.1) Gaussian split all check out by
hand; the three-redundancies table is a genuinely clarifying piece of
exposition; and the q̄-as-ceiling logic (per-cell pullback vs c-averaged q̄)
is exactly right. The budget-N treatment via σ_eff sufficiency is sound and
unusually well cross-checked (T7c plus the AtomicPriors `repeat` fixture).
The spec's readings of its sources are accurate in every substantive respect
I checked — including catching a real sign slip in A&M's Appendix A.1 and
correctly flagging that A&M's own quoted Δ ≈ 2.5 is a marginal leading-order
value (true mean deviation ≈ 2.08, which I re-verified). The falsification
discipline — refusing to assert the headline, demoting the capacity tautology
and the algebraic p_J = p_U identity to unit tests, and keeping the
cooperativeness sweep as the one live screen — is the right structure and
should be preserved while fixing F1; likewise the T0 regression gate,
provenance recording, and the dev-time-fixture pattern for Julia are good
engineering that the F2/F7/F8 fixes should build on rather than replace.
