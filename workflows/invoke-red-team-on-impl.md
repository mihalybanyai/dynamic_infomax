# Workflow: invoke-red-team-on-impl

> Red-team an implementation, then decide, update the spec if needed, regenerate code
> and docs, and re-run the tests one by one. Shared stages are in
> `workflows/invoke-red-team.md`; this file holds only what is specific to
> implementations.

## When to use

When an implementation in `src/` written from a `reviewed` spec passes the red-teamed
test suite and has its documentation in place: the gate between "works and is
documented" and "approved for experimental use". It follows `workflows/implement-spec.md`.

## Prerequisites

- The test suite has been through `invoke-red-team-on-tests.md`, and the implementation
  passes it at HEAD.
- The documentation in `docs/<spec-id>/` is current with the code, including the helper
  scripts that regenerate doc artefacts (e.g. `_make_call_graph.py`).

## Stage 1 — Invoke

```
Red-team the implementation in [[CODE_DIR]] (spec [[SPEC_PATH]], docs [[DOC_PATH]])
with skills/red-team-implementation.md, following workflows/invoke-red-team.md Stage 1.
```

## Stages 2 and 3a — Annotate and decide

As in `workflows/invoke-red-team.md`, upstream check first. Each `> C:` names its
targets: spec, code, docs, a doc helper script, or a routing. A helper script is a
target of its own, because editing it means re-running it. Findings tagged `[test-gap]`
are routed and the test file is not edited here. A `[spec-implication]` is routed too,
unless the human and the main agent agree the code is right and the spec must catch up;
then its `> C:` is a spec edit for 3b.

## Stage 3b — Update the spec (if any)

*Spec edits* in `workflows/invoke-red-team.md`. Code and docs wait for the human's
re-review. If no `> C:` touches the spec, skip to 3c.

## Stage 3c — Regenerate code, docs and helper-script artefacts

Once the spec is re-reviewed, or 3b was skipped:

```
I've reviewed the spec. Make any changes the review calls for first. Then:

1. Remove the red marking from the spec.
2. Make the code edits in [[CODE_DIR]] that the `> C:` annotations call for.
3. Make the documentation edits in [[DOC_PATH]] they call for: inline comments,
   design-decision entries, data-flow and shape annotations, the call graph.
4. Edit each doc helper script they call for (e.g. [[DOC_DIR]]/_make_call_graph.py)
   and re-run it; the regenerated artefact goes in the same commit as the script.
5. In experiments/[[EXPERIMENT_ID]]/CODEGEN_LOG.md, flip every code file edited in
   step 2 to `pending-tests`, keeping its last-passing hash (3d updates it).

Do not commit yet: the re-run in 3d may surface more changes.
```

The edits are one coherent revision (the code change motivates the doc update, which
motivates the helper re-run), so they are made in one pass and committed together.

## Stage 3d — Re-run the eye test and the test suite

```
Re-run the eye test named in experiments/[[EXPERIMENT_ID]]/CODEGEN_LOG.md, tell me
where the figure went, flip its row to `pending review`, and wait for my approval.

Once I approve, flip the row to `passed (<initial>, <date>)` and re-run the full suite
one test at a time. After each test passes, record in CODEGEN_LOG.md the commit hash of
the code version that last passed it. If a test fails, report the failure to me; do not
fix it yourself.

Once all tests pass, flip every `pending-tests` code file back to `done` and commit,
referencing the red-team pass.
```

The eye test comes first because it is the cheap human check: a visible breakage is
caught before the full walk. The one-by-one re-run gives each test a commit hash to
bisect against later; a bulk re-run says only *that* something broke.

**If the eye test or a test fails**, the cause is decided with the human; the workflow
does not presume one:

- the edit was wrong: revisit its `> C:`, and record the correction as a follow-up
  `> M:` and `> C:`;
- the red-team missed something: add it to the report as the next F-number and triage
  it like the others;
- the test is wrong: tag it `[test-gap]` and route it (*Routing upstream* in
  `workflows/invoke-red-team.md`).

The resolution is recorded in the report, and the re-run restarts from the eye test if
that failed, otherwise from the failed test.

`CODEGEN_LOG.md` is updated here because this workflow establishes a verified per-test
code version; other workflows that touch tests or code update it by their own
conventions.
