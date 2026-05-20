"""
Caching Utilities for CQE Runtime

Provides efficient caching for expensive operations like:
- E8 lattice projections
- Niemeier lattice lookups
- Weyl chamber computations
- Phi metric calculations

Author: Manus AI
Date: December 5, 2025
"""

import numpy as np
from typing import Any, Dict, Optional, Tuple
from collections import OrderedDict
import hashlib
import time


def vector_hash(vec: np.ndarray, precision: int = 6) -> str:
    """
    Create a hash key from a vector.
    
    Args:
        vec: Input vector
        precision: Number of decimal places for rounding
    
    Returns:
        Hash string
    """
    rounded = np.round(vec, precision)
    vec_bytes = rounded.tobytes()
    return hashlib.md5(vec_bytes).hexdigest()[:16]


class LRUCache:
    """
    Least Recently Used (LRU) cache implementation.
    
    Automatically evicts least recently used items when capacity is reached.
    """
    
    def __init__(self, capacity: int = 1000):
        """
        Initialize LRU cache.
        
        Args:
            capacity: Maximum number of items to cache
        """
        self.capacity = capacity
        self.cache: OrderedDict = OrderedDict()
        self.hits = 0
        self.misses = 0
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get item from cache.
        
        Args:
            key: Cache key
        
        Returns:
            Cached value or None if not found
        """
        if key in self.cache:
            self.hits += 1
            # Move to end (most recently used)
            self.cache.move_to_end(key)
            return self.cache[key]
        else:
            self.misses += 1
            return None
    
    def put(self, key: str, value: Any):
        """
        Put item in cache.
        
        Args:
            key: Cache key
            value: Value to cache
        """
        if key in self.cache:
            # Update existing item
            self.cache.move_to_end(key)
        else:
            # Add new item
            if len(self.cache) >= self.capacity:
                # Remove least recently used item
                self.cache.popitem(last=False)
        
        self.cache[key] = value
    
    def clear(self):
        """Clear the cache."""
        self.cache.clear()
        self.hits = 0
        self.misses = 0
    
    def hit_rate(self) -> float:
        """Calculate cache hit rate."""
        total = self.hits + self.misses
        if total == 0:
            return 0.0
        return self.hits / total
    
    def __len__(self) -> int:
        return len(self.cache)
    
    def __repr__(self) -> str:
        return (f"LRUCache(capacity={self.capacity}, size={len(self)}, "
                f"hit_rate={self.hit_rate():.2%})")


class LatticeCache:
    """
    Specialized cache for lattice operations.
    
    Caches:
    - E8 projections
    - Leech embeddings
    - Niemeier lattice lookups
    - Weyl chamber determinations
    """
    
    def __init__(self, capacity: int = 10000):
        """
        Initialize lattice cache.
        
        Args:
            capacity: Maximum number of items per cache type
        """
        self.e8_cache = LRUCache(capacity)
        self.leech_cache = LRUCache(capacity)
        self.niemeier_cache = LRUCache(capacity // 10)
        self.weyl_cache = LRUCache(capacity)
    
    def get_e8_projection(self, vec: np.ndarray) -> Optional[np.ndarray]:
        """Get cached E8 projection."""
        key = vector_hash(vec)
        return self.e8_cache.get(key)
    
    def put_e8_projection(self, vec: np.ndarray, projected: np.ndarray):
        """Cache E8 projection."""
        key = vector_hash(vec)
        self.e8_cache.put(key, projected.copy())
    
    def get_leech_embedding(self, vec: np.ndarray) -> Optional[np.ndarray]:
        """Get cached Leech embedding."""
        key = vector_hash(vec)
        return self.leech_cache.get(key)
    
    def put_leech_embedding(self, vec: np.ndarray, embedded: np.ndarray):
        """Cache Leech embedding."""
        key = vector_hash(vec)
        self.leech_cache.put(key, embedded.copy())
    
    def get_weyl_chamber(self, vec: np.ndarray) -> Optional[str]:
        """Get cached Weyl chamber signature."""
        key = vector_hash(vec)
        return self.weyl_cache.get(key)
    
    def put_weyl_chamber(self, vec: np.ndarray, signature: str):
        """Cache Weyl chamber signature."""
        key = vector_hash(vec)
        self.weyl_cache.put(key, signature)
    
    def clear_all(self):
        """Clear all caches."""
        self.e8_cache.clear()
        self.leech_cache.clear()
        self.niemeier_cache.clear()
        self.weyl_cache.clear()
    
    def stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return {
            'e8': {
                'size': len(self.e8_cache),
                'hit_rate': self.e8_cache.hit_rate()
            },
            'leech': {
                'size': len(self.leech_cache),
                'hit_rate': self.leech_cache.hit_rate()
            },
            'niemeier': {
                'size': len(self.niemeier_cache),
                'hit_rate': self.niemeier_cache.hit_rate()
            },
            'weyl': {
                'size': len(self.weyl_cache),
                'hit_rate': self.weyl_cache.hit_rate()
            }
        }
    
    def __repr__(self) -> str:
        stats = self.stats()
        return (f"LatticeCache(e8={stats['e8']['size']}, "
                f"leech={stats['leech']['size']}, "
                f"weyl={stats['weyl']['size']})")


class ResultCache:
    """
    General-purpose result cache with TTL (time-to-live) support.
    
    Useful for caching:
    - Phi metric computations
    - Conservation checks
    - Validation results
    """
    
    def __init__(self, capacity: int = 5000, ttl: float = 3600.0):
        """
        Initialize result cache.
        
        Args:
            capacity: Maximum number of items to cache
            ttl: Time-to-live in seconds (default 1 hour)
        """
        self.capacity = capacity
        self.ttl = ttl
        self.cache: OrderedDict = OrderedDict()
        self.timestamps: Dict[str, float] = {}
        self.hits = 0
        self.misses = 0
    
    def _is_expired(self, key: str) -> bool:
        """Check if cache entry has expired."""
        if key not in self.timestamps:
            return True
        
        age = time.time() - self.timestamps[key]
        return age > self.ttl
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get item from cache.
        
        Args:
            key: Cache key
        
        Returns:
            Cached value or None if not found or expired
        """
        if key in self.cache and not self._is_expired(key):
            self.hits += 1
            self.cache.move_to_end(key)
            return self.cache[key]
        else:
            self.misses += 1
            # Remove expired entry
            if key in self.cache:
                del self.cache[key]
                del self.timestamps[key]
            return None
    
    def put(self, key: str, value: Any):
        """
        Put item in cache.
        
        Args:
            key: Cache key
            value: Value to cache
        """
        if key in self.cache:
            self.cache.move_to_end(key)
        else:
            if len(self.cache) >= self.capacity:
                # Remove oldest item
                old_key = next(iter(self.cache))
                del self.cache[old_key]
                del self.timestamps[old_key]
        
        self.cache[key] = value
        self.timestamps[key] = time.time()
    
    def clear_expired(self):
        """Remove all expired entries."""
        expired_keys = [k for k in self.cache.keys() if self._is_expired(k)]
        for key in expired_keys:
            del self.cache[key]
            del self.timestamps[key]
    
    def clear(self):
        """Clear the cache."""
        self.cache.clear()
        self.timestamps.clear()
        self.hits = 0
        self.misses = 0
    
    def hit_rate(self) -> float:
        """Calculate cache hit rate."""
        total = self.hits + self.misses
        if total == 0:
            return 0.0
        return self.hits / total
    
    def __len__(self) -> int:
        return len(self.cache)
    
    def __repr__(self) -> str:
        return (f"ResultCache(capacity={self.capacity}, size={len(self)}, "
                f"ttl={self.ttl}s, hit_rate={self.hit_rate():.2%})")
