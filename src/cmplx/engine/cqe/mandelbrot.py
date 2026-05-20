"""
Mandelbrot fractal primitives — `|z|≤2` path validity check.

Adapted from `cqe_unified/fractal_mandelbrot.py`. Used by the CQE
runtime to classify a string's "fractal behavior": does its
hash-derived complex coordinate live inside the Mandelbrot set
(`|z|` stays bounded under iteration) or escape?

The conservation tie: NSL's ΔΦ ≤ 0 has a geometric analog in the
Mandelbrot set — lawful paths correspond to bounded iterations
(`|z|≤2`); unlawful paths escape. The runtime emits both metrics so
analysts can correlate.
"""
from __future__ import annotations

import hashlib
from typing import Optional


MAX_ITER_DEFAULT: int = 50
ESCAPE_RADIUS: float = 2.0
ESCAPE_RADIUS_SQ: float = 4.0


def mandelbrot_iterate(
    c_real: float,
    c_imag: float,
    max_iter: int = MAX_ITER_DEFAULT,
) -> dict:
    """Iterate `z := z² + c` starting from `z = 0`. Return escape status.

    Returns a dict with:
      - `escaped`: True iff `|z| > 2` within `max_iter` steps
      - `iterations`: number of steps taken
      - `z_norm`: final `|z|`
      - `c`: input `(c_real, c_imag)` for traceability
    """
    z_r, z_i = 0.0, 0.0
    for n in range(max_iter):
        z_r2 = z_r * z_r
        z_i2 = z_i * z_i
        if z_r2 + z_i2 > ESCAPE_RADIUS_SQ:
            return {
                "escaped": True,
                "iterations": n,
                "z_norm": (z_r2 + z_i2) ** 0.5,
                "c": (c_real, c_imag),
            }
        z_i = 2.0 * z_r * z_i + c_imag
        z_r = z_r2 - z_i2 + c_real
    return {
        "escaped": False,
        "iterations": max_iter,
        "z_norm": (z_r * z_r + z_i * z_i) ** 0.5,
        "c": (c_real, c_imag),
    }


def hash_to_complex(text: str) -> tuple[float, float]:
    """Deterministic `string -> complex_c` via SHA256 prefix.

    Maps to the rectangle `[-2.0, 0.5] × [-1.25, 1.25]` (the
    interesting region of the Mandelbrot set).
    """
    h = hashlib.sha256(text.encode("utf-8")).digest()
    # First 4 bytes for real, next 4 for imag
    r_raw = int.from_bytes(h[:4], "big") / (2 ** 32)
    i_raw = int.from_bytes(h[4:8], "big") / (2 ** 32)
    c_real = -2.0 + 2.5 * r_raw    # → [-2.0, 0.5]
    c_imag = -1.25 + 2.5 * i_raw   # → [-1.25, 1.25]
    return c_real, c_imag


def classify_behavior(result: dict) -> str:
    """Map an iteration result to a behavior label."""
    if not result["escaped"]:
        return "BOUNDED"          # Conserved — path stays inside |z|≤2
    iters = result["iterations"]
    if iters < 5:
        return "FAST_ESCAPE"      # Rapidly diverges
    if iters < 15:
        return "MEDIUM_ESCAPE"
    return "SLOW_ESCAPE"          # Spent time near the boundary


def analyze_string(
    text: str,
    max_iter: int = MAX_ITER_DEFAULT,
) -> dict:
    """End-to-end: text → complex coord → Mandelbrot iteration → behavior.

    The canonical CQE call: every text input has a Mandelbrot
    fingerprint that summarizes whether it's a "lawful" (bounded) or
    "escape" (divergent) path through the |z|≤2 manifold.
    """
    c_real, c_imag = hash_to_complex(text)
    result = mandelbrot_iterate(c_real, c_imag, max_iter)
    result["behavior"] = classify_behavior(result)
    result["text_length"] = len(text)
    return result


def is_in_set(c_real: float, c_imag: float,
              max_iter: int = MAX_ITER_DEFAULT) -> bool:
    """Boolean: is the complex point `c` in the Mandelbrot set?"""
    return not mandelbrot_iterate(c_real, c_imag, max_iter)["escaped"]


def is_bounded_path(behavior: str) -> bool:
    """`True` iff the behavior corresponds to a lawful (bounded) path."""
    return behavior == "BOUNDED"
