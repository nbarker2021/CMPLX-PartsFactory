"""
Port-trigger registration helpers — wire MorphonController port operations
to daemon CRT channels as class-C (periodic) triggers.

This is the §6.2 piece of the port-trigger-map sub-frame: when a daemon
channel fires, the registered handler invokes a specific port operation
on the MorphonController singleton. The runtime's CRT scheduler then
becomes the trigger source for the cmplx ports that opt in.

Usage:

    from daemon.local_crt import LocalCRT
    from daemon.port_triggers import register_port_trigger

    crt = LocalCRT(service_name="runtime")

    # Bind atlas.boundary_recompute to fire every 7 ticks of "brain_sync".
    register_port_trigger(crt, "brain_sync", 7, "atlas", "boundary_recompute")

    crt.start_background()

The handler invocation is wrapped in try/except so a single port-operation
failure doesn't kill the CRT thread. Failures are logged at WARNING level.
"""
from __future__ import annotations

import logging
from typing import Any, Callable

logger = logging.getLogger("daemon.port_triggers")


def register_port_trigger(
    crt: Any,
    channel_name: str,
    period: int,
    port: str,
    operation: str,
    *,
    description: str = "",
    args: tuple = (),
    kwargs: dict | None = None,
) -> Callable[[], Any]:
    """Register a port-operation handler on a CRT channel.

    Args:
        crt: a ``LocalCRT`` (or compatible) instance exposing a
            ``register(channel_name, period, handler, description="")``
            method.
        channel_name: the CRT channel to bind. Should be one of the
            daemon's canonical channels (e.g., ``"brain_sync"``,
            ``"report_generate"``) or a service-local channel.
        period: tick multiplier. The handler fires every ``period``-th
            CRT tick.
        port: the MorphonController port name (e.g., ``"atlas"``).
        operation: the method name to invoke on the port's provider.
            Must be a callable attribute of the registered provider.
        description: optional human-readable description.
        args, kwargs: optional positional and keyword arguments passed
            to the port operation on each firing.

    Returns:
        The handler callable that was registered (also returned for
        introspection / direct invocation in tests).
    """
    if kwargs is None:
        kwargs = {}

    handler = make_port_handler(port, operation, args=args, kwargs=kwargs)
    desc = description or f"trigger {port}.{operation} every {period} ticks"
    crt.register(channel_name, period, handler, description=desc)
    logger.info(
        "Port trigger bound: %s.%s @ channel=%s period=%d",
        port, operation, channel_name, period,
    )
    return handler


def make_port_handler(
    port: str,
    operation: str,
    *,
    args: tuple = (),
    kwargs: dict | None = None,
) -> Callable[[], Any]:
    """Build a zero-arg callable that invokes a port operation.

    The returned handler resolves the MorphonController singleton + port
    provider at call time (not at handler-construction time), so changing
    the registered provider after handler creation still works. Failures
    are caught and logged; the handler never raises.

    Args:
        port: MorphonController port name.
        operation: method name on the port's provider.
        args, kwargs: arguments to pass.

    Returns:
        A zero-arg callable suitable for ``LocalCRT.register``.
    """
    if kwargs is None:
        kwargs = {}

    def handler() -> Any:
        try:
            from cmplx.morphon import MorphonController
            provider = MorphonController.get().get_provider(port)
            method = getattr(provider, operation, None)
            if method is None:
                logger.warning(
                    "Port trigger %s.%s: provider has no method %r",
                    port, operation, operation,
                )
                return None
            result = method(*args, **kwargs)
            logger.debug(
                "Port trigger %s.%s fired: result=%r", port, operation, result,
            )
            return result
        except Exception as exc:
            logger.warning(
                "Port trigger %s.%s failed: %s", port, operation, exc,
            )
            return None

    handler.__name__ = f"port_trigger_{port}_{operation}"
    handler.__qualname__ = f"make_port_handler.<{port}.{operation}>"
    return handler


# ─────────────────────────────────────────────────────────────────────
# Canonical channel ↔ port-operation map
# ─────────────────────────────────────────────────────────────────────
#
# Per docs/sub_frames/port_trigger_map.md §3, the following bindings are
# canonical for class-C operations. Call ``apply_canonical_bindings(crt)``
# to wire all of them in one go. Individual bindings can be overridden
# or skipped by passing ``skip=[...]``.

CANONICAL_BINDINGS: tuple[tuple[str, int, str, str], ...] = (
    # (channel_name, period, port, operation)
    ("governance_check", 31, "receipt", "verify_chain"),
    ("knowledge_sync", 37, "conservation", "ledger_compact"),
    ("brain_sync", 7, "atlas", "boundary_recompute"),
    ("report_generate", 17, "diagnostic", "pulse"),
    ("data_aggregate", 19, "memory", "prune_stale"),
    ("compose_round", 29, "cache", "evict_cold"),
    ("service_discover", 3, "routing", "recompute_lanes"),
)


def apply_canonical_bindings(
    crt: Any,
    *,
    skip: tuple[str, ...] = (),
) -> dict[str, str]:
    """Register every canonical port-trigger binding on a CRT.

    Returns a status map ``{port.operation: "bound" | "skipped" | "failed"}``.

    Bindings whose target operations don't exist on the registered provider
    (e.g., ``memory.prune_stale`` when the registered MMDB provider doesn't
    expose that method) are silently skipped — the handler logs at fire
    time, but registration succeeds. Caller can introspect the returned
    status map to see what's actually live.

    Args:
        crt: a ``LocalCRT`` (or compatible) instance.
        skip: tuple of ``"port.operation"`` strings to skip.
    """
    skip_set = set(skip)
    status: dict[str, str] = {}
    for channel_name, period, port, operation in CANONICAL_BINDINGS:
        key = f"{port}.{operation}"
        if key in skip_set:
            status[key] = "skipped"
            continue
        try:
            register_port_trigger(crt, channel_name, period, port, operation)
            status[key] = "bound"
        except Exception as exc:
            status[key] = f"failed: {exc}"
            logger.warning("Canonical binding %s failed: %s", key, exc)
    return status
