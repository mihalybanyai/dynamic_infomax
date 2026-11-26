# Parked ideas

Ideas raised in passing and not followed up. Each entry says where it came from, what
the idea is, and what would settle it. Nothing here is reviewed or load-bearing for a
spec. Promote an entry to its own note or spec when it is picked up; delete it when it
is dropped.

Empirical ideas go to [`empirics/`](../empirics/README.md) instead.

### Advantage per unit of construction cost (2026-10-24)

*From:* the chat thread behind `notes/budget-value-of-information.md` (MB's idea).
*Idea:* report a prior's advantage per unit of the cost of constructing and using it, so
that a prior that wins only by being much more laborious (mixing over all budgets, an
exact discrete `p*`) is compared fairly with cheap ones. *What would settle it:* a
coherent definition of construction cost (computation, storage, or description length of
the procedure), which is itself open.

### Other off-stimulus information, treated like the budget (2026-10-25)

*From:* MB, after the budget thread (`notes/budget-value-of-information.md`). *Idea:*
apply the same analysis to other information that is part of a task but not of the
stimulus. Screened against that note's grimoire (§5), the candidates are:
- **the task** (what will be asked, the decision threshold, the stakes): the strongest,
  because it supplies the parameter of interest and changes relative relevance;
- **how the data were generated** (random, pedagogical, adversarial, stopping rule);
- **the world's volatility**, where knowledge expires;
- **self-knowledge** (own memory decay), which probably shares the budget's traps [guess].

*What would settle it:* for the task, a minimal model with a 1-D variable, `K` atoms and
a threshold decision at the end, with the threshold known in advance or not. Predicted
[guess]: a definite advantage when capacity binds, none without capacity limits.

### Benchmark natures (2026-11-09)

*From:* MB, in the chat on finding F1 of spec 002's fourth conceptual red-team
(`specs/002-foreign-q-prediction-redteam-conc04.md`). No distribution of
[natures](../GLOSSARY.md#nature) is privileged, and any weighting of natures is itself a
prior, which favours whichever prior of the cast lies closest to it. *Idea:* score the
priors on natures chosen outside the project, as decision-making benchmarks (Atari, ARC)
are. A benchmark makes the natures external, diverse and shared, not representative:
"which distribution of natures?" becomes "which suite?", but the suite cannot encode our
lean. With a summary that needs no weights, such as each prior's largest gap over the
suite to the best prior at each nature, it supports claims like "across these systems,
`p*` is never more than X behind". Atari and ARC themselves do not fit spec 002: their
data-generating processes are programs with no shared smooth parameter space, and a
learned model of them would be misspecified, with millions of parameters. Candidate
sources:
- **Models from science** with explicit generative structure and real parameters, where
  [sloppiness](../GLOSSARY.md#sloppy-model) was found: systems-biology ODE models
  [recalled: Gutenkunst et al. 2007 collected 17, all sloppy], decay chains,
  pharmacokinetic compartments. Fitted values along sloppy directions reflect the
  fitting procedure, not nature, so parameters measured independently of the fit are
  preferable [guess]. These models may look little like everyday learning and decision
  situations (MB).
- **Reduced models of everyday situations.** MB's conjecture [guess]: a few tens of
  parameters describe such situations well, so the millions a learned model has can be
  cut down massively while leaving ample room for prior choice. This needs a look at
  which geometries arise naturally there. One such reduction, judging whether a tower
  of blocks falls, has a note of its own: [block-towers.md](block-towers.md).

*What would settle it:* for science models, a suite of (model, `θ`) pairs with
independently measured parameters and few enough of them to compute `p*`
(`resources/AtomicPriors.jl`), scored as in spec 002. For everyday situations, a
reduction of one task to a few tens of parameters, with its geometry compared to spec
002's families. A suite can go against `p*` [guess]: rates spread over many decades look
roughly uniform in log-rate inside any observation window, which is the uniform prior's
world.

### Budget-conditioned prior network (2026-11-13)

*From:* the chat behind [`literature/empowerment.md`](../literature/empowerment.md). The
wish is MB's: Blahut–Arimoto gives `p*` for normative comparisons, not on the fly. The
construction is Claude's. *Idea:* amortise `p*` over budgets. One network takes the budget
`N` and returns [atoms](../GLOSSARY.md#atom) and weights. With a Gaussian likelihood the
posterior over atoms is exact, so the mutual information can be estimated and climbed
directly, as Abbott & Machta do for one budget at a time [read: A&M App. A.2]. Where the
likelihood has no tractable posterior, a recognition network `q(θ|x, N)` supplies the
Barber–Agakov lower bound, as in Mohamed & Rezende 2015 [read: §4.1–§4.2]: the likelihood
is fixed, the prior and the recognition network are learned, and training uses only the
model's own samples. Other context that changes the likelihood could be added to the
input later.

What it does not address: a solver for large `D` exists already
(`resources/AtomicPriors.jl`, spec 002 OQ-1). Known hazards:
- **Slack in the bound** pulls the prior toward posteriors the recognition network can
  represent. The bound of Nalisnick & Smyth 2017 favoured a prior of two atoms at any
  noise level in Abbott & Machta's models [read: A&M App. A.3]. The Barber–Agakov bound is
  a different one, so that failure need not carry over [guess].
- **Collapse.** A continuous prior family will try to collapse onto atoms [guess]. Mohamed
  & Rezende constrain the source's entropy for a related instability [read: §4.2].

*What would settle it:* the 1-D bounded Gaussian channel of spec 000. Train one network
across budgets and compare with
[Blahut–Arimoto](../GLOSSARY.md#blahut-arimoto-algorithm) at each budget on three counts:
the gap in mutual information, the worst-case
[bias pressure](../GLOSSARY.md#bias-pressure), and whether atoms split at the right
budgets. A failure there ends it cheaply. It would join the cheap updates listed in
`notes/budget-value-of-information.md` §9.

### Particle or variational `p*` for large `D` (2026-11-26)

*From:* the chat on `p_proj`'s cost in spec 002. The variational direction is MB's
interest. The particle idea is a TODO in the overleaf draft
(`resources/overleaf_doc/main.tex:111`), which cites Dauwels 2005; only the bib entry is in
the repo. *Idea:* compute `p*` at one budget with [atoms](../GLOSSARY.md#atom) that move,
instead of [Blahut–Arimoto](../GLOSSARY.md#blahut-arimoto-algorithm) on a fixed candidate
net, whose size grows with the Fisher volume and so fast with `D`. Two steps:
- **Particle Blahut–Arimoto** [recalled: Dauwels 2005]. Blahut–Arimoto reweights a set of
  particles, and each particle moves uphill on its divergence from the
  [Bayes mixture](../GLOSSARY.md#bayes-mixture). The cost grows with the number of atoms,
  not with the net. This would give spec 002 an atomic path (OQ-1) in Python, without
  Julia.
- **Variational, on top.** When the exact posterior over hundreds of atoms in
  high-dimensional data gets expensive, a recognition network replaces it, as in the
  Barber–Agakov bound of Mohamed & Rezende 2015 [read: §4.1–§4.2]. The particles stay as
  the source, since a continuous family collapses onto atoms (see the hazards of the entry
  above).

Either comes with a certificate. Any output density `q` bounds capacity from above,
`C ≤ max_θ D_KL(p(x|θ)‖q)` [recalled]. So the prior's information from below and this
bound from above bracket `C`, and their gap is the worst-case
[bias pressure](../GLOSSARY.md#bias-pressure) `B` that spec 002's tests already check.

The case for it: AtomicPriors' solver, which the
[budget-network entry](#budget-conditioned-prior-network-2026-11-13) counts as the existing
large-`D` solver, scales badly. `nlopt!` on its kernel bound took about 3 hours for 210
atoms at spec 002's T12(c) cell (`D = 2`, `N = 4`, sharing the machine with other runs);
the candidate set builds `p*` at `N = 1` in about 7 seconds (spec 002 docs, DD-J3). The
budget-network entry amortises over budgets; this one is about a single budget at large
`D`, and the two compose.

*What would settle it:* particle Blahut–Arimoto at exp-decay, `D = 2, 3` and
`N = 1, 2, 4`, against the candidate set and the AtomicPriors fixtures of spec 002's
T12(b) and (c), on the gap in `I`, on `B`, and on wall time as the atoms grow. Then
`D = 5, 7, 11`, where the candidate sets fail.

### Deployable priors as `K`-sample agents (2026-11-26)

*From:* the chat on spec 002's OQ-14, where sampled priors failed at thin states. MB
observed that people handle high-dimensional inference quickly, however approximately, so
the difficulty may be one of principle and may differ between families. The link to the
mass bound is Claude's. *Idea:* estimating a prior's marginal `m_π(x)` by sampling the
prior needs about `exp(KL(posterior ‖ prior))` draws [recalled: Chatterjee & Diaconis
2018]. At data from a state `θ` that KL is of the order of the prior's per-state
[redundancy](../GLOSSARY.md#redundancy-and-regret) `R^θ(π)` [guess], which spec 002's mass
bound (3.2.1) ties to `−log π(A(θ))`. So a prior is expensive to use exactly where it is
wrong, by the same number of nats. An agent that carries its prior as `K` samples, as the
sampling hypothesis has it [recalled: Fiser, Berkes, Orbán & Lengyel 2010; Vul et al. 2014],
has a second budget, `log K`: where its prior's redundancy exceeds it, the agent is
over-surprised. Three consequences:
- **Families differ in kind.** Discrete [minimax](../GLOSSARY.md#minimax) priors (`p*`,
  `p_lat`) cap their worst-case redundancy at the [capacity](../GLOSSARY.md#channel-capacity)
  `C_N`, the [equalizer condition](../GLOSSARY.md#equalizer-condition), and their marginals
  are exact finite sums over [atoms](../GLOSSARY.md#atom). [Jeffreys'](../GLOSSARY.md#jeffreys-prior)
  redundancy grows with `D` where the [co-volume](../GLOSSARY.md#co-volume) pulls its mass
  away: `(D−1) log(W/θ_1)` in the hypercone, spec 002 eq. (3.2.2). A sampled Jeffreys then
  needs `K` exponential in `D` there. A&M's bias and this cost are one quantity.
- **A computational twin of budget-consciousness.** A `K`-sample agent should prefer a prior
  whose worst-case redundancy stays below `log K`, which is the equalizer property again.
- **Which Jeffreys is [deployable](../GLOSSARY.md#deployable-prior)?** The continuous one, or
  its `K`-sample version? Spec 002 scores the continuous priors (§2.2); a `K`-sample variant
  of each could join the cast, as the mis-budgeted `p*` did. Amortised inference, a learned
  map from data to posterior, is trained on prior draws and would inherit the same limit
  [guess].

*Evidence so far:* at `D = 3`, `p_LN`'s cloud of 20000 draws, whose threshold would be
`log 20000 ≈ 9.9` nats, was within 0.03 nats of the grid at states where the per-state
divergence was 1.3–6.4 nats, and off by 4–54 nats where it was 16.6–18.8 (spec 002 docs,
*Testing notes*). There are no states between 6.4 and 16.6, so this is consistent with the
threshold, not a test of it. Jeffreys' cloud, drawn from a deliberately broad proposal,
failed far less at the same states: what matters is the sampling distribution's mass at the
posterior, not the prior's. *What would settle it:* at `D = 3`, clouds of 2·10³, 2·10⁴ and
2·10⁵ draws, at states whose divergence spans 6–16 nats; the failure threshold should move
with `log K`. Then `p*`'s atom count across spec 002's `D`-sweep: exponential growth in `D`
would sink the "cheap to use" side [recalled: A&M's figures suggest it stays modest].

*A second budget, the same argument (MB, 2026-11-26).* Spec 002's whole argument could
probably be rerun with `K` in place of `N` [guess]. Both budgets coarse-grain the states:
`N` by what the data can tell apart, about `σ/√N`; `K` by what probability the agent can
represent, about `1/K`. Each then starves the regions a volume-allocated measure leaves
thin. They differ in two ways. Extra computation can buy back part of the `K` error but none
of the `N` error. And `K` is far harder to know or control in an experiment than `N`. Not
spec 002's object of study; there the two effects are to be kept apart.
