"""
CompleteTraversal — the 240-node E8 lattice exploration mode.

Adapted from `morsr_complete.py:CompleteMORSRExplorer`. Visits every
E8 root exactly once per task, blending the current position toward
each root and scoring via NSL. Three traversal strategies:

  - `"systematic"` — sequential 0..239
  - `"distance_ordered"` — closest first (by Euclidean distance)
  - `"chamber_guided"` — Weyl-chamber-sorted (requires geometry port)

Returns a comprehensive analysis with score statistics, node-visit
order, top-k performers, and overlay determinations.
"""
from __future__ import annotations

import math
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from cmplx.nsl import NSLProvider, NSLSectors

from .overlay import Overlay


class TraversalStrategy(str, Enum):
    SYSTEMATIC = "systematic"
    DISTANCE_ORDERED = "distance_ordered"
    CHAMBER_GUIDED = "chamber_guided"


@dataclass
class NodeAnalysis:
    """One node's analysis record."""
    node_index: int
    step: int
    root_vector: tuple[float, ...]
    projected_vector: tuple[float, ...]
    objective_score: float          # = -sectors.total (higher is better)
    sectors: NSLSectors
    distance_to_initial: float
    distance_to_root: float
    root_norm: float

    def to_dict(self) -> dict:
        return {
            "node_index": self.node_index,
            "step": self.step,
            "objective_score": self.objective_score,
            "sectors": self.sectors.to_dict(),
            "distance_to_initial": self.distance_to_initial,
            "distance_to_root": self.distance_to_root,
            "root_norm": self.root_norm,
        }


@dataclass
class TraversalResult:
    """Complete-traversal output."""
    initial_vector: tuple[float, ...]
    best_node_index: int
    best_vector: tuple[float, ...]
    best_score: float
    strategy: str
    total_time: float
    visited: list[NodeAnalysis] = field(default_factory=list)

    def top_k(self, k: int = 20) -> list[NodeAnalysis]:
        return sorted(self.visited, key=lambda n: -n.objective_score)[:k]

    def summary(self) -> dict:
        scores = [n.objective_score for n in self.visited]
        return {
            "strategy": self.strategy,
            "nodes_visited": len(self.visited),
            "total_time_seconds": self.total_time,
            "nodes_per_second": (len(self.visited) / self.total_time) if self.total_time > 0 else 0.0,
            "best_score": self.best_score,
            "best_node_index": self.best_node_index,
            "score_mean": sum(scores) / len(scores) if scores else 0.0,
            "score_max": max(scores) if scores else 0.0,
            "score_min": min(scores) if scores else 0.0,
        }


# ---------------------------------------------------------------------------
# CompleteTraversal — the executor
# ---------------------------------------------------------------------------

class CompleteTraversal:
    """Visit every E8 root exactly once and score each via NSL.

    The root system is supplied at construction (default: a stub set
    of 240 unit vectors derived from index — sufficient for the
    diagnostic shape; canonical E8 roots come from
    `cmplx.geometry.e8.E8_ROOTS` when available).
    """

    name: str = "complete_traversal"

    def __init__(
        self,
        nsl: Optional[NSLProvider] = None,
        roots: Optional[list[tuple[float, ...]]] = None,
        projection_weight: float = 0.3,
    ) -> None:
        self.nsl = nsl or NSLProvider()
        self.roots = list(roots) if roots is not None else self._stub_roots()
        self.projection_weight = projection_weight

    # ── Stub roots (when E8 geometry not available) ──────────────────

    @staticmethod
    def _stub_roots(n: int = 240, dim: int = 8) -> list[tuple[float, ...]]:
        """Generate 240 deterministic unit vectors for diagnostic use.

        Not the actual E8 roots — those come from `cmplx.geometry.e8`.
        These are angularly-distributed unit vectors that give
        traversal something to scan when the geometry port isn't wired.
        """
        roots: list[tuple[float, ...]] = []
        for i in range(n):
            v = [0.0] * dim
            # Three of the 8 components get unit values; cycle through
            # combinations to fill 240 roots.
            a = i % dim
            b = (i // dim) % dim
            c = (i // (dim * dim)) % dim
            sign = -1.0 if (i // 4) % 2 else 1.0
            v[a] += sign
            v[b] += sign * 0.5
            v[c] += sign * 0.25
            # Normalize
            norm = math.sqrt(sum(x * x for x in v)) or 1.0
            roots.append(tuple(x / norm for x in v))
        return roots

    # ── Traversal ────────────────────────────────────────────────────

    def explore(
        self,
        initial: Overlay,
        strategy: TraversalStrategy = TraversalStrategy.SYSTEMATIC,
    ) -> TraversalResult:
        start = time.time()
        initial_vec = tuple(initial.position)
        order = self._traversal_order(initial_vec, strategy)
        result = TraversalResult(
            initial_vector=initial_vec,
            best_node_index=-1,
            best_vector=initial_vec,
            best_score=float("-inf"),
            strategy=strategy.value,
            total_time=0.0,
        )

        for step, node_idx in enumerate(order):
            analysis = self._analyze_node(node_idx, initial_vec, step)
            result.visited.append(analysis)
            if analysis.objective_score > result.best_score:
                result.best_score = analysis.objective_score
                result.best_node_index = node_idx
                result.best_vector = analysis.projected_vector

        result.total_time = time.time() - start
        return result

    def _traversal_order(
        self,
        initial_vec: tuple[float, ...],
        strategy: TraversalStrategy,
    ) -> list[int]:
        n = len(self.roots)
        if strategy == TraversalStrategy.SYSTEMATIC:
            return list(range(n))
        if strategy == TraversalStrategy.DISTANCE_ORDERED:
            distances = [
                (self._l2(self.roots[i], initial_vec), i)
                for i in range(n)
            ]
            distances.sort()
            return [i for _, i in distances]
        if strategy == TraversalStrategy.CHAMBER_GUIDED:
            # Chamber signature = sign pattern of the root vector.
            # Group by sig, then sort within each by distance to initial.
            chamber_groups: dict[str, list[int]] = {}
            for i in range(n):
                sig = "".join(
                    "+" if c >= 0 else "-" for c in self.roots[i]
                )
                chamber_groups.setdefault(sig, []).append(i)
            ordered: list[int] = []
            for sig in sorted(chamber_groups.keys()):
                group = chamber_groups[sig]
                group.sort(
                    key=lambda idx: self._l2(self.roots[idx], initial_vec)
                )
                ordered.extend(group)
            return ordered
        # Fallback
        return list(range(n))

    def _analyze_node(
        self,
        node_idx: int,
        initial_vec: tuple[float, ...],
        step: int,
    ) -> NodeAnalysis:
        root = self.roots[node_idx]
        # Pad to matching length
        dim = max(len(root), len(initial_vec))
        iv = tuple(list(initial_vec) + [0.0] * (dim - len(initial_vec)))
        rv = tuple(list(root) + [0.0] * (dim - len(root)))
        # Blend initial toward root
        w = self.projection_weight
        projected = tuple((1 - w) * iv[i] + w * rv[i] for i in range(dim))
        # NSL score: lower ΔΦ = better; objective_score is the negation
        sectors = self.nsl.compute_sectors(iv, projected)
        score = -sectors.total
        return NodeAnalysis(
            node_index=node_idx,
            step=step,
            root_vector=rv,
            projected_vector=projected,
            objective_score=score,
            sectors=sectors,
            distance_to_initial=self._l2(projected, iv),
            distance_to_root=self._l2(projected, rv),
            root_norm=math.sqrt(sum(x * x for x in rv)),
        )

    @staticmethod
    def _l2(a, b) -> float:
        n = max(len(a), len(b))
        a_p = list(a) + [0.0] * (n - len(a))
        b_p = list(b) + [0.0] * (n - len(b))
        return math.sqrt(sum((x - y) ** 2 for x, y in zip(a_p, b_p)))

    def __repr__(self) -> str:
        return f"<CompleteTraversal roots={len(self.roots)}>"
