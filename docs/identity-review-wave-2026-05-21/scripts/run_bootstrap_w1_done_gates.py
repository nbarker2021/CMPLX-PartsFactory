#!/usr/bin/env python3
"""Run catalog done gates for W0/W1 bootstrap-emitted parts (no witness required)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from catalog_done_gate import run_gate  # noqa: E402

REPO = Path(r"D:/PartsFactory/CMPLX-PartsFactory")
MANIFEST = REPO / "catalog" / "bootstrap_manifest.json"

# Parts with heavy witness/gate_artifacts — run dedicated scripts instead.
SKIP = frozenset(
    {
        "receipt-chain",
        "snap-stratification",
        "speedlight-worldline",
        "tarpit-symbolic",
        "mdhg-addressing",
        "mmdb-memory",
        "agrm-routing",
        "morphon-substrate",
    }
)


def main() -> int:
    if not MANIFEST.exists():
        print(f"missing manifest: {MANIFEST}", file=sys.stderr)
        return 1
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    parts = [p for p in manifest.get("parts", []) if p not in SKIP]
    failed: list[str] = []
    for part_id in parts:
        print(f"--- gate: {part_id} ---")
        rc = run_gate(part_id)
        if rc != 0:
            failed.append(part_id)
    summary = {"checked": len(parts), "failed": failed, "intent_met": not failed}
    print(json.dumps(summary, indent=2))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
