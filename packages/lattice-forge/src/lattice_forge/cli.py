from __future__ import annotations

import argparse
import json
from pathlib import Path

from .forge import Forge


def print_json(payload) -> None:
    print(json.dumps(payload, indent=2, sort_keys=True, default=str))


def forge_from_args(args: argparse.Namespace) -> Forge:
    return Forge.open(args.root)


def cmd_status(args: argparse.Namespace) -> int:
    print_json(forge_from_args(args).status())
    return 0


def cmd_verify_seed(args: argparse.Namespace) -> int:
    payload = forge_from_args(args).verify_seed()
    print_json(payload)
    return 0 if payload["result"].get("status") == "pass" else 1


def cmd_object(args: argparse.Namespace) -> int:
    print_json(forge_from_args(args).object(args.object_id))
    return 0


def cmd_can_close(args: argparse.Namespace) -> int:
    print_json(forge_from_args(args).can_close(args.source_id, args.target_id, args.max_depth))
    return 0


def cmd_future_cone(args: argparse.Namespace) -> int:
    print_json(forge_from_args(args).future_cone(args.object_id, args.max_depth))
    return 0


def cmd_exactness(args: argparse.Namespace) -> int:
    print_json(forge_from_args(args).exactness_dashboard(args.object_id))
    return 0


def cmd_terminal_tree(args: argparse.Namespace) -> int:
    print_json(forge_from_args(args).terminal_tree(args.terminal_id))
    return 0


def cmd_terminal_trees(args: argparse.Namespace) -> int:
    print_json(forge_from_args(args).terminal_trees())
    return 0


def cmd_verify_terminal_trees(args: argparse.Namespace) -> int:
    payload = forge_from_args(args).verify_terminal_trees()
    print_json(payload)
    return 0 if payload["result"].get("status") == "pass" else 1


def cmd_morphonics_model(args: argparse.Namespace) -> int:
    print_json(forge_from_args(args).morphonics_model())
    return 0


def cmd_verify_morphonics(args: argparse.Namespace) -> int:
    payload = forge_from_args(args).verify_morphonics()
    print_json(payload)
    return 0 if str(payload["result"].get("status", "")).startswith("pass") else 1


def cmd_rule30_morphon(args: argparse.Namespace) -> int:
    print_json(forge_from_args(args).rule30_morphon(args.max_depth, args.sample_count))
    return 0


def cmd_verify_rule30(args: argparse.Namespace) -> int:
    payload = forge_from_args(args).verify_rule30(args.max_depth, args.sample_count)
    print_json(payload)
    return 0 if str(payload["result"].get("status", "")).startswith("pass") else 1


def cmd_rule30_vignettes(args: argparse.Namespace) -> int:
    print_json(forge_from_args(args).rule30_vignettes(args.max_order))
    return 0


def cmd_verify_rule30_vignettes(args: argparse.Namespace) -> int:
    payload = forge_from_args(args).verify_rule30_vignettes(args.max_order)
    print_json(payload)
    return 0 if str(payload["result"].get("status", "")).startswith("pass") else 1


def cmd_rule30_moving_frame(args: argparse.Namespace) -> int:
    print_json(forge_from_args(args).rule30_moving_frame(args.max_depth, args.max_order))
    return 0


def cmd_verify_rule30_moving_frame(args: argparse.Namespace) -> int:
    payload = forge_from_args(args).verify_rule30_moving_frame(args.max_depth, args.max_order)
    print_json(payload)
    return 0 if str(payload["result"].get("status", "")).startswith("pass") else 1


def cmd_rule30_color_chirality(args: argparse.Namespace) -> int:
    print_json(forge_from_args(args).rule30_color_chirality(args.max_depth, args.max_order))
    return 0


def cmd_verify_rule30_color_chirality(args: argparse.Namespace) -> int:
    payload = forge_from_args(args).verify_rule30_color_chirality(args.max_depth, args.max_order)
    print_json(payload)
    return 0 if str(payload["result"].get("status", "")).startswith("pass") else 1


def cmd_rule30_lagrangian(args: argparse.Namespace) -> int:
    print_json(forge_from_args(args).rule30_lagrangian(args.max_depth, args.max_order))
    return 0


def cmd_verify_rule30_lagrangian(args: argparse.Namespace) -> int:
    payload = forge_from_args(args).verify_rule30_lagrangian(args.max_depth, args.max_order)
    print_json(payload)
    return 0 if str(payload["result"].get("status", "")).startswith("pass") else 1


def cmd_rule30_lagrangian_trace(args: argparse.Namespace) -> int:
    print_json(forge_from_args(args).rule30_lagrangian_depth_trace(args.max_depth, args.max_order))
    return 0


def cmd_verify_rule30_lagrangian_trace(args: argparse.Namespace) -> int:
    payload = forge_from_args(args).verify_rule30_lagrangian_depth_trace(args.max_depth, args.max_order)
    print_json(payload)
    return 0 if str(payload["result"].get("status", "")).startswith("pass") else 1


def cmd_rule30_mandelbrot_scalar(args: argparse.Namespace) -> int:
    print_json(forge_from_args(args).rule30_mandelbrot_scalar(args.max_depth, args.max_order))
    return 0


def cmd_verify_rule30_mandelbrot_scalar(args: argparse.Namespace) -> int:
    payload = forge_from_args(args).verify_rule30_mandelbrot_scalar(args.max_depth, args.max_order)
    print_json(payload)
    return 0 if str(payload["result"].get("status", "")).startswith("pass") else 1


def cmd_rule30_reduced_alphabet(args: argparse.Namespace) -> int:
    print_json(forge_from_args(args).rule30_reduced_alphabet(args.max_depth, args.max_order))
    return 0


def cmd_verify_rule30_reduced_alphabet(args: argparse.Namespace) -> int:
    payload = forge_from_args(args).verify_rule30_reduced_alphabet(args.max_depth, args.max_order)
    print_json(payload)
    return 0 if str(payload["result"].get("status", "")).startswith("pass") else 1


def cmd_rule30_symmetry_environment(args: argparse.Namespace) -> int:
    print_json(
        forge_from_args(args).rule30_symmetry_environment(
            args.max_depth,
            args.max_period,
            args.max_order,
        )
    )
    return 0


def cmd_verify_rule30_symmetry_environment(args: argparse.Namespace) -> int:
    payload = forge_from_args(args).verify_rule30_symmetry_environment(
        args.max_depth,
        args.max_period,
        args.max_order,
    )
    print_json(payload)
    return 0 if str(payload["result"].get("status", "")).startswith("pass") else 1


def cmd_rule30_physics_method_stack(args: argparse.Namespace) -> int:
    print_json(
        forge_from_args(args).rule30_physics_method_stack(
            args.max_depth,
            args.max_period,
            args.max_order,
            args.max_block,
        )
    )
    return 0


def cmd_verify_rule30_physics_method_stack(args: argparse.Namespace) -> int:
    payload = forge_from_args(args).verify_rule30_physics_method_stack(
        args.max_depth,
        args.max_period,
        args.max_order,
        args.max_block,
    )
    print_json(payload)
    return 0 if str(payload["result"].get("status", "")).startswith("pass") else 1


def cmd_rule30_whole_integer_n_coverage(args: argparse.Namespace) -> int:
    print_json(forge_from_args(args).rule30_whole_integer_n_coverage(args.max_depth, args.max_order))
    return 0


def cmd_verify_rule30_whole_integer_n_coverage(args: argparse.Namespace) -> int:
    payload = forge_from_args(args).verify_rule30_whole_integer_n_coverage(args.max_depth, args.max_order)
    print_json(payload)
    return 0 if str(payload["result"].get("status", "")).startswith("pass") else 1


def cmd_rule30_readout_ribbon_machine(args: argparse.Namespace) -> int:
    print_json(forge_from_args(args).rule30_readout_ribbon_machine(args.max_depth, args.max_order))
    return 0


def cmd_verify_rule30_readout_ribbon_machine(args: argparse.Namespace) -> int:
    payload = forge_from_args(args).verify_rule30_readout_ribbon_machine(args.max_depth, args.max_order)
    print_json(payload)
    return 0 if str(payload["result"].get("status", "")).startswith("pass") else 1


def cmd_rule30_dihedral_block_hypervisor(args: argparse.Namespace) -> int:
    print_json(
        forge_from_args(args).rule30_dihedral_block_hypervisor(
            args.max_depth,
            args.block_size,
            args.max_order,
        )
    )
    return 0


def cmd_verify_rule30_dihedral_block_hypervisor(args: argparse.Namespace) -> int:
    payload = forge_from_args(args).verify_rule30_dihedral_block_hypervisor(
        args.max_depth,
        args.block_size,
        args.max_order,
    )
    print_json(payload)
    return 0 if str(payload["result"].get("status", "")).startswith("pass") else 1


def cmd_rule30_hypervisor_extension_tape(args: argparse.Namespace) -> int:
    print_json(
        forge_from_args(args).rule30_hypervisor_extension_tape(
            args.page_count,
            args.page_size,
            args.block_size,
            args.max_order,
        )
    )
    return 0


def cmd_verify_rule30_hypervisor_extension_tape(args: argparse.Namespace) -> int:
    payload = forge_from_args(args).verify_rule30_hypervisor_extension_tape(
        args.page_count,
        args.page_size,
        args.block_size,
        args.max_order,
    )
    print_json(payload)
    return 0 if str(payload["result"].get("status", "")).startswith("pass") else 1


def cmd_rule30_sheet_operator(args: argparse.Namespace) -> int:
    print_json(
        forge_from_args(args).rule30_sheet_operator(
            args.page_count,
            args.page_size,
            args.block_size,
            args.max_order,
        )
    )
    return 0


def cmd_verify_rule30_sheet_operator(args: argparse.Namespace) -> int:
    payload = forge_from_args(args).verify_rule30_sheet_operator(
        args.page_count,
        args.page_size,
        args.block_size,
        args.max_order,
    )
    print_json(payload)
    return 0 if str(payload["result"].get("status", "")).startswith("pass") else 1


def cmd_rule30_mandelbrot_field_address(args: argparse.Namespace) -> int:
    print_json(
        forge_from_args(args).rule30_mandelbrot_field_address(
            args.n,
            args.page_size,
            args.block_size,
            args.max_order,
        )
    )
    return 0


def cmd_verify_rule30_mandelbrot_field_address(args: argparse.Namespace) -> int:
    payload = forge_from_args(args).verify_rule30_mandelbrot_field_address(
        args.n,
        args.page_size,
        args.block_size,
        args.max_order,
    )
    print_json(payload)
    return 0 if str(payload["result"].get("status", "")).startswith("pass") else 1


def cmd_rule30_exit_trajectory(args: argparse.Namespace) -> int:
    print_json(
        forge_from_args(args).rule30_exit_trajectory(
            args.n,
            args.page_size,
            args.block_size,
            args.max_order,
        )
    )
    return 0


def cmd_verify_rule30_exit_trajectory(args: argparse.Namespace) -> int:
    payload = forge_from_args(args).verify_rule30_exit_trajectory(
        args.n,
        args.page_size,
        args.block_size,
        args.max_order,
    )
    print_json(payload)
    return 0 if str(payload["result"].get("status", "")).startswith("pass") else 1


def cmd_rule30_sheet_lift(args: argparse.Namespace) -> int:
    print_json(
        forge_from_args(args).rule30_sheet_lift(
            args.n,
            args.page_size,
            args.block_size,
            args.max_order,
        )
    )
    return 0


def cmd_verify_rule30_sheet_lift(args: argparse.Namespace) -> int:
    payload = forge_from_args(args).verify_rule30_sheet_lift(
        args.n,
        args.page_size,
        args.block_size,
        args.max_order,
    )
    print_json(payload)
    return 0 if str(payload["result"].get("status", "")).startswith("pass") else 1


def cmd_rule30_julia_resolution(args: argparse.Namespace) -> int:
    print_json(
        forge_from_args(args).rule30_julia_resolution(
            args.n,
            args.page_size,
            args.block_size,
            args.max_order,
        )
    )
    return 0


def cmd_verify_rule30_julia_resolution(args: argparse.Namespace) -> int:
    payload = forge_from_args(args).verify_rule30_julia_resolution(
        args.n,
        args.page_size,
        args.block_size,
        args.max_order,
    )
    print_json(payload)
    return 0 if str(payload["result"].get("status", "")).startswith("pass") else 1


def cmd_rule30_torsor_functor_term(args: argparse.Namespace) -> int:
    print_json(
        forge_from_args(args).rule30_torsor_functor_term(
            args.n,
            args.page_size,
            args.block_size,
            args.max_order,
        )
    )
    return 0


def cmd_verify_rule30_torsor_functor_term(args: argparse.Namespace) -> int:
    payload = forge_from_args(args).verify_rule30_torsor_functor_term(
        args.n,
        args.page_size,
        args.block_size,
        args.max_order,
    )
    print_json(payload)
    return 0 if str(payload["result"].get("status", "")).startswith("pass") else 1


def _oloid_config_from_args(args: argparse.Namespace) -> dict[str, object]:
    return {
        "axis_angle": args.axis_angle,
        "pattern": args.pattern,
        "shell_axis": args.shell_axis,
        "side_axis": args.side_axis,
        "shell_offset": args.shell_offset,
        "side_threshold": args.side_threshold,
        "parameterization": args.parameterization,
    }


def cmd_rule30_spinor_oloid(args: argparse.Namespace) -> int:
    print_json(forge_from_args(args).rule30_spinor_oloid_model(args.max_depth, args.max_order))
    return 0


def cmd_verify_rule30_spinor_oloid(args: argparse.Namespace) -> int:
    payload = forge_from_args(args).verify_rule30_spinor_oloid_model(args.max_depth, args.max_order)
    print_json(payload)
    return 0 if str(payload["result"].get("status", "")).startswith("pass") else 1


def cmd_rule30_oloid_winding(args: argparse.Namespace) -> int:
    print_json(forge_from_args(args).rule30_oloid_winding_from_n(args.n, **_oloid_config_from_args(args)))
    return 0


def cmd_rule30_oloid_antipode(args: argparse.Namespace) -> int:
    print_json(forge_from_args(args).rule30_oloid_antipodal_winding(args.n, **_oloid_config_from_args(args)))
    return 0


def cmd_rule30_oloid_scan(args: argparse.Namespace) -> int:
    print_json(forge_from_args(args).rule30_oloid_parameterization_scan(args.max_depth))
    return 0


def cmd_verify_rule30_oloid_winding(args: argparse.Namespace) -> int:
    payload = forge_from_args(args).verify_rule30_oloid_winding_from_n(
        args.max_depth,
        config=_oloid_config_from_args(args),
    )
    print_json(payload)
    return 0 if str(payload["result"].get("status", "")).startswith("pass") else 1


def cmd_verify_rule30_oloid_antipode(args: argparse.Namespace) -> int:
    payload = forge_from_args(args).verify_rule30_oloid_antipodal_winding(
        args.max_depth,
        config=_oloid_config_from_args(args),
    )
    print_json(payload)
    return 0 if str(payload["result"].get("status", "")).startswith("pass") else 1


def cmd_rule30_winding_number(args: argparse.Namespace) -> int:
    print_json(forge_from_args(args).rule30_winding_number_proof(args.max_depth, args.max_order))
    return 0


def cmd_verify_rule30_winding_number(args: argparse.Namespace) -> int:
    payload = forge_from_args(args).verify_rule30_winding_number_proof(args.max_depth, args.max_order)
    print_json(payload)
    return 0 if str(payload["result"].get("status", "")).startswith("pass") else 1


def cmd_rule30_nth_bit_expression(args: argparse.Namespace) -> int:
    print_json(
        forge_from_args(args).rule30_nth_bit_expression(
            args.n,
            args.page_size,
            args.block_size,
            args.max_order,
        )
    )
    return 0


def cmd_verify_rule30_nth_bit_expression(args: argparse.Namespace) -> int:
    payload = forge_from_args(args).verify_rule30_nth_bit_expression(
        args.n,
        args.page_size,
        args.block_size,
        args.max_order,
    )
    print_json(payload)
    return 0 if str(payload["result"].get("status", "")).startswith("pass") else 1


def cmd_rule30_proof_obligations(args: argparse.Namespace) -> int:
    print_json(
        forge_from_args(args).rule30_proof_obligations(
            args.max_depth,
            args.page_count,
            args.page_size,
            args.block_size,
            args.max_order,
        )
    )
    return 0


def cmd_verify_rule30_proof_obligations(args: argparse.Namespace) -> int:
    payload = forge_from_args(args).verify_rule30_proof_obligations(
        args.max_depth,
        args.page_count,
        args.page_size,
        args.block_size,
        args.max_order,
    )
    print_json(payload)
    return 0 if str(payload["result"].get("status", "")).startswith("pass") else 1


def cmd_witnesses(args: argparse.Namespace) -> int:
    print_json(
        forge_from_args(args).witnesses(
            source_id=args.source_id,
            target_id=args.target_id,
            morphism_id=args.morphism_id,
        )
    )
    return 0


def cmd_obstructions(args: argparse.Namespace) -> int:
    print_json(forge_from_args(args).obstructions(source_id=args.source_id, target_id=args.target_id))
    return 0


def cmd_export_object(args: argparse.Namespace) -> int:
    payload = forge_from_args(args).export_object(args.object_id, vector_limit=args.vector_limit)
    if args.out:
        Path(args.out).write_text(json.dumps(payload["result"], indent=2, sort_keys=True), encoding="utf-8")
        print_json({k: payload[k] for k in ["event_id", "query_id", "receipt_id", "answer", "evidence_level"]} | {"out": args.out})
    else:
        print_json(payload)
    return 0


def cmd_events(args: argparse.Namespace) -> int:
    print_json({"events": forge_from_args(args).latest_events(args.limit)})
    return 0


def cmd_receipts(args: argparse.Namespace) -> int:
    print_json({"receipts": forge_from_args(args).latest_receipts(args.limit)})
    return 0


def cmd_snapshot(args: argparse.Namespace) -> int:
    payload = forge_from_args(args).snapshot(limit=args.limit)
    if args.out:
        Path(args.out).write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
        print_json({"out": args.out})
    else:
        print_json(payload)
    return 0


def cmd_decomposition_verify(args: argparse.Namespace) -> int:
    from lattice_forge.decomposition import verify_all_theorems, verify_checkpoint_store

    theorems = verify_all_theorems(decomposition_depths=range(1, 129))
    checkpoints = verify_checkpoint_store(max_depth=args.max_depth)
    payload = {"theorems": theorems, "checkpoints": checkpoints}
    print_json(payload)
    ok = theorems.get("status") == "pass" and checkpoints.get("status") == "pass"
    return 0 if ok else 1


def cmd_falsify(args: argparse.Namespace) -> int:
    if not args.tier_a:
        raise SystemExit("Specify a falsification tier, e.g. --tier-a")
    from lattice_forge.falsify import run_tier_a

    payload = run_tier_a(max_depth=args.max_depth, quick=args.quick)
    print_json(payload)
    return 0 if payload.get("overall_status") == "pass" else 1


def cmd_serve(args: argparse.Namespace) -> int:
    try:
        import uvicorn
        from .server import create_app
    except ImportError as exc:
        raise SystemExit("Install server dependencies with: pip install lattice-forge[server]") from exc
    uvicorn.run(create_app(args.root), host=args.host, port=args.port)
    return 0


def add_oloid_config_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--axis-angle", type=float, default=1.5707963267948966)
    parser.add_argument("--pattern", default="alternating_xy")
    parser.add_argument("--shell-axis", default="z")
    parser.add_argument("--side-axis", default="x")
    parser.add_argument("--shell-offset", type=float, default=0.0)
    parser.add_argument("--side-threshold", type=float, default=0.05)
    parser.add_argument("--parameterization", default="identity")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="lattice-forge", description="Lattice Forge admissibility engine")
    parser.add_argument("--root", help="Project root for .lattice_forge overlay state")
    sub = parser.add_subparsers(required=True, dest="command")

    p = sub.add_parser("status", help="Show seed and overlay status")
    p.set_defaults(func=cmd_status)

    p = sub.add_parser("verify-seed", help="Verify bundled seed database")
    p.set_defaults(func=cmd_verify_seed)

    p = sub.add_parser("object", help="Inspect one lattice/morphism object")
    p.add_argument("object_id")
    p.set_defaults(func=cmd_object)

    p = sub.add_parser("can-close", help="Ask whether source can close into target")
    p.add_argument("source_id")
    p.add_argument("target_id")
    p.add_argument("--max-depth", type=int, default=10)
    p.set_defaults(func=cmd_can_close)

    p = sub.add_parser("future-cone", help="Query reachable futures for an object")
    p.add_argument("object_id")
    p.add_argument("--max-depth", type=int, default=8)
    p.set_defaults(func=cmd_future_cone)

    p = sub.add_parser("exactness", help="Show exact/computed/template/conceptual support")
    p.add_argument("object_id")
    p.set_defaults(func=cmd_exactness)

    p = sub.add_parser("terminal-tree", help="Generate a terminal form's canonical composition tree")
    p.add_argument("terminal_id")
    p.set_defaults(func=cmd_terminal_tree)

    p = sub.add_parser("terminal-trees", help="List canonical terminal tree summaries for all 24 terminals")
    p.set_defaults(func=cmd_terminal_trees)

    p = sub.add_parser("verify-terminal-trees", help="Verify all 24 terminal composition trees")
    p.set_defaults(func=cmd_verify_terminal_trees)

    p = sub.add_parser("morphonics-model", help="Show the executable Morphonics v0.2 schema ledger")
    p.set_defaults(func=cmd_morphonics_model)

    p = sub.add_parser("verify-morphonics", help="Validate the Morphonics v0.2 schema ledger")
    p.set_defaults(func=cmd_verify_morphonics)

    p = sub.add_parser("rule30-morphon", help="Run the hardened Rule 30 Morphon harness")
    p.add_argument("--max-depth", type=int, default=7)
    p.add_argument("--sample-count", type=int, default=512)
    p.set_defaults(func=cmd_rule30_morphon)

    p = sub.add_parser("verify-rule30", help="Verify the hardened Rule 30 Morphon harness")
    p.add_argument("--max-depth", type=int, default=7)
    p.add_argument("--sample-count", type=int, default=512)
    p.set_defaults(func=cmd_verify_rule30)

    p = sub.add_parser("rule30-vignettes", help="Generate the Rule 30 rotated-cone vignette composition algebra")
    p.add_argument("--max-order", type=int, default=4)
    p.set_defaults(func=cmd_rule30_vignettes)

    p = sub.add_parser("verify-rule30-vignettes", help="Verify the Rule 30 vignette composition algebra")
    p.add_argument("--max-order", type=int, default=4)
    p.set_defaults(func=cmd_verify_rule30_vignettes)

    p = sub.add_parser("rule30-moving-frame", help="Run the Rule 30 moving beam-frame admissibility filter")
    p.add_argument("--max-depth", type=int, default=12)
    p.add_argument("--max-order", type=int, default=4)
    p.set_defaults(func=cmd_rule30_moving_frame)

    p = sub.add_parser("verify-rule30-moving-frame", help="Verify the Rule 30 moving beam-frame filter")
    p.add_argument("--max-depth", type=int, default=12)
    p.add_argument("--max-order", type=int, default=4)
    p.set_defaults(func=cmd_verify_rule30_moving_frame)

    p = sub.add_parser("rule30-color-chirality", help="Generate the Rule 30 color/chirality codeword cipher")
    p.add_argument("--max-depth", type=int, default=12)
    p.add_argument("--max-order", type=int, default=4)
    p.set_defaults(func=cmd_rule30_color_chirality)

    p = sub.add_parser("verify-rule30-color-chirality", help="Verify the Rule 30 color/chirality codeword cipher")
    p.add_argument("--max-depth", type=int, default=12)
    p.add_argument("--max-order", type=int, default=4)
    p.set_defaults(func=cmd_verify_rule30_color_chirality)

    p = sub.add_parser("rule30-lagrangian", help="Generate the Rule 30 discrete Lagrangian/NSL action ledger")
    p.add_argument("--max-depth", type=int, default=12)
    p.add_argument("--max-order", type=int, default=4)
    p.set_defaults(func=cmd_rule30_lagrangian)

    p = sub.add_parser("verify-rule30-lagrangian", help="Verify the Rule 30 discrete Lagrangian/NSL action ledger")
    p.add_argument("--max-depth", type=int, default=12)
    p.add_argument("--max-order", type=int, default=4)
    p.set_defaults(func=cmd_verify_rule30_lagrangian)

    p = sub.add_parser("rule30-lagrangian-trace", help="Run the Rule 30 center-column Lagrangian depth trace")
    p.add_argument("--max-depth", type=int, default=256)
    p.add_argument("--max-order", type=int, default=4)
    p.set_defaults(func=cmd_rule30_lagrangian_trace)

    p = sub.add_parser("verify-rule30-lagrangian-trace", help="Verify the Rule 30 center-column Lagrangian depth trace")
    p.add_argument("--max-depth", type=int, default=256)
    p.add_argument("--max-order", type=int, default=4)
    p.set_defaults(func=cmd_verify_rule30_lagrangian_trace)

    p = sub.add_parser("rule30-mandelbrot-scalar", help="Run the Rule 30 Mandelbrot/Julia boundary scalar map")
    p.add_argument("--max-depth", type=int, default=256)
    p.add_argument("--max-order", type=int, default=4)
    p.set_defaults(func=cmd_rule30_mandelbrot_scalar)

    p = sub.add_parser("verify-rule30-mandelbrot-scalar", help="Verify the Rule 30 Mandelbrot/Julia boundary scalar map")
    p.add_argument("--max-depth", type=int, default=256)
    p.add_argument("--max-order", type=int, default=4)
    p.set_defaults(func=cmd_verify_rule30_mandelbrot_scalar)

    p = sub.add_parser("rule30-reduced-alphabet", help="Run the Rule 30 reduced alphabet rule catalog")
    p.add_argument("--max-depth", type=int, default=1024)
    p.add_argument("--max-order", type=int, default=4)
    p.set_defaults(func=cmd_rule30_reduced_alphabet)

    p = sub.add_parser("verify-rule30-reduced-alphabet", help="Verify the Rule 30 reduced alphabet rule catalog")
    p.add_argument("--max-depth", type=int, default=1024)
    p.add_argument("--max-order", type=int, default=4)
    p.set_defaults(func=cmd_verify_rule30_reduced_alphabet)

    p = sub.add_parser("rule30-symmetry-environment", help="Run the Rule 30 U1/SU2/SU3 finite symmetry environment")
    p.add_argument("--max-depth", type=int, default=1024)
    p.add_argument("--max-period", type=int, default=128)
    p.add_argument("--max-order", type=int, default=4)
    p.set_defaults(func=cmd_rule30_symmetry_environment)

    p = sub.add_parser(
        "verify-rule30-symmetry-environment",
        help="Verify the Rule 30 U1/SU2/SU3 finite symmetry environment",
    )
    p.add_argument("--max-depth", type=int, default=1024)
    p.add_argument("--max-period", type=int, default=128)
    p.add_argument("--max-order", type=int, default=4)
    p.set_defaults(func=cmd_verify_rule30_symmetry_environment)

    p = sub.add_parser("rule30-physics-stack", help="Run six finite physics/method diagnostics over Rule 30")
    p.add_argument("--max-depth", type=int, default=1024)
    p.add_argument("--max-period", type=int, default=128)
    p.add_argument("--max-order", type=int, default=4)
    p.add_argument("--max-block", type=int, default=8)
    p.set_defaults(func=cmd_rule30_physics_method_stack)

    p = sub.add_parser("verify-rule30-physics-stack", help="Verify the six-method Rule 30 physics stack")
    p.add_argument("--max-depth", type=int, default=1024)
    p.add_argument("--max-period", type=int, default=128)
    p.add_argument("--max-order", type=int, default=4)
    p.add_argument("--max-block", type=int, default=8)
    p.set_defaults(func=cmd_verify_rule30_physics_method_stack)

    p = sub.add_parser("rule30-n-coverage", help="Test whole-integer N scalar coverage for Rule 30")
    p.add_argument("--max-depth", type=int, default=4096)
    p.add_argument("--max-order", type=int, default=4)
    p.set_defaults(func=cmd_rule30_whole_integer_n_coverage)

    p = sub.add_parser("verify-rule30-n-coverage", help="Verify whole-integer N scalar coverage for Rule 30")
    p.add_argument("--max-depth", type=int, default=4096)
    p.add_argument("--max-order", type=int, default=4)
    p.set_defaults(func=cmd_verify_rule30_whole_integer_n_coverage)

    p = sub.add_parser("rule30-readout-ribbon", help="Run the Rule 30 finite readout-ribbon machine")
    p.add_argument("--max-depth", type=int, default=4096)
    p.add_argument("--max-order", type=int, default=4)
    p.set_defaults(func=cmd_rule30_readout_ribbon_machine)

    p = sub.add_parser("verify-rule30-readout-ribbon", help="Verify the Rule 30 finite readout-ribbon machine")
    p.add_argument("--max-depth", type=int, default=4096)
    p.add_argument("--max-order", type=int, default=4)
    p.set_defaults(func=cmd_verify_rule30_readout_ribbon_machine)

    p = sub.add_parser("rule30-dihedral-hypervisor", help="Run the Rule 30 8-step dihedral block hypervisor")
    p.add_argument("--max-depth", type=int, default=4096)
    p.add_argument("--block-size", type=int, default=8)
    p.add_argument("--max-order", type=int, default=4)
    p.set_defaults(func=cmd_rule30_dihedral_block_hypervisor)

    p = sub.add_parser(
        "verify-rule30-dihedral-hypervisor",
        help="Verify the Rule 30 8-step dihedral block hypervisor",
    )
    p.add_argument("--max-depth", type=int, default=4096)
    p.add_argument("--block-size", type=int, default=8)
    p.add_argument("--max-order", type=int, default=4)
    p.set_defaults(func=cmd_verify_rule30_dihedral_block_hypervisor)

    p = sub.add_parser("rule30-extension-tape", help="Run hypervisor page-extension tape over Rule 30")
    p.add_argument("--page-count", type=int, default=2)
    p.add_argument("--page-size", type=int, default=4096)
    p.add_argument("--block-size", type=int, default=8)
    p.add_argument("--max-order", type=int, default=4)
    p.set_defaults(func=cmd_rule30_hypervisor_extension_tape)

    p = sub.add_parser("verify-rule30-extension-tape", help="Verify hypervisor page-extension tape over Rule 30")
    p.add_argument("--page-count", type=int, default=2)
    p.add_argument("--page-size", type=int, default=4096)
    p.add_argument("--block-size", type=int, default=8)
    p.add_argument("--max-order", type=int, default=4)
    p.set_defaults(func=cmd_verify_rule30_hypervisor_extension_tape)

    p = sub.add_parser("rule30-sheet-operator", help="Run the finite Rule 30 relative sheet operator")
    p.add_argument("--page-count", type=int, default=2)
    p.add_argument("--page-size", type=int, default=4096)
    p.add_argument("--block-size", type=int, default=8)
    p.add_argument("--max-order", type=int, default=4)
    p.set_defaults(func=cmd_rule30_sheet_operator)

    p = sub.add_parser("verify-rule30-sheet-operator", help="Verify the finite Rule 30 relative sheet operator")
    p.add_argument("--page-count", type=int, default=2)
    p.add_argument("--page-size", type=int, default=4096)
    p.add_argument("--block-size", type=int, default=8)
    p.add_argument("--max-order", type=int, default=4)
    p.set_defaults(func=cmd_verify_rule30_sheet_operator)

    p = sub.add_parser("rule30-field-address", help="Resolve N into the CA-induced Mandelbrot field address")
    p.add_argument("n", type=int)
    p.add_argument("--page-size", type=int, default=4096)
    p.add_argument("--block-size", type=int, default=8)
    p.add_argument("--max-order", type=int, default=4)
    p.set_defaults(func=cmd_rule30_mandelbrot_field_address)

    p = sub.add_parser("verify-rule30-field-address", help="Verify the CA-induced Mandelbrot field address")
    p.add_argument("n", type=int)
    p.add_argument("--page-size", type=int, default=4096)
    p.add_argument("--block-size", type=int, default=8)
    p.add_argument("--max-order", type=int, default=4)
    p.set_defaults(func=cmd_verify_rule30_mandelbrot_field_address)

    p = sub.add_parser("rule30-exit-trajectory", help="Resolve N to its Julia exit trajectory")
    p.add_argument("n", type=int)
    p.add_argument("--page-size", type=int, default=4096)
    p.add_argument("--block-size", type=int, default=8)
    p.add_argument("--max-order", type=int, default=4)
    p.set_defaults(func=cmd_rule30_exit_trajectory)

    p = sub.add_parser("verify-rule30-exit-trajectory", help="Verify the Julia exit trajectory")
    p.add_argument("n", type=int)
    p.add_argument("--page-size", type=int, default=4096)
    p.add_argument("--block-size", type=int, default=8)
    p.add_argument("--max-order", type=int, default=4)
    p.set_defaults(func=cmd_verify_rule30_exit_trajectory)

    p = sub.add_parser("rule30-sheet-lift", help="Lift N onto its k-th sheet in the Julia sheet tower")
    p.add_argument("n", type=int)
    p.add_argument("--page-size", type=int, default=4096)
    p.add_argument("--block-size", type=int, default=8)
    p.add_argument("--max-order", type=int, default=4)
    p.set_defaults(func=cmd_rule30_sheet_lift)

    p = sub.add_parser("verify-rule30-sheet-lift", help="Verify N's k->k+1 sheet lift")
    p.add_argument("n", type=int)
    p.add_argument("--page-size", type=int, default=4096)
    p.add_argument("--block-size", type=int, default=8)
    p.add_argument("--max-order", type=int, default=4)
    p.set_defaults(func=cmd_verify_rule30_sheet_lift)

    p = sub.add_parser("rule30-julia-resolution", help="Resolve N through field address, exit trajectory, and sheet lift")
    p.add_argument("n", type=int)
    p.add_argument("--page-size", type=int, default=4096)
    p.add_argument("--block-size", type=int, default=8)
    p.add_argument("--max-order", type=int, default=4)
    p.set_defaults(func=cmd_rule30_julia_resolution)

    p = sub.add_parser("verify-rule30-julia-resolution", help="Verify N's Julia sheet resolution")
    p.add_argument("n", type=int)
    p.add_argument("--page-size", type=int, default=4096)
    p.add_argument("--block-size", type=int, default=8)
    p.add_argument("--max-order", type=int, default=4)
    p.set_defaults(func=cmd_verify_rule30_julia_resolution)

    p = sub.add_parser("rule30-torsor-functor", help="Resolve N with the Rule 30 torsor/functor term")
    p.add_argument("n", type=int)
    p.add_argument("--page-size", type=int, default=4096)
    p.add_argument("--block-size", type=int, default=8)
    p.add_argument("--max-order", type=int, default=4)
    p.set_defaults(func=cmd_rule30_torsor_functor_term)

    p = sub.add_parser("verify-rule30-torsor-functor", help="Verify N's torsor/functor coherence")
    p.add_argument("n", type=int)
    p.add_argument("--page-size", type=int, default=4096)
    p.add_argument("--block-size", type=int, default=8)
    p.add_argument("--max-order", type=int, default=4)
    p.set_defaults(func=cmd_verify_rule30_torsor_functor_term)

    p = sub.add_parser("rule30-spinor-oloid", help="Run the Rule 30 spinor/Oloid bridge ledger")
    p.add_argument("--max-depth", type=int, default=4096)
    p.add_argument("--max-order", type=int, default=4)
    p.set_defaults(func=cmd_rule30_spinor_oloid)

    p = sub.add_parser("verify-rule30-spinor-oloid", help="Verify the Rule 30 spinor/Oloid bridge ledger")
    p.add_argument("--max-depth", type=int, default=4096)
    p.add_argument("--max-order", type=int, default=4)
    p.set_defaults(func=cmd_verify_rule30_spinor_oloid)

    p = sub.add_parser("rule30-oloid-winding", help="Emit one Rule 30 Oloid winding witness for N")
    p.add_argument("n", type=int)
    add_oloid_config_args(p)
    p.set_defaults(func=cmd_rule30_oloid_winding)

    p = sub.add_parser("rule30-oloid-antipode", help="Emit one Rule 30 +N/-N counter-sheet Oloid witness")
    p.add_argument("n", type=int)
    add_oloid_config_args(p)
    p.set_defaults(func=cmd_rule30_oloid_antipode)

    p = sub.add_parser("rule30-oloid-scan", help="Scan compact Oloid parameterizations against the center bar")
    p.add_argument("--max-depth", type=int, default=256)
    p.set_defaults(func=cmd_rule30_oloid_scan)

    p = sub.add_parser("verify-rule30-oloid-winding", help="Verify an Oloid winding parameterization")
    p.add_argument("--max-depth", type=int, default=256)
    add_oloid_config_args(p)
    p.set_defaults(func=cmd_verify_rule30_oloid_winding)

    p = sub.add_parser("verify-rule30-oloid-antipode", help="Verify the +N/-N counter-sheet Oloid selector")
    p.add_argument("--max-depth", type=int, default=256)
    add_oloid_config_args(p)
    p.set_defaults(func=cmd_verify_rule30_oloid_antipode)

    p = sub.add_parser("rule30-winding-number", help="Build the bounded Rule 30 winding-number witness")
    p.add_argument("--max-depth", type=int, default=4096)
    p.add_argument("--max-order", type=int, default=4)
    p.set_defaults(func=cmd_rule30_winding_number)

    p = sub.add_parser("verify-rule30-winding-number", help="Verify the bounded Rule 30 winding-number witness")
    p.add_argument("--max-depth", type=int, default=4096)
    p.add_argument("--max-order", type=int, default=4)
    p.set_defaults(func=cmd_verify_rule30_winding_number)

    p = sub.add_parser("rule30-nth-bit", help="Emit the Rule 30 nth-bit reduced scalar expression")
    p.add_argument("n", type=int)
    p.add_argument("--page-size", type=int, default=4096)
    p.add_argument("--block-size", type=int, default=8)
    p.add_argument("--max-order", type=int, default=4)
    p.set_defaults(func=cmd_rule30_nth_bit_expression)

    p = sub.add_parser("verify-rule30-nth-bit", help="Verify a Rule 30 nth-bit reduced scalar expression")
    p.add_argument("n", type=int)
    p.add_argument("--page-size", type=int, default=4096)
    p.add_argument("--block-size", type=int, default=8)
    p.add_argument("--max-order", type=int, default=4)
    p.set_defaults(func=cmd_verify_rule30_nth_bit_expression)

    p = sub.add_parser("rule30-proof-obligations", help="Build the Rule 30 submission proof-obligation ledger")
    p.add_argument("--max-depth", type=int, default=4096)
    p.add_argument("--page-count", type=int, default=2)
    p.add_argument("--page-size", type=int, default=4096)
    p.add_argument("--block-size", type=int, default=8)
    p.add_argument("--max-order", type=int, default=4)
    p.set_defaults(func=cmd_rule30_proof_obligations)

    p = sub.add_parser("verify-rule30-proof-obligations", help="Verify the Rule 30 proof-obligation ledger")
    p.add_argument("--max-depth", type=int, default=4096)
    p.add_argument("--page-count", type=int, default=2)
    p.add_argument("--page-size", type=int, default=4096)
    p.add_argument("--block-size", type=int, default=8)
    p.add_argument("--max-order", type=int, default=4)
    p.set_defaults(func=cmd_verify_rule30_proof_obligations)

    p = sub.add_parser("witnesses", help="Query morphism witnesses")
    p.add_argument("--source-id")
    p.add_argument("--target-id")
    p.add_argument("--morphism-id")
    p.set_defaults(func=cmd_witnesses)

    p = sub.add_parser("obstructions", help="Query closure obstructions")
    p.add_argument("--source-id")
    p.add_argument("--target-id")
    p.set_defaults(func=cmd_obstructions)

    p = sub.add_parser("export-object", help="Export an object bundle")
    p.add_argument("object_id")
    p.add_argument("--vector-limit", type=int, default=12)
    p.add_argument("--out")
    p.set_defaults(func=cmd_export_object)

    p = sub.add_parser("events", help="List overlay events")
    p.add_argument("--limit", type=int, default=20)
    p.set_defaults(func=cmd_events)

    p = sub.add_parser("receipts", help="List overlay receipts")
    p.add_argument("--limit", type=int, default=20)
    p.set_defaults(func=cmd_receipts)

    p = sub.add_parser("snapshot", help="Export seed/overlay snapshot")
    p.add_argument("--limit", type=int, default=100)
    p.add_argument("--out")
    p.set_defaults(func=cmd_snapshot)

    dec = sub.add_parser("decomposition", help="Rule 30 decomposition paper commands")
    dec_sub = dec.add_subparsers(required=True, dest="decomposition_command")
    dv = dec_sub.add_parser("verify", help="Verify vendored decomposition paper claims")
    dv.add_argument("--max-depth", type=int, default=512)
    dv.set_defaults(func=cmd_decomposition_verify)

    fal = sub.add_parser("falsify", help="Machine falsification for prize-core claims")
    fal.add_argument("--tier-a", action="store_true", help="Run Tier A breaks B-T1..B-decomp")
    fal.add_argument("--quick", action="store_true", help="Use reduced depth windows (default for CI)")
    fal.add_argument("--max-depth", type=int, default=256, help="Depth for chart/decomposition checks")
    fal.set_defaults(func=cmd_falsify)

    p = sub.add_parser("serve", help="Start optional FastAPI server")
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=8765)
    p.set_defaults(func=cmd_serve)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
