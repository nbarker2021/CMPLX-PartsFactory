import time
import logging
import threading
from typing import Callable

logger = logging.getLogger("mesh.health")


class HealthMonitor:
    def __init__(self, check_interval: float = 15.0):
        self.check_interval = check_interval
        self._checkers: dict[str, Callable] = {}
        self._status: dict[str, bool] = {}
        self._latency: dict[str, float] = {}
        self._uptime: dict[str, float] = {}
        self._last_check: dict[str, float] = {}
        self._failures: dict[str, int] = {}
        self._lock = threading.Lock()
        self._running = False
        self._thread: threading.Thread | None = None

    def register(self, name: str, health_check: Callable):
        with self._lock:
            self._checkers[name] = health_check
            self._status[name] = False
            self._latency[name] = 0.0
            self._failures[name] = 0

    def unregister(self, name: str):
        with self._lock:
            for d in (self._checkers, self._status, self._latency,
                      self._uptime, self._last_check, self._failures):
                d.pop(name, None)

    def start(self):
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False

    def _loop(self):
        while self._running:
            self.check_all()
            time.sleep(self.check_interval)

    def check_all(self) -> dict[str, bool]:
        with self._lock:
            names = list(self._checkers.keys())

        for name in names:
            self._check_one(name)

        with self._lock:
            return dict(self._status)

    def _check_one(self, name: str):
        checker = self._checkers.get(name)
        if checker is None:
            return

        t0 = time.time()
        try:
            result = checker()
            elapsed = time.time() - t0
            is_healthy = bool(result) if not isinstance(result, bool) else result
        except Exception:
            elapsed = time.time() - t0
            is_healthy = False

        with self._lock:
            was_healthy = self._status.get(name, False)
            self._status[name] = is_healthy
            self._latency[name] = round(elapsed * 1000, 2)
            self._last_check[name] = time.time()

            if is_healthy and not was_healthy:
                self._failures[name] = 0

            if not is_healthy:
                self._failures[name] = self._failures.get(name, 0) + 1

            if is_healthy and name not in self._uptime:
                self._uptime[name] = time.time()

    def is_healthy(self, name: str) -> bool:
        return self._status.get(name, False)

    def metrics(self, name: str | None = None) -> dict:
        with self._lock:
            if name:
                return {
                    "healthy": self._status.get(name, False),
                    "latency_ms": self._latency.get(name, 0.0),
                    "consecutive_failures": self._failures.get(name, 0),
                    "last_check": self._last_check.get(name, 0),
                }

            services = {}
            for n in self._checkers:
                services[n] = {
                    "healthy": self._status.get(n, False),
                    "latency_ms": self._latency.get(n, 0.0),
                    "consecutive_failures": self._failures.get(n, 0),
                    "uptime": time.time() - self._uptime.get(n, time.time()) if self._status.get(n, False) else 0,
                }
            return {
                "services": services,
                "healthy_count": sum(1 for v in self._status.values() if v),
                "total_count": len(self._status),
                "check_interval": self.check_interval,
            }
