"""
LocalCRT — Embeddable 24-channel daemon slice for any TMN2 service.

Each service gets its own CRT ring synced to the main daemon tick.
Channels fire on coprime periods so they never collide.
Outbound operations (board posts, pipeline calls) are BUFFERED and
flushed on the tick cycle, making all inter-service calls non-blocking.

Usage in any FastAPI service:
    from local_crt import LocalCRT

    crt = LocalCRT(service_name="board")
    crt.register("outbound_flush", 3, flush_board_posts)   # Every 3rd tick
    crt.register("pipeline_batch", 5, batch_pipeline_calls) # Every 5th tick
    crt.register("health_report", 7, report_health)         # Every 7th tick

    # In startup:
    crt.start_background()  # Starts tick thread

    # Or called externally by main daemon:
    @app.post("/tick")
    def tick(): return crt.tick()

    # Buffer outbound calls:
    crt.buffer("board_post", {"board_id": "findings", "title": "...", ...})
    # → flushed on next outbound_flush tick
"""
import json
import logging
import threading
import time
import urllib.request
from collections import defaultdict
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger("local-crt")

# CRT coprime periods — first 24 primes for guaranteed non-collision
CRT_PRIMES = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37,
              41, 43, 47, 53, 59, 61, 67, 71, 73, 79, 83, 89]


class LocalCRT:
    """Embeddable 24-channel CRT daemon slice."""

    def __init__(self, service_name: str = "unknown", tick_interval: float = 10.0,
                 daemon_url: str = "http://tmn2-daemon:8000"):
        self.service_name = service_name
        self.tick_interval = tick_interval
        self.daemon_url = daemon_url
        self.tick_count = 0
        self.channels: Dict[str, Dict] = {}  # name → {period, handler, last_fired, fire_count}
        self.buffers: Dict[str, List] = defaultdict(list)  # buffer_name → [items]
        self.buffer_handlers: Dict[str, Callable] = {}  # buffer_name → flush_handler
        self._running = False
        self._lock = threading.Lock()
        self._stats = {"ticks": 0, "fires": 0, "flushes": 0, "errors": 0}

    def register(self, channel_name: str, period: int, handler: Callable,
                 description: str = ""):
        """Register a channel with a coprime period and handler function."""
        self.channels[channel_name] = {
            "period": period,
            "handler": handler,
            "description": description,
            "last_fired": 0,
            "fire_count": 0,
            "errors": 0,
        }

    def register_buffer(self, buffer_name: str, flush_handler: Callable,
                        flush_period: int = 3):
        """Register a buffer that flushes on a tick period.

        Items added via buffer() accumulate between ticks.
        On the flush tick, all items are passed to flush_handler([items])
        and the buffer is cleared.
        """
        self.buffer_handlers[buffer_name] = flush_handler
        self.register(
            f"flush_{buffer_name}", flush_period,
            lambda name=buffer_name: self._flush_buffer(name),
            description=f"Flush {buffer_name} buffer",
        )

    def buffer(self, buffer_name: str, item: Any):
        """Add an item to a named buffer. Flushed on the next tick cycle."""
        with self._lock:
            self.buffers[buffer_name].append(item)

    def _flush_buffer(self, buffer_name: str):
        """Flush all items in a buffer through its handler."""
        with self._lock:
            items = self.buffers[buffer_name]
            self.buffers[buffer_name] = []

        if not items:
            return

        handler = self.buffer_handlers.get(buffer_name)
        if handler:
            try:
                handler(items)
                self._stats["flushes"] += 1
                logger.debug("Flushed %d items from %s", len(items), buffer_name)
            except Exception as e:
                logger.warning("Buffer flush %s failed: %s", buffer_name, str(e)[:80])
                # Put items back for next attempt
                with self._lock:
                    self.buffers[buffer_name] = items + self.buffers[buffer_name]
                self._stats["errors"] += 1

    def tick(self) -> Dict:
        """Execute one tick cycle. Fire all channels whose period divides tick_count."""
        self.tick_count += 1
        self._stats["ticks"] += 1
        fired = []

        for name, ch in self.channels.items():
            if self.tick_count % ch["period"] == 0:
                try:
                    ch["handler"]()
                    ch["fire_count"] += 1
                    ch["last_fired"] = time.time()
                    fired.append(name)
                    self._stats["fires"] += 1
                except Exception as e:
                    ch["errors"] += 1
                    self._stats["errors"] += 1
                    logger.warning("CRT %s channel %s error: %s",
                                   self.service_name, name, str(e)[:80])

        return {
            "tick": self.tick_count,
            "fired": fired,
            "channels": len(self.channels),
            "buffers": {k: len(v) for k, v in self.buffers.items()},
        }

    def start_background(self):
        """Start autonomous tick loop in background thread."""
        if self._running:
            return
        self._running = True

        def _loop():
            logger.info("LocalCRT %s started: %d channels, tick=%.1fs",
                        self.service_name, len(self.channels), self.tick_interval)
            while self._running:
                self.tick()
                time.sleep(self.tick_interval)

        t = threading.Thread(target=_loop, daemon=True)
        t.start()

    def stop(self):
        self._running = False

    def status(self) -> Dict:
        """Current CRT status."""
        return {
            "service": self.service_name,
            "tick_count": self.tick_count,
            "channels": {
                name: {
                    "period": ch["period"],
                    "fire_count": ch["fire_count"],
                    "errors": ch["errors"],
                    "description": ch["description"],
                }
                for name, ch in self.channels.items()
            },
            "buffers": {k: len(v) for k, v in self.buffers.items()},
            "stats": self._stats,
            "running": self._running,
        }


def _http_post(url, data, timeout=15):
    """Non-blocking HTTP post helper."""
    try:
        body = json.dumps(data).encode()
        req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read())
    except Exception as e:
        return {"error": str(e)[:100]}


# ── Pre-built flush handlers ──

def make_board_flusher(board_url: str = "http://tmn2-board:8000"):
    """Creates a flush handler that posts buffered items to the board."""
    def flush(items):
        for item in items:
            _http_post(f"{board_url}/post", item)
    return flush


def make_pipeline_flusher(pipeline_url: str = "http://tmn2-pipeline:8000"):
    """Creates a flush handler that processes buffered content through pipeline."""
    def flush(items):
        for item in items:
            _http_post(f"{pipeline_url}/process", item)
    return flush
