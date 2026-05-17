# workflows/

Reusable prompts that orchestrate multiple skills, conventions, or
external steps into a single triggerable action. Pasted at the start
of a session (or at the moment a recurring workflow is invoked) to
get a consistent result without re-deriving the prompt each time.

## What belongs here

A prompt earns a workflow file when:

1. It composes multiple skills or conventions (no single skill covers
   the whole thing).
2. It is expected to recur — at least once a week, or once per session
   of some kind.
3. The prompt itself contains substantive content beyond "follow skill
   X on artifact Y". (If a prompt is just a thin wrapper around a
   single skill, the right place for the invocation pattern is inside
   the skill's "How to invoke" section, not here.)

## What does *not* belong here

- One-off prompts for ad-hoc tasks (spec migration, a specific
  refactor, etc.). These are conversational and don't recur in the
  same shape.
- Thin wrappers around a single skill. Edit the skill instead.

## File convention

Each workflow is one markdown file named with a verb-noun pattern
(e.g. `wake-up-claude-code.md`, `invoke-red-team-on-spec.md`).
This distinguishes workflow files from skill files in `skills/`
(which use noun or noun-noun, e.g. `red-team-spec.md`).

Each file has this structure:

```markdown
# Workflow: <name>

> One-line description of what this workflow accomplishes.

## When to use

Specific conditions. "At the start of a new chat with Claude on
claude.ai" is better than "when starting work".

## Prerequisites

What must be true for the workflow to make sense (files exist,
artifacts are in a particular state, etc.).

## The prompt

The actual text to paste. Template slots are marked with double
square brackets, e.g. `[[CURRENT_SPEC_PATH]]`.

## What this does

Short narrative of what should happen after the prompt is sent.
Useful for verifying the workflow ran correctly.

## Related

Links to skills the workflow invokes, AGENTS.md sections it relies
on, other workflows it composes with.
```

## Current workflows

- `wake-up-claude-code.md` — session start for Claude Code (desktop
  panel or CLI)
- `wake-up-claude-chat.md` — session start for chat.claude.ai

## Maintenance

Workflows are durable but not sacred. When a workflow's content drifts
from current conventions (e.g., AGENTS.md is renamed, a new convention
is added that workflows should reference), update the workflow.
Workflows that haven't been used in a long time should be reviewed
for staleness or removed.
