"""
Morphon — the system's atomic-and-outer-bound primitive.

This implementation follows `INTERFACE.md`. It is hand-built, not
auto-merged. Where useful behavior was identified in the historical
composed canonicals (preserved at `_history_reference/`), it is
either inlined here or noted for extraction.

The Morphon stays usable standalone (no bridge required) for
inspection and lifecycle transitions. Operations that need
neighboring components route through `MorphonController` — see
`BRIDGE.md`.
"""
from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from typing import Any, Mapping, Optional

from .state import MorphonState, assert_transition, is_terminal


@dataclass(frozen=True)
class Receipt:
    """A single event in a morphon's history.

    Receipts are append-only and themselves immutable. The chain of
    receipts on a morphon is its provenance record.
    """
    operation: str
    timestamp: str
    detail: Mapping[str, Any] = field(default_factory=dict)


@dataclass
class Morphon:
    """The atomic-and-outer-bound unit.

    A morphon is structurally a payload + coefficients across geometries
    + a state-machine cursor + an append-only receipt chain. The class
    here stays minimal — operations that change substance (evolution,
    persistence, admission, transport) route through the controller.
    """

    # Identity
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    # Payload — the content this morphon carries
    payload: Mapping[str, Any] = field(default_factory=dict)

    # Lifecycle
    state: MorphonState = MorphonState.CREATED

    # Coefficient table (filled by bridge providers when asked).
    # `None` means "not yet projected onto that geometry."
    e8_coordinates: Optional[tuple[float, ...]] = None
    leech_point: Optional[str] = None
    dr_channel: Optional[int] = None

    # CQE-specific projections (filled by `engine.cqe` when relevant).
    # These exist on the base Morphon because CQE is the pre-CMPLX
    # identity for every system in this build (per design history);
    # CQE atoms ARE morphons with these fields populated.
    quad_encoding: Optional[tuple[int, int, int, int]] = None
    parity_channels: Optional[tuple[int, ...]] = None
    sacred_frequency: Optional[float] = None
    digital_root: Optional[int] = None
    fractal_coordinate: Optional[complex] = None

    # Lineage
    parent: Optional[str] = None
    children: tuple[str, ...] = field(default_factory=tuple)

    # Receipt chain — append-only
    receipts: tuple[Receipt, ...] = field(default_factory=tuple)

    # ------------------------------------------------------------------
    # Construction
    # ------------------------------------------------------------------

    @classmethod
    def forge(
        cls,
        payload: Mapping[str, Any],
        *,
        parent: Optional[str] = None,
        morphon_id: Optional[str] = None,
    ) -> "Morphon":
        """Construct a new morphon at state CREATED.

        Use the `parent` argument to record lineage when a morphon is
        born inside another's evolution.

        Every forged morphon carries ``payload["identity_kind"]`` so
        substrate atoms are distinguishable from TarPit ``Atom`` (ETP
        compression) and from bare receipt ``atom_id`` strings.
        """
        body = dict(payload)
        if body.get("etp_decode"):
            body.setdefault("identity_kind", "morphon_etp_derived")
        else:
            body.setdefault("identity_kind", "morphon")
        m = cls(
            id=morphon_id or str(uuid.uuid4()),
            payload=body,
            parent=parent,
        )
        return m._with_receipt("forge", {"parent": parent})

    # ------------------------------------------------------------------
    # State machine
    # ------------------------------------------------------------------

    def transition_to(self, new_state: MorphonState) -> "Morphon":
        """Advance the lifecycle. Returns a NEW morphon (Morphon is
        treated as immutable from outside; the dataclass is mutable
        but the contract is value-typed).

        Raises `ValueError` if the transition is illegal.
        """
        assert_transition(self.state, new_state)
        new = replace(self, state=new_state)
        return new._with_receipt(
            "transition",
            {"from": self.state.name, "to": new_state.name},
        )

    def is_terminal(self) -> bool:
        """Return True if this morphon is in a state that has no
        further transitions."""
        return is_terminal(self.state)

    # ------------------------------------------------------------------
    # Receipt chain
    # ------------------------------------------------------------------

    def attach_receipt(self, receipt: Receipt) -> "Morphon":
        """Append a receipt to the chain. Receipts are append-only —
        existing receipts are never replaced."""
        return replace(self, receipts=self.receipts + (receipt,))

    def _with_receipt(self, operation: str, detail: Mapping[str, Any]) -> "Morphon":
        """Internal helper: append a receipt for a structural event."""
        r = Receipt(
            operation=operation,
            timestamp=datetime.now(timezone.utc).isoformat(),
            detail=dict(detail),
        )
        updated = self.attach_receipt(r)
        if operation in ("forge", "transition", "evolved_from"):
            from ._receipt_bridge import mint_morphon_event

            mint_morphon_event(
                operation,
                morphon_id=updated.id,
                detail={"state": updated.state.name, **dict(detail)},
            )
        return updated

    # ------------------------------------------------------------------
    # Payload evolution
    # ------------------------------------------------------------------

    def with_payload(self, payload: Mapping[str, Any]) -> "Morphon":
        """Return a new morphon (NEW id) carrying a new payload, with
        `self` recorded as parent. This is the structural shape of
        evolution: substance changes produce a new morphon, not a
        mutation of the existing one.
        """
        child = Morphon.forge(payload=payload, parent=self.id)
        # Existing morphon notes the new child in its receipt chain.
        # (We can't actually mutate self.children without breaking the
        # immutability contract; callers should rely on the receipt for
        # forward links and on `parent` for backward links.)
        return child._with_receipt(
            "evolved_from",
            {"parent_state": self.state.name},
        )

    # ------------------------------------------------------------------
    # Geometric projections — these route through the bridge if a
    # provider is registered, else raise.
    # ------------------------------------------------------------------

    def project_to_channel(self) -> int:
        """Return the digital-root channel for this morphon's payload.

        Requires `addressing` bridge provider to be registered.
        Caches the result on `self.dr_channel`.
        """
        if self.dr_channel is not None:
            return self.dr_channel
        # Lazy import to avoid a controller import-cycle at module load.
        from .controller import MorphonController
        provider = MorphonController.get().get_provider("addressing")
        channel = provider.channel_for(self)
        self.dr_channel = channel
        return channel

    def project_to_e8(self) -> tuple[float, ...]:
        """Return the 8-D E8 projection. Requires `geometry` bridge."""
        if self.e8_coordinates is not None:
            return self.e8_coordinates
        from .controller import MorphonController
        provider = MorphonController.get().get_provider("geometry")
        coords = tuple(provider.e8_coordinates(self))
        self.e8_coordinates = coords
        return coords

    def project_to_leech(self) -> str:
        """Return the encoded Leech-lattice point. Requires `geometry`."""
        if self.leech_point is not None:
            return self.leech_point
        from .controller import MorphonController
        provider = MorphonController.get().get_provider("geometry")
        point = provider.leech_point(self)
        self.leech_point = point
        return point

    # ------------------------------------------------------------------
    # Serialization
    # ------------------------------------------------------------------

    def serialize(self) -> dict[str, Any]:
        """Produce a JSON-safe dict round-trippable via `deserialize`."""
        return {
            "id": self.id,
            "created_at": self.created_at,
            "payload": dict(self.payload),
            "state": self.state.name,
            "e8_coordinates": list(self.e8_coordinates) if self.e8_coordinates else None,
            "leech_point": self.leech_point,
            "dr_channel": self.dr_channel,
            "parent": self.parent,
            "children": list(self.children),
            "receipts": [
                {"operation": r.operation, "timestamp": r.timestamp,
                 "detail": dict(r.detail)}
                for r in self.receipts
            ],
        }

    @classmethod
    def deserialize(cls, data: Mapping[str, Any]) -> "Morphon":
        """Reconstruct a morphon from `serialize()` output."""
        return cls(
            id=data["id"],
            created_at=data["created_at"],
            payload=dict(data.get("payload") or {}),
            state=MorphonState[data["state"]],
            e8_coordinates=(
                tuple(data["e8_coordinates"])
                if data.get("e8_coordinates") is not None
                else None
            ),
            leech_point=data.get("leech_point"),
            dr_channel=data.get("dr_channel"),
            parent=data.get("parent"),
            children=tuple(data.get("children") or ()),
            receipts=tuple(
                Receipt(
                    operation=r["operation"],
                    timestamp=r["timestamp"],
                    detail=dict(r.get("detail") or {}),
                )
                for r in (data.get("receipts") or ())
            ),
        )

    def to_json(self) -> str:
        return json.dumps(self.serialize(), ensure_ascii=False)

    @classmethod
    def from_json(cls, s: str) -> "Morphon":
        return cls.deserialize(json.loads(s))
