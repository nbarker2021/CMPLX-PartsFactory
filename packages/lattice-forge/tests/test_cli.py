from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


def run_cli(tmp_path: Path, *args: str):
    cmd = [sys.executable, "-m", "lattice_forge.cli", "--root", str(tmp_path), *args]
    env = os.environ.copy()
    src = str(Path(__file__).resolve().parents[1] / "src")
    env["PYTHONPATH"] = src + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    return subprocess.run(cmd, text=True, capture_output=True, check=False, env=env)


def test_cli_status_and_can_close(tmp_path: Path):
    status = run_cli(tmp_path, "status")
    assert status.returncode == 0, status.stderr
    payload = json.loads(status.stdout)
    assert payload["package"] == "lattice-forge"
    assert payload["seed_integrity"] == "ok"

    close = run_cli(tmp_path, "can-close", "G2", "Niemeier:A2^12")
    assert close.returncode == 0, close.stderr
    close_payload = json.loads(close.stdout)
    assert close_payload["answer"] == "yes_with_template_glue"

    tree = run_cli(tmp_path, "terminal-tree", "A2^12")
    assert tree.returncode == 0, tree.stderr
    tree_payload = json.loads(tree.stdout)
    assert tree_payload["result"]["terminal_id"] == "Niemeier:A2^12"
    assert tree_payload["result"]["composition_route"][-1]["label"] == "12xA2"
    assert tree_payload["result"]["closure_residue"]["status"] == "residue_closes_by_required_index"

    trees = run_cli(tmp_path, "terminal-trees")
    assert trees.returncode == 0, trees.stderr
    trees_payload = json.loads(trees.stdout)
    assert trees_payload["result"]["terminal_count"] == 24
    assert any(row["terminal_id"] == "Niemeier:Leech" for row in trees_payload["result"]["terminals"])

    assert (tmp_path / ".lattice_forge" / "overlay.sqlite").exists()


def test_cli_verify_seed(tmp_path: Path):
    verify = run_cli(tmp_path, "verify-seed")
    assert verify.returncode == 0, verify.stderr
    payload = json.loads(verify.stdout)
    assert payload["result"]["status"] == "pass"

    verify_trees = run_cli(tmp_path, "verify-terminal-trees")
    assert verify_trees.returncode == 0, verify_trees.stderr
    tree_payload = json.loads(verify_trees.stdout)
    assert tree_payload["result"]["status"] == "pass"
    assert tree_payload["result"]["terminal_count"] == 24

    morphonics = run_cli(tmp_path, "morphonics-model")
    assert morphonics.returncode == 0, morphonics.stderr
    morphonics_payload = json.loads(morphonics.stdout)
    assert morphonics_payload["result"]["model_id"] == "MSCF:morphonics_unified_formal_model_v0_2"

    verify_morphonics = run_cli(tmp_path, "verify-morphonics")
    assert verify_morphonics.returncode == 0, verify_morphonics.stderr
    verify_payload = json.loads(verify_morphonics.stdout)
    assert verify_payload["result"]["schema_status"] == "pass"
    assert verify_payload["result"]["status"] == "pass_with_open_gaps"

    rule30 = run_cli(tmp_path, "rule30-morphon", "--max-depth", "5")
    assert rule30.returncode == 0, rule30.stderr
    rule30_payload = json.loads(rule30.stdout)
    assert rule30_payload["result"]["model_id"] == "rule30_morphon_hardened_v0_6"
    assert rule30_payload["result"]["summary"]["canonical_depths_passed"] == 5

    verify_rule30 = run_cli(tmp_path, "verify-rule30", "--max-depth", "5")
    assert verify_rule30.returncode == 0, verify_rule30.stderr
    verify_rule30_payload = json.loads(verify_rule30.stdout)
    assert verify_rule30_payload["result"]["schema_status"] == "pass"
    assert verify_rule30_payload["result"]["status"] == "pass_with_open_gaps"

    vignettes = run_cli(tmp_path, "rule30-vignettes", "--max-order", "4")
    assert vignettes.returncode == 0, vignettes.stderr
    vignette_payload = json.loads(vignettes.stdout)
    assert vignette_payload["result"]["saturated_zero_preserving_space"] is True
    assert vignette_payload["result"]["unique_function_count"] == 128

    verify_vignettes = run_cli(tmp_path, "verify-rule30-vignettes", "--max-order", "4")
    assert verify_vignettes.returncode == 0, verify_vignettes.stderr
    verify_vignette_payload = json.loads(verify_vignettes.stdout)
    assert verify_vignette_payload["result"]["schema_status"] == "pass"

    moving = run_cli(tmp_path, "rule30-moving-frame", "--max-depth", "8")
    assert moving.returncode == 0, moving.stderr
    moving_payload = json.loads(moving.stdout)
    assert moving_payload["result"]["moving_space_summary"]["candidate_count"] == 56

    verify_moving = run_cli(tmp_path, "verify-rule30-moving-frame", "--max-depth", "8")
    assert verify_moving.returncode == 0, verify_moving.stderr
    verify_moving_payload = json.loads(verify_moving.stdout)
    assert verify_moving_payload["result"]["schema_status"] == "pass"

    chiral = run_cli(tmp_path, "rule30-color-chirality", "--max-depth", "8")
    assert chiral.returncode == 0, chiral.stderr
    chiral_payload = json.loads(chiral.stdout)
    assert chiral_payload["result"]["closure_summary"]["token_count"] == 6
    assert chiral_payload["result"]["closure_summary"]["composition_closed"] is True

    verify_chiral = run_cli(tmp_path, "verify-rule30-color-chirality", "--max-depth", "8")
    assert verify_chiral.returncode == 0, verify_chiral.stderr
    verify_chiral_payload = json.loads(verify_chiral.stdout)
    assert verify_chiral_payload["result"]["schema_status"] == "pass"

    lagrangian = run_cli(tmp_path, "rule30-lagrangian", "--max-depth", "8")
    assert lagrangian.returncode == 0, lagrangian.stderr
    lagrangian_payload = json.loads(lagrangian.stdout)
    assert lagrangian_payload["result"]["action_summary"]["plaquette_count"] == 96
    assert lagrangian_payload["result"]["action_summary"]["action_zero_is_legal_rule30_update"] is True

    verify_lagrangian = run_cli(tmp_path, "verify-rule30-lagrangian", "--max-depth", "8")
    assert verify_lagrangian.returncode == 0, verify_lagrangian.stderr
    verify_lagrangian_payload = json.loads(verify_lagrangian.stdout)
    assert verify_lagrangian_payload["result"]["schema_status"] == "pass"

    trace = run_cli(tmp_path, "rule30-lagrangian-trace", "--max-depth", "64")
    assert trace.returncode == 0, trace.stderr
    trace_payload = json.loads(trace.stdout)
    assert trace_payload["result"]["schedule_summary"]["perfect_zero_action_schedule_count"] == 4

    verify_trace = run_cli(tmp_path, "verify-rule30-lagrangian-trace", "--max-depth", "64")
    assert verify_trace.returncode == 0, verify_trace.stderr
    verify_trace_payload = json.loads(verify_trace.stdout)
    assert verify_trace_payload["result"]["schema_status"] == "pass"

    scalar = run_cli(tmp_path, "rule30-mandelbrot-scalar", "--max-depth", "64")
    assert scalar.returncode == 0, scalar.stderr
    scalar_payload = json.loads(scalar.stdout)
    assert scalar_payload["result"]["boundary_scalar_summary"]["light_setting_count"] == 4
    assert scalar_payload["result"]["boundary_scalar_summary"]["prediction_accuracy"] == 1.0

    verify_scalar = run_cli(tmp_path, "verify-rule30-mandelbrot-scalar", "--max-depth", "64")
    assert verify_scalar.returncode == 0, verify_scalar.stderr
    verify_scalar_payload = json.loads(verify_scalar.stdout)
    assert verify_scalar_payload["result"]["schema_status"] == "pass"

    reduced = run_cli(tmp_path, "rule30-reduced-alphabet", "--max-depth", "128")
    assert reduced.returncode == 0, reduced.stderr
    reduced_payload = json.loads(reduced.stdout)
    assert reduced_payload["result"]["depth_equivalence_summary"]["accuracy"] == 1.0

    verify_reduced = run_cli(tmp_path, "verify-rule30-reduced-alphabet", "--max-depth", "128")
    assert verify_reduced.returncode == 0, verify_reduced.stderr
    verify_reduced_payload = json.loads(verify_reduced.stdout)
    assert verify_reduced_payload["result"]["schema_status"] == "pass"

    symmetry = run_cli(
        tmp_path,
        "rule30-symmetry-environment",
        "--max-depth",
        "128",
        "--max-period",
        "32",
    )
    assert symmetry.returncode == 0, symmetry.stderr
    symmetry_payload = json.loads(symmetry.stdout)
    assert symmetry_payload["result"]["representation_environment"]["tensor_product_space"]["token_dim"] == 6
    assert symmetry_payload["result"]["nonperiodicity_diagnostics"]["no_exact_center_bit_period_in_window"] is True

    verify_symmetry = run_cli(
        tmp_path,
        "verify-rule30-symmetry-environment",
        "--max-depth",
        "128",
        "--max-period",
        "32",
    )
    assert verify_symmetry.returncode == 0, verify_symmetry.stderr
    verify_symmetry_payload = json.loads(verify_symmetry.stdout)
    assert verify_symmetry_payload["result"]["schema_status"] == "pass"

    stack = run_cli(
        tmp_path,
        "rule30-physics-stack",
        "--max-depth",
        "128",
        "--max-period",
        "32",
        "--max-block",
        "6",
    )
    assert stack.returncode == 0, stack.stderr
    stack_payload = json.loads(stack.stdout)
    assert stack_payload["result"]["all_methods_unified"]["stage"] == 6
    assert stack_payload["result"]["all_methods_unified"]["cumulative_defect_count"] == 0

    verify_stack = run_cli(
        tmp_path,
        "verify-rule30-physics-stack",
        "--max-depth",
        "128",
        "--max-period",
        "32",
        "--max-block",
        "6",
    )
    assert verify_stack.returncode == 0, verify_stack.stderr
    verify_stack_payload = json.loads(verify_stack.stdout)
    assert verify_stack_payload["result"]["schema_status"] == "pass"

    coverage = run_cli(tmp_path, "rule30-n-coverage", "--max-depth", "512")
    assert coverage.returncode == 0, coverage.stderr
    coverage_payload = json.loads(coverage.stdout)
    assert coverage_payload["result"]["coverage_summary"]["unassigned_n_count"] == 0
    assert coverage_payload["result"]["coverage_summary"]["single_scalar_adjustment_suffices"] is True

    verify_coverage = run_cli(tmp_path, "verify-rule30-n-coverage", "--max-depth", "1024")
    assert verify_coverage.returncode == 0, verify_coverage.stderr
    verify_coverage_payload = json.loads(verify_coverage.stdout)
    assert verify_coverage_payload["result"]["schema_status"] == "pass"

    ribbon = run_cli(tmp_path, "rule30-readout-ribbon", "--max-depth", "512")
    assert ribbon.returncode == 0, ribbon.stderr
    ribbon_payload = json.loads(ribbon.stdout)
    assert ribbon_payload["result"]["machine_summary"]["feedback_defect_count"] == 0
    assert ribbon_payload["result"]["machine_summary"]["transition_conflict_count"] == 0

    verify_ribbon = run_cli(tmp_path, "verify-rule30-readout-ribbon", "--max-depth", "1024")
    assert verify_ribbon.returncode == 0, verify_ribbon.stderr
    verify_ribbon_payload = json.loads(verify_ribbon.stdout)
    assert verify_ribbon_payload["result"]["schema_status"] == "pass"

    hypervisor = run_cli(tmp_path, "rule30-dihedral-hypervisor", "--max-depth", "512")
    assert hypervisor.returncode == 0, hypervisor.stderr
    hypervisor_payload = json.loads(hypervisor.stdout)
    assert hypervisor_payload["result"]["hypervisor_summary"]["complete_block_count"] == 64
    assert hypervisor_payload["result"]["hypervisor_summary"]["partial_tail"] == 0

    verify_hypervisor = run_cli(tmp_path, "verify-rule30-dihedral-hypervisor", "--max-depth", "512")
    assert verify_hypervisor.returncode == 0, verify_hypervisor.stderr
    verify_hypervisor_payload = json.loads(verify_hypervisor.stdout)
    assert verify_hypervisor_payload["result"]["schema_status"] == "pass"

    extension = run_cli(
        tmp_path,
        "rule30-extension-tape",
        "--page-count",
        "2",
        "--page-size",
        "512",
    )
    assert extension.returncode == 0, extension.stderr
    extension_payload = json.loads(extension.stdout)
    assert extension_payload["result"]["extension_summary"]["page_boundary_defect_count"] == 0
    assert extension_payload["result"]["extension_summary"]["relative_table_stable_across_pages"] is True

    verify_extension = run_cli(
        tmp_path,
        "verify-rule30-extension-tape",
        "--page-count",
        "2",
        "--page-size",
        "512",
    )
    assert verify_extension.returncode == 0, verify_extension.stderr
    verify_extension_payload = json.loads(verify_extension.stdout)
    assert verify_extension_payload["result"]["schema_status"] == "pass"

    sheet = run_cli(tmp_path, "rule30-sheet-operator", "--page-count", "2", "--page-size", "128")
    assert sheet.returncode == 0, sheet.stderr
    sheet_payload = json.loads(sheet.stdout)
    assert sheet_payload["result"]["operator_summary"]["stable_across_pages"] is True

    verify_sheet = run_cli(
        tmp_path,
        "verify-rule30-sheet-operator",
        "--page-count",
        "2",
        "--page-size",
        "128",
    )
    assert verify_sheet.returncode == 0, verify_sheet.stderr
    verify_sheet_payload = json.loads(verify_sheet.stdout)
    assert verify_sheet_payload["result"]["schema_status"] == "pass"

    field = run_cli(tmp_path, "rule30-field-address", "257", "--page-size", "128")
    assert field.returncode == 0, field.stderr
    field_payload = json.loads(field.stdout)
    assert field_payload["result"]["coordinates"]["page_index"] == 2
    assert field_payload["result"]["address"]["prediction_defect"] == 0

    verify_field = run_cli(tmp_path, "verify-rule30-field-address", "257", "--page-size", "128")
    assert verify_field.returncode == 0, verify_field.stderr
    verify_field_payload = json.loads(verify_field.stdout)
    assert verify_field_payload["result"]["schema_status"] == "pass"

    trajectory = run_cli(tmp_path, "rule30-exit-trajectory", "257", "--page-size", "128")
    assert trajectory.returncode == 0, trajectory.stderr
    trajectory_payload = json.loads(trajectory.stdout)
    assert trajectory_payload["result"]["trajectory_definition"]["extra_field_search"] == 0
    assert trajectory_payload["result"]["exit"]["defect"] == 0

    verify_trajectory = run_cli(tmp_path, "verify-rule30-exit-trajectory", "257", "--page-size", "128")
    assert verify_trajectory.returncode == 0, verify_trajectory.stderr
    verify_trajectory_payload = json.loads(verify_trajectory.stdout)
    assert verify_trajectory_payload["result"]["schema_status"] == "pass"

    lift = run_cli(tmp_path, "rule30-sheet-lift", "257", "--page-size", "128")
    assert lift.returncode == 0, lift.stderr
    lift_payload = json.loads(lift.stdout)
    assert lift_payload["result"]["sheet"]["sheet_index_k"] == 257
    assert lift_payload["result"]["sheet"]["next_sheet_index"] == 258

    verify_lift = run_cli(tmp_path, "verify-rule30-sheet-lift", "257", "--page-size", "128")
    assert verify_lift.returncode == 0, verify_lift.stderr
    verify_lift_payload = json.loads(verify_lift.stdout)
    assert verify_lift_payload["result"]["schema_status"] == "pass"

    resolution = run_cli(tmp_path, "rule30-julia-resolution", "257", "--page-size", "128")
    assert resolution.returncode == 0, resolution.stderr
    resolution_payload = json.loads(resolution.stdout)
    assert resolution_payload["result"]["resolved_bit"] == resolution_payload["result"]["center_bit"]
    assert resolution_payload["result"]["sheet_lift"]["sheet_index_k"] == 257

    verify_resolution = run_cli(tmp_path, "verify-rule30-julia-resolution", "257", "--page-size", "128")
    assert verify_resolution.returncode == 0, verify_resolution.stderr
    verify_resolution_payload = json.loads(verify_resolution.stdout)
    assert verify_resolution_payload["result"]["schema_status"] == "pass"

    torsor = run_cli(tmp_path, "rule30-torsor-functor", "257", "--page-size", "128")
    assert torsor.returncode == 0, torsor.stderr
    torsor_payload = json.loads(torsor.stdout)
    assert torsor_payload["result"]["torsor"]["lifted_sheet_id"] == resolution_payload["result"]["sheet_lift"]["lifted_sheet_id"]
    assert torsor_payload["result"]["bitorsor_actions"]["compatibility_defect"] == 0
    assert torsor_payload["result"]["functor_stack"]["two_functor"]["preserves_2_cells"] is True

    verify_torsor = run_cli(tmp_path, "verify-rule30-torsor-functor", "257", "--page-size", "128")
    assert verify_torsor.returncode == 0, verify_torsor.stderr
    verify_torsor_payload = json.loads(verify_torsor.stdout)
    assert verify_torsor_payload["result"]["schema_status"] == "pass"

    spinor = run_cli(tmp_path, "rule30-spinor-oloid", "--max-depth", "64")
    assert spinor.returncode == 0, spinor.stderr
    spinor_payload = json.loads(spinor.stdout)
    assert spinor_payload["result"]["model_id"] == "rule30_spinor_oloid_model_v0_1"

    verify_spinor = run_cli(tmp_path, "verify-rule30-spinor-oloid", "--max-depth", "64")
    assert verify_spinor.returncode == 0, verify_spinor.stderr
    verify_spinor_payload = json.loads(verify_spinor.stdout)
    assert verify_spinor_payload["result"]["status"].startswith("pass")

    oloid_args = (
        "--parameterization",
        "phi",
        "--pattern",
        "alternating_xyz",
        "--axis-angle",
        "0.5235987755982988",
        "--shell-axis",
        "y",
        "--side-axis",
        "z",
        "--shell-offset",
        "-0.125",
    )
    winding = run_cli(tmp_path, "rule30-oloid-winding", "17", *oloid_args)
    assert winding.returncode == 0, winding.stderr
    winding_payload = json.loads(winding.stdout)
    assert winding_payload["result"]["model_id"] == "rule30_oloid_winding_from_n_v0_1"

    antipode = run_cli(tmp_path, "rule30-oloid-antipode", "17", *oloid_args)
    assert antipode.returncode == 0, antipode.stderr
    antipode_payload = json.loads(antipode.stdout)
    assert antipode_payload["result"]["model_id"] == "rule30_oloid_antipodal_winding_v0_1"

    scan = run_cli(tmp_path, "rule30-oloid-scan", "--max-depth", "32")
    assert scan.returncode == 0, scan.stderr
    scan_payload = json.loads(scan.stdout)
    assert scan_payload["result"]["model_id"] == "rule30_oloid_parameterization_scan_v0_1"

    verify_winding = run_cli(tmp_path, "verify-rule30-oloid-winding", "--max-depth", "32", *oloid_args)
    assert verify_winding.returncode == 0, verify_winding.stderr
    verify_winding_payload = json.loads(verify_winding.stdout)
    assert verify_winding_payload["result"]["model_id"] == "rule30_oloid_winding_verifier_v0_1"

    verify_antipode = run_cli(tmp_path, "verify-rule30-oloid-antipode", "--max-depth", "32", *oloid_args)
    assert verify_antipode.returncode == 0, verify_antipode.stderr
    verify_antipode_payload = json.loads(verify_antipode.stdout)
    assert verify_antipode_payload["result"]["status"].startswith("pass")

    winding_number = run_cli(tmp_path, "rule30-winding-number", "--max-depth", "64")
    assert winding_number.returncode == 0, winding_number.stderr
    winding_number_payload = json.loads(winding_number.stdout)
    assert winding_number_payload["result"]["complexity_proof"]["claim_status"] == "BOUNDED_TRACE_WITNESS"

    verify_winding_number = run_cli(tmp_path, "verify-rule30-winding-number", "--max-depth", "64")
    assert verify_winding_number.returncode == 0, verify_winding_number.stderr
    verify_winding_number_payload = json.loads(verify_winding_number.stdout)
    assert verify_winding_number_payload["result"]["status"] == "pass_with_open_gaps"

    nth = run_cli(tmp_path, "rule30-nth-bit", "129", "--page-size", "128")
    assert nth.returncode == 0, nth.stderr
    nth_payload = json.loads(nth.stdout)
    assert nth_payload["result"]["computed_witness"]["defect"] == 0
    assert nth_payload["result"]["julia_resolution"]["defect"] == 0
    assert nth_payload["result"]["torsor_functor"]["compatibility_defect"] == 0

    verify_nth = run_cli(tmp_path, "verify-rule30-nth-bit", "129", "--page-size", "128")
    assert verify_nth.returncode == 0, verify_nth.stderr
    verify_nth_payload = json.loads(verify_nth.stdout)
    assert verify_nth_payload["result"]["schema_status"] == "pass"
