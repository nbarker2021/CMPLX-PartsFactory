#!/usr/bin/env python3
"""Catalog nested git repositories without walking full evidence payloads.

This is intentionally separate from the file/archive catalog. A folder can be a
real repo, a copied repo snapshot, a submodule, a third-party dependency, or just
archive noise; treating that as metadata avoids letting nested `.git` folders
confuse the broader evidence scan.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sqlite3
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path


DEFAULT_DB = Path("data/three_space_catalog.sqlite")
PRIOR_INVENTORY = Path(
    "D:/Manny Unification 2/Manny Unification 2 Implementation/runtime/modules/git_repo_inventory.json"
)

ROOTS = {
    "partsfactory": Path("D:/PartsFactory"),
    "manny": Path("D:/Manny Unification 2"),
    "ocbuild": Path("D:/OC build"),
}

PRUNE_DIRS = {
    ".git",
    ".gitnexus",
    ".hg",
    ".svn",
    ".opencode",
    ".pytest_cache",
    ".venv",
    "venv",
    "__pycache__",
    "node_modules",
    "dist",
    "build",
    ".next",
    ".cache",
    "docker-cache",
    "data/extracted_zips",
}

DEFAULT_SKIP_TOP = {
    # This top-level Manny region is already known to contain very large nested
    # archives and duplicate repo snapshots. Import the prior inventory first,
    # then scan this region separately only when needed.
    "manny": {"datasets from previous review"},
    "partsfactory": set(),
    "ocbuild": set(),
}

SCHEMA = """
CREATE TABLE IF NOT EXISTS git_repo (
    repo_key TEXT PRIMARY KEY,
    space TEXT,
    rel_path TEXT NOT NULL,
    abs_path TEXT NOT NULL,
    git_dir_path TEXT,
    top_segment TEXT,
    discovered_by TEXT NOT NULL,
    classification TEXT,
    remote_urls_json TEXT,
    remote_owner TEXT,
    remote_repo TEXT,
    matches_github_user INTEGER DEFAULT 0,
    branch TEXT,
    head TEXT,
    dirty_state TEXT,
    file_count_capped INTEGER,
    file_count_cap INTEGER,
    last_commit_iso TEXT,
    last_seen_at TEXT NOT NULL,
    notes TEXT
);

CREATE INDEX IF NOT EXISTS idx_git_repo_space ON git_repo(space);
CREATE INDEX IF NOT EXISTS idx_git_repo_class ON git_repo(classification);
CREATE INDEX IF NOT EXISTS idx_git_repo_remote ON git_repo(remote_owner, remote_repo);
CREATE INDEX IF NOT EXISTS idx_git_repo_top ON git_repo(space, top_segment);

CREATE TABLE IF NOT EXISTS github_repo (
    owner TEXT NOT NULL,
    name TEXT NOT NULL,
    url TEXT,
    is_private INTEGER,
    is_fork INTEGER,
    pushed_at TEXT,
    updated_at TEXT,
    description TEXT,
    last_seen_at TEXT NOT NULL,
    PRIMARY KEY(owner, name)
);
"""


@dataclass
class RepoRecord:
    space: str | None
    rel_path: str
    abs_path: str
    git_dir_path: str | None
    top_segment: str | None
    discovered_by: str
    classification: str
    remote_urls: list[str]
    remote_owner: str | None
    remote_repo: str | None
    matches_github_user: bool
    branch: str
    head: str
    dirty_state: str
    file_count_capped: int | None
    file_count_cap: int | None
    last_commit_iso: str
    notes: str


def utc_now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def normalize_path(path: Path | str) -> str:
    return str(path).replace("\\", "/")


def connect(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA busy_timeout=30000")
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.executescript(SCHEMA)
    return conn


def run_git(repo: Path, *args: str, timeout: int = 10) -> str:
    try:
        proc = subprocess.run(
            ["git", "-C", str(repo), *args],
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except Exception:
        return ""
    if proc.returncode != 0:
        return ""
    return proc.stdout.strip()


def parse_github_remote(url: str) -> tuple[str | None, str | None]:
    cleaned = url.strip()
    patterns = [
        r"github\.com[:/](?P<owner>[^/\s:]+)/(?P<repo>[^/\s]+?)(?:\.git)?$",
        r"https?://github\.com/(?P<owner>[^/\s]+)/(?P<repo>[^/\s]+?)(?:\.git)?$",
    ]
    for pattern in patterns:
        match = re.search(pattern, cleaned, re.IGNORECASE)
        if match:
            return match.group("owner"), match.group("repo")
    return None, None


def top_segment(rel_path: str) -> str:
    rel_norm = rel_path.replace("\\", "/")
    return rel_norm.split("/", 1)[0] if rel_norm else "."


def classify_repo(
    space: str | None,
    rel_path: str,
    remote_owner: str | None,
    github_user: str,
    prior_classification: str | None = None,
) -> str:
    rel_lower = rel_path.replace("\\", "/").lower()
    if prior_classification:
        return prior_classification
    if remote_owner and remote_owner.lower() == github_user.lower():
        return "github_owned"
    if ".gemini/history" in rel_lower or "/.history/" in rel_lower:
        return "archive_noise"
    if "node_modules" in rel_lower or "site-packages" in rel_lower:
        return "third_party"
    if space == "manny":
        if rel_lower.startswith("working prototyping/") or rel_lower.startswith("agent ecosystem/"):
            return "active_toolkit"
        if rel_lower.startswith("historical builds/") or rel_lower.startswith("datasets from previous review/"):
            return "historical_system_repo"
    if space == "partsfactory":
        if "cmplx-partsfactory" in rel_lower:
            return "active_workspace"
        return "imported_or_working_repo"
    if space == "ocbuild":
        return "doctrine_reference_repo"
    return "local_repo"


def make_repo_key(space: str | None, abs_path: str, discovered_by: str) -> str:
    raw = f"{space or 'unknown'}:{normalize_path(abs_path).lower()}:{discovered_by}"
    return hashlib.sha256(raw.encode("utf-8", errors="replace")).hexdigest()[:24]


def repo_metadata(
    repo: Path,
    space: str | None,
    rel_path: str,
    discovered_by: str,
    github_user: str,
    prior_classification: str | None = None,
    prior_file_count: int | None = None,
    prior_file_cap: int | None = None,
    prior_notes: str = "",
) -> RepoRecord:
    remote_lines = run_git(repo, "remote", "-v").splitlines()
    remote_urls = sorted({line.split()[1] for line in remote_lines if len(line.split()) >= 2})
    remote_owner = None
    remote_repo = None
    for url in remote_urls:
        owner, name = parse_github_remote(url)
        if owner and name:
            remote_owner = owner
            remote_repo = name
            break

    branch = run_git(repo, "branch", "--show-current")
    head = run_git(repo, "rev-parse", "--short", "HEAD")
    dirty = "unknown"
    status = run_git(repo, "status", "--porcelain", "-uno", timeout=5)
    if status == "":
        dirty = "clean_or_unavailable"
    elif status:
        dirty = "dirty"
    last_commit = run_git(repo, "log", "-1", "--format=%cI")
    classification = classify_repo(space, rel_path, remote_owner, github_user, prior_classification)
    return RepoRecord(
        space=space,
        rel_path=rel_path,
        abs_path=normalize_path(repo),
        git_dir_path=normalize_path(repo / ".git"),
        top_segment=top_segment(rel_path),
        discovered_by=discovered_by,
        classification=classification,
        remote_urls=remote_urls,
        remote_owner=remote_owner,
        remote_repo=remote_repo,
        matches_github_user=bool(remote_owner and remote_owner.lower() == github_user.lower()),
        branch=branch,
        head=head,
        dirty_state=dirty,
        file_count_capped=prior_file_count,
        file_count_cap=prior_file_cap,
        last_commit_iso=last_commit,
        notes=prior_notes,
    )


def upsert_repo(conn: sqlite3.Connection, rec: RepoRecord) -> None:
    key = make_repo_key(rec.space, rec.abs_path, rec.discovered_by)
    conn.execute(
        """
        INSERT INTO git_repo(repo_key, space, rel_path, abs_path, git_dir_path, top_segment,
                             discovered_by, classification, remote_urls_json, remote_owner,
                             remote_repo, matches_github_user, branch, head, dirty_state,
                             file_count_capped, file_count_cap, last_commit_iso, last_seen_at, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(repo_key) DO UPDATE SET
            rel_path=excluded.rel_path,
            abs_path=excluded.abs_path,
            git_dir_path=excluded.git_dir_path,
            top_segment=excluded.top_segment,
            classification=excluded.classification,
            remote_urls_json=excluded.remote_urls_json,
            remote_owner=excluded.remote_owner,
            remote_repo=excluded.remote_repo,
            matches_github_user=excluded.matches_github_user,
            branch=excluded.branch,
            head=excluded.head,
            dirty_state=excluded.dirty_state,
            file_count_capped=excluded.file_count_capped,
            file_count_cap=excluded.file_count_cap,
            last_commit_iso=excluded.last_commit_iso,
            last_seen_at=excluded.last_seen_at,
            notes=excluded.notes
        """,
        (
            key,
            rec.space,
            rec.rel_path,
            rec.abs_path,
            rec.git_dir_path,
            rec.top_segment,
            rec.discovered_by,
            rec.classification,
            json.dumps(rec.remote_urls, sort_keys=True),
            rec.remote_owner,
            rec.remote_repo,
            1 if rec.matches_github_user else 0,
            rec.branch,
            rec.head,
            rec.dirty_state,
            rec.file_count_capped,
            rec.file_count_cap,
            rec.last_commit_iso,
            utc_now(),
            rec.notes,
        ),
    )


def should_prune_dir(name: str) -> bool:
    if name in PRUNE_DIRS:
        return True
    if name.endswith(".egg-info"):
        return True
    return False


def scan_space(
    conn: sqlite3.Connection,
    space: str,
    root: Path,
    github_user: str,
    skip_top: set[str],
    base_root: Path | None = None,
) -> int:
    root = root.resolve()
    base_root = (base_root or root).resolve()
    found = 0
    for current, dirs, _files in os.walk(root, topdown=True):
        current_path = Path(current)
        rel_current = "." if current_path == root else normalize_path(current_path.relative_to(root))
        has_dot_git = ".git" in dirs or (current_path / ".git").is_file()
        if rel_current == ".":
            dirs[:] = [d for d in dirs if d not in skip_top and not should_prune_dir(d)]
        else:
            dirs[:] = [d for d in dirs if not should_prune_dir(d)]

        if not has_dot_git:
            continue

        rel_path = "." if current_path == base_root else normalize_path(current_path.relative_to(base_root))
        rec = repo_metadata(current_path, space, rel_path, "local_scan", github_user)
        upsert_repo(conn, rec)
        found += 1
        # Remove only the git metadata directory. Keep walking children because
        # imported historical trees can contain repo-in-repo copies.
        dirs[:] = [d for d in dirs if d != ".git"]
        if found % 25 == 0:
            conn.commit()
            print(f"  {space}: {found} repos found so far; latest {rel_path}")
    conn.commit()
    return found


def map_prior_path(path: str) -> tuple[str | None, Path | None, str]:
    normalized = path.replace("\\", "/")
    old_root = "C:/Users/borke/Desktop/Manny Unification 2"
    old_impl = "C:/Users/borke/Desktop/Manny Unification 2 Implementation"
    if normalized.startswith(old_root):
        rel = normalized[len(old_root) :].lstrip("/")
        return "manny", ROOTS["manny"] / rel, rel
    if normalized.startswith(old_impl):
        rel = normalized[len(old_impl) :].lstrip("/")
        return "manny", ROOTS["manny"] / "Manny Unification 2 Implementation" / rel, (
            "Manny Unification 2 Implementation/" + rel
        )
    return None, None, normalized


def import_prior_inventory(conn: sqlite3.Connection, inventory: Path, github_user: str) -> int:
    data = json.loads(inventory.read_text(encoding="utf-8-sig"))
    count = 0
    for item in data.get("records", []):
        space, mapped, rel_path = map_prior_path(item.get("repo_path", ""))
        if not mapped:
            continue
        remote_urls = [item["remote"]] if item.get("remote") else []
        remote_owner = None
        remote_repo = None
        for url in remote_urls:
            remote_owner, remote_repo = parse_github_remote(url)
            if remote_owner:
                break
        prior_notes = f"prior inventory generated {data.get('generated_at', '')}; name_hint={item.get('name_hint', '')}"
        rec = RepoRecord(
            space,
            normalize_path(rel_path),
            normalize_path(mapped),
            normalize_path(mapped / ".git"),
            top_segment(normalize_path(rel_path)),
            "prior_gitnexus_inventory",
            item.get("classification") or classify_repo(space, normalize_path(rel_path), remote_owner, github_user),
            remote_urls,
            remote_owner,
            remote_repo,
            bool(remote_owner and remote_owner.lower() == github_user.lower()),
            item.get("branch") or "",
            item.get("head") or "",
            "dirty" if item.get("dirty") else "clean_or_unavailable",
            item.get("file_count_capped"),
            item.get("file_count_cap"),
            "",
            prior_notes,
        )
        upsert_repo(conn, rec)
        count += 1
    conn.commit()
    return count


def fetch_github_repos(owner: str) -> list[dict]:
    proc = subprocess.run(
        [
            "gh",
            "repo",
            "list",
            owner,
            "--limit",
            "300",
            "--json",
            "name,isPrivate,isFork,pushedAt,updatedAt,url,description",
        ],
        check=False,
        capture_output=True,
        text=True,
        timeout=60,
    )
    if proc.returncode != 0:
        print(f"  gh repo list failed: {proc.stderr.strip()}")
        return []
    return json.loads(proc.stdout)


def import_github_repos(conn: sqlite3.Connection, owner: str) -> int:
    rows = fetch_github_repos(owner)
    now = utc_now()
    for row in rows:
        conn.execute(
            """
            INSERT INTO github_repo(owner, name, url, is_private, is_fork, pushed_at,
                                    updated_at, description, last_seen_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(owner, name) DO UPDATE SET
                url=excluded.url,
                is_private=excluded.is_private,
                is_fork=excluded.is_fork,
                pushed_at=excluded.pushed_at,
                updated_at=excluded.updated_at,
                description=excluded.description,
                last_seen_at=excluded.last_seen_at
            """,
            (
                owner,
                row.get("name"),
                row.get("url"),
                1 if row.get("isPrivate") else 0,
                1 if row.get("isFork") else 0,
                row.get("pushedAt"),
                row.get("updatedAt"),
                row.get("description"),
                now,
            ),
        )
    conn.commit()
    return len(rows)


def print_report(conn: sqlite3.Connection) -> None:
    conn.row_factory = sqlite3.Row
    print("\n=== Git Repo Catalog ===")
    for row in conn.execute(
        """
        SELECT space, discovered_by, COUNT(*) count
        FROM git_repo GROUP BY space, discovered_by
        ORDER BY space, discovered_by
        """
    ):
        print(f"  {row['space'] or 'unknown':13s} {row['discovered_by']:24s} {row['count']:>5,}")

    print("\nClassification:")
    for row in conn.execute(
        "SELECT classification, COUNT(*) count FROM git_repo GROUP BY classification ORDER BY count DESC"
    ):
        print(f"  {row['classification'] or 'unknown':28s} {row['count']:>5,}")

    print("\nGitHub-owned local repos:")
    for row in conn.execute(
        """
        SELECT space, rel_path, remote_owner, remote_repo, branch, head, dirty_state
        FROM git_repo
        WHERE matches_github_user=1
        ORDER BY space, rel_path
        LIMIT 80
        """
    ):
        print(
            f"  {row['space'] or 'unknown':12s} {row['remote_owner']}/{row['remote_repo']:<24s} "
            f"{row['branch'] or '-':12s} {row['head'] or '-':10s} {row['dirty_state'] or '-':20s} {row['rel_path']}"
        )

    print("\nGitHub repos for owner:")
    for row in conn.execute(
        "SELECT name, is_private, is_fork, pushed_at, url FROM github_repo ORDER BY pushed_at DESC"
    ):
        privacy = "private" if row["is_private"] else "public"
        fork = " fork" if row["is_fork"] else ""
        print(f"  {row['pushed_at'] or '-':22s} {privacy:7s}{fork:5s} {row['name']:24s} {row['url']}")

    print("\nLocal repos without GitHub remotes:")
    for row in conn.execute(
        """
        SELECT space, classification, rel_path
        FROM git_repo
        WHERE (remote_owner IS NULL OR remote_owner='')
        ORDER BY space, classification, rel_path
        LIMIT 80
        """
    ):
        print(f"  {row['space'] or 'unknown':12s} {row['classification'] or 'unknown':28s} {row['rel_path']}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Catalog nested git repos")
    parser.add_argument("--db", default=str(DEFAULT_DB))
    parser.add_argument("--github-owner", default="nbarker2021")
    parser.add_argument("--import-prior", action="store_true")
    parser.add_argument("--import-github", action="store_true")
    parser.add_argument("--scan", choices=["all", *ROOTS.keys()])
    parser.add_argument("--scan-rel", help="Scan a subdirectory relative to the selected space root")
    parser.add_argument("--include-manny-datasets", action="store_true")
    parser.add_argument("--report", action="store_true")
    args = parser.parse_args()

    conn = connect(Path(args.db))

    if args.import_github:
        count = import_github_repos(conn, args.github_owner)
        print(f"Imported {count} GitHub repos for {args.github_owner}")

    if args.import_prior:
        count = import_prior_inventory(conn, PRIOR_INVENTORY, args.github_owner)
        print(f"Imported {count} prior GitNexus repo records")

    if args.scan:
        if args.scan == "all" and args.scan_rel:
            raise SystemExit("--scan-rel can only be used with a single space")
        spaces = list(ROOTS) if args.scan == "all" else [args.scan]
        for space in spaces:
            skip_top = set(DEFAULT_SKIP_TOP.get(space, set()))
            if space == "manny" and args.include_manny_datasets:
                skip_top.discard("datasets from previous review")
            scan_root = ROOTS[space] / args.scan_rel if args.scan_rel else ROOTS[space]
            print(f"\n=== Scanning git repos in {space}: {scan_root} ===")
            count = scan_space(conn, space, scan_root, args.github_owner, skip_top, ROOTS[space])
            skipped = ", ".join(sorted(skip_top)) or "none"
            print(f"  done: {count} repos found; skipped top-level: {skipped}")

    if args.report or args.import_github or args.import_prior or args.scan:
        print_report(conn)

    conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
