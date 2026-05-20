import os
import logging
from typing import Any

from .mmdb_client import MMDBClient
from .mdhg_client import MDHGClient
from .snap_client import SNAPClient
from .tarpit_client import TarPitClient
from .speedlight_client import SpeedLightClient
from .manny_client import MannyClient

logger = logging.getLogger("cmplx.services")


class ServiceRegistry:
    """Central registry of all running services with health checking."""

    def __init__(self):
        self._clients: dict[str, Any] = {}
        self._healthy: dict[str, bool] = {}
        self._probe()

    def _probe(self):
        entries = {
            "mmdb": (MMDBClient, os.environ.get("MMDB_UNIFIED_URL", "http://mmdb-unified:8084")),
            "mdhg": (MDHGClient, os.environ.get("MDHG_UNIFIED_URL", "http://mdhg-unified:8085")),
            "snap": (SNAPClient, os.environ.get("SNAP_UNIFIED_URL", "http://snap-unified:8083")),
            "tarpit": (TarPitClient, os.environ.get("TARPIT_API_URL", "http://tarpit-api:8844")),
            "speedlight": (SpeedLightClient, os.environ.get("SPEEDLIGHT_API_URL", "http://speedlight-api:8843")),
            "manny": (MannyClient, os.environ.get("MANNY_RUNTIME_URL", "http://manny-runtime:8870")),
        }
        for name, (cls, url) in entries.items():
            try:
                self._clients[name] = cls(url)
                self._healthy[name] = True
                logger.info("Service registered: %s at %s", name, (url or "(default)"))
            except Exception as e:
                logger.warning("Service registration failed: %s — %s", name, e)
                self._healthy[name] = False

    def check_health(self) -> dict[str, bool]:
        for name, client in self._clients.items():
            try:
                client.health()
                self._healthy[name] = True
            except Exception:
                self._healthy[name] = False
        return dict(self._healthy)

    @property
    def mmdb(self) -> MMDBClient:
        return self._clients.get("mmdb")

    @property
    def mdhg(self) -> MDHGClient:
        return self._clients.get("mdhg")

    @property
    def snap(self) -> SNAPClient:
        return self._clients.get("snap")

    @property
    def tarpit(self) -> TarPitClient:
        return self._clients.get("tarpit")

    @property
    def speedlight(self) -> SpeedLightClient:
        return self._clients.get("speedlight")

    @property
    def manny(self) -> MannyClient:
        return self._clients.get("manny")

    def list_services(self) -> list[dict]:
        result = []
        for name in sorted(self._clients):
            result.append({
                "name": name,
                "healthy": self._healthy.get(name, False),
                "client_type": type(self._clients[name]).__name__,
            })
        return result

    def get(self, name: str):
        return self._clients.get(name)


registry = ServiceRegistry()
