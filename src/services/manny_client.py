import os
import requests

DEFAULT_BASE = os.environ.get("MANNY_RUNTIME_URL", "http://manny-runtime:8870")


class MannyClient:
    """
    Manny Runtime — Brain Lattices.
    SELF/MEMORY/BODY/ATTENTION brains, expert domains, triads.
    """

    def __init__(self, base_url: str | None = None):
        self.base_url = (base_url or DEFAULT_BASE).rstrip("/")

    def health(self) -> dict:
        try:
            resp = requests.get(f"{self.base_url}/health", timeout=5)
            if resp.status_code == 200:
                return resp.json()
            return {"status": "ok"}
        except Exception:
            return {"status": "unknown"}

    def run(self, task: str, domain: str = "general",
            context: dict | None = None) -> dict:
        payload = {"task": task, "domain": domain, "context": context or {}}
        resp = requests.post(f"{self.base_url}/run", json=payload, timeout=30)
        resp.raise_for_status()
        return resp.json()

    def probe(self, query: str, domain: str = "general") -> dict:
        payload = {"query": query, "domain": domain}
        resp = requests.post(f"{self.base_url}/probe", json=payload, timeout=15)
        resp.raise_for_status()
        return resp.json()

    def verbalize(self, topic: str) -> dict:
        resp = requests.get(f"{self.base_url}/verbalize", params={"topic": topic}, timeout=15)
        resp.raise_for_status()
        return resp.json()

    def capacity(self) -> dict:
        resp = requests.get(f"{self.base_url}/capacity", timeout=5)
        resp.raise_for_status()
        return resp.json()

    def experts(self) -> dict:
        resp = requests.get(f"{self.base_url}/experts", timeout=5)
        resp.raise_for_status()
        return resp.json()
