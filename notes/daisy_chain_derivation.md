# Daisy chain: state of affairs and the derivation issue

## 1. What the algorithm is

The daisy chain is a process model for representational dynamics built around the Mattingly et al. (2018) / Bernardo reference-prior result: under a finite-horizon information objective, the optimal prior $p^*(\theta)$ is generically **discrete**, and its atoms supply a normatively-grounded coarse-graining of $\Theta$. The chain alternates three steps:

- **MB (model building):** run Blahut–Arimoto on the dynamic objective $\mathcal{L}_{dyn} = I(\theta;\tilde{x}) + I(\theta; X \mid \tilde{x})$ to produce a new discrete prior. The MB step also yields an expected information gain.
- **BI (Bayesian inference):** apply the new prior to the next $n$ real observations; produce a posterior; measure the realised information gain. The discrepancy between expected and realised is the **misspecification signal**.
- **EC (efficient coding):** use the misspecification signal to update the likelihood $p(x\mid\theta)$.

Two interlocked dynamics: the representation re-coarse-grains each cycle (MB), the channel re-fits on the residual (EC). Only MB optimises a closed-form objective; the whole loop does not.

## 2. Outstanding gaps (overview, with the derivation issue called out)

| Gap | Status | Blocks |
|---|---|---|
| **Derivation step at line 316** (this document's focus) | Empirical form works, derived form doesn't, no clean justification | Calling the MB step normative |
| Explicit dependence on $m/n$ | Hidden by the synthetic-observation trick | Claims about horizon effects |
| Uncertainty over $n$ | Mentioned, not addressed | Realistic agent models |
| EC update rule | Gestured at (Młynarski-style); not written down | Closing the loop formally |
| Misspecification signal definition | "Expected − realised bits" but no single equation | Same |
| MI as a special case of representational planning | Section empty (`\todo`) | Embedding claim |
| Fixed-point / stability of the loop | Not analysed | Claims about stable representations, drift, regime changes |
| Discount factor ↔ $n$ correspondence | Noted, not formalised | Linking to RP / RL temporal-preference data |
| Amortised MI computation | `\todo` (particle filter) | Scaling beyond toy settings |
| Comparisons to RR, hierarchical Bayes, autopoiesis | Bullet points only | Positioning against literature |

The rest of this document focuses on the first row.

## 3. The derivation, step by step

### Step A — Setup and one-shot objective

Starting point (well-established, Mattingly et al. 2018):
$$p^*(\theta \mid n, p_{x\mid\theta}) = \argmax_{p(\theta)} I(\theta; X), \quad X = \{x_1, \ldots, x_n\}.$$

Optimised by Blahut–Arimoto:
$$p_{\tau+1}(\theta) = \frac{1}{Z_\tau} e^{\mathrm{KL}[p(X\mid\theta) \,\|\, p(X)]} p_\tau(\theta).$$

**Critique:** No issue here — this is the standard result.

### Step B — Sequential setup

Bring in $m$ old observations summarised by $p(\theta_{old}\mid X_{old})$. Write the desired objective as:
$$\mathcal{L}_{dyn} = I(\theta;\theta_{old}) + I(\theta; X \mid \theta_{old}).$$

**Critique:** This is a *design choice*, not a derivation from a deeper principle. It posits that the right thing to maximise is "old information + future information given old". Two assumptions are buried here:

1. *Independence of contributions.* The decomposition $I(\theta;\theta_{old}) + I(\theta; X\mid\theta_{old})$ equals $I(\theta;\theta_{old}, X)$ by the chain rule. So the design is "maximise joint information between the new latent and (old summary, future data)". This is the natural extension of the one-shot objective, but it commits to treating $\theta_{old}$ on the same footing as future observations.
2. *No relative weighting.* There's no $\alpha I_{past} + (1-\alpha) I_{future}$ or any explicit balance between $m$ and $n$. The weighting is supposed to emerge from the math but doesn't — see Step D.

### Step C — Projecting the posterior into observation space

Define $\tilde{x} \sim p(\tilde{x}) = \sum_{\theta_{old}} p(\tilde{x}\mid\theta_{old}) p(\theta_{old}\mid X_{old})$ — synthetic observations from the old posterior predictive. Then **equivocate** (the document's word) to:
$$\mathcal{L}_{dyn} = I(\theta;\tilde{x}) + I(\theta; X \mid \tilde{x}).$$

**Critique:** This is the first non-trivial move and it is presented as a sidestep, not a derivation. What's actually being claimed is that $I(\theta;\theta_{old})$ can be replaced by $I(\theta;\tilde{x})$ where $\tilde{x}$ is one synthetic observation distributed according to the old posterior predictive. This is **not an identity**:

- $\theta_{old}$ is a $\Theta$-valued random variable summarising $m$ observations; its uncertainty is $H[\theta_{old}\mid X_{old}]$.
- $\tilde{x}$ is a single $\mathcal{X}$-valued observation; by data-processing inequality, $I(\theta;\tilde{x}) \le I(\theta;\theta_{old})$ in general.

So we are optimising a lower bound (or some other related quantity), not the original objective. The document is candid about this ("sidestep", "equivocation"), but the substitution has two downstream consequences:
- It commits to a particular *scale* of past information (one synthetic observation's worth), independent of $m$.
- It restores tractability by living entirely in observation space.

The sampling trick in Step E is then supposed to recover the $m$-dependence by averaging over $m$ synthetic samples.

### Step D — The future term (conditional MI)

Expand $I(\theta; X\mid\tilde{x})$ in the standard way:
$$I(\theta; X\mid\tilde{x}) = \sum_{\tilde{x}} p(\tilde{x}) \sum_\theta p(\theta\mid\tilde{x}) \sum_X p(X\mid\theta,\tilde{x}) \log\frac{p(X\mid\theta,\tilde{x})}{p(X\mid\tilde{x})}.$$

Apply the Markov blanket argument: $\theta$ d-separates $X$ from $\tilde{x}$, so $p(X\mid\theta,\tilde{x}) = p(X\mid\theta)$ and $p(X\mid\tilde{x}) = p(X)$.

Expand the posterior $p(\theta\mid\tilde{x}) = p(\tilde{x}\mid\theta)p(\theta)/p_{new}(\tilde{x})$, where $p_{new}(\tilde{x}) := \sum_\theta p(\tilde{x}\mid\theta) p(\theta)$ uses the **candidate prior $p(\theta)$**, i.e. the variable we are optimising. This gives:
$$I(\theta; X\mid\tilde{x}) = \sum_{\tilde{x}} p(\tilde{x}) \sum_\theta \frac{p(\tilde{x}\mid\theta)}{p_{new}(\tilde{x})} p(\theta) \sum_X p(X\mid\theta) \log\frac{p(X\mid\theta)}{p(X)}.$$

**Critique:** All correct as exact algebra. But notice the structure already contains the seed of the problem: the outer expectation is under $p(\tilde{x})$ (the **old**-posterior-driven distribution) while the posterior factor $1/p_{new}(\tilde{x})$ is under the **new** candidate prior. These are two different distributions — and the Monte Carlo step that follows entangles them.

### Step E — The sampling trick

Draw $\tilde{x}_1, \ldots, \tilde{x}_m \sim p(\tilde{x})$ and replace the outer expectation by the empirical mean:
$$I(\theta; X\mid\tilde{x}) \approx \sum_\theta p(\theta) \left[\frac{1}{m}\sum_s \frac{p(\tilde{x}_s\mid\theta)}{p_{new}(\tilde{x}_s)}\right] \sum_X p(X\mid\theta) \log\frac{p(X\mid\theta)}{p(X)}.$$

**Critique:** The Monte Carlo replacement is mechanically correct given Step C's setup. But it introduces a subtle inconsistency that the document doesn't flag: $p_{new}(\tilde{x}_s)$ is a **function of the optimisation variable $p(\theta)$**, and it appears in the denominator of an outer weight that gets re-evaluated each BA iteration. This is what creates the awkward $p(\tilde{x}_s\mid\theta)/p_{new}(\tilde{x}_s)$ ratio that the empirical objective ends up dropping.

Also: the sampling trick is presented as the mechanism by which $m$ re-enters the objective. But the only effect $m$ has here is to reduce variance of a Monte Carlo estimate of a quantity that **does not itself depend on $m$**. The $m$-dependence in the original Step B was the dependence of $\theta_{old}$'s posterior on the size of the historical dataset — that information is being smuggled in only through the shape of $p(\tilde{x})$ via the old posterior. So increasing $m$ here does *not* increase the weight of the past term relative to the future term, contra the stated intent.

### Step F — The past term

The non-conditional term $I(\theta;\tilde{x})$ is expanded in the same way to use the same samples:
$$I(\theta;\tilde{x}) \approx \sum_\theta p(\theta) \frac{1}{m}\sum_s \frac{p(\tilde{x}_s\mid\theta)}{p_{new}(\tilde{x}_s)} \log\frac{p(\tilde{x}_s\mid\theta)}{p_{new}(\tilde{x}_s)}.$$

**Critique:** Same comment as Step D/E. Algebra is exact prior to sampling. The Monte Carlo step inherits the $1/p_{new}$ factor in the outer weight.

### Step G — The full derived objective (Eq. 306)

Adding the two terms:
$$\mathcal{L}_{dyn} \approx \argmax_{p(\theta)} \sum_\theta p(\theta) \frac{1}{m}\sum_s \frac{p(\tilde{x}_s\mid\theta)}{p_{new}(\tilde{x}_s)} \left[\log\frac{p(\tilde{x}_s\mid\theta)}{p_{new}(\tilde{x}_s)} + \sum_X p(X\mid\theta) \log\frac{p(X\mid\theta)}{p(X)}\right].$$

### Step H — The empirically-working objective (Eq. 312)

Replace the outer weight $p(\tilde{x}_s\mid\theta)/p_{new}(\tilde{x}_s)$ by just $p(\tilde{x}_s\mid\theta)$:
$$\mathcal{L}_{dyn} \approx \argmax_{p(\theta)} \sum_\theta p(\theta) \frac{1}{m}\sum_s p(\tilde{x}_s\mid\theta) \left[\log\frac{p(\tilde{x}_s\mid\theta)}{p_{new}(\tilde{x}_s)} + \sum_X p(X\mid\theta) \log\frac{p(X\mid\theta)}{p(X)}\right].$$

The simulations produce reasonable results with this form, not with the derived one.

## 4. Where the discrepancy comes from

The two forms differ only in the outer weight: derived uses $p(\tilde{x}_s\mid\theta)/p_{new}(\tilde{x}_s)$, empirical uses $p(\tilde{x}_s\mid\theta)$. The factor of difference is exactly $1/p_{new}(\tilde{x}_s)$.

Here is what I think is happening. There are **two algebraically equivalent decompositions of mutual information** that produce different Monte Carlo estimators when you sample $\tilde{x}$ from a fixed proposal:

**Decomposition 1 — "expectation under the marginal of posterior-weighted log-ratio":**
$$I(\theta;\tilde{x}) = \mathbb{E}_{\tilde{x}\sim p(\tilde{x})} \sum_\theta p(\theta\mid\tilde{x}) \log\frac{p(\theta\mid\tilde{x})}{p(\theta)}.$$

If you Monte Carlo the outer expectation with samples from $p(\tilde{x})$ (the old-posterior predictive, which is **not** the marginal of the joint $p(\theta)p(\tilde{x}\mid\theta)$ unless old=new), you get the **derived** form, with $1/p_{new}$ in the weight. This is the path the derivation takes.

**Decomposition 2 — "expectation under the joint":**
$$I(\theta;\tilde{x}) = \sum_\theta p(\theta) \sum_{\tilde{x}} p(\tilde{x}\mid\theta) \log\frac{p(\tilde{x}\mid\theta)}{p_{new}(\tilde{x})}.$$

The inner sum is an expectation under $p(\tilde{x}\mid\theta)$ — which is $\theta$-dependent. If you Monte Carlo this naively using a single set of samples $\{\tilde{x}_s\}$ and treat them as if they were drawn from $p(\tilde{x}\mid\theta)$ for whichever $\theta$ is being evaluated, the outer weight becomes $p(\tilde{x}_s\mid\theta)$ — this is the **empirical** form.

Decomposition 2's Monte Carlo estimator is **biased** (it doesn't importance-correct for the fact that $\{\tilde{x}_s\}$ came from $p(\tilde{x})$, not $p(\tilde{x}\mid\theta)$), but it has a property the derived estimator does not: **the outer weight $p(\tilde{x}_s\mid\theta)$ is bounded in $[0,1]$ regardless of $p_{new}$**, whereas $p(\tilde{x}_s\mid\theta)/p_{new}(\tilde{x}_s)$ can blow up arbitrarily as $p_{new}(\tilde{x}_s) \to 0$.

This is, I believe, the operational reason the empirical form behaves better:

- **The derived estimator has unbounded variance with respect to the optimisation trajectory.** During BA, the candidate prior $p(\theta)$ concentrates onto a few atoms, which makes $p_{new}(\tilde{x})$ small at synthetic samples that those atoms don't predict well. The $1/p_{new}$ factor explodes precisely at the samples that are *informative about whether $\theta$ is wrong*, dominating the objective with high-variance noise terms.
- **The empirical estimator is well-behaved throughout BA.** Replacing the weight with $p(\tilde{x}_s\mid\theta)$ kills the singularity. It's no longer an unbiased estimator of the original $\mathcal{L}_{dyn}$, but it is **an unbiased estimator of a different but related quantity** — namely, a cross-entropy-like functional that still has the right gradient structure for moving probability mass toward atoms that explain the synthetic samples well.

There's also a second, possibly more fundamental point. Look at what the empirical form actually computes:
$$\sum_\theta p(\theta) \frac{1}{m}\sum_s p(\tilde{x}_s\mid\theta) \cdot [\ldots]$$

This is structured exactly like the standard BA objective for an MI-like quantity where the "data" are the synthetic samples and the bracket is the log-density-ratio. It is, up to the bracket's specific form, **the BA-objective-style approximation of $I(\theta;[X,\tilde{x}])$ treating $\tilde{x}$ as an additional observation drawn from $p(\tilde{x}\mid\theta)$**. This is consistent with the document's own Eq. 320–323 in the BA section, which already writes the objective in that form. **The derivation in Step F essentially took a long route to the form in Eq. 323, but the long route accumulated an $1/p_{new}$ factor that the natural "BA on the joint" formulation doesn't have.**

## 5. Candidate resolutions

Three possibilities, with different theoretical commitments:

**Resolution 1 — accept Decomposition 2 as the intended objective.** Drop the route through $p(\theta\mid\tilde{x})$ entirely. Start directly from
$$I(\theta; [X,\tilde{x}]) = \sum_\theta p(\theta) \,\mathrm{KL}[p(X,\tilde{x}\mid\theta) \| p(X,\tilde{x})]$$
and Monte Carlo the inner KL using the shared sample set, accepting that the samples are from $p(\tilde{x})$ rather than $p(\tilde{x}\mid\theta)$ as a controlled approximation (a *self-normalised* importance estimator that drops the normalisation, which is well-known to bias gradients but stabilise them). The empirical objective then is the unbiased estimator under this alternative starting point. **Cost:** the "MI" being maximised is no longer strictly an MI; it's an MI-like surrogate whose properties need to be checked.

**Resolution 2 — fix the variance with self-normalised importance sampling.** Keep Decomposition 1, but replace the outer weight $\frac{1}{m}\sum_s \frac{p(\tilde{x}_s\mid\theta)}{p_{new}(\tilde{x}_s)}$ by the **self-normalised** version:
$$w_s(\theta) = \frac{p(\tilde{x}_s\mid\theta)/p_{new}(\tilde{x}_s)}{\sum_{s'} p(\tilde{x}_{s'}\mid\theta)/p_{new}(\tilde{x}_{s'})}.$$
This bounds the weights and is biased but consistent. Test whether this reproduces the empirical behaviour. **Cost:** still uses $1/p_{new}$, still potentially fragile when $p_{new}$ is near zero on the support of the samples.

**Resolution 3 — change the sampling distribution.** Sample $\tilde{x}_s$ from $p_{new}(\tilde{x})$ instead of $p(\tilde{x})$. Then the proper unbiased estimator of Decomposition 1 has outer weight $p(\tilde{x}_s\mid\theta)$ exactly (the $1/p_{new}$ disappears because we are no longer importance-reweighting). **Cost:** $p_{new}$ changes every BA iteration, so we'd need to re-sample synthetic observations every iteration, which kills the appeal of the original construction (reusing a single sample set, plus the connection to episodic memory).

My read: **Resolution 1 is the cleanest and most likely what's actually going on**, but it requires accepting a small but real reframing of what the MB step optimises. It's no longer $I(\theta;\theta_{old}) + I(\theta;X\mid\theta_{old})$ — it's a tractable surrogate justified by the Markov blanket structure plus the choice of synthetic samples as a proposal. Once you commit to this, the empirical objective is **principled, not a hack**, and the apparent gap at line 316 closes — at the cost of being explicit that "the equivocation" in Step C is the load-bearing one, and that what we get out the other end is a surrogate, not the original MI.

## 6. Implications for the broader project

If Resolution 1 is correct, the immediate consequence is that **the MB step is normative with respect to a tractable surrogate, not the original information functional**. This is fine for cognitive modelling — most normative claims in cognitive science are with respect to a tractable approximation — but it has to be stated explicitly, and the surrogate's properties (does it preserve discreteness? does it preserve the $n$-dependence?) need to be checked in the toy biased-coin setting before moving on.

Once this is settled, the path to formal cognitive arguments runs through: (i) writing down the EC update and the misspecification signal as equations, (ii) reintroducing explicit $m/n$ dependence in the surrogate, (iii) doing at least an informal fixed-point analysis of the loop in the biased-coin case. With those in hand, the daisy chain becomes a well-defined dynamical system one can make claims about.

---

## 7. The misspecification signal as one equation — and a β-search dual (exploratory, 2026-06-02)

> **Status: adventure, not siege.** Written in low-diligence mode after a long chat thread,
> at MB's request. The clean statements below hold in a restricted regime (well-specified
> likelihood family, *pure-σ* misspecification); outside it they degrade to "qualitatively
> right, quantitatively not" — flagged inline. This directly attacks §5 to-do (i): *write the
> EC update and the misspecification signal as equations.*

### 7.1 The signal, written down

The agent assumes likelihood $p_\sigma(x\mid\theta)$ (noise $\sigma$ baked into the channel),
carries the prior $\pi(\theta)$ that MB produced, and predicts the next datum with its Bayes
marginal

$$m_\sigma(x) \;=\; \int p_\sigma(x\mid\theta)\,\pi(\theta)\,d\theta .$$

Reality delivers data with true marginal $q(x)$. Define the misspecification signal as
predicted-minus-realised **predictive log-loss** — what the agent expects to pay per datum
versus what it actually pays (in the binary case this is exactly the $\mathrm{KL}$ term in the
Kelly readout $G=\log 2 - H - \mathrm{KL}$):

$$
\Delta(\sigma)\;=\;\underbrace{\mathbb{E}_{x\sim q}[-\log m_\sigma(x)]}_{\text{realised}}\;-\;\underbrace{\mathbb{E}_{x\sim m_\sigma}[-\log m_\sigma(x)]}_{\text{self-predicted}}\;=\;\underbrace{D(q\,\|\,m_\sigma)}_{\text{shape}}\;+\;\underbrace{\big(H(q)-H(m_\sigma)\big)}_{\text{scale}}.
$$

Two facts:

1. **The shape term $D(q\|m_\sigma)$ is exactly the prior/channel-dependent term of the
   spec-002 redundancy decomposition** $R = I_q + D(m_q\|m_\pi)$ (eq. 2.1.2), with $m_q=q$,
   $m_\pi=m_\sigma$. So the daisy-chain misspecification signal and the foreign-$q$ betting
   redundancy are *the same object*, read dynamically rather than statically.
2. $\Delta(\sigma^\*)=0$ when reality is in the family ($q=m_{\sigma^\*}$): both terms vanish.
   The loop's fixed point is correct calibration.

### 7.2 What EC actually is

The clean EC update is *not* "zero $\Delta$" (the scale term $H(q)-H(m_\sigma)$ is
$\sigma$-dependent and biases that root), but **minimise the realised log-loss** — i.e.
maximum-likelihood / minimum-redundancy fit of the noise to the data:

$$
\hat\sigma \;=\; \arg\min_\sigma\,\mathbb{E}_{x\sim q}[-\log m_\sigma(x)] \;=\; \arg\min_\sigma D(q\,\|\,m_\sigma)\qquad(\text{since }H(q)\text{ is }\sigma\text{-free}),
$$

with fixed point $\sigma=\sigma^\*$. This **resolves the "is this the betting redundancy?"
worry** (raised in chat): betting minimises $D(m_q\|m_\pi)$ over the *prior* (→ matched prior
$\bar q$); EC minimises the *same* divergence over the *channel $\sigma$* (→ true noise
$\sigma^\*$). One redundancy, two arguments — the input column vs the channel column of the
$(\min/\max)\times(\text{input}/\text{channel})$ square.

**Bonus (addresses the causal-discovery note's "decomposable across components" wish).** If
$q$ is genuinely foreign ($\notin\{m_\sigma\}$), then $\min_\sigma D(q\|m_\sigma)=D(q\|m_{\hat\sigma})>0$.
The reducible part is EC's; the **$\sigma$-irreducible residual is the signal that the
representation/family is wrong — MB's job** (re-coarse-grain). So the one scalar splits the
labour: recalibrate the channel (EC) vs re-represent (MB).

### 7.3 The DC is alternating optimisation of the capacity↔RD saddle

Reading the two closed-form steps as corners of the square:

- **MB** $=\arg\max_\pi I_\pi(\theta;X)$ at fixed channel → max-over-**input** = the
  **capacity / least-favourable-prior** corner (design hat).
- **EC** $=\arg\min_\sigma D(q\|m_\sigma)$ at fixed prior → min-over-**channel** = the
  **rate–distortion / calibration** corner.

So the loop alternates the two Blahut–Arimoto problems — capacity and rate–distortion — coupled
by the real-data redundancy $D(q\|m)$ that BI estimates. It is **not** coordinate descent on a
single functional (MB *maximises* $I$, the opposite of redundancy-minimising on the prior);
it is alternating optimisation of the capacity↔RD *saddle*, with reality supplying one of the
two marginals.

### 7.4 A β-search dual, and what Arumugam–Van Roy actually do

**Grounded reading of A&VR 2021 ("Deciding What to Learn", ICML), `resources/arumugam_vanroy.pdf`.**
Their distortion is expected squared regret of a *target action* $\tilde A$ versus optimal,
$d(\tilde a,e)=\mathbb{E}[(r(A^\star)-r(\tilde a))^2\mid E=e,H_t]$; rate is $I_t(E;\tilde A)$;
the loss is $L_\beta(\tilde A\mid H_t)=I_t(E;\tilde A)+\beta\,\mathbb{E}_t[(r(A^\star)-r(\tilde A))^2]$.
Their **BLASTS** algorithm runs Blahut–Arimoto *inside* Thompson sampling to compute, each
period, the target that hits the RD limit at the current $\beta$ and history. So BLASTS is the
**MB-analogue** — the inner BA solve — and the RD *curve* re-adapts each period as the posterior
over $E$ sharpens.

For most of the paper $\beta$ is a free designer preference (the slope of the RD curve, units
*bits per squared-regret*; they sweep it). **But §6.2 introduces an actual β-tuner** (the
`Ψ⁻¹` curve in Fig. 3): set

$$
\beta_t \;=\; \Psi_t^{-1},\qquad \Psi_t=\min_{\pi}\frac{\Delta_t(\pi)^2}{v_t(\pi)},
$$

the inverse **information ratio** ($\Delta_t$ = expected regret, $v_t$ = posterior variance of
the mean reward; a lower bound on the info-gain ratio $\Delta_t^2/g_t$). Units match
($\Psi$ is squared-regret-per-bit, so $\Psi^{-1}$ is bits-per-squared-regret $=\beta$), and the
intuition is that once uncertainty is resolved $\Psi$ is small so $\beta_t$ grows and the target
sharpens to the optimal action. It works (Fig. 3) and is equivalent to rescaling the distortion
by $\Psi^{-1}$.

**The point that matters for us:** $\Psi_t$ is computed entirely from the agent's *current
posterior* — it is an **internal / self-consistent** pin (the resource-rational corner: $\beta$
set by the agent's own estimate of cost-per-bit), *not* a prediction-vs-realised error. So A&VR
**do** tune $\beta$, but with the *internal* knob. The external/forced-budget dual — pinning the
operating point by matching a model prediction to a *realised* quantity, the way EC welds
$\sigma$ to the real data marginal — is the move that (to our knowledge) isn't done, and is the
DC-native one.

**A DC-derived β-search (broad strokes).** Wrap the same inner BA solve in an EC-style outer
loop whose pin is a *prediction error*, not the internal information ratio:

1. **(inner / MB-analogue)** Given current $\beta_t$ and history $H_t$, run Blahut–Arimoto →
   target $\tilde A_{\beta_t}$, with a *predicted* information rate
   $R_t=I_t(E;\tilde A_{\beta_t})$ and predicted distortion $D_t=D(\beta_t\mid H_t)$ (closed form,
   Blahut 1972 Cor. 5).
2. **(BI / reality)** Act on $\tilde A_{\beta_t}$; observe; update the posterior; measure the
   **realised** information actually acquired this period,
   $R^{\mathrm{real}}_t=I_t(E;(A_t,O_{t+1}))$ (and/or realised distortion = achieved squared
   regret).
3. **(EC-analogue / β-update)** misspecification signal $\delta_t=R_t-R^{\mathrm{real}}_t$
   (predicted *demand* for bits vs realised *supply*). If the target demands more bits than the
   period delivers ($R_t>R^{\mathrm{real}}_t$) the agent is over-ambitious → raise the rate
   penalty (lower $\beta$, more satisficing); if it under-uses what's available, lower it. Move
   $\beta$ to drive $\delta_t\to 0$.
4. **Fixed point:** $\beta$ such that the target's demanded rate equals the agent's realised
   acquisition rate — the operating point **welded to the actual information budget the
   environment affords**, not chosen and not read off the internal posterior alone.

The correspondence to EC, side by side:

| | EC (channel $\sigma$) | DC-derived β-search (operating point $\beta\!\leftrightarrow\!D$) |
|---|---|---|
| knob | $\sigma$ (channel noise) | $\beta$ = RD-curve slope $\leftrightarrow$ distortion $D$ |
| inner solve | MB: BA for capacity prior | BLASTS: BA for target action (A&VR) |
| predicted quantity | $m_\sigma$ (predicted data marginal) | $R_t$ (bits the target demands) |
| realised signal (reality) | $q$ (real data marginal, via BI) | $R^{\mathrm{real}}_t$ (bits actually acquired) |
| misspec signal | $D(q\|m_\sigma)$ | $R_t-R^{\mathrm{real}}_t$ |
| update | $\sigma\leftarrow\arg\min_\sigma D(q\|m_\sigma)$ | $\beta\leftarrow$ move until $R_t=R^{\mathrm{real}}_t$ |
| flavour | **external / reality-matched** | **external / reality-matched** |
| A&VR §6.2 analogue | — | $\beta_t=\Psi_t^{-1}$: **internal / self-consistent** |

So the landing for the whole thread: $\beta$-tuning is not absent — A&VR's $\Psi^{-1}$ is a real,
working tuner — but it sits in the **internal** corner (set $\beta$ from the agent's own
information ratio). The daisy chain's contribution, if it has one here, is the **external**
dual: the EC step *is* a $\sigma$-tuner welded to realised data, and its transport to the RD
corner is a $\beta$-tuner welded to realised acquisition. That is exactly the
internal-capacity-vs-forced-budget distinction that motivated the whole project, now showing up
as two different ways to close the loop on the operating point.

### 7.5 Where the ice is thinnest

- The signal identity (7.1) is *exact*. The reduction "EC = ML-fit $\sigma\to\sigma^\*$" (7.2) is
  clean only in the **well-specified-family / pure-$\sigma$** regime; with location
  misspecification or truly foreign $q$, the scale term and a suppressed
  posterior-averaged-likelihood term re-enter. The qualitative split (EC reduces $D$, MB takes
  the residual) survives; the tidy fixed point does not.
- The whole section assumes MB returns the *true* expected MI. The §3–4 line-316 surrogate means
  it returns a cross-entropy-like surrogate, which perturbs the "self-predicted" half of
  $\Delta$. Resolve line 316 before trusting the expected-gain term.
- The DC-derived β-search is **broad strokes, not derived**. The hard open piece is estimating
  $R^{\mathrm{real}}_t=I_t(E;(A_t,O_{t+1}))$ online; outer-loop convergence is unanalysed (same
  status as the DC loop itself).
- "EC is a β-tuner under the capacity↔RD duality" rests on $\sigma\leftrightarrow D$ being a
  genuine rate–distortion correspondence for the Gaussian channel (solid) and $\beta$ being its
  slope (solid). The leap is the claim that nobody does the *external* β-tuner — A&VR §6.2 shows
  the *internal* one exists, so the literature scan should be "is there an external one?" before
  this is called a gap.
