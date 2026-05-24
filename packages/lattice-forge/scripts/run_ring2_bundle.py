"""
Ring 2 proof bundle — regimes + decomposition + transport tower (+ optional monster).
=====================================================================================

Ring 2 companions and engineering proofs unlock deferred Ring 3 work (Oloid, VOA,
full transport promotion). This script is the canonical local/CI gate for that layer.

Usage:
    python scripts/run_ring2_bundle.py [--quick] [--include-monster] [--output PATH]
"""

from __future__ import annotations

import argparse
import json
import pathlib
import subprocess
import sys
import time
from typing import Any


def _run_script(name: str, argv: list[str], cwd: pathlib.Path) -> tuple[int, dict[str, Any] | None]:
    cmd = [sys.executable, str(cwd / "scripts" / name), *argv]
    proc = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    out_path = argv[-1] if argv and argv[-1].endswith(".json") else None
    payload = None
    if out_path and pathlib.Path(out_path).is_file():
        payload = json.loads(pathlib.Path(out_path).read_text(encoding="utf-8"))
    if proc.returncode != 0 and proc.stderr:
        print(proc.stderr, file=sys.stderr)
    return proc.returncode, payload


def _run_decomposition(max_depth: int) -> dict[str, Any]:
    pkg = pathlib.Path(__file__).resolve().parents[1]
    src_path = pkg / "src"
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))

    from lattice_forge.decomposition import verify_all_theorems, verify_checkpoint_store

    depths = range(1, 33) if max_depth <= 256 else range(1, 129)
    theorems = verify_all_theorems(decomposition_depths=depths)
    checkpoints = verify_checkpoint_store(max_depth=max_depth)
    ok = theorems.get("status") == "pass" and checkpoints.get("status") == "pass"
    return {
        "claim_id": "DECOMP-PAPER",
        "companion": "WP-DECOMP-01",
        "theorems": theorems,
        "checkpoints": checkpoints,
        "overall_status": "pass" if ok else "fail",
    }


def _run_monster(max_depth: int) -> dict[str, Any]:
    pkg = pathlib.Path(__file__).resolve().parents[1]
    src_path = pkg / "src"
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))

    from lattice_forge.monster_d4_lift_claim import verify_monster_d4_lift_claim
    from lattice_forge.residual_window_lift import verify_residual_window_lift

    d4 = verify_monster_d4_lift_claim(max_depth=max_depth)
    res = verify_residual_window_lift(max_depth=max_depth)
    ok = d4.get("status") == "pass" and res.get("status") == "pass"
    return {
        "monster_d4_lift": d4,
        "residual_window_lift": res,
        "overall_status": "pass" if ok else "fail",
    }


def run_ring2_bundle(
    *,
    quick: bool,
    max_depth: int,
    include_monster: bool,
    pkg_root: pathlib.Path,
) -> dict[str, Any]:
    depth = 256 if quick else max_depth
    failures: list[str] = []
    report: dict[str, Any] = {
        "ring": 2,
        "submission": "lattice-forge ring-2 bundle v1.0",
        "max_depth": depth,
        "quick": quick,
        "streams": {},
        "companions": {},
        "deferred_companions": {
            "WP-OLOID-01": "quad_oloid + full kinematic roll proof key",
            "WP-MOONSHINE": "voa_lookup harness CONJ closure",
            "WP-TOWER-01": ">=5 transport lemmas PROVEN (pass_with_open_gaps does not count)",
        },
        "honesty": {
            "not_in_ring1": True,
            "depth_only_shortcut": "CONJ",
        },
    }

    print("--- Regimes (WP-REGIMES-01) ---")
    regimes_argv = ["--quick", "--output", str(pkg_root / "proofs_report_regimes.json")] if quick else [
        "--max-depth",
        str(depth),
        "--output",
        str(pkg_root / "proofs_report_regimes.json"),
    ]
    rc, regimes = _run_script("run_regimes_proofs.py", regimes_argv, pkg_root)
    report["streams"]["regimes"] = regimes or {"overall_status": "fail", "error": "no report"}
    if rc != 0 or report["streams"]["regimes"].get("overall_status") != "pass":
        failures.append("regimes")
    report["companions"]["WP-REGIMES-01"] = (
        "ready" if report["streams"]["regimes"].get("overall_status") == "pass" else "blocked"
    )

    print("--- Decomposition (WP-DECOMP-01) ---")
    decomp = _run_decomposition(depth)
    report["streams"]["decomposition"] = decomp
    if decomp.get("overall_status") != "pass":
        failures.append("decomposition")
    report["companions"]["WP-DECOMP-01"] = (
        "ready" if decomp.get("overall_status") == "pass" else "blocked"
    )

    print("--- Transport tower (WP-TOWER-01 gate) ---")
    transport_out = str(pkg_root / "proofs_report_transport.json")
    transport_argv = ["--output", transport_out]
    if quick:
        transport_argv = ["--quick", "--output", transport_out]
    rc, transport = _run_script("run_transport_tower_proofs.py", transport_argv, pkg_root)
    report["streams"]["transport_tower"] = transport or {"overall_status": "fail"}
    if rc != 0 or report["streams"]["transport_tower"].get("overall_status") != "pass":
        failures.append("transport_tower")
    proven = (transport or {}).get("promotion", {}).get("proven_count", 0)
    report["companions"]["WP-TOWER-01"] = (
        "ready" if proven >= 5 else f"deferred ({proven}/5 PROVEN)"
    )

    if include_monster:
        print(f"--- Monster / residual claims (depth={depth}) ---")
        monster = _run_monster(depth)
        report["streams"]["monster_claims"] = monster
        if monster.get("overall_status") != "pass":
            failures.append("monster_claims")

    report["failures"] = failures
    report["overall_status"] = "pass" if not failures else "fail"
    report["unlock_summary"] = {
        "regimes_tools": report["companions"].get("WP-REGIMES-01") == "ready",
        "decomposition_paper": report["companions"].get("WP-DECOMP-01") == "ready",
        "transport_tower_companion": report["companions"].get("WP-TOWER-01") == "ready",
    }
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--quick", action="store_true")
    parser.add_argument("--max-depth", type=int, default=4096)
    parser.add_argument("--include-monster", action="store_true")
    parser.add_argument("--output", default="proofs_report_ring2.json")
    args = parser.parse_args()

    pkg_root = pathlib.Path(__file__).resolve().parents[1]
    print("=== Lattice-Forge Ring 2 Bundle ===")
    print("Honesty: CONJ obligations (depth shortcut, VOA) are not promoted here.")
    t0 = time.time()
    report = run_ring2_bundle(
        quick=args.quick,
        max_depth=args.max_depth,
        include_monster=args.include_monster,
        pkg_root=pkg_root,
    )
    report["elapsed_seconds"] = time.time() - t0

    print()
    print("=== Ring 2 Summary ===")
    print(f"Overall: {report['overall_status']}")
    for cid, state in report["companions"].items():
        print(f"  {cid}: {state}")
    if report["failures"]:
        print(f"Failures: {', '.join(report['failures'])}")

    out = pkg_root / args.output
    out.write_text(json.dumps(report, indent=2, default=str))
    print(f"Bundle report: {out}")
    sys.exit(0 if report["overall_status"] == "pass" else 1)


if __name__ == "__main__":
    main()
