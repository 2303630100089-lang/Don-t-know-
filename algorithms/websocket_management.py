"""
Algorithm 91: WebSocket Management

- Client connects → gateway
- Gateway → session manager
- Fast message routing
- Heartbeat checks
- Auto-reconnect
"""

import time
import threading
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict


class ConnectionState(Enum):
    CONNECTING = "connecting"
    OPEN = "open"
    CLOSING = "closing"
    CLOSED = "closed"
    RECONNECTING = "reconnecting"


@dataclass
class WebSocketConnection:
    """A WebSocket connection."""
    connection_id: str
    client_id: str
    state: ConnectionState = ConnectionState.CONNECTING
    connected_at: float = field(default_factory=time.time)
    last_heartbeat: float = field(default_factory=time.time)
    message_count: int = 0
    reconnect_count: int = 0
    metadata: dict = field(default_factory=dict)


@dataclass
class WSMessage:
    """A WebSocket message."""
    message_id: str
    sender_id: str
    target_id: str  # connection_id, room_id, or "broadcast"
    payload: dict
    timestamp: float = field(default_factory=time.time)


class SessionManager:
    """Manage WebSocket sessions."""

    def __init__(self):
        self.sessions = {}  # connection_id -> WebSocketConnection
        self.client_connections = defaultdict(set)  # client_id -> set of connection_ids
        self.rooms = defaultdict(set)  # room_id -> set of connection_ids

    def register(self, connection):
        """Register a new connection."""
        self.sessions[connection.connection_id] = connection
        self.client_connections[connection.client_id].add(connection.connection_id)
        connection.state = ConnectionState.OPEN

    def unregister(self, connection_id):
        """Unregister a connection."""
        conn = self.sessions.pop(connection_id, None)
        if conn:
            self.client_connections[conn.client_id].discard(connection_id)
            for room_conns in self.rooms.values():
                room_conns.discard(connection_id)
        return conn

    def get_connection(self, connection_id):
        return self.sessions.get(connection_id)

    def get_client_connections(self, client_id):
        return [
            self.sessions[cid]
            for cid in self.client_connections.get(client_id, set())
            if cid in self.sessions
        ]

    def join_room(self, connection_id, room_id):
        self.rooms[room_id].add(connection_id)

    def leave_room(self, connection_id, room_id):
        self.rooms[room_id].discard(connection_id)

    def get_room_members(self, room_id):
        return [
            self.sessions[cid]
            for cid in self.rooms.get(room_id, set())
            if cid in self.sessions
        ]

    @property
    def active_connections(self):
        return len(self.sessions)


class MessageRouter:
    """Route messages between WebSocket connections."""

    def __init__(self, session_manager):
        self.session_manager = session_manager
        self.message_log = []

    def route(self, message):
        """Route a message to its target."""
        self.message_log.append(message)
        targets = []

        if message.target_id == "broadcast":
            targets = list(self.session_manager.sessions.values())
        elif message.target_id.startswith("room:"):
            room_id = message.target_id[5:]
            targets = self.session_manager.get_room_members(room_id)
        else:
            conn = self.session_manager.get_connection(message.target_id)
            if conn:
                targets = [conn]

        delivered = []
        for conn in targets:
            if conn.state == ConnectionState.OPEN and conn.connection_id != message.sender_id:
                conn.message_count += 1
                delivered.append(conn.connection_id)

        return delivered


class HeartbeatMonitor:
    """Monitor connection health via heartbeats."""

    def __init__(self, session_manager, timeout=30.0):
        self.session_manager = session_manager
        self.timeout = timeout

    def heartbeat(self, connection_id):
        """Record a heartbeat from a connection."""
        conn = self.session_manager.get_connection(connection_id)
        if conn:
            conn.last_heartbeat = time.time()
            return True
        return False

    def check_health(self):
        """Check all connections for heartbeat timeout."""
        now = time.time()
        stale = []

        for conn_id, conn in list(self.session_manager.sessions.items()):
            if conn.state == ConnectionState.OPEN:
                if now - conn.last_heartbeat > self.timeout:
                    stale.append(conn_id)

        return stale


class WebSocketGateway:
    """
    WebSocket gateway managing connections, routing, heartbeats,
    and auto-reconnect.
    """

    def __init__(self, heartbeat_timeout=30.0, max_reconnects=5):
        self.session_manager = SessionManager()
        self.router = MessageRouter(self.session_manager)
        self.heartbeat_monitor = HeartbeatMonitor(
            self.session_manager, heartbeat_timeout
        )
        self.max_reconnects = max_reconnects
        self.event_log = []
        self._connection_counter = 0

    def connect(self, client_id, metadata=None):
        """Handle a new client connection."""
        self._connection_counter += 1
        conn_id = f"ws-{self._connection_counter}"

        connection = WebSocketConnection(
            connection_id=conn_id,
            client_id=client_id,
            metadata=metadata or {},
        )

        self.session_manager.register(connection)
        self._log_event("connect", conn_id, client_id)
        return connection

    def disconnect(self, connection_id):
        """Handle client disconnection."""
        conn = self.session_manager.unregister(connection_id)
        if conn:
            conn.state = ConnectionState.CLOSED
            self._log_event("disconnect", connection_id, conn.client_id)
        return conn

    def reconnect(self, connection_id):
        """Auto-reconnect a dropped connection."""
        conn = self.session_manager.get_connection(connection_id)
        if conn is None:
            return None

        if conn.reconnect_count >= self.max_reconnects:
            self.disconnect(connection_id)
            return None

        conn.state = ConnectionState.RECONNECTING
        conn.reconnect_count += 1
        conn.state = ConnectionState.OPEN
        conn.last_heartbeat = time.time()

        self._log_event("reconnect", connection_id, conn.client_id)
        return conn

    def send(self, sender_id, target_id, payload):
        """Send a message through the gateway."""
        msg = WSMessage(
            message_id=f"msg-{len(self.router.message_log)}",
            sender_id=sender_id,
            target_id=target_id,
            payload=payload,
        )
        return self.router.route(msg)

    def join_room(self, connection_id, room_id):
        """Join a chat room."""
        self.session_manager.join_room(connection_id, room_id)
        self._log_event("join_room", connection_id, room_id)

    def leave_room(self, connection_id, room_id):
        """Leave a chat room."""
        self.session_manager.leave_room(connection_id, room_id)
        self._log_event("leave_room", connection_id, room_id)

    def heartbeat(self, connection_id):
        """Process heartbeat."""
        return self.heartbeat_monitor.heartbeat(connection_id)

    def check_stale_connections(self):
        """Check and handle stale connections."""
        stale = self.heartbeat_monitor.check_health()
        for conn_id in stale:
            result = self.reconnect(conn_id)
            if result is None:
                self.disconnect(conn_id)
        return stale

    def _log_event(self, event_type, *args):
        self.event_log.append({
            "type": event_type,
            "args": args,
            "timestamp": time.time(),
        })

    def get_stats(self):
        return {
            "active_connections": self.session_manager.active_connections,
            "total_messages": len(self.router.message_log),
            "rooms": len(self.session_manager.rooms),
            "events": len(self.event_log),
        }


if __name__ == "__main__":
    gateway = WebSocketGateway()

    # Connect clients
    conn_a = gateway.connect("alice")
    conn_b = gateway.connect("bob")
    conn_c = gateway.connect("charlie")

    print(f"Connected: {gateway.get_stats()['active_connections']} clients")

    # Join a room
    gateway.join_room(conn_a.connection_id, "general")
    gateway.join_room(conn_b.connection_id, "general")
    gateway.join_room(conn_c.connection_id, "general")

    # Send message to room
    delivered = gateway.send(
        conn_a.connection_id, "room:general",
        {"text": "Hello everyone!"}
    )
    print(f"Message delivered to {len(delivered)} connections")

    # Direct message
    delivered = gateway.send(
        conn_a.connection_id, conn_b.connection_id,
        {"text": "Hey Bob!"}
    )
    print(f"DM delivered to {len(delivered)} connections")

    # Heartbeat
    gateway.heartbeat(conn_a.connection_id)

    print(f"\nStats: {gateway.get_stats()}")
