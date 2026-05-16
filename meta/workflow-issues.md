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

---

## Resolved / dismissed

<!-- Entries move here when closed, with a one-line resolution note. -->
