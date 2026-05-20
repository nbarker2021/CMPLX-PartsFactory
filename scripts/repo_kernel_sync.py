#!/usr/bin/env python3
"""Refresh and clone the nbarker2021 repo-kernel module set.

The script keeps repo identity outside the active PartsFactory git tree:

- `repo_kernel/manifest/repos.json` records GitHub metadata and pinned commits.
- `repo_kernel/repos/<name>` contains clean clones used by Docker services.

It is intentionally non-destructive. Existing clone directories are fetched, not
deleted. Dirty existing clones are recorded and skipped unless `--force-dirty`
is provided.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import time
from pathlib import Path
from typing import Any


DEFAULT_OWNER = "nbarker2021"
DEFAULT_MANIFEST = Path("repo_kernel/manifest/repos.json")
DEFAULT_REPO_ROOT = Path("repo_kernel/repos")

ROLE_HINTS = {
    "CMPLX-PartsFactory": "active_unification_root",
    "CMPLX-Manny": "manny_identity_system",
    "CMPLX-TMN-main": "tmn_primary",
    "CMPLX-TMN1": "tmn_historical_build",
    "CMPLX-1T": "geometric_system_build",
    "CMPLXDevKit": "developer_toolkit",
    "CMPLX": "baseline_core",
    "CMPLX-Monorepo": "historical_monorepo_reference",
    "CMPLXUNI": "unified_system_build",
    "CMPLXMCP": "mcp_layer",
    "CMPLX-Formalization": "mathematical_doctrine",
    "scout-demo-service": "external_service_reference",
}


def utc_now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def run(cmd: list[str], cwd: Path | None = None, timeout: int = 120) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout, check=False)


def run_git(repo: Path, *args: str) -> str:
    proc = run(["git", "-C", str(repo), *args], timeout=60)
    if proc.returncode != 0:
        return ""
    return proc.stdout.strip()


def fetch_github_repos(owner: str) -> list[dict[str, Any]]:
    proc = run(
        [
            "gh",
            "repo",
            "list",
            owner,
            "--limit",
            "300",
            "--json",
            "name,url,isPrivate,isFork,pushedAt,updatedAt,description,defaultBranchRef",
        ],
        timeout=120,
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or "gh repo list failed")
    rows = json.loads(proc.stdout)
    rows.sort(key=lambda r: (r.get("pushedAt") or "", r.get("name") or ""), reverse=True)
    return rows


def module_from_github(row: dict[str, Any], repo_root: Path) -> dict[str, Any]:
    name = row["name"]
    default_branch = ""
    if isinstance(row.get("defaultBranchRef"), dict):
        default_branch = row["defaultBranchRef"].get("name") or ""
    return {
        "name": name,
        "url": row["url"],
        "default_branch": default_branch,
        "private": bool(row.get("isPrivate")),
        "fork": bool(row.get("isFork")),
        "pushed_at": row.get("pushedAt") or "",
        "updated_at": row.get("updatedAt") or "",
        "description": row.get("description") or "",
        "role": ROLE_HINTS.get(name, "repo_module"),
        "local_path": str(repo_root / name).replace("\\", "/"),
    }


def clone_or_fetch(module: dict[str, Any], force_dirty: bool = False) -> dict[str, Any]:
    name = module["name"]
    dest = Path(module["local_path"])
    result: dict[str, Any] = {"name": name, "path": str(dest), "action": "none", "ok": False}
    dest.parent.mkdir(parents=True, exist_ok=True)

    if dest.exists() and not (dest / ".git").exists():
        result.update({"action": "skipped", "error": "destination exists but is not a git repo"})
        return result

    if not dest.exists():
        proc = run(["gh", "repo", "clone", f"{DEFAULT_OWNER}/{name}", str(dest), "--", "--filter=blob:none"], timeout=900)
        result["action"] = "clone"
        if proc.returncode != 0:
            result.update({"error": proc.stderr.strip() or proc.stdout.strip()})
            return result
        run(["git", "-C", str(dest), "config", "core.longpaths", "true"], timeout=30)
    else:
        run(["git", "-C", str(dest), "config", "core.longpaths", "true"], timeout=30)
        dirty = run_git(dest, "status", "--porcelain", "-uno")
        if dirty and not force_dirty:
            result.update({"action": "skipped", "error": "dirty clone; use --force-dirty to fetch anyway"})
            module["dirty_state"] = "dirty"
            return result
        proc = run(["git", "-C", str(dest), "fetch", "--all", "--prune", "--tags"], timeout=900)
        result["action"] = "fetch"
        if proc.returncode != 0:
            result.update({"error": proc.stderr.strip() or proc.stdout.strip()})
            return result

    branch = module.get("default_branch") or run_git(dest, "branch", "--show-current")
    if branch:
        checkout = run(["git", "-C", str(dest), "checkout", branch], timeout=120)
        if checkout.returncode == 0:
            pull = run(["git", "-C", str(dest), "pull", "--ff-only"], timeout=900)
            if pull.returncode != 0:
                result["pull_warning"] = pull.stderr.strip() or pull.stdout.strip()

    module["pinned_commit"] = run_git(dest, "rev-parse", "HEAD")
    module["pinned_commit_short"] = run_git(dest, "rev-parse", "--short", "HEAD")
    module["checked_out_branch"] = run_git(dest, "branch", "--show-current")
    module["dirty_state"] = "dirty" if run_git(dest, "status", "--porcelain", "-uno") else "clean"
    result.update(
        {
            "ok": True,
            "pinned_commit": module.get("pinned_commit"),
            "branch": module.get("checked_out_branch"),
            "dirty_state": module.get("dirty_state"),
        }
    )
    return result


def write_manifest(path: Path, owner: str, repo_root: Path, modules: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "generated_at": utc_now(),
        "owner": owner,
        "repo_root": str(repo_root).replace("\\", "/"),
        "modules": modules,
    }
    path.write_text(json.dumps(payload, indent=2, sort_keys=False) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Refresh repo kernel manifest and clones")
    parser.add_argument("--owner", default=DEFAULT_OWNER)
    parser.add_argument("--manifest", default=str(DEFAULT_MANIFEST))
    parser.add_argument("--repo-root", default=str(DEFAULT_REPO_ROOT))
    parser.add_argument("--manifest-only", action="store_true", help="Refresh manifest metadata only")
    parser.add_argument("--clone", action="store_true", help="Clone or fetch repositories")
    parser.add_argument("--force-dirty", action="store_true", help="Fetch existing dirty clones")
    args = parser.parse_args()

    manifest_path = Path(args.manifest)
    repo_root = Path(args.repo_root)
    rows = fetch_github_repos(args.owner)
    modules = [module_from_github(row, repo_root) for row in rows]

    clone_results: list[dict[str, Any]] = []
    if args.clone:
        for module in modules:
            result = clone_or_fetch(module, force_dirty=args.force_dirty)
            clone_results.append(result)
            status = "ok" if result["ok"] else "skip/fail"
            print(f"{status:9s} {result['action']:8s} {module['name']} {result.get('pinned_commit', '')[:12]} {result.get('error', '')}")

    write_manifest(manifest_path, args.owner, repo_root, modules)
    print(f"Wrote {manifest_path} with {len(modules)} modules")
    if clone_results:
        ok = sum(1 for r in clone_results if r["ok"])
        print(f"Clone/fetch results: {ok}/{len(clone_results)} ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
