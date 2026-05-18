# Workflow: invoke-red-team-on-tests

> Multi-stage workflow for red-teaming a test suite: trigger the
> red-team sub-agent, then process findings to either apply or
> dismiss each one. Differs from the spec red-team workflow because
> test red-team findings can touch two artifacts — the spec (when
> coverage gaps reveal under-specified properties) and the test
> file itself (when vacuous or weak tests need sharpening) — so the
> processing is split into three explicit steps: decide, update the
> spec, regenerate the tests.

## When to use

When a test file in `tests/` has been written from a spec all of
whose `reviewed` sections are covered, and is ready for the
red-team pass per the convention in `AGENTS.md`. This is the gate
between "tests written" and "approved for implementation."

Do not invoke if sections of the spec the tests cover are still
`draft` or `needs-revision` — the test red-team pass should run
against tests that target a stabilised contract.

## Prerequisites

- The test file covers all `reviewed` sections of the relevant spec.
- `skills/red-team-tests.md` exists and is current.
- The spec it tests against is committed in its current `reviewed`
  state.
- Claude Code session is open and oriented to the project (see
  `workflows/wake-up-claude-code.md`).

## Stage 1 — Invoke the sub-agent

Paste into Claude Code:

```
The test scaffolding and property assertions at [[TEST_PATH]] are now complete for the
sections of [[SPEC_PATH]] that are at status `reviewed`. Per
skills/red-team-tests.md, invoke the red-team-tests skill: spawn a
sub-agent with the adversarial prompt in the skill, give it both
the spec and the test file, and have it write findings to
[[TEST_PATH_WITHOUT_EXT]]-redteam.md in the format the skill
specifies.

The sub-agent should read the spec first, then the tests, then
audit for (1) coverage gaps against the spec's "Properties to
verify" section, and (2) tests that would pass for a wrong
implementation. Findings ordered by descending severity, coverage
gaps before vacuous-test findings within each severity level,
numbered F1, F2, ... after ordering.

Do not read the findings yourself or pre-filter them — just commit
the file when the sub-agent is done.
```

The "do not pre-filter" clause matters: if the main Claude Code
agent reads the sub-agent's output and silently drops findings it
judges spurious, the fresh-context value of the red-team is lost.
Findings land raw, then the human triages.

## Stage 2 — Annotate the report

Open the resulting redteam file. For each finding, append a response
in the file itself using the `> M:` (mihaly, or whoever the human
is) prefix. Two newlines separate the response from the finding
above.

```markdown
### F3: No test for invariance under relabeling [severity: high]

**Location**: Spec §2.3 property P4 / no test file location

**Concern**: ...

**What would resolve it**: ...

> M: Yes — add the test. Use a fixed permutation, fixed seed.

> M: Not sure. The property is real but the test as suggested would
> need a special function we don't have a dep for yet. Is there a
> cheaper version that catches the same wrong implementations?

> M: Dismiss. This is covered implicitly by F1's test once F1 is
> applied.
```

Conventions for `> M:` responses:

- **Confident apply**: state what to apply. Be specific if the
  sub-agent's suggestion needs amendment.
- **Confident dismiss**: explain why. Brief is fine; the explanation
  becomes audit trail.
- **Uncertain**: ask a question, or state the ambiguity. These will
  be discussed before resolution.

There's no required template — natural prose works. The `> M:`
prefix is just for greppability and visual separation.

## Stage 3a — Decide what changes to make

Paste into Claude Code:

```
Process the red-team report at [[REDTEAM_PATH]] which I reviewed
already. We will be doing this as a three-step process.

First step: decide what changes to make. For this, consider
one-by-one the issues raised in the red team report, and my
opinions that I gave in the report file with the `> M:` prefix
after each issue.

Wherever I gave a confident instruction, and you agree, you can
describe the modifications to be made in the redteam file, under
my response, by appending a sentence prefixed by two newlines and
`> C:` stating that you are making the update in the spec, in the
test file, or in both.

If you don't agree with a confident response I gave, push back here
in the chat rather than recording a `> C:` for that finding.

Wherever I expressed uncertainty or a question in my response, come
back to me here with your opinion. We will resolve these one by
one, then you'll describe the updates we converge to as `> C:`
comments under mine in the redteam file.

Do not edit the spec or the test file yet. This step is only
deciding and recording the decisions in the redteam file.
```

A few things to flag about this step that differ from the spec
red-team:

- **Two target artifacts, not one.** Each `> C:` must say whether
  the change is to the spec, the test file, or both. Coverage-gap
  findings often touch only the test file; findings that reveal an
  ambiguity in a property's statement touch the spec; findings that
  expose a load-bearing assumption that was never tested touch
  both.
- **Explicit pushback license.** Spec red-team findings are usually
  math errors or assumptions, which are objectively right or wrong.
  Test red-team findings often involve judgement about whether a
  proposed test is worth adding, which a fresh sub-agent can
  over-suggest. Allowing Claude to disagree with a `> M:` apply is
  part of the design.
- **Convergence happens in chat.** Uncertainties are resolved in
  conversation, then their resolutions are written back into the
  redteam file as `> C:` annotations. The redteam file ends up
  being a self-contained record without the chat being part of it.

## Stage 3b — Update the spec

Once the redteam file's `> C:` annotations are complete and
agreed, paste:

```
Go ahead and make the modifications in [[SPEC_PATH]] for the
findings whose `> C:` annotations indicate a spec change. Apply
red text color (HTML inline spans, see "Notes on red marking"
below) where there is a modification. Revert the status flag of
any affected section(s) back to draft, and add a revision log
entry per skills/write-math-spec.md categorising the changes.

Do not regenerate the test suite yet. The human will re-review the
spec sections before the test regeneration runs.
```

The human then re-reviews the affected spec sections and flips the
status flags forward (`draft → reviewed`) as appropriate. This
review step is the same direction-asymmetry rule used elsewhere in
the project: Claude flips backwards on revision, the human flips
forwards on re-review.

## Stage 3c — Regenerate the test suite

Once the human has re-reviewed the spec and flipped status flags,
paste:

```
I've reviewed the spec. If there are things to modify upon
review, do those first. Then:

1. Remove all the red coloring from the spec (the HTML inline
   spans added in stage 3b). The revision log preserves the audit
   trail.

2. Add the property-to-test table at the beginning of the test
   suite section of the spec, per skill (skills/derive-test-suite.md
   describes the format). One row per property in "Properties to
   verify", with a "Verified by" column naming the test that
   verifies each property, and `*no test yet*` marking any gap.

3. Regenerate the test suite at [[TEST_PATH]], using the updated
   spec and the `> C:` annotations in the redteam file as the
   change set. The regeneration should reflect: (a) any new tests
   added, (b) any tests sharpened to be non-vacuous, (c) any tests
   removed, and (d) the property-to-test table now living in the
   spec.

Commit the changes together with a message referencing the
redteam pass.
```

After stage 3c, the spec has the property-to-test table embedded,
the test file matches the redteam-evaluated state, and the redteam
file has `> C:` annotations describing every change for the audit
trail.

## Notes on red marking

The spec is markdown. Markdown has no native red-text syntax. Three
options for marking revised content:

1. **HTML spans inline**: `<span style="color: red">revised text</span>`.
   Renders in most markdown viewers (VSCode preview, Obsidian,
   GitHub web view). Diffs cleanly.
2. **Block-level callouts**: a `> [!warning]` callout containing
   the revised text. Standout visually but heavier — better for
   big revisions than for word-level edits.
3. **A "revised" CSS class** for tools that support it. Most do
   not; skip this unless you have a reason.

Default to option 1 (inline HTML span) unless a revision is large
enough to warrant a callout. The red marking is removed in stage
3c after the human re-reviews; the revision log preserves the
audit trail.

## What this does

The four stages produce, in order:

1. A redteam file with the sub-agent's raw findings.
2. An annotated redteam file with the human's `> M:` reactions
   inline.
3a. The redteam file fully annotated with `> C:` decisions for
   every finding, recording for each whether it touches the spec,
   the tests, or both.
3b. A revised spec with red-marked changes, status flipped on
   affected sections, and a revision log entry.
3c. A re-reviewed spec (red marking removed, property-to-test
   table added) and a regenerated test file matching the agreed
   change set.

The redteam file is a complete audit trail: what was flagged, what
the human thought, what was done, and which artifact each change
touched. Future readers (labmates, reviewers, future-you) can
reconstruct the reasoning.

## What this is *not* for

- Red-teaming the spec itself, code, or experiment writeups. Those
  have their own sibling workflows (`invoke-red-team-on-spec` and,
  forthcoming, `invoke-red-team-on-implementation`,
  `invoke-red-team-on-result`).
- Re-running red-team after a revision. The current convention is
  "one red-team per test file, run when the test file is complete
  for the spec's reviewed sections." If a substantial revision
  warrants a second red-team pass, that's a judgement call; the
  workflow doesn't prescribe re-runs.
- Adding the property-to-test table to a spec that has never had
  one. The first addition happens here, as part of stage 3c. After
  that, the table is maintained per `skills/derive-test-suite.md`.

## Related

- `skills/red-team-tests.md` — the procedure the sub-agent follows.
- `skills/derive-test-suite.md` — the property-to-test table
  format, plus the rules for maintaining it across edits.
- `skills/write-math-spec.md` — the status table, revision log,
  downstream-approval rules.
- `workflows/invoke-red-team-on-spec.md` — the sibling workflow
  this one parallels; shares the `> M:` / `> C:` annotation
  convention, the red-marking convention, and the
  do-not-pre-filter convention.
- `AGENTS.md` — the red-teaming section that names this as a
  required step.
- `workflows/wake-up-claude-code.md` — must be done before this
  workflow can run.
