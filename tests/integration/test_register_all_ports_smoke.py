"""W0 smoke: every bootstrap-registry port registers via register_all (no mesh)."""
from __future__ import annotations

import pytest

from cmplx.morphon import MorphonController
from cmplx.transform.bridge import reset_bootstrap_state
from runtime.bootstrap_registry import bootstrap_port_names, bootstrap_port_specs
from runtime.cmplx_bootstrap import register_all


@pytest.fixture(autouse=True)
def _reset():
    MorphonController.reset_for_tests()
    reset_bootstrap_state()
    yield
    MorphonController.reset_for_tests()
    reset_bootstrap_state()


def test_registry_matches_bootstrap_port_count():
    assert len(bootstrap_port_specs()) == len(bootstrap_port_names())


def test_register_all_registers_every_bootstrap_port():
    status = register_all()
    ctrl = MorphonController.get()
    expected = bootstrap_port_names()
    missing = [p for p in sorted(expected) if not ctrl.has(p)]
    assert not missing, f"missing ports: {missing}; status={status}"


def test_register_all_status_success_for_bootstrap_ports():
    status = register_all()
    for port in bootstrap_port_names():
        assert port in status
        assert status[port] in (
            "registered (in-process)",
            "already-registered",
        ), f"{port}: {status[port]}"


def test_each_registered_provider_is_non_null():
    register_all()
    ctrl = MorphonController.get()
    for port in bootstrap_port_names():
        provider = ctrl.get_provider(port)
        assert provider is not None
        assert type(provider).__name__
