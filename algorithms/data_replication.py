"""
Algorithm 95: Data Replication

- Master → replicas
- Fast sync
- Conflict resolution
- Failover support
- Consistency checks
"""

import time
import hashlib
import json
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict


class ReplicationMode(Enum):
    SYNC = "synchronous"
    ASYNC = "asynchronous"
    SEMI_SYNC = "semi_synchronous"


class NodeRole(Enum):
    MASTER = "master"
    REPLICA = "replica"
    CANDIDATE = "candidate"


@dataclass
class ReplicationEvent:
    """A replication event in the write-ahead log."""
    sequence_id: int
    operation: str
    key: str
    value: object
    timestamp: float = field(default_factory=time.time)
    checksum: str = ""


@dataclass
class NodeStatus:
    """Status of a replication node."""
    node_id: str
    role: NodeRole
    healthy: bool = True
    last_sequence: int = 0
    lag: int = 0
    last_heartbeat: float = field(default_factory=time.time)


class ReplicationNode:
    """A node in the replication cluster."""

    def __init__(self, node_id, role=NodeRole.REPLICA):
        self.node_id = node_id
        self.role = role
        self.data = {}
        self.wal = []  # Write-ahead log
        self.sequence = 0
        self.healthy = True
        self.last_heartbeat = time.time()

    def write(self, key, value):
        """Write data (only on master)."""
        self.sequence += 1
        event = ReplicationEvent(
            sequence_id=self.sequence,
            operation="write",
            key=key,
            value=value,
            checksum=self._checksum(key, value),
        )
        self.wal.append(event)
        self.data[key] = value
        return event

    def apply_event(self, event):
        """Apply a replication event from master."""
        expected_checksum = self._checksum(event.key, event.value)
        if event.checksum and event.checksum != expected_checksum:
            raise ValueError(f"Checksum mismatch for key={event.key}")

        if event.operation == "write":
            self.data[event.key] = event.value
        elif event.operation == "delete":
            self.data.pop(event.key, None)

        self.sequence = event.sequence_id
        self.wal.append(event)

    def get(self, key):
        return self.data.get(key)

    def get_events_since(self, sequence_id):
        """Get all events since a given sequence ID."""
        return [e for e in self.wal if e.sequence_id > sequence_id]

    @staticmethod
    def _checksum(key, value):
        data = json.dumps({"key": key, "value": value}, sort_keys=True)
        return hashlib.md5(data.encode()).hexdigest()

    def get_status(self):
        return NodeStatus(
            node_id=self.node_id,
            role=self.role,
            healthy=self.healthy,
            last_sequence=self.sequence,
            last_heartbeat=self.last_heartbeat,
        )


class ReplicationCluster:
    """Master-replica replication cluster."""

    def __init__(self, mode=ReplicationMode.SEMI_SYNC, min_sync_replicas=1):
        self.mode = mode
        self.min_sync_replicas = min_sync_replicas
        self.master = None
        self.replicas = []
        self.all_nodes = {}

    def add_master(self, node_id):
        """Add the master node."""
        node = ReplicationNode(node_id, NodeRole.MASTER)
        self.master = node
        self.all_nodes[node_id] = node
        return node

    def add_replica(self, node_id):
        """Add a replica node."""
        node = ReplicationNode(node_id, NodeRole.REPLICA)
        self.replicas.append(node)
        self.all_nodes[node_id] = node
        return node

    def write(self, key, value):
        """Write to master and replicate."""
        if self.master is None or not self.master.healthy:
            raise RuntimeError("No healthy master available")

        event = self.master.write(key, value)
        success_count = self._replicate(event)

        if self.mode == ReplicationMode.SYNC:
            if success_count < len(self.replicas):
                raise RuntimeError("Sync replication failed")
        elif self.mode == ReplicationMode.SEMI_SYNC:
            if success_count < self.min_sync_replicas:
                raise RuntimeError("Semi-sync replication failed")

        return event

    def _replicate(self, event):
        """Replicate an event to all replicas."""
        success_count = 0
        for replica in self.replicas:
            if not replica.healthy:
                continue
            try:
                replica.apply_event(event)
                success_count += 1
            except Exception:
                pass
        return success_count

    def read(self, key, from_master=False):
        """Read data, optionally from master for strong consistency."""
        if from_master or not self.replicas:
            return self.master.get(key) if self.master else None

        # Read from a healthy replica
        for replica in self.replicas:
            if replica.healthy:
                return replica.get(key)

        return self.master.get(key) if self.master else None

    def failover(self):
        """Promote a replica to master when master fails."""
        if self.master and self.master.healthy:
            return None

        # Select replica with highest sequence (most up-to-date)
        candidates = [r for r in self.replicas if r.healthy]
        if not candidates:
            raise RuntimeError("No healthy replicas for failover")

        best = max(candidates, key=lambda r: r.sequence)

        # Promote
        old_master = self.master
        if old_master:
            old_master.role = NodeRole.REPLICA
            self.replicas.append(old_master)

        best.role = NodeRole.MASTER
        self.replicas.remove(best)
        self.master = best

        return best

    def sync_replica(self, replica_id):
        """Fast sync a lagging replica with master."""
        replica = self.all_nodes.get(replica_id)
        if not replica or not self.master:
            return 0

        events = self.master.get_events_since(replica.sequence)
        applied = 0
        for event in events:
            try:
                replica.apply_event(event)
                applied += 1
            except Exception:
                break
        return applied

    def consistency_check(self):
        """Check data consistency across nodes."""
        if not self.master:
            return {"consistent": False, "reason": "No master"}

        issues = []
        for replica in self.replicas:
            if not replica.healthy:
                continue

            lag = self.master.sequence - replica.sequence
            if lag > 0:
                issues.append({
                    "node": replica.node_id,
                    "lag": lag,
                    "master_seq": self.master.sequence,
                    "replica_seq": replica.sequence,
                })

            # Spot-check data consistency
            for key in list(self.master.data.keys())[:10]:
                master_val = self.master.get(key)
                replica_val = replica.get(key)
                if master_val != replica_val:
                    issues.append({
                        "node": replica.node_id,
                        "key": key,
                        "issue": "data_mismatch",
                    })

        return {
            "consistent": len(issues) == 0,
            "issues": issues,
        }


if __name__ == "__main__":
    cluster = ReplicationCluster(
        mode=ReplicationMode.SEMI_SYNC,
        min_sync_replicas=1,
    )

    cluster.add_master("master-0")
    cluster.add_replica("replica-1")
    cluster.add_replica("replica-2")

    # Write data
    for i in range(10):
        cluster.write(f"key-{i}", f"value-{i}")

    print(f"Master sequence: {cluster.master.sequence}")
    print(f"Read from replica: {cluster.read('key-5')}")

    # Consistency check
    check = cluster.consistency_check()
    print(f"Consistent: {check['consistent']}")

    # Simulate master failure and failover
    cluster.master.healthy = False
    print("\nMaster failed! Initiating failover...")
    new_master = cluster.failover()
    print(f"New master: {new_master.node_id}")
    print(f"Read after failover: {cluster.read('key-5')}")
