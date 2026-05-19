# Workflow: implement-spec

> End-to-end workflow for going from a reviewed spec with a
> red-teamed test suite to a passing implementation with
> documentation, ready for the implementation red-team. Five
> stages: code generation, eye test, full test suite, documentation
> finalisation, and handoff to the red-team workflow.

## When to use

When a spec in `specs/` has all sections at status `reviewed`, the
test suite has been through `invoke-red-team-on-tests` and is at its
post-red-team state, and the implementation has not yet been
generated. This is the gate between "tests approved" and "code
written, eye-test passed, full suite passing, documentation in
place — ready for the implementation red-team."

Do not invoke if any spec section is still `draft` or
`needs-revision`, or if the test suite has not been red-teamed.
Implementation generation runs against a stabilised upstream.

## Prerequisites

- All relevant sections of the spec are at status `reviewed`.
- The test suite at `tests/` has been through
  `invoke-red-team-on-tests` and is at its post-red-team state.
- The spec's "Eye test" section (see
  `skills/write-math-spec.md`) names a concrete eye test for this
  implementation. Older specs may not yet have one — see the
  fallback in stage 2.
- An experiment directory exists at
  `experiments/<EXPERIMENT_ID>/` for the codegen log to live in.
  If not, create it before starting.
- `skills/manage-randomness.md` and any other relevant skills
  exist and are current.
- Claude Code session is open and oriented to the project (see
  `workflows/wake-up-claude-code.md`).

## Stage 1 — Code generation

Paste into Claude Code:

```
The test suite red-teaming is complete, so we can proceed to
generate the implementation now. Do this according to the relevant
section in [[SPEC_PATH]] and skills/manage-randomness.md. The
generated code should pass the test suite perfectly.

Generate a very compact code generation log at
experiments/<EXPERIMENT_ID>/CODEGEN_LOG.md that just states what
has already been generated fully and what remains to be done.

Also create a documentation file at [[DOC_PATH]] (typically
docs/<spec-id>/README.md). In a "Design decisions" section, record
all technical decisions you made that are not specified in the
spec — algorithm choices, numerical regime trade-offs, data
structure choices, anything a future reader would predictably ask
"why this?" about.

After generating each file, update the codegen log, and commit
the generated file and the log together as a single commit.
```

The per-file commit cadence is deliberate. It produces a clean
history where each commit corresponds to one generated artifact
and its log entry, and makes the codegen log itself an honest
indicator of progress rather than a doc that gets reconciled at
the end.

The "Design decisions" section accumulates from this stage onward
— it never gets thrown out and regenerated. It's an append-only
record of the choices made, with the audit trail that goes with
them.

### Codegen log structure

The codegen log is short. A minimal version has three sections,
in this order:

```markdown
# Codegen log — <EXPERIMENT_ID>

## File status

| File | Status | Last-passing commit |
|------|--------|---------------------|
| src/infomax/__init__.py     | done           | a3f4d12 |
| src/infomax/ba.py           | done           | a3f4d12 |
| src/infomax/sufficient_stats.py | pending-tests | (none yet) |
| ...                                            |
| tests/test_ba.py            | done           | a3f4d12 |
| tests/test_eye_ba_m2.py     | done           | a3f4d12 |

## Test status

| Test                              | Status         | Last-passing commit |
|-----------------------------------|----------------|---------------------|
| test_ba_iteration_is_monotonic    | passing        | a3f4d12 |
| test_ba_fixed_point_satisfies_ksys| passing        | a3f4d12 |
| test_ba_converges_to_known_answer | passing        | a3f4d12 |
| ...                               |                |         |

## Eye test status

| Eye test       | Status            | Figure path                                  |
|----------------|-------------------|----------------------------------------------|
| ba_m2_n100_1000steps | passed (M, 2026-05-19) | experiments/<EXPERIMENT_ID>/figs/eye_ba_m2.png |
```

Status values used across the three tables:

- **File status**: `pending` (declared, not yet generated),
  `done` (generated and last passed the relevant tests),
  `pending-tests` (modified, needs to re-pass tests before
  flipping back to `done`).
- **Test status**: `passing`, `failing`, `not-yet-run`.
- **Eye test status**: `not-yet-run`, `pending review`,
  `passed`, `rejected`. When `passed` or `rejected`, append the
  reviewer's initial and the date.

The "Last-passing commit" column for files is filled by stage 3
once the full suite passes against that commit. For tests, it's
filled per-test as stage 3 walks the suite. For files that have
never passed tests yet (the initial codegen), the column reads
`(none yet)` until the first stage 3 completes.

The status table is small on purpose. It is not a substitute for
the git log; it's a source of truth for "which version of each
file is known to pass each test" — the bisection breadcrumb. If
the table grows past one page, the experiment is probably too
big and should be split.

## Stage 2 — Eye test

The eye test is a low-ceremony human-judgement check before
spending compute on the full suite. The spec defines what the
eye test is for this implementation (typically a small,
analytically-tractable case where the correct answer has a
recognisable visual signature). The human decides whether the
figure looks right; there are no quantitative criteria.

### If the spec has an "Eye test" section

Paste into Claude Code:

```
Per the "Eye test" section of [[SPEC_PATH]], make a separate test
file at tests/test_eye_<DESCRIPTOR>.py implementing the eye test.
Run it. Add a row to the codegen log's eye test status table with
status `pending review` and the path to the resulting figure. Tell
me where the figure went.
```

The human inspects the figure and replies:

- **If it looks right**: "Eye test passed." Claude flips the
  eye-test row's status to `passed (<initial>, <date>)` and the
  workflow proceeds to stage 3.
- **If it doesn't look right**: "Eye test rejected — \[brief
  reason\]." Workflow branches to the eye-test rejection path
  below.

### If the spec has no "Eye test" section (older specs only)

For older specs that pre-date the eye-test convention, the human
defines the eye test inline when reaching this stage:

```
Insert this eye test at the beginning of the test suite section
in the spec (no need for status flips, direct edit; I'll revise
on review): <DESCRIPTION OF EYE TEST — typically: which case to
run, how long, what to plot, what to look for>.

Then make a separate test file at tests/test_eye_<DESCRIPTOR>.py,
run it, add a row to the codegen log's eye test status table with
status `pending review` and the path to the figure, and tell me
where the figure went.
```

This branch exists only for migration. Once the spec has an "Eye
test" section, it's a `pending-tests`-and-flip-on-review like
anything else in the spec — but the convention going forward is
that eye tests are decided during spec writing, not
during implementation. See `skills/write-math-spec.md` for the
spec-side convention.

### Eye-test rejection — debugging branch

When the human rejects the eye test, two paths are available and
the choice is an active decision, not a default:

- **Path A (default)**: localised debugging. The human and Claude
  discuss what's likely wrong based on the figure, edit the code
  (and possibly the spec or the eye-test definition itself, if
  the rejection reveals an upstream issue), re-run the eye test,
  and iterate until it passes.
- **Path B (active opt-in)**: run the full test suite anyway, as
  a debugging aid. Sometimes the full suite is the fastest way to
  localise the bug, even though the eye test failed. If the human
  chooses this, the workflow jumps to stage 3 with the eye test
  still at `rejected`, and the eye test gets re-run after the
  test-driven debugging completes.

Significant decisions made during eye-test debugging — particularly
ones that touched the spec or the eye-test definition — go into the
documentation file's "Testing notes" section (created at stage 4
if it doesn't yet exist; created here if the rejection forces it
earlier).

Once the eye test is accepted, flip the row to `passed (<initial>,
<date>)` in the codegen log and proceed to stage 3.

## Stage 3 — Full test suite

Once the eye test is `passed`, paste:

```
Eye test passed. Re-run the full test suite one-by-one. After each
test passes, edit experiments/<EXPERIMENT_ID>/CODEGEN_LOG.md with
the commit hash that identifies the code version that last passed
that test, in the Test status table.

After all tests have been run, give me a success report (or a
failure report if any failed). Update the codegen log's File
status table: flip the status of every code file currently at
`pending-tests` to `done`, with the commit hash from the run.

If any tests fail, do not attempt to fix them yourself —
report the failures back to me and we'll decide case by case.
```

The one-by-one cadence is intentional, same reasoning as the
red-team workflow's stage 3d: a per-test commit hash is needed
for future bisection, and a bulk pass-fail summary loses that
information.

### Test-failure branch

If any tests fail, Claude reports the failures back. For each
failure, the resolution is decided jointly between the human and
Claude. Possible actions, with no default:

- **Edit the code** to fix the bug the test caught.
- **Edit the test** if the test is wrong (rare at this stage — the
  test suite has been red-teamed — but possible).
- **Edit the spec** if the failure reveals a spec ambiguity or
  error. Spec edits at this stage follow the same convention as
  spec red-team edits: red text, revision log entry, affected
  sections flipped to `draft`, and the human re-reviews before
  the workflow continues.
- **Edit the eye-test definition** if the failure reveals that
  the eye test was checking the wrong thing.
- **Edit the documentation**, particularly the "Design decisions"
  or "Testing notes" sections, when the decision needed to fix
  the failure adds load-bearing context.

Every significant decision made during test failure resolution
— particularly ones that touched the spec, the test, or the
eye-test definition, but also non-obvious code choices — goes
into the documentation file's "Testing notes" section.

After each batch of fixes, the failed test is re-run individually
(not the whole suite, until at the end). When all tests are
passing one-by-one, run the suite end-to-end once more as a
sanity check, then update the codegen log per the success
instructions in stage 3 above.

## Stage 4 — Documentation finalisation

The documentation file already has a "Design decisions" section
accumulated during stage 1 and possibly a "Testing notes" section
from stage 3. Stage 4 adds the two generated structural diagrams.

Paste:

```
All tests pass. Finalise the documentation at [[DOC_PATH]].

1. Generate a call graph for the implementation using the
   code2flow python package. Embed the result as a mermaid
   diagram in the .md file. Make sure code2flow is added to
   pyproject.toml and uv.lock.

2. Add a data flow diagram showing tensor shapes through the
   main algorithm (e.g. the BA iteration), embedded as mermaid.

The final section order in the .md is:

  1. (Title and one-paragraph overview)
  2. Call graph
  3. Data flow diagram
  4. Design decisions (already present from stage 1)
  5. Testing notes (present if stage 3 had non-trivial failures)

Commit the regenerated doc, the updated pyproject.toml, and
uv.lock as a single commit.
```

### Documentation lifecycle summary

The four content sections of the doc accumulate at different
stages:

- **Design decisions**: from stage 1 onward, append-only,
  records every non-spec'd technical choice.
- **Testing notes**: from stage 3 onward (if any non-trivial
  test failures occur), append-only, records significant
  decisions made during failure resolution.
- **Call graph**: stage 4, regenerated each time the
  structural shape of the code changes (typically only on
  red-team-driven edits — handled by `_make_call_graph.py` or
  equivalent helper script).
- **Data flow diagram**: stage 4, manually maintained,
  regenerated when shape signatures change.

The reason design decisions and testing notes come *after* the
diagrams in the .md is that the diagrams are visual orientation
and read fastest; a labmate coming in cold benefits from seeing
the structural picture before reading the rationale.

## Stage 5 — Handoff to the red-team workflow

At this point the implementation passes the eye test and the full
test suite, the codegen log shows all files at `done` with
per-test commit hashes, and the documentation file has all four
content sections. The workflow ends here.

The next step is `workflows/invoke-red-team-on-impl.md`. Do not
invoke it inline from this workflow — invoke it as a fresh action
once the implementation phase is complete, so the red-team is a
distinct event in the audit trail rather than a buried stage.

## What this does

The five stages produce, in order:

1. An implementation in `src/`, generated file-by-file with a
   matching codegen log entry per file and a "Design decisions"
   section of the doc accumulating in parallel.
2. An eye-test test file and figure, with the figure approved
   (or rejected and iterated until approved).
3. A passing full test suite with per-test commit hashes in the
   codegen log, every code file flipped to `done`, and a
   "Testing notes" section in the doc capturing any non-trivial
   decisions made during failure resolution.
4. A documentation file with a generated call graph (via
   `code2flow`) and a manually-maintained data flow diagram, in
   addition to the design decisions and testing notes.
5. A clean handoff to the implementation red-team workflow.

The codegen log is the durable record of which code version
passes which test, file by file and test by test. The
documentation file is the durable record of why the
implementation looks the way it does.

## What this is *not* for

- Generating an implementation against an un-red-teamed test
  suite. The test red-team is a prerequisite.
- Generating an implementation against a spec with `draft` or
  `needs-revision` sections. The spec must be stable.
- Re-running this workflow after a red-team-driven revision.
  Post-red-team re-runs are handled inside
  `invoke-red-team-on-impl.md` (stages 3c and 3d). This workflow
  only runs once per spec-implementation pair, on initial
  generation.
- Approving the implementation. The red-team is what grants
  approval; this workflow only gets the implementation to the
  state where the red-team can run.

## Related

- `skills/manage-randomness.md` — referenced in stage 1 for the
  randomness conventions the implementation must follow.
- `skills/write-math-spec.md` — defines the "Eye test" section
  of the spec that stage 2 relies on, and the spec status table
  / revision log conventions referenced in the test-failure
  branch.
- `workflows/invoke-red-team-on-tests.md` — the prerequisite
  workflow. This one assumes the test suite is at its
  post-red-team state.
- `workflows/invoke-red-team-on-impl.md` — the follow-on
  workflow. Picks up where this one ends. Note that its stage
  3d re-runs both the eye test (when one is defined) and the
  full test suite after red-team edits.
- `AGENTS.md` — the workflow section that names the overall
  spec → tests → implementation → red-team pipeline.
- `workflows/wake-up-claude-code.md` — must be done before this
  workflow can run.
