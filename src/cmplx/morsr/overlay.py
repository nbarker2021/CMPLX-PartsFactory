"""
Overlay — the state primitive pulses operate on.

Adapted from `CQE_MORSR_NewBest_v1/cqe_plus/overlay.py` (EO class).
Pure-stdlib: position is a tuple of floats; activations are a tuple
of ints (0/1) for the canonical 240-E8-root mask.
"""
from __future__ import annotations

import hashlib
import json
import time
import uuid
from dataclasses import dataclass, field
from typing import Any


DEFAULT_DIM: int = 8
DEFAULT_MASK_LEN: int = 240


def _to_floats(values, dim: int) -> tuple[float, ...]:
    out = [float(x) for x in list(values)[:dim]]
    while len(out) < dim:
        out.append(0.0)
    return tuple(out)


def _to_ints(values, dim: int) -> tuple[int, ...]:
    out = [int(x) & 1 for x in list(values)[:dim]]
    while len(out) < dim:
        out.append(0)
    return tuple(out)


@dataclass
class Overlay:
    """A MORSR state.

    `position` is the centroid coordinate (default 8-D — the E8 base).
    `activations` is the 240-bit mask of active E8 roots (default all
    zero; populate to mark which roots the overlay "occupies").
    `metadata` is arbitrary attached info.
    """

    position: tuple[float, ...] = field(default_factory=lambda: tuple(0.0 for _ in range(DEFAULT_DIM)))
    activations: tuple[int, ...] = field(default_factory=lambda: tuple(0 for _ in range(DEFAULT_MASK_LEN)))
    metadata: dict = field(default_factory=dict)
    overlay_id: str = ""
    created_at: float = 0.0

    def __post_init__(self) -> None:
        self.position = _to_floats(self.position, len(self.position) or DEFAULT_DIM)
        self.activations = _to_ints(self.activations, DEFAULT_MASK_LEN)
        if not self.overlay_id:
            self.overlay_id = uuid.uuid4().hex[:12]
        if not self.created_at:
            self.created_at = time.time()

    # ── Identity ──────────────────────────────────────────────────────

    def hash_id(self) -> str:
        """Content hash of position + activations + metadata."""
        payload = json.dumps({
            "position": list(self.position),
            "activations": list(self.activations),
            "metadata": self.metadata,
        }, sort_keys=True, default=str)
        return hashlib.sha256(payload.encode()).hexdigest()[:24]

    # ── Cloning ───────────────────────────────────────────────────────

    def clone(self, **overrides: Any) -> "Overlay":
        """Return a fresh Overlay with a new id and optional field overrides."""
        new = Overlay(
            position=overrides.get("position", self.position),
            activations=overrides.get("activations", self.activations),
            metadata=overrides.get("metadata", dict(self.metadata)),
        )
        return new

    # ── Active-index helpers ─────────────────────────────────────────

    def active_indices(self) -> list[int]:
        return [i for i, b in enumerate(self.activations) if b]

    def is_active(self, index: int) -> bool:
        return 0 <= index < len(self.activations) and self.activations[index] == 1

    def num_active(self) -> int:
        return sum(self.activations)

    # ── Serialization ─────────────────────────────────────────────────

    def to_dict(self) -> dict:
        return {
            "overlay_id": self.overlay_id,
            "position": list(self.position),
            "activations": list(self.activations),
            "metadata": dict(self.metadata),
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Overlay":
        return cls(
            position=tuple(d.get("position", ())),
            activations=tuple(d.get("activations", ())),
            metadata=dict(d.get("metadata", {})),
            overlay_id=d.get("overlay_id", ""),
            created_at=float(d.get("created_at", 0.0)),
        )

    def __repr__(self) -> str:
        from math import sqrt
        norm = sqrt(sum(x * x for x in self.position))
        return (
            f"<Overlay id={self.overlay_id} dim={len(self.position)} "
            f"actives={self.num_active()} ||p||={norm:.3f}>"
        )
