#!/usr/bin/env python3
"""Validate superpermutation JSON records (exit 1 on missing or bad coverage)."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO / "src") not in sys.path:
    sys.path.insert(0, str(REPO / "src"))

from cmplx.primitives.superperm import load_superperm_record, status_for_n


def validate_n(n: int) -> dict:
    from cmplx.primitives.superperm import coverage_check

    rec = load_superperm_record(n)
    status = status_for_n(n)
    sp = rec.get("superpermutation") or rec.get("superperm")
    ok = status == "validated" and sp and coverage_check(str(sp), n=n)
    result: dict = {
        "n": n,
        "status": status,
        "ok": ok,
        "length": len(str(sp)) if sp else 0,
        "coverage_checksum": rec.get("coverage_checksum"),
    }
    if n == 5 and status == "validated":
        labeled = list(rec.get("labeled_alternates") or [])
        alts = labeled or [{"superpermutation": s} for s in rec.get("alternates") or []]
        alt_ok = []
        for entry in alts:
            text = str(entry.get("superpermutation") or entry)
            passed = coverage_check(text, n=5)
            alt_ok.append(passed)
            if not passed:
                ok = False
        result["alternate_count"] = len(alts)
        result["alternates_ok"] = all(alt_ok) if alt_ok else False
        result["tree_alternate_count"] = sum(
            1 for e in labeled if not e.get("is_palindrome")
        )
        result["has_palindrome"] = any(e.get("is_palindrome") for e in labeled)
        if len(alt_ok) != 8:
            ok = False
        octad_path = Path(__file__).resolve().parents[1] / "data" / "superpermutations" / "octad_n5.json"
        result["octad_n5_present"] = octad_path.is_file()
        if not octad_path.is_file():
            ok = False
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate superpermutation records.")
    parser.add_argument(
        "--require",
        default="4,5",
        help="Comma-separated n values that must be validated (default: 4,5)",
    )
    args = parser.parse_args(argv)
    required = [int(x.strip()) for x in args.require.split(",") if x.strip()]
    results = [validate_n(n) for n in required]
    payload = {"ok": all(r["ok"] for r in results), "results": results}
    print(json.dumps(payload, indent=2))
    return 0 if payload["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
