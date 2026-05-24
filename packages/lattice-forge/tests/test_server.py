from __future__ import annotations

import importlib.util

import pytest

from lattice_forge.server import create_app


pytestmark = pytest.mark.skipif(
    importlib.util.find_spec("fastapi") is None or importlib.util.find_spec("fastapi.testclient") is None,
    reason="FastAPI server extra is not installed",
)


def test_fastapi_server_endpoints(tmp_path):
    from fastapi.testclient import TestClient

    app = create_app(tmp_path)
    client = TestClient(app)

    assert client.get("/health").json()["ok"] is True
    assert client.get("/status").json()["seed_integrity"] == "ok"
    close = client.post(
        "/can-close",
        json={"source_id": "G2", "target_id": "Niemeier:A2^12", "max_depth": 10},
    ).json()
    assert close["answer"] == "yes_with_template_glue"
    assert client.get("/future-cone/G2").status_code == 200
    assert client.get("/exactness/G2").status_code == 200
    tree = client.get("/terminal-tree/A2^12").json()
    assert tree["result"]["terminal_id"] == "Niemeier:A2^12"
    assert tree["result"]["composition_route"][-1]["rank"] == 24
    trees = client.get("/terminal-trees").json()
    assert trees["result"]["terminal_count"] == 24
    verify_trees = client.get("/terminal-trees/verify").json()
    assert verify_trees["result"]["status"] == "pass"
    morphonics = client.get("/morphonics/model").json()
    assert morphonics["result"]["lattice_forge_check"]["test_status"] == "pass"
    verify_morphonics = client.get("/morphonics/verify").json()
    assert verify_morphonics["result"]["schema_status"] == "pass"
    rule30 = client.get("/rule30/morphon?max_depth=5").json()
    assert rule30["result"]["summary"]["canonical_depths_passed"] == 5
    verify_rule30 = client.get("/rule30/verify?max_depth=5").json()
    assert verify_rule30["result"]["schema_status"] == "pass"
    vignettes = client.get("/rule30/vignettes?max_order=4").json()
    assert vignettes["result"]["unique_function_count"] == 128
    verify_vignettes = client.get("/rule30/vignettes/verify?max_order=4").json()
    assert verify_vignettes["result"]["summary"]["saturated_zero_preserving_space"] is True
    moving = client.get("/rule30/moving-frame?max_depth=8").json()
    assert moving["result"]["moving_space_summary"]["candidate_count"] == 56
    verify_moving = client.get("/rule30/moving-frame/verify?max_depth=8").json()
    assert verify_moving["result"]["schema_status"] == "pass"
    chiral = client.get("/rule30/color-chirality?max_depth=8").json()
    assert chiral["result"]["closure_summary"]["token_count"] == 6
    assert chiral["result"]["closure_summary"]["composition_closed"] is True
    verify_chiral = client.get("/rule30/color-chirality/verify?max_depth=8").json()
    assert verify_chiral["result"]["schema_status"] == "pass"
    lagrangian = client.get("/rule30/lagrangian?max_depth=8").json()
    assert lagrangian["result"]["action_summary"]["plaquette_count"] == 96
    assert lagrangian["result"]["action_summary"]["action_zero_is_legal_rule30_update"] is True
    verify_lagrangian = client.get("/rule30/lagrangian/verify?max_depth=8").json()
    assert verify_lagrangian["result"]["schema_status"] == "pass"
    trace = client.get("/rule30/lagrangian-trace?max_depth=64").json()
    assert trace["result"]["schedule_summary"]["perfect_zero_action_schedule_count"] == 4
    verify_trace = client.get("/rule30/lagrangian-trace/verify?max_depth=64").json()
    assert verify_trace["result"]["schema_status"] == "pass"
    scalar = client.get("/rule30/mandelbrot-scalar?max_depth=64").json()
    assert scalar["result"]["boundary_scalar_summary"]["light_setting_count"] == 4
    assert scalar["result"]["boundary_scalar_summary"]["prediction_accuracy"] == 1.0
    verify_scalar = client.get("/rule30/mandelbrot-scalar/verify?max_depth=64").json()
    assert verify_scalar["result"]["schema_status"] == "pass"
    reduced = client.get("/rule30/reduced-alphabet?max_depth=128").json()
    assert reduced["result"]["depth_equivalence_summary"]["accuracy"] == 1.0
    verify_reduced = client.get("/rule30/reduced-alphabet/verify?max_depth=128").json()
    assert verify_reduced["result"]["schema_status"] == "pass"
    symmetry = client.get("/rule30/symmetry-environment?max_depth=128&max_period=32").json()
    assert symmetry["result"]["representation_environment"]["tensor_product_space"]["token_dim"] == 6
    assert symmetry["result"]["nonperiodicity_diagnostics"]["no_exact_center_bit_period_in_window"] is True
    verify_symmetry = client.get("/rule30/symmetry-environment/verify?max_depth=128&max_period=32").json()
    assert verify_symmetry["result"]["schema_status"] == "pass"
    stack = client.get("/rule30/physics-stack?max_depth=128&max_period=32&max_block=6").json()
    assert stack["result"]["all_methods_unified"]["stage"] == 6
    assert stack["result"]["all_methods_unified"]["cumulative_defect_count"] == 0
    verify_stack = client.get("/rule30/physics-stack/verify?max_depth=128&max_period=32&max_block=6").json()
    assert verify_stack["result"]["schema_status"] == "pass"
    coverage = client.get("/rule30/n-coverage?max_depth=512").json()
    assert coverage["result"]["coverage_summary"]["unassigned_n_count"] == 0
    assert coverage["result"]["coverage_summary"]["single_scalar_adjustment_suffices"] is True
    verify_coverage = client.get("/rule30/n-coverage/verify?max_depth=1024").json()
    assert verify_coverage["result"]["schema_status"] == "pass"
    ribbon = client.get("/rule30/readout-ribbon?max_depth=512").json()
    assert ribbon["result"]["machine_summary"]["feedback_defect_count"] == 0
    assert ribbon["result"]["machine_summary"]["transition_conflict_count"] == 0
    verify_ribbon = client.get("/rule30/readout-ribbon/verify?max_depth=1024").json()
    assert verify_ribbon["result"]["schema_status"] == "pass"
    hypervisor = client.get("/rule30/dihedral-hypervisor?max_depth=512").json()
    assert hypervisor["result"]["hypervisor_summary"]["complete_block_count"] == 64
    assert hypervisor["result"]["hypervisor_summary"]["partial_tail"] == 0
    verify_hypervisor = client.get("/rule30/dihedral-hypervisor/verify?max_depth=512").json()
    assert verify_hypervisor["result"]["schema_status"] == "pass"
    extension = client.get("/rule30/extension-tape?page_count=2&page_size=512").json()
    assert extension["result"]["extension_summary"]["page_boundary_defect_count"] == 0
    assert extension["result"]["extension_summary"]["relative_table_stable_across_pages"] is True
    verify_extension = client.get("/rule30/extension-tape/verify?page_count=2&page_size=512").json()
    assert verify_extension["result"]["schema_status"] == "pass"
    sheet = client.get("/rule30/sheet-operator?page_count=2&page_size=128").json()
    assert sheet["result"]["operator_summary"]["stable_across_pages"] is True
    verify_sheet = client.get("/rule30/sheet-operator/verify?page_count=2&page_size=128").json()
    assert verify_sheet["result"]["schema_status"] == "pass"
    field = client.get("/rule30/field-address/257?page_size=128").json()
    assert field["result"]["coordinates"]["page_index"] == 2
    assert field["result"]["address"]["prediction_defect"] == 0
    verify_field = client.get("/rule30/field-address/257/verify?page_size=128").json()
    assert verify_field["result"]["schema_status"] == "pass"
    trajectory = client.get("/rule30/exit-trajectory/257?page_size=128").json()
    assert trajectory["result"]["trajectory_definition"]["extra_field_search"] == 0
    assert trajectory["result"]["exit"]["defect"] == 0
    verify_trajectory = client.get("/rule30/exit-trajectory/257/verify?page_size=128").json()
    assert verify_trajectory["result"]["schema_status"] == "pass"
    lift = client.get("/rule30/sheet-lift/257?page_size=128").json()
    assert lift["result"]["sheet"]["sheet_index_k"] == 257
    assert lift["result"]["sheet"]["next_sheet_index"] == 258
    verify_lift = client.get("/rule30/sheet-lift/257/verify?page_size=128").json()
    assert verify_lift["result"]["schema_status"] == "pass"
    resolution = client.get("/rule30/julia-resolution/257?page_size=128").json()
    assert resolution["result"]["resolved_bit"] == resolution["result"]["center_bit"]
    assert resolution["result"]["sheet_lift"]["sheet_index_k"] == 257
    verify_resolution = client.get("/rule30/julia-resolution/257/verify?page_size=128").json()
    assert verify_resolution["result"]["schema_status"] == "pass"
    torsor = client.get("/rule30/torsor-functor/257?page_size=128").json()
    assert torsor["result"]["torsor"]["lifted_sheet_id"] == resolution["result"]["sheet_lift"]["lifted_sheet_id"]
    assert torsor["result"]["bitorsor_actions"]["compatibility_defect"] == 0
    assert torsor["result"]["functor_stack"]["two_functor"]["preserves_2_cells"] is True
    verify_torsor = client.get("/rule30/torsor-functor/257/verify?page_size=128").json()
    assert verify_torsor["result"]["schema_status"] == "pass"
    spinor = client.get("/rule30/spinor-oloid?max_depth=64").json()
    assert spinor["result"]["model_id"] == "rule30_spinor_oloid_model_v0_1"
    verify_spinor = client.get("/rule30/spinor-oloid/verify?max_depth=64").json()
    assert verify_spinor["result"]["status"].startswith("pass")
    oloid_query = (
        "parameterization=phi&pattern=alternating_xyz&axis_angle=0.5235987755982988"
        "&shell_axis=y&side_axis=z&shell_offset=-0.125"
    )
    winding = client.get(f"/rule30/oloid-winding/17?{oloid_query}").json()
    assert winding["result"]["model_id"] == "rule30_oloid_winding_from_n_v0_1"
    antipode = client.get(f"/rule30/oloid-antipode/17?{oloid_query}").json()
    assert antipode["result"]["model_id"] == "rule30_oloid_antipodal_winding_v0_1"
    scan = client.get("/rule30/oloid-scan?max_depth=32").json()
    assert scan["result"]["model_id"] == "rule30_oloid_parameterization_scan_v0_1"
    verify_winding = client.get(f"/rule30/oloid-winding/verify?max_depth=32&{oloid_query}").json()
    assert verify_winding["result"]["model_id"] == "rule30_oloid_winding_verifier_v0_1"
    verify_antipode = client.get(f"/rule30/oloid-antipode/verify?max_depth=32&{oloid_query}").json()
    assert verify_antipode["result"]["status"].startswith("pass")
    winding_number = client.get("/rule30/winding-number?max_depth=64").json()
    assert winding_number["result"]["complexity_proof"]["claim_status"] == "BOUNDED_TRACE_WITNESS"
    verify_winding_number = client.get("/rule30/winding-number/verify?max_depth=64").json()
    assert verify_winding_number["result"]["status"] == "pass_with_open_gaps"
    nth = client.get("/rule30/nth-bit/129?page_size=128").json()
    assert nth["result"]["computed_witness"]["defect"] == 0
    assert nth["result"]["julia_resolution"]["defect"] == 0
    assert nth["result"]["torsor_functor"]["compatibility_defect"] == 0
    verify_nth = client.get("/rule30/nth-bit/129/verify?page_size=128").json()
    assert verify_nth["result"]["schema_status"] == "pass"
    proof = client.get("/rule30/proof-obligations?max_depth=128&page_count=2&page_size=128").json()
    assert proof["result"]["no_new_token_invariant"]["status"] == "pass"
    verify_proof = client.get("/rule30/proof-obligations/verify?max_depth=128&page_count=2&page_size=128").json()
    assert verify_proof["result"]["schema_status"] == "pass"
    assert client.get("/events").status_code == 200
    assert client.post("/run", json={"command": ["python", "-V"]}).status_code == 404
