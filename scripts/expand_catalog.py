#!/usr/bin/env python3
"""
Expand Catalog — Python-based evidence cataloger (GitNexus-compatible schema).

Walks target directories, extracts code metadata, produces evidence records
in the same schema as GitNexus reports. Stores in SQLite for aggregation.

Usage:
    python scripts/expand_catalog.py --scan <path> --system <name> --tag <tag>
    python scripts/expand_catalog.py --batch-scan batch.json
    python scripts/expand_catalog.py --report
"""

from __future__ import annotations

import argparse
import ast
import json
import os
import sqlite3
import sys
from dataclasses import dataclass
from pathlib import Path

DB_PATH = "data/expanded_catalog.sqlite"

# File extension to language mapping
EXT_LANG = {
    ".py": "python", ".pyx": "python", ".pyi": "python",
    ".js": "javascript", ".mjs": "javascript", ".jsx": "javascript",
    ".ts": "typescript", ".tsx": "typescript",
    ".c": "c", ".h": "c",
    ".cpp": "cpp", ".hpp": "cpp", ".cc": "cpp",
    ".go": "go",
    ".rs": "rust",
    ".java": "java",
    ".rb": "ruby",
    ".sh": "shell", ".bash": "shell",
    ".ps1": "powershell",
    ".yaml": "yaml", ".yml": "yaml",
    ".json": "json",
    ".toml": "toml",
    ".md": "markdown",
    ".dockerfile": "dockerfile", ".dockerignore": "dockerfile",
}

# Directories to skip
SKIP_DIRS = {".git", "__pycache__", "node_modules", ".venv", "venv", "dist", "build", ".pytest_cache", ".opencode"}


@dataclass
class EvidenceRecord:
    evidence_id: str
    name: str
    source_path: str
    system: str
    language: str
    file_size: str
    line_count: int
    implement_status: str
    confidence: str
    capability_summary: str
    top_level_defs: str
    scan_tag: str


def get_language(path: str) -> str:
    ext = Path(path).suffix.lower()
    if ext in EXT_LANG:
        return EXT_LANG[ext]
    basename = Path(path).name.lower()
    if basename in ("dockerfile", ".dockerignore"):
        return "dockerfile"
    if basename.endswith(".sh"):
        return "shell"
    return "unknown"


def extract_python_defs(source: str) -> list[str]:
    try:
        tree = ast.parse(source)
        defs = []
        for node in tree.body:
            if isinstance(node, ast.ClassDef):
                defs.append(f"class:{node.name}")
            elif isinstance(node, ast.FunctionDef):
                defs.append(f"def:{node.name}")
            elif isinstance(node, ast.AsyncFunctionDef):
                defs.append(f"async:{node.name}")
        return defs
    except Exception:
        return []


def summarize_file(path: str, language: str, source: str | None) -> tuple[str, list[str]]:
    """Produce a capability summary and top-level definitions."""
    defs = []
    if language == "python" and source:
        defs = extract_python_defs(source)

    if defs:
        summary = f"{language} module. Top-level: {', '.join(defs[:5])}"
        if len(defs) > 5:
            summary += f" ... ({len(defs)} total)"
    else:
        summary = f"{language} source file. Bulk-registered source - content extraction pending."

    return summary, defs


def scan_target(target_path: str, system_name: str, scan_tag: str) -> list[EvidenceRecord]:
    root = Path(target_path)
    if not root.exists():
        print(f"SKIP: {target_path} does not exist")
        return []

    records = []
    total = 0
    for dirpath, dirnames, filenames in os.walk(root):
        # Prune skip dirs
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]

        for fname in filenames:
            abs_p = Path(dirpath) / fname
            try:
                size = abs_p.stat().st_size
            except (OSError, PermissionError):
                continue

            language = get_language(str(abs_p))
            if language == "unknown" and size < 100:
                continue  # Skip tiny unknown files

            rel = str(abs_p.relative_to(root)).replace("\\", "/")
            evidence_id = f"{scan_tag}_{system_name}_{rel.replace('/', '_').replace('.', '_')[:80]}"

            # Try to read source for Python files
            source = None
            if language == "python" and size < 500_000:  # Skip huge files
                try:
                    source = abs_p.read_text(encoding="utf-8", errors="replace")
                except Exception:
                    pass

            summary, defs = summarize_file(str(abs_p), language, source)
            lines = source.count("\n") + 1 if source else 0

            # Format size like GitNexus
            if size < 1024:
                size_str = f"{size} B"
            elif size < 1024 * 1024:
                size_str = f"{size / 1024:.1f} KB"
            else:
                size_str = f"{size / (1024 * 1024):.1f} MB"

            records.append(EvidenceRecord(
                evidence_id=evidence_id,
                name=fname,
                source_path=rel,
                system=system_name,
                language=language,
                file_size=size_str,
                line_count=lines,
                implement_status="evidence",
                confidence="claim",
                capability_summary=summary,
                top_level_defs=",".join(defs),
                scan_tag=scan_tag,
            ))
            total += 1
            if total % 1000 == 0:
                print(f"  ... {total} files cataloged")

    print(f"  Done: {total} evidence records for {system_name}")
    return records


def save_records(records: list[EvidenceRecord]) -> None:
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
    CREATE TABLE IF NOT EXISTS evidence_catalog (
        evidence_id TEXT PRIMARY KEY,
        name TEXT,
        source_path TEXT,
        system TEXT,
        language TEXT,
        file_size TEXT,
        line_count INTEGER,
        implement_status TEXT,
        confidence TEXT,
        capability_summary TEXT,
        top_level_defs TEXT,
        scan_tag TEXT
    )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_ev_system ON evidence_catalog(system)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_ev_language ON evidence_catalog(language)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_ev_tag ON evidence_catalog(scan_tag)")

    for rec in records:
        conn.execute("""
        INSERT OR REPLACE INTO evidence_catalog VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            rec.evidence_id, rec.name, rec.source_path, rec.system, rec.language,
            rec.file_size, rec.line_count, rec.implement_status, rec.confidence,
            rec.capability_summary, rec.top_level_defs, rec.scan_tag
        ))

    conn.commit()
    conn.close()


def print_report() -> None:
    if not Path(DB_PATH).exists():
        print(f"No catalog found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    print("\n=== EXPANDED CATALOG REPORT ===\n")

    cur = conn.execute("SELECT COUNT(*) as cnt FROM evidence_catalog")
    total = cur.fetchone()["cnt"]
    print(f"Total evidence records: {total}")

    print("\n--- By System ---")
    cur = conn.execute("""
        SELECT system, COUNT(*) as cnt, COUNT(DISTINCT language) as langs, SUM(line_count) as lines
        FROM evidence_catalog GROUP BY system ORDER BY cnt DESC
    """)
    for row in cur:
        print(f"  {row['cnt']:>6} files  {row['langs']:>2} langs  {row['lines'] or 0:>8,} lines  {row['system']}")

    print("\n--- By Language ---")
    cur = conn.execute("""
        SELECT language, COUNT(*) as cnt FROM evidence_catalog GROUP BY language ORDER BY cnt DESC
    """)
    for row in cur:
        print(f"  {row['cnt']:>6} files  {row['language']}")

    print("\n--- Top Python Modules by Line Count ---")
    cur = conn.execute("""
        SELECT name, system, line_count, source_path
        FROM evidence_catalog
        WHERE language = 'python' AND line_count > 0
        ORDER BY line_count DESC
        LIMIT 15
    """)
    for row in cur:
        print(f"  {row['line_count']:>5} lines  {row['system']:20s}  {row['name']:30s}  {row['source_path'][:50]}")

    print("\n--- Shared Names Across Systems ---")
    cur = conn.execute("""
        SELECT name, COUNT(DISTINCT system) as sys_cnt, GROUP_CONCAT(DISTINCT system) as systems
        FROM evidence_catalog
        WHERE name NOT IN ('__init__.py', 'setup.py', '.gitignore', 'README.md')
        GROUP BY name
        HAVING sys_cnt > 1
        ORDER BY sys_cnt DESC
        LIMIT 20
    """)
    for row in cur:
        print(f"  {row['sys_cnt']} systems  {row['name']:40s}  [{row['systems']}]")

    conn.close()


def main() -> int:
    parser = argparse.ArgumentParser(description="Expand Catalog")
    parser.add_argument("--scan", help="Target directory to scan")
    parser.add_argument("--system", help="System name for the scan")
    parser.add_argument("--tag", default="manual", help="Scan tag")
    parser.add_argument("--batch-scan", help="JSON file with scan targets")
    parser.add_argument("--report", action="store_true", help="Print aggregate report")
    args = parser.parse_args()

    if args.batch_scan:
        with open(args.batch_scan, "r") as f:
            targets = json.load(f)
        all_records = []
        for entry in targets:
            path = entry.get("path")
            system = entry.get("system")
            tag = entry.get("tag", "batch")
            if path and system:
                print(f"\nScanning {system} at {path}...")
                records = scan_target(path, system, tag)
                all_records.extend(records)
        if all_records:
            save_records(all_records)
            print(f"\nSaved {len(all_records)} total records")

    elif args.scan and args.system:
        print(f"Scanning {args.system} at {args.scan}...")
        records = scan_target(args.scan, args.system, args.tag)
        if records:
            save_records(records)

    if args.report or args.batch_scan or (args.scan and args.system):
        print_report()

    return 0


if __name__ == "__main__":
    sys.exit(main())
