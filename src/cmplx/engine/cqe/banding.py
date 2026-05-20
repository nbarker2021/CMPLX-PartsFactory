"""
Validation banding — turn a weighted score into a quality band.

Verbatim semantics from `cqe_unified/validation.py`:

  - v_total = Σ wᵢ × scoreᵢ / Σ wᵢ
  - v ≥ 0.80 → BREAKTHROUGH
  - v ≥ 0.60 → PEER_READY
  - else    → EXPLORATORY

The CQE Unified Runtime's `process_text` pipeline ends here: every
input gets a single banded label based on its multi-gate scores.
"""
from __future__ import annotations

from enum import Enum


class ValidationBand(str, Enum):
    BREAKTHROUGH = "BREAKTHROUGH"
    PEER_READY = "PEER_READY"
    EXPLORATORY = "EXPLORATORY"


THRESHOLD_BREAKTHROUGH: float = 0.80
THRESHOLD_PEER_READY: float = 0.60


def compute_v_total(
    scores: dict[str, float],
    weights: dict[str, float],
) -> float:
    """Weighted mean: `Σ wᵢ × sᵢ / Σ wᵢ`. Returns 0.0 if weights sum to 0."""
    numerator = 0.0
    denominator = 0.0
    for key, weight in weights.items():
        numerator += weight * float(scores.get(key, 0.0))
        denominator += weight
    return numerator / denominator if denominator else 0.0


def band_for(v: float) -> str:
    """Map a v_total in [0, 1] to a band label."""
    if v >= THRESHOLD_BREAKTHROUGH:
        return ValidationBand.BREAKTHROUGH.value
    if v >= THRESHOLD_PEER_READY:
        return ValidationBand.PEER_READY.value
    return ValidationBand.EXPLORATORY.value


def band_enum_for(v: float) -> ValidationBand:
    """Like `band_for` but returns the enum value."""
    return ValidationBand(band_for(v))
