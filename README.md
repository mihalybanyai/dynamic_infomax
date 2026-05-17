# dynamic_infomax

Research project on [one-line description here].

## Quick start

```bash
git clone <this-repo-url>
cd dynamic_infomax
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

### Python environment

From the repo root:

```bash
uv sync
```

This reads `pyproject.toml` and `uv.lock`, provisions a Python 3.11+
interpreter if needed, and creates `.venv/` with the pinned dependencies
— both the runtime ones (`numpy`, `scipy`, `matplotlib`, `pytest`) and
the `dev` group used for project tooling (`pypdf` for reading PDFs in
`resources/`, `daft-pgm` for plate-notation diagrams in `diagrams/`).

Run commands inside the env with `uv run …` (e.g. `uv run pytest`,
`uv run python diagrams/000-static-infomax-fig1-pgm.py`), or activate
the venv with `source .venv/bin/activate`.

### What we deliberately *don't* install

- **poppler / pdftotext / pdftoppm.** PDF text extraction in this repo
  goes through `pypdf` (pure Python, no system deps). Poppler is a
  heavy Homebrew install with a long dependency chain and is only
  worth it if you need raster page rendering. See
  `meta/workflow-issues.md` → "Default to lightweight PDF tools in
  skills".

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
