"""
SpeedLight + SpeedLightDistributed — the core idempotent cache.

`SpeedLight.compute(task_id, fn, *args, **kwargs)` is the canonical
idempotent operation: if the task_id is cached, return the receipt's
result with cost=0.0; otherwise run `fn(*args, **kwargs)`, record a
receipt, and return.

`SpeedLight.get_aspect(address, aspect)` / `put_aspect(...)` /
`compute_and_cache(...)` implement the MDHG-shaped key pattern: every
named aspect (gate_w4, kaprekar, ...) of an atom is stored at
`{address}:{aspect}`.

Adapted from `speedlight_sidecar.py` (base SpeedLight) and
`MMDBSpeedLight.py` (compute + receipt persistence).
"""
from __future__ import annotations

import threading
import time
from typing import Any, Callable, Optional

from .address import aspect_key
from .receipt import ComputationReceipt, ReceiptStore, _hash_obj


class SpeedLight:
    """Idempotent computation cache.

    Bundles a `ReceiptStore` (the audit ledger) with a hot
    `receipt_cache` (`task_id → ComputationReceipt`) and a generic
    `key_cache` for the MDHG-shaped aspect keys.
    """

    name: str = "speedlight"

    def __init__(self, max_cache_size: int = 10_000_000) -> None:
        self.max_cache_size = max_cache_size
        self.receipt_cache: dict[str, ComputationReceipt] = {}
        self.key_cache: dict[str, Any] = {}
        self.store = ReceiptStore()
        self._stats = {
            "hits": 0,
            "misses": 0,
            "key_hits": 0,
            "key_misses": 0,
            "bytes_stored": 0,
            "total_cost_avoided": 0.0,
        }
        self._created_at = time.time()

    # ── Idempotent compute ────────────────────────────────────────────

    def compute(
        self,
        task_id: str,
        compute_fn: Optional[Callable] = None,
        *args,
        **kwargs,
    ) -> tuple[Any, float, ComputationReceipt]:
        """Idempotent execute-or-cache.

        Returns `(result, cost_seconds, receipt)`. If `task_id` is
        cached, `cost_seconds == 0.0` and the cached receipt is
        returned; otherwise `compute_fn` is invoked.
        """
        if task_id in self.receipt_cache:
            receipt = self.receipt_cache[task_id]
            self._stats["hits"] += 1
            self._stats["total_cost_avoided"] += receipt.cost_seconds
            return receipt.result, 0.0, receipt

        if compute_fn is None:
            raise LookupError(
                f"task {task_id!r} not cached and no compute_fn provided"
            )

        self._stats["misses"] += 1
        start = time.time()
        result = compute_fn(*args, **kwargs)
        cost = time.time() - start

        receipt = ComputationReceipt(
            task_id=task_id,
            task_hash=_hash_obj({"task_id": task_id,
                                 "args": args, "kwargs": kwargs}),
            result=result,
            cost_seconds=cost,
            fn_name=getattr(compute_fn, "__name__", "<lambda>"),
        )
        self._store_receipt(receipt)
        return result, cost, receipt

    def _store_receipt(self, receipt: ComputationReceipt) -> None:
        self.receipt_cache[receipt.task_id] = receipt
        self.store.append(receipt)
        # Track approximate byte usage (purely informational).
        self._stats["bytes_stored"] += len(receipt.result_hash) + 64

    # ── Key-value cache ───────────────────────────────────────────────

    def get(self, key: str) -> Optional[Any]:
        if key in self.key_cache:
            self._stats["key_hits"] += 1
            return self.key_cache[key]
        self._stats["key_misses"] += 1
        return None

    def put(self, key: str, value: Any) -> None:
        self.key_cache[key] = value

    def has(self, key: str) -> bool:
        return key in self.key_cache

    # ── MDHG-aspect-keyed cache ──────────────────────────────────────

    def get_aspect(self, address: str, aspect: str) -> Optional[Any]:
        return self.get(aspect_key(address, aspect))

    def put_aspect(self, address: str, aspect: str, value: Any) -> None:
        self.put(aspect_key(address, aspect), value)

    def has_aspect(self, address: str, aspect: str) -> bool:
        return aspect_key(address, aspect) in self.key_cache

    def compute_and_cache(
        self,
        address: str,
        aspect: str,
        compute_fn: Callable,
        *args,
        **kwargs,
    ) -> Any:
        """The full idempotent pattern: check cache → compute if miss →
        store → return. f(f(x)) = f(x)."""
        key = aspect_key(address, aspect)
        if key in self.key_cache:
            self._stats["key_hits"] += 1
            return self.key_cache[key]
        self._stats["key_misses"] += 1
        value = compute_fn(*args, **kwargs)
        self.key_cache[key] = value
        return value

    # ── Sharing + maintenance ─────────────────────────────────────────

    def share_cache(self, other: "SpeedLight") -> int:
        """Merge `other`'s receipts into self. Returns count merged."""
        merged = 0
        for receipt in other.store.iter_receipts():
            if receipt.task_id not in self.receipt_cache:
                self._store_receipt(receipt)
                merged += 1
        for key, value in other.key_cache.items():
            if key not in self.key_cache:
                self.key_cache[key] = value
        return merged

    def clear(self) -> None:
        self.receipt_cache.clear()
        self.key_cache.clear()
        self.store.clear()
        for k in self._stats:
            self._stats[k] = 0 if not isinstance(self._stats[k], float) else 0.0

    # ── Reporting ─────────────────────────────────────────────────────

    def stats(self) -> dict:
        total = self._stats["hits"] + self._stats["misses"]
        hit_rate = (self._stats["hits"] / total * 100.0) if total else 0.0
        key_total = self._stats["key_hits"] + self._stats["key_misses"]
        key_hit_rate = (self._stats["key_hits"] / key_total * 100.0) if key_total else 0.0
        avg_compute_cost = 0.0
        if self._stats["misses"]:
            avg_compute_cost = (
                self._stats["total_cost_avoided"]
                / max(self._stats["hits"], 1)
            )
        # Efficiency multiplier: how many times faster relative to a
        # no-cache baseline at this hit rate.
        if hit_rate < 100.0:
            efficiency = 100.0 / (100.0 - hit_rate)
        else:
            efficiency = float("inf")
        return {
            "hits": self._stats["hits"],
            "misses": self._stats["misses"],
            "hit_rate_percent": hit_rate,
            "key_hits": self._stats["key_hits"],
            "key_misses": self._stats["key_misses"],
            "key_hit_rate_percent": key_hit_rate,
            "cached_tasks": len(self.receipt_cache),
            "cached_keys": len(self.key_cache),
            "bytes_stored": self._stats["bytes_stored"],
            "total_cost_avoided_seconds": self._stats["total_cost_avoided"],
            "avg_compute_cost_seconds": avg_compute_cost,
            "efficiency_multiplier": efficiency,
            "uptime_seconds": time.time() - self._created_at,
        }

    def report(self) -> str:
        s = self.stats()
        return (
            "┌─ SpeedLight Report ─────────────────────────\n"
            f"│  hits:           {s['hits']}\n"
            f"│  misses:         {s['misses']}\n"
            f"│  hit rate:       {s['hit_rate_percent']:.2f}%\n"
            f"│  cached tasks:   {s['cached_tasks']}\n"
            f"│  cached keys:    {s['cached_keys']}\n"
            f"│  time saved:     {s['total_cost_avoided_seconds']:.3f}s\n"
            f"│  efficiency:     {s['efficiency_multiplier']:.1f}x baseline\n"
            "└─────────────────────────────────────────────"
        )

    def __repr__(self) -> str:
        s = self.stats()
        return (
            f"<SpeedLight tasks={s['cached_tasks']} "
            f"keys={s['cached_keys']} "
            f"hit_rate={s['hit_rate_percent']:.1f}%>"
        )


class SpeedLightDistributed(SpeedLight):
    """`threading.RLock`-protected SpeedLight for multi-agent use.

    The same surface as `SpeedLight`, with every mutating operation
    serialized. Use this when multiple threads / agents share one
    cache instance.
    """

    name: str = "speedlight_distributed"

    def __init__(self, max_cache_size: int = 10_000_000) -> None:
        super().__init__(max_cache_size)
        self._lock = threading.RLock()

    def compute(self, task_id: str, compute_fn=None, *args, **kwargs):
        with self._lock:
            return super().compute(task_id, compute_fn, *args, **kwargs)

    def put(self, key: str, value) -> None:
        with self._lock:
            super().put(key, value)

    def put_aspect(self, address: str, aspect: str, value) -> None:
        with self._lock:
            super().put_aspect(address, aspect, value)

    def compute_and_cache(self, address: str, aspect: str, compute_fn, *args, **kwargs):
        with self._lock:
            return super().compute_and_cache(address, aspect, compute_fn, *args, **kwargs)

    def share_cache(self, other: SpeedLight) -> int:
        with self._lock:
            return super().share_cache(other)

    def clear(self) -> None:
        with self._lock:
            super().clear()
