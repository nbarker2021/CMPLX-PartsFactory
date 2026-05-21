#!/usr/bin/env python3
"""B3 smoke: integration profile bootstrap against live host stack."""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(r"D:/PartsFactory/CMPLX-PartsFactory")
SRC = REPO / "src"
REPORT = Path(r"D:/PartsFactory/identity_review/reports/b3-integration-profile-smoke-2026-05-21.json")


def main() -> int:
    sys.path.insert(0, str(SRC))
    from cmplx.morphon import MorphonController
    from runtime.integration_profile import register_integration_profile

    MorphonController.reset_for_tests()
    result = register_integration_profile()
    MorphonController.reset_for_tests()

    ok = all(
        str(v).startswith("registered")
        for v in result.get("port_status", {}).values()
    )
    payload = {**result, "all_ports_registered": ok}
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps({"report": str(REPORT), "ok": ok, "remote_ports": result.get("remote_ports", [])}, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
