#!/usr/bin/env python3
"""Build a promotion ledger for repo-kernel modules.

This converts repo-kernel + GitNexus data into a decision surface:

    evidence -> candidate -> promoted module -> canonical module -> archived

The script reads clean clone metadata from `repo_kernel/manifest/repos.json`,
adds local clone shape, adds completed GitNexus metrics when available, scores
each module by likely contribution, and writes SQLite/JSON/Markdown outputs.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import re
import sqlite3
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any


DEFAULT_DB = Path("data/three_space_catalog.sqlite")
DEFAULT_MANIFEST = Path("repo_kernel/manifest/repos.json")
DEFAULT_REPORT = Path("docs/REPO_PROMOTION_LEDGER_2026-05-13.md")
DEFAULT_JSON = Path("reports/repo_promotion_ledger_2026-05-13.json")

CODE_EXTS = {
    ".py",
    ".js",
    ".jsx",
    ".ts",
    ".tsx",
    ".go",
    ".rs",
    ".java",
    ".c",
    ".cpp",
    ".h",
    ".hpp",
    ".cs",
    ".sh",
    ".ps1",
}

PRUNE_DIRS = {".git", ".gitnexus", "node_modules", ".venv", "venv", "__pycache__", ".pytest_cache", "dist", "build"}

ALIAS_BY_REPO = {
    "CMPLX-Formalization": "rk-cmplx-formalization",
    "scout-demo-service": "rk-scout-demo-service",
    "CMPLX-Manny": "rk-cmplx-manny",
    "CMPLX-TMN-main": "rk-cmplx-tmn-main",
    "CMPLX-TMN1": "rk-cmplx-tmn1",
    "CMPLXMCP": "rk-cmplxmcp",
    "CMPLX-Monorepo": "rk-cmplx-monorepo",
    "CMPLXDevKit": "rk-cmplxdevkit",
    "CMPLXUNI": "rk-cmplxuni",
    "CMPLX": "rk-cmplx",
    "CMPLX-1T": "rk-cmplx-1t",
}

ROLE_HINTS = {
    "active_unification_root": ("workspace_root", 0),
    "manny_identity_system": ("memory_identity", 26),
    "tmn_primary": ("service_controller_core", 38),
    "tmn_historical_build": ("historical_tmn_reference", 22),
    "geometric_system_build": ("slice_index_needed", 32),
    "developer_toolkit": ("toolkit_mine", 28),
    "baseline_core": ("baseline_core_candidate", 30),
    "historical_monorepo_reference": ("integration_reference", 26),
    "unified_system_build": ("unified_family_candidate", 40),
    "mcp_layer": ("mcp_api_candidate", 42),
    "mathematical_doctrine": ("doctrine", 34),
    "external_service_reference": ("archive_reference", 8),
}

ROLE_SCORE_CAP = {
    "active_unification_root": 12,
    "external_service_reference": 30,
    "tmn_historical_build": 62,
    "manny_identity_system": 66,
    "historical_monorepo_reference": 74,
    "developer_toolkit": 72,
    "geometric_system_build": 58,
    "baseline_core": 64,
    "mathematical_doctrine": 82,
    "tmn_primary": 92,
    "unified_system_build": 94,
    "mcp_layer": 96,
}

SCHEMA = """
CREATE TABLE IF NOT EXISTS repo_promotion_ledger (
    module_name TEXT PRIMARY KEY,
    status TEXT NOT NULL,
    recommended_action TEXT NOT NULL,
    role TEXT,
    promotion_score REAL,
    readiness_score REAL,
    risk_score REAL,
    gitnexus_alias TEXT,
    gitnexus_indexed INTEGER DEFAULT 0,
    pinned_commit TEXT,
    branch TEXT,
    local_path TEXT,
    summary TEXT,
    evidence_json TEXT,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS repo_module_score (
    module_name TEXT PRIMARY KEY,
    files INTEGER,
    code_files INTEGER,
    bytes INTEGER,
    large_files INTEGER,
    gitnexus_files INTEGER,
    symbols INTEGER,
    edges INTEGER,
    clusters INTEGER,
    processes INTEGER,
    functions INTEGER,
    classes INTEGER,
    routes INTEGER,
    tools INTEGER,
    score_json TEXT,
    updated_at TEXT NOT NULL
);
"""


@dataclass
class LocalStats:
    files: int = 0
    code_files: int = 0
    bytes: int = 0
    large_files: int = 0
    top_dirs: dict[str, int] | None = None
    huge_examples: list[dict[str, Any]] | None = None


def utc_now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def fmt_bytes(n: int | None) -> str:
    n = int(n or 0)
    value = float(n)
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if value < 1024 or unit == "TB":
            return f"{value:,.1f} {unit}" if unit != "B" else f"{n:,} B"
        value /= 1024
    return f"{n:,} B"


def run(cmd: list[str], timeout: int = 120) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, check=False)


def connect(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA busy_timeout=30000")
    conn.execute("PRAGMA journal_mode=WAL")
    conn.executescript(SCHEMA)
    return conn


def load_manifest(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def local_stats(root: Path) -> LocalStats:
    stats = LocalStats(top_dirs={}, huge_examples=[])
    if not root.exists():
        return stats
    for current, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in PRUNE_DIRS]
        current_path = Path(current)
        for filename in files:
            path = current_path / filename
            try:
                size = path.stat().st_size
            except OSError:
                continue
            rel = path.relative_to(root)
            top = rel.parts[0] if rel.parts else "."
            stats.files += 1
            stats.bytes += size
            stats.top_dirs[top] = stats.top_dirs.get(top, 0) + 1
            if path.suffix.lower() in CODE_EXTS:
                stats.code_files += 1
            if size > 512 * 1024:
                stats.large_files += 1
            if size > 2_000_000:
                stats.huge_examples.append({"path": str(rel).replace("\\", "/"), "bytes": size})
    stats.huge_examples = sorted(stats.huge_examples, key=lambda x: x["bytes"], reverse=True)[:10]
    stats.top_dirs = dict(sorted(stats.top_dirs.items(), key=lambda x: x[1], reverse=True)[:10])
    return stats


def parse_gitnexus_list(text: str) -> dict[str, dict[str, Any]]:
    records: dict[str, dict[str, Any]] = {}
    current: dict[str, Any] | None = None
    for raw in text.splitlines():
        line = raw.rstrip()
        if not line.strip():
            continue
        if line.startswith("  ") and not line.startswith("    "):
            name = line.strip()
            current = {"alias": name}
            records[name] = current
            continue
        if current is None:
            continue
        stripped = line.strip()
        if stripped.startswith("Path:"):
            current["path"] = stripped.split("Path:", 1)[1].strip()
        elif stripped.startswith("Indexed:"):
            current["indexed_at"] = stripped.split("Indexed:", 1)[1].strip()
        elif stripped.startswith("Commit:"):
            current["commit"] = stripped.split("Commit:", 1)[1].strip()
        elif stripped.startswith("Stats:"):
            nums = {k: int(v) for v, k in re.findall(r"(\d+)\s+(files|symbols|edges)", stripped)}
            current.update(nums)
        elif stripped.startswith("Clusters:"):
            match = re.search(r"(\d+)", stripped)
            if match:
                current["clusters"] = int(match.group(1))
        elif stripped.startswith("Processes:"):
            match = re.search(r"(\d+)", stripped)
            if match:
                current["processes"] = int(match.group(1))
    return records


def gitnexus_list() -> dict[str, dict[str, Any]]:
    proc = run(
        [
            "docker",
            "exec",
            "gitnexus-rebuild-server",
            "sh",
            "-lc",
            "cd /workspace/current-partsfactory/CMPLX-PartsFactory && node /app/gitnexus/dist/cli/index.js list",
        ],
        timeout=120,
    )
    if proc.returncode != 0:
        return {}
    return parse_gitnexus_list(proc.stdout)


def cypher_count(alias: str, label: str) -> int | None:
    query = f"MATCH (n:{label}) RETURN count(n) AS count"
    proc = run(
        ["docker", "exec", "gitnexus-rebuild-server", "node", "/app/gitnexus/dist/cli/index.js", "cypher", "-r", alias, query],
        timeout=60,
    )
    if proc.returncode != 0 or not proc.stdout.strip():
        return None
    try:
        payload = json.loads(proc.stdout)
    except json.JSONDecodeError:
        return None
    markdown = payload.get("markdown") or ""
    nums = re.findall(r"\|\s*(\d+)\s*\|", markdown)
    return int(nums[-1]) if nums else None


def cypher_examples(alias: str, label: str, column: str, limit: int = 12) -> list[dict[str, Any]]:
    query = f"MATCH (n:{label}) RETURN n.filePath AS file, n.name AS {column} LIMIT {limit}"
    proc = run(
        ["docker", "exec", "gitnexus-rebuild-server", "node", "/app/gitnexus/dist/cli/index.js", "cypher", "-r", alias, query],
        timeout=60,
    )
    if proc.returncode != 0:
        return []
    try:
        payload = json.loads(proc.stdout)
    except json.JSONDecodeError:
        return []
    if not isinstance(payload, dict):
        return []
    markdown = payload.get("markdown") or ""
    rows = []
    for line in markdown.splitlines():
        if not line.startswith("|") or "---" in line or "file" in line:
            continue
        parts = [p.strip() for p in line.strip("|").split("|")]
        if len(parts) >= 2:
            rows.append({"file": parts[0], column: parts[1]})
    return rows


def role_base(role: str) -> tuple[str, int]:
    return ROLE_HINTS.get(role, ("repo_module", 40))


def score_module(module: dict[str, Any], local: LocalStats, gx: dict[str, Any] | None, counts: dict[str, int | None]) -> dict[str, Any]:
    role = module.get("role") or "repo_module"
    contribution, base = role_base(role)
    indexed = gx is not None
    processes = int((gx or {}).get("processes") or 0)
    clusters = int((gx or {}).get("clusters") or 0)
    symbols = int((gx or {}).get("symbols") or 0)
    routes = int(counts.get("Route") or 0)
    tools = int(counts.get("Tool") or 0)
    functions = int(counts.get("Function") or 0)
    classes = int(counts.get("Class") or 0)

    api_surface = min(18, routes * 0.035 + tools * 0.45)
    graph_signal = min(14, math.log10(max(symbols, 1)) * 2.2 + min(processes, 300) / 180)
    implementation = min(12, math.log10(max(functions + classes, 1)) * 2.4)
    freshness = 5 if module.get("pushed_at", "") >= "2026-04-01" else 2
    readiness = 12 if indexed else 2
    noise_penalty = 0
    if local.files > 10_000:
        noise_penalty += 18
    if local.bytes > 750_000_000:
        noise_penalty += 14
    if role == "developer_toolkit":
        noise_penalty += 10
    if role == "geometric_system_build" and not indexed:
        noise_penalty += 20
    if module["name"] == "CMPLX-PartsFactory" and not module.get("pinned_commit"):
        noise_penalty += 35

    cap = ROLE_SCORE_CAP.get(role, 70)
    raw_score = base + api_surface + graph_signal + implementation + freshness + readiness - noise_penalty
    promotion_score = max(0, min(cap, raw_score))
    readiness_score = max(0, min(100, readiness * 2 + graph_signal + (14 if module.get("dirty_state") == "clean" else 0) - noise_penalty / 3))
    risk_score = max(0, min(100, noise_penalty + (20 if not indexed and local.files > 0 else 0) + (10 if local.large_files > 50 else 0)))

    return {
        "contribution": contribution,
        "promotion_score": round(promotion_score, 1),
        "readiness_score": round(readiness_score, 1),
        "risk_score": round(risk_score, 1),
        "api_surface_score": round(api_surface, 1),
        "graph_signal_score": round(graph_signal, 1),
        "implementation_score": round(implementation, 1),
        "noise_penalty": noise_penalty,
    }


def recommend(module: dict[str, Any], score: dict[str, Any], indexed: bool) -> tuple[str, str, str]:
    name = module["name"]
    role = module.get("role") or ""
    if name == "CMPLX-PartsFactory":
        return (
            "workspace_root",
            "keep as orchestration root; do not promote as source module until GitHub repo has a real pinned commit",
            "Active local root and Docker/workspace home, but GitHub clone is empty/no-commit.",
        )
    if role in {"mcp_layer", "unified_system_build", "tmn_primary"}:
        return (
            "promoted_candidate",
            "build adapters and capability tests first",
            "High-value module with clear API/controller implementation surface.",
        )
    if role == "mathematical_doctrine":
        return (
            "canonical_doctrine",
            "promote docs/specs as doctrine layer; no runtime merge needed",
            "Small, focused formalization source.",
        )
    if role == "developer_toolkit":
        return (
            "filtered_candidate",
            "mine for reusable tools after filtering external/vendor shards",
            "Large toolkit source, but noisy and overbroad.",
        )
    if role == "geometric_system_build":
        return (
            "needs_slice_index",
            "index selected subdirectories; do not full-root scan",
            "Potentially valuable but too large/noisy for direct promotion.",
        )
    if role in {"historical_monorepo_reference", "tmn_historical_build"}:
        return (
            "reference_candidate",
            "use for provenance and cross-checking, not first canonical source",
            "Useful integration history but likely superseded by clearer modules.",
        )
    if role == "manny_identity_system":
        return (
            "candidate_review",
            "review memory/identity assets and promote only active pieces",
            "Small enough to inspect; likely identity/memory evidence.",
        )
    if role == "external_service_reference":
        return ("archive_reference", "archive unless a direct service dependency emerges", "External reference with low CMPLX core signal.")
    if not indexed:
        return ("unindexed_review", "index bounded subdirectories or inspect manually", "No completed GitNexus index yet.")
    return ("candidate_review", "manual review", "General candidate.")


def build_ledger(manifest_path: Path, use_gitnexus: bool) -> dict[str, Any]:
    manifest = load_manifest(manifest_path)
    gx_records = gitnexus_list() if use_gitnexus else {}
    modules_out = []
    for module in manifest.get("modules", []):
        name = module["name"]
        alias = ALIAS_BY_REPO.get(name)
        gx = gx_records.get(alias) if alias else None
        stats = local_stats(Path(module["local_path"]))
        counts: dict[str, int | None] = {"Function": None, "Class": None, "Route": None, "Tool": None}
        examples: dict[str, list[dict[str, Any]]] = {"routes": [], "tools": []}
        if use_gitnexus and gx and alias:
            for label in counts:
                counts[label] = cypher_count(alias, label)
            examples["routes"] = cypher_examples(alias, "Route", "route", limit=12)
            examples["tools"] = cypher_examples(alias, "Tool", "tool", limit=12)
        score = score_module(module, stats, gx, counts)
        status, action, summary = recommend(module, score, gx is not None)
        modules_out.append(
            {
                "name": name,
                "role": module.get("role"),
                "contribution": score["contribution"],
                "status": status,
                "recommended_action": action,
                "summary": summary,
                "pinned_commit": module.get("pinned_commit") or "",
                "branch": module.get("checked_out_branch") or module.get("default_branch") or "",
                "local_path": module.get("local_path"),
                "gitnexus_alias": alias,
                "gitnexus_indexed": gx is not None,
                "local": {
                    "files": stats.files,
                    "code_files": stats.code_files,
                    "bytes": stats.bytes,
                    "large_files": stats.large_files,
                    "top_dirs": stats.top_dirs,
                    "huge_examples": stats.huge_examples,
                },
                "gitnexus": {
                    "files": (gx or {}).get("files"),
                    "symbols": (gx or {}).get("symbols"),
                    "edges": (gx or {}).get("edges"),
                    "clusters": (gx or {}).get("clusters"),
                    "processes": (gx or {}).get("processes"),
                    "functions": counts.get("Function"),
                    "classes": counts.get("Class"),
                    "routes": counts.get("Route"),
                    "tools": counts.get("Tool"),
                    "examples": examples,
                },
                "score": score,
            }
        )
    modules_out.sort(key=lambda m: (m["score"]["promotion_score"], -m["score"]["risk_score"]), reverse=True)
    return {"generated_at": utc_now(), "modules": modules_out}


def write_sqlite(conn: sqlite3.Connection, ledger: dict[str, Any]) -> None:
    now = utc_now()
    for m in ledger["modules"]:
        evidence = {"local": m["local"], "gitnexus": m["gitnexus"], "contribution": m["contribution"]}
        conn.execute(
            """
            INSERT INTO repo_promotion_ledger(module_name, status, recommended_action, role,
                promotion_score, readiness_score, risk_score, gitnexus_alias, gitnexus_indexed,
                pinned_commit, branch, local_path, summary, evidence_json, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(module_name) DO UPDATE SET
                status=excluded.status,
                recommended_action=excluded.recommended_action,
                role=excluded.role,
                promotion_score=excluded.promotion_score,
                readiness_score=excluded.readiness_score,
                risk_score=excluded.risk_score,
                gitnexus_alias=excluded.gitnexus_alias,
                gitnexus_indexed=excluded.gitnexus_indexed,
                pinned_commit=excluded.pinned_commit,
                branch=excluded.branch,
                local_path=excluded.local_path,
                summary=excluded.summary,
                evidence_json=excluded.evidence_json,
                updated_at=excluded.updated_at
            """,
            (
                m["name"],
                m["status"],
                m["recommended_action"],
                m["role"],
                m["score"]["promotion_score"],
                m["score"]["readiness_score"],
                m["score"]["risk_score"],
                m["gitnexus_alias"],
                1 if m["gitnexus_indexed"] else 0,
                m["pinned_commit"],
                m["branch"],
                m["local_path"],
                m["summary"],
                json.dumps(evidence, sort_keys=True),
                now,
            ),
        )
        gx = m["gitnexus"]
        loc = m["local"]
        conn.execute(
            """
            INSERT INTO repo_module_score(module_name, files, code_files, bytes, large_files,
                gitnexus_files, symbols, edges, clusters, processes, functions, classes, routes,
                tools, score_json, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(module_name) DO UPDATE SET
                files=excluded.files,
                code_files=excluded.code_files,
                bytes=excluded.bytes,
                large_files=excluded.large_files,
                gitnexus_files=excluded.gitnexus_files,
                symbols=excluded.symbols,
                edges=excluded.edges,
                clusters=excluded.clusters,
                processes=excluded.processes,
                functions=excluded.functions,
                classes=excluded.classes,
                routes=excluded.routes,
                tools=excluded.tools,
                score_json=excluded.score_json,
                updated_at=excluded.updated_at
            """,
            (
                m["name"],
                loc["files"],
                loc["code_files"],
                loc["bytes"],
                loc["large_files"],
                gx.get("files"),
                gx.get("symbols"),
                gx.get("edges"),
                gx.get("clusters"),
                gx.get("processes"),
                gx.get("functions"),
                gx.get("classes"),
                gx.get("routes"),
                gx.get("tools"),
                json.dumps(m["score"], sort_keys=True),
                now,
            ),
        )
    conn.commit()


def markdown_table(modules: list[dict[str, Any]]) -> str:
    lines = [
        "| Rank | Module | Status | Role | Score | Risk | GitNexus | Key signal | Action |",
        "| ---: | --- | --- | --- | ---: | ---: | --- | --- | --- |",
    ]
    for idx, m in enumerate(modules, 1):
        gx = m["gitnexus"]
        signal = []
        if gx.get("routes"):
            signal.append(f"{gx['routes']} routes")
        if gx.get("tools"):
            signal.append(f"{gx['tools']} tools")
        if gx.get("processes"):
            signal.append(f"{gx['processes']} flows")
        if gx.get("symbols"):
            signal.append(f"{gx['symbols']:,} symbols")
        if not signal:
            signal.append(f"{m['local']['code_files']:,} code files")
        lines.append(
            f"| {idx} | `{m['name']}` | `{m['status']}` | `{m['role']}` | "
            f"{m['score']['promotion_score']:.1f} | {m['score']['risk_score']:.1f} | "
            f"{'yes' if m['gitnexus_indexed'] else 'no'} | {', '.join(signal)} | {m['recommended_action']} |"
        )
    return "\n".join(lines)


def write_report(path: Path, ledger: dict[str, Any]) -> None:
    modules = ledger["modules"]
    promoted = [m for m in modules if m["status"] in {"promoted_candidate", "canonical_doctrine"}]
    needs = [m for m in modules if m["status"] in {"needs_slice_index", "filtered_candidate", "unindexed_review"}]
    lines = [
        "# Repo Promotion Ledger - 2026-05-13",
        "",
        "This ledger ranks clean repo-kernel modules for the master CMPLX rebuild.",
        "It is a decision layer, not a deletion list.",
        "",
        "## Promotion States",
        "",
        "- `promoted_candidate`: build adapters/tests first; likely first-wave source.",
        "- `canonical_doctrine`: promote as doctrine/specification, not runtime code.",
        "- `filtered_candidate`: valuable but too noisy to promote wholesale.",
        "- `reference_candidate`: use for provenance/cross-checking.",
        "- `needs_slice_index`: do not full-root index; index selected subdirectories.",
        "- `archive_reference`: keep for archive/evidence unless a dependency emerges.",
        "",
        "## Ranked Ledger",
        "",
        markdown_table(modules),
        "",
        "## First-Wave Promotions",
        "",
    ]
    for m in promoted:
        lines.append(f"- `{m['name']}`: {m['summary']} Action: {m['recommended_action']}.")
    lines.extend(["", "## Needs Filtering Or Slicing", ""])
    for m in needs:
        lines.append(
            f"- `{m['name']}`: {m['summary']} "
            f"Local shape: {m['local']['files']:,} files, {fmt_bytes(m['local']['bytes'])}, "
            f"{m['local']['large_files']:,} large files. Action: {m['recommended_action']}."
        )
    lines.extend(["", "## Route And Tool Signals", ""])
    for m in modules:
        examples = m["gitnexus"].get("examples") or {}
        routes = examples.get("routes") or []
        tools = examples.get("tools") or []
        if not routes and not tools:
            continue
        lines.append(f"### {m['name']}")
        if routes:
            lines.append("")
            lines.append("Routes:")
            for item in routes[:8]:
                lines.append(f"- `{item.get('route')}` in `{item.get('file')}`")
        if tools:
            lines.append("")
            lines.append("Tools:")
            for item in tools[:8]:
                lines.append(f"- `{item.get('tool')}` in `{item.get('file')}`")
        lines.append("")
    lines.extend(
        [
            "## Recommended Next Work",
            "",
            "1. Build adapter skeletons for `CMPLXMCP`, `CMPLXUNI`, and `CMPLX-TMN-main`.",
            "2. Add capability tests around routes/tools rather than repo-native test suites.",
            "3. Slice-index `CMPLX-1T` and selected `CMPLX` directories instead of full-root scans.",
            "4. Filter `CMPLXDevKit` before promotion, especially `src/cqe_organized/` external/test shards.",
            "5. Use `CMPLX-Formalization` as canonical doctrine and provenance language.",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Build repo promotion ledger")
    parser.add_argument("--manifest", default=str(DEFAULT_MANIFEST))
    parser.add_argument("--db", default=str(DEFAULT_DB))
    parser.add_argument("--json-out", default=str(DEFAULT_JSON))
    parser.add_argument("--report", default=str(DEFAULT_REPORT))
    parser.add_argument("--no-gitnexus", action="store_true")
    args = parser.parse_args()

    ledger = build_ledger(Path(args.manifest), use_gitnexus=not args.no_gitnexus)
    Path(args.json_out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.json_out).write_text(json.dumps(ledger, indent=2, sort_keys=False) + "\n", encoding="utf-8")
    write_report(Path(args.report), ledger)
    conn = connect(Path(args.db))
    write_sqlite(conn, ledger)
    conn.close()

    print(f"Wrote {args.report}")
    print(f"Wrote {args.json_out}")
    print("\nTop promotion candidates:")
    for m in ledger["modules"][:8]:
        print(
            f"  {m['score']['promotion_score']:>5.1f} risk {m['score']['risk_score']:>4.1f} "
            f"{m['status']:<22s} {m['name']:<22s} {m['contribution']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
