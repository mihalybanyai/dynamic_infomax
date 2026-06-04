# Workflow: invoke-red-team-on-spec

> Three-stage workflow for red-teaming a spec: trigger the red-team
> sub-agent, get the resulting report, then process findings to either
> apply or dismiss each one. Designed to give the human meaningful
> control over judgement calls while delegating mechanical edits.

## When to use

When a spec in `specs/` has all sections at status `reviewed` and is
ready for the red-team pass per the convention in `AGENTS.md`. This is
the gate between "human-reviewed" and "approved for downstream work
that depends on the whole spec."

Do not invoke if any section is still `draft` or `needs-revision` —
the red-team pass should run against a stabilised artifact.

## Prerequisites

- The spec has all sections at status `reviewed`.
- `skills/red-team-spec.md` exists and is current.
- Source papers and any references the spec cites are available
  either as PDFs in `resources/` or as findable links in
  `resources/references.md` (or equivalent annotated bibliography).
- Claude Code session is open and oriented to the project (see
  `workflows/wake-up-claude-code.md`).
- The session is running an **approved red-teamer model at the highest
  effort tier** (see the roster in `AGENTS.md`). The sub-agent inherits
  both from this session. You do not have to get this right before
  triggering: the spawn-configuration gate (`skills/red-team-spec.md`)
  pauses for your confirmation first, so a misconfigured session can be
  fixed there — re-trigger from a correctly-set session, a separate
  thread if you want a different model version.

## Stage 1 — Invoke the sub-agent

Paste into Claude Code:

```
All sections of [[SPEC_PATH]] are now reviewed. Per
skills/red-team-spec.md, invoke the red-team-spec skill: first run the
spawn-configuration gate (print the reviewer roster with its
Last-verified date and the model/effort caveats, then wait for my
explicit "go"); only after I reply "go", spawn a sub-agent with the
adversarial prompt in the skill, give it the
spec and any files the spec references (PDFs in resources/, daft
PGMs in diagrams/, anything else cited in the spec's References
section), and have it write findings to
[[SPEC_PATH_WITHOUT_EXT]]-redteam.md in the format the skill
specifies.

Primary sources for this spec are in resources/. A reading list with
DOIs and stable links for other references is at
resources/references.md (or equivalent). Use the PDFs for any
verification that depends on a source paper. For other references,
look them up only if a finding specifically requires verifying a
derivation from them; do not preemptively ingest the whole
bibliography.

Do not read the findings yourself or pre-filter them — just commit
the file when the sub-agent is done.
```

**The spawn-configuration gate runs first.** Before any sub-agent is
spawned, Claude Code prints the reviewer roster from `AGENTS.md` with its
Last-verified date and the model/effort inheritance caveats, then waits.
Replying "go" both authorises the spawn and ratifies the roster as
current — Claude Code refreshes its Last-verified date to today. If the
roster is stale (a newer model shipped, a tier changed) or the session is
on the wrong model/effort, stop at the gate, fix it, and re-trigger. This
is the **only** point at which the effort tier is checked — it is not
machine-verifiable — so do not reflexively "go" past it.

The "do not pre-filter" clause matters: if the main Claude Code agent
reads the sub-agent's output and silently drops findings it judges
spurious, the fresh-context value of the red-team is lost. Findings
land raw, then the human triages.

## Stage 2 — Annotate the report

Open the resulting redteam file. For each finding, append a response
in the file itself using the `> M:` (mihaly, or whoever the human is)
prefix:

```markdown
### F3: Some title [severity: medium]

**Location**: §1.4

**Concern**: ... (as written by the sub-agent)

**What would resolve it**: ... (as written by the sub-agent)

> M: Yes — apply the fix the sub-agent suggested. The unstated
> assumption is real and the wording is fine.

> M: Not sure about this one. Is the assumption actually load-bearing,
> or could the derivation go through without it? Let's discuss.

> M: Disagree, dismiss. The concern conflates the population
> distribution with the empirical one; §1.2 already handles this.

> M?: I don't have a feel for whether the suggested subgradient
> step is genuinely equivalent to the original differentiation, or
> only equivalent in the non-degenerate case. Need to understand
> this before I can apply or dismiss.
```

Conventions for `> M:` responses:

- **Confident apply**: state what to apply. Be specific if the
  sub-agent's suggestion needs amendment.
- **Confident dismiss**: explain why. Brief is fine; the explanation
  becomes audit trail.
- **Uncertain**: ask a question, or state the ambiguity. These will
  be discussed before resolution.
- **Not equipped to evaluate**: prefix with `> M?:` (note the
  question mark) rather than `> M:`. Use this when the finding
  touches math you don't yet command well enough to apply or
  dismiss in good conscience. This is distinct from "uncertain"
  (which means you understand the question but don't know the
  answer): `> M?:` means you're not sure you understand the
  question. Findings annotated `> M?:` will be discussed in chat
  in stage 3a before any `> C:` resolution is recorded.

There's no required template — natural prose works. The `> M:` prefix
is just for greppability and visual separation.

## Stage 3a — First pass: apply the confident decisions

Paste into Claude Code:

```
The red team report at [[REDTEAM_PATH]] has been annotated with my
responses (prefixed `> M:`). Process it as follows:

For each finding where I gave a confident instruction (apply or
dismiss):
- Apply or dismiss as instructed.
- If applied: edit the spec in the relevant section, mark the edited
  text in red (using HTML span tags, see "Notes on red marking"
  below). Flip the relevant section's status row back to draft. Add
  a revision log entry to the spec, categorising per
  skills/write-math-spec.md.
- In the redteam file, append below my response a sentence prefixed
  with `> C:` confirming what you did (e.g., "> C: Applied as
  suggested in commit a3f4d12, section §1.4 status flipped to
  draft."). Use two newlines before the `> C:` for separation.

For each finding where I expressed uncertainty or asked a question:
- Do not edit the spec yet.
- Come back to me here with your opinion or answer on each
  uncertain item. Number them by the finding ID so I can respond by
  ID.

For findings annotated `> M?:` (with the question mark), do not
propose a `> C:` action. Instead, come back to chat to explain the
relevant math at the level needed to evaluate the finding. The goal
is for me to be able to make a substantive `> M:` annotation in
good conscience, not for you to make the decision. Calibrate the
explanation to what I'd need to evaluate *this finding* — not a
generic tutorial. If the same concept comes up a second time across
findings or across red-team passes, flag that explicitly so we can
consider promoting the explanation to `tutorials/`.

Once the explanation has landed and I've responded with a `> M:`
annotation (no question mark), proceed as you would for any other
confident-instruction finding.

Do not commit until all confident-decision edits are made; commit
them together with a message referencing the redteam pass.
```

## Stage 3b — Second pass: resolve uncertain findings

After Claude Code returns with opinions on the uncertain items,
respond by finding ID:

```
F1: <decision and any wording specifics>
F4: <decision>
F11: <decision, including any reference or detail to add>
F12: <decision>

Describe these decisions in the red team report file in `> C:`
comments below the appropriate issues. Then make the edits in the
spec in red, flipping status where appropriate, and adding the
revision log entries. Commit when done.
```

The naming convention "F1, F4, ..." comes from the red-team report's
own finding numbering. Use the same IDs the report uses.

## Notes on red marking

The spec is markdown. Markdown has no native red-text syntax. Three
options for marking revised content:

1. **HTML spans inline**: `<span style="color: red">revised text</span>`.
   Renders in most markdown viewers (VSCode preview, Obsidian, GitHub
   web view). Diffs cleanly.
2. **Block-level callouts**: a `> [!warning]` callout containing the
   revised text. Standout visually but heavier — better for big
   revisions than for word-level edits.
3. **A "revised" CSS class** for tools that support it. Most do not;
   skip this unless you have a reason.

Default to option 1 (inline HTML span) unless a revision is large
enough to warrant a callout. After the next post-revision review of
the section flips its status back to `reviewed`, the red marking can
be removed in the same edit — the revision log preserves the audit
trail.

## Notes on math explanations triggered by `> M?:`

The first time a `> M?:` is raised on a concept, the explanation
lives in the chat session. If a `> M:` annotation in the redteam
file references the explanation (e.g., "after the chat explanation
of Lagrangian duality, apply"), the audit trail remains complete —
the chat is ephemeral but the decision lives in the redteam file.

The second time the *same concept* is raised across findings or
red-team passes, promote the explanation to a file in `tutorials/`,
calibrated to this project's specific uses. The trigger is "this
came up twice", not "this seems important" — the former is data,
the latter is forecasting. A 1-page calibrated tutorial against the
project's own derivations is more valuable than a generic
textbook-style chapter; resist the temptation to be comprehensive.

Tutorial files belong in `tutorials/` alongside the existing
infrastructural notes, with names like `lagrangian-duality.md`,
`mutual-information-decompositions.md`, etc. The file should say
at the top which red-team finding(s) prompted it, so the audit
trail back to the originating decision is preserved.

## What this does

The three stages produce, in order:

1. A redteam file with the sub-agent's raw findings.
2. An annotated redteam file with the human's `> M:` reactions
   inline.
3. A revised spec with status flipped on affected sections, a
   revision log capturing the changes, and the redteam file
   additionally annotated with `> C:` confirmations of each
   resolution.

After stage 3b, the spec is in a state where:
- Affected sections need to be re-reviewed by the human (the
  `draft → reviewed` flip per `skills/write-math-spec.md`).
- Once re-reviewed, downstream work can resume against the revised
  sections.
- The redteam file is a complete audit trail: what was flagged,
  what the human thought, what was done. Future readers (labmates,
  reviewers, future-you) can reconstruct the reasoning.

## What this is *not* for

- Red-teaming code, tests, or experiment writeups. Those have their
  own sibling skills (`red-team-tests`, `red-team-implementation`,
  `red-team-result`) and will likely warrant sibling workflows once
  they've been exercised.
- Re-running red-team after a revision. The current convention is
  "one red-team per spec, run when the spec is fully reviewed." If
  a substantial revision warrants a second red-team pass, that's a
  judgement call; the workflow doesn't prescribe re-runs.

## Related

- `skills/red-team-spec.md` — the procedure the sub-agent follows.
- `skills/write-math-spec.md` — the status table, revision log,
  downstream-approval rules.
- `AGENTS.md` — the red-teaming section that names this as a
  required step.
- `workflows/wake-up-claude-code.md` — must be done before this
  workflow can run.
