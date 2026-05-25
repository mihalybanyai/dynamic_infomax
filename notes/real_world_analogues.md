# Real-world decision problems with the structure of a density-region bet

This note collects the real-world phenomena that share mathematical structure with the kind of betting game we want to use to test the information-optimal prior $p^*$. The common pattern is:

- A continuous latent parameter $\theta$ that the agent is uncertain about.
- A finite budget of $n$ noisy observations from which the agent forms a posterior $p(\theta \mid X_{1:n})$.
- A decision set that is *not* a point estimate of $\theta$ — typically discrete actions or region-keyed payoffs — so that the Bayes-optimal action depends on *functionals of the posterior beyond the mean*: tail probabilities $P(\theta \in A \mid X_{1:n})$, higher moments, or the full shape.

These are precisely the conditions under which $p^*$ might have an advantage over smooth reference priors, because the extra bits about $\theta$ that $p^*$ extracts from $n$ observations can be cashed in by the loss function, not washed out by linearity in the posterior mean.

## 1. Clinical trial decisions and treatment thresholds

### Structure

A Bayesian phase-II or phase-III trial estimates a treatment effect $\theta$ (e.g. response rate difference, log hazard ratio) from $n$ patients. The decision rule is typically of the form

$$
\text{advance treatment} \iff P\big(\theta > \tau \,\big|\, X_{1:n}\big) > p_*
$$

where $\tau$ is a minimum clinically important difference (MCID) and $p_*$ is a posterior probability cutoff (commonly $0.95$ or $0.975$). This is exactly a density-region bet with $A = (\tau, \infty)$ and a discrete action set $\{\text{advance}, \text{do not advance}\}$.

The systematic review by the Journal of Clinical Epidemiology (2024) found that across recent Bayesian drug trials, "A decision threshold was set a priori in 68% of the results, and its value ranged from 70% to 99% (median 95%)." So this is genuinely how decisions are made, not a stylised model.

### Mathematical detail

For a binary endpoint with response rate $\theta \in [0,1]$ and $n$ patients with $k_n$ responders, under prior $p(\theta)$:

$$
P(\theta > \tau \mid k_n) = \frac{\int_\tau^1 \theta^{k_n}(1-\theta)^{n-k_n} p(\theta) \, d\theta}{\int_0^1 \theta^{k_n}(1-\theta)^{n-k_n} p(\theta) \, d\theta}.
$$

This is a non-polynomial functional of the posterior — it's a tail integral against an indicator function. No finite list of posterior moments captures it. The decision is a step function of this quantity. So the *whole shape* of the posterior in the region near $\tau$ matters, and a prior that places mass intelligently near plausible values of $\theta$ — which $p^*$ does, in a finite-data-optimal sense — should plausibly outperform a Jeffreys or uniform prior.

The "moment-matched Beta" control we discussed for the betting experiment will *not* generally produce the same tail probability as a discrete $p^*$ even with matched first two moments, because the third and higher moments of the two priors differ, and the tail probability depends on them.

### Operating characteristics and design priors

Bayesian trial design uses two priors: an **analysis prior** used in the posterior update during the trial, and a **design prior** (or sampling prior) used to compute operating characteristics (Bayesian power, type-I error rate, assurance) before the trial. The design prior is essentially nature's $q$ — the distribution of $\theta$ over which performance is averaged when choosing $n$ and $p_*$. The Golchi & Willard (2023) framework formalises this.

The mapping to our experiment is direct: their analysis prior is our $p$ (where $p$ could be $p^*$ or Jeffreys); their design prior is our $q$; their operating characteristic is our $\bar V$. The question "does $p^*$ give better operating characteristics than Jeffreys when averaged over $q$ sampled from a Beta-mixture hyperprior?" is the same as the question their methodology is built to ask.

### References

- Golchi & Willard (2023), "Estimating the Sampling Distribution of Posterior Decision Summaries in Bayesian Clinical Trials", arXiv:2306.09151.
- Berry, Carlin, Lee & Müller (2010), *Bayesian Adaptive Methods for Clinical Trials*. Chapman & Hall/CRC.
- Spiegelhalter, Abrams & Myles (2004), *Bayesian Approaches to Clinical Trials and Health-Care Evaluation*. Wiley.
- Journal of Clinical Epidemiology systematic review of Bayesian drug trial priors and decision thresholds (2024), DOI:10.1016/j.jclinepi.2024.111568.
- For threshold-utility decision analysis specifically: Blangero, Rabilloud, Ecochard & Subtil (2019), "A Bayesian method to estimate the optimal threshold of a marker used to select patients' treatment", Statistical Methods in Medical Research.

## 2. Bayesian foraging and patch-leaving decisions

### Structure

A forager arrives at a patch and starts collecting prey items. Patch quality $\theta$ — the encounter rate of prey, or the total number of prey remaining — is unknown. As the forager forages, it collects observations $X_{1:n}$ (each $X_i$ is the time-to-next-capture, or the binary outcome of a search interval). It maintains a posterior over $\theta$ and at each moment must decide between two discrete actions: **stay** or **leave for another patch**.

The optimal policy, in its cleanest formulation, is: leave the patch when the expected reward rate from staying drops below the environmental average reward rate $\bar R$. Crucially, "expected reward rate from staying" depends on the *posterior* over $\theta$, not just its mean, because:

1. Staying has option value — even if the current estimate of $\theta$ is low, high posterior variance means there's a chance the patch is actually good and worth more sampling.
2. The decision is binary, so what matters is the posterior probability that staying is better than leaving, not a smooth function of the mean.

This is a density-region bet with $A = \{\theta : \text{staying is better than leaving given }\theta\}$, evaluated under the current posterior, with a sequential rather than one-shot structure.

### Mathematical detail (Iwasa-Higashi-Yamamura model)

Consider a patch containing an unknown number $N$ of prey, with prior distribution $\pi(N)$. The forager catches prey at random with rate proportional to the number remaining. After time $T$ in the patch with $N_c$ captures, the posterior over the number remaining $N - N_c$ is

$$
P(N - N_c = m \mid T, N_c) \propto \pi(N_c + m) \cdot \binom{N_c + m}{N_c} e^{-\lambda T (N_c + m)}
$$

up to normalisation. The decision to leave is made when the expected instantaneous reward rate $\lambda \mathbb{E}[N - N_c \mid T, N_c]$ drops below the environmental average $\bar R$. The original paper showed that this expectation depends only on $(T, N_c)$ and that the leaving rule is monotone in these sufficient statistics.

The structural feature we care about: the leaving rule depends on a *threshold on a functional of the posterior* (the expected remaining prey), and that functional is sensitive to the prior $\pi(N)$ in a way that goes beyond its mean — both the posterior mean and its dependence on $(T, N_c)$ change with $\pi$. A more "informative" $\pi$ (in our BA sense) would give sharper posterior estimates from each observation, leading to faster correct leave decisions in low-quality patches and more persistent staying in high-quality ones.

### Modern Bayesian foraging models

Davidson & El Hady (2020) extend this to continuous-time inference with explicit drift-diffusion implementations. Their framework treats the log-posterior-odds between "good patch" and "bad patch" hypotheses as a diffusion process, and the leave decision as crossing a threshold. This connects directly to perceptual decision-making models (drift-diffusion / sequential probability ratio tests). For our project, the relevant point is that this is *literally* a density-region bet ("is patch quality in the good region or the bad region?") in a sequential setting, and the choice of prior over patch qualities has direct behavioural consequences.

Kilpatrick, Davidson & El Hady (2021) show that uncertainty about the environment's structure (the distribution of patch qualities) drives systematic deviations from naive marginal-value-theorem predictions. The environment's distribution of patch qualities is the foraging analogue of our $q$, and the forager's internal prior over patch qualities is the analogue of our $p$. Whether real animals use something like an info-optimal prior over patch qualities is, as far as I can tell, an open question.

### Empirical relevance

The mouse foraging study (Vertechi et al. 2024, PMC10996644) found mice's patch-leaving decisions are consistent with MVT-plus-Bayesian-updating, "and not explainable by simple ethologically motivated heuristic strategies". So the Bayesian framework is empirically supported, not just normative.

### References

- Iwasa, Higashi & Yamamura (1981), "Prey distribution as a factor determining the choice of optimal foraging strategy", American Naturalist 117(5): 710-723. Foundational Bayesian foraging.
- McNamara (1982), "Optimal patch use in a stochastic environment", Theoretical Population Biology 21(2): 269-288.
- Charnov (1976), "Optimal foraging, the marginal value theorem", Theoretical Population Biology 9: 129-136. The non-Bayesian precursor.
- McNamara, Green & Olsson (2006), "Bayes' theorem and its applications in animal behaviour", Oikos 112: 243-251. Review.
- Davidson & El Hady (2020), "Normative theory of patch foraging decisions", arXiv:2004.10671.
- Kilpatrick, Davidson & El Hady (2021), "Uncertainty drives deviations in normative foraging decision strategies", bioRxiv.
- Vertechi et al. (2024), "Foraging Under Uncertainty Follows the Marginal Value Theorem with Bayesian Updating of Environment Representations", PMC10996644.

## 3. Probability weighting in human decision-making

### Structure

Humans evaluating gambles do not act on objective probabilities $p$ directly. Instead they apply a transformation $w(p)$ to probabilities and evaluate gambles as

$$
V = \sum_i w(p_i) \cdot v(x_i)
$$

where $v$ is a value function on outcomes. The empirically robust feature of $w$ is its **inverse-S shape**: $w(p) > p$ for small $p$, $w(p) < p$ for large $p$, with a crossover around $p \approx 0.3$–$0.4$. So a $1\%$ chance feels weighted like $\sim 5\%$, a $99\%$ chance like $\sim 90\%$.

The canonical functional forms are:

- **Prelec (1998):** $w(p) = \exp(-(-\ln p)^\alpha)$ with $\alpha \in (0,1)$ controlling the curvature.
- **Tversky-Kahneman (1992):** $w(p) = p^\gamma / (p^\gamma + (1-p)^\gamma)^{1/\gamma}$.
- **Gonzalez-Wu (1999) "Linear in Log Odds":** $w(p) = \delta p^\gamma / (\delta p^\gamma + (1-p)^\gamma)$.

Empirically, the Prelec-2 and Linear-in-Log-Odds forms most often fit human data best (Cavagnaro et al. 2013, the "adaptive design optimization" paper).

### Connection to our setup

Probability weighting is not directly a density-region bet on a latent $\theta$. It is a transformation applied to *known* probabilities. So the structural analogy with our setup is indirect. The deeper connection is via **derivations** of the inverse-S shape from informational or sampling constraints, which mirror the BA-prior argument.

**Two relevant derivations.**

1. **Noisy estimation + Bayesian regression to the mean.** If the agent doesn't have access to $p$ directly but has experienced $n$ outcomes from which they estimate $\hat p$, and they apply Bayes' rule with some prior over plausible probabilities, the posterior mean of the true probability is pulled toward the centre of the prior. Extreme observed frequencies are tempered. With appropriate priors and noise structure, this produces an inverse-S between objective $p$ and posterior-mean estimated $\hat p$. Steiner & Stewart (2016) work this out in detail.

   **The link to our project:** this derivation says the inverse-S shape is what happens when an agent does Bayesian inference about a probability under a non-flat prior. The shape of the prior matters. An info-optimal prior on $[0,1]$ in this setting would produce a *specific* shape of probability weighting, with discrete-ish mass concentration near $\{0, 1\}$ — which would amplify regression-to-the-mean toward 0 or 1 rather than toward 0.5. That's a falsifiable behavioural prediction.

2. **Rate-distortion / capacity-constrained encoding.** If the brain represents probabilities with finite information capacity, the rate-distortion-optimal lossy encoding (given a smooth loss between true and represented probability) is an inverse-S-shaped distortion. Khaw, Li & Woodford (2021) work this out with explicit information-theoretic budgets.

   **The link to our project:** this is essentially a *sibling* of the BA-prior argument. Both ask: given a finite information budget about a continuous probability, what's the optimal coarse-graining? Both produce discrete/quasi-discrete coarsenings as a consequence. The mathematical objective is different (rate-distortion vs. mutual information with future observations) but the spirit is the same — finite information forces structure on the representation of continuous probabilities.

### Mathematical detail (Khaw-Li-Woodford sketch)

The agent has true probability $p$ to evaluate, and represents it internally as $\hat p$, drawn from an encoding distribution $r(\hat p \mid p)$. The encoding minimises expected distortion $\mathbb{E}[(p - \hat p)^2]$ subject to an information-capacity constraint $I(p; \hat p) \leq C$. The optimal encoding under a prior $\pi(p)$ on which probabilities are encountered is the Blahut-Arimoto rate-distortion solution. For $\pi$ that places more mass near the centre of $[0,1]$ (which is typical), the optimal encoding spends its bits resolving the centre and lumps together the tails — exactly the shape of the inverse-S.

The structural similarity to BA priors is striking: both are coarse-graining solutions to "given finite information about $[0,1]$, what's the best representation?" The differences are (i) BA priors maximise MI with future *observations*, KLW minimise distortion between *internal* representations; (ii) BA priors typically produce discrete supports, KLW produces stochastic encodings with smoother structure. But they are mathematical cousins.

### References

- Prelec (1998), "The Probability Weighting Function", Econometrica 66(3): 497-528.
- Tversky & Kahneman (1992), "Advances in prospect theory: Cumulative representation of uncertainty", Journal of Risk and Uncertainty 5: 297-323.
- Gonzalez & Wu (1999), "On the shape of the probability weighting function", Cognitive Psychology 38: 129-166.
- Cavagnaro, Pitt, Gonzalez & Myung (2013), "Discriminating Among Probability Weighting Functions Using Adaptive Design Optimization", Journal of Risk and Uncertainty 47: 255-289, PMC3895409.
- Steiner & Stewart (2016), "Perceiving prospects properly", American Economic Review 106(7): 1601-1631. Bayesian-regression derivation.
- Khaw, Li & Woodford (2021), "Cognitive imprecision and small-stakes risk aversion", Review of Economic Studies 88(4): 1979-2013. Rate-distortion derivation.
- Woodford (2020), "Modeling imprecision in perception, valuation, and choice", Annual Review of Economics 12: 579-601. Review of the rational-inattention / capacity-constraint program.

## 4. Categorical perception

### Structure

A continuous physical stimulus (e.g. acoustic voice onset time for stop consonants, F1 formant for vowels) is mapped by the perceptual system to a discrete category response. The classical finding is reduced within-category discrimination and enhanced across-category discrimination — as if the perceptual representation is being "snapped" to category prototypes. The Bayesian framing (Feldman, Griffiths & Morgan 2009) treats this as inference: the listener wants to recover a phonetic target $\theta$ given a noisy acoustic signal $X$, and uses a mixture-of-categories prior

$$
p(\theta) = \sum_c \pi_c \, \mathcal{N}(\theta; \mu_c, \sigma_c^2).
$$

The posterior $p(\theta \mid X)$ shrinks toward the category prototype $\mu_c$ for whichever $c$ is most likely. Discrimination experiments effectively measure the perceptual distance between posterior means for two stimuli; with shrinkage to prototypes, this distance is small within a category and large across the boundary.

### Connection to our setup

This is the weakest of the four analogies for our project, because the discreteness in this setting comes from a *mixture prior* — discrete latent category $c$, continuous target $\theta$ within each category — not from an info-max objective applied to a unimodal latent. The structural similarity is that the prior is "discrete-ish" and the posterior inherits that structure, leading to coarse-grained behaviour on continuous stimuli. But it's a different mechanism: known mixture structure rather than emergent discreteness from information optimisation.

There's a more direct connection in the information-theoretic derivations of categorical perception. Bonnasse-Gahot & Nadal derive properties of category perception from mutual information between categories and neural codes — "We exhibit a link between optimal Bayesian decoding and coding efficiency, the latter being measured by the mutual information between the discrete category set and the neural activity". This is closer in spirit to our project: an MI objective, applied to neural representations of stimuli, producing structured (category-aligned) representations. But the latent here is the discrete category, not a continuous $\theta$ to be coarsened.

### The status of "categorical perception" as a concept

Worth flagging that there's an active dispute. The strong version of categorical perception — that within-category information is fully discarded — has been pushed back against by McMurray (2022) and others, who argue that "modern theories of speech perception agree that auditory input is represented continuously and activation for categories is gradient". The Bayesian mixture-prior models reproduce categorical effects without requiring fully discrete representations, which is the current consensus position.

### References

- Liberman, Harris, Hoffman & Griffith (1957), "The discrimination of speech sounds within and across phoneme boundaries", J Exp Psychol 54: 358-368.
- Feldman, Griffiths & Morgan (2009), "The influence of categories on perception", Psychological Review 116: 752-782.
- Kronrod, Coppess & Feldman (2016), "A unified account of categorical effects in phonetic perception", Psychonomic Bulletin & Review.
- Kleinschmidt & Jaeger (2015), "Robust speech perception: Recognize the familiar, generalize to the similar, and adapt to the novel", Psychological Review 122: 148-203.
- McMurray (2022), "The myth of categorical perception", PMC9803395.
- Bonnasse-Gahot & Nadal (2008/2011), "Perception of categories: from coding efficiency to reaction times", arXiv:1102.4749. Information-theoretic angle.

## 5. Summary table

| Domain | Latent | Action set | Why posterior shape (not just mean) matters | Closeness to our project |
|---|---|---|---|---|
| **Clinical trials** | continuous effect size $\theta$ | $\{$advance, halt$\}$ | decision is on tail probability $P(\theta > \tau)$ | **direct** — same density-region bet structure |
| **Foraging** | continuous patch quality $\theta$ | $\{$stay, leave$\}$ | option value depends on posterior variance; threshold on functional | **direct** — finite-data Bayesian decisions with discrete actions |
| **Probability weighting** | (no latent — known probabilities) | continuous gamble valuation | structural cousin: both are coarsenings under finite information about $[0,1]$ | **conceptual** — sibling argument, not same problem |
| **Categorical perception** | continuous phonetic target | discrete category response | mixture prior produces shrinkage; loss is on category identity | **superficial** — different mechanism, but shared coarse-graining flavour |

For motivation purposes the cleanest framings are **clinical trials** (when the audience is statistics/methodology) and **foraging** (when the audience is cognitive science / behavioural ecology). The probability weighting connection is the most provocative but requires a careful framing to avoid overclaiming. The categorical perception connection is the weakest and probably best left aside unless directly asked.

## 6. Implications for the experiment design

Two concrete things to take away for the betting-experiment .md:

1. **Density-region bets are not exotic.** The clinical-trial connection makes "bet on $\theta \in A$" the natural mathematical abstraction of how Bayesian decision-making actually happens in many applied fields. We don't need to apologise for the artificiality of this bet design — it *is* the structure of real decisions.

2. **The foraging setup is sequential, not one-shot.** Our experiment is one-shot ($n$ observations then bet). The natural extension is sequential — bet at each step, update, repeat. The foraging literature has well-developed machinery for this (drift-diffusion implementations of sequential Bayesian decision-making), and if our one-shot experiment shows a $p^*$ advantage, the sequential version would be the obvious follow-up with a direct biological interpretation.
