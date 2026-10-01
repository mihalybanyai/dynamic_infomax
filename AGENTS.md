# AGENTS.md — Project handbook for human and AI collaborators

> Read first by Claude Code (and other agentic tools) at the start of every
> session, and the entry point for any human collaborator. Keep it short,
> opinionated, and current. When a convention changes, update it here first.

## What this project is

`dynamic_infomax` is a research project in [theoretical ML / representation
learning]. Replace this paragraph with a one-paragraph description of the
specific research question once it's stable.

## How we work

Claude is a collaborator, not an autocomplete. The goal is not code produced
faster but **reliable scientific understanding** that a supervisor, a
reviewer, or a future collaborator can audit. Hence:

1. **Math first, then code.** Nontrivial code is preceded by a spec in
   `specs/` stating the math and the algorithm in prose. The spec is the
   contract; the code is one implementation of it.
2. **Tests as specification.** The test suite is written before the
   implementation and doubles as executable documentation.
3. **Diagrams where prose fails.** Architecture, data flow, and mathematical
   structure get a diagram in `diagrams/` (Mermaid for flowcharts, TikZ or
   SVG for math).
4. **Honest review.** Reviewing what you don't understand is delegation in
   review's clothing. When content touches mathematics the human does not
   yet command, flag the gap (`> M?:`, see *Epistemic tags*) rather than
   wave it through. Growing the human's command of the mathematics is a goal
   of the project, not a side-effect.
5. **Brevity.** The human's attention is the project's scarcest resource.
   See *Brevity*.
6. **Marked provenance.** Every claim is either shown or tagged with how we
   know it. See *Epistemic tags*.

### Session types

Every session is either **science** (specs, notes, code, tests,
experiments) or **meta-science** (`AGENTS.md`, `skills/`, `workflows/`,
`meta/`: how we work and communicate). Declare the type in the first message
and in the handoff. Don't switch mid-session: a workflow issue noticed in a
science session becomes an entry under "Open" in `meta/workflow-issues.md`
(title, date, category, one paragraph); a science item noticed in a meta
session goes to a GitHub issue or the handoff.

At the start of a substantial session, skim `meta/workflow-issues.md` for
relevant open items. Address what's cheap inline; note the rest in your plan.

### Brevity

The ideal is Seb Krier's one-page *On Brevity*
([2026](https://x.com/sebkrier/status/2104286780304617912/photo/1)): an
abstract, an introduction reading "See abstract", and a single reference, to
Pascal's apology for a letter made long because he lacked the time to make it
short. Or, as was said of Ulysses Grant's orders: not one unnecessary word,
and no one could mistake the intent.

Text too long to review does not get reviewed; it gets waved through. So:

- **Intent first.** Anything written for human review opens with at most
  three lines: what it claims, and what the reader must decide.
- **The necessity test, continuously.** For each passage, ask whether the
  argument needs it. If not, move it to a footnote, where the human may
  delete it, or delete it outright. There are no word budgets: the test is
  necessity, not length.
- **Core and apparatus.** The core holds every claim the argument rests on;
  it is what the human reviews. The apparatus (footnotes, appendices,
  sibling files) holds only *support* for claims the core already states:
  derivation steps, alternatives considered, provenance, minor findings.
  Each apparatus item is pointed to from the core claim it supports. A
  load-bearing claim found only in the apparatus is a defect; red-teams
  check for it.
- **Define once, link everywhere.** Terms a computational neuroscientist, cognitive
  scientist or theoretical ML researcher may not know are defined in `GLOSSARY.md` and
  linked at first use in each section, not defined inline. A document defines only its
  own core objects. Glossary entries link to each other the same way.
- **Deletion is cheap.** Git is the archive. Cut freely; the human sees the
  cuts in `git diff`.
- **Archives are not reading obligations.** `transcripts/` and resolved
  red-team files are records.

### Epistemic tags

Mark *how we know* a claim, not how sure we feel: a provenance claim can be
checked, a stated probability cannot. An unmarked claim means "shown in this
document, or checked by code or a test". Anything else is tagged:

- `[read: source §X]` — the source was opened and says this.
- `[recalled]` — from memory; not checked.
- `[guess]` — conjecture.

A load-bearing `[recalled]` or `[guess]` gets a footnote naming what would
settle it: `[guess][^4]` with `[^4]: settled by computing b(θ) at d = 10.`
Use GFM footnotes (`[^n]`); they can later render as sidenotes. A reference
you cannot pin down is `[CITATION NEEDED]`, never invented.

The tags route attention: unmarked claims are cheap to accept, tagged ones
are where review goes, and `grep -rn '\[guess\]'` lists the project's
epistemic debt. They apply in chat too, where Claude also says what would
change its mind about a load-bearing claim. Existing documents get tags when
next revised.

The human's mirror is `> M?:` ("I can't evaluate this") in any review of
LLM-generated content (see `workflows/`). Claude then writes an explainer
calibrated to what the evaluation needs: in chat, or in `tutorials/` if the
concept recurs.

If a spec is ambiguous, ask. If a result seems too good, double-check.
Confident-sounding wrong content is the failure mode this project exists to
avoid.

### Iron rules

Constraints on what may happen at all, binding every session, skill, and
workflow; a conflicting skill or workflow loses. The list stays short: a rule
is added only when a failure mode has recurred enough to justify another
always-active constraint, and each rule cites the failure that motivated it.

#### IR-1 — Missing structural context: stop and ask, don't reconstruct

**Rule.** When the *structure or format* of requested output is determined
by a repo artefact (an existing file's conventions, a skill's prescribed
shape, a spec's section layout, a log's entry format) that is not in
context, stop and ask for it. Do not reconstruct the structure from priors.

This binds even when the request feels urgent; a plausible structure can be
guessed with high confidence; the work is "just a draft" or "a starting
point"; reading the artefact looks like a soft prerequisite ("if you have
access, also look at..."); or the artefact was mentioned but not attached,
as though the human assumed access.

**Scope.** Structural context only: formats, conventions, file layouts, the
shape of an entry in an existing list, a spec's section structure, a skill's
voice. Not covered: *content* shaped at the margin (a stylistic preference,
a terminology choice), where one flagged best guess is allowed and often
preferable; *adjacent* artefacts the human did not name as required (asking
for everything is its own failure mode); *unknowable* facts, where you
proceed and flag the uncertainty.

**Action.** (1) Name the missing artefact. (2) Name what depends on it.
(3) Stop: no partial draft, "rough version", or "starting point" of the
structure-dependent work in the same response. Conversation and unrelated
work are fine.

**Anti-pattern.** "I'll write a generic version and you can adapt it to your
existing format." The human can adapt anything; what they cannot recover is
the time spent reading a misformatted draft.

## Directory map

- `GLOSSARY.md` — definitions of terms used across the repo; documents link here.
- `notes/` — ideas and sketches we develop.
- `resources/` — pre-existing material: papers, prior drafts, LaTeX sources.
- `specs/` — math and algorithm specifications: what we will do, before code.
- `src/` — implementation code. `tests/` — one test suite per `src/` module.
- `experiments/` — one subdirectory per experiment, each with its own `PLAN.md`.
- `docs/` — user-facing documentation of each spec's artefacts.
- `diagrams/` — Mermaid, TikZ, SVG.
- `skills/` — procedures for Claude (see `skills/README.md`).
- `workflows/` — reusable prompts that orchestrate skills.
- `tutorials/` — explainers for tools and mathematics.
- `transcripts/` — raw conversation logs; the audit trail.
- `meta/` — notes about the workflow itself; material for the eventual guide.

## Conventions

### Nontrivial requests

1. **Plan first.** A short markdown plan before editing files: the files that
   will change, the order, open questions. Wait for confirmation unless the
   task is small and reversible.
2. **Spec before code** for new mathematical content or a new algorithm.
3. **Tests before implementation**, even if rough.
4. **One artefact per concern.** Don't mix data processing with
   visualisation, or spec with code, in one file.

### Test gates

From spec design to verified implementation, in order:

1. **Spec written**, including its **eye test**: a figure a human inspects
   for qualitative correctness (`skills/write-math-spec.md`).
2. **Test suite derived** from the spec, with a property-to-test table and a
   standalone eye-test file (`skills/derive-test-suite.md`).
3. **Test suite red-teamed** before any implementation is written.
4. **Implementation written** against the red-teamed tests.
5. **Eye test run and human-approved** before the quantitative suite. If it
   fails, debugging comes first; running the full suite as a debugging aid
   is an active choice, not the default.
6. **Full test suite run** only after the eye test passes.

The eye-test gate exists because quantitative tests can all pass while the
implementation is qualitatively wrong (e.g. optimising the right objective
along the wrong dimension); a glance at a figure is the cheapest catch. The
orchestrating workflows are in `workflows/` (a forthcoming
`invoke-test-suite.md` will cover steps 5–6).

### Code style

Python 3.11+. Type hints on any function that crosses module boundaries.
`ruff` for linting and formatting (config goes in `pyproject.toml`). Numerical
code uses `numpy` / `pytorch`; specs stay framework-agnostic.

### Dependencies

The environment is managed by [uv](https://docs.astral.sh/uv/).

- **Never `pip install`.** `uv add <pkg>` for a runtime dep; `uv add --group
  dev <pkg>` for tooling the algorithms don't use (PDF reading, plate
  diagrams). `uv add` updates `pyproject.toml` and `uv.lock` atomically.
- **Commit `pyproject.toml` and `uv.lock` together**, with a message naming
  what the dep is for.
- **Run `uv sync` before committing** a dependency change, to confirm the
  lockfile resolves and the deps import.
- **System-level installs** (`brew install`, installer scripts) the project
  depends on get a line under *Local setup* in `README.md`, in the same task.
  Deliberately avoided installs (e.g. poppler, in favour of `pypdf`) go under
  "What we deliberately don't install".

### Git

One logical change per commit: imperative mood, first line under 72
characters, optional body with the *why*. Never commit secrets in
`transcripts/` (see `.gitignore`). `meta/` is committed: it is the record of
how we worked.

### Spec status changes

`draft → reviewed`: the human only, by direct edit. `reviewed → draft` or
`needs-revision → draft`: whoever revises flips the status in the same edit;
Claude does this automatically, without being asked.

### Red-team reviewer roster

Red-team sub-agents are the project's main quality gate, so they run on the
strongest available configuration, not the session default:

- **Model.** The two latest models intended for *conceptual* work: the
  newest is the primary/default, the second the independent diversity pass
  (`workflows/invoke-red-team-on-spec.md`).
- **Effort.** Always the highest available tier.

Neither fact is machine-discoverable, and effort is not even
machine-checkable from inside the agent (see the spawn-configuration gate in
`skills/red-team-spec.md`). This table is the single source of truth.

| Approved red-teamer (declared identity) | Role | Highest effort tier | Availability |
|---|---|---|---|
| Claude Fable 5 | conceptual — experimental | Max | all paid tiers (not free), but will be excluded later |
| Claude Opus 4.8 | conceptual — primary | Max | all paid tiers (not free) |
| Claude Opus 4.7 | conceptual — diversity | Max | all paid tiers (not free) |

Mechanical sibling red-teams (tests, implementation) may use a cheaper model
(the latest Sonnet); the conceptual spec red-team does not.

**Last verified:** 2026-06-11 (human). The spawn-configuration gate prints
this table at every invocation and refreshes this date on "go", so a stale
roster (a model shipped, a tier changed) is caught by the human noticing it,
not by an automated check. Update the cells by direct edit.

## Reproducibility

Strict from the first line of code, never retrofitted:

1. **Environment via uv.** Dependencies declared in `pyproject.toml`, pinned
   in `uv.lock`; labmate setup is `uv sync`. No system Python, no installs
   outside the project venv.
2. **No global random state; every result provenance-recorded.** All
   randomness flows through explicitly passed generators; every experiment
   has a recorded seed; every run writes `provenance.json` (git hash, package
   versions, spec commit hashes). Details in `skills/manage-randomness.md`.
