"""
Run transport-tower lemma proofs (Ring 2 unlock path for WP-TOWER-01).
======================================================================

Executes the five transport lemmas documented in docs/tower/TRANSPORT_LEMMAS.md.
``pass_with_open_gaps`` is recorded honestly; only rows with status ``pass`` and
``open_gap_count == 0`` count as **PROVEN** per TRANSPORT_TOWER_POLICY.md.

Usage:
    python scripts/run_transport_tower_proofs.py [--quick] [--output PATH]

--quick  : use n=33, page_size=32 (CI-fast; still exercises all five lemmas)
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys
import tempfile
import time
from typing import Any, Callable


def _extract_status(payload: dict[str, Any]) -> dict[str, Any]:
    """Normalize forge wrapper or bare verifier dict."""
    result = payload.get("result", payload)
    return {
        "status": result.get("status", "fail"),
        "schema_status": result.get("schema_status"),
        "open_gap_count": result.get("open_gap_count", result.get("open_gaps")),
        "n": result.get("n"),
    }


def _promotion_status(summary: dict[str, Any]) -> str:
    status = summary.get("status", "fail")
    gaps = summary.get("open_gap_count")
    if gaps is None:
        gaps = 0
    if status == "pass" and int(gaps or 0) == 0:
        return "PROVEN"
    if status in ("pass", "pass_with_open_gaps"):
        return "pass_with_open_gaps"
    return "fail"


def run_transport_tower_proofs(*, n: int, page_size: int, block_size: int, max_order: int) -> dict:
    src_path = pathlib.Path(__file__).resolve().parents[1] / "src"
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))

    from lattice_forge import Forge

    root = pathlib.Path(tempfile.mkdtemp(prefix="lf-transport-"))
    forge = Forge.open(root)
    params = {"n": n, "page_size": page_size, "block_size": block_size, "max_order": max_order}

    specs: list[tuple[str, str, str, Callable[[], dict]]] = [
        (
            "transport.sheet_lift.finite_window",
            "TRANSPORT_SHEET_LIFT",
            "verify_rule30_sheet_lift",
            lambda: forge.verify_rule30_sheet_lift(n, page_size, block_size, max_order),
        ),
        (
            "transport.torsor_functor.coherence",
            "TRANSPORT_TORSOR_FUNCTOR",
            "verify_rule30_torsor_functor_term",
            lambda: forge.verify_rule30_torsor_functor_term(n, page_size, block_size, max_order),
        ),
        (
            "transport.glue.julia_resolution",
            "TRANSPORT_JULIA_RESOLUTION",
            "verify_rule30_julia_resolution",
            lambda: forge.verify_rule30_julia_resolution(n, page_size, block_size, max_order),
        ),
        (
            "transport.field_address.mandelbrot",
            "TRANSPORT_FIELD_ADDRESS",
            "verify_rule30_mandelbrot_field_address",
            lambda: forge.verify_rule30_mandelbrot_field_address(n, page_size, block_size, max_order),
        ),
        (
            "transport.exit_trajectory.julia",
            "TRANSPORT_EXIT_TRAJECTORY",
            "verify_rule30_exit_trajectory",
            lambda: forge.verify_rule30_exit_trajectory(n, page_size, block_size, max_order),
        ),
    ]

    report: dict[str, Any] = {
        "submission": "lattice-forge transport-tower ring-2 v1.0",
        "params": params,
        "lemmas": [],
        "proofs": {},
        "promotion": {"proven_count": 0, "pass_with_open_gaps_count": 0, "fail_count": 0},
        "wp_tower_01": {"deferred": True, "trigger": ">=5 PROVEN rows"},
        "overall_status": "pending",
        "honesty": {
            "pass_with_open_gaps_is_not_proven": True,
            "depth_only_shortcut": "CONJ",
        },
    }
    failures: list[str] = []

    for lemma_id, proof_key, verifier_id, run in specs:
        print(f"[{proof_key}] {lemma_id} (n={n})...")
        raw = run()
        summary = _extract_status(raw)
        promo = _promotion_status(summary)
        row = {
            "lemma_id": lemma_id,
            "proof_key": proof_key,
            "verifier_id": verifier_id,
            "promotion_status": promo,
            **summary,
        }
        report["lemmas"].append(row)
        report["proofs"][proof_key] = summary
        if promo == "PROVEN":
            report["promotion"]["proven_count"] += 1
        elif promo == "pass_with_open_gaps":
            report["promotion"]["pass_with_open_gaps_count"] += 1
        else:
            report["promotion"]["fail_count"] += 1
            failures.append(proof_key)
        print(f"   status={summary['status']} promotion={promo}")

    proven = report["promotion"]["proven_count"]
    report["wp_tower_01"]["deferred"] = proven < 5
    report["wp_tower_01"]["proven_count"] = proven
    report["failures"] = failures
    report["overall_status"] = "pass" if not failures else "fail"
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--quick", action="store_true", help="n=33 page_size=32")
    parser.add_argument("--n", type=int, default=257)
    parser.add_argument("--page-size", type=int, default=128)
    parser.add_argument("--block-size", type=int, default=8)
    parser.add_argument("--max-order", type=int, default=4)
    parser.add_argument("--output", default="proofs_report_transport.json")
    args = parser.parse_args()

    n = 33 if args.quick else args.n
    page_size = 32 if args.quick else args.page_size

    print("=== Lattice-Forge Transport Tower (Ring 2) ===")
    t0 = time.time()
    report = run_transport_tower_proofs(
        n=n,
        page_size=page_size,
        block_size=args.block_size,
        max_order=args.max_order,
    )
    report["elapsed_seconds"] = time.time() - t0

    print()
    print("=== Summary ===")
    print(f"Overall: {report['overall_status']}")
    print(
        f"PROVEN={report['promotion']['proven_count']} "
        f"pass_with_open_gaps={report['promotion']['pass_with_open_gaps_count']} "
        f"fail={report['promotion']['fail_count']}"
    )
    print(f"WP-TOWER-01 deferred: {report['wp_tower_01']['deferred']}")

    out = pathlib.Path(args.output)
    out.write_text(json.dumps(report, indent=2, default=str))
    print(f"Report: {out}")
    sys.exit(0 if report["overall_status"] == "pass" else 1)


if __name__ == "__main__":
    main()
