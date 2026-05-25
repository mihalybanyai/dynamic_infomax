# dynamic_infomax

Research project on [one-line description here].

## Artifacts in need of action

- specs/001-infomax-betting.md: review from 1.2 onward
- notes/infomax_aprv_seed.md: review and generate spec
- notes/real_world_analogues.md: review and decide if implies action
- notes/daisy_chain_derivation.md: review and resolve

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

### Editor (optional)

VSCode can render the Mermaid diagram in `meta/workflow-overview.md`
inline via the **Markdown Preview Mermaid Support** extension (by
Matt Bierner — search the extension marketplace, or install from
[the page](https://marketplace.visualstudio.com/items?itemName=bierner.markdown-mermaid)).
Once installed, opening any `.md` file containing a fenced
`mermaid` code block and triggering the markdown preview
(`Cmd+Shift+V` on macOS, `Ctrl+Shift+V` elsewhere) renders the
diagram in place.

Not strictly required — the diagram's source is human-readable, and
GitHub's web view renders mermaid blocks natively when browsing the
repo online. The extension just makes local reading nicer.

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
