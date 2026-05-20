"""
Escrow merge (2026-05-19T00:00:31Z).
Source: ``CMPLX-history/staging/by-family/unclassified/partsfactory/speedlight_sidecar_plus_v2.py``
Slot: ``slot-04-speedlight-worldline``
"""
# speedlight_sidecar_plus.py
import time, json, os, hashlib
from pathlib import Path
from collections import deque

class SpeedLightV2:
    """
    Stdlib-only sidecar: memory LRU cache + disk cache + JSONL ledger.
    - compute(payload, scope, channel, compute_fn): memoizes by hash(payload,scope,channel)
    - stats(): hits/misses and last elapsed
    """
    def __init__(self, mem_bytes=128*1024*1024, disk_dir='./.reality_craft/cache', ledger_path='./.reality_craft/ledger.jsonl'):
        self.mem_limit = mem_bytes
        self.mem_used = 0
        self.mem = {}          # key -> (size, value)
        self.order = deque()   # LRU ordering
        self.disk_dir = Path(disk_dir); self.disk_dir.mkdir(parents=True, exist_ok=True)
        self.ledger_path = Path(ledger_path); self.ledger_path.parent.mkdir(parents=True, exist_ok=True)
        self._hits = 0; self._misses = 0; self._elapsed = 0.0

    def _key(self, payload, scope, channel):
        m = hashlib.sha256()
        m.update(json.dumps(payload, sort_keys=True, default=str).encode())
        m.update(str(scope).encode()); m.update(str(channel).encode())
        return m.hexdigest()

    def _disk_path(self, key): return self.disk_dir / f"{key}.json"

    def stats(self):
        return {"hits": self._hits, "misses": self._misses, "elapsed_s": round(self._elapsed, 6)}

    def _evict(self):
        while self.mem_used > self.mem_limit and self.order:
            k = self.order.popleft()
            size, _ = self.mem.pop(k, (0, None))
            self.mem_used = max(0, self.mem_used - size)

    def _remember(self, k, v):
        s = len(json.dumps(v, default=str).encode())
        self.mem[k] = (s, v); self.order.append(k); self.mem_used += s; self._evict()

    def _read_disk(self, k):
        p = self._disk_path(k)
        if p.exists():
            try:
                return json.loads(p.read_text(encoding='utf-8'))
            except Exception:
                return None
        return None

    def _write_disk(self, k, v):
        p = self._disk_path(k); 
        try:
            p.write_text(json.dumps(v, ensure_ascii=False), encoding='utf-8')
        except Exception:
            pass

    def _log(self, rec):
        try:
            with open(self.ledger_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        except Exception:
            pass

    def compute(self, payload, scope="default", channel=0, compute_fn=lambda: None):
        k = self._key(payload, scope, channel)
        t0 = time.time()

        # mem cache
        if k in self.mem:
            self._hits += 1
            _, v = self.mem[k]
            self._elapsed = time.time() - t0
            self._log({"ts": time.time(), "key": k, "where": "mem", "scope": scope, "channel": channel, "hits": self._hits, "misses": self._misses})
            return v

        # disk cache
        v = self._read_disk(k)
        if v is not None:
            self._hits += 1
            self._remember(k, v)
            self._elapsed = time.time() - t0
            self._log({"ts": time.time(), "key": k, "where": "disk", "scope": scope, "channel": channel, "hits": self._hits, "misses": self._misses})
            return v

        # compute
        self._misses += 1
        v = compute_fn()
        self._remember(k, v)
        self._write_disk(k, v)
        self._elapsed = time.time() - t0
        self._log({"ts": time.time(), "key": k, "where": "compute", "scope": scope, "channel": channel, "hits": self._hits, "misses": self._misses})
        return v
