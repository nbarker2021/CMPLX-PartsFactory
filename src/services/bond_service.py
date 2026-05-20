"""BondService — Two-layer bond chemistry: geometric (Grain/Dust/Triad) + semantic (Codon assembly)."""
from __future__ import annotations

import hashlib
import json
import logging
import math
import os
import time
import uuid
from collections import Counter
from typing import Any, Dict, FrozenSet, List, Optional, Set, Tuple

from governance.engine import GeometricGovernance, BoundaryEvent

logger = logging.getLogger("bond_service")

_host = "host.docker.internal"

PORT = int(os.environ.get("PORT", "8000"))
EPSILON = float(os.environ.get("BOND_EPSILON", "0.1"))
COUPLING = float(os.environ.get("COUPLING", "0.030076"))


class DimensionalExtent:
    def __init__(self, min_vals: List[float] = None, max_vals: List[float] = None):
        self.min_vals = min_vals or []
        self.max_vals = max_vals or []

    @property
    def centroid(self) -> List[float]:
        if not self.min_vals or not self.max_vals:
            return []
        return [(a + b) / 2.0 for a, b in zip(self.min_vals, self.max_vals)]

    @property
    def span(self) -> List[float]:
        if not self.min_vals or not self.max_vals:
            return []
        return [b - a for a, b in zip(self.min_vals, self.max_vals)]


class Grain:
    def __init__(self, grain_id: str = "", content: str = "", e8_coords: List[float] = None,
                 snap_labels: List[str] = None, extent: Optional[DimensionalExtent] = None, mass: float = 0.0):
        self.grain_id = grain_id or str(uuid.uuid4())[:12]
        self.content = content
        self.e8_coords = e8_coords or []
        self.snap_labels = snap_labels or []
        self.extent = extent
        self.mass = mass
        if self.mass == 0.0 and self.e8_coords:
            self.mass = math.sqrt(sum(x * x for x in self.e8_coords)) or 0.001


class Dust:
    def __init__(self, dust_id: str = "", grains: List[Grain] = None,
                 pole_plus: List[float] = None, pole_minus: List[float] = None,
                 mediator: List[float] = None, certificate: Dict[str, Any] = None,
                 bond_mass: float = 0.0, sin_theta: float = 0.0):
        self.dust_id = dust_id or str(uuid.uuid4())[:12]
        self.grains = grains or []
        self.pole_plus = pole_plus or []
        self.pole_minus = pole_minus or []
        self.mediator = mediator or []
        self.certificate = certificate or {}
        self.bond_mass = bond_mass
        self.sin_theta = sin_theta
        self.created_at = time.time()


class Triad:
    def __init__(self, triad_id: str = "", dusts: List[Dust] = None,
                 closure_certificate: Dict[str, Any] = None,
                 total_mass: float = 0.0, equidistance_error: float = 0.0):
        self.triad_id = triad_id or str(uuid.uuid4())[:12]
        self.dusts = dusts or []
        self.closure_certificate = closure_certificate or {}
        self.total_mass = total_mass
        self.equidistance_error = equidistance_error
        self.created_at = time.time()


class AtomNode:
    def __init__(self, atom_id: str = "", e8_coords: List[float] = None,
                 snap_labels: Set[str] = None, domain: str = "", content_hash: str = ""):
        self.atom_id = atom_id
        self.e8_coords = e8_coords or []
        self.snap_labels = snap_labels or set()
        self.domain = domain
        self.content_hash = content_hash

    @property
    def label_set(self) -> Set[str]:
        return set(self.snap_labels)


class Dimer:
    def __init__(self, dimer_id: str = "", atom_a: Optional[AtomNode] = None,
                 atom_b: Optional[AtomNode] = None, shared_labels: List[str] = None,
                 union_labels: List[str] = None, emergent_labels: List[str] = None,
                 bond_strength: float = 0.0):
        self.dimer_id = dimer_id
        self.atom_a = atom_a
        self.atom_b = atom_b
        self.shared_labels = shared_labels or []
        self.union_labels = union_labels or []
        self.emergent_labels = emergent_labels or []
        self.bond_strength = bond_strength
        self.created_at = time.time()


class Codon:
    def __init__(self, codon_id: str = "", members: List[AtomNode] = None,
                 dimers: List[Dimer] = None, all_labels: List[str] = None,
                 protein_labels: List[str] = None, domain_signature: str = "",
                 stability: float = 0.0, size_tier: str = "",
                 e8_closure_tier: str = ""):
        self.codon_id = codon_id
        self.members = members or []
        self.dimers = dimers or []
        self.all_labels = all_labels or []
        self.protein_labels = protein_labels or []
        self.domain_signature = domain_signature
        self.stability = stability
        self.size_tier = size_tier
        self.e8_closure_tier = e8_closure_tier
        self.created_at = time.time()


# ── Pure functions ──────────────────────────────────────────────────────────

def _dot(a: List[float], b: List[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def _norm(v: List[float]) -> float:
    return math.sqrt(sum(x * x for x in v))


def _sub(a: List[float], b: List[float]) -> List[float]:
    return [x - y for x, y in zip(a, b)]


def _add(a: List[float], b: List[float]) -> List[float]:
    return [x + y for x, y in zip(a, b)]


def _scale(v: List[float], s: float) -> List[float]:
    return [x * s for x in v]


def _midpoint(a: List[float], b: List[float]) -> List[float]:
    return [(x + y) / 2.0 for x, y in zip(a, b)]


def _sin_angle(a: List[float], b: List[float]) -> float:
    na, nb = _norm(a), _norm(b)
    if na < 1e-12 or nb < 1e-12:
        return 0.0
    cos_theta = _dot(a, b) / (na * nb)
    cos_theta = max(-1.0, min(1.0, cos_theta))
    sin_sq = 1.0 - cos_theta * cos_theta
    return math.sqrt(max(0.0, sin_sq))


def _dist(a: List[float], b: List[float]) -> float:
    return _norm(_sub(a, b))


def geometric_bond(grain_a: Grain, grain_b: Grain, epsilon: float = EPSILON) -> Optional[Dust]:
    if not grain_a.e8_coords or not grain_b.e8_coords:
        return None
    if grain_a.grain_id == grain_b.grain_id:
        return None
    dim = max(len(grain_a.e8_coords), len(grain_b.e8_coords))
    va = grain_a.e8_coords + [0.0] * (dim - len(grain_a.e8_coords))
    vb = grain_b.e8_coords + [0.0] * (dim - len(grain_b.e8_coords))
    sin_theta = _sin_angle(va, vb)
    if sin_theta <= epsilon:
        return None
    mid = _midpoint(va, vb)
    direction = _sub(va, vb)
    dir_norm = _norm(direction)
    if dir_norm > 1e-12:
        direction = _scale(direction, 0.5 / dir_norm)
    pole_plus = _add(mid, direction)
    pole_minus = _sub(mid, direction)
    mediator = mid
    mass_a = grain_a.mass or _norm(va)
    mass_b = grain_b.mass or _norm(vb)
    bond_mass = math.sqrt(mass_a * mass_b) * sin_theta
    certificate = {
        "type": "geometric_bond", "sin_theta": round(sin_theta, 6), "epsilon": epsilon,
        "mass_a": round(mass_a, 6), "mass_b": round(mass_b, 6),
        "bond_mass": round(bond_mass, 6), "dimension": dim,
        "grain_a_id": grain_a.grain_id, "grain_b_id": grain_b.grain_id,
    }
    return Dust(grains=[grain_a, grain_b], pole_plus=pole_plus, pole_minus=pole_minus,
                mediator=mediator, certificate=certificate, bond_mass=bond_mass, sin_theta=sin_theta)


def check_triad_closure(dust_ab: Dust, dust_bc: Dust, dust_ca: Dust,
                         tolerance: float = 0.3) -> Optional[Triad]:
    if not all([dust_ab, dust_bc, dust_ca]):
        return None
    total_bond_mass = dust_ab.bond_mass + dust_bc.bond_mass + dust_ca.bond_mass
    all_grains = set()
    for d in [dust_ab, dust_bc, dust_ca]:
        for g in d.grains:
            all_grains.add(g.grain_id)
    if len(all_grains) != 3:
        return None
    d_ab = _dist(dust_ab.mediator, dust_bc.mediator) if dust_ab.mediator and dust_bc.mediator else 0
    d_bc = _dist(dust_bc.mediator, dust_ca.mediator) if dust_bc.mediator and dust_ca.mediator else 0
    d_ca = _dist(dust_ca.mediator, dust_ab.mediator) if dust_ca.mediator and dust_ab.mediator else 0
    distances = [d for d in [d_ab, d_bc, d_ca] if d > 0]
    if not distances:
        equidistance_error = 0.0
    else:
        avg_dist = sum(distances) / len(distances)
        if avg_dist < 1e-12:
            equidistance_error = 0.0
        else:
            equidistance_error = max(abs(d - avg_dist) for d in distances) / avg_dist
    if equidistance_error > tolerance:
        return None
    closure_cert = {
        "type": "triad_closure", "total_bond_mass": round(total_bond_mass, 6),
        "equidistance_error": round(equidistance_error, 6), "tolerance": tolerance,
        "grain_ids": sorted(all_grains),
        "dust_ids": [dust_ab.dust_id, dust_bc.dust_id, dust_ca.dust_id],
    }
    return Triad(dusts=[dust_ab, dust_bc, dust_ca], closure_certificate=closure_cert,
                 total_mass=total_bond_mass, equidistance_error=equidistance_error)


def jaccard(a: Set, b: Set) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def bron_kerbosch(R: Set[str], P: Set[str], X: Set[str],
                  graph: Dict[str, Set[str]], cliques: List[FrozenSet[str]],
                  max_size: int = 6) -> None:
    if not P and not X:
        if len(R) >= 3:
            cliques.append(frozenset(R))
        return
    if len(R) >= max_size:
        cliques.append(frozenset(R))
        return
    candidates = P | X
    if not candidates:
        return
    pivot = max(candidates, key=lambda v: len(graph.get(v, set()) & P))
    for v in list(P - graph.get(pivot, set())):
        neighbors = graph.get(v, set())
        bron_kerbosch(R | {v}, P & neighbors, X & neighbors, graph, cliques, max_size)
        P = P - {v}
        X = X | {v}


def _emergent_from_bond(atom_a: AtomNode, atom_b: AtomNode, shared: Set[str]) -> List[str]:
    emergent = []
    if atom_a.domain and atom_b.domain and atom_a.domain != atom_b.domain:
        pair = "_".join(sorted([atom_a.domain, atom_b.domain]))
        emergent.append(f"geometric_{pair}_bond")
    for lbl in sorted(shared)[:5]:
        parts = lbl.replace("SNAP", "").split("_")
        if len(parts) >= 2:
            emergent.append(f"SNAPcodon_{parts[-1]}_depth2")
    if atom_a.domain:
        emergent.append(f"bonds_with_{atom_a.domain}")
    if atom_b.domain:
        emergent.append(f"bonds_with_{atom_b.domain}")
    a_only = atom_a.label_set - atom_b.label_set - shared
    b_only = atom_b.label_set - atom_a.label_set - shared
    if a_only and b_only:
        a_cluster = sorted(a_only)[0].split("_")[-1] if a_only else ""
        b_cluster = sorted(b_only)[0].split("_")[-1] if b_only else ""
        if a_cluster and b_cluster and a_cluster != b_cluster:
            emergent.append(f"bridge_{a_cluster}_{b_cluster}")
    return list(dict.fromkeys(emergent))


def _emergent_from_codon(members: List[AtomNode], all_labels: Set[str]) -> Tuple[List[str], str, str]:
    emergent = []
    domains = list(dict.fromkeys(m.domain for m in members if m.domain))[:4]
    if len(domains) >= 2:
        emergent.append(f"protein_{'_'.join(sorted(domains))}")
    n = len(members)
    if n == 3: size_tier = "trimer"
    elif n == 4: size_tier = "tetramer"
    elif n == 5: size_tier = "pentamer"
    elif n == 6: size_tier = "hexamer"
    else: size_tier = f"polymer_{n}"
    emergent.append(f"SNAPcodon_tier_{size_tier}")
    if domains:
        all_domains = [m.domain for m in members if m.domain]
        counts = Counter(all_domains)
        consensus = counts.most_common(1)[0][0] if counts else domains[0]
        emergent.append(f"SNAPcodon_consensus_{consensus}")
    e8_members = [m for m in members if m.e8_coords]
    e8_closure_tier = "unknown"
    if len(e8_members) >= 3:
        dim = max(len(m.e8_coords) for m in e8_members)
        coords = []
        for m in e8_members:
            padded = list(m.e8_coords) + [0.0] * (dim - len(m.e8_coords))
            coords.append(padded)
        centroid = [sum(c[i] for c in coords) / len(coords) for i in range(dim)]
        cnorm = _norm(centroid)
        if cnorm < 1.0: e8_closure_tier = "E8_core"
        elif cnorm < 2.0: e8_closure_tier = "E8_shell"
        elif cnorm < 4.0: e8_closure_tier = "E8_mid"
        else: e8_closure_tier = "E8_outer"
        emergent.append(f"SNAPlattice_codon_{e8_closure_tier}")
    return emergent, size_tier, e8_closure_tier


class BondAssembler:
    """Full two-layer bond assembly engine."""

    MIN_BOND_STRENGTH = 0.05
    MIN_CODON_STABILITY = 0.3
    MIN_CODON_SIZE = 3

    def __init__(self):
        self._atoms: Dict[str, AtomNode] = {}
        self._grains: Dict[str, Grain] = {}
        self._dimers: List[Dimer] = []
        self._dusts: List[Dust] = []
        self._triads: List[Triad] = []
        self._codons: List[Codon] = []
        self._emergent_labels: List[str] = []

    def register_atom(self, atom: AtomNode) -> None:
        self._atoms[atom.atom_id] = atom

    def register_grain(self, grain: Grain) -> None:
        self._grains[grain.grain_id] = grain

    def geometric_bond_all(self) -> List[Dust]:
        grains = list(self._grains.values())
        new_dusts = []
        existing = {frozenset(g.grain_id for g in d.grains) for d in self._dusts}
        for i, ga in enumerate(grains):
            for gb in grains[i + 1:]:
                pair = frozenset([ga.grain_id, gb.grain_id])
                if pair in existing:
                    continue
                dust = geometric_bond(ga, gb, EPSILON)
                if dust:
                    new_dusts.append(dust)
                    self._dusts.append(dust)
                    existing.add(pair)
        return new_dusts

    def find_triads(self) -> List[Triad]:
        grain_dusts: Dict[str, List[Dust]] = {}
        for d in self._dusts:
            for g in d.grains:
                grain_dusts.setdefault(g.grain_id, []).append(d)
        new_triads = []
        existing_triads = {frozenset(t.closure_certificate.get("grain_ids", [])) for t in self._triads}
        grain_ids = list(grain_dusts.keys())
        for gid in grain_ids:
            for d1 in grain_dusts.get(gid, []):
                for d2 in grain_dusts.get(gid, []):
                    if d1.dust_id >= d2.dust_id:
                        continue
                    others_1 = [g for g in d1.grains if g.grain_id != gid]
                    others_2 = [g for g in d2.grains if g.grain_id != gid]
                    if not others_1 or not others_2:
                        continue
                    o1_id = others_1[0].grain_id
                    o2_id = others_2[0].grain_id
                    if o1_id == o2_id:
                        continue
                    tri_key = frozenset([gid, o1_id, o2_id])
                    if tri_key in existing_triads:
                        continue
                    d3 = None
                    for candidate in self._dusts:
                        cids = {g.grain_id for g in candidate.grains}
                        if cids == {o1_id, o2_id}:
                            d3 = candidate
                            break
                    if d3:
                        triad = check_triad_closure(d1, d2, d3)
                        if triad:
                            new_triads.append(triad)
                            self._triads.append(triad)
                            existing_triads.add(tri_key)
        return new_triads

    def semantic_bond(self, atom_a: AtomNode, atom_b: AtomNode) -> Optional[Dimer]:
        if atom_a.atom_id == atom_b.atom_id:
            return None
        la, lb = atom_a.label_set, atom_b.label_set
        if not la or not lb:
            return None
        shared = la & lb
        union = la | lb
        strength = len(shared) / len(union) if union else 0.0
        if strength < self.MIN_BOND_STRENGTH:
            return None
        emergent = _emergent_from_bond(atom_a, atom_b, shared)
        dimer = Dimer(dimer_id=hashlib.sha256(f"{atom_a.atom_id}:{atom_b.atom_id}".encode()).hexdigest()[:16],
                      atom_a=atom_a, atom_b=atom_b, shared_labels=sorted(shared),
                      union_labels=sorted(union), emergent_labels=emergent, bond_strength=strength)
        self._dimers.append(dimer)
        self._emergent_labels.extend(emergent)
        return dimer

    def semantic_bond_all(self) -> List[Dimer]:
        atoms = list(self._atoms.values())
        new_dimers = []
        existing = {frozenset([d.atom_a.atom_id, d.atom_b.atom_id]) for d in self._dimers if d.atom_a and d.atom_b}
        for i, a in enumerate(atoms):
            for b in atoms[i + 1:]:
                pair = frozenset([a.atom_id, b.atom_id])
                if pair in existing:
                    continue
                d = self.semantic_bond(a, b)
                if d:
                    new_dimers.append(d)
                    existing.add(pair)
        return new_dimers

    def assemble_codons(self) -> List[Codon]:
        graph: Dict[str, Set[str]] = {}
        dimer_map: Dict[FrozenSet[str], Dimer] = {}
        for d in self._dimers:
            if not d.atom_a or not d.atom_b:
                continue
            a_id, b_id = d.atom_a.atom_id, d.atom_b.atom_id
            graph.setdefault(a_id, set()).add(b_id)
            graph.setdefault(b_id, set()).add(a_id)
            dimer_map[frozenset([a_id, b_id])] = d
        cliques: List[FrozenSet[str]] = []
        all_ids = set(graph.keys())
        if all_ids:
            bron_kerbosch(set(), all_ids, set(), graph, cliques, max_size=6)
        maximal = [c for c in cliques if not any(c < other for other in cliques)]
        existing_codon_ids = {c.codon_id for c in self._codons}
        new_codons = []
        for clique in maximal:
            codon_id = hashlib.sha256(":".join(sorted(clique)).encode()).hexdigest()[:16]
            if codon_id in existing_codon_ids:
                continue
            members = [self._atoms[aid] for aid in clique if aid in self._atoms]
            if len(members) < self.MIN_CODON_SIZE:
                continue
            internal_dimers = []
            for d in self._dimers:
                if d.atom_a and d.atom_b:
                    if frozenset([d.atom_a.atom_id, d.atom_b.atom_id]) <= clique:
                        internal_dimers.append(d)
            stability = (sum(d.bond_strength for d in internal_dimers) / len(internal_dimers)) if internal_dimers else 0.0
            if stability < self.MIN_CODON_STABILITY:
                continue
            all_labels: Set[str] = set()
            for m in members:
                all_labels.update(m.snap_labels)
            for d in internal_dimers:
                all_labels.update(d.emergent_labels)
            protein_labels, size_tier, e8_closure_tier = _emergent_from_codon(members, all_labels)
            domains = [m.domain for m in members if m.domain]
            primary_domain = Counter(domains).most_common(1)[0][0] if domains else "general"
            codon = Codon(codon_id=codon_id, members=members, dimers=internal_dimers,
                          all_labels=sorted(all_labels), protein_labels=protein_labels,
                          domain_signature=primary_domain, stability=stability,
                          size_tier=size_tier, e8_closure_tier=e8_closure_tier)
            self._codons.append(codon)
            self._emergent_labels.extend(protein_labels)
            new_codons.append(codon)
        return new_codons

    def run_full_pass(self) -> Dict[str, Any]:
        new_dusts = self.geometric_bond_all()
        new_triads = self.find_triads()
        new_dimers = self.semantic_bond_all()
        new_codons = self.assemble_codons()
        return {
            "geometric": {"new_dusts": len(new_dusts), "new_triads": len(new_triads),
                          "total_dusts": len(self._dusts), "total_triads": len(self._triads)},
            "semantic": {"new_dimers": len(new_dimers), "new_codons": len(new_codons),
                         "total_dimers": len(self._dimers), "total_codons": len(self._codons)},
            "total_atoms": len(self._atoms), "total_grains": len(self._grains),
            "emergent_labels": self._emergent_labels[-50:],
            "codon_summaries": [{"id": c.codon_id[:8], "members": len(c.members),
                                 "stability": round(c.stability, 3), "size_tier": c.size_tier,
                                 "e8_closure_tier": c.e8_closure_tier, "protein_labels": c.protein_labels}
                                for c in new_codons],
        }

    def stats(self) -> Dict[str, Any]:
        return {
            "atoms": len(self._atoms), "grains": len(self._grains),
            "dimers": len(self._dimers), "dusts": len(self._dusts),
            "triads": len(self._triads), "codons": len(self._codons),
            "emergent_label_count": len(set(self._emergent_labels)),
            "avg_dimer_strength": round(sum(d.bond_strength for d in self._dimers) / len(self._dimers), 4) if self._dimers else 0.0,
            "avg_dust_sin_theta": round(sum(d.sin_theta for d in self._dusts) / len(self._dusts), 4) if self._dusts else 0.0,
        }


class BondService:
    """Two-layer bond chemistry service: geometric (Grain/Dust/Triad) + semantic (Codon assembly)."""

    def __init__(self, governance: Optional[GeometricGovernance] = None):
        self.governance = governance
        self._assembler = BondAssembler()

    def bond_pair(self, atom_a_id: str, atom_a_labels: List[str], atom_a_domain: str,
                  atom_a_coords: List[float], atom_b_id: str, atom_b_labels: List[str],
                  atom_b_domain: str, atom_b_coords: List[float]) -> Dict[str, Any]:
        a = AtomNode(atom_id=atom_a_id, snap_labels=set(atom_a_labels), domain=atom_a_domain, e8_coords=atom_a_coords)
        b = AtomNode(atom_id=atom_b_id, snap_labels=set(atom_b_labels), domain=atom_b_domain, e8_coords=atom_b_coords)
        self._assembler.register_atom(a)
        self._assembler.register_atom(b)
        a_labels = set(atom_a_labels)
        b_labels = set(atom_b_labels)
        shared = a_labels & b_labels
        union_labels = a_labels | b_labels
        strength = jaccard(a_labels, b_labels)
        emergent = _emergent_from_bond(a, b, shared)
        z = 0
        if len(emergent) > 0: z = 1
        if len(emergent) > 2: z = 2
        if len(emergent) > 5: z = 3
        geo_result = None
        if atom_a_coords and atom_b_coords:
            grain_a = Grain(grain_id=atom_a_id, e8_coords=atom_a_coords, snap_labels=atom_a_labels)
            grain_b = Grain(grain_id=atom_b_id, e8_coords=atom_b_coords, snap_labels=atom_b_labels)
            self._assembler.register_grain(grain_a)
            self._assembler.register_grain(grain_b)
            dust = geometric_bond(grain_a, grain_b)
            if dust:
                self._assembler._dusts.append(dust)
                geo_result = {"bonded": True, "sin_theta": round(dust.sin_theta, 6),
                              "bond_mass": round(dust.bond_mass, 6), "dust_id": dust.dust_id}
        if strength >= self._assembler.MIN_BOND_STRENGTH:
            self._assembler.semantic_bond(a, b)
        if self.governance:
            self.governance.record_boundary_event(BoundaryEvent(
                event_id=f"bond-{atom_a_id[:8]}-{atom_b_id[:8]}", timestamp=time.time(),
                entropy_delta=strength * 0.1,
                receipt_data={"atom_a": atom_a_id, "atom_b": atom_b_id, "strength": strength},
                boundary_type="bond_pair",
            ))
        return {"bond_strength": round(strength, 4), "shared_labels": sorted(shared)[:10],
                "union_labels": len(union_labels), "emergent_labels": emergent[:10],
                "z_component": z, "emergence": z > 0, "geometric": geo_result}

    def geometric_bond_op(self, grain_a_id: str, grain_a_content: str, grain_a_coords: List[float],
                          grain_a_labels: List[str], grain_b_id: str, grain_b_content: str,
                          grain_b_coords: List[float], grain_b_labels: List[str],
                          epsilon: float = EPSILON) -> Dict[str, Any]:
        grain_a = Grain(grain_id=grain_a_id or str(uuid.uuid4())[:12], content=grain_a_content,
                        e8_coords=grain_a_coords, snap_labels=grain_a_labels)
        grain_b = Grain(grain_id=grain_b_id or str(uuid.uuid4())[:12], content=grain_b_content,
                        e8_coords=grain_b_coords, snap_labels=grain_b_labels)
        self._assembler.register_grain(grain_a)
        self._assembler.register_grain(grain_b)
        dust = geometric_bond(grain_a, grain_b, epsilon)
        if not dust:
            sin_val = _sin_angle(grain_a.e8_coords, grain_b.e8_coords) if grain_a.e8_coords and grain_b.e8_coords else 0.0
            return {"bonded": False, "reason": f"sin(theta)={sin_val:.4f} <= epsilon={epsilon}", "sin_theta": round(sin_val, 6)}
        self._assembler._dusts.append(dust)
        return {"bonded": True, "dust_id": dust.dust_id, "sin_theta": round(dust.sin_theta, 6),
                "bond_mass": round(dust.bond_mass, 6),
                "pole_plus": [round(x, 6) for x in dust.pole_plus[:8]],
                "pole_minus": [round(x, 6) for x in dust.pole_minus[:8]],
                "mediator": [round(x, 6) for x in dust.mediator[:8]], "certificate": dust.certificate}

    def assemble_codon(self, atoms: List[Dict[str, Any]]) -> Dict[str, Any]:
        if len(atoms) < 3:
            return {"error": "Need at least 3 atoms for codon"}
        nodes = []
        for a in atoms:
            node = AtomNode(atom_id=a["atom_id"], snap_labels=set(a.get("snap_labels", [])),
                            domain=a.get("domain", ""), e8_coords=a.get("e8_coords", []))
            self._assembler.register_atom(node)
            nodes.append(node)
        all_labels_sets = [set(a.get("snap_labels", [])) for a in atoms]
        intersection = all_labels_sets[0] if all_labels_sets else set()
        for s in all_labels_sets[1:]:
            intersection &= s
        union: Set[str] = set()
        for s in all_labels_sets:
            union |= s
        stability = len(intersection) / len(union) if union else 0.0
        protein_labels, size_tier, e8_closure_tier = _emergent_from_codon(nodes, union)
        domains = list(set(a.get("domain", "") for a in atoms if a.get("domain")))
        pairwise_emergent = []
        for i, a_node in enumerate(nodes):
            for b_node in nodes[i + 1:]:
                shared = a_node.label_set & b_node.label_set
                pairwise_emergent.extend(_emergent_from_bond(a_node, b_node, shared))
        pairwise_emergent = list(dict.fromkeys(pairwise_emergent))[:15]
        return {"atoms": len(atoms), "stability": round(stability, 4),
                "shared_labels": sorted(intersection)[:10], "protein_labels": protein_labels,
                "pairwise_emergent": pairwise_emergent, "size_tier": size_tier,
                "e8_closure_tier": e8_closure_tier, "domains": domains, "closed": stability >= 0.3}

    def find_cliques(self, atoms: List[Dict[str, Any]], min_bond_strength: float = 0.05,
                     max_clique_size: int = 6) -> Dict[str, Any]:
        if len(atoms) < 3:
            return {"error": "Need at least 3 atoms", "cliques": []}
        nodes = []
        for a in atoms:
            node = AtomNode(atom_id=a["atom_id"], snap_labels=set(a.get("snap_labels", [])),
                            domain=a.get("domain", ""), e8_coords=a.get("e8_coords", []))
            nodes.append(node)
        graph: Dict[str, Set[str]] = {}
        bond_edges = []
        for i, a in enumerate(nodes):
            for b in nodes[i + 1:]:
                j_val = jaccard(a.label_set, b.label_set)
                if j_val >= min_bond_strength:
                    graph.setdefault(a.atom_id, set()).add(b.atom_id)
                    graph.setdefault(b.atom_id, set()).add(a.atom_id)
                    bond_edges.append({"a": a.atom_id, "b": b.atom_id, "jaccard": round(j_val, 4)})
        cliques: List[FrozenSet[str]] = []
        all_ids = set(graph.keys())
        if all_ids:
            bron_kerbosch(set(), all_ids, set(), graph, cliques, max_clique_size)
        maximal = [c for c in cliques if not any(c < other for other in cliques)]
        clique_results = []
        for clique in maximal:
            members = [n for n in nodes if n.atom_id in clique]
            all_labels: Set[str] = set()
            for m in members:
                all_labels.update(m.snap_labels)
            protein_labels, size_tier, e8_closure_tier = _emergent_from_codon(members, all_labels)
            clique_results.append({"atom_ids": sorted(clique), "size": len(clique),
                                   "size_tier": size_tier, "protein_labels": protein_labels,
                                   "e8_closure_tier": e8_closure_tier})
        return {"total_atoms": len(atoms), "bond_edges": len(bond_edges),
                "cliques_found": len(maximal), "cliques": clique_results, "edges": bond_edges[:50]}

    def register_atoms(self, atoms: List[Dict[str, Any]]) -> Dict[str, Any]:
        for a in atoms:
            node = AtomNode(atom_id=a["atom_id"], snap_labels=set(a.get("snap_labels", [])),
                            domain=a.get("domain", ""), e8_coords=a.get("e8_coords", []))
            self._assembler.register_atom(node)
            if a.get("e8_coords"):
                grain = Grain(grain_id=a["atom_id"], e8_coords=a["e8_coords"], snap_labels=a.get("snap_labels", []))
                self._assembler.register_grain(grain)
        return {"registered": len(atoms), "total_atoms": len(self._assembler._atoms)}

    def run_full_pass(self) -> Dict[str, Any]:
        return self._assembler.run_full_pass()

    def stats(self) -> Dict[str, Any]:
        return self._assembler.stats()

    def health(self) -> Dict[str, Any]:
        return {"ok": True, "service": "opencmplx-bond-v2",
                "atoms": len(self._assembler._atoms), "grains": len(self._assembler._grains),
                "dusts": len(self._assembler._dusts), "dimers": len(self._assembler._dimers),
                "codons": len(self._assembler._codons)}
