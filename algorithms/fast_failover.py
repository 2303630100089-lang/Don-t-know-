"""
Algorithm 101: Fast Failover

- Node health check
- If failure → reroute
- Fast recovery
- Minimal downtime
- Logged event
"""

import time
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict


class NodeHealth(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    DEAD = "dead"


@dataclass
class ServiceNode:
    """A service node with health tracking."""
    node_id: str
    address: str
    health: NodeHealth = NodeHealth.HEALTHY
    last_check: float = field(default_factory=time.time)
    consecutive_failures: int = 0
    total_requests: int = 0
    failed_requests: int = 0
    response_time_ms: float = 0.0


@dataclass
class FailoverEvent:
    """A failover event record."""
    event_id: str
    from_node: str
    to_node: str
    reason: str
    timestamp: float = field(default_factory=time.time)
    recovery_time_ms: float = 0.0


class HealthChecker:
    """Check health of service nodes."""

    def __init__(self, failure_threshold=3, degraded_threshold=1,
                 check_interval=5.0):
        self.failure_threshold = failure_threshold
        self.degraded_threshold = degraded_threshold
        self.check_interval = check_interval

    def check(self, node, simulate_result=True):
        """Perform health check on a node."""
        node.last_check = time.time()

        if not simulate_result:
            node.consecutive_failures += 1
        else:
            node.consecutive_failures = 0

        if node.consecutive_failures >= self.failure_threshold:
            node.health = NodeHealth.DEAD
        elif node.consecutive_failures >= self.degraded_threshold:
            node.health = NodeHealth.UNHEALTHY
        elif node.response_time_ms > 1000:
            node.health = NodeHealth.DEGRADED
        else:
            node.health = NodeHealth.HEALTHY

        return node.health


class FailoverManager:
    """Manage fast failover between service nodes."""

    def __init__(self, health_checker=None):
        self.health_checker = health_checker or HealthChecker()
        self.nodes = {}
        self.primary = None
        self.event_log = []
        self._event_counter = 0

    def add_node(self, node):
        """Add a service node."""
        self.nodes[node.node_id] = node
        if self.primary is None:
            self.primary = node.node_id

    def remove_node(self, node_id):
        """Remove a service node."""
        self.nodes.pop(node_id, None)
        if self.primary == node_id:
            self._elect_new_primary()

    def route_request(self):
        """Route a request to the best available node."""
        if self.primary and self.primary in self.nodes:
            node = self.nodes[self.primary]
            if node.health in (NodeHealth.HEALTHY, NodeHealth.DEGRADED):
                node.total_requests += 1
                return node

        return self._failover()

    def _failover(self):
        """Perform fast failover to a healthy node."""
        start = time.time()
        old_primary = self.primary

        new_primary = self._find_best_node()
        if new_primary is None:
            return None

        self.primary = new_primary.node_id
        recovery_time = (time.time() - start) * 1000

        self._event_counter += 1
        event = FailoverEvent(
            event_id=f"fo-{self._event_counter}",
            from_node=old_primary or "none",
            to_node=new_primary.node_id,
            reason=f"Primary {old_primary} unavailable",
            recovery_time_ms=recovery_time,
        )
        self.event_log.append(event)

        new_primary.total_requests += 1
        return new_primary

    def _find_best_node(self):
        """Find the best available node for failover."""
        candidates = [
            node for node in self.nodes.values()
            if node.health in (NodeHealth.HEALTHY, NodeHealth.DEGRADED)
            and node.node_id != self.primary
        ]

        if not candidates:
            return None

        # Prefer healthy over degraded, then lowest response time
        candidates.sort(key=lambda n: (
            0 if n.health == NodeHealth.HEALTHY else 1,
            n.response_time_ms,
        ))

        return candidates[0]

    def _elect_new_primary(self):
        """Elect a new primary node."""
        best = self._find_best_node()
        self.primary = best.node_id if best else None

    def simulate_failure(self, node_id):
        """Simulate a node failure."""
        node = self.nodes.get(node_id)
        if node:
            node.health = NodeHealth.DEAD
            node.consecutive_failures = 10
            if self.primary == node_id:
                return self._failover()
        return None

    def recover_node(self, node_id):
        """Recover a failed node."""
        node = self.nodes.get(node_id)
        if node:
            node.health = NodeHealth.HEALTHY
            node.consecutive_failures = 0
            node.failed_requests = 0

    def get_stats(self):
        """Get failover statistics."""
        return {
            "primary": self.primary,
            "total_nodes": len(self.nodes),
            "healthy_nodes": sum(
                1 for n in self.nodes.values()
                if n.health == NodeHealth.HEALTHY
            ),
            "failover_count": len(self.event_log),
            "avg_recovery_ms": (
                sum(e.recovery_time_ms for e in self.event_log)
                / len(self.event_log) if self.event_log else 0
            ),
        }


if __name__ == "__main__":
    manager = FailoverManager()

    # Add nodes
    for i in range(4):
        manager.add_node(ServiceNode(
            node_id=f"node-{i}",
            address=f"10.0.0.{i+1}:8080",
            response_time_ms=10.0 + i * 5,
        ))

    print(f"Primary: {manager.primary}")

    # Route requests
    node = manager.route_request()
    print(f"Request routed to: {node.node_id}")

    # Simulate failure
    print("\nSimulating node-0 failure...")
    failover_node = manager.simulate_failure("node-0")
    if failover_node:
        print(f"Failover to: {failover_node.node_id}")

    # Continue routing
    node = manager.route_request()
    print(f"Next request routed to: {node.node_id}")

    # Recover
    manager.recover_node("node-0")
    print(f"\nRecovered node-0")

    stats = manager.get_stats()
    print(f"Stats: {stats}")
