"""
The four canonical MORSR pulse operators.

Adapted from `CQE_MORSR_NewBest_v1/cqe_plus/operators.py`. Each
operator returns a NEW `Overlay` (no in-place mutation). Operators
form the pulse front: at each ring/stage, the engine applies every
operator to the current overlay and gates the candidates.

  - `op_rtheta` — rotation in the first two coordinates by `theta`
  - `op_weyl_reflect` — reflect position across a basis axis
  - `op_midpoint` — average two overlays (geometric midpoint)
  - `op_parity_mirror` — flip the activation parity (XOR with all-ones)

The set is pluggable — the engine's `add_operator(name, fn)` accepts
any `(Overlay, **params) -> Overlay` callable.
"""
from __future__ import annotations

import math
from typing import Callable, Optional

from .overlay import Overlay


# ---------------------------------------------------------------------------
# Operators
# ---------------------------------------------------------------------------

def op_rtheta(overlay: Overlay, theta: float = 0.1) -> Overlay:
    """Rotate `overlay.position` in the (0, 1) 2-plane by `theta` radians."""
    pos = list(overlay.position)
    if len(pos) < 2:
        return overlay.clone()
    c, s = math.cos(theta), math.sin(theta)
    x, y = pos[0], pos[1]
    pos[0] = c * x - s * y
    pos[1] = s * x + c * y
    return overlay.clone(position=tuple(pos))


def op_weyl_reflect(overlay: Overlay, root_index: int = 0) -> Overlay:
    """Reflect across the hyperplane perpendicular to basis axis `root_index`.

    Simplification: negate the component at `root_index`. The full
    Weyl reflection across an E8 root is in `cmplx.geometry.alena`;
    this operator uses the basis-axis form as the default pulse.
    """
    pos = list(overlay.position)
    if 0 <= root_index < len(pos):
        pos[root_index] = -pos[root_index]
    return overlay.clone(position=tuple(pos))


def op_midpoint(overlay: Overlay, other: Optional[Overlay] = None,
                weight: float = 0.5) -> Overlay:
    """Weighted midpoint of `overlay` and `other`.

    If `other` is None, perturbs the current position by a small
    deterministic delta (mirrors the canonical `_generate_probe_overlay`).
    `weight=0.5` is the unweighted midpoint; weight closer to 0 favors
    the current overlay; closer to 1 favors `other`.
    """
    if other is None:
        # Deterministic probe — shift each component by COUPLING-scaled index
        from cmplx.geometry.alena import COUPLING
        pos = tuple(
            x + COUPLING * (i + 1) * 0.1
            for i, x in enumerate(overlay.position)
        )
        return overlay.clone(position=pos)

    w = max(0.0, min(1.0, weight))
    n = max(len(overlay.position), len(other.position))
    a = list(overlay.position) + [0.0] * (n - len(overlay.position))
    b = list(other.position) + [0.0] * (n - len(other.position))
    pos = tuple((1.0 - w) * a[i] + w * b[i] for i in range(n))
    # Activation: bitwise OR (union of actives)
    acts = tuple(
        (overlay.activations[i] | other.activations[i])
        if i < len(overlay.activations) and i < len(other.activations)
        else 0
        for i in range(max(len(overlay.activations), len(other.activations)))
    )
    return overlay.clone(position=pos, activations=acts)


def op_parity_mirror(overlay: Overlay) -> Overlay:
    """Flip the activation parity (XOR mask with all-ones).

    Position is unchanged; only the activation bitmask is inverted.
    Useful as a counterpole probe — the result is the "complement" of
    the current overlay in activation space.
    """
    acts = tuple(1 - b for b in overlay.activations)
    return overlay.clone(activations=acts)


# ---------------------------------------------------------------------------
# OperatorRegistry — pluggable set
# ---------------------------------------------------------------------------

OperatorFn = Callable[..., Overlay]


class OperatorRegistry:
    """Name → operator callable. Default registry has the four canonical ops."""

    def __init__(self) -> None:
        self._ops: dict[str, OperatorFn] = {}
        self._register_canonical()

    def _register_canonical(self) -> None:
        self._ops["rtheta"] = op_rtheta
        self._ops["weyl_reflect"] = op_weyl_reflect
        self._ops["midpoint"] = op_midpoint
        self._ops["parity_mirror"] = op_parity_mirror

    def add(self, name: str, fn: OperatorFn) -> None:
        if name in self._ops:
            raise RuntimeError(f"operator {name!r} already registered")
        self._ops[name] = fn

    def get(self, name: str) -> OperatorFn:
        if name not in self._ops:
            raise LookupError(
                f"operator {name!r} not registered; available: {sorted(self._ops)}"
            )
        return self._ops[name]

    def names(self) -> tuple[str, ...]:
        return tuple(sorted(self._ops))

    def items(self):
        return list(self._ops.items())

    def __len__(self) -> int:
        return len(self._ops)
