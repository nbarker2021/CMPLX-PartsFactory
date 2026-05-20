"""
Mandelbrot membership tests for the Atlas deployment boundary.

The Mandelbrot set M is the set of complex c values for which the
orbit of 0 under z_{n+1} = z_n^2 + c remains bounded. Membership is the
canonical "is this c a valid deployment candidate" test for Atlas.

Two surfaces:

  - ``is_in_mandelbrot(c, max_iter)`` — boolean test
  - ``escape_time(c, max_iter)`` — iteration count before escape (0..max_iter);
    max_iter means "stayed bounded through all iterations" → in set.

Both use the standard |z| > 2 escape criterion (orbit guaranteed unbounded
once magnitude exceeds 2).
"""
from __future__ import annotations


# Standard escape radius — once |z| > 2 the orbit is guaranteed unbounded.
_ESCAPE_RADIUS_SQ = 4.0


def escape_time(c: complex, max_iter: int = 100) -> int:
    """Return iterations before |z| > 2 starting from z_0 = 0.

    Returns ``max_iter`` (not max_iter+1) if the orbit stayed bounded
    through all iterations — that's the "in the Mandelbrot set" signal.

    Args:
        c: the complex parameter to test
        max_iter: hard cap on iterations (default 100). Higher = more
            accurate boundary; lower = faster.

    Returns:
        int in ``[0, max_iter]``. ``< max_iter`` means c is outside the set.
    """
    z = 0j
    for i in range(max_iter):
        z = z * z + c
        if z.real * z.real + z.imag * z.imag > _ESCAPE_RADIUS_SQ:
            return i
    return max_iter


def is_in_mandelbrot(c: complex, max_iter: int = 100) -> bool:
    """True iff the orbit of 0 under z² + c stays bounded for max_iter steps."""
    return escape_time(c, max_iter) == max_iter
