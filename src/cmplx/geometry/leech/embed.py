"""
Leech — 24-D content-addressed encoding.

The geometry-port projection here is the simple form: take 48 hex chars
(24 bytes) from the payload's sha256 and present them as a string with
a `leech::` prefix. Full Leech-lattice math (Golay-code decoding,
nearest-codeword via 3×E8 embedding) is reference material at
`_history_reference/composed_LeechLattice.py` and can be lifted in as
needed.
"""
from __future__ import annotations

import hashlib
import json
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from cmplx.morphon import Morphon


DIMENSION = 24
LEECH_PREFIX = "leech::"


def _sha256_payload(payload) -> str:
    s = json.dumps(payload, sort_keys=True, default=str)
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def leech_point_from_payload(payload) -> str:
    """Deterministic 24-byte Leech-space address for `payload`.

    Format: `leech::<48 hex chars>` (48 hex = 24 bytes).
    """
    h = _sha256_payload(payload)
    # sha256 is 64 hex chars; use chars [16, 64) = 48 hex = 24 bytes.
    return f"{LEECH_PREFIX}{h[16:64]}"


def leech_point_for(morphon: "Morphon") -> str:
    return leech_point_from_payload(morphon.payload)


class Leech:
    """Leech helper — stateless namespace for the encoding functions."""

    DIMENSION = DIMENSION
    PREFIX = LEECH_PREFIX

    @staticmethod
    def point_for(morphon: "Morphon") -> str:
        return leech_point_for(morphon)

    @staticmethod
    def point_from_payload(payload) -> str:
        return leech_point_from_payload(payload)
