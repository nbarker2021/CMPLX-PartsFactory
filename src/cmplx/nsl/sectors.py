"""
NSLSectors + NSLTriads — the 3-sector decomposition of ΔΦ and the
24-D Leech embedding of the sector vectors.

`NSLSectors` is the per-operation triple `(dN, dI, dL)` that
summarizes one state change.

`NSLTriads` is the three 8-D vectors (`noether`, `shannon`,
`landauer`) that together form a 24-D Leech-lattice vector. Sector
scores are computed by inner product with the appropriate triad —
this is the structural connection between conservation and geometry.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Sequence

from .phi import COUPLING, TOLERANCE


# ---------------------------------------------------------------------------
# NSLSectors — the 3-tuple summary
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class NSLSectors:
    """Per-operation NSL breakdown. Sum of components is ΔΦ."""

    dN: float = 0.0   # Noether sector
    dI: float = 0.0   # Information (Shannon) sector
    dL: float = 0.0   # Landauer (erasure) sector

    @property
    def total(self) -> float:
        return self.dN + self.dI + self.dL

    def is_conserved(self, tolerance: float = TOLERANCE) -> bool:
        return self.total <= tolerance

    def to_dict(self) -> dict:
        """Canonical receipt-JSON shape (matches `SNAPNslReceipts2025Q4`)."""
        return {
            "dNoether": self.dN,
            "dShannon": self.dI,
            "dLandauer": self.dL,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "NSLSectors":
        return cls(
            dN=float(d.get("dNoether", d.get("dN", 0.0))),
            dI=float(d.get("dShannon", d.get("dI", 0.0))),
            dL=float(d.get("dLandauer", d.get("dL", 0.0))),
        )

    def __add__(self, other: "NSLSectors") -> "NSLSectors":
        return NSLSectors(
            dN=self.dN + other.dN,
            dI=self.dI + other.dI,
            dL=self.dL + other.dL,
        )

    def __neg__(self) -> "NSLSectors":
        return NSLSectors(dN=-self.dN, dI=-self.dI, dL=-self.dL)


# ---------------------------------------------------------------------------
# NSLTriads — the 24-D Leech embedding of the sector vectors
# ---------------------------------------------------------------------------

TRIAD_DIM: int = 8       # Each sector triad is 8-D
LEECH_DIM: int = 24      # The three triads concatenate to 24-D


def _pad_to_dim(v: Sequence[float], dim: int) -> tuple[float, ...]:
    out = list(float(x) for x in v[:dim])
    while len(out) < dim:
        out.append(0.0)
    return tuple(out)


def _dot(a: Sequence[float], b: Sequence[float]) -> float:
    return sum(float(x) * float(y) for x, y in zip(a, b))


@dataclass
class NSLTriads:
    """Three 8-D triads that together form a 24-D Leech-lattice vector.

    The structural identity:
        Leech₂₄ ⊃ (Noether₈, Shannon₈, Landauer₈)

    Sector scores are computed by inner product with the corresponding
    triad. Hebbian updates learn the triads from rewarded experience.
    """

    noether: list[float] = field(default_factory=lambda: [0.0] * TRIAD_DIM)
    shannon: list[float] = field(default_factory=lambda: [0.0] * TRIAD_DIM)
    landauer: list[float] = field(default_factory=lambda: [0.0] * TRIAD_DIM)

    def __post_init__(self) -> None:
        self.noether = list(_pad_to_dim(self.noether, TRIAD_DIM))
        self.shannon = list(_pad_to_dim(self.shannon, TRIAD_DIM))
        self.landauer = list(_pad_to_dim(self.landauer, TRIAD_DIM))

    # ── Leech embedding ──────────────────────────────────────────────

    @property
    def as_leech_vector(self) -> tuple[float, ...]:
        """Concatenate (noether, shannon, landauer) into a single 24-tuple."""
        return tuple(self.noether) + tuple(self.shannon) + tuple(self.landauer)

    @classmethod
    def from_leech_vector(cls, v24: Sequence[float]) -> "NSLTriads":
        """Inverse: split a 24-D vector into the three sector triads."""
        v = _pad_to_dim(v24, LEECH_DIM)
        return cls(
            noether=list(v[0:TRIAD_DIM]),
            shannon=list(v[TRIAD_DIM:2 * TRIAD_DIM]),
            landauer=list(v[2 * TRIAD_DIM:LEECH_DIM]),
        )

    # ── Scoring ──────────────────────────────────────────────────────

    def score(self, x8: Sequence[float]) -> NSLSectors:
        """Compute `(dN, dI, dL)` as inner products of each triad with `x8`."""
        x = _pad_to_dim(x8, TRIAD_DIM)
        return NSLSectors(
            dN=_dot(self.noether, x),
            dI=_dot(self.shannon, x),
            dL=_dot(self.landauer, x),
        )

    # ── Hebbian learning ─────────────────────────────────────────────

    def hebbian_update(
        self,
        x8: Sequence[float],
        reward: float,
        lr: float = COUPLING,
    ) -> "NSLTriads":
        """Update the triads from rewarded experience.

        - `noether`: rewards negative ΔΦ (conservation-aligned)
        - `shannon`: proportional to |reward| (entropy magnitude)
        - `landauer`: pays a COUPLING-scaled erasure cost

        Mutates in place and returns self for chaining. Exact form
        from `CMPLX-TMN-main/src/personal_node/personal_node.py:243-247`.
        """
        x = _pad_to_dim(x8, TRIAD_DIM)
        effective_lr = lr * abs(reward)
        noether_sign = +1.0 if reward < 0 else -1.0
        for i in range(TRIAD_DIM):
            self.noether[i] += effective_lr * x[i] * noether_sign
            self.shannon[i] += effective_lr * x[i] * abs(reward)
            self.landauer[i] -= lr * x[i] * COUPLING
        return self

    def to_dict(self) -> dict:
        return {
            "noether": list(self.noether),
            "shannon": list(self.shannon),
            "landauer": list(self.landauer),
        }

    def __repr__(self) -> str:
        from math import sqrt
        norm = sqrt(sum(x * x for x in self.as_leech_vector))
        return f"<NSLTriads leech_norm={norm:.4f}>"
