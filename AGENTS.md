# AGENTS.md — Project handbook for human and AI collaborators

> This file is read first by Claude Code (and other agentic tools) at the start
> of every session. It is also the entry point for any human collaborator.
> Keep it short, opinionated, and current. When a convention changes, update
> here first.

## What this project is

`dynamic_infomax` is a research project in [theoretical ML / representation
learning]. Replace this paragraph with a one-paragraph description of the
specific research question once it's stable.

## How we work

We treat Claude as a collaborator, not an autocomplete. The goal is not to
produce code faster; it is to produce **reliable scientific understanding**
that a supervisor, a reviewer, or a future collaborator can audit.

Three commitments follow from that:

1. **Math first, then code.** Every nontrivial piece of code is preceded by a
   spec in `specs/` describing the math and the algorithm in prose. The spec
   is the contract; the code is one implementation of it.

2. **Tests as specification.** Before implementing, we write a test suite that
   the implementation must satisfy. Tests double as executable documentation
   of what the code is supposed to do.

3. **Diagrams where prose fails.** Architecture, data flow, and mathematical
   structure get a diagram in `diagrams/` (Mermaid for flowcharts, TikZ or SVG
   for math). If a labmate would need a diagram to understand something, we
   make the diagram.

## Directory map

- `notes/` — ideas and sketches we develop. New content.
- `resources/` — pre-existing material: papers, prior drafts, latex sources.
- `specs/` — math and algorithm specifications. The "what we will do" before code.
- `skills/` — procedural instructions for Claude. See `skills/README.md`.
- `src/` — implementation code.
- `tests/` — test suites. Each module in `src/` has matching tests here.
- `diagrams/` — Mermaid, TikZ, SVG.
- `experiments/` — one subdir per experiment, each with its own `PLAN.md`.
- `transcripts/` — raw Claude Code conversation logs. The audit trail.
- `meta/` — notes about the workflow itself. Material for the eventual guide.

## Conventions

### When Claude is asked to do something nontrivial

1. **Plan first.** Produce a short plan in markdown before editing files.
   List the files that will change, the order of changes, and any open
   questions. Wait for confirmation before executing, unless the task is
   genuinely small and reversible.
2. **Spec before code.** If the task involves new mathematical content or a
   new algorithm, write or update the relevant `specs/` file first.
3. **Tests before implementation.** Sketch the test cases in `tests/` before
   writing the implementation, even if rough.
4. **One artifact per concern.** Don't mix data processing and visualization
   in one script. Don't mix spec and code in one file.

### Code style

- Python 3.11+. Type hints required for any function that crosses module
  boundaries.
- We use `ruff` for linting and formatting (config in `pyproject.toml` once
  added).
- Numerical code uses `numpy` / `pytorch`. Avoid framework lock-in inside
  `specs/` — keep specs framework-agnostic.

### Git

- One logical change per commit. Commit messages: imperative mood, first line
  under 72 chars, optional body with the *why*.
- Never commit anything in `transcripts/` that contains secrets. (See
  `.gitignore` for the default rules.)
- The `meta/` directory is committed — it's the record of how we worked.

## When you (Claude) are uncertain

Say so. Producing confident-sounding wrong content is the single failure mode
this project is designed to avoid. If a spec is ambiguous, ask. If a result
seems too good, double-check. If a paper citation is needed and you're not
sure of the exact reference, mark it `[CITATION NEEDED]` rather than
inventing one.
