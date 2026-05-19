# Workflow: invoke-red-team-on-impl

> Multi-stage workflow for red-teaming an implementation: trigger the
> red-team sub-agent, then process findings to apply, dismiss, or route
> each one upstream. Differs from the spec and test red-team workflows
> because implementation red-team findings can touch up to three
> artifacts (spec, code, documentation including helper scripts), and
> some findings route *upstream* to the test or spec red-team rather
> than being acted on here. The processing is split into four explicit
> sub-stages: decide, update the spec (if any), regenerate the
> implementation and documentation, then re-run the test suite
> one-by-one with per-test commit hashes logged.

## When to use

When an implementation in `src/` is written from a spec all of whose
relevant sections are at status `reviewed`, the test suite has been
red-teamed and the implementation passes all tests, and the
documentation (design decisions, data flow, call graph, helper scripts
that regenerate doc artifacts) is in place. This is the gate between
"implementation works and is documented" and "approved for downstream
experimental use."

Do not invoke if any of the prerequisites below are missing — the
implementation red-team pass should run against a fully stabilised
upstream chain.

## Prerequisites

- All `reviewed` sections of the relevant spec are committed.
- The test suite has been through `invoke-red-team-on-tests` and is
  at its post-red-team state.
- The implementation passes the full test suite at HEAD.
- The documentation files in `docs/<spec-id>/` exist and are current
  with the implementation as the author understands it. This includes
  any helper scripts (e.g. `_make_call_graph.py`) that regenerate
  doc artifacts.
- `skills/red-team-implementation.md` exists and is current.
- Claude Code session is open and oriented to the project (see
  `workflows/wake-up-claude-code.md`).

## Stage 1 — Invoke the sub-agent

Paste into Claude Code:

```
The implementation at [[CODE_DIR]] passes the full test suite, and
the documentation at [[DOC_PATH]] is in place. Per
skills/red-team-implementation.md, invoke the red-team-implementation
skill: spawn a sub-agent with the adversarial prompt in the skill,
give it the spec at [[SPEC_PATH]], the implementation directory, and
the documentation file, and have it write findings to
[[DOC_DIR]]/redteam-impl.md in the format the skill specifies.

Tell the sub-agent the context explicitly: the spec is at status
`reviewed` across all relevant sections, the test suite has been
red-teamed, and the implementation passes all tests. So the
sub-agent is NOT auditing the math (settled), NOT auditing test
coverage against the spec (settled). Its job is the gap between
"passes the tests" and "is actually a good implementation of the
reviewed spec, well-documented."

The sub-agent should read the spec first, then the docs, then the
code (this order is in the skill, but worth restating). Findings
ordered by descending severity within each of the five categories
(bugs, latent risks, inefficiencies, doc inaccuracies, doc
omissions), with categories in priority order. Numbered F1, F2, ...
after ordering. Routing tags `[test-gap]` and `[spec-implication]`
applied where appropriate per the skill.

Do not read the findings yourself or pre-filter them — just commit
the file when the sub-agent is done.
```

The "do not pre-filter" clause matters: if the main Claude Code agent
reads the sub-agent's output and silently drops findings it judges
spurious, the fresh-context value of the red-team is lost. Findings
land raw, then the human triages.

## Stage 2 — Annotate the report

Open the resulting redteam file. For each finding, append a response
in the file itself using the `> M:` (or appropriate initial) prefix.
Two newlines separate the response from the finding above.

```markdown
### F4: Covariance update reuses unwhitened input [severity: high]

**Location**: src/infomax/sufficient_stats.py:88–104

**Concern**: ...

**What would resolve it**: ...

**Touches**: code, docs

> M: Apply — store a copy of the pre-whitening input. Update the
> data-flow doc to mark the pre-whitening copy as a named
> intermediate.

> M: Not sure this is actually a bug — the covariance of the
> whitened residual may be what we want for the downstream step.
> Let's discuss.

> M: Dismiss. The whitening here is by design idempotent for the
> regime we care about; the covariance of the residual is
> equivalent to the covariance of the raw input up to a constant
> the next stage absorbs.

> M?: I don't have a feel for whether the loss of precision from
> reusing the whitened input is bounded by the spec's stated
> tolerance, or whether it could compound across iterations. Need
> to understand this before I can apply or dismiss.
```

Conventions for `> M:` responses are the same as the spec and test
red-team workflows:

- **Confident apply**: state what to apply. Be specific if the
  sub-agent's suggestion needs amendment.
- **Confident dismiss**: explain why. Brief is fine; the explanation
  becomes audit trail.
- **Uncertain**: ask a question, or state the ambiguity. Resolved in
  chat in stage 3a before any `> C:` is recorded.
- **Not equipped to evaluate**: prefix with `> M?:` (note the
  question mark) rather than `> M:`. Findings annotated `> M?:` will
  be discussed in chat in stage 3a before any `> C:` is recorded.

For findings tagged `[test-gap]` or `[spec-implication]`, the `> M:`
response can still be apply/dismiss/uncertain — the tag only affects
where the resolution goes, not whether it's a real finding. A
`[test-gap]` apply will route to the test red-team queue; a
`[spec-implication]` apply will route to the spec red-team queue
(see stage 3a).

There's no required template — natural prose works. The `> M:` prefix
is just for greppability and visual separation.

## Stage 3a — Decide what changes to make

Paste into Claude Code:

```
Process the red-team report at [[REDTEAM_PATH]] which I reviewed
already. The code is at [[CODE_DIR]], the docs at [[DOC_PATH]].
We will be doing this as a four-step process.

First step: decide what changes to make, including whether any
finding forces us to return to an earlier step of the workflow
(redraft a spec section, regenerate the test suite, or — for
findings tagged `[test-gap]` or `[spec-implication]` — route the
finding to the appropriate upstream red-team queue).

For each finding, consider my opinion (`> M:` prefix) one by one.

Wherever I gave a confident instruction, and you agree, describe
the modifications to be made in the redteam file by appending a
sentence prefixed by two newlines and `> C:` stating what you are
updating: spec, code, doc, doc helper script, or a combination —
or that the finding is being routed upstream because of its tag.

If you don't agree with a confident response I gave, push back here
in the chat rather than recording a `> C:` for that finding.

Wherever I expressed uncertainty or a question in my response, come
back to me here with your opinion. We will resolve these one by
one, then you'll describe the updates we converge to as `> C:`
comments under mine in the redteam file.

For findings annotated `> M?:` (with the question mark), do not
propose a `> C:` action. Instead, come back to chat to explain the
relevant content — numerical, algorithmic, or performance — at the
level needed to evaluate the finding. The goal is for me to be
able to make a substantive `> M:` annotation in good conscience,
not for you to make the decision. Calibrate the explanation to
what I'd need to evaluate *this finding* — not a generic tutorial.
If the same concept comes up a second time across findings or
across red-team passes, flag that explicitly so we can consider
promoting the explanation to `tutorials/`.

Once the explanation has landed and I've responded with a `> M:`
annotation (no question mark), proceed as you would for any other
confident-instruction finding.

For findings tagged `[test-gap]`: the `> C:` should state that the
finding is being routed to the test red-team queue rather than
acted on here. Do not edit the test file. The routing trigger is
the tag, not your judgement that the test should have caught the
bug.

For findings tagged `[spec-implication]`: the `> C:` should state
that the finding is being routed to the spec red-team queue rather
than acted on here. Do not edit the spec. The routing trigger is
the tag.

Do not edit any artifact yet. This step is only deciding and
recording the decisions in the redteam file.
```

Things to flag about this step that differ from the spec and test
red-team workflows:

- **Up to three target artifacts.** Each `> C:` must say whether the
  change is to the spec, the code, the docs, a doc helper script,
  or a combination. Doc helper scripts (e.g.
  `docs/<spec-id>/_make_call_graph.py`) are a distinct target
  because edits to them imply re-running them to regenerate the
  artifacts they produce.
- **Upstream routing as a third option.** Beyond apply/dismiss, the
  implementation red-team has a third resolution: route the finding
  upstream. The tags `[test-gap]` and `[spec-implication]` mark
  these. The routing is mechanical (tag determines destination), not
  judgemental; the redteam file's `> C:` records the routing for
  the audit trail, and the actual upstream re-run is scheduled
  separately (typically as a new invocation of the corresponding
  workflow, or noted in `meta/workflow-issues.md` if the upstream
  red-team has already happened recently and another pass is not
  warranted).
- **Explicit pushback license**, same as the test red-team: a
  fresh sub-agent can over-flag latent risks and doc omissions in
  particular, and Claude is allowed to disagree with a `> M:` apply
  rather than silently recording a `> C:` for it.
- **Convergence happens in chat.** Uncertainties and `> M?:`
  findings resolve in conversation, then their resolutions are
  written back as `> C:` annotations. The redteam file is the
  durable record.

## Stage 3b — Update the spec (if any)

Only applicable if any finding's `> C:` indicates a spec change
(typically these will be the dismissed `[spec-implication]` findings
where the human and Claude agreed the implementation is right and the
spec needs to catch up, or rare cases where a finding revealed an
under-specified property that should be tightened in the spec rather
than routed back through a full spec red-team).

Paste:

```
Go ahead and make the modifications in [[SPEC_PATH]] for the
findings whose `> C:` annotations indicate a spec change. Apply
red text color (HTML inline spans, see "Notes on red marking"
below) where there is a modification. Revert the status flag of
any affected section(s) back to draft, and add a revision log
entry per skills/write-math-spec.md categorising the changes.

Do not regenerate code or docs yet. The human will re-review the
spec sections before the regeneration runs.
```

The human then re-reviews the affected spec sections and flips the
status flags forward (`draft → reviewed`) as appropriate. Same
direction-asymmetry rule as elsewhere: Claude flips backwards on
revision, the human flips forwards on re-review.

If no finding requires a spec edit, skip directly to stage 3c.

## Stage 3c — Regenerate code, docs, and helper-script artifacts

Once the spec is re-reviewed (or skipped if no spec edits), paste:

```
I've reviewed the spec. If there are things to modify upon
review, do those first. Then:

1. Remove all the red coloring from the spec (the HTML inline
   spans added in stage 3b). The revision log preserves the audit
   trail.

2. Make the code edits in [[CODE_DIR]] for findings whose `> C:`
   indicates a code change.

3. Make the documentation edits in [[DOC_PATH]] for findings whose
   `> C:` indicates a doc change. This includes inline comments,
   design-decisions entries, data-flow / shape annotations, and
   the call-graph or structural documentation.

4. For findings whose `> C:` indicates a change to a doc helper
   script (e.g. [[DOC_DIR]]/_make_call_graph.py), edit the script
   AND re-run it to regenerate the artifact(s) it produces. The
   regenerated artifact is committed alongside the script edit.

5. In experiments/<EXPERIMENT_ID>/CODEGEN_LOG.md, flip the status
   of every code file modified in step 2 to `pending-tests`. Leave
   their last-passing commit hashes intact — they record the
   previous verified version, and stage 3d will update them once
   the rerun confirms the new version.

6. Do not commit yet — the rerun in stage 3d may surface
   additional changes.
```

Stage 3c can produce edits to as many as four artifact kinds (code,
documentation, doc helper scripts, regenerated artifacts from those
scripts). They are made in one pass because they form a coherent
revision — the code change motivates the doc update, which motivates
the helper-script re-run, which produces the regenerated call graph
or similar. Splitting them across commits would obscure the unit of
change.

## Stage 3d — Re-run the eye test and the test suite

Once stage 3c is complete, paste:

```
First, re-run the eye test from
experiments/<EXPERIMENT_ID>/CODEGEN_LOG.md (the test file named in
the eye test status row). Show me where the regenerated figure
went and flip the eye test row's status to `pending review`. Wait
for my approval before continuing.

Once I've confirmed the eye test still passes, flip the eye test
row's status to `passed (<initial>, <date>)`, then re-run the
full test suite one-by-one. After each test passes, edit
experiments/<EXPERIMENT_ID>/CODEGEN_LOG.md with the commit hash
that identifies the code version that last passed that test. If
any test fails, come back to me with a report about that failure
— do not attempt to fix it yourself. We'll decide jointly.

Once all tests pass and the per-test hashes are updated, flip the
status of every code file currently at `pending-tests` (set in
stage 3c) back to `done`. Then commit the changes together with a
message referencing the redteam pass.
```

The eye test runs first because it's the cheap human-judgement
check: if the red-team edits broke something visually obvious, you
want to catch that before walking the full suite. If the eye test
fails on the rerun, the failure routes the same way as a test
failure (see the test-failure branch below) — the rerun is paused,
the cause is decided jointly, the fix is applied, and the rerun
restarts from the eye test.

The one-by-one rerun is intentional. A bulk rerun would tell you
*that* something broke but not give you a per-test commit hash to
bisect against. The `CODEGEN_LOG.md` per-test hash is the audit
trail for which code version last verified each property; it lets
future regressions be located precisely.

If a test (eye test or full-suite test) fails on the rerun, the
failure is reported back and decided jointly. The failure can mean
three things and the workflow does not pre-commit to which:

- The edit was wrong. Return to the relevant `> C:` and re-decide;
  the redteam file gets a follow-up `> M:` and `> C:` recording the
  correction.
- A new finding has emerged that the red-team missed. Add it to the
  redteam file as F_n+1 with an appropriate tag, triage it the same
  way as the others.
- A test is wrong. Tag the failure `[test-gap]` and route it to the
  test red-team queue, same routing as during the original triage.

Whichever branch, the resolution is recorded in the redteam file
and the rerun is restarted — from the eye test if it was the eye
test that failed, or from the failed test if it was a full-suite
test.

## Notes on red marking

Same convention as the spec and test red-team workflows. Use HTML
inline spans (`<span style="color: red">revised text</span>`) for
word-level edits and `> [!warning]` callouts for larger revisions.
Red marking is removed in stage 3c after the human re-reviews; the
revision log preserves the audit trail.

## Notes on math or numerical explanations triggered by `> M?:`

Same convention as the spec and test red-team workflows. The first
time a concept is raised via `> M?:`, the explanation lives in chat
and the `> M:` annotation references it (e.g., "after the chat
explanation of the running-cov precision tradeoff, dismiss"). The
second time the same concept is raised across findings or red-team
passes, promote the explanation to a file in `tutorials/`, calibrated
to this project's specific uses. Tutorial files belong in
`tutorials/` with names like `running-covariance-precision.md` or
`einsum-batched-outer-products.md`, and the file should say at the
top which red-team finding(s) prompted it.

## What this does

The five stages produce, in order:

1. A redteam file with the sub-agent's raw findings, including
   `[test-gap]` and `[spec-implication]` routing tags where
   applicable.
2. An annotated redteam file with the human's `> M:` (and `> M?:`)
   reactions inline.
3a. The redteam file fully annotated with `> C:` decisions for every
   finding, recording for each whether it touches the spec, the
   code, the docs, a doc helper script, or is being routed upstream.
3b. (If applicable) A revised spec with red-marked changes, status
   flipped on affected sections, and a revision log entry.
3c. Code edits, doc edits, doc helper script edits, regenerated
   artifacts from those scripts, and modified code files flipped
   to status `pending-tests` in `CODEGEN_LOG.md`.
3d. An eye-test rerun (when an eye test is defined for the
    experiment) re-approved by the human, a full test suite rerun
    with per-test commit hashes logged in
    `experiments/<EXPERIMENT_ID>/CODEGEN_LOG.md`, modified code
    files flipped back to status `done` once all tests pass, and
    a single commit bundling the revision.

The redteam file is a complete audit trail: what was flagged, what
the human thought, what was done, which artifact each change
touched, and where routed findings went. Future readers can
reconstruct the reasoning.

## What this is *not* for

- Red-teaming the spec itself, the tests, or experiment writeups.
  Those have their own sibling workflows
  (`invoke-red-team-on-spec`, `invoke-red-team-on-tests`, and
  forthcoming `invoke-red-team-on-result`).
- Acting on `[test-gap]` or `[spec-implication]` findings in place.
  Those route upstream and are handled by their respective
  workflows.
- Re-running the implementation red-team after a revision. The
  current convention is "one implementation red-team per
  spec-implementation pair, run when the implementation passes the
  red-teamed test suite and the docs are in place." If a
  substantial revision warrants a second red-team pass, that's a
  judgement call; the workflow doesn't prescribe re-runs.
- Maintaining `CODEGEN_LOG.md` outside of stage 3d. The log is
  updated here because this is the workflow that establishes a
  verified per-test code version. Other workflows that touch tests
  or code update the log per their own conventions.

## Related

- `skills/red-team-implementation.md` — the procedure the sub-agent
  follows, plus the annotation conventions and the routing-tag
  semantics.
- `skills/write-math-spec.md` — the status table, revision log,
  downstream-approval rules referenced in stage 3b.
- `workflows/invoke-red-team-on-spec.md` and
  `workflows/invoke-red-team-on-tests.md` — the sibling workflows
  this one parallels; they share the `> M:` / `> C:` annotation
  convention, the `> M?:` chat-then-tutorial convention, the
  red-marking convention, and the do-not-pre-filter convention.
  Findings tagged `[spec-implication]` route to the spec workflow;
  findings tagged `[test-gap]` route to the test workflow.
- `AGENTS.md` — the red-teaming section that names this as a
  required step.
- `workflows/wake-up-claude-code.md` — must be done before this
  workflow can run.
