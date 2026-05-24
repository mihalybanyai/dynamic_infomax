#!/usr/bin/env python3
"""
Bootstrap script for the dynamic_infomax research project.

Creates a directory structure designed for LLM-assisted research with an
emphasis on transparency between supervisors, students, and AI collaborators.

Usage:
    python bootstrap.py [--path PATH]

By default, creates ./dynamic_infomax in the current working directory.
Safe to re-run: existing files are never overwritten.
"""

from __future__ import annotations

import argparse
import platform
import subprocess
import sys
from pathlib import Path

PROJECT_NAME = "dynamic_infomax"

# ---------------------------------------------------------------------------
# Directory layout
# ---------------------------------------------------------------------------

DIRECTORIES = [
    "notes",            # ideas, sketches, working thoughts (new content)
    "resources",        # pre-existing material: papers, prior drafts, latex sources
    "specs",            # math + algorithm specifications (the "what we will do")
    "skills",           # procedural knowledge files for Claude Code
    "workflows",        # reusable prompts that orchestrate skills
    "tutorials",        # short orientations to tools, practices, math concepts
    "tutorials/math",   # math explainers, triggered by red-team `> M?:` annotations
    "src",              # code
    "tests",            # tests
    "diagrams",         # mermaid / tikz / svg, generated alongside code
    "experiments",      # one subdir per experiment, each with its own PLAN.md
    "transcripts",      # raw chat logs (the audit trail)
    "meta",             # notes about the workflow itself, for the eventual guide
    "docs",             # per-spec documentation accompanying implementations
]

# ---------------------------------------------------------------------------
# Seed file contents
# ---------------------------------------------------------------------------

AGENTS_MD = r'''# AGENTS.md — Project handbook for human and AI collaborators

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
'''

SKILL_MANAGE_RANDOMNESS = r'''# Skill: manage-randomness

> Use this skill whenever writing code that involves randomness, or
> setting up an experiment that will be reported as a result. The goal
> is that any result in this repo can be reproduced exactly, given the
> same code and the same seed.

> **Status**: v1, written before first use. Expect revisions after the
> first one or two experiments actually run. See workflow-issues entry
> "Randomness/reproducibility conventions".

## Why this exists

Two reproducibility failures are common and silent:

1. **Implicit global RNG state.** A function calls `np.random.rand()`,
   which reads from numpy's global RNG. Any prior call anywhere in the
   process — including in imported libraries — affects the output. The
   "same code, same seed" guarantee silently fails the moment someone
   reorders imports or adds a new dependency.

2. **Unrecorded provenance.** A result was produced by code at some
   git commit, with some package versions, using some seed. Months later
   the spec changes, the code changes, the deps change, and you cannot
   tell whether the old result is still valid because you don't know
   what produced it.

The conventions in this skill prevent both. They are strict on purpose;
the cost of "always pass a generator" is small, and the savings when
something later needs to be reproduced are large.

## Conventions

### Rule 1: No global random state

Any function in `src/` or `experiments/` that uses randomness takes a
generator as an argument. No exceptions for "quick" or "trivial" calls.

**For numpy** — the only randomness API in this project is
`numpy.random.Generator`:

```python
import numpy as np

def some_function_using_randomness(x: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    noise = rng.standard_normal(x.shape)
    return x + noise
```

Forbidden patterns:

```python
# ✗ Reads global state
np.random.rand(...)
np.random.normal(...)
np.random.seed(42)

# ✗ Constructs a new generator with no seed parameter inside a function
rng = np.random.default_rng()  # in library code
```

**For PyTorch** (when it arrives) — every randomness-using function
takes a `torch.Generator` and passes it to ops that accept it:

```python
def init_weights(shape, generator: torch.Generator) -> torch.Tensor:
    return torch.randn(shape, generator=generator)
```

Forbidden patterns:

```python
# ✗ Reads global state
torch.randn(...)
torch.manual_seed(42)  # except at the top of an experiment entry point
```

### Rule 2: One seed per experiment, recorded

Each experiment in `experiments/NNN-*/` has a single top-level seed,
specified in its `config.yaml` (or equivalent) and recorded in its
`PLAN.md`. The experiment's `run.py` reads the seed, constructs one
generator at the top, and threads it through everything:

```python
# experiments/000-static-fig1/run.py
import numpy as np
from infomax.ba import blahut_arimoto

def main(seed: int, ...):
    rng = np.random.default_rng(seed)
    result = blahut_arimoto(..., rng=rng)
    ...
```

If an experiment needs multiple independent random streams (e.g., one
for initialisation, one for data generation, one for evaluation), spawn
them from the top-level generator rather than creating multiple
independent ones:

```python
rng = np.random.default_rng(seed)
init_rng, data_rng, eval_rng = rng.spawn(3)
```

This guarantees that the spawned generators are deterministic functions
of the seed, while remaining statistically independent of each other.

**Multiple seeds for the same experiment**: when an experiment needs to
be repeated under different seeds (e.g., for variance estimation), each
run gets its own subdirectory:

```
experiments/000-static-fig1/
├── PLAN.md
├── config.yaml         # specifies the list of seeds to run
├── run.py
├── seed-20260518/      # one full set of outputs per seed
├── seed-20260519/
└── seed-20260520/
```

The seeds used are listed in the experiment's `PLAN.md`. Choose seeds
deliberately, not "by feel" — a common convention is to use the date
in `YYYYMMDD` form, which makes the seed self-documenting. Other
deliberate choices (e.g., `42, 43, 44` for a triplet) are fine; the
point is that the seeds are *chosen* and *recorded*, not generated by
the current time or RNG.

### Rule 3: Visible hardcoded seeds in tests

Tests that use randomness construct their own generator with a
hardcoded literal seed at the top of the test:

```python
def test_ba_is_monotonic():
    """BA iterations should produce non-decreasing I_tau."""
    rng = np.random.default_rng(20260518)
    P = make_random_likelihood(rng, m=5, n_theta=100)
    ...
```

Rules:

- Seed is a literal in the test code (not imported from a constant, not
  read from config). Grep-able.
- Seed is the same across runs. Tests are deterministic.
- One seed per test, generally. If tests share fixture randomness, use a
  pytest fixture that constructs the generator once with a known seed.

### Rule 4: Provenance recorded for every experiment run

Every experiment run writes a `provenance.json` file in its output
directory at the start of the run. Minimal contents:

```json
{
  "git_commit": "a3f4d12abc...",
  "git_status": "clean",
  "python_version": "3.11.5",
  "numpy_version": "2.0.1",
  "scipy_version": "1.13.0",
  "platform": "Darwin-23.4.0-arm64",
  "hostname": "banyais-macbook-air",
  "started_at": "2026-05-18T14:32:11Z",
  "seed": 20260518,
  "config_path": "experiments/000-static-fig1/config.yaml",
  "config_hash": "sha256:...",
  "spec_paths": [
    "specs/000-static-infomax-fig1.md"
  ],
  "spec_commit_hashes": {
    "specs/000-static-infomax-fig1.md": "8b29ef0..."
  }
}
```

`git_status` is `clean` if `git status --porcelain` is empty at the
start of the run, otherwise `dirty` (and a result from a dirty
repository should be considered a draft result). The
`spec_commit_hashes` field is the answer to "which version of the spec
did this run depend on" — see the workflow-issues entry on
experiment-to-spec-commit traceability.

A small helper for generating this should live in
`src/infomax/provenance.py` (or wherever — adjust to fit the import
layout):

```python
# Sketch; refine when actually used.
import json, subprocess, platform, sys, hashlib
from pathlib import Path
from datetime import datetime, timezone

def write_provenance(output_dir: Path, seed: int, config_path: Path,
                     spec_paths: list[Path]) -> None:
    info = {
        "git_commit": _git("rev-parse", "HEAD"),
        "git_status": "clean" if not _git("status", "--porcelain") else "dirty",
        "python_version": sys.version.split()[0],
        "platform": platform.platform(),
        "hostname": platform.node(),
        "started_at": datetime.now(timezone.utc).isoformat(),
        "seed": seed,
        "config_path": str(config_path),
        "config_hash": "sha256:" + hashlib.sha256(config_path.read_bytes()).hexdigest(),
        "spec_paths": [str(p) for p in spec_paths],
        "spec_commit_hashes": {
            str(p): _git("log", "-1", "--format=%H", "--", str(p))
            for p in spec_paths
        },
        # Package versions: import each and read __version__, or use importlib.metadata
    }
    (output_dir / "provenance.json").write_text(json.dumps(info, indent=2))

def _git(*args: str) -> str:
    return subprocess.check_output(["git", *args], text=True).strip()
```

The actual implementation should also record package versions for every
package imported in `src/`. Use `importlib.metadata.version()` rather
than hand-listing.

## When the conventions hurt

Two cases will come up:

**Prototyping in a notebook.** Notebooks are exempt from rule 1 in the
sense that you don't have to thread a generator through every cell —
but you should still create a generator at the top of the notebook and
use it explicitly (`rng = np.random.default_rng(20260518)` then
`rng.random()`), never call the global-state functions. Notebooks that
end up producing results that are reported anywhere get the same
provenance treatment as experiments.

**Library code that "needs" randomness but doesn't have a generator
handy.** This is almost always a code-design problem, not a randomness
problem. If a function needs randomness it should accept a generator;
the function's caller is responsible for having one. If you find yourself
wanting to construct an RNG inside library code, that's a signal that
the function's API is wrong.

## Output

When implementing any new module or experiment, this skill is consulted
and the rules are followed. When reviewing code, look for violations
(`np.random.rand`, `torch.randn` without generator, missing
provenance.json) as a checklist item.

## v1 limitations

Things this skill does not yet specify, which we'll revise once we've
hit them:

- Torch CUDA non-determinism (which goes beyond seeds: `torch.use_deterministic_algorithms(True)`, etc.).
- Parallelism: when work is parallelised across processes/workers, each
  worker needs its own deterministic substream — `rng.spawn(n_workers)`
  is the right primitive, but the conventions for *passing* spawned RNGs
  through worker pools aren't worked out here.
- Caching of expensive random computations (so reproducibility coexists
  with not regenerating the same arrays every run).

These are documented as open issues in the corresponding workflow-issues
entry rather than half-answered here.
'''

SKILL_RED_TEAM_SPEC = r'''# Skill: red-team-spec

> Use this skill after a spec in `specs/` has been written or substantially
> modified. The goal is to find errors and weaknesses **before** any code is
> written against the spec.

## Why this exists

A spec written by the same agent that conceived it carries an anchoring bias:
the derivation that produced the spec is in context, and any check from the
same context will tend to confirm rather than challenge it. Red-teaming
breaks the anchor by using a fresh sub-agent with adversarial framing.

## How to invoke

Use the `Task` tool to spawn a sub-agent with the following prompt template.
Substitute `<SPEC_PATH>` with the actual path.

```
You are a hostile reviewer reading the specification at <SPEC_PATH>. Your
job is to find what is wrong with it. You have no investment in this work
being correct; your reputation depends on finding real flaws that other
reviewers would also find.

Read the spec. Also read any files it references (notes, prior specs,
diagrams). Then attack it.

Focus on these failure modes, in roughly this order of value:

1. **Math errors**: sign flips, missing factors, dimension mismatches,
   misapplied identities, expectations taken over the wrong distribution,
   index errors in sums/products.

2. **Unstated assumptions**: places where the derivation only goes through
   under conditions the spec does not name. Differentiability, boundedness,
   independence, stationarity, finite variance, full-rank conditions — be
   specific about which one is missing where.

3. **Spec/algorithm mismatch**: the pseudocode does not implement the math.
   The objective in section X is not what the algorithm in section Y
   actually optimizes. The properties listed in "Properties to verify" do
   not all follow from the math as written.

4. **Notation drift**: a symbol means one thing in section 2 and a different
   thing in section 4. A vector becomes a scalar without warning. An
   expectation switches from over one distribution to another implicitly.

5. **Edge cases the spec ignores**: what happens when the input is empty,
   degenerate, has zero variance, has infinite support, is a single sample?

6. **Vague claims**: any sentence that uses "natural", "obvious", "clearly",
   "well-known", "standard" should be flagged. These words usually hide a
   step the author did not want to write out.

Be specific. Useless: "the proof in section 3 might not work."
Useful: "the inequality in equation (3.7) requires f to be convex, but f is
defined in section 2 as a difference of two convex functions, which is not
in general convex — please justify the inequality or restrict f's
definition."

For each finding, state:
- **Location**: section/equation reference.
- **Concern**: what's wrong, specifically.
- **Severity**: high (invalidates the result), medium (requires non-trivial
  fix or restricts scope), low (cosmetic but should be addressed).
- **What would resolve it**: what the author could add or change to address
  the concern.

**Ordering**: list findings in order of descending severity (high first,
then medium, then low). Within a severity level, order by location in the
spec (earliest section first). Number findings F1, F2, F3, ... *after*
ordering, so F1 is the highest-severity, earliest-located finding.

If you cannot find substantial flaws, say so directly. Do not invent
concerns to seem thorough. A short report with three real flaws is more
valuable than a long report with twenty fake ones.

Write your findings to `<SPEC_PATH_WITHOUT_EXTENSION>-redteam.md` in the
following format:

# Red-team review of <SPEC_NAME>

Reviewer: red-team sub-agent
Date: <YYYY-MM-DD>
Spec version: <git commit hash if available>

## Summary

<one paragraph: qualitative overall impression of the spec — what the
author seems to get right, where the work seems thinnest, whether the
spec is ready for downstream work or needs substantive revision. Do
not include counts of findings by severity; the list below is the
source of truth, and counts produced separately tend to drift from
the actual list.>

## Findings

### F1: <short title> [severity: high]

**Location**: <section / equation>

**Concern**: <specific description>

**What would resolve it**: <specific suggestion>

---

### F2: ...

## What the spec gets right

<one paragraph, briefly. Not flattery — this is so the author knows what
not to inadvertently break when addressing the findings.>
```

## Annotation conventions in the redteam file

The redteam file is a living document, not a one-time report. As findings
are processed, the file accumulates a record of how each one was resolved.

**The human appends a response to each finding** with the `> M:` blockquote
prefix (M for the human's initial; substitute as appropriate), expressing
intent: apply (with any wording specifics), dismiss (with reason), or
uncertain (with a question or ambiguity to discuss). Two newlines separate
the human's response from the finding above.

**Claude (or the human, when editing manually) appends a confirmation**
with the `> C:` blockquote prefix, two newlines below the human's response,
recording what was actually done (e.g., "> C: Applied as suggested in
commit a3f4d12; section §1.4 status flipped to draft and revision log
entry added.").

Example after a full resolution cycle:

```markdown
### F3: Differentiability assumption unstated [severity: medium]

**Location**: §1.4

**Concern**: The optimisation step requires differentiability of f, but
§1.2 defines f as a max of two functions, which is not differentiable
everywhere.

**What would resolve it**: State the assumption explicitly, or replace
the differentiation step with a subgradient version.

> M: Yes, apply the fix. Use subgradients; the max is over a finite
> set so the subgradient is well-defined.

> C: Applied as suggested in commit a3f4d12. §1.4 now uses
> subgradient notation. Section status flipped to draft. Revision
> log entry added as Clarification.
```

This convention makes the redteam file the audit trail for the red-team
pass — what was flagged, what the human decided, what was done, all in
one place. See `workflows/invoke-red-team-on-spec.md` for the full
procedural workflow.

## After the red-team report exists

The author (human or Claude Code main agent) addresses each finding. For
each one, either:

- **Fix it**: edit the spec, then in the redteam file append a `> C:`
  confirmation referencing the commit and any status changes made.
- **Dismiss it**: append a `> M:` response with a justification, and a
  `> C:` confirmation that no spec change was made.

The redteam file is committed alongside the spec. It is part of the audit
trail.

## When to skip this skill

- The spec is a trivial revision (typo fix, notation cleanup) of an
  already-red-teamed version. Note the prior redteam hash and move on.
- The spec is explicitly a working draft marked `DRAFT` in its title and
  not yet ready for review. Red-team only stabilized specs.
'''

SKILL_RED_TEAM_TESTS = r'''# Skill: red-team-tests

> Use this skill after a test file in `tests/` has been written from a
> spec. The goal is to find ways the test suite could pass while the
> implementation is wrong.

## Why this exists

A test suite has two failure modes that are easy to miss from the author's
perspective:

1. **Under-specification**: properties in the spec that are not tested at
   all, so a wrong implementation could pass.
2. **Vacuous tests**: tests that pass trivially, e.g. tests that would pass
   for a function that returns zero, or for a function that returns its
   input unchanged.

A fresh sub-agent reading the spec and the tests separately is well-placed
to catch both.

## How to invoke

Use the `Task` tool to spawn a sub-agent with the following prompt template.
Substitute `<SPEC_PATH>` and `<TEST_PATH>` with the actual paths.

```
You are a hostile test reviewer. Your job is to find ways the test suite
at <TEST_PATH> could pass while the implementation being tested is wrong.

Read the spec at <SPEC_PATH> first, then read the tests. Your job has two
parts.

## Part 1: Coverage gaps

For each property listed in the spec's "Properties to verify" section,
identify which test (or tests) verifies it. Then list any properties that
are not verified by any test, or are only verified weakly.

Also look for properties implied by the math but not listed in "Properties
to verify" — derivable invariances, scaling behaviors, limiting cases.
Flag the most important missing ones.

## Part 2: Vacuous or weak tests

For each test, ask: what is the simplest wrong implementation that would
still pass this test?

Concrete failure patterns to look for:

- **Returns-input tests**: tests that compare output to input and would
  pass for the identity function.
- **Returns-zero tests**: tests that check the output is "small" or "close
  to zero" without specifying what it should actually be.
- **Symmetric inputs**: tests where the input has a symmetry that makes
  many wrong outputs look right (e.g., testing on a uniform distribution
  where many statistics coincide).
- **Tolerance too loose**: `assert_allclose` with `atol=1.0` on a quantity
  that ranges from -2 to 2 — passes for almost anything.
- **Mock-shaped output**: tests that only check `output.shape == expected_shape`
  without checking values. Pass for any implementation that returns the
  right shape.
- **Missing reference value**: tests that compare two implementations to
  each other without an independent ground truth, so both can be wrong in
  the same way.
- **Statistical tests with too few samples**: a test that runs an estimator
  on 10 samples and checks it's within 50% of truth will pass for a very
  noisy estimator.

For each finding, state:
- **Test**: which test function (or "missing test" if it's a coverage gap).
- **Concern**: what wrong implementation would pass this test.
- **Severity**: high (a substantially wrong implementation passes), medium
  (a subtle bug passes), low (the test is fine but could be sharper).
- **What would resolve it**: suggest a sharper test, a known-answer case,
  a tighter tolerance, or an additional invariance check.

Known-answer cases are the most valuable suggestions. If the spec or its
references contain any analytically computable case (a specific
distribution, a specific input where the answer is known in closed form),
flag whether it is tested and recommend adding it if not.

**Ordering**: list findings in order of descending severity (high first,
then medium, then low). Within a severity level, order coverage-gap
findings (Part 1) before vacuous-test findings (Part 2), and within each
of those order by spec section or test function name (earliest first).
Number findings F1, F2, F3, ... *after* ordering.

Write your findings to `<TEST_PATH_WITHOUT_EXTENSION>-redteam.md`,
mirroring the format below. Do not include counts of findings by
severity in the summary; the list is the source of truth.

# Red-team review of <TEST_NAME>

Reviewer: red-team sub-agent
Date: <YYYY-MM-DD>
Test file version: <git commit hash if available>
Spec version reviewed against: <git commit hash if available>

## Summary

<one paragraph: qualitative impression of the test suite — does it
plausibly pin down the spec's claims, where is the weakest area,
what kind of wrong implementation would slip through. No counts.>

## Findings

### F1: <short title> [severity: high]

**Test**: <test function name or "missing">

**Concern**: <specific description, including what wrong implementation
would pass>

**What would resolve it**: <specific suggestion>

---

### F2: ...

## What the test suite gets right

<one paragraph, briefly. So the author knows what not to break.>
```

## Annotation conventions in the redteam file

Same convention as `skills/red-team-spec.md`: the human appends responses
with `> M:` (or appropriate initial) and Claude or the human appends
confirmations with `> C:`, two newlines between each. The redteam file
becomes the audit trail for the test red-team pass.

Example after resolution:

```markdown
### F2: Monotonicity test passes for constant function [severity: high]

**Test**: test_ba_iteration_is_monotonic

**Concern**: The test checks that I_tau is non-decreasing, but a wrong
implementation that always returns I_tau = 0 would pass. The test does
not check that I_tau converges to a nontrivial value.

**What would resolve it**: Add an assertion that I_tau converges to a
value strictly greater than some lower bound (e.g., I_tau >
log(min(m, n_theta)) / 100 for nontrivial likelihoods).

> M: Apply. Use the suggested lower bound but parametrise the constant
> via a fixture so it's not buried as a magic number.

> C: Applied in commit b71f3d4. Added the lower-bound assertion and
> moved the constant to a `NONTRIVIAL_MI_LOWER_BOUND` fixture in
> conftest.py.
```

## After the report exists

The author addresses findings the same way as for spec red-teaming: fix
(by adding or sharpening tests) or dismiss (with justification), with
`> M:` and `> C:` annotations inline. Status table considerations for
the test file (if it has one) follow the same direction-asymmetry rule
as specs — Claude flips backwards on revision, the human flips forwards
on re-review.

## Common dismissals that are *not* acceptable

- "This is implicitly covered by another test." If it's covered, point to
  which test and explain how. Otherwise add the test.
- "The implementation will obviously satisfy this." The whole point is that
  the tests should detect cases where the implementation does not. Add the
  test.

## Common dismissals that *are* acceptable

- "This property is verified in the integration test in
  `experiments/NNN/`." Acceptable if true, and the integration test is
  named.
- "The closed-form known-answer case requires a special function not in
  our dependencies; we'll add it when we add `scipy.special` to
  requirements." Acceptable with a follow-up item in
  `meta/what-didnt.md` or a TODO in the test file.
'''

SKILL_RED_TEAM_IMPLEMENTATION = r'''# Skill: red-team-implementation

> Use this skill after an implementation in `src/` has been written from a
> reviewed spec, the test suite (itself red-teamed) passes, and the
> documentation files for the implementation are in place. The goal is to
> find what "passes the tests" misses — bugs the tests didn't catch,
> latent correctness risks, load-bearing inefficiencies, and inaccuracies
> or load-bearing omissions in the documentation.

## Why this exists

A passing test suite is necessary but not sufficient evidence that an
implementation is correct. Tests only exercise the cases the test author
imagined. The implementation can:

1. Be wrong on cases the tests don't exercise.
2. Be right on the tested regime but rely on assumptions that won't hold
   for the next spec or the next scaling regime.
3. Be slow enough that the spec's intended scale is unreachable.
4. Be documented in a way that misleads a future reader — wrong shape
   annotations, stale design-decision rationale, comments that
   contradict the code.

A fresh sub-agent reading the spec, then the docs, then the code is
positioned to catch all four. The reading order is deliberate: if the
docs claim X and the code does Y, a docs-first reader notices the
mismatch as a mismatch, where a code-first reader would form an
opinion of what the code does and the docs would then have to fight it.

## How to invoke

Use the `Task` tool to spawn a sub-agent with the following prompt
template. Substitute `<SPEC_PATH>`, `<CODE_DIR>`, and `<DOC_PATH>` with
the actual paths.

```
You are a hostile reviewer of an implementation. Your job is to find
the gap between "passes the tests" and "is actually a good
implementation of the reviewed spec, well-documented."

Context you should take as given:
- The spec at <SPEC_PATH> has been red-teamed and is at status
  `reviewed` across all relevant sections. You are NOT auditing the
  math.
- The test suite has been red-teamed and the implementation passes
  all tests. You are NOT auditing test coverage against the spec.
- The implementation lives at <CODE_DIR>. The documentation lives at
  <DOC_PATH>.

Read the spec first to load the contract. Then read the documentation
(design decisions, data flow, call graph, inline conventions). Then
read the code. This order is deliberate: form your picture of what
the implementation *should* do from spec+docs, and let the code be
checked against that picture rather than the other way round.

Audit for the following, in this order of priority:

1. **Bugs the tests didn't catch.** Cases where the code produces
   wrong output for inputs the tests don't exercise. Off-by-one
   errors at boundaries, wrong behaviour for degenerate inputs not
   covered by tests, silent incorrect handling of edge cases the
   spec implicitly requires but the tests don't probe.

   **Meta-rule**: if a bug you find would have been caught by a test
   that already exists and passed, that's not a bug-finding, that's
   a *test* finding — the test is wrong or vacuous. Mark with
   `[test-gap]` in the finding header; it retroactively belongs to
   the test red-team's territory and will be routed there during
   triage.

2. **Latent correctness risks.** Code that produces correct output
   for the spec's exercised cases but contains assumptions that
   would fail under plausible extensions. Examples: assumes a
   specific axis order that the next spec might transpose; relies
   on a numerical regime (small N, large temperature, full-rank
   covariance) that won't hold for the next spec; has undefined
   behaviour on edge cases the current spec doesn't explicitly
   forbid but the next one might exercise.

3. **Load-bearing inefficiencies.** Performance issues that would
   prevent running the experiment at the scale the spec calls for,
   or that scale poorly with parameters the spec varies. NOT
   stylistic optimisations ("you could use np.einsum here"); only
   inefficiencies that block the spec's intended use. If unsure,
   err on the side of not flagging.

4. **Documentation inaccuracies.** For each documentation type:
   - **Design-decisions log**: claims that don't match the code
     (e.g. "we vectorise X" but the code loops), reasoning that
     elides a real alternative, decisions that have silently
     changed in the code without a log entry.
   - **Data-flow / shape documentation**: shape annotations or flow
     descriptions that don't match what the code actually does.
   - **Call graph or structural docs**: stale entries, missing
     edges, edges that no longer exist.
   - **Inline comments**: comments that contradict the code. Always
     flag — a wrong comment is worse than no comment, because it
     misleads.

5. **Documentation omissions.** Things load-bearing for understanding
   the code that aren't documented anywhere — not in the spec, not
   in the doc files, not in comments. A "load-bearing" omission is
   one where a labmate reading the code cold would predictably get
   stuck or make a wrong inference. Random unexplained constants,
   unstated invariants, non-obvious convention choices.

**Not in scope for you:**

- Style or formatting issues (linters cover this).
- Suggestions to add tests (the test red-team owns this).
- Suggestions to revise the spec (the spec red-team owns this). If
  you think a finding actually points at a spec problem rather than
  an implementation problem, flag it as `[spec-implication]` in the
  finding header; the triage will route it.
- Documentation that "would be nice to have" without a load-bearing
  reason. Wishlist items are out of scope.

For each finding, state:
- **Header**: short title with severity in brackets and any
  category tag (e.g. `[test-gap]`, `[spec-implication]`).
- **Location**: file + line range, or doc section.
- **Concern**: 2–4 sentences on what's wrong and why.
- **What would resolve it**: specific suggestion.
- **Touches**: code, docs, or both.

Be specific. Useless: "this function might be slow on large inputs."
Useful: "this function computes the m×n×n covariance tensor by a
triple Python loop over the batch dimension at lines 142–149; for the
m=1024 batch size the spec specifies in §3.2, this is approximately
~10⁶ Python-level operations per training step. Vectorise via the
batched outer product over axis 0."

**Ordering**: findings ordered by descending severity within each of
the five categories above, with the categories themselves in the
priority order listed (bugs first, then latent risks, then
inefficiencies, then doc inaccuracies, then doc omissions). Number
findings F1, F2, F3, ... *after* ordering, so F1 is the
highest-severity finding in the highest-priority category.

If you cannot find substantial issues in a category, say so directly.
Do not invent concerns to seem thorough.

Write your findings to `<DOC_PATH_DIR>/redteam-impl.md` in the
following format:

# Red-team review of <IMPL_NAME>

Reviewer: red-team sub-agent
Date: <YYYY-MM-DD>
Code version: <git commit hash if available>
Spec version reviewed against: <git commit hash if available>
Documentation version: <git commit hash if available>

## Summary

<one paragraph: qualitative impression of the implementation and its
documentation — does the code plausibly do what the spec calls for,
where is it most fragile, does the documentation track the code. No
counts of findings by severity; the list is the source of truth.>

## Findings

### F1: <short title> [severity: high] [<optional tag>]

**Location**: <file:lines or doc section>

**Concern**: <2–4 sentences>

**What would resolve it**: <specific suggestion>

**Touches**: <code | docs | both>

---

### F2: ...

## What the implementation gets right

<one paragraph, briefly. So the author knows what not to inadvertently
break when addressing the findings.>
```

## Annotation conventions in the redteam file

Same convention as `skills/red-team-spec.md` and `skills/red-team-tests.md`:
the human appends responses with `> M:` (or appropriate initial) and
Claude or the human appends confirmations with `> C:`, two newlines
between each. The redteam file becomes the audit trail for the
implementation red-team pass.

`> M?:` (with the question mark) is used for findings the human is not
equipped to evaluate without further explanation — typically when the
finding touches a numerical-stability argument, a non-obvious algorithmic
identity, or a performance claim the human can't size without help.
Distinct from `> M:` with uncertainty (which means the question is
understood but the answer is unclear): `> M?:` means the question itself
needs unpacking. Findings annotated `> M?:` are discussed in chat before
any `> C:` resolution is recorded.

Example after a full resolution cycle:

```markdown
### F4: Covariance update reuses unwhitened input [severity: high]

**Location**: src/infomax/sufficient_stats.py:88–104

**Concern**: The running covariance is updated using `x` directly,
but `x` has already been whitened in-place at line 76. The update
therefore computes the covariance of the whitened residual rather
than the raw input. Tests pass because the test suite only checks
the whitened second moment.

**What would resolve it**: Either compute the update before
whitening, or store a copy of the pre-whitening input and use it in
the update.

**Touches**: code, docs

> M: Apply — store a copy of the pre-whitening input. Update the
> data-flow doc to mark the pre-whitening copy as a named
> intermediate.

> C: Applied in commit 7c9a01e. Added `x_raw = x.copy()` at line 75
> before whitening; covariance update now uses `x_raw`. Data-flow
> doc updated with the named intermediate. Spec untouched.
```

This convention makes the redteam file the audit trail for the red-team
pass — what was flagged, what the human decided, what was done, all in
one place. See `workflows/invoke-red-team-on-impl.md` for the full
procedural workflow, including the three category-routing tags and the
post-edit verification step.

## After the redteam report exists

The triage follows the four-stage process in
`workflows/invoke-red-team-on-impl.md`: decide → update spec (if any) →
regenerate code and docs (flipping the status of any modified code file
in `CODEGEN_LOG.md` to `pending-tests`) → re-run tests one-by-one,
logging per-test commit hashes in `CODEGEN_LOG.md` and flipping the
modified files' status back to `done` once all tests pass. The
four-stage shape exists because findings in this red-team can touch up
to three artifacts (spec, code, docs including helper scripts), and the
regenerated code needs to be verified against the test suite before the
pass is closed. The `pending-tests → done` status flip follows the same
direction-asymmetry rule used elsewhere in the project: Claude flips
backwards on revision, forwards on verification.

For each finding, the outcome is one of:

- **Fix it** in the appropriate artifact (code, docs, helper script, or
  spec), append a `> C:` confirmation referencing the commit and any
  status changes.
- **Dismiss it** with a `> M:` justification, append a `> C:` confirming
  no change was made.
- **Route upstream**: findings tagged `[test-gap]` go to the test
  red-team's territory (they reveal a test that should have caught the
  bug); findings tagged `[spec-implication]` go to the spec red-team's
  territory (they reveal an under-specified or wrong piece of spec).
  Routed findings get a `> C:` noting the routing rather than an
  in-place fix. The downstream effect — re-running the relevant
  upstream red-team or scheduling one — is handled by the workflow,
  not this skill.

The redteam file is committed alongside the implementation, the docs,
and any spec changes that resulted from `[spec-implication]` routing.

## On the test failure branch

After the edits, the workflow re-runs the test suite. If a test fails
on the rerun, the failure is reported back to the human and decided
jointly. The failure can mean three things and the workflow does not
pre-commit to which:

- The edit was wrong (return to the relevant `> C:` and re-decide).
- A new finding has emerged that the red-team missed (add it to the
  redteam file as F_n+1 and triage it like the others).
- A test is wrong (route upstream as `[test-gap]`, same as during the
  original red-team).

This skill flags the junction; the workflow handles the dispatch.

## When to skip this skill

- The implementation is a trivial revision (renaming, comment fix,
  pure refactor with no behavioural change) of an already-red-teamed
  version. Note the prior redteam hash and move on.
- The implementation is explicitly a working draft, the test suite is
  incomplete, or the spec is not at `reviewed` status across the
  sections the implementation covers. Red-team only against a
  stabilised spec and a passing test suite.

## Provenance

This skill was extracted from the first implementation red-team session
(spec `000-static-infomax-fig1`); see the corresponding transcript in
`transcripts/` for the original reasoning. The five-category structure,
the `[test-gap]` and `[spec-implication]` routing tags, and the
test-failure branch were all decided during that session; this skill
codifies them so subsequent implementation red-teams don't rediscover
the shape.
'''

SKILL_RED_TEAM_RESULT = r'''# Skill: red-team-result

> Use this skill after an experiment in `experiments/NNN-*/` has been run,
> its figures and report (`REPORT.md`) have been written, and the relevant
> spec, tests, and implementation are all already at their post-red-team
> states. The goal is to find alternative explanations for the result
> before claiming it supports the hypothesis.

## Why this exists

This is the failure mode that bites scientists worst: a real experiment
produced a real number that looks like a real success, but the number is
explained by something other than the hypothesis. Common sources:

- A bug that happens to produce hypothesis-consistent results.
- A confound in the experimental design.
- A trivial baseline that would explain the result without the proposed
  mechanism.
- A statistical artifact from how the metric is computed.
- Overfitting to the specific seed / dataset / configuration.
- A figure that, read as a hostile reviewer would read it, says something
  weaker (or different) than the report claims.

A red-team sub-agent reading only the spec, the experiment plan, the
code, the figures, and the report — without the development context —
is well-placed to ask "what else could explain this?"

This is also the *last* red-team in the pipeline. All upstream artifacts
(spec, tests, implementation) have already been red-teamed and the
implementation passes the post-red-team test suite. So this red-team
faces a particular routing question that the earlier ones do not: a
finding can, in principle, send the workflow back to any earlier stage.
The skill names the four destinations and the workflow handles the
dispatch.

## How to invoke

Use the `Task` tool to spawn a sub-agent with the following prompt
template. Substitute `<EXPERIMENT_DIR>` with the path (e.g.,
`experiments/000-static-fig1`).

```
You are reviewing the experimental result documented in
<EXPERIMENT_DIR>/REPORT.md. The plan is in <EXPERIMENT_DIR>/PLAN.md.
The experiment code is at <EXPERIMENT_DIR>/run.py (or as named in the
plan). Relevant specs and code modules are referenced from the plan.
Provenance — the exact git commits, seed, and package versions used —
is in <EXPERIMENT_DIR>/output/provenance.json. Consult it whenever
"what version of the spec/code/tests was this run against?" matters
for a finding; the spec, code, or tests may have moved on since the
result was produced.

Context: the spec is at status `reviewed` across all relevant
sections, the test suite has been red-teamed, the implementation
passes the red-teamed test suite, and the implementation has itself
been red-teamed. So you are NOT auditing the math (settled), NOT
auditing test coverage against the spec (settled), and NOT auditing
the implementation against the spec (settled). Your job is the gap
between "the code ran cleanly and produced numbers/figures" and "the
result, as written up in the report, actually supports the claim the
report makes." Read the spec and the plan first, then the report
(including its figures), and only then the code. The "report first,
code second" order is deliberate — if you form a code-first picture
you will unconsciously correct for report inaccuracies and miss them.

## Alternative-explanation checklist

For each result claim, ask:

1. **Bug-as-feature**: could the result be produced by a specific bug?
   What is the simplest wrong implementation that would produce this
   exact result? Is there a test that would distinguish?

2. **Trivial baseline**: what does the simplest possible baseline
   produce on this task? If the baseline is not reported, that is a
   finding. Common skipped baselines: random predictor, constant
   predictor, nearest-neighbor with no learning, the input passed
   through unchanged.

3. **Confound**: is there a feature of the data or the protocol that
   could produce this result without the mechanism the hypothesis
   claims? Common confounds: class imbalance, leakage between train
   and test, a correlated nuisance variable, an unintended ordering
   in the data.

4. **Statistical artifact**: how does the metric behave under the
   null? If the result is a correlation, what is the correlation
   expected from noise alone given the sample size? If the result is
   an accuracy, what is the accuracy expected from chance, and is the
   gap large compared to the standard error?

5. **Seed / configuration sensitivity**: was the experiment run with
   a single seed? Single dataset split? Single hyperparameter? If
   yes, the result has unknown variance. Flag this and recommend the
   minimum robustness check (e.g., 3–5 seeds at a minimum).

6. **Cherry-picking risk**: how many configurations were tried before
   this one was reported? Is there a paper trail (in the experiment
   directory, the codegen log, or elsewhere) of the failed
   configurations? If not, flag the multiple-comparisons risk.

7. **Plot artifacts**: if a figure is the main result, examine it as
   a hostile reviewer would. Are axes truncated? Is the y-axis
   log-scale when linear would tell a different story (or vice
   versa)? Are error bars present and do they reflect what they
   appear to reflect (within-run variance vs. between-run variance
   vs. confidence interval)? Does the legend/caption say something
   the data does not support?

8. **Report-vs-result mismatch**: does the prose in the report claim
   more than the figures and numbers actually show? Common drifts:
   "X improves over Y" when the improvement is within noise,
   "robust" when only one or two conditions were tested, "scales"
   from two data points, qualitative reads of figures that the
   figures do not support.

9. **Sanity checks not run**: list checks the experiment did not run
   but should have. Common missing checks: does the model overfit a
   small dataset (basic capacity check)? Does the loss go down
   (basic training check)? Does the model behave reasonably on a
   held-out example you manually understand?

NOT in scope for the sub-agent:

- Style/formatting issues in the report (the human owns those).
- Suggestions for the next experiment unconnected to defending this
  one. Wishlist items are out of scope; only flag follow-up
  experiments that would resolve a specific concern about *this*
  result.
- Re-auditing the math, the test coverage, or the implementation
  against the spec. If a finding actually points at a problem in one
  of those upstream artifacts, tag it (see "Routing tags" below)
  rather than acting on it.

## Routing tags

The result red-team is the last in the pipeline, so a finding can in
principle imply that an earlier artifact was wrong. Tag findings
accordingly so the routing happens at discovery time, not on read:

- `[spec-implication]` — the result reveals that the spec is wrong,
  incomplete, or ambiguous in a way that mattered for the result.
  Routes to the spec red-team workflow rather than being acted on
  here.
- `[test-gap]` — the result reveals a class of bug that the test
  suite, even at its post-red-team state, would not catch. Routes
  to the test red-team workflow.
- `[code-implication]` — the result reveals a bug or mis-implementation
  in the code that the test suite happened to miss but that is
  scoped to the code, not the spec or tests. Routes back to the
  implementation red-team workflow (or directly to a code edit,
  per the human's judgement).
- (Untagged) — the finding is scoped to this experiment: a report
  edit, a code edit in the experiment's own `run.py`, a regenerated
  figure, an additional baseline run, or an acceptance note in the
  report.

A finding can carry at most one routing tag; if it implies issues at
multiple levels, pick the highest-leverage one and note the others
in the concern paragraph.

## Format

For each finding:
- **Concern**: a specific alternative explanation or risk.
- **Severity**: high (the result might not support the hypothesis at
  all), medium (the result needs an additional control to support
  the hypothesis cleanly), low (a check that should be added for
  defensibility, even if you do not expect it to change the
  conclusion).
- **Routing tag**: one of the above, or none.
- **What would resolve it**: a specific additional experiment,
  baseline, control, analysis, code edit, or report edit. If
  resolution requires touching an upstream artifact (spec, tests,
  implementation), say so.

**Ordering**: list findings in order of descending severity (high
first, then medium, then low). Within a severity level, order by
the checklist category above (bug-as-feature first, then trivial
baseline, then confound, etc.). Number findings F1, F2, F3, …
*after* ordering. Do not include counts of findings by severity in
the summary — the list below is the source of truth, and counts
produced separately tend to drift from the actual list.

Write the report to `<EXPERIMENT_DIR>/redteam-result.md`. Suggested
top-level structure:

# Red-team review of experiment <EXPERIMENT_NAME>

Reviewer: red-team sub-agent
Date: <YYYY-MM-DD>
Experiment commit: <git commit hash from provenance.json>
Spec commit(s) reviewed against: <as recorded in provenance.json>

## Summary

<one paragraph: qualitative impression — how strongly does the
result support the hypothesis as currently presented, what
alternative explanations are most concerning, what would change the
picture. No counts.>

## Findings

### F1: <short title> [severity: high] [routing: none | spec-implication | test-gap | code-implication]

**Concern**: <specific alternative explanation>

**What would resolve it**: <specific additional experiment / edit
/ analysis>

---

### F2: ...

## What the experiment gets right

<one paragraph, briefly.>

End the report with one paragraph: **If after addressing all your
concerns the hypothesis would still be supported, state that. If
your concerns are severe enough that the current result should not
be taken as evidence for the hypothesis, state that, in plain
language.**
```

## Annotation conventions in the redteam file

The redteam file is a living document, not a one-time report. After
the sub-agent writes it, the human and Claude Code annotate it in
place, so that the file at the end of the workflow is a complete
audit trail of which findings were applied, dismissed, or routed,
and why. The conventions match the other red-team skills:

- The human's first-pass reaction goes on a blank line two newlines
  below each finding, prefixed `> M:` (initial-of-author colon).
- A `> M:` annotation can be a confident *apply* instruction, a
  confident *dismiss* explanation, or an explicit *uncertain*
  question. The same prefix covers all three; the content
  disambiguates.
- For findings where the human cannot evaluate the suggestion well
  enough to apply or dismiss in good conscience — because the
  finding turns on statistical reasoning, mathematics, or
  experimental-design concepts the human does not yet command —
  use `> M?:` (note the question mark) rather than `> M:`. This is
  distinct from "uncertain" (`> M:` with a question): `> M?:` means
  "I'm not sure I understand the question." Findings annotated
  `> M?:` will be discussed in chat before any `> C:` resolution
  is recorded; Claude responds with a calibrated math/stats
  explainer, and the human upgrades the annotation to `> M:` once
  they can evaluate the finding. See
  `workflows/invoke-red-team-on-result.md` stage 3a for the
  promotion-to-tutorial rule.
- Claude Code's resolution goes on a blank line two newlines below
  the `> M:` annotation, prefixed `> C:`. Each `> C:` records
  *which artifact(s)* the change touches — the report, the
  experiment code, a figure (regenerated), an upstream artifact via
  a routing tag, or none (dismissed / accepted as limitation). When
  multiple artifacts are touched, list them all.

Example:

```
### F3: No constant-predictor baseline reported [severity: medium] [routing: none]

**Concern**: The reported accuracy of 0.62 is treated as evidence the
model has learned the structure, but the class distribution is
imbalanced (0.55 majority class). The gap to the constant predictor
is therefore 0.07, not 0.62, and the report does not make this
gap explicit.

**What would resolve it**: Run the constant-predictor baseline,
report the gap, and rewrite the relevant paragraph in REPORT.md.

> M: Confirmed, this is a real omission. Add the constant baseline
> to run.py, rerun, and reword the "Results" paragraph to lead with
> the gap-to-baseline rather than the raw accuracy.

> C: Applied. Added `_constant_baseline()` to run.py (touches
> experiment code), reran the experiment, regenerated Fig 2
> (touches figure), and rewrote the "Results" paragraph in
> REPORT.md (touches report). Commit <hash>.
```

For a routed finding the `> C:` records the routing rather than an
in-place edit:

```
> C: Routed. This is a [test-gap]: the test suite would not catch
> the off-by-one in the windowing function that produced the
> spurious correlation. Filed under the test red-team queue; no
> changes to this experiment until the test gap is resolved
> upstream.
```

For a finding that forces a return to an earlier stage of the
workflow, the `> C:` says so explicitly, and the in-experiment
processing pauses until the upstream artifact has been re-stabilised.
See the workflow file's stage 3a for the discussion convention.

## After the report exists

The redteam file is processed via `workflows/invoke-red-team-on-result.md`.
The workflow's stage 3 has four sub-stages, in order:

1. **Stage 3a — Decide.** First, ask the global question: do *any*
   findings, in aggregate or individually, force a return to an
   earlier stage of the workflow (spec / tests / implementation /
   docs)? If yes, surface that in chat before per-finding processing.
   If no, walk each finding top-down by severity, propose a `> C:`
   for confident `> M:` items, push back where you disagree, ask
   the human where they were uncertain, and respond with a
   calibrated explainer for `> M?:` items.
2. **Stage 3b — Update upstream artifacts (if applicable).** For
   findings tagged `[spec-implication]`, `[test-gap]`, or
   `[code-implication]` that were accepted, hand off to the
   corresponding upstream workflow rather than acting in place. In
   the simplest case (stage 3a determined no upstream return is
   needed and all routing tags were rejected) this stage is empty.
3. **Stage 3c — Apply.** Make the in-experiment edits to `run.py`,
   regenerate the affected figures by re-running the experiment,
   and edit the report text. As with the other red-team workflows,
   apply red colouring to changed regions of the report so the
   human can see the diff visually on re-read.
4. **Stage 3d — Finalise.** After the human has re-read the report
   and approved, remove the red colouring and commit the revision
   as a single commit.

If no high-severity findings remain unresolved (either applied or
explicitly accepted with a documented justification in the report),
the result is considered established. Per project convention, the
report should explicitly state the high-severity findings' resolution
status and link to follow-up experiments where any apply.

## Caveat

This is the red-team skill most prone to producing speculative
concerns that are not really problems — the broader the question,
the more space for hypothetical alternatives. Treat findings as
questions to investigate, not verdicts. The point is to make sure
these questions were asked, not to manufacture an answer of "the
result is wrong." Use the pushback license on `> M:` confident
applies liberally if a finding is genuinely a wishlist item dressed
as a concern.

## Provenance

The annotation conventions, the routing tags
(`[spec-implication]` / `[test-gap]` / `[code-implication]`), the
"return to earlier stage" first-pass check, and the four-sub-stage
processing shape were all decided during the first result red-team
session (experiment `000-static-fig1`); see the corresponding
transcript in `transcripts/` for the original reasoning. This skill
codifies them so subsequent result red-teams don't rediscover the
shape.
'''

TUTORIAL_README = r'''# tutorials/

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
'''

TUTORIAL_UV = r'''# uv — quick orientation

> A short orientation to uv as it's used in this project, plus pointers to
> the best external tutorials. Read this for the project-specific context;
> read the external tutorials for depth.

## What uv is, in two sentences

uv is a Rust-written replacement for `pip`, `pip-tools`, `virtualenv`,
and `pyenv` rolled into one tool. It is dramatically faster than the
tools it replaces and produces deterministic, fully-pinned environments
via a lockfile (`uv.lock`).

## Why we use it

Reproducibility. With `pip install` alone, two people doing
`pip install numpy` six months apart can end up with different
sub-dependency versions, producing subtly different numerical results.
`uv` solves this by recording every version of every package — direct
and transitive — in `uv.lock`, which is committed to the repo. Labmate
setup is one command (`uv sync`), and the result is byte-identical to
what the original developer had.

## The five commands you'll actually use

```bash
# One-time install of uv itself
curl -LsSf https://astral.sh/uv/install.sh | sh  # macOS / Linux
# (Windows: see the install link below)

# Once, when you first clone this repo
uv sync

# To run any Python script using the project's environment
uv run python my_script.py
# or, if it's a pytest:
uv run pytest

# To add a new dependency
uv add numpy
# or with a version constraint
uv add "numpy>=2.0"

# To update lockfile after editing pyproject.toml by hand
uv lock
```

That covers ~95% of day-to-day usage.

## Notes on project conventions

- We do **not** manually `source .venv/bin/activate`. Always `uv run`
  the command instead. This guarantees the right environment is used
  regardless of where you are in the terminal.
- `pyproject.toml` is hand-edited for dependency additions (use
  `uv add`, which edits it for you).
- `uv.lock` is **committed to git**. Do not edit it by hand.
- The `.venv/` directory is gitignored. It's regenerated from
  `uv.lock` via `uv sync`.

## When something goes wrong

- `uv sync` taking forever or failing: try `uv cache clean` to clear
  the package cache, then `uv sync` again.
- Wrong Python version: the project pins one via `requires-python` in
  `pyproject.toml`. If you don't have it installed, `uv python install
  3.11` (or whatever version we pin) fixes it.
- "I added a package but it's not available in my script": you ran
  `pip install` instead of `uv add`. Undo that and use `uv add`.

## External material

For depth:

- **Official docs (canonical, current)**: https://docs.astral.sh/uv/
- **Real Python tutorial (thorough, with a sample project)**: https://realpython.com/python-uv/
- **DataCamp's comparison-with-pip guide**: https://www.datacamp.com/tutorial/python-uv

If you have an hour and want to actually understand uv, read the Real
Python tutorial. If you want a five-minute reference, the official docs
quickstart is enough.

## What you do *not* need to learn yet

uv has features for publishing packages, workspaces, scripts with inline
dependency metadata, and more. None are used in this project right now.
If you find yourself needing them, the docs are organised well enough to
look up the relevant guide.
'''

TUTORIAL_GH = r'''# gh (GitHub CLI) — quick orientation

> A short orientation to gh as it's used in this project, plus pointers
> to good external tutorials. Read this for the project context; read the
> linked material for depth.

## What gh is

GitHub's official command-line tool. It does on the command line what
you'd otherwise do via the GitHub web UI: create repos, open pull
requests, manage issues, check CI status, etc. It is *not* a replacement
for `git` — `git` manages local commits and branches, `gh` manages the
GitHub-specific layer (PRs, issues, workflow runs).

## Why we use it

Three reasons:

1. **Authentication for `git push`.** On macOS particularly, `gh auth
   setup-git` is the cleanest way to configure git's credentials for
   pushing to GitHub. One-time setup, then `git push` works without
   prompts.
2. **Creating the GitHub repo.** `gh repo create` skips the
   web-UI-then-paste-URL dance.
3. **Issues and PRs from the terminal.** Once labmates start
   contributing, you'll want to triage issues without context-switching.

## One-time setup

```bash
# Install
brew install gh                      # macOS
# (Windows / Linux: see the install link below)

# Authenticate (interactive — browser-based OAuth)
gh auth login

# Configure git to use gh's credentials for HTTPS pushes
gh auth setup-git
```

After this, `git push` to any GitHub repo just works, and you can use
all the `gh` commands.

## Commands you'll use in this project

```bash
# Create a new repo from the current directory
gh repo create REPO_NAME --public --source . --push

# Open the repo's web page in the browser
gh browse

# List open issues
gh issue list

# Create a new issue from the terminal
gh issue create --title "..." --body "..."

# View a specific PR
gh pr view 123
gh pr view 123 --comments    # with all review comments inline

# Create a PR for the current branch
gh pr create --fill   # uses the latest commit message
# or with explicit fields:
gh pr create --title "..." --body "..." --base main

# Check status of CI on the current PR
gh pr checks
```

## A useful daily-driver tip

`gh pr view --web` opens the current branch's PR in the browser — fastest
way to switch from terminal to GitHub UI when you need the visual diff
view or want to leave a review comment.

## External material

For depth:

- **Official quickstart**: https://docs.github.com/en/github-cli/github-cli/quickstart
- **Practical patterns guide (PR workflows, gh api scripting)**:
  https://32blog.com/en/cli/cli-github-cli-gh
- **Codecademy walkthrough**: https://www.codecademy.com/article/github-cli-tutorial
- **Full command reference**: https://cli.github.com/manual/

The quickstart is enough for our project's current needs. The patterns
guide is worth reading once you start doing PR-heavy work.

## What `gh` doesn't replace

`git` itself. `gh` is the GitHub-specific layer; `git` is the version
control system. You still need to know `git add`, `git commit`,
`git push`, `git branch`, etc. They're complementary.

If your terminal git skills are rusty, the Pro Git book is the canonical
reference (https://git-scm.com/book) — chapters 1-3 are the daily-driver
material.
'''

TUTORIAL_RNG_PASSING = r'''# Passing random generators — how and why

> A project-specific tutorial on how we handle randomness in code. The
> conventions are stricter than typical Python practice, and the
> rationale matters as much as the mechanics.

## The problem we're avoiding

Most Python code that uses numpy randomness looks like this:

```python
# In some library file
def add_noise(x):
    return x + np.random.normal(0, 1, x.shape)

# In some other file
np.random.seed(42)
y = add_noise(x)
```

This *appears* reproducible: same seed, same output. But it has a silent
failure mode. The `np.random.normal()` call reads from a single global
random state, shared by every function in every imported library. If
*anything* — a new import, a logging library that uses RNG internally,
a different version of some package that calls `np.random.rand()` in
its constructor — changes the sequence of calls between `np.random.seed(42)`
and `add_noise(x)`, the output silently changes. Months later when
someone tries to reproduce the result, they get a different number.

This is not theoretical. It is one of the most common reproducibility
failures in scientific Python code.

## The fix

Don't use `np.random.*` at all in this project. Instead, pass around an
explicit `np.random.Generator` object. The same example, done right:

```python
# In some library file
def add_noise(x, rng):
    return x + rng.normal(0, 1, x.shape)

# In some other file
rng = np.random.default_rng(42)
y = add_noise(x, rng)
```

The `rng` is a self-contained object. Its state is not affected by what
any other library does. The same seed produces the same sequence of
calls from this generator, regardless of import order, regardless of
package versions, regardless of any other randomness happening
elsewhere.

## The basic patterns

### Pattern 1: function takes an rng argument

```python
def some_function(x: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    noise = rng.standard_normal(x.shape)
    return x + noise
```

The function does not construct an rng itself. Whoever calls it is
responsible for providing one.

### Pattern 2: the top level of an experiment constructs the rng

```python
# experiments/000-static-fig1/run.py
import numpy as np
from infomax.ba import blahut_arimoto

def main(seed: int):
    rng = np.random.default_rng(seed)
    result = blahut_arimoto(..., rng=rng)
    ...
```

One rng per experiment, constructed at the top, threaded through
everything downstream.

### Pattern 3: tests have visible hardcoded seeds

```python
def test_some_property():
    rng = np.random.default_rng(20260518)
    data = make_random_input(rng)
    ...
```

Seed is a literal number directly in the test code, not a constant
imported from elsewhere. Greppable, transparent, deterministic.

### Pattern 4: spawning independent streams

If a function needs multiple statistically-independent random streams
(e.g., one for initialisation, one for evaluation), use `rng.spawn`:

```python
rng = np.random.default_rng(seed)
init_rng, eval_rng = rng.spawn(2)

initial_state = make_init(init_rng)
evaluate_with(initial_state, eval_rng)
```

This is better than creating two separate rngs from `seed` and
`seed + 1` — `spawn` guarantees statistical independence; ad-hoc seeds
do not.

### Pattern 5: rngs in classes

```python
class BlahutArimoto:
    def __init__(self, rng: np.random.Generator, ...):
        self._rng = rng

    def step(self):
        # use self._rng inside
        ...
```

Pass at construction; store as a private attribute. Methods that need
randomness use `self._rng`.

## What you do *not* do

```python
# ✗ Forbidden: global state
np.random.normal(0, 1)
np.random.rand(10)
np.random.seed(42)

# ✗ Forbidden: constructing a generator inside library code with no seed
rng = np.random.default_rng()    # in src/

# ✗ Forbidden: hidden seeds (constants imported from elsewhere)
from project_config import TEST_SEED
rng = np.random.default_rng(TEST_SEED)   # not greppable

# ✗ Forbidden: relying on time or process state for seeding in
# experiments
seed = int(time.time())   # produces irreproducible results
```

## Where notebooks fit in

Prototyping in notebooks is the one place the rule relaxes slightly.
You don't have to thread the rng through every cell — but you should
still construct one at the top:

```python
# First cell of any notebook that uses randomness:
import numpy as np
rng = np.random.default_rng(20260518)
```

Then use `rng.random()` etc. throughout. Never use `np.random.rand()`
even in notebooks. The cost of typing `rng.` is trivial.

If a notebook produces a result that gets reported anywhere (a figure
in the report, a table in the spec), the same provenance treatment as
experiments applies — see `skills/manage-randomness.md`.

## PyTorch (for when we get there)

The same conventions apply with `torch.Generator`:

```python
def init_weights(shape, generator: torch.Generator) -> torch.Tensor:
    return torch.randn(shape, generator=generator)

# At the top of an experiment:
gen = torch.Generator(device="cpu")
gen.manual_seed(20260518)
```

`torch.manual_seed` (the global one) is only acceptable at the very top
of an experiment script, never in library code. And even there, we
prefer the explicit `torch.Generator()` pattern for consistency.

CUDA non-determinism is a separate beast not covered by this
convention; see `skills/manage-randomness.md` for what's known and
what's still v1-pending.

## Why we're strict about this

Two reasons.

**Reason 1: silent failures are the worst kind.** Code that silently
produces different results under invisible changes (a new import, a
package upgrade) is worse than code that crashes. Crashes get fixed;
silent numerical drift produces papers that don't replicate.

**Reason 2: the cost is tiny once it's a habit.** "Pass an rng" is one
extra argument. The discipline is fully transferred after about a
week of writing this way.

## External material

If you want to read more:

- **Albert Thomas, "Best Practices for Using NumPy's Random Number
  Generators"** (on the scientific-python blog):
  https://blog.scientific-python.org/numpy/numpy-rng/
  — The most thorough treatment, including parallelism and `spawn`.
- **Built In, "NumPy Random Seed: How It Works and Why to Stop Using
  It"**: https://builtin.com/data-science/numpy-random-seed
  — Good general-audience framing of the global-state problem.
- **NumPy docs, Random Generator reference**:
  https://numpy.org/doc/stable/reference/random/generator.html
  — Canonical API reference.

The Albert Thomas piece is the one to read.

## When the convention bites

There are two cases where the rule will feel onerous, and one workaround
that is *not* acceptable.

**Case 1: third-party library that calls `np.random` internally.** Some
older sklearn / scipy code reads from the global state. The fix is
usually to pass a `random_state` argument that those libraries accept
(`KMeans(random_state=42)`, etc.). If a library genuinely has no way to
take an explicit rng, document it as a known reproducibility risk in the
experiment's `README.md`.

**Case 2: deeply nested calls where threading the rng is painful.** If
you're passing rng through five layers of function calls, the API is
probably wrong — consider whether the randomness should be moved to
the top of the call chain.

**The not-acceptable workaround**: setting the global seed at the top
of an experiment as a "belt and suspenders" measure. Don't. Setting
`np.random.seed(42)` *and* using explicit rngs implies the global state
matters, which suggests it might somewhere — and means you can't trust
the explicit rng pattern. Pick one approach. We pick explicit.
'''

TUTORIAL_MATH_KKT = r'''# KKT conditions, calibrated to Blahut-Arimoto

> Just-in-time math explainer triggered by red-team findings on
> `specs/000-static-infomax-fig1.md`. Goal: enough KKT to evaluate
> claims about the BA-optimal prior, not a general theory of
> constrained optimisation. For the latter, see Boyd &
> Vandenberghe, *Convex Optimization*, §5.5.

## What problem are we solving

Blahut-Arimoto finds the input distribution $p^*(\theta)$ over a
finite alphabet that maximises the mutual information $I(\Theta; X)$
through a fixed channel $p(x|\theta)$. The optimisation problem:

$$
\max_{p(\theta)} I(\Theta; X) \quad \text{subject to} \quad
\sum_\theta p(\theta) = 1, \quad p(\theta) \ge 0 \text{ for all } \theta.
$$

Two kinds of constraint: one equality (probabilities sum to 1), $m$
inequalities (probabilities nonnegative, where $m$ is the alphabet
size). KKT is the right tool because we have inequality constraints
and want a *characterisation* of the optimum, not just a numerical
method.

## The KKT conditions in one paragraph of generality

For a problem
$$
\max f(x) \quad \text{s.t.} \quad g_i(x) \le 0, \ h_j(x) = 0
$$
with $f, g_i, h_j$ differentiable, a point $x^*$ that is optimal
satisfies:

1. **Stationarity**: $\nabla f(x^*) = \sum_i \mu_i \nabla g_i(x^*)
   + \sum_j \lambda_j \nabla h_j(x^*)$ for some multipliers
   $\mu_i, \lambda_j$.
2. **Primal feasibility**: $g_i(x^*) \le 0$, $h_j(x^*) = 0$.
3. **Dual feasibility**: $\mu_i \ge 0$ (for $\le$ constraints).
4. **Complementary slackness**: $\mu_i g_i(x^*) = 0$ for every $i$.

For convex problems (and the BA problem is convex in $p(\theta)$
once you fix the right parameterisation — see below), these are
sufficient as well as necessary.

The condition that does most of the work in our case is
**complementary slackness**: for each inequality constraint, either
the multiplier is zero *or* the constraint is active (holds with
equality). Active means "the constraint is binding at the
optimum"; the multiplier nonzero means "loosening the constraint
would let us do better."

## What the conditions say in the BA case

Set up the Lagrangian for the BA problem:

$$
\mathcal{L}(p, \lambda, \mu) = I(\Theta; X) - \lambda \left(\sum_\theta p(\theta) - 1\right) + \sum_\theta \mu_\theta p(\theta).
$$

The sign convention on the $\mu$ term is "+" because we wrote the
inequality as $-p(\theta) \le 0$ and then absorbed the minus sign.
This is one of the small bookkeeping points where signs get flipped
in red-team findings — worth doing slowly when checking a derivation.

Stationarity (differentiate w.r.t. $p(\theta)$, treating each
$p(\theta)$ as an independent variable):

$$
\frac{\partial I(\Theta; X)}{\partial p(\theta)} - \lambda + \mu_\theta = 0.
$$

The mutual-information derivative is a standard result:

$$
\frac{\partial I(\Theta; X)}{\partial p(\theta)} = D\big(p(x|\theta) \,\|\, p(x)\big),
$$

where $D(\cdot \| \cdot)$ is the KL divergence between the
conditional output distribution given input $\theta$ and the
marginal output distribution. Call this quantity $c(\theta)$ — it
is the "per-input contribution" to the mutual information.

Substituting:

$$
c(\theta) = \lambda - \mu_\theta.
$$

Now apply complementary slackness $\mu_\theta p(\theta) = 0$:

- If $p^*(\theta) > 0$: then $\mu_\theta = 0$, so $c(\theta) = \lambda$.
- If $p^*(\theta) = 0$: then $\mu_\theta \ge 0$, so $c(\theta) \le \lambda$.

This is the characterisation we wanted. **At the BA optimum, every
input with positive probability contributes the same per-input
information $\lambda$; inputs with zero probability contribute at
most $\lambda$.** The shared value $\lambda$ is the channel
capacity.

## Why this is the right tool, in one sentence

The reason KKT (rather than Lagrange multipliers alone) is the
correct framework is the inequality constraint $p(\theta) \ge 0$:
the BA optimum can have some inputs at zero probability (the
"three-atom solution" your eye test is checking for, where only 3
of $m$ inputs get used), and a pure Lagrange-multipliers
formulation can't represent this correctly — it would give
multipliers for the equality but no condition for which inputs are
active.

## What a red-team finding in this region might be flagging

Common failure modes in BA derivations or implementations:

1. **Wrong sign on $\mu_\theta$.** If the inequality is written
   $p(\theta) \ge 0$ vs $-p(\theta) \le 0$ inconsistently across
   the derivation, the $\mu$ term lands with the wrong sign in
   stationarity, and the final characterisation has the wrong
   direction for inputs at zero probability. Check: in the
   end-state characterisation, inputs at zero probability should
   have $c(\theta) \le \lambda$, not $\ge$. The "support set"
   of the optimum has the *high*-information inputs.
2. **Conflating "contribution at the optimum" with "contribution
   at iterate $t$".** The KKT characterisation holds *at the
   fixed point*. During BA iteration, the per-input contributions
   $c(\theta)$ are not yet equalised; the algorithm is in the
   process of moving probability mass toward inputs with above-
   average $c(\theta)$. Implementations that check "are
   contributions equal" as a *convergence* criterion are using
   the KKT condition correctly; implementations that check it
   *during* an iteration as a step-validity condition are
   misusing it.
3. **Forgetting complementary slackness when proving uniqueness or
   support-size claims.** "The optimum has support on at most $K$
   inputs" claims usually rest on the inactive-constraint side
   of complementary slackness, where $p^*(\theta) = 0$ is forced
   for inputs with $c(\theta) < \lambda$. A red-team finding that
   asks "why can't the optimum have full support?" is asking for
   this argument explicitly.

## When you'd want general KKT, not this calibration

If you find yourself working on a problem with multiple inequality
constraints that interact (not just nonnegativity), or with a
non-convex objective where KKT is necessary but not sufficient, the
calibrated story above is too thin. At that point read Boyd &
Vandenberghe §5.5 in full; the project-specific calibration only
takes you through the BA-shaped uses.

## Provenance

Triggered by red-team finding(s) on `specs/000-static-infomax-fig1.md`
referencing KKT-based characterisation of the BA optimum. If
subsequent specs raise KKT for other constrained-optimisation
problems (rate-distortion, capacity with cost constraints), expand
this file or split into siblings rather than rewriting the BA-
specific content.
'''

PYPROJECT_TOML = r'''[project]
name = "dynamic_infomax"
version = "0.0.0"
requires-python = ">=3.11"
dependencies = []

[dependency-groups]
dev = ["pytest", "ruff"]
'''

WORKFLOW_ISSUES_STUB = r'''# Workflow issues and improvements

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

<!-- Add entries here as they come up. -->

---

## Resolved / dismissed

<!-- Entries move here when closed, with a one-line resolution note. -->
'''

README_MD = r'''# dynamic_infomax

Research project on [one-line description here].

## Quick start

```bash
git clone <this-repo-url>
cd dynamic_infomax
uv sync                      # creates .venv, installs deps from uv.lock
# Read AGENTS.md before doing anything else.
```

## Local setup

### One-time, system-level

- **[uv](https://docs.astral.sh/uv/)** — Python environment manager.
  Required. Install with one of:

  ```bash
  curl -LsSf https://astral.sh/uv/install.sh | sh   # official installer
  brew install uv                                    # macOS, via Homebrew
  ```

  The official installer drops a single binary into `~/.local/bin/` and
  finishes in seconds; the Homebrew route pulls a dependency chain and
  can be slow.

- **[gh](https://cli.github.com/)** — GitHub CLI. Only needed if you
  push to the repo or create PRs from the command line; not needed to
  read or run the code. Install with `brew install gh` on macOS and then
  `gh auth login`.

See `tutorials/uv.md` and `tutorials/gh.md` for short project-specific
orientations to these tools.

### Python environment

```bash
uv sync          # one-time setup, regenerates .venv from uv.lock
uv run pytest    # run the test suite
uv run python experiments/<NNN-name>/run.py
```

Never `pip install` — use `uv add <pkg>` (or `uv add --group dev <pkg>`
for tooling). See the *Dependencies* section in `AGENTS.md` for the
full convention.

## For collaborators

This project uses an LLM-assisted workflow designed for transparency between
supervisors, students, and AI collaborators. The conventions are documented
in `AGENTS.md`. The skills that Claude follows are in `skills/`. The audit
trail of past sessions is in `transcripts/`.

If you are new here, read in this order:

1. `AGENTS.md` — what we're doing and how
2. `skills/README.md` — the procedural conventions Claude follows
3. `tutorials/` — short orientations to the tools we use
4. `meta/what-worked.md` — patterns that have proven useful
5. `meta/what-didnt.md` — anti-patterns to avoid
'''

GITIGNORE = r'''# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
dist/
*.egg-info/
.pytest_cache/
.ruff_cache/
.mypy_cache/
.venv/
venv/
env/

# Jupyter
.ipynb_checkpoints/

# LaTeX
*.aux
*.log
*.out
*.toc
*.synctex.gz
*.bbl
*.blg
*.fdb_latexmk
*.fls

# Editors
.vscode/
.idea/
*.swp
*.swo
.DS_Store

# Environment / secrets
.env
.env.local
*.key
*.pem

# Experiment outputs (big files we don't want in git)
experiments/*/output/
experiments/*/data/
experiments/*/checkpoints/
*.ckpt
*.pt
*.pth

# Transcripts that might contain sensitive info — review before committing
# (Comment out the next line if you want to commit transcripts by default)
# transcripts/
'''

SKILLS_README = r'''# skills/

Each file in this directory is a procedural skill that Claude should follow
when the relevant task comes up. Claude Code reads `AGENTS.md` first, then
loads skills from here as needed.

## Current skills

Procedural skills (what to do for a recurring task):

- `write-math-spec.md` — turning an idea into a specification in `specs/`
- `derive-test-suite.md` — going from spec to test suite before code
- `document-experiment.md` — structuring an entry in `experiments/`
- `manage-randomness.md` — randomness and provenance conventions for any
  code that touches an RNG

Red-team skills (adversarial review at each stage of the pipeline):

- `red-team-spec.md` — find what's wrong with a spec before code is written
- `red-team-tests.md` — find vacuous tests and coverage gaps
- `red-team-implementation.md` — find what passes-the-tests misses
- `red-team-result.md` — find alternative explanations for the result

Each red-team skill has a sibling workflow file in `workflows/` that
orchestrates invocation, annotation, and post-report processing.

## Adding a new skill

A skill is a markdown file with:

1. A clear name (kebab-case, .md extension)
2. A one-sentence description at the top (used for matching)
3. The procedure itself, written for Claude to follow

Skills should be discovered, not designed: when you find yourself repeating
the same instruction across sessions, extract it into a skill.
'''

ORIG_SKILL_WRITE_MATH_SPEC = r'''# Skill: write-math-spec

> Use this skill when turning an idea or a paper concept into a formal
> specification in `specs/`, before any code is written.

## Goal

A math spec is a self-contained document that defines:

1. The objects involved (variables, spaces, distributions)
2. The relationships between them (equations, constraints)
3. The procedure or algorithm in pseudocode
4. The properties the implementation should satisfy

A spec is **framework-agnostic** — it does not commit to PyTorch vs JAX, or
to any particular tensor shape convention. It describes the math.

## Procedure

1. **Find the source.** Locate the idea — usually a file in `notes/` or
   `resources/`. If the idea exists only in conversation, write a one-page
   note in `notes/` first and link to it.

2. **Name the spec.** `specs/NNN-short-name.md`, where NNN is a zero-padded
   sequence number. Look at the existing files to pick the next number.

3. **Open with a status table.** Every spec begins with a status table
   immediately after the title. The table is the single source of truth
   for which sections have been reviewed and what downstream work is
   permitted. See "Status table" below.

4. **Structure the spec with these sections, in order:**

   - **Context** — one paragraph: what problem this solves, what came before.
   - **Setup** — definitions of all symbols. Use a notation table if there are
     more than 5 symbols.
   - **Generative model** (if applicable) — a plate-notation diagram for any
     probabilistic content. See "Visuals" below.
   - **Objective** — the formal objective function or property of interest.
   - **Derivation** — the math, with steps a reader can verify.
   - **Algorithm** — pseudocode. Use plain numbered steps with mathematical
     notation. If a data-flow or control-flow diagram would clarify the
     algorithm, include one (see "Visuals").
   - **Properties to verify** — what an implementation should satisfy. These
     become the test suite. Be specific: "the loss is invariant under
     permutation of the batch dimension" is good; "it should work" is not.
     - **Eye test** — A figure (or small set of figures) whose qualitative features can be
       inspected by a human to confirm the implementation is roughly correct
       before the full quantitative test suite is run.
     - **Sweep design** — every choice the test code will need to make
       about *what values are tested* is pinned here, not in the test
       file. See "Sweep design" below.
   - **Report** — what the experiment script (`experiments/NNN-*/run.py`)
     will produce: figures, tables, files. The Report section is the
     spec's contract with the experiment script: every choice the
     script will make about *what to plot, at what density, with what
     formatting* is pinned here. See "Report" below.
   - **Open questions** — anything you're unsure about. Mark with `[?]`.
   - **References** — papers, prior work. Use `[CITATION NEEDED]` if unsure.
   - **Revision log** — appended below as the spec is revised. See
     "Revision log" below.

5. **Ask before guessing.** If the source is ambiguous on a definition or
   choice, ask the human collaborator. Do not silently pick a convention.

## Status table

Every spec opens with a table that tracks per-section review status:

```markdown
| Section | Status | Date |
|---|---|---|
| Context | draft | — |
| Setup | draft | — |
| Generative model | draft | — |
| Objective | draft | — |
| Derivation | draft | — |
| Algorithm | draft | — |
| Properties to verify | draft | — |
```

### Status values

- `draft` — written, not yet human-reviewed.
- `reviewed` — read carefully by the human collaborator and accepted.
- `needs-revision` — read and not accepted; specific concerns documented
  in the section itself (e.g., a `> [!note]` callout) or in
  `meta/what-didnt.md` with a `[spec-format]` tag.

Sections move from `draft` to `reviewed` (or `needs-revision`) only by
direct edit to the table. No justification line is required — the
deliberate edit *is* the act of review. If the human cannot bring
themselves to type the change, that itself indicates the section is not
actually reviewed.

The status table is also where omissions show up: if the spec doesn't
have a "Generative model" section because the math isn't probabilistic,
remove that row rather than leaving it as `draft`. An honest table is
small.

### Status transitions on revision

A `reviewed` section is not permanent. Any non-trivial edit to a
`reviewed` section drops it back to `draft`. This is not a punishment;
it is the recognition that the review was performed against a version
of the section that no longer exists. The downstream-approval rules
(below) then apply again: tests written against the old version may be
stale, implementation against the old version may be wrong, experiments
run against the old version may need to be rerun.

When Claude Code does a revision round, do them according to the > M: comments inline and add a Revision log entry categorising it as Correction/Clarification/Refinement. Then flip back the corresponding status entry to `draft`.

When you flip a section back to `draft` because of a revision, add an
entry to the revision log (see below) describing what changed and why.

### Who flips the status

The asymmetry is deliberate.

- **Forward transitions** (`draft → reviewed`) require a direct edit by
  the human collaborator. Claude does not flip a section to `reviewed`
  under any circumstance, even if asked to. The deliberate edit is the
  act of review.

- **Backward transitions** (`needs-revision → draft`) on revision are performed by whoever makes the
  revision — usually Claude Code, sometimes the human. When Claude
  applies a non-trivial edit to a `reviewed` section, Claude flips that
  section's status row back to `draft` as part of the same edit.
  This is automatic; the human does not have to ask.

  The rationale: forgetting to flip a section back to `draft` after a
  revision is a silent failure that would let downstream work proceed
  against an unreviewed section. The cost of that failure is much higher
  than the cost of a redundant flip.

### What each approval unlocks

The status table gates downstream work to prevent building on
unexamined foundations:

- **Setup + Objective both `reviewed`** → Claude may sketch the test
  scaffolding in `tests/test_NNN_*.py`: file structure, fixtures,
  imports, naming conventions. No actual property tests yet.
- **Derivation `reviewed`** → Claude may write the mathematical-property
  tests against the spec's "Properties to verify" section.
- **Algorithm `reviewed`** → Claude may write the implementation in
  `src/`.
- **All sections `reviewed`** → the spec is approved for red-team review
  (see `skills/red-team-spec.md`) and then for the experiment phase.

Downstream work is permitted but not automatic. Always confirm with the
human before starting the next stage.

## Visuals

Visual elements belong in specs when they clarify something prose
cannot. The default conventions:

### Generative models and probabilistic structure

Use **daft** (Python plate-notation package). Install with `pip install
daft`. The source script and the rendered SVG both live in `diagrams/`,
named to match the spec: a script at `diagrams/NNN-short-name-pgm.py`
producing `diagrams/NNN-short-name-pgm.svg`. The spec embeds the SVG:

```markdown
![Generative model](../diagrams/NNN-short-name-pgm.svg)
```

A minimal daft script template:

```python
"""Plate-notation diagram for spec NNN-short-name.

Run: python diagrams/NNN-short-name-pgm.py
Output: diagrams/NNN-short-name-pgm.svg
"""
import daft

pgm = daft.PGM()
# pgm.add_node("z", r"$z$", x=1, y=2)
# pgm.add_node("x", r"$x$", x=1, y=1, observed=True)
# pgm.add_edge("z", "x")
pgm.render()
pgm.savefig("diagrams/NNN-short-name-pgm.svg")
```

Both the script and the SVG are committed. The script is the source of
truth; the SVG is for rendering inside markdown.

Use daft for plate notation with simple node labels (single symbols,
basic subscripts, Greek letters). If a diagram needs richer math inside
nodes — long expressions, multi-line content, complex alignment —
escalate to TikZ (`tikz-bayesnet` LaTeX library). Note the escalation
in `meta/workflow-issues.md`.

### Algorithm / data-flow diagrams

Use **Mermaid** embedded directly inline in the spec markdown. GitHub,
VSCode preview, and Obsidian all render Mermaid natively. Example:

````markdown
```mermaid
graph LR
  X[Input X] --> F[Encoder f]
  F --> Z[Latent Z]
  Z --> G[Decoder g]
  G --> Y[Reconstruction Y]
```
````

No external rendering step. The text in the markdown *is* the diagram.

### When to include a diagram

A diagram earns its place when:

- The setup involves a graphical model. **Always** include a plate
  diagram for any spec with probabilistic structure.
- The algorithm has nontrivial control flow (branches, loops over
  populations, alternating updates).
- The data flow is hard to follow from prose alone.

A spec without a single diagram is a yellow flag: probabilistic content
without a plate diagram is usually under-specified, and an algorithm
without a flow diagram is often hiding a step.

## Sweep design

Any test that varies a quantity across runs — parameter sweeps, grid
resolution sweeps, sample-size sweeps, seed sweeps — implicitly
chooses *which values to test at*. Those choices are part of the
spec's contract with the test code. If they live only in the test
file, the spec cannot be reviewed against the property it actually
asserts: a sparser sweep tests a weaker property than a dense one.

Every property in "Properties to verify" that involves a sweep must
state, in the spec:

- **Variable swept** — name, in the notation of the Setup section.
- **Values** — the explicit tuple (e.g. `m ∈ {1, 2, 5, 20, 100}`) or
  a deterministic generator (e.g. "logarithmically spaced, 8 points,
  from 1 to 100").
- **Why this density** — one line. "Captures the small-m discrete
  regime, the mid-range, and the asymptotic regime"; or "Mattingly
  Fig 1 uses exactly these values"; or "denser than `{1, 10, 100}`
  was needed to see the K(m) growth". The reason matters because it
  is the criterion a reviewer applies when asking whether the sweep
  is dense enough.
- **Coverage relative to other sweeps in the spec** — if the
  experiment script (§ Report) runs a denser or different sweep,
  state explicitly that the test sweep is a subset, and why a
  smaller subset suffices for the property.
- **Randomness** — for any test that draws random values (perturbed
  initialisations, random inputs), the seed and the distribution
  parameters live in the spec, not the test file. "perturbation
  drawn from `1 + 0.1 · N(0, 1)`, seed 20260518" is a complete
  spec-side description; "a small random perturbation" is not.

A sweep choice that the human collaborator did not explicitly make
is an *auto-decision*. Auto-decisions are not forbidden — they are
often fine — but they must be marked explicitly in the spec, e.g.
`(auto-chosen by codegen; please confirm)`. The spec review then
either ratifies them or sends them back. Codegen must not write a
test file containing a sweep that has no corresponding entry in this
subsection.

The cost of skipping this subsection is exactly the failure mode
that motivated it: a test passes, results land, and only retrospect
reveals that the sweep was too sparse to detect the bug, or too
dense to be worth the compute. Both are recoverable if the choice is
visible; neither is if it is buried in the test file.

## Report

The Report section is the spec's contract with the experiment
script (`experiments/NNN-short-name/run.py`). Its purpose is
specifically to pin the choices that, if left implicit in the
script, would force a future reviewer to read `run.py` to
understand what the experiment measured. That set of choices is
small and reasonably well-defined; the section should be too.

What belongs in Report:

- **Outputs.** A flat list naming each artefact the script
  produces — figures, tables, the report file itself — with a
  one-line description of content. Paths relative to
  `experiments/NNN-*/`.

- **Sweep coverage per output.** For each output, whether it uses
  the full sweep defined in the spec or a subset. If a subset,
  *which* subset and *why* a smaller one suffices. The default is
  that the experiment uses the same sweep as the spec — naming a
  subset is the deviation that needs justification.

- **Auxiliary grids and reference curves.** Any evaluation grid,
  query grid, or analytic reference curve that the script uses
  *beyond* the swept variable. Density and bounds. (For a CDF
  comparison: the query grid size. For an analytic limit overlay:
  what is being plotted and what range.) These count because they
  determine what comparison is actually being made; they are spec
  decisions, not styling decisions.

- **Table schema.** For each persisted table (`results_table.json`
  or similar): the list of columns, one row's worth of meaning,
  and — importantly — *what is computed but not persisted*. The
  decision to drop bulky intermediates from a saved table is a
  spec decision because it determines what later analysis can
  re-derive without re-running the experiment.

What does not belong in Report:

- Figure dimensions, DPI, layout grids, marker sizes, colour
  choices, axis-tick formatting, legend placement, alpha values.
  These are properties of the script, not of the experiment.
- Reproductions of figure captions, or word-by-word descriptions
  of what a panel "shows". A one-line "what is being plotted"
  description per figure is enough; specifics belong in the
  script and in `REPORT.md` itself.
- File-format minutiae (PNG vs SVG, indent level of the JSON)
  unless a specific choice is load-bearing for downstream use.

The test of whether a Report subsection is at the right level: a
reviewer reading it should be able to tell whether the
*experiment* is well-designed — sweep wide enough, density of any
secondary grid fine enough, table columns sufficient — without
forming any opinion about whether the *figures will look nice*.

Auto-decisions in the Report section are flagged the same way as
in Sweep design: `(auto-chosen by codegen; please confirm)`. The
same review-and-ratify rule applies.

## Revision log

Every non-trivial change to a spec after its first review is recorded
in a revision log at the bottom of the spec. Each entry has a date, a
category, and a short description.

### Format

```markdown
## Revision log

### YYYY-MM-DD — Category (Section §X.Y)

What changed, why, and how it was discovered. If the change affects
downstream artifacts (tests, implementation, experiments), note the
implication explicitly.
```

### Categories

Each revision falls into one of three categories. The category matters
because it determines what downstream work is affected:

- **Correction** — the math was wrong. The previous version of the
  section is now known to be incorrect. Any tests, implementation, or
  experimental results downstream of the corrected section are
  potentially invalid and must be reviewed.

- **Clarification** — the math was consistent but ambiguous. The
  section now pins down a choice that was previously implicit. Usually
  no implementation change is needed (the implementation already made
  some choice; the spec just now documents it), but tests may need to
  be sharpened to enforce the now-explicit choice.

- **Refinement** — the spec is extended with additional content. Prior
  work against the spec remains valid; new tests and possibly new
  implementation are added to cover the extension.

When in doubt between categories, escalate: prefer Correction over
Clarification, prefer Clarification over Refinement. The cost of
re-checking work that didn't need re-checking is much smaller than the
cost of trusting work that did.

### When to add a revision log entry

- Always, when flipping a `reviewed` section back to `draft`.
- Always, after substantive content changes to any section, even if the
  section was still at `draft`. The reasoning helps future review.
- Not needed for typo fixes, formatting tweaks, or pure prose
  clarifications that change no claims.

## Output

A new file at `specs/NNN-short-name.md` with all sections at `draft`
status, plus the diagram source and rendered files in `diagrams/`. The
spec should be readable by a labmate who has not seen the source idea.
After the first revision, the spec also has a revision log at the
bottom recording how it evolved.

'''

ORIG_SKILL_DERIVE_TEST_SUITE = r'''# Skill: derive-test-suite

> Use this skill when going from a spec in `specs/` to a test suite in
> `tests/`, before the implementation is written.

## Goal

The test suite is the executable form of the spec's "Properties to verify"
section, plus enough additional cases that an implementation passing all
tests is very likely correct.

## Procedure

1. **Read the spec.** Identify the "Properties to verify" section. Each
   property becomes at least one test.

2. **Name the test file.** `tests/test_NNN_short_name.py`, mirroring the
   spec filename.

3. **Cover these categories:**

   - **Sanity tests** — trivial inputs the function must handle without
     crashing (empty input, single sample, etc.).
   - **Mathematical properties** — invariances, symmetries, conservation
     laws stated in the spec. Use `numpy.testing.assert_allclose` or
     `torch.testing.assert_close` with explicit tolerances.
   - **Edge cases** — boundaries of the input space, degenerate distributions,
     extreme values.
   - **Known-answer cases** — inputs for which the correct output is known
     analytically. These are the most valuable tests; spend time finding them.
   - **Consistency tests** — outputs that should agree across different code
     paths (e.g., a vectorized implementation should match a scalar one).

4. **Use `pytest`.** Each test is one function `def test_...():`. Group
   related tests in a class if it helps. Use `pytest.fixture` for shared
   setup. Use `pytest.mark.parametrize` for varying inputs.

5. **Follow the project's randomness conventions.** See
   `skills/manage-randomness.md`. In particular: tests that use randomness
   construct their own generator with a literal hardcoded seed at the top
   of the test. No global RNG state.

6. **Leave the implementation as `NotImplementedError` placeholders.** The
   tests should fail in a meaningful way before any implementation exists.
   Run `pytest` to confirm all tests fail with the expected errors.

7. **Comment generously.** Each test should have a docstring stating *why*
   it exists — what property of the spec it verifies. A reviewer should be
   able to read the test and check that it really tests what it claims.

8. **Update the spec's properties-to-tests table.** This is a durable
   visualization of test coverage and is required output. See below.

## Properties-to-tests table

The spec's "Properties to verify" section gets a column (or a companion
table) naming the test(s) that verify each property. This converts the
spec's bullet list of properties into a bidirectional map between spec
and tests, and makes coverage gaps visible at a glance.

### Format

Add the column to the existing properties table if the spec already has
one, or add a "Verified by" subsection after the properties list. The
table looks like:

```markdown
| # | Property | Verified by |
|---|---|---|
| P1 | I_tau is non-decreasing under BA iteration | `test_ba_iteration_is_monotonic` |
| P2 | Converged I equals channel capacity | `test_ba_converges_to_capacity` |
| P3 | Atom centroids invariant under grid refinement | `test_atom_centroids_grid_invariant` |
| P4 | KS distance to Jeffreys < 0.05 at m=100 | `test_jeffreys_limit` |
| P5 | Atom count in [1, ceil(log2(m))+1] | *no test yet* |
```

Conventions:

- The "Verified by" cell names a test function, fully qualified within
  the test file (`test_ba_iteration_is_monotonic`, not `test_monotonic`).
- If multiple tests verify a property, list all of them, comma-separated.
- If a property is verified only weakly (e.g., on a single input where
  many would be needed), note this: `test_x (single input only)`.
- If no test verifies a property, write `*no test yet*` in italics. The
  italic markup makes gaps grep-able and visually distinct.
- If a property is intentionally not testable (e.g., a claim about
  asymptotic behaviour that can only be verified empirically in an
  experiment, not unit-tested), write `*not unit-testable; see experiment
  NNN*` and ensure the named experiment exists.

### Why this is required output

Three reasons:

1. **Gap visibility.** The italic `*no test yet*` entries are the
   visualization of (a) coverage of the spec by the tests. Easier to
   spot than re-reading the spec and the tests separately.

2. **Bidirectional verifiability.** A CI script (or a careful reader)
   can check two things from this table: every property has a test (or
   a documented reason it doesn't), and every named test actually
   exists in the test file. The table is the contract between the two
   files.

3. **Survives revision.** When a spec is revised (per the
   Correction/Clarification/Refinement categories in
   `skills/write-math-spec.md`), the table makes it immediately
   apparent which tests are downstream of the revised property.

### Maintenance

The table is updated as part of the same change that adds, removes, or
modifies a test. Specifically:

- Adding a new test → add or update the relevant row.
- Removing a test → either update the row or, if the property is now
  unverified, change the entry to `*no test yet*`.
- Adding a property to the spec → add a row with `*no test yet*` until
  a test is written.
- Revising a property → reconsider whether the existing test still
  verifies the revised property; update or replace as needed.

If the table drifts from reality (a named test doesn't exist, or a
test exists but isn't in the table), that's a bug to fix, not a
finding to dismiss.

## Output

A new file at `tests/test_NNN_short_name.py`, with all tests currently
failing. Plus stub files in `src/` if needed so that imports resolve.
The spec is updated to include the properties-to-tests table; this
update is committed together with the new test file. The spec status
table is *not* changed by this step — adding a coverage table is not a
revision to any reviewed section, just an addition reflecting the new
test artifact.

### Eye test file

The eye test specified in the spec gets its own file:
`tests/test_NNN_short_name_eyetest.py`, sibling to the main test file
`tests/test_NNN_short_name.py`. The eye-test file is structurally
different from the main test file:

- It does *not* contain pytest assertions. It is a standalone script.
- It is runnable as `python tests/test_NNN_*_eyetest.py` and produces
  one or more figures, saved to `tests/figures/NNN_short_name/`.
- It prints to stdout a short reminder that human approval is required
  before the full test suite runs.
- It is *not* picked up by pytest in CI. Either name it without the
  `test_` prefix and use a redirecting filename, or add it to the
  pytest ignore list — pick whichever is cleaner in the project's
  current pytest configuration.

The eye test file uses the same randomness conventions as the rest of
the suite (literal hardcoded seed at the top), so reruns are
reproducible without rerunning the implementation.
'''

ORIG_SKILL_DOCUMENT_EXPERIMENT = r'''# Skill: document-experiment

> Use this skill when starting or completing an experiment in `experiments/`.

## Goal

Every experiment is a directory containing enough information that a
labmate (or future you) can:

1. Understand what question the experiment was trying to answer
2. Reproduce the run
3. Read the results without re-running the code

## Procedure for starting an experiment

1. **Create the directory.** `experiments/NNN-short-name/`, sequence number
   continuing from existing experiments.

2. **Write a `PLAN.md`** with:

   - **Question** — one sentence. What are we trying to learn?
   - **Hypothesis** — what we expect to see, and why.
   - **Method** — pointers to specs/code involved, plus the experimental
     setup (hyperparameters, datasets, seeds).
   - **Success criteria** — how will we know if the hypothesis is supported?
   - **Failure modes to watch for** — what could go wrong and silently
     produce a misleading result?

3. **Set up the directory:**
   ```
   experiments/NNN-short-name/
   ├── PLAN.md
   ├── run.py            # or run.sh — the entry point
   ├── config.yaml       # or .toml — the configuration
   ├── output/           # gitignored
   └── README.md         # written after the experiment, see below
   ```

## Procedure for completing an experiment

After the experiment is run, write a `README.md` in the experiment directory:

- **Result** — one paragraph. What happened.
- **Figures** — embed or link the key plots.
- **Interpretation** — does this support the hypothesis? What does it mean?
- **What I'd do differently** — for the next iteration.
- **Provenance** — git commit hash, date, hardware, runtime.

## Output

A new `experiments/NNN-short-name/` directory with `PLAN.md` initially, then
`README.md` and results after the run.
'''

META_WHAT_WORKED = r'''# What worked

> Patterns, prompts, and conventions that have proven useful. Add to this
> file when you notice something working well — don't wait until the project
> is done.

## Format

Each entry: a short title, a one-paragraph description, optionally a date
and a context note. Most useful entries will eventually graduate into a
skill in `skills/` or a convention in `AGENTS.md`.

## Entries

<!-- Add entries below as the project progresses. -->
'''

META_WHAT_DIDNT = r'''# What didn't work

> Anti-patterns, failure modes, and prompts that produced bad output.
> Recording these is at least as valuable as recording what worked.

## Format

Each entry: a short title, what was tried, what went wrong, and (if known)
why. Anti-patterns inform the conventions in `AGENTS.md` and the warnings
in `skills/`.

## Entries

<!-- Add entries below as the project progresses. -->
'''

# Map of relative paths to seed contents
SEED_FILES: dict[str, str] = {
    "AGENTS.md": AGENTS_MD,
    "README.md": README_MD,
    ".gitignore": GITIGNORE,
    "pyproject.toml": PYPROJECT_TOML,
    "skills/README.md": SKILLS_README,
    "skills/write-math-spec.md": ORIG_SKILL_WRITE_MATH_SPEC,
    "skills/derive-test-suite.md": ORIG_SKILL_DERIVE_TEST_SUITE,
    "skills/document-experiment.md": ORIG_SKILL_DOCUMENT_EXPERIMENT,
    "skills/manage-randomness.md": SKILL_MANAGE_RANDOMNESS,
    "skills/red-team-spec.md": SKILL_RED_TEAM_SPEC,
    "skills/red-team-tests.md": SKILL_RED_TEAM_TESTS,
    "skills/red-team-implementation.md": SKILL_RED_TEAM_IMPLEMENTATION,
    "skills/red-team-result.md": SKILL_RED_TEAM_RESULT,
    "tutorials/README.md": TUTORIAL_README,
    "tutorials/uv.md": TUTORIAL_UV,
    "tutorials/gh.md": TUTORIAL_GH,
    "tutorials/rng-passing.md": TUTORIAL_RNG_PASSING,
    "tutorials/math/kkt.md": TUTORIAL_MATH_KKT,
    "meta/what-worked.md": META_WHAT_WORKED,
    "meta/what-didnt.md": META_WHAT_DIDNT,
    "meta/workflow-issues.md": WORKFLOW_ISSUES_STUB,
}


# Directories that should have a .gitkeep so they're tracked even when empty
GITKEEP_DIRS = ["notes", "resources", "specs", "src", "tests",
                "diagrams", "experiments", "transcripts", "docs",
                "workflows"]


# ---------------------------------------------------------------------------
# Logic
# ---------------------------------------------------------------------------

def log(msg: str, *, level: str = "info") -> None:
    prefix = {"info": "  ", "ok": "✓ ", "skip": "· ", "warn": "! "}.get(level, "  ")
    print(f"{prefix}{msg}")


def make_directories(root: Path) -> None:
    for d in DIRECTORIES:
        p = root / d
        if p.exists():
            log(f"directory exists: {d}/", level="skip")
        else:
            p.mkdir(parents=True)
            log(f"created directory: {d}/", level="ok")


def write_seed_files(root: Path) -> None:
    for rel_path, content in SEED_FILES.items():
        p = root / rel_path
        if p.exists():
            log(f"file exists, not overwriting: {rel_path}", level="skip")
        else:
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(content, encoding="utf-8")
            log(f"created file: {rel_path}", level="ok")


def write_gitkeeps(root: Path) -> None:
    for d in GITKEEP_DIRS:
        p = root / d / ".gitkeep"
        # Only add .gitkeep if the directory is empty (no other files)
        if p.parent.exists() and not any(
            child for child in p.parent.iterdir() if child.name != ".gitkeep"
        ):
            if not p.exists():
                p.write_text("", encoding="utf-8")
                log(f"created .gitkeep in: {d}/", level="ok")


def darwin_git_fix(root: Path) -> None:
    """On macOS with Apple's bundled git, HTTPS pushes to GitHub stall during
    object upload due to an HTTP/2 issue. The fix is to use HTTP/1.1 for git
    over HTTPS. Apply locally on Darwin so we don't change the user's global
    git config. See workflow-issues entry on macOS git HTTP/1.1 fix.
    """
    if platform.system() != "Darwin":
        log("git http.version: HTTP/2 (default) — non-Darwin platform", level="info")
        return
    if not (root / ".git").exists():
        # git_init failed earlier; nothing to configure
        return
    try:
        subprocess.run(
            ["git", "config", "http.version", "HTTP/1.1"],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
        )
        log("set git http.version = HTTP/1.1 (macOS HTTPS push fix)", level="ok")
        log("  (workaround for HTTP/2 push stall with Apple's bundled git)", level="info")
    except (FileNotFoundError, subprocess.CalledProcessError) as e:
        msg = e.stderr.strip() if isinstance(e, subprocess.CalledProcessError) else str(e)
        log(f"could not set http.version: {msg}", level="warn")


def git_init(root: Path) -> None:
    """Initialize a git repo if one doesn't already exist."""
    if (root / ".git").exists():
        log("git repository already initialized", level="skip")
        return
    try:
        subprocess.run(
            ["git", "init", "-b", "main"],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
        )
        log("initialized git repository (branch: main)", level="ok")
    except FileNotFoundError:
        log("git not found on PATH — skipping git init", level="warn")
    except subprocess.CalledProcessError as e:
        # Older git versions don't support -b; fall back
        try:
            subprocess.run(
                ["git", "init"], cwd=root, check=True, capture_output=True, text=True
            )
            log("initialized git repository (default branch)", level="ok")
        except subprocess.CalledProcessError:
            log(f"git init failed: {e.stderr.strip()}", level="warn")


def uv_init(root: Path) -> None:
    """Run `uv sync` to create the .venv and produce uv.lock.

    Gracefully handles the absence of uv: prints an instruction and continues.
    Gracefully handles uv failures (e.g. missing Python 3.11): prints the
    output and continues. The labmate can fix the underlying issue and re-run
    `uv sync` themselves; the rest of the bootstrap is independent of uv.
    """
    try:
        subprocess.run(["uv", "--version"], check=True, capture_output=True, text=True)
    except (FileNotFoundError, subprocess.CalledProcessError):
        log("uv not found on PATH — skipping environment setup", level="warn")
        log("  install uv from https://docs.astral.sh/uv/ then run `uv sync`", level="info")
        return
    log("running `uv sync` to create the project environment...", level="info")
    try:
        result = subprocess.run(
            ["uv", "sync"], cwd=root, check=True, capture_output=True, text=True
        )
        log("uv sync complete (.venv created, uv.lock pinned)", level="ok")
        # Surface any uv warnings
        if result.stderr.strip():
            for line in result.stderr.strip().splitlines():
                log(f"  uv: {line}", level="info")
    except subprocess.CalledProcessError as e:
        log("uv sync failed — fix the issue below and re-run `uv sync` by hand:", level="warn")
        for line in (e.stderr or e.stdout or "").strip().splitlines():
            log(f"  {line}", level="info")


def print_next_steps(root: Path) -> None:
    print()
    print("─" * 60)
    print("Bootstrap complete.")
    print("─" * 60)
    print(f"Project location: {root.resolve()}")
    print()
    print("Suggested next steps:")
    print(f"  1.  cd {root}")
    print("  2.  Drop your existing latex source into resources/")
    print("  3.  If `uv sync` was skipped above, install uv and run it now:")
    print("        curl -LsSf https://astral.sh/uv/install.sh | sh")
    print("        uv sync")
    print("  4.  Open the Code panel in Claude desktop (or run `claude`)")
    print("      from this directory — Claude will read AGENTS.md.")
    print("  5.  Ask Claude to create the GitHub repo:")
    print("        gh repo create dynamic_infomax --public --source . --push")
    print("      (or do it yourself if you prefer)")
    print()
    print("Notes for labmates new to the workflow:")
    print("  - Read AGENTS.md before doing anything else.")
    print("  - See tutorials/ for short orientations to uv, gh, RNG handling.")
    print()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--path",
        type=Path,
        default=Path.cwd() / PROJECT_NAME,
        help=f"Where to create the project (default: ./{PROJECT_NAME})",
    )
    args = parser.parse_args()

    root: Path = args.path
    print(f"Bootstrapping {PROJECT_NAME} at: {root}")
    print()

    root.mkdir(parents=True, exist_ok=True)
    make_directories(root)
    write_seed_files(root)
    write_gitkeeps(root)
    git_init(root)
    darwin_git_fix(root)
    uv_init(root)
    print_next_steps(root)
    return 0


if __name__ == "__main__":
    sys.exit(main())
