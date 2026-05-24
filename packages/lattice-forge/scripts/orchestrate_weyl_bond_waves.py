#!/usr/bin/env python3
"""Orchestrate podal/antipodal dual Weyl-bond batches (middle-in, middle-out)."""
from __future__ import annotations

import argparse
import gc
import json
import os
import sys
import time
import uuid
from pathlib import Path
from typing import Any

_ROOT = Path(__file__).resolve().parents[1]
_SRC = _ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from lattice_forge.backwalk.schema import WorkStore  # noqa: E402
from lattice_forge.backwalk.weyl_bond_dual import (  # noqa: E402
    QUADRANT_COUNT,
    WeylBondBatchSpec,
    iter_batch_specs,
    materialize_weyl_bond_batch,
)
from lattice_forge.backwalk.weyl_bond_quadrant import concatenate_quadrant_trees  # noqa: E402
from lattice_forge.seed import SeedStore  # noqa: E402


def _sort_specs(specs: list[WeylBondBatchSpec]) -> list[WeylBondBatchSpec]:
    """Construct poles→middle (depth desc), then read middle→poles (depth asc)."""

    def key(s: WeylBondBatchSpec) -> tuple:
        if s.direction == "construct_in":
            depth_key = -s.dual_depth
        else:
            depth_key = s.dual_depth
        return (s.direction, depth_key, s.source_group, s.target_group)

    return sorted(specs, key=key)


def main() -> int:
    parser = argparse.ArgumentParser(description="Weyl bond dual-wave orchestrator")
    parser.add_argument("--work-db", type=Path, default=Path("/data/backwalk_work.db"))
    parser.add_argument("--manifest", type=Path, default=None)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--max-rows-per-batch", type=int, default=None)
    parser.add_argument("--sleep-ms", type=int, default=None)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--quadrant",
        type=int,
        default=None,
        help="Run a single D4 quadrant search (0..3). Omit with --all-quadrants.",
    )
    parser.add_argument(
        "--all-quadrants",
        action="store_true",
        help="Run four quadrant searches then concatenate result tree (default).",
    )
    parser.add_argument(
        "--concat-only",
        action="store_true",
        help="Only merge existing quadrant rows into weyl_bond_result_tree.",
    )
    args = parser.parse_args()

    max_rows = args.max_rows_per_batch
    if max_rows is None:
        max_rows = int(os.environ.get("WEYL_BOND_MAX_ROWS_PER_BATCH", "64"))
    sleep_ms = args.sleep_ms
    if sleep_ms is None:
        sleep_ms = int(os.environ.get("WEYL_BOND_BATCH_SLEEP_MS", "50"))
    mirror = os.environ.get("WEYL_BOND_MIRROR_OLOID", "1") != "0"

    work_db = args.work_db.resolve()
    manifest_path = args.manifest or work_db.parent / "weyl_bond_manifest.jsonl"
    report_path = work_db.parent / "weyl_bond_orchestrator_report.json"

    seed_before = SeedStore.packaged().verify()
    run_id = str(uuid.uuid4())

    if args.quadrant is not None and args.all_quadrants:
        print("Use either --quadrant N or --all-quadrants, not both", file=sys.stderr)
        return 2
    if args.quadrant is None and not args.all_quadrants and not args.concat_only:
        args.all_quadrants = True

    quadrant_plan: list[int | None]
    if args.concat_only:
        quadrant_plan = []
    elif args.quadrant is not None:
        quadrant_plan = [args.quadrant]
    else:
        quadrant_plan = list(range(QUADRANT_COUNT))

    specs: list[WeylBondBatchSpec] = []
    for q in quadrant_plan:
        specs.extend(list(iter_batch_specs(include_read_out=True, quadrant=q)))
    specs = _sort_specs(specs)

    if args.dry_run:
        print(
            json.dumps(
                {
                    "run_id": run_id,
                    "quadrant_plan": quadrant_plan,
                    "batch_count": len(specs),
                    "dry_run": True,
                },
                indent=2,
            )
        )
        return 0

    if args.concat_only:
        with WorkStore(work_db) as store:
            root = concatenate_quadrant_trees(
                store, tree_path="weyl_bond_result_tree.json"
            )
        print(json.dumps({"run_id": run_id, "concat_only": True, "total_bonds": root["total_bonds"]}, indent=2))
        return 0

    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    with manifest_path.open("w", encoding="utf-8") as mf:
        for spec in specs:
            mf.write(
                json.dumps(
                    {
                        "batch_id": spec.batch_id,
                        "wave_id": spec.wave_id,
                        "direction": spec.direction,
                        "dual_depth": spec.dual_depth,
                        "source_group": spec.source_group,
                        "target_group": spec.target_group,
                    }
                )
                + "\n"
            )

    t0 = time.perf_counter()
    errors: list[str] = []
    completed = 0
    skipped = 0
    total_rows = 0

    bonds_in_db = 0
    tree_root = None
    with WorkStore(work_db) as store:
        for spec in specs:
            if args.resume and store.is_weyl_batch_done(spec.batch_id):
                skipped += 1
                continue
            try:
                stats = materialize_weyl_bond_batch(
                    store,
                    spec,
                    max_rows=max_rows,
                    mirror_oloid=mirror,
                )
                store.weyl_batch_done(spec.batch_id, spec.wave_id, stats["rows_written"])
                completed += 1
                total_rows += stats["rows_written"]
            except Exception as exc:  # noqa: BLE001 — batch boundary must not kill orchestrator
                errors.append(f"{spec.batch_id}: {exc}")
            if sleep_ms > 0:
                time.sleep(sleep_ms / 1000.0)
            if completed % 10 == 0:
                gc.collect()
        bonds_in_db = store.count_weyl_bonds()
        tree_root: dict[str, Any] | None = None
        if args.all_quadrants or len(quadrant_plan) == QUADRANT_COUNT:
            tree_root = concatenate_quadrant_trees(
                store, tree_path="weyl_bond_result_tree.json"
            )

    seed_after = SeedStore.packaged().verify()
    report = {
        "run_id": run_id,
        "work_db": str(work_db),
        "work_db_bytes": work_db.stat().st_size if work_db.exists() else 0,
        "wall_seconds": time.perf_counter() - t0,
        "batch_total": len(specs),
        "batch_completed": completed,
        "batch_skipped": skipped,
        "weyl_bond_rows": total_rows,
        "weyl_bonds_in_db": bonds_in_db,
        "seed_verify_before": seed_before,
        "seed_verify_after": seed_after,
        "errors": errors,
        "status": "fail" if errors else "pass",
        "resource_limits": {
            "max_rows_per_batch": max_rows,
            "sleep_ms": sleep_ms,
            "mirror_oloid": mirror,
        },
        "quadrant_plan": quadrant_plan,
        "result_tree": tree_root,
    }
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
