#!/usr/bin/env python
"""Assemble morphonic-rebuild-handoff-2026-05-19 package."""
from __future__ import annotations

import hashlib
import json
import shutil
import sqlite3
import subprocess
import sys
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PKG = REPO / "export" / "morphonic-rebuild-handoff-2026-05-19"
DB = REPO / "data" / "token_index_identity_review.sqlite"
CRYSTAL = REPO / "crystals" / "identity_review.crystal"

MERMAID = {
    "02_ARCHITECTURE/diagrams/architecture_layers.mmd": """flowchart TB
  subgraph platforms [ExternalPlatforms]
    HF[HuggingFace_stub]
    PT[PyTorch_module]
  end
  subgraph slot48 [Slot48_transform]
    GT[GeometricTransformer]
    NL[N_ladder_8_layers]
  end
  subgraph law [MorphonShell]
    AD[admit_complete]
  end
  subgraph memory [Substrate]
    TB[token_bonds]
    AM[address_meaning]
    TL[translation_links]
  end
  subgraph ship [Crystal_2_1_0]
    CR[crystal_bundle]
  end
  HF --> GT
  PT --> GT
  GT --> NL
  GT --> AD
  AD --> TB
  TB --> CR
  AM --> CR
  TL --> CR
""",
    "02_ARCHITECTURE/diagrams/forward_dataflow.mmd": """sequenceDiagram
  participant User
  participant GT as GeometricTransformer
  participant Tok as MorphonicTokenizer
  participant L as Layer_MORSR_TarPit_NSL
  participant Head as EversionHead
  participant Shell as MorphonShell
  participant SL as SpeedLight
  User->>GT: forward ribbon
  GT->>SL: cache lookup
  GT->>Tok: tokenize
  loop num_layers
    GT->>L: attention FFN NSL
  end
  GT->>Head: ribbon_out
  GT->>Shell: shell_bind admit
  GT->>SL: cache store
""",
    "02_ARCHITECTURE/diagrams/ingest_multistream.mmd": """flowchart LR
  corpus[Corpus_md_txt] --> hub[TranslateHub_noop]
  hub --> en[stream_en]
  corpus --> native[stream_native]
  en --> bonds[token_bonds]
  native --> bonds
  en --> links[translation_links]
  native --> links
  bonds --> geom[token_geometry]
  links --> tp[TokenToolPass]
  tp --> morph[morph_signatures]
""",
    "02_ARCHITECTURE/diagrams/compose_supervisor.mmd": """flowchart TD
  SP[SUPERPERM_N4] --> sup[IndexSupervisor_walk]
  sup --> T[template_query]
  sup --> C[convolve]
  sup --> I[involute]
  sup --> A[abstract]
  T --> shell[MorphonShell_complete]
  C --> shell
  shell --> fwd[optional_forward]
""",
    "02_ARCHITECTURE/diagrams/port_bridge.mmd": """flowchart LR
  transform[cmplx.transform] --> bridge[bridge.py]
  bridge --> morsr[diagnostic_MORSR]
  bridge --> tarpit[symbolic_TarPit]
  bridge --> nsl[conservation_NSL]
  bridge --> sl[cache_SpeedLight]
  bridge --> snap[snap]
  bridge --> receipt[receipt]
""",
    "02_ARCHITECTURE/mindmaps/morphonic_concepts.mmd": """mindmap
  root((Morphonic))
    Substrate
      token_bonds
      address_meaning
      translation_links
    Law
      MorphonShell
      quad_bond
      NSL
    Transform
      MORSR
      TarPit
      N_ladder
    Ship
      Crystal_2_1_0
      SUPERPERM_schedule
""",
    "02_ARCHITECTURE/mindmaps/module_map.mmd": """mindmap
  root((cmplx.transform))
    Core
      transformer.py
      layer.py
      attention.py
      ffn.py
    Index
      token_index
      index_supervisor
      index_mutations
    Ingest
      ingest.py
      tool_pass.py
      crystal_pack.py
    IO
      __main__.py
      compose_pipeline.py
""",
}

METHODS = {
    "05_METHODS/METHOD_INGEST.md": "See REBUILD_FROM_SCRATCH §5. CLI: `python -m cmplx.transform ingest` or `morphonic_ingest_identity_review.py`. EN-first multistream policy.\n",
    "05_METHODS/METHOD_REFINE.md": "CLI: `python -m cmplx.transform refine --db ... --target-coverage 0.25 --limit 500 --allow-partial`. Runs convolve, involute, abstract rounds.\n",
    "05_METHODS/METHOD_CRYSTALLIZE.md": "CLI: `python -m cmplx.transform crystallize --name ... --db ... --lib data/rule_libs --out crystals/...`. Manifest schema 2.1.0.\n",
    "05_METHODS/METHOD_FORWARD_PRODUCTION.md": "CLI: `forward --ribbon ... --production --crystal ...`. Uses ProductionTransformerConfig: 8 layers, shell_bind, ports on init.\n",
    "05_METHODS/METHOD_TOOL_PASS.md": "TokenToolPass per translation_key: tarpit, nsl, snap, nlaecnf, cache. Script: `_phase1_tool_pass.py N` for bounded keys.\n",
    "05_METHODS/METHOD_COMPOSE.md": "compose_pipeline: IndexSupervisor.walk → shell.complete → optional GeometricTransformer.forward.\n",
}

PER_PORT = {
    "diagnostic": ("MORSR", "MorphonicAttention modes pulse/traverse/scan"),
    "symbolic": ("TarPit", "MorphonicFFN derive / run_program"),
    "conservation": ("NSL", "Per-layer gate on delta phi"),
    "cache": ("SpeedLight", "Forward idempotency + residuals"),
    "snap": ("SNAP", "Labels in tool pass"),
    "receipt": ("Receipt", "PROCESS receipts per tool step"),
}


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _export_ddl(conn: sqlite3.Connection, out: Path) -> None:
    out.mkdir(parents=True, exist_ok=True)
    cur = conn.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
    tables = [row[0] for row in cur.fetchall() if row[0]]
    combined = "\n\n".join(tables) + "\n"
    (out / "token_index_schema.sql").write_text(combined, encoding="utf-8")


def _export_jsonl_sample(conn: sqlite3.Connection, table: str, out: Path, limit: int, order: str = "rowid") -> int:
    out.parent.mkdir(parents=True, exist_ok=True)
    cur = conn.execute(f"SELECT * FROM {table} ORDER BY {order} LIMIT ?", (limit,))
    cols = [d[0] for d in cur.description]
    n = 0
    with out.open("w", encoding="utf-8") as fh:
        for row in cur.fetchall():
            fh.write(json.dumps(dict(zip(cols, row)), default=str) + "\n")
            n += 1
    return n


def _copy_head(src: Path, dst: Path, lines: int = 200) -> None:
    if not src.is_file():
        return
    dst.parent.mkdir(parents=True, exist_ok=True)
    with src.open(encoding="utf-8", errors="replace") as inf, dst.open("w", encoding="utf-8") as outf:
        for i, line in enumerate(inf):
            if i >= lines:
                break
            outf.write(line)


def _optional_artifacts() -> list[dict]:
    items = []
    for label, path in [
        ("identity_review_sqlite", DB),
        ("template_index_sqlite", REPO / "data" / "token_index.sqlite"),
        ("crystal_sqlite", CRYSTAL / "token_index.sqlite"),
    ]:
        if path.is_file():
            items.append(
                {
                    "label": label,
                    "host_path": str(path),
                    "size_bytes": path.stat().st_size,
                    "sha256": _sha256(path),
                    "note": "Not included in upload bundle; fetch separately for full fidelity",
                }
            )
    return items


def _write_knowledge_dag(pkg: Path) -> None:
    dag_path = pkg / "08_RAG_AND_GRAPH"
    dag_path.mkdir(parents=True, exist_ok=True)
    nodes = [
        {"id": "concept:substrate", "type": "concept", "label": "Substrate-first"},
        {"id": "module:transform", "type": "module", "label": "cmplx.transform"},
        {"id": "table:token_bonds", "type": "table", "label": "token_bonds"},
        {"id": "table:translation_links", "type": "table", "label": "translation_links"},
        {"id": "artifact:crystal", "type": "artifact", "label": "Crystal 2.1.0"},
    ]
    edges = [
        {"from": "module:transform", "to": "table:token_bonds", "relation": "reads"},
        {"from": "module:transform", "to": "artifact:crystal", "relation": "loads"},
        {"from": "concept:substrate", "to": "module:transform", "relation": "implements"},
    ]
    dag = {"nodes": nodes, "edges": edges}
    (dag_path / "knowledge_dag.json").write_text(json.dumps(dag, indent=2), encoding="utf-8")
    mmd = "flowchart TB\n  concept[Substrate_first] --> transform[cmplx.transform]\n  transform --> bonds[token_bonds]\n  transform --> crystal[Crystal_2_1_0]\n"
    (dag_path / "knowledge_dag.mmd").write_text(mmd, encoding="utf-8")


def _build_cli_surface(pkg: Path) -> None:
    (pkg / "03_MODULE_CATALOG").mkdir(parents=True, exist_ok=True)
    text = """# CLI surface (`python -m cmplx.transform`)

| Command | Purpose |
|---------|---------|
| build-index | Enumerate quad bonds L1-L3 |
| index-stats / template-stats | DB / template coverage reports |
| refine | Mutation rounds toward coverage target |
| ingest | Single-stream corpus ingest |
| meaning-query | Query address_meaning |
| admit / complete | Shell gate |
| morph-probe | Surface morphism verdict |
| forward | Forward pass (`--production` for N-ladder) |
| crystallize / crystal-info | Crystal bundle |
| lib-validate / lib-list | Rule YAML |

Examples in 00_REBUILD_PLAYBOOK/REBUILD_FROM_SCRATCH.md.
"""
    (pkg / "03_MODULE_CATALOG" / "CLI_SURFACE.md").write_text(text, encoding="utf-8")
    api = """# API quick reference

| Symbol | Role |
|--------|------|
| GeometricTransformer | Slot 48 stack |
| ProductionTransformerConfig() | 8-layer N-ladder + shell_bind |
| MorphonShell | admit, complete, slice_ribbon |
| CorpusIngester / ingest_multistream | Corpus → index |
| TokenToolPass | Linked tool chain |
| IndexSupervisor | SP walk + mutations |
| CrystalPackager | pack / load |
| HuggingFaceAdapterStub | export_admit_mask |
"""
    (pkg / "03_MODULE_CATALOG" / "API_QUICKREF.md").write_text(api, encoding="utf-8")


def _verification_docs(pkg: Path) -> None:
    vdir = pkg / "07_VERIFICATION"
    vdir.mkdir(parents=True, exist_ok=True)
    (vdir / "E2E_SMOKE.md").write_text(
        "Run: `PYTHONPATH=src python scripts/morphonic_e2e_smoke.py --quick`\n"
        "CI: `.github/workflows/morphonic-pytest.yml`\n",
        encoding="utf-8",
    )
    (vdir / "OPERATIONAL_V1_EVIDENCE.md").write_text(
        "Crystal bc00ac8ee26c, schema 2.1.0, 37k bonds, 123k links, 1639 morph_signatures. "
        "See 04_DATA_AND_SCHEMA/stats/ and crystal/manifest.json.\n",
        encoding="utf-8",
    )
    tests = sorted((REPO / "tests" / "transform").rglob("test_*.py"))
    lines = ["# Test matrix\n", f"Total transform test files: {len(tests)}\n", "| File | |\n|------|--|\n"]
    for t in tests:
        lines.append(f"| `{t.relative_to(REPO).as_posix()}` | |\n")
    prims = sorted((REPO / "tests" / "primitives").rglob("test_*.py"))
    lines.append(f"\nPrimitives test files: {len(prims)}\n")
    lines.append("Full run: `pytest tests/transform/ tests/primitives/ -q` (122+ passed May 2026).\n")
    (vdir / "TEST_MATRIX.md").write_text("".join(lines), encoding="utf-8")


def _readme(pkg: Path, index: list[dict]) -> None:
    total = sum(i["size_bytes"] for i in index)
    readme = f"""# Morphonic Rebuild Handoff — START HERE

**Package:** morphonic-rebuild-handoff-2026-05-19  
**Purpose:** Enable rebuild of CMPLX Morphonic Slot 48 (substrate + transformer + ports) without the full PartsFactory workspace.  
**Upload tier:** docs + samples + stats (&lt;50 MB). Full DBs: see `10_BINARIES_MANIFEST/OPTIONAL_FULL_ARTIFACTS.json`.

## What this is

A **substrate-first geometric transformer** — not a weight-trained LLM. Validity comes from the **token index**, **Morphon shell**, and **CMPLX port orchestration** (MORSR, TarPit, NSL, SpeedLight, SNAP).

## Read order

1. [01_DOCTRINE_AND_STATUS/DESIGN_VS_REALITY.md](01_DOCTRINE_AND_STATUS/DESIGN_VS_REALITY.md)
2. [00_REBUILD_PLAYBOOK/REBUILD_FROM_SCRATCH.md](00_REBUILD_PLAYBOOK/REBUILD_FROM_SCRATCH.md)
3. [02_ARCHITECTURE/diagrams/architecture_layers.mmd](02_ARCHITECTURE/diagrams/architecture_layers.mmd)
4. [09_FUTURE_WORK/GAP_AND_TODO.md](09_FUTURE_WORK/GAP_AND_TODO.md)
5. [08_RAG_AND_GRAPH/rag_manifest.jsonl](08_RAG_AND_GRAPH/rag_manifest.jsonl) for chunk retrieval

## Environment

- Python 3.10+, `pip install -e ".[dev]"`, `PYTHONPATH=src`
- Acceptance: 122+ pytest, `scripts/morphonic_e2e_smoke.py --quick`

## Package stats

- Files: {len(index)}
- Total size: {total / (1024 * 1024):.2f} MB

## Non-goals

See [09_FUTURE_WORK/GAP_AND_TODO.md](09_FUTURE_WORK/GAP_AND_TODO.md).

## Web AI instructions

[00_REBUILD_PLAYBOOK/EXTERNAL_AI_INSTRUCTIONS.md](00_REBUILD_PLAYBOOK/EXTERNAL_AI_INSTRUCTIONS.md)
"""
    (pkg / "README_START_HERE.md").write_text(readme, encoding="utf-8")
    cover = """# Handoff cover — what to upload first

1. README_START_HERE.md  
2. 01_DOCTRINE_AND_STATUS/DESIGN_VS_REALITY.md + NORTH_STAR.md  
3. 02_ARCHITECTURE/diagrams/architecture_layers.mmd  
4. 09_FUTURE_WORK/GAP_AND_TODO.md  
5. 00_REBUILD_PLAYBOOK/REBUILD_FROM_SCRATCH.md  

Optional: entire `export/morphonic-rebuild-handoff-2026-05-19.zip` if under size limit.
"""
    (pkg / "HANDOFF_COVER.md").write_text(cover, encoding="utf-8")


def build() -> dict:
    if PKG.exists():
        shutil.rmtree(PKG)
    PKG.mkdir(parents=True)

    from handoff_markdown_content import ALL_MARKDOWN

    for rel, body in {**ALL_MARKDOWN, **METHODS}.items():
        p = PKG / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(body, encoding="utf-8")

    for rel, body in MERMAID.items():
        p = PKG / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(body, encoding="utf-8")

    _build_cli_surface(PKG)
    _verification_docs(PKG)
    _write_knowledge_dag(PKG)

    for name, (title, desc) in PER_PORT.items():
        d = PKG / "06_PORTS_ECOSYSTEM" / "per_port" / f"{name}.md"
        d.parent.mkdir(parents=True, exist_ok=True)
        d.write_text(f"# Port: {name}\n\n**Package:** {title}\n\n{desc}\n", encoding="utf-8")

    for src_name, dst_rel in [("BRIDGE.md", "06_PORTS_ECOSYSTEM/BRIDGE.md"), ("INTERFACE.md", "06_PORTS_ECOSYSTEM/INTERFACE.md")]:
        src = REPO / "src" / "cmplx" / "transform" / src_name
        if src.is_file():
            dst = PKG / dst_rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            hdr = f"<!-- source: {src.relative_to(REPO).as_posix()} -->\n\n"
            dst.write_text(hdr + src.read_text(encoding="utf-8"), encoding="utf-8")

    stats_dst = PKG / "04_DATA_AND_SCHEMA" / "stats"
    stats_dst.mkdir(parents=True, exist_ok=True)
    for name in [
        "ingest_identity_review_stats.json",
        "template_stats_before.json",
        "template_stats_after.json",
        "refine_report.json",
        "forward_result.json",
    ]:
        src = REPO / "data" / name
        if src.is_file():
            shutil.copy2(src, stats_dst / name)

    if (REPO / "data" / "rule_libs").is_dir():
        shutil.copytree(REPO / "data" / "rule_libs", PKG / "04_DATA_AND_SCHEMA" / "rule_libs")
    if (REPO / "data" / "superpermutations").is_dir():
        shutil.copytree(REPO / "data" / "superpermutations", PKG / "04_DATA_AND_SCHEMA" / "superpermutations")

    crystal_dst = PKG / "04_DATA_AND_SCHEMA" / "crystal"
    crystal_dst.mkdir(parents=True, exist_ok=True)
    if (CRYSTAL / "manifest.json").is_file():
        shutil.copy2(CRYSTAL / "manifest.json", crystal_dst / "manifest.json")
    _copy_head(CRYSTAL / "translation_links.jsonl", crystal_dst / "translation_links_head.jsonl")
    _copy_head(CRYSTAL / "morph_signatures.jsonl", crystal_dst / "morph_signatures_head.jsonl")
    sidecar = ["translation_links.jsonl", "morph_signatures.jsonl"]
    lines = ["# Crystal sidecar manifest\n"]
    for s in sidecar:
        p = CRYSTAL / s
        if p.is_file():
            lines.append(f"- `{s}`: {p.stat().st_size} bytes on host\n")
    (crystal_dst / "sidecar_manifest.md").write_text("".join(lines), encoding="utf-8")

    if DB.is_file():
        conn = sqlite3.connect(DB)
        try:
            _export_ddl(conn, PKG / "04_DATA_AND_SCHEMA" / "ddl")
        finally:
            conn.close()

    (PKG / "10_BINARIES_MANIFEST").mkdir(parents=True, exist_ok=True)
    artifacts = _optional_artifacts()
    (PKG / "10_BINARIES_MANIFEST" / "OPTIONAL_FULL_ARTIFACTS.json").write_text(
        json.dumps(artifacts, indent=2), encoding="utf-8"
    )

    scripts_dir = REPO / "scripts"
    subprocess.run([sys.executable, str(scripts_dir / "export_morphonic_module_dag.py"), str(PKG / "03_MODULE_CATALOG")], check=True)

    sys.path.insert(0, str(scripts_dir))
    from deepen_morphonic_handoff import deepen, update_checkpoint_doc, update_handoff_cover, update_readme

    deepen_stats = deepen(PKG)

    subprocess.run([sys.executable, str(scripts_dir / "export_morphonic_rag_chunks.py"), str(PKG)], check=True)
    subprocess.run([sys.executable, str(scripts_dir / "build_morphonic_tag_index.py"), str(PKG)], check=True)

    index: list[dict] = []
    for f in sorted(PKG.rglob("*")):
        if f.is_file():
            index.append({"path": f.relative_to(PKG).as_posix(), "size_bytes": f.stat().st_size})
    (PKG / "PACKAGE_INDEX.json").write_text(json.dumps({"files": index, "file_count": len(index)}, indent=2), encoding="utf-8")

    rag_manifest = PKG / "08_RAG_AND_GRAPH" / "rag_manifest.jsonl"
    rag_chunks = sum(1 for _ in rag_manifest.open(encoding="utf-8")) if rag_manifest.is_file() else 0
    total_mb = round(sum(i["size_bytes"] for i in index) / (1024 * 1024), 2)

    pkg_stats = {"file_count": len(index), "mb": total_mb, "rag_chunks": rag_chunks}
    update_readme(PKG, index)
    update_handoff_cover(PKG, pkg_stats)

    zip_path = PKG.parent / "morphonic-rebuild-handoff-2026-05-19.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in PKG.rglob("*"):
            if f.is_file():
                zf.write(f, f.relative_to(PKG.parent).as_posix())
    zip_mb = round(zip_path.stat().st_size / (1024 * 1024), 2)
    update_checkpoint_doc({**pkg_stats, "zip_mb": zip_mb})

    return {
        "package": str(PKG),
        "zip": str(zip_path),
        "files": len(index),
        "mb": total_mb,
        "zip_mb": zip_mb,
        "rag_chunks": rag_chunks,
        "deepen": deepen_stats,
    }


def _table_exists(conn: sqlite3.Connection, name: str) -> bool:
    cur = conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (name,))
    return cur.fetchone() is not None


def main() -> int:
    sys.path.insert(0, str(REPO / "scripts"))
    result = build()
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
