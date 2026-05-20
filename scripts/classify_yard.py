#!/usr/bin/env python3
"""
Yard Classifier — tag every file as noise, template, real, or canonical.

This is the deep bookkeeping layer. It analyzes the full inventory and applies
heuristic classifiers to separate mechanical duplication from authored code.

Usage:
    python scripts/classify_yard.py --analyze   # run all classifiers
    python scripts/classify_yard.py --report    # print summary
    python scripts/classify_yard.py --real      # list only real files
"""

from __future__ import annotations

import argparse
import re
import sqlite3
import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

NOISE_PATTERNS = [
    ("archive_staging", lambda p: "archive-staging" in p),
    ("uuid_dir", lambda p: bool(re.search(r"[0-9a-f]{8}-[0-9a-f]", p))),
    ("pycache", lambda p: "__pycache__" in p or p.endswith(".pyc")),
    ("node_modules", lambda p: "node_modules" in p),
    ("git_internal", lambda p: ".git/" in p),
    ("zip_extracted", lambda p: False),  # populated from DB field
    ("temp_backup", lambda p: any(x in p for x in [".tmp", ".bak", "~", "copy of", " - copy"])),
]

# Files that are almost always templates when duplicated >20x
TEMPLATE_BASENAMES = {
    "dockerfile", "docker-compose.yml", "docker-compose.yaml",
    "shell_lifecycle.py", "sqlite_store.py", "app.py",
    "__init__.py", "setup.py", "requirements.txt",
    "pyproject.toml", ".gitignore", ".dockerignore",
    "README.md", "LICENSE", "CONTRIBUTING.md",
}

# Files that are content-addressable (images, pdfs, zips) and should be deduped by hash
BLOB_EXTENSIONS = {
    ".zip", ".tar", ".gz", ".bz2", ".7z", ".rar",
    ".pdf", ".docx", ".xlsx", ".pptx",
    ".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico",
    ".mp4", ".avi", ".mov", ".webm",
    ".mp3", ".wav", ".ogg",
}


class YardClassifier:
    def __init__(self, db_path: str = "data/yard_inventory.sqlite"):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self._ensure_schema()

    def _ensure_schema(self) -> None:
        self.conn.executescript("""
        CREATE TABLE IF NOT EXISTS file_classification (
            file_id INTEGER PRIMARY KEY REFERENCES file_inventory(file_id),
            classification TEXT NOT NULL,  -- noise | template | blob | real | canonical
            noise_reason TEXT,             -- which pattern matched
            dupe_group TEXT,               -- basename:size_bytes for exact dupes
            template_type TEXT,            -- which template basename
            review_needed INTEGER DEFAULT 0
        );
        CREATE INDEX IF NOT EXISTS idx_class ON file_classification(classification);
        CREATE INDEX IF NOT EXISTS idx_class_reason ON file_classification(noise_reason);
        CREATE INDEX IF NOT EXISTS idx_class_dupe ON file_classification(dupe_group);
        """)
        self.conn.commit()

    def run_classifiers(self) -> dict:
        """Apply all classifiers and return counts."""
        print("=== Running classifiers ===")
        
        # Pre-compute duplicate groups (basename + size match)
        print("  Computing duplicate groups...")
        cur = self.conn.execute("""
            SELECT basename, size_bytes, COUNT(*) as cnt
            FROM file_inventory
            GROUP BY basename, size_bytes
            HAVING cnt > 1
        """)
        dupe_groups = set()
        dupe_counts = {}
        for row in cur:
            key = f"{row['basename']}:{row['size_bytes']}"
            dupe_groups.add(key)
            dupe_counts[key] = row["cnt"]

        # Pre-compute zip extracted paths
        print("  Loading zip registry...")
        cur = self.conn.execute("SELECT extracted_dir FROM zip_registry WHERE extracted_dir IS NOT NULL")
        zip_dirs = {row["extracted_dir"] for row in cur}

        # Process in batches
        print("  Classifying files...")
        batch = []
        total = 0
        cur = self.conn.execute("SELECT * FROM file_inventory")
        for row in cur:
            total += 1
            fid = row["file_id"]
            path = row["rel_path"]
            basename = row["basename"].lower()
            ext = row["extension"].lower()
            size = row["size_bytes"]
            abs_path = row["abs_path"]

            classification = "real"
            reason = None
            dupe_group = None
            template_type = None

            # 1. Noise patterns
            for pattern_name, checker in NOISE_PATTERNS:
                if checker(path):
                    classification = "noise"
                    reason = pattern_name
                    break

            # Check zip extracted
            if classification == "real":
                for zdir in zip_dirs:
                    if abs_path.startswith(zdir):
                        classification = "noise"
                        reason = "zip_extracted"
                        break

            # 2. Blob detection
            if classification == "real" and ext in BLOB_EXTENSIONS:
                classification = "blob"

            # 3. Template detection
            if classification == "real":
                dupe_key = f"{row['basename']}:{size}"
                if dupe_key in dupe_groups:
                    dupe_group = dupe_key
                    count = dupe_counts[dupe_key]
                    if basename in TEMPLATE_BASENAMES and count > 20:
                        classification = "template"
                        template_type = basename
                    elif count > 100:
                        # Even unknown files with 100+ identical copies are probably templates
                        classification = "template"
                        template_type = basename

            batch.append((fid, classification, reason, dupe_group, template_type, 0))
            if len(batch) >= 5000:
                self._insert_batch(batch)
                batch = []
                if total % 50000 == 0:
                    print(f"    ... {total:,} files classified")

        if batch:
            self._insert_batch(batch)

        self.conn.commit()
        print(f"  Done: {total:,} files classified")
        return self.get_counts()

    def _insert_batch(self, batch: list) -> None:
        self.conn.executemany("""
            INSERT OR REPLACE INTO file_classification 
            (file_id, classification, noise_reason, dupe_group, template_type, review_needed)
            VALUES (?, ?, ?, ?, ?, ?)
        """, batch)

    def get_counts(self) -> dict:
        cur = self.conn.execute("""
            SELECT classification, COUNT(*) as cnt, SUM(f.size_bytes) as total_bytes
            FROM file_classification c
            JOIN file_inventory f ON c.file_id = f.file_id
            GROUP BY classification
        """)
        return {row["classification"]: {"files": row["cnt"], "bytes": row["total_bytes"] or 0} for row in cur}

    def report(self) -> None:
        counts = self.get_counts()
        total_files = sum(v["files"] for v in counts.values())
        total_bytes = sum(v["bytes"] for v in counts.values())

        print("\n=== YARD CLASSIFICATION REPORT ===")
        print(f"Total files: {total_files:,}")
        print(f"Total bytes: {total_bytes:,}")
        print()
        for cls in ["noise", "template", "blob", "real", "canonical"]:
            if cls in counts:
                info = counts[cls]
                pct = info["files"] / total_files * 100
                print(f"  {cls:12s}  {info['files']:>8,} files  ({pct:5.1f}%)  {info['bytes']:>15,} bytes")

        print("\n=== NOISE BREAKDOWN ===")
        cur = self.conn.execute("""
            SELECT noise_reason, COUNT(*) as cnt, SUM(f.size_bytes) as total_bytes
            FROM file_classification c
            JOIN file_inventory f ON c.file_id = f.file_id
            WHERE classification = 'noise'
            GROUP BY noise_reason
            ORDER BY cnt DESC
        """)
        for row in cur:
            print(f"  {row['noise_reason']:20s} {row['cnt']:>6,} files  {row['total_bytes'] or 0:>15,} bytes")

        print("\n=== TOP TEMPLATES ===")
        cur = self.conn.execute("""
            SELECT template_type, COUNT(*) as cnt, SUM(f.size_bytes) as total_bytes
            FROM file_classification c
            JOIN file_inventory f ON c.file_id = f.file_id
            WHERE classification = 'template'
            GROUP BY template_type
            ORDER BY cnt DESC
            LIMIT 15
        """)
        for row in cur:
            print(f"  {row['template_type']:30s} {row['cnt']:>6,} copies  {row['total_bytes'] or 0:>15,} bytes")

    def list_real_files(self, limit: int = 50) -> None:
        cur = self.conn.execute("""
            SELECT f.rel_path, f.basename, f.size_bytes
            FROM file_classification c
            JOIN file_inventory f ON c.file_id = f.file_id
            WHERE c.classification = 'real'
            ORDER BY f.size_bytes DESC
            LIMIT ?
        """, (limit,))
        print(f"\n=== REAL FILES (top {limit} by size) ===")
        for row in cur:
            print(f"  {row['size_bytes']:>10,} bytes  {row['basename']:30s}  {row['rel_path'][:70]}")

    def close(self) -> None:
        self.conn.close()


def main() -> int:
    parser = argparse.ArgumentParser(description="Yard Classifier")
    parser.add_argument("--analyze", action="store_true", help="Run all classifiers")
    parser.add_argument("--report", action="store_true", help="Print classification report")
    parser.add_argument("--real", action="store_true", help="List real files")
    parser.add_argument("--db", default="data/yard_inventory.sqlite")
    args = parser.parse_args()

    clf = YardClassifier(args.db)

    if args.analyze:
        counts = clf.run_classifiers()
        for cls, info in counts.items():
            print(f"  {cls}: {info['files']:,} files")

    if args.report or args.analyze:
        clf.report()

    if args.real:
        clf.list_real_files(limit=50)

    clf.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
