"""Glyph Service — TarPit glyph shelling, ecology, and arity system.

Port of TMN2 glyph.py. Grains bond into Dust (2-body) -> Triad (3-body closure).
Glyph shelling partitions glyphs into shells by E8 distance and wall depth.
Superpermutation arity: width 1=atomic, 2=dust, 3=triad, 4=1-ary addition group.
Ecology: glyphs compete for resources, higher mass absorbs lower.
"""
from __future__ import annotations

import hashlib
import json
import logging
import math
import os
import time
from collections import defaultdict
from typing import Any, Optional

from cmplx.primitives.superperm import SUPERPERM_N4

logger = logging.getLogger("services.glyph")

PORT = int(os.environ.get("PORT", "8000"))
COUPLING_CONSTANT = math.log((1 + math.sqrt(5)) / 2) / 16
MAX_ARITY = 3


class GlyphService:
    """Glyph shelling and ecology system.

    Manages glyph registration, bonding (arity-constrained),
    shell assignment by structural depth, and ecology simulation
    where higher-mass glyphs absorb lower-mass neighbors.
    """

    def __init__(self, governance=None):
        self._governance = governance
        self._glyphs: dict[str, dict] = {}
        self._bonds: list[dict] = []
        self._ecology_steps: int = 0
        self._ecology_log: list[dict] = []
        self._stats = {
            "registered": 0, "bonds_formed": 0, "bonds_rejected": 0,
            "ecology_steps": 0, "absorptions": 0, "codons_formed": 0,
        }

    # ── Internal helpers ─────────────────────────────────────

    @staticmethod
    def _generate_glyph_id(content: str) -> str:
        return hashlib.sha256(content.encode()).hexdigest()[:12]

    @staticmethod
    def _compute_mass(glyph: dict) -> float:
        bond_count = len(glyph.get("bonds", []))
        return bond_count + glyph["arity"]

    @staticmethod
    def _compute_energy(mass: float) -> float:
        return COUPLING_CONSTANT * mass

    @staticmethod
    def _e8_distance(a: list[float], b: list[float]) -> float:
        return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))

    @staticmethod
    def _e8_norm(v: list[float]) -> float:
        return math.sqrt(sum(x * x for x in v))

    @staticmethod
    def _parse_wall(encoding: str) -> dict:
        parts = encoding.split(".", 1)
        wall_type = parts[0] if parts else "X"
        directions = []
        if len(parts) > 1:
            for ch in parts[1]:
                if ch.isdigit():
                    directions.append(int(ch))
        return {
            "wall_type": wall_type, "directions": directions,
            "depth": len(directions),
            "is_palindromic": directions == directions[::-1],
        }

    def _assign_shell(self, glyph: dict) -> int:
        wall = self._parse_wall(glyph["wall_encoding"])
        wall_depth = wall["depth"]
        bond_count = len(glyph.get("bonds", []))
        combined_depth = wall_depth + bond_count
        if combined_depth >= 6:
            return 0
        elif combined_depth >= 4:
            return 1
        elif combined_depth >= 2:
            return 2
        else:
            return 3

    @staticmethod
    def _check_arity_compatible(glyph_a: dict, glyph_b: dict) -> bool:
        return glyph_a["arity"] + glyph_b["arity"] <= MAX_ARITY

    def _form_codon(self, glyph_ids: list[str]) -> Optional[dict]:
        if len(glyph_ids) < 3:
            return None
        for i in range(len(glyph_ids)):
            for j in range(i + 1, len(glyph_ids)):
                g_i = self._glyphs.get(glyph_ids[i])
                g_j = self._glyphs.get(glyph_ids[j])
                if not g_i or not g_j:
                    return None
                if glyph_ids[j] not in g_i.get("bonds", []):
                    return None
        total_mass = sum(self._compute_mass(self._glyphs[gid])
                         for gid in glyph_ids if gid in self._glyphs)
        codon_content = "+".join(
            self._glyphs[gid]["content"][:20]
            for gid in glyph_ids if gid in self._glyphs
        )
        codon_id = hashlib.sha256(codon_content.encode()).hexdigest()[:12]
        return {
            "codon_id": codon_id, "glyph_ids": glyph_ids,
            "total_mass": total_mass,
            "total_energy": self._compute_energy(total_mass),
            "content_summary": codon_content[:60],
        }

    # ── Public API ───────────────────────────────────────────

    def register_glyph(self, content: str, arity: int = 1,
                       wall_encoding: str = "X.0",
                       e8_coords: list[float] = None) -> dict:
        glyph_id = self._generate_glyph_id(content)
        wall_info = self._parse_wall(wall_encoding)

        glyph = {
            "glyph_id": glyph_id, "content": content, "arity": arity,
            "wall_encoding": wall_encoding, "wall_info": wall_info,
            "e8_coords": e8_coords or [0.0] * 8,
            "shell": 3, "bonds": [], "mass": arity,
            "energy": self._compute_energy(arity),
            "created_at": time.time(), "absorbed_by": None, "alive": True,
        }

        glyph["shell"] = self._assign_shell(glyph)
        self._glyphs[glyph_id] = glyph
        self._stats["registered"] += 1

        logger.info("Registered glyph %s: arity=%d wall=%s shell=%d",
                    glyph_id, arity, wall_encoding, glyph["shell"])

        if self._governance:
            from governance.engine import BoundaryEvent
            self._governance.record_boundary_event(BoundaryEvent(
                event_id=f"glyph-reg-{glyph_id}",
                timestamp=time.time(), entropy_delta=0.0,
                receipt_data={"glyph_id": glyph_id, "arity": arity},
                boundary_type="glyph_register",
            ))

        return {
            "glyph_id": glyph_id, "content": content[:50],
            "arity": arity, "wall_encoding": wall_encoding,
            "wall_info": wall_info, "shell": glyph["shell"],
            "mass": glyph["mass"], "energy": round(glyph["energy"], 6),
            "total_glyphs": len(self._glyphs),
        }

    def bond_glyphs(self, glyph_a: str, glyph_b: str) -> dict:
        ga = self._glyphs.get(glyph_a)
        gb = self._glyphs.get(glyph_b)

        if not ga:
            raise ValueError(f"Glyph {glyph_a} not found")
        if not gb:
            raise ValueError(f"Glyph {glyph_b} not found")
        if not ga["alive"] or not gb["alive"]:
            raise ValueError("Cannot bond absorbed glyphs")
        if glyph_a == glyph_b:
            raise ValueError("Cannot bond glyph to itself")

        if glyph_b in ga.get("bonds", []):
            return {"bonded": False, "reason": "Already bonded",
                    "glyph_a": glyph_a, "glyph_b": glyph_b}

        if not self._check_arity_compatible(ga, gb):
            self._stats["bonds_rejected"] += 1
            return {
                "bonded": False,
                "reason": f"Combined arity {ga['arity'] + gb['arity']} exceeds max {MAX_ARITY}",
                "glyph_a": glyph_a, "glyph_b": glyph_b,
                "arity_a": ga["arity"], "arity_b": gb["arity"],
            }

        ga["bonds"].append(glyph_b)
        gb["bonds"].append(glyph_a)

        ga["mass"] = self._compute_mass(ga)
        gb["mass"] = self._compute_mass(gb)
        ga["energy"] = self._compute_energy(ga["mass"])
        gb["energy"] = self._compute_energy(gb["mass"])

        ga["shell"] = self._assign_shell(ga)
        gb["shell"] = self._assign_shell(gb)

        bond_type = "DUST" if len(ga["bonds"]) <= 1 and len(gb["bonds"]) <= 1 else "COMPOSITE"

        bond_record = {
            "bond_id": hashlib.sha256(
                f"{glyph_a}:{glyph_b}:{time.time()}".encode()
            ).hexdigest()[:12],
            "glyph_a": glyph_a, "glyph_b": glyph_b, "bond_type": bond_type,
            "combined_arity": ga["arity"] + gb["arity"],
            "distance": round(self._e8_distance(ga["e8_coords"], gb["e8_coords"]), 6),
            "created_at": time.time(),
        }
        self._bonds.append(bond_record)
        self._stats["bonds_formed"] += 1

        codon = None
        shared_bonds = set(ga["bonds"]) & set(gb["bonds"])
        for shared_id in shared_bonds:
            if shared_id != glyph_a and shared_id != glyph_b:
                codon = self._form_codon([glyph_a, glyph_b, shared_id])
                if codon:
                    self._stats["codons_formed"] += 1
                    break

        result = {
            "bonded": True, "bond": bond_record,
            "glyph_a_mass": ga["mass"], "glyph_b_mass": gb["mass"],
            "glyph_a_shell": ga["shell"], "glyph_b_shell": gb["shell"],
        }
        if codon:
            result["codon"] = codon
        return result

    def assign_shell(self, glyph_id: str) -> dict:
        glyph = self._glyphs.get(glyph_id)
        if not glyph:
            raise ValueError(f"Glyph {glyph_id} not found")

        old_shell = glyph["shell"]
        new_shell = self._assign_shell(glyph)
        glyph["shell"] = new_shell
        wall_info = self._parse_wall(glyph["wall_encoding"])

        return {
            "glyph_id": glyph_id, "old_shell": old_shell,
            "new_shell": new_shell, "changed": old_shell != new_shell,
            "wall_info": wall_info, "bond_count": len(glyph.get("bonds", [])),
            "mass": glyph["mass"], "energy": round(glyph["energy"], 6),
        }

    def get_lexicon(self, shell: Optional[int] = None,
                    min_arity: int = 1, max_arity: int = 3,
                    alive_only: bool = True,
                    offset: int = 0, limit: int = 50) -> dict:
        filtered = []
        for gid, g in self._glyphs.items():
            if alive_only and not g["alive"]:
                continue
            if shell is not None and g["shell"] != shell:
                continue
            if g["arity"] < min_arity or g["arity"] > max_arity:
                continue
            filtered.append({
                "glyph_id": gid, "content": g["content"][:50],
                "arity": g["arity"], "wall_encoding": g["wall_encoding"],
                "shell": g["shell"], "mass": g["mass"],
                "energy": round(g["energy"], 6),
                "bonds": len(g.get("bonds", [])), "alive": g["alive"],
            })

        filtered.sort(key=lambda x: -x["mass"])
        total = len(filtered)
        page = filtered[offset:offset + limit]

        return {"total": total, "offset": offset, "limit": limit,
                "returned": len(page), "glyphs": page}

    def get_glyph(self, glyph_id: str) -> dict:
        glyph = self._glyphs.get(glyph_id)
        if not glyph:
            raise ValueError(f"Glyph {glyph_id} not found")

        bond_details = []
        for bid in glyph.get("bonds", []):
            bonded = self._glyphs.get(bid)
            if bonded:
                bond_details.append({
                    "glyph_id": bid, "content": bonded["content"][:30],
                    "arity": bonded["arity"], "mass": bonded["mass"],
                    "alive": bonded["alive"],
                })

        wall_info = self._parse_wall(glyph["wall_encoding"])

        return {
            "glyph_id": glyph_id, "content": glyph["content"],
            "arity": glyph["arity"], "wall_encoding": glyph["wall_encoding"],
            "wall_info": wall_info, "shell": glyph["shell"],
            "mass": glyph["mass"], "energy": round(glyph["energy"], 6),
            "e8_coords": glyph["e8_coords"],
            "bonds": bond_details, "bond_count": len(bond_details),
            "alive": glyph["alive"], "absorbed_by": glyph["absorbed_by"],
            "created_at": glyph["created_at"],
            "superperm_position": min(glyph["arity"], 4),
        }

    def run_ecology(self, interaction_radius: float = 2.0,
                    steps: int = 1) -> dict:
        step_results = []
        for step_num in range(steps):
            alive_glyphs = [g for g in self._glyphs.values() if g["alive"]]
            if len(alive_glyphs) < 2:
                step_results.append({
                    "step": step_num, "absorptions": 0,
                    "reason": "fewer than 2 alive",
                })
                break

            mass_before = sum(g["mass"] for g in alive_glyphs)
            absorptions = 0

            for i in range(len(alive_glyphs)):
                if not alive_glyphs[i]["alive"]:
                    continue
                for j in range(i + 1, len(alive_glyphs)):
                    if not alive_glyphs[j]["alive"]:
                        continue

                    dist = self._e8_distance(
                        alive_glyphs[i]["e8_coords"],
                        alive_glyphs[j]["e8_coords"],
                    )
                    if dist > interaction_radius:
                        continue

                    if alive_glyphs[i]["mass"] > alive_glyphs[j]["mass"]:
                        winner, loser = alive_glyphs[i], alive_glyphs[j]
                    elif alive_glyphs[j]["mass"] > alive_glyphs[i]["mass"]:
                        winner, loser = alive_glyphs[j], alive_glyphs[i]
                    else:
                        continue

                    winner["mass"] += loser["mass"]
                    winner["energy"] = self._compute_energy(winner["mass"])
                    winner["shell"] = self._assign_shell(winner)

                    loser["alive"] = False
                    loser["absorbed_by"] = winner["glyph_id"]
                    absorptions += 1
                    self._stats["absorptions"] += 1

            mass_after = sum(
                g["mass"] for g in self._glyphs.values() if g["alive"]
            )
            total_mass = sum(g["mass"] for g in self._glyphs.values())

            self._ecology_steps += 1
            self._stats["ecology_steps"] += 1

            step_result = {
                "step": step_num, "absorptions": absorptions,
                "alive_before": len(alive_glyphs),
                "alive_after": sum(1 for g in self._glyphs.values() if g["alive"]),
                "mass_before": mass_before,
                "mass_after_alive": mass_after,
                "total_mass": total_mass,
                "conservation_holds": abs(total_mass - mass_before) < 0.001,
            }
            step_results.append(step_result)

            if absorptions == 0:
                step_result["reason"] = "no interactions in radius"
                break

        self._ecology_log.extend(step_results)
        if len(self._ecology_log) > 500:
            self._ecology_log[:] = self._ecology_log[-500:]

        if self._governance:
            from governance.engine import BoundaryEvent
            self._governance.record_boundary_event(BoundaryEvent(
                event_id=f"glyph-ecology-{int(time.time())}",
                timestamp=time.time(), entropy_delta=0.0,
                receipt_data={"steps": len(step_results),
                              "absorptions": sum(s["absorptions"] for s in step_results)},
                boundary_type="glyph_ecology",
            ))

        return {
            "steps_run": len(step_results),
            "total_ecology_steps": self._ecology_steps,
            "results": step_results,
            "alive_glyphs": sum(1 for g in self._glyphs.values() if g["alive"]),
            "dead_glyphs": sum(1 for g in self._glyphs.values() if not g["alive"]),
        }

    @property
    def stats(self) -> dict:
        alive = [g for g in self._glyphs.values() if g["alive"]]
        shell_counts = defaultdict(int)
        arity_counts = defaultdict(int)
        for g in alive:
            shell_counts[g["shell"]] += 1
            arity_counts[g["arity"]] += 1

        return {
            "service": "glyph", "total_glyphs": len(self._glyphs),
            "alive_glyphs": len(alive),
            "dead_glyphs": len(self._glyphs) - len(alive),
            "total_bonds": len(self._bonds),
            "shell_distribution": dict(shell_counts),
            "arity_distribution": dict(arity_counts),
            "total_mass": sum(g["mass"] for g in alive),
            "total_energy": round(sum(g["energy"] for g in alive), 6),
            "coupling_constant": round(COUPLING_CONSTANT, 6),
            "ecology_steps": self._stats["ecology_steps"],
            "absorptions": self._stats["absorptions"],
            "codons_formed": self._stats["codons_formed"],
            "bonds_formed": self._stats["bonds_formed"],
            "bonds_rejected": self._stats["bonds_rejected"],
            "recent_ecology": self._ecology_log[-5:],
        }

    @property
    def health(self) -> dict:
        return {
            "ok": True, "service": "glyph",
            "glyphs": len(self._glyphs), "bonds": len(self._bonds),
            "ecology_steps": self._ecology_steps,
            "coupling_constant": round(COUPLING_CONSTANT, 6),
            "superperm_length": len(SUPERPERM_N4),
        }

    @property
    def superperm(self) -> dict:
        return {
            "n4_string": SUPERPERM_N4, "length": len(SUPERPERM_N4),
            "palindromic": SUPERPERM_N4 == SUPERPERM_N4[::-1],
            "permutations_contained": 24, "max_arity": MAX_ARITY,
            "positions": {
                "1": "atomic glyph (width 1)",
                "2": "dust composite (width 2)",
                "3": "triad composite (width 3)",
                "4": "1-ary addition group (4 atomics via addition, not concat)",
            },
            "arity_rules": {
                "max_concat_arity": 3,
                "position_4_rule": "Requires 1-ary addition group, NOT concatenation",
                "bond_rule": "Two glyphs bond if combined arity <= 3",
            },
        }
