"""MORSR Service — Middle Out Recursive Shape Reader.

Port of TMN2 morsr.py. 240 E8 sonar pulses for geometric navigation
and intersection density. Generates E8 root vectors for directional
sonar, BFS cascade through activated nodes, and shell assignment
by directional coverage.
"""
from __future__ import annotations

import hashlib
import json
import logging
import math
import os
import time
from collections import deque
from itertools import combinations, product
from typing import Any, Optional

logger = logging.getLogger("services.morsr")

PORT = int(os.environ.get("PORT", "8000"))
CONE_ANGLE = float(os.environ.get("CONE_ANGLE", "0.3"))
MAX_CASCADE_DEPTH = int(os.environ.get("MAX_CASCADE_DEPTH", "10"))
MAX_SCAN_FRONTIER = int(os.environ.get("MAX_SCAN_FRONTIER", "500"))

SHELL_THRESHOLDS = {0: 0.50, 1: 0.25, 2: 0.10, 3: 0.0}
SHADOW_CATEGORIES = [
    "geometry", "computation", "agent", "economy",
    "governance", "physics", "observation", "structure",
]


def _generate_e8_roots() -> list[list[float]]:
    roots = []
    for i, j in combinations(range(8), 2):
        for si, sj in product([1.0, -1.0], repeat=2):
            vec = [0.0] * 8
            vec[i] = si
            vec[j] = sj
            roots.append(vec)
    return roots


def _generate_half_integer_roots() -> list[list[float]]:
    roots = []
    for bits in range(256):
        signs = []
        neg_count = 0
        for b in range(8):
            if bits & (1 << b):
                signs.append(-0.5)
                neg_count += 1
            else:
                signs.append(0.5)
        if neg_count % 2 == 0:
            roots.append(signs)
    return roots


_INTEGER_ROOTS = _generate_e8_roots()
_HALF_INT_ROOTS = _generate_half_integer_roots()
_E8_ROOTS = _INTEGER_ROOTS + _HALF_INT_ROOTS
E8_DIRECTIONS = len(_E8_ROOTS)


def _norm(v: list[float]) -> float:
    return math.sqrt(sum(x * x for x in v))


def _normalize(v: list[float]) -> list[float]:
    n = _norm(v)
    return [x / n for x in v] if n > 0 else v


def _dot(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def _distance(a: list[float], b: list[float]) -> float:
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))


_E8_NORMALIZED = [_normalize(r) for r in _E8_ROOTS]


class MORSRService:
    """Middle Out Recursive Shape Reader.

    240-pulse E8 sonar for geometric navigation. Registers atoms
    in E8 space, sends directional sonar pulses, performs BFS
    cascade scans, and assigns shell depth by coverage.
    """

    def __init__(self, governance=None):
        self._governance = governance
        self._atoms: dict[str, dict] = {}
        self._scan_history: list[dict] = []
        self._stats = {"pings": 0, "scans": 0, "total_hits": 0, "depth_checks": 0}

    def register_atom(self, atom_id: str, e8_coords: list[float] = None,
                      labels: list[str] = None) -> dict:
        self._atoms[atom_id] = {
            "coords": e8_coords or [0.0] * 8,
            "labels": labels or [],
            "registered_at": time.time(),
        }
        return {"registered": atom_id, "total_atoms": len(self._atoms)}

    def register_atoms_batch(self, atoms: list[dict]) -> dict:
        count = 0
        for a in atoms:
            self._atoms[a["atom_id"]] = {
                "coords": a.get("e8_coords", [0.0] * 8),
                "labels": a.get("labels", []),
                "registered_at": time.time(),
            }
            count += 1
        return {"registered": count, "total_atoms": len(self._atoms)}

    def ping(self, e8_coords: list[float], radius: float = 5.0) -> dict:
        self._stats["pings"] += 1
        result = self._ping_from(e8_coords, radius)
        self._stats["total_hits"] += result["hit_count"]
        result["source"] = e8_coords
        result["radius"] = radius
        return result

    def _ping_from(self, coords: list[float], radius: float) -> dict:
        hits_by_direction: dict[int, list[dict]] = {}
        directions_hit: set[int] = set()
        total_hits = 0

        for atom_id, atom in self._atoms.items():
            diff = [t - s for t, s in zip(atom["coords"], coords)]
            dist = _norm(diff)
            if dist == 0 or dist > radius:
                continue
            diff_n = _normalize(diff)

            for i, direction in enumerate(_E8_NORMALIZED):
                dot_val = _dot(direction, diff_n)
                if dot_val > (1.0 - CONE_ANGLE):
                    directions_hit.add(i)
                    if i not in hits_by_direction:
                        hits_by_direction[i] = []
                    hits_by_direction[i].append({
                        "atom_id": atom_id,
                        "distance": round(dist, 6),
                        "cone_dot": round(dot_val, 6),
                        "labels": atom.get("labels", [])[:5],
                    })
                    total_hits += 1

        hit_count = len(directions_hit)
        depth_score = hit_count / E8_DIRECTIONS if E8_DIRECTIONS > 0 else 0.0

        shell = 3
        for s, threshold in sorted(SHELL_THRESHOLDS.items()):
            if depth_score >= threshold:
                shell = s

        shadow_actions = self._compute_shadow_actions(directions_hit)

        return {
            "pulses_fired": E8_DIRECTIONS,
            "hit_count": hit_count,
            "total_atom_hits": total_hits,
            "directions_hit": sorted(directions_hit),
            "depth_score": round(depth_score, 6),
            "shell_assignment": shell,
            "shell_name": f"shell_{shell}",
            "hits_by_direction": {
                str(k): v[:3] for k, v in sorted(hits_by_direction.items())[:20]
            },
            "shadow_actions": shadow_actions,
        }

    def _compute_shadow_actions(self, directions_hit: set[int]) -> list[dict]:
        unhit = [i for i in range(E8_DIRECTIONS) if i not in directions_hit]
        if not unhit:
            return []

        octant_gaps: dict[int, int] = {}
        for d_idx in unhit:
            vec = _E8_ROOTS[d_idx]
            dominant_dim = max(range(len(vec)), key=lambda k: abs(vec[k]))
            octant_gaps[dominant_dim] = octant_gaps.get(dominant_dim, 0) + 1

        actions = []
        for dim, count in sorted(octant_gaps.items(), key=lambda x: -x[1]):
            category = SHADOW_CATEGORIES[dim % len(SHADOW_CATEGORIES)]
            actions.append({
                "dimension": dim, "category": category,
                "gap_count": count,
                "gap_fraction": round(count / E8_DIRECTIONS, 4),
                "suggestion": f"Add {category}-related content to fill {count} unhit directions in dimension {dim}",
            })

        return actions[:8]

    def scan(self, e8_coords: list[float], radius: float = 5.0,
             max_depth: int = 5) -> dict:
        self._stats["scans"] += 1
        result = self._bfs_scan(e8_coords, radius, max_depth)

        ping_result = self._ping_from(e8_coords, radius)
        result["directional"] = {
            "directions_hit": len(ping_result["directions_hit"]),
            "depth_score": ping_result["depth_score"],
            "shell_assignment": ping_result["shell_assignment"],
            "shadow_actions": ping_result["shadow_actions"][:3],
        }

        self._scan_history.append({
            "coords": e8_coords,
            "atoms_found": result["atoms_visited"],
            "depth_score": ping_result["depth_score"],
            "timestamp": time.time(),
        })
        if len(self._scan_history) > 200:
            self._scan_history.pop(0)

        if self._governance:
            from governance.engine import BoundaryEvent
            self._governance.record_boundary_event(BoundaryEvent(
                event_id=f"morsr-scan-{int(time.time())}",
                timestamp=time.time(), entropy_delta=0.0,
                receipt_data={"atoms_visited": result["atoms_visited"],
                              "layers": result["layer_count"]},
                boundary_type="morsr_scan",
            ))

        return result

    def _bfs_scan(self, start_coords: list[float],
                  radius: float, max_depth: int) -> dict:
        visited: set[str] = set()
        frontier = deque()
        layers: list[dict] = []

        for atom_id, atom in self._atoms.items():
            dist = _distance(start_coords, atom["coords"])
            if dist <= radius:
                frontier.append((atom_id, 0, dist))

        while frontier and len(visited) < MAX_SCAN_FRONTIER:
            atom_id, depth, dist = frontier.popleft()
            if atom_id in visited or depth > max_depth:
                continue
            visited.add(atom_id)

            atom = self._atoms.get(atom_id)
            if not atom:
                continue

            while len(layers) <= depth:
                layers.append({"depth": len(layers), "atoms": [], "count": 0})
            layers[depth]["atoms"].append({
                "atom_id": atom_id, "distance": round(dist, 6),
                "labels": atom.get("labels", [])[:5],
            })
            layers[depth]["count"] += 1

            for other_id, other in self._atoms.items():
                if other_id not in visited:
                    d = _distance(atom["coords"], other["coords"])
                    if d <= radius:
                        frontier.append((other_id, depth + 1, d))

        for layer in layers:
            if len(layer["atoms"]) > 10:
                layer["atoms"] = layer["atoms"][:10]
                layer["truncated"] = True

        return {
            "start": start_coords, "radius": radius, "max_depth": max_depth,
            "atoms_visited": len(visited), "layers": layers,
            "layer_count": len(layers),
        }

    def determine_depth(self, agent_id: str,
                        explored_directions: list[int] = None) -> dict:
        self._stats["depth_checks"] += 1
        explored = set(explored_directions or [])
        valid_explored = explored & set(range(E8_DIRECTIONS))
        coverage = len(valid_explored) / E8_DIRECTIONS if E8_DIRECTIONS > 0 else 0.0

        shell = 3
        for s, threshold in sorted(SHELL_THRESHOLDS.items()):
            if coverage >= threshold:
                shell = s

        octant_coverage: dict[int, dict] = {}
        for d_idx in range(E8_DIRECTIONS):
            vec = _E8_ROOTS[d_idx]
            dominant_dim = max(range(len(vec)), key=lambda k: abs(vec[k]))
            if dominant_dim not in octant_coverage:
                octant_coverage[dominant_dim] = {"total": 0, "explored": 0}
            octant_coverage[dominant_dim]["total"] += 1
            if d_idx in valid_explored:
                octant_coverage[dominant_dim]["explored"] += 1

        octant_summary = {}
        for dim, data in octant_coverage.items():
            cat = SHADOW_CATEGORIES[dim % len(SHADOW_CATEGORIES)]
            ratio = data["explored"] / data["total"] if data["total"] > 0 else 0
            octant_summary[cat] = {
                "dimension": dim, "explored": data["explored"],
                "total": data["total"], "coverage": round(ratio, 4),
            }

        return {
            "agent_id": agent_id,
            "directions_explored": len(valid_explored),
            "total_directions": E8_DIRECTIONS,
            "coverage": round(coverage, 6), "shell": shell,
            "shell_name": f"shell_{shell}",
            "octant_coverage": octant_summary,
        }

    def list_directions(self, offset: int = 0, limit: int = 20,
                        root_type: str = "all") -> dict:
        if root_type == "integer":
            source = _INTEGER_ROOTS
            type_label = "integer"
        elif root_type == "half_integer":
            source = _HALF_INT_ROOTS
            type_label = "half_integer"
        else:
            source = _E8_ROOTS
            type_label = "all"

        total = len(source)
        page = source[offset:offset + limit]

        directions = []
        for i, vec in enumerate(page):
            dominant_dim = max(range(len(vec)), key=lambda k: abs(vec[k]))
            directions.append({
                "index": offset + i,
                "vector": [round(v, 4) for v in vec],
                "norm": round(_norm(vec), 6),
                "dominant_dimension": dominant_dim,
                "category": SHADOW_CATEGORIES[dominant_dim % len(SHADOW_CATEGORIES)],
            })

        return {
            "root_type": type_label, "total": total,
            "offset": offset, "limit": limit,
            "returned": len(directions), "directions": directions,
        }

    def label_intersection(self, labels_a: list[str] = None,
                           labels_b: list[str] = None,
                           labels_c: list[str] = None) -> dict:
        a = set(labels_a or [])
        b = set(labels_b or [])
        c = set(labels_c or []) if labels_c else set()

        ab = a & b
        ac = a & c if c else set()
        bc = b & c if c else set()
        abc = a & b & c if c else set()

        ab_union = a | b
        jaccard_ab = len(ab) / len(ab_union) if ab_union else 0.0
        jaccard_ac = len(ac) / len(a | c) if (a | c) else 0.0
        jaccard_bc = len(bc) / len(b | c) if (b | c) else 0.0

        density = "dense" if len(ab) > 5 else ("sparse" if len(ab) > 0 else "gap")
        is_gap = len(abc) == 0 and len(a) > 0 and len(b) > 0 and len(c) > 0

        return {
            "a_count": len(a), "b_count": len(b), "c_count": len(c),
            "ab_intersection": len(ab), "ac_intersection": len(ac),
            "bc_intersection": len(bc), "abc_intersection": len(abc),
            "ab_jaccard": round(jaccard_ab, 4),
            "ac_jaccard": round(jaccard_ac, 4),
            "bc_jaccard": round(jaccard_bc, 4),
            "density": density, "gap": is_gap,
            "unique_to_a": sorted(a - b - c)[:10],
            "unique_to_b": sorted(b - a - c)[:10],
            "shared_labels": sorted(ab)[:10],
        }

    @property
    def health(self) -> dict:
        return {
            "ok": True, "service": "morsr",
            "directions": E8_DIRECTIONS,
            "integer_roots": len(_INTEGER_ROOTS),
            "half_integer_roots": len(_HALF_INT_ROOTS),
            "atoms_loaded": len(self._atoms),
        }

    @property
    def stats(self) -> dict:
        return {
            "service": "morsr", "directions": E8_DIRECTIONS,
            "integer_roots": len(_INTEGER_ROOTS),
            "half_integer_roots": len(_HALF_INT_ROOTS),
            "atoms_loaded": len(self._atoms),
            "pings": self._stats["pings"], "scans": self._stats["scans"],
            "total_hits": self._stats["total_hits"],
            "depth_checks": self._stats["depth_checks"],
            "scan_history_size": len(self._scan_history),
            "recent_scans": self._scan_history[-5:],
        }

    @property
    def scan_history(self) -> dict:
        return {
            "total": len(self._scan_history),
            "returned": min(20, len(self._scan_history)),
            "history": self._scan_history[-20:],
        }
