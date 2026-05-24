from __future__ import annotations

import sqlite3
from math import log2
from pathlib import Path

import pytest

from lattice_forge import Forge, SeedStore


def test_seed_integrity_and_counts():
    seed = SeedStore.packaged()

    assert seed.integrity_check() == "ok"
    summary = seed.summary()
    assert summary["object_registry"] >= 61
    assert summary["exact_vectors"] >= 12578
    assert summary["morphism_registry"] >= 66
    assert summary["terminal_24d_forms"] == 24
    assert summary["path_metrics"] >= 53
    assert summary["morphism_witness_registry"] >= 3
    assert summary["nsl_boundary_registry"] >= 53
    assert summary["closure_obstruction_registry"] >= 53


def test_forge_creates_overlay_and_records_queries(tmp_path: Path):
    forge = Forge.open(tmp_path)

    assert (tmp_path / ".lattice_forge" / "overlay.sqlite").exists()
    result = forge.can_close("G2", "Niemeier:A2^12")

    assert result["answer"] == "yes_with_template_glue"
    assert result["evidence_level"] == "template"
    assert result["result"]["closure"]["answer"] == "yes_with_template_glue"
    assert forge.latest_receipts(1)
    assert forge.latest_events(1)


def test_terminal_tree_generates_canonical_route_and_residue(tmp_path: Path):
    forge = Forge.open(tmp_path)
    payload = forge.terminal_tree("A2^12")
    tree = payload["result"]

    assert tree["terminal_id"] == "Niemeier:A2^12"
    assert tree["status"] == "generated_canonical_composition_tree"
    assert tree["composition_model"] == "component_action_tree_with_emergent_residue"
    assert tree["route_uniqueness"] == "single_canonical_route_after_component_ordering_and_orbit_quotient"
    assert len(tree["composition_route"]) == 13
    assert len(tree["action_edges"]) == 12
    assert tree["composition_route"][-1]["label"] == "12xA2"
    assert tree["composition_route"][-1]["rank"] == 24
    assert tree["closure_residue"]["root_lattice_determinant"] == 531441
    assert tree["closure_residue"]["required_overlattice_index"] == 729
    assert tree["closure_residue"]["status"] == "residue_closes_by_required_index"
    assert tree["ambient_dimension"] == 24
    assert tree["root_rank"] == 24
    assert tree["component_action_count"] == 12
    assert tree["residue_status"] == "residue_closes_by_required_index"
    assert tree["involution_tree"]["compact_edge_count"] > 0
    assert tree["compact_involution_count"] == tree["involution_tree"]["compact_edge_count"]
    assert tree["legacy_glue_records"]


def test_terminal_trees_generate_for_all_24_and_verify(tmp_path: Path):
    forge = Forge.open(tmp_path)
    payload = forge.terminal_trees()
    terminals = payload["result"]["terminals"]

    assert payload["result"]["terminal_count"] == 24
    assert len(terminals) == 24
    by_id = {row["terminal_id"]: row for row in terminals}
    assert by_id["Niemeier:Leech"]["ambient_dimension"] == 24
    assert by_id["Niemeier:Leech"]["root_rank"] == 0
    assert by_id["Niemeier:Leech"]["component_action_count"] == 0
    assert by_id["Niemeier:Leech"]["evidence_level"] == "pending_import"

    for terminal_id, row in by_id.items():
        assert row["ambient_dimension"] == 24
        if terminal_id == "Niemeier:Leech":
            continue
        assert row["root_rank"] == 24
        assert row["component_action_count"] > 0
        assert row["compact_involution_count"] > 0
        assert row["residue_status"] == "residue_closes_by_required_index"

    verify = forge.verify_terminal_trees()
    assert verify["result"]["status"] == "pass"
    assert verify["result"]["terminal_count"] == 24
    assert not verify["result"]["errors"]


def test_terminal_aliases_resolve_to_same_tree(tmp_path: Path):
    forge = Forge.open(tmp_path)
    by_id = forge.terminal_tree("Niemeier:A11_D7_E6")["result"]
    by_name = forge.terminal_tree("A11_D7_E6")["result"]
    by_root_system = forge.terminal_tree("A11 D7 E6")["result"]

    assert by_id["terminal_id"] == by_name["terminal_id"] == by_root_system["terminal_id"]
    assert by_id["composition_route"][-1]["state_id"] == by_name["composition_route"][-1]["state_id"]
    assert by_name["composition_route"][-1]["state_id"] == by_root_system["composition_route"][-1]["state_id"]


def test_can_close_embeds_terminal_tree_for_24d_target(tmp_path: Path):
    forge = Forge.open(tmp_path)
    result = forge.can_close("G2", "A2^12")
    closure = result["result"]["closure"]

    assert closure["requested_target"] == "A2^12"
    assert closure["target"] == "Niemeier:A2^12"
    assert closure["closure_model"] == "canonical_terminal_composition_tree"
    assert closure["composition_residue_status"] == "residue_closes_by_required_index"
    assert result["result"]["terminal_tree"]["composition_route"][-1]["label"] == "12xA2"


def test_morphonics_v02_model_is_executable_ledger(tmp_path: Path):
    forge = Forge.open(tmp_path)
    payload = forge.morphonics_model()
    model = payload["result"]

    assert model["model_id"] == "MSCF:morphonics_unified_formal_model_v0_2"
    assert model["lattice_forge_check"]["test_status"] == "pass"
    assert len(model["morphons"]) >= 5
    assert len(model["claims"]) >= 10
    assert any(row["status"] == "OVERCLAIM" for row in model["claims"])
    assert any(row["morphon_id"] == "morphon:niemeier_terminal_tree" for row in model["morphons"])

    verify = forge.verify_morphonics()
    assert verify["result"]["schema_status"] == "pass"
    assert verify["result"]["status"] == "pass_with_open_gaps"
    assert verify["result"]["open_gap_count"] >= 3
    assert verify["result"]["lattice_forge_check"]["terminal_count"] == 24
    assert not verify["result"]["errors"]
    assert all(row["status"] == "pass" for row in verify["result"]["closure_tests"])


def test_rule30_hardened_morphon_preserves_canonical_projection(tmp_path: Path):
    forge = Forge.open(tmp_path)
    payload = forge.rule30_morphon(max_depth=7, sample_count=256)
    model = payload["result"]

    assert model["model_id"] == "rule30_morphon_hardened_v0_6"
    assert model["status"] == "pass_with_open_gaps"
    assert model["summary"]["canonical_depths_passed"] == 7
    assert model["summary"]["final_full_monomials"] == 4852
    assert model["summary"]["final_cumulative_view_records"] < 30
    assert model["summary"]["final_view_growth_vs_anf"] < 0.01
    assert model["open_gaps"]

    for row in model["depths"]:
        assert row["exact_anf_oracle"]["oracle_role"] == "bounded_verification_only"
        assert row["recursive_view_projection"]["canonical_single_seed_correct"] is True
        assert row["hardened_beam_candidate"]["canonical_single_seed_correct"] is True

    verify = forge.verify_rule30(max_depth=7, sample_count=256)
    assert verify["result"]["schema_status"] == "pass"
    assert verify["result"]["status"] == "pass_with_open_gaps"
    assert verify["result"]["open_gap_count"] >= 3
    assert any("arbitrary-row" in warning for warning in verify["result"]["warnings"])


def test_rule30_vignette_algebra_closes_zero_preserving_space(tmp_path: Path):
    forge = Forge.open(tmp_path)
    payload = forge.rule30_vignettes(max_order=4)
    algebra = payload["result"]

    assert algebra["primitive_vignette_count"] == 24
    assert algebra["unique_primitive_signature_count"] == 3
    assert algebra["unique_function_count"] == 128
    assert algebra["coverage_fraction"] == 0.5
    assert algebra["zero_preserving_coverage_fraction"] == 1.0
    assert algebra["saturated_zero_preserving_space"] is True
    assert algebra["unique_count_by_order"][1] == 3
    assert algebra["unique_count_by_order"][4] == 128
    assert len(algebra["primitive_orbits"]) == 3
    assert algebra["decoder_candidate_pool"]

    verify = forge.verify_rule30_vignettes(max_order=4)
    assert verify["result"]["schema_status"] == "pass"
    assert verify["result"]["status"] == "pass_with_open_gaps"
    assert verify["result"]["summary"]["saturated_zero_preserving_space"] is True


def test_rule30_moving_frame_filters_static_vignette_space(tmp_path: Path):
    forge = Forge.open(tmp_path)
    payload = forge.rule30_moving_frame(max_depth=12, max_order=4)
    moving = payload["result"]
    summary = moving["moving_space_summary"]

    assert moving["model_id"] == "rule30_moving_beam_frame_v0_1"
    assert moving["resolver_law"]["LC^LR"] == "CR"
    assert moving["resolver_law"]["LC^CR"] == "LR"
    assert moving["resolver_law"]["LR^CR"] == "LC"
    assert moving["static_algebra_summary"]["unique_function_count"] == 128
    assert summary["candidate_count"] == 56
    assert summary["balanced_candidate_count"] == 28
    assert summary["schedule_count"] == 24
    assert summary["schedule_orbit_count"] == 6
    assert summary["locked_visible_pair_orbit_count"] == 3
    assert summary["full_cycle_orbit_count"] == 3
    assert summary["space_reduction_vs_static"] < 0.5
    assert moving["balanced_locator_candidates"]

    verify = forge.verify_rule30_moving_frame(max_depth=12, max_order=4)
    assert verify["result"]["schema_status"] == "pass"
    assert verify["result"]["status"] == "pass_with_open_gaps"
    assert verify["result"]["summary"]["candidate_count"] == 56


def test_rule30_color_chirality_cipher_closes_six_token_alphabet(tmp_path: Path):
    forge = Forge.open(tmp_path)
    payload = forge.rule30_color_chirality(max_depth=12, max_order=4)
    cipher = payload["result"]
    coverage = cipher["primitive_token_coverage"]
    summary = cipher["closure_summary"]

    assert cipher["model_id"] == "rule30_color_chirality_cipher_v0_1"
    assert coverage["token_count"] == 6
    assert coverage["expected_token_count"] == 6
    assert coverage["token_counts"] == {
        "CR+": 4,
        "CR-": 4,
        "LC+": 4,
        "LC-": 4,
        "LR+": 4,
        "LR-": 4,
    }
    assert cipher["laws"]["color_resolver"]["LC^LR"] == "CR"
    assert cipher["laws"]["color_resolver"]["LC^CR"] == "LR"
    assert cipher["laws"]["color_resolver"]["LR^CR"] == "LC"
    assert summary["rotation_closed"] is True
    assert summary["reflection_closed"] is True
    assert summary["composition_closed"] is True
    assert summary["composition_rows"] == 36
    assert summary["distinct_color_compositions"] == 24
    assert summary["moving_schedule_count"] == 24
    assert summary["chiral_orbit_count"] == 24
    assert summary["full_color_cycle_orbit_count"] == 12
    assert summary["chirality_flip_orbit_count"] == 24
    assert summary["moving_candidate_count"] == 56
    assert summary["balanced_locator_candidate_count"] == 28

    zero_rows = [row for row in cipher["composition_table"] if row["output"] == "ZERO"]
    assert len(zero_rows) == 12
    assert {row["reflect_LR"] for row in cipher["reflection_table"]} == {
        "CR+",
        "CR-",
        "LC+",
        "LC-",
        "LR+",
        "LR-",
    }

    verify = forge.verify_rule30_color_chirality(max_depth=12, max_order=4)
    assert verify["result"]["schema_status"] == "pass"
    assert verify["result"]["status"] == "pass_with_open_gaps"
    assert verify["result"]["summary"]["token_count"] == 6


def test_rule30_discrete_lagrangian_encodes_zero_action_rule_updates(tmp_path: Path):
    forge = Forge.open(tmp_path)
    payload = forge.rule30_lagrangian(max_depth=12, max_order=4)
    model = payload["result"]
    summary = model["action_summary"]
    nsl = model["nsl_accounting"]

    assert model["model_id"] == "rule30_discrete_lagrangian_nsl_v0_1"
    assert model["lagrangian"]["evidence_status"] == "exact_finite_discrete_action"
    assert summary["plaquette_count"] == 96
    assert summary["legal_zero_action_plaquette_count"] == 48
    assert summary["positive_action_plaquette_count"] == 48
    assert summary["action_histogram"] == {0: 48, 1: 48}
    assert summary["action_zero_is_legal_rule30_update"] is True
    assert summary["noether_defect_total"] == 0
    assert round(nsl["token_bits"], 12) == round(2.584962500721156, 12)
    assert round(nsl["unresolved_bits_full_state_to_token"], 12) == round(0.4150374992788439, 12)
    assert nsl["accounting_status"] == "closed_with_named_boundary_scalar"
    assert {row["status"] for row in model["noether_currents"]} <= {
        "closed",
        "conserved_on_interior_or_periodic_windows",
    }

    verify = forge.verify_rule30_lagrangian(max_depth=12, max_order=4)
    assert verify["result"]["schema_status"] == "pass"
    assert verify["result"]["status"] == "pass_with_open_gaps"
    assert verify["result"]["summary"]["action_zero_is_legal_rule30_update"] is True


def test_rule30_lagrangian_depth_trace_finds_locked_cr_zero_action_schedules(tmp_path: Path):
    forge = Forge.open(tmp_path)
    payload = forge.rule30_lagrangian_depth_trace(max_depth=256, max_order=4)
    trace = payload["result"]
    depth = trace["depth_summary"]
    schedules = trace["schedule_summary"]

    assert trace["model_id"] == "rule30_lagrangian_depth_trace_v0_1"
    assert depth["depth_count"] == 256
    assert depth["all_depths_have_zero_action_token"] is True
    assert depth["compatible_token_count_histogram"] == {2: 36, 4: 64, 6: 156}
    assert depth["center_bit_histogram"] == {0: 121, 1: 135}
    assert round(depth["mean_selector_bits_with_local_state"], 12) == round(2.2158365238769546, 12)
    assert schedules["schedule_count"] == 24
    assert schedules["perfect_zero_action_schedule_count"] == 4
    assert schedules["perfect_locked_colors"] == ["CR"]
    assert schedules["perfect_schedules_are_locked_CR"] is True
    assert schedules["best_action_defect_sum"] == 0
    assert schedules["worst_action_defect_sum"] == 70
    assert all(row["locked_color"] == "CR" for row in trace["perfect_schedules"])
    assert all(row["accuracy"] == 1.0 for row in trace["perfect_schedules"])

    verify = forge.verify_rule30_lagrangian_depth_trace(max_depth=256, max_order=4)
    assert verify["result"]["schema_status"] == "pass"
    assert verify["result"]["status"] == "pass_with_open_gaps"
    assert verify["result"]["schedule_summary"]["perfect_zero_action_schedule_count"] == 4


def test_rule30_mandelbrot_scalar_uses_four_signed_light_settings(tmp_path: Path):
    forge = Forge.open(tmp_path)
    payload = forge.rule30_mandelbrot_scalar(max_depth=256, max_order=4)
    scalar = payload["result"]
    summary = scalar["boundary_scalar_summary"]

    assert scalar["model_id"] == "rule30_mandelbrot_boundary_scalar_v0_1"
    assert summary["representative_count"] == 4
    assert summary["light_setting_count"] == 4
    assert summary["exit_lookup_rows"] == 32
    assert summary["ambiguous_exit_key_count"] == 0
    assert summary["total_depth_predictions"] == 1024
    assert summary["correct_depth_predictions"] == 1024
    assert summary["prediction_accuracy"] == 1.0
    assert summary["all_representatives_exact"] is True
    assert len(scalar["light_settings"]) == 4
    for row in scalar["light_settings"]:
        assert row["ast_visible_rule"] == "CR"
        assert {row["positive_projection_term"], row["negative_projection_term"]} == {"LC", "LR"}
        assert row["alignment_status"] == "forward_backward_and_left_right_aligned"
        assert row["resolution_status"] == "one_signed_resolution_of_two_side_terms_under_locked_CR_AST"
    assert scalar["scalar_definition"]["scalar_functor"]["homogenization_role"]
    assert scalar["fourier_summary"]["top_power_bins"]

    verify = forge.verify_rule30_mandelbrot_scalar(max_depth=256, max_order=4)
    assert verify["result"]["schema_status"] == "pass"
    assert verify["result"]["status"] == "pass_with_open_gaps"
    assert verify["result"]["summary"]["prediction_accuracy"] == 1.0


def test_rule30_reduced_alphabet_catalog_reproduces_rule_without_boolean_catalog(tmp_path: Path):
    forge = Forge.open(tmp_path)
    payload = forge.rule30_reduced_alphabet(max_depth=1024, max_order=4)
    model = payload["result"]
    local = model["local_equivalence_summary"]
    depth = model["depth_equivalence_summary"]
    invariant = model["invariant_exchange_summary"]
    catalog = model["catalog"]

    assert model["model_id"] == "rule30_reduced_alphabet_rule_catalog_v0_1"
    assert len(catalog["alphabet"]) == 6
    assert "128-function vignette catalog" in catalog["excluded_rule_sources"]
    assert local["local_rows"] == 32
    assert local["correct_rows"] == 32
    assert local["accuracy"] == 1.0
    assert depth["depth_count"] == 1024
    assert depth["total_predictions"] == 4096
    assert depth["correct_predictions"] == 4096
    assert depth["accuracy"] == 1.0
    assert invariant["pair_product_only_sufficient"] is False
    assert invariant["ambiguous_pair_product_classes"] == {"000": [0, 1]}
    assert invariant["scalar_shell_resolves_pair_product_ambiguity"] is True
    assert invariant["noether_defect_total"] == 0

    verify = forge.verify_rule30_reduced_alphabet(max_depth=1024, max_order=4)
    assert verify["result"]["schema_status"] == "pass"
    assert verify["result"]["status"] == "pass_with_open_gaps"
    assert verify["result"]["depth_equivalence_summary"]["accuracy"] == 1.0


def test_rule30_symmetry_environment_adds_finite_u1_su2_su3_layer(tmp_path: Path):
    forge = Forge.open(tmp_path)
    payload = forge.rule30_symmetry_environment(max_depth=256, max_period=64, max_order=4)
    model = payload["result"]
    env = model["representation_environment"]
    tensor = env["tensor_product_space"]
    nsl = model["nsl_accounting"]
    nonperiodic = model["nonperiodicity_diagnostics"]

    assert model["model_id"] == "rule30_symmetry_environment_s1_su2_su3_v0_1"
    assert env["u1_s1_phase"]["phase_count"] == 4
    assert tensor["color_dim"] == 3
    assert tensor["chirality_dim"] == 2
    assert tensor["token_dim"] == 6
    assert len(tensor["tokens"]) == 6
    assert model["reduced_catalog_summary"]["depth_accuracy"] == 1.0
    assert nsl["noether_defect_total"] == 0
    assert nsl["shannon"]["reduced_catalog_token_bits"] == pytest.approx(log2(6))
    assert nonperiodic["no_exact_center_bit_period_in_window"] is True
    assert nonperiodic["no_exact_reduced_signature_period_in_window"] is True
    assert sum(nonperiodic["bit_counts"].values()) == 256
    assert nonperiodic["fourier_top_power_bins"]

    verify = forge.verify_rule30_symmetry_environment(max_depth=256, max_period=64, max_order=4)
    assert verify["result"]["schema_status"] == "pass"
    assert verify["result"]["status"] == "pass_with_open_gaps"
    assert verify["result"]["representation_summary"]["token_dim"] == 6


def test_rule30_physics_method_stack_tests_solo_and_cumulative_methods(tmp_path: Path):
    forge = Forge.open(tmp_path)
    payload = forge.rule30_physics_method_stack(max_depth=256, max_period=64, max_order=4, max_block=8)
    model = payload["result"]

    assert model["model_id"] == "rule30_physics_method_stack_v0_1"
    assert model["method_order"] == [
        "gauge_normalization",
        "debruijn_transfer_operator",
        "holonomy_closed_loop",
        "correlation_functions",
        "ecc_syndrome_decoder",
        "renormalization_coarse_graining",
    ]
    assert len(model["solo_tests"]) == 6
    assert all(row["solo_status"] == "pass" for row in model["solo_tests"])
    assert model["all_methods_unified"]["stage"] == 6
    assert model["all_methods_unified"]["status"] == "pass"
    assert model["all_methods_unified"]["cumulative_defect_count"] == 0

    by_id = {row["method_id"]: row for row in model["solo_tests"]}
    assert by_id["gauge_normalization"]["representative_reduction_ratio"] == pytest.approx(0.25)
    assert by_id["debruijn_transfer_operator"]["node_count"] == 4
    assert by_id["debruijn_transfer_operator"]["edge_count"] == 8
    assert by_id["holonomy_closed_loop"]["defect_count"] == 0
    assert by_id["correlation_functions"]["top_autocorrelation_lags"]
    assert by_id["ecc_syndrome_decoder"]["pair_product_only_ambiguities"] == {"000": [0, 1]}
    assert by_id["ecc_syndrome_decoder"]["ambiguous_syndromes"] == {}
    assert by_id["renormalization_coarse_graining"]["block_rows"][-1]["block_width"] == 8

    verify = forge.verify_rule30_physics_method_stack(max_depth=256, max_period=64, max_order=4, max_block=8)
    assert verify["result"]["schema_status"] == "pass"
    assert verify["result"]["status"] == "pass_with_open_gaps"
    assert verify["result"]["all_methods_unified"]["cumulative_defect_count"] == 0


def test_rule30_whole_integer_n_scalar_coverage_has_no_unassigned_depths(tmp_path: Path):
    forge = Forge.open(tmp_path)
    payload = forge.rule30_whole_integer_n_coverage(max_depth=1024, max_order=4)
    model = payload["result"]
    summary = model["coverage_summary"]

    assert model["model_id"] == "rule30_whole_integer_n_scalar_coverage_v0_1"
    assert summary["tested_whole_integer_n"] == 1024
    assert summary["unassigned_n_count"] == 0
    assert summary["readout_defect_count"] == 0
    assert summary["single_scalar_adjustment_suffices"] is True
    assert summary["local_scalar_syndrome_count"] == 8
    assert summary["pair_product_only_ambiguities"] == {"000": [0, 1]}
    assert summary["depth_accuracy"] == 1.0
    assert model["terms_not_fitting"][0]["label"] == "NO_TESTED_WHOLE_N_UNASSIGNED"
    assert model["terms_not_fitting"][1]["label"] == "PAIR_PRODUCTS_ALONE_STILL_NOT_ENOUGH"

    verify = forge.verify_rule30_whole_integer_n_coverage(max_depth=1024, max_order=4)
    assert verify["result"]["schema_status"] == "pass"
    assert verify["result"]["status"] == "pass_with_open_gaps"
    assert verify["result"]["coverage_summary"]["unassigned_n_count"] == 0


def test_rule30_readout_ribbon_machine_closes_feedback_and_polarity(tmp_path: Path):
    forge = Forge.open(tmp_path)
    payload = forge.rule30_readout_ribbon_machine(max_depth=1024, max_order=4)
    model = payload["result"]
    summary = model["machine_summary"]
    computability = model["computability_status"]

    assert model["model_id"] == "rule30_readout_ribbon_machine_v0_1"
    assert summary["ribbon_length"] == 1024
    assert summary["feedback_defect_count"] == 0
    assert summary["transition_conflict_count"] == 0
    assert summary["coverage_unassigned_n_count"] == 0
    assert summary["coverage_readout_defect_count"] == 0
    assert summary["single_scalar_adjustment_suffices"] is True
    assert summary["mass_action_proxy_average"] > 0.0
    assert computability["readout_ribbon_machine_form"] == "pass"
    assert computability["formal_turing_completeness"] == "not_claimed_without_universality_proof"

    verify = forge.verify_rule30_readout_ribbon_machine(max_depth=1024, max_order=4)
    assert verify["result"]["schema_status"] == "pass"
    assert verify["result"]["status"] == "pass_with_open_gaps"


def test_rule30_dihedral_block_hypervisor_groups_complete_eight_step_blocks(tmp_path: Path):
    forge = Forge.open(tmp_path)
    payload = forge.rule30_dihedral_block_hypervisor(max_depth=4096, block_size=8, max_order=4)
    model = payload["result"]
    summary = model["hypervisor_summary"]

    assert model["model_id"] == "rule30_dihedral_block_hypervisor_v0_1"
    assert summary["complete_block_count"] == 512
    assert summary["partial_tail"] == 0
    assert summary["expected_complete_blocks_at_4096"] == 512
    assert summary["block_conflict_count"] == 0
    assert summary["ribbon_feedback_defect_count"] == 0
    assert summary["ribbon_transition_conflict_count"] == 0
    assert summary["unique_block_words"] >= 128
    assert len(model["phase_class_summary"]) == 8
    assert all(row["count"] == 512 for row in model["phase_class_summary"])

    verify = forge.verify_rule30_dihedral_block_hypervisor(max_depth=4096, block_size=8, max_order=4)
    assert verify["result"]["schema_status"] == "pass"
    assert verify["result"]["status"] == "pass_with_open_gaps"
    assert verify["result"]["hypervisor_summary"]["complete_block_count"] == 512


def test_rule30_hypervisor_extension_tape_chains_pages_with_stable_relative_table(tmp_path: Path):
    forge = Forge.open(tmp_path)
    payload = forge.rule30_hypervisor_extension_tape(page_count=2, page_size=1024, block_size=8, max_order=4)
    model = payload["result"]
    summary = model["extension_summary"]

    assert model["model_id"] == "rule30_hypervisor_extension_tape_v0_1"
    assert summary["page_count"] == 2
    assert summary["page_size"] == 1024
    assert summary["blocks_per_page"] == 128
    assert summary["total_blocks"] == 256
    assert summary["page_boundary_defect_count"] == 0
    assert summary["relative_table_hash_count"] == 1
    assert summary["relative_table_stable_across_pages"] is True
    assert summary["ribbon_feedback_defect_count"] == 0
    assert summary["ribbon_transition_conflict_count"] == 0
    assert summary["all_pages_complete"] is True

    verify = forge.verify_rule30_hypervisor_extension_tape(page_count=2, page_size=1024, block_size=8, max_order=4)
    assert verify["result"]["schema_status"] == "pass"
    assert verify["result"]["status"] == "pass_with_open_gaps"


def test_rule30_sheet_operator_and_nth_bit_expression_are_formulaic_surfaces(tmp_path: Path):
    forge = Forge.open(tmp_path)
    sheet_payload = forge.rule30_sheet_operator(page_count=2, page_size=128, block_size=8, max_order=4)
    sheet = sheet_payload["result"]
    summary = sheet["operator_summary"]

    assert sheet["model_id"] == "rule30_sheet_operator_v0_1"
    assert summary["state_count"] > 0
    assert summary["transition_conflict_count"] == 0
    assert summary["page_hash_count"] == 1
    assert summary["stable_across_pages"] is True
    assert sheet["power_law"]["same_operator_reused"] is True

    sheet_verify = forge.verify_rule30_sheet_operator(page_count=2, page_size=128, block_size=8, max_order=4)
    assert sheet_verify["result"]["schema_status"] == "pass"
    assert sheet_verify["result"]["status"] == "pass_with_open_gaps"

    nth_payload = forge.rule30_nth_bit_expression(129, page_size=128, block_size=8, max_order=4)
    nth = nth_payload["result"]
    witness = nth["computed_witness"]

    assert nth["model_id"] == "rule30_nth_bit_expression_v0_1"
    assert nth["expression_status"] == "EXPRESSIBLE_AND_EXECUTABLE_IN_REDUCED_SCALAR_LANGUAGE"
    assert nth["nth_bit_formula"]["depth_decomposition"]["page_index"] == 1
    assert witness["defect"] == 0
    assert witness["sheet_table_bit"] == witness["center_bit"]
    assert witness["scalar_emitted_bit"] == witness["center_bit"]

    nth_verify = forge.verify_rule30_nth_bit_expression(129, page_size=128, block_size=8, max_order=4)
    assert nth_verify["result"]["schema_status"] == "pass"
    assert nth_verify["result"]["status"] == "pass_with_open_gaps"


def test_rule30_julia_resolution_uses_field_address_and_lifted_sheets(tmp_path: Path):
    forge = Forge.open(tmp_path)
    n = 257

    address = forge.rule30_mandelbrot_field_address(n, page_size=128, block_size=8, max_order=4)["result"]
    assert address["model_id"] == "rule30_mandelbrot_field_address_v0_1"
    assert address["address"]["prediction_defect"] == 0
    assert address["coordinates"]["page_index"] == 2

    trajectory = forge.rule30_exit_trajectory(n, page_size=128, block_size=8, max_order=4)["result"]
    assert trajectory["model_id"] == "rule30_exit_trajectory_v0_1"
    assert trajectory["exit"]["defect"] == 0
    assert trajectory["trajectory_definition"]["extra_field_search"] == 0

    lift = forge.rule30_sheet_lift(n, page_size=128, block_size=8, max_order=4)["result"]
    assert lift["model_id"] == "rule30_sheet_lift_v0_1"
    assert lift["sheet"]["sheet_index_k"] == n
    assert lift["sheet"]["next_sheet_index"] == n + 1
    assert lift["sheet"]["primitive_sheet"] in {"J_closed_0", "J_open_1"}
    assert lift["sheet"]["defect"] == 0

    resolution = forge.rule30_julia_resolution(n, page_size=128, block_size=8, max_order=4)["result"]
    assert resolution["model_id"] == "rule30_julia_resolution_v0_1"
    assert resolution["defect"] == 0
    assert resolution["resolved_bit"] == resolution["center_bit"]
    assert resolution["sheet_lift"]["sheet_index_k"] == n
    assert resolution["grid_resolution"]["grid_square_id"].startswith(f"sheet={n}|")

    verify = forge.verify_rule30_julia_resolution(n, page_size=128, block_size=8, max_order=4)
    assert verify["result"]["schema_status"] == "pass"
    assert verify["result"]["status"] == "pass_with_open_gaps"

    torsor = forge.rule30_torsor_functor_term(n, page_size=128, block_size=8, max_order=4)["result"]
    assert torsor["model_id"] == "rule30_torsor_functor_term_v0_1"
    assert torsor["torsor"]["base_fiber"] == ["J_closed_0", "J_open_1"]
    assert torsor["torsor"]["lifted_sheet_id"] == resolution["sheet_lift"]["lifted_sheet_id"]
    assert torsor["bitorsor_actions"]["compatibility_defect"] == 0
    assert torsor["functor_stack"]["naturality_defect"] == 0
    assert torsor["functor_stack"]["two_functor"]["preserves_2_cells"] is True
    assert torsor["spin_state"]["spin_bit"] in {0, 1}

    torsor_verify = forge.verify_rule30_torsor_functor_term(n, page_size=128, block_size=8, max_order=4)
    assert torsor_verify["result"]["schema_status"] == "pass"
    assert torsor_verify["result"]["status"] == "pass_with_open_gaps"

    nth = forge.rule30_nth_bit_expression(n, page_size=128, block_size=8, max_order=4)["result"]
    assert nth["julia_resolution"]["lifted_sheet_id"] == resolution["sheet_lift"]["lifted_sheet_id"]
    assert nth["julia_resolution"]["grid_square_id"] == resolution["grid_resolution"]["grid_square_id"]
    assert nth["torsor_functor"]["torsor_hash"] == torsor["torsor"]["torsor_hash"]
    assert nth["torsor_functor"]["compatibility_defect"] == 0


def test_rule30_oloid_scan_result_can_be_verified_as_config():
    from lattice_forge.rule30 import (
        rule30_oloid_antipodal_winding,
        rule30_oloid_parameterization_scan,
        verify_rule30_oloid_antipodal_winding,
        verify_rule30_oloid_winding_from_n,
    )

    scan = rule30_oloid_parameterization_scan(max_depth=32)
    assert scan["model_id"] == "rule30_oloid_parameterization_scan_v0_1"
    assert scan["best_defect_rate"] < 1.0

    verify = verify_rule30_oloid_winding_from_n(max_depth=32, config=scan["best_config"])
    assert verify["model_id"] == "rule30_oloid_winding_verifier_v0_1"
    assert verify["total"] == 32
    assert verify["defect_count"] == scan["best_config"]["defects"]

    config = {
        key: value
        for key, value in scan["best_config"].items()
        if key
        in {
            "axis_angle",
            "pattern",
            "shell_axis",
            "side_axis",
            "shell_offset",
            "side_threshold",
            "parameterization",
        }
    }
    antipode = rule30_oloid_antipodal_winding(17, **config)
    assert antipode["model_id"] == "rule30_oloid_antipodal_winding_v0_1"
    assert antipode["antipodal_definition"]["counter_sheet"] == "-N"
    assert antipode["best_mode"] in antipode["selection_modes"]

    antipode_verify = verify_rule30_oloid_antipodal_winding(max_depth=32, config=scan["best_config"])
    assert antipode_verify["model_id"] == "rule30_oloid_antipodal_winding_verifier_v0_1"
    assert antipode_verify["total"] == 32
    assert antipode_verify["status"].startswith("pass")
    assert antipode_verify["adaptive_selector_defects"] == 0


def test_rule30_oloid_surfaces_are_public_forge_queries(tmp_path: Path):
    forge = Forge.open(tmp_path)
    cfg = {
        "axis_angle": 0.5235987755982988,
        "pattern": "alternating_xyz",
        "shell_axis": "y",
        "side_axis": "z",
        "shell_offset": -0.125,
        "parameterization": "phi",
    }

    spinor = forge.rule30_spinor_oloid_model(max_depth=64, max_order=4)["result"]
    assert spinor["model_id"] == "rule30_spinor_oloid_model_v0_1"
    spinor_verify = forge.verify_rule30_spinor_oloid_model(max_depth=64, max_order=4)["result"]
    assert spinor_verify["status"].startswith("pass")

    winding = forge.rule30_oloid_winding_from_n(17, **cfg)["result"]
    assert winding["model_id"] == "rule30_oloid_winding_from_n_v0_1"
    assert winding["status"] == "candidate_witness"
    assert "emitted_bit" in winding

    antipode = forge.rule30_oloid_antipodal_winding(17, **cfg)["result"]
    assert antipode["model_id"] == "rule30_oloid_antipodal_winding_v0_1"
    assert antipode["antipodal_definition"]["antipode_operation"] == "(x,y,z)->(-x,-y,-z)"

    winding_verify = forge.verify_rule30_oloid_winding_from_n(max_depth=32, config=cfg)["result"]
    assert winding_verify["model_id"] == "rule30_oloid_winding_verifier_v0_1"
    antipode_verify = forge.verify_rule30_oloid_antipodal_winding(max_depth=32, config=cfg)["result"]
    assert antipode_verify["model_id"] == "rule30_oloid_antipodal_winding_verifier_v0_1"
    assert antipode_verify["status"].startswith("pass")
    assert antipode_verify["adaptive_selector_accuracy"] == 1.0

    bounded = forge.rule30_winding_number_proof(max_depth=64, max_order=4)["result"]
    assert bounded["complexity_proof"]["claim_status"] == "BOUNDED_TRACE_WITNESS"
    bounded_verify = forge.verify_rule30_winding_number_proof(max_depth=64, max_order=4)["result"]
    assert bounded_verify["status"] == "pass_with_open_gaps"


def test_rule30_proof_obligations_name_submission_blockers_without_overclaim(tmp_path: Path):
    forge = Forge.open(tmp_path)
    payload = forge.rule30_proof_obligations(
        max_depth=128,
        page_count=2,
        page_size=128,
        block_size=8,
        max_order=4,
    )
    ledger = payload["result"]
    release = ledger["release_summary"]
    obligation_ids = {row["obligation_id"] for row in ledger["obligations"]}

    assert ledger["model_id"] == "rule30_proof_obligation_ledger_v0_1"
    assert ledger["no_new_token_invariant"]["status"] == "pass"
    assert "rule30.scalar_formula.nth_bit_expression" in obligation_ids
    assert "rule30.prize.depth_only_shortcut" in obligation_ids
    assert release["status_counts"]["BOUNDED_EXEC"] >= 4
    assert "rule30.prize.depth_only_shortcut" in release["blocking_obligations"]
    assert all(row["status"] != "OVERCLAIM" for row in ledger["obligations"])

    verify = forge.verify_rule30_proof_obligations(
        max_depth=128,
        page_count=2,
        page_size=128,
        block_size=8,
        max_order=4,
    )
    assert verify["result"]["schema_status"] == "pass"
    assert verify["result"]["status"] == "pass_with_open_gaps"


def test_seed_db_is_not_mutated_by_overlay_queries(tmp_path: Path):
    forge = Forge.open(tmp_path)
    seed_path = forge.seed.db_path

    before = seed_path.stat().st_mtime_ns
    forge.future_cone("G2")
    forge.exactness_dashboard("G2")
    forge.witnesses(source_id="G2", target_id="A2")
    forge.obstructions(source_id="G2")
    forge.export_object("G2")
    forge.terminal_tree("Niemeier:A2^12")
    forge.terminal_trees()
    forge.verify_terminal_trees()
    forge.morphonics_model()
    forge.verify_morphonics()
    forge.rule30_morphon(max_depth=5)
    forge.verify_rule30(max_depth=5)
    forge.rule30_vignettes(max_order=4)
    forge.verify_rule30_vignettes(max_order=4)
    forge.rule30_moving_frame(max_depth=8, max_order=4)
    forge.verify_rule30_moving_frame(max_depth=8, max_order=4)
    forge.rule30_color_chirality(max_depth=8, max_order=4)
    forge.verify_rule30_color_chirality(max_depth=8, max_order=4)
    forge.rule30_lagrangian(max_depth=8, max_order=4)
    forge.verify_rule30_lagrangian(max_depth=8, max_order=4)
    forge.rule30_lagrangian_depth_trace(max_depth=32, max_order=4)
    forge.verify_rule30_lagrangian_depth_trace(max_depth=32, max_order=4)
    forge.rule30_mandelbrot_scalar(max_depth=32, max_order=4)
    forge.verify_rule30_mandelbrot_scalar(max_depth=32, max_order=4)
    forge.rule30_reduced_alphabet(max_depth=32, max_order=4)
    forge.verify_rule30_reduced_alphabet(max_depth=32, max_order=4)
    forge.rule30_symmetry_environment(max_depth=32, max_period=8, max_order=4)
    forge.verify_rule30_symmetry_environment(max_depth=32, max_period=8, max_order=4)
    forge.rule30_physics_method_stack(max_depth=32, max_period=8, max_order=4, max_block=4)
    forge.verify_rule30_physics_method_stack(max_depth=32, max_period=8, max_order=4, max_block=4)
    forge.rule30_whole_integer_n_coverage(max_depth=32, max_order=4)
    forge.verify_rule30_whole_integer_n_coverage(max_depth=32, max_order=4)
    forge.rule30_readout_ribbon_machine(max_depth=32, max_order=4)
    forge.verify_rule30_readout_ribbon_machine(max_depth=32, max_order=4)
    forge.rule30_dihedral_block_hypervisor(max_depth=32, block_size=8, max_order=4)
    forge.verify_rule30_dihedral_block_hypervisor(max_depth=32, block_size=8, max_order=4)
    forge.rule30_hypervisor_extension_tape(page_count=2, page_size=32, block_size=8, max_order=4)
    forge.verify_rule30_hypervisor_extension_tape(page_count=2, page_size=32, block_size=8, max_order=4)
    forge.rule30_sheet_operator(page_count=2, page_size=32, block_size=8, max_order=4)
    forge.verify_rule30_sheet_operator(page_count=2, page_size=32, block_size=8, max_order=4)
    forge.rule30_mandelbrot_field_address(33, page_size=32, block_size=8, max_order=4)
    forge.verify_rule30_mandelbrot_field_address(33, page_size=32, block_size=8, max_order=4)
    forge.rule30_exit_trajectory(33, page_size=32, block_size=8, max_order=4)
    forge.verify_rule30_exit_trajectory(33, page_size=32, block_size=8, max_order=4)
    forge.rule30_sheet_lift(33, page_size=32, block_size=8, max_order=4)
    forge.verify_rule30_sheet_lift(33, page_size=32, block_size=8, max_order=4)
    forge.rule30_julia_resolution(33, page_size=32, block_size=8, max_order=4)
    forge.verify_rule30_julia_resolution(33, page_size=32, block_size=8, max_order=4)
    forge.rule30_torsor_functor_term(33, page_size=32, block_size=8, max_order=4)
    forge.verify_rule30_torsor_functor_term(33, page_size=32, block_size=8, max_order=4)
    forge.rule30_spinor_oloid_model(max_depth=32, max_order=4)
    forge.verify_rule30_spinor_oloid_model(max_depth=32, max_order=4)
    forge.rule30_oloid_winding_from_n(17)
    forge.rule30_oloid_antipodal_winding(17)
    forge.rule30_oloid_parameterization_scan(max_depth=16)
    forge.verify_rule30_oloid_winding_from_n(max_depth=16)
    forge.verify_rule30_oloid_antipodal_winding(max_depth=16)
    forge.rule30_winding_number_proof(max_depth=32, max_order=4)
    forge.verify_rule30_winding_number_proof(max_depth=32, max_order=4)
    forge.rule30_nth_bit_expression(33, page_size=32, block_size=8, max_order=4)
    forge.verify_rule30_nth_bit_expression(33, page_size=32, block_size=8, max_order=4)
    forge.rule30_proof_obligations(max_depth=32, page_count=2, page_size=32, block_size=8, max_order=4)
    forge.verify_rule30_proof_obligations(max_depth=32, page_count=2, page_size=32, block_size=8, max_order=4)
    after = seed_path.stat().st_mtime_ns

    assert before == after
    with sqlite3.connect(tmp_path / ".lattice_forge" / "overlay.sqlite") as conn:
        event_count = conn.execute("SELECT COUNT(*) FROM events").fetchone()[0]
    assert event_count >= 63
