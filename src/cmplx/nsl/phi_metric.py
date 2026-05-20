"""
Phi Metric - Composite Quality Metric for CQE

The CQE framework evaluates transitions using a composite objective
function Φ that aggregates geometric alignment, parity consistency,
sparsity of operator application, and kissing number deviations.

The Φ metric governs monotone optimization: transformations are only
accepted when the total Φ does not increase (ΔΦ ≤ 0).

This implementation provides both the basic structure and enhanced
computations based on actual geometric properties.

Ported from cqe-complete/cqe/core/phi_metric.py
Author: Manus AI (based on CQE research)
Date: December 5, 2025
"""

import numpy as np
from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class PhiComponents:
    """
    Data class representing the four components of the Φ metric.
    
    All components follow the convention: lower is better.
    """
    geom: float = 0.0      # Geometric alignment (distance to lattice)
    parity: float = 0.0    # Parity consistency (CRT/Golay syndrome)
    sparsity: float = 0.0  # Operator sparsity (complexity penalty)
    kissing: float = 0.0   # Kissing number deviation
    
    def __repr__(self) -> str:
        return (f"PhiComponents(geom={self.geom:.4f}, parity={self.parity:.4f}, "
                f"sparsity={self.sparsity:.4f}, kissing={self.kissing:.4f})")


class PhiMetric:
    """
    Composite Φ metric for CQE.
    
    The metric is computed as a weighted sum of four components:
    - Geometric alignment (40%): How well vector aligns with lattice
    - Parity consistency (30%): Digital root and modular consistency
    - Sparsity (20%): Complexity of transformation
    - Kissing number (10%): Local neighborhood quality
    
    Default weights can be customized via constructor.
    """
    
    # Golden ratio for scaling
    PHI = (1 + np.sqrt(5)) / 2
    
    # Standard weights
    DEFAULT_WEIGHTS = {
        'geom': 0.4,
        'parity': 0.3,
        'sparsity': 0.2,
        'kissing': 0.1
    }
    
    def __init__(self, 
                 w_geom: float = 0.4, 
                 w_parity: float = 0.3,
                 w_sparsity: float = 0.2, 
                 w_kissing: float = 0.1):
        """
        Initialize phi metric with custom weights.
        
        Args:
            w_geom: Weight for geometric component
            w_parity: Weight for parity component
            w_sparsity: Weight for sparsity component
            w_kissing: Weight for kissing number component
        """
        self.w_geom = w_geom
        self.w_parity = w_parity
        self.w_sparsity = w_sparsity
        self.w_kissing = w_kissing
        
        # Normalize weights to sum to 1
        total = w_geom + w_parity + w_sparsity + w_kissing
        if abs(total - 1.0) > 1e-6:
            self.w_geom /= total
            self.w_parity /= total
            self.w_sparsity /= total
            self.w_kissing /= total
    
    def compute(self, context: Dict[str, Any]) -> PhiComponents:
        """
        Compute the Φ metric components from context.
        
        Args:
            context: Dictionary containing:
                - 'vector': Input vector
                - 'projected': Projected lattice point (optional)
                - 'operators': List of applied operators (optional)
                - 'digital_root': Digital root value (optional)
                - 'neighbors': Number of neighbors (optional)
        
        Returns:
            PhiComponents with computed values
        """
        # Extract context
        vector = context.get('vector')
        projected = context.get('projected')
        operators = context.get('operators', [])
        digital_root = context.get('digital_root')
        neighbors = context.get('neighbors')
        
        # Compute geometric component
        geom = self._compute_geometric(vector, projected)
        
        # Compute parity component
        parity = self._compute_parity(vector, digital_root)
        
        # Compute sparsity component
        sparsity = self._compute_sparsity(operators)
        
        # Compute kissing number component
        kissing = self._compute_kissing(neighbors)
        
        return PhiComponents(
            geom=geom,
            parity=parity,
            sparsity=sparsity,
            kissing=kissing
        )
    
    def _compute_geometric(self, 
                          vector: Optional[np.ndarray], 
                          projected: Optional[np.ndarray]) -> float:
        """
        Compute geometric alignment component.
        
        Measures distance from vector to nearest lattice point.
        """
        if vector is None:
            return 0.0
        
        if projected is None:
            # No projection available, use vector norm as proxy
            return float(np.linalg.norm(vector))
        
        # Distance to lattice
        distance = np.linalg.norm(vector - projected)
        
        # Scale by golden ratio for natural units
        return float(distance / self.PHI)
    
    def _compute_parity(self, 
                       vector: Optional[np.ndarray], 
                       digital_root: Optional[int]) -> float:
        """
        Compute parity consistency component.
        
        Measures consistency with digital root and modular arithmetic.
        """
        if vector is None:
            return 0.0
        
        # Compute digital root from vector if not provided
        if digital_root is None:
            vector_sum = int(np.sum(np.abs(vector)))
            digital_root = self._compute_digital_root(vector_sum)
        
        # Parity score: 0 if DR is 0 or 9 (perfect), increases otherwise
        if digital_root in [0, 9]:
            return 0.0
        else:
            # Penalize deviation from 0/9
            return float(min(digital_root, 9 - digital_root)) / 9.0
    
    def _compute_digital_root(self, n: int) -> int:
        """Compute digital root (repeated digit sum until single digit)."""
        n = abs(n)
        if n == 0:
            return 0
        return 1 + ((n - 1) % 9)
    
    def _compute_sparsity(self, operators: list) -> float:
        """
        Compute sparsity component.
        
        Penalizes complex transformations with many operators.
        """
        if not operators:
            return 0.0
        
        # Simple count-based sparsity
        count = len(operators)
        
        # Scale logarithmically to avoid excessive penalty
        return float(np.log1p(count) / self.PHI)
    
    def _compute_kissing(self, neighbors: Optional[int]) -> float:
        """
        Compute kissing number deviation component.
        
        Measures how far local neighborhood deviates from optimal.
        For E8: optimal kissing number is 240
        For Leech: optimal kissing number is 196560
        """
        if neighbors is None:
            return 0.0
        
        # Assume E8 context (240 neighbors optimal)
        optimal = 240
        
        # Compute relative deviation
        if neighbors == 0:
            return 1.0  # Maximum penalty
        
        deviation = abs(neighbors - optimal) / optimal
        
        # Cap at 1.0
        return float(min(deviation, 1.0))
    
    def total(self, comps: PhiComponents) -> float:
        """
        Compute the weighted total Φ from its components.
        
        Args:
            comps: PhiComponents with individual values
        
        Returns:
            Total Φ value (lower is better)
        """
        return (self.w_geom * comps.geom +
                self.w_parity * comps.parity +
                self.w_sparsity * comps.sparsity +
                self.w_kissing * comps.kissing)
    
    def evaluate(self, context: Dict[str, Any]) -> float:
        """
        Convenience method to compute and return total Φ.
        
        Args:
            context: Context dictionary
        
        Returns:
            Total Φ value
        """
        comps = self.compute(context)
        return self.total(comps)
    
    def is_valid_transition(self, 
                           phi_before: float, 
                           phi_after: float) -> bool:
        """
        Check if a transition is valid (ΔΦ ≤ 0).
        
        Args:
            phi_before: Φ value before transition
            phi_after: Φ value after transition
        
        Returns:
            True if transition decreases or maintains Φ
        """
        delta_phi = phi_after - phi_before
        return delta_phi <= 0
    
    def __repr__(self) -> str:
        return (f"PhiMetric(w_geom={self.w_geom:.2f}, w_parity={self.w_parity:.2f}, "
                f"w_sparsity={self.w_sparsity:.2f}, w_kissing={self.w_kissing:.2f})")
