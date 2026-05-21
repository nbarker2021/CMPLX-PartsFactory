#!/usr/bin/env python3
"""Emit or merge catalog/parts/*.json from runtime bootstrap registry (W0)."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(r"D:/PartsFactory")
REPO = ROOT / "CMPLX-PartsFactory"
SRC = REPO / "src"
CATALOG_DIR = REPO / "catalog" / "parts"
MANIFEST_PATH = REPO / "catalog" / "bootstrap_manifest.json"


def _load_registry():
    if str(SRC) not in sys.path:
        sys.path.insert(0, str(SRC))
    from runtime.bootstrap_registry import (  # noqa: PLC0415
        bootstrap_port_specs,
        catalog_stub_from_spec,
    )

    return bootstrap_port_specs, catalog_stub_from_spec


def _deep_merge(base: dict[str, Any], overlay: dict[str, Any]) -> dict[str, Any]:
    out = dict(base)
    for key, val in overlay.items():
        if key in out and isinstance(out[key], dict) and isinstance(val, dict):
            out[key] = _deep_merge(out[key], val)
        else:
            out[key] = val
    return out


def emit(*, dry_run: bool = False, check: bool = False) -> int:
    specs_fn, stub_fn = _load_registry()
    specs = specs_fn()
    issues: list[str] = []
    written: list[str] = []

    for spec in specs:
        part_id = spec["part_id"]
        path = CATALOG_DIR / f"{part_id}.json"
        stub = stub_fn(spec)
        if path.exists():
            existing = json.loads(path.read_text(encoding="utf-8"))
            merged = _deep_merge(existing, stub)
        else:
            merged = stub

        if check:
            on_disk = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
            for key in ("bootstrap_ports", "bootstrap_source", "pluggability"):
                if on_disk.get(key) != stub.get(key):
                    issues.append(f"{part_id}: stale or missing {key}")
            continue

        payload = json.dumps(merged, indent=2, ensure_ascii=False) + "\n"
        if dry_run:
            print(f"would write {path.name} ({len(payload)} bytes)")
        else:
            CATALOG_DIR.mkdir(parents=True, exist_ok=True)
            path.write_text(payload, encoding="utf-8")
            written.append(part_id)

    manifest = {
        "version": "2026-05-21-w0",
        "source": "src/runtime/bootstrap_registry.py",
        "port_count": len(specs),
        "parts": [s["part_id"] for s in specs],
        "ports": [s["port"] for s in specs],
    }
    if not check and not dry_run:
        MANIFEST_PATH.write_text(
            json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

    if check:
        if issues:
            for i in issues:
                print(i, file=sys.stderr)
            return 1
        print(f"check ok: {len(specs)} parts")
        return 0

    print(f"emitted {len(written)} catalog parts -> {CATALOG_DIR}")
    if not dry_run:
        print(f"manifest -> {MANIFEST_PATH}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--check", action="store_true", help="Verify bootstrap fields on disk")
    args = parser.parse_args()
    return emit(dry_run=args.dry_run, check=args.check)


if __name__ == "__main__":
    raise SystemExit(main())
