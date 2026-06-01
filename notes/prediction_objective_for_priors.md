# A predictive-scoring objective for testing `p*` as an inference prior

*Created 2026-05-31. Status: working note / maths development (not a spec).*

**Purpose.** Abbott & Machta ("Far from Asymptopia", *Entropy* 2023) show that
in high `d` the finite-data infomax prior `p*` is *unbiased* in prediction space
while Jeffreys (and other fixed continuous priors) are catastrophically biased.
But their score is a **bias of the posterior's centre** (`Δ`, below), in-sample
and **self-consistent** — they draw the data from `p*` itself (`x ∼ p*`), and
`b(θ)=0` on `supp(p*)` is the equalizer/KKT condition — so what they establish is
that `p*` codes *its own* source unbiasedly, *not* that it infers a *foreign*
nature `q` well. The right question is therefore **not** "is `p*` a good epistemic
prior": under a proper score it is dominated by the matched prior `q̄`, and it is a
*design* object by construction (`notes/infomax_two_hats_and_directions.md` §2).
It is: **does the high-`d`, coupled, ribbon-geometry setting create a difficulty
that bites *deployable non-infomax* priors (Jeffreys, uniform-`θ`, log-normal)
disproportionately — a co-volume pathology `p*` is structurally less sensitive to
— and does that advantage *transfer* to held-out predictive accuracy under a
foreign `q`, or evaporate once `p*` is no longer flattered by self-sampling?**
This note builds the **held-out posterior-predictive log-loss (= redundancy)**
objective under which that question is answerable, and isolates what `Δ` cannot
see. It is the maths behind §10 offer 5 / §4 of
`notes/infomax_two_hats_and_directions.md`, and leans on
`tutorials/math/redundancy-capacity.md` (equalizer/capacity) and `kelly.md`.

Companion files to pull: the two-hats note (§4 cumulative-Kelly = redundancy,
§5.3 matched `q̄`, §10 offer 5); `redundancy-capacity.md`; `kelly.md`.

---

## 0. Notation

- Model family `{p(x|θ) : θ ∈ Θ}`. Running examples: the Bernoulli/binomial
  channel (1-D, `redundancy-capacity.md`) and A&M's sum-of-exponentials
  hyperribbon `p(x|θ)=N(y(θ),σ²I_m)` (multi-D).
- Agent's prior `π`, a candidate from `{p*, p_J (Jeffreys), p_U (uniform-θ),
  p_LN (log-normal), q̄ (matched)}`.
- Bayes mixture / one-shot predictive `m_π(x) = ∫ p(x|θ)\,π(dθ)`; posterior
  `π(θ|x_{1:t})`; sequential predictive
  `m_π(x_{t+1}|x_{1:t}) = ∫ p(x_{t+1}|θ)\,π(θ|x_{1:t})\,dθ`.
- **Nature**: true distribution over `θ` is `q` (the note's `q`); true data
  marginal `m_q(x) = ∫ p(x|θ)\,q(dθ)`.

---

## 1. The two objectives, side by side

### 1.1 A&M's objective — posterior deviation `Δ` (what they actually score)

$$
\Delta(x)=\frac1\sigma\Big|\,y(\hat\theta_x)-\!\int d\theta\,p(\theta\mid x)\,y(\theta)\,\Big|,
\qquad \hat\theta_x=\arg\max_\theta p(x\mid\theta).
$$

It measures, in noise units, the gap between the **MLE prediction**
`y(θ̂_x)` (= projection of `x` onto the model manifold) and the **posterior-mean
prediction** `⟨y⟩_x`. It is: *bias of the centre*, **in-sample** (same `x`),
**point summary** (first moment of the predictive only), and in their figures
**self-consistent** (`x ∼ p*`). Ideal `Δ≈0`; Jeffreys at `d=26` gives `Δ>20`.

> **Self-consistency caveat (load-bearing — the transfer is asymmetric).** A&M
> evaluate `Δ` on data drawn from `p*`'s own marginal,
> `x ∼ p*(x) = ∫ p*(θ) p(x|θ) dθ`, and `b(θ)=0` on `supp(p*)` is the
> equalizer/KKT condition — both *self-referential* (design) properties. So
> `Δ≈0` says `p*` codes its *own* source unbiasedly, **not** that it infers a
> foreign nature `q` without bias. The transfer to a foreign-`q` predictive test
> is **asymmetric**:
> - **Jeffreys' badness transfers.** In the hypercone (A&M Appendix A.1) the
>   posterior-mean bias is `Δ = (d−1)/x`, a *pointwise* property of the posterior
>   at the observed `x` — independent of how `x` was generated, and *largest at
>   the thin end* (`x` small), exactly where a foreign interior/edge `q` puts its
>   data. A foreign `q` does not rescue Jeffreys; it can make it worse.
> - **`p*`'s goodness is partly self-served.** `p*`'s pointwise bias is bounded
>   by its atom spacing ≈ resolution ≈ `O(1)` Fisher length, *independent of `d`*
>   (it tiles the relevant subspace and collapses the irrelevant ones — A&M
>   Fig. 5's "ignores added irrelevant parameters"). Self-sampling lands data on
>   the atoms, where that `O(1)` is near-zero; under foreign `q` data can land
>   *between* atoms, and `p*` then pays its `O(1)` spacing penalty *plus* the
>   marginal-mismatch `D(m_q‖m_{p*})` of §2.1.
>
> Net: **`p*`'s pointwise bias is `O(1)`; Jeffreys' is `O(d)`.** The foreign-`q`
> experiment tests whether that `O(d)`-vs-`O(1)` gap survives once `p*` is no
> longer flattered by self-sampling — *not* whether `p*` is unbiased in any
> absolute sense (it is not the matched prior, so it cannot be).

### 1.2 Our objective — held-out predictive log-loss `=` redundancy

Train on `x_{1:t} ∼ p(·|θ)`, predict a *fresh* `x' ∼ p(·|θ)` with the posterior
predictive `m_π(x'|x_{1:t})`, score `−log m_π(x'|x_{1:t})`. Per-step excess over
the oracle (who knows `θ`):

$$
\rho_t(\pi;\theta)=\mathbb E_{x_{1:t}\sim\theta}\,D_{\mathrm{KL}}\!\big(p(\cdot\mid\theta)\,\|\,m_\pi(\cdot\mid x_{1:t})\big)\ \ge 0 .
$$

Cumulative over horizon `N` (telescoping / chain rule — the §4 identity):

$$
R_N(\pi;\theta)=\sum_{t=0}^{N-1}\rho_t(\pi;\theta)=\mathbb E_{x_{1:N}\sim\theta}\,D_{\mathrm{KL}}\!\big(p(x_{1:N}\mid\theta)\,\|\,m_\pi(x_{1:N})\big).
$$

This is a **proper** score (full predictive, all moments), **held-out**
(generalisation), and reduces to the **redundancy** we already analyse.

### 1.3 What separates them — table

| | A&M `Δ` | log-loss `R` (ours) |
|---|---|---|
| scores | posterior **mean** of `y` | **full** predictive distribution |
| sample | **in-sample** (same `x`) | **held-out** (fresh `x'`) |
| measures | bias of the centre | bias **+** calibration/spread |
| proper rule? | no | yes |
| `p*` by construction | unbiased **on `x∼p*`** (`b=0` is self-referential; §1.1) | `O(1)` bias vs Jeffreys' `O(d)` — **does it transfer to foreign `q`?** (§1.1, §3) |

---

## 2. The two regimes of `R`, and what each prior pays

### 2.1 Average-case under `q` — reduces to a marginal-mismatch KL

By the **compensation identity** (apply to the `N`-fold marginals):

$$
\boxed{\;R_N^{q}(\pi)\;=\;\mathbb E_{\theta\sim q}\,D_{\mathrm{KL}}\!\big(p(x_{1:N}\mid\theta)\,\|\,m_\pi\big)\;=\;I_q(\Theta;X_{1:N})\;+\;D_{\mathrm{KL}}\!\big(m_q\,\|\,m_\pi\big)\;}
$$

with `I_q = E_{θ~q} D(p(·|θ)‖m_q)` (the matched floor) and `m_q,m_π` the `N`-fold
data marginals. So:

- **the matched prior** (`m_π=m_q`, e.g. `π=q̄`) is average-case optimal, value
  `I_q`;
- **any other prior's excess regret is exactly `D(m_q‖m_π)`** — the KL between
  *its* Bayes-mixture data-marginal and nature's. Everything reduces to
  comparing data-marginals. (This is also the §5.3 `q̄`-baseline gap, now in
  log-loss currency.)

*Derivation to check:* `E_{θ~q}∫p(x|θ)log[p(x|θ)/m_π] = E_{θ~q}∫p[log(p/m_q)+log(m_q/m_π)] = I_q + ∫ m_q log(m_q/m_π)`. ✔ (do the `N`-fold version carefully).

### 2.2 Worst-case over `θ` — the capacity/minimax corner (where `p*` is a theorem)

$$
R_N^{\max}(\pi)=\max_\theta R_N(\pi;\theta),\qquad \min_\pi R_N^{\max}(\pi)=C_N\ \text{(capacity)},\ \ \arg\min=p^\star_N\ (\to p_J\ \text{as }N\to\infty).
$$

This is the redundancy–capacity result (`redundancy-capacity.md`): `p*` is the
least-favourable / equalizer prior, provably minimax, **at any `d`**.

### 2.3 `A&M`'s `B` is (almost) our worst-case `R` — so they already test that corner

Their worst-case bias pressure `B=max_θ b(θ)` with `b(θ)=D(p(·|θ)‖m_π)−I(\Theta;X)`:

$$
B(\pi)=\max_\theta D\big(p(\cdot\mid\theta)\,\|\,m_\pi\big)-I(\pi)=R_1^{\max}(\pi)-I(\pi),
$$

so `B=0 ⇔ max_θ R = I = C` (the equalizer), achieved by `p*`. **Minimising `B`
is minimising worst-case (one-shot) redundancy** up to the additive `I`. So for
the *worst-case* corner, A&M's criterion and ours coincide (both → `p*`) — good,
that's corroboration. **What A&M do *not* do, and this note targets:** the
**average-case** `R_N^q` under a realistic `q` (§2.1), and the **calibration**
content of `R` beyond the centre (§3).

---

## 3. The real question: does the co-volume bias transfer to a foreign `q`? (and the bias/calibration split)

For the Gaussian manifold model `p(x|θ)=N(y(θ),σ²I)`, approximate the
posterior-predictive as `m_π(x'|x_{1:t})≈N(μ_π,Σ_π)`. Then

$$
D_{\mathrm{KL}}\!\big(N(y(\theta),\sigma^2I)\,\|\,N(\mu_\pi,\Sigma_\pi)\big)=\tfrac12\Big[\underbrace{(\mu_\pi-y(\theta))^{\!\top}\Sigma_\pi^{-1}(\mu_\pi-y(\theta))}_{\text{bias term} \approx\ \text{A\&M's }\Delta^2\ \text{(precision-weighted)}}+\underbrace{\sigma^2\,\mathrm{tr}\,\Sigma_\pi^{-1}-m+\log\frac{\det\Sigma_\pi}{\sigma^{2m}}}_{\text{calibration/spread term}}\Big].
$$

So **`R` ≈ bias term + calibration term**. A&M's `Δ` sees (a precision-weighted
version of) the **bias term only**. The **calibration term** — predictive
covariance `Σ_π` vs the noise `σ²I` — is exactly what `Δ` misses, and is zero
only when the predictive spread matches the noise (you've correctly resolved
`θ`).

**Central question (two parts).** *(a) Transfer of the bias term — the decider.*
A&M show the *bias* term blows up for Jeffreys (`Δ`) on self-sampled data; the
live question is whether the **gap** — `p*`'s `O(1)` bias vs the deployable
non-infomax priors' `O(d)` bias (§1.1) — survives scoring on a **foreign `q`**,
where `p*` is no longer flattered by self-sampling and pays `D(m_q‖m_{p*})`. The
bias term of `R` is the right currency: it equals a precision-weighted `Δ²`, so
it *inherits* A&M's discrimination of the competitors while *also* charging `p*`
for its foreign-`q` mis-centring — exactly what `Δ`-on-`x∼p*` hides. *(b)
Calibration — a secondary refinement.* `p*` is **discrete/atomic**, so its
posterior `Σ_π` can be *lumpy* even where `μ_π` is unbiased; but because the atoms
sit ~1 Fisher length apart **in prediction space by construction**, this
miscalibration is bounded at `O(σ²)` — a constant-factor effect, *not* the `O(d)`
blow-up that lives in the bias term. So calibration can *modulate* the contest at
the boundary but is unlikely to *decide* it; the deciding quantity is the
foreign-`q` transfer of the bias gap. Both are invisible to `Δ`-on-`x∼p*` — that
is what makes the proper held-out score, not `Δ`, the instrument. (The high-`d`
analogue of the §1 1-D betting failure lives in part (b): there `p*`'s discrete
posterior was a bad *belief* under a proper score; here the question is whether
prediction-space tiling keeps that penalty `O(σ²)` rather than `O(d)`.)

Caveats to handle in the maths:
- Reference point: A&M's bias uses `y(θ̂_x)` (MLE, in-sample); the held-out bias
  term uses `y(θ_true)`. Relate them (`θ̂_x ≈` projection of `x`; for held-out
  use `θ_true`).
- The Gaussian-predictive approximation is heuristic for a *discrete* `p*` (its
  true predictive is a finite mixture, not Gaussian); the bias/calibration split
  is still informative but the calibration term should really be the full
  mixture KL.
- Prior washout: `D(m_q‖m_π)` is the `O(1)` prior-mismatch term; it is a
  meaningful fraction of `R_N` only at **finite `N`** (it `→` const while
  `I_q^{(N)}~(d/2)\log N→∞`). So the test must live at finite `N` — exactly the
  "far from asymptopia" regime.

---

## 4. Predicted map (to verify, not assume)

For `π ∈ {p*, p_J, p_U, p_LN, q̄}`, sweeping `d` and `N` (≡ `σ`):

| regime | expected winner | mechanism |
|---|---|---|
| worst-case over `θ`, any `d` | **`p*`** | minimax/equalizer (theorem); `=` A&M `B→0` |
| high-`d`, average-`q` | **`p*`** (on bias) | Jeffreys' co-volume bias `D(m_q‖m_{p_J})` blows up |
| low-`d`, benign-`q`, average | `q̄` / smooth | `p*` pays large `D(m_q‖m_{p*})` (endpoint marginal); §1 |
| any high-`d`, **calibration** | **unknown** | does `p*`'s discreteness spoil `Σ_π`? (§3) |

The genuinely new cell is the last: a proper-score (log-loss) win for `p*` in
high `d` would be the first evidence that its high-`d` *unbiasedness* (A&M)
upgrades to *predictive* goodness.

---

## 5. Maths to work through (checklist)

0. **Go/no-go precondition (the *informative* one — replaces the capacity
   tautology).** The tempting screen — confirm `max_θ R_N(p*_N;θ)=C_N`, flat on
   the support — is the redundancy–capacity **theorem** (`redundancy-capacity.md`;
   `C_1=log2`, `C_2=0.754` nats already in hand). It **cannot fail** modulo a
   code bug, so it gives **zero** go/no-go signal about the open question; keep it
   only as a unit-test of the `p*`/MI machinery, not as a viability gate. (One
   genuine clarification it *does* settle: switching the currency from plug-in
   Kelly to the full mixture predictor removes the §1 `n=1` `+∞` — the design
   loss `D(p(·|θ)‖m_π)` is finite whenever the prior has interior support — so the
   proper score is at least the right *kind* of object. That is coherence, not
   evidence.) The informative precondition is a **two-part falsification screen**
   on the foreign-`q` predictive log-loss itself:
   - *(i) Negative control — flat co-volume ⇒ everyone ties.* In the
     **constant-cross-section** cone (no taper, `r(θ_rel)=const`, so `√det g`
     constant and `b(θ)≡0` for Jeffreys), `p*`, `p_J`, `p_U` must agree on `R`
     within Monte-Carlo error, at every `d`. **If `p*` "wins" here it is a bug**
     (or the estimator is rigged): with no co-volume pathology to avoid, no prior
     can beat another on the prior-dependent term `D(m_q‖m_π)`.
   - *(ii) Sign-of-advantage under non-cooperative `q`.* Sweep `q` from
     **cooperative** (`q≈m_{p*}`, mass where `p*` expects it) to
     **non-cooperative** (mass at the thin end / in `p*`'s atom gaps). `p*` wins
     the cooperative end by self-sampling, *of course*; the question is whether
     its advantage over the **best deployable non-infomax prior** persists into
     the non-cooperative range. **`p*` wins across realistic `q` ⇒ the
     `O(d)`-vs-`O(1)` gap transfers (positive result). `p*` wins only for
     `q≈m_{p*}` ⇒ the effect is self-served and A&M's verdict does not generalise
     (a clean negative).**
   - *Why this is the right gate:* its outcome is **genuinely unknown today**
     (unlike the capacity theorem), it is the cheapest probe of the *actual* open
     claim, and it is built to detect the experiment's own failure modes —
     estimator bias via the control, and predetermined-by-`q` confounding via the
     sweep (the F1 pathology of `specs/001-infomax-betting-redteam_third.md`,
     where the headline was fixed by an unstated hyperprior-shape choice).
   - **Run this first; only if (i) holds and (ii) shows life beyond `q≈m_{p*}` do
     items 1–5 carry weight.**

1. **Compensation identity** `R_N^q(π)=I_q+D(m_q‖m_π)` — verify the `N`-fold
   version and the prior-washout `O(1)` claim. (§2.1)
2. **Bernoulli sanity check (1-D).** Compute `D(m_q‖m_π)` for
   `π∈{p*_n, p_J, p_U, q̄}`, `q=Beta(c,c)`: confirm `p*` pays a large marginal
   mismatch under benign interior `q` (recovers §1), and check whether the
   worst-case `R^max` flips to favour `p*` (it should). Cross-check against the
   `n=1,2` numbers in `redundancy-capacity.md`.
3. **Bias/calibration split** (§3): derive it cleanly for the Gaussian manifold,
   relate the bias term to `Δ²`, and decide how to *measure the calibration term
   for a discrete `p*`* (full mixture KL, or PIT / reliability in simulation).
4. **`B = R₁^max − I`** (§2.3): confirm, and decide whether to report `B`
   (distance-from-equalized) or `R^max` (worst-case loss) — same `arg\min`.
5. **Estimators** for the eventual experiment: posterior-predictive log-loss via
   the sequential predictive (telescoping), worst-case via the equalizer/BA, and
   `D(m_q‖m_π)` via Monte-Carlo on the marginals. (A&M's `AtomicPriors.jl` finds
   `p*`; our repo has BA for the discrete case.)

## 6. Experiment design: locate the boundary, don't maximise the effect

**Framing (MB).** A&M go for **dramatic effect** (`d=26`, `Δ>20σ`) to make the
phenomenon unmissable. We want the opposite: the **minimal structural settings**
where the same effect is *just* visible (presumably to a small degree), and on
each structural axis the **boundary** separating `p*` *useful* from *useless* as
an epistemic prior. **Dimension is not the axis** — independent high-`D` (100
separable bets) is the null; the axes are the likelihood **structure**
(scale hierarchy + coupling), per the §6/§7.3 anisotropy argument of the
two-hats note.

### 6.1 What "useful" means — two reference comparisons, two order parameters

- **(i) `p*` vs the pathological default (Jeffreys).** Onset of *any* co-volume
  bias. Order parameter: A&M's **`B = max_θ b(θ) > 0`** — *prior-only, `q`-free,
  cheap* (their `AtomicPriors.jl`). Boundary sits at **zero coupling**
  (block-diagonal / independent ⇒ `B=0` ⇒ `p*=p_J`). Necessary but weak:
  beating a broken default ≠ being a good belief.
- **(ii) `p*` vs the best *deployable smooth* default** (uniform-`θ`,
  log-normal) on **held-out log-loss** — the meaningful line, where `p*`'s
  *benefit* (avoiding the co-volume bias) finally exceeds its *cost* (the
  discreteness / endpoint miscalibration that sank it in §1, i.e. the §3
  calibration term). The **matched `q̄` is the ceiling, not a competitor**: by
  §2.1 it achieves the floor `I_q`, so `p*` can *never* beat it average-case —
  the gap `p*→q̄` measures only the room left. *Caveat:* boundary (ii) depends
  on the test `q`; report it as a function of `q` (or fix a canonical one — the
  model's own measure, or `q̄`).

Region between (i) and (ii): "`p*` beats the broken Jeffreys but is still a worse
belief than a plain smooth prior." Beyond (ii): "`p*` is the best deployable
epistemic prior." The §1 regime is *below* (ii); A&M's `d=26` is far *beyond* it.

### 6.2 Structural axes to sweep (deconfounded), with the expected boundary

1. **Coupling / co-volume gradient** (the irrelevant scale *varying along* the
   relevant directions — the hypercone taper `r(θ_rel)`): the **necessary**
   ingredient. Boundary (i) at taper `=0`. **Negative control:** constant
   cross-section / independent dims ⇒ `B=0`, log-loss gap `=0`. *If `p*` "wins"
   there, it's a bug.*
2. **Scale-hierarchy depth / sloppiness** (spectrum slope; # directions with
   Fisher length `L<1`): more/steeper ⇒ more co-volume to misweight ⇒ boundary
   (ii) reached sooner. Sweep **at fixed `d`** to deconfound from dimension —
   A&M never do this (their `d`-sweep silently deepens the spectrum, since
   exp-decay eigenvalues `∝10^{-d}`).
3. **Anisotropy / rotation** of the resolvable directions off the parameter
   axes: hurts *coordinate* priors (uniform-`θ`) specifically; isolates
   geometry-driven from coordinate-driven bias.
4. **Data budget `N`/`σ`** (the finite-data axis): the *average-case* advantage
   **vanishes as `N→∞`** (interior posteriors agree, `I_J→I*`; only a worst-case
   boundary bias `B_J↛0` persists). So there is an **upper-`N` boundary** past
   which `p*` stops being needed — and it is *exponential in `d`* for sloppy
   models (`~10^d` reps; "far from asymptopia"). The useful regime is small `N`.
5. **Dimension `d`** (last, axes 1–4 fixed): in the hypercone `Δ=(d−1)/x`, so the
   effect is **continuous from `d=2`** — *no sharp onset in `d`*. Confirms `d` is
   a magnitude knob, not the boundary variable.

### 6.3 Minimal model

Smallest setting that already shows it: **`d=2`, one relevant + one irrelevant,
coupled (tapering)** — A&M's own Fig. 1 model, which they use only to
*illustrate*. There the bias is tiny (hypercone `Δ=(d−1)/x ≈ 0.1σ` at `d=2`),
which is exactly why it's the right place to **locate boundary (ii)** (does `p*`
beat a smooth prior on held-out log-loss when the effect is *small*?) rather than
to dramatise.

**Caveat — the bare hypercone is a strawman for `p_U`/`p_LN`.** In the
*axis-aligned* hypercone the relevant coordinate **is** `θ₁`, so a prior uniform
in `θ` projects to *flat* on `θ₁` and is **unbiased** — only Jeffreys (which
carries the `θ₁^{d−1}` co-volume) is a victim. A `p*` win there is a win over
Jeffreys *only*, i.e. A&M re-derived, and reproduces the F1 trap (a contest whose
answer is fixed by an unstated modelling choice). To make uniform-`θ` and
log-normal genuine competitors that *also* fail, the relevant direction must be
**misaligned with the parameter coordinates** — a fixed **rotation/shear** of the
embedding, or genuine **curvature** of `y(θ)` (A&M's uniform/log-normal failures
live in the *curved* exp-decay and enzyme models, not in the cone). So the
minimal *non-vacuous* model is **taper (⇒ Jeffreys fails) + non-alignment (⇒
coordinate priors fail)**: coupling buys one victim, rotation/curvature buys the
rest. Build the controlled family on the **hypercone with a tunable rotation**
(tunable taper + spectrum + rotation; closed-form `Δ=(d−1)/x` retained as the
calibration cross-check on the relevant axis), with the **constant-cross-section /
independent-dims null** as the negative control (§5.0 (i)). The curved exp-decay
model (A&M Eq. 6) is the realistic companion where all three deployable priors
demonstrably fail.

### 6.4 A positive result, stated minimally

A `d=2`–small-`d` model, moderate `σ`, *modest* (single-digit-`σ`, not `20σ`)
Jeffreys bias, in which **`p*`'s held-out log-loss beats every deployable smooth
default and lands close to the `q̄` ceiling** — boundary (ii) crossed in an
undramatic setting. That would show the effect is **generic and graded**, not a
high-`d` curiosity, and would be the first evidence `p*` is a good *epistemic*
prior off the worst-case corner. Conversely, if boundary (ii) only ever crosses
at large `d`/steep sloppiness, that *localises* `p*`'s epistemic usefulness to
the extreme regime — itself a clean, publishable negative.

**Slogan for the note:** *A&M proved `p*` puts the prediction in the right
place (unbiased centre) in high `d`; the open question is whether it also gets
the prediction's spread right (calibration) — and only a proper log-loss score,
not `Δ`, can see that.*
