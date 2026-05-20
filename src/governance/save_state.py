"""SNAPDNASaveState — Universal data transformation to DNA strands with geometric recall."""
from __future__ import annotations
import time
import uuid
import logging
from typing import Dict, List, Any, Tuple

import numpy as np

logger = logging.getLogger("snapdna_save")


class SNAPDNASaveState:
    """Universal data transformation to DNA strands with geometry-based recall."""

    def __init__(self, dna_encoder):
        self.dna_encoder = dna_encoder
        self.save_states: Dict[str, Dict[str, Any]] = {}
        self.type_mappings: Dict[str, str] = {}

    def snap_data(self, data: Any, save_state_id: str = None,
                  context_metadata: Dict[str, Any] = None) -> str:
        if save_state_id is None:
            save_state_id = f"snap_{int(time.time())}_{str(uuid.uuid4())[:8]}"
        analysis = self._analyze_data(data)
        tailored = self._create_tailored_encoding(data, analysis)
        ctx = context_metadata or {}
        ctx.update({
            "data_type": analysis["type"],
            "data_structure": analysis["structure"],
            "encoding_strategy": tailored["strategy"],
            "relevance_score": tailored["relevance_score"],
        })
        from .dna import DNAStrand
        strand = DNAStrand()
        strand.encode_data({
            "original_data": data,
            "tailored_metadata": ctx,
            "encoding_info": tailored,
        })
        slices = self._generate_embedding_slices(data, analysis)
        for s in slices:
            strand.add_embedding(s)
        strand_id = self.dna_encoder.encode(
            {"original_data": data, "context": ctx}, save_state_id
        )
        self.save_states[save_state_id] = {
            "save_state_id": save_state_id,
            "strand_id": strand_id,
            "original_type": type(data).__name__,
            "data_analysis": analysis,
            "tailored_encoding": tailored,
            "context_metadata": ctx,
            "created_at": time.time(),
        }
        self.type_mappings[type(data).__name__] = tailored["strategy"]
        return save_state_id

    def _analyze_data(self, data: Any) -> Dict[str, Any]:
        analysis = {"type": type(data).__name__, "size": len(str(data)),
                     "complexity": 1, "structure": "simple"}
        if isinstance(data, dict):
            analysis.update({"structure": "dictionary", "complexity": len(data),
                             "keys": list(data.keys())})
        elif isinstance(data, list):
            analysis.update({"structure": "list", "complexity": len(data),
                             "element_types": list(set(type(i).__name__ for i in data))})
        elif isinstance(data, str):
            analysis["structure"] = "string"
            analysis["complexity"] = len(data.split())
        elif isinstance(data, (int, float)):
            analysis["structure"] = "numeric"
        return analysis

    def _create_tailored_encoding(self, data: Any, analysis: Dict[str, Any]) -> Dict[str, Any]:
        encoding = {"strategy": "default", "relevance_score": 1.0, "optimization_hints": []}
        if analysis["structure"] == "dictionary":
            encoding.update({"strategy": "key_value_optimized", "relevance_score": 0.9,
                             "optimization_hints": ["preserve_key_order", "compress_common_keys"]})
        elif analysis["structure"] == "list":
            encoding.update({"strategy": "sequence_optimized", "relevance_score": 0.8,
                             "optimization_hints": ["preserve_order", "compress_repeats"]})
        elif analysis["structure"] == "numeric":
            encoding.update({"strategy": "numeric_optimized", "relevance_score": 0.95,
                             "optimization_hints": ["preserve_precision", "compact_representation"]})
        elif analysis["structure"] == "string":
            encoding.update({"strategy": "text_optimized", "relevance_score": 0.7,
                             "optimization_hints": ["compress_common_words", "preserve_semantics"]})
        return encoding

    def _generate_embedding_slices(self, data: Any, analysis: Dict[str, Any]) -> List[np.ndarray]:
        slices = []
        if analysis["structure"] == "dictionary" and isinstance(data, dict):
            slices.append(self._text_to_embedding(" ".join(str(k) for k in data.keys())))
            slices.append(self._text_to_embedding(" ".join(str(v) for v in data.values())))
        elif analysis["structure"] == "list" and isinstance(data, list):
            slices.append(self._text_to_embedding(" ".join(str(i) for i in data)))
        else:
            slices.append(self._text_to_embedding(str(data)))
        slices.append(self._text_to_embedding(analysis["type"]))
        return slices

    def _text_to_embedding(self, text: str) -> np.ndarray:
        words = text.lower().split()
        embedding = np.zeros(50)
        for i, word in enumerate(words[:50]):
            embedding[i % 50] += hash(word) % 1000 / 1000.0
        norm = np.linalg.norm(embedding)
        return embedding / (norm + 1e-10)

    def recall_by_geometry(self, query_embedding: np.ndarray,
                           top_k: int = 5) -> List[Tuple[str, float]]:
        similarities = []
        for ss_id, ss in self.save_states.items():
            sid = ss.get("strand_id")
            if sid and sid in getattr(self.dna_encoder, "strands", {}):
                strand = self.dna_encoder.strands[sid]
                max_sim = 0.0
                for es in getattr(strand, "embedding_vectors", []):
                    sim = float(np.dot(query_embedding, es))
                    max_sim = max(max_sim, sim)
                similarities.append((ss_id, max_sim))
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:top_k]

    def restore_save_state(self, save_state_id: str) -> Any:
        if save_state_id not in self.save_states:
            raise ValueError(f"Save state {save_state_id} not found")
        decoded = self.dna_encoder.decode(self.save_states[save_state_id]["strand_id"])
        if decoded and "original_data" in decoded:
            return decoded["original_data"]
        raise ValueError(f"Failed to restore save state {save_state_id}")
