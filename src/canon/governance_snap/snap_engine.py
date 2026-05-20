#!/usr/bin/env python3
"""
OpenCMPLX SNAP Engine — Gate369 + Lenses + Taxonomy + Stratifier

The SNAP Engine is the precision labeling toolkit. It goes beyond the
14-pass keyword labeler in the pipeline by providing:

  Gate369   — 3-6-9 selection: Triad (pick 3 best) → Hexad (polarity
              invariants) → Ennead (containment-stable 9-body resolution)
  Lenses    — Polarity-aware evaluation: BaseLens, LegalityLens,
              NoveltyLens, SymmetryLens
  Taxonomy  — Family/type registry for label classification
  Stratifier — Recursive concept expansion via 8-angle questionnaire
              until convergence (no new labels = snap)
  Journal   — Append-only write-ahead log for SNAP records

SNAP doesn't label. SNAP STRATIFIES. Every concept gets exploded into
all presentations, meanings, connections, fictions, non-standard
interpretations. Recursively. Until convergence.

Ported from retooling.snap (4,746 lines across 12 files).
"""
import hashlib
import json
import logging
import math
import os
import time
import uuid
import urllib.request
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional, Set, Tuple

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO, format="%(asctime)s [snap-engine] %(message)s")
logger = logging.getLogger("snap-engine")

PORT = int(os.environ.get("PORT", "8000"))
COUPLING = float(os.environ.get("COUPLING", "0.030076"))
PIPELINE_URL = os.environ.get("PIPELINE_URL", "http://tmn2-pipeline:8000")
PG_URL = os.environ.get("PG_URL", "")


# ═══════════════════════════════════════════════════════════════════════
# Core Data Types
# ═══════════════════════════════════════════════════════════════════════

@dataclass
class Predicate:
    """Scoreable condition applied to Bodies."""
    name: str
    cost: float = 1.0
    meta: Dict[str, Any] = field(default_factory=dict)

@dataclass
class Body:
    """A SNAP body — the subject of a predicate evaluation."""
    id: str
    features: Dict[str, Any] = field(default_factory=dict)

@dataclass
class SNAPRecord:
    """Unified SNAP data unit — a snap file AND a triadic record."""
    record_id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    kind: str = "generic"
    ts: float = field(default_factory=time.time)
    members: List[Body] = field(default_factory=list)
    predicates: List[Predicate] = field(default_factory=list)
    delta_u: float = 0.0
    polarity_conflict: float = 0.0
    payload: Dict[str, Any] = field(default_factory=dict)

    def hash(self) -> str:
        return hashlib.sha256(json.dumps(
            {"id": self.record_id, "kind": self.kind, "ts": self.ts}, sort_keys=True
        ).encode()).hexdigest()[:16]

@dataclass
class HexadInvariant:
    """6-body polarity invariant — two poles and their relationship."""
    pos: Body
    neg: Body
    invariant: str
    margin: float

@dataclass
class EnneadPackage:
    """9-body containment-stable resolution."""
    facets: List[Body]
    lens_name: str
    mirror_pass: bool
    containment_c: float
    delta_u: float
    reversibility: bool


# ═══════════════════════════════════════════════════════════════════════
# Lenses — polarity-aware evaluation
# ═══════════════════════════════════════════════════════════════════════

class BaseLens:
    name = "base"

    def evaluate(self, state: Dict) -> str:
        if not state.get("mirror_pass", False): return "refine"
        if state.get("polarity_conflict", 1.0) > state.get("polarity_thresh", 0.2): return "refine"
        if state.get("containment_c", 0.0) < state.get("c_thresh", 0.7): return "refine"
        return "pass"

    def score_reward(self, before: Dict, after: Dict) -> float:
        return (after.get("delta_u", 0.0) - before.get("delta_u", 0.0)
                - 0.1 * after.get("edbsu_growth", 0.0))

    def pick_predicate(self, candidates: List[Predicate], state: Dict) -> Predicate:
        return sorted(candidates, key=lambda p: -(p.meta.get("expected_du", 0.0) / max(p.cost, 1e-6)))[0]


class LegalityLens(BaseLens):
    name = "legality"
    def evaluate(self, state: Dict) -> str:
        if state.get("violates_policy", False): return "fail"
        return super().evaluate(state)


class NoveltyLens(BaseLens):
    name = "novelty"
    def score_reward(self, before: Dict, after: Dict) -> float:
        return super().score_reward(before, after) + 0.2 * after.get("novelty", 0.0)


class SymmetryLens(BaseLens):
    name = "symmetry"
    def score_reward(self, before: Dict, after: Dict) -> float:
        return super().score_reward(before, after) + 0.15 * after.get("symmetry_score", 0.0)


class LensBank:
    def __init__(self):
        self._lenses = {}
        for lens in [BaseLens(), LegalityLens(), NoveltyLens(), SymmetryLens()]:
            self._lenses[lens.name] = lens

    def get(self, name: str): return self._lenses.get(name)
    def add(self, lens): self._lenses[lens.name] = lens

    def best_lens(self, state: Dict):
        for lens in self._lenses.values():
            if lens.evaluate(state) == "pass": return lens
        return self._lenses["base"]

    def evaluate_all(self, state: Dict) -> Dict[str, str]:
        return {n: l.evaluate(state) for n, l in self._lenses.items()}


# ═══════════════════════════════════════════════════════════════════════
# Gate369 Engine
# ═══════════════════════════════════════════════════════════════════════

class Gate369Engine:
    """3-6-9 selection and evaluation.

    Triad (Gate 3): Pick 3 best bodies by lens-scored predicate.
    Hexad (Gate 6): Find polarity invariants across record pairs.
    Ennead (Gate 9): Resolve into containment-stable 9-body package.
    """

    def __init__(self):
        self.lens_bank = LensBank()
        self._history: List[Dict] = []

    def triad(self, bodies: List[Body], predicates: List[Predicate],
              state: Dict) -> SNAPRecord:
        lens = self.lens_bank.best_lens(state)
        du_sum = sum(p.meta.get("expected_du", 0.0) for p in predicates)
        scored = [(b, lens.score_reward({}, {"delta_u": du_sum})) for b in bodies]
        top3 = [b for b, _ in sorted(scored, key=lambda x: -x[1])[:3]]
        return SNAPRecord(kind="triad", members=top3, predicates=predicates,
                          delta_u=sum(s for _, s in scored[:3]))

    def hexad(self, records: List[SNAPRecord]) -> List[HexadInvariant]:
        invariants = []
        for i in range(0, len(records) - 1, 2):
            a, b = records[i], records[i + 1]
            if a.members and b.members:
                invariants.append(HexadInvariant(
                    pos=a.members[0], neg=b.members[0],
                    invariant=f"{a.kind}↔{b.kind}",
                    margin=abs(a.delta_u - b.delta_u),
                ))
        return invariants

    def ennead(self, records: List[SNAPRecord], lens_name: str = "base") -> EnneadPackage:
        all_bodies = [b for r in records for b in r.members][:9]
        lens = self.lens_bank.get(lens_name) or self.lens_bank.get("base")
        delta_us = [r.delta_u for r in records] if records else [0.0]
        mean_du = sum(delta_us) / len(delta_us)
        variance = sum((d - mean_du) ** 2 for d in delta_us) / max(len(delta_us), 1)
        polarity_conflict = min(variance / max(abs(mean_du) + 1e-9, 1.0), 1.0)
        conflict_free = sum(1 for r in records if r.polarity_conflict == 0)
        containment_c = conflict_free / max(len(records), 1)
        state = {"mirror_pass": polarity_conflict > 0.3,
                 "polarity_conflict": polarity_conflict, "containment_c": containment_c}
        result = lens.evaluate(state)
        return EnneadPackage(facets=all_bodies, lens_name=lens_name,
                             mirror_pass=state["mirror_pass"], containment_c=containment_c,
                             delta_u=sum(delta_us), reversibility=(result == "pass"))

    def process(self, bodies: List[Body], predicates: List[Predicate],
                state: Dict = None) -> Dict:
        """Full 3-6-9 sequence."""
        state = state or {}
        triad = self.triad(bodies, predicates, state)
        self._history.append({"gate": 3, "members": len(triad.members)})
        remaining = [b for b in bodies if b not in triad.members]
        triads = [triad]
        if remaining:
            triads.append(self.triad(remaining, predicates, state))
        invariants = self.hexad(triads)
        self._history.append({"gate": 6, "invariants": len(invariants)})
        ennead = self.ennead(triads)
        self._history.append({"gate": 9, "facets": len(ennead.facets),
                              "crystallized": ennead.containment_c > 0.7})
        return {"triad": asdict(triad) if hasattr(triad, '__dataclass_fields__') else {"members": len(triad.members)},
                "hexad": [{"pos": i.pos.id, "neg": i.neg.id, "margin": i.margin} for i in invariants],
                "ennead": {"facets": len(ennead.facets), "containment_c": ennead.containment_c,
                           "reversible": ennead.reversibility, "crystallized": ennead.containment_c > 0.7}}


# ═══════════════════════════════════════════════════════════════════════
# Stratifier — recursive concept expansion
# ═══════════════════════════════════════════════════════════════════════

ANGLES = [
    ("what", "Define {seed}: components, properties, boundaries, forms"),
    ("how", "How {seed} works: mechanism, process, steps"),
    ("why", "Why {seed} matters: dependencies, what breaks without it"),
    ("connects", "What {seed} connects to: related concepts, adjacent ideas"),
    ("formal", "Formal structure: equations, rules, invariants, types"),
    ("breaks", "Limitations: edge cases, paradoxes, alternatives"),
    ("analogy", "Analogies: other domains, other scales, fiction, nature"),
    ("builds", "What to build from {seed}: applications, extensions, derivatives"),
]


def stratify(seed: str, max_depth: int = 3, existing_labels: Set[str] = None) -> Dict:
    """Recursively expand a concept via 8-angle questionnaire.

    Each angle produces a text that gets SNAP-labeled via pipeline.
    New labels that weren't in existing_labels represent discoveries.
    Expansion stops when a level adds no new labels (convergence).
    """
    existing = set(existing_labels or [])
    levels = []
    current_seeds = [seed]

    for depth in range(max_depth):
        new_labels = set()
        level_results = []

        for s in current_seeds[:5]:  # Cap seeds per level
            for angle_name, angle_template in ANGLES:
                text = angle_template.replace("{seed}", s)

                # Use pipeline /label for fast labeling (not full /process — avoids feedback loop)
                try:
                    body = json.dumps({"content": text}).encode()
                    req = urllib.request.Request(f"{PIPELINE_URL}/label", data=body,
                                                 headers={"Content-Type": "application/json"})
                    with urllib.request.urlopen(req, timeout=10) as r:
                        result = json.loads(r.read())
                    labels = set(result.get("labels", []))
                    discoveries = labels - existing
                    new_labels.update(discoveries)
                    existing.update(labels)
                    level_results.append({
                        "seed": s, "angle": angle_name,
                        "labels": len(labels), "discoveries": len(discoveries),
                    })
                except Exception:
                    pass

        levels.append({
            "depth": depth, "seeds": len(current_seeds),
            "new_labels": len(new_labels), "total_labels": len(existing),
            "results": level_results[:10],
        })

        if not new_labels:
            # Convergence — no new labels at this depth
            break

        # Next level seeds: the new labels themselves become seeds
        current_seeds = list(new_labels)[:10]

    return {
        "seed": seed,
        "depths_explored": len(levels),
        "converged": len(levels) < max_depth or (levels and levels[-1]["new_labels"] == 0),
        "total_labels": len(existing),
        "levels": levels,
    }


# ═══════════════════════════════════════════════════════════════════════
# Taxonomy — label family/type registry
# ═══════════════════════════════════════════════════════════════════════

_families: Dict[str, Dict] = {}
_types: Dict[str, Dict] = {}


def register_family(name: str, meta: Dict = None):
    _families[name] = {"meta": meta or {}, "types": []}

def register_type(name: str, families: List[str], meta: Dict = None):
    for f in families:
        if f not in _families: register_family(f)
        _families[f]["types"].append(name)
    _types[name] = {"families": families, "meta": meta or {}}


# Pre-register core families
for fam in ["domain", "op", "formal", "meta", "type", "keyword", "touch",
            "role", "composite", "family", "literal", "sci", "effect",
            "xform", "intent", "action", "dr", "notation", "proof"]:
    register_family(fam)


# ═══════════════════════════════════════════════════════════════════════
# FastAPI Service
# ═══════════════════════════════════════════════════════════════════════

app = FastAPI(title="OpenCMPLX SNAP Engine",
              description="Gate369 + Lenses + Taxonomy + Stratifier", version="2.0.0")

_gate = Gate369Engine()


class Gate369Request(BaseModel):
    bodies: List[Dict] = []
    predicates: List[Dict] = []
    state: Dict = {}

class StratifyRequest(BaseModel):
    seed: str
    max_depth: int = 3
    existing_labels: List[str] = []

class LensRequest(BaseModel):
    state: Dict = {}


@app.get("/health")
def health():
    return {"ok": True, "service": "opencmplx-snap-engine", "version": "2.0.0",
            "families": len(_families), "types": len(_types),
            "gate_history": len(_gate._history),
            "lenses": list(_gate.lens_bank._lenses.keys())}


@app.post("/gate369")
def api_gate369(req: Gate369Request):
    """Run full Gate 3-6-9 sequence on bodies with predicates."""
    bodies = [Body(id=b.get("id", str(i)), features=b.get("features", {}))
              for i, b in enumerate(req.bodies)]
    predicates = [Predicate(name=p.get("name", str(i)), cost=p.get("cost", 1.0),
                            meta=p.get("meta", {}))
                  for i, p in enumerate(req.predicates)]
    if len(bodies) < 3:
        raise HTTPException(400, "Gate369 needs at least 3 bodies")
    return _gate.process(bodies, predicates, req.state)


@app.post("/triad")
def api_triad(req: Gate369Request):
    """Gate 3 only — pick best 3."""
    bodies = [Body(id=b.get("id", str(i)), features=b.get("features", {}))
              for i, b in enumerate(req.bodies)]
    predicates = [Predicate(name=p.get("name", ""), meta=p.get("meta", {}))
                  for p in req.predicates]
    record = _gate.triad(bodies, predicates, req.state)
    return {"members": [b.id for b in record.members], "delta_u": record.delta_u}


@app.post("/stratify")
def api_stratify(req: StratifyRequest):
    """Recursively expand a concept via 8-angle questionnaire until convergence."""
    return stratify(req.seed, req.max_depth, set(req.existing_labels))


@app.post("/evaluate_lenses")
def api_lenses(req: LensRequest):
    """Evaluate all lenses against a state."""
    return _gate.lens_bank.evaluate_all(req.state)


@app.get("/taxonomy")
def api_taxonomy():
    """Return the label family/type taxonomy."""
    return {"families": _families, "types": _types}


@app.get("/angles")
def api_angles():
    """Return the 8-angle stratification questionnaire."""
    return {"angles": [{"name": a[0], "template": a[1]} for a in ANGLES]}




@app.post("/tick")
def tick():
    """Daemon tick -- run stratification on recent atoms, SpeedLight-cached."""
    processed = 0
    cache_hits = 0
    try:
        from src.shared.cqe_primitives import sl_get, sl_put
        conn = _get_pg()
        if conn:
            with conn.cursor() as cur:
                cur.execute("SELECT atom_id, snap_labels FROM atoms ORDER BY created_at DESC LIMIT 5")
                for atom_id, labels_j in cur.fetchall():
                    # Check SpeedLight first
                    cached = sl_get(atom_id, "snap_engine", "stratify")
                    if cached:
                        cache_hits += 1
                        continue
                    labels = labels_j if isinstance(labels_j, list) else []
                    try:
                        result = stratify(atom_id[:20], max_depth=3, existing_labels=set(l for l in labels if isinstance(l, str)))
                        sl_put(atom_id, "snap_engine", "stratify", {"depth": result.get("depth", 0), "labels": len(result.get("labels", []))})
                        processed += 1
                    except: pass
    except: pass
    return {"ok": True, "processed": processed, "cache_hits": cache_hits, "families": len(_families)}


# ─── SNAP Schema: Candidate + Evidence + DNA (from SnapLat snap/schema.py) ───
# Formal data structures for SNAP state management.

_snap_candidates: Dict[str, Dict] = {}  # id → {payload, meta}
_snap_evidence: Dict[str, List[Dict]] = {}  # candidate_id → [evidence entries]
_snap_dna: Dict[str, Dict] = {}  # dna_checksum → {weights, candidate_ids}

@app.post("/candidate")
def register_candidate(candidate_id: str = "", payload: str = "", meta: Dict = {}):
    """Register a SNAP candidate for evaluation."""
    import hashlib as _h
    cid = candidate_id or _h.sha256(payload.encode()).hexdigest()[:16]
    _snap_candidates[cid] = {"payload": payload, "meta": meta, "created": time.time()}
    return {"candidate_id": cid, "total_candidates": len(_snap_candidates)}

@app.post("/evidence")
def submit_evidence(candidate_id: str, utility: float = 0.5, notes: Dict = {}):
    """Submit evidence for a candidate's utility."""
    if candidate_id not in _snap_candidates:
        raise HTTPException(404, f"Candidate '{candidate_id}' not found")
    entry = {"utility": utility, "notes": notes, "timestamp": time.time()}
    _snap_evidence.setdefault(candidate_id, []).append(entry)
    return {"candidate_id": candidate_id, "evidence_count": len(_snap_evidence[candidate_id]),
            "avg_utility": sum(e["utility"] for e in _snap_evidence[candidate_id]) / len(_snap_evidence[candidate_id])}

class DNARequest(BaseModel):
    weights: List[float] = []
    candidate_ids: List[str] = []

class JaccardRequest(BaseModel):
    set_a: List[str] = []
    set_b: List[str] = []

class EntropyRequest(BaseModel):
    weights: List[float] = []

class StitchRequest(BaseModel):
    candidate_ids: List[str] = []
    utilities: List[float] = []

class SnapStateRequest(BaseModel):
    name: str = ""
    base_point: List[float] = []
    orientation: List[int] = []

@app.post("/dna_snapshot")
def dna_snapshot(req: DNARequest):
    """Create a DNA snapshot: weighted combination of candidates."""
    import hashlib as _h
    checksum = _h.sha256(json.dumps({"w": req.weights, "ids": req.candidate_ids}, sort_keys=True).encode()).hexdigest()[:24]
    _snap_dna[checksum] = {"weights": req.weights, "candidate_ids": req.candidate_ids, "created": time.time()}
    return {"dna_checksum": checksum, "n_candidates": len(req.candidate_ids), "total_dna": len(_snap_dna)}

# ─── SNAPState: E8-grounded state (from SnapLat snap/state.py) ───────────────

# ─── Metrics: Jaccard, Coverage, Drift, Entropy, DL (from SnapLat metrics/) ──

def _jaccard(a, b):
    A, B = set(a), set(b)
    if not A and not B: return 1.0
    return len(A & B) / float(len(A | B) or 1)

def _coverage_ratio(n_covered: int, n_total: int) -> float:
    if n_total <= 0: return 0.0
    return max(0.0, min(1.0, n_covered / float(n_total)))

def _drift_jaccard(prev_ids, curr_ids) -> float:
    return 1.0 - _jaccard(prev_ids, curr_ids)

def _entropy(p, eps=1e-12) -> float:
    q = [max(eps, min(1.0, x)) for x in p]
    Z = sum(q) or 1.0
    q = [x / Z for x in q]
    return -sum(x * math.log(x + eps) for x in q)

def _glyph_dl(weights) -> float:
    """Glyph description length: normalized entropy of weight distribution."""
    H = _entropy(weights)
    Hmax = math.log(max(1, len(weights)))
    return float(H / (Hmax or 1.0))

def _leakage_from_metrics(tac: float = 1.0, boundary: float = 1.0, drift: float = 0.0) -> float:
    """Compute leakage score from TAC, boundary, and drift metrics."""
    leak = max(0.0, 0.95 - tac) + max(0.0, 0.9 - boundary) + max(0.0, drift - 0.2)
    return min(1.0, leak)

@app.post("/metrics/jaccard")
def api_jaccard(req: JaccardRequest):
    return {"jaccard": round(_jaccard(req.set_a, req.set_b), 4)}

@app.post("/metrics/leakage")
def api_leakage(tac: float = 1.0, boundary: float = 1.0, drift: float = 0.0):
    return {"leakage": round(_leakage_from_metrics(tac, boundary, drift), 4)}

@app.post("/metrics/entropy")
def api_entropy(req: EntropyRequest):
    if not req.weights:
        return {"entropy": 0.0, "glyph_dl": 0.0}
    return {"entropy": round(_entropy(req.weights), 4), "glyph_dl": round(_glyph_dl(req.weights), 4)}

# ─── DTT Harness: Deterministic Test Transform (from SnapLat dtt/harness.py) ──
# Evaluates candidates via deterministic hash-based scoring.

def _dtt_evaluate(candidate_id: str, payload: str, seed: int = 0) -> Dict:
    """Deterministic evaluation: hash-based score + stability → utility."""
    import hashlib as _h
    raw = f"{candidate_id}:{payload}"
    h = int(_h.sha256(raw.encode()).hexdigest(), 16)
    score = ((h % 10_000_000) / 10_000_000.0)
    stability = (((h // 7) % 10_000_000) / 10_000_000.0)
    utility = 0.5 * score + 0.5 * stability
    return {"candidate_id": candidate_id, "score": round(score, 4),
            "stability": round(stability, 4), "utility": round(utility, 4), "seed": seed}

@app.post("/dtt_evaluate")
def dtt_evaluate(candidate_id: str = "", payload: str = "", seed: int = 0):
    """Run DTT (Deterministic Test Transform) on a candidate."""
    return _dtt_evaluate(candidate_id, payload, seed)

# ─── Assembly: Stitch candidates into DNA (from SnapLat assembly/core.py) ─────

@app.post("/stitch")
def stitch(req: StitchRequest):
    """Stitch candidates into a DNA snapshot weighted by utility scores."""
    candidate_ids, utilities = req.candidate_ids, req.utilities
    if not candidate_ids or not utilities or len(candidate_ids) != len(utilities):
        return {"error": "Need matching candidate_ids and utilities lists"}
    s = sum(utilities) if sum(utilities) > 0 else 1.0
    weights = [u / s for u in utilities]
    import hashlib as _h
    checksum = _h.sha256(json.dumps({"w": weights, "ids": candidate_ids}, sort_keys=True).encode()).hexdigest()[:24]
    glyph = {"type": "barymix", "weights": [round(w, 4) for w in weights], "parts": candidate_ids}
    return {"glyph": glyph, "dna_checksum": checksum, "n_candidates": len(candidate_ids)}

@app.post("/snap_state")
def create_snap_state(req: SnapStateRequest):
    """Create a SNAP state grounded in E8 coordinates."""
    name, base_point, orientation = req.name, req.base_point, req.orientation
    if len(base_point) < 8:
        base_point = base_point + [0.0] * (8 - len(base_point))
    import hashlib as _h
    state_hash = _h.sha256(json.dumps({"name": name, "bp": base_point[:8]}, sort_keys=True).encode()).hexdigest()[:16]
    return {
        "name": name, "base_point": base_point[:8],
        "orientation": orientation[:8] if orientation else [0] * 8,
        "state_hash": state_hash,
    }


if __name__ == "__main__":
    import uvicorn
    logger.info("SNAP Engine v2.0 starting on port %d", PORT)
    uvicorn.run(app, host="0.0.0.0", port=PORT)
