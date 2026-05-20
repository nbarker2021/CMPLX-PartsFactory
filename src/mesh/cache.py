import os
import time
import json
import threading
from typing import Any

try:
    import redis as _redis
    HAS_REDIS = True
except ImportError:
    HAS_REDIS = False

REDIS_URL = os.environ.get("REDIS_URL", "redis://host.docker.internal:6379/0")


class MeshCache:
    def __init__(self, speedlight_client=None):
        self._l1: dict[str, tuple[Any, float]] = {}
        self._l1_max = 1000
        self._l1_ttl = 30
        self._lock = threading.Lock()

        self._redis: Any = None
        if HAS_REDIS:
            try:
                self._redis = _redis.from_url(REDIS_URL, decode_responses=True, socket_timeout=2)
                self._redis.ping()
            except Exception:
                self._redis = None

        self._speedlight = speedlight_client

    def get(self, key: str, default: Any = None) -> Any:
        value = self._get_l1(key)
        if value is not None:
            return value

        value = self._get_redis(key)
        if value is not None:
            self._set_l1(key, value)
            return value

        value = self._get_speedlight(key)
        if value is not None:
            self._set_l1(key, value)
            self._set_redis(key, value)
            return value

        return default

    def set(self, key: str, value: Any, ttl: int = 3600):
        self._set_l1(key, value)
        self._set_redis(key, value, ttl)
        self._set_speedlight(key, value, ttl)

    def delete(self, key: str):
        with self._lock:
            self._l1.pop(key, None)
        if self._redis:
            try:
                self._redis.delete(key)
            except Exception:
                pass
        if self._speedlight:
            try:
                speedlight_key = f"mesh:{key}"
                self._speedlight.get(speedlight_key)
            except Exception:
                pass

    def invalidate_pattern(self, pattern: str):
        with self._lock:
            self._l1 = {k: v for k, v in self._l1.items() if pattern not in k}
        if self._redis:
            try:
                cursor = 0
                while True:
                    cursor, keys = self._redis.scan(cursor, match=pattern, count=100)
                    if keys:
                        self._redis.delete(*keys)
                    if cursor == 0:
                        break
            except Exception:
                pass

    def _get_l1(self, key: str) -> Any | None:
        with self._lock:
            entry = self._l1.get(key)
        if entry is None:
            return None
        value, expires = entry
        if expires < time.time():
            with self._lock:
                self._l1.pop(key, None)
            return None
        return value

    def _set_l1(self, key: str, value: Any):
        with self._lock:
            if len(self._l1) >= self._l1_max:
                oldest = min(self._l1.keys(), key=lambda k: self._l1[k][1])
                self._l1.pop(oldest, None)
            self._l1[key] = (value, time.time() + self._l1_ttl)

    def _get_redis(self, key: str) -> Any | None:
        if not self._redis:
            return None
        try:
            val = self._redis.get(key)
            if val is not None:
                return json.loads(val)
        except Exception:
            pass
        return None

    def _set_redis(self, key: str, value: Any, ttl: int = 3600):
        if not self._redis:
            return
        try:
            self._redis.setex(key, min(ttl, 86400), json.dumps(value))
        except Exception:
            pass

    def _get_speedlight(self, key: str) -> Any | None:
        if not self._speedlight:
            return None
        try:
            sk = f"mesh:{key}"
            return self._speedlight.get(sk)
        except Exception:
            return None

    def _set_speedlight(self, key: str, value: Any, ttl: int = 3600):
        if not self._speedlight:
            return
        try:
            sk = f"mesh:{key}"
            self._speedlight.put(sk, value, ttl)
        except Exception:
            pass

    def stats(self) -> dict:
        with self._lock:
            return {
                "l1_size": len(self._l1),
                "l1_max": self._l1_max,
                "redis_available": self._redis is not None,
                "speedlight_available": self._speedlight is not None,
            }
