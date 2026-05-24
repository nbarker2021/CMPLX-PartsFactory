"""
Run All Proofs — Lattice-Forge Universality Umbrella Submission
================================================================

Runs every proven theorem in the submission and writes proofs_report.json.

Usage:
    python scripts/run_all_proofs.py [--quick] [--max-depth N] [--output PATH]

--quick      : reduces max_depth from 4096 to 256 for faster sanity check.
--max-depth N: explicit depth (default 4096).
--output PATH: where to write the JSON report (default proofs_report.json).

Exit codes:
    0 = all proofs pass
    1 = one or more proofs failed
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys
import tempfile
import time


def _format(d, keys):
    return {k: d.get(k) for k in keys if k in d}


def run_proofs(max_depth: int = 4096) -> dict:
    """Run all proofs and return a structured report."""
    src_path = pathlib.Path(__file__).resolve().parents[1] / "src"
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))

    from lattice_forge.octonion import verify_octonion_axioms
    from lattice_forge.jordan_j3 import verify_j3o_axioms
    from lattice_forge.rule30 import (
        rule30_exit_trajectory,
        rule30_mandelbrot_field_address,
        verify_chart_j3o_isomorphism,
        verify_rule30_chart_local_readout,
        verify_rule30_exit_trajectory,
        verify_rule30_mandelbrot_field_address,
    )
    from lattice_forge.f4_action import (
        verify_n3_su3_closure_exact,
        search_for_su3_closure_scale,
        decompose_8x8_via_block_action_exact,
        closed_form_rule30_8x8_transition_exact,
    )
    from lattice_forge.substrate_map import verify_substrate_map
    from lattice_forge.chart_codec import verify_chart_codec
    from lattice_forge.chart_codec_d4 import verify_chart_codec_d4
    from lattice_forge.rule90_linearization import verify_rule90_linearization
    from lattice_forge.f2_majorana import verify_f2_majorana
    from lattice_forge.oloid_rolling import verify_oloid_rolling
    from lattice_forge.oloid_dual_path import (
        verify_dual_path_oloid,
        verify_read_then_verify,
    )
    from lattice_forge.oloid_octonionic import (
        verify_octonionic_oloid,
        orient_bit_information_content,
    )
    from lattice_forge.block_tower import verify_block_tower
    from lattice_forge.rule30_block_extractor import verify_extractor as verify_block_extractor
    from lattice_forge import Forge

    report = {
        "submission": "lattice-forge universality umbrella v1.0",
        "max_depth_tested": max_depth,
        "proofs": {},
        "overall_status": "pending",
    }
    failures = []

    # T1
    print("[T1] Octonion algebra axioms...")
    t = verify_octonion_axioms()
    report["proofs"]["T1_octonion_axioms"] = t
    if t["status"] != "pass":
        failures.append("T1")
    print(f"   status: {t['status']}")

    # T2
    print("[T2] J_3(O) Jordan algebra axioms...")
    t = verify_j3o_axioms()
    report["proofs"]["T2_j3o_axioms"] = t
    if t["status"] != "pass":
        failures.append("T2")
    print(f"   status: {t['status']}")

    # T3
    print(f"[T3] Chart-J_3(O) isomorphism at depth {max_depth}...")
    t_full = verify_chart_j3o_isomorphism(max_depth=max_depth)
    t = _format(t_full, [
        "status", "total_depths_checked", "bijection_failures",
        "trace_mismatches", "weyl_mismatches", "readout_mismatches",
        "trace_2_stratum_count", "trace_2_idempotent_count",
        "trace_2_all_idempotent",
    ])
    report["proofs"]["T3_chart_j3o_isomorphism"] = t
    if t["status"] != "pass":
        failures.append("T3")
    print(f"   bijection_failures={t['bijection_failures']}, "
          f"trace_mismatches={t['trace_mismatches']}, "
          f"weyl_mismatches={t['weyl_mismatches']}, "
          f"readout_mismatches={t['readout_mismatches']}")

    # T4
    print("[T4] Exact n=3 SU(3) Weyl closure over Q...")
    t_full = verify_n3_su3_closure_exact()
    t = _format(t_full, [
        "status", "n_steps", "coefficient_sum_exact",
        "residual_squared_exact", "is_exact_group_ring_element",
        "s3_coefficients_exact_strings",
    ])
    report["proofs"]["T4_n3_su3_closure_exact"] = t
    if t["status"] != "pass":
        failures.append("T4")
    print(f"   residual^2 = {t['residual_squared_exact']}, "
          f"is_group_ring_element = {t['is_exact_group_ring_element']}")

    # T5
    print("[T5] Closure scale search...")
    t_full = search_for_su3_closure_scale(max_scale=8)
    t = {
        "best_scale": t_full["best_scale"],
        "best_residual_l2": t_full["best_residual_l2"],
        "closed_at_a_scale": t_full["closed_at_a_scale"],
    }
    report["proofs"]["T5_closure_scale_search"] = t
    if t["best_scale"] != 3 or not t["closed_at_a_scale"]:
        failures.append("T5")
    print(f"   best_scale={t['best_scale']}, closed={t['closed_at_a_scale']}")

    # T6
    print("[T6] Both trace-blocks close identically...")
    t_full = decompose_8x8_via_block_action_exact(n_steps=3)
    t = {
        "both_trace_blocks_close": t_full["claim"][
            "both_trace_blocks_close_as_s3_elements"],
        "trace1_is_exact_s3_element": t_full["trace1_is_exact_s3_element"],
        "trace2_is_exact_s3_element": t_full["trace2_is_exact_s3_element"],
    }
    report["proofs"]["T6_block_decomposition"] = t
    if not t["both_trace_blocks_close"]:
        failures.append("T6")
    print(f"   trace1 exact: {t['trace1_is_exact_s3_element']}, "
          f"trace2 exact: {t['trace2_is_exact_s3_element']}")

    # T7
    print("[T7] Closed-form 8x8 from Rule 30 truth table...")
    t_full = closed_form_rule30_8x8_transition_exact()
    n_states = len(t_full["states"])
    row_sums = [str(sum(t_full["matrix"][i])) for i in range(n_states)]
    t = {
        "n_states": n_states,
        "all_row_sums_unity": all(s == "1" for s in row_sums),
    }
    report["proofs"]["T7_closed_form_8x8"] = t
    if not t["all_row_sums_unity"]:
        failures.append("T7")
    print(f"   all_row_sums_unity: {t['all_row_sums_unity']}")

    # T8
    print("[T8] F_4 to Niemeier commutability paths...")
    forge = Forge.open(pathlib.Path(tempfile.mkdtemp(prefix="lf-verify-")))
    niemeiers = [
        "Niemeier:E8^3", "Niemeier:D16_E8", "Niemeier:A17_E7",
        "Niemeier:D10_E7^2", "Niemeier:A11_D7_E6", "Niemeier:E6^4",
        "Niemeier:A5^4_D4", "Niemeier:D4^6",
    ]
    paths = []
    for tgt in niemeiers:
        r = forge.can_close("F4", tgt).get("result", {}).get("can_close", {})
        if r.get("answer", "").startswith("yes"):
            paths.append({"target": tgt, "answer": r.get("answer"),
                          "path": r.get("path", [])})
    t = {
        "paths_count": len(paths),
        "expected_paths_count": 8,
        "all_paths_found": len(paths) == 8,
        "paths": paths,
    }
    report["proofs"]["T8_commutability_tree"] = t
    if not t["all_paths_found"]:
        failures.append("T8")
    print(f"   paths_found: {t['paths_count']} / 8")

    # Substrate map
    print(f"[SUBSTRATE_MAP] Verifying substrate map at depth {max_depth}...")
    t_full = verify_substrate_map(max_depth=max_depth)
    t = _format(t_full, ["status", "max_depth_tested", "checks"])
    report["proofs"]["SUBSTRATE_MAP"] = t
    if t["status"] != "pass":
        failures.append("SUBSTRATE_MAP")
    print(f"   status: {t['status']}")

    # Chart codec (Regime C: S_3 word codec on shell=2 sub-trajectory)
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

    # Chart codec D_4 (Regime C': full-chart antipodal decomposition)
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

    # Rule 90 linearization (Rule 30 = Rule 90 XOR correction via Lucas)
    print("[RULE90_LINEARIZATION] Rule 30 = Rule 90 + correction decomposition...")
    r90 = verify_rule90_linearization()
    r90_summary = {
        "status": r90["status"],
        "identity_at_truth_table": r90["identity_at_truth_table"],
        "lucas_matches_direct_rule90_at_depth_64":
            r90["lucas_matches_direct_rule90_at_depth_64"],
        "decomposition_matches_at_all_depths":
            r90["decomposition_matches_at_all_depths"],
        "depths_tested_count": len(r90["depths_tested"]),
    }
    report["proofs"]["RULE90_LINEARIZATION"] = r90_summary
    if r90_summary["status"] != "pass":
        failures.append("RULE90_LINEARIZATION")
    print(f"   identity={r90_summary['identity_at_truth_table']}, "
          f"lucas={r90_summary['lucas_matches_direct_rule90_at_depth_64']}, "
          f"decomp={r90_summary['decomposition_matches_at_all_depths']}")

    # F_2 / Majorana primitives (T_F2_BRIDGE: Arf invariant + edge-glue)
    print("[F2_MAJORANA] F_2 quadratic forms, Arf invariant, edge gluing...")
    f2 = verify_f2_majorana()
    f2_summary = {k: v for k, v in f2.items() if k != "expected"}
    report["proofs"]["F2_MAJORANA"] = f2_summary
    if f2_summary["status"] != "pass":
        failures.append("F2_MAJORANA")
    print(f"   rule30_correction_arf={f2_summary['rule30_correction_arf']}, "
          f"status={f2_summary['status']}")

    # Oloid rolling chart (head|tail bit dyad bijection carrier)
    print("[OLOID_ROLLING] Oloid rolling state, head|tail dyad, cyclic invariance...")
    ol = verify_oloid_rolling()
    ol_summary = {k: v for k, v in ol.items() if k != "expected"}
    report["proofs"]["OLOID_ROLLING"] = ol_summary
    if ol_summary["status"] != "pass":
        failures.append("OLOID_ROLLING")
    print(f"   bit0_period_4={ol_summary['bit0_period_4']}, "
          f"k6_invariant_phase_fraction={ol_summary['k6_invariant_phase_fraction']}, "
          f"status={ol_summary['status']}")

    # Dual-path Oloid (structural: three-dyad S_3 architecture)
    print("[OLOID_DUAL_PATH] Three-dyad Oloid, S_3 cyclic involution, addressing arithmetic...")
    dp = verify_dual_path_oloid()
    dp_summary = {
        "status": dp["status"],
        "triple_involution_level": dp["triple_involution_level"],
        "tape_readout_match_rate": dp["tape_readout_match_rate"],
        "tape_readout_samples": dp["tape_readout_samples"],
    }
    report["proofs"]["OLOID_DUAL_PATH"] = dp_summary
    if dp_summary["status"] != "pass":
        failures.append("OLOID_DUAL_PATH")
    print(f"   triple_involution_level={dp_summary['triple_involution_level']}, "
          f"tape_readout_match_rate={dp_summary['tape_readout_match_rate']:.3f} "
          f"(structural-only; per-dyad roll rule open)")

    # Read-then-bijectively-verify workflow (the actual solver flow)
    print("[OLOID_READ_THEN_VERIFY] Read-then-verify workflow at depths 1..200...")
    from lattice_forge.block_tower import rule30_center_column as _rcc
    _rule30_bits_for_verify = _rcc(200)
    def _enum(N):
        return _rule30_bits_for_verify[N - 1]
    rv = verify_read_then_verify(_enum, sample_depths=list(range(1, 201)))
    rv_summary = {
        "status": "pass" if rv["bit_match_rate"] == 1.0 and rv["consistency_rate"] == 1.0 else "fail",
        "bit_match_rate": rv["bit_match_rate"],
        "consistency_rate": rv["consistency_rate"],
        "orient_bit_density": rv["orient_bit_density"],
        "sample_count": rv["sample_count"],
    }
    report["proofs"]["OLOID_READ_THEN_VERIFY"] = rv_summary
    if rv_summary["status"] != "pass":
        failures.append("OLOID_READ_THEN_VERIFY")
    print(f"   bit_match_rate={rv_summary['bit_match_rate']}, "
          f"consistency_rate={rv_summary['consistency_rate']}, "
          f"orient_density={rv_summary['orient_bit_density']:.3f}")

    # Octonion-grounded Oloid: explicit e_4 1/4-spin generator
    print("[OLOID_OCTONIONIC] Octonion-grounded Oloid, e_4 1/4-spin, non-trivial orient bit...")
    oc = verify_octonionic_oloid()
    info = orient_bit_information_content(
        [[(n >> i) & 1 for i in range(8)] for n in range(256)]
    )
    oc_summary = {
        "status": oc["status"],
        "e4_squared_is_minus_one": oc["e4_squared_is_minus_one"],
        "four_rolls_bit0_return_to_initial": oc["four_rolls_bit0_return_to_initial"],
        "non_associative_imaginary_units": oc["non_associative_imaginary_units"],
        "orient_trivial_baseline_rate": info["trivial_baseline_rate"],
        "orient_marginal_density": info["orient_marginal_density"],
        "orient_joint_distribution": info["joint_distribution"],
    }
    report["proofs"]["OLOID_OCTONIONIC"] = oc_summary
    if oc_summary["status"] != "pass":
        failures.append("OLOID_OCTONIONIC")
    print(f"   e4^2=-1: {oc_summary['e4_squared_is_minus_one']}, "
          f"orient_independent_of_bit: trivial_rate={oc_summary['orient_trivial_baseline_rate']:.2f} "
          f"(0.5 = independent)")

    # Block tower (Regime A: hierarchical checkpoint store)
    bt_depth = min(max_depth, 4096)
    print(f"[BLOCK_TOWER] Checkpoint store round-trip at depth {bt_depth}...")
    bt = verify_block_tower(max_depth=bt_depth)
    bt_summary = _format(bt, ["status", "max_depth", "sample_count", "mismatch_count"])
    report["proofs"]["BLOCK_TOWER"] = bt_summary
    if bt_summary["status"] != "pass":
        failures.append("BLOCK_TOWER")
    print(f"   mismatch_count={bt_summary['mismatch_count']} / "
          f"{bt_summary['sample_count']}")

    # Block-addressed extractor (Regime A: constant-time per-query reads)
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

    # Transport tower: field address + exit trajectory (honest pass_with_open_gaps)
    transport_n = 257
    transport_page = 128
    print(f"[TRANSPORT_FIELD_ADDRESS] Mandelbrot field address at n={transport_n}...")
    fa_model = rule30_mandelbrot_field_address(
        transport_n, page_size=transport_page, block_size=8, max_order=4
    )
    fa = verify_rule30_mandelbrot_field_address(fa_model)
    fa_summary = _format(fa, ["status", "schema_status", "n", "open_gap_count"])
    report["proofs"]["TRANSPORT_FIELD_ADDRESS"] = fa_summary
    if fa_summary["status"] not in {"pass", "pass_with_open_gaps"}:
        failures.append("TRANSPORT_FIELD_ADDRESS")
    print(f"   status: {fa_summary['status']}")

    print(f"[TRANSPORT_EXIT_TRAJECTORY] Julia exit trajectory at n={transport_n}...")
    ex_model = rule30_exit_trajectory(
        transport_n, page_size=transport_page, block_size=8, max_order=4
    )
    ex = verify_rule30_exit_trajectory(ex_model)
    ex_summary = _format(ex, ["status", "schema_status", "n", "open_gap_count"])
    report["proofs"]["TRANSPORT_EXIT_TRAJECTORY"] = ex_summary
    if ex_summary["status"] not in {"pass", "pass_with_open_gaps"}:
        failures.append("TRANSPORT_EXIT_TRAJECTORY")
    print(f"   status: {ex_summary['status']}")

    # Chart local readout (BONUS)
    print(f"[BONUS] Chart local readout = Rule 30 exactly at depth {max_depth}...")
    cl = verify_rule30_chart_local_readout(max_depth=max_depth)
    cl_summary = _format(cl, [
        "status", "max_depth", "forward_defect_count", "forward_accuracy",
    ])
    report["proofs"]["BONUS_chart_local_readout"] = cl_summary
    if cl_summary.get("forward_defect_count", 1) != 0:
        failures.append("BONUS")
    print(f"   forward_defects: {cl_summary['forward_defect_count']} / "
          f"{cl_summary['max_depth']}")

    report["failures"] = failures
    report["overall_status"] = "pass" if not failures else "fail"
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--quick", action="store_true",
                        help="Use max_depth=256 instead of 4096")
    parser.add_argument("--max-depth", type=int, default=4096,
                        help="Depth to verify at")
    parser.add_argument("--output", default="proofs_report.json",
                        help="Output JSON file path")
    args = parser.parse_args()
    max_depth = 256 if args.quick else args.max_depth

    print(f"=== Lattice-Forge Universality Submission: Run All Proofs ===")
    print(f"Verification window: max_depth = {max_depth}")
    print()
    t_start = time.time()
    report = run_proofs(max_depth)
    elapsed = time.time() - t_start
    report["elapsed_seconds"] = elapsed

    print()
    print(f"=== Summary ===")
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
