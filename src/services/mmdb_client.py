import os
import requests

DEFAULT_BASE = os.environ.get("MMDB_UNIFIED_URL", "http://mmdb-unified:8084")


class MMDBClient:
    """
    MMDB — VOA-like crystal storage service.
    PostgreSQL-backed crystal store with E8-proximity search.
    
    Endpoints:
      POST /store         — Store a crystal
      GET  /crystal/{id}  — Retrieve by ID
      POST /search        — Proximity search by E8 coords / snap labels
      GET  /stats         — Store statistics
      POST /compact       — Compact / deduplicate
      GET  /moonshine_feature — Moonshine feature extraction
      GET  /j_function    — j-function computation
      POST /tick          — Service heartbeat
    """

    def __init__(self, base_url: str | None = None):
        self.base_url = (base_url or DEFAULT_BASE).rstrip("/")

    def health(self) -> dict:
        resp = requests.get(f"{self.base_url}/health", timeout=5)
        resp.raise_for_status()
        return resp.json()

    def store(self, content: str, snap_labels: list[str] | None = None,
              e8_coords: list[float] | None = None, mdhg_address: str = "",
              domain: str = "general", metadata: dict | None = None) -> dict:
        payload = {
            "content": content,
            "snap_labels": snap_labels or [],
            "e8_coords": e8_coords or [0.0] * 8,
            "mdhg_address": mdhg_address,
            "domain": domain,
            "metadata": metadata or {},
        }
        resp = requests.post(f"{self.base_url}/store", json=payload, timeout=10)
        resp.raise_for_status()
        return resp.json()

    def get_crystal(self, crystal_id: str) -> dict:
        resp = requests.get(f"{self.base_url}/crystal/{crystal_id}", timeout=5)
        if resp.status_code == 404:
            return {}
        resp.raise_for_status()
        return resp.json()

    def search(self, snap_labels: list[str] | None = None,
               e8_center: list[float] | None = None,
               radius: float = 1.0, limit: int = 50) -> list[dict]:
        payload = {
            "snap_labels": snap_labels or [],
            "e8_center": e8_center or [0.0] * 8,
            "radius": radius,
            "limit": limit,
        }
        resp = requests.post(f"{self.base_url}/search", json=payload, timeout=10)
        resp.raise_for_status()
        return resp.json()

    def stats(self) -> dict:
        resp = requests.get(f"{self.base_url}/stats", timeout=5)
        resp.raise_for_status()
        return resp.json()

    def tick(self, coupling: float = 0.030076) -> dict:
        resp = requests.post(f"{self.base_url}/tick", json={"coupling": coupling}, timeout=5)
        resp.raise_for_status()
        return resp.json()
