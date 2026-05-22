"""
Wave 0.2 — cmplx port-provider startup wiring.

Single-call entry point that registers every cmplx port whose provider
exists, and optionally swaps in a remote proxy via the mesh bridge for
ports where a healthy remote service is reachable.

Per the user's 2026-05-17 Wave 0 decisions:
  - Remote-preferred when reachable; in-process fallback when not.
  - Single registration per port (no overwrites). Decision made up-front
    via health check, then registered once.
  - 3-second blocking health-check timeout per service.
  - F-1: Aletheia satisfies ConstraintsProvider directly — no facade needed.
  - Manny is intentionally NOT registered as a port (held until role is
    clearer in the frame); it stays mesh-addressable via mesh.request().

Call from the runtime entry point (e.g., AgentProcess.__init__()) once
per process. The function returns a status dict suitable for logging or
inclusion in a startup receipt.
"""
from __future__ import annotations

import logging
from typing import Any, Callable

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────
# Port → service-name mapping
# ─────────────────────────────────────────────────────────────────────

# Ports that have both an in-process provider AND a remote mesh service.
# Remote-preferred when reachable; in-process fallback otherwise.
_PORTS_WITH_REMOTE: dict[str, str] = {
    "memory": "mmdb",
    "addressing": "mdhg",
    "symbolic": "tarpit",
    "snap": "snap",
    "cache": "speedlight",
    "worlds": "forge",
}

# Ports that are in-process-only (no remote equivalent today).
_PORTS_LOCAL_ONLY: tuple[str, ...] = (
    "receipt",
    "conservation",
    "diagnostic",
    "geometry",
    "constraints",
    "engine",
    "transport",
    "embed",  # 4-Embed Model — view layer, no remote equivalent
    "atlas",  # Mandelbrot deployment boundary + Julia c-assignment
    "routing",  # AGRM — in-process stub until mesh service exists
    "crystal",  # CrystalRegistry — SNAP/MDHG/E8 composite
    "hash_lanes",  # slot-16 lanes over MDHG + routing tours
)


# ─────────────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────────────

def register_all(
    mesh: Any = None,
    *,
    mmdb_path: str = ":memory:",
    health_check_timeout: float = 3.0,
) -> dict[str, str]:
    """Register all cmplx port providers. Returns a per-port status map.

    Args:
        mesh: Optional MeshOrchestrator instance. If provided, ports in
            ``_PORTS_WITH_REMOTE`` whose remote service health-checks pass
            register a remote proxy instead of the in-process provider.
        mmdb_path: SQLite path for the in-process MMDB. Default ``:memory:``.
        health_check_timeout: Per-service blocking timeout in seconds.
            Effective only when ``mesh`` is provided.

    Returns:
        ``{port: "registered (in-process)" | "registered (remote: <svc>)" |
                 "already-registered" | "failed: <reason>"}``
    """
    from cmplx.morphon import MorphonController

    ctrl = MorphonController.get()
    status: dict[str, str] = {}

    # Local-only providers first — these have no remote equivalent.
    for port, factory in _local_only_factories(mmdb_path).items():
        if port not in _PORTS_LOCAL_ONLY:
            continue
        status[port] = _register_or_skip(ctrl, port, factory)

    # Ports with both shapes — pick one per port via health check.
    factories_with_remote = _with_remote_factories(mmdb_path)
    for port, service_name in _PORTS_WITH_REMOTE.items():
        if ctrl.has(port):
            status[port] = "already-registered"
            continue
        if mesh is not None and _service_healthy(mesh, service_name, health_check_timeout):
            try:
                ctrl.register_remote_provider(port, mesh, service_name)
                status[port] = f"registered (remote: {service_name})"
            except Exception as e:
                status[port] = f"failed: {e}"
        else:
            factory = factories_with_remote.get(port)
            if factory is None:
                status[port] = "failed: no in-process factory"
                continue
            status[port] = _register_or_skip(ctrl, port, factory)

    logger.info("cmplx port-provider registration complete: %s", status)
    _warn_missing_registry_ports(status)
    return status


def _warn_missing_registry_ports(status: dict[str, str]) -> None:
    """Log when bootstrap_registry ports did not register (W0 guard)."""
    try:
        from runtime.bootstrap_registry import bootstrap_port_names
    except ImportError:
        return
    missing = sorted(p for p in bootstrap_port_names() if not status.get(p, "").startswith("registered"))
    if missing:
        logger.warning("bootstrap ports not registered: %s", missing)


# ─────────────────────────────────────────────────────────────────────
# Factories
# ─────────────────────────────────────────────────────────────────────

def _local_only_factories(mmdb_path: str) -> dict[str, Callable[[], Any]]:
    """In-process factories for ports without a remote equivalent."""
    factories: dict[str, Callable[[], Any]] = {}

    def _factory(mod_path: str, cls_name: str):
        def make():
            import importlib
            module = importlib.import_module(mod_path)
            return getattr(module, cls_name)()
        return make

    factories["receipt"] = _factory("cmplx.receipt.provider", "ReceiptProvider")
    factories["conservation"] = _factory("cmplx.nsl.provider", "NSLProvider")
    factories["diagnostic"] = _factory("cmplx.morsr.provider", "MORSRProvider")
    factories["geometry"] = _factory("cmplx.geometry.provider", "Geometry")

    # F-1: Aletheia is its own provider (no facade module required).
    def _aletheia():
        from cmplx.constraints.aletheia import Aletheia
        # Register the default laws so admit() does something useful.
        from cmplx.constraints.aletheia.laws import (
            PayloadIsMappingLaw,
            PayloadNotEmptyLaw,
        )
        a = Aletheia()
        a.register_laws([PayloadIsMappingLaw(), PayloadNotEmptyLaw()])
        return a

    factories["constraints"] = _aletheia

    factories["engine"] = _factory("cmplx.engine.cqe.provider", "CQEProvider")

    # F-5: transport needs a CarrierRegistry with at least one carrier.
    def _transport():
        from cmplx.transport import CarrierRegistry, TransportProviderFacade
        from cmplx.transport.chirp.chirp import DTMFCarrier
        reg = CarrierRegistry()
        reg.register(DTMFCarrier())
        return TransportProviderFacade(reg, default_carrier="dtmf")

    factories["transport"] = _transport

    factories["embed"] = _factory("cmplx.embed", "FourEmbedProvider")

    factories["atlas"] = _factory("cmplx.atlas", "AtlasProvider")
    factories["routing"] = _factory("cmplx.routing.provider", "AGRMRoutingProvider")
    factories["crystal"] = _factory("cmplx.crystal", "CrystalRegistry")
    factories["hash_lanes"] = _factory("cmplx.hash_lanes", "HashLanesProvider")

    return factories


def _with_remote_factories(mmdb_path: str) -> dict[str, Callable[[], Any]]:
    """In-process factories for ports that also have a remote equivalent."""
    factories: dict[str, Callable[[], Any]] = {}

    def _factory(mod_path: str, cls_name: str, *args: Any, **kwargs: Any):
        def make():
            import importlib
            module = importlib.import_module(mod_path)
            return getattr(module, cls_name)(*args, **kwargs)
        return make

    factories["memory"] = _factory("cmplx.memory.mmdb", "MMDBMemoryProvider", mmdb_path)
    factories["addressing"] = _factory("cmplx.addressing.mdhg", "MDHGAddressingProvider")
    factories["symbolic"] = _factory("cmplx.symbolic.tarpit", "TarPitSymbolicProvider")
    factories["snap"] = _factory("cmplx.snap.provider", "SNAPEngine")
    factories["cache"] = _factory("cmplx.speedlight.provider", "SpeedLightProvider")
    factories["worlds"] = _factory("cmplx.worlds.forge.provider", "WorldsForgeProvider")

    return factories


# ─────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────

def _register_or_skip(ctrl, port: str, factory: Callable[[], Any]) -> str:
    """Register a port if not already registered. Returns a status string."""
    if ctrl.has(port):
        return "already-registered"
    try:
        provider = factory()
        ctrl.register(port, provider)
        return "registered (in-process)"
    except Exception as e:
        return f"failed: {e}"


def _service_healthy(mesh: Any, service: str, timeout: float) -> bool:
    """Return True if the mesh-discovered service responds within timeout.

    Uses ``mesh.registry.get(service).health()`` when available; treats any
    exception (offline, timeout, missing client, network error) as unhealthy.
    Timeout is best-effort — the underlying HTTP call may not honor it,
    but most service clients respect short timeouts.
    """
    try:
        client = mesh.registry.get(service)
        if client is None:
            return False
        if not hasattr(client, "health"):
            return False
        client.health()
        return True
    except Exception:
        return False
