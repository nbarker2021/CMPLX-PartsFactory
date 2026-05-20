"""Shared hash→E8 embed primitives (e8 + leech families)."""
from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass
from typing import List


@dataclass
class EmbedResult:
    coordinates: List[float]
    lattice_id: str
    seed_hash: str


def sha256_hex(data: str | bytes) -> str:
    if isinstance(data, str):
        data = data.encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def e8_from_seed(seed: str) -> List[float]:
    digest = sha256_hex(seed)
    coords: list[float] = []
    for i in range(8):
        chunk = digest[i * 8 : (i + 1) * 8]
        value = int(chunk, 16) / 0xFFFFFFFF
        coords.append((value * 2.0) - 1.0)
    norm_sq = sum(c * c for c in coords)
    if norm_sq > 0:
        scale = math.sqrt(2.0 / norm_sq)
        coords = [c * scale for c in coords]
    return coords


def embed_atom(seed: str, lattice_id: str = "E8") -> EmbedResult:
    coords = e8_from_seed(seed)
    return EmbedResult(coordinates=coords, lattice_id=lattice_id, seed_hash=sha256_hex(seed))
