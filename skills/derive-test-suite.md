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

5. **Leave the implementation as `NotImplementedError` placeholders.** The
   tests should fail in a meaningful way before any implementation exists.
   Run `pytest` to confirm all tests fail with the expected errors.

6. **Comment generously.** Each test should have a docstring stating *why*
   it exists — what property of the spec it verifies. A reviewer should be
   able to read the test and check that it really tests what it claims.

## Output

A new file at `tests/test_NNN_short_name.py`, with all tests currently
failing. Plus stub files in `src/` if needed so that imports resolve.
