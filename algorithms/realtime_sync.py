"""
Algorithm 81: Real-Time Sync

- Client → Sync service
- Service → DB + cache
- Fast delta updates
- Conflict resolution
- Event-driven notifications
"""

import time
import hashlib
import json
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict


class ConflictStrategy(Enum):
    LAST_WRITE_WINS = "last_write_wins"
    FIRST_WRITE_WINS = "first_write_wins"
    MERGE = "merge"


@dataclass
class SyncEvent:
    """A single sync event/change."""
    event_id: str
    client_id: str
    resource_id: str
    operation: str  # "create", "update", "delete"
    data: dict
    timestamp: float = field(default_factory=time.time)
    version: int = 0


@dataclass
class SyncState:
    """Current sync state for a resource."""
    resource_id: str
    data: dict
    version: int
    last_modified: float
    checksum: str


class Database:
    """Simulated database for sync storage."""

    def __init__(self):
        self.store = {}
        self.versions = defaultdict(int)

    def get(self, resource_id):
        return self.store.get(resource_id)

    def put(self, resource_id, data, version):
        self.store[resource_id] = {
            "data": data,
            "version": version,
            "timestamp": time.time(),
        }
        self.versions[resource_id] = version

    def delete(self, resource_id):
        self.store.pop(resource_id, None)
        self.versions.pop(resource_id, None)

    def get_version(self, resource_id):
        return self.versions.get(resource_id, 0)


class Cache:
    """In-memory cache for fast access."""

    def __init__(self, ttl=300):
        self.store = {}
        self.ttl = ttl

    def get(self, key):
        if key in self.store:
            entry = self.store[key]
            if time.time() - entry["timestamp"] < self.ttl:
                return entry["data"]
            del self.store[key]
        return None

    def put(self, key, data):
        self.store[key] = {"data": data, "timestamp": time.time()}

    def invalidate(self, key):
        self.store.pop(key, None)


class ConflictResolver:
    """Resolve sync conflicts between concurrent updates."""

    def __init__(self, strategy=ConflictStrategy.LAST_WRITE_WINS):
        self.strategy = strategy

    def resolve(self, local_event, remote_event):
        """Resolve conflict between local and remote events."""
        if self.strategy == ConflictStrategy.LAST_WRITE_WINS:
            if local_event.timestamp >= remote_event.timestamp:
                return local_event
            return remote_event

        elif self.strategy == ConflictStrategy.FIRST_WRITE_WINS:
            if local_event.timestamp <= remote_event.timestamp:
                return local_event
            return remote_event

        elif self.strategy == ConflictStrategy.MERGE:
            merged_data = {**remote_event.data, **local_event.data}
            return SyncEvent(
                event_id=f"merged-{local_event.event_id}",
                client_id="system",
                resource_id=local_event.resource_id,
                operation="update",
                data=merged_data,
                version=max(local_event.version, remote_event.version) + 1,
            )

        raise ValueError(f"Unknown strategy: {self.strategy}")


class SyncService:
    """Real-time sync service with delta updates and conflict resolution."""

    def __init__(self, conflict_strategy=ConflictStrategy.LAST_WRITE_WINS):
        self.db = Database()
        self.cache = Cache()
        self.conflict_resolver = ConflictResolver(conflict_strategy)
        self.event_log = []
        self.subscribers = defaultdict(list)  # resource_id -> [callbacks]
        self.pending_events = defaultdict(list)  # client_id -> [events]

    @staticmethod
    def _compute_checksum(data):
        return hashlib.md5(json.dumps(data, sort_keys=True).encode()).hexdigest()

    def sync(self, event):
        """Process a sync event from a client."""
        current_version = self.db.get_version(event.resource_id)

        if event.version > 0 and event.version != current_version:
            current_data = self.db.get(event.resource_id)
            if current_data:
                remote_event = SyncEvent(
                    event_id=f"remote-{event.resource_id}",
                    client_id="db",
                    resource_id=event.resource_id,
                    operation="update",
                    data=current_data["data"],
                    timestamp=current_data["timestamp"],
                    version=current_version,
                )
                event = self.conflict_resolver.resolve(event, remote_event)

        new_version = current_version + 1
        event.version = new_version

        if event.operation == "delete":
            self.db.delete(event.resource_id)
            self.cache.invalidate(event.resource_id)
        else:
            self.db.put(event.resource_id, event.data, new_version)
            self.cache.put(event.resource_id, event.data)

        self.event_log.append(event)
        self._notify_subscribers(event)

        return SyncState(
            resource_id=event.resource_id,
            data=event.data,
            version=new_version,
            last_modified=event.timestamp,
            checksum=self._compute_checksum(event.data),
        )

    def get_delta(self, resource_id, since_version):
        """Get delta updates since a given version."""
        deltas = []
        for event in self.event_log:
            if event.resource_id == resource_id and event.version > since_version:
                deltas.append(event)
        return deltas

    def subscribe(self, resource_id, callback):
        """Subscribe to changes on a resource."""
        self.subscribers[resource_id].append(callback)

    def _notify_subscribers(self, event):
        """Event-driven notification to subscribers."""
        for callback in self.subscribers.get(event.resource_id, []):
            callback(event)

    def get_state(self, resource_id):
        """Get current state of a resource (cache-first)."""
        cached = self.cache.get(resource_id)
        if cached is not None:
            version = self.db.get_version(resource_id)
            return SyncState(
                resource_id=resource_id,
                data=cached,
                version=version,
                last_modified=time.time(),
                checksum=self._compute_checksum(cached),
            )

        db_entry = self.db.get(resource_id)
        if db_entry:
            self.cache.put(resource_id, db_entry["data"])
            return SyncState(
                resource_id=resource_id,
                data=db_entry["data"],
                version=db_entry["version"],
                last_modified=db_entry["timestamp"],
                checksum=self._compute_checksum(db_entry["data"]),
            )

        return None


if __name__ == "__main__":
    service = SyncService(conflict_strategy=ConflictStrategy.MERGE)

    notifications = []
    service.subscribe("doc1", lambda e: notifications.append(e))

    # Client A creates a document
    event_a = SyncEvent(
        event_id="e1", client_id="clientA", resource_id="doc1",
        operation="create", data={"title": "Hello", "body": "World"},
    )
    state = service.sync(event_a)
    print(f"Created: version={state.version}, data={state.data}")

    # Client B updates the same document
    event_b = SyncEvent(
        event_id="e2", client_id="clientB", resource_id="doc1",
        operation="update", data={"title": "Hello", "body": "Updated"},
        version=1,
    )
    state = service.sync(event_b)
    print(f"Updated: version={state.version}, data={state.data}")

    # Get delta updates
    deltas = service.get_delta("doc1", since_version=0)
    print(f"Delta updates: {len(deltas)} events")

    print(f"Notifications received: {len(notifications)}")
