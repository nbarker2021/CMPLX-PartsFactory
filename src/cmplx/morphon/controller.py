"""
MorphonController — the bridge runtime.

See `BRIDGE.md` for the full contract. This module implements the
small registry that lets other components plug operations into the
morphon package without circular imports.

Other components register a *provider* against a *port*; user code
asks the morphon for an operation that needs that port; the
controller looks up the provider and dispatches.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Mapping, Protocol, runtime_checkable

from .morphon import Morphon, Receipt


# ---------------------------------------------------------------------------
# Common types — shared report shapes for Protocols below
# ---------------------------------------------------------------------------

@dataclass
class FourEmbedView:
    """Typed decomposition of a morphon into 4 channels.

    Per Aletheia_CQE_Operational_Package §4-Embed Model: any morphon can be
    viewed through four independent typed channels, each carrying a distinct
    semantic role:

      - **constraint**: laws, policies, invariants the morphon must satisfy.
        Read-only contract surface.
      - **state**: the current value/payload. The mutable "what is."
      - **evidence**: facts/data backing the state. Provenance + witness.
      - **operator**: how to transform this morphon. Available actions.

    The four channels are explicit so consumers (Aletheia laws, MORSR
    diagnostics, ThinkTank deliberation, etc.) can read just the channel
    they need without conflating fact-vs-assumption-vs-action.

    A morphon payload that uses the explicit shape
    ``{"constraint": ..., "state": ..., "evidence": ..., "operator": ...}``
    decomposes cleanly. Otherwise the whole payload is treated as state
    and the other channels default to empty.
    """

    constraint: Any = None
    state: Any = None
    evidence: Any = None
    operator: Any = None
    morphon_id: str = ""


@dataclass
class SymbolicReport:
    """Dual-report returned by ``SymbolicProvider.derive()``.

    Per the port-facades sub-frame (decision 2026-05-17): callers receive
    both the typed trace AND the raw ecology so all categorical types,
    labels, and receipts associated with each are available to them. No
    information is hidden behind the typed view; the raw ecology remains
    a full-surface escape hatch.

    Fields:
        trace: stepwise ledger rows (one dict per ETP execution step). Each
            row carries ip/ptr/grain-count/torus8/wall10/error_class and the
            full state snapshot. Deterministic per (program, seed).
        ecology: the raw TarpitEcology instance (Any to avoid leaking
            tarpit-internal types into the morphon Protocol surface).
        output_walls: OutputWall instances emitted during the run.
        error_walls: ErrorWall instances + mirror recovery hints.
        receipts: cmplx.receipt.Receipt list — populated by the runner
            when the `receipt` port is registered, empty otherwise.
        summary: the final summary dict (halted, bonds_formed, final_mass,
            wall_serial, etc.) from run_etp_with_ledger.
    """

    trace: list[dict] = field(default_factory=list)
    ecology: Any = None
    output_walls: list = field(default_factory=list)
    error_walls: list = field(default_factory=list)
    receipts: list = field(default_factory=list)
    summary: dict = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Provider protocols
#
# ETP (Encoded Tarpit Program) is the universal IR — symbolic, addressing,
# memory, and transport Protocols all expose ``encode_to_etp(morphon) -> str``
# and ``decode_from_etp(ledger) -> Morphon`` so the four ports share a single
# wire format. Each Protocol's port-specific methods are built on top of that
# common encode/decode pair.
# ---------------------------------------------------------------------------

@runtime_checkable
class AddressingProvider(Protocol):
    """`addressing` port — typically implemented by cmplx.addressing.mdhg.

    Core method: ``channel_for``. Extensions (Wave 1, per port-facades
    sub-frame): multi-scale slot quantization + ETP encode/decode.
    """

    # core
    def channel_for(self, morphon: "Morphon") -> int:
        """Return the digital-root channel (1-9) for this morphon's payload."""

    # multi-scale extensions
    def quantize24(self, morphon: "Morphon") -> tuple[int, ...]:
        """Return the 24-element MDHG quantization tuple for this morphon."""

    def slot_id(self, q24: tuple[int, ...]) -> str:
        """Return the stable slot ID string for a 24-tuple quantization."""

    # ETP integration
    def encode_to_etp(self, morphon: "Morphon") -> str:
        """Encode this morphon as an ETP program string.

        The encoding routes through this provider's addressing scheme so
        that a morphon's address shape is reflected in the ETP program.
        """

    def decode_from_etp(self, ledger: list[dict]) -> "Morphon":
        """Reconstruct a Morphon from an ETP ledger. Round-trip with encode_to_etp."""


@runtime_checkable
class GeometryProvider(Protocol):
    """`geometry` port — cmplx.geometry.{e8,leech,niemeier}."""

    def e8_coordinates(self, morphon: "Morphon") -> tuple[float, ...]:
        ...

    def leech_point(self, morphon: "Morphon") -> str:
        ...


@runtime_checkable
class MemoryProvider(Protocol):
    """`memory` port — cmplx.memory.mmdb.

    Core methods: ``store`` / ``fetch``. Extensions (Wave 1, per port-facades
    sub-frame): edge traversal + E8-coordinate queries + ETP encode/decode.
    """

    # core
    def store(self, morphon: "Morphon") -> None: ...
    def fetch(self, morphon_id: str) -> "Morphon | None": ...

    # edge traversal extensions
    def store_edge(
        self,
        from_id: str,
        to_id: str,
        relation: str,
        weight: float = 1.0,
    ) -> None:
        """Record a typed weighted edge between two stored morphons."""

    def neighbors(
        self,
        morphon_id: str,
        relation: str | None = None,
    ) -> list[str]:
        """Return morphon IDs reachable from morphon_id via edges of relation.

        If relation is None, return neighbors over all relation types.
        """

    # E8-coordinate query
    def by_e8_coordinates(
        self,
        coords: tuple[float, ...],
        radius: float = 0.0,
    ) -> list["Morphon"]:
        """Return stored morphons whose E8 coordinates fall within radius of coords."""

    # ETP integration
    def encode_to_etp(self, morphon: "Morphon") -> str:
        """Encode the morphon as an ETP program reflecting its stored shape."""

    def decode_from_etp(self, ledger: list[dict]) -> "Morphon":
        """Reconstruct a Morphon from an ETP ledger."""


@runtime_checkable
class ConstraintsProvider(Protocol):
    """`constraints` port — cmplx.constraints.aletheia."""

    def admit(self, morphon: "Morphon") -> tuple[bool, str]:
        """Return (admitted, reason_if_rejected_else_empty)."""


@runtime_checkable
class EngineProvider(Protocol):
    """`engine` port — cmplx.engine.cqe."""

    def evolve(self, morphon: "Morphon", op: str, **kwargs: Any) -> "Morphon": ...


@runtime_checkable
class AtlasProvider(Protocol):
    """`atlas` port — Mandelbrot deployment boundary + Julia c-assignment.

    Each Morphon IS a Julia set with fixed c (Observer-Julia Correspondence
    from the Atlas Microkernel Architecture). The Atlas keeps the
    Morphon-Mandelbrot Isomorphism honest: deployment is bounded by the
    Mandelbrot set, c-values are derived from Morphon identity.

    Operations and their trigger classes (per
    docs/sub_frames/port_trigger_map.md):

      - ``julia_c``: A (user) or B (event-driven at forge)
      - ``in_boundary``: A (user query) or B (admission)
      - ``admit_to_deployment``: B (fires inside admit_and_store)
      - ``deployment_stats``: A (read-only)
      - ``boundary_recompute``: C (daemon-periodic, when wired)

    Parent frame Slots 26 (atlas-mandelbrot) + 27 (julia-c-assignment).
    """

    def julia_c(self, morphon: "Morphon") -> complex: ...
    def in_boundary(self, c: complex, *, max_iter: int | None = None) -> bool: ...
    def admit_to_deployment(self, morphon: "Morphon") -> tuple[bool, str]: ...
    def deployment_stats(self) -> dict: ...
    def encode_to_etp(self, morphon: "Morphon") -> str: ...
    def decode_from_etp(self, ledger: list[dict]) -> "Morphon": ...


@runtime_checkable
class EmbedProvider(Protocol):
    """`embed` port — 4-Embed Model decomposition.

    Decomposes a morphon into the typed Constraint/State/Evidence/Operator
    channels of the 4-Embed Model. Implementations live in ``cmplx.embed``.
    Consumers (Aletheia, MORSR, ThinkTank) read just the channel they need.

    Also exposes the universal ETP encode/decode pair (the 4-Embed view
    can be projected onto an ETP program with channel tagging so the IR
    carries the typed decomposition across transport).
    """

    def decompose(self, morphon: "Morphon") -> "FourEmbedView":
        """Return the 4-channel typed view of this morphon."""

    def encode_to_etp(self, morphon: "Morphon") -> str:
        """Encode the morphon (with 4-channel awareness) as an ETP program."""

    def decode_from_etp(self, ledger: list[dict]) -> "Morphon":
        """Reconstruct a morphon from an ETP ledger."""


@runtime_checkable
class SymbolicProvider(Protocol):
    """`symbolic` port — cmplx.symbolic.tarpit; the ETP IR runtime.

    Surfaces ETP both as a high-level ``derive(morphon)`` operation (returning
    a dual-report SymbolicReport per user 2026-05-17 decision) and as a raw
    ``run_program(program, ...)`` execution. Also exposes the universal
    encode/decode pair that other Protocols (addressing/memory/transport)
    consume — the SymbolicProvider IS the canonical ETP encode/decode source.
    """

    def derive(self, morphon: "Morphon") -> "SymbolicReport":
        """Run ETP on the morphon's payload. Returns dual-report (trace + ecology)."""

    def run_program(self, program: str, **kwargs: Any) -> dict:
        """Direct ETP execution. Returns ``{summary, ledger}`` dict shape from
        run_etp_with_ledger. Lower-level than derive(); for callers who want
        full control over the program string and runner kwargs."""

    def encode_to_etp(self, morphon: "Morphon") -> str:
        """Canonical morphon → ETP-program string encoding. The IR's source-of-truth
        for how a Morphon becomes an ETP program. Other Protocols' encode_to_etp
        methods typically delegate here (possibly after port-specific prefixing)."""

    def decode_from_etp(self, ledger: list[dict]) -> "Morphon":
        """Canonical ETP ledger → Morphon round-trip from encode_to_etp."""


@runtime_checkable
class TransportProvider(Protocol):
    """`transport` port — cmplx.transport carriers (chirp/dtmf/pixel/etc.).

    Core methods: ``encode`` / ``decode``. ETP integration: encode_to_etp /
    decode_from_etp are the canonical wire-format for cross-channel transport;
    encode/decode bytes are the physical channel-specific representation
    (chirp tones, pixel matrices, etc.) wrapping ETP.
    """

    # physical channel encoding
    def encode(self, morphon: "Morphon") -> bytes:
        """Encode the morphon as physical-channel bytes (chirp / pixel / etc.)."""

    def decode(self, payload: bytes) -> "Morphon":
        """Decode physical-channel bytes back into a Morphon. Round-trip with encode."""

    # ETP integration (wire format used for cross-channel transport)
    def encode_to_etp(self, morphon: "Morphon") -> str:
        """Encode the morphon as an ETP program for cross-channel transport."""

    def decode_from_etp(self, ledger: list[dict]) -> "Morphon":
        """Reconstruct a Morphon from an ETP ledger received over a channel."""


# Known ports — extending the system means adding a port here and
# implementing a provider somewhere.
KNOWN_PORTS: frozenset[str] = frozenset({
    "addressing",
    "geometry",
    "memory",
    "constraints",
    "engine",
    "transport",
    "symbolic",
    "routing",
    "crystal",
    "snap",
    "cache",
    "conservation",
    "diagnostic",
    "receipt",
    "embed",  # 4-Embed Model — Constraint/State/Evidence/Operator decomposition
    "atlas",  # Mandelbrot deployment boundary + Julia c-assignment (Slots 26-27)
})


# ---------------------------------------------------------------------------
# The controller
# ---------------------------------------------------------------------------

class MorphonController:
    """Singleton registry mediating operations across component boundaries.

    Access via ``MorphonController.get()``.
    """

    _instance: "MorphonController | None" = None

    def __init__(self) -> None:
        self._providers: dict[str, Any] = {}

    # -- singleton --------------------------------------------------------

    @classmethod
    def get(cls) -> "MorphonController":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def reset_for_tests(cls) -> None:
        """Discard the singleton. Test fixtures use this between cases."""
        cls._instance = None

    # -- registration -----------------------------------------------------

    def register(self, port: str, provider: Any) -> None:
        if port not in KNOWN_PORTS:
            raise ValueError(
                f"unknown port {port!r}; known: {sorted(KNOWN_PORTS)}"
            )
        if port in self._providers:
            raise RuntimeError(
                f"port {port!r} already has a registered provider"
            )
        self._providers[port] = provider
        from ._receipt_bridge import mint_morphon_event

        mint_morphon_event(
            "register",
            detail={"port": port, "provider": getattr(provider, "name", type(provider).__name__)},
        )

    def has(self, port: str) -> bool:
        return port in self._providers

    def get_provider(self, port: str) -> Any:
        if port not in self._providers:
            from ._receipt_bridge import mint_morphon_event

            mint_morphon_event(
                "gate_miss",
                detail={"port": port, "registered": sorted(self._providers)},
            )
            raise LookupError(
                f"no provider registered for port {port!r} "
                f"(registered: {sorted(self._providers)})"
            )
        return self._providers[port]

    def register_remote_provider(
        self, port: str, mesh: Any, service_name: str
    ) -> None:
        """Register a remote mesh-discovered service as the provider for a port.

        The proxy class lives in ``mesh.morphon_bridge`` so that ``cmplx`` does
        not import the mesh layer at module load. The import here is local —
        triggered only when a runtime that has the mesh layer calls this method.

        After registration, the behavior is identical to ``register(port, ...)``
        with an in-process provider: ``get_provider(port)`` returns the proxy,
        and any method call on the proxy dispatches through ``mesh.request``.

        Validation (unknown port, double-registration) is delegated to the
        standard ``register`` method.
        """
        from mesh.morphon_bridge import _MeshServiceProxy  # local — see docstring
        self.register(port, _MeshServiceProxy(mesh, service_name))

    # -- compound operations ---------------------------------------------

    def admit_and_store(self, morphon: Morphon) -> Morphon:
        """Run a morphon through the full admit→address→geometry→store
        sequence. Each step's provider must be registered; otherwise
        LookupError surfaces from the first missing port.

        Records one summary receipt for the whole sequence.
        """
        used_ports: list[str] = []

        # 1. admission
        constraints = self.get_provider("constraints")
        admitted, reason = constraints.admit(morphon)
        used_ports.append("constraints")
        if not admitted:
            raise PermissionError(
                f"morphon {morphon.id} rejected by constraints: {reason}"
            )

        # 1b. atlas — Mandelbrot deployment-boundary check (Slots 26-27).
        # Optional: only runs if the atlas port is registered. Verifies the
        # morphon's Julia c-value is inside the Mandelbrot boundary AND the
        # current deployment has headroom under the kissing-number capacity.
        if self.has("atlas"):
            atlas = self.get_provider("atlas")
            atlas_ok, atlas_reason = atlas.admit_to_deployment(morphon)
            used_ports.append("atlas")
            if not atlas_ok:
                raise PermissionError(
                    f"morphon {morphon.id} rejected by atlas: {atlas_reason}"
                )

        # 2. addressing — cache DR channel
        addressing = self.get_provider("addressing")
        morphon.dr_channel = addressing.channel_for(morphon)
        used_ports.append("addressing")

        # 3. geometry — cache E8 + Leech projections
        if self.has("geometry"):
            geometry = self.get_provider("geometry")
            morphon.e8_coordinates = tuple(geometry.e8_coordinates(morphon))
            morphon.leech_point = geometry.leech_point(morphon)
            used_ports.append("geometry")

        # 4. attach the summary receipt BEFORE persistence so the
        # stored row reflects the full chain.
        used_ports.append("memory")
        finalized = morphon.attach_receipt(Receipt(
            operation="admit_and_store",
            timestamp=datetime.now(timezone.utc).isoformat(),
            detail={"ports_used": used_ports},
        ))

        # 5. persist
        memory = self.get_provider("memory")
        memory.store(finalized)
        return finalized

    def evolve(self, morphon: Morphon, op: str, **kwargs: Any) -> Morphon:
        """Run a CQE operation on the morphon. Returns the new morphon."""
        engine = self.get_provider("engine")
        new = engine.evolve(morphon, op, **kwargs)
        return new.attach_receipt(Receipt(
            operation=f"evolve:{op}",
            timestamp=datetime.now(timezone.utc).isoformat(),
            detail={"parent": morphon.id, **{k: str(v) for k, v in kwargs.items()}},
        ))


# ---------------------------------------------------------------------------
# Convenience: module-level helpers that delegate to the singleton
# ---------------------------------------------------------------------------

def register(port: str, provider: Any) -> None:
    """Register a provider against a port. See ``MorphonController.register``."""
    MorphonController.get().register(port, provider)


def get_provider(port: str) -> Any:
    """Return the registered provider for a port, or raise LookupError."""
    return MorphonController.get().get_provider(port)
