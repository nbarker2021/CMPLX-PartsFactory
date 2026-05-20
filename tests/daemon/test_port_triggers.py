"""
§6.2 tests — daemon port-trigger registration.

Verifies:
  1. make_port_handler returns a zero-arg callable.
  2. The handler invokes the right port operation on MorphonController.
  3. The handler swallows exceptions (CRT thread must never crash).
  4. register_port_trigger wires the handler into a CRT-compatible stub.
  5. apply_canonical_bindings runs the canonical map.
"""
from __future__ import annotations

import pytest

from cmplx.morphon import MorphonController
from daemon.port_triggers import (
    CANONICAL_BINDINGS,
    apply_canonical_bindings,
    make_port_handler,
    register_port_trigger,
)


class _FakeCRT:
    """Minimal CRT shim that records registrations."""

    def __init__(self):
        self.registered: list[tuple[str, int, str]] = []
        self.handlers: dict[str, callable] = {}

    def register(self, channel_name: str, period: int, handler, description: str = ""):
        self.registered.append((channel_name, period, description))
        self.handlers[channel_name] = handler


@pytest.fixture(autouse=True)
def _reset_controller():
    MorphonController.reset_for_tests()
    yield
    MorphonController.reset_for_tests()


# ─────────────────────────────────────────────────────────────────
# 1. make_port_handler basics
# ─────────────────────────────────────────────────────────────────

def test_make_port_handler_returns_callable():
    handler = make_port_handler("atlas", "deployment_stats")
    assert callable(handler)
    # Zero-arg invocation contract
    import inspect
    sig = inspect.signature(handler)
    assert len(sig.parameters) == 0


def test_make_port_handler_invokes_method():
    from cmplx.atlas import AtlasProvider
    atlas = AtlasProvider()
    MorphonController.get().register("atlas", atlas)

    handler = make_port_handler("atlas", "deployment_stats")
    result = handler()
    assert result is not None
    assert result["deployed_count"] == 0
    assert result["capacity"] == 196_560


def test_make_port_handler_passes_args():
    """args/kwargs flow through to the operation."""
    class _Recorder:
        def __init__(self):
            self.calls = []
        def echo(self, *args, **kwargs):
            self.calls.append((args, kwargs))
            return "recorded"

    rec = _Recorder()
    MorphonController.get().register("atlas", rec)
    handler = make_port_handler(
        "atlas", "echo", args=("hello",), kwargs={"x": 1}
    )
    assert handler() == "recorded"
    assert rec.calls == [(("hello",), {"x": 1})]


# ─────────────────────────────────────────────────────────────────
# 2. Failure isolation
# ─────────────────────────────────────────────────────────────────

def test_handler_swallows_lookup_error_when_port_unregistered():
    """Port not registered → handler returns None, doesn't raise."""
    handler = make_port_handler("atlas", "deployment_stats")
    # MorphonController.reset_for_tests() means no atlas registered.
    result = handler()
    assert result is None


def test_handler_swallows_attribute_error_when_method_missing():
    """Provider has no such method → handler returns None, logs warning."""
    class _Empty:
        pass
    MorphonController.get().register("atlas", _Empty())
    handler = make_port_handler("atlas", "nonexistent_method")
    result = handler()
    assert result is None


def test_handler_swallows_runtime_exception():
    """Provider method raises → handler returns None, logs warning."""
    class _Boom:
        def crash(self):
            raise RuntimeError("kaboom")

    MorphonController.get().register("atlas", _Boom())
    handler = make_port_handler("atlas", "crash")
    result = handler()
    assert result is None


# ─────────────────────────────────────────────────────────────────
# 3. CRT registration
# ─────────────────────────────────────────────────────────────────

def test_register_port_trigger_wires_into_crt():
    crt = _FakeCRT()
    handler = register_port_trigger(crt, "brain_sync", 7, "atlas", "boundary_recompute")
    assert len(crt.registered) == 1
    channel, period, _desc = crt.registered[0]
    assert channel == "brain_sync"
    assert period == 7
    assert crt.handlers["brain_sync"] is handler


def test_register_port_trigger_handler_fires_correctly():
    """Simulate the CRT firing the registered handler — should hit the port."""
    from cmplx.atlas import AtlasProvider
    MorphonController.get().register("atlas", AtlasProvider())

    crt = _FakeCRT()
    register_port_trigger(crt, "brain_sync", 7, "atlas", "boundary_recompute")
    result = crt.handlers["brain_sync"]()  # simulate CRT firing
    assert result is not None
    assert result["deployed_count"] == 0


# ─────────────────────────────────────────────────────────────────
# 4. Canonical bindings
# ─────────────────────────────────────────────────────────────────

def test_canonical_bindings_match_sub_frame_table():
    """Sanity check: the canonical bindings cover the operations the
    port-trigger sub-frame documented as class-C in §3."""
    keys = {f"{port}.{op}" for _, _, port, op in CANONICAL_BINDINGS}
    expected_subset = {
        "atlas.boundary_recompute",
        "receipt.verify_chain",
        "memory.prune_stale",
        "cache.evict_cold",
        "diagnostic.pulse",
    }
    assert expected_subset.issubset(keys)


def test_apply_canonical_bindings_returns_status_per_binding():
    crt = _FakeCRT()
    status = apply_canonical_bindings(crt)
    # Every binding gets a status entry.
    for _, _, port, op in CANONICAL_BINDINGS:
        key = f"{port}.{op}"
        assert key in status
        assert status[key] in ("bound", "skipped") or status[key].startswith("failed:")


def test_apply_canonical_bindings_skip_list():
    crt = _FakeCRT()
    status = apply_canonical_bindings(crt, skip=("atlas.boundary_recompute",))
    assert status["atlas.boundary_recompute"] == "skipped"
    # Other bindings still went through.
    assert any(s == "bound" for s in status.values())


def test_apply_canonical_bindings_registers_all_non_skipped():
    crt = _FakeCRT()
    apply_canonical_bindings(crt)
    # Every channel name from CANONICAL_BINDINGS should be in crt.registered.
    registered_channels = {c for c, _, _ in crt.registered}
    expected_channels = {chan for chan, _, _, _ in CANONICAL_BINDINGS}
    assert expected_channels.issubset(registered_channels)
