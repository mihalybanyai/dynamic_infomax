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
    "src",              # code
    "tests",            # tests
    "diagrams",         # mermaid / tikz / svg, generated alongside code
    "experiments",      # one subdir per experiment, each with its own PLAN.md
    "transcripts",      # raw chat logs (the audit trail)
    "meta",             # notes about the workflow itself, for the eventual guide
]

# ---------------------------------------------------------------------------
# Seed file contents
# ---------------------------------------------------------------------------

AGENTS_MD = """# AGENTS.md — Project handbook for human and AI collaborators

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
"""

README_MD = """# dynamic_infomax

Research project on [one-line description here].

## Quick start

```bash
git clone <this-repo-url>
cd dynamic_infomax
# Read AGENTS.md before doing anything else.
```

## For collaborators

This project uses an LLM-assisted workflow designed for transparency between
supervisors, students, and AI collaborators. The conventions are documented
in `AGENTS.md`. The skills that Claude follows are in `skills/`. The audit
trail of past sessions is in `transcripts/`.

If you are new here, read in this order:

1. `AGENTS.md` — what we're doing and how
2. `skills/README.md` — the procedural conventions Claude follows
3. `meta/what-worked.md` — patterns that have proven useful
4. `meta/what-didnt.md` — anti-patterns to avoid
"""

GITIGNORE = """# Python
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
"""

SKILLS_README = """# skills/

Each file in this directory is a procedural skill that Claude should follow
when the relevant task comes up. Claude Code reads `AGENTS.md` first, then
loads skills from here as needed.

## Current skills

- `write-math-spec.md` — turning an idea into a specification in `specs/`
- `derive-test-suite.md` — going from spec to test suite before code
- `document-experiment.md` — structuring an entry in `experiments/`

## Adding a new skill

A skill is a markdown file with:

1. A clear name (kebab-case, .md extension)
2. A one-sentence description at the top (used for matching)
3. The procedure itself, written for Claude to follow

Skills should be discovered, not designed: when you find yourself repeating
the same instruction across sessions, extract it into a skill.
"""

SKILL_WRITE_MATH_SPEC = """# Skill: write-math-spec

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

3. **Structure the spec with these sections, in order:**

   - **Context** — one paragraph: what problem this solves, what came before.
   - **Setup** — definitions of all symbols. Use a notation table if there are
     more than 5 symbols.
   - **Objective** — the formal objective function or property of interest.
   - **Derivation** — the math, with steps a reader can verify.
   - **Algorithm** — pseudocode. Use the convention in `skills/pseudocode-style.md`
     if it exists; otherwise use plain numbered steps with mathematical notation.
   - **Properties to verify** — what an implementation should satisfy. These
     become the test suite. Be specific: "the loss is invariant under
     permutation of the batch dimension" is good; "it should work" is not.
   - **Open questions** — anything you're unsure about. Mark with `[?]`.
   - **References** — papers, prior work. Use `[CITATION NEEDED]` if unsure.

4. **Ask before guessing.** If the source is ambiguous on a definition or
   choice, ask the human collaborator. Do not silently pick a convention.

5. **Diagram if it helps.** If the setup involves a graphical model, an
   architecture, or a data flow, produce a Mermaid or TikZ diagram in
   `diagrams/` and link to it from the spec.

## Output

A new file at `specs/NNN-short-name.md`, plus possibly a diagram. The spec
should be readable by a labmate who has not seen the source idea.
"""

SKILL_DERIVE_TEST_SUITE = """# Skill: derive-test-suite

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

5. **Leave the implementation as `NotImplementedError` placeholders.** The
   tests should fail in a meaningful way before any implementation exists.
   Run `pytest` to confirm all tests fail with the expected errors.

6. **Comment generously.** Each test should have a docstring stating *why*
   it exists — what property of the spec it verifies. A reviewer should be
   able to read the test and check that it really tests what it claims.

## Output

A new file at `tests/test_NNN_short_name.py`, with all tests currently
failing. Plus stub files in `src/` if needed so that imports resolve.
"""

SKILL_DOCUMENT_EXPERIMENT = """# Skill: document-experiment

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
"""

META_WHAT_WORKED = """# What worked

> Patterns, prompts, and conventions that have proven useful. Add to this
> file when you notice something working well — don't wait until the project
> is done.

## Format

Each entry: a short title, a one-paragraph description, optionally a date
and a context note. Most useful entries will eventually graduate into a
skill in `skills/` or a convention in `AGENTS.md`.

## Entries

<!-- Add entries below as the project progresses. -->
"""

META_WHAT_DIDNT = """# What didn't work

> Anti-patterns, failure modes, and prompts that produced bad output.
> Recording these is at least as valuable as recording what worked.

## Format

Each entry: a short title, what was tried, what went wrong, and (if known)
why. Anti-patterns inform the conventions in `AGENTS.md` and the warnings
in `skills/`.

## Entries

<!-- Add entries below as the project progresses. -->
"""

# Map of relative paths to seed contents
SEED_FILES: dict[str, str] = {
    "AGENTS.md": AGENTS_MD,
    "README.md": README_MD,
    ".gitignore": GITIGNORE,
    "skills/README.md": SKILLS_README,
    "skills/write-math-spec.md": SKILL_WRITE_MATH_SPEC,
    "skills/derive-test-suite.md": SKILL_DERIVE_TEST_SUITE,
    "skills/document-experiment.md": SKILL_DOCUMENT_EXPERIMENT,
    "meta/what-worked.md": META_WHAT_WORKED,
    "meta/what-didnt.md": META_WHAT_DIDNT,
}

# Directories that should have a .gitkeep so they're tracked even when empty
GITKEEP_DIRS = ["notes", "resources", "specs", "src", "tests",
                "diagrams", "experiments", "transcripts"]


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
    print("  3.  Open the Code panel in Claude desktop (or run `claude`)")
    print("      from this directory — Claude will read AGENTS.md.")
    print("  4.  Ask Claude to create the GitHub repo:")
    print("        gh repo create dynamic_infomax --public --source . --push")
    print("      (or do it yourself if you prefer)")
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
    print_next_steps(root)
    return 0


if __name__ == "__main__":
    sys.exit(main())
