"""
Pure Phi primitives — potential, ΔΦ, Landauer cost, Shannon bound,
enforcement.

Adapted verbatim from `CMPLX-1T/docker/unified/aletheia_mvp/
conservation_law.py`. Pure-stdlib (no numpy); vectors are sequences
of floats.
"""
from __future__ import annotations

import math
from typing import Sequence


# Canonical constants
COUPLING: float = 0.030076      # Matches geometry.alena.COUPLING
TOLERANCE: float = 1e-10        # ΔΦ ≤ TOLERANCE counts as conserved
BOLTZMANN_K: float = 1.380649e-23   # J/K
DEFAULT_TEMPERATURE: float = 300.0  # K


def _norm_sq(v: Sequence[float]) -> float:
    return sum(float(x) * float(x) for x in v)


def potential(vector: Sequence[float]) -> float:
    """`Φ(v) = ||v||² / 2`.

    The morphonic-field potential — lower = more stable. Used as the
    base scalar that every ΔΦ computation references.
    """
    return _norm_sq(vector) / 2.0


def delta_phi(v_before: Sequence[float], v_after: Sequence[float]) -> float:
    """`ΔΦ = Φ(after) - Φ(before)`."""
    return potential(v_after) - potential(v_before)


def shannon_bound(vector: Sequence[float]) -> float:
    """`H(v) = log₂(||v||² + 1)` bits.

    The Shannon information bound — the upper limit on bits extractable
    from this state. Used as the dI sector in `NSLSectors`.
    """
    return math.log2(_norm_sq(vector) + 1.0)


def landauer_cost(d_phi: float, temperature: float = DEFAULT_TEMPERATURE) -> float:
    """`E_cost = k_B × T × |ΔΦ|` joules.

    Landauer's principle says erasing one bit costs at least
    `k_B T ln(2)` joules. The conservation law generalizes this: any
    state change with `|ΔΦ|` units of potential change costs
    `k_B T |ΔΦ|` joules.

    When `ΔΦ < 0`, energy is released (not consumed); but the
    magnitude of the cost is the same.
    """
    return BOLTZMANN_K * temperature * abs(d_phi)


def enforce_conservation(
    v_before: Sequence[float],
    v_after: Sequence[float],
    tolerance: float = TOLERANCE,
) -> tuple[tuple[float, ...], bool]:
    """If `ΔΦ > tolerance`, scale `v_after` so `||v_after||² =
    ||v_before||²` (making `ΔΦ = 0`). Returns `(adjusted_v_after,
    was_adjusted)`.

    Edge case: if `||v_before|| = 0`, the only legal `v_after` is the
    zero vector; returns that.
    """
    d = delta_phi(v_before, v_after)
    if d <= tolerance:
        return tuple(float(x) for x in v_after), False

    sq_before = _norm_sq(v_before)
    sq_after = _norm_sq(v_after)

    if sq_before <= 0.0:
        zeros = tuple(0.0 for _ in v_after)
        return zeros, True

    if sq_after <= 0.0:
        # Already conserved at zero; nothing to scale
        return tuple(float(x) for x in v_after), False

    scale_factor = math.sqrt(sq_before / sq_after)
    adjusted = tuple(float(x) * scale_factor for x in v_after)
    return adjusted, True


def is_conserved(
    v_before: Sequence[float],
    v_after: Sequence[float],
    tolerance: float = TOLERANCE,
) -> bool:
    """`True` iff `ΔΦ ≤ tolerance`."""
    return delta_phi(v_before, v_after) <= tolerance
