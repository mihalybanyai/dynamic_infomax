# Glossary

Terms used across the repo that a computational neuroscientist, cognitive scientist or
theoretical ML researcher may not know. Each document defines its own core objects (for
spec 002: `p*`, `p_proj`, `q`, the score `R_N^q`, the model families). This file holds
everything else, and documents link here at the first use of a term in each section.

*Every entry was drafted by Claude on 2026-10-01 and none has been reviewed by MB yet.*
Standard textbook definitions carry no tag; claims beyond the definition carry
provenance tags (`AGENTS.md`, *Epistemic tags*).

### Amplitude-constrained Gaussian channel

A channel whose output is the input plus Gaussian noise, with the input confined to a
bounded interval. Its [capacity-achieving input distribution](#channel-capacity) is discrete; below an
interval length of about `3.3` noise standard deviations it is just the two endpoints
(Smith 1971) [recalled; the repo's Blahut–Arimoto reproduces the threshold,
`notes/infomax_two_hats_and_directions.md` §7.4].

### Atom

A point carrying finite probability mass. A discrete prior is a weighted set of atoms.

### Bayes mixture

The distribution of data implied by a prior: `m_π(x) = ∫ p(x|θ) π(dθ)`, also called the
prior predictive or marginal likelihood. It is the single predictive distribution a
Bayesian with prior `π` uses. More: `tutorials/math/redundancy-capacity.md`.

### Bias pressure

Abbott & Machta's score of how strongly a prior disfavours the predictions of a parameter
value `θ`: the divergence of `θ`'s data distribution from the prior's [Bayes mixture](#bayes-mixture), minus
the prior's mutual information [read: A&M Eq. 5]. It is zero on the support of the
[capacity-achieving prior](#channel-capacity) and non-positive elsewhere; positive values mark regions a prior
under-weights.

### Blahut-Arimoto algorithm

An iterative algorithm that computes a channel's [capacity](#channel-capacity) and its capacity-achieving
input distribution by alternating updates (Blahut 1972; Arimoto 1972). It needs a
discrete input, so continuous parameters are gridded.

### Channel capacity

The maximum, over input distributions, of the mutual information between a channel's
input and output. Reading a statistical model as a channel `θ → x`, the capacity is the
most information an experiment can carry about `θ`, and the maximising input distribution
is the *capacity-achieving prior* (`p*` in this repo).

### Code length

A distribution `q` defines a code assigning `−log q(x)` nats to outcome `x`, so log-loss
*is* code length. The expected excess code length of `q` over the true distribution `p`
is `D_KL(p‖q)`.

### Co-volume

In a model with [relevant and irrelevant directions](#relevant-and-irrelevant-directions), the volume contributed by the
irrelevant ones: their combined Fisher extent at a given point of the relevant directions
[read: A&M §2]. It varies wildly across parameter space and is invisible to the data, yet
a volume-based prior such as [Jeffreys](#jeffreys-prior) still weights it [read: A&M §1]. Spec 002 §1.2
gives the global version `V_⊥`.

### Deployable prior

A prior an agent can actually adopt before seeing data, using only the model and the
data budget, without knowing [nature's](#nature) distribution. In spec 002, the "deployable
non-infomax" priors are the standard defaults ([Jeffreys](#jeffreys-prior), uniform-`θ`, log-normal), with
`p_proj` added to the headline lineup. The matched prior `q̄` is not deployable: it
requires knowing nature.

### Effective dimensionality

The number of parameter directions the data can actually resolve, often far below the
nominal parameter count in [sloppy models](#sloppy-model). Abbott & Machta define it from how the
[capacity](#channel-capacity) grows as noise shrinks, `I⋆ ∼ d_eff log(1/σ)` [read: A&M Eq. 8].

### Empirical and hierarchical Bayes

Choosing the prior from data (empirical Bayes) or from a higher-level distribution over
priors (hierarchical Bayes), rather than fixing it in advance.

### Equalizer condition

The optimality condition of the [capacity-achieving prior](#channel-capacity): every parameter value in its
support has the same divergence from the prior's [Bayes mixture](#bayes-mixture), equal to the capacity,
and no parameter value has more. Equivalently, its [bias pressure](#bias-pressure) is zero on the support
and non-positive elsewhere [read: A&M Eq. 5]. More:
[`tutorials/math/redundancy-capacity.md`](tutorials/math/redundancy-capacity.md#the-equalizer-property).

### Fisher information metric

The Riemannian metric on parameter space given by the Fisher information matrix.
Distance under it measures how distinguishable nearby parameter values are from data, in
units of noise standard deviations; it is the central object of information geometry.

### Fisher length

The length of a path in parameter space measured with the [Fisher metric](#fisher-information-metric). Along a
direction it counts roughly how many distinguishable predictions lie end to end [read:
A&M §1]. The [sloppy-models literature](#sloppy-model) calls the Fisher length of the model manifold
along a principal direction its *width*; widths scale like the square roots of the
Fisher eigenvalues [read: A&M App. A.7].

### Hyperribbon

A model manifold whose [widths](#fisher-length) fall off roughly geometrically over many orders of
magnitude: long in a few directions, extremely thin in many [read: Quinn §2]. It is the
characteristic geometry of [sloppy models](#sloppy-model). "Ribbon geometry" means the same.

### Identifiable model

A model in which different parameter values give different data distributions, so `θ`
could in principle be recovered from enough data.

### Information radius

For a family of distributions `{p_θ}`, the distribution `m` minimising the worst-case
divergence `max_θ D_KL(p_θ‖m)` is the *KL-centre*; the minimum value is the *radius*. The
radius equals the [channel capacity](#channel-capacity), and the centre is the [Bayes mixture](#bayes-mixture) of the
capacity-achieving prior (see the [redundancy-capacity theorem](#redundancy-capacity-theorem)).

### Jeffreys prior

The prior proportional to `√det` of the [Fisher information](#fisher-information-metric): the parameter-space volume
element of information geometry, derived from invariance to reparametrisation [read: A&M
§1]. It ignores the data budget, because repeating the experiment rescales the Fisher
information but leaves Jeffreys unchanged [read: A&M §2.1].

### Least-favourable prior

In a statistical game against [nature](#nature), the prior under which the best response performs
worst. For log-loss it is the [capacity-achieving prior](#channel-capacity). It is a worst-case hedge, a
design object, not a belief about the world.

### Minimax

Choosing the option with the smallest worst-case loss. Minimax [expected redundancy](#redundancy-and-regret) is
attained by the [capacity-achieving prior](#channel-capacity); minimax pointwise regret by [NML](#normalized-maximum-likelihood-nml).

### Minimum description length (MDL)

Model selection and prediction by compression: prefer the description of the data that is
shortest overall (Rissanen). [NML](#normalized-maximum-likelihood-nml) is MDL's [minimax](#minimax) code. The "MDL prior" in spec 002 is
`p_proj`. More: [`tutorials/math/nml-mdl.md`](tutorials/math/nml-mdl.md).

### Nature

Decision-theory term for the unknown process that generates the true parameter and the
data. "Nature's distribution" is the distribution of the true `θ`.

### Noise halo

The region of data space just outside the model manifold whose points have their maximum
likelihood estimate at a given boundary point. At a *convex vertex* (a corner where the
manifold bends away) the halo is large, and sharpening the corner enlarges it.
Constructions that push data back to their MLE, such as `p_proj`, therefore put extra
mass on edges and corners [read: A&M App. A.3; Quinn §5.1, Fig. 10].

### Normalized maximum likelihood (NML)

The distribution over data sets that gives each data set the likelihood of its
best-fitting parameter, normalised over all data sets (Shtarkov 1987). It is the [minimax](#minimax)
code for [pointwise regret](#redundancy-and-regret), and that regret is its log-normaliser, the parametric
complexity. No prior's [Bayes mixture](#bayes-mixture) equals it at finite sample size
([`tutorials/math/nml-mdl.md`](tutorials/math/nml-mdl.md) §4).

### Parametric complexity

The log-normaliser of the [NML](#normalized-maximum-likelihood-nml) distribution: the [minimax](#minimax) [pointwise regret](#redundancy-and-regret) of a model
class, a measure of how many distinguishable data patterns it can fit. Asymptotically
`(d/2) log(N/2π) + log ∫√det g` [read: Rissanen 1996, Thm. 1]. The *stochastic
complexity* of a data set is its NML [code length](#code-length).

### Posterior deviation

Abbott & Machta's bias measure for a single observation: the distance, in noise units,
between the maximum-likelihood prediction and the posterior-mean prediction [read: A&M
Eq. 9].

### Prequential

"Predictive sequential" (Dawid): scoring a forecaster by predicting each observation from
the ones before it, then revealing it. The cumulative log-loss of a Bayesian's sequential
predictions equals the [code length](#code-length) of its [Bayes mixture](#bayes-mixture) for the whole sequence.

### Probability integral transform (PIT)

For a continuous predictive distribution with CDF `F` and an outcome `x`, the value
`F(x)`. Under calibrated forecasts PIT values are uniform. A hump-shaped histogram means
over-dispersed (too wide) forecasts; a U-shape means under-dispersed ones.

### Proper scoring rule

A rule for scoring probabilistic forecasts under which reporting your true belief
optimises your expected score; *strictly* proper if the true belief is the unique optimum
(Gneiting & Raftery 2007). Log-loss is strictly proper: `𝔼_{x∼p}[−log q(x)]` is minimised
uniquely at `q = p`.

### Pushforward

The distribution of `f(X)` when `X` has distribution `P`.

### Redundancy and regret

Two ways to charge a code `q` for not knowing `θ`. *Expected redundancy* is its excess
[code length](#code-length) over the true `θ`'s code, averaged over data from `θ`: `D_KL(p_θ‖q)`.
*Pointwise regret* is its excess over the best-fitting `θ` in hindsight on a given data
set. More: [`tutorials/math/nml-mdl.md`](tutorials/math/nml-mdl.md#1-two-regrets-from-one-numerator).

### Redundancy-capacity theorem

The [minimax](#minimax) [expected redundancy](#redundancy-and-regret) over a model family equals the [channel capacity](#channel-capacity), and both
are attained by the capacity-achieving prior and its [Bayes mixture](#bayes-mixture): two faces of one
saddle point [read: A&M Eqs. 3–4, citing their refs 10–12]. More:
[`tutorials/math/redundancy-capacity.md`](tutorials/math/redundancy-capacity.md#capacity-and-the-two-games).

### Reference prior

Bernardo's (1979) prior that maximises the information expected from an experiment,
defined in the limit of infinitely many repetitions, where it becomes [Jeffreys](#jeffreys-prior). The
finite-repetition versions are discrete; Abbott & Machta object to calling `p*` a
reference prior for this reason [read: A&M App. A.8].

### Relevant and irrelevant directions

Parameter directions whose [Fisher length](#fisher-length) exceeds 1 (the data can tell their ends apart)
or falls below it (they cannot) [read: A&M §1–§2]. *Stiff* and *sloppy* are the
[sloppy-models](#sloppy-model) names for the same split, based on the eigenvalues of the [Fisher metric](#fisher-information-metric).

### Self-sampling

Evaluating a prior on data drawn from its own [Bayes mixture](#bayes-mixture). Under self-sampling `p*`
looks unbiased by construction; spec 002 asks what survives without it.

### Sloppy model

A many-parameter model whose predictions depend on a few stiff parameter combinations and
barely on the many sloppy others. The eigenvalues of its [Fisher information matrix](#fisher-information-metric) spread
roughly evenly on a log scale over many decades, and its model manifold is a [hyperribbon](#hyperribbon)
[read: Quinn §1–§2]. Typical of mechanistic models across the sciences [read: Quinn
Fig. 3].

### Two-hat error

Scoring a *design* object (a prior built to hedge the worst case, like `p*`) as if it were
an *inference* belief (a prior meant to describe the world). Coined in
[`notes/infomax_two_hats_and_directions.md`](notes/infomax_two_hats_and_directions.md) to
diagnose spec 001.

### Uninformative prior

A prior meant to express ignorance about `θ`, chosen by a formal rule rather than by
belief: uniform, [Jeffreys](#jeffreys-prior), [reference priors](#reference-prior).

### Universal coding

Coding data from an unknown member of a model family with one code that does nearly as
well as the best member's own code. [Bayes mixtures](#bayes-mixture) and [NML](#normalized-maximum-likelihood-nml) are universal codes; their
excess [code length](#code-length) is the [redundancy](#redundancy-and-regret) or regret.
