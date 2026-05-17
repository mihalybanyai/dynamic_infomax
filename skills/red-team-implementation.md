# Skill: red-team-implementation

> Use this skill after an implementation in `src/` passes its test suite.
> The goal is to find ways the implementation could be wrong despite the
> tests passing.

## Why this exists

Passing tests is necessary but not sufficient. An implementation can pass
all tests while:

- Being subtly wrong in a region the tests do not probe.
- Having numerical issues that only manifest at scale or in deployment.
- Disagreeing with the spec in ways the tests do not check.
- Containing dead code, unreachable branches, or unused parameters that
  hide bugs.

A fresh sub-agent with access to spec, tests, and implementation — but
without the context of how the implementation was developed — can audit
this.

## How to invoke

Use the `Task` tool to spawn a sub-agent with the following prompt template.
Substitute `<SPEC_PATH>`, `<TEST_PATH>`, and `<SRC_PATHS>` with actual paths.

```
You are auditing an implementation for correctness. The spec is at
<SPEC_PATH>, the tests are at <TEST_PATH>, and the implementation is at
<SRC_PATHS>.

The tests currently pass. Your job is to find ways the implementation
could be wrong anyway. You should consider:

## Audit dimensions

1. **Spec/implementation mismatch**: line by line, does the code do what
   the spec says? Look especially for:
   - The objective function the code optimizes is not the objective in
     the spec.
   - The algorithm is the same shape but a step is in the wrong order, or
     a step is missing.
   - The code uses a related-but-different formula than the spec (e.g.,
     biased vs. unbiased estimator, mean vs. median, log-base-e vs.
     log-base-2 where it matters).

2. **Numerical issues**:
   - Computing `log(exp(x))` instead of using `x` directly (overflow).
   - Computing `softmax` without subtracting the max (overflow).
   - Computing `log(1 - p)` instead of `log1p(-p)` when p is small.
   - Dividing by something that can be zero without a guard.
   - Accumulating in float32 where float64 would matter.
   - Using `**` for matrix power when matrix multiplication is intended,
     or vice versa.

3. **Shape and broadcasting errors that pass tests**: tests with
   square-ish inputs (batch_size == feature_dim, etc.) often miss
   broadcasting bugs that surface only on asymmetric inputs.

4. **Hidden state**: does the implementation rely on global state, module
   state, RNG state that is not reset between calls? Would two
   back-to-back calls with the same input give the same output?
   (See also `skills/manage-randomness.md` for the project's
   no-global-RNG convention; flag any violation.)

5. **Untested branches**: any `if`/`else`, exception handler, or fallback
   that is not exercised by the tests. Flag each; some may be defensive
   and fine, others may hide bugs.

6. **Dead parameters**: function parameters that are accepted but never
   used. Almost always a refactor bug.

7. **Default values that affect correctness**: defaults that change
   behavior silently. A `bias=True` default in a layer the spec says
   should have no bias is a real bug that no test about the gradient flow
   would catch.

8. **Comments that lie**: a comment says one thing, the code does
   another. The comment is documentation; the code is what runs. Flag
   the mismatch — usually one of them is wrong.

## Approach

- Read the spec first. Then read the implementation without consulting
  the tests, and try to predict what the tests should check. If your
  predictions and the tests diverge significantly, that is itself a
  finding.
- Then read the tests and ask: for each part of the implementation, what
  test pins down its correctness? If you find parts of the implementation
  with no clear corresponding test, flag those as audit risks even if no
  specific bug is visible.

## Format

For each finding:
- **Location**: file and line numbers.
- **Concern**: what's wrong or potentially wrong.
- **Evidence**: how you would demonstrate the bug (a specific input, a
  specific call sequence, a specific edge case). If you cannot construct
  a demonstration, label the finding "speculative" and rank it lower.
- **Severity**: high (correctness bug, would change outputs in normal
  use), medium (correctness bug only in edge cases or at scale), low
  (style/maintainability/clarity).
- **What would resolve it**: a specific fix, a specific additional test,
  or both.

Distinguish carefully between "this is a bug" and "this is a risk".
A bug is something you can demonstrate. A risk is something you cannot
demonstrate but think is worth flagging because the code structure
makes it likely. Both are valuable; conflating them is not.

**Ordering**: list findings in order of descending severity (high first,
then medium, then low). Within a severity level, order bugs (demonstrable)
before risks (speculative), and within each of those by file path then
line number. Number findings F1, F2, F3, ... *after* ordering.

Write to `<SRC_PATH_OR_MODULE>-redteam.md`. If the implementation spans
multiple files, write one consolidated report at
`src/<module>-redteam.md`. Do not include counts of findings by severity
in the summary.

# Red-team review of <SRC_NAME>

Reviewer: red-team sub-agent
Date: <YYYY-MM-DD>
Implementation version: <git commit hash if available>
Spec version reviewed against: <git commit hash if available>
Tests version reviewed against: <git commit hash if available>

## Summary

<one paragraph: qualitative impression of the implementation — does it
faithfully implement the spec, where are the most likely places for bugs,
how much confidence in correctness do the passing tests warrant. No counts.>

## Findings

### F1: <short title> [severity: high]

**Location**: <file:line>

**Concern**: <specific description>

**Evidence**: <how to demonstrate, or "speculative">

**What would resolve it**: <specific fix>

---

### F2: ...

## What the implementation gets right

<one paragraph, briefly.>
```

## Annotation conventions in the redteam file

Same as `skills/red-team-spec.md`: `> M:` for the human's response,
`> C:` for the confirmation of action taken, two newlines between each.

For implementation findings specifically, the `> C:` confirmation should
note whether a test was added (proving the bug existed) before the fix
was applied. The standard pattern is: write a failing test first, then
fix the implementation, confirm the test passes. The `> C:` records both
commits.

Example:

```markdown
### F1: log-sum-exp without max subtraction [severity: high]

**Location**: src/infomax/ba.py:42

**Concern**: The line computes `np.log(np.sum(np.exp(x)))` directly,
which overflows for large x. The standard log-sum-exp trick is missing.

**Evidence**: Input with any element > ~700 produces inf.

**What would resolve it**: Use `scipy.special.logsumexp` or implement
the max-subtraction trick by hand.

> M: Apply, use scipy.special.logsumexp. Add a test that exercises
> the overflow regime first.

> C: Failing test added in commit c12ab40 (test_ba_handles_large_logits
> with x including 1000.0; fails on master with overflow). Fix applied
> in commit d34cd71 using scipy.special.logsumexp. Test now passes.
```

## After the report exists

For each finding that is a bug: write a test that fails for the current
implementation (proving the bug), fix the bug, confirm the test passes.
Commit both together (or as a paired sequence). Record both commit hashes
in the `> C:` annotation.

For each finding that is a risk: either write a test that would catch
that class of bug (preferred), or document explicitly in the `> M:`
response why the risk is accepted, with a `> C:` confirming no code change.

## Caveat

A red-team sub-agent can produce false-positive findings — claims of bugs
that are not actually bugs. Treat each finding as a hypothesis to verify.
If the sub-agent is wrong about a concern, the `> M:` response explains
why and the `> C:` confirms no change. This is itself useful audit trail.
