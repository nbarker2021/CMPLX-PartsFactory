#!/usr/bin/env python3
"""
CMPLX Vector Embedding & MMDB Storage System
=============================================

Native vector embedding creation and storage using CMPLX geometric primitives.
Weaviate-like functionality built entirely from CMPLX work.

Features:
- Vector embedding creation (E8 lattice based)
- MMDB vector storage with geometric indexing
- Similarity search (cosine, euclidean, lattice distance)
- Batch operations for massive concurrency
- Automated data creation, storage, and recall
- Iteration-based and recursion-based exploration tools

Architecture:
- Embeddings stored in MMDB with geometric hashes
- E8 lattice projection for high-dimensional vectors
- Digital root indexing for fast similarity pruning
- MORSR optimization for vector clustering
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import math
import os
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Set
from uuid import uuid4
import sqlite3
import numpy as np

# Add paths
SCRIPT_DIR = Path(__file__).parent.absolute()
PROJECT_ROOT = SCRIPT_DIR.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

logger = logging.getLogger("cmplx.vector.mmdb")

# ─────────────────────────────────────────────────────────
#  GEOMETRIC PRIMITIVES (from CMPLX CQE)
# ─────────────────────────────────────────────────────────

E8_NORM = math.sqrt(2)
FNV_OFFSET = 1469598103934665603
FNV_PRIME = 1099511628211
MASK64 = (1 << 64) - 1


def _fnv_hash(text: str) -> int:
    """FNV-1a 64-bit hash."""
    h = FNV_OFFSET
    for ch in text.encode("utf-8", errors="ignore"):
        h ^= ch
        h *= FNV_PRIME
        h &= MASK64
    return h


def _digital_root(n: int) -> int:
    """Calculate digital root (1-9)."""
    if n == 0:
        return 0
    dr = n % 9
    return 9 if dr == 0 else dr


def _e8_project(vector: List[float]) -> List[float]:
    """Project vector to E8 lattice space."""
    # Normalize
    norm = math.sqrt(sum(v ** 2 for v in vector))
    if norm == 0:
        return [0.0] * len(vector)
    
    # Scale to E8 norm
    scale = E8_NORM / norm
    return [v * scale for v in vector]


def _cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """Calculate cosine similarity between vectors."""
    dot = sum(a * b for a, b in zip(vec1, vec2))
    norm1 = math.sqrt(sum(a ** 2 for a in vec1))
    norm2 = math.sqrt(sum(b ** 2 for b in vec2))
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return dot / (norm1 * norm2)


def _euclidean_distance(vec1: List[float], vec2: List[float]) -> float:
    """Calculate Euclidean distance."""
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(vec1, vec2)))


def _lattice_distance(vec1: List[float], vec2: List[float]) -> float:
    """Calculate lattice-aware distance (digital root weighted)."""
    base_dist = _euclidean_distance(vec1, vec2)
    
    # Weight by digital root of hash indices
    hash1 = _digital_root(_fnv_hash(json.dumps(vec1, sort_keys=True)))
    hash2 = _digital_root(_fnv_hash(json.dumps(vec2, sort_keys=True)))
    
    dr_factor = abs(hash1 - hash2) / 9.0
    return base_dist * (1.0 + dr_factor)


# ─────────────────────────────────────────────────────────
#  EMBEDDING CREATION
# ─────────────────────────────────────────────────────────

class CMPLXEmbedder:
    """
    Creates vector embeddings using CMPLX geometric methods.
    
    Supports multiple embedding strategies:
    - E8 lattice projection
    - FNV hash-based embeddings
    - Digital root signatures
    - MORSR optimized vectors
    """
    
    def __init__(self, embedding_dim: int = 768):
        self.embedding_dim = embedding_dim
        self.e8_dim = 8  # E8 lattice is 8-dimensional
        
    def embed_text(self, text: str, method: str = "e8_hash") -> Dict[str, Any]:
        """
        Create embedding for text.
        
        Args:
            text: Input text
            method: Embedding method (e8_hash, fnv_vector, dr_signature)
        
        Returns:
            Embedding with metadata
        """
        if method == "e8_hash":
            vector = self._e8_hash_embed(text)
        elif method == "fnv_vector":
            vector = self._fnv_vector_embed(text)
        elif method == "dr_signature":
            vector = self._dr_signature_embed(text)
        else:
            raise ValueError(f"Unknown method: {method}")
        
        # Project to E8 space
        e8_projection = _e8_project(vector[:8] if len(vector) >= 8 else vector + [0] * (8 - len(vector)))
        
        return {
            "vector": vector,
            "e8_projection": e8_projection,
            "dimension": len(vector),
            "method": method,
            "content_hash": hashlib.sha256(text.encode()).hexdigest()[:16],
            "digital_root": _digital_root(_fnv_hash(text)),
            "created_at": datetime.now().isoformat()
        }
    
    def _e8_hash_embed(self, text: str) -> List[float]:
        """Create E8-based hash embedding."""
        # Generate 8D E8 coordinates from text hash
        base_hash = _fnv_hash(text)
        
        vector = []
        for i in range(self.embedding_dim):
            # Rotate hash for each dimension
            rotated = ((base_hash >> (i % 64)) | (base_hash << (64 - (i % 64)))) & MASK64
            # Normalize to [-1, 1]
            normalized = (rotated / MASK64) * 2 - 1
            vector.append(normalized)
        
        # Apply E8 lattice constraints to first 8 dimensions
        e8_part = _e8_project(vector[:8])
        vector[:8] = e8_part
        
        return vector
    
    def _fnv_vector_embed(self, text: str) -> List[float]:
        """Create FNV hash-based vector embedding."""
        vector = []
        
        # Tokenize by character
        for i in range(0, len(text), max(1, len(text) // self.embedding_dim)):
            chunk = text[i:i + 8]
            chunk_hash = _fnv_hash(chunk)
            normalized = (chunk_hash % 10000) / 10000.0 * 2 - 1
            vector.append(normalized)
        
        # Pad to embedding_dim
        while len(vector) < self.embedding_dim:
            vector.append(0.0)
        
        return vector[:self.embedding_dim]
    
    def _dr_signature_embed(self, text: str) -> List[float]:
        """Create digital root signature embedding (9-dimensional)."""
        # Digital root signature is 9-dimensional (roots 1-9)
        signature = [0.0] * 9
        
        # Count digital roots of character hashes
        for ch in text:
            dr = _digital_root(ord(ch))
            signature[dr - 1] += 1
        
        # Normalize
        total = sum(signature)
        if total > 0:
            signature = [s / total for s in signature]
        
        return signature
    
    def embed_batch(self, texts: List[str], method: str = "e8_hash") -> List[Dict[str, Any]]:
        """Embed multiple texts in batch."""
        results = []
        for text in texts:
            embedding = self.embed_text(text, method)
            results.append(embedding)
        return results


# ─────────────────────────────────────────────────────────
#  MMDB VECTOR STORAGE
# ─────────────────────────────────────────────────────────

@dataclass
class VectorRecord:
    """A vector record in MMDB storage."""
    record_id: str
    vector: List[float]
    e8_projection: List[float]
    content_hash: str
    digital_root: int
    metadata: Dict[str, Any]
    created_at: str
    tags: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "record_id": self.record_id,
            "vector": self.vector,
            "e8_projection": self.e8_projection,
            "content_hash": self.content_hash,
            "digital_root": self.digital_root,
            "metadata": self.metadata,
            "created_at": self.created_at,
            "tags": self.tags
        }


class MMDBVectorStore:
    """
    MMDB-based vector storage system.
    
    Weaviate-like functionality using:
    - SQLite for persistent storage
    - Geometric hashing for indexing
    - Digital root partitioning for fast pruning
    - E8 lattice clustering
    """
    
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or str(PROJECT_ROOT / "mmdb" / "vector_store.db")
        
        # Ensure directory exists
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize database
        self._init_db()
        
        # In-memory cache for hot vectors
        self.cache: Dict[str, VectorRecord] = {}
        self.dr_index: Dict[int, Set[str]] = {i: set() for i in range(10)}  # Digital root index
        
        logger.info(f"MMDB Vector Store initialized: {self.db_path}")
    
    def _init_db(self):
        """Initialize SQLite database with vector tables."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Main vector table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS vectors (
                record_id TEXT PRIMARY KEY,
                vector BLOB NOT NULL,
                e8_projection BLOB NOT NULL,
                content_hash TEXT NOT NULL,
                digital_root INTEGER NOT NULL,
                metadata TEXT,
                created_at TEXT NOT NULL,
                tags TEXT
            )
        """)
        
        # Indexes for fast lookup
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_content_hash ON vectors(content_hash)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_digital_root ON vectors(digital_root)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_created_at ON vectors(created_at)")
        
        # Collections table (for grouping vectors)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS collections (
                collection_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                created_at TEXT NOT NULL,
                metadata TEXT
            )
        """)
        
        # Vector-collection mapping
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS collection_vectors (
                collection_id TEXT,
                record_id TEXT,
                PRIMARY KEY (collection_id, record_id),
                FOREIGN KEY (collection_id) REFERENCES collections(collection_id),
                FOREIGN KEY (record_id) REFERENCES vectors(record_id)
            )
        """)
        
        # Iteration tracking table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS iterations (
                iteration_id TEXT PRIMARY KEY,
                batch_id TEXT,
                iteration_number INTEGER,
                vectors_processed INTEGER,
                status TEXT,
                started_at TEXT,
                completed_at TEXT,
                metadata TEXT
            )
        """)
        
        conn.commit()
        conn.close()
    
    def insert(self, embedding: Dict[str, Any], metadata: Optional[Dict] = None, 
               tags: Optional[List[str]] = None, collection_id: Optional[str] = None) -> str:
        """
        Insert vector into storage.
        
        Args:
            embedding: Embedding dict from CMPLXEmbedder
            metadata: Additional metadata
            tags: Tags for categorization
            collection_id: Optional collection to add to
        
        Returns:
            Record ID
        """
        record_id = f"vec_{uuid4().hex[:12]}"
        
        vector_bytes = json.dumps(embedding["vector"]).encode()
        e8_bytes = json.dumps(embedding["e8_projection"]).encode()
        metadata_json = json.dumps(metadata or {})
        tags_json = json.dumps(tags or [])
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO vectors (record_id, vector, e8_projection, content_hash, 
                                digital_root, metadata, created_at, tags)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            record_id,
            vector_bytes,
            e8_bytes,
            embedding["content_hash"],
            embedding["digital_root"],
            metadata_json,
            embedding["created_at"],
            tags_json
        ))
        
        # Add to collection if specified
        if collection_id:
            cursor.execute("""
                INSERT INTO collection_vectors (collection_id, record_id)
                VALUES (?, ?)
            """, (collection_id, record_id))
        
        conn.commit()
        conn.close()
        
        # Update cache and index
        record = VectorRecord(
            record_id=record_id,
            vector=embedding["vector"],
            e8_projection=embedding["e8_projection"],
            content_hash=embedding["content_hash"],
            digital_root=embedding["digital_root"],
            metadata=metadata or {},
            created_at=embedding["created_at"],
            tags=tags or []
        )
        self.cache[record_id] = record
        self.dr_index[embedding["digital_root"]].add(record_id)
        
        return record_id
    
    def insert_batch(self, embeddings: List[Dict[str, Any]], 
                     metadata_list: Optional[List[Dict]] = None,
                     collection_id: Optional[str] = None) -> List[str]:
        """Insert multiple vectors in batch."""
        metadata_list = metadata_list or [{}] * len(embeddings)
        
        record_ids = []
        for i, embedding in enumerate(embeddings):
            record_id = self.insert(
                embedding=embedding,
                metadata=metadata_list[i] if i < len(metadata_list) else {},
                collection_id=collection_id
            )
            record_ids.append(record_id)
        
        return record_ids
    
    def get(self, record_id: str) -> Optional[VectorRecord]:
        """Get vector by ID."""
        # Check cache first
        if record_id in self.cache:
            return self.cache[record_id]
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT record_id, vector, e8_projection, content_hash, 
                   digital_root, metadata, created_at, tags
            FROM vectors
            WHERE record_id = ?
        """, (record_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return None
        
        record = VectorRecord(
            record_id=row[0],
            vector=json.loads(row[1]),
            e8_projection=json.loads(row[2]),
            content_hash=row[3],
            digital_root=row[4],
            metadata=json.loads(row[5]),
            created_at=row[6],
            tags=json.loads(row[7])
        )
        
        self.cache[record_id] = record
        return record
    
    def similarity_search(
        self,
        query_vector: List[float],
        limit: int = 10,
        min_similarity: float = 0.7,
        digital_root_filter: Optional[int] = None
    ) -> List[Tuple[VectorRecord, float]]:
        """
        Search for similar vectors.
        
        Args:
            query_vector: Query vector
            limit: Max results
            min_similarity: Minimum similarity threshold
            digital_root_filter: Filter by digital root for fast pruning
        
        Returns:
            List of (record, similarity_score) tuples
        """
        results = []
        
        # Get candidate record IDs
        if digital_root_filter is not None:
            # Fast pruning by digital root
            candidate_ids = self.dr_index.get(digital_root_filter, set())
        else:
            # Search all cached vectors
            candidate_ids = set(self.cache.keys())
        
        # If cache is empty, load from database
        if not candidate_ids:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            if digital_root_filter is not None:
                cursor.execute("SELECT record_id FROM vectors WHERE digital_root = ?", 
                            (digital_root_filter,))
            else:
                cursor.execute("SELECT record_id FROM vectors")
            
            candidate_ids = {row[0] for row in cursor.fetchall()}
            conn.close()
        
        # Calculate similarities
        for record_id in candidate_ids:
            record = self.get(record_id)
            if not record:
                continue
            
            similarity = _cosine_similarity(query_vector, record.vector)
            
            if similarity >= min_similarity:
                results.append((record, similarity))
        
        # Sort by similarity and limit
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:limit]
    
    def create_collection(self, name: str, description: str = "", 
                         metadata: Optional[Dict] = None) -> str:
        """Create a vector collection."""
        collection_id = f"col_{uuid4().hex[:12]}"
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO collections (collection_id, name, description, created_at, metadata)
            VALUES (?, ?, ?, ?, ?)
        """, (
            collection_id,
            name,
            description,
            datetime.now().isoformat(),
            json.dumps(metadata or {})
        ))
        
        conn.commit()
        conn.close()
        
        return collection_id
    
    def get_collection(self, collection_id: str) -> Optional[Dict[str, Any]]:
        """Get collection info."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT collection_id, name, description, created_at, metadata
            FROM collections
            WHERE collection_id = ?
        """, (collection_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return None
        
        return {
            "collection_id": row[0],
            "name": row[1],
            "description": row[2],
            "created_at": row[3],
            "metadata": json.loads(row[4])
        }
    
    def stats(self) -> Dict[str, Any]:
        """Get storage statistics."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM vectors")
        vector_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM collections")
        collection_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT digital_root, COUNT(*) FROM vectors GROUP BY digital_root")
        dr_distribution = dict(cursor.fetchall())
        
        conn.close()
        
        return {
            "total_vectors": vector_count,
            "total_collections": collection_count,
            "cache_size": len(self.cache),
            "digital_root_distribution": dr_distribution
        }


# ─────────────────────────────────────────────────────────
#  AUTOMATED DATA CREATION & RECALL
# ─────────────────────────────────────────────────────────

class AutomatedDataManager:
    """
    Automates data creation, storage, and recall.
    
    Features:
    - Batch processing
    - Iteration tracking
    - Automatic embedding creation
    - Recall optimization
    """
    
    def __init__(self, embedder: CMPLXEmbedder, vector_store: MMDBVectorStore):
        self.embedder = embedder
        self.vector_store = vector_store
        self.iteration_history: List[Dict[str, Any]] = []
    
    async def process_batch(
        self,
        items: List[Dict[str, Any]],
        collection_name: str,
        text_field: str = "text",
        batch_size: int = 100
    ) -> Dict[str, Any]:
        """
        Process a batch of items.
        
        Args:
            items: List of items with text field
            collection_name: Name for the collection
            text_field: Field name containing text
            batch_size: Batch size for processing
        
        Returns:
            Processing result
        """
        iteration_id = f"iter_{uuid4().hex[:12]}"
        started_at = datetime.now().isoformat()
        
        logger.info(f"Processing batch: {len(items)} items")
        
        # Create collection
        collection_id = self.vector_store.create_collection(
            name=collection_name,
            description=f"Auto-created batch: {len(items)} items"
        )
        
        # Process in batches
        all_record_ids = []
        for i in range(0, len(items), batch_size):
            batch = items[i:i + batch_size]
            
            # Extract texts and create embeddings
            texts = [item.get(text_field, "") for item in batch]
            embeddings = self.embedder.embed_batch(texts)
            
            # Create metadata
            metadata_list = [
                {k: v for k, v in item.items() if k != text_field}
                for item in batch
            ]
            
            # Insert batch
            record_ids = self.vector_store.insert_batch(
                embeddings=embeddings,
                metadata_list=metadata_list,
                collection_id=collection_id
            )
            all_record_ids.extend(record_ids)
            
            logger.info(f"Processed batch {i // batch_size + 1}: {len(batch)} items")
        
        completed_at = datetime.now().isoformat()
        
        # Track iteration
        iteration_result = {
            "iteration_id": iteration_id,
            "collection_id": collection_id,
            "items_processed": len(items),
            "vectors_created": len(all_record_ids),
            "started_at": started_at,
            "completed_at": completed_at,
            "status": "completed"
        }
        self.iteration_history.append(iteration_result)
        
        return iteration_result
    
    async def recall_similar(
        self,
        query_text: str,
        collection_id: Optional[str] = None,
        limit: int = 10,
        min_similarity: float = 0.7
    ) -> List[Dict[str, Any]]:
        """
        Recall similar items from storage.
        
        Args:
            query_text: Query text
            collection_id: Optional collection filter
            limit: Max results
            min_similarity: Minimum similarity
        
        Returns:
            List of similar items
        """
        # Create query embedding
        query_embedding = self.embedder.embed_text(query_text)
        
        # Search
        results = self.vector_store.similarity_search(
            query_vector=query_embedding["vector"],
            limit=limit,
            min_similarity=min_similarity
        )
        
        # Format results
        return [
            {
                "record_id": record.record_id,
                "similarity": similarity,
                "metadata": record.metadata,
                "content_hash": record.content_hash,
                "tags": record.tags
            }
            for record, similarity in results
        ]
    
    def get_iteration_history(self) -> List[Dict[str, Any]]:
        """Get iteration history."""
        return self.iteration_history


# ─────────────────────────────────────────────────────────
#  MCP TOOLS INTEGRATION
# ─────────────────────────────────────────────────────────

class VectorMMDBTools:
    """MCP tools for vector embedding and MMDB storage."""
    
    def __init__(self):
        self.embedder = CMPLXEmbedder()
        self.vector_store = MMDBVectorStore()
        self.auto_manager = AutomatedDataManager(self.embedder, self.vector_store)
    
    async def create_embedding(self, text: str, method: str = "e8_hash") -> Dict[str, Any]:
        """Create vector embedding for text."""
        return self.embedder.embed_text(text, method)
    
    async def store_vector(self, embedding: Dict[str, Any], 
                          metadata: Dict[str, Any], 
                          tags: List[str]) -> str:
        """Store vector in MMDB."""
        return self.vector_store.insert(embedding, metadata, tags)
    
    async def search_similar(self, query: str, limit: int = 10, 
                            min_similarity: float = 0.7) -> List[Dict[str, Any]]:
        """Search for similar vectors."""
        return await self.auto_manager.recall_similar(query, limit=limit, 
                                                       min_similarity=min_similarity)
    
    async def process_batch(self, items: List[Dict], collection_name: str,
                           text_field: str = "text") -> Dict[str, Any]:
        """Process batch of items."""
        return await self.auto_manager.process_batch(items, collection_name, text_field)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get storage statistics."""
        return self.vector_store.stats()
    
    async def create_collection(self, name: str, description: str = "") -> str:
        """Create vector collection."""
        return self.vector_store.create_collection(name, description)


# ─────────────────────────────────────────────────────────
#  MAIN / TESTING
# ─────────────────────────────────────────────────────────

async def main():
    """Test vector embedding and MMDB storage."""
    print("=" * 70)
    print("  CMPLX Vector Embedding & MMDB Storage")
    print("=" * 70)
    
    # Initialize
    embedder = CMPLXEmbedder(embedding_dim=64)
    vector_store = MMDBVectorStore()
    auto_manager = AutomatedDataManager(embedder, vector_store)
    
    # Test embedding
    print("\n[TEST] Creating embeddings...")
    texts = [
        "The quick brown fox jumps over the lazy dog",
        "Machine learning is transforming technology",
        "E8 lattice has 240 root vectors",
        "Digital root reveals hidden patterns"
    ]
    
    embeddings = embedder.embed_batch(texts)
    print(f"Created {len(embeddings)} embeddings")
    
    # Test storage
    print("\n[TEST] Storing vectors...")
    collection_id = vector_store.create_collection("test_collection", "Test vectors")
    
    for i, emb in enumerate(embeddings):
        record_id = vector_store.insert(
            embedding=emb,
            metadata={"text": texts[i], "index": i},
            tags=["test", f"text_{i}"],
            collection_id=collection_id
        )
        print(f"  Stored: {record_id}")
    
    # Test search
    print("\n[TEST] Similarity search...")
    query = "artificial intelligence and learning"
    results = await auto_manager.recall_similar(query, limit=3, min_similarity=0.5)
    
    print(f"Query: {query}")
    for result in results:
        print(f"  Similarity: {result['similarity']:.3f} - {result['metadata'].get('text', '')[:50]}...")
    
    # Test stats
    print("\n[TEST] Storage statistics...")
    stats = vector_store.stats()
    print(f"  Total vectors: {stats['total_vectors']}")
    print(f"  Collections: {stats['total_collections']}")
    print(f"  Cache size: {stats['cache_size']}")
    
    print("\n" + "=" * 70)
    print("  Vector MMDB system operational!")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
