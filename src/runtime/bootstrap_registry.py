"""
Canonical bootstrap port registry — single source of truth for W0+ catalog emit.

``runtime.cmplx_bootstrap.register_all`` must register every port listed here.
"""
from __future__ import annotations

from typing import Any, TypedDict


class BootstrapPortSpec(TypedDict, total=False):
    port: str
    part_id: str
    package: str
    module: str
    provider_class: str
    landing_path: str
    remote_service: str | None
    depends_on: list[str]
    pytest_target: str
    import_modules: list[str]


# Mirrors ``cmplx_bootstrap`` factories (2026-05-21). Update when adding a port.
BOOTSTRAP_PORT_SPECS: tuple[BootstrapPortSpec, ...] = (
    {
        "port": "receipt",
        "part_id": "receipt-chain",
        "package": "cmplx.receipt",
        "module": "cmplx.receipt.provider",
        "provider_class": "ReceiptProvider",
        "landing_path": "src/cmplx/receipt",
        "remote_service": None,
        "depends_on": [],
        "pytest_target": "tests/receipt/",
        "import_modules": ["cmplx.receipt.provider"],
    },
    {
        "port": "conservation",
        "part_id": "nsl-conservation",
        "package": "cmplx.nsl",
        "module": "cmplx.nsl.provider",
        "provider_class": "NSLProvider",
        "landing_path": "src/cmplx/nsl",
        "remote_service": None,
        "depends_on": ["receipt-chain"],
        "pytest_target": "tests/nsl/",
        "import_modules": ["cmplx.nsl.provider"],
    },
    {
        "port": "diagnostic",
        "part_id": "morsr-diagnostic",
        "package": "cmplx.morsr",
        "module": "cmplx.morsr.provider",
        "provider_class": "MORSRProvider",
        "landing_path": "src/cmplx/morsr",
        "remote_service": None,
        "depends_on": ["receipt-chain"],
        "pytest_target": "tests/morsr/",
        "import_modules": ["cmplx.morsr.provider"],
    },
    {
        "port": "geometry",
        "part_id": "geometry-e8",
        "package": "cmplx.geometry",
        "module": "cmplx.geometry.provider",
        "provider_class": "Geometry",
        "landing_path": "src/cmplx/geometry",
        "remote_service": None,
        "depends_on": ["receipt-chain"],
        "pytest_target": "tests/geometry/",
        "import_modules": ["cmplx.geometry.provider"],
    },
    {
        "port": "constraints",
        "part_id": "constraints-aletheia",
        "package": "cmplx.constraints",
        "module": "cmplx.constraints.aletheia",
        "provider_class": "Aletheia",
        "landing_path": "src/cmplx/constraints",
        "remote_service": None,
        "depends_on": ["receipt-chain"],
        "pytest_target": "tests/constraints/",
        "import_modules": ["cmplx.constraints.aletheia"],
    },
    {
        "port": "engine",
        "part_id": "engine-cqe",
        "package": "cmplx.engine.cqe",
        "module": "cmplx.engine.cqe.provider",
        "provider_class": "CQEProvider",
        "landing_path": "src/cmplx/engine/cqe",
        "remote_service": None,
        "depends_on": ["receipt-chain", "constraints-aletheia"],
        "pytest_target": "tests/engine/",
        "import_modules": ["cmplx.engine.cqe.provider"],
    },
    {
        "port": "transport",
        "part_id": "transport-carriers",
        "package": "cmplx.transport",
        "module": "cmplx.transport",
        "provider_class": "TransportProviderFacade",
        "landing_path": "src/cmplx/transport",
        "remote_service": None,
        "depends_on": ["receipt-chain"],
        "pytest_target": "tests/transport/",
        "import_modules": ["cmplx.transport"],
    },
    {
        "port": "embed",
        "part_id": "embed-four-channel",
        "package": "cmplx.embed",
        "module": "cmplx.embed",
        "provider_class": "FourEmbedProvider",
        "landing_path": "src/cmplx/embed",
        "remote_service": None,
        "depends_on": ["receipt-chain"],
        "pytest_target": "tests/embed/",
        "import_modules": ["cmplx.embed"],
    },
    {
        "port": "atlas",
        "part_id": "atlas-mandelbrot",
        "package": "cmplx.atlas",
        "module": "cmplx.atlas",
        "provider_class": "AtlasProvider",
        "landing_path": "src/cmplx/atlas",
        "remote_service": None,
        "depends_on": ["receipt-chain", "geometry-e8"],
        "pytest_target": "tests/atlas/",
        "import_modules": ["cmplx.atlas"],
    },
    {
        "port": "memory",
        "part_id": "mmdb-memory",
        "package": "cmplx.memory.mmdb",
        "module": "cmplx.memory.mmdb",
        "provider_class": "MMDBMemoryProvider",
        "landing_path": "src/cmplx/memory/mmdb",
        "remote_service": "mmdb",
        "depends_on": ["receipt-chain", "mdhg-addressing", "morphon-substrate"],
        "pytest_target": "tests/memory/",
        "import_modules": ["cmplx.memory.mmdb"],
    },
    {
        "port": "addressing",
        "part_id": "mdhg-addressing",
        "package": "cmplx.addressing.mdhg",
        "module": "cmplx.addressing.mdhg",
        "provider_class": "MDHGAddressingProvider",
        "landing_path": "src/cmplx/addressing/mdhg",
        "remote_service": "mdhg",
        "depends_on": ["receipt-chain", "morphon-substrate"],
        "pytest_target": "tests/addressing/",
        "import_modules": ["cmplx.addressing.mdhg"],
    },
    {
        "port": "routing",
        "part_id": "agrm-routing",
        "package": "cmplx.routing",
        "module": "cmplx.routing.provider",
        "provider_class": "AGRMRoutingProvider",
        "landing_path": "src/cmplx/routing",
        "remote_service": None,
        "depends_on": ["mdhg-addressing", "morphon-substrate"],
        "pytest_target": "tests/routing/",
        "import_modules": ["cmplx.routing.provider"],
    },
    {
        "port": "symbolic",
        "part_id": "tarpit-symbolic",
        "package": "cmplx.symbolic.tarpit",
        "module": "cmplx.symbolic.tarpit",
        "provider_class": "TarPitSymbolicProvider",
        "landing_path": "src/cmplx/symbolic/tarpit",
        "remote_service": "tarpit",
        "depends_on": ["receipt-chain"],
        "pytest_target": "tests/symbolic/",
        "import_modules": ["cmplx.symbolic.tarpit"],
    },
    {
        "port": "snap",
        "part_id": "snap-stratification",
        "package": "cmplx.snap",
        "module": "cmplx.snap.provider",
        "provider_class": "SNAPEngine",
        "landing_path": "src/cmplx/snap",
        "remote_service": "snap",
        "depends_on": ["receipt-chain", "morphon-substrate"],
        "pytest_target": "tests/snap/",
        "import_modules": ["cmplx.snap.provider"],
    },
    {
        "port": "cache",
        "part_id": "speedlight-worldline",
        "package": "cmplx.speedlight",
        "module": "cmplx.speedlight.provider",
        "provider_class": "SpeedLightProvider",
        "landing_path": "src/cmplx/speedlight",
        "remote_service": "speedlight",
        "depends_on": ["receipt-chain"],
        "pytest_target": "tests/speedlight/",
        "import_modules": ["cmplx.speedlight.provider"],
    },
    {
        "port": "hash_lanes",
        "part_id": "hash-lanes",
        "package": "cmplx.hash_lanes",
        "module": "cmplx.hash_lanes",
        "provider_class": "HashLanesProvider",
        "landing_path": "src/cmplx/hash_lanes",
        "remote_service": None,
        "depends_on": ["mdhg-addressing", "agrm-routing", "receipt-chain"],
        "pytest_target": "tests/hash_lanes/",
        "import_modules": ["cmplx.hash_lanes"],
    },
    {
        "port": "crystal",
        "part_id": "crystal-registry",
        "package": "cmplx.crystal",
        "module": "cmplx.crystal",
        "provider_class": "CrystalRegistry",
        "landing_path": "src/cmplx/crystal",
        "remote_service": None,
        "depends_on": [
            "receipt-chain",
            "snap-stratification",
            "mdhg-addressing",
            "morphon-substrate",
        ],
        "pytest_target": "tests/crystal/",
        "import_modules": ["cmplx.crystal", "cmplx.crystal.registry"],
    },
    {
        "port": "worlds",
        "part_id": "lattice-forge",
        "package": "cmplx.worlds.forge",
        "module": "cmplx.worlds.forge.provider",
        "provider_class": "WorldsForgeProvider",
        "landing_path": "src/cmplx/worlds/forge",
        "remote_service": "forge",
        "depends_on": ["receipt-chain", "geometry-e8", "tarpit-symbolic"],
        "pytest_target": "tests/worlds/",
        "import_modules": ["cmplx.worlds.forge.provider", "lattice_forge"],
    },
)


def bootstrap_port_specs() -> list[BootstrapPortSpec]:
    return list(BOOTSTRAP_PORT_SPECS)


def bootstrap_port_names() -> frozenset[str]:
    return frozenset(s["port"] for s in BOOTSTRAP_PORT_SPECS)


def spec_for_port(port: str) -> BootstrapPortSpec | None:
    for spec in BOOTSTRAP_PORT_SPECS:
        if spec["port"] == port:
            return spec
    return None


def catalog_stub_from_spec(spec: BootstrapPortSpec) -> dict[str, Any]:
    """Minimal catalog part document derived from bootstrap registry."""
    port = spec["port"]
    remote = spec.get("remote_service")
    return {
        "part_id": spec["part_id"],
        "slot": f"slot-bootstrap-{port}",
        "version": "2026-05-21-w0",
        "description": f"Bootstrap-wired port {port!r} — emitted from runtime/bootstrap_registry.py",
        "package": spec["package"],
        "landing_path": spec["landing_path"],
        "depends_on": list(spec.get("depends_on") or []),
        "bootstrap_ports": [port],
        "bootstrap_source": "src/runtime/cmplx_bootstrap.py",
        "bootstrap_registry": "src/runtime/bootstrap_registry.py",
        "pluggability": "instant_with_bootstrap_factory",
        "provider": {
            "module": spec.get("module"),
            "class": spec.get("provider_class"),
        },
        "remote_service": remote,
        "import_modules": list(spec.get("import_modules") or []),
        "pytest_target": spec.get("pytest_target") or "",
        "tests": [
            f"PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest {spec.get('pytest_target', '')} -q",
            "python identity_review/scripts/emit_bootstrap_catalog_parts.py --check",
        ],
    }
