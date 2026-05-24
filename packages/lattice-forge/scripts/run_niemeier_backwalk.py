#!/usr/bin/env python3
"""Materialize backward Niemeier category slices into a writable work SQLite DB."""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import uuid
from dataclasses import asdict
from pathlib import Path

# Allow running as script from repo root or package dir
_ROOT = Path(__file__).resolve().parents[1]
_SRC = _ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from lattice_forge.backwalk import (  # noqa: E402
    PILOT_TERMINAL_IDS,
    WorkStore,
    all_niemeier_terminal_ids,
    materialize_exceptional_spine,
    materialize_terminals,
)
from lattice_forge.seed import SeedStore  # noqa: E402


def _parse_exceptionals(raw: str) -> set[str]:
    return {x.strip() for x in raw.split(",") if x.strip()}


def _terminals_for_phase(phase: str, explicit: str | None) -> list[str]:
    if explicit:
        return [t.strip() for t in explicit.split(",") if t.strip()]
    if phase == "pilot":
        return list(PILOT_TERMINAL_IDS)
    if phase == "full24":
        return all_niemeier_terminal_ids()
    if phase == "exceptional-only":
        return []
    raise ValueError(f"unknown phase: {phase}")


def _expected_state_count(terminal_id: str) -> int | None:
    """Pilot acceptance counts from plan."""
    expected = {
        "Niemeier:Leech": 1,
        "Niemeier:D4^6": 7,
        "Niemeier:A2^12": 13,
        "Niemeier:A1^24": 25,
    }
    return expected.get(terminal_id)


def main() -> int:
    parser = argparse.ArgumentParser(description="Niemeier backward-category builder")
    parser.add_argument("--phase", choices=("pilot", "full24", "exceptional-only"), default="pilot")
    parser.add_argument("--terminals", default=None, help="Comma-separated terminal IDs")
    parser.add_argument("--work-db", type=Path, default=Path("data/backwalk_work.db"))
    parser.add_argument("--progress-jsonl", type=Path, default=None)
    parser.add_argument("--baseline-report", type=Path, default=None)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument(
        "--include-exceptionals",
        default=os.environ.get("BACKWALK_EXCEPTIONALS", "g2,f4,e6"),
    )
    parser.add_argument(
        "--involution-limit",
        type=int,
        default=None,
        help="Cap involutions per component (default: env BACKWALK_INVOLUTION_LIMIT or unlimited for pilot)",
    )
    args = parser.parse_args()

    inv_limit = args.involution_limit
    if inv_limit is None and os.environ.get("BACKWALK_INVOLUTION_LIMIT"):
        inv_limit = int(os.environ["BACKWALK_INVOLUTION_LIMIT"])
    if args.phase == "full24" and inv_limit is None:
        inv_limit = 50

    work_db = args.work_db.resolve()
    progress_path = args.progress_jsonl or work_db.parent / "progress.jsonl"
    baseline_path = args.baseline_report or work_db.parent / "baseline_report.json"

    seed_verify_before = SeedStore.packaged().verify()
    run_id = str(uuid.uuid4())
    config = {
        "phase": args.phase,
        "terminals": args.terminals,
        "involution_limit": inv_limit,
        "include_exceptionals": args.include_exceptionals,
        "resume": args.resume,
    }

    t0 = time.perf_counter()
    errors: list[str] = []

    with WorkStore(work_db) as store:
        store.start_run(run_id, args.phase, config)
        terminal_ids = _terminals_for_phase(args.phase, args.terminals)

        stats_list = []
        if terminal_ids:
            stats_list = materialize_terminals(
                store,
                terminal_ids,
                involution_limit=inv_limit,
                resume=args.resume,
            )

        ex_summary = materialize_exceptional_spine(
            store,
            include=_parse_exceptionals(args.include_exceptionals),
        )

        for st in stats_list:
            exp = _expected_state_count(st.terminal_id)
            if exp is not None and st.state_count != exp:
                errors.append(
                    f"{st.terminal_id}: expected {exp} states, got {st.state_count}"
                )
            peel_exp = max(0, st.state_count - 1)
            if st.peel_morphism_count != peel_exp:
                errors.append(
                    f"{st.terminal_id}: expected {peel_exp} peel morphisms, got {st.peel_morphism_count}"
                )

        if "g2" in args.include_exceptionals.lower() and "f4" in args.include_exceptionals.lower():
            if not ex_summary.get("g2_f4_path"):
                errors.append("exceptional spine missing G2->F4 path")

        if "e6" in args.include_exceptionals.lower():
            if store.count_exceptional_morphisms("cartan_extension") < 1 and "e7" in args.include_exceptionals.lower():
                errors.append("expected E6->E7 cartan_extension when e6,e7 enabled")

    seed_verify_after = SeedStore.packaged().verify()

    report = {
        "run_id": run_id,
        "phase": args.phase,
        "work_db": str(work_db),
        "work_db_bytes": work_db.stat().st_size if work_db.exists() else 0,
        "wall_seconds": time.perf_counter() - t0,
        "seed_verify_before": seed_verify_before,
        "seed_verify_after": seed_verify_after,
        "terminals": [asdict(s) for s in stats_list],
        "exceptional": ex_summary,
        "errors": errors,
        "status": "fail" if errors else "pass",
    }

    baseline_path.parent.mkdir(parents=True, exist_ok=True)
    baseline_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    with progress_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps({"event": "run_complete", **report}, default=str) + "\n")

    print(json.dumps(report, indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
