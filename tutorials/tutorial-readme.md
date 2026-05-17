# tutorials/

Short orientation notes for tools and practices that this project uses,
some of which may be new to people joining the workflow.

## Convention

Each tutorial is one markdown file. Two patterns:

- **External-pointer tutorials** (uv, gh, …): short orientation to how
  the tool is used in *this* project, plus annotated links to the best
  existing external material. No re-explaining what good tutorials
  already cover.

- **Project-specific tutorials** (RNG passing, …): self-contained
  walkthroughs of conventions that are specific enough to this project
  that no good external tutorial covers them.

The criterion for which pattern a tutorial uses: if a labmate could
learn the practice equally well from external sources, use the
pointer pattern; if the practice is opinionated to this project, write
it fully.

## Audience

Labmates new to the workflow, plus future-you who has forgotten how
some piece of the setup works. Tutorials should assume Python
competence but not familiarity with the specific tools.

## Current tutorials

- `uv.md` — Python package and environment management
- `gh.md` — GitHub CLI for authentication, repo creation, PRs, issues
- `rng-passing.md` — How and why we pass random generators explicitly

## Adding a new tutorial

A tutorial earns its place when:

1. A tool or practice appears in this project that a labmate would not
   already know.
2. Either no good external material exists, or external material exists
   but the project's use of the tool needs orienting context.

Don't write tutorials for things obvious from a quick read of `AGENTS.md`
or a skill. Don't write tutorials for tools the project doesn't actually
use — speculation isn't useful.
