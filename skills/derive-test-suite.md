# Skill: derive-test-suite

> Use this skill when going from a spec in `specs/` to a test suite in
> `tests/`, before the implementation is written.

## Goal

The test suite is the executable form of the spec's "Properties to verify"
section, plus enough additional cases that an implementation passing all
tests is very likely correct.

## Procedure

1. **Read the spec.** Identify the "Properties to verify" section. Each
   property becomes at least one test.

2. **Name the test file.** `tests/test_NNN_short_name.py`, mirroring the
   spec filename.

3. **Cover these categories:**

   - **Sanity tests** — trivial inputs the function must handle without
     crashing (empty input, single sample, etc.).
   - **Mathematical properties** — invariances, symmetries, conservation
     laws stated in the spec. Use `numpy.testing.assert_allclose` or
     `torch.testing.assert_close` with explicit tolerances.
   - **Edge cases** — boundaries of the input space, degenerate distributions,
     extreme values.
   - **Known-answer cases** — inputs for which the correct output is known
     analytically. These are the most valuable tests; spend time finding them.
   - **Consistency tests** — outputs that should agree across different code
     paths (e.g., a vectorized implementation should match a scalar one).

4. **Use `pytest`.** Each test is one function `def test_...():`. Group
   related tests in a class if it helps. Use `pytest.fixture` for shared
   setup. Use `pytest.mark.parametrize` for varying inputs.

5. **Follow the project's randomness conventions.** See
   `skills/manage-randomness.md`. In particular: tests that use randomness
   construct their own generator with a literal hardcoded seed at the top
   of the test. No global RNG state.

6. **Leave the implementation as `NotImplementedError` placeholders.** The
   tests should fail in a meaningful way before any implementation exists.
   Run `pytest` to confirm all tests fail with the expected errors.

7. **Comment generously.** Each test should have a docstring stating *why*
   it exists — what property of the spec it verifies. A reviewer should be
   able to read the test and check that it really tests what it claims.

8. **Update the spec's properties-to-tests table.** This is a durable
   visualization of test coverage and is required output. See below.

## Properties-to-tests table

The spec's "Properties to verify" section gets a column (or a companion
table) naming the test(s) that verify each property. This converts the
spec's bullet list of properties into a bidirectional map between spec
and tests, and makes coverage gaps visible at a glance.

### Format

Add the column to the existing properties table if the spec already has
one, or add a "Verified by" subsection after the properties list. The
table looks like:

```markdown
| # | Property | Verified by |
|---|---|---|
| P1 | I_tau is non-decreasing under BA iteration | `test_ba_iteration_is_monotonic` |
| P2 | Converged I equals channel capacity | `test_ba_converges_to_capacity` |
| P3 | Atom centroids invariant under grid refinement | `test_atom_centroids_grid_invariant` |
| P4 | KS distance to Jeffreys < 0.05 at m=100 | `test_jeffreys_limit` |
| P5 | Atom count in [1, ceil(log2(m))+1] | *no test yet* |
```

Conventions:

- The "Verified by" cell names a test function, fully qualified within
  the test file (`test_ba_iteration_is_monotonic`, not `test_monotonic`).
- If multiple tests verify a property, list all of them, comma-separated.
- If a property is verified only weakly (e.g., on a single input where
  many would be needed), note this: `test_x (single input only)`.
- If no test verifies a property, write `*no test yet*` in italics. The
  italic markup makes gaps grep-able and visually distinct.
- If a property is intentionally not testable (e.g., a claim about
  asymptotic behaviour that can only be verified empirically in an
  experiment, not unit-tested), write `*not unit-testable; see experiment
  NNN*` and ensure the named experiment exists.

### Why this is required output

Three reasons:

1. **Gap visibility.** The italic `*no test yet*` entries are the
   visualization of (a) coverage of the spec by the tests. Easier to
   spot than re-reading the spec and the tests separately.

2. **Bidirectional verifiability.** A CI script (or a careful reader)
   can check two things from this table: every property has a test (or
   a documented reason it doesn't), and every named test actually
   exists in the test file. The table is the contract between the two
   files.

3. **Survives revision.** When a spec is revised (per the
   Correction/Clarification/Refinement categories in
   `skills/write-math-spec.md`), the table makes it immediately
   apparent which tests are downstream of the revised property.

### Maintenance

The table is updated as part of the same change that adds, removes, or
modifies a test. Specifically:

- Adding a new test → add or update the relevant row.
- Removing a test → either update the row or, if the property is now
  unverified, change the entry to `*no test yet*`.
- Adding a property to the spec → add a row with `*no test yet*` until
  a test is written.
- Revising a property → reconsider whether the existing test still
  verifies the revised property; update or replace as needed.

If the table drifts from reality (a named test doesn't exist, or a
test exists but isn't in the table), that's a bug to fix, not a
finding to dismiss.

## Output

A new file at `tests/test_NNN_short_name.py`, with all tests currently
failing. Plus stub files in `src/` if needed so that imports resolve.
The spec is updated to include the properties-to-tests table; this
update is committed together with the new test file. The spec status
table is *not* changed by this step — adding a coverage table is not a
revision to any reviewed section, just an addition reflecting the new
test artifact.
