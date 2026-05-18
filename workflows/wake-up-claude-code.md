# Workflow: wake-up-claude-code

> Standard session-opening prompt for Claude Code (desktop panel or
> CLI). Restores context so Claude Code can act on current conventions
> and current state of the repo.

## When to use

At the start of a Claude Code session — either a brand new session, or
one resumed after enough time has passed that context might have
slipped. Not needed if you're picking up the same Code session from a
few minutes ago.

## Prerequisites

- `AGENTS.md` is current.
- `meta/workflow-issues.md` has been kept up to date.
- `meta/handoff.md` was written at the end of the previous session,
  or is recent enough to be relevant.
- The skill(s) relevant to today's task are in `skills/`.

If any of these are stale, edit them before starting Claude Code —
or note the staleness inline in the prompt (see "When something is
stale" below).

## The prompt

```
Continuing work on dynamic_infomax. Read in order:

1. AGENTS.md — current conventions for this project.
2. meta/workflow-issues.md — known meta-level open items; skim for
   anything relevant to today's task.
3. meta/handoff.md — where we left off last session.
4. The current artifact being worked on: [[CURRENT_ARTIFACT_PATH]]
5. The skill(s) governing today's work: [[RELEVANT_SKILL_PATHS]]

After reading, summarise your understanding in two short paragraphs:
(a) what state the project is in, and (b) what the immediate task is.
Wait for me to confirm before taking any action.

Then today's task is: [[TASK_DESCRIPTION]]

All work should be done on the main branch, and no other branch or worktree should be created without explicit instruction by the human. If there is a worktree auto-created by the harness at session start, before you do anything, switch back to the main branch and tear down the worktree.
```

## When something is stale

If `meta/handoff.md` is known to be inaccurate (e.g., the editor
question is resolved, a referenced file has been renamed), add an
inline correction to the prompt rather than fixing the handoff first:

```
[...standard prompt above...]

Note: the handoff is stale on [specific point] — the correct state is
[corrected statement]. Rely on the current files, not the handoff,
where they conflict.
```

This is acceptable in the moment. End-of-session, update the handoff
itself so the next session doesn't need the correction.

## What this does

Claude Code reads the four+ files in sequence, building a mental
model of project state. The "summarise before acting" step is
deliberate — it surfaces misalignments between what Claude Code thinks
the state is and what the state actually is, *before* any tool calls
that might compound a misunderstanding.

After confirmation, Claude Code is in the right context to execute
the task. If the summary is wrong, correct it and re-summarise
before proceeding.

## Common task descriptions

A few task patterns that come up repeatedly. These are not full
workflows but sentence-templates for the `[[TASK_DESCRIPTION]]` slot:

- **Apply a small revision**: "I've reviewed section X of the spec
  and need a small revision: [the change]. Apply it, add a Revision
  log entry categorising as Correction/Clarification/Refinement per
  `skills/write-math-spec.md`, and flip the affected section's status
  back to draft."

- **Begin downstream work after a section is approved**: "Section X
  is now reviewed. Per the downstream-approval rules in
  `skills/write-math-spec.md`, [next step it unlocks] is now
  permitted. Proceed with [next step]."

- **Invoke a red-team pass**: see the (forthcoming)
  `workflows/invoke-red-team-on-spec.md`.

## Related

- `AGENTS.md` — particularly the "Session start" subsection.
- `skills/write-math-spec.md` — the per-section status table and
  downstream-approval rules.
- `workflows/wake-up-claude-chat.md` — the equivalent for
  chat.claude.ai sessions.
- (forthcoming) `workflows/close-session.md` — the bookend to this
  workflow.
