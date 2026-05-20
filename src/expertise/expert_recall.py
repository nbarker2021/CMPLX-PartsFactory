"""ExpertRecall — Existing experts can self-insert into relevant future tasks.

Pattern drawn from CMPLXUNI's agent_config system.
Experts self-identify relevance to incoming problems based on:
  - Domain match
  - Capability overlap
  - Prior success with similar problems
  - Semantic similarity via embeddings
"""

from __future__ import annotations
import time
import json
import logging
from typing import Dict, List, Any, Optional

import numpy as np

from .expert_memory import ExpertMemory
from .expert_registry import ExpertRegistry

logger = logging.getLogger("expertise.recall")


class ExpertRecall:
    """Expert recall system — experts self-insert into relevant tasks.

    Maintains a semantic index of expert capabilities and matches
    incoming problems against them to suggest relevant experts.
    """

    def __init__(self, registry: ExpertRegistry):
        self.registry = registry
        self._relevance_cache: Dict[str, float] = {}

    def find_relevant_experts(self, problem: str, domain: str = None,
                               top_k: int = 5,
                               min_relevance: float = 0.3) -> List[Dict[str, Any]]:
        """Find experts relevant to a given problem."""
        experts = self.registry.search_experts(domain=domain, limit=100)
        problem_embedding = self._compute_embedding(problem)

        scored = []
        for expert in experts:
            relevance = self._compute_relevance(expert, problem, problem_embedding)
            if relevance >= min_relevance:
                scored.append((relevance, expert))

        scored.sort(key=lambda x: x[0], reverse=True)
        result = []
        for relevance, expert in scored[:top_k]:
            expert_copy = dict(expert)
            expert_copy["relevance_score"] = relevance
            expert_copy["matched_by"] = "expert_recall"
            result.append(expert_copy)

        return result

    def self_insert(self, problem: str, active_expert_ids: List[str] = None,
                    domain: str = None) -> Dict[str, Any]:
        """Self-insert relevant experts into a problem context.

        Returns the problem augmented with relevant expert suggestions.
        """
        relevant = self.find_relevant_experts(problem, domain=domain)

        if active_expert_ids:
            relevant = [e for e in relevant
                        if e.get("expert_id") not in active_expert_ids]

        inserted_experts = []
        for expert in relevant[:3]:
            memory = ExpertMemory(expert["expert_id"])
            memory.connect()
            similar = memory.recall(problem, top_k=2)
            memory.close()
            inserted_experts.append({
                "expert_id": expert["expert_id"],
                "name": expert.get("name", "unknown"),
                "domain": expert.get("domain", "unknown"),
                "archetype": expert.get("archetype", "unknown"),
                "capabilities": expert.get("capabilities", []),
                "relevance_score": expert.get("relevance_score", 0.0),
                "similar_experiences": similar,
            })

        return {
            "problem": problem,
            "self_inserted_experts": inserted_experts,
            "suggestion": f"Consider involving {len(inserted_experts)} "
                          f"existing expert(s) with relevant experience",
        }

    def _compute_relevance(self, expert: Dict[str, Any],
                            problem: str,
                            problem_embedding: np.ndarray = None) -> float:
        """Compute relevance score between an expert and a problem."""
        if problem_embedding is None:
            problem_embedding = self._compute_embedding(problem)

        score = 0.0

        expert_purpose = expert.get("purpose", "")
        purpose_embedding = self._compute_embedding(expert_purpose)
        purpose_sim = float(np.dot(problem_embedding, purpose_embedding) /
                            (np.linalg.norm(problem_embedding) *
                             np.linalg.norm(purpose_embedding) + 1e-10))
        score += purpose_sim * 0.4

        capabilities = expert.get("capabilities", [])
        cap_text = " ".join(capabilities) if isinstance(capabilities, list) else str(capabilities)
        cap_embedding = self._compute_embedding(cap_text)
        cap_sim = float(np.dot(problem_embedding, cap_embedding) /
                        (np.linalg.norm(problem_embedding) *
                         np.linalg.norm(cap_embedding) + 1e-10))
        score += cap_sim * 0.3

        domain = expert.get("domain", "")
        domain_embedding = self._compute_embedding(domain)
        domain_sim = float(np.dot(problem_embedding, domain_embedding) /
                           (np.linalg.norm(problem_embedding) *
                            np.linalg.norm(domain_embedding) + 1e-10))
        score += domain_sim * 0.2

        success_rate = expert.get("success_rate", 0.0)
        performance_score = expert.get("performance_score", 0.0)
        score += (success_rate * 0.05 + performance_score * 0.05)

        return min(max(score, 0.0), 1.0)

    def _compute_embedding(self, text: str) -> np.ndarray:
        words = text.lower().split()
        embedding = np.zeros(128, dtype=np.float64)
        for i, word in enumerate(words[:128]):
            embedding[i % 128] += hash(word) % 10000 / 10000.0
        norm = np.linalg.norm(embedding)
        return embedding / (norm + 1e-10)
