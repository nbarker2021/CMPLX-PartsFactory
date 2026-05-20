"""Escrow stubs for Aletheia3 Leech wrapper (original Nick module not in tree)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

import numpy as np


@dataclass
class LeechVector:
    vector: np.ndarray
    norm_squared: float
    is_minimal: bool = False


class Aletheia3E8:
    def project(self, v: Any) -> dict[str, Any]:
        arr = np.asarray(v, dtype=float).ravel()
        return {"projected": arr[:8] if arr.size >= 8 else arr}


def from_e8_triple(a: Any, b: Any, c: Any) -> np.ndarray:
    return np.concatenate([np.asarray(a, dtype=float).ravel()[:8],
                           np.asarray(b, dtype=float).ravel()[:8],
                           np.asarray(c, dtype=float).ravel()[:8]])


def to_e8_triple(leech_vector: Any, e8_proj: Callable[[Any], Any]) -> tuple[Any, Any, Any]:
    v = np.asarray(leech_vector, dtype=float).ravel()
    n = max(1, len(v) // 3)
    return e8_proj(v[:n]), e8_proj(v[n : 2 * n]), e8_proj(v[2 * n : 3 * n])


def validate_leech_vector(vector: Any) -> dict[str, Any]:
    v = np.asarray(vector, dtype=float).ravel()
    return {"valid": v.size == 24, "dimension": int(v.size), "norm_squared": float(np.dot(v, v))}
