# Infomax on the AP–RV model: mathematical seed for a computational experiment

**Purpose.** Pin down the math we need to evaluate the static finite-$n$ infomax objective on the manuscript's generative model, separately for AP and RV, and identify which derivations are missing before we can plug into the existing BA implementation. Endpoint: a spec for the simulation and a list of curves to plot.

---

## 1. The model, transcribed from the manuscript

### 1.1 Latents and observation

Per trial $t$, the generative model has:

- $z_t \in \{-1, +1\}$: shape identity (decision variable)
- $y_t$: noise level (nuisance, drawn from a known $P(y)$ — uniform between min and max in the Test phase)
- $x_t \in \mathbb{R}$: scalar internal observation, the participant's percept

Two parameters of interest:

- $AP \in [0.5, 1]$: appearance probability of the more frequent shape, i.e. $P(z=+1) = AP$
- $RV \in [0.5, 1]$: relative visibility of the more frequent shape vs. the rare one

In the manuscript's parametrization (Methods §7.4, Eqs. 10–11, §8.4):

$$P(z = +1; AP) = AP$$

$$P(x \mid z; RV)$$

is constructed such that

$$\sum_z P(x \mid z; RV=0.5) \, P(z; AP=q) \;=\; \sum_z P(x \mid z; RV=q) \, P(z; AP=0.5)$$

i.e. AP and RV are designed so that biasing either produces the same marginal $P(x)$. This is the ridge: combinations with $AP + RV \approx \text{const}$ are likelihood-equivalent at the level of the steady-state marginal.

> M: the following part until the section end has to be reviewed, it's not very fluid

The unbiased likelihood is

$$P(x \mid z; RV=0.5) = \int dy \; P^\star(x \mid y) \, P^\star(y \mid z)$$

where $P^\star(y \mid z)$ is the experimental noise distribution and $P^\star(x \mid y)$ the shape-independent noise likelihood.

The biased likelihood is constructed (§8.4) via

$$P(z=1 \mid x; AP=0.5, RV=q) = P_{UB}(z=1 \mid x) - a_q \cdot h(x)$$

with
$$h(x) = \tfrac{1}{2}^2 - \left(P_{UB}(z=1 \mid x) - \tfrac{1}{2}\right)^2$$

and $a_q$ fixed by the normalization constraint (Eq. 41). RV-induced distortion of the likelihood is localized where the unbiased observer is most uncertain ($P_{UB} \approx 0.5$).

### 1.2 The two parameters carry information differently

Worth saying explicitly before deriving anything:

- AP is the parameter of a **discrete output** (the category $z$). Each trial gives at most one Bernoulli sample of $z$, observed indirectly through $x$. Information about AP accumulates at roughly Bernoulli rate.
- RV is a parameter that **warps the continuous likelihood** $P(x \mid z)$ at specific values of $x$ (the diagnostic region near $P_{UB} \approx 0.5$). Trials with high-noise stimuli (where $x$ lands in the diagnostic region) carry a lot of information about RV; low-noise trials carry almost none.

This asymmetry is the candidate source of the discretization asymmetry. We need to make it quantitative.

---

## 2. The infomax objective

From `main.tex` Eq. (1), the static finite-$n$ optimal prior over a parameter $\theta$ is

$$p^*(\theta \mid n, p_{x \mid \theta}) = \arg\max_{p(\theta)} I\!\left(\theta; \{x_1, \ldots, x_n\}\right)$$

with the BA update (Appendix §A.1):

$$p_{\tau+1}(\theta) \;=\; \frac{1}{Z_\tau} \exp\!\left[ \mathrm{KL}\!\left( p(X \mid \theta) \;\|\; p(X) \right) \right] p_\tau(\theta)$$

where $X = (x_1, \ldots, x_n)$ and $p(X) = \sum_\theta p(X \mid \theta) p_\tau(\theta)$.

For i.i.d. observations, $p(X \mid \theta) = \prod_i p(x_i \mid \theta)$, and the KL decomposes:

$$\mathrm{KL}\!\left( p(X \mid \theta) \;\|\; p(X) \right) \;\neq\; n \cdot \mathrm{KL}\!\left( p(x \mid \theta) \;\|\; p(x) \right)$$

(the LHS is not $n \times$ the single-trial KL because $p(X) = \sum_\theta \prod_i p(x_i \mid \theta) p(\theta)$ is *not* $\prod_i p(x)$ — the marginal over multiple trials carries information about $\theta$ that the per-trial marginal doesn't). This is the standard subtlety in finite-$n$ infomax; the single-trial Jeffreys limit is only recovered as $n \to \infty$.

> M: ok so I'm not sure this actually makes sense. Will have to check.

**This is the term we actually need to evaluate, and it's where the asymmetry between AP and RV will live.**

---

## 3. What we need to derive

### 3.1 The per-trial likelihoods $p(x \mid \theta)$ for each parameter

For the **AP-only** problem (RV fixed at 0.5):

$$p(x \mid AP) \;=\; \sum_{z \in \{\pm 1\}} P(x \mid z; RV=0.5) \, P(z; AP)$$

This is a mixture of two fixed component distributions with mixing weight $AP$. Standard exponential-family-ish structure; Fisher information is well-behaved.

For the **RV-only** problem (AP fixed at 0.5):

$$p(x \mid RV) \;=\; \sum_{z \in \{\pm 1\}} P(x \mid z; RV) \cdot \tfrac{1}{2}$$

This is a mixture of two *RV-dependent* component distributions with equal weights. The RV-dependence is concentrated at the diagnostic region per §8.4.

**TODO 1.** Write out both $p(x \mid AP)$ and $p(x \mid RV)$ explicitly, using the manuscript's construction of $P(x \mid z; RV)$. We need closed forms (or at least numerical evaluations on a grid) of both.

### 3.2 Fisher information for each parameter — the paper-and-pencil step

Before any BA runs, compute and plot:

$$\mathcal{I}_{AP}(AP) \;=\; \mathbb{E}_{x \mid AP} \!\left[ \left( \partial_{AP} \log p(x \mid AP) \right)^2 \right]$$

$$\mathcal{I}_{RV}(RV) \;=\; \mathbb{E}_{x \mid RV} \!\left[ \left( \partial_{RV} \log p(x \mid RV) \right)^2 \right]$$

**Prediction to test.** If the asymmetry hypothesis is right, $\mathcal{I}_{RV}$ should be sharply peaked or spiked (informative only in a narrow regime of $x$), while $\mathcal{I}_{AP}$ should be smooth and slowly varying. The Jeffreys prior $\propto \sqrt{\mathcal{I}}$ is the $n \to \infty$ limit of the infomax prior; if $\sqrt{\mathcal{I}_{RV}}$ is already concentrated and $\sqrt{\mathcal{I}_{AP}}$ is diffuse, that's the first sign that finite-$n$ BA will discretize RV but not AP.

**TODO 2.** Compute $\mathcal{I}_{AP}$ and $\mathcal{I}_{RV}$ analytically where possible, numerically otherwise. Plot.

### 3.3 The multi-trial KL for BA

For the BA update we need

$$D_n(\theta) \;:=\; \mathrm{KL}\!\left( p(x_1, \ldots, x_n \mid \theta) \;\|\; p(x_1, \ldots, x_n) \right)$$

evaluated on a discretized grid of $\theta$ values.

For i.i.d. observations this is

$$D_n(\theta) \;=\; \int dx_1 \cdots dx_n \; \prod_i p(x_i \mid \theta) \log \frac{\prod_i p(x_i \mid \theta)}{\sum_{\theta'} \prod_i p(x_i \mid \theta') p(\theta')}$$

The high-dimensional integral is the practical obstacle. Standard tricks:

- Monte Carlo over $X$ sampled from $p(X \mid \theta)$
- For moderate $n$, sufficient statistics: AP only enters through $\sum_i \mathbb{1}[z_i = +1]$ (which the agent doesn't observe directly but only through $x_i$), so we may be able to reduce the integral to a 1D or 2D one over sufficient stats of $X$
- For very large $n$, asymptotic expansion gives $D_n(\theta) \approx \tfrac{1}{2}\log n + \tfrac{1}{2}\log \mathcal{I}(\theta) + \text{const}$ — useful as a sanity check

**TODO 3.** Decide which evaluation strategy to use for each of (AP-only, RV-only, joint AP–RV). MC is the safe default but may be expensive at large $n$.

### 3.4 Discretization of the parameter support

BA operates on a finite grid. The choice of grid affects what "discrete" means in the output: if we discretize $\theta$ on a grid of 50 points, BA can at best return mass on those 50 points, and "discrete output" means *the support of $p^*$ collapses to a small subset of the grid*.

**TODO 4.** Specify grid resolution and support range:
- AP grid: $[0.5, 1.0]$ in steps of e.g. 0.01 → 51 points
- RV grid: $[0.5, 1.0]$ in steps of e.g. 0.01 → 51 points
- Joint grid: 51 × 51 = 2601 points
- Should verify the qualitative result is stable under grid refinement (factor of 2 either way)

The choice of support endpoint matters — extending RV beyond [0.5, 1] vs truncating matters for whether atoms appear at the boundary or in the interior. **This is where the "atoms appear only because of boundary truncation" worry from the previous discussion bites.** We should run BA on at least two support choices to check.

### 3.5 Joint AP–RV case

The joint problem has $p(x \mid AP, RV)$ given by the manuscript's full construction. The ridge means there are many $(AP, RV)$ combinations with nearly equal $p(x)$ at the marginal level, but they can be distinguished given enough trials (because $p(x_1, \ldots, x_n)$ retains some information about which combination generated the data through the joint structure — this is exactly why the manuscript's *dynamic* model can pick atoms at all).

**Open question for the joint case.** Does finite-$n$ BA on the joint $(AP, RV)$ space:
(a) Concentrate on the ridge (a 1D structure within the 2D grid) but spread continuously along it?
(b) Concentrate on a few discrete points along the ridge, near the endpoints?
(c) Concentrate on points off the ridge somewhere?

Answer (b) with endpoints near $\{AP=0.5, RV=q\}$ and $\{AP=q, RV=0.5\}$ would be the strong version of the original state-file hypothesis. Answer (a) would mean the marginal asymmetry story (per-parameter discretization) is the better framing and the joint analysis is largely a confirmation.

---

## 4. Simulation spec

### 4.1 Experiment 1 — Marginal infomax, AP only

- Fix $RV = 0.5$
- Compute $p(x \mid AP)$ on a fine $x$ grid for each $AP$ in $\{0.5, 0.51, \ldots, 1.0\}$
- Run BA for $n \in \{1, 5, 10, 20, 50, 100, 200, 500, 1000\}$
- Output: $p^*(AP)$ for each $n$

### 4.2 Experiment 2 — Marginal infomax, RV only

- Same as 4.1 but with $AP = 0.5$ fixed and $RV$ varying
- Same grid of $n$
- Output: $p^*(RV)$ for each $n$

### 4.3 Experiment 3 — Joint infomax

- Both AP and RV vary on the 2D grid
- Same grid of $n$ (or a coarser subset, since this is more expensive)
- Output: $p^*(AP, RV)$ for each $n$, plus the marginals $p^*(AP) = \sum_{RV} p^*(AP, RV)$ and vice versa

### 4.4 Sensitivity checks

- Grid resolution: re-run at half and double resolution for at least one $n$, confirm shape of $p^*$ is stable
- Support endpoints: extend AP, RV ranges beyond [0.5, 1] (e.g. allow [0.4, 1] or [0.5, 1.2] with appropriate construction) and check if atoms move

---

## 5. Curves to plot

1. **The two likelihoods.** $p(x \mid AP)$ for a few values of $AP$ overlaid; same for RV. To make the qualitative shape difference visible.
2. **The two Fisher informations.** $\mathcal{I}_{AP}(AP)$ and $\mathcal{I}_{RV}(RV)$ side by side. Predicted: smooth-ish for AP, spiked for RV.
3. **Jeffreys priors as $n \to \infty$ limit.** $\sqrt{\mathcal{I}_{AP}} / Z$ and $\sqrt{\mathcal{I}_{RV}} / Z$. Predicted: diffuse for AP, concentrated for RV.
4. **Infomax priors vs $n$ — marginal cases.** A grid of plots: rows = parameter (AP, RV), columns = $n$. Each cell shows $p^*(\theta)$ at that $n$. Predicted: RV row discretizes at small $n$, AP row stays diffuse for a much wider range of $n$.
5. **Support size vs $n$.** A scalar summary: number of grid points with $p^*(\theta) >$ threshold (e.g. 0.01), as a function of $n$, for both AP and RV. Predicted: RV support collapses to 2 atoms at moderate $n$; AP support stays large.
6. **Joint $p^*(AP, RV)$ as a function of $n$.** Heatmaps overlaid with the manuscript's ridge. Predicted (per the new framing): mass concentrates *along the ridge*, with the concentration along the $RV$ axis sharper than along the $AP$ axis, producing atoms preferentially at the ridge endpoint $\{AP=0.5, RV=q\}$.

---

## 6. Open derivation questions before any code runs

1. **Closed form (or at least clean numerical recipe) for $P(x \mid z; RV)$.** §8.4 of the manuscript defines this implicitly through Eqs. 37–42, which requires knowing $P_{UB}(z=1 \mid x)$ and $P(x)$ first. Is there an existing implementation we're reusing, or do we need to reconstruct it?

2. **The multi-trial marginal $p(x_1, \ldots, x_n)$ — how to evaluate efficiently.** Sufficient statistics? MC? Asymptotic approximation for sanity check?

3. **Sanity check for the $n \to \infty$ limit.** Does BA recover the Jeffreys prior $\propto \sqrt{\mathcal{I}}$ as $n$ grows large for both AP and RV? If yes, that validates the implementation. If RV's Jeffreys is already two-peaked, the discretization story is essentially the asymptotic story and the finite-$n$ result is less surprising; if Jeffreys is smooth but BA discretizes at finite $n$, that's a more interesting result.

4. **What grid for $\theta$ is fair?** Equal-spaced vs. spaced according to $\sqrt{\mathcal{I}(\theta)} d\theta$ (Jeffreys metric). The latter is more principled but harder to interpret visually. Start with equal-spaced and revisit if results look grid-artifact-y.

---

## 7. What this experiment can and can't settle

**Settles:** Whether the manuscript's likelihood structure naturally produces a discretization asymmetry between AP and RV under finite-$n$ infomax. If yes, that's the seed of a normative story for why RV is the jumpy parameter. If no, the reframing fails and we go back to the drawing board.

**Doesn't settle:** What $n$ corresponds to for the experimental participant. We can plot $p^*$ across a range of $n$ and observe the transition, but mapping that to a real-world horizon needs a separate argument (probably tied to $D_{RV}$ in the manuscript's dynamics hyperprior, per the previous discussion).

**Doesn't settle:** Whether discretization of RV at the *representation* level actually causes CP-like *behavioral* trajectories of RV (the Reading-2 question from the previous turn). That requires a dynamic version of the model and a different simulation.
