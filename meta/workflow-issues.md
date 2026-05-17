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

### Add macOS git HTTP/1.1 fix to bootstrap.py [bootstrap]

*Opened 2026-05-16*

On macOS with Apple's bundled git (2.39.2), HTTPS pushes to GitHub stall
during object upload due to an HTTP/2 issue. Fix: `git config http.version
HTTP/1.1` (local scope). Should be applied automatically by bootstrap.py
when running on Darwin, with a printed note explaining what was done.
Suggest also printing a brief note about the issue in the bootstrap output
on all platforms so labmates have a reference if they encounter related
push problems on other systems.

### Default to lightweight PDF tools in skills [skills]

*Opened 2026-05-16*

When skills involve PDF processing, default to Claude's built-in PDF
reading or to pure-Python libraries (`pypdf`, `pymupdf`, `pdfplumber`).
Avoid system-level dependencies like poppler unless rasterization is
actually needed — Homebrew installs of poppler can take many minutes
due to dependency chains, and the typical research task (reading paper
text) does not need it. When writing skills that touch PDFs, prefer the
simpler path and note in the skill what to escalate to if the simple
path fails.

### Revise write-math-spec skill after first 3 specs [skills]

*Opened 2026-05-17*

The current `skills/write-math-spec.md` is a reasonable first guess at
spec structure but is not yet informed by use. After three specs have
been written and used (tested against, red-teamed, possibly implemented),
review observations tagged `[spec-format]` in `meta/what-worked.md` and
`meta/what-didnt.md`, then decide what to revise. Do not revise piecemeal
in the meantime.

### Evaluate status-table convention after a few specs [conventions]

*Opened 2026-05-17*

The status table in `skills/write-math-spec.md` requires the human to
flip per-section status by direct table edit. After three specs have
been reviewed under this convention, evaluate: does it actually slow
down rubber-stamping? Or has it become an empty ritual? If the former,
keep. If the latter, redesign.

### Evaluate downstream-approval gating after a few specs [conventions]

*Opened 2026-05-17*

The rules in `skills/write-math-spec.md` gate test scaffolding behind
Setup+Objective approval, property tests behind Derivation approval, and
implementation behind Algorithm approval. These are conservative
guesses. After three specs reach implementation, evaluate whether the
gates were appropriate, too strict (causing workarounds), or too loose
(letting unreviewed math drive code). Revise the skill accordingly.

### Test traceability to spec sections [conventions]

*Opened 2026-05-17*

When a spec revision is a Correction, the affected tests need to be
identified and marked stale. Right now this is manual. Candidate
conventions: test docstrings that name the spec section they verify,
or a separate `tests/SPEC_MAPPING.md`. Decide based on what actually
hurts during the first Correction cycle, not in advance.

### Experiment-to-spec-commit traceability [conventions]

*Opened 2026-05-17*

When a spec is revised after experiments have been run against it,
identifying affected experiments is currently manual. Candidate
convention: experiment READMEs record the git commit hash of each spec
they depend on. Add this to `skills/document-experiment.md` if needed,
based on first-cycle experience.

### Settle on transcript-capture conventions [conventions]

*Opened 2026-05-17*

Today's sessions need to be captured to `transcripts/` but the right
mechanism hasn't been chosen. Candidates: (a) browser extension export
to Markdown for chat.claude.ai sessions, (b) raw JSONL from
~/.claude/projects/ for Claude Code, (c) Claude Code self-summarizing
the previous session at the start of the next. Pick after a few
sessions of seeing which captures actually get read back.

### Codify session-end routine after a few cycles [skills]

*Opened 2026-05-17*

Today established a rough session-end routine: dump transcript to
`transcripts/`, write `meta/handoff.md`, commit and push, skim
workflow-issues for open items. After this routine has been used
several times, consider codifying as `skills/close-session.md`. Hold
off on writing the skill until the routine has stabilized.

### Handle parallel work tracks via separate handoffs [conventions]

*Opened 2026-05-18*

The project will have at least two concurrent threads: (a) the
implementation track (currently spec 000), and (b) a more
mathematical/conceptual sub-project (TBD which spec or note files).
Convention: one handoff file per active track (`meta/handoff-<track>.md`),
updated only by sessions working on that track. Start of a session
loads the relevant handoff. Don't mix tracks within a single
conversation — switch tracks by closing the session and opening a new
one with the other handoff. Revisit if a third track appears or if
this becomes cumbersome.

### Codify Claude Code session-start prompt [skills]

*Opened 2026-05-18*

Each Claude Code session starts with a similar wake-up prompt: read
AGENTS.md, workflow-issues, handoff, current spec, then a specific
task. After a few sessions, consider codifying the structure as
`skills/start-session.md` or as a script that emits the prompt. Hold
off until the pattern stabilises.

---

## Resolved / dismissed

<!-- Entries move here when closed, with a one-line resolution note. -->
