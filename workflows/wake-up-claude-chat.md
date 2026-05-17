# Workflow: wake-up-claude-chat

> Standard session-opening prompt for chat.claude.ai sessions
> (browser, desktop app, or mobile). Restores context so Claude can
> reason about the project with current conventions and state.

## When to use

At the start of a new claude.ai chat session about this project, or
when continuing in a session that has been dormant long enough that
context might have slipped. Not needed within an active conversation.

## Prerequisites

- The repo is at https://github.com/mihalybanyai/dynamic_infomax (or
  whatever the public URL is — update this workflow if the repo
  moves).
- `AGENTS.md`, `meta/workflow-issues.md`, and `meta/handoff.md` are
  reasonably current.
- If specific files need to be reviewed in this session, they exist
  in the repo.

## The prompt

```
Continuing work on dynamic_infomax. Repo is at
https://github.com/mihalybanyai/dynamic_infomax. Please read
AGENTS.md, meta/workflow-issues.md, meta/handoff.md, and
[[ACTIVE_ARTIFACT_PATH(S)]], then we'll start with
[[NEXT_STEP_DESCRIPTION]].
```

## When the chat-Claude can't read the repo

Some of Claude's web-reading tools are blocked by GitHub's robots.txt
on certain paths. If Claude reports it can't fetch a meta/ or specs/
file, the fallback is:

1. Open the relevant files in VSCode (or wherever).
2. Paste the contents into the chat as attached files or as inline
   content.

For the minimum-viable wake-up, the spec being worked on is the most
important attachment. `AGENTS.md` and `meta/handoff.md` are recent
enough in the project's history that an earlier conversation usually
gives the chat-Claude enough orientation without re-reading them.

## What this does

Claude (chat) reads the repo state and orients to current conventions.
Unlike Claude Code, chat-Claude has no automatic access to the repo —
it has to fetch the URLs in the prompt, and its web-fetch tools may
not work on all GitHub paths. The prompt is structured so the most
important file (the current artifact) is named explicitly, in case
the meta/ files can't be fetched.

After reading, chat-Claude can be asked design and review questions,
help triage red-team findings, draft prompts for Claude Code, and so
on. It cannot directly edit files — that's Claude Code's role.

## What this is *not* for

- Continuing an existing active chat. Just keep typing.
- Voice sessions. Voice mode has no file access; treat voice sessions
  as scratchpad work that gets pinned to the repo later via a text
  session.

## Related

- `workflows/wake-up-claude-code.md` — the equivalent for Claude Code
  sessions, with stricter context-building since Code will edit
  files.
- `meta/handoff.md` — the artifact this workflow is built around.
- (forthcoming) `workflows/close-session.md` — the end-of-session
  bookend.
