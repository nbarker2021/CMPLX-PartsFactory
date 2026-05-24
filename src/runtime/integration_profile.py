"""
B3 — Integration profile: host Docker stack + receipt bridges + mesh-preferred bootstrap.

Use when the PartsFactory compose stack is up on localhost mapped ports.
Set ``CMPLX_INTEGRATION_PROFILE=1`` or call ``register_integration_profile()``
directly from agent/transform startup.
"""
from __future__ import annotations

import logging
import os
import urllib.error
import urllib.request
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)

# Host-published ports (docker compose stack on Windows)
_HOST_STACK: dict[str, tuple[str, str]] = {
    "mmdb": ("http://localhost:8824", "MMDB_UNIFIED_URL"),
    "mdhg": ("http://localhost:8825", "MDHG_UNIFIED_URL"),
    "snap": ("http://localhost:8823", "SNAP_UNIFIED_URL"),
    "tarpit": ("http://localhost:8844", "TARPIT_API_URL"),
    "speedlight": ("http://localhost:8843", "SPEEDLIGHT_API_URL"),
}

_RECEIPT_BRIDGE_DEFAULTS: dict[str, str] = {
    "CMPLX_INTEGRATION_PROFILE": "1",
    "MDHG_MINT_RECEIPT": "1",
    "MMDB_MINT_RECEIPT": "1",
    "SNAP_MINT_RECEIPT": "1",
    "SPEEDLIGHT_MINT_RECEIPT": "1",
    "TARPIT_MINT_RECEIPT": "1",
    "MORPHON_MINT_RECEIPT": "1",
}

_CLIENT_FACTORIES: dict[str, Callable[[str], Any]] = {}


def _load_client_factories() -> dict[str, Callable[[str], Any]]:
    if _CLIENT_FACTORIES:
        return _CLIENT_FACTORIES
    from services.mdhg_client import MDHGClient
    from services.mmdb_client import MMDBClient
    from services.snap_client import SNAPClient
    from services.speedlight_client import SpeedLightClient
    from services.tarpit_client import TarPitClient

    _CLIENT_FACTORIES.update(
        {
            "mmdb": MMDBClient,
            "mdhg": MDHGClient,
            "snap": SNAPClient,
            "tarpit": TarPitClient,
            "speedlight": SpeedLightClient,
        }
    )
    return _CLIENT_FACTORIES


def integration_profile_enabled() -> bool:
    return os.environ.get("CMPLX_INTEGRATION_PROFILE", "").strip().lower() in (
        "1",
        "true",
        "yes",
    )


def apply_integration_env(*, force: bool = False) -> dict[str, str]:
    """Turn on receipt bridges for integration runs (respect explicit user overrides unless force)."""
    applied: dict[str, str] = {}
    for key, default in _RECEIPT_BRIDGE_DEFAULTS.items():
        if force or not os.environ.get(key):
            os.environ[key] = default
        applied[key] = os.environ[key]
    return applied


def clear_integration_env(keys: Optional[tuple[str, ...]] = None) -> None:
    """Remove integration env vars set by ``apply_integration_env()``.

    Used in test teardown to prevent cross-test leakage when monkeypatch
    does not catch direct ``os.environ`` mutations.
    """
    for key in (keys or _RECEIPT_BRIDGE_DEFAULTS):
        os.environ.pop(key, None)


def _health_ok(base_url: str, timeout: float = 2.0) -> bool:
    url = base_url.rstrip("/") + "/health"
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            return 200 <= resp.status < 300
    except (urllib.error.URLError, TimeoutError, OSError):
        return False


class _HostStackRegistry:
    """Minimal registry for ``register_all(mesh=...)`` health checks."""

    def __init__(self, clients: dict[str, Any]) -> None:
        self._clients = clients

    def get(self, name: str) -> Any:
        return self._clients.get(name)


class _HostStackMesh:
    """Thin mesh handle — health via service clients; no full MeshOrchestrator required."""

    def __init__(self, registry: _HostStackRegistry) -> None:
        self.registry = registry


def detect_host_stack(*, min_services: int = 3, timeout: float = 2.0) -> dict[str, Any]:
    """Probe localhost mapped ports; return healthy service names."""
    healthy: list[str] = []
    for name, (base, env_key) in _HOST_STACK.items():
        if _health_ok(base, timeout=timeout):
            healthy.append(name)
            os.environ.setdefault(env_key, base)
    return {
        "healthy": healthy,
        "count": len(healthy),
        "stack_up": len(healthy) >= min_services,
    }


def try_build_host_mesh(*, min_services: int = 3, timeout: float = 2.0) -> tuple[Any | None, dict[str, Any]]:
    """Build mesh handle when enough compose services respond on localhost."""
    probe = detect_host_stack(min_services=min_services, timeout=timeout)
    if not probe["stack_up"]:
        return None, {"mode": "in-process", "reason": "host stack not detected", **probe}

    factories = _load_client_factories()
    clients: dict[str, Any] = {}
    for name in probe["healthy"]:
        base, _ = _HOST_STACK[name]
        try:
            clients[name] = factories[name](base)
        except Exception as exc:  # noqa: BLE001
            logger.warning("host client %s failed: %s", name, exc)

    if len(clients) < min_services:
        return None, {"mode": "in-process", "reason": "client construction failed", "healthy": list(clients)}

    return _HostStackMesh(_HostStackRegistry(clients)), {
        "mode": "host_mesh",
        "services": sorted(clients),
        **probe,
    }


def register_integration_profile(
    *,
    mmdb_path: str = ":memory:",
    health_check_timeout: float = 3.0,
    prefer_mesh: bool = True,
    auto_env: bool = True,
    min_mesh_services: int = 3,
) -> dict[str, Any]:
    """Apply integration env, optional host mesh, then ``register_all()``."""
    env_applied = apply_integration_env() if auto_env else {}
    mesh = None
    mesh_meta: dict[str, Any] = {"mode": "in-process"}
    if prefer_mesh:
        mesh, mesh_meta = try_build_host_mesh(min_services=min_mesh_services)

    from runtime.cmplx_bootstrap import register_all

    status = register_all(
        mesh=mesh,
        mmdb_path=mmdb_path,
        health_check_timeout=health_check_timeout,
    )
    remote_ports = [p for p, s in status.items() if s.startswith("registered (remote:")]
    return {
        "integration_profile": True,
        "env": env_applied,
        "mesh": mesh_meta,
        "port_status": status,
        "remote_ports": remote_ports,
    }


def register_for_startup(
    mesh: Any = None,
    *,
    mmdb_path: str = ":memory:",
    health_check_timeout: float = 3.0,
    config: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """Entry for AgentProcess / transform — picks integration vs plain bootstrap."""
    cfg = config or {}
    if cfg.get("integration_profile") or integration_profile_enabled():
        if mesh is not None:
            apply_integration_env()
            from runtime.cmplx_bootstrap import register_all

            status = register_all(
                mesh=mesh,
                mmdb_path=mmdb_path,
                health_check_timeout=health_check_timeout,
            )
            return {
                "integration_profile": True,
                "mesh": {"mode": "provided"},
                "port_status": status,
                "remote_ports": [
                    p for p, s in status.items() if str(s).startswith("registered (remote:")
                ],
            }
        return register_integration_profile(
            mmdb_path=mmdb_path,
            health_check_timeout=health_check_timeout,
            prefer_mesh=cfg.get("prefer_mesh", True),
        )
    from runtime.cmplx_bootstrap import register_all

    status = register_all(
        mesh=mesh,
        mmdb_path=mmdb_path,
        health_check_timeout=health_check_timeout,
    )
    return {"integration_profile": False, "port_status": status}
