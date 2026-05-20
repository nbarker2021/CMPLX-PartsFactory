"""Compatibility E8 lattice and encoder surface.

This module keeps the older ``cmplx.lattice`` import path alive while the live
geometry implementation continues to grow under ``cmplx.geometry``.
"""
from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass
from enum import Enum
from typing import Iterable, Sequence

import numpy as np

from cmplx.primitives.core import generate_e8_roots


class E8RootType(str, Enum):
    TYPE_A = "type_a"
    TYPE_D = "type_d"


@dataclass(frozen=True)
class E8Root:
    coords: tuple[float, ...]
    root_type: E8RootType
    index: int

    def __post_init__(self) -> None:
        if len(self.coords) != 8:
            raise ValueError("E8 roots must be 8-dimensional")
        object.__setattr__(self, "coords", tuple(float(c) for c in self.coords))

    def norm_squared(self) -> float:
        return float(sum(c * c for c in self.coords))

    def as_array(self) -> np.ndarray:
        return np.asarray(self.coords, dtype=np.float64)


def _root_type(coords: Sequence[float]) -> E8RootType:
    return E8RootType.TYPE_D if all(abs(abs(c) - 0.5) < 1e-12 for c in coords) else E8RootType.TYPE_A


class E8WeylGroup:
    """Small Weyl-group facade exposing the generated root system."""

    def __init__(self) -> None:
        self.root_system = [
            E8Root(tuple(float(x) for x in row), _root_type(row), i)
            for i, row in enumerate(generate_e8_roots())
        ]


class E8Lattice:
    """Minimal E8 lattice facade used by legacy encoder tests."""

    def __init__(self) -> None:
        self.weyl = E8WeylGroup()
        self.minimal_vectors = [root.as_array() for root in self.weyl.root_system]

    def nearest_root_index(self, vector: Sequence[float]) -> int:
        vec = _as_8d(vector)
        roots = np.vstack(self.minimal_vectors)
        return int(np.argmin(np.linalg.norm(roots - vec, axis=1)))


def _as_8d(values: Iterable[float]) -> np.ndarray:
    arr = np.asarray(list(values), dtype=np.float64).flatten()
    if arr.size < 8:
        arr = np.pad(arr, (0, 8 - arr.size))
    return np.nan_to_num(arr[:8], nan=0.0, posinf=1.0, neginf=-1.0).astype(np.float64)


def _hash_to_8d(data: bytes | str) -> np.ndarray:
    raw = data if isinstance(data, bytes) else str(data).encode("utf-8", errors="replace")
    digest = hashlib.sha256(raw).digest()
    vals = [(digest[i] / 255.0) * 2.0 - 1.0 for i in range(8)]
    return np.asarray(vals, dtype=np.float64)


def encode_phi_psi(phi: float, psi: float) -> np.ndarray:
    return _as_8d([phi, psi, math.sin(phi), math.cos(psi), phi * psi, phi - psi, phi + psi, 1.0])


def encode_hash(value: bytes | str) -> np.ndarray:
    return _hash_to_8d(value)


def encode_genome(sequence: str) -> np.ndarray:
    mapping = {"A": 1.0, "C": 0.5, "G": -0.5, "T": -1.0}
    return _as_8d(mapping.get(ch.upper(), 0.0) for ch in sequence[:8])


def encode_prime(prime: int) -> np.ndarray:
    return _as_8d([prime % p / p for p in (2, 3, 5, 7, 11, 13, 17, 19)])


def encode_gauss_code(crossing_count: int, code: Sequence[float]) -> np.ndarray:
    return _as_8d([crossing_count, *code])


def encode_species(
    population: float,
    mutation_rate: float,
    selection_pressure: float,
    generation: float,
    traits: Sequence[str],
    fitness: float,
) -> np.ndarray:
    return _as_8d(
        [population, mutation_rate, selection_pressure, generation, len(traits), fitness, *encode_hash("|".join(traits))[:2]]
    )


def encode_velocity(*values: float) -> np.ndarray:
    return _as_8d(values)


def encode_gap(*values: float) -> np.ndarray:
    return _as_8d(values)


def encode_chromophore_state(wavelength: float, angles: Sequence[float], excitation: float) -> np.ndarray:
    return _as_8d([wavelength / 1000.0, *angles, excitation])


def encode_user(user_id: int, *features: float) -> np.ndarray:
    seed = _hash_to_8d(str(user_id))
    return _as_8d(seed + _as_8d(features) * 0.1)


def encode_element(features: Sequence[float]) -> np.ndarray:
    return _as_8d(features)


def encode_system_state(state: Sequence[float], adjacency: Sequence[Sequence[float]], temperature: float) -> np.ndarray:
    flat_adj = [x for row in adjacency for x in row]
    return _as_8d([*state, *flat_adj, temperature])


def encode_gps_state(latitude: float, longitude: float, altitude: float, speed: float, heading: float) -> np.ndarray:
    return _as_8d([latitude / 90.0, longitude / 180.0, altitude, speed, heading])


def encode_drug(features: Sequence[float]) -> np.ndarray:
    return _as_8d(features)


def encode_target_window(window: Sequence[Sequence[float]]) -> np.ndarray:
    return _as_8d(x for row in window for x in row)


def encode_density_point(density: float, position: Sequence[float], velocity: Sequence[float], *rest: float) -> np.ndarray:
    return _as_8d([density, *position, *velocity, *rest])


def encode_cdr3(sequence: str) -> np.ndarray:
    return _hash_to_8d(sequence)


def encode_institution(*values: float) -> np.ndarray:
    return _as_8d(values)


class E8Encoder:
    """Lattice-aware placement helper over raw encoders."""

    def __init__(self) -> None:
        self.lattice = E8Lattice()

    def snap_to_root(self, vector: Sequence[float]) -> int:
        return self.lattice.nearest_root_index(vector)

    def encode_cooccurrence(self, terms: Sequence[str]) -> np.ndarray:
        return encode_hash("|".join(terms))

    def encode_fingerprint(self, fingerprint: Sequence[float]) -> int:
        return self.snap_to_root(fingerprint)

    def place_phi_psi(self, *args) -> int:
        return self.snap_to_root(encode_phi_psi(*args))

    def place_hash(self, *args) -> int:
        return self.snap_to_root(encode_hash(*args))

    def place_genome(self, *args) -> int:
        return self.snap_to_root(encode_genome(*args))

    def place_prime(self, *args) -> int:
        return self.snap_to_root(encode_prime(*args))

    def place_gauss_code(self, *args) -> int:
        return self.snap_to_root(encode_gauss_code(*args))

    def place_species(self, *args) -> int:
        return self.snap_to_root(encode_species(*args))

    def place_velocity(self, *args) -> int:
        return self.snap_to_root(encode_velocity(*args))

    def place_gap(self, *args) -> int:
        return self.snap_to_root(encode_gap(*args))

    def place_chromophore_state(self, *args) -> int:
        return self.snap_to_root(encode_chromophore_state(*args))

    def place_user(self, *args) -> int:
        return self.snap_to_root(encode_user(*args))

    def place_element(self, *args) -> int:
        return self.snap_to_root(encode_element(*args))

    def place_system_state(self, *args) -> int:
        return self.snap_to_root(encode_system_state(*args))

    def place_gps_state(self, *args) -> int:
        return self.snap_to_root(encode_gps_state(*args))

    def place_drug(self, *args) -> int:
        return self.snap_to_root(encode_drug(*args))

    def place_target_window(self, *args) -> int:
        return self.snap_to_root(encode_target_window(*args))

    def place_density_point(self, *args) -> int:
        return self.snap_to_root(encode_density_point(*args))

    def place_cdr3(self, *args) -> int:
        return self.snap_to_root(encode_cdr3(*args))

    def place_institution(self, *args) -> int:
        return self.snap_to_root(encode_institution(*args))


__all__ = [
    "E8Encoder",
    "E8Lattice",
    "E8Root",
    "E8RootType",
    "E8WeylGroup",
    "encode_cdr3",
    "encode_chromophore_state",
    "encode_density_point",
    "encode_drug",
    "encode_element",
    "encode_gauss_code",
    "encode_gap",
    "encode_genome",
    "encode_gps_state",
    "encode_hash",
    "encode_institution",
    "encode_phi_psi",
    "encode_prime",
    "encode_species",
    "encode_system_state",
    "encode_target_window",
    "encode_user",
    "encode_velocity",
]
