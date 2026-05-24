"""Smoke tests for prize-core Tier A falsification."""

from __future__ import annotations

import json
from pathlib import Path

from lattice_forge.falsify import run_tier_a, tier_a_break_specs


def test_tier_a_break_specs_cover_theorems():
    specs = tier_a_break_specs()
    break_ids = {row["break_id"] for row in specs}
    assert break_ids == {
        "B-T1",
        "B-T2",
        "B-T3",
        "B-T4",
        "B-T5",
        "B-T6",
        "B-T7",
        "B-T8",
        "B-BONUS",
        "B-WITNESS",
        "B-decomp",
    }


def test_run_tier_a_quick_passes():
    report = run_tier_a(quick=True)
    assert report["overall_status"] == "pass"
    assert report["failures"] == []
    assert len(report["breaks"]) == len(tier_a_break_specs())


def test_registry_jsonl_loads_and_lists_core_claims():
    registry_path = Path(__file__).resolve().parents[1] / "claims" / "registry.jsonl"
    rows = [json.loads(line) for line in registry_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    claim_ids = {row["claim_id"] for row in rows}
    for theorem in [f"T{i}" for i in range(1, 9)]:
        assert theorem in claim_ids
    for prize in ("P1", "P2", "P3"):
        assert prize in claim_ids
    t1 = next(row for row in rows if row["claim_id"] == "T1")
    assert t1["honesty_label"] == "PROVEN"
    assert t1["falsify_break"] == "B-T1"
    p3 = next(row for row in rows if row["claim_id"] == "P3")
    assert p3["honesty_label"] == "CONJ"
