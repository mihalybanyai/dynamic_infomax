"""Generate the Mermaid call graphs of `src/infomax/` for spec 002's documentation.

Runs `code2flow` on the package and emits two graphs:

- the module graph: one node per module, one edge per pair of modules with at least one
  call between them, labelled with the number of distinct function-to-function calls.
  Printed to stdout, for `docs/002-foreign-q-prediction/README.md`'s *Call graph*.
- the function graph: every function code2flow finds, grouped by module, written to
  `call_graph_functions.md` beside this script (with `--functions`).

code2flow traces calls by name. It misses most calls through an instance, such as
`prior.log_marginal(...)` inside `score.score_cell`, so the module graph adds a dashed
edge for every package import behind which code2flow traced no call. Matching by name
also invents calls: every `rng.uniform(...)` is taken for spec 000's `GridPrior.uniform`
and `set.add` for `pstar._Net.add`. Cross-module edges into those two (`MISRESOLVED`) are
dropped; checked against the imports on 2026-11-27, they were the only false ones.
Re-run when `src/infomax/` changes.

Usage:
    uv run python docs/002-foreign-q-prediction/_make_call_graph.py [--functions]
"""
from __future__ import annotations

import ast
import json
import subprocess
import sys
import tempfile
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parent.parent
SRC_DIR = REPO_ROOT / "src" / "infomax"


MISRESOLVED: frozenset[str] = frozenset({"prior::GridPrior.uniform", "pstar::_Net.add"})
"""Targets code2flow matches to library calls of the same name (`Generator.uniform`, `set.add`)."""


def _module(name: str) -> str:
    return name.split("::", maxsplit=1)[0] if "::" in name else "<module>"


def _graph() -> dict:
    with tempfile.TemporaryDirectory() as td:
        out = Path(td) / "graph.json"
        subprocess.run(
            ["code2flow", str(SRC_DIR), "--output", str(out), "--language", "py", "--quiet"],
            check=True,
        )
        graph = json.loads(out.read_text())["graph"]
    nodes = graph["nodes"]

    def real(e: dict) -> bool:
        src, dst = nodes[e["source"]]["name"], nodes[e["target"]]["name"]
        return not (dst in MISRESOLVED and _module(src) != _module(dst))

    graph["edges"] = [e for e in graph["edges"] if real(e)]
    return graph


def _imports() -> dict[str, set[str]]:
    """{module: package modules it imports}, from the source."""
    out: dict[str, set[str]] = {}
    for path in sorted(SRC_DIR.glob("*.py")):
        if path.name.startswith("_"):
            continue
        found: set[str] = set()
        for node in ast.walk(ast.parse(path.read_text())):
            if isinstance(node, ast.ImportFrom) and node.module and node.module.startswith("infomax."):
                found.add(node.module.split(".")[1])
        out[path.stem] = found
    return out


def _label(name: str) -> str:
    return name.rsplit("::", maxsplit=1)[-1].replace("(global)", "<module>")


def _safe(s: str) -> str:
    return "".join(c if c.isalnum() else "_" for c in s)


def module_graph(graph: dict) -> str:
    nodes = graph["nodes"]
    modules = sorted({p.stem for p in SRC_DIR.glob("*.py") if not p.name.startswith("_")})
    pairs: Counter = Counter()
    for e in graph["edges"]:
        a, b = _module(nodes[e["source"]]["name"]), _module(nodes[e["target"]]["name"])
        if a != b:
            pairs[(a, b)] += 1
    lines = ["```mermaid", "flowchart LR"]
    lines += [f'    {_safe(m)}["{m}.py"]' for m in modules]
    lines += [f"    {_safe(a)} -->|{n}| {_safe(b)}" for (a, b), n in sorted(pairs.items())]
    for a, deps in sorted(_imports().items()):
        lines += [f"    {_safe(a)} -.->|import| {_safe(b)}" for b in sorted(deps) if (a, b) not in pairs]
    lines.append("```")
    return "\n".join(lines) + "\n"


def function_graph(graph: dict) -> str:
    nodes = graph["nodes"]
    by_module: dict[str, list[tuple[str, str]]] = {}
    for node_id, info in nodes.items():
        by_module.setdefault(_module(info["name"]), []).append((_safe(node_id), _label(info["name"])))
    lines = ["```mermaid", "flowchart LR"]
    for m, items in sorted(by_module.items()):
        lines.append(f'    subgraph {_safe(m)}["{m}.py"]')
        lines += [f'        {i}["{lab}"]' for i, lab in sorted(items, key=lambda t: t[1])]
        lines.append("    end")
    seen: set[tuple[str, str]] = set()
    for e in graph["edges"]:
        pair = (_safe(e["source"]), _safe(e["target"]))
        if pair not in seen:
            seen.add(pair)
            lines.append(f"    {pair[0]} --> {pair[1]}")
    lines.append("```")
    return "\n".join(lines) + "\n"


def main() -> None:
    graph = _graph()
    sys.stdout.write(module_graph(graph))
    if "--functions" in sys.argv[1:]:
        n, k = len(graph["nodes"]), len({(e["source"], e["target"]) for e in graph["edges"]})
        header = (
            "# Spec 002 — function-level call graph\n\n"
            f"Generated by `_make_call_graph.py --functions` from `src/infomax/` with `code2flow`: "
            f"{n} functions and {k} calls. Calls through an instance (a prior's methods called "
            "from the scoring code) are mostly missing; see the script's docstring. The module "
            "graph in [README.md](README.md#call-graph) is the readable summary.\n\n"
        )
        (HERE / "call_graph_functions.md").write_text(header + function_graph(graph))


if __name__ == "__main__":
    main()
