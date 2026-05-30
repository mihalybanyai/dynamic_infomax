# Red-team review of 001-infomax-betting

Reviewer: red-team sub-agent
Date: 2026-05-30
Spec version: 32402c4 (commit 32402c4930f93fdb2ec65693f8376f9f24180860)

## Summary

The closed-form machinery of this spec is, to my surprise, almost entirely
correct. I checked every moment derivation it leans on — the Part-1 collapse
(1.4.4) and its §9.1–§9.2 expansion, the Part-2 loss-term moment difference
(1.5.2)/§9.4, the moment-matched Beta inversion (1.8.1)/§9.5, the oracle
digamma log-moment identities (§4.3), the Kelly growth identity (1.3.2)–(1.3.3),
and the general-odds Kelly fraction in `tutorials/math/kelly.md` — against
independent numerical references, and all of them hold to ~1e-12. The
oracle upper bound (T5) and reflection symmetry (T7) are genuine invariants.
The PGM diagram matches the prose. So the math and the test suite are in good
shape and the author should not break them while addressing the findings below.

Where the spec is thinnest is not the algebra but the **experiment design and
its connection to the §0 aim**. I instantiated `p*_n` from spec 000 and
evaluated the actual `V̄₁`/`V̄₂` win-fractions across all three hyperpriors:
`p*` loses to `p_J` and `p_U` in essentially 100% of samples for both parts,
and it only wins when `q` is far more endpoint-concentrated (≈ `Beta(0.1, 0.1)`)
than *any* of H1/H2/H3 ever produces. The headline answer to §0's question is
therefore effectively predetermined by an un-justified, un-stated choice of
hyperprior shape ranges, and the design has near-zero power to detect the
regime where `p*` actually helps. That is the one substantive problem; the
remaining findings are notation and cross-reference slips. The spec needs a
design-level revision (or at least an honest scoping of what it can conclude)
before it is ready for downstream work; the math sections are ready as-is.

## Findings

### F1: The headline §0 question is confounded by the hyperprior choice; the design has near-zero power to detect a `p*` win against the reference priors [severity: high]

**Location**: §0 (Purpose and scope, the "does `p*` win?" framing and the
average-over-hyperpriors plan); §1.9 (hyperprior definitions H1/H2/H3); §7 OQ-1.

**Concern**: §0 frames the experiment as an open empirical question — "does
`p*_n` yield higher expected log-wealth than Jeffreys/uniform when nature draws
`θ` from a different `q`", averaged over a hyperprior of `q`s, reporting "whether
`p*` wins on average and how often." But the answer is not open: it is fixed by
where the hyperprior places `q`-mass, and the three chosen hyperpriors place it
almost entirely in a regime where `p*` *loses*.

I computed `p*_n` from spec 000's BA solver and evaluated the spec's own
closed forms. For Part 1, with `K = 2` and 200 `q`-samples per cell:

| n | H1 (p\*>p_J / p\*>p_U) | H2 | H3 |
|---|---|---|---|
| 2 | 0.00 / 0.00 | 0.00 / 0.00 | 0.09 / 0.14 |
| 5 | 0.00 / 0.00 | 0.00 / 0.00 | 0.00 / 0.06 |
| 10 | 0.00 / 0.01 | 0.00 / 0.00 | 0.00 / 0.14 |

Part 2 is the same story against `p_J`/`p_U` (win fractions ≈ 0.00–0.15); `p*`
only beats its own moment-matched control `p_MM` with any regularity (up to 0.85
under H2). The mechanism is concrete and not a bug: `p*_5` puts mass ≈ 0.35 on
each endpoint cell (`θ ≈ 0.0005`, `0.9995`), so its posterior-mean function is
pathological — `μ̂(h=0) ≈ 0.016`, `μ̂(h=5) ≈ 0.984`, but `μ̂(h=1..4) ∈
[0.44, 0.56]`, i.e. nearly flat at ½ for all interior `h`. Against interior or
moderate `q` it is badly miscalibrated relative to the smooth Beta priors, whose
`μ̂` tracks `h` affinely.

Crucially, `p*` *can* win — but only for `q` much more U-shaped than the
hyperpriors generate. `Beta(0.1, 0.1)` and `Beta(0.05, 0.05)` give a clean `p*`
win over both `p_J` and `p_U`; but the most endpoint-favouring `q` H1 can
produce is `Beta(0.3, 0.3)` (shape params `Uniform(0.3, 1.0)`), and at
`Beta(0.3, 0.3)` `p*` already *loses* to both (`V̄₁`: `p*` 0.295 vs `p_J` 0.329
vs `p_U` 0.306). So the win/lose boundary sits *outside* the support of every
hyperprior, and the prose tag "H1 = endpoint-favouring" overstates how
endpoint-favouring H1 actually is.

Consequences for the stated aim:
- A "`p*` loses" result — which the design makes near-certain for the
  `{p_J, p_U}` comparison §0 names as headline — does not license the natural
  reading "`p*` is not useful for Kelly betting." The result is an artifact of
  the hyperprior shape range, not a robust property of `p*`.
- The spec never reports sensitivity of the conclusion to the hyperprior shape
  range, even though that choice — not `K`, which OQ-1 worries about — is what
  determines the answer.
- The experiment as specified cannot answer §0's question in an unconfounded
  way: it is structurally rigged toward "`p*` loses" against the reference
  priors and has no cell in which a `p*` advantage could surface.

**What would resolve it**: Either (a) add a hyperprior (or extend H1) that
reaches the genuinely U-shaped regime (`a, b ≲ 0.15`) where `p*`'s endpoint
structure is matched, so the sweep brackets *both* sides of the win/lose
boundary and "how often does `p*` win" becomes a real question with a
non-degenerate answer; or (b) explicitly rescope §0 to the honest claim the
design can support — "against smooth interior/moderate `q`, does the
MI-optimal prior's coarse endpoint structure cost log-wealth, and by how much?"
— and add a stated, justified rationale for the H1/H2/H3 shape ranges plus a
sensitivity check showing the conclusion's dependence on them. Folding the
mechanism (endpoint atoms → flat interior `μ̂` → miscalibration vs interior `q`)
into the §7 "what each result would mean" grid would also keep a reader from
over-reading a foregone "`p*` loses."

---

### F2: `G₁`/`G₂` are labelled "realised" growth but are defined as the outcome-averaged growth `g̅` [severity: low]

**Location**: §1.1 symbol table (`G₁`, `G₂`, `V₁`, `V₂` rows); eq. (1.4.1),
(1.5.1).

**Concern**: The symbol table calls `G₁`, `G₂` "Realised log-wealth growth for
Parts 1 and 2", and calls `V₁`, `V₂` the "Expectation of `G` over `X_{1:n}`
given `θ`." But eq. (1.4.1) defines `G₁(θ, p, X_{1:n}) = g̅(θ, μ̂_n(p, h_n))`,
and `g̅` (eq. (1.3.3)) is already the expectation of the realised growth
`g(Y, π̂)` (eq. (1.3.2)) over the bet outcome `Y`. So `G₁` is *not* the realised
growth — the average over `Y` is the first step and is silently baked into
`G₁`'s definition. The realised growth still depends on the actual outcome `Y`,
which `G₁` has integrated out. The chain is really
`g(Y,·) →[avg over Y] g̅ =: G₁ →[avg over X_{1:n}] V₁ →[avg over θ~q] V̄₁`, and
the label "realised" is attached to the wrong link. A careful reader trying to
reconcile "realised" with (1.4.1) is sent in a circle.

**What would resolve it**: Relabel `G₁`, `G₂` in the §1.1 table as
"bet-outcome-averaged (expected-over-`Y`) log-growth", or introduce a separate
symbol for the genuinely realised `g(Y, π̂)` and reserve `G` for the
`Y`-averaged quantity. Either makes the three-stage averaging
(`Y`, then `X_{1:n}`, then `θ`) explicit and consistent with (1.4.1)/(1.5.1).

---

### F3: §3.2 names the MC-reference tests as "(T2, T3)" but the MC tests are T2a/T2b; T3 uses no Monte-Carlo [severity: low]

**Location**: §3.2, "`S_q` for MC-reference tests" bullet ("`S_q = 200` for
closed-form-vs-MC tests (T2, T3)").

**Concern**: There are no tests named `T2` or `T3`-as-an-MC-test in the §3.3
table. The closed-form-vs-Monte-Carlo tests are `T2a` (`V̄₁` vs MC) and `T2b`
(`V̄₂` vs MC). `T3` (property P3) is the matched-belief identity
`g̅(p, p) = log 2 − H_B(p)`, checked pointwise to atol `1e-12` with *no* MC,
no `S_q`, and no `M`/`R` sampling at all. So the parenthetical "(T2, T3)" is a
stale reference that mislabels which tests the `S_q = 200`, `M = 5000`, `R = 50`
sampling budget applies to.

**What would resolve it**: Change "(T2, T3)" to "(T2a, T2b)".

---

### F4: T6's `n = 100` is used by no declared sweep [severity: low]

**Location**: §3.2 (test-side sweep design, "`n` sweep for per-`n` property
tests" = `{2, 3, 5, 10}`); §3.3 P6 / §3.4 T6 (gap at `n = 100` vs `n = 5`).

**Concern**: §3.2 states the test-side `n` sweep is `{2, 3, 5, 10}` and frames
that subsection as the place where "which values to sweep over … live so spec
review covers them." But T6 evaluates the oracle gap at `n = 100`, a value
absent from every declared sweep (experiment `{2,3,5,10,20}` and test
`{2,3,5,10}`). It is computable — T6 uses `p_U`, a Beta prior needing no BA — so
this is not a correctness problem, only a coverage-of-pinned-values gap: a
reviewer reading §3.2 would not know `n = 100` is exercised anywhere. (I
confirmed the `5×` claim itself holds: the `n=5`→`n=100` gap ratio is ≈ 12–17
across several `q`, comfortably above 5.)

**What would resolve it**: Add `n = 100` to §3.2 as a T6-specific value with a
one-line note that it is a Beta-only convergence probe (no BA, no extra
runtime), mirroring how spec 000 §4's "Per-test sweep restrictions" calls out
T9's `m = 1`-only and T4's `m = 100`-only usages.

## What the spec gets right

The derivations are sound and independently reproducible: I verified (1.4.4),
(1.5.2), the §9.1/§9.2/§9.4/§9.5 expansions, the loss-term moment difference
`M_{h,n−h} − M_{h+k₊,n−h}` and its non-negativity argument, the moment-matched
Beta inversion (1.8.1), the digamma oracle identities of §4.3, the Kelly growth
identity (1.3.3) and its peak `log 2 − H_B(p)`, and the tutorial's general-odds
Kelly fraction — all to machine precision. The oracle upper bound (T5) and the
reflection-symmetry invariance (T7) are real and hold numerically. The
`n = 1` / `p_MM` boundary reasoning (gridded `σ² ≈ 0.2495 < ¼`, `ν ≈ 0.0020`)
is numerically correct, and the §1.5 non-negativity justification (single
expectation with a `≥ 0` integrand, not two separately-non-negative moments) is
the right argument. The log-space evaluation guards (§1.7 `≤ 0` per-component
ratios; §2.4 `log1p`/`logsumexp` paths) are well-founded, and the discrete
`p*` belief `r̂ ∈ (0,1)` strictly, so the §3.2 "clip never triggers" claim
holds. The test suite is unusually well-targeted (T1a vs `betaln` path, T12's
two-independent-ways exact pin, T13 log-space vs naive Bayes), and the PGM
diagram matches the prose generative model.
