"""ThinkTank Engine — Multi-perspective deliberation with quorum consensus.

Port of TMN2 thinktank.py into CMPLX-PartsFactory.

8 perspectives: geometry, tarpit, snap, agent, physics, economics, code, philosophy.
3-8 perspectives selected by content complexity.
Quorum: >=3 agree for simple, >=5 for complex (>500 chars).
Integrates with ServiceRegistry (snap, manny) and GeometricGovernance.
"""

from __future__ import annotations
import hashlib
import json
import logging
import math
import re
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger("thinktank")

SIMPLE_QUORUM = 3
COMPLEX_QUORUM = 5
COMPLEX_CHAR_THRESHOLD = 500
MAX_ROUNDS = 5

PERSPECTIVES = {
    "geometry": {
        "name": "Geometry", "bias": "spatial structure and symmetry",
        "keywords": ["e8", "leech", "lattice", "symmetry", "rotation", "manifold", "dimension",
                     "golay", "niemeier", "weyl", "root", "coordinate", "vector", "morsr",
                     "dihedral", "group", "algebra", "topology", "embedding", "projection"],
    },
    "tarpit": {
        "name": "TarPit", "bias": "minimal computation and reduction",
        "keywords": ["tarpit", "glyph", "lambda", "reduce", "abstract", "jot", "sk",
                     "combinator", "rewrite", "tape", "wall", "bonding", "arity", "superperm",
                     "palindrome", "etp", "minimal", "turing"],
    },
    "snap": {
        "name": "SNAP", "bias": "labeling and classification",
        "keywords": ["snap", "label", "classify", "domain", "layer", "keyword", "semantic",
                     "formal", "literal", "operational", "digital_root", "3-6-9", "crt",
                     "channel", "coordinate", "tag", "index"],
    },
    "agent": {
        "name": "Agent", "bias": "agent lifecycle and behavior",
        "keywords": ["agent", "brain", "daemon", "spawn", "birth", "death", "lifecycle",
                     "nanobot", "living", "tool", "sap", "sentinel", "arbiter", "porter",
                     "identity", "tier", "shell", "epoch", "capacity"],
    },
    "physics": {
        "name": "Physics", "bias": "conservation and dynamics",
        "keywords": ["conservation", "delta_phi", "energy", "morphon", "field", "potential",
                     "spinor", "wave", "particle", "mass", "coupling", "noether", "shannon",
                     "landauer", "entropy", "momentum", "force"],
    },
    "economics": {
        "name": "Economics", "bias": "coins, markets, and value",
        "keywords": ["coin", "economy", "market", "mint", "cite", "supply", "demand",
                     "ledger", "transaction", "shell", "ticker", "portfolio", "weight",
                     "price", "trade", "surplus", "spend"],
    },
    "code": {
        "name": "Code", "bias": "implementation and architecture",
        "keywords": ["function", "class", "module", "import", "api", "endpoint", "service",
                     "docker", "compose", "database", "query", "pipeline", "test", "deploy",
                     "config", "schema", "interface", "implement"],
    },
    "philosophy": {
        "name": "Philosophy", "bias": "meaning, ontology, and emergence",
        "keywords": ["emergence", "ontology", "meaning", "consciousness", "observer",
                     "reality", "truth", "knowledge", "complexity", "self", "recursive",
                     "fractal", "holistic", "boundary", "identity", "existence"],
    },
}


def _tokenize(text: str) -> List[str]:
    return re.findall(r'[a-z_][a-z0-9_]*', text.lower())


def _analyze_perspective(name: str, config: Dict, content: str, tokens: List[str]) -> Dict:
    keywords = config["keywords"]
    matches = [kw for kw in keywords if kw in tokens]
    token_set = set(tokens)
    keyword_set = set(keywords)
    overlap = token_set & keyword_set

    coverage = len(overlap) / len(keywords) if keywords else 0
    relevance = len(matches) / max(len(tokens), 1)

    confidence = math.sqrt(coverage * relevance) if coverage > 0 and relevance > 0 else 0.0
    confidence = min(confidence * 5, 1.0)

    if confidence >= 0.6:
        verdict = "approve"
    elif confidence >= 0.3:
        verdict = "deepen"
    else:
        verdict = "reject"

    snap_labels = [f"domain:{name}"]
    for kw in matches:
        snap_labels.append(f"keyword:{kw}")
    if coverage > 0.3:
        snap_labels.append(f"strong_signal:{name}")

    return {
        "perspective": name, "domain": config["name"], "bias": config["bias"],
        "matched_keywords": matches, "coverage": round(coverage, 4),
        "relevance": round(relevance, 6), "confidence": round(confidence, 4),
        "verdict": verdict, "snap_labels": snap_labels,
    }


def _select_perspectives(content: str) -> List[str]:
    length = len(content)
    tokens = _tokenize(content)
    unique = len(set(tokens))

    if length > 2000 or unique > 200:
        return list(PERSPECTIVES.keys())
    elif length > 1000 or unique > 100:
        return list(PERSPECTIVES.keys())[:6]
    elif length > 500 or unique > 50:
        return list(PERSPECTIVES.keys())[:5]
    else:
        tokens_set = set(tokens)
        scores = []
        for name, config in PERSPECTIVES.items():
            overlap = len(tokens_set & set(config["keywords"]))
            scores.append((name, overlap))
        scores.sort(key=lambda x: -x[1])
        selected = [s[0] for s in scores[:3]]
        if len(selected) < 3:
            selected = list(PERSPECTIVES.keys())[:3]
        return selected


def _build_consensus(analyses: List[Dict], is_complex: bool) -> Dict:
    quorum = COMPLEX_QUORUM if is_complex else SIMPLE_QUORUM

    by_verdict = {}
    for a in analyses:
        by_verdict.setdefault(a["verdict"], []).append(a)

    dominant_verdict = max(by_verdict.keys(), key=lambda v: len(by_verdict[v])) if by_verdict else "reject"
    dominant_count = len(by_verdict.get(dominant_verdict, []))
    has_quorum = dominant_count >= quorum

    domain_scores = {}
    for a in analyses:
        d = a["perspective"]
        domain_scores[d] = domain_scores.get(d, 0) + a["confidence"]
    top_domain = max(domain_scores, key=domain_scores.get) if domain_scores else "unknown"

    all_labels = set()
    for a in analyses:
        all_labels.update(a.get("snap_labels", []))

    avg_confidence = sum(a["confidence"] for a in analyses) / len(analyses) if analyses else 0

    return {
        "consensus": has_quorum,
        "dominant_verdict": dominant_verdict,
        "dominant_count": dominant_count,
        "quorum_required": quorum,
        "top_domain": top_domain,
        "domain_scores": {k: round(v, 4) for k, v in domain_scores.items()},
        "avg_confidence": round(avg_confidence, 4),
        "snap_labels": sorted(all_labels),
        "by_verdict": {k: len(v) for k, v in by_verdict.items()},
    }


class ThinkTankEngine:
    """Multi-perspective deliberation engine with quorum consensus.

    Selects 3-8 perspectives based on content complexity, analyzes from each,
    and builds consensus via quorum voting. Integrates with GeometricGovernance
    for audit and ServiceRegistry for downstream service calls.
    """

    def __init__(self, governance: Any = None, service_registry: Any = None):
        self.governance = governance
        self.service_registry = service_registry
        self._deliberations: List[Dict] = []
        self._stats = {
            "total": 0, "consensual": 0, "non_consensual": 0,
            "by_domain": {}, "avg_confidence": 0.0, "total_perspectives_used": 0,
        }

    # ── Public API ──────────────────────────────────────────────────────────

    def reason(self, content: str, context: Dict = None, depth: str = "normal") -> Dict:
        tokens = _tokenize(content)
        is_complex = len(content) > COMPLEX_CHAR_THRESHOLD

        selected = _select_perspectives(content)
        if depth == "deep":
            selected = list(PERSPECTIVES.keys())
        elif depth == "quick":
            selected = selected[:3]

        analyses = []
        for name in selected:
            config = PERSPECTIVES[name]
            analysis = _analyze_perspective(name, config, content, tokens)
            analyses.append(analysis)

        consensus = _build_consensus(analyses, is_complex)

        result = {
            "perspectives": analyses,
            "consensus": consensus,
            "confidence": consensus["avg_confidence"],
            "snap_labels": consensus["snap_labels"],
            "content_length": len(content),
            "is_complex": is_complex,
            "depth": depth,
            "perspectives_used": len(selected),
            "timestamp": time.time(),
        }

        self._deliberations.append(result)
        self._update_stats(result)
        self._audit("reason", result)

        return result

    def deliberate(self, content: str, context: Dict = None) -> Dict:
        tokens = _tokenize(content)
        is_complex = len(content) > COMPLEX_CHAR_THRESHOLD

        analyses = []
        for name, config in PERSPECTIVES.items():
            analysis = _analyze_perspective(name, config, content, tokens)
            analyses.append(analysis)

        rounds = []
        for round_num in range(MAX_ROUNDS):
            consensus = _build_consensus(analyses, is_complex)
            rounds.append({
                "round": round_num + 1,
                "consensus": consensus["consensus"],
                "avg_confidence": consensus["avg_confidence"],
                "dominant": consensus["dominant_verdict"],
            })

            if consensus["consensus"]:
                break

            dominant = consensus["dominant_verdict"]
            for a in analyses:
                if a["verdict"] == dominant:
                    a["confidence"] = min(a["confidence"] + 0.05, 1.0)

        final_consensus = _build_consensus(analyses, is_complex)

        result = {
            "perspectives": analyses,
            "consensus": final_consensus,
            "confidence": final_consensus["avg_confidence"],
            "snap_labels": final_consensus["snap_labels"],
            "rounds": rounds,
            "converged": final_consensus["consensus"],
            "content_length": len(content),
            "timestamp": time.time(),
        }

        self._deliberations.append(result)
        self._update_stats(result)
        self._audit("deliberate", result)

        return result

    def grade(self, content_a: str, content_b: str, criteria: List[str] = None) -> Dict:
        tokens_a = _tokenize(content_a)
        tokens_b = _tokenize(content_b)

        grades_a = []
        grades_b = []
        for name, config in PERSPECTIVES.items():
            ga = _analyze_perspective(name, config, content_a, tokens_a)
            gb = _analyze_perspective(name, config, content_b, tokens_b)
            grades_a.append(ga)
            grades_b.append(gb)

        score_a = sum(g["confidence"] for g in grades_a)
        score_b = sum(g["confidence"] for g in grades_b)

        comparisons = []
        for ga, gb in zip(grades_a, grades_b):
            if ga["confidence"] > gb["confidence"]:
                winner = "A"
            elif gb["confidence"] > ga["confidence"]:
                winner = "B"
            else:
                winner = "tie"
            comparisons.append({
                "perspective": ga["perspective"],
                "score_a": ga["confidence"], "score_b": gb["confidence"],
                "winner": winner,
            })

        a_wins = sum(1 for c in comparisons if c["winner"] == "A")
        b_wins = sum(1 for c in comparisons if c["winner"] == "B")

        return {
            "winner": "A" if score_a > score_b else ("B" if score_b > score_a else "tie"),
            "score_a": round(score_a, 4), "score_b": round(score_b, 4),
            "a_perspective_wins": a_wins, "b_perspective_wins": b_wins,
            "comparisons": comparisons,
            "margin": round(abs(score_a - score_b), 4),
        }

    def list_perspectives(self) -> Dict:
        return {
            "count": len(PERSPECTIVES),
            "perspectives": {
                name: {
                    "name": c["name"], "bias": c["bias"],
                    "keyword_count": len(c["keywords"]),
                    "sample_keywords": c["keywords"][:5],
                }
                for name, c in PERSPECTIVES.items()
            },
            "quorum_simple": SIMPLE_QUORUM,
            "quorum_complex": COMPLEX_QUORUM,
            "complex_threshold": COMPLEX_CHAR_THRESHOLD,
        }

    def get_stats(self) -> Dict:
        return dict(self._stats)

    def recent_deliberations(self, limit: int = 10) -> List[Dict]:
        return self._deliberations[-limit:]

    # ── Integration helpers ─────────────────────────────────────────────────

    def classify_with_snap(self, text: str) -> Optional[Dict]:
        if not self.service_registry or not self.service_registry.snap:
            return None
        try:
            return self.service_registry.snap.stratify(text)
        except Exception as e:
            logger.warning("SNAP classify failed: %s", e)
            return None

    def probe_with_manny(self, query: str, domain: str = "general") -> Optional[Dict]:
        if not self.service_registry or not self.service_registry.manny:
            return None
        try:
            return self.service_registry.manny.probe(query=query, domain=domain)
        except Exception as e:
            logger.warning("Manny probe failed: %s", e)
            return None

    # ── Internal ────────────────────────────────────────────────────────────

    def _update_stats(self, result: Dict):
        self._stats["total"] += 1
        consensus = result.get("consensus", {})
        if consensus.get("consensus"):
            self._stats["consensual"] += 1
        else:
            self._stats["non_consensual"] += 1

        top = consensus.get("top_domain", "unknown")
        self._stats["by_domain"][top] = self._stats["by_domain"].get(top, 0) + 1

        n = self._stats["total"]
        self._stats["avg_confidence"] = round(
            (self._stats["avg_confidence"] * (n - 1) + result.get("confidence", 0)) / n, 4)
        self._stats["total_perspectives_used"] += result.get(
            "perspectives_used", len(result.get("perspectives", [])))

    def _audit(self, action: str, result: Dict):
        if not self.governance:
            return
        try:
            self.governance.record_boundary_event(
                event_type=f"thinktank:{action}",
                data={
                    "top_domain": result.get("consensus", {}).get("top_domain"),
                    "consensus": result.get("consensus", {}).get("consensus"),
                    "confidence": result.get("confidence"),
                    "perspectives_used": result.get("perspectives_used"),
                    "content_length": result.get("content_length"),
                },
            )
        except Exception as e:
            logger.warning("Governance audit failed: %s", e)
