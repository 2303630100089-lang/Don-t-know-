"""
Algorithms 106-115: System Infrastructure Algorithms

106. Civic API Gateway
107. Real-Time Monitoring
108. Distributed Logging
109. BI Dashboard
110. User Engagement Scoring
111. Recommendation Refresh
112. Secure File Sharing
113. Enterprise Sync
114. Video Conferencing
115. Adaptive QoS
"""

import time
import hashlib
import secrets
import math
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, deque


# ============================================================
# Algorithm 106: Civic API Gateway
# ============================================================

class CivicAPIGateway:
    """API Gateway for routing to government/civic APIs with validation."""

    def __init__(self):
        self.routes = {}
        self.request_log = []
        self.rate_limits = defaultdict(lambda: {"count": 0, "window_start": time.time()})

    def register_route(self, path, backend_url, auth_required=True):
        self.routes[path] = {"url": backend_url, "auth_required": auth_required}

    def handle_request(self, path, headers=None, payload=None):
        """Route request to backend with validation."""
        route = self.routes.get(path)
        if not route:
            return {"status": 404, "body": "Not found"}

        if route["auth_required"]:
            if not headers or "Authorization" not in headers:
                return {"status": 401, "body": "Unauthorized"}

        self.request_log.append({"path": path, "timestamp": time.time()})
        return {"status": 200, "body": f"Routed to {route['url']}", "backend": route["url"]}


# ============================================================
# Algorithm 107: Real-Time Monitoring
# ============================================================

@dataclass
class MetricPoint:
    name: str
    value: float
    labels: dict = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)


class AlertRule:
    def __init__(self, name, metric_name, threshold, comparison="gt"):
        self.name = name
        self.metric_name = metric_name
        self.threshold = threshold
        self.comparison = comparison

    def evaluate(self, value):
        if self.comparison == "gt":
            return value > self.threshold
        elif self.comparison == "lt":
            return value < self.threshold
        return False


class RealTimeMonitor:
    """Metrics collection, visualization, alerts, and anomaly detection."""

    def __init__(self, window_size=100):
        self.metrics = defaultdict(lambda: deque(maxlen=window_size))
        self.alert_rules = []
        self.triggered_alerts = []

    def record(self, metric):
        self.metrics[metric.name].append(metric)

    def add_alert_rule(self, rule):
        self.alert_rules.append(rule)

    def check_alerts(self):
        """Check all alert rules against current metrics."""
        alerts = []
        for rule in self.alert_rules:
            values = self.metrics.get(rule.metric_name, [])
            if values:
                latest = values[-1].value
                if rule.evaluate(latest):
                    alert = {"rule": rule.name, "value": latest, "threshold": rule.threshold}
                    alerts.append(alert)
                    self.triggered_alerts.append(alert)
        return alerts

    def detect_anomaly(self, metric_name, z_threshold=2.0):
        """Simple z-score based anomaly detection."""
        values = [m.value for m in self.metrics.get(metric_name, [])]
        if len(values) < 5:
            return False, 0.0

        mean = sum(values) / len(values)
        std = math.sqrt(sum((v - mean) ** 2 for v in values) / len(values))
        if std == 0:
            return False, 0.0

        z_score = abs(values[-1] - mean) / std
        return z_score > z_threshold, z_score

    def get_summary(self, metric_name):
        values = [m.value for m in self.metrics.get(metric_name, [])]
        if not values:
            return {}
        return {
            "min": min(values), "max": max(values),
            "avg": sum(values) / len(values),
            "count": len(values),
        }


# ============================================================
# Algorithm 108: Distributed Logging
# ============================================================

@dataclass
class LogEntry:
    level: str
    message: str
    service: str
    trace_id: str = ""
    timestamp: float = field(default_factory=time.time)
    metadata: dict = field(default_factory=dict)


class LogCollector:
    """Collects logs from services and forwards to storage."""

    def __init__(self, buffer_size=1000):
        self.buffer = deque(maxlen=buffer_size)
        self.index = defaultdict(list)

    def collect(self, entry):
        self.buffer.append(entry)
        self.index[entry.service].append(entry)
        if entry.trace_id:
            self.index[f"trace:{entry.trace_id}"].append(entry)

    def query(self, service=None, level=None, trace_id=None, limit=50):
        if trace_id:
            entries = self.index.get(f"trace:{trace_id}", [])
        elif service:
            entries = self.index.get(service, [])
        else:
            entries = list(self.buffer)

        if level:
            entries = [e for e in entries if e.level == level]
        return entries[-limit:]


# ============================================================
# Algorithm 109: BI Dashboard
# ============================================================

class BIDashboard:
    """Business intelligence dashboard with fast queries."""

    def __init__(self):
        self.data_warehouse = defaultdict(list)

    def ingest(self, table, records):
        self.data_warehouse[table].extend(records)

    def query(self, table, filters=None, aggregation=None, group_by=None):
        records = self.data_warehouse.get(table, [])

        if filters:
            for key, value in filters.items():
                records = [r for r in records if r.get(key) == value]

        if group_by:
            groups = defaultdict(list)
            for r in records:
                groups[r.get(group_by, "unknown")].append(r)

            if aggregation:
                field_name = aggregation.get("field")
                func = aggregation.get("func", "sum")
                result = {}
                for group_key, group_records in groups.items():
                    values = [r.get(field_name, 0) for r in group_records]
                    if func == "sum":
                        result[group_key] = sum(values)
                    elif func == "avg":
                        result[group_key] = sum(values) / len(values) if values else 0
                    elif func == "count":
                        result[group_key] = len(values)
                return result
            return dict(groups)

        return records


# ============================================================
# Algorithm 110: User Engagement Scoring
# ============================================================

class EngagementScorer:
    """Score user engagement based on actions."""

    WEIGHTS = {
        "login": 1, "view": 1, "click": 2, "like": 3,
        "comment": 4, "share": 5, "purchase": 10,
    }

    def __init__(self, decay_factor=0.1):
        self.decay_factor = decay_factor
        self.scores = {}

    def score_user(self, user_id, actions):
        total = 0.0
        now = time.time()
        for action_type, timestamp in actions:
            weight = self.WEIGHTS.get(action_type, 1)
            age_days = (now - timestamp) / 86400
            decay = math.exp(-self.decay_factor * age_days)
            total += weight * decay

        self.scores[user_id] = total
        return total

    def get_ranking(self, top_k=10):
        sorted_users = sorted(self.scores.items(), key=lambda x: x[1], reverse=True)
        return sorted_users[:top_k]


# ============================================================
# Algorithm 111: Recommendation Refresh
# ============================================================

class RecommendationRefresher:
    """Refresh recommendations based on real-time user events."""

    def __init__(self):
        self.user_features = defaultdict(lambda: defaultdict(float))
        self.item_catalog = {}
        self.recommendations = {}

    def update_features(self, user_id, event_type, item_id, item_tags=None):
        weight = {"view": 1, "like": 3, "purchase": 5}.get(event_type, 1)
        for tag in (item_tags or []):
            self.user_features[user_id][tag] += weight

    def add_item(self, item_id, tags):
        self.item_catalog[item_id] = tags

    def refresh(self, user_id, top_k=10):
        prefs = self.user_features.get(user_id, {})
        if not prefs:
            return []

        scores = []
        for item_id, tags in self.item_catalog.items():
            score = sum(prefs.get(tag, 0) for tag in tags)
            scores.append((item_id, score))

        scores.sort(key=lambda x: x[1], reverse=True)
        self.recommendations[user_id] = scores[:top_k]
        return scores[:top_k]


# ============================================================
# Algorithm 112: Secure File Sharing
# ============================================================

class SecureFileSharing:
    """File sharing with tokenized URLs and CDN delivery."""

    def __init__(self):
        self.files = {}
        self.tokens = {}
        self.access_log = []

    def upload(self, file_id, data, owner_id, permissions=None):
        self.files[file_id] = {
            "data": data, "owner": owner_id,
            "permissions": permissions or {"public": False},
            "uploaded_at": time.time(),
        }

    def generate_share_link(self, file_id, expires_in=3600):
        token = secrets.token_urlsafe(32)
        self.tokens[token] = {
            "file_id": file_id,
            "expires_at": time.time() + expires_in,
        }
        return f"https://cdn.example.com/files/{token}"

    def access_file(self, token, user_id):
        token_data = self.tokens.get(token)
        if not token_data:
            return None, "Invalid token"
        if time.time() > token_data["expires_at"]:
            return None, "Token expired"

        file_data = self.files.get(token_data["file_id"])
        self.access_log.append({
            "file_id": token_data["file_id"],
            "user_id": user_id,
            "timestamp": time.time(),
        })
        return file_data, "OK"


# ============================================================
# Algorithm 113: Enterprise Sync
# ============================================================

class EnterpriseSyncService:
    """Sync workspace data with CRM/ERP systems."""

    def __init__(self):
        self.workspace_data = {}
        self.external_systems = {}
        self.sync_log = []

    def register_system(self, system_id, system_type):
        self.external_systems[system_id] = {"type": system_type, "data": {}}

    def sync(self, workspace_id, data, target_systems=None):
        self.workspace_data[workspace_id] = data
        targets = target_systems or list(self.external_systems.keys())
        results = []

        for sys_id in targets:
            if sys_id in self.external_systems:
                self.external_systems[sys_id]["data"][workspace_id] = data
                results.append({"system": sys_id, "status": "synced"})
                self.sync_log.append({
                    "workspace": workspace_id, "system": sys_id,
                    "timestamp": time.time(),
                })

        return results


# ============================================================
# Algorithm 114: Video Conferencing
# ============================================================

class VideoConferenceManager:
    """Manage video conferencing sessions with signaling and QoS."""

    def __init__(self):
        self.rooms = {}
        self.participants = defaultdict(set)

    def create_room(self, room_id, host_id):
        self.rooms[room_id] = {
            "host": host_id, "created_at": time.time(),
            "settings": {"encryption": True, "max_participants": 100},
        }
        self.participants[room_id].add(host_id)
        return self.rooms[room_id]

    def join_room(self, room_id, user_id):
        if room_id not in self.rooms:
            return False, "Room not found"
        max_p = self.rooms[room_id]["settings"]["max_participants"]
        if len(self.participants[room_id]) >= max_p:
            return False, "Room full"
        self.participants[room_id].add(user_id)
        return True, "Joined"

    def leave_room(self, room_id, user_id):
        self.participants[room_id].discard(user_id)

    def get_room_info(self, room_id):
        return {
            "room": self.rooms.get(room_id),
            "participants": list(self.participants.get(room_id, set())),
            "count": len(self.participants.get(room_id, set())),
        }


# ============================================================
# Algorithm 115: Adaptive QoS
# ============================================================

class AdaptiveQoS:
    """Adaptive Quality of Service management."""

    def __init__(self):
        self.network_history = deque(maxlen=50)
        self.current_settings = {
            "video_bitrate": 2500, "audio_bitrate": 128,
            "resolution": "720p", "fps": 30,
        }

    def record_network(self, bandwidth_kbps, latency_ms, loss_ratio):
        self.network_history.append({
            "bandwidth": bandwidth_kbps, "latency": latency_ms,
            "loss": loss_ratio, "timestamp": time.time(),
        })

    def adapt(self):
        """Adapt QoS settings based on network conditions."""
        if not self.network_history:
            return self.current_settings

        recent = list(self.network_history)[-5:]
        avg_bw = sum(m["bandwidth"] for m in recent) / len(recent)
        avg_loss = sum(m["loss"] for m in recent) / len(recent)

        if avg_bw > 5000 and avg_loss < 0.01:
            self.current_settings = {
                "video_bitrate": 5000, "audio_bitrate": 256,
                "resolution": "1080p", "fps": 30,
            }
        elif avg_bw > 2000 and avg_loss < 0.05:
            self.current_settings = {
                "video_bitrate": 2500, "audio_bitrate": 128,
                "resolution": "720p", "fps": 30,
            }
        elif avg_bw > 500:
            self.current_settings = {
                "video_bitrate": 800, "audio_bitrate": 64,
                "resolution": "480p", "fps": 15,
            }
        else:
            self.current_settings = {
                "video_bitrate": 200, "audio_bitrate": 32,
                "resolution": "240p", "fps": 10,
            }

        return self.current_settings

    def get_metrics(self):
        if not self.network_history:
            return {}
        recent = list(self.network_history)[-10:]
        return {
            "avg_bandwidth": sum(m["bandwidth"] for m in recent) / len(recent),
            "avg_latency": sum(m["latency"] for m in recent) / len(recent),
            "avg_loss": sum(m["loss"] for m in recent) / len(recent),
            "current_settings": self.current_settings,
        }


# ============================================================
# Main demonstration
# ============================================================

if __name__ == "__main__":
    # 106: Civic API Gateway
    gateway = CivicAPIGateway()
    gateway.register_route("/api/permits", "https://gov.example.com/permits")
    result = gateway.handle_request("/api/permits", {"Authorization": "Bearer token123"})
    print(f"106 Gateway: {result['status']} → {result.get('backend', 'N/A')}")

    # 107: Real-Time Monitoring
    monitor = RealTimeMonitor()
    monitor.add_alert_rule(AlertRule("high_cpu", "cpu", 80))
    for v in [45, 60, 75, 85, 90]:
        monitor.record(MetricPoint("cpu", v))
    alerts = monitor.check_alerts()
    print(f"107 Monitor: {len(alerts)} alerts triggered")

    # 108: Distributed Logging
    logger = LogCollector()
    logger.collect(LogEntry("INFO", "Request handled", "api-service", trace_id="t1"))
    logger.collect(LogEntry("ERROR", "DB timeout", "db-service", trace_id="t1"))
    logs = logger.query(trace_id="t1")
    print(f"108 Logging: {len(logs)} log entries for trace t1")

    # 109: BI Dashboard
    bi = BIDashboard()
    bi.ingest("sales", [
        {"region": "US", "amount": 100}, {"region": "EU", "amount": 200},
        {"region": "US", "amount": 150},
    ])
    result = bi.query("sales", group_by="region", aggregation={"field": "amount", "func": "sum"})
    print(f"109 BI: {result}")

    # 110: Engagement Scoring
    scorer = EngagementScorer()
    now = time.time()
    score = scorer.score_user("user1", [
        ("login", now), ("view", now), ("purchase", now),
    ])
    print(f"110 Engagement: user1 score={score:.1f}")

    # 111: Recommendation Refresh
    rec = RecommendationRefresher()
    rec.add_item("item1", ["tech", "ai"])
    rec.add_item("item2", ["sports"])
    rec.update_features("user1", "like", "item1", ["tech", "ai"])
    recs = rec.refresh("user1")
    print(f"111 Recommendations: {recs[:3]}")

    # 112: Secure File Sharing
    fs = SecureFileSharing()
    fs.upload("doc1", b"secret data", "alice")
    link = fs.generate_share_link("doc1")
    token = link.split("/")[-1]
    data, status = fs.access_file(token, "bob")
    print(f"112 File Sharing: {status}")

    # 113: Enterprise Sync
    sync = EnterpriseSyncService()
    sync.register_system("salesforce", "CRM")
    results = sync.sync("ws-1", {"contacts": 100})
    print(f"113 Enterprise Sync: {results}")

    # 114: Video Conferencing
    vc = VideoConferenceManager()
    vc.create_room("room-1", "alice")
    vc.join_room("room-1", "bob")
    info = vc.get_room_info("room-1")
    print(f"114 Video Conference: {info['count']} participants")

    # 115: Adaptive QoS
    qos = AdaptiveQoS()
    qos.record_network(8000, 20, 0.005)
    settings = qos.adapt()
    print(f"115 QoS: {settings['resolution']} @ {settings['video_bitrate']}kbps")
