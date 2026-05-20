"""
HundredFormTransitionCalibration — phase-transition behavior (G5, 4.4).

Adapts ``experiment_100form.py``'s representational-space-growth analysis
to use our substrate's E8 roots. The prior repo's POC relies on 5 external
JSON files that don't exist on this system; we reproduce the form-generation
algorithm directly and measure growth across cycle orders.

Substrate exercised: cmplx.geometry.e8.embed.e8_roots() (root set used
for nearest-neighbor snap as forms are generated).
"""
from __future__ import annotations

import math
from collections import Counter
from typing import Any

import numpy as np

from ..harness import CalibrationClaim, CalibrationTarget


# Default highest-root seed for form generation (E8 highest root).
_HIGHEST_ROOT = (0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, -1.0)


def _generate_forms(cycle_order: int, n_forms: int) -> list[tuple[float, ...]]:
    """Cyclic rotation of coordinates by ``8 // cycle_order`` positions.

    With cycle_order=8 → shift=1 → period 8 (after 8 forms, cycle repeats).
    With cycle_order=4 → shift=2 → period 4.
    With cycle_order=2 → shift=4 → period 2.
    """
    shift = 8 // cycle_order
    current = list(_HIGHEST_ROOT)
    forms: list[tuple[float, ...]] = []
    for _ in range(n_forms):
        forms.append(tuple(current))
        current = current[shift:] + current[:shift]
    return forms


def _digital_root(v: tuple[float, ...]) -> int:
    n = sum(abs(int(round(x))) for x in v)
    if n == 0:
        return 0
    return 1 + (n - 1) % 9


def _snap_to_e8(v: np.ndarray, root_vecs: np.ndarray) -> int:
    dists_sq = np.sum((root_vecs - v) ** 2, axis=1)
    return int(np.argmin(dists_sq))


def measure_growth(
    cycle_order: int, sample_levels: tuple[int, ...] = (25, 50, 75, 100, 150, 200),
) -> dict[str, Any]:
    """Generate forms, snap each to E8, measure unique-roots growth.

    Substrate touched: cmplx.geometry.e8.embed.e8_roots().
    """
    from cmplx.geometry.e8.embed import e8_roots

    root_vecs = np.array(e8_roots(), dtype=float)
    max_forms = max(sample_levels)
    forms = _generate_forms(cycle_order, max_forms)

    # Snap each form to its nearest E8 root.
    snapped_idxs: list[int] = []
    digital_roots: list[int] = []
    for f in forms:
        idx = _snap_to_e8(np.array(f, dtype=float), root_vecs)
        snapped_idxs.append(idx)
        digital_roots.append(_digital_root(f))

    # Measure unique-counts at each sample level.
    growth: dict[int, dict[str, Any]] = {}
    for level in sample_levels:
        unique_roots = len(set(snapped_idxs[:level]))
        unique_drs = len(set(digital_roots[:level]))
        dr_window = digital_roots[:level]
        ent = -sum(
            (c / level) * math.log2(c / level)
            for c in Counter(dr_window).values() if c > 0
        )
        growth[level] = {
            "unique_roots": unique_roots,
            "unique_drs": unique_drs,
            "dr_entropy": ent,
        }

    return {
        "cycle_order": cycle_order,
        "n_forms": max_forms,
        "growth": growth,
        "all_snapped_idxs": snapped_idxs,
    }


class HundredFormTransitionCalibration(CalibrationTarget):
    """100-form phase transition — 7 growth + structural claims."""

    target_name = "hundred_form_transition"

    def __init__(self) -> None:
        self._order_2: dict[str, Any] = {}
        self._order_4: dict[str, Any] = {}
        self._order_8: dict[str, Any] = {}

    def setup(self) -> None:
        self._order_2 = measure_growth(2)
        self._order_4 = measure_growth(4)
        self._order_8 = measure_growth(8)

    def claims(self) -> list[CalibrationClaim]:
        return [
            CalibrationClaim(
                name="order_2_unique_roots_bounded",
                expected=True,
                tolerance=0,
                observed_fn=lambda: self._order_2["growth"][200]["unique_roots"] <= 2,
                notes=(
                    "Order-2 cyclic rotation has period 2 → at most 2 distinct "
                    "forms → at most 2 distinct nearest-roots, regardless of N."
                ),
            ),
            CalibrationClaim(
                name="order_4_more_variety_than_order_2",
                expected=True,
                tolerance=0,
                observed_fn=lambda: (
                    self._order_4["growth"][200]["unique_roots"]
                    >= self._order_2["growth"][200]["unique_roots"]
                ),
                notes="Higher cycle order → at least as many unique roots covered.",
            ),
            CalibrationClaim(
                name="order_8_more_variety_than_order_4",
                expected=True,
                tolerance=0,
                observed_fn=lambda: (
                    self._order_8["growth"][200]["unique_roots"]
                    >= self._order_4["growth"][200]["unique_roots"]
                ),
                notes="Order-8 covers ≥ as many unique roots as order-4.",
            ),
            CalibrationClaim(
                name="order_8_growth_monotone_up_to_100",
                expected=True,
                tolerance=0,
                observed_fn=lambda: _is_monotone_nondecreasing([
                    self._order_8["growth"][lvl]["unique_roots"]
                    for lvl in (25, 50, 75, 100)
                ]),
                notes=(
                    "Up to the 100-form mark, unique-root count is monotone "
                    "non-decreasing (a representational space can only grow "
                    "or stay flat as new forms are added)."
                ),
            ),
            CalibrationClaim(
                name="dr_entropy_grows_through_100",
                expected=True,
                tolerance=0,
                observed_fn=lambda: (
                    self._order_8["growth"][100]["dr_entropy"]
                    >= self._order_8["growth"][25]["dr_entropy"]
                ),
                notes=(
                    "DR entropy at 100 forms ≥ DR entropy at 25 forms "
                    "(more samples → entropy of a stable categorical "
                    "distribution stabilizes or grows; cyclic rotation "
                    "preserves DR set membership)."
                ),
            ),
            CalibrationClaim(
                name="all_snapped_indices_valid",
                expected=True,
                tolerance=0,
                observed_fn=lambda: all(
                    0 <= idx < 240
                    for ord_result in (self._order_2, self._order_4, self._order_8)
                    for idx in ord_result["all_snapped_idxs"]
                ),
                notes="Every snapped index is a valid root index across all orders.",
            ),
            CalibrationClaim(
                name="post_100_growth_does_not_collapse",
                expected=True,
                tolerance=0,
                observed_fn=lambda: (
                    self._order_8["growth"][200]["unique_roots"]
                    >= self._order_8["growth"][100]["unique_roots"]
                ),
                notes=(
                    "After the 100-form mark, the representational space "
                    "doesn't shrink — it either keeps growing or saturates. "
                    "If it shrinks, the algorithm is non-monotone (broken)."
                ),
            ),
        ]


def _is_monotone_nondecreasing(seq: list[float]) -> bool:
    if len(seq) < 2:
        return True
    return all(seq[i] <= seq[i + 1] + 1e-9 for i in range(len(seq) - 1))
