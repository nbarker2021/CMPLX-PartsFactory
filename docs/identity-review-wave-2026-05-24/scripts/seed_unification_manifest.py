#!/usr/bin/env python3
"""Seed unification_manifest JSONL from HARDENED_INDEX (read-only; no mass promote)."""
from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CMPLX = ROOT / "CMPLX-PartsFactory"
HARDENED = CMPLX / "data" / "HARDENED_INDEX.md"
OUT = ROOT / "identity_review" / "registers" / "unification_manifest.seed.jsonl"


def _parse_hardened_table(text: str) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for line in text.splitlines():
        if not line.startswith("| `"):
            continue
        parts = [p.strip() for p in line.split("|")]
        if len(parts) < 5:
            continue
        family = parts[1].strip("` ")
        name = parts[2].strip("` ")
        file_path = parts[4].strip()
        if family.lower() == "family":
            continue
        rows.append({"family": family, "canonical_name": name, "file_path": file_path})
    return rows


def _replica_count(text: str, family: str, name: str) -> int:
    for line in text.splitlines():
        if f"`{family}`" in line and f"`{name}`" in line:
            parts = [p.strip() for p in line.split("|")]
            if len(parts) >= 4 and parts[3].isdigit():
                return int(parts[3])
    return 0


def main() -> int:
    if not HARDENED.is_file():
        print(f"missing {HARDENED}", file=sys.stderr)
        return 1
    text = HARDENED.read_text(encoding="utf-8")
    parsed = _parse_hardened_table(text)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc).isoformat()
    with OUT.open("w", encoding="utf-8") as fh:
        for row in parsed:
            replicas = _replica_count(text, row["family"], row["canonical_name"])
            canonical_target = row["file_path"].replace("\\", "/")
            record = {
                "version": 1,
                "generated_at": now,
                "family": row["family"],
                "canonical_name": row["canonical_name"],
                "canonical_target": canonical_target,
                "replica_count": replicas,
                "witness_paths": [canonical_target],
                "atomic_file_id": None,
                "gitnexus_repo": None,
                "promote": "hardened",
                "role": row["family"],
                "notes": "Seeded from HARDENED_INDEX.md; Phase C2 intel only — no filesystem promote.",
            }
            fh.write(json.dumps(record) + "\n")
    print(json.dumps({"output": str(OUT), "row_count": len(parsed)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
