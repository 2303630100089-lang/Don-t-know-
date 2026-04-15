"""
Algorithm 85: Database Sharding

- Data partitioned by user ID
- Shard lookup via router
- Fast query routing
- Load balanced
- Replication for fault tolerance
"""

import hashlib
import time
from dataclasses import dataclass, field
from collections import defaultdict


@dataclass
class Shard:
    """A database shard."""
    shard_id: int
    data: dict = field(default_factory=dict)
    replicas: list = field(default_factory=list)
    load: int = 0

    def put(self, key, value):
        self.data[key] = value
        self.load += 1

    def get(self, key):
        return self.data.get(key)

    def delete(self, key):
        if key in self.data:
            del self.data[key]
            self.load = max(0, self.load - 1)

    def size(self):
        return len(self.data)


@dataclass
class ReplicaShard(Shard):
    """A replica of a primary shard for fault tolerance."""
    primary_shard_id: int = 0
    is_replica: bool = True


class ConsistentHashRouter:
    """Route queries to shards using consistent hashing."""

    def __init__(self, num_shards, virtual_nodes=150):
        self.num_shards = num_shards
        self.virtual_nodes = virtual_nodes
        self.ring = {}
        self.sorted_keys = []
        self._build_ring()

    def _build_ring(self):
        """Build consistent hash ring."""
        for shard_id in range(self.num_shards):
            for vn in range(self.virtual_nodes):
                key = f"shard-{shard_id}-vn-{vn}"
                hash_val = self._hash(key)
                self.ring[hash_val] = shard_id
                self.sorted_keys.append(hash_val)
        self.sorted_keys.sort()

    @staticmethod
    def _hash(key):
        return int(hashlib.sha256(str(key).encode()).hexdigest(), 16)

    def get_shard(self, user_id):
        """Get shard ID for a given user ID."""
        hash_val = self._hash(user_id)

        for ring_key in self.sorted_keys:
            if hash_val <= ring_key:
                return self.ring[ring_key]

        return self.ring[self.sorted_keys[0]]


class LoadBalancer:
    """Balance load across shards."""

    def __init__(self, shards):
        self.shards = shards

    def get_loads(self):
        """Get load distribution across shards."""
        return {s.shard_id: s.load for s in self.shards.values()}

    def is_balanced(self, threshold=0.3):
        """Check if load is balanced within threshold."""
        loads = list(self.get_loads().values())
        if not loads:
            return True
        avg = sum(loads) / len(loads)
        if avg == 0:
            return True
        max_deviation = max(abs(l - avg) for l in loads)
        return max_deviation / avg <= threshold

    def get_least_loaded(self):
        """Get the least loaded shard."""
        return min(self.shards.values(), key=lambda s: s.load)


class ShardedDatabase:
    """Database with sharding, routing, load balancing, and replication."""

    def __init__(self, num_shards=4, replication_factor=2):
        self.num_shards = num_shards
        self.replication_factor = replication_factor
        self.router = ConsistentHashRouter(num_shards)
        self.shards = {}
        self.replicas = defaultdict(list)
        self._init_shards()
        self.load_balancer = LoadBalancer(self.shards)
        self.query_log = []

    def _init_shards(self):
        """Initialize shards and their replicas."""
        for i in range(self.num_shards):
            self.shards[i] = Shard(shard_id=i)

            for r in range(self.replication_factor):
                replica = ReplicaShard(
                    shard_id=self.num_shards + i * self.replication_factor + r,
                    primary_shard_id=i,
                )
                self.replicas[i].append(replica)

    def put(self, user_id, key, value):
        """Store data in the appropriate shard."""
        shard_id = self.router.get_shard(user_id)
        shard = self.shards[shard_id]
        composite_key = f"{user_id}:{key}"

        shard.put(composite_key, value)

        for replica in self.replicas[shard_id]:
            replica.put(composite_key, value)

        self._log_query("put", user_id, shard_id)
        return shard_id

    def get(self, user_id, key):
        """Retrieve data from the appropriate shard."""
        shard_id = self.router.get_shard(user_id)
        shard = self.shards[shard_id]
        composite_key = f"{user_id}:{key}"

        result = shard.get(composite_key)

        if result is None:
            for replica in self.replicas[shard_id]:
                result = replica.get(composite_key)
                if result is not None:
                    break

        self._log_query("get", user_id, shard_id)
        return result

    def delete(self, user_id, key):
        """Delete data from shard and replicas."""
        shard_id = self.router.get_shard(user_id)
        composite_key = f"{user_id}:{key}"

        self.shards[shard_id].delete(composite_key)
        for replica in self.replicas[shard_id]:
            replica.delete(composite_key)

        self._log_query("delete", user_id, shard_id)

    def _log_query(self, operation, user_id, shard_id):
        self.query_log.append({
            "operation": operation,
            "user_id": user_id,
            "shard_id": shard_id,
            "timestamp": time.time(),
        })

    def get_stats(self):
        """Get shard statistics."""
        stats = {}
        for shard_id, shard in self.shards.items():
            stats[shard_id] = {
                "size": shard.size(),
                "load": shard.load,
                "replicas": len(self.replicas[shard_id]),
            }
        return stats


if __name__ == "__main__":
    db = ShardedDatabase(num_shards=4, replication_factor=2)

    users = [f"user_{i}" for i in range(20)]
    for user in users:
        db.put(user, "profile", {"name": user, "active": True})
        db.put(user, "settings", {"theme": "dark"})

    print("Shard distribution:")
    for shard_id, stats in db.get_stats().items():
        print(f"  Shard {shard_id}: {stats['size']} keys, load={stats['load']}, "
              f"replicas={stats['replicas']}")

    print(f"\nLoad balanced: {db.load_balancer.is_balanced()}")

    profile = db.get("user_5", "profile")
    print(f"\nRetrieved user_5 profile: {profile}")
