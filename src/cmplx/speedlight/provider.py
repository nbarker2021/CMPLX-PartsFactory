"""
SpeedLightProvider — the `cache` port provider.

Bundles `SpeedLight` (idempotent compute) + `GlobalIndex` (E8
proximity) + `EquivalenceLearner` (cosine-similarity prototype merge)
+ optional `WorldlineCache` (MDHGMultiScale-backed time axis).

Register on the `cache` port:
    MorphonController.get().register("cache", SpeedLightProvider())
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Callable, Optional

from .cache import SpeedLight
from .equivalence import EquivalenceLearner
from .index import GlobalIndex
from .receipt import ComputationReceipt
from .worldline import WorldlineCache


class SpeedLightProvider:
    """Composite SpeedLight provider.

    Each computation flows through the cache; on miss, the result is
    admitted to the index (for proximity queries) and offered to the
    equivalence learner (for prototype merging).
    """

    name: str = "speedlight_provider"

    def __init__(
        self,
        speedlight: Optional[SpeedLight] = None,
        index: Optional[GlobalIndex] = None,
        equivalence: Optional[EquivalenceLearner] = None,
        worldline: Optional[WorldlineCache] = None,
    ) -> None:
        self.speedlight = speedlight or SpeedLight()
        self.index = index or GlobalIndex()
        self.equivalence = equivalence or EquivalenceLearner()
        self.worldline = worldline  # optional; set when MDHGMultiScale present

    # ── Idempotent compute (with auto-admit to index + equivalence) ──

    def compute(
        self,
        task_id: str,
        compute_fn: Optional[Callable] = None,
        e8_coords: Optional[list[float]] = None,
        labels: Optional[list[str]] = None,
        *args,
        **kwargs,
    ) -> tuple[Any, float, ComputationReceipt]:
        """Idempotent execute-or-cache. On miss, the receipt is also
        admitted to the geometric index (if `e8_coords` given) and the
        equivalence learner."""
        was_cached = task_id in self.speedlight.receipt_cache
        result, cost, receipt = self.speedlight.compute(
            task_id, compute_fn, *args, **kwargs
        )
        if not was_cached:  # genuine miss (cost may be 0.0 on fast fn)
            if e8_coords is not None:
                receipt.e8_coords = list(e8_coords)
                self.index.admit(
                    atom_id=task_id,
                    e8_coords=e8_coords,
                    labels=labels or [],
                    content_hash=receipt.result_hash,
                )
            self.equivalence.register(receipt)
            if _mint_receipt_on_miss_enabled():
                self._mint_unified_receipt_on_miss(task_id, receipt)
        return result, cost, receipt

    def _mint_unified_receipt_on_miss(
        self, task_id: str, comp: ComputationReceipt
    ) -> None:
        try:
            from cmplx.receipt.types import ReceiptType

            from cmplx.morphon import MorphonController

            prov = MorphonController.get().get_provider("receipt")
            if prov is not None:
                prov.mint(
                    receipt_type=ReceiptType.POST.value,
                    atom_id=task_id,
                    operation="speedlight_cache_miss",
                    payload={
                        "computation_receipt_id": comp.receipt_id,
                        "result_hash": comp.result_hash,
                    },
                )
                return
        except Exception:
            pass
        from cmplx.receipt.chain import ReceiptChain
        from cmplx.receipt.types import ReceiptType

        ReceiptChain().mint(
            receipt_type=ReceiptType.POST.value,
            atom_id=task_id,
            operation="speedlight_cache_miss",
            payload={
                "computation_receipt_id": comp.receipt_id,
                "result_hash": comp.result_hash,
            },
        )

    def mint_cache_snapshot(
        self,
        workspace: Path,
        run_id: str,
        step_id: str,
        *,
        task_id: str = "",
        inputs: Optional[dict] = None,
        outputs: Optional[dict] = None,
        mirror_computation: bool = True,
    ) -> dict:
        """Write run receipt via receipt spine; optionally mirror into cache store."""
        from cmplx.receipt.chain import ReceiptChain

        chain = ReceiptChain()
        run_receipt = chain.write_run_receipt(
            workspace=workspace,
            run_id=run_id,
            step_id=step_id,
            controller="speedlight",
            inputs=inputs or {"task_id": task_id},
            outputs=outputs or {},
            artifacts=[],
            extra={"snapshot": True},
        )
        if mirror_computation and task_id:
            cached = self.speedlight.receipt_cache.get(task_id)
            if cached is None:
                self.speedlight.compute(task_id, lambda: outputs or {})
        return run_receipt

    # ── Cache pass-throughs ───────────────────────────────────────────

    def get(self, key: str) -> Optional[Any]:
        return self.speedlight.get(key)

    def put(self, key: str, value: Any) -> None:
        self.speedlight.put(key, value)

    def get_aspect(self, address: str, aspect: str) -> Optional[Any]:
        return self.speedlight.get_aspect(address, aspect)

    def put_aspect(self, address: str, aspect: str, value: Any) -> None:
        self.speedlight.put_aspect(address, aspect, value)

    def compute_and_cache(self, address: str, aspect: str,
                          compute_fn: Callable, *args, **kwargs) -> Any:
        return self.speedlight.compute_and_cache(
            address, aspect, compute_fn, *args, **kwargs
        )

    # ── Proximity / equivalence ──────────────────────────────────────

    def query_proximity(self, e8_coords, k: int = 10,
                        label_filter: Optional[list[str]] = None) -> list:
        return self.index.query(e8_coords, k, label_filter)

    def find_equivalent_result(self, result) -> Optional[dict]:
        """Look up an existing prototype for `result`. Returns the
        prototype dict (or None)."""
        from .equivalence import _result_to_vector
        vec = _result_to_vector(result)
        if vec is None:
            return None
        proto = self.equivalence.find_equivalent(vec)
        return proto.to_dict() if proto else None

    # ── Worldline integration ────────────────────────────────────────

    def attach_worldline(self, multiscale) -> WorldlineCache:
        """Attach an MDHGMultiScale instance for time-axis caching.

        Returns the `WorldlineCache` so callers can `prewarm()` /
        `admit_keyframe()` directly.
        """
        self.worldline = WorldlineCache(self.speedlight, multiscale)
        return self.worldline

    # ── Reporting ─────────────────────────────────────────────────────

    @property
    def health(self) -> dict:
        return {
            "ok": True,
            "service": "speedlight_provider",
            "cache": self.speedlight.stats(),
            "index": self.index.stats(),
            "equivalence": self.equivalence.stats(),
            "worldline_attached": self.worldline is not None,
        }

    def stats(self) -> dict:
        return self.health

    def report(self) -> str:
        return self.speedlight.report()

    def __repr__(self) -> str:
        return (
            f"<SpeedLightProvider tasks={len(self.speedlight.receipt_cache)} "
            f"index={len(self.index)} "
            f"prototypes={self.equivalence.prototype_count()}>"
        )


def _mint_receipt_on_miss_enabled() -> bool:
    return os.environ.get("SPEEDLIGHT_MINT_RECEIPT", "1").strip().lower() in (
        "1",
        "true",
        "yes",
    )
