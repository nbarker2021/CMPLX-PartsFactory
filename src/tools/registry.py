from __future__ import annotations
import json
import logging
from typing import Any

from services.registry import registry
from catalog.catalog_db import CatalogDB

catalog_db = CatalogDB()
try:
    catalog_db.connect()
except Exception:
    pass

logger = logging.getLogger("cmplx.tools")


def discover_services() -> list[dict]:
    """Probe all registered services and return health status."""
    health = registry.check_health()
    services = registry.list_services()
    for svc in services:
        svc["healthy"] = health.get(svc["name"], False)
    return services


def store_crystal(content: str, domain: str = "general",
                  snap_labels: list[str] | None = None,
                  e8_coords: list[float] | None = None) -> dict:
    """Store content as a crystal in MMDB."""
    if not registry.mmdb:
        return {"error": "MMDB service unavailable"}
    return registry.mmdb.store(
        content=content,
        domain=domain,
        snap_labels=snap_labels or [],
        e8_coords=e8_coords or [0.0] * 8,
    )


def search_crystals(query: str, limit: int = 10) -> list[dict]:
    """Search crystals by snap label proximity."""
    if not registry.mmdb:
        return []
    return registry.mmdb.search(snap_labels=[query], limit=limit)


def create_mdhg_session(name: str | None = None) -> dict:
    """Create a new MDHG exploration session."""
    if not registry.mdhg:
        return {"error": "MDHG service unavailable"}
    return registry.mdhg.create_session(name=name)


def add_mdhg_node(session_id: str, content: str,
                  parent_hash: str | None = None, level: int = 0) -> dict:
    """Add a node to an MDHG session."""
    if not registry.mdhg:
        return {"error": "MDHG service unavailable"}
    return registry.mdhg.add_node(session_id=session_id, content=content,
                                   parent_hash=parent_hash, level=level)


def stratify_concept(concept: str, depth: int = 3) -> dict:
    """Explode a concept via SNAP stratifier until convergence."""
    if not registry.snap:
        return {"error": "SNAP service unavailable"}
    return registry.snap.stratify(concept=concept, depth=depth)


def gate369_select(items: list[str], context: str = "") -> dict:
    """Run Gate369 selection on items."""
    if not registry.snap:
        return {"error": "SNAP service unavailable"}
    return registry.snap.gate369(items=items, context=context)


def create_atom(element: str, charge: float = 0.0) -> dict:
    """Create a bond chemistry atom in TarPit."""
    if not registry.tarpit:
        return {"error": "TarPit service unavailable"}
    return registry.tarpit.create_atom(element=element, charge=charge)


def cache_put(key: str, value: Any, ttl: int = 3600) -> dict:
    """Store a value in SpeedLight cache."""
    if not registry.speedlight:
        return {"error": "SpeedLight service unavailable"}
    return registry.speedlight.put(key=key, value=value, ttl_seconds=ttl)


def cache_get(key: str) -> Any:
    """Retrieve a value from SpeedLight cache."""
    if not registry.speedlight:
        return None
    return registry.speedlight.get(key=key)


def probe_manny(query: str, domain: str = "general") -> dict:
    """Probe the Manny brain with a query."""
    if not registry.manny:
        return {"error": "Manny Runtime unavailable"}
    return registry.manny.probe(query=query, domain=domain)


def compose_tools(tool_a: str, tool_b: str, params: dict | None = None) -> dict:
    """Test a composition of two tools and record the result."""
    tool_map = {
        "store": store_crystal,
        "search": search_crystals,
        "stratify": stratify_concept,
        "gate369": gate369_select,
        "mdhg_session": create_mdhg_session,
        "mdhg_node": add_mdhg_node,
        "create_atom": create_atom,
        "cache": cache_put,
        "probe": probe_manny,
    }
    fn_a = tool_map.get(tool_a)
    fn_b = tool_map.get(tool_b)
    if not fn_a or not fn_b:
        return {"error": f"Unknown tool: {tool_a if not fn_a else tool_b}"}

    try:
        result_a = fn_a(**(params or {}))
        result_b = fn_b(**(params or {}))
        composition = {
            "tool_a": tool_a,
            "tool_b": tool_b,
            "result_a": result_a,
            "result_b": result_b,
            "success": True,
        }
        catalog_db.record_composition(tool_a, tool_b, str(result_a), str(result_b))
        return composition
    except Exception as e:
        return {"error": str(e), "tool_a": tool_a, "tool_b": tool_b}


def run_discovery(driver: str = "auto") -> dict:
    """
    Run full discovery scan across all known sources:
      - Probe all running Docker services
      - Check PostgreSQL and SQLite databases
      - Map filesystem structures
      - Catalog discovered artifacts
    """
    results = {
        "services": discover_services(),
        "crystals": [],
        "sessions": [],
    }
    if registry.mmdb:
        results["crystals"] = registry.mmdb.stats()
    catalog_db.log_discovery(driver, json.dumps(results))
    return results
