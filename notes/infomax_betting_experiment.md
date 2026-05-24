# Does the information-optimal prior win at betting?

## 1. Motivation and claim

The Blahut–Arimoto (BA) algorithm applied to the finite-data mutual information objective produces a prior $p^*$ that maximises $I(\theta; X_{1:n})$ — the expected number of bits about the latent $\theta$ carried by $n$ future observations. Under mild conditions $p^*$ is discrete, with a finite number $K^*$ of atoms in $[0,1]$ for a Bernoulli observation model.

The claim we want to test is: **using $p^*$ as the prior leads to better expected performance in a Kelly-style betting game than using a smooth reference prior (Jeffreys, uniform)**, where "better" is averaged over a distribution $q$ of generating $\theta$ that we sample from a flexible nonparametric family, and where $q$ is *not* equal to $p^*$ — i.e. the agent is not artificially matched to nature.

The experiment is split into two parts:

- **Part 1 (one-shot Kelly on one toss).** Tests whether $p^*$ produces a better posterior-mean function than Beta priors. Only the posterior mean enters the bet, so this part can only show differences in how priors smooth data into a predictive probability.
- **Part 2 (one-shot bet on a pattern over $k$ future tosses).** The bet payoff depends on higher moments / the full shape of the posterior, so the discreteness of $p^*$ — placement of atoms, variance structure — can enter the result.

## 2. Notation

- $\theta \in [0,1]$: probability of heads on a Bernoulli toss.
- $X_{1:n} = (X_1, \dots, X_n) \in \{0,1\}^n$: training observations.
- $k_n = \sum_{i=1}^n X_i$: number of heads in $n$ tosses; sufficient statistic for $\theta$ under the Bernoulli likelihood.
- $p(\theta)$: prior on $\theta$. Special cases: $p_{\mathrm{U}} = \mathrm{Beta}(1,1)$ (uniform), $p_{\mathrm{J}} = \mathrm{Beta}(0.5, 0.5)$ (Jeffreys), $p^*_n$ (info-optimal for budget $n$).
- $p(\theta \mid X_{1:n})$: posterior. For Beta$(\alpha,\beta)$ prior this is Beta$(\alpha+k_n, \beta+n-k_n)$. For discrete $p^* = \sum_a \pi_a \delta_{\theta_a}$ this is $\sum_a \pi'_a \delta_{\theta_a}$ with $\pi'_a \propto \pi_a \theta_a^{k_n}(1-\theta_a)^{n-k_n}$.
- $\hat\mu_n(p, X_{1:n}) = \mathbb{E}_{p(\theta \mid X_{1:n})}[\theta]$: posterior mean. This is the agent's predictive probability for the next toss.
- $\hat\mu_n^{(j)}(p, X_{1:n}) = \mathbb{E}_{p(\theta \mid X_{1:n})}[\theta^j]$: $j$-th posterior raw moment.
- $q(\theta)$: "nature's" distribution over the true $\theta$, sampled from a hyperprior described in §5.

## 3. The prior $p^*$: definition and computation

The info-optimal prior for budget $n$ is

$$
p^*_n = \argmax_{p} I_p(\theta; X_{1:n}) = \argmax_p \sum_{X \in \{0,1\}^n} \int p(\theta) p(X \mid \theta) \log \frac{p(X \mid \theta)}{p(X)} \, d\theta
$$

with $p(X) = \int p(\theta) p(X \mid \theta) d\theta$. For Bernoulli observations $X_{1:n}$ depends on $\theta$ only through $k_n \sim \mathrm{Binomial}(n, \theta)$, so the MI can be computed in the sufficient-statistic space:

$$
I_p(\theta; k_n) = \sum_{k=0}^n \int p(\theta) \binom{n}{k} \theta^k (1-\theta)^{n-k} \log \frac{\binom{n}{k}\theta^k(1-\theta)^{n-k}}{p(k)} \, d\theta
$$

with $p(k) = \int p(\theta) \binom{n}{k}\theta^k(1-\theta)^{n-k} d\theta$. The $\binom{n}{k}$ factor cancels in the log ratio, leaving

$$
I_p(\theta; k_n) = \sum_{k=0}^n \int p(\theta) \binom{n}{k}\theta^k(1-\theta)^{n-k} \log \frac{\theta^k(1-\theta)^{n-k}}{\tilde p(k)} \, d\theta
$$

where $\tilde p(k) = p(k)/\binom{n}{k} = \int p(\theta) \theta^k(1-\theta)^{n-k} d\theta$.

### BA updates

We discretise $[0,1]$ on a fine grid $\theta_1, \dots, \theta_G$ (e.g. $G=1000$) and iterate

$$
p_{\tau+1}(\theta_i) = \frac{1}{Z_\tau} \, p_\tau(\theta_i) \, \exp\!\Big( \mathrm{KL}\big( p(k \mid \theta_i) \,\|\, p_\tau(k) \big) \Big)
$$

where $p(k \mid \theta_i) = \binom{n}{k} \theta_i^k (1-\theta_i)^{n-k}$ and $p_\tau(k) = \sum_i p_\tau(\theta_i) p(k \mid \theta_i)$. The KL is over the $n+1$ values of $k$. Iterate until $\| p_{\tau+1} - p_\tau \|_1 < \epsilon$.

The fixed point has support on a finite set of grid points; we extract atoms by thresholding $p_\tau(\theta_i) > \eta$ (e.g. $\eta = 10^{-4}$) and re-normalising. Call the resulting discrete distribution $p^*_n = \sum_{a=1}^{K^*_n} \pi_a \, \delta_{\theta_a}$.

## 4. Expected Kelly log-wealth — analytic formulas

### 4.1 Part 1: one-shot bet on toss $n+1$

After $n$ observations the agent forms posterior $p(\theta \mid X_{1:n})$ and bets a Kelly fraction $f = 2\hat\mu - 1$ of wealth on heads, where $\hat\mu = \hat\mu_n(p, X_{1:n})$. Realised log-growth against truth $\theta$ is

$$
G_1(\theta, \hat\mu) = \theta \log(1+f) + (1-\theta)\log(1-f) = \theta \log(2\hat\mu) + (1-\theta)\log(2(1-\hat\mu)).
$$

This rearranges to

$$
G_1(\theta, \hat\mu) = \log 2 - H_{\mathrm{Bin}}(\theta) - \mathrm{KL}\!\big(\mathrm{Bern}(\theta) \,\|\, \mathrm{Bern}(\hat\mu)\big)
$$

where $H_{\mathrm{Bin}}(\theta) = -\theta\log\theta - (1-\theta)\log(1-\theta)$ is the binary entropy.

**Expectation over observations given $\theta$.** $X_{1:n}$ enters only through $k_n$, so

$$
V_1(\theta, p, n) = \mathbb{E}_{k_n \sim \mathrm{Bin}(n,\theta)}\big[ G_1(\theta, \hat\mu_n(p, k_n)) \big] = \sum_{k=0}^n \binom{n}{k}\theta^k(1-\theta)^{n-k} \, G_1(\theta, \hat\mu_n(p, k)).
$$

This is a finite sum over $n+1$ terms; analytic given $\hat\mu_n(p, k)$.

**Posterior mean as a function of $k$.**

- For Beta$(\alpha, \beta)$ prior: $\hat\mu_n(p, k) = (\alpha + k)/(\alpha + \beta + n)$.
- For discrete $p^* = \sum_a \pi_a \delta_{\theta_a}$: $\hat\mu_n(p^*, k) = \sum_a \theta_a \, \pi'_a(k)$ with $\pi'_a(k) \propto \pi_a \theta_a^k (1-\theta_a)^{n-k}$, normalised over $a$.

**Expectation over $\theta$ under nature $q$.** This is the quantity we ultimately report:

$$
\bar V_1(p, n, q) = \int_0^1 V_1(\theta, p, n) \, q(\theta) \, d\theta.
$$

For $q$ a Beta mixture $q(\theta) = \sum_{j=1}^J w_j \, \mathrm{Beta}(\theta; a_j, b_j)$, this becomes a sum of integrals against a single Beta. Each integral has the form

$$
\int_0^1 \theta^k(1-\theta)^{n-k} \, F(\theta) \, \mathrm{Beta}(\theta; a, b) \, d\theta
$$

with $F$ being one of $\log\hat\mu$, $\log(1-\hat\mu)$, $\theta\log\theta$, $(1-\theta)\log(1-\theta)$, or $\log 2$. Decomposing $G_1$ into these pieces:

$$
G_1(\theta, \hat\mu) = \log 2 + \theta\log\hat\mu + (1-\theta)\log(1-\hat\mu).
$$

Then

$$
V_1(\theta, p, n) = \log 2 + \sum_{k=0}^n \binom{n}{k}\theta^k(1-\theta)^{n-k} \Big[ \theta \log\hat\mu_n(p,k) + (1-\theta) \log(1-\hat\mu_n(p,k)) \Big].
$$

Note $\log \hat\mu_n(p,k)$ does not depend on $\theta$ — it's a constant for each $(p, k)$. So

$$
\bar V_1(p, n, q) = \log 2 + \sum_{k=0}^n \binom{n}{k} \Big[ \log\hat\mu_n(p,k) \cdot M_{k+1, n-k}(q) + \log(1-\hat\mu_n(p,k)) \cdot M_{k, n-k+1}(q) \Big]
$$

where

$$
M_{r,s}(q) = \int_0^1 \theta^r (1-\theta)^s \, q(\theta) \, d\theta.
$$

For a Beta mixture, $M_{r,s}(q) = \sum_j w_j \cdot B(a_j + r, b_j + s) / B(a_j, b_j)$, which is exact.

**So $\bar V_1$ is fully analytic** given the Beta-mixture parameters of $q$ and the posterior-mean function $\hat\mu_n(p, k)$.

### 4.2 Part 2: one-shot bet on a pattern over $k_+$ future tosses

We bet on a specific pattern $\omega \in \{0,1\}^{k_+}$ being realised by tosses $n+1, \dots, n+k_+$ (for concreteness, $\omega = (1,1,\dots,1) = $ "all heads"). Under the agent's belief, the predictive probability of $\omega$ is

$$
\hat r_n(p, X_{1:n}, \omega) = \mathbb{E}_{p(\theta\mid X_{1:n})}\!\left[ \theta^{|\omega|}(1-\theta)^{k_+ - |\omega|} \right]
$$

where $|\omega|$ is the number of 1s in $\omega$. For $\omega = $ all-heads, $\hat r = \hat\mu^{(k_+)}_n$, the $k_+$-th raw posterior moment.

The bet is even-money on the pattern: stake $f$, gain $f$ if $\omega$ occurs, lose $f$ otherwise. Kelly fraction $f = 2\hat r - 1$ (set to $0$ if $\hat r \le 0.5$). Realised log-growth against truth $\theta$:

$$
G_2(\theta, \hat r, k_+) = r(\theta) \log(2 \hat r) + (1-r(\theta)) \log(2(1-\hat r))
$$

where $r(\theta) = \theta^{|\omega|}(1-\theta)^{k_+ - |\omega|}$ is the truth's probability of the pattern.

**Expectation over training observations.** Same structure as before: $X_{1:n}$ enters via $k_n$, and the pattern outcome is independent of $X_{1:n}$ given $\theta$. So

$$
V_2(\theta, p, n, k_+) = \sum_{k=0}^n \binom{n}{k} \theta^k (1-\theta)^{n-k} \, G_2(\theta, \hat r_n(p, k, \omega), k_+).
$$

**Posterior pattern probability as a function of $k$.**

- For Beta$(\alpha,\beta)$ prior with $\omega = $ all-heads: posterior is Beta$(\alpha+k, \beta+n-k)$, and

$$
\hat r_n(\mathrm{Beta}(\alpha,\beta), k, \mathrm{all\text{-}heads}) = \frac{B(\alpha+k+k_+, \beta+n-k)}{B(\alpha+k, \beta+n-k)} = \prod_{j=0}^{k_+ - 1} \frac{\alpha+k+j}{\alpha+\beta+n+j}.
$$

- For discrete $p^*$: $\hat r_n(p^*, k, \omega) = \sum_a \pi'_a(k) \, \theta_a^{|\omega|}(1-\theta_a)^{k_+ - |\omega|}$.

**Expectation over $\theta$ under nature $q$.** Decompose $G_2$:

$$
G_2(\theta, \hat r, k_+) = \log 2 + r(\theta) \log \hat r + (1 - r(\theta)) \log(1-\hat r).
$$

For $\omega = $ all-heads, $r(\theta) = \theta^{k_+}$. Then

$$
\bar V_2(p, n, q, k_+) = \log 2 + \sum_{k=0}^n \binom{n}{k} \Big[ \log\hat r_n(p,k) \cdot M_{k+k_+, n-k}(q) + \log(1-\hat r_n(p,k)) \cdot \big(M_{k, n-k}(q) - M_{k+k_+, n-k}(q)\big) \Big].
$$

Again exact for Beta-mixture $q$ via the $M_{r,s}$ moments.

## 5. The hyperprior over $q$

$q(\theta) = \sum_{j=1}^K w_j \, \mathrm{Beta}(\theta; a_j, b_j)$ with $K$ growing from a small starting value.

- $K$ starts at $K=1$ (single Beta) and grows; we decide whether to push it higher based on whether the qualitative result has stabilised.
- $w \sim \mathrm{Dirichlet}(\mathbf{1}_K)$ (symmetric, flat over the simplex).
- $(a_j, b_j)$ drawn iid from a hyperprior $\mathcal{H}$ that controls the *qualitative shape* of components:

  - **H1 (endpoint-favouring):** $a_j, b_j \sim \mathrm{Uniform}(0.3, 1.0)$. Components are U-shaped or flat, putting mass near $\{0, 1\}$.
  - **H2 (interior-favouring):** $a_j, b_j \sim \mathrm{Uniform}(2, 10)$. Components are unimodal bumps in the interior.
  - **H3 (agnostic):** $\log a_j, \log b_j \sim \mathrm{Uniform}(\log 0.3, \log 10)$. Covers both regimes.

For each hyperprior we draw $S_q$ samples of $q$ (a sample = a draw of $K, w, \{(a_j, b_j)\}_{j=1}^K$ — though $K$ is fixed per experimental cell, not random within a cell).

## 6. The full experimental design

**Fixed factors:**
- $n \in \{2, 3, 5, 10, 20\}$.
- Three priors compared: $p^*_n$ (info-optimal), $p_{\mathrm{J}} = \mathrm{Beta}(0.5, 0.5)$, $p_{\mathrm{U}} = \mathrm{Beta}(1,1)$.
- Three hyperpriors: H1, H2, H3.
- $K \in \{1, 2, 3\}$ initially; expand if results are not stable.
- Part 2: $k_+ \in \{2, 3, 5\}$.
- Part 2 only: add moment-matched Beta control $p_{\mathrm{MM}}$, defined as the Beta with the same mean and variance as $p^*_n$ (closed-form: given mean $\mu$ and variance $\sigma^2$, set $\alpha = \mu(\mu(1-\mu)/\sigma^2 - 1)$, $\beta = (1-\mu)(\mu(1-\mu)/\sigma^2 - 1)$).

**Sample sizes:**
- $S_q$ samples of $q$ per (hyperprior, $K$) cell. Start with $S_q = 200$; check Monte-Carlo standard error and increase if needed.
- No sampling over $X_{1:n}$ or $\theta$ — both expectations are closed-form given $q$ as a Beta mixture.

**Procedure (per cell of the experimental design):**

1. Compute $p^*_n$ via BA on a grid of $G=1000$ points until $L_1$ convergence $< 10^{-8}$. Extract atoms.
2. For each prior $p \in \{p^*_n, p_{\mathrm{J}}, p_{\mathrm{U}}\}$ (and $p_{\mathrm{MM}}$ for Part 2), precompute $\hat\mu_n(p, k)$ for $k = 0, \dots, n$ (Part 1) and $\hat r_n(p, k, \omega)$ for $k = 0, \dots, n$ (Part 2).
3. For each of $S_q$ samples of $q$:
   - Compute moments $M_{r,s}(q)$ for all needed $(r, s)$ pairs. For Part 1: $(r,s) \in \{(k+1, n-k), (k, n-k+1) : k = 0, \dots, n\}$. For Part 2: $(r, s) \in \{(k+k_+, n-k), (k, n-k) : k = 0, \dots, n\}$.
   - Compute $\bar V_1(p, n, q)$ for each prior $p$ using the closed-form formula in §4.1.
   - Compute $\bar V_2(p, n, q, k_+)$ for each prior $p$ and each $k_+$ using the formula in §4.2.
   - Record the *difference* $\bar V(p^*) - \bar V(p)$ for each comparison prior $p$.
4. Aggregate over $S_q$: report mean, standard error, fraction of samples where $p^*$ wins.

## 7. Plots and tables

- **Plot A (per part).** For each (hyperprior, $K$), heatmap of mean $\bar V(p^*_n) - \bar V(p_{\mathrm{J}})$ over $(n, k_+)$. Same for vs $p_{\mathrm{U}}$. Red = $p^*$ wins, blue = loses.
- **Plot B.** Per hyperprior and per $n$, the distribution (across the $S_q$ samples of $q$) of $\bar V(p^*_n) - \bar V(p_{\mathrm{J}})$ as a histogram or violin plot. Shows not just the mean but the spread — does $p^*$ win on average because it wins everywhere, or because of a few big wins?
- **Plot C.** Per $n$, plot of $p^*_n$ itself: atom locations and weights. Helps interpret which regions of $\theta$ the prior is "betting on" being informative.
- **Plot D (Part 2 only).** $\bar V$ difference as a function of $k_+$, separately for $p^*$ vs $p_{\mathrm{J}}$ and $p^*$ vs $p_{\mathrm{MM}}$. The $p^*$ vs $p_{\mathrm{MM}}$ comparison isolates the contribution of discreteness beyond moment-matching.
- **Table.** Summary: for each (Part, $n$, hyperprior, comparison), the mean advantage of $p^*$ and the fraction of $q$ samples where it wins.

## 8. What each result would mean

- **Part 1, $p^*$ beats Beta priors under H1:** $p^*$'s endpoint-loving structure aligns with H1's endpoint-loving nature samples; expected, less informative.
- **Part 1, $p^*$ beats Beta priors under H2:** non-trivial — would mean the posterior-mean function of $p^*$ is genuinely better-calibrated for interior $\theta$, not just better-aligned.
- **Part 1, $p^*$ beats Beta priors under H3:** the headline result we want. Robust advantage across nature shapes.
- **Part 2, $p^*$ beats $p_{\mathrm{J}}$ but not $p_{\mathrm{MM}}$:** the advantage is moment-level, not shape-level. Discreteness per se isn't doing extra work.
- **Part 2, $p^*$ beats $p_{\mathrm{MM}}$:** discreteness is doing extra work — the shape of the posterior, not just its first two moments, is what's helping. This would be the strongest evidence for the structural distinctiveness of $p^*$.
- **$p^*$ loses to $p_{\mathrm{J}}$ in some regime (especially H2):** would mark the boundary of the claim. Useful to know and report.

## 9. Open issues to revisit

- The advantage scales with $1/n$ in some intuitive sense (small $n$ = prior matters more); we should verify and quantify.
- For very small $n$ (e.g. $n=2$), the BA prior may concentrate on just 2 atoms ($\theta \in \{0, 1\}$); the comparison with smooth priors is then almost a caricature. Worth examining the $n$ at which $K^*$ transitions.
- We may want to add a non-Kelly bet variant later (e.g. fixed-stake binary bet) to confirm that the result depends on the log-proper-score structure as predicted.
- What is a betting game in which the shape of the distribution matters beyond the moments? 
