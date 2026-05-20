import os
import time
import json
import logging
from typing import Any, Callable

from .circuit_breaker import CircuitBreaker
from .health_monitor import HealthMonitor
from .service_discovery import ServiceDiscovery
from .router import IntentRouter, RoutingDecision
from .cache import MeshCache
from .dependency_graph import ServiceDependencyGraph
from .dashboard import HealthDashboard
from .error_handler import (
    MeshError, ServiceUnavailableError, RetryExhaustedError, TimeoutError,
    retry, fallback,
)
from services.registry import registry
from services.speedlight_client import SpeedLightClient
from governance.engine import GeometricGovernance, BoundaryEvent

logger = logging.getLogger("mesh")


class MeshOrchestrator:
    def __init__(self):
        self.registry = registry
        self.health = HealthMonitor(check_interval=15.0)
        self.discovery = ServiceDiscovery()
        self.router = IntentRouter()
        self.dep_graph = ServiceDependencyGraph()
        self.dashboard = HealthDashboard(
            health_monitor=self.health,
            service_registry=registry,
        )
        self.governance = GeometricGovernance()

        sl_url = os.environ.get("SPEEDLIGHT_API_URL", "http://host.docker.internal:8843")
        self._speedlight = SpeedLightClient(sl_url)
        self.cache = MeshCache(speedlight_client=self._speedlight)

        self._breakers: dict[str, CircuitBreaker] = {}
        self._started = False

    def start(self):
        if self._started:
            return
        self._register_services()
        self._build_dependency_graph()
        self.health.start()
        self._started = True
        logger.info("Mesh orchestrator started with %d services", len(self.registry.list_services()))

    def stop(self):
        self.health.stop()
        self._started = False

    def _register_services(self):
        for svc in self.registry.list_services():
            name = svc["name"]
            client = self.registry.get(name)
            if client is None:
                continue
            self.health.register(name, client.health)
            self._breakers[name] = CircuitBreaker(name=name)
            self.dep_graph.add_service(name, {"client_type": svc.get("client_type", "")})
            self.dashboard._breakers = self._breakers

    def _build_dependency_graph(self):
        self.dep_graph.add_dependency("manny", "mmdb")
        self.dep_graph.add_dependency("manny", "snap")
        self.dep_graph.add_dependency("snap", "mmdb")
        self.dep_graph.add_dependency("tarpit", "mmdb")
        self.dep_graph.add_dependency("speedlight", "mmdb")

    def request(self, service: str, endpoint: str, payload: dict | None = None,
                timeout: float = 30.0, use_cache: bool = False) -> dict:
        t0 = time.time()
        client = self.registry.get(service)
        if client is None:
            raise ServiceUnavailableError(service, endpoint)

        if use_cache:
            cache_key = f"{service}:{endpoint}:{json.dumps(payload or {}, sort_keys=True)}"
            cached = self.cache.get(cache_key)
            if cached is not None:
                self.dashboard.record_request(service, endpoint, (time.time() - t0) * 1000, True)
                return cached

        breaker = self._breakers.get(service)
        if breaker:
            try:
                result = breaker(client.health)
            except MeshError:
                self.dashboard.record_request(service, endpoint, (time.time() - t0) * 1000, False, 503)
                raise

        try:
            import requests as _req
            route = self._resolve_endpoint(client.base_url, endpoint, payload)
            method, url, body = route

            resp = _req.request(method, url, json=body, timeout=timeout)
            elapsed = (time.time() - t0) * 1000
            resp.raise_for_status()
            result = resp.json()

            if use_cache:
                self.cache.set(cache_key, result)

            self.dashboard.record_request(service, endpoint, elapsed, True)
            return result

        except _req.exceptions.Timeout:
            elapsed = (time.time() - t0) * 1000
            self.dashboard.record_request(service, endpoint, elapsed, False, 504)
            raise TimeoutError(service, endpoint, timeout=timeout)
        except Exception as e:
            elapsed = (time.time() - t0) * 1000
            self.dashboard.record_request(service, endpoint, elapsed, False)
            raise MeshError(str(e), service=service, endpoint=endpoint)

    async def request_async(self, service: str, endpoint: str, payload: dict | None = None,
                            timeout: float = 30.0) -> dict:
        import asyncio
        import aiohttp

        client = self.registry.get(service)
        if client is None:
            raise ServiceUnavailableError(service, endpoint)

        route = self._resolve_endpoint(client.base_url, endpoint, payload)
        method, url, body = route

        t0 = time.time()
        try:
            async with aiohttp.ClientSession() as session:
                async with session.request(method, url, json=body, timeout=aiohttp.ClientTimeout(total=timeout)) as resp:
                    result = await resp.json()
                    elapsed = (time.time() - t0) * 1000
                    self.dashboard.record_request(service, endpoint, elapsed, resp.ok)
                    if not resp.ok:
                        raise MeshError(f"HTTP {resp.status}", service=service, endpoint=endpoint)
                    return result
        except asyncio.TimeoutError:
            elapsed = (time.time() - t0) * 1000
            self.dashboard.record_request(service, endpoint, elapsed, False, 504)
            raise TimeoutError(service, endpoint, timeout=timeout)

    def request_by_intent(self, intent: str, payload: dict | None = None) -> dict:
        decision: RoutingDecision = self.router.route_or_fallback(intent)
        logger.info("Routing intent '%s' → %s.%s (confidence=%.2f)", intent, decision.service, decision.endpoint, decision.confidence)
        return self.request(decision.service, decision.endpoint, payload)

    def request_with_retry(self, service: str, endpoint: str, payload: dict | None = None,
                           max_attempts: int = 3) -> dict:
        last_error = None
        for attempt in range(max_attempts):
            try:
                return self.request(service, endpoint, payload)
            except (ServiceUnavailableError, TimeoutError) as e:
                last_error = e
                if attempt < max_attempts - 1:
                    delay = 0.5 * (2 ** attempt)
                    logger.info("Retry %d/%d for %s.%s after %.2fs", attempt + 1, max_attempts, service, endpoint, delay)
                    time.sleep(delay)
        raise RetryExhaustedError(service, endpoint, attempts=max_attempts, last_error=str(last_error))

    def request_with_fallback(self, service: str, endpoint: str, payload: dict | None = None,
                              fallback_service: str = "", fallback_endpoint: str = "") -> dict:
        try:
            return self.request(service, endpoint, payload)
        except MeshError:
            if fallback_service and fallback_endpoint:
                logger.warning("Falling back %s.%s → %s.%s", service, endpoint, fallback_service, fallback_endpoint)
                return self.request(fallback_service, fallback_endpoint, payload)
            raise

    def health_summary(self) -> dict:
        if not self._started:
            self.health.check_all()
        return self.dashboard.summary()

    def discover_services(self) -> dict[str, Any]:
        discovered = self.discovery.scan()
        for sid, info in discovered.items():
            self.dep_graph.add_service(sid, info)
        return discovered

    def audit(self, action: str, service: str, endpoint: str,
              payload: dict | None = None, result: dict | None = None):
        import hashlib
        event = BoundaryEvent(
            event_id=f"{action}_{int(time.time())}",
            timestamp=time.time(),
            entropy_delta=0.0,
            receipt_data={
                "action": action,
                "service": service,
                "endpoint": endpoint,
                "payload": payload,
                "result": result,
            },
            boundary_type="mesh_call",
        )
        self.governance.record_boundary_event(event)

    def get_audit_trail(self) -> list[dict]:
        return list(self.governance.audit_trail)

    def status(self) -> dict:
        return {
            "started": self._started,
            "services": {
                "total": len(self._breakers),
                "healthy": sum(1 for s in self.registry.list_services() if s.get("healthy")),
            },
            "circuit_breakers": {n: b.metrics() for n, b in self._breakers.items()},
            "health": self.health.metrics(),
            "cache": self.cache.stats(),
            "dependency_graph": self.dep_graph.to_dict(),
        }

    def _resolve_endpoint(self, base_url: str, endpoint: str,
                           payload: dict | None) -> tuple[str, str, dict | None]:
        method = "POST"
        url = f"{base_url.rstrip('/')}/{endpoint.lstrip('/')}"
        if endpoint in ("stats", "taxonomy", "atoms"):
            method = "GET"
            url = f"{base_url.rstrip('/')}/{endpoint.lstrip('/')}"
        return method, url, payload
