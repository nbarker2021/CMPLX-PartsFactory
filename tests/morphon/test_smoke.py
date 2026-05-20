"""
Smoke tests for cmplx.morphon — the first component built under the
new "parts-plugged-into-a-designed-system" approach. These tests
establish the pattern every other component's tests follow:

  1. The component is usable standalone (no bridge needed) for
     construction, inspection, and lifecycle transitions.
  2. The state machine refuses illegal transitions.
  3. Bridge ports raise cleanly when no provider is registered.
  4. When a fake provider is registered, bridge calls dispatch.
"""
from __future__ import annotations

import pytest

from cmplx.morphon import (
    Morphon,
    MorphonController,
    MorphonState,
    Receipt,
    can_transition,
    is_terminal,
)


# ---------------------------------------------------------------------------
# 1. Standalone construction & inspection
# ---------------------------------------------------------------------------

def test_forge_creates_morphon_at_created_state():
    m = Morphon.forge(payload={"text": "hello"})
    assert m.state is MorphonState.CREATED
    assert m.payload == {"text": "hello"}
    assert m.id
    assert m.created_at
    # The forge call should leave one receipt.
    assert len(m.receipts) == 1
    assert m.receipts[0].operation == "forge"


def test_morphon_identity_is_stable_across_state_transitions():
    m = Morphon.forge(payload={"x": 1})
    original_id = m.id
    m2 = m.transition_to(MorphonState.VALIDATING)
    assert m2.id == original_id


def test_with_payload_creates_a_new_morphon_with_parent_link():
    parent = Morphon.forge(payload={"x": 1})
    child = parent.with_payload({"x": 2})
    assert child.id != parent.id
    assert child.parent == parent.id
    assert child.state is MorphonState.CREATED
    assert child.payload == {"x": 2}


def test_serialize_round_trip():
    m = Morphon.forge(payload={"k": "v"})
    m = m.transition_to(MorphonState.VALIDATING)
    m = m.transition_to(MorphonState.POLICY_CHECK)
    data = m.serialize()
    m2 = Morphon.deserialize(data)
    assert m2.id == m.id
    assert m2.state is m.state
    assert m2.payload == m.payload
    assert len(m2.receipts) == len(m.receipts)


# ---------------------------------------------------------------------------
# 2. State machine
# ---------------------------------------------------------------------------

def test_legal_transition_succeeds():
    m = Morphon.forge(payload={})
    m = m.transition_to(MorphonState.VALIDATING)
    assert m.state is MorphonState.VALIDATING


def test_illegal_transition_raises():
    m = Morphon.forge(payload={})
    # CREATED → EXECUTING is not legal; must go through VALIDATING etc.
    with pytest.raises(ValueError, match="illegal MorphonState transition"):
        m.transition_to(MorphonState.EXECUTING)


def test_terminal_states_have_no_outgoing_transitions():
    assert is_terminal(MorphonState.COMPLETED)
    assert is_terminal(MorphonState.FAILED)
    assert is_terminal(MorphonState.CANCELLED)
    assert not is_terminal(MorphonState.CREATED)


def test_transition_appends_receipt():
    m = Morphon.forge(payload={})
    n_before = len(m.receipts)
    m = m.transition_to(MorphonState.VALIDATING)
    assert len(m.receipts) == n_before + 1
    assert m.receipts[-1].operation == "transition"
    assert m.receipts[-1].detail["from"] == "CREATED"
    assert m.receipts[-1].detail["to"] == "VALIDATING"


def test_can_transition_helper():
    assert can_transition(MorphonState.CREATED, MorphonState.VALIDATING)
    assert can_transition(MorphonState.CREATED, MorphonState.CANCELLED)
    assert not can_transition(MorphonState.CREATED, MorphonState.EXECUTING)
    assert not can_transition(MorphonState.COMPLETED, MorphonState.CREATED)


# ---------------------------------------------------------------------------
# 3. Bridge — unregistered ports raise
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def _reset_controller():
    """Each test starts with a clean controller singleton."""
    MorphonController.reset_for_tests()
    yield
    MorphonController.reset_for_tests()


def test_project_to_channel_raises_without_addressing_provider():
    m = Morphon.forge(payload={"k": "v"})
    with pytest.raises(LookupError, match="addressing"):
        m.project_to_channel()


def test_project_to_e8_raises_without_geometry_provider():
    m = Morphon.forge(payload={"k": "v"})
    with pytest.raises(LookupError, match="geometry"):
        m.project_to_e8()


def test_unknown_port_register_raises():
    with pytest.raises(ValueError, match="unknown port"):
        MorphonController.get().register("not_a_real_port", object())


def test_double_register_raises():
    controller = MorphonController.get()
    controller.register("addressing", object())
    with pytest.raises(RuntimeError, match="already has a registered provider"):
        controller.register("addressing", object())


# ---------------------------------------------------------------------------
# 4. Bridge — registered provider dispatches correctly
# ---------------------------------------------------------------------------

class _FakeAddressing:
    """Test provider for the addressing port."""

    def __init__(self, channel: int = 7) -> None:
        self.channel = channel
        self.calls: list[str] = []

    def channel_for(self, morphon: Morphon) -> int:
        self.calls.append(morphon.id)
        return self.channel


class _FakeGeometry:
    """Test provider for the geometry port."""

    def e8_coordinates(self, morphon: Morphon) -> tuple[float, ...]:
        # Deterministic fake — hash payload and reduce.
        s = sum(ord(c) for c in str(morphon.payload))
        return tuple(((s >> i) & 0xFF) / 256.0 for i in range(8))

    def leech_point(self, morphon: Morphon) -> str:
        return f"leech::{morphon.id[:8]}"


def test_registered_addressing_dispatches():
    fake = _FakeAddressing(channel=5)
    MorphonController.get().register("addressing", fake)

    m = Morphon.forge(payload={"k": "v"})
    assert m.project_to_channel() == 5
    assert m.dr_channel == 5
    assert fake.calls == [m.id]


def test_cached_channel_is_not_recomputed():
    fake = _FakeAddressing(channel=3)
    MorphonController.get().register("addressing", fake)
    m = Morphon.forge(payload={"k": "v"})
    m.project_to_channel()
    m.project_to_channel()
    # Provider should only be called once — second call hits the cache.
    assert len(fake.calls) == 1


def test_registered_geometry_caches_both_projections():
    MorphonController.get().register("geometry", _FakeGeometry())
    m = Morphon.forge(payload={"k": "v"})
    coords = m.project_to_e8()
    point = m.project_to_leech()
    assert len(coords) == 8
    assert point.startswith("leech::")
    assert m.e8_coordinates == coords
    assert m.leech_point == point


# ---------------------------------------------------------------------------
# 5. Compound operations — admit_and_store happy path
# ---------------------------------------------------------------------------

class _FakeConstraints:
    def admit(self, morphon: Morphon) -> tuple[bool, str]:
        return True, ""


class _FakeMemory:
    def __init__(self) -> None:
        self.stored: dict[str, Morphon] = {}

    def store(self, morphon: Morphon) -> None:
        self.stored[morphon.id] = morphon

    def fetch(self, morphon_id: str) -> Morphon | None:
        return self.stored.get(morphon_id)


def test_admit_and_store_runs_the_full_sequence():
    controller = MorphonController.get()
    controller.register("constraints", _FakeConstraints())
    controller.register("addressing", _FakeAddressing(channel=4))
    controller.register("geometry", _FakeGeometry())
    memory = _FakeMemory()
    controller.register("memory", memory)

    m = Morphon.forge(payload={"hello": "world"})
    result = controller.admit_and_store(m)

    assert result.dr_channel == 4
    assert result.e8_coordinates is not None
    assert result.leech_point is not None
    assert m.id in memory.stored
    # Receipt chain records the compound op
    assert any(r.operation == "admit_and_store" for r in result.receipts)


class _RejectingConstraints:
    def admit(self, morphon: Morphon) -> tuple[bool, str]:
        return False, "payload contains forbidden term"


def test_admit_and_store_raises_when_constraints_reject():
    controller = MorphonController.get()
    controller.register("constraints", _RejectingConstraints())
    controller.register("addressing", _FakeAddressing())
    controller.register("memory", _FakeMemory())

    m = Morphon.forge(payload={"k": "v"})
    with pytest.raises(PermissionError, match="rejected by constraints"):
        controller.admit_and_store(m)
