#!/usr/bin/env python3
"""Exhaust lattice forms accessible to 24D terminals + quadrant Weyl + E8 pod bijection."""
from __future__ import annotations

import argparse
import json
import os
import sys
import uuid
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
_SRC = _ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from lattice_forge.backwalk.lattice_space_job import run_lattice_space_exhaustion  # noqa: E402
from lattice_forge.backwalk.schema import WorkStore  # noqa: E402
from lattice_forge.seed import SeedStore  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Lattice space exhaustion (quadrant Weyl method)")
    parser.add_argument("--work-db", type=Path, default=Path("/data/backwalk_work.db"))
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    work_db = args.work_db.resolve()
    report_path = work_db.parent / "lattice_space_exhaustion_report.json"

    if args.dry_run:
        print(
            json.dumps(
                {
                    "work_db": str(work_db),
                    "phases": [
                        "lattice_catalog",
                        "weyl_quadrant_shards",
                        "e8_pod_assign",
                        "proof_capture",
                    ],
                    "weyl_batches": 200,
                    "e8_weyl_order": 696729600,
                },
                indent=2,
            )
        )
        return 0

    seed_before = SeedStore.packaged().verify()
    run_id = str(uuid.uuid4())

    with WorkStore(work_db) as store:
        result = run_lattice_space_exhaustion(
            store,
            resume=args.resume,
            max_rows_per_weyl_batch=int(os.environ.get("WEYL_BOND_MAX_ROWS_PER_BATCH", "64")),
            weyl_sleep_ms=int(os.environ.get("WEYL_BOND_BATCH_SLEEP_MS", "50")),
            mirror_oloid=os.environ.get("WEYL_BOND_MIRROR_OLOID", "1") != "0",
            max_library_needs=int(os.environ.get("LATTICE_SPACE_MAX_LIBRARY_NEEDS", "200")),
            max_pod_per_lattice=int(os.environ["LATTICE_SPACE_MAX_POD_PER_LATTICE"])
            if os.environ.get("LATTICE_SPACE_MAX_POD_PER_LATTICE")
            else None,
        )

    seed_after = SeedStore.packaged().verify()
    report = {
        "run_id": run_id,
        "status": "pass",
        "work_db": str(work_db),
        "work_db_bytes": work_db.stat().st_size if work_db.exists() else 0,
        "seed_verify_before": seed_before,
        "seed_verify_after": seed_after,
        **result,
    }
    report_path.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    print(json.dumps(report, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
