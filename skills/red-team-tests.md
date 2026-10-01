# Skill: red-team-tests

> Use after a test file in `tests/` has been written from a spec, to find ways the
> suite could pass while the implementation is wrong. Shared rules are in
> `skills/red-team.md`; this file holds only what is specific to tests.

## Why this stage

A test suite has two failure modes that are easy to miss from the author's side:
**under-specification** (spec properties not tested at all) and **vacuous tests** (tests
that would pass for a function returning zero, or returning its input). A fresh
sub-agent reading the spec and the tests separately is well placed to catch both.

## Prompt template

Run the spawn-configuration gate (`skills/red-team.md` §1), then spawn with:

```
You are a hostile test reviewer: find ways the test suite at <TEST_PATH> could pass
while the implementation it tests is wrong. The spec is at <SPEC_PATH>. Before anything
else, read `skills/red-team.md` §3 (sub-agent rules) and the "Sub-agent brief" section
of `skills/red-team-tests.md`, and follow both throughout. Approved red-teamers:
<APPROVED_ROSTER>. Effort tier: <EFFORT_TIER>. Roster verified: <ROSTER_VERIFIED_DATE>.
```

## Sub-agent brief

### Reading order and scope

Read the spec first, then the tests. The job has two parts.

### Checklist

**Part 1: coverage gaps.** For each property in the spec's "Properties to verify",
identify the test(s) that verify it, and list the properties no test verifies or that
are verified only weakly. Also look for properties implied by the math but not listed:
derivable invariances, scaling behaviours, limiting cases. Flag the most important.

**Part 2: vacuous or weak tests.** For each test, ask: what is the simplest wrong
implementation that would still pass? Patterns to look for:

- **Returns-input**: compares output to input; passes for the identity function.
- **Returns-zero**: checks the output is "small" without saying what it should be.
- **Symmetric inputs**: a symmetry in the input makes many wrong outputs look right
  (e.g. a uniform distribution, where many statistics coincide).
- **Tolerance too loose**: `atol=1.0` on a quantity ranging over `[-2, 2]`.
- **Shape-only**: checks `output.shape` but not values.
- **No reference value**: compares two implementations with no independent ground
  truth, so both can be wrong the same way.
- **Too few samples**: an estimator run on 10 samples and checked to within 50%.

Known-answer cases are the most valuable suggestions. If the spec or its references
contain an analytically computable case, flag whether it is tested, and recommend it if
not.

### Findings

The **Location** field is named **Test**: the test function, or "missing" for a
coverage gap. The concern says which wrong implementation would pass. Severity:
**high** if a substantially wrong implementation passes; **medium** if a subtle bug
passes; **low** if the test is fine but could be sharper. Within a severity level,
coverage gaps (Part 1) come before vacuous tests (Part 2), each ordered by spec section
or test name. No routing tags.

### Report

Write to `<TEST_PATH_WITHOUT_EXTENSION>-redteam.md`. Summary focus: does the suite
plausibly pin down the spec's claims, where is it weakest, which wrong implementation
would slip through. The artefact in "What the … gets right" is the test suite.

## After the report

A test file with a status table follows the same direction asymmetry as a spec.

Dismissals that are **not** acceptable:

- "This is implicitly covered by another test." Name the test and explain how;
  otherwise add the test.
- "The implementation will obviously satisfy this." Tests exist to detect when it does
  not. Add the test.

Dismissals that **are** acceptable:

- "Verified by the integration test in `experiments/NNN/`", if true and the test is
  named.
- "The known-answer case needs a special function not in our dependencies", with a
  follow-up item in `meta/what-didnt.md` or a TODO in the test file.
