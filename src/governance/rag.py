"""RAG-based knowledge base for agent tools."""
from __future__ import annotations
import time
import logging
from collections import defaultdict
from typing import Dict, List, Any, Tuple

try:
    import numpy as np
    HAVE_NUMPY = True
except ImportError:
    np = None
    HAVE_NUMPY = False

logger = logging.getLogger("rag")


class RAGKnowledgeBase:
    """RAG-based knowledge base with document indexing and similarity search."""

    def __init__(self):
        self.documents: Dict[str, Dict[str, Any]] = {}
        self.embeddings: Dict[str, np.ndarray] = {}
        self.index_mapping: Dict[str, List[str]] = defaultdict(list)

    def add_document(self, doc_id: str, content: str,
                     metadata: Dict[str, Any] = None) -> None:
        self.documents[doc_id] = {
            "content": content,
            "metadata": metadata or {},
            "timestamp": time.time(),
        }
        embedding = self._generate_embedding(content)
        self.embeddings[doc_id] = embedding
        for keyword in content.lower().split():
            self.index_mapping[keyword].append(doc_id)

    def _generate_embedding(self, text: str):
        if not HAVE_NUMPY:
            return [0.0] * 100
        words = text.lower().split()
        embedding = np.zeros(100)
        for i, word in enumerate(words[:100]):
            embedding[i % 100] += hash(word) % 1000 / 1000.0
        norm = np.linalg.norm(embedding)
        return embedding / (norm + 1e-10)

    def query(self, query_text: str, top_k: int = 5) -> List[Tuple[str, float, Dict[str, Any]]]:
        query_embedding = self._generate_embedding(query_text)
        similarities = []
        for doc_id, doc_embedding in self.embeddings.items():
            if HAVE_NUMPY:
                similarity = float(np.dot(query_embedding, doc_embedding))
            else:
                similarity = sum(a * b for a, b in zip(query_embedding, doc_embedding))
            similarities.append((doc_id, similarity, self.documents[doc_id]))
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:top_k]
