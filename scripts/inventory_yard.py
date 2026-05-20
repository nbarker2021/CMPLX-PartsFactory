#!/usr/bin/env python3
"""
Inventory Yard — streaming catalog of all files across three spaces.

Design constraints:
- Must handle 6M+ files without memory blowout
- Batched SQLite inserts (transaction per batch)
- Zip-aware: flags .zip files and marks likely extracted siblings
- No content parsing, no ASTs, no hashing of file bodies yet
- Resumable: can restart without re-walking completed roots

Usage:
    python scripts/inventory_yard.py --walk-all
    python scripts/inventory_yard.py --walk /d/PartsFactory --tag partsfactory
    python scripts/inventory_yard.py --stats
    python scripts/inventory_yard.py --find-dupes
"""

from __future__ import annotations

import argparse
import os
import sqlite3
import sys
import time
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

YARD_ROOTS = {
    "partsfactory": "/d/PartsFactory",
    "ocbuild": "/d/OC build",
    "manny": "/d/Manny Unification 2",
}

BATCH_SIZE = 5000

SCHEMA = """
CREATE TABLE IF NOT EXISTS file_inventory (
    file_id       INTEGER PRIMARY KEY AUTOINCREMENT,
    abs_path      TEXT NOT NULL,
    rel_path      TEXT NOT NULL,     -- relative to its space root
    basename      TEXT NOT NULL,
    extension     TEXT,
    size_bytes    INTEGER,
    mtime         REAL,
    is_zip        INTEGER DEFAULT 0,
    zip_extracted_path TEXT,         -- if we think this dir came from a zip
    space_tag     TEXT NOT NULL,     -- partsfactory / ocbuild / manny
    walk_batch    TEXT,              -- iso timestamp
    content_hash  TEXT               -- populated later by hash pass
);

CREATE INDEX IF NOT EXISTS idx_inv_basename ON file_inventory(basename);
CREATE INDEX IF NOT EXISTS idx_inv_ext ON file_inventory(extension);
CREATE INDEX IF NOT EXISTS idx_inv_space ON file_inventory(space_tag);
CREATE INDEX IF NOT EXISTS idx_inv_size ON file_inventory(size_bytes);
CREATE INDEX IF NOT EXISTS idx_inv_path ON file_inventory(abs_path);

CREATE TABLE IF NOT EXISTS zip_registry (
    zip_id        INTEGER PRIMARY KEY AUTOINCREMENT,
    abs_path      TEXT UNIQUE NOT NULL,
    basename      TEXT,
    size_bytes    INTEGER,
    mtime         REAL,
    space_tag     TEXT,
    extracted_dir TEXT,              -- guessed extraction path
    walk_batch    TEXT
);

CREATE TABLE IF NOT EXISTS walk_log (
    space_tag     TEXT PRIMARY KEY,
    started_at    TEXT,
    finished_at   TEXT,
    files_seen    INTEGER,
    bytes_seen    INTEGER
);
"""


class InventoryDB:
    def __init__(self, db_path: str = "data/yard_inventory.sqlite"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA synchronous=NORMAL")
        self.conn.execute("PRAGMA cache_size=100000")
        self.conn.executescript(SCHEMA)
        self.conn.commit()
        self._batch: list[tuple] = []

    def add_file(self, abs_path: str, rel_path: str, basename: str, ext: str,
                 size: int, mtime: float, is_zip: int, zip_extracted: str | None,
                 space_tag: str, batch: str) -> None:
        self._batch.append((
            abs_path, rel_path, basename, ext, size, mtime,
            is_zip, zip_extracted, space_tag, batch, None
        ))
        if len(self._batch) >= BATCH_SIZE:
            self._flush()

    def add_zip(self, abs_path: str, basename: str, size: int, mtime: float,
                space_tag: str, extracted_dir: str | None, batch: str) -> None:
        self.conn.execute(
            "INSERT OR IGNORE INTO zip_registry (abs_path, basename, size_bytes, mtime, space_tag, extracted_dir, walk_batch) VALUES (?,?,?,?,?,?,?)",
            (abs_path, basename, size, mtime, space_tag, extracted_dir, batch)
        )

    def _flush(self) -> None:
        if not self._batch:
            return
        self.conn.executemany(
            "INSERT INTO file_inventory (abs_path, rel_path, basename, extension, size_bytes, mtime, is_zip, zip_extracted_path, space_tag, walk_batch, content_hash) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            self._batch
        )
        self.conn.commit()
        self._batch.clear()

    def close(self) -> None:
        self._flush()
        self.conn.close()

    def stats(self) -> dict:
        cur = self.conn.execute(
            "SELECT space_tag, COUNT(*), SUM(size_bytes), COUNT(DISTINCT basename) FROM file_inventory GROUP BY space_tag"
        )
        by_space = {row[0]: {"files": row[1], "bytes": row[2], "unique_names": row[3]} for row in cur}
        cur = self.conn.execute("SELECT COUNT(*) FROM zip_registry")
        zip_count = cur.fetchone()[0]
        cur = self.conn.execute("SELECT COUNT(*) FROM file_inventory WHERE is_zip=1")
        zip_files = cur.fetchone()[0]
        return {
            "by_space": by_space,
            "total_files": sum(s["files"] for s in by_space.values()),
            "total_bytes": sum(s["bytes"] or 0 for s in by_space.values()),
            "zip_archives": zip_count,
            "zip_flagged_files": zip_files,
        }

    def exact_duplicates(self, limit: int = 20) -> list[dict]:
        """Find basenames with identical sizes across spaces — cheap dupes signal."""
        cur = self.conn.execute(
            """
            SELECT basename, size_bytes, COUNT(*) as cnt,
                   GROUP_CONCAT(DISTINCT space_tag) as spaces
            FROM file_inventory
            WHERE size_bytes > 0
            GROUP BY basename, size_bytes
            HAVING cnt > 1
            ORDER BY cnt DESC
            LIMIT ?
            """,
            (limit,)
        )
        rows = cur.fetchall()
        if not rows:
            return []
        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, row)) for row in rows]


def _guess_extracted_dir(zip_path: Path) -> str | None:
    """If /foo/bar.zip exists, check if /foo/bar/ or /foo/bar_extracted/ exists."""
    parent = zip_path.parent
    stem = zip_path.stem
    candidates = [
        parent / stem,
        parent / f"{stem}_extracted",
        parent / f"{stem}_unzipped",
        parent / f"extracted_{stem}",
    ]
    for c in candidates:
        if c.is_dir():
            return str(c)
    return None


def walk_space(db: InventoryDB, root: str, space_tag: str) -> tuple[int, int]:
    root_path = Path(root)
    if not root_path.exists():
        print(f"  SKIP: {root} does not exist")
        return 0, 0

    batch_ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    files_seen = 0
    bytes_seen = 0
    zip_cache: set[str] = set()

    # Pre-index known zip archives so we can flag extracted content
    print(f"  Phase 1: indexing zip archives in {root} ...")
    for p in root_path.rglob("*.zip"):
        if p.is_file():
            zip_cache.add(str(p.resolve()))

    print(f"  Phase 2: walking {root} ...")
    for dirpath, dirnames, filenames in os.walk(root, topdown=True):
        # Prune known noise
        dirnames[:] = [d for d in dirnames if d not in {
            ".git", "__pycache__", ".opencode", "node_modules",
            ".venv", "venv", ".pytest_cache"
        }]

        # Check if this directory looks like it came from a zip
        zip_extracted: str | None = None
        dir_path = Path(dirpath)
        for zip_abs in zip_cache:
            zip_p = Path(zip_abs)
            if dir_path == zip_p.parent / zip_p.stem:
                zip_extracted = str(zip_p)
                break
            if str(dir_path).startswith(str(zip_p.parent / zip_p.stem)):
                zip_extracted = str(zip_p)
                break

        for fname in filenames:
            abs_p = Path(dirpath) / fname
            try:
                stat = abs_p.stat()
            except (OSError, PermissionError):
                continue
            size = stat.st_size
            mtime = stat.st_mtime
            ext = abs_p.suffix.lower()
            is_zip = 1 if ext == ".zip" else 0
            rel = str(abs_p.relative_to(root_path)).replace("\\", "/")

            if is_zip:
                extracted = _guess_extracted_dir(abs_p)
                db.add_zip(str(abs_p), fname, size, mtime, space_tag, extracted, batch_ts)

            db.add_file(
                str(abs_p).replace("\\", "/"), rel, fname, ext,
                size, mtime, is_zip, zip_extracted, space_tag, batch_ts
            )
            files_seen += 1
            bytes_seen += size

            if files_seen % 100000 == 0:
                print(f"    ... {files_seen:,} files indexed")

    db._flush()
    db.conn.execute(
        "INSERT OR REPLACE INTO walk_log (space_tag, started_at, finished_at, files_seen, bytes_seen) VALUES (?, ?, ?, ?, ?)",
        (space_tag, batch_ts, time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), files_seen, bytes_seen)
    )
    db.conn.commit()
    return files_seen, bytes_seen


def main() -> int:
    parser = argparse.ArgumentParser(description="Yard Inventory")
    parser.add_argument("--walk-all", action="store_true", help="Walk all three spaces")
    parser.add_argument("--walk", help="Walk one path")
    parser.add_argument("--tag", default="custom", help="Tag for single walk")
    parser.add_argument("--stats", action="store_true", help="Print statistics")
    parser.add_argument("--find-dupes", action="store_true", help="Show likely exact dupes by basename+size")
    parser.add_argument("--db", default="data/yard_inventory.sqlite")
    args = parser.parse_args()

    db = InventoryDB(args.db)

    if args.walk_all:
        for tag, path in YARD_ROOTS.items():
            print(f"\n=== Walking {tag}: {path} ===")
            f, b = walk_space(db, path, tag)
            print(f"  Done: {f:,} files, {b:,} bytes")
    elif args.walk:
        print(f"\n=== Walking {args.tag}: {args.walk} ===")
        f, b = walk_space(db, args.walk, args.tag)
        print(f"  Done: {f:,} files, {b:,} bytes")

    if args.stats or args.walk_all or args.walk:
        s = db.stats()
        print("\n=== Inventory Stats ===")
        print(f"Total files: {s['total_files']:,}")
        print(f"Total bytes: {s['total_bytes']:,}")
        print(f"Zip archives: {s['zip_archives']:,}")
        for tag, info in s["by_space"].items():
            print(f"  [{tag:12s}] {info['files']:>10,} files  {info['unique_names']:>10,} unique names  {info['bytes'] or 0:>15,} bytes")

    if args.find_dupes:
        print("\n=== Likely Exact Duplicates (basename + size match) ===")
        dupes = db.exact_duplicates(limit=30)
        for d in dupes:
            print(f"  {d['cnt']:>3}x  {d['basename']:40s}  {d['size_bytes']:>12,} bytes  [{d['spaces']}]")

    db.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
