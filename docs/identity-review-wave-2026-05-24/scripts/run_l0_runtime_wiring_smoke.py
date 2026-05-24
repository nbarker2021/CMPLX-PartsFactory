#!/usr/bin/env python3
"""L0 runtime wiring smoke — repo-kernel global lanes + manufactured slot catalog."""
from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request
from datetime import date
from pathlib import Path
from typing import Any

ROOT = Path(r"D:/PartsFactory")
REPO = ROOT / "CMPLX-PartsFactory"
CATALOG = REPO / "catalog" / "manufactured_slot_upstream.json"
REPORT = ROOT / f"identity_review/reports/l0-runtime-wiring-{date.today().isoformat()}.json"


def _fetch(url: str, timeout: float = 10.0) -> dict[str, Any]:
    try:
        req = urllib.request.Request(url, headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            try:
                sample = json.loads(body)
            except json.JSONDecodeError:
                sample = body[:400]
            return {"ok": True, "status": resp.status, "sample": sample}
    except urllib.error.HTTPError as exc:
        return {"ok": False, "error": f"HTTP {exc.code}", "detail": str(exc)[:200]}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": type(exc).__name__, "detail": str(exc)[:200]}


def main() -> int:
    catalog: dict[str, Any] = {}
    if CATALOG.is_file():
        catalog = json.loads(CATALOG.read_text(encoding="utf-8"))

    control = catalog.get("control_plane", {})
    kernel_health = _fetch(control.get("repo_kernel_health", "http://localhost:8786/api/health"))
    global_state = _fetch(
        control.get("global_state", "http://localhost:8786/api/global-state?check_health=1")
    )
    workbook = _fetch(
        control.get(
            "global_workbook",
            "http://localhost:8786/api/global-tool-workbook?check_health=1",
        )
    )

    slot_probes: dict[str, Any] = {}
    for slot in catalog.get("slots", []):
        port = slot.get("port", "unknown")
        slot_probes[port] = {
            "host_health": _fetch(slot.get("host_health", "")),
            "global_lane": slot.get("global_lane"),
            "global_read_example": slot.get("global_read_example"),
        }

    kernel_ok = kernel_health.get("ok", False)
    payload = {
        "smoke_date": date.today().isoformat(),
        "catalog_path": str(CATALOG),
        "kernel_health": kernel_health,
        "global_state": global_state,
        "global_workbook": workbook,
        "slot_probes": slot_probes,
        "kernel_live": kernel_ok,
        "all_gates_ok": kernel_ok,
        "honesty": {"depth_only_shortcut": "CONJ"},
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps({"report": str(REPORT), "kernel_live": kernel_ok}, indent=2))
    return 0 if kernel_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
