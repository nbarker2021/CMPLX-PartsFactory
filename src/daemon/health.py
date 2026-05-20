"""ServiceHealthPinger — Pings all running Docker services on CRT schedule.

Integrates with:
  - HealthMonitor (mesh.health_monitor)
  - GeometricGovernance audit trail (governance.engine)
  - CRT buffers for outbound alert dispatch
"""

import json
import logging
import time
import urllib.request
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger("daemon.health")

ALL_SERVICE_ENDPOINTS = {
    "mmdb":       {"url": "http://host.docker.internal:8824/health",   "required": True},
    "mdhg":       {"url": "http://host.docker.internal:8825/health",   "required": True},
    "snap":       {"url": "http://host.docker.internal:8823/health",   "required": True},
    "tarpit":     {"url": "http://host.docker.internal:8844/health",   "required": True},
    "speedlight": {"url": "http://host.docker.internal:8843/health",   "required": True},
    "manny":      {"url": "http://host.docker.internal:8870/health",   "required": False},
    "research":   {"url": "http://host.docker.internal:3000/health",   "required": False},
    "pipeline":   {"url": "http://host.docker.internal:8000/health",   "required": False},
    "crystal":    {"url": "http://host.docker.internal:8001/health",   "required": False},
    "board":      {"url": "http://host.docker.internal:8002/health",   "required": False},
    "snapreplay": {"url": "http://host.docker.internal:9100/health",   "required": False},
    "cqe":        {"url": "http://host.docker.internal:9000/health",   "required": False},
    "governance": {"url": "http://host.docker.internal:8003/health",   "required": False},
    "knowledge":  {"url": "http://host.docker.internal:8004/health",   "required": False},
    "interface":  {"url": "http://host.docker.internal:8005/health",   "required": False},
    "mesh":       {"url": "http://host.docker.internal:8006/health",   "required": False},
    "expertise":  {"url": "http://host.docker.internal:8007/health",   "required": False},
    "runtime":    {"url": "http://host.docker.internal:8008/health",   "required": False},
}

HEALTH_PING_TIMEOUT = 5


class ServiceHealthPinger:
    """Pings all Docker services and reports health to dashboard + audit trail."""

    def __init__(self, governance=None, on_alert: Callable = None):
        self.governance = governance
        self._on_alert = on_alert
        self._health: Dict[str, Dict[str, Any]] = {}
        self._history: List[Dict[str, Any]] = []
        self._alert_count = 0

    def ping_all(self) -> Dict[str, Any]:
        """Ping every registered service. Returns full health report."""
        results = {}
        healthy_count = 0
        degraded_count = 0

        for name, info in ALL_SERVICE_ENDPOINTS.items():
            result = self._ping_one(name, info["url"])
            required = info["required"]
            is_healthy = result["healthy"]
            if required and not is_healthy:
                degraded_count += 1
            elif is_healthy:
                healthy_count += 1

            prev = self._health.get(name, {})
            if prev.get("healthy") and not is_healthy:
                self._alert_count += 1
                alert = {
                    "service": name,
                    "previous_status": "healthy",
                    "current_status": "unhealthy",
                    "timestamp": time.time(),
                    "alert_id": f"alert_{self._alert_count}",
                }
                if self._on_alert:
                    self._on_alert(alert)
                result["alert"] = alert

            results[name] = result
            self._health[name] = result

        report = {
            "timestamp": time.time(),
            "total": len(ALL_SERVICE_ENDPOINTS),
            "healthy": healthy_count,
            "degraded": degraded_count,
            "services": results,
            "all_healthy": degraded_count == 0,
        }

        self._history.append(report)
        if len(self._history) > 100:
            self._history = self._history[-100:]

        self._audit(report)
        return report

    def _ping_one(self, name: str, url: str) -> Dict[str, Any]:
        """Ping a single service endpoint."""
        t0 = time.time()
        try:
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=HEALTH_PING_TIMEOUT) as r:
                elapsed = time.time() - t0
                body = r.read().decode()
                data = json.loads(body) if body else {}
                return {
                    "healthy": True,
                    "latency_ms": round(elapsed * 1000, 2),
                    "status_code": r.status,
                    "response": data,
                    "last_check": time.time(),
                }
        except Exception as e:
            elapsed = time.time() - t0
            return {
                "healthy": False,
                "latency_ms": round(elapsed * 1000, 2),
                "status_code": None,
                "error": str(e)[:120],
                "last_check": time.time(),
            }

    def _audit(self, report: Dict[str, Any]):
        """Record health report to governance audit trail."""
        if not self.governance:
            return
        try:
            from governance.engine import BoundaryEvent
            event = BoundaryEvent(
                event_id=f"health_ping_{int(time.time())}",
                timestamp=time.time(),
                entropy_delta=0.0,
                receipt_data={
                    "healthy": report["healthy"],
                    "total": report["total"],
                    "degraded": report["degraded"],
                },
                boundary_type="health_ping",
            )
            self.governance.record_boundary_event(event)
        except Exception as e:
            logger.warning("health audit failed: %s", str(e)[:80])

    def get_health(self, name: str = None) -> Dict:
        if name:
            return self._health.get(name, {"healthy": False, "error": "unknown"})
        return dict(self._health)

    def get_history(self, limit: int = 10) -> List[Dict]:
        return self._history[-limit:]

    def summary(self) -> Dict:
        if not self._health:
            return {"status": "unknown", "healthy": 0, "total": 0}
        hc = sum(1 for v in self._health.values() if v.get("healthy"))
        return {
            "status": "healthy" if hc == len(self._health) else "degraded",
            "healthy": hc,
            "total": len(self._health),
            "alerts": self._alert_count,
        }
