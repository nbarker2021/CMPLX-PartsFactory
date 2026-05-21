#!/usr/bin/env python3
"""Materialize escrow AGRM refactored reference into staging/by-family/agrm (W3)."""
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

ROOT = Path(r"D:/PartsFactory")
REPO = ROOT / "CMPLX-PartsFactory"
TARGET_DIR = REPO / "staging/by-family/agrm/mdhg_hierarchy"
SOURCE = Path(
    r"D:/PartsFactory/work/attractor-assembly/corpus-visible/roots"
    r"/unification-prototypes/_extracted_variants/agrm/AGRM_refactored"
    r"/53e25b8d_AGRM_refactored.py"
)
ALIASES = ("53e25b8d_AGRM_refactored.py", "AGRM_refactored.py")


def main() -> int:
    if not SOURCE.is_file():
        print(f"source missing: {SOURCE}", file=sys.stderr)
        return 1
    TARGET_DIR.mkdir(parents=True, exist_ok=True)
    copied: list[str] = []
    for name in ALIASES:
        dest = TARGET_DIR / name
        shutil.copy2(SOURCE, dest)
        copied.append(str(dest.relative_to(REPO)))
    report = {
        "source": str(SOURCE),
        "target_dir": str(TARGET_DIR),
        "copied": copied,
    }
    out = ROOT / "identity_review/reports/agrm-staging-materialized-2026-05-21.json"
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
