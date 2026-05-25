# Kelly betting, calibrated to the infomax-betting experiment

> Just-in-time math explainer triggered by review of
> `specs/001-infomax-betting.md`. Goal: enough Kelly to evaluate
> claims about why log-wealth is the right downstream task for
> testing posterior quality, why Part 1 depends on the posterior only
> through its mean, and why Part 2 graduates to a higher-moment
> dependence — not a general theory of optimal gambling. For the
> latter, see Kelly (1956) and MacLean, Thorp & Ziemba (2010).

## What problem are we solving

Spec 001 needs a *downstream task* — a concrete decision problem
whose expected payoff distinguishes priors by the quality of the
posteriors they produce. The candidate task is one-shot Kelly
betting on a Bernoulli outcome (Part 1) or on a `k₊`-toss pattern
(Part 2). Two questions have to be settled before the spec's
derivations make sense:

1. What is the Kelly bet, in the specific even-money-Bernoulli form
   the spec uses?
2. Why Kelly specifically — what bridges *posterior quality* to
   *measurable wealth*, and what gets broken by other bet
   structures?

This explainer answers both, in that order, then connects the
answers to the structure of the spec.

## The bet, in the spec's form

A Kelly bettor with belief `π̂` about the next Bernoulli outcome
chooses a fraction `f` of current wealth to stake, with `f > 0`
betting on heads and `f < 0` betting on tails. Under *even-money*
payouts — stake `S`, gain `S` on a win, lose `S` on a loss, i.e.
payout ratio 1:1 — wealth after one round is

```
W' = W · (1 + f)   if the outcome is heads,
W' = W · (1 − f)   if the outcome is tails.
```

If the *true* probability of heads is `π_true`, the expected
log-growth per round is

```
g̅(π_true, f)   =   π_true · log(1 + f)   +   (1 − π_true) · log(1 − f).
```

Maximising over `f` gives `f* = 2 π̂ − 1` *for a bettor whose belief
is `π̂`* — which is what spec §1.3 uses as the Kelly fraction. At
the truth-matched belief `π̂ = π_true` the maximum is

```
g̅(π_true, 2 π_true − 1)   =   log 2  −  H_B(π_true),
```

where `H_B(p) = −p log p − (1−p) log(1−p)` is the binary entropy in
nats. For any other belief `π̂ ≠ π_true`, the realised expected
growth drops below this maximum by *exactly* the KL divergence from
the truth to the belief:

```
g̅(π_true, 2 π̂ − 1)   =   log 2  −  H_B(π_true)  −  D_KL( Bern(π_true) ‖ Bern(π̂) ).
```

(This is the identity spec §1.3 records on the line `g̅(π_true, π̂)
= log 2 − H_B(π_true) − D_KL(Bern(π_true) ‖ Bern(π̂))`. It is the
hinge of the whole experiment — see the next section.)

The same machinery applies to Part 2 with `π̂ = r̂_n(p, h, ω)` (the
posterior predictive probability of the pattern) and `π_true =
θ^{k₊}` (the true probability of all-heads under `θ`), per spec
§1.5. The Kelly fraction is again `f = 2 π̂ − 1`, the bet is again
even-money, the expected-growth identity is the same; only what
plays the role of `π̂` and `π_true` changes.

## Why Kelly specifically — the bridge to posterior quality

The spec's headline claim is that priors with *better posteriors*
should yield *better betting performance*. "Better posterior" is
the property `p*` is normatively built for (it maximises
`I(Θ; X_{1:n})`); "better betting performance" is the property we
*measure*. The bridge between the two is the KL-from-truth identity
above. Read it again:

```
g̅(π_true, π̂)   =   [ log 2 − H_B(π_true) ]   −   D_KL( π_true ‖ π̂ ).
```

The first bracket is independent of the bettor's belief — it is the
"truth's own" expected growth, the same for every bettor. The
second term is the bettor-specific penalty, and it is *exactly* the
KL divergence from the truth to the belief. So *across bettors with
different beliefs, the ranking of expected log-growth is exactly
the reverse of the ranking of KL-divergence-from-truth of the
belief*. "The bettor with the predictive distribution closest in
KL to the truth wins, in expectation" becomes a mathematical
identity, not a vague intuition.

This is the structural reason for Kelly's appearance in spec 001:
the expected log-wealth is a strictly proper scoring rule
(Gneiting & Raftery 2007) whose expected value under the truth is
the negative KL from belief to truth. *Posterior quality measured
by KL ⇔ betting performance measured by log-wealth* — and the
two are linked by an equality, not an approximation.

### What breaks the bridge

Three alternative bet structures look reasonable and break the
bridge in different ways:

- **Pick-a-side, fixed stake.** "Bet a fixed amount on the
  more-likely side, win 1 unit or lose 1 unit." The expected payoff
  is `2 · max(π̂, 1 − π̂) − 1` averaged over which side wins, which
  depends on `π̂` *only through which side of 0.5 it is on*. Two
  bettors with `π̂ = 0.51` and `π̂ = 0.99` get the same expected
  payoff against the same truth. The bet is insensitive to
  *calibration* — which is the property we want to discriminate.
- **Maximise expected wealth directly.** A non-log bettor who
  maximises `E[W']` would either bet 0 or 100% of wealth on every
  round (depending on whether `π̂` is on the favoured side of the
  break-even probability), making the expected-wealth distribution
  dominated by tail behaviour rather than typical-case bit content.
  Repeated rounds drive wealth to 0 or ∞ depending on a single
  coin flip's outcome; we want the *typical* expected log-wealth,
  not the *expected* expected wealth.
- **Quadratic / Brier score on the predictive probability.** A
  proper scoring rule, but the one tied to *KL* divergence rather
  than to mean-squared error is the *log* score. The whole
  identity-with-KL structure relies on `log`; swapping in a
  quadratic loss gives a bridge to a different distance (Brier =
  mean-squared error) that does not match what `p*` is constructed
  to optimise.

Kelly + even-money + log-utility is therefore not an arbitrary
choice. It is the unique combination that makes the betting score
tied to KL by an equality.

## Why this is the right tool, in one sentence

Kelly betting is the answer to "what downstream task makes
expected payoff equal to negative KL from belief to truth", which
is exactly the bridge spec 001 needs between the prior's
information-theoretic optimality (an optimisation over KL) and a
measurable financial-style outcome (expected log-wealth).

## What this means for the structure of spec 001

The KL-bridge collapses to different posterior summaries in
different bet variants. Spec §1.4 and §1.5 use this to derive the
closed-form expressions for `V̄₁` and `V̄₂`; the same fact also
explains the design decisions in §0 and §7 about *which priors* to
compare.

### Part 1 depends on the posterior only through the mean

For one-shot Kelly on a single Bernoulli toss, `π̂` is the agent's
predictive probability of heads on toss `n+1`. Under any prior `p`,
this is

```
π̂  =  P_p(X_{n+1} = 1 | X_{1:n})
    =  E_{p(θ | X_{1:n})}[ P(X_{n+1} = 1 | θ) ]
    =  E_{p(θ | X_{1:n})}[ θ ]
    =  μ̂_n(p, h_n).
```

The bet uses *only* the posterior mean. Two priors that induce the
same posterior-mean function `h ↦ μ̂_n(p, h)` give identical
expected log-wealth for every `θ`, against every nature `q`. This
is why spec §0 says Part 1 "isolates whether `p*`'s posterior-mean
function is better calibrated than the Beta priors'" — there is
*nothing else* of the posterior the bet can see.

This also explains a possible non-result: if `p*`'s posterior-mean
function turns out to be approximately Beta-shaped (affine in `h`,
which is what Beta posteriors give), Part 1 will not distinguish
the priors much. The advantage, if any, has to come from
*non-affineness* of `h ↦ μ̂_n(p*, h)`. That is an empirical
question the spec is set up to answer, not a property of the
posterior-mean derivation itself.

### Part 2 graduates to a higher moment

Betting on a `k₊`-toss pattern `ω = (1, …, 1)` ("all heads")
changes `π̂` from the posterior mean to the predictive probability
of the pattern,

```
π̂  =  P_p(X_{n+1:n+k₊} = (1, …, 1) | X_{1:n})
    =  E_{p(θ | X_{1:n})}[ P(all heads | θ) ]
    =  E_{p(θ | X_{1:n})}[ θ^{k₊} ]
    =  r̂_n(p, h_n, ω).
```

The bet now uses the *`k₊`-th raw posterior moment*. Two priors
with the same posterior *mean* but different higher moments give
different bets — which is why spec §0 says Part 2 "exposes
higher-moment / shape-level structure of `p*` that Part 1 cannot".

The moment-matched Beta control `p_MM` (spec §1.8) is constructed
specifically to share `p*`'s mean *and* variance. If `p*` beats
`p_MM` at Part 2, the win has to come from posterior structure
beyond the first two moments — i.e. from the *placement* of `p*`'s
atoms, not just from the moments those atoms collectively
reproduce. If `p*` ties `p_MM` but both beat `p_J`, the win is at
the second-moment level; if `p*` beats `p_MM` itself, the win is
at the shape level.

### When the bet depends on something beyond moments

A natural extension (spec §8 OQ-3) is a *density-region bet*: "an
oracle reveals `θ` after the bet; you win if `θ ∈ A` for some
fixed measurable `A ⊆ [0, 1]`". The Bayes-optimal probability is

```
π̂  =  ∫_A  p(θ | X_{1:n})  dθ,
```

which is a linear functional of the posterior. For non-polynomial
indicators `1_A` (e.g. `A = [0.4, 0.6]` probing the centre of
`[0, 1]`), this is *not* expressible as a finite combination of
posterior moments — it is genuinely sensitive to the local density
of the posterior. The Kelly + KL-bridge machinery still applies
unchanged: `π_true = 1_A(θ_true)` and the realised log-growth is
`g̅(1_A(θ), π̂)`. The whole analytic apparatus of spec §1.4–1.5
carries through with `r(θ) = 1_A(θ)` replacing `θ^{k₊}`.

This is why OQ-3 is the *natural* shape-beyond-moments extension
and why it is held over as an open question rather than
constructed inline — it is a different bet, not a different
analytic regime.

## Even-money vs general odds

The spec restricts to *even-money* bets (1:1 payout) — DC-1 in §7.
General `b:1` odds (win `b · S`, lose `S`) give a Kelly fraction

```
f*  =  ( b · π̂  −  (1 − π̂) )  /  b,
```

which shifts the break-even probability from `0.5` to `1 / (b + 1)`
and so shifts the *indifference point* of the bet away from the
symmetry point of the Bernoulli likelihood (which is at `θ =
0.5`). This is a knob worth turning if you want to probe whether
`p*` is exploiting the `θ ↔ 1 − θ` symmetry of the Bernoulli — but
it is a different experiment, not a refinement of this one, and
the spec defers it accordingly.

## What a red-team finding in this region might be flagging

Common failure modes when reviewing Kelly-based derivations:

1. **Confusing the bettor's belief with the truth.** The Kelly
   fraction `f = 2 π̂ − 1` uses the *bettor's* belief; the expected
   log-growth `g̅(π_true, f)` is averaged against the *truth*. A
   derivation that writes both as `π` and then maximises over `π`
   is silently asserting the bettor is the oracle — which is the
   `p_oracle` reference of spec §1.10, not the agent of the actual
   experiment. Check: the optimality `f* = 2 π̂ − 1` is in terms of
   what the bettor knows; the *value* `log 2 − H_B(π_true)` is in
   terms of what nature picks.
2. **Forgetting the KL is from truth to belief, not the other way.**
   `D_KL(π_true ‖ π̂)` is asymmetric. The Kelly identity uses
   *forward* KL (truth in the first argument); swapping the order
   gives a different and incorrect penalty. A red-team finding that
   asks "why is the truth in the first slot?" is asking for the
   derivation through `g̅(π_true, π̂) = log 2 − H_B(π_true) − …` —
   the asymmetry follows mechanically once that line is written
   down.
3. **Treating `f = 2 π̂ − 1` as universal.** This is the Kelly
   fraction for *even-money* bets. Under `b:1` odds the formula
   changes (see "Even-money vs general odds" above); a derivation
   that imports `f = 2 π̂ − 1` into a non-even-money setting is
   silently restoring even-money payoff structure.
4. **Reading "posterior mean only" as a *property of `p*`*.** It
   is a property of the *one-shot even-money Kelly bet on a single
   Bernoulli*, not of `p*`. *Any* prior gives a Part-1 bet that
   uses only the posterior mean. The advantage of `p*` over Beta
   priors at Part 1, if there is one, comes from `p*`'s posterior-
   mean function being differently shaped — not from `p*` using
   more of its posterior than the Beta priors do.
5. **Conflating "expected log-wealth" with "log of expected
   wealth".** These are not the same and are not even ranked the
   same way across bettors. The Kelly identity is for `E[log W']`;
   `log E[W']` is what a non-log bettor maximises and gives the
   pathological always-bet-everything strategy noted under "What
   breaks the bridge" above. Any derivation that swaps `log` and
   `E` is suspect.

## When you'd want general Kelly theory, not this calibration

If you find yourself working on a continuous-outcome Kelly bet (a
portfolio of multiple assets, a fractional payout, a bet on a
continuous random variable rather than a Bernoulli), or on
*sequential* Kelly with reinvestment over many rounds with
trajectory-level constraints (drawdown bounds, "fractional Kelly"
risk-management), the calibrated story above is too thin. Kelly's
original 1956 paper covers the binary case cleanly; MacLean,
Thorp & Ziemba (2010) covers the modern theory including the
risk-management and portfolio extensions. For this project's
purposes — one-shot binary or pattern bets on a Bernoulli — the
calibration above is what's needed.

## Provenance

Triggered by review of `specs/001-infomax-betting.md`: an inline
`> M:` annotation flagged that Kelly betting is the load-bearing
choice of downstream task for the whole experiment and warranted a
file rather than a chat-only explanation, given that the same
concept appears in spec §0 (motivation), §1.3–1.5 (derivation),
§2 (lab-meeting framing), §7 DC-1 (even-money restriction), and §8
OQ-2/OQ-3 (the natural extensions). If subsequent specs raise
Kelly for sequential / portfolio variants, expand this file or
split into siblings rather than absorbing the new content
inline. The pre-trigger criterion from `tutorials/tutorial-readme.md`
("two or more `> M?:` occurrences") was anticipated by the human
collaborator on the first occurrence in §0, since the recurrence
across §1–§8 was already visible at review time.
