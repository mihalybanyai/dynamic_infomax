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

## How to invoke

Use the `Task` tool to spawn a sub-agent with the following prompt template.
Substitute `<SPEC_PATH>` and `<TEST_PATH>` with the actual paths.

```
You are a hostile test reviewer. Your job is to find ways the test suite
at <TEST_PATH> could pass while the implementation being tested is wrong.

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

Write your findings to `<TEST_PATH_WITHOUT_EXTENSION>-redteam.md`, mirroring
the format in `skills/red-team-spec.md`.
```

## After the report exists

The author addresses findings the same way as for spec red-teaming: fix
(by adding or sharpening tests, with a note linking the commit) or dismiss
(with justification).

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
