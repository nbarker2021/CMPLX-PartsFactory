"""
Bridge between the transformer package and the MorphonController port
registry.

The transformer never imports a concrete provider directly; it asks for
a port and the controller hands back whatever is registered (in-process
provider, mesh proxy, or test double). `ensure_bootstrapped()` makes
the first transformer constructed in a process responsible for wiring
up the default in-process providers via `runtime.cmplx_bootstrap`.
"""
from __future__ import annotations

import logging
import os
from typing import Any, Optional

from cmplx.morphon import MorphonController
from runtime.integration_profile import integration_profile_enabled

logger = logging.getLogger(__name__)

# Module-level cache so repeated TransformerConfig instances do not
# re-run register_all. Reset between tests via reset_bootstrap_state().
_BOOTSTRAP_STATUS: Optional[dict] = None


def ensure_bootstrapped(
    *,
    mmdb_path: str = ":memory:",
    health_check_timeout: float = 3.0,
    mesh: Any = None,
) -> dict:
    """Register every cmplx port provider once per process.

    Subsequent calls are no-ops and return the cached status map.
    """
    global _BOOTSTRAP_STATUS
    if _BOOTSTRAP_STATUS is not None:
        return _BOOTSTRAP_STATUS
    if integration_profile_enabled():
        from runtime.integration_profile import register_for_startup

        boot = register_for_startup(
            mesh,
            mmdb_path=mmdb_path,
            health_check_timeout=health_check_timeout,
        )
        _BOOTSTRAP_STATUS = boot.get("port_status", boot)
    else:
        from runtime.cmplx_bootstrap import register_all

        _BOOTSTRAP_STATUS = register_all(
            mesh=mesh,
            mmdb_path=mmdb_path,
            health_check_timeout=health_check_timeout,
        )
    logger.info("transform: port registration %s", _BOOTSTRAP_STATUS)
    return _BOOTSTRAP_STATUS


def reset_bootstrap_state() -> None:
    """Test-only helper — forget cached bootstrap status."""
    global _BOOTSTRAP_STATUS
    _BOOTSTRAP_STATUS = None


# ────────────────────────────────────────────────────────────────────────────
# Lazy provider accessors
# ────────────────────────────────────────────────────────────────────────────

def get_provider(port: str) -> Any:
    """Return the provider registered against `port`, or raise."""
    return MorphonController.get().get_provider(port)


def has_provider(port: str) -> bool:
    return MorphonController.get().has(port)


def get_diagnostic_provider() -> Any:
    return get_provider("diagnostic")


def get_symbolic_provider() -> Any:
    return get_provider("symbolic")


def get_conservation_provider() -> Any:
    return get_provider("conservation")


def get_cache_provider() -> Any:
    return get_provider("cache")


def get_receipt_provider() -> Any:
    return get_provider("receipt")


def get_atlas_provider() -> Any:
    return get_provider("atlas")


def get_constraints_provider() -> Any:
    return get_provider("constraints")


def get_engine_provider() -> Any:
    return get_provider("engine")


def get_geometry_provider() -> Any:
    return get_provider("geometry")


def get_memory_provider() -> Any:
    return get_provider("memory")


def get_addressing_provider() -> Any:
    return get_provider("addressing")


def get_snap_provider() -> Any:
    return get_provider("snap")


__all__ = [
    "ensure_bootstrapped",
    "reset_bootstrap_state",
    "get_provider",
    "has_provider",
    "get_diagnostic_provider",
    "get_symbolic_provider",
    "get_conservation_provider",
    "get_cache_provider",
    "get_receipt_provider",
    "get_atlas_provider",
    "get_constraints_provider",
    "get_engine_provider",
    "get_geometry_provider",
    "get_memory_provider",
    "get_addressing_provider",
    "get_snap_provider",
]
