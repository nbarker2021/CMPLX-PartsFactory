"""
Smoke tests for cmplx.memory.mmdb — SQLite-backed Morphon storage.
"""
from __future__ import annotations

import pytest

from cmplx.addressing.mdhg import MDHG
from cmplx.geometry import Geometry
from cmplx.memory.mmdb import MMDB
from cmplx.morphon import Morphon, MorphonController, MorphonState


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def db():
    with MMDB(":memory:") as d:
        yield d


@pytest.fixture(autouse=True)
def _reset_controller():
    MorphonController.reset_for_tests()
    yield
    MorphonController.reset_for_tests()


# ---------------------------------------------------------------------------
# Lifecycle
# ---------------------------------------------------------------------------

def test_empty_db_count_is_zero(db):
    assert db.count() == 0


def test_store_then_fetch_round_trip(db):
    m = Morphon.forge(payload={"hello": "world"})
    m = m.transition_to(MorphonState.VALIDATING)
    db.store(m)
    fetched = db.fetch(m.id)
    assert fetched is not None
    assert fetched.id == m.id
    assert fetched.state is MorphonState.VALIDATING
    assert fetched.payload == m.payload


def test_store_preserves_receipt_chain(db):
    m = Morphon.forge(payload={"k": "v"})
    m = m.transition_to(MorphonState.VALIDATING)
    m = m.transition_to(MorphonState.POLICY_CHECK)
    n_receipts = len(m.receipts)
    db.store(m)
    fetched = db.fetch(m.id)
    assert len(fetched.receipts) == n_receipts


def test_fetch_unknown_returns_none(db):
    assert db.fetch("not-a-real-id") is None


def test_store_is_idempotent(db):
    m = Morphon.forge(payload={"k": "v"})
    db.store(m)
    db.store(m)
    db.store(m)
    assert db.count() == 1


def test_re_store_updates_state(db):
    m = Morphon.forge(payload={"k": "v"})
    db.store(m)
    m2 = m.transition_to(MorphonState.VALIDATING)
    db.store(m2)
    fetched = db.fetch(m.id)
    assert fetched.state is MorphonState.VALIDATING


def test_delete_removes_row(db):
    m = Morphon.forge(payload={"k": "v"})
    db.store(m)
    assert db.delete(m.id) is True
    assert db.fetch(m.id) is None
    assert db.delete(m.id) is False  # idempotent


# ---------------------------------------------------------------------------
# Indexed queries
# ---------------------------------------------------------------------------

def test_find_by_channel(db):
    # Set channels manually
    m1 = Morphon.forge(payload={"a": 1})
    m1.dr_channel = 3
    m2 = Morphon.forge(payload={"a": 2})
    m2.dr_channel = 3
    m3 = Morphon.forge(payload={"a": 3})
    m3.dr_channel = 7
    db.store(m1); db.store(m2); db.store(m3)

    ch3 = list(db.find_by_channel(3))
    assert {m.id for m in ch3} == {m1.id, m2.id}
    ch7 = list(db.find_by_channel(7))
    assert {m.id for m in ch7} == {m3.id}


def test_find_by_parent(db):
    parent = Morphon.forge(payload={"role": "parent"})
    child1 = parent.with_payload({"role": "child1"})
    child2 = parent.with_payload({"role": "child2"})
    db.store(parent); db.store(child1); db.store(child2)

    children = list(db.find_by_parent(parent.id))
    assert {m.id for m in children} == {child1.id, child2.id}


# ---------------------------------------------------------------------------
# Bridge integration — admit_and_store happy path with REAL components
# ---------------------------------------------------------------------------

class _PassThroughConstraints:
    """All morphons admitted. Used to test the wiring, not the policy."""
    def admit(self, morphon):
        return True, ""


def test_admit_and_store_with_real_providers(db):
    """End-to-end: morphon flows through real MDHG + Geometry + MMDB.

    This is the wiring proof — all three components built so far cooperate
    correctly through the MorphonController bridge."""
    controller = MorphonController.get()
    controller.register("constraints", _PassThroughConstraints())
    controller.register("addressing", MDHG())
    controller.register("geometry", Geometry())
    controller.register("memory", db)

    m = Morphon.forge(payload={"text": "hello, unified system"})
    stored = controller.admit_and_store(m)

    # All projections populated
    assert stored.dr_channel is not None
    assert 1 <= stored.dr_channel <= 9
    assert stored.e8_coordinates is not None
    assert len(stored.e8_coordinates) == 8
    assert stored.leech_point is not None
    assert stored.leech_point.startswith("leech::")

    # Persisted
    assert db.count() == 1
    fetched = db.fetch(stored.id)
    assert fetched is not None
    assert fetched.dr_channel == stored.dr_channel
    assert fetched.e8_coordinates == stored.e8_coordinates

    # Receipt chain records the compound op
    assert any(r.operation == "admit_and_store" for r in fetched.receipts)


def test_admit_and_store_multiple_morphons(db):
    """Stress: store 50 morphons and verify channel distribution."""
    controller = MorphonController.get()
    controller.register("constraints", _PassThroughConstraints())
    controller.register("addressing", MDHG())
    controller.register("geometry", Geometry())
    controller.register("memory", db)

    ids = []
    for i in range(50):
        m = Morphon.forge(payload={"i": i, "label": f"morphon-{i}"})
        stored = controller.admit_and_store(m)
        ids.append(stored.id)

    assert db.count() == 50

    # Round-trip every one
    for mid in ids:
        fetched = db.fetch(mid)
        assert fetched is not None
        assert 1 <= fetched.dr_channel <= 9
