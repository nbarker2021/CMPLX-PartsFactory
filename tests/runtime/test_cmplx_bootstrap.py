"""
Wave 0.2 tests — cmplx bootstrap registration.

Verifies:
  1. All bootstrap-registry ports are registered after register_all() with no mesh.
  2. Each registered provider satisfies its Protocol where applicable.
  3. With a FakeMesh whose services are all healthy, ports in
     _PORTS_WITH_REMOTE register the remote proxy instead of in-process.
  4. With a FakeMesh whose services all fail health, in-process providers
     are used as fallback.
  5. Aletheia (F-1) is registered with default laws and admits a normal morphon.
  6. Idempotency: second call returns "already-registered" rather than failing.
"""
from __future__ import annotations

import pytest

from cmplx.morphon import (
    AddressingProvider,
    ConstraintsProvider,
    MemoryProvider,
    Morphon,
    MorphonController,
    SymbolicProvider,
    TransportProvider,
)
from runtime.bootstrap_registry import bootstrap_port_names
from runtime.cmplx_bootstrap import register_all


_EXPECTED_PORTS = bootstrap_port_names()


class _HealthyFakeMesh:
    """Mesh stub where every service health-checks healthy."""

    class _HealthyClient:
        def health(self):
            return {"ok": True}

    class _Registry:
        def get(self, service):
            return _HealthyFakeMesh._HealthyClient()

    def __init__(self):
        self.registry = self._Registry()
        self.requests = []

    def request(self, service, endpoint, payload=None):
        self.requests.append((service, endpoint, payload))
        return {"ok": True, "remote": True}


class _UnhealthyFakeMesh:
    """Mesh stub where every service health-check raises."""

    class _DeadClient:
        def health(self):
            raise RuntimeError("service unavailable")

    class _Registry:
        def get(self, service):
            return _UnhealthyFakeMesh._DeadClient()

    def __init__(self):
        self.registry = self._Registry()


@pytest.fixture(autouse=True)
def _reset_controller():
    MorphonController.reset_for_tests()
    yield
    MorphonController.reset_for_tests()


# ---------------------------------------------------------------------------
# 1. No-mesh path: every port lands in-process
# ---------------------------------------------------------------------------

def test_register_all_no_mesh_registers_every_port():
    status = register_all()
    ctrl = MorphonController.get()
    for port in _EXPECTED_PORTS:
        assert ctrl.has(port), f"port {port!r} not registered (status: {status.get(port)})"


def test_register_all_no_mesh_status_marks_in_process():
    status = register_all()
    for port in _EXPECTED_PORTS:
        assert status[port] == "registered (in-process)"


# ---------------------------------------------------------------------------
# 2. Protocol compliance for the L0-L1 providers
# ---------------------------------------------------------------------------

def test_registered_constraints_satisfies_protocol():
    register_all()
    p = MorphonController.get().get_provider("constraints")
    assert isinstance(p, ConstraintsProvider)


def test_registered_memory_satisfies_protocol():
    register_all()
    p = MorphonController.get().get_provider("memory")
    assert isinstance(p, MemoryProvider)


def test_registered_addressing_satisfies_protocol():
    register_all()
    p = MorphonController.get().get_provider("addressing")
    assert isinstance(p, AddressingProvider)


def test_registered_symbolic_satisfies_protocol():
    register_all()
    p = MorphonController.get().get_provider("symbolic")
    assert isinstance(p, SymbolicProvider)


def test_registered_transport_satisfies_protocol():
    register_all()
    p = MorphonController.get().get_provider("transport")
    assert isinstance(p, TransportProvider)


# ---------------------------------------------------------------------------
# 3. Healthy mesh: remote-preferred for _PORTS_WITH_REMOTE
# ---------------------------------------------------------------------------

def test_healthy_mesh_registers_remote_for_dual_ports():
    mesh = _HealthyFakeMesh()
    status = register_all(mesh=mesh)
    for port in ("memory", "addressing", "symbolic", "snap", "cache"):
        assert status[port].startswith("registered (remote:"), (
            f"port {port!r} should be remote; got: {status[port]}"
        )


def test_healthy_mesh_leaves_local_only_ports_in_process():
    mesh = _HealthyFakeMesh()
    status = register_all(mesh=mesh)
    local_only = bootstrap_port_names() - frozenset(
        ("memory", "addressing", "symbolic", "snap", "cache")
    )
    for port in local_only:
        assert status[port] == "registered (in-process)"


def test_healthy_mesh_remote_calls_routed_via_mesh():
    """Calling a method on a remote-registered provider hits mesh.request."""
    mesh = _HealthyFakeMesh()
    register_all(mesh=mesh)
    memory = MorphonController.get().get_provider("memory")
    # Calling any method on the proxy should reach mesh.request
    memory.store(morphon_id="abc", payload={"k": "v"})
    assert len(mesh.requests) == 1
    service, endpoint, _ = mesh.requests[0]
    assert service == "mmdb"
    assert endpoint == "store"


# ---------------------------------------------------------------------------
# 4. Unhealthy mesh: in-process fallback
# ---------------------------------------------------------------------------

def test_unhealthy_mesh_falls_back_to_in_process():
    mesh = _UnhealthyFakeMesh()
    status = register_all(mesh=mesh)
    for port in _EXPECTED_PORTS:
        assert status[port] == "registered (in-process)"


# ---------------------------------------------------------------------------
# 5. F-1: Aletheia admits a normal morphon
# ---------------------------------------------------------------------------

def test_aletheia_admits_normal_morphon():
    register_all()
    constraints = MorphonController.get().get_provider("constraints")
    m = Morphon.forge(payload={"k": "v"})
    admitted, reason = constraints.admit(m)
    assert admitted is True
    assert reason == ""


def test_aletheia_rejects_empty_payload():
    """The default PayloadNotEmptyLaw should reject empty-dict payloads."""
    register_all()
    constraints = MorphonController.get().get_provider("constraints")
    # forge() injects identity_kind; use a bare morphon for empty payload.
    m = Morphon(payload={})
    admitted, reason = constraints.admit(m)
    assert admitted is False
    assert "empty" in reason.lower()


# ---------------------------------------------------------------------------
# 6. Idempotency
# ---------------------------------------------------------------------------

def test_double_call_returns_already_registered():
    register_all()
    status = register_all()  # second call
    for port in _EXPECTED_PORTS:
        assert status[port] == "already-registered"


# ---------------------------------------------------------------------------
# 7. The full pipeline (admit_and_store) works end-to-end after bootstrap
# ---------------------------------------------------------------------------

def test_admit_and_store_works_after_bootstrap():
    register_all()
    m = Morphon.forge(payload={"hello": "world"})
    # Wave 5 added atlas to bootstrap — admit_and_store now also checks
    # whether the morphon's Julia c-value is in the Mandelbrot boundary.
    # Pre-set fractal_coordinate to a known in-set value so this test
    # exercises the happy path regardless of the morphon's hash-derived c.
    m.fractal_coordinate = 0+0j
    result = MorphonController.get().admit_and_store(m)
    # Should have channel + e8 coords + leech point cached
    assert result.dr_channel is not None
    assert result.e8_coordinates is not None
    assert result.leech_point is not None
    # And it should be fetchable from memory
    memory = MorphonController.get().get_provider("memory")
    fetched = memory.fetch(m.id)
    assert fetched is not None
    assert fetched.id == m.id


def test_admit_and_store_rejects_out_of_boundary_morphon_after_bootstrap():
    """End-to-end: bootstrap-registered atlas rejects out-of-set morphons."""
    register_all()
    m = Morphon.forge(payload={"hello": "world"})
    m.fractal_coordinate = 100+100j  # forced out-of-set
    with pytest.raises(PermissionError, match="rejected by atlas"):
        MorphonController.get().admit_and_store(m)
