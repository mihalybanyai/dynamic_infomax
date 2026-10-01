# Skill: red-team-implementation

> Use after an implementation in `src/` has been written from a reviewed spec, passes
> the (red-teamed) test suite, and has its documentation in place. The goal is what
> "passes the tests" misses: uncaught bugs, latent correctness risks, load-bearing
> inefficiencies, and inaccurate or missing documentation. Shared rules are in
> `skills/red-team.md`; this file holds only what is specific to implementations.

## Why this stage

Tests exercise only the cases their author imagined. An implementation can be wrong on
cases the tests skip; right in the tested regime but resting on assumptions the next
spec will break; too slow for the scale the spec intends; or documented in a way that
misleads (wrong shape annotations, stale design rationale, comments that contradict the
code).

## Prompt template

Run the spawn-configuration gate (`skills/red-team.md` §1), then spawn with:

```
You are a hostile reviewer of an implementation: find the gap between "passes the
tests" and "a good, well-documented implementation of the reviewed spec". Spec:
<SPEC_PATH>. Code: <CODE_DIR>. Documentation: <DOC_PATH>. Before anything else, read
`skills/red-team.md` §3 (sub-agent rules) and the "Sub-agent brief" section of
`skills/red-team-implementation.md`, and follow both throughout. Approved red-teamers:
<APPROVED_ROSTER>. Effort tier: <EFFORT_TIER>. Roster verified: <ROSTER_VERIFIED_DATE>.
```

## Sub-agent brief

### Reading order and scope

Take as given: the spec has been red-teamed and is `reviewed` in all relevant sections,
so you are **not** auditing the math; the test suite has been red-teamed and passes, so
you are **not** auditing coverage against the spec.

Read the spec first, then the documentation (design decisions, data flow, call graph,
inline conventions), then the code. The order is deliberate: form your picture of what
the code *should* do from spec and docs, and check the code against it. A code-first
reader forms an opinion of what the code does, and the docs then have to fight it.

Out of scope: style and formatting (linters cover it); new tests (the test red-team owns
them); spec revisions (the spec red-team owns them); documentation that would be nice to
have but is not load-bearing.

### Checklist

In priority order:

1. **Bugs the tests didn't catch**: wrong output for inputs the tests don't exercise;
   off-by-one errors at boundaries; degenerate inputs; edge cases the spec implicitly
   requires. If an existing, passing test should have caught the bug, it is a test
   finding: tag it `[test-gap]`.
2. **Latent correctness risks**: correct for the exercised cases, but resting on
   assumptions that plausible extensions break (an axis order the next spec might
   transpose; a numerical regime such as small `N` or full-rank covariance that won't
   hold; undefined behaviour the current spec doesn't forbid).
3. **Load-bearing inefficiencies**: only those that would prevent running at the scale
   the spec calls for, or that scale badly in a parameter the spec varies. Not stylistic
   optimisations. If unsure, do not flag.
4. **Documentation inaccuracies**: design-decision entries that don't match the code or
   elide a real alternative; shape or data-flow descriptions that don't match; stale or
   missing call-graph edges; inline comments that contradict the code (always flag: a
   wrong comment is worse than none).
5. **Documentation omissions**: anything a labmate reading the code cold would
   predictably get stuck on or misread: unexplained constants, unstated invariants,
   non-obvious conventions.

Specificity example. Useless: "this function might be slow on large inputs." Useful:
"lines 142–149 build the m×n×n covariance tensor with a triple Python loop over the batch
dimension; at the batch size m=1024 that §3.2 specifies, that is about 10⁶ Python-level
operations per training step. Vectorise via the batched outer product over axis 0."

### Findings

**Location** is a file and line range, or a doc section. The concern takes two to four
sentences. Add a **Touches** field: code, docs, or both. Routing tags allowed:
`[test-gap]` and `[spec-implication]`. Ordering is category-major: the five categories
in the order above, and descending severity within each. Severity calibration is left
to the invoking prompt.

### Report

Write to `<DOC_PATH_DIR>/redteam-impl.md`. Summary focus: does the code plausibly do
what the spec calls for, where is it most fragile, does the documentation track the
code. The artefact in "What the … gets right" is the implementation.

## After the report

Processing follows the four stages of `workflows/invoke-red-team-on-impl.md` (decide,
update spec if needed, regenerate code and docs, re-run tests one by one), because
findings here can touch up to three artefacts and regenerated code must be verified
against the suite before the pass closes. Modified code files flip to `pending-tests` in
`CODEGEN_LOG.md` and back to `done` once all tests pass.

**If a test fails on the re-run**, report it and decide with the human; the workflow
does not pre-commit to a cause. The edit may be wrong (revisit its `> C:`), the failure
may be a new finding the red-team missed (add it as the next F-number and triage it), or
the test may be wrong (route as `[test-gap]`).

**Additional prerequisites** (beyond `skills/red-team.md` §6): the spec is `reviewed`
in every section the implementation covers, and the test suite is complete and passing.

Extracted from the first implementation red-team (spec 000); the original reasoning is
in `transcripts/`.
