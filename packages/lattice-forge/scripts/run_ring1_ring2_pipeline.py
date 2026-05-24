"""
Ring 1 → Ring 2 pipeline (canonical order).
============================================

Ring 1 is **not frozen**: it is the prize-core gate (T1–T8, BONUS, falsify tier-A).
Ring 2 engineering proofs run **after** Ring 1 passes. CONJ obligations remain CONJ
by policy; they are listed in the audit but do not block Ring 2 unless core theorems fail.

Usage:
    python scripts/run_ring1_ring2_pipeline.py [--quick] [--skip-ring2] [--include-monster]
"""

from __future__ import annotations

import argparse
import json
import pathlib
import subprocess
import sys
import time
from typing import Any

_PKG = pathlib.Path(__file__).resolve().parents[1]


def _run(cmd: list[str]) -> int:
    print("$", " ".join(cmd))
    return subprocess.run(cmd, cwd=_PKG, check=False).returncode


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--quick", action="store_true")
    parser.add_argument("--skip-ring2", action="store_true")
    parser.add_argument("--include-monster", action="store_true")
    parser.add_argument("--output", default="proofs_report_ring1_ring2.json")
    args = parser.parse_args()

    quick_flag = ["--quick"] if args.quick else []
    t0 = time.time()
    pipeline: dict[str, Any] = {
        "pipeline": "ring1_then_ring2",
        "quick": args.quick,
        "stages": {},
        "overall_status": "pending",
    }

    print("=== Stage 1: Ring 1 prize-core (run_all_proofs) ===")
    ring1_report = _PKG / "proofs_report.json"
    rc = _run(
        [sys.executable, "scripts/run_all_proofs.py", *quick_flag, "--output", str(ring1_report)]
    )
    pipeline["stages"]["ring1_proofs"] = {"exit_code": rc, "report": str(ring1_report)}

    print()
    print("=== Stage 1b: Ring 1 open audit ===")
    import importlib.util

    audit_mod = importlib.util.spec_from_file_location(
        "ring1_open_audit",
        _PKG / "scripts" / "ring1_open_audit.py",
    )
    assert audit_mod and audit_mod.loader
    mod = importlib.util.module_from_spec(audit_mod)
    audit_mod.loader.exec_module(mod)
    audit = mod.audit_ring1_open(ring1_report)
    pipeline["stages"]["ring1_audit"] = audit
    print(f"Ring 1 gate: {'PASS' if audit['ring1_gate_pass'] else 'FAIL'}")
    print(f"CONJ still open: {len(audit['open_conj_obligations'])}")
    print(f"Harness pass_with_open_gaps: {len(audit['harness_pass_with_open_gaps'])}")

    print()
    print("=== Stage 1b2: Open-claims honesty harness ===")
    oargv = [
        sys.executable,
        str(_PKG / "scripts" / "run_open_claims_harness.py"),
        "--output",
        str(_PKG / "proofs_report_open_claims.json"),
    ]
    if args.quick:
        oargv.append("--quick")
    rc_open = subprocess.run(oargv, cwd=_PKG, check=False).returncode
    open_path = _PKG / "proofs_report_open_claims.json"
    open_report = None
    if open_path.is_file():
        open_report = json.loads(open_path.read_text(encoding="utf-8"))
    pipeline["stages"]["open_claims_harness"] = {
        "exit_code": rc_open,
        "report": open_report,
    }
    if rc_open != 0:
        failures.append("open_claims_harness")

    print()
    print("=== Stage 1c: Tier A falsify (Ring 1 honesty) ===")
    fal_argv = [sys.executable, "-m", "lattice_forge.cli", "falsify", "--tier-a"]
    if args.quick:
        fal_argv.append("--quick")
    rc_fal = _run(fal_argv)
    pipeline["stages"]["tier_a_falsify"] = {"exit_code": rc_fal}

    failures: list[str] = []
    if rc != 0:
        failures.append("ring1_proofs")
    if not audit["ring1_gate_pass"]:
        failures.append("ring1_gate")
    if rc_fal != 0:
        failures.append("tier_a_falsify")

    if not args.skip_ring2:
        if audit["ring1_gate_pass"]:
            print()
            print("=== Stage 2: Ring 2 bundle (regimes + decomp + transport) ===")
            r2_argv = [
                sys.executable,
                "scripts/run_ring2_bundle.py",
                "--output",
                str(_PKG / "proofs_report_ring2.json"),
            ]
            if args.quick:
                r2_argv.append("--quick")
            if args.include_monster:
                r2_argv.append("--include-monster")
            rc2 = _run(r2_argv)
            pipeline["stages"]["ring2_bundle"] = {"exit_code": rc2}
            if rc2 != 0:
                failures.append("ring2_bundle")
            r2_path = _PKG / "proofs_report_ring2.json"
            if r2_path.is_file():
                pipeline["stages"]["ring2_bundle"]["report"] = json.loads(
                    r2_path.read_text(encoding="utf-8")
                )
        else:
            print("=== Stage 2: SKIPPED (Ring 1 gate failed) ===")
            pipeline["stages"]["ring2_bundle"] = {"skipped": True, "reason": "ring1_gate_fail"}
            failures.append("ring2_skipped_ring1_fail")

    pipeline["failures"] = failures
    pipeline["overall_status"] = "pass" if not failures else "fail"
    pipeline["elapsed_seconds"] = time.time() - t0

    out = _PKG / args.output
    out.write_text(json.dumps(pipeline, indent=2, default=str))
    print()
    print(f"Pipeline overall: {pipeline['overall_status']}")
    print(f"Report: {out}")
    sys.exit(0 if pipeline["overall_status"] == "pass" else 1)


if __name__ == "__main__":
    main()
