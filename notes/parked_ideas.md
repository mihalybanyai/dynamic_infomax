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
