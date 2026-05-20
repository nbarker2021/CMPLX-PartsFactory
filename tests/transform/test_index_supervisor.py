"""Tests for IndexSupervisor and OctadSheet."""
from __future__ import annotations

import pytest

from cmplx.primitives.superperm import SUPERPERM_N4
from cmplx.transform.index_supervisor import ComposeAction, IndexSupervisor
from cmplx.transform.octad import OctadSheet
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
            max_entries=500,
            register_ports=False,
        )
    )
    builder.build()
    builder.store.close()
    return db


def test_octad_sheet_has_pal_and_seven_trees():
    sheet = OctadSheet.from_json()
    assert sheet.n == 4
    assert sheet.slot_id(0) == sheet.palindrome_id
    assert len(sheet.tree_ids) == 7
    assert sheet.slot_id(1) == sheet.tree_ids[0]
    assert sheet.partial_pattern("1", phase=0) == "a??????a"


def test_supervisor_walk_length(indexed_db):
    supervisor = IndexSupervisor.from_db(indexed_db)
    run = supervisor.walk()
    assert len(run.steps) == len(SUPERPERM_N4)
    template_steps = [s for s in run.steps if s.action is ComposeAction.TEMPLATE]
    assert len(template_steps) == sum(1 for ch in SUPERPERM_N4 if ch == "1")
    pal_steps = [s for s in run.steps if s.phase == 0 and s.action is ComposeAction.TEMPLATE]
    assert len(pal_steps) >= 1


def test_forced_cell_report(indexed_db):
    supervisor = IndexSupervisor.from_db(indexed_db)
    report = supervisor.forced_cell_report()
    assert "baseline_forced_pct" in report
    assert report["palindrome_template_steps"] >= 1
    assert "run" in report


def test_supervisor_tower_level_filters_templates(indexed_db):
    full = IndexSupervisor.from_db(indexed_db, tower_level=None)
    shallow = IndexSupervisor.from_db(indexed_db, tower_level=1)
    full_run = full.walk()
    shallow_run = shallow.walk()
    assert full_run.tower_level is None
    assert shallow_run.tower_level == 1
    full_admits = sum(1 for s in full_run.steps if s.admit is not None)
    shallow_admits = sum(1 for s in shallow_run.steps if s.admit is not None)
    assert shallow_admits <= full_admits
    report = shallow.forced_cell_report()
    assert report["tower_level"] == 1
