"""
Kernel Geometric — E8 Lattice Projection
==========================================

Projects arbitrary vectors into the E8 lattice and provides
E8-based encoding/decoding for the kernel.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger("cmplx.kernel.geometric.e8_projection")

try:
    import numpy as np
    _HAS_NUMPY = True
except ImportError:
    np = None  # type: ignore
    _HAS_NUMPY = False


def project_to_e8(vector: Any, normalize: bool = True) -> Dict:
    """
    Project a vector into the E8 lattice.

    Parameters
    ----------
    vector : array-like, shape (8,)
        Input vector to project.
    normalize : bool
        If True, normalize the vector before projection.

    Returns
    -------
    dict
        ``{"projected": list, "nearest_root": list, "distance": float}``
    """
    if not _HAS_NUMPY:
        return {"projected": vector, "nearest_root": None, "distance": None}
    try:
        from unified_families._core.geometric_engine import _build_e8_roots, e8_snap
        v = np.asarray(vector, dtype=float)
        if normalize and np.linalg.norm(v) > 0:
            v = v / np.linalg.norm(v) * np.sqrt(2)  # Scale to E8 root norm
        snapped = e8_snap(v)
        distance = float(np.linalg.norm(v - snapped))
        return {
            "projected": v.tolist(),
            "nearest_root": snapped.tolist(),
            "distance": distance,
        }
    except Exception as exc:
        logger.warning("E8 projection failed: %s", exc)
        return {"projected": list(vector), "nearest_root": None, "distance": None}


def encode_to_e8(data: Any, target_dim: int = 8) -> List[float]:
    """
    Encode arbitrary data as an E8 lattice point.

    Uses a hash-based encoding to map data to an 8-dimensional vector,
    then snaps to the nearest E8 root.
    """
    import hashlib
    raw = str(data).encode()
    h = hashlib.sha256(raw).digest()
    if _HAS_NUMPY:
        arr = np.frombuffer(h[:target_dim * 4], dtype=np.float32).astype(float)
        arr = arr[:target_dim]
        if len(arr) < target_dim:
            arr = np.pad(arr, (0, target_dim - len(arr)))
        # Normalize to E8 root norm
        norm = np.linalg.norm(arr)
        if norm > 0:
            arr = arr / norm * np.sqrt(2)
        result = project_to_e8(arr)
        return result.get("nearest_root") or arr.tolist()
    return [int(h[i]) / 255.0 for i in range(min(target_dim, len(h)))]
