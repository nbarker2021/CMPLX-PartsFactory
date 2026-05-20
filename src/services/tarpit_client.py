import os
import requests

DEFAULT_BASE = os.environ.get("TARPIT_API_URL", "http://tarpit-api:8844")


class TarPitClient:
    """
    TarPit — Bond Chemistry / Atom Service.
    Creates atoms, checks bonds, navigates bond chains.
    
    Endpoints:
      POST /tarpit/create_atom
      POST /tarpit/bond
      POST /tarpit/bond_chain
      POST /tarpit/navigate
      GET  /tarpit/atoms
    """

    def __init__(self, base_url: str | None = None):
        self.base_url = (base_url or DEFAULT_BASE).rstrip("/")

    def health(self) -> dict:
        resp = requests.get(f"{self.base_url}/health", timeout=5)
        resp.raise_for_status()
        return resp.json()

    def create_atom(self, element: str, charge: float = 0.0,
                    metadata: dict | None = None) -> dict:
        payload = {"element": element, "charge": charge, "metadata": metadata or {}}
        resp = requests.post(f"{self.base_url}/tarpit/create_atom", json=payload, timeout=10)
        resp.raise_for_status()
        return resp.json()

    def bond(self, atom_a_id: str, atom_b_id: str, bond_type: str = "ionic") -> dict:
        payload = {"atom_a_id": atom_a_id, "atom_b_id": atom_b_id, "bond_type": bond_type}
        resp = requests.post(f"{self.base_url}/tarpit/bond", json=payload, timeout=10)
        resp.raise_for_status()
        return resp.json()

    def bond_chain(self, atom_ids: list[str], bond_type: str = "ionic") -> dict:
        payload = {"atom_ids": atom_ids, "bond_type": bond_type}
        resp = requests.post(f"{self.base_url}/tarpit/bond_chain", json=payload, timeout=15)
        resp.raise_for_status()
        return resp.json()

    def navigate(self, start_atom_id: str, max_depth: int = 3) -> dict:
        payload = {"start_atom_id": start_atom_id, "max_depth": max_depth}
        resp = requests.post(f"{self.base_url}/tarpit/navigate", json=payload, timeout=10)
        resp.raise_for_status()
        return resp.json()

    def atoms(self) -> dict:
        resp = requests.get(f"{self.base_url}/tarpit/atoms", timeout=5)
        resp.raise_for_status()
        return resp.json()
