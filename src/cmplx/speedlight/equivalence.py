"""
EquivalenceLearner — merges receipts whose result vectors are cosine-
similar above a threshold.

The "learn_equivalence" endpoint from the TMN2 engine. When two
distinct task_ids produce result vectors with cosine similarity ≥
threshold, they are recognized as the same equivalence class — and
future computations producing similar results can reuse the prototype.

This is the dedup-at-the-semantic-level half of SpeedLight: even when
two callers ask for slightly different things, if their results turn
out to match a prototype, both share the cache.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Iterable, Optional

from .receipt import ComputationReceipt


@dataclass
class Prototype:
    """One learned equivalence class."""
    prototype_id: str
    centroid: tuple[float, ...]
    receipt_ids: list[str] = field(default_factory=list)
    representative_result: object = None

    def to_dict(self) -> dict:
        return {
            "prototype_id": self.prototype_id,
            "centroid": list(self.centroid),
            "receipt_count": len(self.receipt_ids),
        }


def _result_to_vector(result) -> Optional[tuple[float, ...]]:
    """Best-effort coercion of a receipt result to a feature vector.

    - list / tuple of numbers → tuple of floats
    - dict with `e8_coords` or `vector` → that field
    - everything else → None (skip in similarity)
    """
    if result is None:
        return None
    if isinstance(result, (list, tuple)):
        try:
            return tuple(float(x) for x in result)
        except (TypeError, ValueError):
            return None
    if isinstance(result, dict):
        for key in ("e8_coords", "vector", "embedding"):
            if key in result:
                try:
                    return tuple(float(x) for x in result[key])
                except (TypeError, ValueError):
                    return None
    return None


def cosine_similarity(a: tuple[float, ...], b: tuple[float, ...]) -> float:
    """Cosine similarity ∈ [-1, 1]. Padded with zeros on length mismatch."""
    n = max(len(a), len(b))
    a_p = a + (0.0,) * (n - len(a))
    b_p = b + (0.0,) * (n - len(b))
    dot = sum(x * y for x, y in zip(a_p, b_p))
    norm_a = math.sqrt(sum(x * x for x in a_p))
    norm_b = math.sqrt(sum(x * x for x in b_p))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


class EquivalenceLearner:
    """Cosine-similarity prototype merger.

    Threshold defaults to 0.95 (the TMN2-engine canonical). Tune
    higher for stricter equivalence; lower for broader clustering.
    """

    name: str = "equivalence_learner"

    def __init__(self, threshold: float = 0.95) -> None:
        if not -1.0 <= threshold <= 1.0:
            raise ValueError(f"threshold must be in [-1, 1], got {threshold}")
        self.threshold = threshold
        self._prototypes: list[Prototype] = []
        self._next_id = 0
        self._stats = {"registered": 0, "merged": 0, "new_prototypes": 0}

    def register(self, receipt: ComputationReceipt) -> Optional[Prototype]:
        """Admit a receipt. Returns the prototype it was merged into,
        or a new prototype if no match. Returns None if the receipt's
        result can't be vectorized."""
        vec = _result_to_vector(receipt.result)
        if vec is None:
            return None
        self._stats["registered"] += 1
        existing = self.find_equivalent(vec)
        if existing is not None:
            existing.receipt_ids.append(receipt.receipt_id)
            self._stats["merged"] += 1
            return existing
        proto = Prototype(
            prototype_id=f"proto-{self._next_id:06d}",
            centroid=vec,
            representative_result=receipt.result,
            receipt_ids=[receipt.receipt_id],
        )
        self._next_id += 1
        self._prototypes.append(proto)
        self._stats["new_prototypes"] += 1
        return proto

    def find_equivalent(self, vec: tuple[float, ...]) -> Optional[Prototype]:
        """Return the first prototype whose centroid is within the
        cosine-similarity threshold; None if no match."""
        for proto in self._prototypes:
            sim = cosine_similarity(vec, proto.centroid)
            if sim >= self.threshold:
                return proto
        return None

    def prototypes(self) -> list[dict]:
        return [p.to_dict() for p in self._prototypes]

    def prototype_count(self) -> int:
        return len(self._prototypes)

    def stats(self) -> dict:
        return {
            **self._stats,
            "prototype_count": len(self._prototypes),
            "threshold": self.threshold,
        }

    def clear(self) -> None:
        self._prototypes.clear()
        self._next_id = 0
        for k in self._stats:
            self._stats[k] = 0

    def __repr__(self) -> str:
        return (
            f"<EquivalenceLearner threshold={self.threshold} "
            f"prototypes={len(self._prototypes)}>"
        )
