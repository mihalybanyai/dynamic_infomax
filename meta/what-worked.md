# What worked

> Patterns, prompts, and conventions that have proven useful. Add to this
> file when you notice something working well — don't wait until the project
> is done.

## Format

Each entry: a short title, a one-paragraph description, optionally a date
and a context note. Most useful entries will eventually graduate into a
skill in `skills/` or a convention in `AGENTS.md`.

## Entries

### Spec 000 used its own section structure rather than the skill's default [spec-format]

*Observed 2026-05-18*

The first spec (`specs/000-static-infomax-fig1.md`) was written by
Claude Code with section names of its own choosing (Purpose and scope /
Mathematical statement / Why this objective / Computational
specification / Test suite / Report / Layout / Deferred choices / Open
questions) rather than the default in `skills/write-math-spec.md`
(Context / Setup / Objective / Derivation / Algorithm / Properties to
verify / Open questions / References). The custom structure groups
things mathematically rather than procedurally, and on a first read
held together coherently — the §1 Mathematical statement subsection
covers the skill's Setup/Objective/Derivation, the §3 Computational
specification covers Algorithm, the §4 Test suite covers Properties.
The deferred-choices section (DC-1, DC-2, DC-3) was a genuine addition
that the skill template doesn't have an explicit slot for, but probably
should.

We accepted the divergence and added References and Revision log
sections as a minimal migration rather than reshaping. Whether the
skill should be revised to accommodate this pattern — or to make the
default section names more flexible — is something to evaluate after
two more specs. (See workflow-issues entry on revising the skill after
three specs.)