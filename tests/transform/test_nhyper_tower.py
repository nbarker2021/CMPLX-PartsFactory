"""NHyperTower escrow wiring and tower_level manifest resolution."""
from __future__ import annotations

import pytest

from cmplx.transform.index_supervisor import IndexSupervisor
from cmplx.primitives.superperm import status_for_n, superperm_n
from cmplx.transform.nhyper_tower import (
    build_nhyper_escrow_state,
    load_nhyper_from_manifest,
    nhyper_active_n,
    query_nhyper_witness_paths,
    tower_level_for_supervisor,
)
from cmplx.transform.token_index import (
    CaseMode,
    TokenIndexBuildConfig,
    TokenIndexBuilder,
    any_filter,
)


@pytest.fixture
def indexed_db(tmp_path):
    db = str(tmp_path / "token_index.sqlite")
    builder = TokenIndexBuilder(
        TokenIndexBuildConfig(
            levels=(1, 2),
            alphabet=tuple("abcde"),
            case_modes=[CaseMode.LOWER],
            languages=[any_filter()],
            db_path=db,
            progress_every=0,
            max_entries=80,
            register_ports=False,
        )
    )
    builder.build()
    builder.store.close()
    return db


def test_nhyper_escrow_state_has_status():
    state = build_nhyper_escrow_state(tower_level=1)
    block = state.as_dict()
    assert block["status"] == "escrow"
    assert block["tower_level"] == 1


def test_tower_level_from_manifest_override():
    manifest = {"nhyper_tower": {"status": "escrow", "tower_level": 2}}
    assert tower_level_for_supervisor(manifest, override=1) == 1
    assert tower_level_for_supervisor(manifest) == 2


def test_supervisor_from_manifest_respects_tower_level(indexed_db):
    manifest = {
        "nhyper_tower": {"status": "escrow", "tower_level": 1},
        "superpermutation": {"octad_version": "1_palindrome_7_trees"},
    }
    sup = IndexSupervisor.from_manifest(indexed_db, manifest)
    run = sup.walk()
    assert run.tower_level == 1
    loaded = load_nhyper_from_manifest(manifest)
    assert loaded.status == "escrow"


def test_query_nhyper_witness_paths_optional():
    paths = query_nhyper_witness_paths(atomic_db="/nonexistent/atomic.sqlite")
    assert paths == []


@pytest.mark.parametrize(
    "level,expected_n,expected_len",
    [(0, 4, 33), (1, 5, 153), (2, 6, 873)],
)
def test_nhyper_active_n_table(level, expected_n, expected_len):
    assert nhyper_active_n(level) == expected_n
    if status_for_n(expected_n) != "validated":
        pytest.skip(f"n={expected_n} not validated")
    assert len(superperm_n(expected_n)) == expected_len


def test_supervisor_tower_level_2_walk_length(indexed_db):
    if status_for_n(6) != "validated":
        pytest.skip("n6 not validated")
    manifest = {"nhyper_tower": {"status": "escrow", "tower_level": 2}}
    sup = IndexSupervisor.from_manifest(indexed_db, manifest)
    run = sup.walk()
    assert run.active_n == 6
    assert len(run.steps) == 873


def test_atomic_index_witness_query_when_present():
    from pathlib import Path

    repo = Path(__file__).resolve().parents[2]
    atomic = repo / "data" / "atomic_index.sqlite"
    if not atomic.is_file():
        pytest.skip("atomic_index.sqlite not present")
    paths = query_nhyper_witness_paths(atomic_db=atomic, limit=5)
    assert isinstance(paths, list)
