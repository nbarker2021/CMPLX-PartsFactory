"""
Enumerate lattice-forge library needs (claims + proof keys + gaps + infra).

Writes claims/library_needs.jsonl — canonical needs-first inventory.
Regenerate after registry or harness changes.

Usage:
    python scripts/enumerate_library_needs.py [--output PATH]
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys
from typing import Any

_PKG = pathlib.Path(__file__).resolve().parents[1]
_REGISTRY = _PKG / "claims" / "registry.jsonl"

# Proof keys from run_all_proofs + ring2 + transport + honesty (not all have registry rows)
_PROOF_KEYS: list[dict[str, Any]] = [
    {"proof_key": "T1_octonion_axioms", "layer": "theorem", "ring": 1, "impl": "octonion.py", "harness": "verify_octonion_axioms"},
    {"proof_key": "T2_j3o_axioms", "layer": "theorem", "ring": 1, "impl": "jordan_j3.py", "harness": "verify_j3o_axioms"},
    {"proof_key": "T3_chart_j3o_isomorphism", "layer": "theorem", "ring": 1, "impl": "core.py", "harness": "verify_chart_j3o_isomorphism"},
    {"proof_key": "T4_n3_su3_closure_exact", "layer": "theorem", "ring": 1, "impl": "f4_action.py", "harness": "verify_n3_su3_closure_exact"},
    {"proof_key": "T5_closure_scale_search", "layer": "theorem", "ring": 1, "impl": "f4_action.py", "harness": "search_for_su3_closure_scale"},
    {"proof_key": "T6_block_decomposition", "layer": "theorem", "ring": 1, "impl": "f4_action.py", "harness": "decompose_8x8_via_block_action_exact"},
    {"proof_key": "T7_closed_form_8x8", "layer": "theorem", "ring": 1, "impl": "f4_action.py", "harness": "closed_form_rule30_8x8_transition_exact"},
    {"proof_key": "T8_commutability_tree", "layer": "theorem", "ring": 1, "impl": "forge.py", "harness": "forge.can_close"},
    {"proof_key": "BONUS_chart_local_readout", "layer": "theorem", "ring": 1, "impl": "rule30.py", "harness": "verify_rule30_chart_local_readout"},
    {"proof_key": "SUBSTRATE_MAP", "layer": "regime", "ring": 2, "impl": "substrate_map.py", "harness": "verify_substrate_map"},
    {"proof_key": "CHART_CODEC", "layer": "regime", "ring": 2, "impl": "chart_codec.py", "harness": "verify_chart_codec"},
    {"proof_key": "CHART_CODEC_D4", "layer": "regime", "ring": 2, "impl": "chart_codec_d4.py", "harness": "verify_chart_codec_d4"},
    {"proof_key": "BLOCK_TOWER", "layer": "regime", "ring": 2, "impl": "block_tower.py", "harness": "verify_block_tower"},
    {"proof_key": "BLOCK_EXTRACTOR", "layer": "regime", "ring": 2, "impl": "rule30_block_extractor.py", "harness": "verify_extractor"},
    {"proof_key": "TRANSPORT_SHEET_LIFT", "layer": "transport", "ring": 2, "impl": "rule30.py", "harness": "verify_rule30_sheet_lift"},
    {"proof_key": "TRANSPORT_TORSOR_FUNCTOR", "layer": "transport", "ring": 2, "impl": "rule30.py", "harness": "verify_rule30_torsor_functor_term"},
    {"proof_key": "TRANSPORT_JULIA_RESOLUTION", "layer": "transport", "ring": 2, "impl": "rule30.py", "harness": "verify_rule30_julia_resolution"},
    {"proof_key": "TRANSPORT_FIELD_ADDRESS", "layer": "transport", "ring": 2, "impl": "rule30.py", "harness": "verify_rule30_mandelbrot_field_address"},
    {"proof_key": "TRANSPORT_EXIT_TRAJECTORY", "layer": "transport", "ring": 2, "impl": "rule30.py", "harness": "verify_rule30_exit_trajectory"},
    {"proof_key": "SHEET_POWER_LAW_BOUNDED", "layer": "obligation", "ring": 1, "impl": "honesty_harness.py", "harness": "verify_sheet_power_law_bounded"},
    {"proof_key": "DEPTH_EXTRACTION_ACCOUNTING", "layer": "obligation", "ring": 1, "impl": "honesty_harness.py", "harness": "verify_depth_extraction_accounting"},
    {"proof_key": "NONPERIODICITY_DENSITY_BOUNDED", "layer": "obligation", "ring": 1, "impl": "honesty_harness.py", "harness": "verify_nonperiodicity_density_bounded"},
    {"proof_key": "P3_WEYL_ENGINEERING", "layer": "engineering", "ring": 1, "impl": "substrate_map.py", "harness": "verify_p3_weyl_engineering"},
    {"proof_key": "VOA_HARNESS", "layer": "umbrella", "ring": 1, "impl": "voa_harness.py", "harness": "verify_voa_harness"},
    {"proof_key": "MONSTER_D4_LIFT", "layer": "umbrella", "ring": 2, "impl": "monster_d4_lift_claim.py", "harness": "verify_monster_d4_lift_claim"},
    {"proof_key": "RESIDUAL_WINDOW_LIFT", "layer": "umbrella", "ring": 2, "impl": "residual_window_lift.py", "harness": "verify_residual_window_lift"},
    {"proof_key": "RULE90_LINEARIZATION", "layer": "umbrella", "ring": 3, "impl": "rule90_linearization.py", "harness": "verify_rule90_linearization"},
    {"proof_key": "F2_MAJORANA", "layer": "umbrella", "ring": 3, "impl": "f2_majorana.py", "harness": "verify_f2_majorana"},
    {"proof_key": "OLOID_ROLLING", "layer": "umbrella", "ring": 3, "impl": "oloid_rolling.py", "harness": "verify_oloid_rolling"},
    {"proof_key": "OLOID_DUAL_PATH", "layer": "umbrella", "ring": 3, "impl": "oloid_dual_path.py", "harness": "verify_dual_path_oloid"},
    {"proof_key": "OLOID_READ_THEN_VERIFY", "layer": "umbrella", "ring": 3, "impl": "oloid_dual_path.py", "harness": "verify_read_then_verify"},
    {"proof_key": "OLOID_OCTONIONIC", "layer": "umbrella", "ring": 3, "impl": "oloid_octonionic.py", "harness": "verify_octonionic_oloid"},
    {"proof_key": "QUAD_OLOID", "layer": "umbrella", "ring": 3, "impl": "quad_oloid.py", "harness": "verify_quad_oloid"},
    {"proof_key": "OLOID_KINEMATIC", "layer": "umbrella", "ring": 3, "impl": "oloid_kinematic.py", "harness": "verify_oloid_kinematic"},
    {"proof_key": "FIVE_LANE_ROUTER", "layer": "umbrella", "ring": 3, "impl": "rule30.py", "harness": "five_lane_router"},
    {"proof_key": "ACTUATION", "layer": "umbrella", "ring": 3, "impl": "actuation.py", "harness": "verify_actuation"},
    {"proof_key": "J_MODULAR_MATRIX", "layer": "umbrella", "ring": 3, "impl": "j_modular_matrix.py", "harness": "verify_j_modular_matrix"},
    {"proof_key": "GAUSS_FOURIER_LIFT", "layer": "umbrella", "ring": 3, "impl": "gauss_fourier_lift.py", "harness": "verify_gauss_fourier_lift"},
    {"proof_key": "THREE_MOVE_CLOSURE", "layer": "umbrella", "ring": 3, "impl": "three_move_closure.py", "harness": "verify_three_move_closure"},
    {"proof_key": "G2_F4_T5_CONJUGATE", "layer": "umbrella", "ring": 3, "impl": "g2_f4_t5_conjugate.py", "harness": "verify_conjugate_triple"},
]

# Needs without full closure yet (explicit backlog)
_BACKLOG_NEEDS: list[dict[str, Any]] = [
    {
        "need_id": "need.P1.readout_injectivity",
        "layer": "prize",
        "ring": 1,
        "need_statement": "Prove 8-state chart orbit injects to center bit (no periodic folding)",
        "honesty_current": "CONJ",
        "honesty_target": "PROVEN",
        "impl_module": "core.py+rule30.py",
        "harness_id": None,
        "priority": "P0",
        "depends_on": ["P1", "T3", "BONUS"],
    },
    {
        "need_id": "need.P3.weyl_e8_full_table",
        "layer": "engineering",
        "ring": 1,
        "need_statement": "Full W(E8) coset key + O(1) lookup table (~2.6GB) with depth_N indexer",
        "honesty_current": "CONJ",
        "honesty_target": "BOUNDED_EXEC",
        "impl_module": None,
        "harness_id": "weyl_table_prototype",
        "priority": "P0",
        "depends_on": ["P3"],
        "artifact_expected": "weyl_table_prototype.py",
    },
    {
        "need_id": "need.T4.M3_spectral_nilpotent",
        "layer": "theorem",
        "ring": 1,
        "need_statement": "Formalize M=(1/8)J+N, N^3=0, M^3=(1/8)J in harness",
        "honesty_current": "CONJ",
        "honesty_target": "PROVEN",
        "impl_module": "f4_action.py",
        "priority": "P1",
        "depends_on": ["T4", "T6"],
    },
    {
        "need_id": "rule30.turing_universality",
        "layer": "obligation",
        "ring": 1,
        "need_statement": "Ribbon Turing-completeness simulation theorem",
        "honesty_current": "CONJ",
        "honesty_target": "PROVEN",
        "impl_module": "rule30.py",
        "priority": "P2",
        "blocks_release": True,
    },
    {
        "need_id": "need.infra.proofs_report_4096",
        "layer": "infra",
        "ring": 0,
        "need_statement": "Committed proofs_report_4096.json + expected_outputs depth ladder",
        "honesty_current": "missing",
        "honesty_target": "BOUNDED_EXEC",
        "artifact_expected": "proofs_report_4096.json",
        "priority": "P0",
    },
    {
        "need_id": "need.transport.tower_proven_5",
        "layer": "transport",
        "ring": 2,
        "need_statement": "≥5 transport lemmas PROVEN (open_gap_count=0) for WP-TOWER-01",
        "honesty_current": "pass_with_open_gaps",
        "honesty_target": "PROVEN",
        "harness_id": "run_transport_tower_proofs.py",
        "priority": "P1",
        "depends_on": ["WP-TOWER-01"],
    },
    {
        "need_id": "need.companion.WP-OLOID-01",
        "layer": "companion",
        "ring": 3,
        "need_statement": "QUAD_OLOID + full kinematic roll unconditional pass",
        "honesty_current": "deferred",
        "honesty_target": "BOUNDED_EXEC",
        "priority": "P2",
    },
    {
        "need_id": "need.companion.WP-MOONSHINE",
        "layer": "companion",
        "ring": 3,
        "need_statement": "VOA hypothesis PROVEN_AT_TESTED_DEPTH or documented refutation",
        "honesty_current": "deferred",
        "honesty_target": "BOUNDED_EXEC",
        "priority": "P2",
    },
    {
        "need_id": "need.voa.O1_correction_via_voa",
        "layer": "engineering",
        "ring": 3,
        "need_statement": "Implement mckay_thompson_coefficient_parity / correction_via_voa",
        "honesty_current": "stub",
        "honesty_target": "BOUNDED_EXEC",
        "impl_module": "voa_lookup.py",
        "priority": "P1",
    },
    {
        "need_id": "need.sheet.all_page_induction",
        "layer": "obligation",
        "ring": 1,
        "need_statement": "T_page^k induction for all integer pages (not only tested window)",
        "honesty_current": "CONJ",
        "honesty_target": "PROVEN",
        "depends_on": ["rule30.sheet_operator.power_law"],
        "priority": "P1",
    },
]

_SUBPACKAGE = {
    "theorem": "prize-core",
    "prize": "prize-core",
    "obligation": "prize-core",
    "regime": "regimes",
    "transport": "transport-tower",
    "umbrella": "umbrella",
    "engineering": "prize-core",
    "infra": "proofs",
    "companion": "prize-core",
}


def _load_registry() -> list[dict[str, Any]]:
    rows = []
    for line in _REGISTRY.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def _impl_status(path: str | None) -> str:
    if not path:
        return "missing"
    mod = path.split("+")[0].split("/")[0]
    p = _PKG / "src" / "lattice_forge" / mod
    return "present" if p.is_file() else "partial" if (_PKG / "src" / "lattice_forge").is_dir() else "missing"


def _harness_status(label: str | None, proof_key: str | None) -> str:
    if not proof_key and not label:
        return "none"
    if label == "PROVEN":
        return "proven"
    if label in ("BOUNDED_EXEC", "EXPRESSIBLE", "TRANSPORTED"):
        return "bounded"
    if label == "CONJ":
        return "conj"
    return "gaps"


def _priority(row: dict[str, Any]) -> str:
    if row.get("blocks_release") or row.get("honesty_current") == "CONJ" and row.get("layer") == "prize":
        return "P0"
    if row.get("honesty_target") == "PROVEN" and row.get("harness_status") in ("conj", "gaps", "none"):
        return "P1"
    if row.get("layer") == "infra":
        return "P0"
    return "P2"


def _row_from_registry(reg: dict[str, Any]) -> dict[str, Any]:
    label = reg.get("honesty_label", "CONJ")
    pk = reg.get("proof_key")
    cid = reg.get("claim_id")
    layer = reg.get("kind", "obligation")
    if layer == "lift":
        layer = "umbrella"
    ring = int(reg.get("ring", 1))
    artifact = None
    if cid == "DECOMP-PAPER":
        artifact = "docs/decomposition/README.md"
    return {
        "need_id": cid,
        "claim_id": cid,
        "proof_key": pk,
        "layer": layer if layer in _SUBPACKAGE else "obligation",
        "ring": ring,
        "subpackage": _SUBPACKAGE.get(layer, "prize-core"),
        "need_statement": reg.get("notes") or reg.get("statement_ref") or cid,
        "honesty_current": label,
        "honesty_target": "PROVEN" if label == "PROVEN" else ("BOUNDED_EXEC" if label == "CONJ" else label),
        "impl_module": reg.get("verifier_id"),
        "impl_status": _impl_status(reg.get("verifier_id")),
        "harness_id": pk or reg.get("verifier_id"),
        "harness_status": _harness_status(label, pk),
        "test_status": "partial",
        "artifact_expected": artifact,
        "artifact_present": bool(artifact and (_PKG / artifact).is_file()),
        "blocks_release": label == "CONJ" and "depth_only" in cid,
        "priority": "P2",
        "depends_on": reg.get("implicated_by", []),
        "notes": reg.get("notes", ""),
    }


def _row_from_proof_key(spec: dict[str, Any], registry_by_pk: dict[str, dict]) -> dict[str, Any] | None:
    pk = spec["proof_key"]
    reg = registry_by_pk.get(pk)
    if reg:
        return None
    return {
        "need_id": pk,
        "claim_id": None,
        "proof_key": pk,
        "layer": spec["layer"],
        "ring": spec["ring"],
        "subpackage": _SUBPACKAGE.get(spec["layer"], "umbrella"),
        "need_statement": f"Proof key {pk} in run_all_proofs",
        "honesty_current": "BOUNDED_EXEC",
        "honesty_target": "BOUNDED_EXEC",
        "impl_module": spec["impl"],
        "impl_status": _impl_status(spec["impl"]),
        "harness_id": spec["harness"],
        "harness_status": "bounded",
        "test_status": "partial",
        "artifact_expected": "proofs_report.json",
        "artifact_present": (_PKG / "proofs_report.json").is_file(),
        "blocks_release": False,
        "priority": "P2",
        "depends_on": [],
        "notes": "Umbrella/structural; not_in_ring1",
    }


def _row_from_backlog(spec: dict[str, Any]) -> dict[str, Any]:
    impl = spec.get("impl_module")
    art = spec.get("artifact_expected")
    hs = spec.get("honesty_current", "CONJ")
    harness = spec.get("harness_id")
    row = {
        "need_id": spec["need_id"],
        "claim_id": spec.get("claim_id"),
        "proof_key": spec.get("proof_key"),
        "layer": spec["layer"],
        "ring": spec["ring"],
        "subpackage": _SUBPACKAGE.get(spec["layer"], "prize-core"),
        "need_statement": spec["need_statement"],
        "honesty_current": hs,
        "honesty_target": spec.get("honesty_target", "BOUNDED_EXEC"),
        "impl_module": impl,
        "impl_status": _impl_status(impl) if impl else "missing",
        "harness_id": harness,
        "harness_status": "deferred" if hs == "deferred" else ("none" if not harness else "conj"),
        "test_status": "none",
        "artifact_expected": art,
        "artifact_present": bool(art and (_PKG / art).is_file()),
        "blocks_release": spec.get("blocks_release", False),
        "priority": spec.get("priority", "P2"),
        "depends_on": spec.get("depends_on", []),
        "notes": "",
    }
    row["priority"] = _priority(row)
    return row


def enumerate_needs() -> dict[str, Any]:
    registry = _load_registry()
    by_pk = {r["proof_key"]: r for r in registry if r.get("proof_key")}
    seen: set[str] = set()
    rows: list[dict[str, Any]] = []

    for reg in registry:
        row = _row_from_registry(reg)
        cid = row["need_id"]
        if cid in seen:
            continue
        seen.add(cid)
        row["priority"] = _priority(row)
        rows.append(row)

    for spec in _PROOF_KEYS:
        extra = _row_from_proof_key(spec, by_pk)
        if extra and extra["need_id"] not in seen:
            seen.add(extra["need_id"])
            rows.append(extra)

    for spec in _BACKLOG_NEEDS:
        nid = spec["need_id"]
        if nid not in seen:
            seen.add(nid)
            rows.append(_row_from_backlog(spec))

    counts = {
        "total": len(rows),
        "by_priority": {},
        "by_harness_status": {},
        "by_honesty_current": {},
        "blocking": sum(1 for r in rows if r.get("blocks_release")),
        "missing_impl": sum(1 for r in rows if r.get("impl_status") == "missing"),
        "no_harness": sum(1 for r in rows if r.get("harness_status") in ("none", "conj")),
    }
    for r in rows:
        for k, bucket in [
            ("priority", counts["by_priority"]),
            ("harness_status", counts["by_harness_status"]),
            ("honesty_current", counts["by_honesty_current"]),
        ]:
            v = r[k]
            bucket[v] = bucket.get(v, 0) + 1

    return {
        "generated_from": str(_REGISTRY),
        "package": "lattice-forge",
        "focus": "needs_first_enumeration",
        "summary": counts,
        "needs": rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default=str(_PKG / "claims" / "library_needs.jsonl"))
    args = parser.parse_args()

    report = enumerate_needs()
    out = pathlib.Path(args.output)
    with out.open("w", encoding="utf-8") as f:
        for row in report["needs"]:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    meta = _PKG / "claims" / "library_needs.meta.json"
    meta.write_text(
        json.dumps({k: v for k, v in report.items() if k != "needs"}, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(report["summary"], indent=2))
    print(f"Wrote {len(report['needs'])} rows -> {out}")
    print(f"Meta -> {meta}")


if __name__ == "__main__":
    main()
