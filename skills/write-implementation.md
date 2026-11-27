# Skill: write-implementation

> Use this skill whenever writing or revising code in `src/` that implements a spec. The
> goal is code whose every result is either right for the regime it was built for or
> says that it is not.

> **Status**: v1, written after spec 002's implementation red team (2026-11-27). Two
> rules so far; add one only when a failure recurs. The procedure (what to generate in
> which order, the codegen log, design-decision entries) is in
> `workflows/implement-spec.md`; randomness is in `skills/manage-randomness.md`.

## Why this exists

A test suite pins the cases its author imagined, and a red-teamed one still cannot
cover every regime the code will meet: a `D` no test reaches, a box no test builds on,
a cell harder than any the solver has seen. Outside them, the failure that costs most is
the silent one: a number that looks like every other number. It gets plotted, compared
and believed. Spec 002's implementation passed both suites and still had two: its
capacity solver stopped at a hidden round cap with its tolerance unmet (red team F2),
and on the matched box its sampled Jeffreys collapsed to 59 distinct states at `D = 6`,
`log Z` 6 nats off (F3). Neither warned.

## Conventions

### Rule 1: Fail loudly outside the expected regime

Know the regime each component is validated in: a dimension range, a convergence
criterion, a minimum effective sample size, finite inputs. At its boundary:

- **raise** when the result would be meaningless: too few particles inside `Θ`, a
  non-finite normaliser, an input outside the validated range that the spec does not
  call for;
- **warn and record** when the result is usable but degraded: a solve stopped by its
  round cap returns `converged=False` and its remaining gap, and the caller stores both
  with the result, so a report can show them;
- **never** return a fallback (the last iterate, a clipped value, an empty set) as if
  it were the answer. At `D = 7`, L-BFGS returned its last iterate, not its best, and a
  per-point marginal came out `-inf` (docs 002, Testing notes, 2026-11-26).

Keep it lean. Guard what would otherwise pass silently and is cheap to check: a count,
a flag, `np.isfinite`. Do not guard what the next line or a test already catches, and
do not wrap every function. Where a guard's threshold is itself a modelling choice
(what counts as "too few"), record it as a design decision in the docs; where it
changes what is computed, raise it with the human first.

### Rule 2: Peak memory is part of the cost

IR-2 (`AGENTS.md`) counts memory with time. In code, an array over (data × nodes),
(states × candidates) or (draws × atoms) is formed in batches whose size does not grow
with the number of draws. The batch size is a named constant whose docstring gives the
bytes per entry. Before relying on a function at the largest cell the spec runs,
measure its peak (`tracemalloc`, or `/usr/bin/time -l` for the process). Motivating
failure: §3.3's split held about 7 GB at experiment 002's tier 0; batched, 304 MB and
bit-identical (docs 002, DD-K4).

## When the conventions hurt

A guard that fires on most runs is noise, and noise gets ignored: if a warning fires
routinely, the regime it guards is the normal one, so move the boundary (a design
decision) instead of keeping the warning. Batching costs nothing when the batch holds
everything; do not batch an array that cannot grow.

## Output

Code whose results carry their diagnostics, and a design-decision entry for each
regime boundary and threshold chosen.
