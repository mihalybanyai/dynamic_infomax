"""Generate a Mermaid call graph of the `src/infomax/` package.

Runs `code2flow` on the package, parses its JSON output, and emits a
Mermaid `flowchart` block. An AST pass supplements code2flow: modules
with no intra-package call edges still appear as subgraphs with their
public top-level functions as nodes, so the graph reflects the full
package surface rather than only the reachable call graph. The intent
is to paste the block into `docs/000-static-infomax-fig1/README.md`.
Re-run if `src/infomax/` changes.

Usage:
    uv run python docs/000-static-infomax-fig1/_make_call_graph.py
"""
from __future__ import annotations

import ast
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SRC_DIR = REPO_ROOT / "src" / "infomax"


def _shorten(name: str) -> str:
    """Strip the leading file path and parens; keep e.g. `ba::blahut_arimoto`."""
    last = name.rsplit("::", maxsplit=1)[-1]
    return last.replace("(global)", "<module>")


def _file_of(name: str) -> str:
    """File component of code2flow's qualified name (`ba::foo` → `ba`)."""
    if "::" not in name:
        return "<module>"
    return name.split("::", maxsplit=1)[0]


def _ast_top_level_functions(src_dir: Path) -> dict[str, list[str]]:
    """Return {module_stem: [function_name]} for all public top-level functions.

    Used as a fallback: modules that code2flow produces zero nodes for
    (e.g. because their functions only make instance-method calls that
    static analysis cannot trace) still appear in the call graph.
    Only non-private files (not starting with `_`) and non-private
    functions (not starting with `_`) are included.
    """
    result: dict[str, list[str]] = {}
    for py_file in sorted(src_dir.glob("*.py")):
        if py_file.name.startswith("_"):
            continue
        stem = py_file.stem
        tree = ast.parse(py_file.read_text())
        names: list[str] = []
        for node in ast.iter_child_nodes(tree):
            if isinstance(node, ast.FunctionDef) and not node.name.startswith("_"):
                names.append(node.name)
        result[stem] = names
    return result


def main() -> None:
    with tempfile.TemporaryDirectory() as td:
        json_path = Path(td) / "graph.json"
        subprocess.run(
            [
                "code2flow",
                str(SRC_DIR),
                "--output",
                str(json_path),
                "--language",
                "py",
                "--quiet",
            ],
            check=True,
        )
        graph = json.loads(json_path.read_text())["graph"]

    nodes = graph["nodes"]
    edges = graph["edges"]

    # Group nodes by source file for subgraphs.
    by_file: dict[str, list[tuple[str, str]]] = {}
    id_to_label: dict[str, str] = {}
    for node_id, info in nodes.items():
        label = _shorten(info["name"])
        file_ = _file_of(info["name"])
        by_file.setdefault(file_, []).append((node_id, label))
        id_to_label[node_id] = label

    # AST fallback: add subgraphs for modules code2flow produced no nodes for.
    ast_symbols = _ast_top_level_functions(SRC_DIR)
    for stem, names in ast_symbols.items():
        if stem not in by_file:
            by_file[stem] = []
            for name in names:
                node_id = "ast_" + hashlib.md5(f"{stem}::{name}".encode()).hexdigest()[:8]
                by_file[stem].append((node_id, name))
                id_to_label[node_id] = name

    lines = ["```mermaid", "flowchart LR"]
    for file_, items in sorted(by_file.items()):
        safe_file = file_.replace(".", "_")
        lines.append(f'    subgraph {safe_file}["{file_}.py"]')
        for node_id, label in items:
            safe_id = node_id.replace("(", "_").replace(")", "_")
            lines.append(f'        {safe_id}["{label}"]')
        lines.append("    end")
    seen_edges: set[tuple[str, str]] = set()
    for edge in edges:
        src = edge["source"].replace("(", "_").replace(")", "_")
        dst = edge["target"].replace("(", "_").replace(")", "_")
        if (src, dst) in seen_edges:
            continue
        seen_edges.add((src, dst))
        lines.append(f"    {src} --> {dst}")
    lines.append("```")
    sys.stdout.write("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
