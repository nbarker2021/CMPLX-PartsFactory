"""
GlobalIndex — in-process E8 geometric proximity index.

Adapted from `tmn1_speedlight_service.py:GlobalIndex` (198–251).
Same semantics, pure-stdlib (no numpy; L2 distance computed in pure
Python with tuples).

Use case: given an `e8_coords` query, find the top-k atoms whose
recorded E8 coordinates are closest (with optional label-filter mask).
This is what the proximity / nearest-neighbor APIs in the historical
service used; the TMN1 form keyed by `atom_id` with a Redis backing.
"""
from __future__ import annotations

import math
import time
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class IndexEntry:
    atom_id: str
    e8_coords: tuple[float, ...]
    labels: list[str] = field(default_factory=list)
    content_hash: str = ""
    timestamp: float = field(default_factory=time.time)


class GlobalIndex:
    """E8 geometric index over admitted atoms.

    `admit(atom_id, e8_coords, labels, content_hash)` records an
    entry; `query(e8_coords, k, label_filter)` returns the top-k
    closest entries by L2 distance, optionally filtered to entries
    whose labels include all `label_filter` items.
    """

    name: str = "global_index"

    def __init__(self, max_entries: int = 1_000_000) -> None:
        self.max_entries = max_entries
        self._entries: dict[str, IndexEntry] = {}
        self._stats = {
            "total_admits": 0,
            "total_queries": 0,
            "total_evictions": 0,
        }

    def admit(
        self,
        atom_id: str,
        e8_coords,
        labels: Optional[list[str]] = None,
        content_hash: str = "",
    ) -> IndexEntry:
        coords = tuple(float(c) for c in e8_coords)
        entry = IndexEntry(
            atom_id=atom_id,
            e8_coords=coords,
            labels=list(labels or []),
            content_hash=content_hash,
        )
        self._entries[atom_id] = entry
        self._stats["total_admits"] += 1
        while len(self._entries) > self.max_entries:
            # Evict the oldest by insertion order (Python dict preserves order)
            oldest = next(iter(self._entries))
            self._entries.pop(oldest)
            self._stats["total_evictions"] += 1
        return entry

    def query(
        self,
        e8_coords,
        k: int = 10,
        label_filter: Optional[list[str]] = None,
    ) -> list[tuple[str, float, list[str]]]:
        """Return `(atom_id, distance, labels)` for the top-k nearest
        admitted entries. Optional `label_filter` keeps only entries
        whose `labels` is a superset of the filter list."""
        self._stats["total_queries"] += 1
        q = tuple(float(c) for c in e8_coords)
        results: list[tuple[str, float, list[str]]] = []
        filter_set = set(label_filter or [])
        for entry in self._entries.values():
            if filter_set and not filter_set.issubset(entry.labels):
                continue
            dist = _l2(q, entry.e8_coords)
            results.append((entry.atom_id, dist, entry.labels))
        results.sort(key=lambda r: r[1])
        return results[:k]

    def has(self, atom_id: str) -> bool:
        return atom_id in self._entries

    def get(self, atom_id: str) -> Optional[IndexEntry]:
        return self._entries.get(atom_id)

    def stats(self) -> dict:
        return {
            **self._stats,
            "entries": len(self._entries),
            "max_entries": self.max_entries,
        }

    def clear(self) -> None:
        self._entries.clear()
        for k in self._stats:
            self._stats[k] = 0

    def __len__(self) -> int:
        return len(self._entries)

    def __repr__(self) -> str:
        return f"<GlobalIndex entries={len(self._entries)}>"


def _l2(a: tuple[float, ...], b: tuple[float, ...]) -> float:
    """L2 distance. Pads the shorter tuple with zeros."""
    n = max(len(a), len(b))
    a_padded = a + (0.0,) * (n - len(a))
    b_padded = b + (0.0,) * (n - len(b))
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(a_padded, b_padded)))
