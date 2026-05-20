#!/usr/bin/env python3
"""Run registered CMPLX repos behind one thin command-line wrapper.

The wrapper does not merge files. It keeps each registered repo as its own
checkout, runs commands from that repo root, and reports one combined result.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
from pathlib import Path
from typing import Any


DEFAULT_MANIFEST = Path("repo_kernel/manifest/repos.json")
DEFAULT_EXCLUDES = {"CMPLX-PartsFactory", "scout-demo-service"}


def load_manifest(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def select_modules(
    manifest: dict[str, Any],
    names: list[str] | None,
    count: int | None,
    excludes: set[str],
) -> list[dict[str, Any]]:
    modules = manifest.get("modules", [])
    if names:
        by_name = {module["name"]: module for module in modules}
        missing = [name for name in names if name not in by_name]
        if missing:
            raise SystemExit(f"unknown registered module(s): {', '.join(missing)}")
        return [by_name[name] for name in names]
    candidates = [module for module in modules if module.get("name") not in excludes]
    candidates.sort(key=lambda module: module.get("pushed_at") or module.get("updated_at") or "")
    if count is not None:
        return candidates[:count]
    return candidates


def module_root(module: dict[str, Any]) -> Path:
    return Path(module.get("local_path") or f"repo_kernel/repos/{module['name']}").resolve()


def module_env(module: dict[str, Any], root: Path) -> dict[str, str]:
    env = os.environ.copy()
    env.update({
        "CMPLX_SYSTEM_NAME": module["name"],
        "CMPLX_SYSTEM_ROLE": str(module.get("role") or ""),
        "CMPLX_SYSTEM_ROOT": str(root),
    })
    return env


def run_process(cmd: list[str], cwd: Path, timeout: int, env: dict[str, str] | None = None) -> dict[str, Any]:
    try:
        proc = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
            env=env,
        )
        return {
            "command_line": cmd,
            "return_code": proc.returncode,
            "stdout": proc.stdout.strip(),
            "stderr": proc.stderr.strip(),
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "command_line": cmd,
            "return_code": 124,
            "stdout": (exc.stdout or "") if isinstance(exc.stdout, str) else "",
            "stderr": f"timeout after {timeout}s",
        }


def describe(modules: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "bundle_id": "registered-bundle-" + "+".join(module["name"] for module in modules),
        "policy": "repo roots stay separate; wrapper supplies one CLI/API surface",
        "modules": [
            {
                "name": module["name"],
                "role": module.get("role"),
                "pushed_at": module.get("pushed_at"),
                "pinned_commit": module.get("pinned_commit"),
                "cwd": str(module_root(module)),
                "commands": supported_commands(module),
            }
            for module in modules
        ],
    }


def supported_commands(module: dict[str, Any]) -> list[str]:
    commands = {"status", "probe", "readme", "tree"}
    if module.get("name") == "CMPLXMCP":
        commands.add("native-verify")
    return sorted(commands)


def run_module(module: dict[str, Any], command: str, args: argparse.Namespace) -> dict[str, Any]:
    root = module_root(module)
    base = {
        "module": module["name"],
        "role": module.get("role"),
        "cwd": str(root),
        "command": command,
    }
    if not root.is_dir():
        return {**base, "error": "module checkout is missing"}
    if command == "status":
        return {**base, **run_process(["git", "status", "--short", "--branch"], root, args.timeout)}
    if command == "tree":
        entries = []
        for child in sorted(root.iterdir(), key=lambda item: (not item.is_dir(), item.name.lower()))[:args.limit]:
            if child.name == ".git":
                continue
            entries.append({
                "type": "dir" if child.is_dir() else "file",
                "path": child.name,
                "size": child.stat().st_size if child.is_file() else None,
            })
        return {**base, "entries": entries}
    if command == "readme":
        for name in ("README.md", "readme.md"):
            path = root / name
            if path.is_file():
                text = path.read_text(encoding="utf-8", errors="replace")
                return {**base, "path": name, "content": text[: args.max_bytes], "truncated": len(text) > args.max_bytes}
        return {**base, "error": "no README file found"}
    if command == "probe":
        return {
            **base,
            "exists": True,
            "markers": {
                "git": (root / ".git").exists(),
                "readme": any((root / name).is_file() for name in ("README.md", "readme.md")),
                "python": any((root / name).is_file() for name in ("pyproject.toml", "setup.py", "requirements.txt")),
                "node": (root / "package.json").is_file(),
                "docker": (root / "Dockerfile").is_file(),
            },
            "top_level_entries": len([child for child in root.iterdir() if child.name != ".git"]),
        }
    if command == "native-verify":
        if module.get("name") != "CMPLXMCP":
            return {**base, "supported": False, "reason": "no native verify command registered for this module"}
        native = ["python", "verify-mcp.py"]
        if not args.execute_native:
            return {**base, "supported": True, "dry_run": True, "command_line": native}
        return {
            **base,
            "supported": True,
            "dry_run": False,
            **run_process(native, root, args.timeout, env=module_env(module, root)),
        }
    return {**base, "error": f"unsupported command: {command}"}


def main() -> int:
    parser = argparse.ArgumentParser(prog="registered-systems-bundle")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--count", type=int, default=None, help="Limit selected repos; default includes all registered repos")
    parser.add_argument("--module", action="append", dest="modules")
    parser.add_argument("--include-partsfactory", action="store_true")
    parser.add_argument("--include-scout", action="store_true")
    parser.add_argument("--limit", type=int, default=100)
    parser.add_argument("--max-bytes", type=int, default=20000)
    parser.add_argument("--timeout", type=int, default=45)
    parser.add_argument("--execute-native", action="store_true")
    parser.add_argument("action", choices=["describe", "run"])
    parser.add_argument("command", nargs="?", default="status", choices=["status", "probe", "readme", "tree", "native-verify"])
    args = parser.parse_args()

    excludes = set(DEFAULT_EXCLUDES)
    if args.include_partsfactory:
        excludes.discard("CMPLX-PartsFactory")
    if args.include_scout:
        excludes.discard("scout-demo-service")

    manifest = load_manifest(args.manifest)
    modules = select_modules(manifest, args.modules, args.count, excludes)
    if args.action == "describe":
        print(json.dumps(describe(modules), indent=2))
        return 0

    result = {
        "bundle_id": "registered-bundle-" + "+".join(module["name"] for module in modules),
        "command": args.command,
        "results": [run_module(module, args.command, args) for module in modules],
    }
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
