"""Parametrized coverage for ingested superpermutation JSON (n=5..8)."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from cmplx.primitives.superperm import coverage_check, load_superperm_record, status_for_n

REPO = Path(__file__).resolve().parents[2]
DATA = REPO / "data" / "superpermutations"


@pytest.mark.parametrize("n,expected_len", [(5, 153), (6, 873), (7, 5908), (8, 46205)])
def test_committed_json_coverage(n: int, expected_len: int):
    path = DATA / f"n{n}.json"
    if not path.is_file():
        pytest.skip(f"{path.name} not committed yet")
    rec = json.loads(path.read_text(encoding="utf-8"))
    if rec.get("status") != "validated":
        pytest.skip(f"n={n} not validated")
    sp = rec.get("superpermutation")
    assert sp
    assert len(sp) == expected_len
    assert coverage_check(sp, n=n)


def test_n5_canonical_matches_runtime():
    if status_for_n(5) != "validated":
        pytest.skip("n5 not validated")
    rec = load_superperm_record(5)
    canonical = rec["superpermutation"]
    assert len(canonical) == 153
    assert coverage_check(canonical, n=5)
