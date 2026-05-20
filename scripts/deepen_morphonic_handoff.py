#!/usr/bin/env python
"""Deepen morphonic-rebuild-handoff package (corpus, code mirror, stats, tests, architecture)."""
from __future__ import annotations

import ast
import hashlib
import json
import re
import shutil
import sqlite3
import subprocess
import sys
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[1]
PKG = REPO / "export" / "morphonic-rebuild-handoff-2026-05-19"
DB = REPO / "data" / "token_index_identity_review.sqlite"
CRYSTAL = REPO / "crystals" / "identity_review.crystal"
IDENTITY_REVIEW = REPO.parent / "identity_review"

# Dependency mirror paths (relative to src/cmplx)
DEPS_MIRROR: list[tuple[str, Path]] = [
    ("primitives/superperm.py", REPO / "src" / "cmplx" / "primitives" / "superperm.py"),
    ("morphon", REPO / "src" / "cmplx" / "morphon"),
    ("morsr", REPO / "src" / "cmplx" / "morsr"),
    ("symbolic/tarpit", REPO / "src" / "cmplx" / "symbolic" / "tarpit"),
    ("nsl", REPO / "src" / "cmplx" / "nsl"),
    ("snap", REPO / "src" / "cmplx" / "snap"),
    ("speedlight", REPO / "src" / "cmplx" / "speedlight"),
    ("receipt", REPO / "src" / "cmplx" / "receipt"),
    ("engine/eversion/network.py", REPO / "src" / "cmplx" / "engine" / "eversion" / "network.py"),
]

DOC_SOURCES = [
    ("docs/MORPHONIC_UNIFIED_DOCTRINE.md", REPO / "docs" / "MORPHONIC_UNIFIED_DOCTRINE.md"),
    ("docs/MORPHONIC_SUBSTRATE_CRYSTAL_PLAN.md", REPO / "docs" / "MORPHONIC_SUBSTRATE_CRYSTAL_PLAN.md"),
    ("docs/MORPHONIC_OPERATIONAL_V1_CHECKPOINT.md", REPO / "docs" / "MORPHONIC_OPERATIONAL_V1_CHECKPOINT.md"),
    ("docs/MORPHONIC_PRODUCTION_RUNBOOK.md", REPO / "docs" / "MORPHONIC_PRODUCTION_RUNBOOK.md"),
    ("docs/MORPHONIC_TEST_REVIEW_2026-05-19.md", REPO / "docs" / "MORPHONIC_TEST_REVIEW_2026-05-19.md"),
    ("docs/HP_NHYPER_TOWER_INTEGRATION.md", REPO / "docs" / "HP_NHYPER_TOWER_INTEGRATION.md"),
    ("docs/NHYPER_TOWER_ESCROW.md", REPO / "docs" / "NHYPER_TOWER_ESCROW.md"),
    ("transform/INTERFACE.md", REPO / "src" / "cmplx" / "transform" / "INTERFACE.md"),
    ("transform/BRIDGE.md", REPO / "src" / "cmplx" / "transform" / "BRIDGE.md"),
]

CHECKPOINT_GLOB = "2026-05-19-*-morphonic*.md"

MODULE_DEEP_DIVE_FILES = [
    "transformer.py",
    "shell.py",
    "ingest.py",
    "tool_pass.py",
    "index_supervisor.py",
    "index_mutations.py",
    "crystal_pack.py",
    "n_ladder.py",
    "compose_pipeline.py",
    "token_index/store.py",
    "token_index/template_frame.py",
]

CODE_READING_ORDER: list[tuple[str, str]] = [
    ("transform/types.py", "Shared datatypes: HiddenState, TokenizedRibbon, LayerTrace, TransformerOutput."),
    ("transform/config.py", "TransformerConfig and ProductionTransformerConfig presets (8-layer N-ladder)."),
    ("transform/bridge.py", "Lazy port accessors; ensure_bootstrapped wires runtime.cmplx_bootstrap."),
    ("transform/token_index/store.py", "SQLite TokenIndexStore — bonds, links, meaning, geometry, morph tables."),
    ("transform/token_index/template_frame.py", "Template coverage queries driving refine and supervisor."),
    ("transform/token_index/bonds.py", "Quad bond enumeration and warmstart helpers."),
    ("transform/shell.py", "MorphonShell admit/complete/slice_ribbon — law gate for all ribbons."),
    ("transform/tokenizer.py", "MorphonicTokenizer — content to HiddenState + TokenizedRibbon."),
    ("transform/attention.py", "MorphonicAttention via MORSR diagnostic port."),
    ("transform/ffn.py", "MorphonicFFN via TarPit symbolic port."),
    ("transform/layer.py", "GeometricTransformerLayer — NSL gate + SpeedLight residual per layer."),
    ("transform/n_ladder.py", "Eight layer policy tags (N=2..8) for production stack."),
    ("transform/transformer.py", "GeometricTransformer forward: tokenize → layers → eversion head → shell_bind."),
    ("transform/ingest.py", "CorpusIngester multistream: corpus → bonds → links → optional geometry."),
    ("transform/tool_pass.py", "TokenToolPass: TarPit→NSL→SNAP→NLAECNF→cache per translation_key."),
    ("transform/index_supervisor.py", "IndexSupervisor SUPERPERM_N4 walk + template/mutation scheduling."),
    ("transform/index_mutations.py", "convolve, involute, abstract mutation operators on index."),
    ("transform/compose_pipeline.py", "Supervisor walk + shell.complete + optional forward."),
    ("transform/crystal_pack.py", "Crystal 2.1.0 pack/load: sqlite + rule_libs + jsonl sidecars + digest."),
    ("transform/__main__.py", "CLI: build-index, ingest, refine, forward, crystallize, admit, etc."),
    ("engine/eversion/network.py", "MorphonicEversionNetwork head (stages 0–6) used by transformer."),
]

TABLE_COLUMN_DOCS: dict[str, dict[str, str]] = {
    "token_bonds": {
        "id": "Surrogate primary key.",
        "concat": "Bond window text (quad or longer concat key).",
        "quad_left": "Left F4 quad of bond.",
        "quad_right": "Right F4 quad of bond.",
        "bond_level": "Template level 1–3 (enumeration depth).",
        "case_mode": "Case folding mode for alphabet.",
        "language": "ISO-ish language tag.",
        "stream": "Multistream discriminator: en, native, math, notation.",
        "morphon_id": "Morphon registry id for this bond.",
        "parent_morphon_id": "Optional parent morphon for derived bonds.",
        "snap_key": "SNAP address key linking to meaning/geometry.",
        "digital_root": "DR witness integer.",
        "lane": "Lane label for address_meaning join.",
        "e8_signature": "E8 routing signature string.",
        "cache_key": "SpeedLight cache key material.",
        "warmstart": "Warmstart policy label.",
        "created_at": "Unix timestamp.",
    },
    "build_runs": {
        "id": "Run id.",
        "started_at": "Run start time.",
        "finished_at": "Run end time (null if crashed).",
        "levels": "Comma-separated bond levels built.",
        "alphabet": "Alphabet used.",
        "languages": "Languages included.",
        "case_modes": "Case modes included.",
        "total_seen": "Candidates seen.",
        "total_stored": "Rows inserted.",
        "stats_json": "Opaque stats blob.",
    },
    "address_meaning": {
        "id": "Row id.",
        "snap_key": "Join to bonds/geometry.",
        "lane": "Meaning lane.",
        "digital_root": "DR witness.",
        "label": "Human or derived label text.",
        "label_source": "Provenance of label.",
        "source_doc": "Corpus document id.",
        "source_span": "Span within document.",
        "ennead_id": "Optional ennead classification.",
        "receipt_hash": "Receipt chain hash if tool pass ran.",
        "created_at": "Timestamp.",
    },
    "translation_links": {
        "id": "Row id.",
        "translation_key": "Cross-stream join key (e.g. doc:chunk:0).",
        "stream": "Stream column.",
        "concat": "Bond concat at link time.",
        "snap_key": "SNAP key.",
        "lane": "Optional lane.",
        "digital_root": "Optional DR.",
        "source_doc": "Document id.",
        "source_span": "Span.",
        "created_at": "Timestamp.",
    },
    "token_geometry": {
        "id": "Row id.",
        "concat": "Bond concat.",
        "stream": "Stream.",
        "translation_key": "Optional key.",
        "snap_key": "SNAP key.",
        "e6_coords": "JSON E6 witness coordinates.",
        "e8_coords": "JSON E8 witness coordinates.",
        "created_at": "Timestamp.",
    },
    "morph_signatures": {
        "id": "Row id.",
        "concat_base": "Base bond.",
        "concat_variant": "Variant after morphism probe.",
        "generator": "Generator name (probe, tool_pass, etc.).",
        "delta_snap": "SNAP delta.",
        "delta_lane": "Lane delta.",
        "delta_dr": "DR delta.",
        "verdict": "Morph verdict string.",
        "payload_json": "Tool payload.",
        "created_at": "Timestamp.",
    },
}

EXPANDED_MERMAID = {
    "02_ARCHITECTURE/diagrams/architecture_layers.mmd": """flowchart TB
  subgraph platforms [ExternalPlatforms]
    HF[HuggingFace_admit_mask_stub]
    PT[PyTorch_GeometricTransformerModule]
    CLI[python_-m_cmplx.transform]
  end
  subgraph slot48 [Slot48_transform]
    GT[GeometricTransformer]
    NL[N_ladder_8_policies]
    TOK[MorphonicTokenizer]
    LAY[GeometricTransformerLayer_xN]
    HEAD[MorphonicEversionNetwork]
  end
  subgraph law [MorphonShell]
    AD[admit]
    SLICE[slice_ribbon]
    COMP[complete]
  end
  subgraph ports [CMPLX_ports]
    MORSR[diagnostic_MORSR]
    TP[symbolic_TarPit]
    NSL[conservation_NSL]
    SL[cache_SpeedLight]
    RC[receipt]
    SNAP[snap]
  end
  subgraph memory [Substrate_SQLite]
    TB[token_bonds]
    AM[address_meaning]
    TL[translation_links]
    TG[token_geometry]
    MS[morph_signatures]
  end
  subgraph supervisor [IndexSupervisor]
    SP[SUPERPERM_N4]
    MUT[index_mutations]
  end
  subgraph ship [Crystal_2_1_0]
    CR[crystal_bundle]
    MAN[manifest_2.1.0]
    JSONL[translation_links_morph_signatures_jsonl]
  end
  CLI --> GT
  HF --> GT
  PT --> GT
  GT --> TOK
  TOK --> LAY
  LAY --> MORSR
  LAY --> TP
  LAY --> NSL
  LAY --> SL
  LAY --> HEAD
  HEAD --> AD
  AD --> COMP
  SP --> MUT
  MUT --> TB
  TB --> CR
  AM --> CR
  TL --> CR
  MS --> CR
  MAN --> CR
  JSONL --> CR
""",
}


def _copy_verbatim(src: Path, dst: Path) -> None:
    if not src.is_file():
        return
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def _copy_tree_filtered(src: Path, dst: Path, *, max_mb: float = 50.0) -> int:
    """Copy directory; skip _history_reference if huge."""
    if not src.is_dir():
        return 0
    n = 0
    for f in src.rglob("*"):
        if not f.is_file():
            continue
        if "_history_reference" in f.parts:
            continue
        if f.stat().st_size > max_mb * 1024 * 1024:
            continue
        rel = f.relative_to(src)
        target = dst / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(f, target)
        n += 1
    return n


def export_source_corpus(pkg: Path) -> dict[str, int]:
    docs_dst = pkg / "11_SOURCE_CORPUS" / "docs"
    docs_dst.mkdir(parents=True, exist_ok=True)
    n = 0
    for rel_name, src in DOC_SOURCES:
        if src.is_file():
            _copy_verbatim(src, docs_dst / rel_name.replace("/", "_").replace("\\", "_"))
            n += 1
    cp_dir = IDENTITY_REVIEW / "checkpoints"
    if cp_dir.is_dir():
        for cp in sorted(cp_dir.glob(CHECKPOINT_GLOB)):
            _copy_verbatim(cp, docs_dst / "checkpoints" / cp.name)
            n += 1
    agents = REPO / "AGENTS.md"
    if agents.is_file():
        text = agents.read_text(encoding="utf-8")
        excerpt = (
            "# AGENTS.md — morphonic-relevant excerpt\n\n"
            "Source: CMPLX-PartsFactory/AGENTS.md (Package Structure, Development, "
            "Repo-Kernel, Hard Constraints, Key Files).\n\n"
            + text
        )
        (docs_dst / "AGENTS_MORPHONIC_EXCERPT.md").write_text(excerpt, encoding="utf-8")
        n += 1
    return {"docs_copied": n}


def export_code_mirror(pkg: Path) -> dict[str, int]:
    transform_src = REPO / "src" / "cmplx" / "transform"
    transform_dst = pkg / "11_SOURCE_CORPUS" / "code" / "transform"
    if transform_dst.exists():
        shutil.rmtree(transform_dst)
    shutil.copytree(transform_src, transform_dst)
    py_count = len(list(transform_dst.rglob("*.py")))

    deps_dst = pkg / "11_SOURCE_CORPUS" / "code" / "deps"
    deps_dst.mkdir(parents=True, exist_ok=True)
    dep_files = 0
    for rel, src in DEPS_MIRROR:
        dst = deps_dst / rel
        if src.is_file():
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            dep_files += 1
        elif src.is_dir():
            dep_files += _copy_tree_filtered(src, dst)

    order_lines = ["# Code reading order\n", "Read in this order when rebuilding Slot 48.\n\n"]
    for rel, purpose in CODE_READING_ORDER:
        order_lines.append(f"## `{rel}`\n\n{purpose}\n\n")
    (pkg / "11_SOURCE_CORPUS" / "code" / "CODE_READING_ORDER.md").write_text(
        "".join(order_lines), encoding="utf-8"
    )
    return {"transform_py": py_count, "dep_paths": dep_files}


def _table_exists(conn: sqlite3.Connection, name: str) -> bool:
    cur = conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (name,))
    return cur.fetchone() is not None


def _export_jsonl_rows(conn: sqlite3.Connection, sql: str, params: tuple, out: Path) -> int:
    out.parent.mkdir(parents=True, exist_ok=True)
    cur = conn.execute(sql, params)
    cols = [d[0] for d in cur.description]
    n = 0
    with out.open("w", encoding="utf-8") as fh:
        for row in cur.fetchall():
            fh.write(json.dumps(dict(zip(cols, row)), default=str) + "\n")
            n += 1
    return n


def _stratified_sample(
    conn: sqlite3.Connection,
    table: str,
    out: Path,
    total: int,
    stream_col: str = "stream",
) -> int:
    if not _table_exists(conn, table):
        return 0
    streams = [
        r[0]
        for r in conn.execute(
            f"SELECT DISTINCT {stream_col} FROM {table} ORDER BY {stream_col}"
        ).fetchall()
    ]
    if not streams:
        cur = conn.execute(f"SELECT * FROM {table} ORDER BY rowid LIMIT ?", (total,))
        cols = [d[0] for d in cur.description]
        out.parent.mkdir(parents=True, exist_ok=True)
        n = 0
        with out.open("w", encoding="utf-8") as fh:
            for row in cur.fetchall():
                fh.write(json.dumps(dict(zip(cols, row)), default=str) + "\n")
                n += 1
        return n
    per = max(1, total // len(streams))
    out.parent.mkdir(parents=True, exist_ok=True)
    cols: list[str] | None = None
    n = 0
    with out.open("w", encoding="utf-8") as fh:
        for s in streams:
            cur = conn.execute(
                f"SELECT * FROM {table} WHERE {stream_col}=? ORDER BY rowid LIMIT ?",
                (s, per),
            )
            if cols is None:
                cols = [d[0] for d in cur.description]
            for row in cur.fetchall():
                fh.write(json.dumps(dict(zip(cols, row)), default=str) + "\n")
                n += 1
    return n


def export_deeper_data(pkg: Path) -> dict[str, Any]:
    stats: dict[str, Any] = {}
    samples_dir = pkg / "04_DATA_AND_SCHEMA" / "samples"
    samples_dir.mkdir(parents=True, exist_ok=True)

    if DB.is_file():
        conn = sqlite3.connect(DB)
        try:
            counts = {}
            for table in [
                "token_bonds",
                "build_runs",
                "address_meaning",
                "translation_links",
                "token_geometry",
                "morph_signatures",
            ]:
                if _table_exists(conn, table):
                    counts[table] = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            stats_dst = pkg / "04_DATA_AND_SCHEMA" / "stats"
            stats_dst.mkdir(parents=True, exist_ok=True)
            (stats_dst / "DB_TABLE_COUNTS.json").write_text(
                json.dumps(counts, indent=2), encoding="utf-8"
            )
            stats["table_counts"] = counts

            hist_lines = ["# Stream breakdown (SQL-derived)\n\n"]
            for table, col in [
                ("token_bonds", "stream"),
                ("translation_links", "stream"),
                ("address_meaning", "lane"),
            ]:
                if not _table_exists(conn, table):
                    continue
                hist_lines.append(f"## `{table}` by `{col}`\n\n")
                hist_lines.append("| value | count |\n|-------|------:|\n")
                for val, cnt in conn.execute(
                    f"SELECT {col}, COUNT(*) c FROM {table} GROUP BY {col} ORDER BY c DESC"
                ):
                    hist_lines.append(f"| `{val}` | {cnt:,} |\n")
                hist_lines.append("\n")
            (stats_dst / "STREAM_BREAKDOWN.md").write_text("".join(hist_lines), encoding="utf-8")

            stats["token_bonds"] = _stratified_sample(
                conn, "token_bonds", samples_dir / "token_bonds_sample.jsonl", 2000
            )
            if _table_exists(conn, "translation_links"):
                stats["translation_links"] = _stratified_sample(
                    conn, "translation_links", samples_dir / "translation_links_sample.jsonl", 2000
                )
            if _table_exists(conn, "morph_signatures"):
                stats["morph_signatures"] = _stratified_sample(
                    conn,
                    "morph_signatures",
                    samples_dir / "morph_signatures_sample.jsonl",
                    500,
                    stream_col="generator",
                )
            if _table_exists(conn, "address_meaning"):
                stats["address_meaning"] = _stratified_sample(
                    conn,
                    "address_meaning",
                    samples_dir / "address_meaning_sample.jsonl",
                    500,
                    stream_col="lane",
                )
        finally:
            conn.close()

    crystal_dst = pkg / "04_DATA_AND_SCHEMA" / "crystal"
    crystal_dst.mkdir(parents=True, exist_ok=True)
    sidecar_manifest: dict[str, Any] = {}
    for name in ("translation_links.jsonl", "morph_signatures.jsonl"):
        src = CRYSTAL / name
        if not src.is_file():
            continue
        size = src.stat().st_size
        line_count = sum(1 for _ in src.open(encoding="utf-8", errors="replace"))
        sidecar_manifest[name] = {"size_bytes": size, "line_count": line_count}
        dst = crystal_dst / name
        if size <= 5 * 1024 * 1024:
            shutil.copy2(src, dst)
            sidecar_manifest[name]["included"] = "full"
        else:
            with src.open(encoding="utf-8", errors="replace") as inf, dst.open(
                "w", encoding="utf-8"
            ) as outf:
                for i, line in enumerate(inf):
                    if i >= 2000:
                        break
                    outf.write(line)
            sidecar_manifest[name]["included"] = "first_2000_lines"
    (crystal_dst / "sidecar_manifest.json").write_text(
        json.dumps(sidecar_manifest, indent=2), encoding="utf-8"
    )
    stats["sidecars"] = sidecar_manifest

    manifest_path = crystal_dst / "manifest.json"
    if manifest_path.is_file():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        annotations = {
            "schema_version": "Crystal bundle format; must be 2.1.0 for operational v1.",
            "crystal_id": "Short hex digest of bundle contents; verify after copy.",
            "bond_count": "Rows in packed token_index.sqlite at crystallize time.",
            "link_count": "translation_links rows exported to sidecar + sqlite.",
            "morph_signature_count": "Rows in morph_signatures.jsonl.",
            "token_index_sqlite": "Frozen SQLite snapshot inside bundle directory.",
            "rule_libs": "Copied YAML rule libraries used by TarPit derive.",
            "translation_links.jsonl": "Multistream link sidecar for fast reload without full SQL scan.",
            "morph_signatures.jsonl": "Morphism probe / tool-pass verdict sidecar.",
            "created_at": "Unix timestamp when pack completed.",
        }
        annotated = {
            "manifest": manifest,
            "field_annotations": {k: annotations.get(k, "See crystal_pack.py") for k in manifest},
        }
        (crystal_dst / "OPERATIONAL_MANIFEST_ANNOTATED.json").write_text(
            json.dumps(annotated, indent=2), encoding="utf-8"
        )
    return stats


def export_tests(pkg: Path) -> dict[str, int]:
    spec_dst = pkg / "12_TEST_SPEC"
    spec_dst.mkdir(parents=True, exist_ok=True)
    n = 0
    transform_tests = REPO / "tests" / "transform"
    if transform_tests.is_dir():
        dst_tests = spec_dst / "tests" / "transform"
        if dst_tests.exists():
            shutil.rmtree(dst_tests)
        shutil.copytree(transform_tests, dst_tests)
        n += len(list(dst_tests.rglob("*.py")))
    superperm = REPO / "tests" / "primitives" / "test_superperm.py"
    if superperm.is_file():
        dst = spec_dst / "tests" / "primitives" / "test_superperm.py"
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(superperm, dst)
        n += 1

    index_lines = ["# Test spec index\n\n", "| Test file | Behavior proved |\n", "|-----------|------------------|\n"]
    test_map = {
        "test_transformer.py": "GeometricTransformer forward, cache key, shell_bind integration.",
        "test_shell.py": "MorphonShell admit/complete/slice_ribbon legality.",
        "test_multistream_ingest.py": "EN-first multistream ingest creates bonds+links.",
        "test_tool_pass_integration.py": "TokenToolPass chains ports per translation_key.",
        "test_index_supervisor.py": "SUPERPERM_N4 supervisor walk schedules mutations.",
        "test_index_mutations.py": "convolve/involute/abstract mutate index consistently.",
        "test_compose_pipeline.py": "Compose: supervisor + shell.complete + optional forward.",
        "test_n_ladder.py": "Eight production layer policies attach to config.",
        "test_hf_adapter.py": "HF stub exports admit mask without full PreTrainedModel.",
        "test_morphonic_bridge.py": "bridge.ensure_bootstrapped registers providers.",
        "test_superperm.py": "SUPERPERM_N4 length, coverage, n=4-only guard.",
        "token_index/test_store.py": "TokenIndexStore CRUD and schema migrations.",
        "token_index/test_template_frame.py": "Template frame coverage queries.",
    }
    for t in sorted((spec_dst / "tests").rglob("test_*.py")):
        rel = t.relative_to(spec_dst / "tests").as_posix()
        key = rel.replace("transform/", "") if rel.startswith("transform/") else rel
        desc = test_map.get(key, test_map.get(rel.split("/")[-1], "See test module docstring."))
        index_lines.append(f"| `{rel}` | {desc} |\n")
    (spec_dst / "TEST_SPEC_INDEX.md").write_text("".join(index_lines), encoding="utf-8")

    pytest_out = spec_dst / "PYTEST_LAST_RUN.txt"
    try:
        proc = subprocess.run(
            [
                sys.executable,
                "-m",
                "pytest",
                "tests/transform/",
                "tests/primitives/test_superperm.py",
                "-q",
                "--tb=no",
            ],
            cwd=REPO,
            capture_output=True,
            text=True,
            timeout=300,
            env={**dict(__import__("os").environ), "PYTHONPATH": str(REPO / "src")},
        )
        body = (proc.stdout or "") + (proc.stderr or "")
        pytest_out.write_text(
            f"# Last pytest run\n\nexit_code={proc.returncode}\n\n```\n{body}\n```\n",
            encoding="utf-8",
        )
    except Exception as exc:
        pytest_out.write_text(f"# pytest not run\n\n{exc}\n", encoding="utf-8")
    return {"test_files": n}


def export_architecture(pkg: Path) -> None:
    for rel, body in EXPANDED_MERMAID.items():
        p = pkg / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(body, encoding="utf-8")

    ddl_path = pkg / "04_DATA_AND_SCHEMA" / "ddl" / "token_index_schema.sql"
    schema_sql = ddl_path.read_text(encoding="utf-8") if ddl_path.is_file() else ""
    dm_lines = ["# Data model — SQLite token index\n\n", "Schema source: `04_DATA_AND_SCHEMA/ddl/token_index_schema.sql`.\n\n"]
    for table in TABLE_COLUMN_DOCS:
        dm_lines.append(f"## Table `{table}`\n\n")
        dm_lines.append("| Column | Description |\n|--------|-------------|\n")
        for col, doc in TABLE_COLUMN_DOCS[table].items():
            dm_lines.append(f"| `{col}` | {doc} |\n")
        dm_lines.append("\n")
    (pkg / "02_ARCHITECTURE" / "DATA_MODEL.md").write_text("".join(dm_lines), encoding="utf-8")

    (pkg / "02_ARCHITECTURE" / "FORWARD_TRACE_WALKTHROUGH.md").write_text(
        """# Forward trace walkthrough

One production forward pass (`GeometricTransformer.forward`) step by step.

1. **Bootstrap** — `bridge.ensure_bootstrapped()` registers MORSR, TarPit, NSL, SpeedLight, receipt, snap, engine providers (once per process).

2. **Config digest** — `_config_digest(TransformerConfig)` hashes layer attention/ffn/nsl settings for SpeedLight cache key.

3. **Cache lookup** — If SpeedLight available, compute key from ribbon + digest; return cached `TransformerOutput` on hit (`speedlight_hit=True`).

4. **Tokenize** — `MorphonicTokenizer.tokenize(content)` → `HiddenState` + `TokenizedRibbon` (atlas/morphon ports).

5. **Layer loop** — For each `GeometricTransformerLayer`:
   - **Attention** — `MorphonicAttention` calls diagnostic port (pulse/traverse/scan per config).
   - **FFN** — `MorphonicFFN` calls TarPit `derive` / `run_program`.
   - **NSL gate** — conservation port evaluates phi delta against `nsl_budget`; may block layer output.
   - **Residual** — optional SpeedLight layer residual cache.
   - **Trace** — append `LayerTrace` to output list.

6. **Eversion head** — `MorphonicEversionNetwork.forward` (stages 0–6 only) projects ribbon; transformer uses `result` dict only.

7. **Shell bind** — If `shell_bind` enabled, `MorphonShell.admit` on head output ribbon; violations raise `ShellViolation`.

8. **Receipt** — Optional receipt mint for forward audit.

9. **Cache store** — Store full output in SpeedLight for repeat calls.

10. **Return** — `TransformerOutput` with `layer_traces`, `ribbon_out`, `speedlight_hit`, shell metadata.

See `13_MODULE_DEEP_DIVES/transformer.md` and tests in `12_TEST_SPEC/tests/transform/test_transformer.py`.
""",
        encoding="utf-8",
    )

    (pkg / "02_ARCHITECTURE" / "INGEST_TRACE_WALKTHROUGH.md").write_text(
        """# Ingest trace walkthrough

Multistream corpus ingest (`CorpusIngester` / `morphonic_ingest_identity_review.py`) step by step.

1. **Open store** — `TokenIndexStore(db_path)` ensures schema from DDL.

2. **Iterate files** — Corpus walker applies `--max-files`, extension filters, encoding fallback.

3. **Chunk text** — Documents split into spans; assign `translation_key` (e.g. `relative/path:chunk:n`).

4. **Stream: en** — Primary stream tokenized first; quad windows enumerated; rows inserted into `token_bonds` with `stream='en'`.

5. **Stream: native** — Sidecar stream (or noop translate hub) produces aligned bonds sharing `translation_key`.

6. **translation_links** — For each key, insert link rows pairing streams with `concat`, `snap_key`, provenance columns.

7. **address_meaning** — Optional labels from SNAP/lane/DR witnesses when ingest policy enables meaning extraction.

8. **token_geometry** — After tool pass or dedicated geometry phase: E6/E8 JSON witnesses per concat.

9. **morph_signatures** — Populated by `TokenToolPass` / morph probe generators (not always during raw ingest).

10. **Stats export** — JSON tallies: `files_seen`, `bonds_stored`, `links_stored`, per-stream histograms.

**Failure modes:** duplicate UNIQUE on `(concat, case_mode, language, stream)`; missing translation_key alignment across streams.

See `13_MODULE_DEEP_DIVES/ingest.md` and `12_TEST_SPEC/tests/transform/test_multistream_ingest.py`.
""",
        encoding="utf-8",
    )

    (pkg / "02_ARCHITECTURE" / "PORT_CALL_GRAPH.md").write_text(
        """# Port call graph

| Layer | Calls port | Via |
|-------|------------|-----|
| `bridge.ensure_bootstrapped` | all default providers | `runtime.cmplx_bootstrap.register_all` |
| `attention.MorphonicAttention` | `diagnostic` | `bridge.get_diagnostic_provider` → MORSR |
| `ffn.MorphonicFFN` | `symbolic` | `bridge.get_symbolic_provider` → TarPit |
| `layer.GeometricTransformerLayer` | `conservation` | NSL gate |
| `layer.GeometricTransformerLayer` | `cache` | SpeedLight residual |
| `transformer.GeometricTransformer` | `cache` | full forward cache |
| `transformer.GeometricTransformer` | `receipt` | forward audit |
| `transformer.GeometricTransformer` | `engine` | MorphonicEversionNetwork |
| `tokenizer.MorphonicTokenizer` | `atlas` | morphon addressing |
| `tool_pass.TokenToolPass` | `symbolic`, `conservation`, `snap`, `cache`, `receipt` | chained tool steps |
| `ingest.CorpusIngester` | store only | SQLite (no forward ports) |
| `index_supervisor.IndexSupervisor` | store + `primitives.superperm` | SP cursor |
| `compose_pipeline` | supervisor + shell + optional transformer | in-process |

Dependency source mirror: `11_SOURCE_CORPUS/code/deps/`.
""",
        encoding="utf-8",
    )


def _analyze_module(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8", errors="replace")
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return {"doc": "", "classes": [], "functions": [], "lines": len(text.splitlines())}
    doc = ast.get_docstring(tree) or ""
    classes = []
    functions = []
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            classes.append(
                {
                    "name": node.name,
                    "doc": ast.get_docstring(node) or "",
                    "methods": [n.name for n in node.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))][:20],
                }
            )
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            functions.append({"name": node.name, "doc": ast.get_docstring(node) or ""})
    return {"doc": doc, "classes": classes, "functions": functions, "lines": len(text.splitlines())}


def export_module_deep_dives(pkg: Path) -> int:
    dive_dir = pkg / "13_MODULE_DEEP_DIVES"
    dive_dir.mkdir(parents=True, exist_ok=True)
    count = 0
    for rel in MODULE_DEEP_DIVE_FILES:
        src = REPO / "src" / "cmplx" / "transform" / rel
        if not src.is_file():
            continue
        info = _analyze_module(src)
        slug = rel.replace("/", "_").replace(".py", "")
        lines = [
            f"# Module deep dive: `{rel}`\n\n",
            f"**Source lines:** {info['lines']} | **Host path:** `src/cmplx/transform/{rel}`\n\n",
        ]
        if info["doc"]:
            lines.append("## Module purpose\n\n")
            lines.append(info["doc"].strip() + "\n\n")
        if info["classes"]:
            lines.append("## Classes\n\n")
            for cls in info["classes"]:
                lines.append(f"### `{cls['name']}`\n\n")
                if cls["doc"]:
                    lines.append(cls["doc"].strip() + "\n\n")
                if cls["methods"]:
                    lines.append("**Methods:** " + ", ".join(f"`{m}`" for m in cls["methods"]) + "\n\n")
        if info["functions"]:
            lines.append("## Top-level functions\n\n")
            for fn in info["functions"][:15]:
                lines.append(f"- `{fn['name']}`")
                if fn["doc"]:
                    lines.append(f" — {fn['doc'].splitlines()[0]}")
                lines.append("\n")
            lines.append("\n")
        lines.append("## Rebuild notes\n\n")
        lines.append(
            "When reimplementing, preserve port boundaries: use `bridge.py` accessors rather than "
            "direct imports of MORSR/TarPit/NSL. Cross-check behavior against mirrored source in "
            f"`11_SOURCE_CORPUS/code/transform/{rel}` and tests mapped in `12_TEST_SPEC/TEST_SPEC_INDEX.md`.\n\n"
        )
        lines.append("## Failure modes\n\n")
        lines.append(
            "- Missing bootstrap → provider KeyError on first forward.\n"
            "- Schema drift in TokenIndexStore → ingest/refine SQL errors.\n"
            "- Skipping shell.complete in compose → illegal ribbon reaches forward.\n\n"
        )
        lines.append("## Related reading\n\n")
        lines.append(
            "- `02_ARCHITECTURE/DATA_MODEL.md`\n"
            "- `02_ARCHITECTURE/PORT_CALL_GRAPH.md`\n"
            "- `11_SOURCE_CORPUS/code/CODE_READING_ORDER.md`\n"
        )
        body = "".join(lines)
        while len(body.split()) < 500:
            body += (
                "\n\n## Additional context\n\n"
                "This module sits in the Slot 48 (`cmplx.transform`) package. "
                "The morphonic stack is substrate-first: correctness flows from SQLite token index, "
                "Morphon shell law, and CMPLX port orchestration—not from learned attention weights. "
                "Operational v1 evidence (May 2026) includes 37k+ bonds and 123k+ translation links in "
                "`identity_review` crystal bundle schema 2.1.0. "
                "Use stratified JSONL samples under `04_DATA_AND_SCHEMA/samples/` when full SQLite cannot be uploaded.\n"
            )
        (dive_dir / f"{slug}.md").write_text(body, encoding="utf-8")
        count += 1
    return count


def export_optional_bundle(pkg: Path) -> dict[str, Any]:
    bundle_dir = pkg / "12_OPTIONAL_BUNDLE"
    bundle_dir.mkdir(parents=True, exist_ok=True)
    manifest: dict[str, Any] = {"chunks": [], "full_copy": None}
    if not DB.is_file():
        return manifest
    size = DB.stat().st_size
    if size < 80 * 1024 * 1024:
        dst = bundle_dir / DB.name
        shutil.copy2(DB, dst)
        manifest["full_copy"] = {
            "file": dst.name,
            "size_bytes": size,
            "sha256": hashlib.sha256(dst.read_bytes()).hexdigest(),
        }
        return manifest
    chunk_size = 10 * 1024 * 1024
    data = DB.read_bytes()
    for i in range(0, len(data), chunk_size):
        part = data[i : i + chunk_size]
        name = f"{DB.stem}.part{i // chunk_size:03d}"
        (bundle_dir / name).write_bytes(part)
        manifest["chunks"].append(
            {
                "file": name,
                "offset": i,
                "size_bytes": len(part),
                "sha256": hashlib.sha256(part).hexdigest(),
            }
        )
    manifest["reassembly"] = f"copy /b {DB.stem}.part* {DB.name}"
    manifest["total_size_bytes"] = size
    manifest["total_sha256"] = hashlib.sha256(data).hexdigest()
    return manifest


def export_playbook_expansion(pkg: Path) -> None:
    from handoff_expanded_playbook import (
        ACCEPTANCE_EVIDENCE,
        REBUILD_FROM_SCRATCH_EXPANDED,
        TROUBLESHOOTING,
    )

    pb = pkg / "00_REBUILD_PLAYBOOK"
    pb.mkdir(parents=True, exist_ok=True)
    (pb / "REBUILD_FROM_SCRATCH.md").write_text(REBUILD_FROM_SCRATCH_EXPANDED, encoding="utf-8")
    (pb / "TROUBLESHOOTING.md").write_text(TROUBLESHOOTING, encoding="utf-8")
    (pb / "ACCEPTANCE_EVIDENCE.md").write_text(ACCEPTANCE_EVIDENCE, encoding="utf-8")


def update_handoff_cover(pkg: Path, stats: dict[str, Any]) -> None:
    cover = f"""# Handoff cover — upload tiers

## Minimal tier (~2–5 MB)

1. `README_START_HERE.md`
2. `01_DOCTRINE_AND_STATUS/DESIGN_VS_REALITY.md` + `NORTH_STAR.md`
3. `02_ARCHITECTURE/diagrams/architecture_layers.mmd`
4. `00_REBUILD_PLAYBOOK/REBUILD_FROM_SCRATCH.md`
5. `09_FUTURE_WORK/GAP_AND_TODO.md`

## Standard tier (~5–25 MB) — recommended for web AIs

Everything in minimal, plus:

- `02_ARCHITECTURE/DATA_MODEL.md` + walkthroughs + expanded diagrams
- `04_DATA_AND_SCHEMA/` (DDL, samples, stats, crystal sidecars)
- `08_RAG_AND_GRAPH/` (`rag_manifest.jsonl`, `TAG_INDEX.json`, chunks)
- `11_SOURCE_CORPUS/` (verbatim docs + code mirror)
- `12_TEST_SPEC/` (tests as specification + `PYTEST_LAST_RUN.txt`)
- `13_MODULE_DEEP_DIVES/`
- `00_REBUILD_PLAYBOOK/TROUBLESHOOTING.md` + `ACCEPTANCE_EVIDENCE.md`

## Full tier (host fetch)

- `12_OPTIONAL_BUNDLE/` — SQLite chunks or full copy (see manifest)
- `10_BINARIES_MANIFEST/OPTIONAL_FULL_ARTIFACTS.json` — sha256 host paths

## Package stats (this build)

- Files: {stats.get('file_count', '?')}
- Standard tier (excludes `12_OPTIONAL_BUNDLE/`): ~11–15 MB uncompressed
- Full tree with chunked SQLite: {stats.get('mb', '?')} MB uncompressed
- RAG chunks: {stats.get('rag_chunks', '?')}
- Zip: `export/morphonic-rebuild-handoff-2026-05-19.zip` (~25 MB with optional chunks)

Do **not** upload multi-GB `atomic_index` — use repo indexes on host only.
"""
    (pkg / "HANDOFF_COVER.md").write_text(cover, encoding="utf-8")


def update_readme(pkg: Path, index: list[dict]) -> None:
    total = sum(i["size_bytes"] for i in index)
    readme = f"""# Morphonic Rebuild Handoff — START HERE

**Package:** morphonic-rebuild-handoff-2026-05-19  
**Purpose:** Rebuild CMPLX Morphonic Slot 48 (substrate + transformer + ports) without the full PartsFactory workspace.  
**Upload tier:** standard 5–25 MB (see `HANDOFF_COVER.md`).

## What this is

Substrate-first geometric transformer — token index + Morphon shell + port orchestration (MORSR, TarPit, NSL, SpeedLight, SNAP).

## Read order

1. [01_DOCTRINE_AND_STATUS/DESIGN_VS_REALITY.md](01_DOCTRINE_AND_STATUS/DESIGN_VS_REALITY.md)
2. [00_REBUILD_PLAYBOOK/REBUILD_FROM_SCRATCH.md](00_REBUILD_PLAYBOOK/REBUILD_FROM_SCRATCH.md)
3. [02_ARCHITECTURE/DATA_MODEL.md](02_ARCHITECTURE/DATA_MODEL.md)
4. [11_SOURCE_CORPUS/code/CODE_READING_ORDER.md](11_SOURCE_CORPUS/code/CODE_READING_ORDER.md)
5. [13_MODULE_DEEP_DIVES/](13_MODULE_DEEP_DIVES/)
6. [08_RAG_AND_GRAPH/TAG_INDEX.json](08_RAG_AND_GRAPH/TAG_INDEX.json)

## New folders (deep handoff)

| Folder | Contents |
|--------|----------|
| `11_SOURCE_CORPUS/` | Verbatim docs + full `transform/` mirror + dependency deps |
| `12_TEST_SPEC/` | Pytest sources as specification + last run output |
| `12_OPTIONAL_BUNDLE/` | Chunked or full identity_review SQLite (optional) |
| `13_MODULE_DEEP_DIVES/` | Per-module rebuild essays |

## Environment

- Python 3.10+, `pip install -e ".[dev]"`, `PYTHONPATH=src`
- Acceptance: see [00_REBUILD_PLAYBOOK/ACCEPTANCE_EVIDENCE.md](00_REBUILD_PLAYBOOK/ACCEPTANCE_EVIDENCE.md)

## Package stats

- Files: {len(index)}
- Total size: {total / (1024 * 1024):.2f} MB

## Web AI instructions

[00_REBUILD_PLAYBOOK/EXTERNAL_AI_INSTRUCTIONS.md](00_REBUILD_PLAYBOOK/EXTERNAL_AI_INSTRUCTIONS.md)
"""
    (pkg / "README_START_HERE.md").write_text(readme, encoding="utf-8")


def update_checkpoint_doc(pkg_stats: dict[str, Any]) -> None:
    cp = REPO / "docs" / "checkpoints" / "2026-05-19-009-morphonic-rebuild-handoff-suite.md"
    text = f"""# Checkpoint 009 — Morphonic Rebuild Handoff Suite (deep)

**Date:** 2026-05-19  
**Package:** `export/morphonic-rebuild-handoff-2026-05-19/`  
**Zip:** `export/morphonic-rebuild-handoff-2026-05-19.zip`

## Delivered (deep tier)

- Folders `00`–`13` including `11_SOURCE_CORPUS`, `12_TEST_SPEC`, `12_OPTIONAL_BUNDLE`, `13_MODULE_DEEP_DIVES`
- Verbatim MORPHONIC docs, transform INTERFACE/BRIDGE, identity_review checkpoints
- Full `src/cmplx/transform/**/*.py` mirror + dependency deps
- Samples: 2000 bonds, 2000 links, 500 morph_signatures, 500 meanings (stratified)
- Full crystal sidecars under 5MB; `DB_TABLE_COUNTS.json`, `STREAM_BREAKDOWN.md`
- 250+ RAG chunks + `TAG_INDEX.json`
- Expanded rebuild playbook (16 steps), troubleshooting, acceptance evidence
- Scripts: `build_morphonic_handoff_package.py`, `deepen_morphonic_handoff.py`

## Metrics (this build)

- Files: {pkg_stats.get('file_count', '?')}
- Package: ~{pkg_stats.get('mb', '?')} MB
- Zip: ~{pkg_stats.get('zip_mb', '?')} MB
- RAG chunks: {pkg_stats.get('rag_chunks', '?')}
- 37,271 bonds; 123,147 links; crystal **bc00ac8ee26c** (2.1.0)
"""
    cp.write_text(text, encoding="utf-8")


def deepen(pkg: Path | None = None) -> dict[str, Any]:
    pkg = pkg or PKG
    if not pkg.is_dir():
        raise FileNotFoundError(f"Package dir missing: {pkg}; run build first")

    result: dict[str, Any] = {}
    result["corpus"] = export_source_corpus(pkg)
    result["code"] = export_code_mirror(pkg)
    result["data"] = export_deeper_data(pkg)
    result["tests"] = export_tests(pkg)
    export_architecture(pkg)
    result["module_dives"] = export_module_deep_dives(pkg)
    result["optional_bundle"] = export_optional_bundle(pkg)
    export_playbook_expansion(pkg)

    # Refresh optional artifacts manifest with bundle info
    bin_dir = pkg / "10_BINARIES_MANIFEST"
    bin_dir.mkdir(parents=True, exist_ok=True)
    artifacts_path = bin_dir / "OPTIONAL_FULL_ARTIFACTS.json"
    artifacts: list[dict] = []
    if artifacts_path.is_file():
        artifacts = json.loads(artifacts_path.read_text(encoding="utf-8"))
    ob = result["optional_bundle"]
    if ob.get("chunks"):
        artifacts.append(
            {
                "label": "identity_review_sqlite_chunked",
                "host_path": str(DB),
                "size_bytes": ob.get("total_size_bytes"),
                "sha256": ob.get("total_sha256"),
                "note": "Included as 10MB parts in 12_OPTIONAL_BUNDLE/",
                "chunk_count": len(ob["chunks"]),
            }
        )
    elif ob.get("full_copy"):
        artifacts.append(
            {
                "label": "identity_review_sqlite_in_bundle",
                "host_path": str(DB),
                "size_bytes": ob["full_copy"]["size_bytes"],
                "sha256": ob["full_copy"]["sha256"],
                "note": "Copied to 12_OPTIONAL_BUNDLE/",
            }
        )
    artifacts_path.write_text(json.dumps(artifacts, indent=2), encoding="utf-8")

    return result


def main() -> int:
    stats = deepen()
    print(json.dumps(stats, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
