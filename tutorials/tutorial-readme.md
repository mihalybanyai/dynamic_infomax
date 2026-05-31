# tutorials/

Short orientation notes for tools, practices, and mathematical
concepts that this project uses, some of which may be new to people
joining the workflow or to the human collaborator in the moment of
needing them.

## Convention

Each tutorial is one markdown file. Three patterns:

- **External-pointer tutorials** (uv, gh, …): short orientation to
  how the tool is used in *this* project, plus annotated links to
  the best existing external material. No re-explaining what good
  tutorials already cover.

- **Project-specific tutorials** (RNG passing, …): self-contained
  walkthroughs of conventions that are specific enough to this
  project that no good external tutorial covers them.

- **Math explainers** (`math/` subfolder): just-in-time explanations
  of mathematical concepts, calibrated to the project's specific use
  rather than the concept in general. Triggered by `> M?:`
  annotations in red-team workflows (see `workflows/` and
  `AGENTS.md`), promoted from chat to file the second time the same
  concept comes up. Each math explainer scopes itself explicitly in
  its opening paragraph — what it covers, what it doesn't, and
  pointers to canonical external sources for fuller treatment.

The criterion for which pattern a tutorial uses: if a labmate could
learn the practice equally well from external sources, use the
pointer pattern; if the practice is opinionated to this project,
write it fully; if it's mathematics, calibrate to the project's use
and live in `math/`.

## Audience

Labmates new to the workflow, plus future-you who has forgotten how
some piece of the setup works or who has hit the same mathematical
concept for the second time. Tutorials should assume Python
competence but not familiarity with the specific tools or specific
mathematical sub-areas.

## Current tutorials

- `uv.md` — Python package and environment management
- `gh.md` — GitHub CLI for authentication, repo creation, PRs, issues
- `rng-passing.md` — How and why we pass random generators explicitly
- `math/kkt.md` — KKT conditions, calibrated to Blahut-Arimoto
- `math/kelly.md` — Kelly betting, calibrated to the infomax-betting experiment
- `math/redundancy-capacity.md` — coding redundancy, capacity, equalizer
  priors, and why `p*` is discrete (the design-loss case)

## Adding a new tutorial

For infrastructural tutorials (the first two patterns), a tutorial
earns its place when:

1. A tool or practice appears in this project that a labmate would
   not already know.
2. Either no good external material exists, or external material
   exists but the project's use of the tool needs orienting context.

For math explainers (the third pattern), the trigger is different:
a math explainer earns its place when the same mathematical concept
has been flagged with `> M?:` annotations on **two or more separate
red-team findings or sessions** — the "data, not forecasting"
criterion. The first occurrence is handled in chat; only the
second triggers the file.

Don't write tutorials for things obvious from a quick read of
`AGENTS.md` or a skill. Don't write tutorials for tools the project
doesn't actually use — speculation isn't useful. Don't write math
explainers preemptively for concepts that *seem* important; wait
for the second `> M?:`.

## Math explainer scope discipline

A math explainer is calibrated to *the project's use of the concept*,
not the concept in general. Concretely: it should be organised around
the spec(s) or derivation(s) that prompted it, with general theory
introduced only as needed to make the specific application make
sense. The opening paragraph names this scope explicitly, and a
provenance footer at the end points back to the originating
red-team finding(s).

If a math explainer starts to look like a textbook chapter, it has
drifted from the discipline. The right reaction: split into a
shorter calibrated file plus pointers to external material, rather
than absorbing more general content.