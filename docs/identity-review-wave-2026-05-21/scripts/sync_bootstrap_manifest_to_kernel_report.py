#!/usr/bin/env python3
"""W1c: Merge bootstrap_manifest + live repo-kernel reads into one report."""
from __future__ import annotations

import json
import urllib.request
from pathlib import Path

ROOT = Path(r"D:/PartsFactory")
REPO = ROOT / "CMPLX-PartsFactory"
OUT = ROOT / "identity_review/reports/w1c-bootstrap-kernel-sync-2026-05-21.json"
KERNEL = "http://localhost:8786"


def _get(path: str, timeout: float = 35.0) -> dict:
    try:
        with urllib.request.urlopen(f"{KERNEL}{path}", timeout=timeout) as resp:
            return {"ok": True, "data": json.loads(resp.read().decode("utf-8"))}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": str(exc)}


def main() -> int:
    manifest = json.loads((REPO / "catalog/bootstrap_manifest.json").read_text(encoding="utf-8"))
    parts_dir = REPO / "catalog/parts"
    part_summaries = []
    for part_id in manifest.get("parts", []):
        path = parts_dir / f"{part_id}.json"
        if path.exists():
            row = json.loads(path.read_text(encoding="utf-8"))
            part_summaries.append(
                {
                    "part_id": part_id,
                    "ports": row.get("bootstrap_ports", []),
                    "package": row.get("package"),
                    "pluggability": row.get("pluggability"),
                }
            )
    payload = {
        "bootstrap_manifest": manifest,
        "catalog_parts": part_summaries,
        "repo_kernel": {
            "health": _get("/api/health"),
            "global_state": _get("/api/global-state?check_health=1"),
            "workbook": _get("/api/global-tool-workbook?check_health=1"),
            "gitnexus_status": _get("/api/gitnexus/status?include_repos=false"),
            "morphonic_status": _get("/api/morphonic/status"),
        },
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    ok = payload["repo_kernel"]["health"].get("ok", False)
    print(json.dumps({"report": str(OUT), "kernel_ok": ok, "port_count": manifest.get("port_count")}, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
