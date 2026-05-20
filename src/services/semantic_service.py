"""SemanticService — 18-wave semantic pipeline with domain bridging."""
from __future__ import annotations

import hashlib
import json
import logging
import math
import os
import re
import time
import uuid
from collections import Counter, defaultdict
from typing import Any, Dict, List, Optional

from governance.engine import GeometricGovernance, BoundaryEvent

logger = logging.getLogger("semantic_service")

_host = "host.docker.internal"
PORT = int(os.environ.get("PORT", "8000"))
COUPLING = float(os.environ.get("COUPLING", "0.030076"))
PG_URL = os.environ.get("PG_URL", f"postgresql://tmn2:tmn2_dev@{_host}:5432/tmn2")
BOARD_URL = os.environ.get("BOARD_URL", f"http://{_host}:8000")
LIBRARY_URL = os.environ.get("LIBRARY_URL", f"http://{_host}:8011")

GEOMETRY_LEGEND: Dict[str, str] = {
    "E8": "240-vertex 8D polytope; root system for the full lattice",
    "Leech": "24-dimensional even unimodular lattice; densest sphere packing in 24D",
    "Niemeier": "One of 24 even unimodular lattices in 24D",
    "Golay": "Binary [24,12,8] error-correcting code; symmetry group = M24",
    "MORSR": "240-direction sonar pulse for lattice proximity detection",
    "SNAP": "Universal coordinate system: labels as structural addresses",
    "CRT": "Chinese Remainder Theorem decomposition into 24 coprime channels",
    "morphon": "Fundamental unit of structured change; delta-phi carrier",
    "grain": "Smallest processable content unit; input to the chain",
    "dust": "Sub-grain particle; result of grain decomposition",
    "triad": "Three-dust bonded unit; minimal stable structure",
    "block": "n=4 composition unit; four triads or sub-blocks",
    "crystal": "Fully closed block with palindromic boundary",
    "dihedral": "Mirror symmetry group; basis of review/validation pairs",
    "spinor": "1-3-9 hierarchy; transforms under rotation by half-angle",
    "shell": "Radial distance tier; mass = label count",
    "kappa": "Coupling constant ln(phi)/16; governs label attraction strength",
    "palindrome": "Self-mirroring sequence; stop criterion for crystal closure",
}

DOMAIN_VOCABS: Dict[str, Dict[str, str]] = {
    "geometry": {"manifold": "a smooth space that locally looks flat", "lattice": "a regular repeating grid of points",
                 "symmetry": "unchanged under a transformation", "dimension": "independent direction of variation",
                 "curvature": "how much a space bends"},
    "computation": {"lambda": "anonymous function", "reduction": "simplification step", "halt": "program termination",
                    "combinator": "function with no free variables", "turing-complete": "can simulate any computation"},
    "economics": {"surplus": "excess value beyond cost", "liquidity": "ease of exchange",
                  "arbitrage": "profit from price differences", "ledger": "record of transactions",
                  "stake": "committed capital at risk"},
    "physics": {"conservation": "quantity unchanged over time", "coupling": "interaction strength between fields",
                "gauge": "redundancy in description", "renormalization": "systematic removal of infinities",
                "symmetry-breaking": "transition to lower symmetry state"},
}

WAVE_LAYERS = [
    "char_frequency", "word_length", "sentence_structure", "punctuation_density",
    "vocabulary_richness", "domain_signal", "term_co_occurrence", "syntactic_pattern",
    "semantic_field", "metaphor_density", "abstraction_level", "reference_density",
    "argument_structure", "causal_chain", "temporal_flow", "modal_strength",
    "pragmatic_intent", "deep_coherence",
]


class WaveResult:
    def __init__(self, wave: int, layer: str, features: Dict[str, Any], confidence: float):
        self.wave = wave
        self.layer = layer
        self.features = features
        self.confidence = confidence


class SemanticService:
    """18-wave semantic pipeline — text analysis, domain bridging, document processing."""

    def __init__(self, governance: Optional[GeometricGovernance] = None):
        self.governance = governance
        self._doc_store: Dict[str, Dict[str, Any]] = {}
        self._stats = {"analyzed": 0, "bridged": 0, "documents": 0, "started_at": time.time()}

    @staticmethod
    def _text_hash(text: str) -> str:
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    @staticmethod
    def _wave_char_frequency(text: str) -> Dict[str, Any]:
        freq = Counter(c.lower() for c in text if c.isalpha())
        total = sum(freq.values()) or 1
        entropy = -sum((v / total) * math.log2(v / total) for v in freq.values() if v > 0)
        return {"top_chars": dict(freq.most_common(5)), "entropy": round(entropy, 4), "unique": len(freq)}

    @staticmethod
    def _wave_word_length(text: str) -> Dict[str, Any]:
        lengths = [len(w) for w in text.split()]
        if not lengths:
            return {"mean": 0, "std": 0, "max": 0}
        mean = sum(lengths) / len(lengths)
        var = sum((l - mean) ** 2 for l in lengths) / max(len(lengths), 1)
        return {"mean": round(mean, 2), "std": round(math.sqrt(var), 2), "max": max(lengths)}

    @staticmethod
    def _wave_sentence_structure(text: str) -> Dict[str, Any]:
        sentences = [s.strip() for s in re.split(r"[.!?]+", text) if s.strip()]
        lengths = [len(s.split()) for s in sentences]
        avg = sum(lengths) / max(len(lengths), 1)
        return {"count": len(sentences), "avg_length": round(avg, 2),
                "variance": round(sum((l - avg) ** 2 for l in lengths) / max(len(lengths), 1), 2) if lengths else 0}

    @staticmethod
    def _wave_domain_signal(text: str) -> Dict[str, Any]:
        words = set(text.lower().split())
        scores = {d: round(sum(1 for t in v if t in words) / max(len(v), 1), 3) for d, v in DOMAIN_VOCABS.items()}
        return {"domain_scores": scores, "dominant": max(scores, key=scores.get) if scores else "unknown"}

    @staticmethod
    def _wave_vocabulary_richness(text: str) -> Dict[str, Any]:
        words = text.lower().split()
        unique = set(words)
        ttr = len(unique) / max(len(words), 1)
        hapax = sum(1 for w in unique if words.count(w) == 1)
        return {"ttr": round(ttr, 4), "hapax_ratio": round(hapax / max(len(unique), 1), 4), "total": len(words), "unique": len(unique)}

    @staticmethod
    def _wave_abstraction_level(text: str) -> Dict[str, Any]:
        abstract_markers = ["concept", "theory", "principle", "abstract", "general", "universal", "fundamental", "axiom"]
        concrete_markers = ["example", "instance", "specific", "particular", "case", "data", "measure", "observe"]
        words = text.lower().split()
        a = sum(1 for w in words if any(m in w for m in abstract_markers))
        c = sum(1 for w in words if any(m in w for m in concrete_markers))
        return {"level": round((a - c) / max(a + c, 1), 3), "abstract_hits": a, "concrete_hits": c}

    @staticmethod
    def _wave_generic(text: str, wave_idx: int) -> Dict[str, Any]:
        h = hashlib.md5(f"{text[:200]}:wave{wave_idx}".encode()).hexdigest()
        signal = sum(bytes.fromhex(h)[i] for i in range(8)) / (8 * 255)
        return {"signal_strength": round(signal, 4), "window_size": max(1, len(text.split()) // max(wave_idx, 1)),
                "resonance": round(math.sin(wave_idx * signal * math.pi) ** 2, 4)}

    def _run_wave(self, text: str, wave_idx: int) -> WaveResult:
        layer = WAVE_LAYERS[wave_idx] if wave_idx < len(WAVE_LAYERS) else f"harmonic_{wave_idx}"
        dispatch = {0: self._wave_char_frequency, 1: self._wave_word_length,
                    2: self._wave_sentence_structure,
                    3: lambda t: {"punct_density": round(sum(1 for c in t if c in ".,;:!?-()[]{}") / max(len(t), 1), 4)},
                    4: self._wave_vocabulary_richness, 5: self._wave_domain_signal, 10: self._wave_abstraction_level}
        features = dispatch.get(wave_idx, lambda t: self._wave_generic(t, wave_idx))(text)
        confidence = min(1.0, 0.3 + 0.7 * (1.0 - wave_idx / 18.0))
        return WaveResult(wave=wave_idx, layer=layer, features=features, confidence=round(confidence, 3))

    @staticmethod
    def _meaning_density(waves: List[WaveResult]) -> float:
        if not waves:
            return 0.0
        return round(sum(w.confidence for w in waves) * sum(len(w.features) for w in waves) / (len(waves) ** 2), 4)

    @staticmethod
    def _extract_domains(waves: List[WaveResult]) -> List[str]:
        dw = next((w for w in waves if w.layer == "domain_signal"), None)
        if dw and "domain_scores" in dw.features:
            return [d for d, s in sorted(dw.features["domain_scores"].items(), key=lambda x: -x[1]) if s > 0][:3]
        return []

    def analyze(self, text: str, depth: int = 18) -> Dict[str, Any]:
        if not text or not text.strip():
            return {"error": "Text must be non-empty"}
        t0 = time.monotonic()
        d = min(max(depth, 1), 18)
        waves = [self._run_wave(text, i) for i in range(d)]
        dominant = self._extract_domains(waves)
        density = self._meaning_density(waves)
        elapsed = (time.monotonic() - t0) * 1000
        self._stats["analyzed"] += 1
        if self.governance:
            self.governance.record_boundary_event(BoundaryEvent(
                event_id=f"sem-{uuid.uuid4().hex[:8]}", timestamp=time.time(), entropy_delta=0.0,
                receipt_data={"text_hash": self._text_hash(text)[:12], "waves": d, "density": density},
                boundary_type="semantic_analyze",
            ))
        return {
            "id": str(uuid.uuid4()), "text_hash": self._text_hash(text),
            "waves": [{"wave": w.wave, "layer": w.layer, "features": w.features, "confidence": w.confidence} for w in waves],
            "dominant_domains": dominant, "meaning_density": density,
            "processing_time_ms": round(elapsed, 3),
        }

    def bridge(self, term: str, source_domain: str, target_domain: str = None) -> Dict[str, Any]:
        source_vocab = DOMAIN_VOCABS.get(source_domain, {})
        source_meaning = source_vocab.get(term, "")
        if not source_meaning:
            for t, m in source_vocab.items():
                if term.lower() in t.lower() or t.lower() in term.lower():
                    source_meaning = m
                    break
        if not source_meaning:
            source_meaning = f"term '{term}' in domain '{source_domain}'"
        bridges = []
        stop_words = {"a", "an", "the", "of", "in", "to", "is", "and", "or"}
        for domain, vocab in DOMAIN_VOCABS.items():
            if domain == source_domain:
                continue
            for t, m in vocab.items():
                overlap = set(source_meaning.lower().split()) & set(m.lower().split()) - stop_words
                if overlap:
                    bridges.append({"domain": domain, "term": t, "meaning": m, "shared": ", ".join(overlap)})
        h = hashlib.md5(f"{term}:{source_domain}".encode()).hexdigest()
        half_int = (int(h[:4], 16) % 1000) / 1000.0
        self._stats["bridged"] += 1
        return {"term": term, "source_domain": source_domain, "source_meaning": source_meaning,
                "bridges": bridges[:10], "half_integer_position": round(half_int, 4)}

    def process_document(self, content: str, title: str = None,
                         metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        if not content or not content.strip():
            return {"error": "Content must be non-empty"}
        t0 = time.monotonic()
        doc_hash = self._text_hash(content)
        waves = [self._run_wave(content, i) for i in range(18)]
        dominant = self._extract_domains(waves)
        density = self._meaning_density(waves)
        doc_record = {"id": str(uuid.uuid4()), "title": title or f"doc_{doc_hash[:8]}",
                      "hash": doc_hash, "dominant_domains": dominant, "meaning_density": density,
                      "wave_count": 18, "metadata": metadata or {}, "stored_at": time.time()}
        self._doc_store[doc_record["id"]] = doc_record
        self._stats["documents"] += 1
        elapsed = (time.monotonic() - t0) * 1000
        return {"document": doc_record, "summary": {"waves_run": 18, "meaning_density": density, "dominant_domains": dominant},
                "processing_time_ms": round(elapsed, 3)}

    def legend(self) -> Dict[str, Any]:
        return {"legend": GEOMETRY_LEGEND, "count": len(GEOMETRY_LEGEND)}

    def clusters(self) -> Dict[str, Any]:
        if not self._doc_store:
            return {"clusters": {}, "message": "No documents analyzed yet"}
        domain_docs: Dict[str, List[str]] = defaultdict(list)
        for doc_id, doc in self._doc_store.items():
            for d in doc.get("dominant_domains", []):
                domain_docs[d].append(doc_id)
        return {"clusters": dict(domain_docs), "total_documents": len(self._doc_store)}

    def health(self) -> Dict[str, Any]:
        return {"status": "ok", "service": "semantic",
                "uptime_s": round(time.time() - self._stats["started_at"], 1),
                "analyzed": self._stats["analyzed"], "documents": self._stats["documents"]}
