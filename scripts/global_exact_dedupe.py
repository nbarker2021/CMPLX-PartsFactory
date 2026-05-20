#!/usr/bin/env python3
"""Exact duplicate analysis for the three-space catalog.

This script never deletes files. It builds an incremental SHA-256 layer for
files that are plausible duplicate candidates, then reports how many bytes are
truly redundant. It also separates "exact duplicate" from "deletion-ready";
active databases, git internals, and running-system state need a retention policy
even when bytes are identical.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sqlite3
import time
from pathlib import Path


DEFAULT_DB = Path("data/three_space_catalog.sqlite")
ZERO_SHA256 = hashlib.sha256(b"").hexdigest()

SCHEMA = """
CREATE TABLE IF NOT EXISTS file_hash (
    file_id INTEGER PRIMARY KEY,
    space TEXT NOT NULL,
    rel_path TEXT NOT NULL,
    abs_path TEXT NOT NULL,
    size_bytes INTEGER,
    sha256 TEXT,
    hash_status TEXT NOT NULL,
    error TEXT,
    hashed_at TEXT NOT NULL,
    FOREIGN KEY(file_id) REFERENCES file(file_id)
);

CREATE INDEX IF NOT EXISTS idx_file_hash_sha ON file_hash(sha256);
CREATE INDEX IF NOT EXISTS idx_file_hash_size ON file_hash(size_bytes);
CREATE INDEX IF NOT EXISTS idx_file_hash_status ON file_hash(hash_status);

CREATE TABLE IF NOT EXISTS dedupe_run (
    run_id INTEGER PRIMARY KEY AUTOINCREMENT,
    started_at TEXT NOT NULL,
    finished_at TEXT,
    details_json TEXT
);
"""


def utc_now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def connect(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA busy_timeout=30000")
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.executescript(SCHEMA)
    return conn


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def classify_risk(space: str, rel_path: str) -> str:
    rel = rel_path.replace("\\", "/").lower()
    if "/.git/" in rel or rel.startswith(".git/") or rel.endswith("/.git"):
        return "never_delete_git_internal"
    active_markers = [
        "data/postgres/",
        "/postgres/",
        "/pg_wal/",
        "/base/",
        "/neo4j/",
        "/transactions/",
        "dockerdesktopwsl/",
        "docker-cache/",
    ]
    if any(marker in rel for marker in active_markers):
        return "operational_state_review"
    if rel.endswith((".sqlite", ".sqlite3", ".db", ".duckdb", ".wal", ".shm")):
        return "database_review"
    if space in {"manny", "ocbuild"}:
        return "evidence_duplicate_candidate"
    if "datasets from previous review/" in rel or "historical builds/" in rel:
        return "evidence_duplicate_candidate"
    if "corpus_extracted/" in rel or "data/extracted_zips/" in rel:
        return "staged_duplicate_candidate"
    return "working_tree_review"


def fmt_bytes(n: int | None) -> str:
    n = int(n or 0)
    units = ["B", "KB", "MB", "GB", "TB"]
    value = float(n)
    for unit in units:
        if value < 1024 or unit == units[-1]:
            return f"{value:,.2f} {unit}" if unit != "B" else f"{n:,} B"
        value /= 1024
    return f"{n:,} B"


def parse_size(value: str | None) -> int | None:
    if value is None:
        return None
    text = str(value).strip().lower()
    if not text:
        return None
    suffixes = {
        "k": 1024,
        "kb": 1024,
        "m": 1024**2,
        "mb": 1024**2,
        "g": 1024**3,
        "gb": 1024**3,
    }
    for suffix, mult in suffixes.items():
        if text.endswith(suffix):
            return int(float(text[: -len(suffix)].strip()) * mult)
    return int(text)


def candidate_where(spaces: list[str] | None, max_size: int | None) -> tuple[str, list[object]]:
    clauses = ["f.size_bytes IS NOT NULL"]
    params: list[object] = []
    if spaces:
        placeholders = ",".join("?" for _ in spaces)
        clauses.append(f"f.space IN ({placeholders})")
        params.extend(spaces)
    if max_size is not None:
        clauses.append("f.size_bytes <= ?")
        params.append(max_size)
    return " AND ".join(clauses), params


def size_candidate_summary(conn: sqlite3.Connection, spaces: list[str] | None, max_size: int | None) -> dict:
    where, params = candidate_where(spaces, max_size)
    row = conn.execute(
        f"""
        WITH s AS (
            SELECT f.size_bytes, COUNT(*) c
            FROM file f
            WHERE {where}
            GROUP BY f.size_bytes
            HAVING COUNT(*) > 1
        )
        SELECT COUNT(*) size_groups,
               COALESCE(SUM(c),0) candidate_files,
               COALESCE(SUM(c-1),0) removable_if_same_content,
               COALESCE(SUM((c-1)*size_bytes),0) candidate_duplicate_bytes
        FROM s
        """,
        params,
    ).fetchone()
    return {
        "size_groups": row[0],
        "candidate_files": row[1],
        "removable_if_same_content": row[2],
        "candidate_duplicate_bytes": row[3],
    }


def hash_candidates(
    conn: sqlite3.Connection,
    spaces: list[str] | None,
    max_size: int | None,
    limit: int | None,
    include_already_hashed: bool,
) -> dict:
    where, params = candidate_where(spaces, max_size)
    already_clause = "" if include_already_hashed else "AND fh.file_id IS NULL"
    sql = f"""
        WITH dup_sizes AS (
            SELECT f.size_bytes
            FROM file f
            WHERE {where}
            GROUP BY f.size_bytes
            HAVING COUNT(*) > 1
        )
        SELECT f.file_id, f.space, f.rel_path, f.abs_path, f.size_bytes
        FROM file f
        JOIN dup_sizes ds ON ds.size_bytes = f.size_bytes
        LEFT JOIN file_hash fh ON fh.file_id = f.file_id AND fh.hash_status='hashed'
        WHERE 1=1 {already_clause}
        ORDER BY f.size_bytes ASC, f.space, f.rel_path
    """
    if limit is not None:
        sql += " LIMIT ?"
        params = [*params, limit]

    run_details = {
        "spaces": spaces,
        "max_size": max_size,
        "limit": limit,
        "include_already_hashed": include_already_hashed,
    }
    run_id = conn.execute(
        "INSERT INTO dedupe_run(started_at, details_json) VALUES (?, ?)",
        (utc_now(), json.dumps(run_details, sort_keys=True)),
    ).lastrowid
    conn.commit()

    processed = 0
    hashed = 0
    missing = 0
    errors = 0
    started = time.time()
    rows = conn.execute(sql, params)
    for row in rows:
        file_id, space, rel_path, abs_path, size_bytes = row
        path = Path(abs_path)
        status = "hashed"
        digest = None
        error = None
        try:
            if not path.is_file():
                status = "missing"
                missing += 1
            elif int(size_bytes or 0) == 0:
                digest = ZERO_SHA256
                hashed += 1
            else:
                digest = sha256_file(path)
                hashed += 1
        except Exception as exc:
            status = "error"
            error = str(exc)[:500]
            errors += 1

        conn.execute(
            """
            INSERT INTO file_hash(file_id, space, rel_path, abs_path, size_bytes,
                                  sha256, hash_status, error, hashed_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(file_id) DO UPDATE SET
                space=excluded.space,
                rel_path=excluded.rel_path,
                abs_path=excluded.abs_path,
                size_bytes=excluded.size_bytes,
                sha256=excluded.sha256,
                hash_status=excluded.hash_status,
                error=excluded.error,
                hashed_at=excluded.hashed_at
            """,
            (file_id, space, rel_path, abs_path, size_bytes, digest, status, error, utc_now()),
        )
        processed += 1
        if processed % 1000 == 0:
            conn.commit()
            elapsed = max(time.time() - started, 0.001)
            print(
                f"  hashed pass: {processed:,} processed, {hashed:,} hashed, "
                f"{missing:,} missing, {errors:,} errors ({processed/elapsed:,.1f} files/sec)"
            )
    conn.commit()
    result = {
        "processed": processed,
        "hashed": hashed,
        "missing": missing,
        "errors": errors,
        "elapsed_seconds": round(time.time() - started, 3),
    }
    conn.execute(
        "UPDATE dedupe_run SET finished_at=?, details_json=? WHERE run_id=?",
        (utc_now(), json.dumps({**run_details, **result}, sort_keys=True), run_id),
    )
    conn.commit()
    return result


def report(conn: sqlite3.Connection) -> None:
    conn.row_factory = sqlite3.Row
    print("\n=== Exact Duplicate Hash Coverage ===")
    row = conn.execute(
        """
        SELECT COUNT(*) rows,
               SUM(hash_status='hashed') hashed,
               SUM(hash_status='missing') missing,
               SUM(hash_status='error') errors,
               COALESCE(SUM(CASE WHEN hash_status='hashed' THEN size_bytes ELSE 0 END),0) hashed_bytes
        FROM file_hash
        """
    ).fetchone()
    print(
        f"  file_hash rows: {row['rows'] or 0:,}; hashed: {row['hashed'] or 0:,}; "
        f"missing: {row['missing'] or 0:,}; errors: {row['errors'] or 0:,}; "
        f"hashed bytes: {fmt_bytes(row['hashed_bytes'])}"
    )

    print("\n=== Verified Duplicate Totals ===")
    row = conn.execute(
        """
        WITH g AS (
            SELECT sha256, size_bytes, COUNT(*) copies
            FROM file_hash
            WHERE hash_status='hashed' AND sha256 IS NOT NULL
            GROUP BY sha256, size_bytes
            HAVING COUNT(*) > 1
        )
        SELECT COUNT(*) groups,
               COALESCE(SUM(copies),0) duplicate_files,
               COALESCE(SUM(copies-1),0) removable_exact_copies,
               COALESCE(SUM((copies-1)*size_bytes),0) redundant_bytes
        FROM g
        """
    ).fetchone()
    print(
        f"  groups: {row['groups'] or 0:,}; files in duplicate groups: {row['duplicate_files'] or 0:,}; "
        f"extra copies: {row['removable_exact_copies'] or 0:,}; "
        f"verified redundant bytes: {fmt_bytes(row['redundant_bytes'])}"
    )

    print("\nBy risk class:")
    for row in conn.execute(
        """
        WITH dup AS (
            SELECT sha256, size_bytes
            FROM file_hash
            WHERE hash_status='hashed' AND sha256 IS NOT NULL
            GROUP BY sha256, size_bytes
            HAVING COUNT(*) > 1
        ),
        ranked AS (
            SELECT fh.*,
                   ROW_NUMBER() OVER (
                     PARTITION BY fh.sha256, fh.size_bytes
                     ORDER BY
                       CASE fh.space WHEN 'partsfactory' THEN 0 WHEN 'manny' THEN 1 ELSE 2 END,
                       length(fh.rel_path),
                       fh.rel_path
                   ) rn
            FROM file_hash fh
            JOIN dup d ON d.sha256=fh.sha256 AND d.size_bytes=fh.size_bytes
            WHERE fh.hash_status='hashed'
        )
        SELECT space, COUNT(*) duplicate_instances,
               SUM(CASE WHEN rn>1 THEN 1 ELSE 0 END) extra_copies,
               SUM(CASE WHEN rn>1 THEN size_bytes ELSE 0 END) redundant_bytes
        FROM ranked
        GROUP BY space
        ORDER BY redundant_bytes DESC
        """
    ):
        print(
            f"  {row['space']:13s} duplicate instances {row['duplicate_instances']:>8,}; "
            f"extra {row['extra_copies']:>8,}; redundant {fmt_bytes(row['redundant_bytes'])}"
        )

    print("\nTop verified duplicate groups:")
    for row in conn.execute(
        """
        SELECT sha256, size_bytes, COUNT(*) copies,
               (COUNT(*)-1)*size_bytes redundant_bytes,
               GROUP_CONCAT(space || ':' || rel_path, ' | ') paths
        FROM file_hash
        WHERE hash_status='hashed' AND sha256 IS NOT NULL
        GROUP BY sha256, size_bytes
        HAVING COUNT(*) > 1
        ORDER BY redundant_bytes DESC
        LIMIT 20
        """
    ):
        paths = row["paths"] or ""
        if len(paths) > 220:
            paths = paths[:220] + "..."
        print(
            f"  {row['copies']:>5,} copies | {fmt_bytes(row['size_bytes']):>12s} each | "
            f"{fmt_bytes(row['redundant_bytes']):>12s} redundant | {row['sha256'][:12]} | {paths}"
        )


def main() -> int:
    parser = argparse.ArgumentParser(description="Global exact duplicate analyzer")
    parser.add_argument("--db", default=str(DEFAULT_DB))
    parser.add_argument("--spaces", help="Comma-separated spaces to include, e.g. partsfactory,manny")
    parser.add_argument("--max-size", help="Only hash files up to this size, e.g. 50mb, 2gb")
    parser.add_argument("--limit", type=int, help="Max candidate files to hash this run")
    parser.add_argument("--rehash", action="store_true", help="Rehash files even if already hashed")
    parser.add_argument("--hash-candidates", action="store_true", help="Hash candidate files in duplicate-size groups")
    parser.add_argument("--size-summary", action="store_true", help="Print size-only candidate ceiling")
    parser.add_argument("--report", action="store_true", help="Print verified duplicate report")
    args = parser.parse_args()

    conn = connect(Path(args.db))
    spaces = [s.strip() for s in args.spaces.split(",") if s.strip()] if args.spaces else None
    max_size = parse_size(args.max_size)

    if args.size_summary:
        summary = size_candidate_summary(conn, spaces, max_size)
        print("\n=== Size-Only Duplicate Candidate Ceiling ===")
        print(f"  size groups: {summary['size_groups']:,}")
        print(f"  candidate files: {summary['candidate_files']:,}")
        print(f"  possible extra copies: {summary['removable_if_same_content']:,}")
        print(f"  possible duplicate bytes: {fmt_bytes(summary['candidate_duplicate_bytes'])}")

    if args.hash_candidates:
        result = hash_candidates(conn, spaces, max_size, args.limit, args.rehash)
        print("\n=== Hash Pass Complete ===")
        print(json.dumps(result, indent=2, sort_keys=True))

    if args.report or args.hash_candidates:
        report(conn)

    conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
