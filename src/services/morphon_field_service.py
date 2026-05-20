"""MorphonFieldService — M0, observation functors, potential field, MGLC, MorphonBeam."""
from __future__ import annotations

import hashlib
import json
import logging
import math
import os
import time
import uuid
from collections import Counter
from typing import Any, Dict, List, Optional

from governance.engine import GeometricGovernance, BoundaryEvent

logger = logging.getLogger("morphon_field_service")

_host = "host.docker.internal"

PORT = int(os.environ.get("PORT", "8000"))
COUPLING = float(os.environ.get("COUPLING", "0.030076"))
PG_URL = os.environ.get("PG_URL", "")
PHI = (1 + math.sqrt(5)) / 2


class GeometrySpec:
    def __init__(self, name: str, dimension: int, rank: int, root_count: int, properties: Dict[str, Any] = None):
        self.name = name
        self.dimension = dimension
        self.rank = rank
        self.root_count = root_count
        self.properties = properties or {}


GEOMETRIES = {
    "E6":     GeometrySpec("E6", 6, 6, 72, {"triality": True}),
    "E7":     GeometrySpec("E7", 7, 7, 126, {}),
    "E8":     GeometrySpec("E8", 8, 8, 240, {"coupling": COUPLING, "kissing": 240}),
    "Leech":  GeometrySpec("Leech", 24, 0, 0, {"kissing": 196560, "rootless": True}),
    "D4":     GeometrySpec("D4", 4, 4, 24, {"triality": True}),
    "A1":     GeometrySpec("A1", 1, 1, 2, {"su2": True}),
    "A2":     GeometrySpec("A2", 2, 2, 6, {"su3": True}),
    "G2":     GeometrySpec("G2", 2, 2, 12, {}),
    "F4":     GeometrySpec("F4", 4, 4, 48, {}),
    "BCC":    GeometrySpec("BCC", 3, 3, 8, {"lattice_type": "body-centered-cubic"}),
    "FCC":    GeometrySpec("FCC", 3, 3, 12, {"lattice_type": "face-centered-cubic"}),
}


class ObservationResult:
    def __init__(self, functor_name: str = "", geometry_name: str = "", dimension: int = 0,
                 coordinates: List[float] = None, morphon_z: float = 0.0, morphon_phi: float = 0.0,
                 morphon_dphi: float = 0.0, morphon_R: float = 0.0,
                 labels: List[str] = None, receipt: str = ""):
        self.functor_name = functor_name
        self.geometry_name = geometry_name
        self.dimension = dimension
        self.coordinates = coordinates or []
        self.morphon_z = morphon_z
        self.morphon_phi = morphon_phi
        self.morphon_dphi = morphon_dphi
        self.morphon_R = morphon_R
        self.labels = labels or []
        self.receipt = receipt


class ObservationFunctor:
    def __init__(self, name: str, target_geometry: str, bias: Dict[str, float] = None):
        self.name = name
        self.target = target_geometry
        self.bias = bias or {}
        self.observation_count = 0

    def observe(self, content: str, e8_coords: List[float] = None) -> ObservationResult:
        self.observation_count += 1
        geo = GEOMETRIES.get(self.target, GEOMETRIES["E8"])
        z = self._shannon_entropy(content)
        e8 = e8_coords or [0.0] * 8
        R = math.sqrt(sum(c * c for c in e8[:geo.dimension]))
        phi = R * R
        dphi = -z * COUPLING
        projected = e8[:geo.dimension]
        for i in range(len(projected)):
            dim_key = f"dim_{i}"
            if dim_key in self.bias:
                projected[i] *= self.bias[dim_key]
        return ObservationResult(
            functor_name=self.name, geometry_name=geo.name,
            dimension=geo.dimension, coordinates=projected,
            morphon_z=z, morphon_phi=phi, morphon_dphi=dphi, morphon_R=R,
            receipt=hashlib.sha256(f"{self.name}:{content[:50]}:{time.time()}".encode()).hexdigest()[:16],
        )

    @staticmethod
    def _shannon_entropy(text: str) -> float:
        if not text:
            return 0.0
        freq = Counter(text)
        total = len(text)
        entropy = -sum((c / total) * math.log2(c / total) for c in freq.values() if c > 0)
        max_entropy = math.log2(min(len(freq), 256)) if freq else 1.0
        return min(entropy / max(max_entropy, 1e-10), 1.0)


FUNCTORS = {
    "pipeline":   ObservationFunctor("pipeline", "E8", {"dim_0": 1.0, "dim_7": COUPLING}),
    "tarpit":     ObservationFunctor("tarpit", "E6", {"dim_0": PHI}),
    "crystal":    ObservationFunctor("crystal", "Leech"),
    "snap":       ObservationFunctor("snap", "E8"),
    "mdhg":       ObservationFunctor("mdhg", "E8"),
    "morsr":      ObservationFunctor("morsr", "E8", {"dim_0": 1.0 / 240}),
    "daemon":     ObservationFunctor("daemon", "Leech"),
    "economy":    ObservationFunctor("economy", "D4"),
    "agent":      ObservationFunctor("agent", "E8"),
    "simulation": ObservationFunctor("simulation", "E8"),
    "board":      ObservationFunctor("board", "A2"),
}


class MorphonPotential:
    def __init__(self, morphon_id: str = "", committed_geometry: str = "",
                 committed_coords: List[float] = None, committed_dphi: float = 0.0,
                 open_paths: List[Dict] = None, total_potential: float = 0.0,
                 labels: List[str] = None):
        self.morphon_id = morphon_id or f"mpot-{uuid.uuid4().hex[:8]}"
        self.committed_geometry = committed_geometry
        self.committed_coords = committed_coords or []
        self.committed_dphi = committed_dphi
        self.open_paths = open_paths or []
        self.total_potential = total_potential
        self.labels = labels or []


def compute_potential(content: str, e8_coords: List[float] = None) -> MorphonPotential:
    results = []
    for name, functor in FUNCTORS.items():
        obs = functor.observe(content, e8_coords)
        results.append((name, obs))
    results.sort(key=lambda x: x[1].morphon_dphi)
    committed = results[0] if results else None
    open_paths = []
    for name, obs in results[1:]:
        open_paths.append({"functor": name, "geometry": obs.geometry_name,
                           "dphi": obs.morphon_dphi, "R": obs.morphon_R})
    pot = MorphonPotential(
        committed_geometry=committed[1].geometry_name if committed else "",
        committed_coords=committed[1].coordinates if committed else [],
        committed_dphi=committed[1].morphon_dphi if committed else 0.0,
        open_paths=open_paths,
        total_potential=sum(abs(obs.morphon_dphi) for _, obs in results),
    )
    return pot


def overlay(content: str, e8_coords: List[float] = None) -> Dict:
    pot = compute_potential(content, e8_coords)
    return {"operation": "overlay", "morphon_id": pot.morphon_id,
            "committed_geometry": pot.committed_geometry, "dphi": pot.committed_dphi,
            "open_paths": len(pot.open_paths), "total_potential": pot.total_potential, "state": "staged"}


def commit_op(morphon_id: str, dphi: float) -> Dict:
    if dphi > 0:
        return {"operation": "commit", "morphon_id": morphon_id,
                "state": "rejected", "reason": f"dPhi={dphi:.4f} > 0"}
    return {"operation": "commit", "morphon_id": morphon_id, "state": "crystal_active", "dphi": dphi}


def refocus(morphon_id: str, dphi: float) -> Dict:
    return {"operation": "refocus", "morphon_id": morphon_id,
            "state": "enrichment_queue", "dphi": dphi}


def morphon_beam(e8_coords: List[float], max_iter: int = 100) -> Dict:
    c_real = e8_coords[0] if e8_coords else 0.0
    c_imag = e8_coords[1] if len(e8_coords) > 1 else 0.0
    z_r, z_i = 0.0, 0.0
    trajectory = []
    for n in range(max_iter):
        z_r2, z_i2 = z_r * z_r, z_i * z_i
        trajectory.append({"r": round(z_r, 6), "i": round(z_i, 6), "norm": round(math.sqrt(z_r2 + z_i2), 6)})
        if z_r2 + z_i2 > 4.0:
            return {"escaped": True, "iterations": n, "escape_norm": math.sqrt(z_r2 + z_i2),
                    "trajectory": trajectory[-10:]}
        z_i = 2 * z_r * z_i + c_imag
        z_r = z_r2 - z_i2 + c_real
    return {"escaped": False, "iterations": max_iter,
            "final_norm": math.sqrt(z_r * z_r + z_i * z_i),
            "trajectory": trajectory[-10:]}


class MorphonFieldService:
    """M0, observation functors, potential field, MGLC, MorphonBeam."""

    def __init__(self, governance: Optional[GeometricGovernance] = None):
        self.governance = governance

    def observe(self, content: str, functor: str = "pipeline",
                e8_coords: List[float] = None) -> Dict[str, Any]:
        f = FUNCTORS.get(functor)
        if not f:
            return {"error": f"Functor '{functor}' not found. Available: {list(FUNCTORS.keys())}"}
        result = f.observe(content, e8_coords or None)
        if self.governance:
            self.governance.record_boundary_event(BoundaryEvent(
                event_id=result.receipt, timestamp=time.time(), entropy_delta=result.morphon_dphi,
                receipt_data={"functor": functor, "morphon_z": result.morphon_z, "morphon_R": result.morphon_R},
                boundary_type="morphon_observe",
            ))
        return {"functor_name": result.functor_name, "geometry_name": result.geometry_name,
                "dimension": result.dimension, "coordinates": result.coordinates,
                "morphon_z": result.morphon_z, "morphon_phi": result.morphon_phi,
                "morphon_dphi": result.morphon_dphi, "morphon_R": result.morphon_R,
                "receipt": result.receipt}

    def potential(self, content: str, e8_coords: List[float] = None) -> Dict[str, Any]:
        pot = compute_potential(content, e8_coords or None)
        return {"morphon_id": pot.morphon_id, "committed_geometry": pot.committed_geometry,
                "committed_coords": pot.committed_coords, "committed_dphi": pot.committed_dphi,
                "open_paths": pot.open_paths, "total_potential": pot.total_potential}

    def overlay(self, content: str, e8_coords: List[float] = None) -> Dict[str, Any]:
        return overlay(content, e8_coords or None)

    def commit(self, morphon_id: str, dphi: float) -> Dict[str, Any]:
        return commit_op(morphon_id, dphi)

    def refocus(self, morphon_id: str, dphi: float) -> Dict[str, Any]:
        return refocus(morphon_id, dphi)

    def beam(self, e8_coords: List[float], max_iter: int = 100) -> Dict[str, Any]:
        result = morphon_beam(e8_coords, max_iter)
        if self.governance:
            self.governance.record_boundary_event(BoundaryEvent(
                event_id=f"beam-{uuid.uuid4().hex[:8]}", timestamp=time.time(), entropy_delta=0.0,
                receipt_data={"escaped": result.get("escaped"), "iterations": result.get("iterations")},
                boundary_type="morphon_beam",
            ))
        return result

    def geometries(self) -> Dict[str, Any]:
        return {name: {"name": g.name, "dimension": g.dimension, "rank": g.rank,
                       "root_count": g.root_count, "properties": g.properties}
                for name, g in GEOMETRIES.items()}

    def functors(self) -> Dict[str, Any]:
        return {name: {"target": f.target, "observations": f.observation_count, "bias": f.bias}
                for name, f in FUNCTORS.items()}

    def health(self) -> Dict[str, Any]:
        total_obs = sum(f.observation_count for f in FUNCTORS.values())
        return {"ok": True, "service": "opencmplx-morphon-field", "version": "2.0.0",
                "geometries": len(GEOMETRIES), "functors": len(FUNCTORS),
                "total_observations": total_obs}
