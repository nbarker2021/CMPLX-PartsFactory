"""
Toroidal sacred geometry primitives.

Adapted from `cqe_unified/toroidal.py`. Generates points on a torus
surface and classifies them by rotation-pattern signature. Used by
the CQE runtime's `toroidal` stage to compute a shell of geometric
samples with pattern statistics.

Concept: the morphonic field's gravitational/EM/weak/strong analogs
correspond to the 4 toroidal rotation modes (poloidal, toroidal,
meridional, helical). This module produces the basic shell and
pattern tally — the GVS / WorldForge work elsewhere consumes it.
"""
from __future__ import annotations

import hashlib
import math
import random
from typing import Optional


# Canonical pattern labels (4 toroidal rotation modes)
ROTATION_PATTERNS: tuple[str, ...] = (
    "poloidal",     # Through the donut hole (EM analog)
    "toroidal",     # Around the donut (Weak analog)
    "meridional",   # Surface latitude (Strong analog)
    "helical",      # Spiral combination (Gravity analog)
)


def torus_point(
    u: float,
    v: float,
    R: float = 2.0,
    r: float = 1.0,
) -> tuple[float, float, float]:
    """Standard torus parameterization: (u, v) ∈ [0, 2π]² → (x, y, z)."""
    x = (R + r * math.cos(v)) * math.cos(u)
    y = (R + r * math.cos(v)) * math.sin(u)
    z = r * math.sin(v)
    return x, y, z


def _classify_point(u: float, v: float) -> str:
    """Choose a rotation-pattern label based on (u, v) angle signature.

    Quadrant-style classification — the canonical form just buckets
    points into the four pattern names with a simple modulus rule.
    """
    # Normalize to [0, 1)
    u_n = (u / (2 * math.pi)) % 1.0
    v_n = (v / (2 * math.pi)) % 1.0
    # 4-quadrant pattern
    if u_n < 0.5 and v_n < 0.5:
        return "poloidal"
    if u_n < 0.5 and v_n >= 0.5:
        return "toroidal"
    if u_n >= 0.5 and v_n < 0.5:
        return "meridional"
    return "helical"


def generate_toroidal_shell(
    n_points: int = 64,
    seed: Optional[int] = None,
    R: float = 2.0,
    r: float = 1.0,
) -> list[dict]:
    """Generate `n_points` on a torus surface with pattern labels.

    Deterministic when `seed` is provided. Each point has:
      - `u, v`: parameter pair
      - `position`: (x, y, z) tuple
      - `pattern`: one of `ROTATION_PATTERNS`
      - `radius_ratio`: `r / R` (constant across the shell)
    """
    rng = random.Random(seed)
    points: list[dict] = []
    for _ in range(n_points):
        u = rng.uniform(0.0, 2 * math.pi)
        v = rng.uniform(0.0, 2 * math.pi)
        x, y, z = torus_point(u, v, R, r)
        points.append({
            "u": u,
            "v": v,
            "position": (x, y, z),
            "pattern": _classify_point(u, v),
            "radius_ratio": r / R if R > 0 else 0.0,
        })
    return points


def pattern_distribution(shell: list[dict]) -> dict[str, int]:
    """Count occurrences of each rotation pattern in a shell."""
    counts: dict[str, int] = {p: 0 for p in ROTATION_PATTERNS}
    for point in shell:
        pat = point.get("pattern")
        if pat in counts:
            counts[pat] += 1
    return counts


def pattern_balance(shell: list[dict]) -> float:
    """Score how balanced the pattern distribution is (1.0 = perfectly
    balanced across all 4 patterns; 0.0 = concentrated in one pattern).

    Returns `1 - normalized_variance` of the counts.
    """
    counts = pattern_distribution(shell)
    total = sum(counts.values()) or 1
    mean = total / len(ROTATION_PATTERNS)
    variance = sum((c - mean) ** 2 for c in counts.values()) / len(ROTATION_PATTERNS)
    # Normalize against max possible variance (all in one bucket)
    max_var = (total - mean) ** 2 / len(ROTATION_PATTERNS) + 3 * (mean ** 2) / len(ROTATION_PATTERNS)
    if max_var <= 0:
        return 1.0
    return max(0.0, 1.0 - variance / max_var)


def sacred_frequency(text: str) -> float:
    """Deterministic sacred-frequency assignment from a string.

    The CQE system associates each datum with a frequency drawn from
    the "solfeggio" range (174-963 Hz). Encoded via SHA256 prefix.
    """
    h = hashlib.sha256(text.encode("utf-8")).digest()
    raw = int.from_bytes(h[:4], "big") / (2 ** 32)
    return 174.0 + raw * (963.0 - 174.0)
