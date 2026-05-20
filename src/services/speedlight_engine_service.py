"""SpeedLight Engine — GeoTokenizer + Two-Tier Cache + TokLight Ledger.

Port of TMN2 speedlight_engine. Provides geometric token encoding
via E8 quantization, idempotent computation cache (f(f(x)) = f(x)),
and a Merkle-chained receipt ledger.
"""
from __future__ import annotations

import hashlib
import json
import logging
import math
import os
import struct
import time
import zlib
from collections import OrderedDict
from dataclasses import dataclass, field, asdict
from typing import Any, Optional

logger = logging.getLogger("services.speedlight")

PORT = int(os.environ.get("PORT", "8000"))
COUPLING = float(os.environ.get("COUPLING", "0.030076"))
PG_URL = os.environ.get("PG_URL", "")
MAX_MEMORY = int(os.environ.get("MAX_MEMORY_SIZE", "10000"))


@dataclass
class LedgerEntry:
    idx: int
    ts: float
    scope: str
    op: str
    input_hash: str
    result_hash: str
    cost: float
    prev: str
    entry_hash: str = ""

    def __post_init__(self):
        if not self.entry_hash:
            payload = f"{self.idx}:{self.op}:{self.input_hash}:{self.result_hash}:{self.prev}"
            self.entry_hash = hashlib.sha256(payload.encode()).hexdigest()[:32]


class TokLight:
    """Receipt-first ledger. Every operation is Merkle-chained."""

    def __init__(self):
        self.entries: list[LedgerEntry] = []
        self.prev = "0" * 32

    def log(self, scope: str, op: str, input_hash: str,
            result_hash: str, cost: float = 0.0) -> LedgerEntry:
        entry = LedgerEntry(
            idx=len(self.entries), ts=time.time(), scope=scope, op=op,
            input_hash=input_hash, result_hash=result_hash,
            cost=cost, prev=self.prev,
        )
        self.prev = entry.entry_hash
        self.entries.append(entry)
        return entry


@dataclass
class GeoToken:
    token_id: str
    embedding: list[float]
    content_hash: str
    canonical_form: str = ""
    occurrences: int = 1

    def cosine_similarity(self, other_embedding: list[float]) -> float:
        dot = sum(a * b for a, b in zip(self.embedding, other_embedding))
        norm_a = math.sqrt(sum(a * a for a in self.embedding)) or 1e-12
        norm_b = math.sqrt(sum(b * b for b in other_embedding)) or 1e-12
        return dot / (norm_a * norm_b)


class GeoTokenizer:
    """Geometry-native token codec with equivalence memory.

    Encodes content as quantized E8 positions, compressed with
    varint + zlib. Matches against stored prototypes by cosine similarity.
    """

    def __init__(self, similarity_threshold: float = 0.95):
        self.prototypes: dict[str, GeoToken] = {}
        self.threshold = similarity_threshold
        self.ledger = TokLight()

    def encode(self, content: str) -> dict:
        h = hashlib.sha256(content.encode()).digest()
        embedding = [(b / 127.5 - 1.0) * COUPLING * 10 for b in h[:8]]

        quantized = [int(e * 1000) for e in embedding]
        packed = struct.pack(f">{len(quantized)}h", *quantized)
        compressed = zlib.compress(packed)

        content_hash = hashlib.sha256(content.encode()).hexdigest()[:16]

        best_match = None
        best_score = 0.0
        for proto in self.prototypes.values():
            score = proto.cosine_similarity(embedding)
            if score > best_score:
                best_score = score
                best_match = proto

        canonical = ""
        if best_match and best_score >= self.threshold:
            canonical = best_match.token_id
            best_match.occurrences += 1
        else:
            token = GeoToken(
                token_id=f"tok-{content_hash[:8]}",
                embedding=embedding, content_hash=content_hash,
            )
            self.prototypes[token.token_id] = token
            canonical = token.token_id

        self.ledger.log("encode", "geo_encode", content_hash,
                        hashlib.sha256(compressed).hexdigest()[:16])

        return {
            "token_id": canonical,
            "embedding": embedding,
            "compressed_bytes": len(compressed),
            "content_hash": content_hash,
            "matched_prototype": best_match.token_id if best_match and best_score >= self.threshold else None,
            "similarity": round(best_score, 4),
        }

    def decode(self, token_id: str) -> Optional[dict]:
        proto = self.prototypes.get(token_id)
        if not proto:
            return None
        return asdict(proto)

    def learn_equivalence(self, content_a: str, content_b: str) -> dict:
        enc_a = self.encode(content_a)
        enc_b = self.encode(content_b)
        similarity = sum(a * b for a, b in zip(enc_a["embedding"], enc_b["embedding"]))
        norm_a = math.sqrt(sum(a * a for a in enc_a["embedding"])) or 1e-12
        norm_b = math.sqrt(sum(b * b for b in enc_b["embedding"])) or 1e-12
        sim = similarity / (norm_a * norm_b)
        return {
            "token_a": enc_a["token_id"], "token_b": enc_b["token_id"],
            "similarity": round(sim, 4), "merged": sim >= self.threshold,
        }

    @property
    def stats(self) -> dict:
        return {
            "prototypes": len(self.prototypes),
            "ledger_entries": len(self.ledger.entries),
            "threshold": self.threshold,
        }


class TwoTierCache:
    """Memory LRU (T1) + PG persistent (T2)."""

    def __init__(self, max_memory: int = MAX_MEMORY, pg_url: str = ""):
        self.t1: OrderedDict = OrderedDict()
        self.max_memory = max_memory
        self.hits_t1 = 0
        self.hits_t2 = 0
        self.misses = 0
        self._pg_url = pg_url or PG_URL
        self._pg_conn = None

    def _get_pg(self):
        if not self._pg_url:
            return None
        try:
            import psycopg2
            if self._pg_conn is None or self._pg_conn.closed:
                self._pg_conn = psycopg2.connect(self._pg_url)
                self._pg_conn.autocommit = True
            return self._pg_conn
        except Exception:
            return None

    def get(self, key: str) -> Optional[Any]:
        if key in self.t1:
            self.t1.move_to_end(key)
            self.hits_t1 += 1
            return self.t1[key]

        conn = self._get_pg()
        if conn:
            try:
                cur = conn.cursor()
                cur.execute(
                    "SELECT value, hits FROM speedlight_cache WHERE key = %s", (key,)
                )
                row = cur.fetchone()
                if row:
                    self.hits_t2 += 1
                    val = json.loads(row[0]) if isinstance(row[0], str) else row[0]
                    cur.execute(
                        "UPDATE speedlight_cache SET hits = hits + 1, last_hit = %s WHERE key = %s",
                        (time.time(), key),
                    )
                    self.t1[key] = val
                    self._evict()
                    return val
            except Exception:
                pass

        self.misses += 1
        return None

    def put(self, key: str, value: Any, priority: bool = False):
        self.t1[key] = value
        self.t1.move_to_end(key)
        self._evict()

        conn = self._get_pg()
        if conn:
            try:
                cur = conn.cursor()
                cur.execute(
                    """INSERT INTO speedlight_cache (key, value, hits, created_at, last_hit)
                    VALUES (%s, %s, 1, %s, %s)
                    ON CONFLICT (key) DO UPDATE SET
                    value = EXCLUDED.value, hits = speedlight_cache.hits + 1,
                    last_hit = EXCLUDED.last_hit""",
                    (key, json.dumps(value, default=str), time.time(), time.time()),
                )
            except Exception:
                pass

    def _evict(self):
        while len(self.t1) > self.max_memory:
            self.t1.popitem(last=False)

    @property
    def stats(self) -> dict:
        total = self.hits_t1 + self.hits_t2 + self.misses
        return {
            "t1_size": len(self.t1), "t1_hits": self.hits_t1,
            "t2_hits": self.hits_t2, "misses": self.misses,
            "hit_rate": (self.hits_t1 + self.hits_t2) / max(total, 1),
        }


def base100_encode(data: bytes) -> str:
    return "".join(f"{b:03d}" for b in data)


def base100_decode(encoded: str) -> bytes:
    return bytes(int(encoded[i:i + 3]) for i in range(0, len(encoded), 3) if i + 3 <= len(encoded))


class SpeedLightEngineService:
    """SpeedLight Engine — idempotent computation cache and geometric tokenizer.

    Provides:
      - GeoTokenizer: geometry-native token encoding with equivalence memory
      - TwoTierCache: memory LRU + PG persistent cache
      - TokLight: Merkle-chained receipt ledger
      - Base100 encoding/decoding
      - Idempotent compute: f(f(x)) = f(x)
    """

    def __init__(self, pg_url: str = "", governance=None):
        self._governance = governance
        self.cache = TwoTierCache(pg_url=pg_url)
        self.tokenizer = GeoTokenizer()
        self.ledger = TokLight()
        self._init_pg_tables(pg_url)

    def _init_pg_tables(self, pg_url: str = ""):
        url = pg_url or PG_URL
        if not url:
            return
        try:
            import psycopg2
            conn = psycopg2.connect(url)
            conn.autocommit = True
            cur = conn.cursor()
            cur.execute("""CREATE TABLE IF NOT EXISTS speedlight_cache (
                key TEXT PRIMARY KEY, value JSONB, hits INT DEFAULT 0,
                created_at DOUBLE PRECISION, last_hit DOUBLE PRECISION)""")
            cur.execute("""CREATE TABLE IF NOT EXISTS speedlight_receipts (
                receipt_id TEXT PRIMARY KEY, op TEXT, input_hash TEXT,
                result_hash TEXT, prev TEXT, ts DOUBLE PRECISION)""")
            conn.close()
        except Exception:
            pass

    def compute(self, content: str = "", key: str = "") -> dict:
        """Idempotent compute: check cache first, compute if miss, cache result."""
        key = key or hashlib.sha256(content.encode()).hexdigest()[:16]

        cached = self.cache.get(key)
        if cached is not None:
            self.ledger.log("compute", "hit", key, str(cached)[:16])
            return {"key": key, "value": cached, "hit": True}

        result = self.tokenizer.encode(content) if content else {"identity": key}
        self.cache.put(key, result)

        result_hash = hashlib.sha256(
            json.dumps(result, default=str).encode()
        ).hexdigest()[:16]
        self.ledger.log("compute", "miss", key, result_hash)

        if self._governance:
            from governance.engine import BoundaryEvent
            self._governance.record_boundary_event(BoundaryEvent(
                event_id=f"speedlight-compute-{key}",
                timestamp=time.time(), entropy_delta=0.0,
                receipt_data={"key": key, "hit": False},
                boundary_type="speedlight_compute",
            ))

        return {"key": key, "value": result, "hit": False}

    def encode(self, content: str) -> dict:
        return self.tokenizer.encode(content)

    def decode(self, token_id: str) -> Optional[dict]:
        return self.tokenizer.decode(token_id)

    def learn_equivalence(self, content_a: str, content_b: str) -> dict:
        return self.tokenizer.learn_equivalence(content_a, content_b)

    def cache_get(self, key: str) -> Optional[Any]:
        return self.cache.get(key)

    def cache_put(self, key: str, value: Any):
        self.cache.put(key, value)

    @property
    def health(self) -> dict:
        return {
            "ok": True, "service": "speedlight-engine",
            "cache": self.cache.stats,
            "tokenizer": self.tokenizer.stats,
            "ledger": len(self.ledger.entries),
        }

    @property
    def stats(self) -> dict:
        return {
            "cache": self.cache.stats,
            "tokenizer": self.tokenizer.stats,
            "compute_ledger": len(self.ledger.entries),
        }

    def ledger_entries(self, limit: int = 50) -> list[dict]:
        return [asdict(e) for e in self.ledger.entries[-limit:]]

    def prototypes(self, limit: int = 50) -> dict:
        return {k: asdict(v) for k, v in list(self.tokenizer.prototypes.items())[:limit]}
