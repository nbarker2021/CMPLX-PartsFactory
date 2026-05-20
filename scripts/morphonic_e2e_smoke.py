#!/usr/bin/env python
"""Morphonic E2E smoke: seed index → refine → crystallize → production forward.

Chains on a temp fixture DB (no identity_review corpus). Exit non-zero on failure.
Use --quick for CI-sized limits.
"""
from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "src"))

from cmplx.transform.config import ProductionTransformerConfig
from cmplx.transform.crystal_pack import CrystalPackager, SCHEMA_VERSION
from cmplx.transform.index_mutations import refine_to_coverage
from cmplx.transform.token_index.template_frame import template_report
from cmplx.transform.ingest import MultistreamIngestPolicy, ingest_multistream
from cmplx.transform.shell import MorphonShell
from cmplx.transform.shell_config import ShellConfig
from cmplx.transform.token_index import (
    CaseMode,
    TokenIndexBuildConfig,
    TokenIndexBuilder,
    TokenIndexStore,
    any_filter,
)
from cmplx.transform.transformer import GeometricTransformer


def _seed_corpus(root: Path) -> None:
    root.mkdir(parents=True, exist_ok=True)
    (root / "smoke_en.md").write_text(
        "# Morphonic smoke\n\nEight-char bond windows admit substrate tokens.\n",
        encoding="utf-8",
    )
    (root / "smoke_native.md").write_text(
        "Substrat morphonique admet fenetres de liaison.\n",
        encoding="utf-8",
    )


def _seed_build_index(db: Path, *, quick: bool) -> None:
    alphabet = tuple("abcde") if quick else tuple("abcdefghij")
    levels = (1, 2) if quick else (1, 2, 3)
    builder = TokenIndexBuilder(
        TokenIndexBuildConfig(
            levels=levels,
            alphabet=alphabet,
            case_modes=[CaseMode.LOWER],
            languages=[any_filter()],
            db_path=str(db),
            progress_every=0,
            max_entries=120 if quick else 400,
            register_ports=False,
        )
    )
    builder.build()
    builder.store.close()


def _pick_ribbon(db: Path) -> str:
    store = TokenIndexStore(str(db))
    try:
        row = store._conn.execute(
            "SELECT concat FROM token_bonds ORDER BY bond_level LIMIT 1"
        ).fetchone()
    finally:
        store.close()
    if not row:
        raise RuntimeError("no token_bonds rows after seed")
    return str(row[0])


def _production_db_gate(
    db: Path,
    *,
    crystal: Path | None = None,
) -> dict:
    """Post-chain gate for identity_review production paths (optional in CI)."""
    gate: dict = {"production_db": str(db), "db_exists": db.is_file()}
    if not db.is_file():
        gate["skipped"] = "production db not present"
        return gate

    report = template_report(db)
    sweep = report.get("forced_cell_sweep_lower_any") or {}
    gate["forced_pct"] = sweep.get("forced_pct")
    slot_summary = report.get("slot_summary") or {}
    gate["aggregate_slot_coverage"] = slot_summary.get("aggregate_coverage")

    bundle = crystal or (REPO_ROOT / "crystals" / "identity_review.crystal")
    gate["production_crystal"] = str(bundle)
    if bundle.exists():
        info = CrystalPackager.info(bundle)
        manifest = info.get("manifest") or info
        schema = manifest.get("schema_version") if isinstance(manifest, dict) else None
        gate["production_schema_version"] = schema
        if schema != SCHEMA_VERSION:
            raise RuntimeError(
                f"production crystal schema {schema!r} != {SCHEMA_VERSION}"
            )
    else:
        gate["production_crystal_skipped"] = "bundle not present"
    return gate


def run_smoke(
    *,
    quick: bool,
    use_ingest: bool,
    production_db: Path | None = None,
    production_crystal: Path | None = None,
) -> dict:
    lib = REPO_ROOT / "data" / "rule_libs"
    if not lib.is_dir():
        raise FileNotFoundError(f"rule_libs missing: {lib}")

    with tempfile.TemporaryDirectory(prefix="morphonic_e2e_") as tmp:
        tmp_path = Path(tmp)
        db = tmp_path / "token_index.sqlite"
        crystal_dir = tmp_path / "e2e.crystal"
        corpus = tmp_path / "corpus"

        if use_ingest:
            _seed_corpus(corpus)
            policy = MultistreamIngestPolicy(streams=("en",), en_first=True)
            stats = ingest_multistream(
                corpus,
                db=db,
                policy=policy,
                max_files=2,
                register_ports=False,
            )
            if not stats.get("en") or stats["en"].chunks_seen < 1:
                raise RuntimeError(f"ingest produced no EN chunks: {stats}")
        else:
            _seed_build_index(db, quick=quick)

        convolve_limit = 80 if quick else 500
        refine_report = refine_to_coverage(
            db,
            0.1,
            max_rounds=2 if quick else 4,
            register_ports=False,
            convolve_limit=convolve_limit,
        )
        if not refine_report.get("reached_target") and not refine_report.get("rounds"):
            raise RuntimeError("refine did not reach target and produced no rounds")

        packager = CrystalPackager()
        crystal = packager.pack("e2e_smoke", db=str(db), libs=str(lib), out=str(crystal_dir))
        info = CrystalPackager.info(crystal_dir)
        manifest = info.get("manifest") or info
        schema = manifest.get("schema_version") if isinstance(manifest, dict) else None
        if schema and schema != SCHEMA_VERSION:
            raise RuntimeError(f"unexpected schema_version {schema!r} (want {SCHEMA_VERSION})")

        ribbon = _pick_ribbon(db)
        bundle_db = crystal_dir / "token_index.sqlite"
        if not bundle_db.is_file():
            raise FileNotFoundError(f"crystal missing token_index.sqlite: {bundle_db}")

        store = TokenIndexStore(str(bundle_db))
        shell = MorphonShell(ShellConfig(), store)
        try:
            admit = shell.admit(ribbon)
            if not admit.admitted:
                raise RuntimeError(f"ribbon not admitted: {ribbon!r} ({admit.reason})")
            model = GeometricTransformer(
                ProductionTransformerConfig(register_ports_on_init=False),
                shell=shell,
            )
            out = model.forward(ribbon)
            if len(out.layer_traces) != 8:
                raise RuntimeError(
                    f"production forward expected 8 layer traces, got {len(out.layer_traces)}"
                )
            repeat = model.forward(ribbon)
            if not repeat.speedlight_hit:
                raise RuntimeError("production forward second call expected speedlight_hit")
        finally:
            store.close()

        summary = {
            "ok": True,
            "quick": quick,
            "seed": "ingest" if use_ingest else "build-index",
            "refine": refine_report,
            "crystal_id": crystal.crystal_id,
            "schema_version": schema or SCHEMA_VERSION,
            "ribbon": ribbon,
            "num_layer_traces": len(out.layer_traces),
            "cache_key": out.cache_key,
        }
        if production_db is not None:
            summary["production_gate"] = _production_db_gate(
                production_db,
                crystal=production_crystal,
            )
        return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Morphonic substrate E2E smoke.")
    parser.add_argument(
        "--quick",
        action="store_true",
        help="CI-sized limits (small alphabet, convolve cap, fewer refine rounds).",
    )
    parser.add_argument(
        "--ingest",
        action="store_true",
        help="Seed via multistream ingest instead of build-index (slower).",
    )
    parser.add_argument(
        "--production-db",
        nargs="?",
        const=REPO_ROOT / "data" / "token_index_identity_review.sqlite",
        default=None,
        type=Path,
        metavar="PATH",
        help=(
            "After fixture chain, verify production DB template stats and "
            "crystal schema (flag alone → data/token_index_identity_review.sqlite)."
        ),
    )
    parser.add_argument(
        "--production-crystal",
        type=Path,
        default=None,
        metavar="PATH",
        help="Crystal bundle for --production-db gate (default: crystals/identity_review.crystal).",
    )
    args = parser.parse_args(argv)
    try:
        summary = run_smoke(
            quick=args.quick,
            use_ingest=args.ingest,
            production_db=args.production_db,
            production_crystal=args.production_crystal,
        )
    except Exception as exc:
        json.dump({"ok": False, "error": str(exc)}, sys.stderr, indent=2)
        sys.stderr.write("\n")
        return 1
    json.dump(summary, sys.stdout, indent=2, default=str)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
