# uv — quick orientation

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
