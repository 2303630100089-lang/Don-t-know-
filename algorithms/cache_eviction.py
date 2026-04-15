"""
Algorithm 94: Cache Eviction

- LRU policy
- Fast eviction
- TTL expiration
- Distributed consistency
- Cache warm-up
"""

import time
import threading
from collections import OrderedDict
from dataclasses import dataclass, field


@dataclass
class CacheEntry:
    """A single cache entry with metadata."""
    key: str
    value: object
    created_at: float = field(default_factory=time.time)
    last_accessed: float = field(default_factory=time.time)
    ttl: float = 0  # 0 means no expiration
    access_count: int = 0
    size_bytes: int = 0


class LRUCache:
    """LRU cache with TTL expiration support."""

    def __init__(self, max_size=1000, default_ttl=300):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.cache = OrderedDict()
        self.lock = threading.Lock()
        self.stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0,
            "expirations": 0,
        }

    def get(self, key):
        """Get a value from cache (LRU update)."""
        with self.lock:
            if key not in self.cache:
                self.stats["misses"] += 1
                return None

            entry = self.cache[key]

            # Check TTL
            if entry.ttl > 0 and time.time() - entry.created_at > entry.ttl:
                del self.cache[key]
                self.stats["expirations"] += 1
                self.stats["misses"] += 1
                return None

            # LRU: move to end
            self.cache.move_to_end(key)
            entry.last_accessed = time.time()
            entry.access_count += 1
            self.stats["hits"] += 1
            return entry.value

    def put(self, key, value, ttl=None):
        """Put a value in cache with optional TTL."""
        with self.lock:
            if key in self.cache:
                self.cache.move_to_end(key)
                entry = self.cache[key]
                entry.value = value
                entry.last_accessed = time.time()
                entry.ttl = ttl if ttl is not None else self.default_ttl
                return

            # Evict if at capacity
            while len(self.cache) >= self.max_size:
                evicted_key, _ = self.cache.popitem(last=False)
                self.stats["evictions"] += 1

            entry = CacheEntry(
                key=key,
                value=value,
                ttl=ttl if ttl is not None else self.default_ttl,
            )
            self.cache[key] = entry

    def delete(self, key):
        """Delete a key from cache."""
        with self.lock:
            return self.cache.pop(key, None) is not None

    def clear(self):
        """Clear all cache entries."""
        with self.lock:
            self.cache.clear()

    def cleanup_expired(self):
        """Remove all expired entries."""
        with self.lock:
            now = time.time()
            expired_keys = [
                key for key, entry in self.cache.items()
                if entry.ttl > 0 and now - entry.created_at > entry.ttl
            ]
            for key in expired_keys:
                del self.cache[key]
                self.stats["expirations"] += 1
            return len(expired_keys)

    @property
    def size(self):
        return len(self.cache)

    @property
    def hit_ratio(self):
        total = self.stats["hits"] + self.stats["misses"]
        return self.stats["hits"] / total if total > 0 else 0.0


class DistributedCacheNode:
    """A node in a distributed cache system."""

    def __init__(self, node_id, max_size=1000, default_ttl=300):
        self.node_id = node_id
        self.cache = LRUCache(max_size, default_ttl)
        self.version_map = {}  # key -> version for consistency

    def get(self, key):
        return self.cache.get(key)

    def put(self, key, value, version=None, ttl=None):
        if version is not None:
            current_version = self.version_map.get(key, 0)
            if version < current_version:
                return False  # Stale update
            self.version_map[key] = version

        self.cache.put(key, value, ttl)
        return True

    def invalidate(self, key):
        return self.cache.delete(key)


class DistributedCache:
    """Distributed cache with consistency and warm-up support."""

    def __init__(self, num_nodes=3, max_size_per_node=1000, default_ttl=300):
        self.nodes = [
            DistributedCacheNode(f"node-{i}", max_size_per_node, default_ttl)
            for i in range(num_nodes)
        ]
        self.version_counter = 0

    def _get_node(self, key):
        """Simple hash-based node selection."""
        return self.nodes[hash(key) % len(self.nodes)]

    def get(self, key):
        """Get from the responsible node."""
        node = self._get_node(key)
        return node.get(key)

    def put(self, key, value, ttl=None):
        """Put with version-based consistency."""
        self.version_counter += 1
        version = self.version_counter

        # Write to primary node
        primary = self._get_node(key)
        primary.put(key, value, version, ttl)

        # Replicate to other nodes for consistency
        for node in self.nodes:
            if node != primary:
                node.put(key, value, version, ttl)

    def invalidate(self, key):
        """Invalidate across all nodes."""
        for node in self.nodes:
            node.invalidate(key)

    def warm_up(self, data_source):
        """Pre-populate cache from a data source."""
        count = 0
        for key, value in data_source.items():
            self.put(key, value)
            count += 1
        return count

    def get_stats(self):
        """Get aggregated stats."""
        total_hits = sum(n.cache.stats["hits"] for n in self.nodes)
        total_misses = sum(n.cache.stats["misses"] for n in self.nodes)
        total_evictions = sum(n.cache.stats["evictions"] for n in self.nodes)

        return {
            "total_hits": total_hits,
            "total_misses": total_misses,
            "total_evictions": total_evictions,
            "overall_hit_ratio": total_hits / (total_hits + total_misses)
            if (total_hits + total_misses) > 0 else 0,
            "nodes": {
                n.node_id: {
                    "size": n.cache.size,
                    "hit_ratio": n.cache.hit_ratio,
                }
                for n in self.nodes
            },
        }


if __name__ == "__main__":
    # Single-node LRU cache
    cache = LRUCache(max_size=5, default_ttl=60)

    for i in range(8):
        cache.put(f"key-{i}", f"value-{i}")

    print(f"Cache size: {cache.size} (max=5)")
    print(f"Evictions: {cache.stats['evictions']}")

    # Access pattern
    for i in range(8):
        result = cache.get(f"key-{i}")
        status = "HIT" if result else "MISS"
        print(f"  key-{i}: {status}")

    print(f"Hit ratio: {cache.hit_ratio:.1%}")

    # Distributed cache with warm-up
    dist_cache = DistributedCache(num_nodes=3)

    warmup_data = {f"item-{i}": {"data": f"value-{i}"} for i in range(100)}
    warmed = dist_cache.warm_up(warmup_data)
    print(f"\nWarmed up {warmed} entries")

    # Access patterns
    for i in range(100):
        dist_cache.get(f"item-{i}")

    stats = dist_cache.get_stats()
    print(f"Distributed hit ratio: {stats['overall_hit_ratio']:.1%}")
