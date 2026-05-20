"""Minimal CLI for cmplx.transform.

Usage:
    python -m cmplx.transform forward --ribbon "hello"
    python -m cmplx.transform build-index --levels 1,2 --lib data/rule_libs
    python -m cmplx.transform ingest --root PATH --db data/token_index.sqlite
    python -m cmplx.transform crystallize --name workstate --db ... --out crystals/workstate.crystal/
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from cmplx.runtime_paths import runtime_path

from . import GeometricTransformer, TransformerConfig
from .config import ProductionTransformerConfig
from .crystal_pack import CrystalPackager
from .index_mutations import refine_to_coverage
from .ingest import CorpusIngester
from .tool_pass import run_tool_pass_batch
from .meaning_store import AddressMeaningStore
from .rule_lib import RuleLibraryLoader
from .shell import MorphonShell, AdmitResult
from .shell_config import ShellConfig
from .token_index import (
    CaseMode,
    DEFAULT_ALPHABET,
    DEFAULT_CASE_MODES,
    TokenIndexBuildConfig,
    TokenIndexBuilder,
    TokenIndexStore,
    get_filter,
    template_report,
)
from .metrics import compute_morph_signature, probe_case_pair


DEFAULT_TOKEN_INDEX_DB = str(runtime_path("data", "token_index.sqlite"))


def _cmd_forward(args: argparse.Namespace) -> int:
    db = args.db
    if args.crystal:
        bundle_db = Path(args.crystal) / "token_index.sqlite"
        if bundle_db.is_file():
            db = str(bundle_db)
    if args.production:
        config = ProductionTransformerConfig(
            output_mode=args.output_mode,
            register_ports_on_init=not args.no_ports,
        )
    else:
        config = TransformerConfig(
            num_layers=args.num_layers,
            output_mode=args.output_mode,
            register_ports_on_init=not args.no_ports,
        )
    shell = None
    if db:
        store = TokenIndexStore(db)
        shell = MorphonShell(ShellConfig(), store)
    model = GeometricTransformer(config, shell=shell)
    out = model.forward(args.ribbon)
    summary = {
        "cache_key": out.cache_key,
        "morphon_id": out.final_morphon.id,
        "speedlight_hit": out.speedlight_hit,
        "num_layer_traces": len(out.layer_traces),
        "ribbon_out": out.ribbon_out,
        "summary": out.summary,
    }
    json.dump(summary, sys.stdout, indent=2, default=str)
    sys.stdout.write("\n")
    return 0


def _cmd_config_dump(args: argparse.Namespace) -> int:
    config = TransformerConfig(num_layers=args.num_layers)
    json.dump(
        {
            "num_layers": config.num_layers,
            "n_domains": config.n_domains,
            "hidden_dim": config.hidden_dim,
            "seq_length": config.seq_length,
            "output_mode": config.output_mode,
        },
        sys.stdout,
        indent=2,
    )
    sys.stdout.write("\n")
    return 0


def _cmd_build_index(args: argparse.Namespace) -> int:
    levels = tuple(int(x) for x in args.levels.split(","))
    alphabet = tuple(args.alphabet) if args.alphabet else DEFAULT_ALPHABET
    languages = [get_filter(n.strip()) for n in args.languages.split(",")]
    if args.case_modes:
        case_modes = [CaseMode(c.strip()) for c in args.case_modes.split(",")]
    else:
        case_modes = list(DEFAULT_CASE_MODES)
    lib_paths = tuple(args.lib) if args.lib else ()
    cfg = TokenIndexBuildConfig(
        levels=levels,
        alphabet=alphabet,
        languages=languages,
        case_modes=case_modes,
        db_path=args.db,
        lib_paths=lib_paths,
        max_entries=args.max_entries,
        progress_every=args.progress_every,
    )
    builder = TokenIndexBuilder(cfg)
    result = builder.build()
    json.dump(result.as_dict(), sys.stdout, indent=2, default=str)
    sys.stdout.write("\n")
    return 0


def _cmd_index_stats(args: argparse.Namespace) -> int:
    store = TokenIndexStore(args.db)
    try:
        stats = store.stats()
    finally:
        store.close()
    json.dump(stats, sys.stdout, indent=2, default=str)
    sys.stdout.write("\n")
    return 0


def _cmd_template_stats(args: argparse.Namespace) -> int:
    report = template_report(args.db)
    json.dump(report, sys.stdout, indent=2, default=str)
    sys.stdout.write("\n")
    return 0


def _cmd_lib_validate(args: argparse.Namespace) -> int:
    loader = RuleLibraryLoader(args.lib)
    paths = [args.lib] if args.lib else []
    errors = loader.validate(*paths) if paths else loader.validate(loader.root)
    out = {"ok": len(errors) == 0, "errors": errors}
    json.dump(out, sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0 if out["ok"] else 1


def _cmd_lib_list(args: argparse.Namespace) -> int:
    loader = RuleLibraryLoader(args.lib)
    json.dump({"libraries": loader.list_libraries()}, sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0


def _cmd_meaning_query(args: argparse.Namespace) -> int:
    store = AddressMeaningStore(args.db)
    try:
        if args.snap_key:
            rows = store.by_snap_key(args.snap_key, limit=args.limit)
        elif args.label:
            rows = store.by_label(args.label, limit=args.limit)
        elif args.doc:
            rows = store.by_doc(args.doc, limit=args.limit)
        else:
            rows = store.all_rows(limit=args.limit)
        json.dump([r.as_dict() for r in rows], sys.stdout, indent=2, default=str)
    finally:
        store.close()
    sys.stdout.write("\n")
    return 0


def _cmd_ingest(args: argparse.Namespace) -> int:
    ingester = CorpusIngester(
        register_ports=not args.no_ports,
        max_files=args.max_files,
        stream=args.stream,
    )
    lib_paths = args.lib_paths or ["data/rule_libs"]
    stats = ingester.ingest_path(
        Path(args.root),
        lib_paths=lib_paths,
        db=args.db,
        lib=args.lib,
    )
    json.dump(stats.as_dict(), sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0


def _cmd_admit(args: argparse.Namespace) -> int:
    store = TokenIndexStore(args.db)
    shell = MorphonShell(ShellConfig(), store)
    try:
        result = shell.admit(args.token, lang=args.lang)
        json.dump(
            {
                "admitted": result.admitted,
                "token": result.token,
                "reason": result.reason,
                "snap_key": result.snap_key,
                "segments": result.segments,
            },
            sys.stdout,
            indent=2,
        )
    finally:
        store.close()
    sys.stdout.write("\n")
    return 0


def _cmd_complete(args: argparse.Namespace) -> int:
    store = TokenIndexStore(args.db)
    shell = MorphonShell(ShellConfig(), store)
    try:
        candidates = shell.complete(args.partial, max_candidates=args.max_candidates)
        json.dump({"partial": args.partial, "candidates": candidates}, sys.stdout, indent=2)
    finally:
        store.close()
    sys.stdout.write("\n")
    return 0


def _cmd_morph_probe(args: argparse.Namespace) -> int:
    from .token_index.bonds import QuadBond
    from .token_index.case import CaseMode, apply_case
    from .token_index.notation import SurfaceMode, load_notation_lib, surfaces_equivalent

    a = args.concat_a[:8].ljust(8, "a")
    b = args.concat_b[:8].ljust(8, "a")
    if args.notation_equiv:
        lib = load_notation_lib()
        if not surfaces_equivalent(a, b, mode=SurfaceMode.UNICODE_EQUIV, lib=lib):
            json.dump({"verdict": "notation_mismatch", "a": a, "b": b}, sys.stdout, indent=2)
            sys.stdout.write("\n")
            return 1

    bond = QuadBond(quad_left=a[:4], quad_right=a[4:], level=1)
    case_mode = CaseMode.LEAD_RIGHT
    if b != a.lower():
        for mode in CaseMode:
            if apply_case(bond, mode).concat == b:
                case_mode = mode
                break
    sig = probe_case_pair(bond, case_mode) if b.lower() == a.lower() else compute_morph_signature(
        a, b, case_mode=case_mode
    )
    json.dump(sig.as_dict(), sys.stdout, indent=2, default=str)
    sys.stdout.write("\n")
    return 0


def _cmd_crystallize(args: argparse.Namespace) -> int:
    packager = CrystalPackager()
    crystal = packager.pack(
        args.name,
        db=args.db,
        libs=args.lib,
        out=args.out,
    )
    json.dump(
        {"crystal_id": crystal.crystal_id, "name": crystal.name, "state": crystal.state, "out": args.out},
        sys.stdout,
        indent=2,
    )
    sys.stdout.write("\n")
    return 0


def _cmd_refine(args: argparse.Namespace) -> int:
    report = refine_to_coverage(
        args.db,
        args.target_coverage,
        max_rounds=args.max_rounds,
        register_ports=not args.no_ports,
        convolve_limit=args.limit,
    )
    json.dump(report, sys.stdout, indent=2, default=str)
    sys.stdout.write("\n")
    return 0 if report.get("reached_target") or args.allow_partial else 1


def _cmd_crystal_info(args: argparse.Namespace) -> int:
    info = CrystalPackager.info(args.bundle)
    json.dump(info, sys.stdout, indent=2, default=str)
    sys.stdout.write("\n")
    return 0


def _cmd_train_window(args: argparse.Namespace) -> int:
    from .torch.train_window import TrainWindowConfig, run_train_window

    config = TrainWindowConfig(
        crystal_bundle=Path(args.crystal),
        max_steps=args.max_steps,
        wall_clock_budget_sec=args.wall_clock_budget_sec,
        dataset=args.dataset,
        tokens_file=args.tokens_file or None,
        db_path=args.db or None,
        dry_run=args.dry_run,
        allow_mutations=args.allow_mutations,
    )
    result = run_train_window(config, force=args.force)
    json.dump(result.as_dict(), sys.stdout, indent=2, default=str)
    sys.stdout.write("\n")
    if args.dry_run:
        return 0
    return 0 if result.ran or result.reason == "train_window_off" else 1


def _cmd_tool_pass(args: argparse.Namespace) -> int:
    streams = [s.strip() for s in args.streams.split(",") if s.strip()] or None
    if args.translation_key:
        from .tool_pass import TokenToolPass

        runner = TokenToolPass.from_db(args.db)
        runner.strict_receipts = args.strict_receipts
        try:
            result = runner.run(args.translation_key, streams=streams)
        finally:
            if runner.geometry is not None:
                runner.geometry.close()
            runner.links.close()
        json.dump(result.as_dict(), sys.stdout, indent=2, default=str)
        sys.stdout.write("\n")
        if args.strict_receipts and not all(r.ok for r in result.receipts):
            return 1
        return 0
    report = run_tool_pass_batch(
        args.db,
        max_keys=args.max_keys,
        streams=streams,
        strict_receipts=args.strict_receipts,
    )
    json.dump(report, sys.stdout, indent=2, default=str)
    sys.stdout.write("\n")
    return 0 if report.get("step_errors", 0) == 0 else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="cmplx.transform")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_fwd = sub.add_parser("forward", help="Run one forward pass and print the summary.")
    p_fwd.add_argument("--ribbon", required=True, help="Ribbon content to embed.")
    p_fwd.add_argument("--num-layers", type=int, default=2)
    p_fwd.add_argument("--output-mode", default="json", choices=("json", "etp", "raw"))
    p_fwd.add_argument("--production", action="store_true", help="Use ProductionTransformerConfig preset.")
    p_fwd.add_argument("--crystal", default="", help="Crystal bundle path (sets DB for shell bind).")
    p_fwd.add_argument("--db", default="", help="Token index DB for shell bind.")
    p_fwd.add_argument("--no-ports", action="store_true")
    p_fwd.set_defaults(func=_cmd_forward)

    p_cfg = sub.add_parser("config-dump", help="Print the default config as JSON.")
    p_cfg.add_argument("--num-layers", type=int, default=4)
    p_cfg.set_defaults(func=_cmd_config_dump)

    p_idx = sub.add_parser(
        "build-index",
        help="Build the quad-bond token index with warm-start cache reuse.",
    )
    p_idx.add_argument("--levels", default="1,2,3", help="Comma-separated levels.")
    p_idx.add_argument("--alphabet", default="", help="Characters to enumerate (default: a-z).")
    p_idx.add_argument("--languages", default="any,english", help="Comma-separated language filter names.")
    p_idx.add_argument("--case-modes", default="", help="Comma-separated case modes.")
    p_idx.add_argument("--lib", action="append", default=[], help="Rule library path (repeatable).")
    p_idx.add_argument("--db", default=DEFAULT_TOKEN_INDEX_DB, help="SQLite output path.")
    p_idx.add_argument("--max-entries", type=int, default=None)
    p_idx.add_argument("--progress-every", type=int, default=1000)
    p_idx.set_defaults(func=_cmd_build_index)

    p_stats = sub.add_parser("index-stats", help="Print summary statistics for an existing token index DB.")
    p_stats.add_argument("--db", default=DEFAULT_TOKEN_INDEX_DB)
    p_stats.set_defaults(func=_cmd_index_stats)

    p_tmpl = sub.add_parser("template-stats", help="Template frame coverage report.")
    p_tmpl.add_argument("--db", default=DEFAULT_TOKEN_INDEX_DB)
    p_tmpl.set_defaults(func=_cmd_template_stats)

    p_ref = sub.add_parser("refine", help="Run index mutations toward target slot coverage.")
    p_ref.add_argument("--db", default=DEFAULT_TOKEN_INDEX_DB)
    p_ref.add_argument("--target-coverage", type=float, default=0.45)
    p_ref.add_argument("--max-rounds", type=int, default=5)
    p_ref.add_argument("--no-ports", action="store_true")
    p_ref.add_argument(
        "--allow-partial",
        action="store_true",
        help="Exit 0 even when target coverage is not reached.",
    )
    p_ref.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Max token_bonds rows per convolve pass (large DB safety).",
    )
    p_ref.set_defaults(func=_cmd_refine)

    p_lval = sub.add_parser("lib-validate", help="Validate rule library YAML files.")
    p_lval.add_argument("--lib", default="data/rule_libs")
    p_lval.set_defaults(func=_cmd_lib_validate)

    p_llist = sub.add_parser("lib-list", help="List rule library YAML files.")
    p_llist.add_argument("--lib", default="data/rule_libs")
    p_llist.set_defaults(func=_cmd_lib_list)

    p_mean = sub.add_parser("meaning-query", help="Query address_meaning rows.")
    p_mean.add_argument("--db", default=DEFAULT_TOKEN_INDEX_DB)
    p_mean.add_argument("--snap-key", default="")
    p_mean.add_argument("--label", default="")
    p_mean.add_argument("--doc", default="")
    p_mean.add_argument("--limit", type=int, default=50)
    p_mean.set_defaults(func=_cmd_meaning_query)

    p_ing = sub.add_parser("ingest", help="Ingest a corpus directory into the token index.")
    p_ing.add_argument("--root", required=True)
    p_ing.add_argument(
        "--stream",
        default="en",
        choices=("en", "native", "math", "notation"),
        help="Token stream (en hub or sidecar native/math/notation).",
    )
    p_ing.add_argument(
        "--lib",
        default=None,
        help="YAML lib path for native/math/notation encoders.",
    )
    p_ing.add_argument("--lib-paths", action="append", default=[], dest="lib_paths")
    p_ing.add_argument("--db", default=DEFAULT_TOKEN_INDEX_DB)
    p_ing.add_argument("--no-ports", action="store_true")
    p_ing.add_argument("--max-files", type=int, default=None)
    p_ing.set_defaults(func=_cmd_ingest)

    p_morph = sub.add_parser("morph-probe", help="Surface morphism verdict (typo vs intentional).")
    p_morph.add_argument("--concat-a", required=True)
    p_morph.add_argument("--concat-b", required=True)
    p_morph.add_argument(
        "--notation-equiv",
        action="store_true",
        help="Require notation YAML equivalence (e.g. - vs U+2212).",
    )
    p_morph.set_defaults(func=_cmd_morph_probe)

    p_adm = sub.add_parser("admit", help="Check shell admission for a token.")
    p_adm.add_argument("--token", required=True)
    p_adm.add_argument("--lang", default="any")
    p_adm.add_argument("--db", default=DEFAULT_TOKEN_INDEX_DB)
    p_adm.set_defaults(func=_cmd_admit)

    p_cmp = sub.add_parser("complete", help="Complete a partial token window.")
    p_cmp.add_argument("--partial", required=True)
    p_cmp.add_argument("--max-candidates", type=int, default=64)
    p_cmp.add_argument("--db", default=DEFAULT_TOKEN_INDEX_DB)
    p_cmp.set_defaults(func=_cmd_complete)

    p_cry = sub.add_parser("crystallize", help="Pack index + meaning into a crystal bundle.")
    p_cry.add_argument("--name", required=True)
    p_cry.add_argument("--db", default=DEFAULT_TOKEN_INDEX_DB)
    p_cry.add_argument("--lib", default="data/rule_libs")
    p_cry.add_argument("--out", required=True)
    p_cry.set_defaults(func=_cmd_crystallize)

    p_cinfo = sub.add_parser("crystal-info", help="Inspect a crystal bundle.")
    p_cinfo.add_argument("--bundle", required=True)
    p_cinfo.set_defaults(func=_cmd_crystal_info)

    p_tw = sub.add_parser(
        "train-window",
        help="Bounded train window (admit-mask substrate loop; optional CMPLX_HF_MODEL).",
    )
    p_tw.add_argument("--crystal", required=True, help="Crystal bundle path.")
    p_tw.add_argument(
        "--dataset",
        default="identity_review",
        help="Dataset id or path hint (default: identity_review bonds).",
    )
    p_tw.add_argument("--max-steps", type=int, default=10)
    p_tw.add_argument("--wall-clock-budget-sec", type=float, default=120.0)
    p_tw.add_argument("--tokens-file", default="", help="Newline-delimited token list.")
    p_tw.add_argument("--db", default="", help="Override token index DB for tokens.")
    p_tw.add_argument("--dry-run", action="store_true", help="Plan only, no steps.")
    p_tw.add_argument("--force", action="store_true", help="Bypass env gate (tests).")
    p_tw.add_argument(
        "--allow-mutations",
        action="store_true",
        help="Document intent to allow port mutations during window (not applied in phase A).",
    )
    p_tw.set_defaults(func=_cmd_train_window)

    p_tp = sub.add_parser("tool-pass", help="Run TarPit-first tool chain per translation_key.")
    p_tp.add_argument("--db", default=DEFAULT_TOKEN_INDEX_DB)
    p_tp.add_argument("--max-keys", type=int, default=None)
    p_tp.add_argument(
        "--streams",
        default="",
        help="Comma-separated streams (en,native,math,notation); default all.",
    )
    p_tp.add_argument("--strict-receipts", action="store_true")
    p_tp.add_argument("--translation-key", default="", help="Single key instead of batch.")
    p_tp.set_defaults(func=_cmd_tool_pass)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
