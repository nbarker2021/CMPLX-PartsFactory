"""
WorldlineCache — time-axis caching on top of MDHGMultiScale.

Bridges a `SpeedLight` instance with `cmplx.addressing.mdhg.MDHGMultiScale`
so that the same task at successive time-ticks lands in the right
temporal tier:

  - `fast` — per-tick / per-frame state
  - `med`  — keyframes (where drift surfaces)
  - `slow` — archive / canonical

User framing: "SpeedLight, tuned for this tool, could produce any
kind of worldline needed as cache, and additionally JIT and Ahead of
Time loading."

JIT pattern: cache on first compute.
AOT pattern: pre-populate via `prewarm(specs)` before consumers ask.
"""
from __future__ import annotations

from typing import Any, Callable, Optional

from .cache import SpeedLight


class WorldlineCache:
    """Pairs a `SpeedLight` with an `MDHGMultiScale` for worldline-aware
    caching.

    The multiscale arg is duck-typed: anything with
    `admit_all_layers(vec24)` and `admit(vec24, meta, layer)`.
    """

    name: str = "worldline_cache"

    def __init__(self, speedlight: SpeedLight, multiscale) -> None:
        self.speedlight = speedlight
        self.multiscale = multiscale
        self._tick: int = 0

    # ── Time-axis admission ───────────────────────────────────────────

    def admit(
        self,
        task_id: str,
        result_vec24,
        layer: str = "fast",
        meta: Optional[dict] = None,
    ) -> dict:
        """Admit a worldline tick. The result vector lands in the
        named layer of the multiscale cache; SpeedLight retains the
        result by task_id."""
        meta = dict(meta or {})
        meta.setdefault("tick", self._tick)
        self._tick += 1
        return self.multiscale.admit(result_vec24, meta=meta, layer=layer)

    def admit_keyframe(
        self,
        task_id: str,
        result_vec24,
        meta: Optional[dict] = None,
    ) -> dict[str, dict]:
        """Promote this tick into every layer (fast+med+slow) — what
        you do at a keyframe so the canonical state survives eviction
        from `fast`."""
        meta = dict(meta or {})
        meta.setdefault("tick", self._tick)
        meta.setdefault("keyframe", True)
        self._tick += 1
        return self.multiscale.admit_all_layers(result_vec24, meta=meta)

    # ── JIT / AOT ─────────────────────────────────────────────────────

    def jit_compute(
        self,
        task_id: str,
        compute_fn: Callable,
        *args,
        **kwargs,
    ) -> Any:
        """Just-in-time: cache on first call via SpeedLight."""
        result, _, _ = self.speedlight.compute(task_id, compute_fn, *args, **kwargs)
        return result

    def prewarm(
        self,
        specs: list[tuple[str, Callable, tuple, dict]],
    ) -> dict:
        """Ahead-of-time: pre-populate by running every `(task_id, fn,
        args, kwargs)` spec. Returns a small summary dict."""
        before = self.speedlight.stats()["misses"]
        for task_id, fn, args, kwargs in specs:
            self.speedlight.compute(task_id, fn, *args, **kwargs)
        after = self.speedlight.stats()["misses"]
        return {
            "prewarmed_tasks": len(specs),
            "new_misses": after - before,
        }

    # ── Reporting ─────────────────────────────────────────────────────

    @property
    def tick(self) -> int:
        return self._tick

    def stats(self) -> dict:
        out = {"tick": self._tick}
        if hasattr(self.multiscale, "occupancy_snapshot"):
            out["multiscale_occupancy"] = self.multiscale.occupancy_snapshot()
        out["speedlight"] = self.speedlight.stats()
        return out

    def __repr__(self) -> str:
        return f"<WorldlineCache tick={self._tick}>"
