"""
Pure-stdlib vector helpers for TarPit.

The historical `evolving_tarpit` used numpy throughout. We keep
8-dim vectors as tuples of floats and provide the small set of ops
needed: norm, dot, parallelogram area (Gram determinant √),
midpoint, reflection across a hyperplane, normalization.
"""
from __future__ import annotations

import math
import random
from typing import Sequence


Vec = tuple[float, ...]


def vec(values: Sequence[float]) -> Vec:
    return tuple(float(v) for v in values)


def add(a: Sequence[float], b: Sequence[float]) -> Vec:
    return tuple(float(x + y) for x, y in zip(a, b))


def sub(a: Sequence[float], b: Sequence[float]) -> Vec:
    return tuple(float(x - y) for x, y in zip(a, b))


def scale(a: Sequence[float], k: float) -> Vec:
    return tuple(float(x * k) for x in a)


def neg(a: Sequence[float]) -> Vec:
    return tuple(float(-x) for x in a)


def dot(a: Sequence[float], b: Sequence[float]) -> float:
    return float(sum(x * y for x, y in zip(a, b)))


def norm(a: Sequence[float]) -> float:
    return math.sqrt(sum(x * x for x in a))


def normalize(a: Sequence[float], target: float = 1.0) -> Vec:
    n = norm(a)
    if n == 0:
        return tuple(a)
    return tuple(float(x / n * target) for x in a)


def parallelogram_area(a: Sequence[float], b: Sequence[float]) -> float:
    """√(||a||²||b||² - <a,b>²) — the Gram-determinant area."""
    a_sq = sum(x * x for x in a)
    b_sq = sum(x * x for x in b)
    d = dot(a, b)
    area_sq = a_sq * b_sq - d * d
    return math.sqrt(max(area_sq, 0.0))


def midpoint(a: Sequence[float], b: Sequence[float]) -> Vec:
    return tuple(float((x + y) / 2) for x, y in zip(a, b))


def reflect(a: Sequence[float], normal: Sequence[float]) -> Vec:
    """v − 2(v·n̂)n̂ — reflection across hyperplane with normal `normal`."""
    n_hat = normalize(normal)
    coef = 2.0 * dot(a, n_hat)
    return tuple(float(x - coef * h) for x, h in zip(a, n_hat))


def mean(vectors: Sequence[Sequence[float]]) -> Vec:
    if not vectors:
        return ()
    n = len(vectors)
    dim = len(vectors[0])
    out = [0.0] * dim
    for v in vectors:
        for i, x in enumerate(v):
            out[i] += x
    return tuple(x / n for x in out)


def random_unit_vec(dim: int, rng: random.Random | None = None) -> Vec:
    r = rng or random
    v = [r.gauss(0, 1) for _ in range(dim)]
    n = math.sqrt(sum(x * x for x in v)) or 1.0
    return tuple(x / n for x in v)


def zeros(dim: int) -> Vec:
    return tuple(0.0 for _ in range(dim))
