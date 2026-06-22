"""Caching layer for oracle computations."""
import hashlib
import json
import time


class OracleCache:
    def __init__(self, ttl: float = 3600.0, max_size: int = 1000):
        self.cache = {}
        self.ttl = ttl
        self.max_size = max_size
        self.hits = 0
        self.misses = 0

    def _make_key(self, chromosome_id: str, entropy_packet: dict) -> str:
        ep_str = json.dumps(entropy_packet, sort_keys=True, default=str)
        return f"{chromosome_id}:{hashlib.md5(ep_str.encode()).hexdigest()}"

    def get(self, chromosome_id: str, entropy_packet: dict) -> dict | None:
        key = self._make_key(chromosome_id, entropy_packet)
        if key in self.cache:
            entry = self.cache[key]
            if time.time() - entry["timestamp"] < self.ttl:
                self.hits += 1
                return entry["result"]
            else:
                del self.cache[key]
        self.misses += 1
        return None

    def set(self, chromosome_id: str, entropy_packet: dict, result: dict):
        if len(self.cache) >= self.max_size:
            oldest_key = min(self.cache.keys(), key=lambda k: self.cache[k]["timestamp"])
            del self.cache[oldest_key]

        key = self._make_key(chromosome_id, entropy_packet)
        self.cache[key] = {"result": result, "timestamp": time.time()}

    def clear(self):
        self.cache.clear()

    def get_stats(self) -> dict:
        total = self.hits + self.misses
        return {
            "size": len(self.cache),
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": self.hits / total if total > 0 else 0,
        }
