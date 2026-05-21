#!/usr/bin/env python3
"""Emit promotions-bootstrap.jsonl from catalog/bootstrap_manifest (B2)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(r"D:/PartsFactory/CMPLX-PartsFactory")
MANIFEST = REPO / "catalog/bootstrap_manifest.json"
OUT = Path(r"D:/PartsFactory/identity_review/registers/promotions-bootstrap.jsonl")


def main() -> int:
    if not MANIFEST.exists():
        print(f"missing {MANIFEST}", file=sys.stderr)
        return 1
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    lines: list[str] = []
    for part_id in manifest.get("parts", []):
        row = {
            "part_id": part_id,
            "status": "wired",
            "source": "bootstrap_manifest",
            "promotion": "register_all",
        }
        lines.append(json.dumps(row, ensure_ascii=False))
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"rows": len(lines), "path": str(OUT)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
