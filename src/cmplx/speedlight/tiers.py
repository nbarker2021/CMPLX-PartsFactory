"""
TwoTierCache — T1 (memory LRU) + T2 (durable backend).

Adapted from `speedlight_engine.py` TwoTierCache pattern. T1 misses
check T2 and promote to T1 on hit. T2 is a pluggable backend; the
default is an in-process dict, but adapter callables for MMDB / Redis
plug in via the constructor.
"""
from __future__ import annotations

from collections import OrderedDict
from typing import Any, Callable, Optional


class TwoTierCache:
    """Two-tier LRU cache. T1 = hot memory; T2 = durable.

    `t2_get(key) -> value | None` and `t2_put(key, value) -> None`
    are pluggable callables for the durable backend. The defaults
    keep everything in-process.
    """

    def __init__(
        self,
        max_t1_entries: int = 10_000,
        t2_get: Optional[Callable[[str], Any]] = None,
        t2_put: Optional[Callable[[str, Any], None]] = None,
    ) -> None:
        self.max_t1_entries = max_t1_entries
        self._t1: OrderedDict[str, Any] = OrderedDict()
        self._t2_store: dict[str, Any] = {}
        self._t2_get = t2_get or self._default_t2_get
        self._t2_put = t2_put or self._default_t2_put
        self._stats = {
            "t1_hits": 0, "t2_hits": 0, "misses": 0,
            "t1_promotions": 0, "evictions": 0,
        }

    def _default_t2_get(self, key: str) -> Any:
        return self._t2_store.get(key)

    def _default_t2_put(self, key: str, value: Any) -> None:
        self._t2_store[key] = value

    def get(self, key: str) -> Optional[Any]:
        if key in self._t1:
            self._t1.move_to_end(key)
            self._stats["t1_hits"] += 1
            return self._t1[key]
        # T1 miss → check T2
        value = self._t2_get(key)
        if value is not None:
            self._stats["t2_hits"] += 1
            self._stats["t1_promotions"] += 1
            self._promote(key, value)
            return value
        self._stats["misses"] += 1
        return None

    def put(self, key: str, value: Any) -> None:
        """Store in both tiers (write-through)."""
        self._promote(key, value)
        self._t2_put(key, value)

    def _promote(self, key: str, value: Any) -> None:
        if key in self._t1:
            self._t1.move_to_end(key)
            self._t1[key] = value
            return
        self._t1[key] = value
        while len(self._t1) > self.max_t1_entries:
            self._t1.popitem(last=False)
            self._stats["evictions"] += 1

    def __contains__(self, key: str) -> bool:
        return key in self._t1 or self._t2_get(key) is not None

    def __len__(self) -> int:
        return len(self._t1)

    def stats(self) -> dict:
        total = (
            self._stats["t1_hits"] + self._stats["t2_hits"] + self._stats["misses"]
        )
        hit_rate = 0.0
        if total > 0:
            hit_rate = (
                (self._stats["t1_hits"] + self._stats["t2_hits"]) / total * 100.0
            )
        return {
            **self._stats,
            "t1_entries": len(self._t1),
            "total_lookups": total,
            "hit_rate_percent": hit_rate,
        }

    def clear(self) -> None:
        self._t1.clear()
        self._t2_store.clear()
        for k in self._stats:
            self._stats[k] = 0

    def __repr__(self) -> str:
        return f"<TwoTierCache t1={len(self._t1)} max_t1={self.max_t1_entries}>"
