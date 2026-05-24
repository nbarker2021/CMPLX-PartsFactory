#!/usr/bin/env python3
"""CLI entry: run empirical platform matrix."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from lattice_forge.empirical.runner import run_claim_platform, run_empirical_matrix


def main() -> int:
    p = argparse.ArgumentParser(description="Empirical testing matrix for lattice-forge claims")
    p.add_argument("--quick", action="store_true", help="depth ladder [256] only")
    p.add_argument("--exhaustive", action="store_true", help="depth ladder up to 4096")
    p.add_argument("--claim", help="single claim_id")
    p.add_argument("--output", type=Path, default=ROOT / "empirical_matrix_report.json")
    args = p.parse_args()
    mode = "quick" if args.quick else ("exhaustive" if args.exhaustive else "standard")
    if args.claim:
        row = run_claim_platform(args.claim, exhaustion_mode=mode)
        print(row)
        return 0 if row.get("status") != "fail" else 1
    report = run_empirical_matrix(exhaustion_mode=mode, output=args.output)
    print(f"overall_status={report['overall_status']} failures={report['failures']}")
    return 0 if report["overall_status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
