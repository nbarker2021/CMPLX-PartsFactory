"""
MDHGMultiScale — 3-layer (fast / med / slow) admission with drift tracking.

Compressed from `composed_mdhg_v3.py` (8720 lines, 69 methods). The
historical surface had:
  - MDHGHashTable (Hamiltonian-path navigation, φ sizing)
  - MDHGCache (24D → 16-bin quantization → 2D slot, drift signatures)
  - MDHGMultiScale (3 independent layer caches)
  - MDHGController (E8-aware grids, knn/range/cluster)

The runnable form here keeps the structural ideas the rest of the
build depends on:
  - 24-D quantization (one cell per coordinate, configurable bins)
  - 3 admission layers with independent occupancy
  - drift detection (signature change between successive admits at a slot)
  - propose_topK based on access counts

It does NOT yet replicate the Hamiltonian-path table, jump_hash
placement, or the 4310-line MDHGAddress chain. Those land as follow-up
work when the engine needs them.
"""
from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass, field
from typing import Any, Optional


LAYERS: tuple[str, ...] = ("fast", "med", "slow")
DEFAULT_BINS: int = 16
QUANT_DIMS: int = 24


def quantize_24(vec: list[float], bins: int = DEFAULT_BINS) -> tuple[int, ...]:
    """Map a 24-D vector to a 24-tuple of integer bin indices.

    Vectors shorter than 24 dims are zero-padded; longer ones truncated.
    Each component is normalized assuming roughly [-1, 1] range; bins
    are clamped to [0, bins-1].
    """
    v = list(vec[:QUANT_DIMS]) + [0.0] * max(0, QUANT_DIMS - len(vec))
    out = []
    for x in v:
        # Map roughly-[-1,1] → [0, bins)
        idx = int((x + 1.0) * 0.5 * bins)
        if idx < 0:
            idx = 0
        elif idx >= bins:
            idx = bins - 1
        out.append(idx)
    return tuple(out)


def slot_id_from_q24(q24: tuple[int, ...]) -> str:
    """Hash a 24-tuple into a 16-hex-char slot id."""
    payload = ",".join(str(i) for i in q24)
    return hashlib.sha256(payload.encode()).hexdigest()[:16]


@dataclass
class SlotRecord:
    """One slot's bookkeeping in a layer cache."""
    slot_id: str
    q24: tuple[int, ...]
    signature: str = ""       # hash of last-admitted vector
    meta: dict = field(default_factory=dict)
    access_count: int = 0
    last_seen: float = 0.0
    drift_events: int = 0     # bumped on every signature change


@dataclass
class LayerCache:
    """One temporal-resolution layer (fast / med / slow).

    Holds a dict of slot_id → SlotRecord. Admission updates the slot
    record and detects drift (signature change vs. last admit).
    """
    name: str
    bins: int = DEFAULT_BINS
    slots: dict[str, SlotRecord] = field(default_factory=dict)

    def admit(self, vec: list[float], meta: Optional[dict] = None) -> dict:
        q24 = quantize_24(vec, self.bins)
        slot_id = slot_id_from_q24(q24)
        sig = hashlib.sha256(
            ",".join(f"{x:.6f}" for x in vec[:QUANT_DIMS]).encode()
        ).hexdigest()[:16]

        rec = self.slots.get(slot_id)
        drift = False
        if rec is None:
            rec = SlotRecord(slot_id=slot_id, q24=q24, signature=sig,
                             meta=dict(meta or {}))
            self.slots[slot_id] = rec
        else:
            if rec.signature != sig:
                drift = True
                rec.drift_events += 1
                rec.signature = sig
            if meta:
                rec.meta.update(meta)
        rec.access_count += 1
        rec.last_seen = time.time()

        return {
            "layer": self.name,
            "slot": slot_id,
            "q24": q24,
            "drift": drift,
            "access_count": rec.access_count,
        }

    def occupancy(self) -> int:
        return len(self.slots)

    def top_k(self, k: int = 5) -> list[SlotRecord]:
        """Return slots sorted by access_count descending."""
        return sorted(self.slots.values(),
                      key=lambda r: -r.access_count)[:k]


class MDHGMultiScale:
    """3-layer admission with independent caches per layer.

    Use cases:
      - `fast` for per-tick / per-frame state (high churn)
      - `med` for keyframe / checkpoint state (drift surfaces)
      - `slow` for archive / canonical state (long-tail occupancy)

    The same vector can be admitted to multiple layers simultaneously
    via `admit_all_layers`. This is what SpeedLight wants: the same
    worldline tick lives in every layer at once and ages out of fast
    first.
    """

    name: str = "mdhg_multiscale"

    def __init__(self, bins: int = DEFAULT_BINS) -> None:
        self._layers: dict[str, LayerCache] = {
            n: LayerCache(name=n, bins=bins) for n in LAYERS
        }

    def admit(self, vec: list[float], meta: Optional[dict] = None,
              layer: str = "fast") -> dict:
        if layer not in self._layers:
            raise ValueError(
                f"unknown layer {layer!r}; expected one of {LAYERS}"
            )
        return self._layers[layer].admit(vec, meta)

    def admit_all_layers(
        self,
        vec: list[float],
        meta: Optional[dict] = None,
    ) -> dict[str, dict]:
        return {n: self._layers[n].admit(vec, meta) for n in LAYERS}

    def layer(self, name: str) -> LayerCache:
        if name not in self._layers:
            raise ValueError(
                f"unknown layer {name!r}; expected one of {LAYERS}"
            )
        return self._layers[name]

    def occupancy_snapshot(self) -> dict[str, int]:
        return {n: lc.occupancy() for n, lc in self._layers.items()}

    def propose_topK(self, k: int = 5, layer: str = "slow") -> list[SlotRecord]:
        return self.layer(layer).top_k(k)

    def __repr__(self) -> str:
        return f"<MDHGMultiScale {self.occupancy_snapshot()}>"
