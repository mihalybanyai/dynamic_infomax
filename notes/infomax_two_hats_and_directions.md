# Infomax, the two-hat problem, and where a normative theory can actually live

*Created 2026-05-31. Status: discussion summary / research-direction memo (not a spec).*

This note distils a long working discussion that started from the **third
red-team report's main finding** on the infomax-betting experiment and ended
up re-drawing the map of where information-maximisation can and cannot ground
a *normative* theory. It is organised logically (not by the order we discussed
it), for two uses: (1) a get-to-the-point-but-detailed reminder for MB, and
(2) context re-instatement for Claude next session.

**Documents to pull alongside this note next time:**
- `specs/001-infomax-betting.md` — the experiment spec (esp. §1.3 Kelly
  identity, §1.4 `V̄₁`, §1.10 oracle, §1.9 hyperpriors H1/H2/H3).
- `specs/001-infomax-betting-redteam_third.md` — the finding this note starts
  from (F1).
- `tutorials/math/kelly.md` — the Kelly / log-loss identity used throughout.
- `specs/000-static-infomax-fig1.md` + `resources/mattingly_paper.pdf` — the
  finite-data infomax prior `p*` and its convergence to Jeffreys.
- `notes/infomax_betting_experiment.md`, `notes/real_world_analogues.md` — the
  prior framing this discussion revises.

**Confidence flags.** The load-bearing *external* results (Clarke–Barron;
redundancy–capacity; Mattingly's `p*→`Jeffreys; rate–distortion discreteness)
are textbook/standard and cited below. The win-fraction numbers in §1 are the
third red-team's own computation (not independently reproduced here). The
synthesis (two-hat framing, the constraint lattice in §8) is mine, built on
those results.

---

## TL;DR (the spine)

1. **Finding:** `p*` essentially never beats Jeffreys/uniform at the spec's
   Kelly game; it only wins for `q` far more endpoint-concentrated
   (`≈Beta(0.1,0.1)`) than any hyperprior produces.
2. **Diagnosis:** a **two-hat conflation**. Infomax `p*` is a *design /
   least-favourable* object; the experiment uses it as an *inferential
   belief*. The optimum for one role is wrong for the other.
3. **Why it bites:** Kelly rewards KL-calibrated posteriors (true), but
   infomax optimises a *different* KL — minimax not average, cumulative not
   one-shot, under `p*` not `q`. And **Jeffreys is the asymptotic infomax
   prior**, so the headline is finite-`n` infomax vs `∞`-`n` infomax: a near
   tie by construction.
4. **"Bits = regret":** `I(Θ;X)` is the cumulative learning gap to the oracle,
   not a dividend. Maximising it = choosing the *hardest* (most informative)
   learning problem; infomax = minimise that gap *in the worst case* — robust
   insurance, paid for on benign `q`.
5. **Where infomax is provably right:** **worst-case cumulative** predictive /
   coding loss (redundancy–capacity), and — its model-selection sibling —
   **MDL / information-volume model choice** in the *multi-parameter* setting.
6. **Discretisation of continuous features:** survives, but only as a
   *rate–distortion (encoder)* phenomenon — it needs a *cost on fineness*.
   Finite observations alone bound *resolvability*, not *representation*; the
   Bayes-optimal response to scarce data is a *wide continuous* posterior, not
   a discrete one.

---

## 1. Origin: the third red-team finding (F1)

The red-team instantiated `p*_n` from spec 000's BA solver and evaluated the
spec's own closed forms. Result: `p*` loses to both `p_J` and `p_U` in
**essentially 100%** of samples across H1/H2/H3 (Part 1 and Part 2). Win
fractions vs `p_J`/`p_U` ≈ 0.00–0.15; `p*` only beats its own moment-matched
control `p_MM` with any regularity.

Concrete mechanism (not a bug): `p*_5` puts mass ≈ 0.35 on each *endpoint*
cell (`θ ≈ 0.0005, 0.9995`), so its posterior-mean function is `μ̂(h{=}0)≈0.016`,
`μ̂(h{=}5)≈0.984`, but **`μ̂(h{=}1..4) ∈ [0.44,0.56]` — nearly flat at ½ for all
interior `h`**. Against interior/moderate `q` that is badly miscalibrated
relative to the smooth Betas, whose `μ̂` tracks `h` affinely.

`p*` *can* win, but only for `q` much more U-shaped than the hyperpriors reach:
`Beta(0.1,0.1)`/`Beta(0.05,0.05)` give a clean win; the most endpoint-favouring
`q` H1 can produce is `Beta(0.3,0.3)`, where `p*` already **loses** (`V̄₁`:
0.295 vs `p_J` 0.329 vs `p_U` 0.306). The win/lose boundary (`a,b ≲ 0.15`) sits
*outside every hyperprior's support* — so the headline answer is effectively
**predetermined by an unstated hyperprior-shape choice**, and the design has
near-zero power to detect the regime where `p*` helps.

The interesting question this raised: *Kelly is supposed to reward better
KL-posteriors, and infomax is supposed to give the best posterior — so why
doesn't `p*` win?*

## 2. The core diagnosis: the two-hat problem

### 2.1 The decomposition that makes the contest exact

With the Kelly identity (spec §1.3, eq. 1.3.3),
$$
\bar V_1(p,n,q)=\underbrace{\log 2-\mathbb E_q[H_B(\theta)]}_{\text{oracle — same for all priors}}-\underbrace{\mathbb E_{\theta\sim q}\,\mathbb E_{h\sim\mathrm{Bin}(n,\theta)}\,D_{\mathrm{KL}}\!\big(\theta\,\|\,\hat\mu_n(p,h)\big)}_{\text{only term that depends on }p}.
$$
So "does `p*` win?" = "is `p*`'s posterior-mean function the best KL-calibrated
under `q`?" The first half of the intuition ("better KL → wins") is correct.

### 2.2 The flawed syllogism

"Infomax gives the best KL with `p*`" is the false step: infomax optimises a
*different* KL. Three mismatches:
- **Minimax, not average.** Infomax = capacity-achieving = *least-favourable*
  prior; it minimises the **worst-case** over `θ`. The experiment averages
  under a benign `q`.
- **Cumulative, not one-shot.** `I(Θ;X_{1:n})` is a whole-sequence quantity;
  the spec scores a single terminal bet, and Part 1 collapses the posterior to
  its **mean** (discarding the higher-moment structure where `p*` could matter).
- **Under `p*`, not `q`.** Infomax is self-referential (the prior is the
  marginal the MI is taken against); it says nothing about a foreign `q`.

### 2.3 The kicker: Jeffreys = asymptotic infomax

Clarke & Barron: the prior maximising `I(Θ;X^n)` as `n→∞` is **Jeffreys**
(`∝1/√(θ(1−θ))`). Mattingly: `p*_n` is atomic for finite `n` and **converges to
Jeffreys** (atom count `~√n`). So the headline "p* vs Jeffreys" is **finite-`n`
infomax vs `∞`-`n` infomax** — the same object at two ends of a limit, a near
tie by construction. `p*` can only pull ahead where its finite-`n` atomic
structure helps: small `n` *and* `q` near the least-favourable prior `≈p*`
(the `Beta(0.1,0.1)` regime). Uniform is the only genuinely naïve baseline.

### 2.4 The two hats

- **Hat (i) — design distribution:** used to decide *what to measure / which
  experiment is most informative*. Infomax (`p*`) is the right tool. Bernardo's
  reference prior is *defined* this way and is **explicitly not a belief**.
- **Hat (ii) — inferential belief:** the prior you Bayes-update and decide
  with. Here you want a prior **matched to `q`**.

The optima conflict (spread-to-capacity vs match-nature). The spec puts `p*` in
hat (ii) and scores it by decision loss — the category error.

### 2.5 It is *not* catastrophic failure of the competitors

Near a boundary truth a smooth prior gives `μ̂` bounded away from 0/1, so it
**under-bets** — a mild, bounded one-shot penalty, not a blow-up (in repeated
betting it is actually *safer*). The driver is the minimax-vs-average mismatch
plus Jeffreys-is-infomax, not competitor implosion.

## 3. "Bits = regret": what infomax actually maximises

$$
I(\Theta;X_{1:N})=\mathbb E_{\theta\sim p}\,D_{\mathrm{KL}}\!\big(p(X_{1:N}\mid\theta)\,\|\,m_p(X_{1:N})\big)=H(\Theta)-H(\Theta\mid X),
$$
where `m_p` is the Bayes mixture. That KL is the **redundancy** — the cumulative
amount the must-learn predictor lags the oracle. "Uncertainty removed by data"
and "cumulative regret-to-oracle" are the **same number**: the bits you learn
are the regret you pay, not a head start.

So "maximise `I`" = pick the prior making the data *as informative as possible*
= the learning problem *hardest* = the learner lags the oracle by the *most*
(under matched nature). Infomax is sensible only via the **minimax twist**:
among priors, `p*` makes this unavoidable learning cost *equalised across `θ`
and smallest in the worst case* (redundancy–capacity). That is worst-case
**insurance**; on benign interior `q` the premium is wasted and a smooth prior
matched to the interior wins.

For one-shot Part 1 there is a second leak: a **more informative (lower-entropy,
atomic) posterior can have a worse-calibrated mean** — confident quantisation
vs smooth tracking (exactly the flat-interior-`μ̂` pathology in §1).

## 4. The cumulative-sequential-log-wealth remedy (and its limit)

Bet Kelly on **every** toss as it streams. The shortfall vs the oracle
**telescopes** (chain rule of relative entropy):
$$
\sum_{t=0}^{N-1}\mathbb E_q\,\mathbb E\big[D_{\mathrm{KL}}(\theta\,\|\,\hat\mu_t)\big]=\mathbb E_{\theta\sim q}\,D_{\mathrm{KL}}\!\big(p(X_{1:N}\mid\theta)\,\|\,m_p(X_{1:N})\big),
$$
i.e. the cumulative Kelly penalty **is** the redundancy (the per-step penalty is
the per-step predictive log-loss regret; `m_p(·|x_{1:t}) = Bern(μ̂_t)`).
When `q=p` this equals `I(Θ;X_{1:N})`. The one-shot bet is one late term of this
sum — taken after the prior has washed out, discarding the early prior-sensitive
steps.

**Remedy is partial.** Cumulative fixes the *currency* (loss = redundancy). It
does **not** by itself make `p*` win on average — average-case redundancy is
minimised by the prior closest to `q`. The decisive change is **worst-case over
`θ` (minimax / least-favourable)**: there `p*` is the saddle point. So the
criterion under which infomax is *provably* optimal is **worst-case cumulative
log-wealth shortfall** — the opposite corner from the spec's average-case
one-shot. (Even then, Jeffreys wins at large `N`, being the asymptotic minimax
prior.)

**Multi-D corroboration — a *prediction* task family where `p*` is good as an
inference prior (Quinn, Abbott, Transtrum, Machta & Sethna 2023).** The
sloppy-models review (same lineage; the multi-D generalisation of `p*` —
discrete infomax prior, atoms on the model-manifold *boundaries* along sloppy
directions, `→` Jeffreys as data `→∞`) scores priors as *inference* priors in
**prediction space** (posterior-predicted outputs vs data, in noise units), not
by a betting/point score — and there `p*` is good while **Jeffreys is
catastrophic**: in high-`D` hyperribbon models Jeffreys' posterior is biased by
many `σ` (their `D=26` sum-of-exponentials: `~20σ` off the data), because in
high `D` the Fisher volume is dominated by *unidentifiable* directions and
Jeffreys spreads mass there, dragging the predictive posterior off; the
edge-weighted `p*`/projected-ML priors keep mass on the identifiable boundary,
so predictions stay calibrated. This is a **second** reason `p*` wins as a
predictor, *beyond* the worst-case argument above: in high `D` even the
**typical/average** case favours it, because the natural competitor (Jeffreys)
carries a dimension-driven volume pathology. It also **reconciles with §1 rather
than contradicting it**: §1's betting loss is `1-D`, average-case, benign-`q` —
where Jeffreys is benign and `p*`'s endpoint atoms mis-calibrate — whereas
Quinn is high-`D` prediction, where it flips. So the controlling axes are
**worst-case-vs-average** and **dimension**, *not* "betting vs prediction" per
se: `p*` wins (i) worst-case over `θ` at any `D` (redundancy theorem, provable)
and (ii) high-`D` typical-case (empirical). **How systematic is it? — Abbott &
Machta (2023, "Far from Asymptopia")**, the focused companion, makes it
quantitative, not visual: they define a **bias pressure**
`b(θ) = D_KL(p(x|θ)‖p(x)) − I(Θ;X)` — which is *exactly* the equalizer residual
of `redundancy-capacity.md` (per-`θ` redundancy minus capacity) — show
`b(θ)=0` on `supp(p*)` (the KKT/equalizer condition), and give scaling laws for
worst-case bias vs dimension. **So `p*`'s prediction-space *unbiasedness* and
its design/coding *optimality* are the same condition** (`b=0` ⇔ equalizer) —
the success is theorem-grounded, not just empirical. Two consequences: (i) the
pathology is **generic to fixed parameter-space priors**, not special to
Jeffreys — "any measure treating all parameters equally is far from uniform when
projected onto the relevant subspace," and they confirm a **log-normal** prior
also degrades with `d`, so **uniform-in-`θ` is no escape**; (ii) the unbiased
measure **must be data-dependent** (resolution-adapted = `p*`) — *no fixed
continuous prior is unbiased in high `D`*, and the right notion of "uniform" is
uniform over *distinguishable predictions*, not parameters. The one genuinely
open bit is now narrow: a **held-out proper-scoring (log-loss) sweep** (§10
offer 5), since they score bias/unbiasedness rather than predictive log-loss.

## 5. The two-hat agent, concretely (bank of `m` coins)

World: `m` coins, biases `θ_i ~ q`, budget `T` tosses; at each step choose
*which coin to toss*; then bet. (The spec's literal world has **no** design
freedom — `n` passive tosses — so hat (i) is empty and `p*` gets drafted into
the belief role. That emptiness *is* the diagnosis.)

The agent carries **two** distributions:
- **Design `p*`** — enters only the experiment-selection objective.
- **Inference `π_0`** — enters only Bayes' rule; set to the **matched** prior.

### 5.1 What `p*` is *over*, and how it looks

`p*` is a distribution over the **bias axis `θ∈[0,1]`** (shared by all coins) —
*not* over coins/allocations/data. The budget only sets its **resolution** via
the per-coin toss count: `p*_{T/m}` if you'll bet on all coins, `p*_T` if one
target. It is a comb of `~√n` atoms **equally spaced in the arcsine coordinate**
`φ=2arcsin√θ` (hence bunched at 0 and 1), weights `~1/√(θ(1−θ))`, filling in
toward the **Jeffreys/arcsine density** as `n` grows. (`n=1`: 2 atoms at the
ends; `n=10`: 3–4; `n=100`: ~10 tracing the arcsine curve.) Its job is the
*resolution map* — "how finely can these tosses resolve a bias, and where."

### 5.2 The loop

- **Pre-data:** compute `p*_{T/m}`, read its resolution (go/no-go: can `√(T/m)`
  levels support the bet?); set inference prior `π_0 = q̄`; first toss is a
  symmetric **tie** (exchangeable coins → equal EIG), so the design only wakes
  once data breaks symmetry.
- **Each step `t>1`:** Bayes-update each coin under `q̄`; toss the coin with max
  expected information gain (`p*` as the *robust working prior* / *target
  resolution* — stop probing a coin once resolved to within `p*`'s atom
  spacing).
- **Final:** Kelly bet with `μ̂_i = E_{q̄}[θ_i | data_i]`.

### 5.3 The matched prior `q̄`

If you know `q`, the matched prior **is** `q`. If you only know the hyperprior
`𝓗`, it is the marginal `q̄(θ)=∫q(θ)\,d𝓗(q)` (hierarchical / empirical Bayes).
Log-loss is a proper scoring rule, so the posterior-predictive mean under the
*true* prior is Bayes-optimal — `q̄` is the **ceiling for hat (ii)**, strictly
below the oracle, above every mismatched prior.

**Payoff that closes the loop on §1:** for H1/H2/H3, `q̄` is broad/interior —
nothing like the endpoint-spiked `p*`. So **uniform/Jeffreys win partly because
they are crude stand-ins for `q̄`**, while `p*` approximates the
*least-favourable* distribution. *Constructive suggestion:* add `q̄` to the prior
lineup as a "best achievable inference prior" baseline; the gap from
`p*`/Jeffreys/uniform up to `q̄` quantifies how much each fixed prior loses by
not being matched.

## 6. Where infomax has normative bite: multi-D model selection

- **1-D model choice is vacuous** (only a resolution knob). The "which
  variables/directions are epistemically real" question is **multi-D only** —
  and that *is* Mattingly's "maximising information from finite data selects a
  simple model."
- **Refine the mapping:** multi-D ≠ multi-coin (separable). Parameters are
  coupled through a shared likelihood, so the resolvable objects are
  **eigendirections of the Fisher Information Matrix** — *stiff* (resolvable)
  vs *sloppy* (not) collective coordinates, not individual variables (sloppy-
  model theory: Transtrum, Machta, Sethna). The infomax prior collapses the
  sloppy directions → an effectively lower-dimensional model; effective
  dimension `~` information volume `∫√(det g_n)`, growing with `n`.
- **Caveat — sloppy ≠ (practically) unidentifiable.** The FIM eigenvalue
  spread (sloppiness) is *not* the same property as practical identifiability:
  a sloppy model can still be practically identifiable given enough/appropriate
  data, and designs that optimise identifiability differ from those that
  minimise sloppiness (Chis, Banga et al.; *Sloppy models can be identifiable*).
  So "collapse the sloppy directions" is **budget-relative** — drop what is
  *unresolvable at budget `n`*, which the sloppy spectrum only *flags as a
  candidate* — not an intrinsic verdict on the coordinate.
- **Two-hat survives:** infomax answers the *design/identifiability* model
  choice ("what is resolvable at budget `n`"), **not** "what is true" or "what
  predicts best under `q`."
- **Not vague — it is MDL.** "Number of distinguishable distributions" =
  geometric complexity `log∫√(det g_n)` = the MDL/NML stochastic-complexity
  penalty (Rissanen; Balasubramanian; Clarke–Barron) = Mattingly's atom count
  generalised. Provably normative for **worst-case cumulative predictive
  (coding) loss** — the model-selection sibling of §4.
- **Recipe (two hats composed):** use infomax / info-volume as a *diagnostic*
  to choose the model's effective dimension + stiff coordinates (design); then
  do Bayesian inference *inside* that model with a **matched** prior (belief).
- **Residual gap:** complexity-normative (worst-case coding), not
  truth-normative or `q`-decision-normative. For decisions in a *specific*
  environment, fold in `q` (Bayesian model selection / predictive risk).
- **Meta:** this moves the programme from "is `p*` a good prior to *bet* with"
  (wrong seat) to "is `p*`/info-volume a good way to *choose the effective
  model*" (right seat, for the coding criterion).

### 6.1 Learnability as a model-selection constraint: prior art, and the cost it needs

**The goal.** Model selection / the frame problem is underconstrained, and an
agent must solve it *in real time*; the pure-belief (maxent) picture cries out
for an extra constraint, and **learnability** is a principled one — *don't spend
model structure on distinctions the data you'll get cannot constrain anyway.*

**Prior art (not new).** Banners worth knowing:
- **MDL / geometric complexity** (Rissanen; Balasubramanian): penalise a model
  by its count of *distinguishable* distributions `log∫√(det g)` — learnability
  *is* the complexity measure. (= §6 above.)
- **Sloppy models / practical identifiability** (Transtrum–Machta–Sethna; MBAM
  manifold-boundary reduction): collapse directions data can't constrain (with
  the §6 sloppy ≠ unidentifiable caveat).
- **Singular learning theory** (Watanabe): the real log-canonical threshold is
  the *effective* resolvable dimension near singularities — the rigorous modern
  version of "effective dimension `< nominal`".
- **Resource-rational / bounded-rational analysis** (Simon; Griffiths–Lieder;
  active inference): the agent-in-real-time framing.
- **Zellner's MDIP** (§9): maxent prior-entropy term **+** an (uncoupled)
  data-information term — a literal maxent↔reference *bridge prior*, but it
  selects a prior *within* a model, does no model choice, and can give improper
  posteriors. Right spirit, wrong altitude.

**Why it is not a heuristic (load-bearing).** Under a strictly proper loss,
unbounded compute, and **no representation cost**, the Bayes-optimal object is the
full continuous posterior (§8) — so learnability-as-selection **cannot** be derived
as loss-optimal for *ideal* inference. That is exactly why it *feels* bolted on.
It becomes a theorem the instant you **name the non-epistemic criterion** doing
the work: a **coding/capacity cost** (→ MDL / RD makes dropping unresolvable
structure *forced*) or a **worst-case/minimax stance** (→ least-favourable /
capacity). The agent stance ("agents don't have purely epistemic beliefs")
*supplies* that criterion non-arbitrarily — an embodied agent has a
compute/communication budget and faces adversarial-ish environments. **Rule for
the programme:** never claim learnability is normative for inference; *name the
cost* that makes it normative, and let the agent supply it. The heuristic-*feel*
is the symptom of overloading one prior with both hats; in the coherent split
(design-criterion ∘ matched-belief, §6 recipe) the design criterion is a genuine
theorem.

**The "source" is part of the same fiction.** `I(Θ;X)` needs *both* `p(θ)` and
`p(x∣θ)`: you cannot write "the source over `θ`" without first fixing a
parametrisation and likelihood — i.e. a **measurement model**. So the "source" is
never measurement-independent (no Platonic "constant radiance of data"); it is a
coordinate on the agent's own model. As a *design* object `p*` is fine ("the input
that makes *this* measurement maximally informative" — a statement about the
apparatus); as a *belief* it would need the measurement-independent source that
does not exist — the same fiction as "`p*` is your belief". The agent reframing
dissolves it: the data stream is *endogenous* (actions shape what is sampled), so
"learnable models" = those distinguishable by the data this agent will actually
get, *through this channel at this budget* — intrinsically channel/budget-relative,
which lands on the **rate–distortion / IB side** (§7), away from the source-side
capacity object that needed the fiction. The source-discomfort and the
learnability-goal point at the same resolution.

## 7. Discretisation of continuous features

The hope: infomax explains why people discretise continuous features
(categorical perception). The worry: it rested on the two-hat conflation
(representation treated as belief).

### 7.1 Representation is an encoder, not a belief

Discreteness lives in the **code**; the belief downstream of the code can stay
continuous ("green" is a discrete code; the posterior over wavelength given
"green" is continuous). So discretisation is a legitimate **hat-(i)** question —
exactly where infomax/efficient-coding is normative.

### 7.2 The right home is rate–distortion — the *other* dual

Two duals of the same `I`:
- **Capacity / infomax prior** — optimise the *input*, **worst-case**, **no
  task**; belief-tangle-prone (what the project used).
- **Rate–distortion** — optimise the *encoder* for a **given source `q`** and
  **distortion `d`** under a **rate budget `R`**; **average-case under `q`,
  task-aware**, design-side.

Representation = encoder ⇒ rate–distortion side. *You were using the capacity
dual when you wanted the rate–distortion dual.* RD's optimum is a **discrete
codebook** (`~2^R` categories) placed where `q` is dense and `d` punishes
confusions — dodging *both* the two-hat and the worst-case caveats. Discreteness
under a rate budget is generic (Smith 1971: amplitude-constrained Gaussian
channel → discrete optimal input; quantisation generally). Cognitive anchors:
**Sims** (rate–distortion of perception, *Cognition* 2016; generalisation law,
*Science* 2018), **Wei & Stocker** (efficient-coding perceptual bias, 2015),
**Information Bottleneck** (Tishby–Pereira–Bialek 1999) for the task-relevant
version.

### 7.3 Dimensionality asymmetry + composition

**Discretisation is well-posed in 1-D** (RD of one feature → categories);
**variable-selection is vacuous in 1-D** (needs multi-D). Opposite dimensionality
needs because they are different sub-theories. **Why the asymmetry, in one line:**
*selection exploits **anisotropy** of learnability — different resolvability in
different directions — and anisotropy is a `≥2`-D phenomenon.* In 1-D the Fisher
information is a scalar `g(θ)`; `∫√g\,dθ` is just a **length** (= the resolution /
JND count), a `1×1` matrix has no eigenvalue *spread*, and the only sub-model
below a 1-D model is "fix `θ`" — so there is nothing to *select*. Hence the
unifying statement over §6–§7: **learnability alone buys a *scale* (resolution);
a *structural choice* needs either another dimension (anisotropy → selection, §6)
or another constraint (a cost → discretisation, §7).** 1-D resolution and 1-D
discretisation are both well-posed; 1-D *selection* is the one operation that
genuinely cannot exist. They **compose**:
$$
\text{representational format}=\underbrace{(\text{dims kept})}_{\text{info-volume / MDL, multi-D}}\;\otimes\;\underbrace{(\text{discretisation within each})}_{\text{rate–distortion, 1-D ok}}.
$$
Both are design-hat, both computable with the **Blahut–Arimoto family** already
in the repo (capacity/Arimoto side ↔ the project's `blahut_arimoto`; rate–
distortion is the Blahut sibling).

### 7.4 Atom count, JND count, and bits — and discrete latents

§7.3's one-liner "`∫√g\,dθ` = the resolution / JND count" fuses three quantities a
capacity-achieving prior keeps distinct; prising them apart is what makes the
discrete-latent case behave.

- **Fisher length `L = ∫√{ds²}`** — the JND count, how many `~1σ`-resolvable steps
  fit along the direction end to end.
- **Atom count `K(L)`** — how many mass points `p*` places, and *not* one per JND.
  Blahut–Arimoto on the 1-D bounded Gaussian channel (`x∼N(θ,1)`, `θ∈[0,L]`; the
  repo's `blahut_arimoto`) gives `K=2` — the two endpoints — for *all* `L ≲ 3.33`
  (Smith's 1971 threshold `2A₀`, recovered on the grid), then a new atom roughly
  every `~2.5` Fisher lengths (`K=3` at `L≈3.4`, `4` near `5.5`, `5` near `9`). So
  `K ≈ 1 + L/2.5`, **linear, floored at 2** — *not* `L^{4/3}` (the `MI≈ζ\log K`,
  `ζ≈¾` scaling is the multi-D / large-`m` Mattingly regime, not a single bounded
  direction; checked, not assumed).
- **Information `MI(L)`** — what those atoms actually buy. A 2-atom direction carries
  **far less than one bit** until its ends are well separated: `≈0.04` bit at
  `L=0.5`, `0.16` at `1`, `0.48` at `2`, `0.80` at `3.2`, reaching `\log 2` only as
  `L→∞` (where a third atom has already taken over). The endpoints carry `O(L²)` bits
  while close, saturating at one bit when far.

**No literal submanifold (refines §6).** Because `K≥2` for any `L>0`, infomax never
collapses a direction to a point — it returns a graded **resolution profile**
`K(L_μ)`, never a lower-dimensional *model*. A true submanifold needs an extra
**threshold** ("a direction under `ε` bits is not worth keeping"), which is
budget-relative (the §8 lattice) and external to infomax; the `d_eff` in capacity
counts (`C_N ∼ (d_eff/2)\log N`) is exactly that thresholded count. The minimum-2
floor is, read this way, the refusal to quantise *below* a resolvable binary
distinction.

**Discrete latents, on the right currency.** The cutoff must therefore be on
**information / distinguishability**, never on atom count. A 2-atom continuous sloppy
direction (`L≪1`, `≪1` bit) and a 2-atom *intrinsically binary* latent whose states
are far apart in data space (`is the sun on?`, `~1` full bit) carry the same atom
count and `~20×` different information — only an MI cutoff separates them, keeping the
sun and dropping the sloppy direction. Discreteness per se does not protect the sun;
**separation** does (`KL ≈ ‖Δy‖²/2σ²`, so a binary latent with `y(0)≈y(1)` is just as
collapsible at coarse budget, and just as resolvable once `N` is large). This is why
the **Blahut–Arimoto / capacity** object is the right primitive — it treats discrete
and continuous channels alike and needs no smooth manifold, whereas the Fisher-`√det
g` geometry (its smooth special case) cannot even *see* a discrete latent (no
tangent). Mixed models factor as *(continuous manifold, reduced by collapsing short
directions)* `⊗` *(discrete latent, reduced by **merging states the budget cannot
tell apart**)* — one distinguishability cutoff, both factors.

**The caveat that keeps it honest (hat (i), not (ii)).** Distinguishability is a
*resolution / coding* criterion — what the experiment can tell apart — not *decision
stakes*. The sun is safe only because it is *both* highly resolvable *and* highly
decision-relevant; those coincide here but need not. The genuinely hard case —
**decision-critical yet poorly resolvable** (you care enormously whether the sun is
on, but it is pitch dark and the data barely discriminate) — is invisible to
`p*`/MDL, which collapses it: correct for description length, wrong for acting under
uncertainty, where you keep the bit and propagate it. That needs a **loss-weighted**
relevance, not an MI one — the design-vs-decision seam of §2.4 and §8. In a Gaussian
manifold the two nearly coincide (the Fisher metric *is* the prediction-space
metric), but in general they part, and `specs/002` scoring held-out predictive
log-loss `D(m_q‖m_π)` rather than MI is a deliberate step onto the decision-relevant
side. Slogan, sharpening §8: *the environment tells you what is worth distinguishing,
the atom count how finely it bothered to — neither tells you what is worth caring
about.*

## 8. The crux refinement: environment-side vs agent-side constraint

MB's distinction: RD's constraint is **agent-side** (limited storage/compute).
The target was **environment-side** — *finite observations limit learnability* —
with **unbounded** agent compute. Does discretisation survive *that*?

**Verdict: no — and the reason is clean.** Finite data bounds *resolvability*
but imposes **no cost on representing finely**. With unbounded compute the
Bayes-optimal representation of a continuous `θ` is the posterior `p(θ\mid h_n)`
— *wide* when `n` is small, never *discrete*. Discreteness of the representation
needs a **cost on fineness** (capacity / communication / finite action) — the RD
ingredient being excluded. Under any strictly proper loss with no representation
cost, the optimum is the full continuous posterior; any discretisation strictly
loses.

**Strongest survivor (and its limit):** the **minimal sufficient statistic**
`h_n ∈ {0,…,n}` is discrete, finite-data-driven, capacity-free, normative — but
it discretises the **evidence**, not the **feature**; it is **lossless** (keeps
all relevant info), whereas categorical perception is **lossy** (discards
within-category distinctions). Empirical tell: **categorical perception persists
with unlimited exposure**, the signature of a compression/capacity effect, not a
finite-sample one (finite-sample effects *sharpen* with `n`).

**What finite-data-alone *does* give:** **resolution / learnability /
identifiability** — `~√n` distinguishable JNDs, Fisher/info-volume geometry, the
MDL distinguishable-distribution count. That is discreteness of *what is
resolvable*, not of *the representation*. (Reading it as a representational
prescription would be a subtle cousin of the two-hat conflation.)

### The constraint lattice

| | no agent cost | capacity cost `R` |
|---|---|---|
| **infinite data** | continuous posterior | discretisation (RD), data-independent |
| **finite data `n`** | resolution / learnability (`√n` JNDs, continuous belief) | **data-modulated discretisation** |

- Top-left (the "pure environment" cell) is **continuous** — the negative
  result.
- Bottom-right is the prize: **finite data × capacity** → categories whose
  count/sharpness/placement are shaped by *both* the budget and how much the
  environment let you learn (scarce data ⇒ coarser/softer categories). The only
  cell where finite observations genuinely shape discretisation; single-variable
  friendly; relatively underexplored.

**Recommendation:** for discretisation *with environmental content*, own the
capacity ingredient and study the **interaction** (data × capacity). For
*pure-environment* normativity, the honest target is **learnability/resolution**
(the §6 dimensionality / variable-choice direction), where the output is a
resolvable-cell *count*, not a representational *format*. Slogan: *the
environment tells you what is worth distinguishing; only a cost tells you to
stop representing in between.*

## 9. Consolidated references (with what each supplies)

- **Mattingly, Transtrum, Abbott, Machta (2018), PNAS** — finite-data infomax
  prior `p*`: discrete atoms, count `~√n`, `→` Jeffreys as `n→∞`. (In
  `resources/`.)
- **Quinn, Abbott, Transtrum, Machta, Sethna (2023), *Rep. Prog. Phys.*** —
  multi-D generalisation of `p*`: discrete infomax prior with atoms on
  model-manifold *boundaries*, `→` Jeffreys as data `→∞`; MBAM model reduction;
  the high-`D` hyperribbon **Jeffreys-as-inference-prior catastrophe** (`~20σ`
  prediction-space bias) fixed by edge-weighted priors. Multi-D evidence for the
  two-hat split, scored in *prediction space* (visual + the prior's own MI, not
  a proper scoring rule). DOI 10.1088/1361-6633/aca6f8.
- **Abbott & Machta (2023, "Far from Asymptopia", *Entropy* 25(3):434; arXiv
  2205.03343; code `mcabbott/AtomicPriors.jl`)** — the focused, *systematic*
  high-`D` result behind the review. Defines **bias pressure** `b(θ) = ∂I/∂p(θ)
  = D_KL(p(x|θ)‖p(x)) − I(Θ;X)` (Eq. 5) — which is the *variational gradient* of
  `I` and, by our identification, the `redundancy-capacity` equalizer residual;
  the optimal `p*` has `b=0` on its support, found by minimising `B=max_θ b(θ)`.
  Shows `b` **correlates with posterior bias** (posterior-mean prediction pulled
  `Δ>20σ` off the data at `d=26`, with `I<1` bit, `B>500` bits learned), and that
  **Jeffreys *and* other fixed continuous priors (a log-normal they test)
  degrade with `d`** — their general claim ("any measure treating all parameters
  equally") covers uniform-in-`θ` too. The unbiased measure must be
  **data-dependent** (`p*`); the asymptotic (Jeffreys) limit needs data
  *exponential in d* ("longer than the age of the universe"). Sharp framings:
  Bayesian **model selection exists to avoid measure-induced bias, not
  overfitting**; and a **new invariance** — predictions independent of
  unobservable detail — *replacing* Jeffreys' repetition-invariance. Bears on §4:
  strong support that `p*` is a good *inference* prior under a
  *prediction/unbiasedness* criterion — it **refines** rather than vindicates
  "p* bad as belief" (they argue `p*` gives the *best, unbiased* posteriors, i.e.
  the design object is the right belief *for this loss*; the §1 betting/decision
  loss is untested by them). NB they reserve "reference prior" for Bernardo's
  *asymptotic* limit (= Jeffreys) and call the finite-`n` object the
  "optimal / Shannon-optimal prior" — so our "finite-data reference prior" is
  loose usage.
- **Clarke & Barron (1990, 1994)** — Jeffreys asymptotically least-favourable /
  maximises `I(Θ;X^n)`; asymptotic minimax redundancy.
- **Redundancy–capacity theorem** (Gallager 1968; Davisson 1973) — minimax
  redundancy = channel capacity; capacity-achieving prior = least-favourable.
- **Bernardo (1979)** — reference prior as an information-maximising *design*
  device, explicitly *not* a subjective belief. (Already in spec 001 §8.)
- **Zellner (1977; 1996, *J. Econometrics*; Zellner & Min 1993)** — maximal data
  information prior (MDIP): maximises *prior entropy* **+** *average data
  information*, `p(θ)∝exp{∫f(x∣θ)log f(x∣θ)dx}`. A maxent↔reference **bridge
  prior**: the data term is *uncoupled* (no mixture marginal `m(x)`), hence
  linear in `p` and ≠ the reference prior; can give improper posteriors; selects
  a prior *within* a model, not a model.
- **Gneiting & Raftery (2007)** — log-loss is a strictly proper scoring rule ⇒
  the matched prior's posterior-predictive mean is Bayes-optimal. (In spec §8.)
- **Rissanen (MDL); Balasubramanian (1997); Clarke–Barron** — model selection
  via geometric complexity `log∫√(det g)` = number of distinguishable
  distributions = NML penalty.
- **Sloppy models** — Transtrum, Machta, Sethna: FIM eigenspectrum, stiff/sloppy
  collective coordinates.
- **Sloppiness ≠ identifiability** — Chis, Banga et al. (*On the relationship
  between sloppiness and identifiability*); *Sloppy models can be identifiable*:
  sloppy directions are candidates for collapse, not verdicts; practical
  identifiability is budget-relative.
- **Singular learning theory** — Watanabe: real log-canonical threshold =
  effective resolvable dimension near singularities.
- **Resource-rational / bounded rationality** — Simon; Griffiths & Lieder;
  active inference (Friston): beliefs as action-tools under compute/budget
  limits (the "agents lack purely epistemic beliefs" stance).
- **Rate–distortion** — Shannon; Berger; **Blahut (1972)** algorithm; **Smith
  (1971)** amplitude-constrained channel → discrete optimal input.
- **Cognitive discretisation** — **Sims (2016 *Cognition*; 2018 *Science*)**;
  **Wei & Stocker (2015 *Nat. Neurosci.*)**; **Tishby, Pereira, Bialek (1999)**
  Information Bottleneck.
- **Adaptive experiment design** — QUEST/Psi (Watson & Pelli) as EIG-based
  experiment selection — the concrete hat-(i) computation.

## 10. Open threads / where to pick up

**Standing computational offers (each uses spec 000's BA + the spec's closed
forms; no new theory needed):**
1. **Crossover plot** — `V̄₁(p*) − V̄₁(p_J)` and `− V̄₁(p_U)` vs the
   concentration `c` of `q=Beta(c,c)`. Expected: smooth and modest near the
   boundary (rules out "catastrophic competitor failure"), zero-crossing where
   `Beta(c,c)` starts to resemble `p*_n`. Settles §2.5 empirically.
2. **Redundancy identity check** — numerically verify cumulative-Kelly shortfall
   `= D_KL(p(X_{1:N}|θ) || m_p)` and that its **worst-case-over-`θ`** value is
   minimised by `p*` while the `q`-average is not. Concretises §4.
3. **`q̄` baseline** — add the matched prior `q̄=E_𝓗[q]` to the lineup; measure
   the gap up to it from each fixed prior (§5.3).
4. **1-D rate–distortion** — BA rate–distortion codebook for a single feature
   going discrete, category count tracking the rate (§7).
5. **Proper-scoring prediction sweep** — score `p*` vs `p_J` vs `q̄` by
   **held-out posterior-predictive log-loss (= redundancy)**, *not* the
   plug-in-mean Kelly bet, across worst-case-vs-average `q` and across `n` (1-D)
   / `D` (multi-D toy, e.g. sum-of-exponentials). Predicted map: `p*` wins
   worst-case at any `D`, and high-`D` average-case (Jeffreys volume pathology,
   Quinn et al.), while losing low-`D` average-case (§1). Turns Quinn's
   visual/MI evidence into a proper-scoring result; the prediction-task analogue
   of offers 1–2 (§4).

**Three candidate research directions (not mutually exclusive):**
- **(A) Data × capacity → data-modulated discretisation** (bottom-right of the
  §8 lattice). Single-variable friendly; the only place finite observations
  shape discretisation; relatively novel. Needs a motivated distortion `d` and
  capacity `R`; predicts the data-dependence (coarser categories under scarcer
  data) that pure RD cannot.
- **(B) Pure-environment learnability / identifiability** via info-volume / MDL
  (§6, §6.1 — normative only relative to a *named* cost). Multi-D; variable
  choice as dimensionality reduction (stiff coordinates),
  not include/exclude. Normative for worst-case coding; bring `q` for decisions.
- **(C) Daisy-chain mismatch signal under the two-hat split** (revives the
  `resources/overleaf_doc/main.tex` §"daisy chain": MB → BI → misspecification
  signal → EC adjusts the likelihood). The original loop reads off the *expected*
  bits-to-learn (the future component of the MI) in the MB step and compares it
  to the *actual* bits from a Bayesian-inference step; the residual is meant to
  signal whether the agent's **likelihood** `p_A` matches nature's `p_N`, and an
  efficient-coding step then nudges `p_A`. **The catch:** the loop silently uses
  `p*` as *both* the MB design object *and* the BI belief, so "expected vs
  actual" is self-consistent. Once inference uses a separate epistemic prior
  `π_A` (maxent/matched), the gap splits into a **prior gap** (`p*` ≠ `π_A`,
  present even with a correct likelihood) and the wanted **likelihood gap**
  (`p_A` ≠ `p_N`); the naive comparison conflates them → false misspecification
  alarms — the two-hat conflation, inherited by the loop.
  - *Fix:* baseline the expected learning under the **same `π_A` you infer
    with**, and read the signal as **predictive-log-loss excess**, not raw
    info-gain (the prior→posterior KL is not sign-definite under misspecification;
    the cumulative log-loss → `H(p_N) + D(p_N‖p_A(·|θ*))`). The redundancy split
    `regret = estimation (prior-dependent, vanishes ~ d·log t / 2t) +
    D(p_N‖best-in-class)` shows the **misspecification floor is prior-invariant**
    — `π_A` only sets convergence speed. So `p*`/capacity keeps a *different*
    job (the learnability **budget** `C`: whether/what to measure), the inference
    prior does the update **and** the self-consistent baseline, and the prior-free
    floor is the EC target.
  - *Payoff:* the two-hat split **sharpens** the loop rather than killing it —
    maxent inference + a self-consistent baseline *removes* the prior-as-belief
    confound the `p*`-does-everything loop carried; asymptotically the belief
    prior washes out and the misspecification signal (hence the EC update) is
    prior-invariant. *Caveats:* an unknown `n`/horizon is a third confound (the
    log-loss-**rate** form is more robust than a one-shot bit count); EC can
    reduce the floor only to `D(p_N‖closest representable encoder)`, and that
    irreducible residual ("my representational class can't capture nature") is
    itself the interesting meta-cognitive signal. Connects to §3 (bits=regret),
    §4 (cumulative-Kelly = redundancy), §6.1 (name the cost), and efficient
    coding (`main.tex` §ec). Tutorial stays focused; the mechanics live in
    `tutorials/math/redundancy-capacity.md`.

**One-line status of the spec itself:** the third red-team's F1 (design has
near-zero power; headline confounded by hyperprior shape) is *not yet processed*
into `specs/001-infomax-betting.md` — it needs either an added genuinely-U-shaped
hyperprior (`a,b ≲ 0.15`) or an honest rescoping of §0 + a sensitivity check.
That is the next concrete spec action whenever the betting experiment is resumed.
