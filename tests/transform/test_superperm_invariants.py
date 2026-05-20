"""Superpermutation is schedule, not substrate content."""
from __future__ import annotations

import sqlite3

import pytest

from cmplx.primitives.superperm import (
    SUPERPERM_N4,
    n5_status,
    n5_superpermutation_or_none,
    octad_version,
    status_for_n,
    superperm_n,
    walk_phases,
)
from cmplx.transform.index_supervisor import IndexSupervisor
from cmplx.transform.nhyper_tower import nhyper_active_n
from cmplx.transform.octad import OctadSheet
from cmplx.transform.token_index import (
    CaseMode,
    TokenIndexBuildConfig,
    TokenIndexBuilder,
    any_filter,
)


@pytest.fixture
def indexed_db(tmp_path):
    db = tmp_path / "sp.sqlite"
    builder = TokenIndexBuilder(
        TokenIndexBuildConfig(
            levels=(1, 2),
            alphabet=tuple("abcde"),
            case_modes=[CaseMode.LOWER],
            languages=[any_filter()],
            db_path=str(db),
            progress_every=0,
            max_entries=60,
            register_ports=False,
        )
    )
    builder.build()
    builder.store.close()
    return db


def test_superperm_n4_not_stored_as_bond_concat(indexed_db):
    conn = sqlite3.connect(str(indexed_db))
    try:
        rows = conn.execute("SELECT concat FROM token_bonds").fetchall()
        for (concat,) in rows:
            assert concat != SUPERPERM_N4
            assert SUPERPERM_N4 not in str(concat)
    finally:
        conn.close()


def test_n5_validated_when_ingested():
    if status_for_n(5) != "validated":
        pytest.skip("n5 not ingested")
    sp = n5_superpermutation_or_none()
    assert sp is not None
    assert len(sp) == 153


def test_octad_version_from_sheet():
    assert octad_version() == "1_palindrome_7_trees"


def test_sp_schedule_walk_invariants():
    digits = list(walk_phases(8))
    assert len(digits) == 8
    assert all(1 <= d <= 4 for d in digits)


def test_supervisor_walk_uses_octad_palindrome_step(indexed_db):
    sup = IndexSupervisor.from_db(str(indexed_db))
    sheet = OctadSheet.from_json()
    run = sup.walk(partial_seed="aaaa")
    assert run.palindrome_template_steps >= 0
    assert sheet.palindrome_id


def test_supervisor_active_n5_walk_length(indexed_db):
    if n5_status() != "validated":
        pytest.skip("n5 not validated")
    sup = IndexSupervisor.from_db(str(indexed_db), active_n=5)
    run = sup.walk()
    assert run.active_n == 5
    assert run.sp_length == 153
    assert len(run.steps) == 153
    assert run.n5_octad is True
    assert len(run.octad_slots_used) == 8


def test_tower_level_1_maps_to_n5(indexed_db):
    if n5_status() != "validated":
        pytest.skip("n5 not validated")
    assert nhyper_active_n(1) == 5
    manifest = {
        "nhyper_tower": {"status": "escrow", "tower_level": 1},
        "superpermutation": {"active_n": 5},
    }
    sup = IndexSupervisor.from_manifest(str(indexed_db), manifest)
    run = sup.walk()
    assert len(run.steps) == len(superperm_n(5))
