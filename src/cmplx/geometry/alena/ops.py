"""
ALENA — projection primitives for the unified system.

The geometric math layer that carriers, routing, and engine
components share. Adapted from the historical CQE-GVS ALENAOps
(60 file replicas in the index, sourced from
`history/cmplx_pending/...` and the GVS source files at
`history/gvs_source_files/`).

This implementation is hand-built from the spec in INTERFACE.md
and stays pure-stdlib for the operations that don't strictly need
numpy. The history reference (`_history_reference/`) preserves the
original numpy-heavy form for callers that want it.
"""
from __future__ import annotations

import math
from typing import Iterable, Optional, Sequence

from cmplx.geometry.e8 import e8_roots, nearest_root, DIMENSION


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

COUPLING = 0.03
PHI = (1 + math.sqrt(5)) / 2
E8_NORM = math.sqrt(2)


# ---------------------------------------------------------------------------
# Module-level helpers
# ---------------------------------------------------------------------------

def fibonacci_radii(n_low: int = -10, n_high: int = 10) -> list[float]:
    """Golden-spiral radii: φ^n × COUPLING for n in [n_low, n_high].

    The Fibonacci lattice — radius levels used by r_theta_snap.
    Returns a sorted, ascending list.
    """
    radii = [PHI ** n * COUPLING for n in range(n_low, n_high + 1)]
    radii.sort()
    return radii


def _l2_norm(v: Sequence[float]) -> float:
    return math.sqrt(sum(x * x for x in v))


def _normalize(v: Sequence[float], target_norm: float = E8_NORM) -> tuple[float, ...]:
    n = _l2_norm(v)
    if n == 0:
        return tuple(v)
    return tuple(x / n * target_norm for x in v)


def _vec(v: Sequence[float]) -> tuple[float, ...]:
    """Coerce to a tuple of floats (immutable, hashable, lightweight)."""
    return tuple(float(x) for x in v)


# ---------------------------------------------------------------------------
# The operator object
# ---------------------------------------------------------------------------

class ALENA:
    """Projection primitives. Stateless aside from a cached fibonacci-radius
    sequence and the E8 root system (which is also globally cached).

    >>> alena = ALENA()
    >>> snapped = alena.r_theta_snap((0.5, 0.5, 0, 0, 0, 0, 0, 0))
    """

    def __init__(self, fib_n_low: int = -10, fib_n_high: int = 10) -> None:
        self._fib_radii = fibonacci_radii(fib_n_low, fib_n_high)

    # ------------------------------------------------------------------
    # r_theta_snap — Fibonacci-radius snap
    # ------------------------------------------------------------------

    def r_theta_snap(self, vector: Sequence[float]) -> tuple[float, ...]:
        """Snap to nearest Fibonacci-radius point on the golden spiral.

        Preserves direction (unit-vector) and snaps magnitude to one of
        the radii in `fibonacci_radii()`. Zero vector returns unchanged.
        """
        v = _vec(vector)
        r = _l2_norm(v)
        if r == 0:
            return v
        nearest_r = min(self._fib_radii, key=lambda x: abs(x - r))
        scale = nearest_r / r
        return tuple(x * scale for x in v)

    # ------------------------------------------------------------------
    # weyl_flip — chamber-boundary reflection
    # ------------------------------------------------------------------

    def weyl_flip(self, vector: Sequence[float]) -> tuple[float, ...]:
        """Reflect across the hyperplane normal of the vector's nearest
        E8 root direction. Returns the reflected vector, re-normalized
        to E8_NORM if non-zero.

        This is a Weyl reflection on the lattice: any state with a
        positive projection onto a root direction gets mirrored to the
        negative side.
        """
        v = _vec(vector)
        if len(v) != DIMENSION:
            raise ValueError(f"expected {DIMENSION}-D vector, got {len(v)}-D")
        # Find nearest root direction; use it as the hyperplane normal.
        root = nearest_root(v)
        root_norm_sq = sum(x * x for x in root)
        if root_norm_sq == 0:
            return v
        dot = sum(a * b for a, b in zip(v, root))
        scale = 2 * dot / root_norm_sq
        reflected = tuple(a - scale * b for a, b in zip(v, root))
        # Re-normalize to the E8 manifold
        return _normalize(reflected)

    # ------------------------------------------------------------------
    # midpoint_ecc — error-correcting midpoint
    # ------------------------------------------------------------------

    def midpoint_ecc(
        self, v1: Sequence[float], v2: Sequence[float]
    ) -> tuple[float, ...]:
        """Midpoint of v1 and v2, then snapped to the nearest E8 root
        (the closest valid codeword)."""
        a = _vec(v1)
        b = _vec(v2)
        if len(a) != len(b):
            raise ValueError("v1 and v2 must have the same length")
        mid = tuple((x + y) / 2 for x, y in zip(a, b))
        if len(mid) != DIMENSION:
            # Not an 8-D vector — can't snap to E8; just return midpoint
            return mid
        return nearest_root(mid)

    # ------------------------------------------------------------------
    # project_curvature — E8 face → R^7 stereographic + curvature in 8th
    # ------------------------------------------------------------------

    def project_curvature(
        self, vector: Sequence[float], face_angle: float = 0.0
    ) -> tuple[float, ...]:
        """Stereographic projection from the E8 north pole to R^7, with
        the projection magnitude embedded as a curvature measure in the
        8th coordinate.

        Useful for transmitting "this state lives on a curved manifold"
        through a flat carrier — the curvature is preserved as metadata.
        """
        v = _vec(vector)
        if len(v) != DIMENSION:
            raise ValueError(f"expected {DIMENSION}-D vector, got {len(v)}-D")

        # Apply face rotation: rotate in 4 orthogonal planes by angles
        # scaled by powers of PHI (the golden spiral cascade).
        rotated = self._face_rotation(v, face_angle)

        # Stereographic projection from north pole (rotated[7] = 1)
        if abs(rotated[7] - 1.0) < 1e-9:
            projected = rotated[:7]
        else:
            scale = 1.0 / (1.0 - rotated[7])
            projected = tuple(x * scale for x in rotated[:7])

        # Embed back with the curvature in the 8th coord
        projected_norm = _l2_norm(projected)
        curved = (*projected, projected_norm * COUPLING)
        return _normalize(curved)

    @staticmethod
    def _rotate_2plane(
        v: tuple[float, ...], axis1: int, axis2: int, angle: float
    ) -> tuple[float, ...]:
        """Rotate `v` in the (axis1, axis2) plane by `angle` radians."""
        cos_a = math.cos(angle)
        sin_a = math.sin(angle)
        x = v[axis1]
        y = v[axis2]
        out = list(v)
        out[axis1] = cos_a * x - sin_a * y
        out[axis2] = sin_a * x + cos_a * y
        return tuple(out)

    def _face_rotation(
        self, vector: tuple[float, ...], angle: float
    ) -> tuple[float, ...]:
        """Rotate in 4 orthogonal planes (the "face" of E8), with each
        plane's angle scaled by a power of PHI."""
        v = vector
        v = self._rotate_2plane(v, 0, 1, angle)
        v = self._rotate_2plane(v, 2, 3, angle * PHI)
        v = self._rotate_2plane(v, 4, 5, angle * PHI ** 2)
        v = self._rotate_2plane(v, 6, 7, angle * PHI ** 3)
        return _normalize(v)

    # ------------------------------------------------------------------
    # project_to_channels — the 3/6/9 projection encoder pattern
    # ------------------------------------------------------------------

    def project_to_channels(
        self,
        vector: Sequence[float],
        channels: tuple[int, ...] = (3, 6, 9),
    ) -> tuple[float, ...]:
        """Snap a vector's polar coordinate into one of the named
        digital-root channels.

        For each component beyond the first two (3-D and up), reduce
        modulo the channel value. This is the original "projection
        channels" pattern in the historical ALENAOps. With channels
        (3, 6, 9) it produces the MID/HIGH-triad CRT rails the GVS
        used for pixel encoding.

        Returns a vector of the same length, with components shaped to
        the channel grid.
        """
        v = _vec(vector)
        if not channels:
            raise ValueError("channels must be non-empty")
        out = []
        for i, comp in enumerate(v):
            ch = channels[i % len(channels)]
            # Modulo into [0, ch); keep sign convention with the original
            mod_val = abs(comp) % ch
            sign = -1.0 if comp < 0 else 1.0
            out.append(sign * mod_val)
        return tuple(out)
