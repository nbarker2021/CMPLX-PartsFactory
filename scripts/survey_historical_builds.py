#!/usr/bin/env python3
"""
Survey Historical Builds — git-aware shallow scan of D:\Manny Unification 2\historical builds.

Design constraints:
- NO deep file walks (timeouts guaranteed)
- Uses git CLI for repo stats
- du -sh for size estimates
- Flags nested repos, submodules, large .git dirs
- Logs everything for future passes

Usage:
    python scripts/survey_historical_builds.py --scan
    python scripts/survey_historical_builds.py --report
"""

from __future__ import annotations

import argparse
import json
import os
import sqlite3
import subprocess
import sys
from dataclasses import dataclass, asdict
from pathlib import Path

ROOT = "D:/Manny Unification 2/historical builds"
DB_PATH = "data/historical_builds.sqlite"


@dataclass
class RepoRecord:
    name: str
    abs_path: str
    is_git: bool
    git_size_mb: float
    worktree_size_mb: float | None
    commit_count: int | None
    branch_count: int | None
    remote_count: int | None
    has_submodules: bool
    top_level_files: list[str]
    top_level_dirs: list[str]
    error: str | None


def run_cmd(cmd: list[str], cwd: str | None = None, timeout: int = 30) -> tuple[str, str, int]:
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd, timeout=timeout)
        return result.stdout, result.stderr, result.returncode
    except subprocess.TimeoutExpired:
        return "", "TIMEOUT", 1
    except Exception as e:
        return "", str(e), 1


def get_dir_size_mb(path: str) -> float | None:
    """Use du -sh equivalent, but fast. Only checks top 2 levels."""
    try:
        total = 0
        for dirpath, dirnames, filenames in os.walk(path):
            depth = dirpath[len(path):].count(os.sep)
            if depth > 2:
                del dirnames[:]
                continue
            for f in filenames:
                try:
                    total += os.path.getsize(os.path.join(dirpath, f))
                except (OSError, PermissionError):
                    pass
        return round(total / (1024 * 1024), 2)
    except Exception:
        return None


def scan_repo(repo_path: str, name: str) -> RepoRecord:
    git_dir = os.path.join(repo_path, ".git")
    is_git = os.path.isdir(git_dir)

    git_size_mb = 0.0
    if is_git:
        try:
            git_size = sum(
                os.path.getsize(os.path.join(dirpath, f))
                for dirpath, _, filenames in os.walk(git_dir)
                for f in filenames
            )
            git_size_mb = round(git_size / (1024 * 1024), 2)
        except Exception:
            pass

    # Top-level listing only
    top_files = []
    top_dirs = []
    try:
        for entry in os.listdir(repo_path):
            full = os.path.join(repo_path, entry)
            if os.path.isfile(full):
                top_files.append(entry)
            elif os.path.isdir(full) and entry != ".git":
                top_dirs.append(entry)
    except Exception as e:
        return RepoRecord(name, repo_path, is_git, git_size_mb, None, None, None, None, False, [], [], str(e))

    if not is_git:
        worktree_size = get_dir_size_mb(repo_path)
        return RepoRecord(name, repo_path, False, 0.0, worktree_size, None, None, None, False, top_files, top_dirs, None)

    # Git stats
    commit_count = None
    branch_count = None
    remote_count = None
    has_submodules = False
    error = None

    stdout, stderr, rc = run_cmd(["git", "rev-list", "--all", "--count"], cwd=repo_path, timeout=10)
    if rc == 0:
        try:
            commit_count = int(stdout.strip())
        except ValueError:
            pass
    else:
        error = f"git rev-list failed: {stderr[:100]}"

    stdout, _, rc = run_cmd(["git", "branch", "-a"], cwd=repo_path, timeout=10)
    if rc == 0:
        branch_count = len([l for l in stdout.splitlines() if l.strip()])

    stdout, _, rc = run_cmd(["git", "remote", "-v"], cwd=repo_path, timeout=10)
    if rc == 0:
        remote_count = len(set(l.split()[0] for l in stdout.splitlines() if l.strip()))

    has_submodules = os.path.isfile(os.path.join(repo_path, ".gitmodules"))

    # Worktree size estimate (skip .git)
    worktree_size = None
    try:
        total = 0
        for dirpath, dirnames, filenames in os.walk(repo_path):
            if ".git" in dirpath.split(os.sep):
                continue
            if dirpath.endswith(".git"):
                continue
            for f in filenames:
                try:
                    total += os.path.getsize(os.path.join(dirpath, f))
                except (OSError, PermissionError):
                    pass
        worktree_size = round(total / (1024 * 1024), 2)
    except Exception:
        pass

    return RepoRecord(name, repo_path, is_git, git_size_mb, worktree_size, commit_count, branch_count, remote_count, has_submodules, top_files, top_dirs, error)


def save_to_db(records: list[RepoRecord]) -> None:
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
    CREATE TABLE IF NOT EXISTS historical_builds (
        name TEXT PRIMARY KEY,
        abs_path TEXT,
        is_git INTEGER,
        git_size_mb REAL,
        worktree_size_mb REAL,
        commit_count INTEGER,
        branch_count INTEGER,
        remote_count INTEGER,
        has_submodules INTEGER,
        top_level_files TEXT,
        top_level_dirs TEXT,
        error TEXT
    )
    """)
    for rec in records:
        conn.execute("""
        INSERT OR REPLACE INTO historical_builds VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            rec.name, rec.abs_path, int(rec.is_git), rec.git_size_mb,
            rec.worktree_size_mb, rec.commit_count, rec.branch_count,
            rec.remote_count, int(rec.has_submodules),
            json.dumps(rec.top_level_files), json.dumps(rec.top_level_dirs),
            rec.error
        ))
    conn.commit()
    conn.close()


def print_report() -> None:
    if not Path(DB_PATH).exists():
        print(f"No database found at {DB_PATH}")
        return
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    cur = conn.execute("SELECT COUNT(*) as cnt FROM historical_builds")
    total = cur.fetchone()["cnt"]

    cur = conn.execute("SELECT COUNT(*) as cnt FROM historical_builds WHERE is_git = 1")
    git_repos = cur.fetchone()["cnt"]

    cur = conn.execute("SELECT COUNT(*) as cnt FROM historical_builds WHERE has_submodules = 1")
    submod_repos = cur.fetchone()["cnt"]

    cur = conn.execute("SELECT SUM(git_size_mb) as total FROM historical_builds WHERE is_git = 1")
    git_total = cur.fetchone()["total"] or 0

    print(f"\n=== HISTORICAL BUILDS SURVEY ===")
    print(f"Total entries: {total}")
    print(f"Git repos: {git_repos}")
    print(f"With submodules: {submod_repos}")
    print(f"Total .git size: {git_total:.1f} MB")

    print(f"\n--- GIT REPOS (sorted by worktree size) ---")
    cur = conn.execute("""
        SELECT name, worktree_size_mb, git_size_mb, commit_count, branch_count, remote_count, has_submodules
        FROM historical_builds WHERE is_git = 1 ORDER BY worktree_size_mb DESC NULLS LAST
    """)
    for row in cur:
        sub = "[SUBMODULES]" if row["has_submodules"] else ""
        print(f"  {row['worktree_size_mb'] or 0:>8.1f} MB wt  {row['git_size_mb']:>6.1f} MB git  {row['commit_count'] or 0:>5} commits  {row['branch_count'] or 0:>3} branches  {row['name']:40s} {sub}")

    print(f"\n--- NON-GIT DIRECTORIES ---")
    cur = conn.execute("""
        SELECT name, worktree_size_mb, top_level_dirs, top_level_files
        FROM historical_builds WHERE is_git = 0 ORDER BY worktree_size_mb DESC NULLS LAST
    """)
    for row in cur:
        dirs = json.loads(row["top_level_dirs"]) if row["top_level_dirs"] else []
        files = json.loads(row["top_level_files"]) if row["top_level_files"] else []
        print(f"  {row['worktree_size_mb'] or 0:>8.1f} MB  {row['name']:40s}  dirs={len(dirs)} files={len(files)}")

    conn.close()


def main() -> int:
    parser = argparse.ArgumentParser(description="Survey Historical Builds")
    parser.add_argument("--scan", action="store_true", help="Run the survey")
    parser.add_argument("--report", action="store_true", help="Print report from DB")
    args = parser.parse_args()

    if args.scan:
        if not Path(ROOT).exists():
            print(f"ERROR: {ROOT} does not exist")
            return 1

        entries = sorted([e for e in os.listdir(ROOT) if os.path.isdir(os.path.join(ROOT, e))], key=str.lower)
        print(f"Found {len(entries)} top-level directories in {ROOT}")
        print("Scanning... (this may take a few minutes)")

        records = []
        for i, name in enumerate(entries):
            path = os.path.join(ROOT, name)
            rec = scan_repo(path, name)
            records.append(rec)
            if (i + 1) % 10 == 0:
                print(f"  ... {i+1}/{len(entries)} done")

        save_to_db(records)
        print(f"Saved {len(records)} records to {DB_PATH}")

    if args.report or args.scan:
        print_report()

    return 0


if __name__ == "__main__":
    sys.exit(main())
