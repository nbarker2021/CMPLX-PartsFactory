"""
ChainRunner — builds the 7-station chain, wires cohort neighbors, manages the
shared 12-thread budget (7 stations + 5 helper slots), runs tasks, aggregates
stats.

The user's budget: 12 threads total; 7 reserved for stations, 5 available for
dynamically-spawned helper subcontainers (here: helper threads; containers
can come later if a helper becomes hot).
"""
from __future__ import annotations

import logging
import threading
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, List, Optional

from ._escrow_stubs import (
    Item,
    Station,
    TaskConfig,
    get_brain,
    get_brain_spec,
    task_config_for,
)

logger = logging.getLogger("chain.runner")


STATION_ORDER = ["TRIAGE", "EXTRACT", "VALIDATE", "SCORE", "RATE", "COMPARE", "EMIT", "REPORT"]

# Budget grew to 13 threads to accommodate the new REPORT station
# (8 stations + 5 helper slots).
MAX_TOTAL_THREADS = 13
STATION_THREAD_COUNT = 8
HELPER_THREAD_BUDGET = MAX_TOTAL_THREADS - STATION_THREAD_COUNT   # 5


class ChainRunner:
    """Owns the 7 stations + helper pool, runs tasks end-to-end."""

    def __init__(self, station_classes: Dict[str, type]):
        """station_classes maps station-name -> concrete Station subclass."""
        missing = set(STATION_ORDER) - set(station_classes.keys())
        if missing:
            raise ValueError(f"missing station classes for: {missing}")
        self.stations: List[Station] = []
        for sname in STATION_ORDER:
            spec = get_brain_spec(sname)
            brain = get_brain(spec)
            cls = station_classes[sname]
            self.stations.append(cls(sname, brain))
        # Wire cohort (each station gets its left+right neighbor)
        for i, st in enumerate(self.stations):
            left = self.stations[i - 1] if i > 0 else None
            right = self.stations[i + 1] if i + 1 < len(self.stations) else None
            st.wire(left, right)

        # Shared helper pool for spawned subtasks
        self.helper_pool = ThreadPoolExecutor(
            max_workers=HELPER_THREAD_BUDGET,
            thread_name_prefix="chain-helper",
        )
        self._current_config: Optional[TaskConfig] = None

    # ── Lifecycle ────────────────────────────────────────────────

    def start(self, cfg: TaskConfig) -> None:
        self._current_config = cfg
        logger.info(
            f"ChainRunner starting — task={cfg.task_name} ({cfg.task_id}) "
            f"stations={[s.name for s in self.stations]} "
            f"threads: stations={STATION_THREAD_COUNT} helpers={HELPER_THREAD_BUDGET}"
        )
        for st in self.stations:
            st.start(cfg)

    def stop(self) -> None:
        for st in self.stations:
            st.stop()
        self.helper_pool.shutdown(wait=False)
        logger.info("ChainRunner stopped")

    # ── Item submission ─────────────────────────────────────────

    def submit(self, item: Item) -> None:
        """Push an item into the head station's queue."""
        item.current_station = STATION_ORDER[0]
        if self._current_config is not None:
            item.task_id = self._current_config.task_id
            item.task_config = {
                "task_name": self._current_config.task_name,
            }
        self.stations[0].input_queue.put(item)

    def submit_batch(self, items: List[Item]) -> int:
        for it in items:
            self.submit(it)
        return len(items)

    # ── Helper pool API (used by stations via their autonomy) ────

    def request_helper(self, subtask: Dict[str, Any]) -> Any:
        """A station calls this to offload a subtask to the helper pool.
        Returns a Future. Stations must not block on this; helpers are advisory."""
        logger.debug(f"helper requested: kind={subtask.get('kind')} source_station={subtask.get('source_station')}")
        def _run():
            # Subtask handlers are station-specific; each station defines them
            # and passes a callable in subtask['callable']. The runner just
            # provides the thread.
            fn = subtask.get("callable")
            if fn is None:
                return {"error": "no callable in subtask"}
            try:
                return fn()
            except Exception as e:
                return {"error": f"{type(e).__name__}: {e}"}
        return self.helper_pool.submit(_run)

    # ── Stats ────────────────────────────────────────────────────

    def stats(self) -> Dict[str, Any]:
        return {
            "task": self._current_config.task_name if self._current_config else None,
            "station_stats": [s.stats() for s in self.stations],
            "thread_budget": {
                "total": MAX_TOTAL_THREADS,
                "stations": STATION_THREAD_COUNT,
                "helpers": HELPER_THREAD_BUDGET,
            },
        }

    # ── Convenience ─────────────────────────────────────────────

    def wait_until_drained(self, timeout: float = 300.0) -> bool:
        """Block until every station's queue is empty. Returns False on timeout."""
        import time as _time
        start = _time.time()
        while _time.time() - start < timeout:
            if all(s.input_queue.empty() for s in self.stations):
                # Check no station is mid-processing by confirming sizes stay 0
                _time.sleep(0.5)
                if all(s.input_queue.empty() for s in self.stations):
                    return True
            _time.sleep(1.0)
        return False
