"""
Smoke tests for cmplx.constraints.aletheia.
"""
from __future__ import annotations

import pytest

from cmplx.addressing.mdhg import MDHG
from cmplx.constraints.aletheia import (
    Aletheia,
    ConservationLaw,
    NoForbiddenKeysLaw,
    PayloadSizeLimitLaw,
    RejectionError,
)
from cmplx.geometry import Geometry
from cmplx.memory.mmdb import MMDB
from cmplx.morphon import Morphon, MorphonController, MorphonState


@pytest.fixture(autouse=True)
def _reset_controller():
    MorphonController.reset_for_tests()
    yield
    MorphonController.reset_for_tests()


# ---------------------------------------------------------------------------
# Default law set
# ---------------------------------------------------------------------------

def test_default_aletheia_admits_well_formed_morphon():
    a = Aletheia()
    m = Morphon.forge(payload={"hello": "world"})
    ok, reason = a.admit(m)
    assert ok is True
    assert reason == ""


def test_empty_payload_is_refused():
    a = Aletheia()
    m = Morphon.forge(payload={})
    ok, reason = a.admit(m)
    assert ok is False
    assert "payload_not_empty" in reason
    assert "empty" in reason


def test_non_mapping_payload_is_refused():
    a = Aletheia()
    m = Morphon.forge(payload={"x": 1})
    # Force-replace payload with a non-mapping for the test
    object.__setattr__(m, "payload", "not a mapping")
    ok, reason = a.admit(m)
    assert ok is False
    assert "payload_is_mapping" in reason


def test_terminal_state_is_refused():
    a = Aletheia()
    m = Morphon.forge(payload={"x": 1})
    # Walk to a terminal state via the legal path: CREATED -> CANCELLED
    m = m.transition_to(MorphonState.CANCELLED)
    ok, reason = a.admit(m)
    assert ok is False
    assert "state_admittable" in reason


def test_payload_size_limit_refuses_oversize():
    a = Aletheia(laws=[PayloadSizeLimitLaw(max_bytes=100)])
    big = {"blob": "x" * 1000}
    m = Morphon.forge(payload=big)
    ok, reason = a.admit(m)
    assert ok is False
    assert "payload_size_limit" in reason


# ---------------------------------------------------------------------------
# Custom laws
# ---------------------------------------------------------------------------

def test_no_forbidden_keys_law_blocks_password():
    a = Aletheia()
    a.register_law(NoForbiddenKeysLaw("password", "secret"))
    bad = Morphon.forge(payload={"user": "alice", "password": "p"})
    ok, reason = a.admit(bad)
    assert ok is False
    assert "password" in reason

    good = Morphon.forge(payload={"user": "alice"})
    ok, _ = a.admit(good)
    assert ok is True


def test_custom_law_short_circuits():
    """First refusing law wins; later laws aren't called."""

    class _CountingLaw(ConservationLaw):
        name = "counting"
        def __init__(self):
            self.calls = 0
        def evaluate(self, morphon):
            self.calls += 1
            return True, ""

    counter = _CountingLaw()
    a = Aletheia(laws=[NoForbiddenKeysLaw("secret"), counter])
    bad = Morphon.forge(payload={"secret": "x"})
    a.admit(bad)
    # The forbidden law refuses; the counter is never called.
    assert counter.calls == 0


def test_law_raising_exception_becomes_refusal():
    class _BrokenLaw(ConservationLaw):
        name = "broken"
        def evaluate(self, morphon):
            raise RuntimeError("oops")

    a = Aletheia(laws=[_BrokenLaw()])
    m = Morphon.forge(payload={"k": "v"})
    ok, reason = a.admit(m)
    assert ok is False
    assert "broken" in reason
    assert "RuntimeError" in reason
    assert "oops" in reason


def test_admit_strict_raises():
    a = Aletheia()
    m = Morphon.forge(payload={})  # empty payload — refused
    with pytest.raises(RejectionError) as ei:
        a.admit_strict(m)
    assert ei.value.law_name == "payload_not_empty"


def test_admit_strict_does_not_raise_on_well_formed():
    a = Aletheia()
    m = Morphon.forge(payload={"k": "v"})
    a.admit_strict(m)  # should not raise


def test_clear_then_no_laws_admits_everything():
    a = Aletheia()
    a.clear()
    m = Morphon.forge(payload={})  # would be refused with default laws
    ok, _ = a.admit(m)
    assert ok is True


# ---------------------------------------------------------------------------
# End-to-end: replace the pass-through fake with real Aletheia
# in the admit_and_store flow.
# ---------------------------------------------------------------------------

def test_admit_and_store_with_real_aletheia():
    """The mmdb test used a fake constraints provider. With real Aletheia,
    a well-formed morphon flows through; an empty one is refused at the
    constraints step."""

    with MMDB(":memory:") as db:
        controller = MorphonController.get()
        controller.register("constraints", Aletheia())
        controller.register("addressing", MDHG())
        controller.register("geometry", Geometry())
        controller.register("memory", db)

        # Happy path — well-formed morphon, full bridge.
        m = Morphon.forge(payload={"text": "hello, system"})
        stored = controller.admit_and_store(m)
        assert stored.dr_channel is not None
        assert db.count() == 1
        # Real Aletheia ran — no test fake.
        assert any(r.operation == "admit_and_store" for r in stored.receipts)

        # Rejection path — empty payload refused at constraints step.
        bad = Morphon.forge(payload={})
        with pytest.raises(PermissionError, match="payload_not_empty"):
            controller.admit_and_store(bad)
        # The rejected morphon is NOT in the store.
        assert db.count() == 1
