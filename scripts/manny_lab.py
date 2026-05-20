#!/usr/bin/env python3
"""
Manny Lab Notebook — review one folder at a time.

For each target directory, produces:
- File count, total size, depth
- Zip inventory (count, total size, largest)
- Git presence (nested repos, .git sizes)
- File type breakdown
- Largest individual files
- Flags for review issues (massive files, deep nesting, etc.)

Usage:
    python scripts/manny_lab.py --scan "/d/Manny Unification 2/historical builds"
    python scripts/manny_lab.py --scan "/d/Manny Unification 2/datasets from previous review"
    python scripts/manny_lab.py --list-top
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def analyze_directory(target: str, max_depth: int = 3) -> dict:
    root = Path(target)
    if not root.exists():
        return {"error": f"Path does not exist: {target}"}

    files = 0
    dirs = 0
    total_size = 0
    zips = []
    git_dirs = []
    extensions = {}
    largest_files = []
    massive_files = []  # > 100MB
    deep_dirs = []  # depth > max_depth

    for dirpath, dirnames, filenames in os.walk(root):
        rel = Path(dirpath).relative_to(root)
        depth = len(rel.parts) if str(rel) != "." else 0

        if depth > max_depth:
            deep_dirs.append(str(rel))
            # Don't prune — we want full counts, just flag depth

        for d in dirnames:
            if d == ".git":
                git_path = Path(dirpath) / d
                try:
                    git_size = sum(f.stat().st_size for f in git_path.rglob("*") if f.is_file())
                except Exception:
                    git_size = 0
                git_dirs.append({
                    "rel_path": str((Path(dirpath).relative_to(root) / d)).replace("\\", "/"),
                    "size": git_size,
                })
            dirs += 1

        for fname in filenames:
            files += 1
            abs_p = Path(dirpath) / fname
            try:
                size = abs_p.stat().st_size
            except (OSError, PermissionError):
                continue
            total_size += size
            ext = abs_p.suffix.lower()
            extensions[ext] = extensions.get(ext, {"count": 0, "size": 0})
            extensions[ext]["count"] += 1
            extensions[ext]["size"] += size

            if ext == ".zip":
                zips.append({
                    "rel_path": str((Path(dirpath).relative_to(root) / fname)).replace("\\", "/"),
                    "size": size,
                })

            if size > 100_000_000:
                massive_files.append({
                    "rel_path": str((Path(dirpath).relative_to(root) / fname)).replace("\\", "/"),
                    "size": size,
                })

            largest_files.append({
                "rel_path": str((Path(dirpath).relative_to(root) / fname)).replace("\\", "/"),
                "size": size,
            })

    largest_files.sort(key=lambda x: x["size"], reverse=True)
    zips.sort(key=lambda x: x["size"], reverse=True)
    massive_files.sort(key=lambda x: x["size"], reverse=True)

    return {
        "path": str(root),
        "files": files,
        "dirs": dirs,
        "total_size": total_size,
        "zips": zips,
        "zip_count": len(zips),
        "zip_total_size": sum(z["size"] for z in zips),
        "git_dirs": git_dirs,
        "git_count": len(git_dirs),
        "extensions": extensions,
        "largest_files": largest_files[:20],
        "massive_files": massive_files,
        "deep_dirs": list(set(deep_dirs))[:10],
    }


def print_report(report: dict) -> None:
    if "error" in report:
        print(f"ERROR: {report['error']}")
        return

    print(f"\n=== LAB NOTEBOOK: {report['path']} ===")
    print(f"Files:        {report['files']:,}")
    print(f"Directories:  {report['dirs']:,}")
    print(f"Total size:   {report['total_size']:,} bytes ({report['total_size'] / 1e9:.2f} GB)")
    print(f"Zips:         {report['zip_count']:,} ({report['zip_total_size'] / 1e9:.2f} GB)")
    print(f"Git repos:    {report['git_count']:,}")
    if report["massive_files"]:
        print(f"MASSIVE FILES (>100MB): {len(report['massive_files'])}")
    if report["deep_dirs"]:
        print(f"DEEP DIRECTORIES (>3 levels): {len(report['deep_dirs'])} sample paths")

    if report["zips"]:
        print(f"\n--- ZIPS (top 10) ---")
        for z in report["zips"][:10]:
            print(f"  {z['size']:>12,} bytes  {z['rel_path'][:80]}")

    if report["git_dirs"]:
        print(f"\n--- GIT REPOS ---")
        for g in report["git_dirs"]:
            print(f"  {g['size']:>12,} bytes  {g['rel_path'][:80]}")

    if report["massive_files"]:
        print(f"\n--- MASSIVE FILES ---")
        for m in report["massive_files"][:10]:
            print(f"  {m['size']:>12,} bytes  {m['rel_path'][:80]}")

    if report["deep_dirs"]:
        print(f"\n--- DEEP DIRECTORIES (sample) ---")
        for d in report["deep_dirs"][:5]:
            print(f"  {d[:80]}")

    # File type breakdown
    print(f"\n--- FILE TYPES (top 10) ---")
    sorted_exts = sorted(report["extensions"].items(), key=lambda x: x[1]["size"], reverse=True)
    for ext, info in sorted_exts[:10]:
        print(f"  {ext or '(no ext)':10s}  {info['count']:>5,} files  {info['size']:>15,} bytes")

    print()


def main() -> int:
    parser = argparse.ArgumentParser(description="Manny Lab Notebook")
    parser.add_argument("--scan", help="Analyze one directory")
    parser.add_argument("--list-top", action="store_true", help="List top-level dirs of Manny")
    parser.add_argument("--max-depth", type=int, default=3, help="Depth threshold for flagging")
    args = parser.parse_args()

    if args.list_top:
        root = Path("/d/Manny Unification 2")
        if root.exists():
            print("=== Manny Unification 2 — Top Level ===")
            for entry in sorted(root.iterdir(), key=lambda x: x.name.lower()):
                if entry.is_dir():
                    print(f"  [DIR]  {entry.name}")
                else:
                    size = entry.stat().st_size
                    print(f"  [FILE] {entry.name} ({size:,} bytes)")
        return 0

    if args.scan:
        report = analyze_directory(args.scan, max_depth=args.max_depth)
        print_report(report)
        return 0

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
