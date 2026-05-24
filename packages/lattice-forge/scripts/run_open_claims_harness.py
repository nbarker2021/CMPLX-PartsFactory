"""
Run open-claims honesty promotion harness and optionally sync registry.jsonl.

Usage:
    python scripts/run_open_claims_harness.py [--quick] [--write-registry] [--output PATH]
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--quick", action="store_true")
    parser.add_argument("--max-depth", type=int, default=256)
    parser.add_argument("--write-registry", action="store_true", help="Apply promotions to claims/registry.jsonl")
    parser.add_argument("--output", default="proofs_report_open_claims.json")
    args = parser.parse_args()

    src = pathlib.Path(__file__).resolve().parents[1] / "src"
    if str(src) not in sys.path:
        sys.path.insert(0, str(src))

    from lattice_forge.honesty_harness import apply_registry_patch, run_open_claims_harness

    depth = 256 if args.quick else args.max_depth
    print("=== Open claims honesty harness ===")
    report = run_open_claims_harness(depth, quick=args.quick)
    print(f"Overall: {report['overall_status']}")
    print(f"Promotions: {len(report['promotions'])}")
    for p in report["promotions"]:
        print(f"  {p['claim_id']}: {p['from']} -> {p['to']} ({p.get('proof_key')})")
    print(f"Still CONJ: {report['still_conj']}")
    print(f"Ledger blocking: {report['ledger']['blocking_obligations']}")

    out = pathlib.Path(args.output)
    out.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    print(f"Report: {out}")

    if args.write_registry:
        n = apply_registry_patch(report["registry_patch"])
        print(f"Registry rows updated: {n}")

    sys.exit(0 if report["overall_status"] == "pass" else 1)


if __name__ == "__main__":
    main()
