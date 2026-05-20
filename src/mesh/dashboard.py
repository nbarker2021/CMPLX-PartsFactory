import time
from typing import Any


class HealthDashboard:
    def __init__(self, health_monitor=None, circuit_breakers: dict[str, Any] | None = None,
                 service_registry=None):
        self._health = health_monitor
        self._breakers = circuit_breakers or {}
        self._registry = service_registry
        self._request_log: list[dict] = []
        self._max_log = 1000

    def record_request(self, service: str, endpoint: str, duration_ms: float,
                       success: bool, status_code: int = 200):
        self._request_log.append({
            "service": service,
            "endpoint": endpoint,
            "duration_ms": round(duration_ms, 2),
            "success": success,
            "status_code": status_code,
            "timestamp": time.time(),
        })
        if len(self._request_log) > self._max_log:
            self._request_log = self._request_log[-self._max_log:]

    def summary(self) -> dict[str, Any]:
        services: dict[str, dict] = {}
        total_requests = len(self._request_log)

        if self._health:
            health_metrics = self._health.metrics()
            for name, info in health_metrics.get("services", {}).items():
                services[name] = {
                    "healthy": info.get("healthy", False),
                    "latency_ms": info.get("latency_ms", 0),
                    "consecutive_failures": info.get("consecutive_failures", 0),
                    "uptime_seconds": info.get("uptime", 0),
                }
                cb = self._breakers.get(name)
                if cb:
                    services[name]["circuit_breaker"] = cb.metrics()

        recent = self._request_log[-100:] if total_requests > 100 else self._request_log

        success_count = sum(1 for r in recent if r["success"])
        error_count = sum(1 for r in recent if not r["success"])
        avg_latency = sum(r["duration_ms"] for r in recent) / max(len(recent), 1)

        by_service: dict[str, dict] = {}
        for r in recent:
            svc = r["service"]
            by_service.setdefault(svc, {"count": 0, "errors": 0, "total_latency": 0})
            by_service[svc]["count"] += 1
            by_service[svc]["total_latency"] += r["duration_ms"]
            if not r["success"]:
                by_service[svc]["errors"] += 1

        service_stats = {}
        for svc, s in by_service.items():
            service_stats[svc] = {
                "request_count": s["count"],
                "error_count": s["errors"],
                "avg_latency_ms": round(s["total_latency"] / max(s["count"], 1), 2),
                "error_rate": round(s["errors"] / max(s["count"], 1) * 100, 1),
            }

        healthy_count = sum(1 for s in services.values() if s.get("healthy"))
        total_count = len(services)

        return {
            "timestamp": time.time(),
            "overview": {
                "total_services": total_count,
                "healthy_services": healthy_count,
                "unhealthy_services": total_count - healthy_count,
                "health_score": round(healthy_count / max(total_count, 1) * 100, 1),
            },
            "performance": {
                "total_requests_logged": total_requests,
                "recent_requests": len(recent),
                "recent_success": success_count,
                "recent_errors": error_count,
                "recent_error_rate": round(error_count / max(len(recent), 1) * 100, 1),
                "average_latency_ms": round(avg_latency, 2),
            },
            "services": services,
            "service_stats": service_stats,
        }

    def recent_requests(self, limit: int = 50) -> list[dict]:
        return self._request_log[-limit:]
