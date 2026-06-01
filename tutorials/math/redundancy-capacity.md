# Coding redundancy, capacity, and equalizer priors, calibrated to the design-loss case

> Just-in-time math explainer triggered by the *design-loss* column of
> `notes/infomax_two_hats_and_directions.md` (the claim that `p*` is
> provably optimal under one loss and catastrophic under another). Goal:
> enough universal-coding / channel-capacity machinery to see **why the
> discrete infomax prior `p*` is the right object for the coding-redundancy
> loss, and why it comes out discrete** — not a general theory of universal
> coding. For the general theory see Cover & Thomas, *Elements of
> Information Theory*; Csiszár & Shields, *Information Theory and
> Statistics*; Grünwald, *The Minimum Description Length Principle*. This
> file is the design-hat companion to `tutorials/math/kelly.md` (the
> belief-hat / decision-loss side), to `tutorials/math/kkt.md` (the
> optimisation side of the same fixed-point), and to
> `tutorials/math/nml-mdl.md` (the **pointwise-regret / NML** dual of this
> **expected-regret / capacity** file — the budget-dependent sibling prior
> `p_proj`).

## What problem are we solving

The two-hats note splits the contest between priors into **two different
losses**, and the punchline is that `p*` wins one and loses (even
catastrophically) the other:

- **Design loss** — *coding redundancy*. Score a prior by how well its
  Bayes-mixture predictor codes / predicts the **data**, in the worst
  case over `θ`. This is the loss under which `p*` is a theorem.
- **Belief loss** — *one-shot Kelly with the plug-in posterior mean*. Score
  a prior by the decision loss of betting `μ̂ = E[θ|data]`. This is the loss
  the betting experiment used, and the one `p*` is *wrong* for (note §2; at
  `n=1` it is `+∞`).

This file builds only the **design-loss** machinery: redundancy, the Bayes
mixture, mutual information as average redundancy, channel capacity, the
redundancy–capacity theorem, the **equalizer / least-favourable** property,
and the argument that the capacity-achieving `p*` is **discrete**. The
belief-loss side and the two-hat split itself live in the note and in
`kelly.md`; we point back rather than re-derive.

**The channel.** Throughout, the parameter is a Bernoulli bias
`θ ∈ [0,1]`, and the data is the sufficient statistic `h ∈ {0,…,n}` of `n`
tosses, `h ∼ Binomial(n,θ)`. So the "channel" is the map
$\theta \mapsto p(h\mid\theta)=\binom{n}{h}\theta^h(1-\theta)^{n-h}$, with a
**continuous input** `[0,1]` and a **finite output alphabet** of `n+1`
symbols. That finiteness is what forces discreteness later.

## Observation, sufficient statistic, and notation

Three notational choices, made once and used everywhere below. They answer
recurring confusions, so they are worth stating in excruciating detail.

- **Observation `x`, sufficient statistic `h`.** The raw observation is the
  sequence of `n` tosses, `x = (x_1,\dots,x_n) \in \{0,1\}^n`. The number of
  heads `h = \sum_i x_i \in \{0,1,\dots,n\}` is a **sufficient statistic**:
  the likelihood `p(x\mid\theta)=\theta^{h}(1-\theta)^{n-h}` depends on `x`
  only through `h`. As the box below shows, this lets us work entirely with
  `h` and lose nothing, so from here on "the data" *is* `h`, ranging over the
  `n+1` values `\{0,\dots,n\}`.
- **Explicit arguments, no dots.** We spell the argument out —
  `p(h\mid\theta)`, `q_A(h)`, `m_\pi(h)` — rather than write the placeholder
  dot `p(\cdot\mid\theta)`. The thing inside a KL is the *whole
  distribution*; the spelled-out `h` is a **bound (dummy) variable** ranging
  over `\{0,\dots,n\}`, not a fixed value. (The only reason to prefer the dot
  is to stress "this slot holds a distribution, not a number" — with the
  bound-variable reading made explicit, the spelled-out form is unambiguous
  and easier to read.)
- **`q_A` for the agent's predictor, `r` for redundancy.** The predictor is
  the **agent's** distribution over the data, written `q_A` (subscript `A` to
  keep it distinct from the note's `q`, which there denotes *nature's* true
  distribution over `\theta` — a different object). We can, by a mild abuse,
  feed `q_A` the sufficient statistic directly and write `q_A(h)`. The
  redundancy itself is called `r` (Greek letters are reserved for measures /
  priors).

> **Why working with `h` loses nothing (sufficiency, in full).** For *any*
> predictor `q_A(x)` over the full sequence, the chain rule of relative
> entropy splits the redundancy as
> $$
> D\big(p(x\mid\theta)\,\|\,q_A(x)\big)
> = D\big(p(h\mid\theta)\,\|\,q_A^{h}(h)\big)
> + \mathbb{E}_{h\sim p(h\mid\theta)}\,D\big(p(x\mid h)\,\|\,q_A(x\mid h)\big),
> $$
> where `q_A^{h}` is the marginal `q_A` induces on `h`. Sufficiency means the
> true conditional `p(x\mid h,\theta)=p(x\mid h)` is *uniform over the
> `\binom{n}{h}` arrangements and free of `\theta`*. The second term is
> therefore `\ge 0`, and `=0` exactly when the agent matches that same
> arrangement-uniform law. So the redundancy-minimising predictor depends on
> `x` only through `h`, and on that class the arrangement law `p(x\mid h)`
> cancels top and bottom in the log-ratio, leaving
> `D(p(x\mid\theta)\,\|\,q_A) = D(p(h\mid\theta)\,\|\,q_A(h))` — the
> `\binom{n}{h}` in `p(h\mid\theta)` and in `m_\pi(h)` cancels identically.
> We define everything on `h` from the start.

## Redundancy: the cost of coding with the wrong distribution

Fix a single value of the parameter `\theta` and a single predictor `q_A`
(a distribution over the data `h`). The **redundancy** of `q_A` against
`\theta` is the KL divergence

$$
r_\theta(q_A) \;=\; D\big(p(h\mid\theta)\,\big\|\,q_A\big)
\;=\; \sum_{h=0}^{n} p(h\mid\theta)\,\log\frac{p(h\mid\theta)}{q_A(h)},
$$

where the sum runs over the `n+1` possible counts `h \in \{0,1,\dots,n\}`.

Two readings, both exact:

1. **Extra code length.** By the Kraft/Shannon correspondence "code length
   `= −\log q_A`", `r_\theta(q_A)` is the *expected number of extra nats* you
   spend coding `h\sim p(h\mid\theta)` with the code matched to `q_A` instead
   of the code matched to the truth `p(h\mid\theta)`. The oracle who knew
   `\theta` would use `p(h\mid\theta)` and pay `0`; you pay `r_\theta(q_A)`.
2. **Cumulative predictive log-loss regret.** Streaming the `n` tosses and
   predicting each next bit with the running predictive, the *summed*
   one-step log-loss regret versus the oracle telescopes (chain rule of
   relative entropy) to exactly `r_\theta` for the whole sequence. This is the
   note's §4 identity: **cumulative-Kelly log-wealth shortfall = coding
   redundancy.** The per-step penalty is the proper-scoring-rule regret of
   `kelly.md`; redundancy is its total over the stream.

**Nothing here is worst-case or anticipatory yet.** At this point `\theta` is
*fixed*, the predictor `q_A` is *given*, and the only averaging is the
expectation `\mathbb{E}_{h\sim p(h\mid\theta)}` over the data *at that fixed
`\theta`*. There is no maximisation over `\theta` and no prior over `\theta`:
the latent is just a label saying which true distribution we code against. So
— answering the natural question — yes, the predictor is purely about the
*observation*, and the latent and the worst-case enter only later, in
§"Capacity and the two games". The redundancy is exactly "the cost of a given
predictor, integrated over the distribution of observations at one `\theta`",
nothing more.

The crucial contrast with the **belief loss** is *what sits in the second
slot of the KL*. The design loss scores the agent's full predictive `q_A(h)`
against the data. The belief loss instead scores a *point summary* — the
plug-in posterior mean `\hat\mu = \mathbb{E}[\theta\mid h]`, read as a single
Bernoulli prediction of the next bit — against the truth:

$$
\underbrace{r_\theta(q_A)=D\big(p(h\mid\theta)\,\big\|\,q_A(h)\big)}_{\text{design loss (this file)}}
\qquad\text{versus}\qquad
\underbrace{D\big(\mathrm{Bern}(\theta)\,\big\|\,\mathrm{Bern}(\hat\mu)\big)}_{\text{belief loss (note §2, }\texttt{kelly.md}\text{)}}.
$$

The belief-loss KL is `+\infty` exactly when `\mathrm{Bern}(\hat\mu)` assigns
probability zero to an outcome `\mathrm{Bern}(\theta)` gives positive
probability — i.e. (for the Bernoulli) exactly when `\hat\mu \in \{0,1\}`
while `\theta \in (0,1)`: `\hat\mu=0` declares heads impossible, `\hat\mu=1`
declares tails impossible, and the opposite outcome then carries infinite
log-loss. That is the *only* route to `+\infty` in the binary one-shot case.
The general rule behind it: `D(P\|Q)=+\infty` iff `P \not\ll Q`, i.e. `Q`
puts zero mass on an event `P` does not. In a richer predictive — the Part-2
pattern bet, or a prior whose support fails to cover the needed `\theta` — the
same `+\infty` can arise from *any* such zero; in the single-Bernoulli
plug-in mean the only such zero is `\hat\mu\in\{0,1\}`. The **design loss
cannot diverge this way**, because the mixture `m_\pi(h) > 0` for every
reachable `h` whenever the prior has interior support — which is the whole
point of scoring a full distribution rather than a point estimate.

## The Bayes mixture is the best single predictor

So far the predictor `q_A` was arbitrary. Now suppose the agent summarises its
uncertainty about `θ` as a distribution `π_A` over `[0,1]` — the **agent's
working prior**. At this point `π_A` is *any* distribution over the latent; we
are **not** yet talking about nature sampling `θ`. (The true data-generating
distribution over `θ` — the note's `q` — enters only in the games of the next
section. The subscript `A` marks `π_A` as the *agent's*, to keep it distinct
from nature's `q`.)

> **Belief or design?** `π_A` is deliberately *role-agnostic* here. It might be
> a genuine **belief** about `θ` (hat ii) or a **design prior** chosen to make
> an experiment informative (hat i); the mathematics of this section does not
> care which. "The agent's working prior" is the neutral name; *which hat it
> wears* is the two-hat question, settled only by how `π_A` is chosen and what
> it is scored against — deferred to the capacity games and to the note.

Given `π_A`, the **Bayes mixture** is the predictive marginal of the data —
what the agent predicts about the observation if it integrates the (known)
likelihood over its working prior:

$$
m_{\pi_A}(h) \;=\; \int p(h\mid\theta)\,\pi_A(d\theta).
$$

This is *one* way to turn a distribution over `θ` into a predictor `q_A` for
the formulas above — and it is the **right** way: among *all* predictors
`q_A`, the one minimising the `π_A`-average redundancy is exactly the mixture
`m_{\pi_A}`, and the minimum value is the **mutual information**:

$$
\min_{q_A}\; \mathbb{E}_{\theta\sim\pi_A}\,r_\theta(q_A)
\;=\; \mathbb{E}_{\theta\sim\pi_A}\,r_\theta(m_{\pi_A})
\;=\; \mathbb{E}_{\theta\sim\pi_A}\,D\big(p(h\mid\theta)\,\|\,m_{\pi_A}\big)
\;=\; I(\Theta;X).
$$

So once you have committed to a working prior `π_A`, **not** building your
predictor from it (using some `q_A \ne m_{\pi_A}`) is strictly worse. The
**compensation identity** (Topsøe 1979) makes the penalty exact: for any
`q_A`,

$$
\mathbb{E}_{\pi_A}\,r_\theta(q_A) \;=\; I(\Theta;X) + D\big(m_{\pi_A}\,\|\,q_A\big) \;\ge\; I(\Theta;X),
$$

with equality iff `q_A = m_{\pi_A}`; the cost of not using your own working
prior is precisely `D(m_{\pi_A}\|q_A) \ge 0`. (One caveat that becomes the
whole story later: this optimality is *under the same `π_A` you are scored
against*. If nature's true distribution over `θ` differs from `π_A`, then
`m_{\pi_A}` is no longer optimal — the mismatch the belief loss punishes.)

Three readings of the identity:

- *Dependence (generalised correlation).* The same number is the statistical
  **dependence** between `Θ` and `X` in the joint `π_A(θ)·p(h|θ)` — formally
  `I = D( joint ‖ π_A ⊗ m_{π_A} )`, the KL from the joint to the product of its
  marginals (zero iff independent, growing with coupling). It is literally
  *one integral grouped two ways*: `E_{θ,h} log[ p(h|θ) / m_{π_A}(h) ]` read as
  "extra code length" (redundancy) **is** the same quantity read as "distance
  from independence" (correlation). And it is the dependence `π_A` *would
  induce if it were the truth* — a counterfactual property of `π_A`, asserting
  nothing about the real nature. (*Why does higher dependence mean a higher
  price, not a lower one?* Because the price is a **regret to the oracle**, not
  an absolute coding cost: `I` is the **value of `θ` as side-information**. The
  θ-blind code `m_{π_A}` pays for the predictability it *cannot* exploit — the
  more `X` depends on `θ`, the more the oracle who knows `θ` beats it, so the
  bigger the gap. Independence ⇒ `θ` is worthless ⇒ zero gap, the floor. The
  high-predictability of a strongly-dependent channel is real but *locked
  behind `θ`*, which the blind code lacks.)
- *Meaning (price).* The expected nats you pay, using the predictor that
  integrates the likelihood over your working prior, **equal the mutual
  information** `I(Θ;X)` between latent and observation, for the fixed
  likelihood and that `π_A` — *provided* `θ` is averaged under `π_A` (the
  matched, self-consistent case). The mixture is the **universal code**: the
  best single code against a `π_A`-random source, its irreducible average
  redundancy being `I` itself.
- *Identity.* `I(Θ;X) = H(Θ) − H(Θ|X) = E_θ r_θ(m_{π_A})` — "uncertainty
  removed by the data" and "average cumulative regret-to-oracle" are the same
  number (note §3).

**What makes `I(Θ;X)` larger or smaller?** With the likelihood fixed, `I` is a
*concave* function of `π_A`, and reading it as `H(Θ) − H(Θ|X)` says what it
rewards: spread `π_A` over θ-values the data can actually *tell apart*.

- A **point mass** `π_A = δ_{θ_0}` gives `I = 0` — no uncertainty to resolve
  (`H(Θ)=0`).
- Spreading over θ-values whose likelihoods `p(h|θ)` heavily **overlap**
  (nearly indistinguishable) also gives little — the data barely cuts `H(Θ)`,
  so `H(Θ|X) ≈ H(Θ)`.
- `I` is **largest** when `π_A` puts mass on **well-separated, highly
  distinguishable** θ — for the Bernoulli channel, weighted toward the
  endpoints `0` and `1`, where the `Binomial(n,θ)` output laws are most nearly
  disjoint (at `n=1` the maximiser sits exactly at `{0,1}`).

So "maximise `I`" pushes mass toward the most distinguishable, endpoint-heavy
configurations — exactly the shape of the capacity-achieving `p*`, and the
reason it is endpoint-loaded and discrete. Its maximal value is the **channel
capacity**, the subject of the next section.

The per-input derivative `∂I/∂π_A(θ) = D(p(h|θ)‖m_{π_A}) = r_θ(m_{π_A})` (used
in `kkt.md`) is just the integrand above: each `θ`'s contribution to `I` is
its own redundancy against the mixture.

## Capacity and the two games

The **channel capacity** is the largest average redundancy any prior can
extract:

$$
C \;=\; \sup_{\pi}\, I(\Theta;X).
$$

A prior achieving the sup is **capacity-achieving**. Capacity is a property of
the **likelihood / channel alone** — the prior is maximised out — namely the
most Θ–X dependence (equivalently, the largest average redundancy) the channel
*can be made to* induce, over all input priors.

Now a **role shift**, worth stating carefully because it is easy to mis-map.
The distribution over `θ` is no longer the agent's working prior `π_A`; it is
the variable being *optimised over*. Two different actors run that same
optimisation `\sup_\pi I`:

- **Nature, adversarially** — picking the input distribution that makes the
  prediction problem *hardest*. Crucially this is **not** "nature undercutting
  a fixed, mismatched belief": in the *coding* game the agent always
  **best-responds** with the matched mixture `m_\pi` (the maximin bullet
  below), so there is no mismatch here. Nature's lever is the **choice of
  learning problem**, not the exploitation of a wrong belief. (The
  undercut-a-fixed-belief disaster is a *different* game — the belief loss,
  scored by the plug-in decision rule — and lives in the note: there a
  committed `p*` is catastrophic, whereas here a committed `m_{p*}` is robust.)
- **A designer, constructively** — picking the input distribution that makes
  the experiment *most informative*, i.e. maximising `I(Θ;X)` (Bernardo's
  reference-prior / infomax design objective). The designer maximises
  **information**, which is a good thing — *not* its own coding cost. The
  agent-as-coder never maximises its cost; minimisation is always the coder's
  job (`\inf_{q_A}`). The maximisation belongs to the *other* role (nature, or
  the designer choosing the experiment).

These are the *same* optimisation `\sup_\pi I = C`, read adversarially and
constructively — the two-hat duality, at the capacity level. The punchline
below is that the agent's best *robust* working prior is to set `π_A = π*`, the
maximiser. Capacity sits at the meeting point of two games, one for each
player's move order:

- **Maximin (average / Bayesian redundancy).** Nature randomises `θ` with a
  prior `π`; the agent then picks the best code:
  $\sup_\pi \inf_{q_A} \mathbb{E}_\pi D = \sup_\pi I(\Theta;X) = C$.
- **Minimax (worst-case redundancy).** The agent commits to a code
  `q_A`; nature then picks the worst single `θ`:
  $\inf_{q_A} \sup_\theta D\big(p(h\mid\theta)\,\|\,q_A\big)$.

The **redundancy–capacity theorem** says these coincide,

$$
\inf_{q_A}\,\sup_\theta\, D\big(p(h\mid\theta)\,\|\,q_A\big)
\;=\;\sup_\pi\, I(\Theta;X)\;=\;C,
$$

under mild regularity, whose terms are worth unpacking:

- **Compact input** — the parameter set (`θ ∈ [0,1]`) is closed and bounded.
  This guarantees the `\sup_\pi` is *attained* — a maximising prior `p*`
  actually exists, not merely approached.
- **Finite output** — the data alphabet (`h ∈ {0,…,n}`, `n+1` symbols) is
  finite. This keeps `I` well-behaved as a function of `π` and underlies the
  discreteness bound later (support `≤ n+1` atoms).
- **A saddle** — a pair `(p*, m_{p*})` at which neither player gains by
  deviating alone: nature cannot raise the value by changing its prior, the
  agent cannot lower it by changing its code. This is exactly the **Nash
  equilibrium** of the zero-sum redundancy game (for two-player zero-sum games
  "saddle point" and "Nash equilibrium" coincide): `p*` is nature's optimal
  *mixed* strategy — a randomisation over `θ` — and `m_{p*}` is the agent's
  best response. A saddle existing is *exactly* what licenses swapping the
  order, `\inf\sup = \sup\inf` (strong duality / von Neumann's minimax
  theorem), so the two games below share the single value `C`.

with the minimising code `q_A^* = m_{π^*}` (the Bayes mixture under the
maximising prior). (Gallager 1968/1976; Davisson 1973; Kemperman 1974;
Ryabko 1979; Sibson 1969's "information radius"; Haussler 1997 gives the
clean general saddle.)

So the capacity-achieving prior `p* = π*` carries **two names for one
object**:

- the **least-favourable prior** — nature's optimal randomisation, the
  distribution over `θ` that makes prediction hardest;
- the prior whose **Bayes-mixture predictor `m_{p*}` is the minimax-robust
  code** — the agent's worst-case-optimal choice, i.e. the agent's robust
  working prior is `π_A = p*`.

This is the precise content of "choose `p*` so the worst case is least
bad": the *robust object is the mixture predictor* `m_{p*}`, and `p*` is
*simultaneously* nature's worst-case prior. Both are about the **coding
loss**; under the belief loss `p*` is the opposite of robust.

**Why the two games coincide (the move-order question).** In general the
player who moves *second* has the advantage, so `\max\min \le \min\max` always
(weak duality). They are *equal* precisely when a saddle exists: at
`(p*, m_{p*})` the two strategies are **mutual best responses**, so each game's
optimal play already *anticipates* the other's best reply and neither regrets
its move after seeing the other's. That mutual-best-response property is what
makes the move order immaterial — the reading "the commit-first game is
anticipating the other" is right, with the one caveat that it works *because*
the saddle removes the second-mover advantage; without a saddle the two games
would not share a value.

## The equalizer property

At the saddle, the per-`θ` redundancy against the optimal mixture satisfies
the **equalizer / KKT condition**:

$$
r_\theta(m_{p*}) \;=\; D\big(p(h\mid\theta)\,\|\,m_{p*}\big)
\begin{cases}
= C & \theta \in \operatorname{supp}(p*),\\[2pt]
\le C & \text{otherwise.}
\end{cases}
$$

An **equalizer rule** (Berger 1985, decision theory) is one whose **risk** —
the decision-theory term for the expected loss of a rule at a given state of
nature `θ`, which for us is exactly the per-`θ` regret cost `r_θ(m_{p*})` — is
constant over the relevant set; here `p*` equalises that redundancy across its
support. Two intuitions for *why* the optimum equalises:

- **Game-theoretic.** At a saddle, nature must be *indifferent* among the
  pure strategies it actively mixes — otherwise it would shift mass toward
  the better one and raise the value. So every `θ` in `supp(p*)` ties at the
  top value `C`; any `θ` nature *doesn't* use can only be worse (`≤ C`).
- **Optimisation.** This is exactly complementary slackness for the BA
  problem (`kkt.md`): the per-input contribution `D(p(h|θ)‖m)` equals the
  multiplier `λ = C` on the support and is `≤ λ` off it. **`kkt.md` and this
  file describe the same fixed point** — one from the convex-optimisation
  side, one from the coding-game side.

Your reading of the mechanism is exactly right, and it shows both players'
views of one condition: a support `θ` whose redundancy sat *below* `C` would be
a wasted slot — shifting its mass onto the `C`-valued points raises the average
`I` (the optimiser, equivalently nature maximising), so the optimum will not let
it persist; and from nature's side a below-`C` `θ` is an *easier* target (the
mixture already predicts it well), so the adversary puts no mass there. Both
give the same verdict — positive mass only where `r_θ = C`. (One subtlety: the
quantity being equalised, `r_θ(m_{p*}) = D(p(h|θ)‖m_{p*})`, is the *marginal*
gain in `I` from a touch more mass at `θ` — the variational derivative from
`kkt.md` — so this is first-order stationarity, the discrete analogue of
water-filling.)

The equalizer view is the cleanest test for "is this really the capacity
prior": compute `r_θ(m_p)` and check it is *flat at `C`* on the support and
*below* elsewhere. A prior whose worst-case redundancy *overshoots* `C`
(like uniform, below) is provably not minimax.

## Why `p*` is discrete

This is the result the design-loss case rests on, and it is **not** the
KL-infinity of the belief loss — it is a property of the capacity optimum.

**Immediate bound (finite output ⇒ finite support).** The output alphabet
has `n+1` symbols, so the achievable set `{(p(h|θ))_h : θ∈[0,1]}` lives in
an `(n+1)`-dimensional simplex. A Carathéodory / convexity argument
(Witsenhausen 1980) then gives: a capacity-achieving input distribution can
be taken with **at most `n+1` mass points**. Discreteness is automatic; the
only question is how many atoms and where.

Two distinct counts are easy to conflate here. The `n+1` is an *alphabet
ceiling* — how many output symbols exist — and it binds only for small `n`
(`2` at `n=1`, `3` at `n=2`). The *operative* count — how many `θ`-values the
data can actually **tell apart** — is the **resolution**, which grows like
`√n`, far below the `n+1` ceiling once `n` is large. Your diminishing-returns
intuition is exactly why the operative count is `√n` and not `n`: the 101st
head after 100 carries far less than the first, the standard error shrinks like
`1/√n`, so the number of *distinguishable* `θ`-levels accumulates like `√n`.
(So "the max that could be differentiated" is the `√n` resolution, not the
`n+1` alphabet ceiling; they coincide only at small `n`, where the ceiling
binds. See *Count and placement* below.)

*When is the optimum continuous rather than discrete?* It is **not** a clean
negation of the two conditions (the full picture is in the chat discussion).
The key points: the continuous **Jeffreys** prior is the `n→∞` limit, where the
`√n` atoms proliferate and fill in. **Unbounded, unconstrained** input (e.g. a
Gaussian *mean* over all of `ℝ`) makes `I` unbounded — infinite capacity, no
maximiser — which is the integrals-diverge case you have in mind. But the deep
driver of *discreteness* is **inhomogeneity** — special points like the `0,1`
boundary, where Fisher information blows up. On a **homogeneous** domain with no
special points — a circular / **von Mises** location parameter — rotation
symmetry makes `r(θ)` genuinely *constant*, the equalizer is met by the
**uniform** prior over the whole circle, and the optimum is continuous.
Conversely, continuous output alone does *not* force a continuous optimum: an
amplitude-constrained Gaussian channel has a *discrete* optimal input (Smith
1971). So: finite output ⇒ discrete; symmetry ⇒ continuous; inhomogeneity +
a constraint ⇒ discrete even with continuous output.

*Caution — a continuous optimal prior does **not** mean infinite resolution.*
On the circle the data still pin `μ` only to `∼√n` precision: the von Mises
location has finite (constant) Fisher information `κA(κ)`, so capacity is finite
and the observations carry only finitely many bits about `μ`, exactly as for the
Bernoulli. Two different quantities are at play, and they coincide only by
accident in the finite-output case: **resolution** (`∼√n`, a Fisher/posterior
property — how finely the data distinguish parameter values — *always finite*
here) versus **discreteness of the optimal prior** (an input-geometry property,
forced by the finite-output dimensional bottleneck). For the Bernoulli the
finite output *forces* a discrete prior and the resolution then sets its atom
*spacing*, so atom-count = resolution; on the circle nothing forces discreteness,
so the prior is continuous while the resolution lives (still finite) in the
posterior. "Atoms sit at the resolution scale" is thus a finite-output feature,
not a law about resolvability.

**The analyticity argument (why it doesn't spread, and why it persists).**
The per-`θ` redundancy `r(θ) = D(p(h|θ)‖m_{p*})` is a **real-analytic function
of `θ`** on `(0,1)`: it is a finite sum of terms `p(h|θ)·log[p(h|θ)/m_{p*}(h)]`,
each `p(h|θ)=\binom{n}{h}θ^h(1-θ)^{n-h}` being a *polynomial* in `θ` (hence
analytic), and `log` of a positive analytic function is again analytic.
Analyticity — *not* mere smoothness — is what the next step needs: the identity
theorem (a function equal to a constant on a set with an accumulation point is
constant *everywhere*) is an *analytic*-function rigidity, and is **false** for
merely `C^∞` functions — a smooth bump can sit flat on an interval without being
flat everywhere. The KKT condition says `r(θ) = C` on `supp(p*)`. If the support had an **accumulation
point** — a point with infinitely many support-points clustering arbitrarily
close to it (not an open set; think of `1/2, 1/3, 1/4, …` piling up at `0`) —
then `r = C` would hold on a set with a limit point, and the identity theorem
for analytic functions would force `r ≡ C` *everywhere* — impossible, since `r`
genuinely varies. Hence the support has no accumulation point; a bounded set
with none is **finite** (Bolzano–Weierstrass: any infinite subset of the
compact `[0,1]` *must* have one), so `supp(p*)` is a finite set of isolated
atoms — **discrete**. This is Smith's (1971) mechanism (originally for the
amplitude-constrained Gaussian channel), and is why discreteness survives even
when the output is *not* finite.

**The intuition the proof hides.** Picture the redundancy curve `r(θ)` and its
ceiling `C`. The equalizer condition puts the support *exactly where the curve
touches the ceiling*. A smooth, non-flat curve touches a horizontal line at
**isolated points** (tangencies); to touch it along a whole *interval* it would
have to run flat at `C` there — and an analytic curve flat on any interval is
flat *everywhere*. So unless the channel is symmetric enough that `r` is
globally flat (the homogeneous / circular case → continuous uniform optimum),
the support can only be those isolated kiss-points: a **discrete comb**. The
same fact in resolution language: two atoms closer than the channel's `√n`
resolution induce nearly identical output laws (confusable) and add no capacity,
so the optimiser never places them — it spaces atoms at the just-resolvable
scale and puts *nothing* in between. Discreteness is *"don't pay to distinguish
what the channel cannot see."*

**Count and placement (the project's `p*`).** Bounded by `n+1` always;
**asymptotically `∼√n`** (Mattingly et al. 2018). For small `n` the alphabet
bound `n+1` binds (we will see exactly `2` atoms at `n=1`, `3` at `n=2`);
for large `n` the `√n` scaling takes over (`n=10`: 3–4 atoms; `n=100`:
`∼10`). The atoms sit **equally spaced in the arcsine coordinate**
`φ = 2\arcsin\sqrt{θ}`, with weights filling toward the **Jeffreys/arcsine
density** $p_J(\theta)\propto 1/\sqrt{\theta(1-\theta)}$ as `n→∞`. The
arcsine coordinate is the Fisher–Rao arclength
($ds = d\theta/\sqrt{\theta(1-\theta)} = d\varphi$), so the atoms are placed
at the **just-resolvable spacing** of the channel — `~√n` distinguishable
levels — and packing more would waste capacity (confusable), packing fewer
would leave resolvable distinctions unused.

## Asymptotics: the capacity prior is Jeffreys

The discrete `p*` is **finite-`n` infomax**; its `n→∞` limit is Jeffreys,
**`∞`-`n` infomax** (note §2.3). Clarke & Barron (1990, 1994): Jeffreys is
asymptotically least-favourable under entropy (redundancy) risk, and the
minimax redundancy expands as

$$
C_n \;=\; \tfrac{d}{2}\,\log\frac{n}{2\pi} \;+\; \log\!\int\!\sqrt{\det g(\theta)}\,d\theta \;+\; o(1),
$$

with `d` the parameter dimension and `g` the Fisher information metric. For
the `d=1` Bernoulli, $\int_0^1 d\theta/\sqrt{\theta(1-\theta)} = \pi$, so
`C_n = ½\log n + O(1)`. The geometric term `log∫√(det g)` is the **number of
distinguishable distributions** = Balasubramanian's (1997) geometric
complexity = the MDL/NML stochastic-complexity penalty (Rissanen). This is
the bridge to the note's §6 (model selection via information volume): the
design-loss machinery here is the one-parameter case of the same object that
counts effective model dimension in many parameters.

## Worked Bernoulli channel: `n=1` and `n=2`

Numbers below are computed from the closed forms / Blahut–Arimoto and
hand-checked; capacities in nats (bits `= nats/\log 2`).

**`n=1`** (output `{0,1}`, alphabet bound `2`).
- `p* = ½δ₀ + ½δ₁`; `C = log 2 = 1` bit; mixture `m* = Bern(½)`.
- Redundancy `r(θ) = D(Bern(θ)‖Bern(½)) = log 2 − H_B(θ)`: equals `C` exactly
  at `θ∈{0,1}` (the support, `H_B=0`) and is `< C` strictly inside. **Clean
  equalizer.**
- Worst-case `θ` is the support `{0,1}`; nature is indifferent there.

**`n=2`** (output `{0,1,2}`, alphabet bound `3`).
- `p* = 0.441\,δ₀ + 0.118\,δ_{1/2} + 0.441\,δ₁` (the 3-atom form beats the
  2-atom `{0,1}`, whose `I=\log2`); `C = 0.754` nats `= 1.087` bits.
- Mixture `m*(0)=m*(2)=0.4706`, `m*(1)=0.0588`. Equalizer check by hand:
  `r(0)=\log(1/0.4706)=0.754`, `r(½)=¼\log\frac{¼}{0.4706}+½\log\frac{½}{0.0588}+¼\log\frac{¼}{0.4706}=0.754`,
  `r(1)=r(0)=0.754` — **flat at `C` on `{0,½,1}`**, `≤ C` elsewhere.
- The third (interior) atom is what makes `p*` usable as a belief at `n≥2`
  (it pulls the plug-in means `μ̂(0)=0.03, μ̂(2)=0.97` off the boundary, so
  the belief loss is finite rather than the `n=1` `+∞`) — but that is the
  *other* loss; see the note.

**Contrast: uniform / maxent is not the capacity prior.** Uniform has mixture
`m_U = (\tfrac13,\tfrac13,\tfrac13)` at `n=2`, so its worst-case redundancy is
`log 3 = 1.099 > C` (**overshoots — not minimax**), while its average
redundancy is only `I_U = 0.330 < C` (**not capacity-achieving either**). It
fails the equalizer test on both ends: too spread to be the minimax code,
too crude to extract capacity.

| n | prior | support | `C` or `I` (nats) | worst-case redundancy `\max_\theta r` |
|---|-------|---------|-------------------|------------------------------------------|
| 1 | `p*` | `{0,1}` | `C=0.693` | `0.693 = C` on `{0,1}` (equalizer) |
| 1 | uniform | `[0,1]` | `I=0.193` | `0.693` at `{0,1}` (ties by `n=1` degeneracy) |
| 2 | `p*` | `{0,½,1}` | `C=0.754` | `0.754 = C` on `{0,½,1}` (equalizer) |
| 2 | uniform | `[0,1]` | `I=0.330` | `1.099 = \log3` at `{0,1}` (overshoots `C`) |

## Connections worth noting

- **Rate–distortion is the *other* dual of `I`.** Capacity (here) optimises
  the **input**, worst-case, no task. Rate–distortion optimises the
  **encoder** for a *given* source under a distortion + rate budget. That is
  where discreteness-*of-representation* (categorical perception) belongs —
  note §7. Same `I`, opposite optimisation; the Blahut sibling of the
  Arimoto/`blahut_arimoto` capacity solver already in the repo.
- **Bernardo's reference prior** *is* this least-favourable prior used as a
  **design device**, explicitly not a belief (Bernardo 1979; note §2.4). The
  `m→∞` limit to Jeffreys is the same Clarke–Barron asymptotics above.
- **The belief loss is genuinely different.** Under one-shot plug-in Kelly,
  `p*` can be catastrophic (note §2; `n=1` gives `+∞`). Nothing in this file
  says `p*` is a good *belief*; it says `p*` is the optimal *code/design*.

## Why this is the right tool, in one sentence

Coding redundancy is the loss for which the infomax prior is a theorem:
`p*` is the prior whose Bayes mixture is the minimax-optimal code and is
simultaneously nature's least-favourable prior, the equalizer condition
pins it to `≤ C` everywhere with equality on its support, and the finite
output alphabet forces that support to be **discrete** — which is exactly
the object the project's Blahut–Arimoto solver returns.

## What a red-team finding in this region might be flagging

1. **Scoring the wrong loss.** A finding that `p*` "fails" or "blows up"
   may be silently using the **belief loss** (plug-in posterior mean) rather
   than the **coding redundancy** (full mixture predictor). The `+∞` lives
   only in the former. Check which distribution sits in the second slot of
   the KL: `m_p(h)` (design) or `Bern(μ̂)` (belief).
2. **Confusing the robust object.** "Use `p*` to be robust" is correct only
   if the robust object is the **mixture predictor `m_{p*}`**, not a plug-in
   decision built from `p*`. `p*` is *nature's* least-favourable prior; its
   robustness is a statement about `m_{p*}`, by saddle-point duality.
3. **Reading discreteness as a numerical/grid artifact or a KL infinity.**
   It is neither: it is Carathéodory (finite output ⇒ `≤ n+1` atoms) plus the
   Smith analyticity argument (KKT equality on an accumulation set would
   force `r≡C`). A finding that asks "why isn't the optimum a smooth density
   for finite `n`?" is asking for this argument.
4. **Forgetting the equalizer is over the support only.** `r_θ = C` holds on
   `supp(p*)`, and `r_θ ≤ C` off it. Claiming `r ≡ C` on all of `[0,1]`, or
   testing flatness off the support, misreads the KKT condition.
5. **Conflating capacity with the value under a particular prior.**
   `C = sup_π I` is the *maximum*; `I` under uniform (or any fixed prior) is
   generally `< C`. A derivation that treats uniform's `I` as "the capacity"
   has dropped the sup.
6. **Direction of the KL.** Redundancy is `D(p(h|θ)‖m)` — *truth in the
   first slot, code in the second* (forward KL, the code-length direction).
   Swapping the order gives a different and incorrect quantity, the same trap
   as `kelly.md`'s failure mode (2).

## When you'd want general theory, not this calibration

If you move to a **multi-parameter** model (the note §6 model-selection
direction), a **continuous output** channel, **capacity with a cost
constraint**, or the **rate–distortion** dual, the one-parameter
finite-output story here is too thin. Then: Cover & Thomas and Gallager 1968
for capacity; Csiszár & Shields and Grünwald for universal coding / minimax
redundancy / MDL; Haussler 1997 for the general minimax relative-entropy
saddle; Smith 1971 with Chan–Hranilovic–Kschischang (2005) for discreteness
of capacity-achieving inputs in general; and the Blahut (1972) rate–
distortion algorithm (the sibling of the repo's `blahut_arimoto`) for the
encoder dual.

## References

External (full treatment of the general theory):

- **Shannon (1948)**, *A mathematical theory of communication* — mutual
  information, channel capacity.
- **Cover & Thomas**, *Elements of Information Theory* — capacity, KL,
  code-length / redundancy; the standard textbook.
- **Gallager (1968)**, *Information Theory and Reliable Communication*;
  **(1976)** source-coding notes — capacity and the redundancy–capacity
  link.
- **Davisson (1973)**, *Universal noiseless coding*, IEEE IT — minimax
  redundancy.
- **Kemperman (1974)**; **Sibson (1969)** "information radius" — minimax
  redundancy = capacity, and its geometry.
- **Ryabko (1979)** — universal coding redundancy.
- **Haussler (1997)**, *A general minimax result for relative entropy*,
  IEEE IT — existence of the saddle and the equalizer characterisation in
  general; the cleanest minimax theorem for KL.
- **Topsøe (1979)** — the compensation identity
  `E_π D(p‖q_A)=I + D(m_π‖q_A)`.
- **Smith (1971)**, *Information capacity of amplitude- and
  variance-constrained scalar Gaussian channels*, Information and Control —
  discreteness of capacity-achieving inputs via analyticity. Generalised by
  **Chan, Hranilovic & Kschischang (2005)**.
- **Witsenhausen (1980)**, *Some aspects of convexity useful in information
  theory*, IEEE IT — Carathéodory bound: support `≤ |output alphabet|`.
- **Clarke & Barron (1990)**, *Information-theoretic asymptotics of Bayes
  methods*, IEEE IT; **(1994)**, *Jeffreys' prior is asymptotically least
  favorable under entropy risk*, JSPI — asymptotic least-favourable =
  Jeffreys; minimax redundancy expansion.
- **Balasubramanian (1997)**, *Statistical inference, Occam's razor, and
  statistical mechanics …*, Neural Computation; **Rissanen (MDL)** — geometric
  complexity = number of distinguishable distributions = NML penalty.
- **Berger (1985)**, *Statistical Decision Theory and Bayesian Analysis* —
  least-favourable priors, minimax, equalizer rules.
- **Grünwald (2007)**, *The Minimum Description Length Principle*; **Csiszár
  & Shields**, *Information Theory and Statistics: A Tutorial* — universal
  coding / minimax redundancy book-length treatments.

In-repo (already cited by the specs/notes):

- **Mattingly, Transtrum, Abbott, Machta (2018)**, PNAS (`resources/`) —
  finite-data infomax prior `p*`: discrete, `∼√n` atoms, `→` Jeffreys.
- **Bernardo (1979)**, JRSS-B — reference prior as a design device, not a
  belief.
- **Blahut (1972) / Arimoto (1972)** — the BA algorithm behind `p*`.
- **Gneiting & Raftery (2007)** — log-loss as a strictly proper scoring
  rule (the per-step redundancy of §"Redundancy").

## Provenance

Triggered by the design-loss case of
`notes/infomax_two_hats_and_directions.md` and the `n=1/n=2` worked examples
developed alongside it. The concepts here recur across **spec 000**
(Blahut–Arimoto / capacity-achieving `p*`), **spec 001** (the prior-vs-prior
betting contest, whose redundancy decomposition is the design loss), and the
note (§2 two hats, §3 bits=regret, §4 cumulative-Kelly = redundancy, §6
MDL/model selection). Promoted from chat to file because the
redundancy/capacity/equalizer/discreteness cluster is load-bearing for the
note's central claim and is the design-hat counterpart to the already-filed
`kelly.md` (belief hat) and `kkt.md` (optimisation). The notation choices
(`r` for redundancy, `q_A` for the agent's predictor, explicit `h` argument,
sufficiency reduction) were settled in a round of `> M:` clarifications on
this file. If a later spec needs the **rate–distortion** dual or the
**multi-parameter** model-selection geometry, expand into siblings
(`rate-distortion.md`, `info-volume.md`) rather than growing this file past
its one-parameter, finite-output scope.
