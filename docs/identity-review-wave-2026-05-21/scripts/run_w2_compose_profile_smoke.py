#!/usr/bin/env python3
"""W2: HTTP profile smoke for catalog parts with compose housings."""
from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

ROOT = Path(r"D:/PartsFactory")
REPO = ROOT / "CMPLX-PartsFactory"
REPORT = ROOT / "identity_review/reports/w2-compose-profile-smoke-2026-05-21.json"

# Manufactured HTTP surfaces (port may differ when main stack maps services)
HTTP_CHECKS: list[dict[str, Any]] = [
    {"part_id": "receipt-chain", "base": "http://localhost:8010", "paths": ["/health", "/stats"]},
    {"part_id": "speedlight-worldline", "base": "http://localhost:8843", "paths": ["/health"]},
    {"part_id": "snap-stratification", "base": "http://localhost:8823", "paths": ["/health"]},
    {"part_id": "tarpit-symbolic", "base": "http://localhost:8844", "paths": ["/health", "/stats"]},
    {"part_id": "mdhg-addressing", "base": "http://localhost:8825", "paths": ["/health"]},
    {"part_id": "mmdb-memory", "base": "http://localhost:8824", "paths": ["/health"]},
]


def _get(url: str, timeout: float = 8.0) -> dict[str, Any]:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            try:
                sample = json.loads(body)
            except json.JSONDecodeError:
                sample = body[:400]
            return {"ok": True, "status": resp.status, "sample": sample}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": type(exc).__name__, "detail": str(exc)[:300]}


def _post_json(url: str, payload: dict, timeout: float = 8.0) -> dict[str, Any]:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            return {"ok": True, "status": resp.status, "sample": json.loads(body)}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": type(exc).__name__, "detail": str(exc)[:300]}


def main() -> int:
    results: list[dict[str, Any]] = []
    for check in HTTP_CHECKS:
        row = {"part_id": check["part_id"], "base": check["base"], "paths": {}}
        for path in check["paths"]:
            row["paths"][path] = _get(f"{check['base']}{path}")
        results.append(row)

    receipt_mint = _post_json(
        "http://localhost:8010/mint",
        {"operation": "W2_SMOKE", "detail": {"probe": True}},
    )
    snap_gate = _post_json(
        "http://localhost:8823/gate369",
        {"items": ["w2-a", "w2-b", "w2-c"], "context": "w2-compose-profile"},
    )
    if not snap_gate.get("ok"):
        snap_gate = _post_json(
            "http://localhost:8823/triad",
            {"items": ["w2-a", "w2-b", "w2-c"]},
        )

    payload = {
        "http_checks": results,
        "mutations": {
            "receipt_mint": receipt_mint,
            "snap_gate_or_triad": snap_gate,
        },
        "all_get_ok": all(
            p.get("ok") for r in results for p in r["paths"].values()
        ),
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(
        {
            "report": str(REPORT),
            "all_get_ok": payload["all_get_ok"],
            "receipt_mint_ok": receipt_mint.get("ok"),
            "snap_mutation_ok": snap_gate.get("ok"),
        },
        indent=2,
    ))
    ok = payload["all_get_ok"] and receipt_mint.get("ok") and snap_gate.get("ok")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
