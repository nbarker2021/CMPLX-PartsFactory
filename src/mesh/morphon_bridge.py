"""
morphon_bridge — adapter from MorphonController ports to remote mesh services.

The MorphonController port registry (cmplx.morphon.controller) treats every
provider as an in-process object satisfying a Protocol (e.g. MemoryProvider
with .store() and .fetch()). Remote services live behind HTTP and speak
``mesh.request(service, endpoint, payload)``.

This module is the only point of contact between the two layers. The proxy
wraps a service name and a mesh handle, then exposes any method-style
attribute as a callable that translates the call into a mesh request.

The controller exposes a convenience method ``register_remote_provider`` that
constructs a proxy and registers it. That method does a local import of this
module so cmplx still loads cleanly in environments without the mesh layer.

Wave 0.1 — see docs/wave_0_proposals.md and docs/ATTRACTOR_FRAME.md Slot 11
(morphon-controller) + Slot 31 (mesh-orchestrator).
"""
from __future__ import annotations

from typing import Any


class _MeshServiceProxy:
    """Adapter exposing a remote mesh service as a port-provider object.

    Every public attribute access returns a callable. Calling it issues
    ``mesh.request(service, attribute_name, payload)`` and returns whatever
    the mesh returns (typically a JSON dict).

    The payload shape is:
        {"args": [...]} if only positional arguments were passed,
        {"kwargs": {...}} if only keyword arguments,
        {"args": [...], "kwargs": {...}} if both,
        None if the call had no arguments.

    Remote service implementations are expected to read this shape; the
    wire contract is documented here and in the mesh service's adapter
    layer.

    Errors raised by ``mesh.request`` (timeouts, HTTP failures, circuit
    breaker trips) propagate unchanged so callers see the same exception
    surface they would calling the mesh directly.
    """

    __slots__ = ("_service", "_mesh")

    def __init__(self, mesh: Any, service_name: str) -> None:
        # Slot assignment uses standard attribute machinery; __getattr__
        # is only consulted when normal lookup fails.
        self._service = service_name
        self._mesh = mesh

    def __getattr__(self, name: str) -> Any:
        # Private/dunder names should never proxy. __getattribute__ handles
        # dunders normally; this guards against bare-underscore typos that
        # would otherwise be silently sent to the remote.
        if name.startswith("_"):
            raise AttributeError(
                f"private attribute {name!r} is not proxied to remote service "
                f"{self._service!r}"
            )

        service = self._service
        mesh = self._mesh

        def remote_call(*args: Any, **kwargs: Any) -> Any:
            payload: dict[str, Any] | None
            if args and kwargs:
                payload = {"args": list(args), "kwargs": kwargs}
            elif args:
                payload = {"args": list(args)}
            elif kwargs:
                payload = {"kwargs": kwargs}
            else:
                payload = None
            return mesh.request(service, name, payload=payload)

        remote_call.__name__ = name
        remote_call.__qualname__ = f"_MeshServiceProxy[{service}].{name}"
        return remote_call

    def __repr__(self) -> str:
        return f"<_MeshServiceProxy service={self._service!r}>"
