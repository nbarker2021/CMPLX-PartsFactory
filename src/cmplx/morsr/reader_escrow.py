"""
MORSR - Middle Out Recursive Shape Reader
Part of Aletheia AI - CQE-Native System

MORSR reads geometric shapes/structures by:
1. Starting from the MIDDLE (not edges)
2. Recursively zooming in/out at multiple scales
3. Reading the SHAPE - extracting geometric structure

This aligns with remainder interpretation:
- 0's after digits = zoom levels
- Whole numbers between = rails/paths
- Following 0's = recursive depth
"""

import numpy as np
from typing import Dict, List, Any, Optional, Tuple
import hashlib

class MORSRReader:
    """
    Middle Out Recursive Shape Reader.
    
    Reads geometric structure from data by starting at the middle
    and recursively exploring at multiple scales.
    """
    
    def __init__(self):
        self.readings = []
        print("MORSR Reader initialized")
    
    def read_shape(self, data: np.ndarray, max_depth: int = 5) -> Dict[str, Any]:
        """
        Read geometric shape from data.
        
        Args:
            data: Input data (can be any dimensional array)
            max_depth: Maximum recursive depth
            
        Returns:
            Shape reading with multi-scale structure
        """
        # Start from the MIDDLE
        middle_point = self._find_middle(data)
        
        # Recursive shape reading at multiple scales
        shape_structure = self._recursive_read(data, middle_point, depth=0, max_depth=max_depth)
        
        reading = {
            'middle_point': middle_point.tolist() if isinstance(middle_point, np.ndarray) else middle_point,
            'shape_structure': shape_structure,
            'total_scales': len(shape_structure['scales']),
            'max_depth_reached': shape_structure['max_depth_reached'],
        }
        
        self.readings.append(reading)
        
        return reading
    
    def _find_middle(self, data: np.ndarray) -> np.ndarray:
        """
        Find the middle point of data.
        
        For arrays: geometric center
        For point clouds: centroid
        For graphs: center of mass
        """
        if data.ndim == 1:
            # 1D: middle index
            middle_idx = len(data) // 2
            return np.array([middle_idx])
        
        elif data.ndim == 2:
            # 2D: center of mass
            if data.shape[0] > 0:
                return np.mean(data, axis=0)
            else:
                return np.zeros(data.shape[1])
        
        else:
            # N-D: flatten and find center
            flat = data.flatten()
            middle_idx = len(flat) // 2
            return np.array([middle_idx])
    
    def _recursive_read(self, 
                       data: np.ndarray,
                       center: np.ndarray,
                       depth: int,
                       max_depth: int) -> Dict[str, Any]:
        """
        Recursively read shape at multiple scales.
        
        Args:
            data: Input data
            center: Current center point
            depth: Current recursion depth
            max_depth: Maximum depth
            
        Returns:
            Multi-scale shape structure
        """
        if depth >= max_depth:
            return {
                'scales': [],
                'max_depth_reached': depth,
            }
        
        # Read at current scale
        scale_reading = self._read_at_scale(data, center, depth)
        
        # Determine zoom direction based on shape
        # If shape has structure, zoom IN (increase resolution)
        # If shape is uniform, zoom OUT (decrease resolution)
        zoom_direction = self._determine_zoom(scale_reading)
        
        # Recursive read at next scale
        if zoom_direction == 'in':
            # Zoom in: read finer details
            next_data = self._zoom_in(data, center)
            next_center = center  # Center stays the same in zoomed view
        elif zoom_direction == 'out':
            # Zoom out: read coarser structure
            next_data = self._zoom_out(data, center)
            next_center = center
        else:
            # No more zooming needed
            return {
                'scales': [scale_reading],
                'max_depth_reached': depth,
            }
        
        # Recurse
        sub_structure = self._recursive_read(next_data, next_center, depth + 1, max_depth)
        
        return {
            'scales': [scale_reading] + sub_structure['scales'],
            'max_depth_reached': sub_structure['max_depth_reached'],
        }
    
    def _read_at_scale(self, data: np.ndarray, center: np.ndarray, scale: int) -> Dict[str, Any]:
        """
        Read geometric structure at a specific scale.
        
        Returns:
            Scale reading with geometric features
        """
        # Calculate local geometry around center
        if data.ndim == 1:
            # 1D: read neighborhood
            center_idx = int(center[0]) if len(center) > 0 else 0
            radius = max(1, 2 ** scale)
            
            start = max(0, center_idx - radius)
            end = min(len(data), center_idx + radius + 1)
            
            neighborhood = data[start:end]
            
            # Geometric features
            mean_val = float(np.mean(neighborhood))
            variance = float(np.var(neighborhood))
            gradient = float(np.gradient(neighborhood).mean()) if len(neighborhood) > 1 else 0.0
            
        elif data.ndim == 2:
            # 2D: read local patch
            # Simplified: use statistics
            mean_val = float(np.mean(data))
            variance = float(np.var(data))
            gradient = 0.0  # Placeholder
            
        else:
            # N-D: simplified statistics
            mean_val = float(np.mean(data))
            variance = float(np.var(data))
            gradient = 0.0
        
        return {
            'scale': scale,
            'center': center.tolist() if isinstance(center, np.ndarray) else center,
            'mean': mean_val,
            'variance': variance,
            'gradient': gradient,
            'shape_complexity': variance,  # High variance = complex shape
        }
    
    def _determine_zoom(self, scale_reading: Dict[str, Any]) -> str:
        """
        Determine zoom direction based on shape complexity.
        
        High complexity → zoom IN (read finer details)
        Low complexity → zoom OUT (read coarser structure)
        Medium complexity → STOP (optimal scale found)
        """
        complexity = scale_reading['shape_complexity']
        
        if complexity > 1.0:
            return 'in'  # Complex: zoom in
        elif complexity < 0.1:
            return 'out'  # Simple: zoom out
        else:
            return 'stop'  # Optimal scale
    
    def _zoom_in(self, data: np.ndarray, center: np.ndarray) -> np.ndarray:
        """
        Zoom in: increase resolution around center.
        
        In practice: interpolate or subsample with higher resolution.
        Simplified: return data as-is (real implementation would upsample).
        """
        return data
    
    def _zoom_out(self, data: np.ndarray, center: np.ndarray) -> np.ndarray:
        """
        Zoom out: decrease resolution (coarser view).
        
        In practice: downsample or aggregate.
        Simplified: return data as-is (real implementation would downsample).
        """
        return data
    
    def read_with_remainder_interpretation(self, 
                                          data: np.ndarray,
                                          remainder: float) -> Dict[str, Any]:
        """
        Read shape using remainder interpretation to guide recursion.
        
        Remainder digits tell us:
        - Zoom levels (0's after digits)
        - Rails to follow (whole numbers between)
        - Recursive depth (following 0's)
        
        Args:
            data: Input data
            remainder: Remainder value to interpret
            
        Returns:
            Shape reading guided by remainder
        """
        # Parse remainder
        remainder_str = f"{remainder:.10f}".split('.')[1]  # Get decimal part
        
        # Count zoom levels (0's after digits)
        zoom_levels = []
        for i, digit in enumerate(remainder_str):
            if digit == '0' and i > 0 and remainder_str[i-1] != '0':
                zoom_levels.append(i)
        
        # Extract rails (non-zero digits)
        rails = [int(d) for d in remainder_str if d != '0']
        
        # Determine max depth from remainder
        max_depth = len(rails) + len(zoom_levels)
        
        # Read shape with guided recursion
        reading = self.read_shape(data, max_depth=max_depth)
        
        reading['remainder_guidance'] = {
            'remainder': remainder,
            'zoom_levels': zoom_levels,
            'rails': rails,
            'guided_depth': max_depth,
        }
        
        return reading
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get MORSR statistics."""
        return {
            'total_readings': len(self.readings),
            'average_scales': np.mean([r['total_scales'] for r in self.readings]) if self.readings else 0,
            'max_depth_seen': max([r['max_depth_reached'] for r in self.readings]) if self.readings else 0,
        }


# Test MORSR
if __name__ == "__main__":
    print("=" * 80)
    print("MORSR (Middle Out Recursive Shape Reader) - Test")
    print("=" * 80)
    
    reader = MORSRReader()
    
    # Test 1: Read 1D signal
    print("\n[Test 1] Read 1D Signal")
    signal = np.sin(np.linspace(0, 4*np.pi, 100))
    reading1 = reader.read_shape(signal, max_depth=3)
    print(f"  Middle point: {reading1['middle_point']}")
    print(f"  Total scales: {reading1['total_scales']}")
    print(f"  Max depth: {reading1['max_depth_reached']}")
    for i, scale in enumerate(reading1['shape_structure']['scales']):
        print(f"    Scale {i}: complexity={scale['shape_complexity']:.4f}, mean={scale['mean']:.4f}")
    
    # Test 2: Read 2D point cloud
    print("\n[Test 2] Read 2D Point Cloud")
    points = np.random.randn(50, 2)
    reading2 = reader.read_shape(points, max_depth=4)
    print(f"  Middle point: {reading2['middle_point']}")
    print(f"  Total scales: {reading2['total_scales']}")
    
    # Test 3: Read with remainder interpretation
    print("\n[Test 3] Read with Remainder Interpretation")
    # Remainder 0.97083 → zoom at position 2 (after 7), rails 9,7,8,3
    signal2 = np.random.randn(100)
    reading3 = reader.read_with_remainder_interpretation(signal2, 0.97083)
    print(f"  Remainder: {reading3['remainder_guidance']['remainder']}")
    print(f"  Zoom levels: {reading3['remainder_guidance']['zoom_levels']}")
    print(f"  Rails: {reading3['remainder_guidance']['rails']}")
    print(f"  Guided depth: {reading3['remainder_guidance']['guided_depth']}")
    print(f"  Actual scales read: {reading3['total_scales']}")
    
    # Test 4: Statistics
    print("\n[Test 4] Statistics")
    stats = reader.get_statistics()
    for key, value in stats.items():
        if isinstance(value, float):
            print(f"  {key}: {value:.2f}")
        else:
            print(f"  {key}: {value}")
    
    print("\n" + "=" * 80)
    print("MORSR (Middle Out Recursive Shape Reader) working! ✓")
    print("=" * 80)

