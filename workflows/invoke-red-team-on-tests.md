# Workflow: invoke-red-team-on-tests

> Red-team a test suite, then decide, update the spec and regenerate the tests. Shared
> stages are in `workflows/invoke-red-team.md`; this file holds only what is specific
> to tests.

## When to use

When a test file in `tests/` covers every `reviewed` section of its spec: the gate
between "tests written" and "approved for implementation". Not while a section the tests
cover is `draft` or `needs-revision`.

## Prerequisites

The spec is committed in its current `reviewed` state.

## Stage 1 — Invoke

```
Red-team the test suite [[TEST_PATH]] against [[SPEC_PATH]] with
skills/red-team-tests.md, following workflows/invoke-red-team.md Stage 1.
```

## Stages 2 and 3a — Annotate and decide

As in `workflows/invoke-red-team.md`. Each `> C:` says whether the change is to the
spec, the test file or both. A coverage gap usually touches only the tests; an
ambiguously stated property touches the spec; a load-bearing assumption that was never
tested touches both. Which dismissals are acceptable is in `skills/red-team-tests.md`.

## Stage 3b — Update the spec

If any `> C:` calls for a spec change: *Spec edits* in `workflows/invoke-red-team.md`.
The tests are not regenerated until the human has re-reviewed the spec.

## Stage 3c — Regenerate the test suite

Once the spec is re-reviewed (or straight after 3a, if no `> C:` touched the spec):

```
I've reviewed the spec. Make any changes the review calls for first. Then:

1. Remove the red marking from the spec.
2. Add or update the property-to-test table at the start of the spec's test-suite
   section (format in skills/derive-test-suite.md): one row per property in
   "Properties to verify", a "Verified by" column, `*no test yet*` for each gap.
3. Regenerate [[TEST_PATH]] from the updated spec, with the `> C:` annotations in
   [[REDTEAM_PATH]] as the change set: tests added, sharpened or removed.

Commit together, referencing the red-team pass.
```

A spec's first property-to-test table is added here; after that it is maintained per
`skills/derive-test-suite.md`.
