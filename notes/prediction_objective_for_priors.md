# A predictive-scoring objective for testing `p*` as an inference prior

*Created 2026-05-31. Status: working note / maths development (not a spec).*

**Purpose.** Abbott & Machta ("Far from Asymptopia", *Entropy* 2023) show that
in high `d` the finite-data infomax prior `p*` is *unbiased* in prediction space
while Jeffreys (and other fixed continuous priors) are catastrophically biased.
But their score is a **bias of the posterior's centre** (`Δ`, below), in-sample
and self-consistent — *not* a proper predictive scoring rule. This note builds
the **held-out posterior-predictive log-loss (= redundancy)** objective under
which one could test, systematically, whether `p*` is a good *inference* prior —
and isolates the one question their `Δ` cannot answer. It is the maths behind
§10 offer 5 / §4 of `notes/infomax_two_hats_and_directions.md`, and leans on
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
| `p*` by construction | unbiased (`b=0`) | **unknown — the open question** |

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

## 3. The open question: does `Δ`-unbiased ⇒ `R`-good? (bias vs calibration)

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

**Central question.** A&M show `p*` controls the **bias** term in high `d`
(`Δ≈0`, by `b=0`). Does `p*` *also* control the **calibration** term? `p*` is
**discrete/atomic**, so its posterior — and hence `Σ_π` — can be *lumpy*
(over- or under-dispersed) even where the centre `μ_π` is unbiased. If the
calibration term is large, `p*` could be `Δ`-unbiased yet `R`-bad — the high-`d`
analogue of the §1 1-D betting failure (where `p*`'s discrete posterior is a bad
*belief* under a proper score, even when its mean is not crazy). **This is the
thing to settle, and it is invisible to `Δ`.**

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

**Slogan for the note:** *A&M proved `p*` puts the prediction in the right
place (unbiased centre) in high `d`; the open question is whether it also gets
the prediction's spread right (calibration) — and only a proper log-loss score,
not `Δ`, can see that.*
