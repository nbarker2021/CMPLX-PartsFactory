import os
import requests

DEFAULT_BASE = os.environ.get("MDHG_UNIFIED_URL", "http://mdhg-unified:8085")


class MDHGClient:
    """
    MDHG — Multi-Dimensional Hash Graph Sandbox.
    9-level hierarchy (grain→dust→triad→block→cluster→domain→region→planet→universe).
    Session-based node traversal with directional travel.
    
    Endpoints:
      POST  /session/{id}     — Create exploration session
      POST  /add_node         — Add node to session graph
      GET   /graph/{session}  — Get full graph
      POST  /traverse         — Traverse (up/down/siblings/all)
      GET   /depth/{session}  — Compute max depth
      DELETE /session/{id}    — Delete session
      POST  /tick             — Service heartbeat
    """

    def __init__(self, base_url: str | None = None):
        self.base_url = (base_url or DEFAULT_BASE).rstrip("/")

    def health(self) -> dict:
        resp = requests.get(f"{self.base_url}/health", timeout=5)
        resp.raise_for_status()
        return resp.json()

    def create_session(self, name: str | None = None, max_depth: int = 9) -> dict:
        payload = {"name": name, "max_depth": max_depth}
        resp = requests.post(f"{self.base_url}/session", json=payload, timeout=10)
        resp.raise_for_status()
        return resp.json()

    def add_node(self, session_id: str, content: str,
                 parent_hash: str | None = None, level: int = 0,
                 metadata: dict | None = None) -> dict:
        payload = {
            "session_id": session_id,
            "content": content,
            "parent_hash": parent_hash,
            "level": level,
            "metadata": metadata or {},
        }
        resp = requests.post(f"{self.base_url}/add_node", json=payload, timeout=10)
        resp.raise_for_status()
        return resp.json()

    def get_graph(self, session_id: str) -> dict:
        resp = requests.get(f"{self.base_url}/graph/{session_id}", timeout=10)
        resp.raise_for_status()
        return resp.json()

    def traverse(self, session_id: str, start_hash: str,
                 direction: str = "down", max_steps: int = 10) -> dict:
        payload = {
            "session_id": session_id,
            "start_hash": start_hash,
            "direction": direction,
            "max_steps": max_steps,
        }
        resp = requests.post(f"{self.base_url}/traverse", json=payload, timeout=10)
        resp.raise_for_status()
        return resp.json()

    def delete_session(self, session_id: str) -> dict:
        resp = requests.delete(f"{self.base_url}/session/{session_id}", timeout=5)
        resp.raise_for_status()
        return resp.json()

    def tick(self) -> dict:
        resp = requests.post(f"{self.base_url}/tick", json={}, timeout=5)
        resp.raise_for_status()
        return resp.json()
