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

4. **Honest review.** When a suggestion or finding touches mathematics
   the human collaborator does not yet command, the right response is
   to flag the gap rather than wave the suggestion through. Reviewing
   what you don't understand is not review; it is delegation in
   review's clothing. The `> M?:` annotation in red-team workflows and any other review of LLM-generated content by a human
   (see `workflows/`) is the mechanism for flagging these gaps
   explicitly. A premise of this project is that growing the human's
   command of the mathematics is itself one of the goals, not a
   side-effect.

### Session start

At the start of a substantial session, skim `meta/workflow-issues.md` for
any open items relevant to today's work. Address what's cheap inline;
leave the rest for later but note in your plan that you saw them.

### Iron rules

Rules that bind every session, every skill, every workflow. These are
not procedural guidance ("how to do X well"); they are constraints on
what is allowed to happen at all. A skill or workflow that conflicts
with an iron rule loses.

The list is deliberately short. New rules are added only when a
specific failure mode has recurred enough to warrant the cost of
another always-active constraint. Each rule cites the failure that
motivated it.

---

#### IR-1 — Missing structural context: stop and ask, don't reconstruct

**The rule.** When a request requires producing output whose
*structure or format* is determined by an artefact in the repo
(an existing file's conventions, a skill's prescribed shape, a
spec section's layout, a log's entry format), and that artefact
is not in context, stop and ask for it. Do not reconstruct the
structure from priors and proceed.

This binds even when:

- The request feels urgent or the human seems to want a fast answer.
- A plausible structure can be guessed with high confidence.
- The work is "just a draft" or "a starting point".
- Reading the artefact appears to be a soft prerequisite ("if you
  have access, also look at...") rather than a hard one.
- The artefact was *mentioned* in the request but not *attached*,
  and the request reads as though the human assumed access.

**The scope.** The rule covers *structural* context only —
formats, conventions, file layouts, the shape of an entry in an
existing list, the section structure of an existing spec, the
voice of an existing skill. It does *not* cover:

- *Content* context shaped at the margin (a stylistic
  preference, a minor terminology choice). For these, a single
  best-guess interpretation with an explicit flag is allowed
  and often preferable to asking.
- *Adjacent* artefacts that might be useful but were not named
  by the human as required reading. Asking for everything
  tangentially related is its own failure mode.
- *Genuinely unknowable* facts (what the human will think of an
  approach, what an external service will return). For these,
  proceed and flag uncertainty.

**The action.** When the rule fires:

1. Name the missing artefact explicitly. ("I need
   `meta/workflow-issues.md` to match the existing entry
   format.")
2. Name what depends on it. ("The entry I'm about to draft will
   guess at section headers, status fields, and category tags
   that already exist in that file.")
3. Stop output. Do not produce a partial draft, a "rough
   version", or a "starting point" of the structure-dependent
   work in the same response. Conversational acknowledgement
   and unrelated work are fine.

**Anti-pattern to avoid.** "I'll write a generic version and
you can adapt it to your existing format." This sounds helpful
and is occasionally appropriate, but in the specific case
covered by IR-1 it is the failure the rule prohibits. The
human can adapt anything; what they cannot do is recover the
time spent reading a misformatted draft.

---

## Cross-references

- `AGENTS.md` references this file in its session-start section
  so the rules load before any skill or task is invoked.
- The standard Claude Code wake-up prompt includes a one-line
  pointer to this file alongside the AGENTS.md / workflow-issues
  / handoff reads.
- Chat sessions: the rules apply equally; no per-session prompt
  enforces them, so the rules are part of the project's
  standing context that any session is expected to honour.

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

### Test gates

Test artifacts are gated, not run all-at-once. From spec design through
implementation verification, the order is:

1. **Spec written**, including a per-spec **eye test** (a figure that a
   human inspects for qualitative correctness — see
   `skills/write-math-spec.md`).
2. **Test suite derived** from the spec, including a property-to-test
   table and a standalone eye-test file (see
   `skills/derive-test-suite.md`).
3. **Test suite red-teamed** before any implementation is written.
4. **Implementation written** against the red-teamed tests.
5. **Eye test run and human-approved** before the full quantitative
   suite runs. If the eye test fails, debugging takes precedence over
   the full suite — though running the full suite as a debugging aid
   is an option, it should be an active choice, not the default.
6. **Full test suite run** only after the eye test passes.

The eye-test gate exists because quantitative tests can all pass while
the implementation is qualitatively wrong (e.g. optimising the right
objective along the wrong dimension). A human glance at a figure is
the cheapest way to catch this class of bug.

The workflow that orchestrates these gates is in `workflows/`
(forthcoming `invoke-test-suite.md` will cover steps 5–6).

### Code style

- Python 3.11+. Type hints required for any function that crosses module
  boundaries.
- We use `ruff` for linting and formatting (config in `pyproject.toml` once
  added).
- Numerical code uses `numpy` / `pytorch`. Avoid framework lock-in inside
  `specs/` — keep specs framework-agnostic.

### Dependencies

The Python environment is managed by [uv](https://docs.astral.sh/uv/).
The rules:

- **Never run `pip install`.** Use `uv add <pkg>` for a runtime dep, or
  `uv add --group dev <pkg>` for tooling (PDF reading, plate diagrams,
  anything not used by the algorithms themselves). `uv add` edits
  `pyproject.toml` and regenerates `uv.lock` atomically, so the two
  files can never drift.
- **Commit `pyproject.toml` and `uv.lock` together** in the same
  commit, with a message that names what the dep is for. Never one
  without the other.
- **System-level installs** (`brew install X`, installer scripts,
  anything outside the venv) that the project depends on get a line in
  the *Local setup* section of `README.md` in the same task. If we
  deliberately *avoid* a system install (e.g. poppler, in favour of
  `pypdf`), say so under "What we deliberately don't install" so the
  next person doesn't reflexively `brew install` it.
- **Run `uv sync` before committing** any dependency change, to confirm
  the lockfile actually resolves and the deps actually import.

### Git

- One logical change per commit. Commit messages: imperative mood, first line
  under 72 chars, optional body with the *why*.
- Never commit anything in `transcripts/` that contains secrets. (See
  `.gitignore` for the default rules.)
- The `meta/` directory is committed — it's the record of how we worked.

### Spec status changes

`draft → reviewed`: human only, by direct edit.

`reviewed → draft` or `needs-revision → draft` after a revision: whoever makes the revision flips
the status as part of the same edit. Claude does this automatically
when revising a `reviewed` or or `needs-revision` section; no need to be asked.

## Reproducibility

Two non-negotiables for any code in this repo:

1. **Environment via uv.** The repo declares dependencies in
   `pyproject.toml` and pins them in `uv.lock`. Labmate setup is
   `uv sync`. Do not use system Python; do not pip-install outside
   the project venv.

2. **No global random state, and every result is provenance-recorded.**
   See `skills/manage-randomness.md` for the details. Summary: all
   randomness flows through explicitly-passed generators; every
   experiment has a recorded seed; every experiment run writes
   `provenance.json` capturing git hash, package versions, and spec
   commit hashes.

Both conventions are strict from the start of any code, not retrofitted
later. See workflow-issues entries on uv-in-bootstrap and randomness
conventions.

## When you (Claude) are uncertain

Say so. Producing confident-sounding wrong content is the single failure mode
this project is designed to avoid. If a spec is ambiguous, ask. If a result
seems too good, double-check. If a paper citation is needed and you're not
sure of the exact reference, mark it `[CITATION NEEDED]` rather than
inventing one.

The mirror of this for the human: if a Claude- or red-team-generated
suggestion is in a region you can't evaluate, flag it (`> M?:` in
red-team files) rather than passing judgement you don't have grounds
for. Claude can then generate a math-explainer in the chat session
(or, for concepts that recur, in `tutorials/`) calibrated to what
you actually need to evaluate the suggestion.

If you notice a workflow-level issue mid-session — something we should
change about how we work, not about the immediate task — add it to
`meta/workflow-issues.md` rather than derailing the current work. A short
entry under "Open" with a title, today's date, a category, and one
paragraph of context is enough.

