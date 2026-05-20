"""CRTOrchestrator — Master 24-channel CRT daemon for all CMPLX services.

Pre-configured channels fire on coprime periods for non-colliding ticks:
  - health_ping (2): ping all services
  - service_discover (3): discover new services
  - pipeline_process (5): process pipeline queue
  - brain_sync (7): sync brain states
  - wallet_check (11): verify wallets
  - identity_audit (13): audit agent identities
  - report_generate (17): generate reports
  - data_aggregate (19): aggregate data to PostgreSQL
  - expert_review (23): review expert performance
  - compose_round (29): run composition round
  - governance_check (31): verify governance invariants
  - knowledge_sync (37): sync knowledge bases

Channels 13-24 are available for dynamic registration by services.
"""

import json
import logging
import time
import threading
from typing import Any, Callable, Dict, List, Optional

from .local_crt import LocalCRT, _http_post

logger = logging.getLogger("daemon.orchestrator")

SERVICE_ENDPOINTS = {
    "mmdb":       "http://host.docker.internal:8824",
    "mdhg":       "http://host.docker.internal:8825",
    "snap":       "http://host.docker.internal:8823",
    "tarpit":     "http://host.docker.internal:8844",
    "speedlight": "http://host.docker.internal:8843",
    "manny":      "http://host.docker.internal:8870",
    "research":   "http://host.docker.internal:3000",
    "pipeline":   "http://host.docker.internal:8000",
    "crystal":    "http://host.docker.internal:8001",
    "board":      "http://host.docker.internal:8002",
    "snapreplay": "http://host.docker.internal:9100",
    "cqe":        "http://host.docker.internal:9000",
    "governance": "http://host.docker.internal:8003",
    "knowledge":  "http://host.docker.internal:8004",
    "interface":  "http://host.docker.internal:8005",
    "mesh":       "http://host.docker.internal:8006",
    "expertise":  "http://host.docker.internal:8007",
    "runtime":    "http://host.docker.internal:8008",
}

CHANNEL_0_11 = [
    ("health_ping",      2,  "ping all services"),
    ("service_discover", 3,  "discover new services"),
    ("pipeline_process", 5,  "process pipeline queue"),
    ("brain_sync",       7,  "sync brain states"),
    ("wallet_check",     11, "verify wallets"),
    ("identity_audit",   13, "audit agent identities"),
    ("report_generate",  17, "generate reports"),
    ("data_aggregate",   19, "aggregate data to PostgreSQL"),
    ("expert_review",    23, "review expert performance"),
    ("compose_round",    29, "run composition round"),
    ("governance_check", 31, "verify governance invariants"),
    ("knowledge_sync",   37, "sync knowledge bases"),
]


class CRTOrchestrator:
    """Master 24-channel CRT daemon. Coordinates all service ticks."""

    def __init__(self, tick_interval: float = 10.0,
                 daemon_url: str = "http://host.docker.internal:8080"):
        self.crt = LocalCRT(
            service_name="crt-orchestrator",
            tick_interval=tick_interval,
            daemon_url=daemon_url,
        )
        self._service_health: Dict[str, bool] = {}
        self._service_latency: Dict[str, float] = {}
        self._lock = threading.Lock()
        self._init_channels()
        self._init_buffers()

    def _init_channels(self):
        for name, period, desc in CHANNEL_0_11:
            handler = getattr(self, f"_on_{name}", None)
            if handler:
                self.crt.register(name, period, handler, description=desc)
        self.crt.register(
            "tick_sync", 1,
            self._on_tick_sync,
            description="sync tick counter to daemon API",
        )

    def _init_buffers(self):
        self.crt.register_buffer("outbound_posts", self._flush_outbound, flush_period=3)
        self.crt.register_buffer("pipeline_submissions", self._flush_pipeline, flush_period=5)
        self.crt.register_buffer("governance_events", self._flush_governance, flush_period=7)
        self.crt.register_buffer("data_aggregation", self._flush_data, flush_period=19)

    # ── Pre-configured channel handlers ───────────────────────

    def _on_health_ping(self):
        results = {}
        for name, url in SERVICE_ENDPOINTS.items():
            t0 = time.time()
            try:
                resp = _http_post(f"{url}/health", {})
                ok = resp and "error" not in resp
                results[name] = {"healthy": ok, "latency_ms": round((time.time() - t0) * 1000, 2)}
            except Exception:
                results[name] = {"healthy": False, "latency_ms": None}
        with self._lock:
            for name, r in results.items():
                self._service_health[name] = r["healthy"]
                self._service_latency[name] = r["latency_ms"]

    def _on_service_discover(self):
        _http_post(f"{SERVICE_ENDPOINTS.get('mesh')}/discover", {})

    def _on_pipeline_process(self):
        items = self.crt.buffers.get("pipeline_submissions", [])
        if items:
            _http_post(f"{SERVICE_ENDPOINTS.get('pipeline')}/tick", {"queued": len(items)})
        if SERVICE_ENDPOINTS.get("expertise"):
            _http_post(f"{SERVICE_ENDPOINTS.get('expertise')}/tick", {})

    def _on_brain_sync(self):
        if SERVICE_ENDPOINTS.get("manny"):
            _http_post(f"{SERVICE_ENDPOINTS['manny']}/sync", {"source": "crt-daemon"})

    def _on_wallet_check(self):
        _http_post(f"{SERVICE_ENDPOINTS.get('mmdb')}/tick", {})

    def _on_identity_audit(self):
        _http_post(f"{SERVICE_ENDPOINTS.get('governance')}/audit", {})

    def _on_report_generate(self):
        _http_post(f"{SERVICE_ENDPOINTS.get('interface')}/report", {"source": "crt-daemon"})

    def _on_data_aggregate(self):
        items = self.crt.buffers.get("data_aggregation", [])
        if items:
            _http_post(f"{SERVICE_ENDPOINTS.get('mdhg')}/aggregate", {"count": len(items)})

    def _on_expert_review(self):
        if SERVICE_ENDPOINTS.get("expertise"):
            _http_post(f"{SERVICE_ENDPOINTS['expertise']}/review", {})

    def _on_compose_round(self):
        if SERVICE_ENDPOINTS.get("crystal"):
            _http_post(f"{SERVICE_ENDPOINTS['crystal']}/compose", {"round": self.crt.tick_count})

    def _on_governance_check(self):
        _http_post(f"{SERVICE_ENDPOINTS.get('governance')}/validate", {"tick": self.crt.tick_count})

    def _on_knowledge_sync(self):
        if SERVICE_ENDPOINTS.get("snap"):
            _http_post(f"{SERVICE_ENDPOINTS['snap']}/sync", {})

    def _on_tick_sync(self):
        pass

    # ── Buffer flush handlers ─────────────────────────────────

    def _flush_outbound(self, items: List[Any]):
        for item in items:
            url = item.pop("_url", None)
            if url:
                _http_post(url, item)

    def _flush_pipeline(self, items: List[Any]):
        if items and SERVICE_ENDPOINTS.get("pipeline"):
            _http_post(f"{SERVICE_ENDPOINTS['pipeline']}/process",
                       {"batch": items, "tick": self.crt.tick_count})

    def _flush_governance(self, items: List[Any]):
        if items and SERVICE_ENDPOINTS.get("governance"):
            for item in items:
                _http_post(f"{SERVICE_ENDPOINTS['governance']}/record", item)

    def _flush_data(self, items: List[Any]):
        if items and SERVICE_ENDPOINTS.get("mmdb"):
            for item in items:
                _http_post(f"{SERVICE_ENDPOINTS['mmdb']}/store", item)

    # ── Public API ────────────────────────────────────────────

    @property
    def tick_count(self) -> int:
        return self.crt.tick_count

    def register(self, channel_name: str, period: int, handler: Callable,
                 description: str = ""):
        self.crt.register(channel_name, period, handler, description)

    def register_buffer(self, buffer_name: str, flush_handler: Callable,
                        flush_period: int = 3):
        self.crt.register_buffer(buffer_name, flush_handler, flush_period)

    def buffer(self, buffer_name: str, item: Any):
        self.crt.buffer(buffer_name, item)

    def tick(self) -> Dict:
        return self.crt.tick()

    def start_background(self):
        self.crt.start_background()

    def stop(self):
        self.crt.stop()

    def status(self) -> Dict:
        s = self.crt.status()
        with self._lock:
            s["services"] = {
                name: {
                    "healthy": h,
                    "latency_ms": self._service_latency.get(name),
                }
                for name, h in self._service_health.items()
            }
        return s

    def service_health(self, name: str = None) -> Dict:
        with self._lock:
            if name:
                return {
                    "service": name,
                    "healthy": self._service_health.get(name, False),
                    "latency_ms": self._service_latency.get(name),
                }
            return dict(self._service_health)
