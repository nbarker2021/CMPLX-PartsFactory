"""n=5 octad: palindrome + seven tree minimals must all be scheduled."""
from __future__ import annotations

import pytest

from cmplx.primitives.n5_octad import load_n5_octad_schedule
from cmplx.primitives.superperm import (
    coverage_check,
    n5_alternates,
    n5_status,
    n5_tree_alternates,
)
from cmplx.transform.index_supervisor import IndexSupervisor
from cmplx.transform.token_index import (
    CaseMode,
    TokenIndexBuildConfig,
    TokenIndexBuilder,
    any_filter,
)


@pytest.fixture
def indexed_db(tmp_path):
    db = tmp_path / "n5.sqlite"
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


@pytest.mark.skipif(n5_status() != "validated", reason="n5 not ingested")
def test_eight_minimals_all_pass_coverage():
    alts = n5_alternates()
    assert len(alts) == 8
    assert sum(1 for s in alts if s == s[::-1]) == 1
    assert len(n5_tree_alternates()) == 7
    for s in alts:
        assert len(s) == 153
        assert coverage_check(s, n=5)


@pytest.mark.skipif(n5_status() != "validated", reason="n5 not ingested")
def test_n5_octad_schedule_has_eight_distinct_slots():
    schedule = load_n5_octad_schedule()
    assert schedule.walk_length == 153
    assert len(schedule.slots) == 8
    assert schedule.palindrome_slot().is_palindrome
    assert len(schedule.tree_slots()) == 7
    sp_by_phase = {schedule.slot_at_phase(p).superpermutation for p in range(8)}
    assert len(sp_by_phase) == 8


@pytest.mark.skipif(n5_status() != "validated", reason="n5 not ingested")
def test_supervisor_uses_all_seven_trees_not_only_palindrome(indexed_db):
    sup = IndexSupervisor.from_db(str(indexed_db), active_n=5)
    run = sup.walk()
    assert run.n5_octad is True
    assert len(run.steps) == 153
    tree_labels = {
        s.sp_label for s in run.steps if s.phase != 0 and s.sp_label
    }
    assert len(tree_labels) == 7
    pal_steps = [s for s in run.steps if s.is_palindrome_sp]
    assert len(pal_steps) == 20  # steps where phase % 8 == 0
    assert all(s.is_palindrome_sp for s in pal_steps)
    tree_steps = [s for s in run.steps if not s.is_palindrome_sp]
    assert len(tree_steps) == 153 - len(pal_steps)
    # Each tree minimal must appear at its phase steps
    for phase in range(1, 8):
        phase_steps = [s for s in run.steps if s.phase == phase]
        assert phase_steps
        assert len({s.alternate_index for s in phase_steps}) == 1
        assert not phase_steps[0].is_palindrome_sp


@pytest.mark.skipif(n5_status() != "validated", reason="n5 not ingested")
def test_digit_at_step_matches_labeled_string():
    schedule = load_n5_octad_schedule()
    for i in range(153):
        phase, digit, slot = schedule.digit_at_step(i)
        assert digit == slot.superpermutation[i]
        assert schedule.slot_at_phase(phase).alternate_index == slot.alternate_index
