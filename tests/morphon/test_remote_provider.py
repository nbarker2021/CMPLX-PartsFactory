"""
Wave 0.1 tests — mesh ↔ MorphonController bridge.

A remote service registered via ``register_remote_provider`` appears to
in-process callers as a normal port provider. Method calls on the provider
translate to ``mesh.request(service, method_name, payload)`` invocations.

These tests verify:
  1. Registration calls the standard register() machinery (unknown port,
     double-register errors propagate).
  2. Attribute access on a proxy returns a callable.
  3. Calling that callable invokes mesh.request with the right shape.
  4. Mesh exceptions propagate unchanged.
  5. Private-name access on a proxy raises AttributeError.
  6. The cmplx → mesh import remains deferred (local import only).
"""
from __future__ import annotations

import inspect

import pytest

from cmplx.morphon import MorphonController


class _FakeMesh:
    """Records every request and returns a configurable reply."""

    def __init__(self, reply: object = None) -> None:
        self.calls: list[tuple[str, str, dict | None]] = []
        self.reply = reply

    def request(
        self, service: str, endpoint: str, payload: dict | None = None
    ):
        self.calls.append((service, endpoint, payload))
        return self.reply


@pytest.fixture(autouse=True)
def _reset_controller():
    """Each test starts with a clean controller singleton."""
    MorphonController.reset_for_tests()
    yield
    MorphonController.reset_for_tests()


# ---------------------------------------------------------------------------
# 1. Registration delegates to register()
# ---------------------------------------------------------------------------

def test_register_remote_provider_registers_on_known_port():
    mesh = _FakeMesh()
    controller = MorphonController.get()
    controller.register_remote_provider("memory", mesh, "mmdb")

    assert controller.has("memory")
    provider = controller.get_provider("memory")
    assert provider is not None


def test_register_remote_provider_rejects_unknown_port():
    mesh = _FakeMesh()
    controller = MorphonController.get()
    with pytest.raises(ValueError, match="unknown port"):
        controller.register_remote_provider("not_a_real_port", mesh, "mmdb")


def test_register_remote_provider_rejects_double_registration():
    mesh = _FakeMesh()
    controller = MorphonController.get()
    controller.register_remote_provider("memory", mesh, "mmdb")
    with pytest.raises(RuntimeError, match="already has a registered provider"):
        controller.register_remote_provider("memory", mesh, "another_service")


def test_register_remote_provider_rejects_double_register_against_inproc():
    """Mixing remote and in-process for the same port is still a conflict."""
    mesh = _FakeMesh()
    controller = MorphonController.get()
    controller.register("memory", object())  # in-process first
    with pytest.raises(RuntimeError, match="already has a registered provider"):
        controller.register_remote_provider("memory", mesh, "mmdb")


# ---------------------------------------------------------------------------
# 2-3. Proxy method calls translate to mesh.request
# ---------------------------------------------------------------------------

def test_proxy_keyword_args_go_into_kwargs_payload():
    mesh = _FakeMesh(reply={"ok": True, "id": "abc"})
    controller = MorphonController.get()
    controller.register_remote_provider("memory", mesh, "mmdb")

    provider = controller.get_provider("memory")
    result = provider.store(morphon_id="abc", payload={"k": "v"})

    assert result == {"ok": True, "id": "abc"}
    assert len(mesh.calls) == 1
    service, endpoint, payload = mesh.calls[0]
    assert service == "mmdb"
    assert endpoint == "store"
    assert payload == {"kwargs": {"morphon_id": "abc", "payload": {"k": "v"}}}


def test_proxy_positional_args_go_into_args_payload():
    mesh = _FakeMesh(reply=None)
    controller = MorphonController.get()
    controller.register_remote_provider("addressing", mesh, "mdhg")

    provider = controller.get_provider("addressing")
    provider.channel_for("morphon_id_1")

    service, endpoint, payload = mesh.calls[0]
    assert service == "mdhg"
    assert endpoint == "channel_for"
    assert payload == {"args": ["morphon_id_1"]}


def test_proxy_mixed_args_payload_has_both_keys():
    mesh = _FakeMesh(reply=None)
    controller = MorphonController.get()
    controller.register_remote_provider("memory", mesh, "mmdb")

    provider = controller.get_provider("memory")
    provider.upsert("abc", overwrite=True, ttl=30)

    _, _, payload = mesh.calls[0]
    assert payload == {"args": ["abc"], "kwargs": {"overwrite": True, "ttl": 30}}


def test_proxy_no_args_sends_no_payload():
    mesh = _FakeMesh(reply={"status": "ok"})
    controller = MorphonController.get()
    controller.register_remote_provider("diagnostic", mesh, "speedlight")

    provider = controller.get_provider("diagnostic")
    provider.health()

    service, endpoint, payload = mesh.calls[0]
    assert service == "speedlight"
    assert endpoint == "health"
    assert payload is None


# ---------------------------------------------------------------------------
# 4. Mesh errors propagate
# ---------------------------------------------------------------------------

def test_proxy_propagates_mesh_exceptions():
    class _BoomMesh:
        def request(self, service, endpoint, payload=None):
            raise RuntimeError("boom: service down")

    controller = MorphonController.get()
    controller.register_remote_provider("memory", _BoomMesh(), "mmdb")

    provider = controller.get_provider("memory")
    with pytest.raises(RuntimeError, match="boom: service down"):
        provider.store(payload={"k": "v"})


# ---------------------------------------------------------------------------
# 5. Private attribute access is rejected
# ---------------------------------------------------------------------------

def test_proxy_rejects_private_attribute_access():
    mesh = _FakeMesh()
    controller = MorphonController.get()
    controller.register_remote_provider("memory", mesh, "mmdb")

    provider = controller.get_provider("memory")
    with pytest.raises(AttributeError, match="private attribute"):
        _ = provider._secret_thing


def test_proxy_repr_includes_service_name():
    mesh = _FakeMesh()
    controller = MorphonController.get()
    controller.register_remote_provider("memory", mesh, "mmdb")
    provider = controller.get_provider("memory")

    rep = repr(provider)
    assert "mmdb" in rep
    assert "_MeshServiceProxy" in rep


# ---------------------------------------------------------------------------
# 6. cmplx → mesh import remains deferred
# ---------------------------------------------------------------------------

def test_register_remote_provider_uses_local_import():
    """cmplx.morphon must remain importable without mesh installed.

    Verifies the implementation defers ``from mesh.morphon_bridge import ...``
    until call time. Module-load coupling would break standalone cmplx use.
    """
    src = inspect.getsource(MorphonController.register_remote_provider)
    assert "from mesh.morphon_bridge import" in src, (
        "register_remote_provider must use a local import to avoid "
        "cmplx → mesh module-load coupling"
    )


# ---------------------------------------------------------------------------
# 7. The proxy survives the existing controller compound-op contract
# ---------------------------------------------------------------------------

class _FakeConstraints:
    def admit(self, morphon):
        return True, ""


def test_proxy_can_serve_as_memory_provider_in_admit_and_store():
    """The remote-proxy must look enough like an in-process MemoryProvider
    that compound operations dispatch through it without special-casing."""
    from cmplx.morphon import Morphon

    mesh = _FakeMesh(reply={"stored": True})
    controller = MorphonController.get()
    controller.register_remote_provider("memory", mesh, "mmdb")
    controller.register("constraints", _FakeConstraints())

    class _FakeAddressing:
        def channel_for(self, morphon):
            return 3
    controller.register("addressing", _FakeAddressing())

    m = Morphon.forge(payload={"hello": "world"})
    controller.admit_and_store(m)

    # Mesh request was issued for the .store() call
    assert any(c[1] == "store" for c in mesh.calls)
    store_call = next(c for c in mesh.calls if c[1] == "store")
    service, endpoint, payload = store_call
    assert service == "mmdb"
    assert endpoint == "store"
    # admit_and_store called store(finalized_morphon) — single positional
    assert payload is not None
    assert "args" in payload
    assert len(payload["args"]) == 1
