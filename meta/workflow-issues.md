# Workflow issues and improvements

Tracks meta-level issues with the project's workflow itself — things to
fix, reconsider, or add to the conventions. For research and code issues,
use GitHub Issues on the repo.

## Conventions

- Every entry has: a short title, status, date opened, category, and a
  paragraph of context.
- Status: `open` / `in-progress` / `resolved` / `dismissed`.
- Categories: `bootstrap`, `skills`, `conventions`, `tooling`, `meta`.
- Resolved and dismissed entries stay in the file with a resolution
  note — they are the project's institutional memory.

## Review cadence

Skim this file at the start of each significant session, particularly
before starting a new spec or experiment. Quick scan of open items;
address what's cheap, file what's not.

---

## Open

### Add red-team skills to bootstrap.py [bootstrap]

*Opened 2026-05-16*

The bootstrap script currently seeds `skills/` with three procedural
skills (`write-math-spec`, `derive-test-suite`, `document-experiment`).
The four red-team skills (`red-team-spec`, `red-team-tests`,
`red-team-implementation`, `red-team-result`) were drafted later in the
same session but only dropped into the live repo, not added to the
bootstrap. A labmate running `bootstrap.py` today would not get them.

Action: add them to `SEED_FILES` in `bootstrap.py`, and when they're
added also add a corresponding `## Red-teaming` section to the
`AGENTS_MD` seed content describing when to invoke each.

---

## Resolved / dismissed

<!-- Entries move here when closed, with a one-line resolution note. -->
