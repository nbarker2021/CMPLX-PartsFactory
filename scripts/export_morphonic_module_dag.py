#!/usr/bin/env python
"""Export SOURCE_MANIFEST + PORT_DEPENDENCY_DAG for morphonic handoff package."""
from __future__ import annotations

import ast
import json
import os
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SRC = REPO / "src"
TRANSFORM = SRC / "cmplx" / "transform"
RUNTIME_ROOT = Path(
    os.environ.get("CMPLX_RUNTIME_DIR", REPO.parent / "runtime" / "CMPLX-PartsFactory")
)
DEFAULT_OUT = RUNTIME_ROOT / "export" / "morphonic-rebuild-handoff-2026-05-19" / "03_MODULE_CATALOG"

PORT_MAP = {
    "diagnostic": "cmplx.morsr",
    "symbolic": "cmplx.symbolic.tarpit",
    "conservation": "cmplx.nsl",
    "cache": "cmplx.speedlight",
    "receipt": "cmplx.receipt",
    "atlas": "cmplx.atlas",
    "constraints": "cmplx.constraints.aletheia",
    "engine": "cmplx.engine",
    "geometry": "cmplx.geometry",
    "memory": "cmplx.memory.mmdb",
    "addressing": "cmplx.addressing.mdhg",
    "snap": "cmplx.snap",
    "embed": "cmplx.embed",
    "transport": "cmplx.transport",
    "worlds": "cmplx.worlds.forge",
}

EXTRA_PACKAGES = [
    "cmplx.primitives.superperm",
    "cmplx.engine.eversion.network",
    "cmplx.morphon",
    "cmplx.worlds.forge",
    "runtime.cmplx_bootstrap",
]

# Worlds forge (slot-19) consumes bootstrap ports for witness + receipt wiring.
WORLDS_FORGE_EDGES: list[tuple[str, str]] = [
    ("worlds", "receipt"),
    ("worlds", "geometry"),
    ("worlds", "symbolic"),
]


def _imports_in_file(path: Path) -> set[str]:
    out: set[str] = set()
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except (SyntaxError, OSError):
        return out
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                out.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom) and node.module:
            out.add(node.module)
    return out


def _cmplx_modules_from_imports(imports: set[str], module: str) -> set[str]:
    found: set[str] = set()
    for imp in imports:
        if imp == "cmplx" or imp.startswith("cmplx."):
            found.add(imp if "." in imp else "cmplx")
        if imp == "runtime":
            found.add("runtime.cmplx_bootstrap")
    if module.startswith("cmplx."):
        found.add(module.rsplit(".", 1)[0] if "." in module else module)
    return found


def build_source_manifest() -> list[dict]:
    rows: list[dict] = []
    for path in sorted(TRANSFORM.rglob("*.py")):
        rel = path.relative_to(SRC).as_posix()
        module = rel.replace("/", ".").replace(".py", "")
        rows.append(
            {
                "path": rel,
                "module": module,
                "role": "transform_core",
            }
        )
    for pkg in ["cmplx/primitives/superperm.py", "cmplx/morphon/__init__.py"]:
        p = SRC / pkg
        if p.is_file():
            rows.append({"path": pkg, "module": pkg.replace("/", ".").replace(".py", ""), "role": "dependency"})
    return rows


def build_port_dag() -> dict:
    edges: list[dict] = []
    nodes = {"transform": {"id": "transform", "type": "package", "label": "cmplx.transform"}}
    for port, pkg in PORT_MAP.items():
        nid = f"port:{port}"
        nodes[nid] = {"id": nid, "type": "port", "label": port, "package": pkg}
        edges.append({"from": "transform", "to": nid, "relation": "consumes_port"})
        pkg_id = f"pkg:{pkg}"
        nodes[pkg_id] = {"id": pkg_id, "type": "package", "label": pkg}
        edges.append({"from": nid, "to": pkg_id, "relation": "resolves_to"})
    for pkg in EXTRA_PACKAGES:
        pid = f"pkg:{pkg}"
        nodes[pid] = {"id": pid, "type": "package", "label": pkg}
        edges.append({"from": "transform", "to": pid, "relation": "imports"})
    worlds_nid = "port:worlds"
    nodes[worlds_nid] = {
        "id": worlds_nid,
        "type": "port",
        "label": "worlds",
        "package": "cmplx.worlds.forge",
    }
    nodes["pkg:cmplx.worlds.forge"] = {
        "id": "pkg:cmplx.worlds.forge",
        "type": "package",
        "label": "cmplx.worlds.forge",
    }
    edges.append({"from": worlds_nid, "to": "pkg:cmplx.worlds.forge", "relation": "resolves_to"})
    for _from, consumes in WORLDS_FORGE_EDGES:
        target = f"port:{consumes}"
        if target not in nodes:
            nodes[target] = {
                "id": target,
                "type": "port",
                "label": consumes,
                "package": PORT_MAP.get(consumes, consumes),
            }
        edges.append({"from": worlds_nid, "to": target, "relation": "consumes_port"})
    return {"nodes": list(nodes.values()), "edges": edges}


def to_mermaid(dag: dict) -> str:
    lines = ["flowchart TB", "  transform[cmplx.transform]"]
    for node in dag["nodes"]:
        if node["id"] == "transform":
            continue
        if node["type"] == "port":
            lines.append(f'  {node["id"]}[{node["label"]}]')
    for edge in dag["edges"]:
        if edge["relation"] == "consumes_port":
            lines.append(f'  transform --> {edge["to"]}')
    return "\n".join(lines) + "\n"


def main() -> int:
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_OUT
    out.mkdir(parents=True, exist_ok=True)
    manifest = build_source_manifest()
    (out / "SOURCE_MANIFEST.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    dag = build_port_dag()
    (out / "PORT_DEPENDENCY_DAG.json").write_text(json.dumps(dag, indent=2), encoding="utf-8")
    (out / "PORT_DEPENDENCY_DAG.mmd").write_text(to_mermaid(dag), encoding="utf-8")
    print(json.dumps({"manifest_files": len(manifest), "dag_nodes": len(dag["nodes"]), "out": str(out)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
