#!/usr/bin/env python3
"""Canon Scan — discover all Python artifacts and cluster by functional equivalence.

Usage:
    python scripts/canon_scan.py              # full scan of all repos
    python scripts/canon_scan.py --cluster registry.py   # review one basename
    python scripts/canon_scan.py --report registry       # print lineage report
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from canon.scanner import ArtifactScanner
from canon.database import LineageDB
from canon.cluster import ClusterEngine


REPOS = {
    "CMPLX-PartsFactory": ".",
    "CMPLX-1T": "./CMPLX-1T",
    "CMPLX-Manny": "./CMPLX-Manny",
    "CMPLX-TMN-main": "./CMPLX-TMN-main",
    "CMPLXMCP": "./CMPLXMCP",
    "CMPLXUNI": "./CMPLXUNI",
}


def do_full_scan(db: LineageDB) -> None:
    print("=== Full artifact scan ===")
    total = 0
    for tag, path in REPOS.items():
        p = Path(path).resolve()
        if not p.exists():
            print(f"  SKIP {tag}: {p} not found")
            continue
        scanner = ArtifactScanner(str(p), repo_tags={str(p): tag})
        count = 0
        for rec in scanner.scan():
            db.insert_artifact(rec)
            count += 1
            total += 1
        print(f"  {tag}: {count} artifacts")
    db.commit()
    print(f"\nTotal artifacts recorded: {total}")
    print(f"Database: {db.db_path}")


def do_cluster(db: LineageDB, basename: str) -> None:
    print(f"\n=== Cluster review: {basename} ===")
    engine = ClusterEngine(db)
    groups = engine.auto_cluster_basename(basename)
    print(f"Found {len(groups)} structural group(s)\n")
    for i, g in enumerate(groups, 1):
        print(f"  Group {i} — AST hash: {g['ast_hash'][:16]}... ({g['count']} variants)")
        for art in g["artifacts"]:
            repo = art["repo_tag"]
            lines = art["lines"]
            path = art["rel_path"][:80]
            print(f"    [{repo:20s}] {lines:5d}L  {path}")
        print()

    # Auto-register clusters if not already present
    for g in groups:
        if g["ast_hash"] in ("INVALID_SYNTAX", "AST_ERROR"):
            continue
        cluster_id = __import__("hashlib").sha256((basename + g["ast_hash"]).encode()).hexdigest()[:16]
        # Check if exists
        cur = db._conn.execute("SELECT 1 FROM cluster WHERE cluster_id = ?", (cluster_id,))
        if not cur.fetchone():
            aids = [a["artifact_id"] for a in g["artifacts"]]
            engine.register_cluster(basename, g["ast_hash"], aids, notes=f"Auto-clustered from basename scan")
            print(f"  -> Registered cluster {cluster_id} with {len(aids)} members")


def do_report(db: LineageDB, tool_name: str) -> None:
    print(f"\n=== Lineage report: {tool_name} ===")
    report = db.cluster_report(tool_name)
    if "error" in report:
        print(report["error"])
        return
    print(f"Tool: {report['tool_name']}")
    print(f"Status: {report['cluster']['status']}")
    print(f"Total variants: {report['total_variants']}")
    print(f"Total lines if all kept: {report['total_lines_if_kept_all']}")
    print(f"\nVariants:")
    for v in report["variants"]:
        rank = v.get("rank") or "-"
        reason = v.get("reason") or ""
        print(f"  [{rank:>3}] {v['lines']:5d}L  {v['repo_tag']:20s}  {v['rel_path'][:70]}")
        if reason:
            print(f"        reason: {reason}")
    if report["canonical"]:
        c = report["canonical"]
        print(f"\n*** CANONICAL ***")
        print(f"  Path: {c['rel_path']}")
        print(f"  Lines: {c['lines']}")
        print(f"  Content hash: {c['content_hash'][:16]}...")
        print(f"  Derived from {len(__import__('json').loads(c['derived_from']))} variants")


def main() -> int:
    parser = argparse.ArgumentParser(description="CMPLX Canonicalization Scanner")
    parser.add_argument("--cluster", help="Review clusters for a basename (e.g. registry.py)")
    parser.add_argument("--report", help="Print lineage report for a tool name")
    parser.add_argument("--db", default="data/canonicalization.sqlite", help="Path to lineage DB")
    args = parser.parse_args()

    db = LineageDB(args.db)

    if args.report:
        do_report(db, args.report)
    elif args.cluster:
        do_cluster(db, args.cluster)
    else:
        do_full_scan(db)
        print("\nTip: review a specific basename with  python scripts/canon_scan.py --cluster <basename>")

    db.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
