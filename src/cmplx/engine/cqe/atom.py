"""
CQEAtom — the CQE-flavor view of a Morphon.

Per user clarification: CQE was the pre-CMPLX identity tag of every
system; CQEAtom IS a Morphon, just with its CQE-specific fields
populated. This module provides:

  - `CQEAtom` — a builder/decorator that takes a Morphon and ensures
    its `quad_encoding`, `parity_channels`, `sacred_frequency`,
    `digital_root`, and `fractal_coordinate` are populated.
  - `CQEAtomBuilder.forge(data, ...)` — construct a new Morphon
    pre-populated with all the CQE fields.

The 4-tuple `quad_encoding` is the canonical CQE primitive: each
component is 1..4. Parity channels are 8 bits derived from the quad.
Sacred frequency is from `toroidal.sacred_frequency(text)`. Digital
root is the conventional 1..9 reduction. Fractal coordinate comes
from `mandelbrot.hash_to_complex(text)`.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Any, Optional

from cmplx.morphon import Morphon

from .mandelbrot import hash_to_complex
from .toroidal import sacred_frequency


# ---------------------------------------------------------------------------
# Quad encoding (4-tuple of 1..4 values)
# ---------------------------------------------------------------------------

def quad_from_text(text: str) -> tuple[int, int, int, int]:
    """SHA256 prefix → 4 ints in [1, 4]. Deterministic per text."""
    h = hashlib.sha256(text.encode("utf-8")).digest()
    return tuple(((b % 4) + 1) for b in h[:4])  # type: ignore[return-value]


def quad_from_payload(payload: Any) -> tuple[int, int, int, int]:
    """Stable quad encoding from any JSON-serializable payload."""
    import json
    s = json.dumps(payload, sort_keys=True, default=str)
    return quad_from_text(s)


# ---------------------------------------------------------------------------
# Parity channels (8 bits from quad encoding)
# ---------------------------------------------------------------------------

def parity_from_quad(quad: tuple[int, int, int, int]) -> tuple[int, ...]:
    """Compute 8 parity channels from the 4-tuple quad encoding.

    Same formula as `cqe_governance._validate_parity_consistency`:
        [q1%2, q2%2, q3%2, q4%2,
         (q1+q2)%2, (q3+q4)%2,
         (q1+q3)%2, (q2+q4)%2]
    """
    q1, q2, q3, q4 = quad
    return (
        q1 % 2, q2 % 2, q3 % 2, q4 % 2,
        (q1 + q2) % 2, (q3 + q4) % 2,
        (q1 + q3) % 2, (q2 + q4) % 2,
    )


# ---------------------------------------------------------------------------
# Digital root (1..9)
# ---------------------------------------------------------------------------

def digital_root_of_quad(quad: tuple[int, int, int, int]) -> int:
    """Reduce sum-of-quad to a single digit 1..9 (the canonical DR rule)."""
    total = sum(quad)
    while total >= 10:
        total = sum(int(d) for d in str(total))
    return total if total > 0 else 9


# ---------------------------------------------------------------------------
# CQEAtom — the Morphon view with CQE fields populated
# ---------------------------------------------------------------------------

class CQEAtom:
    """A view onto a Morphon that ensures CQE-specific fields are set.

    `CQEAtom(morphon)` wraps an existing morphon and computes any
    missing CQE fields. `CQEAtom.forge(...)` constructs a fresh
    morphon with everything pre-populated. Either way, the underlying
    state is a Morphon (per user direction: CQEAtom IS a Morphon).
    """

    def __init__(self, morphon: Morphon, source_text: Optional[str] = None) -> None:
        self.morphon = morphon
        self._source_text = source_text or self._derive_source(morphon)
        self._populate_fields()

    @staticmethod
    def _derive_source(morphon: Morphon) -> str:
        """Best-effort source-text derivation from a morphon's payload."""
        import json
        if isinstance(morphon.payload, dict) and "text" in morphon.payload:
            return str(morphon.payload["text"])
        return json.dumps(morphon.payload, sort_keys=True, default=str)

    def _populate_fields(self) -> None:
        """Fill in any CQE fields that aren't yet set on the morphon."""
        m = self.morphon
        if m.quad_encoding is None:
            m.quad_encoding = quad_from_text(self._source_text)
        if m.parity_channels is None and m.quad_encoding is not None:
            m.parity_channels = parity_from_quad(m.quad_encoding)
        if m.digital_root is None and m.quad_encoding is not None:
            m.digital_root = digital_root_of_quad(m.quad_encoding)
        if m.sacred_frequency is None:
            m.sacred_frequency = sacred_frequency(self._source_text)
        if m.fractal_coordinate is None:
            cr, ci = hash_to_complex(self._source_text)
            m.fractal_coordinate = complex(cr, ci)

    # ── Convenience accessors ────────────────────────────────────────

    @property
    def id(self) -> str:
        return self.morphon.id

    @property
    def quad_encoding(self) -> tuple[int, int, int, int]:
        return self.morphon.quad_encoding  # type: ignore[return-value]

    @property
    def parity_channels(self) -> tuple[int, ...]:
        return self.morphon.parity_channels  # type: ignore[return-value]

    @property
    def digital_root(self) -> int:
        return self.morphon.digital_root  # type: ignore[return-value]

    @property
    def sacred_frequency(self) -> float:
        return self.morphon.sacred_frequency  # type: ignore[return-value]

    @property
    def fractal_coordinate(self) -> complex:
        return self.morphon.fractal_coordinate  # type: ignore[return-value]

    # ── Construction ──────────────────────────────────────────────────

    @classmethod
    def forge(
        cls,
        payload: Any,
        *,
        source_text: Optional[str] = None,
        parent: Optional[str] = None,
        morphon_id: Optional[str] = None,
    ) -> "CQEAtom":
        """Build a fresh Morphon with all CQE fields pre-populated.

        If `payload` is a string, it's used as the source_text and
        wrapped in a `{"text": payload}` dict for the morphon. If it's
        a dict, used directly.
        """
        if isinstance(payload, str):
            if source_text is None:
                source_text = payload
            payload = {"text": payload}
        m = Morphon.forge(payload=payload, parent=parent, morphon_id=morphon_id)
        return cls(m, source_text=source_text)

    def to_dict(self) -> dict:
        """JSON-friendly view of all CQE fields + morphon id."""
        return {
            "id": self.id,
            "quad_encoding": list(self.quad_encoding),
            "parity_channels": list(self.parity_channels),
            "digital_root": self.digital_root,
            "sacred_frequency": self.sacred_frequency,
            "fractal_coordinate": {
                "real": self.fractal_coordinate.real,
                "imag": self.fractal_coordinate.imag,
            },
        }

    def __repr__(self) -> str:
        return (
            f"<CQEAtom morphon={self.id[:8]} "
            f"quad={self.quad_encoding} dr={self.digital_root}>"
        )
