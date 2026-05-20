"""
Polarity-aware lenses for SNAP evaluation.

Verbatim semantics from the canonical files:
  - BaseLens (cmplx_pending/snap/BaseLens.py)
  - LegalityLens
  - NoveltyLens
  - SymmetryLens

Plus a `LensBank` keyed by lens name, with a `best_lens(state)` picker
that the Gate369Engine uses to choose the active evaluation lens for
a given context.
"""
from __future__ import annotations

from typing import Any, Optional


class BaseLens:
    """Base polarity-aware lens.

    `evaluate(state)` returns `"pass"` or `"refine"` based on three
    thresholds. `score_reward(before, after)` returns a scalar utility
    delta with an edbsu-growth penalty.
    """

    name: str = "base"

    def evaluate(self, state: dict) -> str:
        if not state.get("mirror_pass", False):
            return "refine"
        if state.get("polarity_conflict", 1.0) > state.get("polarity_thresh", 0.2):
            return "refine"
        if state.get("containment_c", 0.0) < state.get("c_thresh", 0.7):
            return "refine"
        return "pass"

    def score_reward(self, before: dict, after: dict) -> float:
        return (
            after.get("delta_u", 0.0)
            - before.get("delta_u", 0.0)
            - 0.1 * after.get("edbsu_growth", 0.0)
        )

    def pick_predicate(self, candidates: list, state: dict):
        """Sort predicates by expected utility / cost; pick best.

        Predicate-shape contract: each candidate has `meta` dict and
        a numeric `cost` attribute.
        """
        if not candidates:
            raise ValueError("no predicate candidates supplied")
        return sorted(
            candidates,
            key=lambda p: -(
                p.meta.get("expected_du", 0.0) / max(p.cost, 1e-6)
            ),
        )[0]

    def __repr__(self) -> str:
        return f"<{type(self).__name__} name={self.name!r}>"


class LegalityLens(BaseLens):
    """Refines/fails on policy violations. Otherwise BaseLens behavior."""

    name = "legality"

    def evaluate(self, state: dict) -> str:
        if state.get("violates_policy", False):
            return "fail"
        return super().evaluate(state)


class NoveltyLens(BaseLens):
    """Adds a 0.2 × novelty bonus to the reward."""

    name = "novelty"

    def score_reward(self, before: dict, after: dict) -> float:
        return super().score_reward(before, after) + 0.2 * after.get("novelty", 0.0)


class SymmetryLens(BaseLens):
    """Adds a 0.15 × symmetry_score bonus to the reward."""

    name = "symmetry"

    def score_reward(self, before: dict, after: dict) -> float:
        return super().score_reward(before, after) + 0.15 * after.get("symmetry_score", 0.0)


class LensBank:
    """Name → lens registry. Default bank pre-loads the four canonical lenses."""

    def __init__(self) -> None:
        self._lenses: dict[str, BaseLens] = {}
        for lens in (BaseLens(), LegalityLens(), NoveltyLens(), SymmetryLens()):
            self.register(lens)

    def register(self, lens: BaseLens) -> None:
        self._lenses[lens.name] = lens

    def get(self, name: str) -> Optional[BaseLens]:
        return self._lenses.get(name)

    def names(self) -> tuple[str, ...]:
        return tuple(sorted(self._lenses))

    def best_lens(self, state: dict) -> BaseLens:
        """Pick the right lens for a state.

        Heuristic that matches the canonical's intent:
          - violates_policy → LegalityLens
          - high novelty signal → NoveltyLens
          - high symmetry signal → SymmetryLens
          - else → BaseLens
        """
        if state.get("violates_policy", False):
            return self._lenses["legality"]
        if state.get("novelty", 0.0) > 0.3:
            return self._lenses["novelty"]
        if state.get("symmetry_score", 0.0) > 0.3:
            return self._lenses["symmetry"]
        return self._lenses["base"]
