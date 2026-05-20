"""
SonarScan — 240-direction ping diagnostic.

Adapted from `morsr_service.py` (`Middle Out Recursive Shape Reader`).
From a starting coordinate, send 240 directional "pings" — one per E8
root — and record per-direction hit/no-hit. Classify the coverage
into shells, emit shadow actions for unhit directions.

  - `shell_0` ≥ 50% directions hit (≥ 120 of 240)
  - `shell_1` ≥ 25% (≥ 60)
  - `shell_2` ≥ 10% (≥ 24)
  - `shell_3` < 10%

Shadow actions categorize unhit dimensions into 8 semantic buckets:
geometry, computation, agent, economy, governance, physics,
observation, structure.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


# The 8 shadow categories — one per E8 axis
SHADOW_CATEGORIES: tuple[str, ...] = (
    "geometry",
    "computation",
    "agent",
    "economy",
    "governance",
    "physics",
    "observation",
    "structure",
)

# Shell thresholds (cumulative hit-fraction)
SHELL_THRESHOLDS: tuple[tuple[str, float], ...] = (
    ("shell_0", 0.50),
    ("shell_1", 0.25),
    ("shell_2", 0.10),
)

E8_DIRECTIONS_DEFAULT: int = 240


class SonarShell(str, Enum):
    SHELL_0 = "shell_0"
    SHELL_1 = "shell_1"
    SHELL_2 = "shell_2"
    SHELL_3 = "shell_3"


# ---------------------------------------------------------------------------
# Atom record (what's in the scan field)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class SonarAtom:
    """An atom in the scan field — anything with an E8 coordinate."""
    atom_id: str
    e8_coords: tuple[float, ...]
    labels: tuple[str, ...] = ()


# ---------------------------------------------------------------------------
# Shadow action — gap-filling suggestion
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ShadowAction:
    category: str
    dimension: int
    unhit_count: int
    suggestion: str


# ---------------------------------------------------------------------------
# Scan result
# ---------------------------------------------------------------------------

@dataclass
class SonarScanResult:
    """Full output of one ping scan."""
    source: tuple[float, ...]
    radius: float
    directions_total: int
    hit_count: int
    depth_score: float
    shell: str
    hits_by_direction: dict[int, list[str]] = field(default_factory=dict)
    shadow_actions: list[ShadowAction] = field(default_factory=list)

    def coverage_by_category(self) -> dict[str, int]:
        """Per-category hit count: how many of this category's directions hit."""
        # Re-derive from hits_by_direction: each direction index maps
        # to a category by `dimension = direction_index % 8`.
        out: dict[str, int] = {cat: 0 for cat in SHADOW_CATEGORIES}
        for dir_idx in self.hits_by_direction:
            dim = dir_idx % len(SHADOW_CATEGORIES)
            out[SHADOW_CATEGORIES[dim]] += 1
        return out

    def to_dict(self) -> dict:
        return {
            "source": list(self.source),
            "radius": self.radius,
            "directions_total": self.directions_total,
            "hit_count": self.hit_count,
            "depth_score": self.depth_score,
            "shell": self.shell,
            "hits": {str(k): list(v) for k, v in self.hits_by_direction.items()},
            "shadow_actions": [
                {
                    "category": a.category,
                    "dimension": a.dimension,
                    "unhit_count": a.unhit_count,
                    "suggestion": a.suggestion,
                }
                for a in self.shadow_actions
            ],
            "coverage_by_category": self.coverage_by_category(),
        }


# ---------------------------------------------------------------------------
# SonarScan — the executor
# ---------------------------------------------------------------------------

class SonarScan:
    """The 240-direction ping scanner.

    >>> scan = SonarScan()
    >>> scan.register_atom("a1", [0.5, 0, 0, 0, 0, 0, 0, 0])
    >>> result = scan.ping([0, 0, 0, 0, 0, 0, 0, 0], radius=1.0)
    >>> result.shell        # "shell_0" / "shell_1" / "shell_2" / "shell_3"
    """

    name: str = "sonar_scan"

    def __init__(
        self,
        directions: int = E8_DIRECTIONS_DEFAULT,
        cone_angle: float = 0.3,  # cone tolerance (1 - cone_angle = dot threshold)
        dim: int = 8,
        directions_seed: Optional[list[tuple[float, ...]]] = None,
    ) -> None:
        self.directions_count = directions
        self.cone_angle = cone_angle
        self.dim = dim
        self.directions = (
            directions_seed if directions_seed is not None
            else self._stub_directions(directions, dim)
        )
        self._atoms: dict[str, SonarAtom] = {}

    # ── Direction seed (stub when geometry not registered) ───────────

    @staticmethod
    def _stub_directions(n: int, dim: int) -> list[tuple[float, ...]]:
        """Generate `n` deterministic unit vectors in `dim`-D space."""
        out: list[tuple[float, ...]] = []
        for i in range(n):
            v = [0.0] * dim
            a, b, c = i % dim, (i // dim) % dim, (i // (dim * dim)) % dim
            sign = -1.0 if (i // 4) % 2 else 1.0
            v[a] += sign
            v[b] += sign * 0.5
            v[c] += sign * 0.25
            norm = math.sqrt(sum(x * x for x in v)) or 1.0
            out.append(tuple(x / norm for x in v))
        return out

    # ── Atom management ──────────────────────────────────────────────

    def register_atom(
        self,
        atom_id: str,
        e8_coords,
        labels: Optional[list[str]] = None,
    ) -> SonarAtom:
        atom = SonarAtom(
            atom_id=atom_id,
            e8_coords=tuple(float(c) for c in e8_coords),
            labels=tuple(labels or ()),
        )
        self._atoms[atom_id] = atom
        return atom

    def register_atoms_batch(self, atoms: list[dict]) -> int:
        for a in atoms:
            self.register_atom(
                atom_id=a["atom_id"],
                e8_coords=a.get("e8_coords", []),
                labels=a.get("labels"),
            )
        return len(self._atoms)

    @property
    def atom_count(self) -> int:
        return len(self._atoms)

    # ── Ping ─────────────────────────────────────────────────────────

    def ping(self, source, radius: float = 5.0) -> SonarScanResult:
        """Send a 240-direction ping from `source`.

        For each atom within `radius` of `source`, compute the
        normalized offset vector and assign it to whichever direction
        it falls into (the direction with the highest dot product
        above the cone threshold).
        """
        src = tuple(float(x) for x in source)
        dot_threshold = 1.0 - self.cone_angle

        # Direction index → list of atom_ids that landed there
        hits: dict[int, list[str]] = {}

        for atom in self._atoms.values():
            diff = self._sub(atom.e8_coords, src)
            dist = self._norm(diff)
            if dist == 0.0 or dist > radius:
                continue
            unit = self._scale(diff, 1.0 / dist)
            # Find best direction
            best_idx = -1
            best_dot = -2.0
            for idx, d in enumerate(self.directions):
                dot = self._dot(unit, d)
                if dot > best_dot:
                    best_dot = dot
                    best_idx = idx
            if best_dot >= dot_threshold and best_idx >= 0:
                hits.setdefault(best_idx, []).append(atom.atom_id)

        hit_count = len(hits)
        depth_score = hit_count / self.directions_count
        shell = self._classify_shell(depth_score)
        shadow_actions = self._compute_shadow_actions(hits)

        return SonarScanResult(
            source=src,
            radius=radius,
            directions_total=self.directions_count,
            hit_count=hit_count,
            depth_score=depth_score,
            shell=shell,
            hits_by_direction=hits,
            shadow_actions=shadow_actions,
        )

    @staticmethod
    def _classify_shell(depth_score: float) -> str:
        for shell_name, threshold in SHELL_THRESHOLDS:
            if depth_score >= threshold:
                return shell_name
        return "shell_3"

    def _compute_shadow_actions(
        self,
        hits: dict[int, list[str]],
    ) -> list[ShadowAction]:
        """For each E8 axis (8 categories), count unhit directions and
        emit a suggestion."""
        per_category_unhit: dict[int, int] = {
            i: 0 for i in range(len(SHADOW_CATEGORIES))
        }
        for dir_idx in range(self.directions_count):
            if dir_idx in hits:
                continue
            dim = dir_idx % len(SHADOW_CATEGORIES)
            per_category_unhit[dim] += 1

        actions: list[ShadowAction] = []
        for dim, unhit in per_category_unhit.items():
            if unhit == 0:
                continue
            category = SHADOW_CATEGORIES[dim]
            actions.append(ShadowAction(
                category=category,
                dimension=dim,
                unhit_count=unhit,
                suggestion=(
                    f"Add {category}-related content to fill {unhit} "
                    f"unhit direction(s) on axis {dim}."
                ),
            ))
        actions.sort(key=lambda a: -a.unhit_count)
        return actions

    # ── Vector helpers ───────────────────────────────────────────────

    @staticmethod
    def _sub(a, b):
        n = max(len(a), len(b))
        a_p = tuple(a) + (0.0,) * (n - len(a))
        b_p = tuple(b) + (0.0,) * (n - len(b))
        return tuple(x - y for x, y in zip(a_p, b_p))

    @staticmethod
    def _scale(v, k):
        return tuple(x * k for x in v)

    @staticmethod
    def _dot(a, b):
        n = min(len(a), len(b))
        return sum(a[i] * b[i] for i in range(n))

    @staticmethod
    def _norm(v):
        return math.sqrt(sum(x * x for x in v))

    def __repr__(self) -> str:
        return (
            f"<SonarScan dirs={self.directions_count} "
            f"atoms={len(self._atoms)}>"
        )
