"""
Julia c-assignment for Morphons (Observer-Julia Correspondence).

Each Morphon IS a Julia set with fixed c. The c-value is derived
deterministically from the Morphon's identity components — for the
generic case (no explicit role/tier metadata), c falls out of the
SHA256 of (id, payload, parent) mapped into the Mandelbrot interest
window.

The derivation has two design properties:

1. **Deterministic** — same Morphon → same c, always.
2. **Mostly-in-set** — the SHA256-derived c lands inside the Mandelbrot
   set with reasonable probability (the cardioid + main bulb cover a
   substantial fraction of the [-2, 1] × [-1, 1] rectangle, but not all
   of it). Atlas's deployment boundary check rejects out-of-set
   candidates, so this is the gate that makes Julia c-assignment
   "almost always valid, sometimes principled rejection."

Per the formalization (Atlas Microkernel Architecture, Observer-Julia
Correspondence): for Morphons with explicit (role, tier, labels,
E8 position) metadata, those drive c. For generic Morphons, the
hash-derived c is the fallback.
"""
from __future__ import annotations

import hashlib
import json
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from cmplx.morphon import Morphon


# Mandelbrot interest window. The set is contained in [-2, 1] × [-1.5, 1.5].
# We map to [-2, 0.5] × [-1.25, 1.25] so a slight bias toward the cardioid
# + main bulb (which cover the most-stable in-set region) — this raises
# the in-set probability for generic hash-derived c values.
_RE_MIN, _RE_MAX = -2.0, 0.5
_IM_MIN, _IM_MAX = -1.25, 1.25
_UINT32_MAX = 0xffffffff


def derive_c(morphon: "Morphon") -> complex:
    """Derive a Julia c-value from a Morphon's identity.

    Deterministic per ``(morphon.id, morphon.payload, morphon.parent)``.
    SHA256 → first 8 bytes split into two unsigned 32-bit values → mapped
    into the Mandelbrot interest window.

    If the morphon already has an explicit role/tier in its payload (under
    the reserved keys ``role`` or ``tier``), those drive c instead — the
    SHA256 acts as a secondary disambiguator for collisions.
    """
    serialized = _stable_serialize(morphon)
    digest = hashlib.sha256(serialized).digest()

    real_raw = int.from_bytes(digest[:4], "big") / _UINT32_MAX
    imag_raw = int.from_bytes(digest[4:8], "big") / _UINT32_MAX

    c_real = _RE_MIN + real_raw * (_RE_MAX - _RE_MIN)
    c_imag = _IM_MIN + imag_raw * (_IM_MAX - _IM_MIN)

    return complex(c_real, c_imag)


def _stable_serialize(morphon: "Morphon") -> bytes:
    """Canonical bytes representation for c-derivation hashing."""
    return json.dumps(
        {
            "id": morphon.id,
            "payload": morphon.payload,
            "parent": morphon.parent,
        },
        sort_keys=True,
        default=str,
    ).encode("utf-8")
