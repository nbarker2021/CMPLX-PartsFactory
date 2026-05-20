import os
import requests

DEFAULT_BASE = os.environ.get("SPEEDLIGHT_API_URL", "http://speedlight-api:8843")


class SpeedLightClient:
    """
    SpeedLight — Receipt Cache / Merkle Ledger.
    SHA-256 content-addressed storage with LRU caching and JSONL receipt trails.
    """

    def __init__(self, base_url: str | None = None):
        self.base_url = (base_url or DEFAULT_BASE).rstrip("/")

    def health(self) -> dict:
        resp = requests.get(f"{self.base_url}/health", timeout=5)
        if resp.status_code == 200:
            return {"status": "ok"}
        return {"status": "unknown"}

    def get(self, key: str) -> dict | None:
        resp = requests.get(f"{self.base_url}/v1/cache/{key}", timeout=5)
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        return resp.json()

    def put(self, key: str, value: dict | str,
            ttl_seconds: int = 3600) -> dict:
        payload = {"key": key, "value": value, "ttl": ttl_seconds}
        resp = requests.post(f"{self.base_url}/v1/cache", json=payload, timeout=10)
        resp.raise_for_status()
        return resp.json()

    def receipt(self, receipt_id: str) -> dict | None:
        resp = requests.get(f"{self.base_url}/v1/receipts/{receipt_id}", timeout=5)
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        return resp.json()
