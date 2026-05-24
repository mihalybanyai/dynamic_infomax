# Workflow: invoke-red-team-on-result

> Multi-stage workflow for red-teaming an experimental result: trigger
> the red-team sub-agent, then process findings to apply, dismiss, or
> route each one upstream. Differs from the spec, test, and
> implementation red-team workflows in two ways. First, this is the
> last red-team in the pipeline, so findings can in principle route
> back to *any* earlier artifact (spec, tests, implementation, or the
> implementation's documentation); the processing begins with an
> explicit first-pass check for whether any finding forces a return to
> an earlier stage. Second, "downstream" here is the experiment's own
> `run.py`, its regenerated figures, and the `REPORT.md` prose; the
> processing ends with a re-read of the report by the human before
> the final commit.

## When to use

When an experiment in `experiments/NNN-*/` has been run, its figures
and `REPORT.md` are written, and all upstream artifacts are at their
post-red-team states (spec `reviewed`, test suite post-red-team,
implementation post-red-team, implementation docs post-red-team).
This is the gate between "the experiment ran cleanly and produced a
report" and "the result is established and can be cited by downstream
work."

Do not invoke if any of the prerequisites below are missing — the
result red-team pass should run against a fully stabilised upstream
chain. Findings against a still-moving spec or implementation are
worse than no findings, because they conflate "the result is wrong"
with "the artifact the result was produced against has since changed."

## Prerequisites

- All relevant sections of the spec are at status `reviewed` and have
  been through `invoke-red-team-on-spec`.
- The test suite has been through `invoke-red-team-on-tests` and is
  at its post-red-team state.
- The implementation has been through `invoke-red-team-on-impl` and
  is at its post-red-team state. The implementation passes the full
  test suite at HEAD.
- The implementation's documentation in `docs/<spec-id>/` is at its
  post-red-team state, current with the implementation.
- The experiment has been run end-to-end and produced its figures
  and `REPORT.md`. The `provenance.json` in the experiment's
  `output/` records the exact commits, seed, and package versions
  used.
- `skills/red-team-result.md` exists and is current.
- Claude Code session is open and oriented to the project (see
  `workflows/wake-up-claude-code.md`).

## Stage 1 — Invoke the sub-agent

Paste into Claude Code:

```
The experiment at [[EXPERIMENT_DIR]] has been run and the report is
in place at [[EXPERIMENT_DIR]]/REPORT.md. Per
skills/red-team-result.md, invoke the red-team-result skill: spawn
a sub-agent with the adversarial prompt in the skill, give it the
plan, the experiment code, the report (including figures), and
pointers to the relevant spec, test suite, implementation, and
provenance.json, and have it write findings to
[[EXPERIMENT_DIR]]/redteam-result.md in the format the skill
specifies.

Tell the sub-agent the context explicitly: the spec is at status
`reviewed` across all relevant sections, the test suite has been
red-teamed, the implementation passes all tests and has itself been
red-teamed, and the implementation's documentation has been
red-teamed. So the sub-agent is NOT auditing the math (settled),
NOT auditing test coverage against the spec (settled), and NOT
auditing the implementation against the spec (settled). Its job is
the gap between "the code ran cleanly and produced numbers/figures"
and "the result, as written up in the report, actually supports the
claim the report makes."

The sub-agent should read the spec and the plan first, then the
report (including the figures), and only then the code (this order
is in the skill, but worth restating). Findings ordered by
descending severity, with the checklist categories as the secondary
order key. Numbered F1, F2, ... after ordering. Routing tags
`[spec-implication]`, `[test-gap]`, and `[code-implication]`
applied where appropriate per the skill.

Do not read the findings yourself or pre-filter them — just commit
the file when the sub-agent is done.
```

The "do not pre-filter" clause matters: if the main Claude Code
agent reads the sub-agent's output and silently drops findings it
judges spurious, the fresh-context value of the red-team is lost.
Findings land raw, then the human triages.

## Stage 2 — Annotate the report

This stage is the human's alone — no Claude action.

Open the resulting `redteam-result.md`. For each finding, append a
response in the file itself using the `> M:` (or appropriate
initial) prefix. Two newlines separate the response from the
finding above. Conventions:

- **Confident apply**: state what to apply. Example:
  `> M: Confirmed; rerun with 5 seeds and report mean ± SE.`
- **Confident dismiss**: explain why. Example:
  `> M: Out of scope for this experiment — the baseline named here
  > is the topic of experiment 002.`
- **Uncertain**: ask a question or state the ambiguity, with a
  hypothesis if possible. Example:
  `> M: Possible but I'm not sure the effect would be visible at
  > this sample size; thoughts?`
- **Not equipped to evaluate**: prefix with `> M?:` (note the
  question mark) rather than `> M:`. Use this when the finding
  turns on statistical or mathematical reasoning the human does
  not yet command well enough to apply or dismiss in good
  conscience. This is distinct from "uncertain" (which means the
  human understands the question but does not know the answer):
  `> M?:` means "I'm not sure I understand the question." Findings
  annotated `> M?:` will be discussed in chat in stage 3a before
  any `> C:` resolution is recorded.

The human is also responsible for noticing routing tags applied by
the sub-agent (`[spec-implication]`, `[test-gap]`,
`[code-implication]`) and for forming a preliminary view, per
finding, on whether the routing is correct. Disagreement with the
routing belongs in the `> M:` annotation: e.g.,
`> M: Disagree with [test-gap] — this is really a [spec-implication]
> because the spec under-specifies the windowing convention.`

The convention is that even confident `> M:` items are open to
pushback from Claude in stage 3a (see below). Mark applies that you
are *especially* sure about with an explicit "no pushback please"
or similar; otherwise expect Claude to push back where it disagrees.

## Stage 3 — Resolve

Stage 3 has four sub-stages. They correspond to: (3a) deciding what
to do, including the global "do we need to return to an earlier
stage of the workflow?" check; (3b) updating upstream artifacts via
their respective workflows for accepted routed findings, if any;
(3c) applying the in-experiment edits to code, figures, and report;
(3d) re-reading the report and finalising.

### Stage 3a — Decide what changes to make

Paste into Claude Code:

```
Process the red-team report on the result at
[[EXPERIMENT_DIR]]/redteam-result.md, which I've already annotated.
We will be doing this as a four-step process. The current step is
the first: decide what changes to make.

Before walking the findings individually, address the global
question: do any findings, in aggregate or individually, force a
return to an earlier stage of the workflow — redrafting the spec,
regenerating the test suite, regenerating the implementation, or
regenerating the documentation? If yes, surface that here in chat
before per-finding processing so we can discuss the scope of the
return.

If no global return is needed, walk the findings one-by-one, top-down
by severity. For each finding:

- If I gave a confident `> M:` instruction and you agree, describe
  the modification in the redteam file under my response: add a
  `> C:` annotation (two newlines before) stating which
  artifact(s) the change touches — the report, the experiment
  code, a figure (regenerated), an upstream artifact via a routing
  tag, or none (dismissed / accepted as limitation).
- If I gave a confident `> M:` instruction and you disagree, push
  back here in chat. We resolve, then you write the agreed
  resolution as a `> C:` in the file.
- Wherever I expressed uncertainty or asked a question in my `> M:`
  response, come back to me here with your opinion so we can
  resolve.
- For findings annotated `> M?:` (with the question mark), do not
  propose a `> C:` action. Instead, come back to chat to explain
  the relevant math or statistics at the level needed to evaluate
  the finding. Calibrate the explanation to what I'd need to
  evaluate *this finding* — not a generic tutorial. If the same
  concept comes up a second time across findings or across
  red-team passes, flag that explicitly so we can consider
  promoting the explanation to `tutorials/`. Once the explanation
  has landed and I respond with a `> M:` (no question mark),
  proceed as for any other confident-instruction finding.
- For findings tagged `[spec-implication]`, `[test-gap]`, or
  `[code-implication]` that we accept, the `> C:` records the
  routing rather than an in-place edit; the actual change happens
  in stage 3b via the corresponding upstream workflow.

We resolve issues one by one here, and then you describe the
agreed updates in the file in `> C:` comments under mine. After
this is complete, we will make the edits to the experiment code,
rerun the experiment if needed, regenerate the report figures,
and edit the report text. Don't start those yet.
```

### Stage 3b — Update upstream artifacts (if applicable)

If stage 3a determined that one or more findings force a return to
an earlier stage of the workflow, or if any routing-tagged findings
were accepted, those go through their corresponding upstream
workflows now. Hand off rather than acting in place:

- `[spec-implication]` accepted → re-open the relevant spec
  section(s); the actual edits go through
  `workflows/invoke-red-team-on-spec.md` or its post-red-team
  revision pattern (whichever is appropriate given how far
  upstream the return goes). If the spec change is substantial
  enough that the test suite or implementation also need to be
  regenerated, that cascade is handled by the spec workflow's
  downstream-approval rules.
- `[test-gap]` accepted → re-open the test red-team via
  `workflows/invoke-red-team-on-tests.md`. The test suite is
  regenerated through that workflow.
- `[code-implication]` accepted → re-open the implementation
  red-team via `workflows/invoke-red-team-on-impl.md`, or, for
  small scoped bug fixes, just open the per-bug
  "failing-test-first-then-fix" loop directly with Claude Code per
  `skills/red-team-implementation.md`.

In the simplest case (stage 3a determined no upstream return is
needed and no routing tags were accepted) this stage is empty and
the workflow proceeds directly to 3c.

Once the upstream re-stabilisation is complete, return here. The
remaining sub-stages run against the new upstream state.

### Stage 3c — Apply: edit the code, rerun, edit the report

Paste into Claude Code:

```
I confirm your suggestions for all issues. Write the `> C:` notes
in the redteam file (use two newlines before each one), and go
ahead to make the edits to the experiment code per the agreed
`> C:` actions. Rerun the experiment if any code or seed changed,
regenerate the affected figures, and edit the report text as
needed.

Wherever you edit the report, mark the changed regions in red so
I can see the diff visually on re-read. Use the same red-marking
convention as the spec and test red-team workflows: HTML inline
spans <span style="color:red">...</span> for prose, and either an
adjacent caption note or a red border on regenerated figures.

Update the experiment's provenance.json (or whatever
provenance-tracking artifact lives in [[EXPERIMENT_DIR]]/output/)
to record the new commit hash and any changed package versions.

Commit each `> C:` action's edits as you go, with messages
referencing the finding number (e.g., "F3: add constant-predictor
baseline"). Leave the red-marking-removal commit for the next
stage.
```

The per-finding commit cadence matters: it produces a clean history
where each commit corresponds to one finding's resolution, and
makes the redteam file's `> C:` annotations honest indicators of
what was changed when.

### Stage 3d — Finalise: re-read, remove red, commit

The human re-reads the report with the red markings still in
place. This is the gate: if the red-marked changes do not actually
say what the human wanted them to say, return to 3c with specific
edits. Only when the red-marked report reads correctly does this
stage proceed.

Paste into Claude Code:

```
Looks good. Now remove all the red markings from the report and
commit the cleanup. Use the same red-removal convention as the
spec and test red-team workflows: strip the HTML spans / caption
notes / figure borders, leaving the underlying text and figures
intact.

Update the experiment's README (or REPORT.md, as relevant) to
record the redteam findings' resolution status, per the
result-skill convention: list high-severity findings and their
resolution, or note any that remain outstanding with a pointer to
the follow-up.
```

If a finding was *accepted as a limitation* rather than fixed,
the report's resolution section explicitly states the limitation
and the justification for accepting it. This is the audit trail's
record that the finding was considered, not missed.

## What this does

The four stages produce, in order:

1. A `redteam-result.md` with the sub-agent's raw findings,
   including `[spec-implication]`, `[test-gap]`, and
   `[code-implication]` routing tags where applicable.
2. An annotated `redteam-result.md` with the human's `> M:` (and
   `> M?:`) reactions inline.
3a. The redteam file fully annotated with `> C:` decisions for
   every finding, recording for each whether it touches the
   report, the experiment code, a figure, an upstream artifact via
   a routing tag, or none. Includes the global "do we need to
   return upstream?" decision.
3b. (If applicable) Updated upstream artifacts via their respective
   workflows. Empty in the simplest case.
3c. In-experiment code edits, regenerated figures from a rerun, and
   report edits with the changed regions marked in red. Per-finding
   commits.
3d. The red-marking removed, the report's resolution-status section
   updated, and a single cleanup commit closing out the workflow.

The redteam file is a complete audit trail: what was flagged, what
the human thought, what was done, which artifact each change
touched, and where routed findings went. Future readers can
reconstruct the reasoning.

## What this is *not* for

- Red-teaming the spec, the tests, or the implementation. Those
  have their own sibling workflows (`invoke-red-team-on-spec`,
  `invoke-red-team-on-tests`, `invoke-red-team-on-impl`).
- Acting on `[spec-implication]`, `[test-gap]`, or
  `[code-implication]` findings in place. Those route upstream
  and are handled by their respective workflows in stage 3b.
- Re-running the result red-team after a revision. The current
  convention is "one result red-team per experiment, run when the
  report is in place and all upstream artifacts are at their
  post-red-team states." If a substantial revision warrants a
  second red-team pass — e.g., the experiment was re-run with a
  materially different protocol — that's a judgement call; the
  workflow doesn't prescribe re-runs.
- Approving the result. The red-team is what grants approval; this
  workflow only gets the result through the audit.

## Related

- `skills/red-team-result.md` — the procedure the sub-agent
  follows, plus the annotation conventions and the routing-tag
  semantics.
- `skills/write-math-spec.md` — the status table, revision log,
  downstream-approval rules referenced when `[spec-implication]`
  findings are accepted.
- `workflows/invoke-red-team-on-spec.md`,
  `workflows/invoke-red-team-on-tests.md`, and
  `workflows/invoke-red-team-on-impl.md` — the sibling workflows
  this one parallels; they share the `> M:` / `> M?:` / `> C:`
  annotation convention, the red-marking convention, and the
  do-not-pre-filter convention. Stage 3b dispatches to them for
  accepted routed findings.
- `AGENTS.md` — the red-teaming section that names this as a
  required step.
- `workflows/wake-up-claude-code.md` — must be done before this
  workflow can run.
