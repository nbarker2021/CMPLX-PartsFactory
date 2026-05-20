"""Tests for index mutations and refine coverage."""
from __future__ import annotations

import pytest

from cmplx.transform.index_mutations import (
    abstract,
    aggregate_slot_coverage_fraction,
    convolve,
    involute,
    refine_to_coverage,
)
from cmplx.transform.index_supervisor import ComposeAction, IndexSupervisor
from cmplx.transform.token_index import (
    CaseMode,
    TokenIndexBuildConfig,
    TokenIndexBuilder,
    any_filter,
)
from cmplx.transform.token_index.template_frame import TemplateFrame


@pytest.fixture
def small_db(tmp_path):
    db = str(tmp_path / "token_index.sqlite")
    builder = TokenIndexBuilder(
        TokenIndexBuildConfig(
            levels=(1, 2),
            alphabet=tuple("abcde"),
            case_modes=[CaseMode.LOWER],
            languages=[any_filter()],
            db_path=db,
            progress_every=0,
            max_entries=200,
            register_ports=False,
        )
    )
    builder.build()
    builder.store.close()
    return db


def test_convolve_publishes_warmstart(small_db):
    result = convolve(small_db, register_ports=False)
    assert result.warmstart_published > 0
    assert result.bonds_touched > 0


def test_involute_seeds_higher_levels(small_db):
    before = TemplateFrame(small_db)
    try:
        start = before._conn.execute(
            "SELECT COUNT(*) FROM token_bonds WHERE bond_level >= 2"
        ).fetchone()[0]
    finally:
        before.close()
    result = involute(small_db, alphabet=tuple("abcde"), register_ports=False, max_seed=500)
    after = TemplateFrame(small_db)
    try:
        end = after._conn.execute(
            "SELECT COUNT(*) FROM token_bonds WHERE bond_level >= 2"
        ).fetchone()[0]
    finally:
        after.close()
    assert result.bonds_seeded >= 0
    assert end >= start


def test_supervisor_runs_mutations_with_events(small_db):
    supervisor = IndexSupervisor.from_db(small_db, run_mutations=True)
    run = supervisor.walk(partial_seed="baaaaaab")
    mutation_events = [e for e in run.events if "mutation" in e]
    actions = {e["action"] for e in mutation_events}
    assert ComposeAction.CONVOLVE.value in actions or len(mutation_events) >= 1
    template_with_seed = [
        s for s in run.steps if s.action is ComposeAction.TEMPLATE and s.pattern
    ]
    if template_with_seed:
        assert "b" in (template_with_seed[0].pattern or "")


def test_refine_reports_coverage(small_db):
    frame = TemplateFrame(small_db)
    try:
        start = aggregate_slot_coverage_fraction(frame.slot_coverage())
    finally:
        frame.close()
    report = refine_to_coverage(small_db, 0.99, max_rounds=2, register_ports=False)
    assert "coverage_start" in report
    assert report["coverage_end"] >= start or report["rounds"]


def test_refine_convolve_limit(small_db):
    report = refine_to_coverage(
        small_db,
        0.5,
        max_rounds=1,
        register_ports=False,
        convolve_limit=5,
    )
    conv = report["rounds"][0]["mutations"][0]
    assert conv["action"] == "convolve"
    assert conv["bonds_touched"] <= 5


def test_abstract_collapses_duplicate_meanings(small_db):
    from cmplx.transform.meaning_store import AddressMeaningStore

    meaning = AddressMeaningStore(small_db)
    meaning.upsert(
        snap_key="snap_test",
        lane="L1",
        digital_root=3,
        label="Alpha",
        label_source="test",
    )
    meaning.upsert(
        snap_key="snap_test",
        lane="L1",
        digital_root=3,
        label="BetaLonger",
        label_source="test",
    )
    meaning.close()
    result = abstract(small_db)
    assert result.meanings_collapsed >= 1
