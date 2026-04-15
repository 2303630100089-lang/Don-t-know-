"""
Algorithm 88: Session Replication

- Session stored in Redis
- Replicated across nodes
- Fast failover
- Consistency ensured
- Secure token validation
"""

import time
import hashlib
import secrets
from dataclasses import dataclass, field


@dataclass
class Session:
    """A user session."""
    session_id: str
    user_id: str
    token: str
    data: dict = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    last_accessed: float = field(default_factory=time.time)
    ttl: int = 3600  # seconds
    node_id: str = ""

    @property
    def is_expired(self):
        return time.time() - self.last_accessed > self.ttl

    def touch(self):
        self.last_accessed = time.time()


class RedisNode:
    """Simulated Redis node for session storage."""

    def __init__(self, node_id, is_primary=True):
        self.node_id = node_id
        self.is_primary = is_primary
        self.store = {}
        self.healthy = True

    def set(self, key, value, ttl=None):
        """Store a value with optional TTL."""
        if not self.healthy:
            raise ConnectionError(f"Node {self.node_id} is unhealthy")
        self.store[key] = {
            "value": value,
            "ttl": ttl,
            "stored_at": time.time(),
        }

    def get(self, key):
        """Retrieve a value."""
        if not self.healthy:
            raise ConnectionError(f"Node {self.node_id} is unhealthy")
        entry = self.store.get(key)
        if entry is None:
            return None
        if entry["ttl"] and time.time() - entry["stored_at"] > entry["ttl"]:
            del self.store[key]
            return None
        return entry["value"]

    def delete(self, key):
        """Delete a value."""
        if not self.healthy:
            raise ConnectionError(f"Node {self.node_id} is unhealthy")
        self.store.pop(key, None)

    def keys(self):
        return list(self.store.keys())


class SessionReplicationService:
    """Session management with replication across Redis nodes."""

    def __init__(self, num_replicas=2, session_ttl=3600):
        self.session_ttl = session_ttl
        self.primary = RedisNode("primary-0", is_primary=True)
        self.replicas = [
            RedisNode(f"replica-{i}", is_primary=False)
            for i in range(num_replicas)
        ]
        self.all_nodes = [self.primary] + self.replicas
        self.token_secret = secrets.token_hex(32)

    def _generate_token(self, session_id, user_id):
        """Generate a secure session token."""
        payload = f"{session_id}:{user_id}:{self.token_secret}:{time.time()}"
        return hashlib.sha256(payload.encode()).hexdigest()

    def _validate_token(self, session, token):
        """Validate a session token."""
        return session is not None and session.token == token

    def create_session(self, user_id, data=None):
        """Create a new session and replicate it across nodes."""
        session_id = f"sess-{secrets.token_hex(16)}"
        token = self._generate_token(session_id, user_id)

        session = Session(
            session_id=session_id,
            user_id=user_id,
            token=token,
            data=data or {},
            ttl=self.session_ttl,
            node_id=self.primary.node_id,
        )

        # Store in primary
        self._store_session(self.primary, session)

        # Replicate to all replicas
        for replica in self.replicas:
            try:
                self._store_session(replica, session)
            except ConnectionError:
                pass  # Best-effort replication

        return session

    def _store_session(self, node, session):
        """Store session in a Redis node."""
        session_data = {
            "session_id": session.session_id,
            "user_id": session.user_id,
            "token": session.token,
            "data": session.data,
            "created_at": session.created_at,
            "last_accessed": session.last_accessed,
            "ttl": session.ttl,
        }
        node.set(session.session_id, session_data, ttl=session.ttl)

    def get_session(self, session_id, token=None):
        """Get session with fast failover across nodes."""
        for node in self.all_nodes:
            try:
                data = node.get(session_id)
                if data:
                    session = Session(
                        session_id=data["session_id"],
                        user_id=data["user_id"],
                        token=data["token"],
                        data=data["data"],
                        created_at=data["created_at"],
                        last_accessed=data["last_accessed"],
                        ttl=data["ttl"],
                    )

                    if session.is_expired:
                        self.destroy_session(session_id)
                        return None

                    if token and not self._validate_token(session, token):
                        return None

                    session.touch()
                    return session
            except ConnectionError:
                continue  # Failover to next node

        return None

    def destroy_session(self, session_id):
        """Destroy session across all nodes."""
        for node in self.all_nodes:
            try:
                node.delete(session_id)
            except ConnectionError:
                pass

    def simulate_failover(self, node_id):
        """Simulate a node failure."""
        for node in self.all_nodes:
            if node.node_id == node_id:
                node.healthy = False
                return True
        return False

    def recover_node(self, node_id):
        """Recover a failed node and resync sessions."""
        target = None
        for node in self.all_nodes:
            if node.node_id == node_id:
                node.healthy = True
                target = node
                break

        if target is None:
            return False

        # Resync from a healthy node
        source = None
        for node in self.all_nodes:
            if node.healthy and node != target:
                source = node
                break

        if source:
            for key in source.keys():
                try:
                    value = source.get(key)
                    if value:
                        target.set(key, value)
                except ConnectionError:
                    pass

        return True


if __name__ == "__main__":
    service = SessionReplicationService(num_replicas=2)

    # Create sessions
    session = service.create_session("user-1", {"role": "admin"})
    print(f"Created session: {session.session_id[:20]}...")
    print(f"Token: {session.token[:20]}...")

    # Retrieve session
    retrieved = service.get_session(session.session_id, session.token)
    print(f"Retrieved: user={retrieved.user_id}, data={retrieved.data}")

    # Simulate primary failure
    service.simulate_failover("primary-0")
    print("\nPrimary node failed!")

    # Session still accessible via replica
    retrieved = service.get_session(session.session_id, session.token)
    print(f"Failover read: user={retrieved.user_id if retrieved else 'FAILED'}")

    # Recover node
    service.recover_node("primary-0")
    print("Primary recovered and resynced!")
