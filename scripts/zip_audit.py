#!/usr/bin/env python3
"""
Zip Audit — map every zip archive to its extracted content, flag orphans.

Logic:
- Find all .zip files
- For each zip, search for likely extracted directories (multiple naming patterns)
- Flag zips with NO extracted dir as "orphan" — these may contain unreviewed content
- Flag directories that look like extractions but have no parent zip as "unmatched extraction"

Usage:
    python scripts/zip_audit.py --scan /d/PartsFactory
    python scripts/zip_audit.py --scan /d/Manny Unification 2 --one-level
    python scripts/zip_audit.py --orphans
"""

from __future__ import annotations

import argparse
import os
import sqlite3
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Patterns that suggest a directory is an extraction of a zip
EXTRACTION_PATTERNS = [
    lambda stem, dirname: dirname == stem,
    lambda stem, dirname: dirname == f"{stem}_extracted",
    lambda stem, dirname: dirname == f"{stem}_unzipped",
    lambda stem, dirname: dirname == f"extracted_{stem}",
    lambda stem, dirname: dirname == f"{stem}_contents",
    lambda stem, dirname: dirname == stem.lower(),
    lambda stem, dirname: dirname == stem.replace(" ", "_"),
    lambda stem, dirname: dirname == stem.replace("-", "_"),
    lambda stem, dirname: dirname.startswith(f"{stem}_") and len(dirname) > len(stem) + 1,
]


def find_extracted_dir(zip_path: Path, search_root: Path, max_depth: int = 3) -> str | None:
    """Search near the zip for a directory that looks like its extraction."""
    stem = zip_path.stem
    parent = zip_path.parent
    
    # First: check siblings
    for entry in parent.iterdir():
        if entry.is_dir():
            for pattern in EXTRACTION_PATTERNS:
                if pattern(stem, entry.name):
                    return str(entry)
    
    # Second: check one level up (sometimes zips are in a subdir and extraction is at parent)
    grandparent = parent.parent
    if grandparent != parent and search_root in grandparent.parents or grandparent == search_root:
        for entry in grandparent.iterdir():
            if entry.is_dir():
                for pattern in EXTRACTION_PATTERNS:
                    if pattern(stem, entry.name):
                        return str(entry)
    
    return None


def quick_zip_list(zip_path: str) -> list[str]:
    """List top-level entries in a zip without full extraction."""
    try:
        with zipfile.ZipFile(zip_path, 'r') as zf:
            return zf.namelist()[:20]
    except Exception:
        return []


class ZipAuditor:
    def __init__(self, db_path: str = "data/yard_inventory.sqlite"):
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self._ensure_schema()
    
    def _ensure_schema(self):
        self.conn.executescript("""
        CREATE TABLE IF NOT EXISTS zip_audit (
            zip_id INTEGER PRIMARY KEY REFERENCES zip_registry(zip_id),
            has_extraction INTEGER DEFAULT 0,
            extracted_dir TEXT,
            extraction_confidence TEXT,  -- direct | sibling | parent | none
            top_contents TEXT,           -- JSON list of first 20 entries
            orphan INTEGER DEFAULT 0,    -- 1 if no extraction found anywhere
            reviewed INTEGER DEFAULT 0
        );
        CREATE INDEX IF NOT EXISTS idx_zip_orphan ON zip_audit(orphan);
        """)
        self.conn.commit()
    
    def audit_space(self, root_path: str, one_level: bool = False) -> dict:
        root = Path(root_path)
        if not root.exists():
            print(f"SKIP: {root} does not exist")
            return {}
        
        print(f"=== Auditing zips in {root} ===")
        
        # Find all zips
        zips = list(root.rglob("*.zip")) if not one_level else [p for p in root.iterdir() if p.suffix == '.zip']
        print(f"Found {len(zips)} zip files")
        
        orphans = 0
        matched = 0
        
        for zip_path in zips:
            rel = str(zip_path.relative_to(root)).replace("\\", "/")
            extracted = find_extracted_dir(zip_path, root)
            
            # Also check if we already know this zip from inventory
            # Normalize path to match inventory storage (backslashes on Windows)
            abs_path_str = str(zip_path)
            cur = self.conn.execute(
                "SELECT zip_id, size_bytes FROM zip_registry WHERE abs_path = ?",
                (abs_path_str,)
            )
            row = cur.fetchone()
            zip_id = row["zip_id"] if row else None
            
            if extracted:
                matched += 1
                confidence = "direct"
            else:
                orphans += 1
                confidence = "none"
            
            contents = quick_zip_list(str(zip_path))
            
            if zip_id:
                self.conn.execute("""
                    INSERT OR REPLACE INTO zip_audit 
                    (zip_id, has_extraction, extracted_dir, extraction_confidence, top_contents, orphan, reviewed)
                    VALUES (?, ?, ?, ?, ?, ?, 1)
                """, (
                    zip_id, 1 if extracted else 0, extracted, confidence, 
                    str(contents), 1 if not extracted else 0
                ))
            
            if len(zips) <= 20 or (len(zips) <= 100 and not extracted):
                status = "[ORPHAN]" if not extracted else "[MATCHED]"
                size = row["size_bytes"] if row else "?"
                print(f"  {status} {rel[:70]} ({size} bytes)")
                if not extracted and contents:
                    print(f"           contents: {contents[:5]}")
        
        self.conn.commit()
        print(f"\nDone: {matched} matched, {orphans} orphans")
        return {"total": len(zips), "matched": matched, "orphans": orphans}
    
    def report_orphans(self, space_tag: str | None = None) -> None:
        where = "WHERE z.space_tag = ?" if space_tag else ""
        params = (space_tag,) if space_tag else ()
        
        cur = self.conn.execute(f"""
            SELECT z.abs_path, z.basename, z.size_bytes, za.top_contents
            FROM zip_registry z
            JOIN zip_audit za ON z.zip_id = za.zip_id
            WHERE za.orphan = 1
            {where}
            ORDER BY z.size_bytes DESC
        """, params)
        
        rows = cur.fetchall()
        print(f"\n=== ORPHAN ZIPS ({len(rows)} total) ===")
        for row in rows:
            contents = eval(row["top_contents"]) if row["top_contents"] else []
            hint = contents[0] if contents else "unknown"
            name = row['basename'][:40]
            print(f"  {row['size_bytes']:>12,} bytes  {name:<40s}  -> {hint[:50]}")
    
    def close(self):
        self.conn.close()


def main() -> int:
    parser = argparse.ArgumentParser(description="Zip Auditor")
    parser.add_argument("--scan", help="Scan a directory for zips")
    parser.add_argument("--one-level", action="store_true", help="Only scan top level (for Manny root)")
    parser.add_argument("--orphans", action="store_true", help="Report orphan zips")
    parser.add_argument("--space-tag", help="Filter by space tag")
    parser.add_argument("--db", default="data/yard_inventory.sqlite")
    args = parser.parse_args()
    
    auditor = ZipAuditor(args.db)
    
    if args.scan:
        auditor.audit_space(args.scan, one_level=args.one_level)
    
    if args.orphans or args.scan:
        auditor.report_orphans(args.space_tag)
    
    auditor.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
