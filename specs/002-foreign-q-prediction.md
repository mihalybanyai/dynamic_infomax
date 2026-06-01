# Spec 002 — Does the infomax prior's high-`d` unbiasedness transfer to a foreign nature? (held-out predictive log-loss in ribbon geometry)

| Section | Status | Date |
|---|---|---|
| [0. Context](#0-context) | draft | — |
| [Generative model](#generative-model) | draft | — |
| [1. Setup](#1-setup) | draft | — |
| [2. Objective](#2-objective) | draft | — |
| [3. Derivation](#3-derivation) | draft | — |
| [4. Algorithm](#4-algorithm) | draft | — |
| [5. Properties to verify](#5-properties-to-verify) | draft | — |
| [6. Report](#6-report) | draft | — |
| [7. Open questions](#7-open-questions) | draft | — |
| [8. References](#8-references) | draft | — |
| [9. Derivations](#9-derivations) | draft | — |
| [10. Revision log](#10-revision-log) | n/a | — |

## 0. Context

Spec 000 reproduced the static infomax prior `p*` (discrete, `~√n` atoms, `→`
Jeffreys); spec 001 scored it as a *betting belief* and found it loses to smooth
priors — diagnosed in `notes/infomax_two_hats_and_directions.md` as a **two-hat
category error** (a *design* / least-favourable object scored as an *inference*
belief). Abbott & Machta (2023, "Far from Asymptopia") make the opposite-seeming
claim: in high-`d` ribbon-geometry models, fixed "uninformative" priors (Jeffreys,
and they show log-normal too) carry an enormous **posterior bias** from the
irrelevant *co-volume*, which the data-adapted `p*` avoids. But their score is the
posterior-centre deviation `Δ`, evaluated **on data drawn from `p*` itself**
(`x ∼ p*`), and their `b(θ)=0` is the self-referential equalizer/KKT condition —
so what they establish is that `p*` codes *its own* source unbiasedly, not that it
infers a *foreign* nature `q` well.

This spec tests the one thing that separation leaves open. It is **not** "is `p*` a
good epistemic prior" — under a strictly proper score `p*` is dominated by the
matched prior `q̄` *by theorem* (the compensation identity, §3.1), and `p*` is a
design object by construction. It is the **transfer** question stated in
`notes/prediction_objective_for_priors.md` §0/§3:

> Does the high-`d`, coupled, ribbon-geometry setting create a difficulty that
> bites *deployable non-infomax* priors (Jeffreys, uniform-`θ`, log-normal)
> **disproportionately** — a co-volume pathology `p*` is structurally less
> sensitive to — and does that advantage **transfer** to held-out predictive
> accuracy under a *foreign* `q`, scored by a proper rule, rather than evaporating
> once `p*` is no longer flattered by self-sampling?

The transfer is expected to be **asymmetric** (note §1.1): the *badness* of the
deployable priors is a pointwise posterior property (hypercone bias `Δ=(d−1)/x`,
`O(d)`, independent of how the data was generated), while `p*`'s near-zero `Δ` is
partly self-served (its pointwise bias is `O(1)`, set by atom spacing, but on
foreign `q` it pays the marginal-mismatch `D(m_q‖m_{p*})`). The experiment measures
whether the `O(d)`-vs-`O(1)` gap survives, and — crucially — is built to detect its
own failure modes via a **negative control** (flat co-volume ⇒ everyone ties) and a
**cooperativeness sweep** over `q` (does `p*` win only when nature lives where it
expects?), so the answer is not predetermined by an unstated `q`-choice — the F1
pathology of `specs/001-infomax-betting-redteam_third.md`.

This is the project's **first multi-parameter spec** (deferred from spec 000 §0).
`q̄` appears only as a **reference ceiling**, not a competitor.

## Generative model

![Generative model](../diagrams/002-foreign-q-prediction-pgm.svg)

This diagram is the *external environment* (nature), **not** what the agent
assumes — same convention as spec 001. A q-family knob `c` fixes which foreign
nature `q` is drawn (swept from *cooperative* to *non-cooperative*, §4.3); for each
of `S_q` draws, the truth `θ ∼ q`; the agent conditions on `N` training
observations `x_i ∼ p(x|θ)` and is scored on a fresh held-out `x' ∼ p(x|θ)`. The
likelihood geometry — prediction map `y(θ)`, noise `σ`, dimension `d`, taper,
rotation — is fixed across draws and described in §4.1, not drawn.

The agent's prior `π ∈ {p*, p_J, p_U, p_LN}` (with `q̄` as a reference ceiling) is
**decoupled from `q`**: it is chosen from the likelihood geometry and the data
budget `N`/`σ` alone, exactly as in spec 001. That decoupling (agent ≠ nature) is
the whole point — it is what lets the held-out score test transfer rather than
self-consistency. The agent's prior is therefore omitted from this nature-only
diagram.

## 1. Setup

| Symbol | Meaning |
|---|---|
| `d` | Number of model parameters (the dimension being stressed). |
| `θ ∈ Θ ⊂ ℝ^d` | Parameter vector. `Θ` a compact box (per model, §4.1). |
| `m` | Number of observation times / output coordinates. |
| `y(θ) ∈ ℝ^m` | Prediction (mean-data) map; the model manifold is `{y(θ) : θ ∈ Θ}`. |
| `σ` | Gaussian observation-noise scale. Sets the data budget: `M` repetitions ≡ `σ/√M` (A&M §2.1). |
| `p(x\|θ)` | Likelihood `= 𝒩(y(θ), σ²I_m)`, `x ∈ ℝ^m`. |
| `N` | Data budget: number of i.i.d. training observations `x_i ∼ p(·\|θ)`. |
| `X_{1:N}` | The training sample `(x_1, …, x_N)`. |
| `x'` | A fresh held-out observation `∼ p(·\|θ)` (the single-step diagnostic). |
| `g(θ)` | Fisher information metric, `g_{μν}(θ) = σ^{-2} Σ_t ∂_μ y_t ∂_ν y_t` (Gaussian, §4.1). |
| `L` | A Fisher length `∫√{ds²}`; "relevant" if `L>1`, "irrelevant" if `L<1`. |
| `q` | Nature's distribution over `θ` (the *foreign* truth). |
| `c` | The q-family cooperativeness knob (§4.3): `c=0` cooperative (`q≈m_{p*}`-pullback), `c=1` non-cooperative. |
| `m_q(X_{1:N})` | Nature's `N`-fold data marginal `= ∫ p(X_{1:N}\|θ) q(dθ)`. |
| `π` | Agent's prior, one of `{p*, p_J, p_U, p_LN, q̄}`. |
| `p*` | Infomax / capacity-achieving prior, `argmax_π I(Θ;X)` (§4.2). Discrete. |
| `p_J` | Jeffreys prior `∝ √{det g(θ)}`, normalised on `Θ`. |
| `p_U` | Uniform on the parameter box `Θ`. |
| `p_LN` | Log-normal in `θ` (A&M Eq. 10): `∝ Π_μ e^{-(θ_μ-θ̄)²/2σ̄²}`. |
| `q̄` | The hyper-averaged matched prior `= 𝔼_c[q]` (reference ceiling only, §2.3). |
| `m_π(X_{1:N})` | Agent's Bayes mixture `= ∫ p(X_{1:N}\|θ) π(dθ)`. |
| `π(θ\|X_{1:N})` | Posterior under prior `π`. |
| `I(Θ;X)` | Mutual information `= 𝔼_π D_{KL}(p(x\|θ)‖m_π)`. |
| `C` | Channel capacity `= sup_π I(Θ;X)`. |
| `b(θ)` | Bias pressure `= D_{KL}(p(x\|θ)‖m_π) − I(Θ;X)` (A&M Eq. 5). |
| `Δ(x)` | Posterior deviation `= σ^{-1}\|y(θ̂_x) − 𝔼_{π(θ\|x)} y(θ)\|` (A&M Eq. 9). |
| `R_N^q(π)` | The headline score: redundancy / cumulative held-out predictive log-loss (§2.1). |
| `I_q^{(N)}` | Matched floor `= 𝔼_{θ∼q} D_{KL}(p(X_{1:N}\|θ)‖m_q)` (prior-independent). |
| `G` | Per-axis grid resolution for the discrete `p*` solver (§4.2). |

All logs in nats; bits `= nats/log 2` at report time.

## 2. Objective

### 2.1 The score: redundancy = cumulative held-out predictive log-loss

The agent with prior `π` predicts the data through its Bayes mixture `m_π`. The
**redundancy** of `π` against a foreign nature `q`, over budget `N`, is

$$
R_N^q(\pi) \;=\; \mathbb{E}_{\theta\sim q}\,\mathbb{E}_{X_{1:N}\sim p(\cdot\mid\theta)}\Big[\log p(X_{1:N}\mid\theta) - \log m_\pi(X_{1:N})\Big]
\;=\; \mathbb{E}_{\theta\sim q}\,D_{\mathrm{KL}}\!\big(p(X_{1:N}\mid\theta)\,\|\,m_\pi(X_{1:N})\big). \tag{2.1.1}
$$

This is a **strictly proper** score (Gneiting & Raftery 2007), it is the
oracle-relative excess log-loss, and by the chain rule it equals the **cumulative
one-step-ahead predictive log-loss regret** `Σ_t 𝔼 D_{KL}(p(·|θ)‖m_π(·|X_{1:t}))`
(`tutorials/math/redundancy-capacity.md`; note §1.2, §4). It is the proper-score
upgrade of A&M's `Δ`: it scores the *full* predictive distribution, *held-out*, and
— unlike `Δ`-on-`x∼p*` — under a *foreign* `q`.

By the **compensation identity** (Topsøe 1979), applied to the `N`-fold marginals,

$$
\boxed{\;R_N^q(\pi) \;=\; \underbrace{I_q^{(N)}}_{\text{matched floor, }\pi\text{-free}} \;+\; \underbrace{D_{\mathrm{KL}}\!\big(m_q \,\|\, m_\pi\big)}_{\text{the only }\pi\text{-dependent term}}\;}\tag{2.1.2}
$$

with `I_q^{(N)} = 𝔼_{θ∼q} D_{KL}(p(X_{1:N}|θ)‖m_q)` (§9.1). So the entire
prior-dependence of the held-out predictive loss is the **marginal mismatch**
`D(m_q‖m_π)` — how far the prior's Bayes-mixture data-marginal sits from nature's.
The contest between two priors is exactly

$$
\Delta R(\pi,\pi') \;=\; R_N^q(\pi) - R_N^q(\pi') \;=\; D_{\mathrm{KL}}(m_q\|m_\pi) - D_{\mathrm{KL}}(m_q\|m_{\pi'}). \tag{2.1.3}
$$

### 2.2 What "wins" means — and what cannot be asserted

`p*` is interesting here **only** if its marginal `m_{p*}` sits closer to a foreign
`m_q` than the *best deployable non-infomax prior*'s does — i.e. if avoiding the
co-volume bias (real, `O(d)`, §3.3) outweighs the foreign-`q` mismatch it pays
(`O(1)` atom spacing + `D(m_q‖m_{p*})`). The headline statistic is therefore
`min_{π' ∈ {p_J, p_U, p_LN}} ΔR(p*, π')` — the gap from `p*` to the **best**
deployable competitor — as a function of `(d, σ, taper, rotation, c)`.

We **cannot** assert the sign of this gap and must not: that `p*` wins is the open
question. Asserting it would make the experiment unfalsifiable (§5 states this
explicitly). The test suite asserts only the *machinery* (decomposition,
construction, controls), never the headline.

### 2.3 `q̄` is the ceiling, not a competitor

Two floors must be kept distinct. *Per cell* (fixed `c`, nature `= q_c`), the floor
of `R_N^q` is the matched value `I_q^{(N)}`, attained by the prior whose marginal
matches *that* `q_c` (its own pullback) — not by `q̄`. *Across the `c`-sweep*, by
(2.1.2) the single fixed prior minimising the **`c`-averaged** `R` is the one whose
marginal matches nature's hyper-average, `m_π = 𝔼_c[m_q]` — i.e.
`q̄ = 𝔼_c[q]` (hierarchical/empirical Bayes; note §5.3). So `q̄` lower-bounds the
**`c`-averaged** `R` over all fixed priors: `p*` **cannot** beat it on the
`c`-average. `q̄` is plotted as the **reference ceiling** (the best deployable
fixed prior); the gap from each fixed prior up to `q̄` measures how much it loses by
not being matched. "Does `p*` beat `q̄`" is a non-question.

### 2.4 The falsification structure (the §5.0 go/no-go of the note)

Two screens decide whether the effect is real or self-served, replacing the
redundancy-capacity *tautology* (which cannot fail and is demoted to a unit test,
T3):

- **Negative control (flat co-volume ⇒ everyone ties).** In the constant-cross-
  section model (no taper, §4.1), `√det g` is constant, `b(θ)≡0`, and there is no
  co-volume pathology to avoid: `R_N^q(p*) = R_N^q(p_J) = R_N^q(p_U)` within
  Monte-Carlo error, at every `d`. **If `p*` "wins" here, the result is an
  artefact** (T2).
- **Sign-of-advantage vs cooperativeness `c`.** `p*` wins the cooperative end
  (`c=0`, `q≈m_{p*}`) by self-sampling, trivially. The reported quantity is whether
  `min_{π'} ΔR(p*,π') < 0` *persists* into the non-cooperative range (`c→1`). Win
  across realistic `c` ⇒ transfer (positive result); win only at `c≈0` ⇒
  self-served (clean negative). This is a **reported curve**, not a pass/fail test.

## 3. Derivation

### 3.1 The compensation identity and why `q̄` is the floor

For any predictor `q_A` over the data, `𝔼_{θ∼π} D(p(·|θ)‖q_A) = I_π + D(m_π‖q_A)`
with equality-minimiser `q_A=m_π` (Topsøe 1979; `redundancy-capacity.md`). Applied
with the *expectation under nature* `q` (not the agent's `π`) and the `N`-fold
likelihood, the term that survives as prior-dependent is `D(m_q‖m_π)`, giving
(2.1.2). Full steps in §9.1. The minimiser over fixed priors of the hyper-average
is `m_π = 𝔼_c[m_q]`, attained by `π=q̄` (§2.3) — the proof that `p*` cannot win
average-case.

### 3.2 The Gaussian bias/calibration split

For a Gaussian manifold model, approximate the posterior-predictive as
`m_π(x'|X_{1:N}) ≈ 𝒩(μ_π, Σ_π)` (heuristic for discrete `p*`, whose true predictive
is a finite mixture — see §3.5 caveat). Then the per-step held-out loss is

$$
D_{\mathrm{KL}}\!\big(\mathcal{N}(y(\theta),\sigma^2 I)\,\|\,\mathcal{N}(\mu_\pi,\Sigma_\pi)\big)
= \tfrac12\Big[\underbrace{(\mu_\pi-y(\theta))^{\!\top}\Sigma_\pi^{-1}(\mu_\pi-y(\theta))}_{\text{bias term}}
+ \underbrace{\sigma^2\,\mathrm{tr}\,\Sigma_\pi^{-1}-m+\log\tfrac{\det\Sigma_\pi}{\sigma^{2m}}}_{\text{calibration term}}\Big]. \tag{3.2.1}
$$

The **bias term** is a precision-weighted `Δ²` (A&M's quantity, up to weighting);
the **calibration term** — predictive spread `Σ_π` vs noise `σ²I` — is exactly what
`Δ` cannot see. Always `Σ_π = σ²I + \mathrm{Cov}_\pi[y(θ)|X_{1:N}] \succeq σ²I`, so
the predictive is over-dispersed by the residual posterior uncertainty about the
prediction.

### 3.3 The asymmetry: `O(d)` competitor bias vs `O(1)` `p*` bias

**Hypercone (A&M Appendix A.1; reproduced in §9.2).** One relevant coordinate
`θ_1` (length `L`), `d−1` irrelevant tapering directions, `√det g ∝ θ_1^{d-1}`, so
Jeffreys' effective marginal `p_J(θ_1) ∝ θ_1^{d-1}`. The posterior under `p_J` for
an observation at relevant-coordinate value `x` (with `1 ≪ x ≪ L`) has mean
deviation

$$
\Delta \;=\; \big|\langle\theta_1\rangle_{p_J(\theta_1\mid x)} - x\big| \;=\; \frac{d-1}{x} + O\!\big(x^{-3}\big). \tag{3.3.1}
$$

This is a **pointwise** posterior property: it does not reference `p*` or `q`, and
it is *largest at the thin end* (`x` small) — precisely where an interior/edge
foreign `q` places data. Hence the deployable priors' bias **transfers** to any
foreign `q` and grows like `O(d)`.

`p*`'s posterior is a finite mixture over atoms ≈ 1 Fisher length apart **in
prediction space**, so its worst-case pointwise bias is bounded by the atom
spacing, `O(1)` in noise units, *independent of `d`* (it tiles the relevant
subspace and collapses the irrelevant ones — A&M Fig. 5). Self-sampling (`x∼p*`)
lands data on the atoms (bias `≈0`); a foreign `q` can land data in atom gaps, so
`p*` pays `O(1)` + the marginal mismatch `D(m_q‖m_{p*})` of (2.1.2). The experiment
asks whether the resulting net favours `p*` once the self-sampling flattery is
removed.

### 3.4 Calibration is bounded, so the bias term decides

Because `p*`'s atoms are ~1 Fisher length apart in prediction space, its
calibration term (3.2.1) is `O(σ²)` even in atom gaps — a constant-factor effect,
not the `O(d)` blow-up that lives in the bias term. A smooth well-specified prior
gives the same `O(σ²)` order. So calibration *modulates* the boundary but does not
*decide* the contest; the decider is the foreign-`q` transfer of the bias gap (note
§3). The calibration term is reported (a PIT/over-dispersion diagnostic, §6) but is
not the headline.

### 3.5 Caveats carried into the algorithm

- **Reference point.** A&M's `Δ` uses the in-sample MLE `θ̂_x`; the held-out bias
  term (3.2.1) uses `y(θ_true)`. For held-out data `θ̂_{x'} ≈` projection of `x'`;
  we score against `y(θ_true)` throughout. The hypercone closed form (3.3.1) is the
  in-sample reference and is used only as the calibration *cross-check* (T6), not
  as the score.
- **Discrete predictive.** The Gaussian-predictive approximation in §3.2 is
  heuristic for the discrete `p*`; its true predictive is a finite Gaussian
  mixture. The score (2.1.1) is computed from the *exact* mixture, not the Gaussian
  approximation — the split (3.2.1) is interpretive, used for the diagnostic
  decomposition, not for the headline number.
- **Finite `N`.** The mismatch `D(m_q‖m_π)` is the `O(1)` term that washes out as
  `N→∞` (interior posteriors agree, `I_q^{(N)}~(d/2)\log N → ∞`). The test must live
  at **finite `N`** — the "far from asymptopia" regime.

## 4. Algorithm

### 4.1 Model families

All three share the Gaussian likelihood `p(x|θ)=𝒩(y(θ),σ²I_m)` and FIM
`g_{μν}(θ)=σ^{-2}Σ_t ∂_μ y_t ∂_ν y_t`.

1. **Exponential-decay (primary; A&M Eq. 6).**
   `y_t(θ) = Σ_{μ=1}^d a_μ e^{-k_μ t}`, `k_μ = e^{-θ_μ}`, `a_μ = 1/d`, observed at
   `m` times `t`. `∂_μ y_t = a_μ t k_μ e^{-k_μ t}` (closed-form FIM, §9.3). This is
   the model where uniform-`θ` and log-normal demonstrably fail (curved manifold,
   relevant directions not coordinate-aligned), and the eye-test anchor (A&M
   Fig. 5).
2. **Square hypercone (analytic companion; A&M Appendix A.1).**
   `y(θ) = (θ_1, r θ_2, …, r θ_d)`, `r(θ_1)=θ_1/L`, `0≤θ_1≤L`, `0≤θ_μ≤1`. Gives the
   closed-form `Δ=(d−1)/x` (3.3.1) for the calibration cross-check (T6). A **tunable
   rotation** `θ ↦ Q θ` of the embedding (orthogonal `Q`, angle swept, §5 sweep)
   moves the relevant direction off the coordinate axes so that uniform-`θ` is no
   longer trivially unbiased (note §6.3) — making it a fair competitor in the
   controlled model too.
3. **Constant-cross-section cone (negative control).** As (2) but `r(θ_1)=r_0`
   constant (taper `=0`): `√det g` constant, `b(θ)≡0`, no co-volume gradient.

### 4.2 Prior construction

- **`p*` — discrete infomax prior.** *Primary method (small `d`):* multi-dimensional
  Blahut–Arimoto on a `θ`-grid of `G` cells per axis, generalising spec 000's 1-D
  solver, with the continuous-output `f_KL(θ)=D(p(x|θ)‖m_π)` estimated by the
  kernel-density approximation of A&M Appendix A.2 (Eq. A1) or by Monte-Carlo over
  `x`. *Cross-check / larger `d`:* atomic optimisation (L-BFGS over atom positions
  and weights) per A&M Appendix A.2, i.e. the method of `mcabbott/AtomicPriors.jl`.
  The two methods must agree on `R` (T7b) where both are feasible. **The `p*`
  solver is the principal new infrastructure and the main feasibility risk — see
  §7 OQ-1.**
- **`p_J` — Jeffreys.** `∝ √det g(θ)`, normalised over `Θ` by grid quadrature.
  Closed-form FIM from §4.1; in the hypercone, cross-checked against the analytic
  `p_J(θ_1) ∝ θ_1^{d-1}` (T4).
- **`p_U` — uniform** on the box `Θ`.
- **`p_LN` — log-normal** in `θ` (A&M Eq. 10), `θ̄=0`, `σ̄=1` per coordinate
  (auto-chosen; please confirm — see §7 OQ-3).
- **`q̄` — reference ceiling** `= 𝔼_c[q]`, computed from the q-family (§4.3).

### 4.3 Foreign-`q` family

`q` is a distribution over `θ` parameterised by a **cooperativeness** knob
`c ∈ [0,1]`, interpolating between two anchors **defined in prediction space** then
pulled back to `Θ`:

- `c=0` (**cooperative**): `q` places `θ` so that `y(θ)` is ≈ uniform over the
  *distinguishable* predictions — i.e. `m_q ≈ m_{p*}` (nature lives where `p*`
  expects). 
- `c=1` (**non-cooperative**): `q` concentrates on the *thin end* of the manifold
  and in the *gaps between `p*`'s atoms* (nature lives where `p*` does not expect).

Implemented as a mixture `q_c = (1−c)·q_{coop} + c·q_{non}`. **The exact
parameterisation of `q_{coop}`/`q_{non}` is an open choice (§7 OQ-2); it must span
cooperative→non-cooperative and is reported per-sample so results can be subset by
`q`-shape.** No other randomness enters the model.

### 4.4 Score estimation

For each cell `(model, d, σ, taper, rotation, c)`:

```
1.  Build y(·), FIM g(·) on the θ-box.
2.  Construct priors: p* (BA / atomic), p_J ∝ √det g, p_U, p_LN, q̄.
3.  For s = 1 .. S_q:
        θ_s        ~ q_c                                   # nature's truth
        X_{1:N}    ~ p(·|θ_s)          (N i.i.d. draws)    # training sample
        for each prior π:
            log m_π(X_{1:N}) = log ∫ p(X_{1:N}|θ') π(dθ')   # mixture marginal
            R_s(π)  = log p(X_{1:N}|θ_s) − log m_π(X_{1:N})  # per-sample redundancy
        record R_s(π) for all π, plus q-sample metadata.
4.  R_N^q(π) = mean_s R_s(π);  report MCSE.
5.  Decomposition cross-check: estimate I_q^{(N)} and D(m_q‖m_π) separately,
        verify R_N^q(π) = I_q^{(N)} + D(m_q‖m_π)  (T1).
```

**`m_π(X_{1:N})` evaluation.** Discrete `p*`: exact finite sum
`logsumexp_a [log λ_a + log p(X_{1:N}|θ_a)]`. Continuous priors: grid quadrature
over `Θ` for small `d`; for the badly-behaved case where `X_{1:N}` is far from the
prior's mass (A&M Appendix A.4), Bennett's method / importance sampling. All in
log-space.

**Single-step held-out diagnostic.** Optionally draw a fresh `x' ∼ p(·|θ_s)` after
the `N` training draws and record the one-step loss `−log m_π(x'|X_{1:N})` and the
PIT of `x'` under `m_π(·|X_{1:N})` — feeds the calibration diagnostic (§3.4, §6).

**Randomness.** One child RNG per cell, spawned from a single experiment seed
(`manage-randomness.md`); BA itself is deterministic. Seed pinned in §5 Sweep
design.

## 5. Properties to verify

Test functions live in `tests/test_002_foreign_q_prediction.py`. The suite pins the
*machinery*; it deliberately does **not** assert the headline (§2.2).

### 5.1 Property-to-tests table

| # | Property (spec §) | Verified by |
|---|---|---|
| P1 | Redundancy decomposition `R_N^q(π) = I_q^{(N)} + D(m_q‖m_π)` (§2.1, §3.1) | `test_t1_redundancy_decomposition` |
| P2 | **Negative control**: flat co-volume ⇒ `R(p*)=R(p_J)=R(p_U)` within MCSE, all `d` (§2.4) | `test_t2_negative_control_ties` |
| P3 | `p*` machinery (demoted tautology): equalizer `b(θ)=0` on `supp(p*)`, `≤0` off; `I_{p*}=C` (§2.4, §4.2) | `test_t3_pstar_equalizer` |
| P4 | Jeffreys construction: `p_J ∝ √det g` normalises; matches analytic `θ_1^{d-1}` in hypercone (§4.2) | `test_t4_jeffreys_construction` |
| P5 | Gaussian KL closed form (3.2.1) matches numeric KL of two Gaussians (§3.2) | `test_t5_gaussian_kl_split` |
| P6 | Hypercone closed-form `Δ=(d−1)/x` matches numeric `p_J`-posterior deviation, `1≪x≪L` (§3.3, §9.2) | `test_t6_hypercone_delta` |
| P7a | `m_π(X_{1:N})`: discrete sum (p*) vs quadrature agree (§4.4) | `test_t7a_mixture_marginal_consistency` |
| P7b | `p*` solver: grid-BA vs atomic agree on `R` where both feasible (§4.2) | `test_t7b_pstar_method_agreement` |
| P8 | Floors: `R_N^q(π) ≥ I_q^{(N)} ≥ 0` per cell; `q̄` minimises the **`c`-averaged** `R` (§2.3) | `test_t8_floors` |
| P9 | A&M prior-side reproduction: `I_{p*}(d) ≥ I_{p_J}(d)` and `B_{p*}(d) ≤ B_{p_J}(d)`, all `d` (§0; A&M Fig. 5) | `test_t9_am_prior_side_dominance` |
| P10 | Determinism: fixed seed ⇒ identical `R` arrays across runs (§4.4) | `test_t10_seed_determinism` |
| — | **Headline** `min_{π'} ΔR(p*,π') < 0` under non-cooperative `q` | *not tested — the open question; asserting it would make the experiment unfalsifiable (§2.2)* |

### 5.2 Test descriptions

**T1 — Redundancy decomposition.** For a fixed cheap cell, estimate `R_N^q(π)`
directly via (2.1.1) and independently via `I_q^{(N)} + D(m_q‖m_π)` (separate MC of
each term); assert agreement within combined MCSE. Defends against a mis-derived or
mis-estimated score — the single tightest check that the headline quantity means
what §2.1 says.

**T2 — Negative control.** In the constant-cross-section model (§4.1.3) at each
`d ∈` sweep, assert `|R(p*) − R(p_J)|`, `|R(p*) − R(p_U)|` are within `3·MCSE`. This
is the §2.4 falsification screen: with no co-volume gradient, no prior can beat
another on `D(m_q‖m_π)`, so a `p*` "win" here exposes an estimator bias or a rigged
comparison. The most important non-headline test in the suite.

**T3 — `p*` equalizer (the demoted capacity tautology).** Confirm the solver
returns a genuine capacity prior: `b(θ) = D(p(x|θ)‖m_{p*}) − I_{p*}` is `≈0` on
`supp(p*)` and `≤0` (up to numerical slack) off it, and `I_{p*}` equals the BA
fixed-point value. This *cannot* speak to the headline (it is the redundancy–
capacity theorem) and is here only as a unit test of the new multi-`d` solver.

**T4 — Jeffreys construction.** `Σ p_J = 1` after quadrature normalisation; in the
hypercone the marginal on `θ_1` matches the analytic `∝ θ_1^{d-1}` (§9.2) within
quadrature tolerance. Catches a wrong `det g`, a missing normaliser, or an
axis-ordering bug.

**T5 — Gaussian KL split.** For random `(y, σ, μ_π, Σ_π)`, the closed form (3.2.1)
matches a direct numeric `D_{KL}(𝒩‖𝒩)`. Decoupled from the model; catches a sign or
trace error in the bias/calibration decomposition used by the §6 diagnostic.

**T6 — Hypercone `Δ`.** Construct the hypercone `p_J` posterior at observations with
`1 ≪ x ≪ L` (e.g. `L=50`, `x≈10`, `d∈{6,11,26}` per A&M), and assert the numeric
posterior-mean deviation matches `(d−1)/x` within `O(x^{-3})` tolerance. Cross-check
against A&M Appendix A.1 — validates the bias mechanism the whole spec rests on.

**T7a — Mixture-marginal consistency.** For a discrete `p*` and a coarse continuous
prior, `log m_π(X_{1:N})` from the exact atom sum agrees with grid quadrature on a
shared support to tight tolerance. **T7b — `p*` method agreement.** Where both
grid-BA and the atomic optimiser are feasible (small `d`), the resulting `R_N^q`
agree within MCSE + solver tolerance. Defends against a solver-specific artefact
driving the result.

**T8 — Floors.** *(a) Per cell:* `R_N^q(π) ≥ I_q^{(N)} ≥ 0` for every prior `π`
(the prior-dependent term `D(m_q‖m_π) ≥ 0`), with the per-cell minimum attained by
the prior matched to *that* `q_c`. *(b) Across `c`:* among the fixed priors, the
`c`-averaged `R` is minimised by `q̄` (§2.3). A per-cell violation means the score
or the marginal estimator is wrong; a violation of (b) means the `q̄` construction
is wrong. Note `q̄` need **not** win per cell — only on the `c`-average — so this
test does *not* assert `R(q̄) ≤ R(π)` cellwise.

**T9 — A&M prior-side reproduction.** Over the `d`-sweep, `I_{p*}(d) ≥ I_{p_J}(d)`
and `B_{p*}(d) ≤ B_{p_J}(d)` (worst-case bias). This is A&M's *established* result
(Fig. 5) — known shape, not our headline — so it is a legitimate quantitative check
that the prior-side machinery (model, `p*`, MI/`b` estimators, Jeffreys) is correct
before the foreign-`q` scoring runs.

**T10 — Determinism.** Two runs with the same seed produce bit-identical `R`
arrays. Standard reproducibility guard (`manage-randomness.md`).

We do **not** test: the headline sign (§2.2); exact `p*` atom positions at
intermediate `d` (no closed form); behaviour at `d` beyond the solver's feasible
range (§7 OQ-1).

### 5.3 Eye test (manual gate before the full suite)

**Anchor — A&M (2023), Figure 5.** The figure plots, vs dimension `d` (same data,
same noise across `d`): *(top)* mutual information `I(X;Θ)/log 2` — the optimal
prior roughly **flat/high**, Jeffreys **declining to < 1 bit**; *(bottom)*
worst-case bias `max_θ b(θ)/log 2` — `≈ 0` for `p*`, **rising** for Jeffreys. This
is A&M's established result with an unambiguous known shape, freely available
([Entropy 25(3):434, MDPI, CC BY](https://www.mdpi.com/1099-4300/25/3/434)); it is
**not** this spec's headline (the foreign-`q` predictive contest), so it is a valid
correctness anchor for the prior-side machinery.

- **Configuration.** Exponential-decay model (§4.1.1), `m=26` times in `1≤t≤5`,
  `σ=0.1`, `a_μ=1/d`; `d` swept over the solver-feasible range
  (`d ∈ {1,2,3,4}` for grid-BA; extend toward A&M's `d≤26` only if the atomic
  method is used — see §7 OQ-1). Priors `p*`, `p_J`. Seed `20260601`
  (auto-chosen — today's date per `manage-randomness.md`; please confirm).
- **Output.** A two-panel figure
  `tests/figures/002_foreign_q_prediction/eyetest_am_fig5.png`: `I/log2` and
  `max_θ b/log2` vs `d`, one line per prior.
- **Acceptance.** Human-reviewed against the *known* features: `I_{p*}` flat-to-
  gently-varying while `I_{p_J}` declines; `B_{p*}≈0` while `B_{p_J}` rises with
  `d`. A figure where Jeffreys does **not** degrade, or where `p*` is not flat,
  exposes a wrong FIM, a mis-normalised Jeffreys, or a broken MI/`b` estimator —
  before any foreign-`q` number is trusted. Outcome recorded in
  `experiments/002-foreign-q-prediction/CODEGEN_LOG.md`; the full suite runs only
  after approval.

#### 5.3.1 Eye-test file structure

Standalone script `tests/eye_test_002_foreign_q_prediction.py` (no `test_` prefix,
not pytest-collected): builds the exp-decay model over the `d`-sweep, computes
`p*` and `p_J`, estimates `I` and `max_θ b` for each, writes the two-panel PNG, and
prints a reminder that human approval gates the suite. Running it *is* the smoke
check; it must complete and write a non-empty figure before review.

### 5.4 Sweep design

Values the test code uses, pinned here (not in the test file). Auto-decisions are
flagged for ratification.

- **Dimension `d`.** `d ∈ {1, 2, 3, 4}` (grid-BA-feasible). *Why:* `d=1` is the
  spec-000 sanity floor; `d=2` is A&M's Fig. 1 minimal setting (small effect — the
  boundary, note §6); `d=3,4` show the trend. Reaching A&M's dramatic `d≥11`
  requires the atomic solver and is **deferred** (§7 OQ-1).
- **Noise / budget `σ`.** `σ ∈ {0.05, 0.1, 0.2, 0.4}` with `N=1`, *or* `σ=0.1` with
  `N ∈ {1,2,4,8}` (equivalent via `σ/√N`). *Why:* `σ=0.1` matches A&M; the spread
  spans "far from asymptopia" (large `σ`, small `N`) to nearer it. (Auto-chosen
  range; please confirm.)
- **Taper.** `{0 (negative control), 1 (full hypercone), 0.5}` in the hypercone
  family. *Why:* `0` is the T2 control; `1` is A&M's case; `0.5` locates the onset.
- **Rotation angle (hypercone).** `{0, π/8, π/4}`. *Why:* `0` is axis-aligned
  (uniform-`θ` unbiased strawman, note §6.3); nonzero makes uniform-`θ` a fair
  competitor. (Auto-chosen; please confirm.)
- **Cooperativeness `c`.** `c ∈ {0, 0.25, 0.5, 0.75, 1}`. *Why:* the §2.4 sign-flip
  sweep needs the cooperative and non-cooperative ends plus enough interior to see
  where the sign changes. (Auto-chosen density; please confirm.)
- **Grid resolution `G`.** Per-axis `G=50` for `d≤2`, `G=30` for `d=3`, `G=20` for
  `d=4` (so the grid stays `≤ 10^6` cells). *Why:* `G ≫ √(budget)` resolves the
  `~√n` atom spacing (spec 000 §1.3) while keeping `d`-dim BA tractable. Grid-
  refinement check at one cell: `G ∈ {20, 30, 50}`. (Auto-chosen; please confirm.)
- **`q`-samples `S_q`.** `S_q = 500` per cell, raised to `2000` for any cell with
  `MCSE/|mean ΔR| > 0.1`. *Why:* the headline is a difference of large terms (the
  matched floor `I_q` cancels in `ΔR`), so the difference needs more samples than an
  absolute mean. (Auto-chosen; please confirm.)
- **Seed.** Single experiment seed `20260601`; one child stream per cell via
  `rng.spawn`, cells enumerated in fixed lexicographic order.
- **Test-suite subset.** T1, T3, T5, T7, T10 run at a single cheap cell
  (`exp-decay, d=2, σ=0.1, c=0.5`); T2 over the `d`-sweep in the control model; T6
  at `d∈{6,11,26}` (hypercone, analytic — no solver needed); T9 over the full
  `d`-sweep. The experiment script (§6) runs the full cross-product.

## 6. Report

Report at `experiments/002-foreign-q-prediction/REPORT.md`, generated by
`experiments/002-foreign-q-prediction/run.py`.

### 6.1 Outputs

Under `experiments/002-foreign-q-prediction/`:

- `figures/am_fig5_reproduction.png` — `I/log2` and `max_θ b/log2` vs `d` (the
  eye-test figure, exp-decay), priors `p*`, `p_J`, `p_LN`.
- `figures/transfer_vs_c.png` — the headline: `min_{π'} ΔR(p*,π')` and the gap to
  `q̄`, vs cooperativeness `c`, one panel per `d`. The §2.4 sign-of-advantage curve.
- `figures/R_vs_d.png` — `R_N^q(π)` vs `d` per prior, at fixed `(σ, c)`, with the
  `q̄` ceiling line.
- `figures/negative_control.png` — `R(π)` vs `d` in the constant-cross-section
  model; the curves should coincide (visual companion to T2).
- `figures/calibration_pit.png` — PIT histogram / over-dispersion of the held-out
  `x'` under each prior's predictive (the §3.4 calibration diagnostic).
- `results_table.json` — per-cell summary; schema in §6.3.
- `provenance.json` — git `HEAD`, `HEAD:src/infomax`, package versions, spec commit
  hash (per `meta/workflow-issues.md` "Wire experiment commit hashes …" — recorded
  at run time, **not** hand-edited, and cited by REPORT.md).
- `REPORT.md` — body per §6.4.

### 6.2 Sweep coverage per output

`am_fig5_reproduction.png` uses the exp-decay `d`-sweep at `σ=0.1`.
`transfer_vs_c.png` and `R_vs_d.png` use the full `(d, σ, c)` cross-product in the
exp-decay (primary) and rotated-hypercone (controlled) models.
`negative_control.png` uses the constant-cross-section model only.
`results_table.json` carries the full cross-product.

### 6.3 Table schema

`results_table.json` — one row per `(model, d, σ, taper, rotation, c)` cell:

- `model`, `d`, `sigma`, `taper`, `rotation`, `c` — the cell key.
- `R_mean[π]`, `R_mcse[π]` for `π ∈ {p*, p_J, p_U, p_LN, q̄}` (nats).
- `delta_R_best` — `min_{π'∈{p_J,p_U,p_LN}} (R[p*] − R[π'])` and its MCSE (the
  headline statistic).
- `I_pstar`, `I_pJ`, `B_pstar`, `B_pJ` (bits) — the A&M prior-side scores.
- `pstar_n_atoms`, `pstar_method` (`grid-BA` / `atomic`).
- `S_q`, `seed_stream` — provenance.

Computed but **not persisted**: per-sample `R_s` arrays (length `S_q`), the full
grids, the q-sample parameters (kept in a separate `q_metadata.jsonl` so the table
stays small but a `q`-subset analysis can re-key off it).

### 6.4 Report body

1. A&M Fig. 5 reproduction (with the eye-test approval note).
2. The transfer-vs-`c` headline figure, per `d`, with the negative-control panel
   alongside.
3. `R` vs `d` with the `q̄` ceiling.
4. Calibration diagnostic.
5. A table embedding `d`, `c`, `delta_R_best`, and the gap to `q̄`.
6. Test results: T1–T10 pass/fail with achieved tolerances.
7. Notes: the §2.4 verdict (transfer / self-served), solver-method caveats (OQ-1),
   and anything surprising.

## 7. Open questions

- **OQ-1 (blocking infrastructure).** The multi-`d` `p*` solver is the principal new
  build and the feasibility ceiling. Grid-BA is `O(G^d)` and realistically caps at
  `d≈4`; A&M's dramatic regime (`d≥11`) needs the atomic L-BFGS optimiser
  (`AtomicPriors.jl`-style). *Decision needed:* port the atomic optimiser now (wider
  `d`, more faithful, more work) or ship grid-BA first (small-`d` boundary only) and
  defer the atomic method? The spec is written so grid-BA suffices for the minimal-
  setting result; the atomic method is required only to reach A&M's `d`. [?]
- **OQ-2 (definition).** The exact `q_{coop}`/`q_{non}` parameterisation (§4.3). It
  must be defined in prediction space and span cooperative→non-cooperative; the
  concrete family (e.g. mixtures of pulled-back uniforms on manifold edges vs
  interior) needs a human choice so the cooperativeness axis is principled, not
  reverse-engineered to a desired answer. [?]
- **OQ-3 (convention).** `p_LN` meta-parameters `(θ̄, σ̄)` — A&M use `(0,1)`; do we
  follow, or tune to make `p_LN` the *strongest* deployable competitor (A&M note a
  tuned variational prior can approximate `p*`)? The honest competitor is the best
  deployable non-infomax prior (§2.2), which argues for at least a light tune. [?]
- **OQ-4 (scope).** Primary model = exp-decay (curved, all competitors fail) with
  the rotated hypercone as the controlled companion. Is that the right split, or
  should the controlled rotated-hypercone be primary (closed-form `Δ`, cleaner
  boundary location) with exp-decay as the realism check? [?]
- **OQ-5.** Discreteness is **not** assumed to be the load-bearing property (per the
  discussion behind this spec); a resolution-adapted *smooth* prior might capture
  the same benefit. Should the competitor set include a smoothed/variational
  resolution-adapted prior to isolate whether discreteness does any work? Deferred,
  but flagged: a `p*` win that a smooth resolution-adapted prior also achieves does
  not implicate discreteness. [?]

## 8. References

- Abbott, M. C. & Machta, B. B. (2023). Far from Asymptopia: Unbiased
  High-Dimensional Inference Cannot Assume Unlimited Data. *Entropy* 25(3), 434.
  [doi:10.3390/e25030434](https://doi.org/10.3390/e25030434);
  [open-access PDF / figures](https://www.mdpi.com/1099-4300/25/3/434);
  code [mcabbott/AtomicPriors.jl](https://github.com/mcabbott/AtomicPriors.jl).
  The bias-pressure `b(θ)`, posterior deviation `Δ`, the exp-decay and hypercone
  models, and Fig. 5 (eye-test anchor).
- Mattingly, H. H., Transtrum, M. K., Abbott, M. C. & Machta, B. B. (2018).
  Maximizing the information learned from finite data selects a simple model.
  *PNAS* 115(8), 1760–1765.
  [doi:10.1073/pnas.1715306115](https://doi.org/10.1073/pnas.1715306115). The
  finite-data `p*`; spec 000.
- Quinn, K. N., Abbott, M. C., Transtrum, M. K., Machta, B. B. & Sethna, J. P.
  (2023). Information geometry for multiparameter models. *Rep. Prog. Phys.*
  [doi:10.1088/1361-6633/aca6f8](https://doi.org/10.1088/1361-6633/aca6f8). Multi-`d`
  `p*`, MBAM, the high-`d` Jeffreys-as-inference-prior catastrophe.
- Clarke, B. S. & Barron, A. R. (1994). Jeffreys' prior is asymptotically least
  favorable under entropy risk. *JSPI* 41(1), 37–60.
  [doi:10.1016/0378-3758(94)90153-8](https://doi.org/10.1016/0378-3758(94)90153-8).
  `p* → ` Jeffreys; minimax redundancy.
- Gneiting, T. & Raftery, A. E. (2007). Strictly proper scoring rules, prediction,
  and estimation. *JASA* 102(477), 359–378.
  [doi:10.1198/016214506000001437](https://doi.org/10.1198/016214506000001437).
  Log-loss is strictly proper ⇒ the matched prior is Bayes-optimal (§2.3).
- Topsøe, F. (1979). Information-theoretical optimization techniques. *Kybernetika*
  15(1), 8–27.
  [link](https://www.kybernetika.cz/content/1979/1/8). The compensation identity
  (2.1.2).
- Bernardo, J. M. (1979). Reference posterior distributions for Bayesian inference.
  *JRSS-B* 41(2), 113–147.
  [doi:10.1111/j.2517-6161.1979.tb01066.x](https://doi.org/10.1111/j.2517-6161.1979.tb01066.x).
  Reference prior as a design device, explicitly not a belief.
- Smith, J. G. (1971). The information capacity of amplitude- and
  variance-constrained scalar Gaussian channels. *Information and Control* 18(3),
  203–219.
  [doi:10.1016/S0019-9958(71)90346-9](https://doi.org/10.1016/S0019-9958(71)90346-9).
  Discreteness of capacity-achieving inputs (continuous output).
- Blahut, R. E. (1972). Computation of channel capacity and rate-distortion
  functions. *IEEE Trans. IT* 18(4), 460–473.
  [doi:10.1109/TIT.1972.1054855](https://doi.org/10.1109/TIT.1972.1054855); Arimoto,
  S. (1972). *IEEE Trans. IT* 18(1), 14–20.
  [doi:10.1109/TIT.1972.1054753](https://doi.org/10.1109/TIT.1972.1054753). The BA
  solver (spec 000), generalised to multi-`d` here.
- In-repo: `notes/prediction_objective_for_priors.md` (the maths this spec
  formalises), `notes/infomax_two_hats_and_directions.md` (the two-hat diagnosis),
  `tutorials/math/redundancy-capacity.md` (compensation identity, equalizer),
  `tutorials/math/kelly.md`, `specs/000-static-infomax-fig1.md`,
  `specs/001-infomax-betting.md` and `specs/001-infomax-betting-redteam_third.md`
  (the F1 predetermined-by-`q` pathology this design guards against).

## 9. Derivations

### 9.1 The compensation identity for the `N`-fold marginal (eq. (2.1.2))

Starting from (2.1.1) with `θ` averaged under nature `q`:

$$
\begin{aligned}
R_N^q(\pi)
 &= \mathbb{E}_{\theta\sim q}\int p(X_{1:N}\mid\theta)\,\log\frac{p(X_{1:N}\mid\theta)}{m_\pi(X_{1:N})}\,dX_{1:N} \\
 &= \mathbb{E}_{\theta\sim q}\int p(X_{1:N}\mid\theta)\Big[\log\frac{p(X_{1:N}\mid\theta)}{m_q(X_{1:N})} + \log\frac{m_q(X_{1:N})}{m_\pi(X_{1:N})}\Big]dX_{1:N} \\
 &= I_q^{(N)} + \int m_q(X_{1:N})\,\log\frac{m_q(X_{1:N})}{m_\pi(X_{1:N})}\,dX_{1:N} \\
 &= I_q^{(N)} + D_{\mathrm{KL}}\!\big(m_q \,\|\, m_\pi\big),
\end{aligned}
\tag{9.1.1}
$$

where line 3 uses `𝔼_{θ∼q} p(X_{1:N}|θ) = m_q(X_{1:N})` in the second term and
`I_q^{(N)} := 𝔼_{θ∼q} D_{KL}(p(X_{1:N}|θ)‖m_q)` in the first. The first term is
prior-independent; the second is `≥ 0`, zero iff `m_π = m_q`. Minimising over fixed
priors of the `c`-average gives `m_π = 𝔼_c[m_q]`, attained by `π = q̄` (§2.3).

### 9.2 Hypercone posterior deviation (eq. (3.3.1))

For the hypercone (§4.1.2), `√det g(θ) = r(θ_1)^{d-1} = (θ_1/L)^{d-1}` (A&M
Appendix A.1; the relevant `√det g_rel = 1 + O(L^{-2})`). Integrating the irrelevant
coordinates gives the effective Jeffreys marginal `p_J(θ_1) ∝ θ_1^{d-1}`. For one
observation `x` along the relevant axis (noise `σ=1`),

$$
p(\theta_1\mid x) \propto e^{-(x-\theta_1)^2/2}\,\theta_1^{\,d-1},\qquad
\frac{d}{d\theta_1}\Big[-\tfrac12(x-\theta_1)^2 + (d-1)\log\theta_1\Big] = 0 \;\Rightarrow\; \theta_1 = x + \frac{d-1}{\theta_1}, \tag{9.2.1}
$$

so to leading order for `1 ≪ x ≪ L` the posterior mode/mean sits at
`θ_1 ≈ x + (d-1)/x`, giving `Δ = |⟨θ_1⟩ − x| = (d-1)/x + O(x^{-3})`. The
prior factor `θ_1^{d-1}` pulls the centre toward the thick end; the pull grows with
`d` and is largest at small `x` (the thin end).

### 9.3 Exponential-decay FIM

With `y_t(θ)=Σ_μ a_μ e^{-k_μ t}`, `k_μ=e^{-θ_μ}`,
`∂y_t/∂θ_μ = a_μ e^{-k_μ t}(-t)(\partial k_μ/\partial θ_μ) = a_μ t\,k_μ\,e^{-k_μ t}`
(using `∂k_μ/∂θ_μ = -k_μ`). Hence
`g_{μν}(θ) = σ^{-2} Σ_{t} (a_μ t k_μ e^{-k_μ t})(a_ν t k_ν e^{-k_ν t})`, a
closed-form `d×d` matrix per `θ`, from which `p_J ∝ √det g` and the eye-test scores
follow.

## 10. Revision log

### 2026-06-01 — Initial draft (all sections)

First draft, derived from `notes/prediction_objective_for_priors.md` (as revised
2026-06-01 to retire the "is `p*` a good epistemic prior" framing in favour of the
foreign-`q` transfer question, add the self-consistency asymmetry caveat, require
rotation/curvature in the minimal model, and replace the capacity tautology with
the negative-control + sign-flip go/no-go). Principal open items carried as OQ-1
(multi-`d` `p*` solver feasibility — blocking), OQ-2 (the `q`-cooperativeness
family), and OQ-4 (primary-model choice). All sections at `draft` pending human
review; per the gating rules, no test scaffolding or code until Setup + Objective
are `reviewed`.
