#!/usr/bin/env python3
"""
Aggregate GitNexus Reports — parse 4,791 code evidence reports into a capability index.

Extracts structured fields from each report.md, builds SQLite index,
and produces cross-system capability maps.

Usage:
    python scripts/aggregate_gitnexus.py --scan
    python scripts/aggregate_gitnexus.py --report
    python scripts/aggregate_gitnexus.py --capability <system>
"""

from __future__ import annotations

import argparse
import os
import re
import sqlite3
import sys
from dataclasses import dataclass
from pathlib import Path

REPORTS_ROOT = "D:/Manny Unification 2/output/reports/code-reports"
DB_PATH = "data/gitnexus_index.sqlite"


@dataclass
class ReportRecord:
    report_id: str
    name: str
    source_path: str
    source_id: str
    system: str
    language: str
    file_size: str
    implement_status: str
    confidence: str
    capability_summary: str


def parse_report(report_path: str) -> ReportRecord | None:
    try:
        with open(report_path, "r", encoding="utf-8", errors="replace") as f:
            text = f.read()
    except Exception:
        return None

    # Extract report name from heading
    name_match = re.search(r"# Code Report: (.+)", text)
    name = name_match.group(1).strip() if name_match else ""

    # Provenance fields
    system = re.search(r"\*\*System of origin\*\*: (.+)", text)
    language = re.search(r"\*\*Language\*\*: (.+)", text)
    source_path = re.search(r"\*\*Source path\*\*: `(.+?)`", text)
    source_id = re.search(r"\*\*Source ID\*\*: `(.+?)`", text)
    file_size = re.search(r"\*\*File size\*\*: (.+)", text)
    implement_status = re.search(r"\*\*Implement status\*\*: `(.+?)`", text)
    confidence = re.search(r"\*\*Confidence\*\*: `(.+?)`", text)

    # Capability Summary
    cap_match = re.search(r"## Capability Summary\n+(.+?)(?:\n##|$)", text, re.DOTALL)
    capability_summary = cap_match.group(1).strip()[:500] if cap_match else ""

    report_id = Path(report_path).parent.name

    return ReportRecord(
        report_id=report_id,
        name=name,
        source_path=source_path.group(1) if source_path else "",
        source_id=source_id.group(1) if source_id else "",
        system=system.group(1).strip() if system else "unknown",
        language=language.group(1).strip() if language else "unknown",
        file_size=file_size.group(1).strip() if file_size else "",
        implement_status=implement_status.group(1) if implement_status else "unknown",
        confidence=confidence.group(1) if confidence else "unknown",
        capability_summary=capability_summary,
    )


def build_index() -> None:
    print(f"Scanning {REPORTS_ROOT}...")
    reports = []
    for root, dirs, files in os.walk(REPORTS_ROOT):
        if "report.md" in files:
            path = os.path.join(root, "report.md")
            rec = parse_report(path)
            if rec:
                reports.append(rec)
        if len(reports) % 500 == 0:
            print(f"  ... parsed {len(reports)} reports")

    print(f"Parsed {len(reports)} reports. Building index...")

    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
    CREATE TABLE IF NOT EXISTS gitnexus_reports (
        report_id TEXT PRIMARY KEY,
        name TEXT,
        source_path TEXT,
        source_id TEXT,
        system TEXT,
        language TEXT,
        file_size TEXT,
        implement_status TEXT,
        confidence TEXT,
        capability_summary TEXT
    )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_system ON gitnexus_reports(system)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_language ON gitnexus_reports(language)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_status ON gitnexus_reports(implement_status)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_name ON gitnexus_reports(name)")

    for rec in reports:
        conn.execute("""
        INSERT OR REPLACE INTO gitnexus_reports VALUES (?,?,?,?,?,?,?,?,?,?)
        """, (
            rec.report_id, rec.name, rec.source_path, rec.source_id,
            rec.system, rec.language, rec.file_size, rec.implement_status,
            rec.confidence, rec.capability_summary
        ))

    conn.commit()
    conn.close()
    print(f"Index saved to {DB_PATH}")


def print_report() -> None:
    if not Path(DB_PATH).exists():
        print(f"No database found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    print("\n=== GITNEXUS AGGREGATE REPORT ===\n")

    # Overall stats
    cur = conn.execute("SELECT COUNT(*) as cnt FROM gitnexus_reports")
    total = cur.fetchone()["cnt"]
    print(f"Total reports indexed: {total}")

    # By system
    print("\n--- By System ---")
    cur = conn.execute("""
        SELECT system, COUNT(*) as cnt, COUNT(DISTINCT language) as langs
        FROM gitnexus_reports GROUP BY system ORDER BY cnt DESC
    """)
    for row in cur:
        print(f"  {row['cnt']:>5} reports  {row['langs']:>2} languages  {row['system']}")

    # By language
    print("\n--- By Language ---")
    cur = conn.execute("""
        SELECT language, COUNT(*) as cnt FROM gitnexus_reports GROUP BY language ORDER BY cnt DESC
    """)
    for row in cur:
        print(f"  {row['cnt']:>5} reports  {row['language']}")

    # By implement status
    print("\n--- By Implement Status ---")
    cur = conn.execute("""
        SELECT implement_status, COUNT(*) as cnt FROM gitnexus_reports GROUP BY implement_status ORDER BY cnt DESC
    """)
    for row in cur:
        print(f"  {row['cnt']:>5} reports  {row['implement_status']}")

    # Largest files by system
    print("\n--- Largest Files (by parsed size) ---")
    cur = conn.execute("""
        SELECT name, system, file_size FROM gitnexus_reports
        ORDER BY CAST(REPLACE(REPLACE(file_size, ' KB', ''), ' MB', '') AS REAL) *
            CASE WHEN file_size LIKE '%MB%' THEN 1024 WHEN file_size LIKE '%GB%' THEN 1024*1024 ELSE 1 END DESC
        LIMIT 15
    """)
    for row in cur:
        print(f"  {row['file_size']:>12}  {row['system']:20s}  {row['name'][:60]}")

    # Duplicate capability names across systems
    print("\n--- Shared Capability Names (appearing in 2+ systems) ---")
    cur = conn.execute("""
        SELECT name, COUNT(DISTINCT system) as sys_cnt, GROUP_CONCAT(DISTINCT system) as systems
        FROM gitnexus_reports
        WHERE name != ''
        GROUP BY name
        HAVING sys_cnt > 1
        ORDER BY sys_cnt DESC
        LIMIT 20
    """)
    for row in cur:
        print(f"  {row['sys_cnt']} systems  {row['name'][:50]:50s}  [{row['systems']}]")

    conn.close()


def capability_search(system: str | None = None, language: str | None = None) -> None:
    if not Path(DB_PATH).exists():
        print(f"No database found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    where = []
    params = []
    if system:
        where.append("system = ?")
        params.append(system)
    if language:
        where.append("language = ?")
        params.append(language)

    clause = "WHERE " + " AND ".join(where) if where else ""

    print(f"\n=== CAPABILITY SEARCH ===")
    if system:
        print(f"System: {system}")
    if language:
        print(f"Language: {language}")

    cur = conn.execute(f"SELECT COUNT(*) as cnt FROM gitnexus_reports {clause}", params)
    total = cur.fetchone()["cnt"]
    print(f"Matching reports: {total}\n")

    cur = conn.execute(f"""
        SELECT name, capability_summary, file_size, implement_status
        FROM gitnexus_reports {clause}
        ORDER BY name
        LIMIT 50
    """, params)

    for row in cur:
        print(f"[{row['implement_status']}] {row['name'][:60]:60s}  ({row['file_size']})")
        if row['capability_summary']:
            print(f"  {row['capability_summary'][:120]}...")
        print()

    conn.close()


def main() -> int:
    parser = argparse.ArgumentParser(description="Aggregate GitNexus Reports")
    parser.add_argument("--scan", action="store_true", help="Build index from reports")
    parser.add_argument("--report", action="store_true", help="Print aggregate report")
    parser.add_argument("--capability", help="Search capabilities for a system")
    parser.add_argument("--language", help="Filter by language")
    args = parser.parse_args()

    if args.scan:
        build_index()

    if args.report or args.scan:
        print_report()

    if args.capability or args.language:
        capability_search(args.capability, args.language)

    return 0


if __name__ == "__main__":
    sys.exit(main())
