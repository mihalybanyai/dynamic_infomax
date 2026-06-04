# Skill: red-team-tests

> Use this skill after a test file in `tests/` has been written from a
> spec. The goal is to find ways the test suite could pass while the
> implementation is wrong.

## Why this exists

A test suite has two failure modes that are easy to miss from the author's
perspective:

1. **Under-specification**: properties in the spec that are not tested at
   all, so a wrong implementation could pass.
2. **Vacuous tests**: tests that pass trivially, e.g. tests that would pass
   for a function that returns zero, or for a function that returns its
   input unchanged.

A fresh sub-agent reading the spec and the tests separately is well-placed
to catch both.

## Before invoking — the spawn-configuration gate

The sub-agent inherits this session's model and effort tier. Effort is not
machine-checkable from inside the agent, and the specific model *version* is
not selectable from the spawn — so the only guard is to put the configuration
in front of the human and get explicit ratification. Before spawning, the main
agent MUST:

1. **Print the roster.** Reproduce the "Red-team reviewer roster" table from
   `AGENTS.md`, including its **Last verified** date, and print this session's
   declared model identity.

2. **Print the inheritance caveats and ask to proceed:**

   > Red-team spawn check:
   > - Model: this session is `<declared identity>`; the sub-agent inherits it.
   >   For the diversity pass on the *other* approved model, stop now and re-run
   >   this trigger from a session set to that model (a separate thread).
   > - Effort: the sub-agent inherits this session's effort tier. Policy is the
   >   highest available tier; this is NOT machine-checkable. If this session is
   >   not at the highest tier, stop now, raise it, and re-run this trigger.
   > - Replying "go" both spawns the red team **and** ratifies the roster above
   >   as current — its Last verified date will be set to today. If the roster
   >   is stale (a newer model shipped, a tier changed), fix the table first,
   >   then reply "go".

3. **Wait for an explicit "go".** Do not call the `Task` tool until the human
   replies. Conversational acknowledgement is not "go".

4. **On "go":**
   - Set the roster's **Last verified** date in `AGENTS.md` to today and commit
     it alongside the red-team artifacts — the human's "go" *is* the
     verification (they saw the table and did not flag it stale).
   - Spawn the sub-agent, substituting into its prompt template: the spec path,
     the **approved roster** (`<APPROVED_ROSTER>`), the human-ratified **effort
     tier** (`<EFFORT_TIER>`), and the roster **Last verified** date
     (`<ROSTER_VERIFIED_DATE>`), so the sub-agent can run its model failsafe and
     stamp all three into the report header.

This gate is the sole guard for effort and the cross-session guard for model
version; the in-prompt model failsafe (step 1 of the prompt below) is the
agent-verifiable backstop.

## How to invoke

Use the `Task` tool to spawn a sub-agent with the following prompt template.
Substitute `<SPEC_PATH>` and `<TEST_PATH>` with the actual paths.

```
You are a hostile test reviewer. Your job is to find ways the test suite
at <TEST_PATH> could pass while the implementation being tested is wrong.

Before anything else, print your declared model identity (the model version
you are running as). The approved red-teamers for this project are:
<APPROVED_ROSTER>. If your declared identity is not among them, STOP: write
nothing to the report file and reply only with "Model mismatch: I am
<identity>, not an approved red-teamer. Aborting." Do not review.

The project's Python environment is managed by `uv` and already ships the
scientific stack — currently numpy, scipy, matplotlib, pypdf, pypdfium2, and
daft-pgm. Run Python via `uv run python` (or `uv run <script.py>`); do NOT
install anything (no `pip install`, no `uv add`) — run `uv pip list` if you need
to confirm what is available. Also do NOT read any other red-team report
(`*-redteam*.md`, prior or concurrent) for this artefact — review it
independently, on its own merits.

Read the spec at <SPEC_PATH> first, then read the tests. Your job has two
parts.

## Part 1: Coverage gaps

For each property listed in the spec's "Properties to verify" section,
identify which test (or tests) verifies it. Then list any properties that
are not verified by any test, or are only verified weakly.

Also look for properties implied by the math but not listed in "Properties
to verify" — derivable invariances, scaling behaviors, limiting cases.
Flag the most important missing ones.

## Part 2: Vacuous or weak tests

For each test, ask: what is the simplest wrong implementation that would
still pass this test?

Concrete failure patterns to look for:

- **Returns-input tests**: tests that compare output to input and would
  pass for the identity function.
- **Returns-zero tests**: tests that check the output is "small" or "close
  to zero" without specifying what it should actually be.
- **Symmetric inputs**: tests where the input has a symmetry that makes
  many wrong outputs look right (e.g., testing on a uniform distribution
  where many statistics coincide).
- **Tolerance too loose**: `assert_allclose` with `atol=1.0` on a quantity
  that ranges from -2 to 2 — passes for almost anything.
- **Mock-shaped output**: tests that only check `output.shape == expected_shape`
  without checking values. Pass for any implementation that returns the
  right shape.
- **Missing reference value**: tests that compare two implementations to
  each other without an independent ground truth, so both can be wrong in
  the same way.
- **Statistical tests with too few samples**: a test that runs an estimator
  on 10 samples and checks it's within 50% of truth will pass for a very
  noisy estimator.

For each finding, state:
- **Test**: which test function (or "missing test" if it's a coverage gap).
- **Concern**: what wrong implementation would pass this test.
- **Severity**: high (a substantially wrong implementation passes), medium
  (a subtle bug passes), low (the test is fine but could be sharper).
- **What would resolve it**: suggest a sharper test, a known-answer case,
  a tighter tolerance, or an additional invariance check.

Known-answer cases are the most valuable suggestions. If the spec or its
references contain any analytically computable case (a specific
distribution, a specific input where the answer is known in closed form),
flag whether it is tested and recommend adding it if not.

**Ordering**: list findings in order of descending severity (high first,
then medium, then low). Within a severity level, order coverage-gap
findings (Part 1) before vacuous-test findings (Part 2), and within each
of those order by spec section or test function name (earliest first).
Number findings F1, F2, F3, ... *after* ordering.

Write your findings to `<TEST_PATH_WITHOUT_EXTENSION>-redteam.md`,
mirroring the format below. Do not include counts of findings by
severity in the summary; the list is the source of truth.

# Red-team review of <TEST_NAME>

Reviewer: red-team sub-agent
Reviewer model (declared identity): <the identity you printed as your first action>
Effort tier: <EFFORT_TIER> (human-set; not machine-verified)
Roster verified: <ROSTER_VERIFIED_DATE>
Date: <YYYY-MM-DD>
Spec version: <git commit hash if available>

## Summary

<one paragraph: qualitative impression of the test suite — does it
plausibly pin down the spec's claims, where is the weakest area,
what kind of wrong implementation would slip through. No counts.>

## Findings

### F1: <short title> [severity: high]

**Test**: <test function name or "missing">

**Concern**: <specific description, including what wrong implementation
would pass>

**What would resolve it**: <specific suggestion>

---

### F2: ...

## What the test suite gets right

<one paragraph, briefly. So the author knows what not to break.>
```

## Annotation conventions in the redteam file

Same convention as `skills/red-team-spec.md`: the human appends responses
with `> M:` (or appropriate initial) and Claude or the human appends
confirmations with `> C:`, two newlines between each. The redteam file
becomes the audit trail for the test red-team pass.

Example after resolution:

```markdown
### F2: Monotonicity test passes for constant function [severity: high]

**Test**: test_ba_iteration_is_monotonic

**Concern**: The test checks that I_tau is non-decreasing, but a wrong
implementation that always returns I_tau = 0 would pass. The test does
not check that I_tau converges to a nontrivial value.

**What would resolve it**: Add an assertion that I_tau converges to a
value strictly greater than some lower bound (e.g., I_tau >
log(min(m, n_theta)) / 100 for nontrivial likelihoods).

> M: Apply. Use the suggested lower bound but parametrise the constant
> via a fixture so it's not buried as a magic number.

> C: Applied in commit b71f3d4. Added the lower-bound assertion and
> moved the constant to a `NONTRIVIAL_MI_LOWER_BOUND` fixture in
> conftest.py.
```

## After the report exists

The author addresses findings the same way as for spec red-teaming: fix
(by adding or sharpening tests) or dismiss (with justification), with
`> M:` and `> C:` annotations inline. Status table considerations for
the test file (if it has one) follow the same direction-asymmetry rule
as specs — Claude flips backwards on revision, the human flips forwards
on re-review.

## Common dismissals that are *not* acceptable

- "This is implicitly covered by another test." If it's covered, point to
  which test and explain how. Otherwise add the test.
- "The implementation will obviously satisfy this." The whole point is that
  the tests should detect cases where the implementation does not. Add the
  test.

## Common dismissals that *are* acceptable

- "This property is verified in the integration test in
  `experiments/NNN/`." Acceptable if true, and the integration test is
  named.
- "The closed-form known-answer case requires a special function not in
  our dependencies; we'll add it when we add `scipy.special` to
  requirements." Acceptable with a follow-up item in
  `meta/what-didnt.md` or a TODO in the test file.
