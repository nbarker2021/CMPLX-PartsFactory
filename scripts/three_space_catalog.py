#!/usr/bin/env python3
"""Three-space evidence catalog for PartsFactory, Manny, and OC build.

The catalog separates four jobs that should not be conflated:

1. Filesystem inventory across the three roots.
2. Zip/archive manifesting without extraction.
3. Controlled extraction into PartsFactory-managed staging.
4. GitNexus target planning for bounded graph indexes.

Extraction never writes into Manny or OC build. Zip payloads are staged under
`data/extracted_zips/<space>/<zip-id>/` in the active PartsFactory repo.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sqlite3
import time
import zipfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath


DEFAULT_DB = Path("data/three_space_catalog.sqlite")
DEFAULT_EXTRACT_ROOT = Path("data/extracted_zips")

ROOTS = {
    "partsfactory": Path("D:/PartsFactory"),
    "manny": Path("D:/Manny Unification 2"),
    "ocbuild": Path("D:/OC build"),
}

PRUNE_DIRS = {
    ".git",
    ".gitnexus",
    ".opencode",
    ".pytest_cache",
    "__pycache__",
    "node_modules",
    ".venv",
    "venv",
    "docker-cache",
}

ARCHIVE_EXTS = {".zip"}
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
    ".h",
    ".cpp",
    ".hpp",
    ".cs",
    ".rb",
    ".php",
    ".swift",
    ".kt",
    ".sh",
    ".ps1",
}

DOC_EXTS = {".md", ".txt", ".rst", ".json", ".yaml", ".yml", ".toml", ".sql"}

SCHEMA = """
CREATE TABLE IF NOT EXISTS root (
    space TEXT PRIMARY KEY,
    host_path TEXT NOT NULL,
    container_path TEXT,
    access_mode TEXT NOT NULL,
    last_scanned_at TEXT
);

CREATE TABLE IF NOT EXISTS file (
    file_id INTEGER PRIMARY KEY AUTOINCREMENT,
    space TEXT NOT NULL,
    rel_path TEXT NOT NULL,
    abs_path TEXT NOT NULL,
    basename TEXT NOT NULL,
    extension TEXT,
    size_bytes INTEGER,
    mtime REAL,
    file_kind TEXT,
    is_archive INTEGER DEFAULT 0,
    in_extracted_tree INTEGER DEFAULT 0,
    extracted_from_zip_id INTEGER,
    scan_batch TEXT NOT NULL,
    UNIQUE(space, rel_path)
);

CREATE INDEX IF NOT EXISTS idx_file_space ON file(space);
CREATE INDEX IF NOT EXISTS idx_file_ext ON file(extension);
CREATE INDEX IF NOT EXISTS idx_file_kind ON file(file_kind);
CREATE INDEX IF NOT EXISTS idx_file_basename ON file(basename);
CREATE INDEX IF NOT EXISTS idx_file_archive ON file(is_archive);
CREATE INDEX IF NOT EXISTS idx_file_size ON file(size_bytes);

CREATE TABLE IF NOT EXISTS zip_archive (
    zip_id TEXT PRIMARY KEY,
    space TEXT NOT NULL,
    rel_path TEXT NOT NULL,
    abs_path TEXT NOT NULL,
    basename TEXT NOT NULL,
    size_bytes INTEGER,
    mtime REAL,
    member_count INTEGER,
    total_uncompressed_bytes INTEGER,
    top_entries_json TEXT,
    likely_extracted_dir TEXT,
    extraction_status TEXT DEFAULT 'queued',
    extraction_path TEXT,
    extraction_error TEXT,
    indexed_repo_alias TEXT,
    last_manifested_at TEXT,
    UNIQUE(space, rel_path)
);

CREATE INDEX IF NOT EXISTS idx_zip_space ON zip_archive(space);
CREATE INDEX IF NOT EXISTS idx_zip_status ON zip_archive(extraction_status);
CREATE INDEX IF NOT EXISTS idx_zip_size ON zip_archive(size_bytes);

CREATE TABLE IF NOT EXISTS extraction_file (
    extract_file_id INTEGER PRIMARY KEY AUTOINCREMENT,
    zip_id TEXT NOT NULL,
    rel_path TEXT NOT NULL,
    abs_path TEXT NOT NULL,
    basename TEXT,
    extension TEXT,
    size_bytes INTEGER,
    file_kind TEXT,
    UNIQUE(zip_id, rel_path)
);

CREATE INDEX IF NOT EXISTS idx_extract_zip ON extraction_file(zip_id);
CREATE INDEX IF NOT EXISTS idx_extract_kind ON extraction_file(file_kind);

CREATE TABLE IF NOT EXISTS gitnexus_target (
    alias TEXT PRIMARY KEY,
    source_type TEXT NOT NULL, -- root | imported_system | extracted_zip | evidence_dir
    space TEXT,
    host_path TEXT NOT NULL,
    container_path TEXT,
    status TEXT DEFAULT 'planned',
    file_count INTEGER DEFAULT 0,
    code_file_count INTEGER DEFAULT 0,
    indexed_at TEXT,
    notes TEXT
);

CREATE TABLE IF NOT EXISTS scan_log (
    scan_id INTEGER PRIMARY KEY AUTOINCREMENT,
    action TEXT NOT NULL,
    started_at TEXT NOT NULL,
    finished_at TEXT,
    details_json TEXT
);
"""


@dataclass
class ScanStats:
    files: int = 0
    bytes_seen: int = 0
    archives: int = 0
    code_files: int = 0
    doc_files: int = 0


def utc_now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def normalize_path(path: Path) -> str:
    return str(path).replace("\\", "/")


def classify_file(path: Path) -> str:
    ext = path.suffix.lower()
    if ext in ARCHIVE_EXTS:
        return "archive"
    if ext in CODE_EXTS:
        return "code"
    if ext in DOC_EXTS:
        return "doc"
    if ext in {".sqlite", ".sqlite3", ".db", ".duckdb"}:
        return "database"
    if ext in {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".ico"}:
        return "image"
    if ext in {".pdf", ".docx", ".pptx", ".xlsx"}:
        return "document_blob"
    if ext in {".pt", ".pth", ".onnx", ".bin", ".npy", ".npz"}:
        return "model_or_binary"
    return "other"


def stable_zip_id(space: str, rel_path: str, size: int | None) -> str:
    raw = f"{space}:{rel_path}:{size or 0}".encode("utf-8", errors="replace")
    return hashlib.sha256(raw).hexdigest()[:16]


def connect(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.executescript(SCHEMA)
    return conn


def seed_roots(conn: sqlite3.Connection) -> None:
    rows = [
        ("partsfactory", normalize_path(ROOTS["partsfactory"]), "/workspace/current-partsfactory", "rw"),
        ("manny", normalize_path(ROOTS["manny"]), "/workspace/current-manny-root", "ro-evidence"),
        ("ocbuild", normalize_path(ROOTS["ocbuild"]), "/workspace/current-oc-build", "ro-doctrine"),
    ]
    conn.executemany(
        """
        INSERT INTO root(space, host_path, container_path, access_mode)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(space) DO UPDATE SET
            host_path=excluded.host_path,
            container_path=excluded.container_path,
            access_mode=excluded.access_mode
        """,
        rows,
    )
    conn.commit()


def likely_extracted_dir(zip_path: Path) -> str | None:
    parent = zip_path.parent
    stem = zip_path.stem
    candidates = [
        parent / stem,
        parent / f"{stem}_extracted",
        parent / f"{stem}_unzipped",
        parent / f"extracted_{stem}",
        parent / stem.replace("-", "_"),
        parent / stem.replace(" ", "_"),
    ]
    for candidate in candidates:
        if candidate.is_dir():
            return normalize_path(candidate)
    return None


def manifest_zip(zip_path: Path, max_names: int = 25) -> tuple[int | None, int | None, list[str], str | None]:
    try:
        with zipfile.ZipFile(zip_path, "r") as zf:
            infos = zf.infolist()
            total = sum(i.file_size for i in infos)
            names = [i.filename for i in infos[:max_names]]
            return len(infos), total, names, None
    except Exception as exc:
        return None, None, [], str(exc)[:500]


def scan_space(conn: sqlite3.Connection, space: str, root_path: Path, manifest_archives: bool) -> ScanStats:
    stats = ScanStats()
    batch = utc_now()
    started = utc_now()
    conn.execute(
        "INSERT INTO scan_log(action, started_at, details_json) VALUES (?, ?, ?)",
        ("scan_space", started, json.dumps({"space": space, "root": normalize_path(root_path)})),
    )
    scan_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]

    file_rows: list[tuple] = []
    zip_rows: list[tuple] = []

    def flush() -> None:
        nonlocal file_rows, zip_rows
        if file_rows:
            conn.executemany(
                """
                INSERT INTO file(space, rel_path, abs_path, basename, extension, size_bytes, mtime,
                                 file_kind, is_archive, scan_batch)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(space, rel_path) DO UPDATE SET
                    abs_path=excluded.abs_path,
                    basename=excluded.basename,
                    extension=excluded.extension,
                    size_bytes=excluded.size_bytes,
                    mtime=excluded.mtime,
                    file_kind=excluded.file_kind,
                    is_archive=excluded.is_archive,
                    scan_batch=excluded.scan_batch
                """,
                file_rows,
            )
            file_rows = []
        if zip_rows:
            conn.executemany(
                """
                INSERT INTO zip_archive(zip_id, space, rel_path, abs_path, basename, size_bytes, mtime,
                                        member_count, total_uncompressed_bytes, top_entries_json,
                                        likely_extracted_dir, extraction_status, last_manifested_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(space, rel_path) DO UPDATE SET
                    abs_path=excluded.abs_path,
                    basename=excluded.basename,
                    size_bytes=excluded.size_bytes,
                    mtime=excluded.mtime,
                    member_count=excluded.member_count,
                    total_uncompressed_bytes=excluded.total_uncompressed_bytes,
                    top_entries_json=excluded.top_entries_json,
                    likely_extracted_dir=excluded.likely_extracted_dir,
                    last_manifested_at=excluded.last_manifested_at
                """,
                zip_rows,
            )
            zip_rows = []
        conn.commit()

    for dirpath, dirnames, filenames in os.walk(root_path, topdown=True):
        dirnames[:] = [d for d in dirnames if d not in PRUNE_DIRS]
        for fname in filenames:
            abs_path = Path(dirpath) / fname
            try:
                st = abs_path.stat()
            except (OSError, PermissionError):
                continue
            rel_path = normalize_path(abs_path.relative_to(root_path))
            kind = classify_file(abs_path)
            is_archive = 1 if abs_path.suffix.lower() in ARCHIVE_EXTS else 0
            file_rows.append(
                (
                    space,
                    rel_path,
                    normalize_path(abs_path),
                    fname,
                    abs_path.suffix.lower(),
                    st.st_size,
                    st.st_mtime,
                    kind,
                    is_archive,
                    batch,
                )
            )
            stats.files += 1
            stats.bytes_seen += st.st_size
            if kind == "archive":
                stats.archives += 1
                zip_id = stable_zip_id(space, rel_path, st.st_size)
                if manifest_archives:
                    member_count, total_uncompressed, top_entries, err = manifest_zip(abs_path)
                    extraction_status = "manifest_error" if err else "queued"
                else:
                    member_count, total_uncompressed, top_entries, extraction_status = None, None, [], "unmanifested"
                zip_rows.append(
                    (
                        zip_id,
                        space,
                        rel_path,
                        normalize_path(abs_path),
                        fname,
                        st.st_size,
                        st.st_mtime,
                        member_count,
                        total_uncompressed,
                        json.dumps(top_entries),
                        likely_extracted_dir(abs_path),
                        extraction_status,
                        utc_now(),
                    )
                )
            elif kind == "code":
                stats.code_files += 1
            elif kind == "doc":
                stats.doc_files += 1

            if stats.files % 5000 == 0:
                flush()
            if stats.files % 100000 == 0:
                print(f"  {space}: {stats.files:,} files, {stats.archives:,} zips")
    flush()
    conn.execute("UPDATE root SET last_scanned_at=? WHERE space=?", (utc_now(), space))
    conn.execute(
        "UPDATE scan_log SET finished_at=?, details_json=? WHERE scan_id=?",
        (utc_now(), json.dumps(stats.__dict__), scan_id),
    )
    conn.commit()
    return stats


def safe_member_path(name: str) -> Path | None:
    pure = PurePosixPath(name.replace("\\", "/"))
    if pure.is_absolute() or ".." in pure.parts:
        return None
    parts = [p for p in pure.parts if p not in ("", ".")]
    if not parts:
        return None
    return Path(*parts)


def extract_zip(
    conn: sqlite3.Connection,
    zip_id: str,
    extract_root: Path,
    max_members: int,
    max_uncompressed_mb: int,
) -> bool:
    row = conn.execute("SELECT * FROM zip_archive WHERE zip_id=?", (zip_id,)).fetchone()
    if not row:
        print(f"  missing zip_id {zip_id}")
        return False
    cols = [d[0] for d in conn.execute("SELECT * FROM zip_archive LIMIT 0").description]
    z = dict(zip(cols, row))
    zip_path = Path(z["abs_path"])
    dest = extract_root / z["space"] / zip_id
    max_uncompressed = max_uncompressed_mb * 1024 * 1024

    try:
        with zipfile.ZipFile(zip_path, "r") as archive:
            infos = archive.infolist()
            total = sum(i.file_size for i in infos)
            if len(infos) > max_members:
                raise RuntimeError(f"member limit exceeded: {len(infos)} > {max_members}")
            if total > max_uncompressed:
                raise RuntimeError(f"uncompressed limit exceeded: {total} > {max_uncompressed}")

            if dest.exists():
                shutil.rmtree(dest)
            dest.mkdir(parents=True, exist_ok=True)

            extracted_rows = []
            for info in infos:
                if info.is_dir():
                    continue
                member_rel = safe_member_path(info.filename)
                if member_rel is None:
                    continue
                out_path = dest / member_rel
                out_path.parent.mkdir(parents=True, exist_ok=True)
                with archive.open(info, "r") as src, open(out_path, "wb") as out:
                    shutil.copyfileobj(src, out)
                kind = classify_file(out_path)
                extracted_rows.append(
                    (
                        zip_id,
                        normalize_path(member_rel),
                        normalize_path(out_path),
                        out_path.name,
                        out_path.suffix.lower(),
                        info.file_size,
                        kind,
                    )
                )

        conn.executemany(
            """
            INSERT INTO extraction_file(zip_id, rel_path, abs_path, basename, extension, size_bytes, file_kind)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(zip_id, rel_path) DO UPDATE SET
                abs_path=excluded.abs_path,
                basename=excluded.basename,
                extension=excluded.extension,
                size_bytes=excluded.size_bytes,
                file_kind=excluded.file_kind
            """,
            extracted_rows,
        )
        code_count = sum(1 for r in extracted_rows if r[-1] == "code")
        alias = "zip-" + zip_id
        conn.execute(
            """
            INSERT INTO gitnexus_target(alias, source_type, space, host_path, container_path,
                                        status, file_count, code_file_count, notes)
            VALUES (?, 'extracted_zip', ?, ?, ?, 'planned', ?, ?, ?)
            ON CONFLICT(alias) DO UPDATE SET
                host_path=excluded.host_path,
                container_path=excluded.container_path,
                file_count=excluded.file_count,
                code_file_count=excluded.code_file_count,
                notes=excluded.notes
            """,
            (
                alias,
                z["space"],
                normalize_path(dest),
                "/workspace/current-partsfactory/CMPLX-PartsFactory/" + normalize_path(dest),
                len(extracted_rows),
                code_count,
                f"extracted from {z['space']}:{z['rel_path']}",
            ),
        )
        conn.execute(
            "UPDATE zip_archive SET extraction_status='extracted', extraction_path=?, extraction_error=NULL, indexed_repo_alias=? WHERE zip_id=?",
            (normalize_path(dest), alias, zip_id),
        )
        conn.commit()
        print(f"  extracted {z['basename']} -> {dest} ({len(extracted_rows)} files, {code_count} code)")
        return True
    except Exception as exc:
        conn.execute(
            "UPDATE zip_archive SET extraction_status='extract_error', extraction_error=? WHERE zip_id=?",
            (str(exc)[:500], zip_id),
        )
        conn.commit()
        print(f"  extract failed {z['basename']}: {exc}")
        return False


def seed_gitnexus_targets(conn: sqlite3.Connection) -> None:
    targets = [
        ("cmplx-partsfactory-root", "root", "partsfactory", ROOTS["partsfactory"] / "CMPLX-PartsFactory", "/workspace/current-partsfactory/CMPLX-PartsFactory", "indexed", "active root"),
        ("partsfactory-cmplxuni", "imported_system", "partsfactory", ROOTS["partsfactory"] / "CMPLX-PartsFactory" / "CMPLXUNI", "/workspace/current-partsfactory/CMPLX-PartsFactory/CMPLXUNI", "planned", "imported variant"),
        ("partsfactory-cmplxmcp", "imported_system", "partsfactory", ROOTS["partsfactory"] / "CMPLX-PartsFactory" / "CMPLXMCP", "/workspace/current-partsfactory/CMPLX-PartsFactory/CMPLXMCP", "planned", "imported variant"),
        ("partsfactory-cmplx-tmn-main", "imported_system", "partsfactory", ROOTS["partsfactory"] / "CMPLX-PartsFactory" / "CMPLX-TMN-main", "/workspace/current-partsfactory/CMPLX-PartsFactory/CMPLX-TMN-main", "planned", "imported variant"),
        ("ocbuild-query-toolkit-sandbox", "evidence_dir", "ocbuild", ROOTS["ocbuild"] / "prototypes" / "query-toolkit-sandbox", "/workspace/current-oc-build/prototypes/query-toolkit-sandbox", "planned", "prior query toolkit work"),
    ]
    for alias, source_type, space, host, container, status, notes in targets:
        if not host.exists():
            continue
        file_count = 0
        code_count = 0
        for root, dirs, files in os.walk(host, topdown=True):
            dirs[:] = [d for d in dirs if d not in PRUNE_DIRS]
            for fname in files:
                file_count += 1
                if classify_file(Path(fname)) == "code":
                    code_count += 1
        conn.execute(
            """
            INSERT INTO gitnexus_target(alias, source_type, space, host_path, container_path, status,
                                        file_count, code_file_count, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(alias) DO UPDATE SET
                source_type=excluded.source_type,
                host_path=excluded.host_path,
                container_path=excluded.container_path,
                file_count=excluded.file_count,
                code_file_count=excluded.code_file_count,
                notes=excluded.notes
            """,
            (alias, source_type, space, normalize_path(host), container, status, file_count, code_count, notes),
        )
    conn.commit()


def print_report(conn: sqlite3.Connection) -> None:
    conn.row_factory = sqlite3.Row
    print("\n=== Three-Space Catalog ===")
    for row in conn.execute(
        """
        SELECT space, COUNT(*) files, SUM(size_bytes) bytes,
               SUM(CASE WHEN file_kind='code' THEN 1 ELSE 0 END) code,
               SUM(CASE WHEN is_archive=1 THEN 1 ELSE 0 END) zips
        FROM file GROUP BY space ORDER BY files DESC
        """
    ):
        print(
            f"  {row['space']:13s} {row['files']:>10,} files "
            f"{row['code'] or 0:>8,} code {row['zips'] or 0:>6,} zips "
            f"{row['bytes'] or 0:>15,} bytes"
        )
    zip_total = conn.execute("SELECT COUNT(*), COALESCE(SUM(size_bytes),0) FROM zip_archive").fetchone()
    print(f"\nZip archives: {zip_total[0]:,} ({zip_total[1]:,} bytes compressed)")
    print("\nZip status:")
    for row in conn.execute("SELECT extraction_status, COUNT(*) c FROM zip_archive GROUP BY extraction_status ORDER BY c DESC"):
        print(f"  {row['extraction_status'] or 'unknown':16s} {row['c']:>8,}")
    print("\nTop zip archives:")
    for row in conn.execute(
        """
        SELECT zip_id, space, basename, size_bytes, member_count, total_uncompressed_bytes, extraction_status
        FROM zip_archive ORDER BY size_bytes DESC LIMIT 15
        """
    ):
        print(
            f"  {row['zip_id']} {row['space']:12s} {row['size_bytes'] or 0:>12,} "
            f"{row['member_count'] or 0:>7,} members {row['extraction_status']:14s} {row['basename'][:52]}"
        )
    print("\nGitNexus targets:")
    for row in conn.execute(
        "SELECT alias, source_type, status, file_count, code_file_count, host_path FROM gitnexus_target ORDER BY status, alias"
    ):
        print(
            f"  {row['status']:10s} {row['alias']:38s} "
            f"{row['file_count']:>7,} files {row['code_file_count']:>6,} code  {row['source_type']}"
        )


def main() -> int:
    parser = argparse.ArgumentParser(description="Three-space evidence catalog")
    parser.add_argument("--db", default=str(DEFAULT_DB))
    parser.add_argument("--scan", choices=["all", *ROOTS.keys()], help="Scan one root or all roots")
    parser.add_argument("--manifest-archives", action="store_true", help="Open zips and record member summaries during scan")
    parser.add_argument("--extract-queued", type=int, default=0, help="Extract N queued zips")
    parser.add_argument("--extract-root", default=str(DEFAULT_EXTRACT_ROOT))
    parser.add_argument("--max-members", type=int, default=5000)
    parser.add_argument("--max-uncompressed-mb", type=int, default=500)
    parser.add_argument("--prefer-space", choices=list(ROOTS.keys()), help="Prefer extracting zips from this space")
    parser.add_argument("--seed-gitnexus-targets", action="store_true")
    parser.add_argument("--report", action="store_true")
    args = parser.parse_args()

    conn = connect(Path(args.db))
    seed_roots(conn)

    if args.scan:
        spaces = list(ROOTS.keys()) if args.scan == "all" else [args.scan]
        for space in spaces:
            root = ROOTS[space]
            print(f"\n=== Scanning {space}: {root} ===")
            stats = scan_space(conn, space, root, manifest_archives=args.manifest_archives)
            print(
                f"  done: {stats.files:,} files, {stats.code_files:,} code, "
                f"{stats.archives:,} zips, {stats.bytes_seen:,} bytes"
            )

    if args.seed_gitnexus_targets:
        seed_gitnexus_targets(conn)

    if args.extract_queued:
        extract_root = Path(args.extract_root)
        where = "WHERE extraction_status='queued'"
        params: tuple = ()
        if args.prefer_space:
            where += " AND space=?"
            params = (args.prefer_space,)
        rows = conn.execute(
            f"""
            SELECT zip_id FROM zip_archive
            {where}
            ORDER BY
                CASE WHEN total_uncompressed_bytes IS NULL THEN 1 ELSE 0 END,
                COALESCE(total_uncompressed_bytes, size_bytes) ASC
            LIMIT ?
            """,
            (*params, args.extract_queued),
        ).fetchall()
        print(f"\n=== Extracting {len(rows)} queued zips ===")
        for (zip_id,) in rows:
            extract_zip(conn, zip_id, extract_root, args.max_members, args.max_uncompressed_mb)

    if args.report or args.scan or args.extract_queued or args.seed_gitnexus_targets:
        print_report(conn)

    conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
