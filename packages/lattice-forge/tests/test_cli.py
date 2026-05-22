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
