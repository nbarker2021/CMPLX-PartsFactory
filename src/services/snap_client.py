import os
import requests

DEFAULT_BASE = os.environ.get("SNAP_UNIFIED_URL", "http://snap-unified:8083")


class SNAPClient:
    """
    SNAP Engine — Gate369 + Lenses + Taxonomy + Stratifier.
    Precision labeling toolkit.
    
    SNAP doesn't label — it STRATIFIES. Every concept gets exploded into
    all presentations, meanings, connections, fictions, non-standard interpretations.
    Recursively until convergence.
    
    Endpoints:
      POST /gate369          — 3-6-9 selection (Triad → Hexad → Ennead)
      POST /triad            — Pick 3 best
      POST /stratify         — Recursive concept expansion
      POST /evaluate_lenses  — Polarity-aware evaluation
      GET  /taxonomy         — Family/type registry
      GET  /angles           — 8-angle questionnaire
      POST /candidate        — Register candidate
      POST /evidence         — Register evidence
      POST /dna_snapshot     — Full DNA snapshot
      POST /dtt_evaluate     — DTT evaluation
      POST /stitch           — Stitch records
      POST /snap_state       — Full state snapshot
    """

    def __init__(self, base_url: str | None = None):
        self.base_url = (base_url or DEFAULT_BASE).rstrip("/")

    def health(self) -> dict:
        resp = requests.get(f"{self.base_url}/health", timeout=5)
        resp.raise_for_status()
        return resp.json()

    def gate369(self, items: list[str], context: str = "") -> dict:
        resp = requests.post(f"{self.base_url}/gate369",
                             json={"items": items, "context": context}, timeout=10)
        resp.raise_for_status()
        return resp.json()

    def gate369_bodies(self, bodies: list[str], predicates: list[str]) -> dict:
        resp = requests.post(f"{self.base_url}/gate369",
                             json={"bodies": bodies, "predicates": predicates}, timeout=10)
        resp.raise_for_status()
        return resp.json()

    def triad(self, items: list[str], context: str = "") -> dict:
        resp = requests.post(f"{self.base_url}/triad",
                             json={"items": items, "context": context}, timeout=10)
        resp.raise_for_status()
        return resp.json()

    def stratify(self, concept: str, depth: int = 3) -> dict:
        resp = requests.post(f"{self.base_url}/stratify",
                             json={"concept": concept, "depth": depth}, timeout=30)
        resp.raise_for_status()
        return resp.json()

    def evaluate_lenses(self, body: dict) -> dict:
        resp = requests.post(f"{self.base_url}/evaluate_lenses",
                             json=body, timeout=10)
        resp.raise_for_status()
        return resp.json()

    def taxonomy(self) -> dict:
        resp = requests.get(f"{self.base_url}/taxonomy", timeout=5)
        resp.raise_for_status()
        return resp.json()

    def angles(self) -> dict:
        resp = requests.get(f"{self.base_url}/angles", timeout=5)
        resp.raise_for_status()
        return resp.json()

    def tick(self) -> dict:
        resp = requests.post(f"{self.base_url}/tick", json={}, timeout=5)
        resp.raise_for_status()
        return resp.json()
