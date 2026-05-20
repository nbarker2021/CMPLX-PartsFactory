#!/usr/bin/env python3
"""
E8 Lattice - Complete Implementation

The E8 lattice is the unique even unimodular lattice in 8 dimensions.
It has remarkable properties:
- Densest sphere packing in 8D
- 240 minimal vectors (roots)
- Related to exceptional Lie group E8
- Weyl group of order 696,729,600

This implementation provides:
- Vector operations in 8D
- Root system (240 roots)
- Weyl group operations
- Projection to/from Leech lattice
- MDHG addressing
"""

import hashlib
import json
import math
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
from itertools import permutations, product


# E8 Lattice constants
E8_DIM = 8
E8_MIN_NORM = 2  # Minimal norm (squared) of roots
E8_ROOT_COUNT = 240  # Number of roots


@dataclass
class E8Vector:
    """Vector in E8 lattice."""
    coords: Tuple[float, ...] = field(default_factory=lambda: tuple([0.0] * E8_DIM))
    norm_squared: float = 0.0
    
    def __post_init__(self):
        if len(self.coords) != E8_DIM:
            raise ValueError(f"E8 vector must have {E8_DIM} dimensions")
        if self.norm_squared == 0.0:
            self.norm_squared = sum(c * c for c in self.coords)
    
    def __add__(self, other: 'E8Vector') -> 'E8Vector':
        return E8Vector(tuple(a + b for a, b in zip(self.coords, other.coords)))
    
    def __sub__(self, other: 'E8Vector') -> 'E8Vector':
        return E8Vector(tuple(a - b for a, b in zip(self.coords, other.coords)))
    
    def __neg__(self) -> 'E8Vector':
        return E8Vector(tuple(-c for c in self.coords))
    
    def __mul__(self, scalar: float) -> 'E8Vector':
        return E8Vector(tuple(c * scalar for c in self.coords))
    
    def dot(self, other: 'E8Vector') -> float:
        return sum(a * b for a, b in zip(self.coords, other.coords))
    
    def norm(self) -> float:
        return math.sqrt(self.norm_squared)
    
    def fingerprint(self) -> str:
        return hashlib.sha256(json.dumps([round(c, 6) for c in self.coords]).encode()).hexdigest()[:24]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'coords': [round(c, 6) for c in self.coords],
            'norm_squared': round(self.norm_squared, 6),
            'norm': round(self.norm(), 6),
            'fingerprint': self.fingerprint(),
        }
    
    @classmethod
    def from_coords(cls, coords: List[float]) -> 'E8Vector':
        return cls(tuple(coords))
    
    @classmethod
    def zero(cls) -> 'E8Vector':
        return cls()
    
    @classmethod
    def basis(cls, index: int) -> 'E8Vector':
        coords = [0.0] * E8_DIM
        coords[index % E8_DIM] = 1.0
        return cls(tuple(coords))


class E8RootSystem:
    """
    E8 Root System - 240 roots in 8D.
    
    The 240 roots are of two types:
    1. (±1, ±1, 0, 0, 0, 0, 0, 0) - 112 roots (permutations)
    2. (±½, ±½, ±½, ±½, ±½, ±½, ±½, ±½) with even number of minus signs - 128 roots
    """
    
    def __init__(self):
        self._roots = None
    
    def generate_roots(self) -> List[E8Vector]:
        """Generate all 240 roots."""
        if self._roots is not None:
            return self._roots
        
        roots = []
        
        # Type 1: (±1, ±1, 0^6) - 112 roots
        for i in range(E8_DIM):
            for j in range(i + 1, E8_DIM):
                for s1 in [1, -1]:
                    for s2 in [1, -1]:
                        coords = [0.0] * E8_DIM
                        coords[i] = float(s1)
                        coords[j] = float(s2)
                        roots.append(E8Vector(tuple(coords)))
        
        # Type 2: (±½^8) with even number of minus signs - 128 roots
        for signs in product([0.5, -0.5], repeat=8):
            if sum(1 for s in signs if s < 0) % 2 == 0:
                roots.append(E8Vector(signs))
        
        self._roots = roots
        return roots
    
    def get_roots(self, count: int = 240) -> List[E8Vector]:
        """Get roots (up to 240)."""
        return self.generate_roots()[:count]
    
    def is_root(self, v: E8Vector) -> bool:
        """Check if vector is a root."""
        norm_sq = round(v.norm_squared, 6)
        return abs(norm_sq - E8_MIN_NORM) < 0.001
    
    def weyl_group_order(self) -> int:
        """Return order of Weyl group (696,729,600)."""
        return 696729600
    
    def coxeter_number(self) -> int:
        """Return Coxeter number (30)."""
        return 30
    
    def dual_coxeter_number(self) -> int:
        """Return dual Coxeter number (30)."""
        return 30


class E8Lattice:
    """
    Complete E8 Lattice Implementation.
    
    Provides:
    - Vector operations
    - Root system (240 roots)
    - Weyl reflections
    - Projection to Leech
    - MDHG addressing
    """
    
    def __init__(self):
        self.root_system = E8RootSystem()
        self._cache = {}
    
    def zero(self) -> E8Vector:
        """Return zero vector."""
        return E8Vector.zero()
    
    def basis(self, index: int) -> E8Vector:
        """Return basis vector."""
        return E8Vector.basis(index)
    
    def add(self, v1: E8Vector, v2: E8Vector) -> E8Vector:
        """Add two vectors."""
        return v1 + v2
    
    def subtract(self, v1: E8Vector, v2: E8Vector) -> E8Vector:
        """Subtract two vectors."""
        return v1 - v2
    
    def scale(self, v: E8Vector, scalar: float) -> E8Vector:
        """Scale a vector."""
        return v * scalar
    
    def dot(self, v1: E8Vector, v2: E8Vector) -> float:
        """Dot product."""
        return v1.dot(v2)
    
    def norm_squared(self, v: E8Vector) -> float:
        """Squared norm."""
        return v.norm_squared
    
    def norm(self, v: E8Vector) -> float:
        """Norm."""
        return v.norm()
    
    def get_roots(self, count: int = 240) -> List[E8Vector]:
        """Get root vectors."""
        return self.root_system.get_roots(count)
    
    def weyl_reflection(self, v: E8Vector, root: E8Vector) -> E8Vector:
        """
        Apply Weyl reflection across root.
        
        s_α(v) = v - 2(v·α)/(α·α) * α
        """
        root_norm_sq = root.dot(root)
        if root_norm_sq == 0:
            return v
        factor = 2 * v.dot(root) / root_norm_sq
        return v - root * factor
    
    def cartan_matrix(self) -> List[List[int]]:
        """
        Return E8 Cartan matrix (8x8).
        
        The Cartan matrix encodes the simple root structure.
        """
        return [
            [2, -1, 0, 0, 0, 0, 0, 0],
            [-1, 2, -1, 0, 0, 0, 0, 0],
            [0, -1, 2, -1, 0, 0, 0, 0],
            [0, 0, -1, 2, -1, 0, 0, 0],
            [0, 0, 0, -1, 2, -1, 0, -1],
            [0, 0, 0, 0, -1, 2, -1, 0],
            [0, 0, 0, 0, 0, -1, 2, 0],
            [0, 0, 0, 0, -1, 0, 0, 2],
        ]
    
    def dynkin_diagram(self) -> str:
        """Return ASCII Dynkin diagram."""
        return """
        O---O---O---O---O---O---O
                            |
                            O
        """
    
    def projection_to_leech(self, v: E8Vector) -> List[float]:
        """
        Project E8 vector to Leech lattice (24D).
        
        Uses the fact that Leech contains 3 copies of E8.
        """
        # Simple embedding: repeat coords 3 times
        leech_coords = list(v.coords) * 3
        return leech_coords[:24]
    
    def from_leech_projection(self, leech_coords: List[float]) -> E8Vector:
        """
        Reconstruct E8 vector from Leech projection.
        
        Averages the 3 copies.
        """
        if len(leech_coords) < 24:
            leech_coords = leech_coords + [0.0] * (24 - len(leech_coords))
        
        e8_coords = []
        for i in range(8):
            avg = (leech_coords[i] + leech_coords[i + 8] + leech_coords[i + 16]) / 3
            e8_coords.append(avg)
        
        return E8Vector(tuple(e8_coords))
    
    def to_mdhg_address(self, v: E8Vector) -> Dict[str, Any]:
        """
        Convert E8 vector to MDHG address.
        
        MDHG address format:
        - room, floor, building from first 6 coords
        - city, planet from remaining 2 + hash
        """
        coords = v.coords
        
        def hash_segment(segment: Tuple[float, ...]) -> str:
            return hashlib.sha256(json.dumps([round(c, 6) for c in segment]).encode()).hexdigest()[:8]
        
        return {
            'room': f"room_{hash_segment(coords[0:2])}",
            'floor': f"floor_{hash_segment(coords[2:4])}",
            'building': f"building_{hash_segment(coords[4:6])}",
            'city': f"city_{hash_segment(coords[6:8])}",
            'planet': f"planet_e8_{v.fingerprint()[:6]}",
            'norm': round(v.norm(), 6),
        }
    
    def fingerprint(self, v: E8Vector) -> str:
        """Generate fingerprint."""
        return v.fingerprint()
    
    def stats(self) -> Dict[str, Any]:
        """Get lattice statistics."""
        return {
            'dimension': E8_DIM,
            'minimal_norm': E8_MIN_NORM,
            'root_count': E8_ROOT_COUNT,
            'weyl_group_order': self.root_system.weyl_group_order(),
            'coxeter_number': self.root_system.coxeter_number(),
            'packing_density': self.packing_density(),
        }
    
    def packing_density(self) -> float:
        """
        Return sphere packing density.
        
        E8 achieves density π^4 / 384 ≈ 0.2537
        """
        return (math.pi ** 4) / 384
    
    def kissing_number(self) -> int:
        """Return kissing number (240)."""
        return E8_ROOT_COUNT


__all__ = ['E8Vector', 'E8RootSystem', 'E8Lattice']
