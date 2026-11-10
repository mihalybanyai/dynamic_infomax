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
  which geometries arise naturally there.

*What would settle it:* for science models, a suite of (model, `θ`) pairs with
independently measured parameters and few enough of them to compute `p*`
(`resources/AtomicPriors.jl`), scored as in spec 002. For everyday situations, a
reduction of one task to a few tens of parameters, with its geometry compared to spec
002's families. A suite can go against `p*` [guess]: rates spread over many decades look
roughly uniform in log-rate inside any observation window, which is the uniform prior's
world.
