"""
Aletheia3 Leech Lattice Wrapper

Wraps Nick's original Leech lattice implementation.
"""

import numpy as np
from typing import Dict, Tuple

from ._leech_original import (
    Aletheia3E8,
    LeechVector,
    from_e8_triple,
    to_e8_triple,
    validate_leech_vector,
)


class Aletheia3Leech:
    """
    Aletheia3 Leech Lattice Interface
    
    Wraps Nick's original Leech lattice construction.
    Leech emerges from 3×E8 + Golay structure.
    """
    
    def __init__(self):
        """Initialize Leech lattice interface."""
        self.dimension = 24
        self.kissing_number = 196560
        self.minimal_norm = 4.0
        
        # E8 for transitions
        self._e8 = Aletheia3E8()
        
    def construct_from_e8_blocks(self, blocks: list) -> np.ndarray:
        """
        Construct Leech vector from three E8 blocks.
        
        Uses Nick's original from_e8_triple construction.
        
        Args:
            blocks: List of three 8D E8 vectors
            
        Returns:
            24D Leech vector
        """
        if len(blocks) != 3:
            raise ValueError("Need exactly 3 E8 blocks")
            
        return from_e8_triple(blocks[0], blocks[1], blocks[2])
        
    def decompose_to_e8_blocks(self, leech_vector: np.ndarray) -> Dict:
        """
        Decompose Leech vector into three E8 blocks.
        
        Uses Nick's original to_e8_triple decomposition.
        
        Args:
            leech_vector: 24D Leech vector
            
        Returns:
            Dictionary with three E8 blocks
        """
        def e8_proj(v):
            return self._e8.project(v)["projected"]
            
        e8_1, e8_2, e8_3 = to_e8_triple(leech_vector, e8_proj)
        
        return {
            "block_1": e8_1,
            "block_2": e8_2,
            "block_3": e8_3,
            "original": leech_vector
        }
        
    def validate_leech_vector(self, vector: np.ndarray) -> Dict:
        """
        Validate if vector satisfies Leech lattice properties.
        
        Args:
            vector: 24D vector
            
        Returns:
            Dictionary with validation results
        """
        return validate_leech_vector(vector)
        
    def create_leech_vector(self, vector: np.ndarray) -> LeechVector:
        """
        Create LeechVector dataclass from numpy array.
        
        Args:
            vector: 24D vector
            
        Returns:
            LeechVector with computed properties
        """
        return LeechVector(
            vector=vector,
            norm_squared=float(np.dot(vector, vector)),
            is_minimal=False  # Will be computed in __post_init__
        )


def create_leech() -> Aletheia3Leech:
    """Create and return a Leech lattice interface."""
    return Aletheia3Leech()
