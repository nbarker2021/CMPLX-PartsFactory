"""Smoke tests for prize-core falsify Tier A."""

from __future__ import annotations

import json
import pathlib

from lattice_forge.falsify import run_tier_a


def test_tier_a_quick_passes():
    report = run_tier_a(max_depth=256, quick=True)
    assert report["overall_status"] == "pass", report.get("failures")
    assert report["tier"] == "A"
    break_ids = {c["break_id"] for c in report["checks"]}
    assert "B-T1" in break_ids
    assert "B-decomp" in break_ids


def test_tier_a_honest_status_no_conj_upgrade():
    report = run_tier_a(max_depth=64, quick=True)
    for check in report["checks"]:
        status = check.get("status", "")
        assert status != "conj"
        if status == "pass_with_open_gaps":
            assert check["passed"] is False or check.get("not_in_ring1")


def test_registry_ring1_proven_claims_loaded():
    root = pathlib.Path(__file__).resolve().parents[1]
    registry = root / "claims" / "registry.jsonl"
    if not registry.is_file():
        return
    report = run_tier_a(max_depth=64, quick=True, registry_path=registry)
    ids = report.get("registry_ring1_proven_claim_ids", [])
    assert "T1" in ids
