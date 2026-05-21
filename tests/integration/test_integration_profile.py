"""B3 integration profile — receipt env + host mesh bootstrap."""
from __future__ import annotations

import os

import pytest

from cmplx.morphon import MorphonController
from cmplx.transform.bridge import reset_bootstrap_state
from runtime.integration_profile import (
    apply_integration_env,
    detect_host_stack,
    integration_profile_enabled,
    register_integration_profile,
    try_build_host_mesh,
)


@pytest.fixture(autouse=True)
def _reset():
    MorphonController.reset_for_tests()
    reset_bootstrap_state()
    yield
    MorphonController.reset_for_tests()
    reset_bootstrap_state()


def test_apply_integration_env_enables_receipt_bridges(monkeypatch):
    for key in ("MDHG_MINT_RECEIPT", "MMDB_MINT_RECEIPT", "CMPLX_INTEGRATION_PROFILE"):
        monkeypatch.delenv(key, raising=False)
    applied = apply_integration_env()
    assert applied["MDHG_MINT_RECEIPT"] == "1"
    assert applied["MMDB_MINT_RECEIPT"] == "1"
    assert integration_profile_enabled()


def test_register_integration_profile_wires_all_ports(monkeypatch):
    monkeypatch.setenv("CMPLX_INTEGRATION_PROFILE", "1")
    monkeypatch.setattr(
        "runtime.integration_profile.try_build_host_mesh",
        lambda **_: (None, {"mode": "in-process", "reason": "test"}),
    )
    result = register_integration_profile(prefer_mesh=False)
    status = result["port_status"]
    from runtime.bootstrap_registry import bootstrap_port_names

    for port in bootstrap_port_names():
        assert port in status
        assert status[port].startswith("registered")


@pytest.mark.skipif(
    not os.environ.get("CMPLX_RUN_HOST_STACK_TESTS"),
    reason="set CMPLX_RUN_HOST_STACK_TESTS=1 when Docker stack is up",
)
def test_host_mesh_when_stack_up():
    probe = detect_host_stack(min_services=3, timeout=3.0)
    if not probe["stack_up"]:
        pytest.skip("compose stack not detected on localhost")
    mesh, meta = try_build_host_mesh(min_services=3)
    assert mesh is not None
    assert meta["mode"] == "host_mesh"
    assert len(meta["services"]) >= 3
