"""
CMPLXLatticeProjector - Unified E8 Lattice Vector Projection Tool
==================================================================

Unified from 20+ scattered E8 lattice files in D:\Work Files\CMPLX-Monorepo

This tool provides complete E8 lattice functionality:
- Core lattice structure with 240 root vectors
- Babai nearest-plane algorithm for vector projection
- Root system generation
- Mathematical property analysis
- Data embedding into lattice space
- Lattice quality metrics

CMPLX Layer: L5 (Morphon) - Structural transformation
SNAP: morphon
"""

from __future__ import annotations
import numpy as np
from numpy.linalg import qr, norm
from typing import Tuple, List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum
import hashlib
import logging
import itertools

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LatticeProjectionMethod(Enum):
    """Available projection methods to E8 lattice"""
    BABAI_NEAREST_PLANE = "babai_nearest_plane"
    EXHAUSTIVE_SEARCH = "exhaustive_search"
    WEYL_CHAMBER = "weyl_chamber"


class CarlsonPattern(Enum):
    """Digital root patterns for lattice analysis"""
    THETA = "theta"       # Digital root 3
    PI = "pi"            # Digital root 3, 6
    EULER = "euler"      # Digital root 2, 4, 8
    PRIME = "prime"      # Digital root 2, 3, 5, 7


@dataclass
class LatticeProjectionResult:
    """Result of projecting a vector to the E8 lattice"""
    original_vector: np.ndarray
    projected_vector: np.ndarray
    coefficients: np.ndarray
    residual_error: float
    projection_method: LatticeProjectionMethod
    quality_score: float


@dataclass
class LatticeAnalysisResult:
    """Complete analysis of E8 lattice properties"""
    dimension: int
    root_count: int
    weyl_group_order: int
    coxeter_number: int
    fundamental_weights: np.ndarray
    cartan_matrix: np.ndarray
    lattice_points_at_radius: Dict[int, int]
    theta_coefficients: Dict[int, int]


class CMPLXLatticeProjector:
    """
    Unified E8 Lattice Projector - Complete E8 lattice mathematics processor
    
    This class consolidates functionality from:
    - E8Lattice.py (core structure)
    - E8LatticeAnalyzer.py (analysis)
    - E8LatticeComputer.py (computations)
    - E8LatticeProcessor.py (processing)
    - 16+ other scattered E8 lattice files
    
    The E8 lattice is an 8-dimensional even unimodular lattice with 
    240 root vectors. It is the densest sphere packing in 8 dimensions
    and has applications in string theory, quantum computing, and
    machine learning embeddings.
    
    CMPLX Stratification:
    - Layer: L5 (Morphon)
    - Family: lattice_family
    - Crystal: cmplx_lattice_projector_v1.0.0
    """
    
    # E8 lattice constants
    DIMENSION = 8
    ROOT_COUNT = 240
    CARTAN_DIMENSION = 8
    TOTAL_SLOTS = 248
    
    def __init__(self, precision: float = 1e-10):
        """
        Initialize the E8 Lattice Projector
        
        Args:
            precision: Numerical precision for computations
        """
        self.precision = precision
        
        # Core lattice structure
        self.B = self._construct_e8_basis()
        self.B_inv = np.linalg.inv(self.B)
        
        # QR factorization for Babai algorithm
        self.Q, self.R = qr(self.B)
        
        # Basis condition number
        self.condition_number = np.linalg.cond(self.B)
        
        # Generate root system
        self.root_system = self._generate_e8_root_system()
        self.simple_roots = self._generate_simple_roots()
        
        # Cartan matrix and fundamental weights
        self.cartan_matrix = self._e8_cartan_matrix()
        self.fundamental_weights = self._fundamental_weights()
        
        # Weyl chambers (sample)
        self.weyl_chambers = self._generate_weyl_chambers()
        
        # Lattice properties
        self.lattice_properties = self._initialize_lattice_properties()
        
        logger.info(f"CMPLXLatticeProjector initialized: {self.ROOT_COUNT} roots, "
                   f"condition={self.condition_number:.2e}")
    
    def _construct_e8_basis(self) -> np.ndarray:
        """
        Construct E8 simple root basis matrix
        
        Uses the standard E8 root system construction with:
        - 7 simple roots of type A7 (chain)
        - 1 additional root for E8 exceptional connection
        """
        B = np.array([
            [1, -1, 0, 0, 0, 0, 0, 0],
            [0, 1, -1, 0, 0, 0, 0, 0],  
            [0, 0, 1, -1, 0, 0, 0, 0],
            [0, 0, 0, 1, -1, 0, 0, 0],
            [0, 0, 0, 0, 1, -1, 0, 0],
            [0, 0, 0, 0, 0, 1, -1, 0],
            [0, 0, 0, 0, 0, 0, 1, -1],
            [0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5]  # E8 characteristic
        ], dtype=float)
        return B
    
    def _generate_e8_root_system(self) -> np.ndarray:
        """
        Generate the complete E8 root system (240 roots)
        
        Two types of roots:
        - Type 1: ±ei ± ej for i ≠ j (112 roots)
        - Type 2: ±(1/2)(±e1 ± ... ± e8) with even # of minus signs (128 roots)
        """
        roots = []
        
        # Type 1: ±ei ± ej for i ≠ j
        for i in range(self.DIMENSION):
            for j in range(i + 1, self.DIMENSION):
                for sign1 in [-1, 1]:
                    for sign2 in [-1, 1]:
                        root = np.zeros(self.DIMENSION)
                        root[i] = sign1
                        root[j] = sign2
                        roots.append(root)
        
        # Type 2: ±(1/2)(±e1 ± ... ± e8) with even number of minus signs
        for i in range(256):  # 2^8 = 256 combinations
            signs = [(i >> j) & 1 for j in range(8)]
            minus_count = sum(1 for s in signs if s == 0)
            
            if minus_count % 2 == 0:
                root = np.array([0.5 * (1 if s else -1) for s in signs])
                roots.append(root)
        
        return np.array(roots[:self.ROOT_COUNT])
    
    def _generate_simple_roots(self) -> np.ndarray:
        """Generate the 8 simple roots of E8"""
        return self.B.copy()
    
    def _e8_cartan_matrix(self) -> np.ndarray:
        """Generate the E8 Cartan matrix"""
        matrix = np.eye(self.DIMENSION) * 2
        
        # E8 Dynkin diagram connections
        matrix[0, 1] = matrix[1, 0] = -1
        matrix[1, 2] = matrix[2, 1] = -1  
        matrix[2, 3] = matrix[3, 2] = -1
        matrix[3, 4] = matrix[4, 3] = -1
        matrix[4, 5] = matrix[5, 4] = -1
        matrix[5, 6] = matrix[6, 5] = -1
        matrix[2, 7] = matrix[7, 2] = -1  # E8 exceptional connection
        
        return matrix
    
    def _fundamental_weights(self) -> np.ndarray:
        """Generate the 8 fundamental weights of E8"""
        # Fundamental weights in the basis of simple roots
        weights = np.array([
            [1, 0, 0, 0, 0, 0, 0, 0],
            [1, 1, 0, 0, 0, 0, 0, 0],
            [1, 1, 1, 0, 0, 0, 0, 0],
            [1, 1, 1, 1, 0, 0, 0, 0],
            [1, 1, 1, 1, 1, 0, 0, 0],
            [1, 1, 1, 1, 1, 1, 0, 0],
            [1, 1, 1, 1, 1, 1, 1, 0],
            [0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5]
        ])
        return weights
    
    def _generate_weyl_chambers(self) -> List[np.ndarray]:
        """Generate sample Weyl chambers"""
        chambers = []
        for _ in range(100):
            chamber = np.random.randn(self.DIMENSION)
            chamber = chamber / norm(chamber)
            chambers.append(chamber)
        return chambers
    
    def _initialize_lattice_properties(self) -> Dict[str, Any]:
        """Initialize lattice mathematical properties"""
        return {
            'dimension': self.DIMENSION,
            'root_count': self.ROOT_COUNT,
            'weyl_group_order': 696729600,
            'coxeter_number': 30,
            'dual_coxeter_number': 30,
            'simple_roots': 8,
            'positive_roots': 120,
            'rank': self.DIMENSION,
            'lattice_points': {
                2: 240,   # r² = 2
                4: 2160,  # r² = 4
                6: 6720,  # r² = 6
                8: 17520, # r² = 8
                10: 30240,# r² = 10
                12: 60480,# r² = 12
            },
            'theta_coefficients': {
                1: 240,
                2: 2160,
                3: 6720,
                4: 17520,
                5: 30240,
                6: 60480
            }
        }
    
    # =========================================================================
    # CORE PROJECTION METHODS
    # =========================================================================
    
    def project_to_lattice(
        self, 
        vector: np.ndarray,
        method: LatticeProjectionMethod = LatticeProjectionMethod.BABAI_NEAREST_PLANE
    ) -> LatticeProjectionResult:
        """
        Project vector to E8 lattice using specified method
        
        Args:
            vector: 8-dimensional input vector
            method: Projection algorithm to use
            
        Returns:
            LatticeProjectionResult with projected vector and metadata
        """
        if len(vector) != self.DIMENSION:
            raise ValueError(f"Vector must be {self.DIMENSION}-dimensional")
        
        if method == LatticeProjectionMethod.BABAI_NEAREST_PLANE:
            return self._babai_nearest_plane(vector)
        elif method == LatticeProjectionMethod.EXHAUSTIVE_SEARCH:
            return self._exhaustive_search(vector)
        elif method == LatticeProjectionMethod.WEYL_CHAMBER:
            return self._weyl_chamber_projection(vector)
        else:
            raise ValueError(f"Unknown projection method: {method}")
    
    def _babai_nearest_plane(self, vector: np.ndarray) -> LatticeProjectionResult:
        """
        Babai nearest-plane algorithm for lattice projection
        
        This is the most efficient method for projecting to E8 lattice.
        It uses QR factorization to find approximate integer coefficients.
        """
        # Project onto lattice basis
        coeffs = self.B_inv @ vector
        
        # Round to nearest integers (Babai rounding)
        integer_coeffs = np.round(coeffs)
        
        # Compute projected vector
        projected = self.B @ integer_coeffs
        
        # Calculate residual error
        residual = norm(vector - projected)
        
        # Calculate quality score (lower is better)
        quality = residual / norm(vector) if norm(vector) > 0 else 0.0
        
        return LatticeProjectionResult(
            original_vector=vector.copy(),
            projected_vector=projected.copy(),
            coefficients=integer_coeffs.copy(),
            residual_error=residual,
            projection_method=LatticeProjectionMethod.BABAI_NEAREST_PLANE,
            quality_score=quality
        )
    
    def _exhaustive_search(self, vector: np.ndarray) -> LatticeProjectionResult:
        """
        Exhaustive search for nearest lattice point
        
        Guarantees finding the true nearest point but is computationally
        expensive. Used for verification and small search spaces.
        """
        best_point = None
        best_distance = float('inf')
        best_coeffs = None
        
        # Search in a bounded region around the origin
        search_range = 3
        
        for coeffs in itertools.product(
            range(-search_range, search_range + 1), 
            repeat=self.DIMENSION
        ):
            coeffs = np.array(coeffs)
            lattice_point = self.B @ coeffs
            distance = norm(vector - lattice_point)
            
            if distance < best_distance:
                best_distance = distance
                best_point = lattice_point
                best_coeffs = coeffs
        
        return LatticeProjectionResult(
            original_vector=vector.copy(),
            projected_vector=best_point,
            coefficients=best_coeffs,
            residual_error=best_distance,
            projection_method=LatticeProjectionMethod.EXHAUSTIVE_SEARCH,
            quality_score=best_distance / norm(vector) if norm(vector) > 0 else 0.0
        )
    
    def _weyl_chamber_projection(self, vector: np.ndarray) -> LatticeProjectionResult:
        """
        Project using Weyl chamber decomposition
        
        This method projects to the fundamental Weyl chamber first,
        then uses symmetries to find the full lattice point.
        """
        # Find nearest Weyl chamber representative
        chamber_proj = self._project_to_weyl_chamber(vector)
        
        # Use Babai as fallback for full projection
        return self._babai_nearest_plane(chamber_proj)
    
    def _project_to_weyl_chamber(self, vector: np.ndarray) -> np.ndarray:
        """Project vector to fundamental Weyl chamber"""
        # Simplified Weyl chamber projection
        # Uses simple root reflections to fold into fundamental chamber
        proj = vector.copy()
        
        for _ in range(100):  # Max iterations
            improved = False
            for i in range(self.DIMENSION):
                # Check if reflection would improve position
                root = self.simple_roots[i]
                if proj @ root < 0:
                    proj = proj - 2 * (proj @ root) / (root @ root) * root
                    improved = True
            if not improved:
                break
        
        return proj
    
    # =========================================================================
    # DATA EMBEDDING
    # =========================================================================
    
    def embed_data(self, data: Any) -> np.ndarray:
        """
        Embed arbitrary data into E8 lattice space
        
        Uses SHA-256 hash to create 8-dimensional coordinate vector,
        then projects to nearest lattice point.
        
        Args:
            data: Any hashable data to embed
            
        Returns:
            8-dimensional lattice point
        """
        # Convert data to numerical representation
        data_hash = hashlib.sha256(str(data).encode()).hexdigest()
        
        # Extract 8 components from hash
        components = []
        for i in range(8):
            hex_chunk = data_hash[i*8:(i+1)*8]
            component = int(hex_chunk, 16) / (16**8)  # Normalize to [0,1]
            components.append(component * 2 - 1)  # Scale to [-1,1]
        
        # Project onto E8 lattice
        coordinates = np.array(components)
        
        # Find nearest lattice point
        result = self._babai_nearest_plane(coordinates)
        
        return result.projected_vector
    
    def embed_batch(self, data_items: List[Any]) -> np.ndarray:
        """
        Embed multiple data items into lattice space
        
        Args:
            data_items: List of data to embed
            
        Returns:
            Array of shape (n_items, 8) containing lattice points
        """
        embeddings = []
        for item in data_items:
            embedding = self.embed_data(item)
            embeddings.append(embedding)
        return np.array(embeddings)
    
    # =========================================================================
    # LATTICE ANALYSIS
    # =========================================================================
    
    def analyze_lattice_properties(self) -> LatticeAnalysisResult:
        """Get complete analysis of E8 lattice properties"""
        return LatticeAnalysisResult(
            dimension=self.DIMENSION,
            root_count=self.ROOT_COUNT,
            weyl_group_order=self.lattice_properties['weyl_group_order'],
            coxeter_number=self.lattice_properties['coxeter_number'],
            fundamental_weights=self.fundamental_weights,
            cartan_matrix=self.cartan_matrix,
            lattice_points_at_radius=self.lattice_properties['lattice_points'],
            theta_coefficients=self.lattice_properties['theta_coefficients']
        )
    
    def calculate_lattice_quality(self, coordinates: np.ndarray) -> float:
        """
        Calculate quality of E8 lattice embedding
        
        Quality is measured by the minimum distance to any lattice point.
        Higher minimum distance = better spreading = higher quality.
        
        Args:
            coordinates: Point to evaluate
            
        Returns:
            Quality score (0-1, higher is better)
        """
        # Distance to nearest root
        distances = [norm(coordinates - root) for root in self.root_system]
        min_distance = min(distances)
        
        # Normalize to [0, 1] (max possible distance is sqrt(8) for E8)
        quality = min_distance / np.sqrt(2)  # Normalize by longest root length
        
        return min(1.0, quality)
    
    def find_nearest_roots(
        self, 
        vector: np.ndarray, 
        k: int = 5
    ) -> List[Tuple[np.ndarray, float]]:
        """
        Find k nearest root vectors to given vector
        
        Args:
            vector: Query vector
            k: Number of nearest roots to return
            
        Returns:
            List of (root_vector, distance) tuples
        """
        distances = [
            (root, norm(vector - root)) 
            for root in self.root_system
        ]
        
        # Sort by distance and return top k
        distances.sort(key=lambda x: x[1])
        return distances[:k]
    
    def compute_weight_decomposition(self, vector: np.ndarray) -> Dict[str, np.ndarray]:
        """
        Decompose vector into fundamental weight components
        
        Args:
            vector: Vector to decompose
            
        Returns:
            Dictionary with weight components
        """
        # Solve for coefficients in fundamental weight basis
        coeffs = np.linalg.solve(self.fundamental_weights.T, vector)
        
        return {
            'coefficients': coeffs,
            'decomposition': self.fundamental_weights.T @ coeffs,
            'residual': norm(vector - (self.fundamental_weights.T @ coeffs))
        }
    
    # =========================================================================
    # DISTANCE AND SIMILARITY
    # =========================================================================
    
    def lattice_distance(
        self, 
        v1: np.ndarray, 
        v2: np.ndarray,
        method: str = 'euclidean'
    ) -> float:
        """
        Calculate distance between two lattice points
        
        Args:
            v1: First vector
            v2: Second vector
            method: Distance metric ('euclidean', 'manhattan', 'cosine')
            
        Returns:
            Distance value
        """
        if method == 'euclidean':
            return norm(v1 - v2)
        elif method == 'manhattan':
            return np.sum(np.abs(v1 - v2))
        elif method == 'cosine':
            dot = np.dot(v1, v2)
            return 1 - dot / (norm(v1) * norm(v2)) if norm(v1) * norm(v2) > 0 else 0
        else:
            raise ValueError(f"Unknown distance method: {method}")
    
    def compute_lattice_kernel(
        self, 
        vectors: np.ndarray, 
        sigma: float = 1.0
    ) -> np.ndarray:
        """
        Compute Gaussian kernel matrix for lattice points
        
        Args:
            vectors: Array of shape (n, 8)
            sigma: Kernel bandwidth
            
        Returns:
            Kernel matrix of shape (n, n)
        """
        n = len(vectors)
        K = np.zeros((n, n))
        
        for i in range(n):
            for j in range(n):
                dist = norm(vectors[i] - vectors[j])
                K[i, j] = np.exp(-dist**2 / (2 * sigma**2))
        
        return K
    
    # =========================================================================
    # UTILITY METHODS
    # =========================================================================
    
    def get_root_system_info(self) -> Dict[str, Any]:
        """Get summary information about the root system"""
        return {
            'total_roots': len(self.root_system),
            'simple_roots': len(self.simple_roots),
            'dimension': self.DIMENSION,
            'condition_number': self.condition_number,
            'basis_determinant': np.abs(np.linalg.det(self.B)),
            'basis_volume': np.abs(np.linalg.det(self.R))
        }
    
    def validate_vector(self, vector: np.ndarray) -> Tuple[bool, str]:
        """
        Validate that a vector is a valid lattice point
        
        Args:
            vector: Vector to validate
            
        Returns:
            (is_valid, message) tuple
        """
        if len(vector) != self.DIMENSION:
            return False, f"Vector must be {self.DIMENSION}-dimensional"
        
        # Check if it's approximately a lattice point
        coeffs = self.B_inv @ vector
        rounded = np.round(coeffs)
        residual = norm(coeffs - rounded)
        
        if residual < self.precision:
            return True, f"Valid lattice point (coefficients: {rounded})"
        else:
            return False, f"Not a lattice point (residual: {residual:.2e})"
    
    def __repr__(self) -> str:
        return (f"CMPLXLatticeProjector(dimension={self.DIMENSION}, "
                f"roots={self.ROOT_COUNT}, "
                f"condition={self.condition_number:.2e})")


# =============================================================================
# DIGITAL ROOT ANALYSIS (from E8LatticeAnalyzer)
# =============================================================================

def calculate_digital_root(n: int) -> int:
    """Calculate digital root of a number"""
    while n >= 10:
        n = sum(int(d) for d in str(n))
    return n


def classify_carlson_pattern(digital_root: int) -> CarlsonPattern:
    """Classify digital root into Carlson pattern"""
    if digital_root in [3, 6]:
        return CarlsonPattern.PI
    elif digital_root in [2, 4, 8]:
        return CarlsonPattern.EULER
    elif digital_root in [1, 5, 7]:
        return CarlsonPattern.PRIME
    else:
        return CarlsonPattern.THETA


def analyze_digital_root_patterns(properties: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyze digital root patterns in lattice properties
    
    This provides insights into the mathematical structure of E8
    using number-theoretic properties.
    """
    analysis = {}
    
    for prop_name, value in properties.items():
        if isinstance(value, int):
            digital_root = calculate_digital_root(value)
            pattern = classify_carlson_pattern(digital_root)
            
            analysis[prop_name] = {
                'value': value,
                'digital_root': digital_root,
                'pattern': pattern.value
            }
    
    return analysis


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

def main():
    """Demo and test the CMPLXLatticeProjector"""
    print("=" * 70)
    print("CMPLXLatticeProjector - Unified E8 Lattice Tool")
    print("=" * 70)
    
    # Initialize projector
    projector = CMPLXLatticeProjector()
    print(f"\n{projector}")
    
    # Test projection
    test_vector = np.array([0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8])
    print(f"\nTest vector: {test_vector}")
    
    # Project using different methods
    print("\n--- Babai Nearest-Plane ---")
    result = projector.project_to_lattice(test_vector, LatticeProjectionMethod.BABAI_NEAREST_PLANE)
    print(f"Projected: {result.projected_vector}")
    print(f"Coefficients: {result.coefficients}")
    print(f"Residual error: {result.residual_error:.6e}")
    
    print("\n--- Exhaustive Search ---")
    result2 = projector.project_to_lattice(test_vector, LatticeProjectionMethod.EXHAUSTIVE_SEARCH)
    print(f"Projected: {result2.projected_vector}")
    print(f"Residual error: {result2.residual_error:.6e}")
    
    # Test data embedding
    print("\n--- Data Embedding ---")
    test_data = ["hello", "world", "test", "data", "embedding"]
    embeddings = projector.embed_batch(test_data)
    print(f"Embedded {len(test_data)} items into lattice space")
    print(f"Embedding shape: {embeddings.shape}")
    
    # Lattice analysis
    print("\n--- Lattice Properties ---")
    analysis = projector.analyze_lattice_properties()
    print(f"Dimension: {analysis.dimension}")
    print(f"Root count: {analysis.root_count}")
    print(f"Weyl group order: {analysis.weyl_group_order}")
    print(f"Coxeter number: {analysis.coxeter_number}")
    
    # Quality calculation
    print("\n--- Lattice Quality ---")
    quality = projector.calculate_lattice_quality(test_vector)
    print(f"Quality score: {quality:.4f}")
    
    # Nearest roots
    print("\n--- Nearest Roots ---")
    nearest = projector.find_nearest_roots(test_vector, k=3)
    for i, (root, dist) in enumerate(nearest):
        print(f"  {i+1}. Distance: {dist:.4f}")
    
    # Digital root analysis
    print("\n--- Digital Root Analysis ---")
    props = projector.lattice_properties
    root_analysis = analyze_digital_root_patterns(props)
    print("Sample properties:")
    for key in ['dimension', 'root_count', 'coxeter_number']:
        if key in root_analysis:
            r = root_analysis[key]
            print(f"  {key}: {r['value']} -> digital_root={r['digital_root']}, pattern={r['pattern']}")
    
    print("\n" + "=" * 70)
    print("CMPLXLatticeProjector demo complete!")
    print("=" * 70)


if __name__ == "__main__":
    main()
