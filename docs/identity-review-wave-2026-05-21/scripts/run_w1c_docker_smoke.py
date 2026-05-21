#!/usr/bin/env python3
"""W1c/W2: Docker health smoke for manufactured slots + repo-kernel bridge."""
from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

ROOT = Path(r"D:/PartsFactory")
REPO = ROOT / "CMPLX-PartsFactory"
REPORT = ROOT / "identity_review/reports/w1c-docker-smoke-2026-05-21.json"

ENDPOINTS: list[tuple[str, str]] = [
    ("repo-kernel", "http://localhost:8786/api/health"),
    ("receipt", "http://localhost:8010/health"),
    ("speedlight", "http://localhost:8843/health"),
    ("snap", "http://localhost:8823/health"),
    ("tarpit", "http://localhost:8844/health"),
    ("gitnexus-direct", "http://localhost:4747/"),
    ("mdhg", "http://localhost:8825/health"),
    ("mmdb", "http://localhost:8824/health"),
]

KERNEL_READS: list[tuple[str, str]] = [
    ("global-state", "http://localhost:8786/api/global-state?check_health=1"),
    ("global-tool-workbook", "http://localhost:8786/api/global-tool-workbook?check_health=1"),
    ("gitnexus-status", "http://localhost:8786/api/gitnexus/status"),
    ("morphonic-status", "http://localhost:8786/api/morphonic/status"),
]


def _fetch(url: str, timeout: float = 12.0) -> dict[str, Any]:
    try:
        req = urllib.request.Request(url, headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            try:
                sample = json.loads(body)
            except json.JSONDecodeError:
                sample = body[:500]
            return {"ok": True, "status": resp.status, "sample": sample}
    except urllib.error.HTTPError as exc:
        return {"ok": False, "error": f"HTTP {exc.code}", "detail": str(exc)[:300]}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": type(exc).__name__, "detail": str(exc)[:300]}


def main() -> int:
    manifest_path = REPO / "catalog/bootstrap_manifest.json"
    manifest: dict[str, Any] = {}
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    health: dict[str, Any] = {name: _fetch(url) for name, url in ENDPOINTS}
    kernel: dict[str, Any] = {}
    if health.get("repo-kernel", {}).get("ok"):
        kernel = {name: _fetch(url, timeout=8.0) for name, url in KERNEL_READS}

    required = ("repo-kernel", "receipt", "speedlight", "snap", "tarpit", "mdhg", "mmdb")
    all_required_ok = all(health.get(name, {}).get("ok") for name in required)
    payload = {
        "manifest": manifest,
        "health": health,
        "kernel_reads": kernel,
        "all_health_ok": all(v.get("ok") for v in health.values()),
        "all_required_ok": all_required_ok,
        "kernel_live": health.get("repo-kernel", {}).get("ok", False),
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(
        {
            "report": str(REPORT),
            "all_required_ok": payload["all_required_ok"],
            "all_health_ok": payload["all_health_ok"],
            "failed": [k for k, v in health.items() if not v.get("ok")],
        },
        indent=2,
    ))
    return 0 if payload["all_required_ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
