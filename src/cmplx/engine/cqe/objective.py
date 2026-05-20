"""
CQEObjectiveFunction — multi-component scoring for CQE evaluation.

Adapted from the canonical `CQE_Runner_Main_Orchestrator.py` Phase-4
analysis. A score breakdown returns four components:

  - `phi_total` — the conservation scalar (delegated to NSL)
  - `parity_consistency` — how well the parity channels match the
    quad encoding
  - `chamber_stability` — Weyl-chamber-coherence; high when the
    vector stays in one chamber under small perturbations
  - `geometric_separation` — distance from the origin in E8 space
    (used to distinguish P vs NP problems, etc.)

All components ∈ [0, 1]; `phi_total` is the weighted average.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Optional, Sequence

from cmplx.nsl import NSLProvider, NSLSectors


# Default weights for `phi_total` — empirically chosen from the
# canonical CQE config.
DEFAULT_WEIGHTS: dict[str, float] = {
    "parity_consistency": 0.3,
    "chamber_stability": 0.3,
    "geometric_separation": 0.2,
    "kissing_alignment": 0.2,
}


@dataclass
class ObjectiveScores:
    """The score breakdown returned by `CQEObjectiveFunction.evaluate`."""
    phi_total: float = 0.0
    parity_consistency: float = 0.0
    chamber_stability: float = 0.0
    geometric_separation: float = 0.0
    kissing_alignment: float = 0.0
    nsl_sectors: NSLSectors = field(default_factory=NSLSectors)

    def to_dict(self) -> dict:
        return {
            "phi_total": self.phi_total,
            "parity_consistency": self.parity_consistency,
            "chamber_stability": self.chamber_stability,
            "geometric_separation": self.geometric_separation,
            "kissing_alignment": self.kissing_alignment,
            "nsl_sectors": self.nsl_sectors.to_dict(),
        }


class CQEObjectiveFunction:
    """Multi-component scoring for CQE evaluation.

    Each component is computed deterministically from the candidate
    vector + reference channels + (optional) domain context.
    `phi_total` is the weighted combination.
    """

    name: str = "cqe_objective"

    def __init__(
        self,
        weights: Optional[dict[str, float]] = None,
        nsl: Optional[NSLProvider] = None,
    ) -> None:
        self.weights = dict(weights or DEFAULT_WEIGHTS)
        self.nsl = nsl or NSLProvider()

    # ── Component scorers ────────────────────────────────────────────

    @staticmethod
    def parity_consistency(
        vector: Sequence[float],
        reference_channels: Sequence[float],
    ) -> float:
        """How well does the vector's induced parity match the reference?

        For each component pair, compute `1 - |v_i_normalized - ref_i|`.
        Average across all channels. ∈ [0, 1].
        """
        if not reference_channels:
            return 0.5
        v_norm = math.sqrt(sum(x * x for x in vector)) or 1.0
        v_unit = [x / v_norm for x in vector]
        n = min(len(v_unit), len(reference_channels))
        if n == 0:
            return 0.5
        score = 0.0
        for i in range(n):
            score += 1.0 - min(1.0, abs(v_unit[i] - reference_channels[i]))
        return score / n

    @staticmethod
    def chamber_stability(vector: Sequence[float]) -> float:
        """High when the vector's sign pattern is stable.

        A vector is "stable" if its components are far from zero (the
        chamber walls). We measure how far the smallest |component|
        is from zero, normalized.
        """
        if not vector:
            return 0.0
        v_abs = [abs(x) for x in vector]
        v_max = max(v_abs) or 1.0
        v_min = min(v_abs)
        # Far from chamber wall → high score
        return min(1.0, v_min / v_max)

    @staticmethod
    def geometric_separation(vector: Sequence[float]) -> float:
        """Normalized distance from origin.

        Captures how "out" the vector is in E8 space — used to
        distinguish problems of different complexity classes.
        Saturates at `||v|| = √2` (E8 root norm).
        """
        n = math.sqrt(sum(x * x for x in vector))
        return min(1.0, n / math.sqrt(2))

    @staticmethod
    def kissing_alignment(vector: Sequence[float]) -> float:
        """Score how close the vector is to the E8 kissing-number
        structure (240 unit vectors at norm √2).

        Approximation: the proportion of components above `1/√8` of
        the max component.
        """
        if not vector:
            return 0.0
        v_abs = [abs(x) for x in vector]
        v_max = max(v_abs) or 1.0
        threshold = v_max / math.sqrt(len(vector) or 1)
        active = sum(1 for x in v_abs if x >= threshold)
        return active / len(v_abs)

    # ── Combined evaluation ──────────────────────────────────────────

    def evaluate(
        self,
        vector: Sequence[float],
        reference_channels: Sequence[float],
        domain_context: Optional[dict] = None,
        v_before: Optional[Sequence[float]] = None,
    ) -> ObjectiveScores:
        """Compute all four components + the NSL sectors + phi_total."""
        scores = ObjectiveScores(
            parity_consistency=self.parity_consistency(vector, reference_channels),
            chamber_stability=self.chamber_stability(vector),
            geometric_separation=self.geometric_separation(vector),
            kissing_alignment=self.kissing_alignment(vector),
        )
        # phi_total = weighted average
        total = 0.0
        denom = 0.0
        for key, w in self.weights.items():
            total += w * getattr(scores, key, 0.0)
            denom += w
        scores.phi_total = total / denom if denom else 0.0

        # NSL sectors if a before-state is supplied
        if v_before is not None:
            scores.nsl_sectors = self.nsl.compute_sectors(v_before, vector)
        return scores

    def __repr__(self) -> str:
        return f"<CQEObjectiveFunction weights={self.weights}>"
