"""
E8 — content-addressed projection into 8-dimensional E8 space.

This module implements the hash-based E8 embedding (the `snapdna.py`
pattern observed across all historical runtimes). It does not require
numpy; full lattice-point operations (nearest-root, Weyl chamber
navigation) live alongside in the package's reference material and
can be exposed later as needed.

See INTERFACE.md and BRIDGE.md at `cmplx.geometry` for the full
contract.
"""
from __future__ import annotations

import hashlib
import json
import math
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from cmplx.morphon import Morphon


# Standard parameters
DIMENSION = 8
HASH_HEX_LEN = 64
BYTES_USED = DIMENSION  # 8 bytes from sha256 produce the 8 coords


def _sha256_payload(payload) -> str:
    """sha256 of stable JSON serialization of `payload`."""
    s = json.dumps(payload, sort_keys=True, default=str)
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def e8_coordinates_from_payload(payload) -> tuple[float, ...]:
    """Deterministic 8-D unit-sphere projection of a payload.

    Steps (from the snapdna.py historical pattern):
      1. sha256(payload)
      2. take first 16 hex chars = 8 bytes
      3. map each byte [0,255] → [-1, 1] via (byte - 128) / 128
      4. normalize to L2 = 1
      5. round to 6 decimal places
    """
    h = _sha256_payload(payload)
    raw = [int(h[i * 2 : i * 2 + 2], 16) for i in range(BYTES_USED)]
    vec = [(b - 128) / 128.0 for b in raw]
    norm = math.sqrt(sum(x * x for x in vec)) or 1.0
    return tuple(round(x / norm, 6) for x in vec)


def e8_coordinates_for(morphon: "Morphon") -> tuple[float, ...]:
    """Public entry: 8-D coordinates for a morphon's payload."""
    return e8_coordinates_from_payload(morphon.payload)


# ---------------------------------------------------------------------------
# Optional: nearest-root snap. The pure-Python version below works on
# the unit-sphere coordinates and returns the closest E8 root vector
# (240 roots, of squared length 2). Useful for callers that want the
# lattice-quantized point rather than the surface projection.
# ---------------------------------------------------------------------------

def _e8_roots() -> list[tuple[float, ...]]:
    """Generate the 240 E8 root vectors.

    Type 1 (112 roots): permutations of (±1, ±1, 0, 0, 0, 0, 0, 0).
    Type 2 (128 roots): (±½)^8 with even number of minus signs.
    """
    roots: list[tuple[float, ...]] = []
    # Type 1
    for i in range(DIMENSION):
        for j in range(i + 1, DIMENSION):
            for si in (1.0, -1.0):
                for sj in (1.0, -1.0):
                    v = [0.0] * DIMENSION
                    v[i] = si
                    v[j] = sj
                    roots.append(tuple(v))
    # Type 2 — 256 sign combos, half (those with even # of negatives) kept
    for mask in range(256):
        signs = [-0.5 if (mask >> b) & 1 else 0.5 for b in range(DIMENSION)]
        if sum(1 for s in signs if s < 0) % 2 == 0:
            roots.append(tuple(signs))
    assert len(roots) == 240
    return roots


_ROOTS_CACHE: list[tuple[float, ...]] | None = None


def e8_roots() -> list[tuple[float, ...]]:
    """Return the cached list of 240 E8 root vectors."""
    global _ROOTS_CACHE
    if _ROOTS_CACHE is None:
        _ROOTS_CACHE = _e8_roots()
    return _ROOTS_CACHE


def nearest_root(vec: tuple[float, ...]) -> tuple[float, ...]:
    """Return the E8 root vector with minimum squared distance to `vec`."""
    if len(vec) != DIMENSION:
        raise ValueError(f"expected {DIMENSION}-D vector, got {len(vec)}-D")
    best = None
    best_d2 = float("inf")
    for r in e8_roots():
        d2 = sum((a - b) ** 2 for a, b in zip(vec, r))
        if d2 < best_d2:
            best_d2 = d2
            best = r
    return best  # type: ignore[return-value]


# ---------------------------------------------------------------------------
# Small public surface
# ---------------------------------------------------------------------------

class E8:
    """E8 helper. Stateless; mostly a namespace for the functions above.

    Useful for callers that want the lattice operations directly, beyond
    what the geometry port exposes.
    """

    DIMENSION = DIMENSION
    KISSING_NUMBER = 240

    @staticmethod
    def coordinates_for(morphon: "Morphon") -> tuple[float, ...]:
        return e8_coordinates_for(morphon)

    @staticmethod
    def coordinates_from_payload(payload) -> tuple[float, ...]:
        return e8_coordinates_from_payload(payload)

    @staticmethod
    def roots() -> list[tuple[float, ...]]:
        return e8_roots()

    @staticmethod
    def nearest_root(vec: tuple[float, ...]) -> tuple[float, ...]:
        return nearest_root(vec)
