"""
E8 Root System Implementation
=============================

Direct implementation from CQE E8_LATTICE card formalizations.
"""
import numpy as np
from typing import List, Tuple, Set
import itertools


class E8RootSystem:
    """
    E8 Root System
    
    From E8_LATTICE_0 card:
    E₈ = {(x₁, x₂, ..., x₈) ∈ ℝ⁸ : 2xᵢ ∈ ℤ ∀i, ∑xᵢ ∈ 2ℤ}
    
    The E8 lattice is the set of points in 8D space where:
    - All coordinates are either integers or half-integers
    - The sum of coordinates is even
    """
    
    DIM = 8
    ROOT_COUNT = 240
    NORM_SQUARED = 2.0
    
    def __init__(self):
        self._roots: np.ndarray = None
        self._root_set: Set[Tuple[float, ...]] = None
        self._simple_roots: np.ndarray = None
    
    def generate_roots(self) -> np.ndarray:
        """
        Generate all 240 E8 roots.
        
        Two types:
        1. Type D8: (±1, ±1, 0^6) - 112 roots
        2. Type E8: (±½)^8 with even number of positive signs - 128 roots
        """
        if self._roots is not None:
            return self._roots
        
        roots = []
        
        # Type 1: (±1, ±1, 0^6) permutations
        # Choose 2 positions from 8 for non-zero entries
        for i, j in itertools.combinations(range(self.DIM), 2):
            for s1 in [1, -1]:
                for s2 in [1, -1]:
                    root = np.zeros(self.DIM)
                    root[i] = s1
                    root[j] = s2
                    roots.append(root)
        
        # Type 2: (±½)^8 with even number of positive signs
        # 128 roots (2^7 = 128 combinations with constraint)
        for signs in self._even_sign_combinations():
            root = np.array([s * 0.5 for s in signs])
            roots.append(root)
        
        self._roots = np.array(roots)
        self._root_set = set(tuple(r) for r in roots)
        
        assert len(roots) == self.ROOT_COUNT, f"Expected {self.ROOT_COUNT} roots, got {len(roots)}"
        
        return self._roots
    
    def _even_sign_combinations(self) -> List[Tuple[int, ...]]:
        """Generate 8D sign combinations with even number of + signs."""
        combinations = []
        for signs in itertools.product([1, -1], repeat=self.DIM):
            if sum(1 for s in signs if s > 0) % 2 == 0:
                combinations.append(signs)
        return combinations
    
    def nearest_root(self, vector: np.ndarray) -> np.ndarray:
        """Find nearest E8 root to a given vector."""
        roots = self.generate_roots()
        distances = np.linalg.norm(roots - vector, axis=1)
        return roots[np.argmin(distances)]
    
    def is_root(self, vector: np.ndarray, tolerance: float = 1e-10) -> bool:
        """Check if vector is in the E8 root system."""
        if self._roots is None:
            self.generate_roots()
        return tuple(np.round(vector, 10)) in self._root_set
    
    def norm_squared(self, vector: np.ndarray) -> float:
        """Calculate ||vector||²."""
        return float(np.dot(vector, vector))
    
    def validate_root(self, root: np.ndarray) -> bool:
        """
        Validate that a root satisfies E8 lattice conditions:
        - ||root||² = 2
        - Either all coordinates are integers, or all are half-integers
        - Sum of coordinates is even
        """
        # Check norm
        if abs(self.norm_squared(root) - self.NORM_SQUARED) > 1e-10:
            return False
        
        # Check integer or half-integer
        doubled = 2 * root
        if not np.allclose(doubled, np.round(doubled)):
            return False
        
        # Check sum is even
        if int(np.round(np.sum(doubled))) % 2 != 0:
            return False
        
        return True
    
    def get_simple_roots(self) -> np.ndarray:
        """
        Get the 8 simple roots of E8.
        
        Simple roots form a basis for the root system.
        """
        if self._simple_roots is not None:
            return self._simple_roots
        
        # E8 simple roots (standard form)
        simple = np.array([
            [1, -1, 0, 0, 0, 0, 0, 0],
            [0, 1, -1, 0, 0, 0, 0, 0],
            [0, 0, 1, -1, 0, 0, 0, 0],
            [0, 0, 0, 1, -1, 0, 0, 0],
            [0, 0, 0, 0, 1, -1, 0, 0],
            [0, 0, 0, 0, 0, 1, -1, 0],
            [0, 0, 0, 0, 0, 0, 1, -1],
            [0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5],
        ])
        
        self._simple_roots = simple
        return simple
    
    def weyl_group_order(self) -> int:
        """
        Return the order of the Weyl group of E8.
        
        |W(E8)| = 2^14 × 3^5 × 5^2 × 7 = 696,729,600
        """
        return 696729600
    
    def cartan_matrix(self) -> np.ndarray:
        """
        Compute the Cartan matrix of E8.
        
        C[i,j] = 2(αᵢ, αⱼ) / (αⱼ, αⱼ)
        where αᵢ are simple roots.
        """
        simple = self.get_simple_roots()
        n = len(simple)
        cartan = np.zeros((n, n))
        
        for i in range(n):
            for j in range(n):
                cartan[i, j] = 2 * np.dot(simple[i], simple[j]) / np.dot(simple[j], simple[j])
        
        return cartan


class E8Embedding:
    """
    E8 Embedding Operations
    
    From E8_LATTICE_1 card:
    φₚ: Problem_Space → E8_Configuration_Space
    """
    
    def __init__(self, e8_system: E8RootSystem = None):
        self.e8 = e8_system or E8RootSystem()
        self.e8.generate_roots()
    
    def embed_problem(self, problem_vector: np.ndarray) -> np.ndarray:
        """
        Embed a problem space vector into E8 configuration space.
        
        Maps to: (r₁, r₂, ..., r₂₄₀, w₁, w₂, ..., w₈)
        where rᵢ are root projections and wᵢ are weights.
        """
        # Project onto each root
        root_projections = np.array([
            np.dot(problem_vector[:self.e8.DIM], root)
            for root in self.e8._roots
        ])
        
        # Weight components (simplified - just use input coordinates)
        weights = problem_vector[:self.e8.DIM]
        
        return np.concatenate([root_projections, weights])
    
    def nearest_root(self, vector: np.ndarray) -> np.ndarray:
        """Find nearest E8 root to a given vector."""
        roots = self.e8.generate_roots()
        distances = np.linalg.norm(roots - vector, axis=1)
        return roots[np.argmin(distances)]
    
    def snap_to_lattice(self, vector: np.ndarray) -> np.ndarray:
        """
        Snap a vector to the nearest E8 lattice point (ALENA operation).
        
        From E8_LATTICE card: Project vector to nearest E8 lattice point
        with deviation < 1e-14.
        """
        # Find nearest root
        nearest = self.nearest_root(vector)
        
        # Validate snap precision
        deviation = np.linalg.norm(vector - nearest)
        assert deviation < 1e-14, f"Snap deviation {deviation} exceeds tolerance"
        
        return nearest


def demo():
    """Demonstrate E8 root system."""
    print("=" * 70)
    print("E8 ROOT SYSTEM DEMONSTRATION")
    print("=" * 70)
    
    # Create E8 system
    e8 = E8RootSystem()
    
    # Generate roots
    print("\n[1] Generating 240 E8 roots...")
    roots = e8.generate_roots()
    print(f"    Generated {len(roots)} roots")
    
    # Validate
    print("\n[2] Validating all roots...")
    valid = all(e8.validate_root(r) for r in roots)
    print(f"    All roots valid: {valid}")
    
    # Show sample roots
    print("\n[3] Sample roots:")
    for i in [0, 112, 128, 239]:
        root = roots[i]
        norm = e8.norm_squared(root)
        print(f"    Root {i}: {root}")
        print(f"           Norm² = {norm:.6f}")
    
    # Simple roots
    print("\n[4] Simple roots (8 generators):")
    simple = e8.get_simple_roots()
    for i, s in enumerate(simple):
        print(f"    alpha{i+1}: {s}")
    
    # Weyl group
    print(f"\n[5] Weyl group order: {e8.weyl_group_order():,}")
    
    # Cartan matrix
    print("\n[6] Cartan matrix (8×8):")
    cartan = e8.cartan_matrix()
    print(cartan.astype(int))
    
    # Embedding demo
    print("\n[7] Embedding demo:")
    embedding = E8Embedding(e8)
    test_vector = np.array([0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5])
    embedded = embedding.embed_problem(test_vector)
    print(f"    Input: {test_vector}")
    print(f"    Embedded shape: {embedded.shape}")
    
    print("\n" + "=" * 70)
    print("E8 ROOT SYSTEM: OPERATIONAL")
    print("=" * 70)


if __name__ == "__main__":
    demo()
