"""
Run Regimes Proofs — Ring 2 substrate / engineering layer regression
====================================================================

Runs regime-scoped verifiers (block tower, extractor, codecs, substrate map)
and writes a regimes proofs report. Separate from Ring 1 prize core in
``run_all_proofs.py``.

Usage:
    python scripts/run_regimes_proofs.py [--quick] [--max-depth N] [--output PATH]

--quick      : reduces max_depth from 4096 to 256 for faster sanity check.
--max-depth N: explicit depth (default 4096).
--output PATH: where to write the JSON report (default proofs_report_regimes.json).

Exit codes:
    0 = all regime proofs pass
    1 = one or more regime proofs failed
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys
import time


def _format(d, keys):
    return {k: d.get(k) for k in keys if k in d}


def run_regimes_proofs(max_depth: int = 4096) -> dict:
    """Run Ring 2 regime proofs and return a structured report."""
    src_path = pathlib.Path(__file__).resolve().parents[1] / "src"
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))

    from lattice_forge.substrate_map import verify_substrate_map
    from lattice_forge.chart_codec import verify_chart_codec
    from lattice_forge.chart_codec_d4 import verify_chart_codec_d4
    from lattice_forge.block_tower import verify_block_tower
    from lattice_forge.rule30_block_extractor import verify_extractor as verify_block_extractor

    report = {
        "submission": "lattice-forge regimes ring-2 v1.0",
        "max_depth_tested": max_depth,
        "proofs": {},
        "overall_status": "pending",
        "honesty": {
            "not_in_ring1": True,
            "depth_only_shortcut": "CONJ",
            "obligation_id": "rule30.prize.depth_only_shortcut",
        },
    }
    failures = []

    print(f"[SUBSTRATE_MAP] Verifying substrate map at depth {max_depth}...")
    t_full = verify_substrate_map(max_depth=max_depth)
    t = _format(t_full, ["status", "max_depth_tested", "checks"])
    report["proofs"]["SUBSTRATE_MAP"] = t
    if t["status"] != "pass":
        failures.append("SUBSTRATE_MAP")
    print(f"   status: {t['status']}")

    print(f"[CHART_CODEC] Encoding shell=2 sub-trajectory as S_3 word at depth {max_depth}...")
    cc = verify_chart_codec(max_depth=max_depth)
    cc_summary = _format(cc, [
        "status", "max_depth", "shell2_length", "word_length",
        "round_trip_mismatches", "element_counts",
    ])
    report["proofs"]["CHART_CODEC"] = cc_summary
    if cc_summary["status"] != "pass":
        failures.append("CHART_CODEC")
    print(f"   shell2_length={cc_summary['shell2_length']}, "
          f"round_trip_mismatches={cc_summary['round_trip_mismatches']}")

    print(f"[CHART_CODEC_D4] Antipodal D_4 decomposition of full chart at depth {max_depth}...")
    cc4 = verify_chart_codec_d4(max_depth=max_depth)
    cc4_summary = _format(cc4, [
        "status", "max_depth", "trajectory_length",
        "round_trip_mismatches", "label_counts", "sheet_counts",
    ])
    report["proofs"]["CHART_CODEC_D4"] = cc4_summary
    if cc4_summary["status"] != "pass":
        failures.append("CHART_CODEC_D4")
    print(f"   round_trip_mismatches={cc4_summary['round_trip_mismatches']}")

    bt_depth = min(max_depth, 4096)
    print(f"[BLOCK_TOWER] Checkpoint store round-trip at depth {bt_depth}...")
    bt = verify_block_tower(max_depth=bt_depth)
    bt_summary = _format(bt, ["status", "max_depth", "sample_count", "mismatch_count"])
    report["proofs"]["BLOCK_TOWER"] = bt_summary
    if bt_summary["status"] != "pass":
        failures.append("BLOCK_TOWER")
    print(f"   mismatch_count={bt_summary['mismatch_count']} / "
          f"{bt_summary['sample_count']}")

    print(f"[BLOCK_EXTRACTOR] Block-addressed extractor at depth {bt_depth}...")
    be = verify_block_extractor(max_depth=bt_depth)
    be_summary = _format(be, [
        "status", "max_depth", "sample_count",
        "individual_mismatch_count", "range_match_rate",
    ])
    report["proofs"]["BLOCK_EXTRACTOR"] = be_summary
    if be_summary["status"] != "pass":
        failures.append("BLOCK_EXTRACTOR")
    print(f"   individual_mismatches={be_summary['individual_mismatch_count']}, "
          f"range_match_rate={be_summary['range_match_rate']}")

    report["failures"] = failures
    report["overall_status"] = "pass" if not failures else "fail"
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--quick", action="store_true",
                        help="Use max_depth=256 instead of 4096")
    parser.add_argument("--max-depth", type=int, default=4096,
                        help="Depth to verify at")
    parser.add_argument("--output", default="proofs_report_regimes.json",
                        help="Output JSON file path")
    args = parser.parse_args()
    max_depth = 256 if args.quick else args.max_depth

    print("=== Lattice-Forge Regimes (Ring 2): Run Proofs ===")
    print(f"Verification window: max_depth = {max_depth}")
    print("Honesty: depth-only shortcut remains CONJ (not proven here)")
    print()
    t_start = time.time()
    report = run_regimes_proofs(max_depth)
    elapsed = time.time() - t_start
    report["elapsed_seconds"] = elapsed

    print()
    print("=== Summary ===")
    print(f"Overall status: {report['overall_status']}")
    print(f"Failures: {len(report['failures'])}")
    if report["failures"]:
        for f in report["failures"]:
            print(f"  - {f}")
    print(f"Elapsed: {elapsed:.1f}s")
    print(f"Report written to: {args.output}")

    out_path = pathlib.Path(args.output)
    out_path.write_text(json.dumps(report, indent=2, default=str))

    sys.exit(0 if report["overall_status"] == "pass" else 1)


if __name__ == "__main__":
    main()
