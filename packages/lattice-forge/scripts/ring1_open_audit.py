"""
Audit Ring 1 claims vs latest proofs report — what is still open before Ring 2.
"""

from __future__ import annotations

import json
import pathlib
from typing import Any

_PKG = pathlib.Path(__file__).resolve().parents[1]
_REGISTRY = _PKG / "claims" / "registry.jsonl"
_DEFAULT_REPORT = _PKG / "proofs_report.json"

# Proof-key aliases from run_all_proofs → registry claim_ids
_PROOF_KEY_TO_CLAIMS: dict[str, list[str]] = {
    "T1_octonion_axioms": ["T1"],
    "T2_j3o_axioms": ["T2"],
    "T3_chart_j3o_isomorphism": ["T3"],
    "T4_n3_su3_closure_exact": ["T4"],
    "T5_closure_scale_search": ["T5"],
    "T6_block_decomposition": ["T6"],
    "T7_closed_form_8x8": ["T7"],
    "T8_commutability_tree": ["T8"],
    "BONUS_chart_local_readout": ["BONUS"],
    "TRANSPORT_FIELD_ADDRESS": ["P3"],
    "TRANSPORT_EXIT_TRAJECTORY": ["P3"],
}


def load_registry_ring1() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in _REGISTRY.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        row = json.loads(line)
        if int(row.get("ring", 0)) == 1:
            rows.append(row)
    return rows


def audit_ring1_open(
    proofs_report_path: pathlib.Path | None = None,
) -> dict[str, Any]:
    report_path = proofs_report_path or _DEFAULT_REPORT
    proofs: dict[str, Any] = {}
    raw: dict[str, Any] = {}
    overall = "missing_report"
    if report_path.is_file():
        raw = json.loads(report_path.read_text(encoding="utf-8"))
        proofs = raw.get("proofs", {})
        overall = raw.get("overall_status", "unknown")

    ring1 = load_registry_ring1()
    by_label: dict[str, list[str]] = {}
    open_conj: list[dict[str, Any]] = []
    open_gaps_in_harness: list[dict[str, Any]] = []
    proven_ok: list[str] = []

    for row in ring1:
        cid = row["claim_id"]
        label = row.get("honesty_label", "?")
        by_label.setdefault(label, []).append(cid)
        if label == "CONJ":
            open_conj.append(
                {
                    "claim_id": cid,
                    "verifier_id": row.get("verifier_id"),
                    "notes": row.get("notes"),
                    "scope": "stays CONJ until disproved or proven; not blocking Ring 2 engineering",
                }
            )
        elif label in ("PROVEN", "TRANSPORTED", "BOUNDED_EXEC", "EXPRESSIBLE"):
            proven_ok.append(cid)

    for proof_key, entry in proofs.items():
        status = entry.get("status", "")
        if status == "pass_with_open_gaps":
            open_gaps_in_harness.append(
                {
                    "proof_key": proof_key,
                    "status": status,
                    "open_gap_count": entry.get("open_gap_count"),
                    "linked_claims": _PROOF_KEY_TO_CLAIMS.get(proof_key, []),
                }
            )

    def _theorem_ok(key: str, entry: dict[str, Any]) -> bool:
        if entry.get("status") == "pass":
            return True
        if key == "T5_closure_scale_search":
            return bool(entry.get("closed_at_a_scale"))
        if key == "T6_block_decomposition":
            return bool(entry.get("both_trace_blocks_close"))
        if key == "T7_closed_form_8x8":
            return bool(entry.get("all_row_sums_unity"))
        if key == "T8_commutability_tree":
            return bool(entry.get("all_paths_found"))
        return entry.get("status") == "pass"

    _RING1_CORE_KEYS = (
        "T1_octonion_axioms",
        "T2_j3o_axioms",
        "T3_chart_j3o_isomorphism",
        "T4_n3_su3_closure_exact",
        "T5_closure_scale_search",
        "T6_block_decomposition",
        "T7_closed_form_8x8",
        "T8_commutability_tree",
        "BONUS_chart_local_readout",
    )

    gate_pass = overall == "pass"
    blocking: list[str] = []
    for key in _RING1_CORE_KEYS:
        entry = proofs.get(key)
        if not entry:
            gate_pass = False
            blocking.append(f"{key}:missing")
        elif not _theorem_ok(key, entry):
            gate_pass = False
            blocking.append(f"{key}:fail")
    if overall != "pass":
        blocking.append(f"overall_status={overall}")

    return {
        "ring": 1,
        "proofs_report": str(report_path),
        "proofs_report_present": report_path.is_file(),
        "overall_status": overall,
        "ring1_gate_pass": gate_pass,
        "blocking_failures": blocking,
        "counts_by_honesty_label": {k: len(v) for k, v in sorted(by_label.items())},
        "open_conj_obligations": open_conj,
        "harness_pass_with_open_gaps": open_gaps_in_harness,
        "policy": {
            "scope_lock": "CONJ claims are in Ring 1 abstract but must not be promoted to PROVEN",
            "not_frozen": "Ring 1 harness runs first; Ring 2 follows when T1-T8+BONUS gate passes",
            "wp_honest_03": "depth_only_shortcut, nonperiodicity_density, P3 — documented open in companion",
        },
    }


def main() -> None:
    import argparse
    import sys

    p = argparse.ArgumentParser()
    p.add_argument("--proofs-report", type=pathlib.Path, default=_DEFAULT_REPORT)
    args = p.parse_args()
    out = audit_ring1_open(args.proofs_report)
    print(json.dumps(out, indent=2))
    sys.exit(0 if out["ring1_gate_pass"] else 1)


if __name__ == "__main__":
    main()
