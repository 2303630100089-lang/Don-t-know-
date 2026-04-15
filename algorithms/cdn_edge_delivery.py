"""
Algorithm 90: CDN Edge Delivery

- Content cached at edge
- Fast lookup
- Geo-routing
- Cache invalidation
- User served nearest node
"""

import time
import math
from dataclasses import dataclass, field
from collections import OrderedDict


@dataclass
class GeoLocation:
    """Geographic coordinates."""
    latitude: float
    longitude: float
    region: str = ""


@dataclass
class EdgeNode:
    """A CDN edge node."""
    node_id: str
    location: GeoLocation
    cache: OrderedDict = field(default_factory=OrderedDict)
    max_cache_size: int = 1000
    hits: int = 0
    misses: int = 0

    def get(self, content_key):
        """Get content from edge cache."""
        if content_key in self.cache:
            self.cache.move_to_end(content_key)
            self.hits += 1
            return self.cache[content_key]
        self.misses += 1
        return None

    def put(self, content_key, content):
        """Cache content at edge node."""
        if content_key in self.cache:
            self.cache.move_to_end(content_key)
        self.cache[content_key] = {
            "data": content,
            "cached_at": time.time(),
            "access_count": 0,
        }
        while len(self.cache) > self.max_cache_size:
            self.cache.popitem(last=False)

    def invalidate(self, content_key):
        """Invalidate a specific cache entry."""
        self.cache.pop(content_key, None)

    def invalidate_pattern(self, prefix):
        """Invalidate all keys matching a prefix."""
        to_delete = [k for k in self.cache if k.startswith(prefix)]
        for k in to_delete:
            del self.cache[k]

    @property
    def hit_ratio(self):
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0


class GeoRouter:
    """Route users to the nearest edge node."""

    @staticmethod
    def haversine_distance(loc1, loc2):
        """Calculate distance between two coordinates in kilometers."""
        R = 6371  # Earth radius in km

        lat1 = math.radians(loc1.latitude)
        lat2 = math.radians(loc2.latitude)
        dlat = math.radians(loc2.latitude - loc1.latitude)
        dlon = math.radians(loc2.longitude - loc1.longitude)

        a = (math.sin(dlat / 2) ** 2 +
             math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        return R * c

    def find_nearest(self, user_location, edge_nodes):
        """Find the nearest edge node to the user."""
        nearest = None
        min_distance = float('inf')

        for node in edge_nodes:
            distance = self.haversine_distance(user_location, node.location)
            if distance < min_distance:
                min_distance = distance
                nearest = node

        return nearest, min_distance


class OriginServer:
    """Origin server holding the source content."""

    def __init__(self):
        self.content = {}

    def put(self, content_key, data):
        self.content[content_key] = data

    def get(self, content_key):
        return self.content.get(content_key)


class CDN:
    """Content Delivery Network with edge caching and geo-routing."""

    def __init__(self):
        self.origin = OriginServer()
        self.edge_nodes = []
        self.geo_router = GeoRouter()
        self.request_log = []

    def add_edge_node(self, node):
        """Add an edge node to the CDN."""
        self.edge_nodes.append(node)

    def publish(self, content_key, data):
        """Publish content to origin server."""
        self.origin.put(content_key, data)

    def deliver(self, content_key, user_location):
        """Deliver content to user from nearest edge."""
        nearest, distance = self.geo_router.find_nearest(
            user_location, self.edge_nodes
        )

        if nearest is None:
            return self.origin.get(content_key)

        # Try edge cache first
        content = nearest.get(content_key)
        cache_hit = content is not None

        if not cache_hit:
            # Fetch from origin and cache at edge
            origin_content = self.origin.get(content_key)
            if origin_content:
                nearest.put(content_key, origin_content)
                content = nearest.get(content_key)

        self.request_log.append({
            "content_key": content_key,
            "edge_node": nearest.node_id,
            "cache_hit": cache_hit,
            "distance_km": distance,
            "timestamp": time.time(),
        })

        return content

    def invalidate(self, content_key):
        """Invalidate content across all edge nodes."""
        for node in self.edge_nodes:
            node.invalidate(content_key)

    def invalidate_pattern(self, prefix):
        """Invalidate by pattern across all edge nodes."""
        for node in self.edge_nodes:
            node.invalidate_pattern(prefix)

    def get_stats(self):
        """Get CDN performance statistics."""
        total_hits = sum(n.hits for n in self.edge_nodes)
        total_misses = sum(n.misses for n in self.edge_nodes)
        total = total_hits + total_misses

        return {
            "total_requests": total,
            "cache_hits": total_hits,
            "cache_misses": total_misses,
            "hit_ratio": total_hits / total if total > 0 else 0.0,
            "edge_nodes": len(self.edge_nodes),
            "per_node": {
                n.node_id: {
                    "hits": n.hits,
                    "misses": n.misses,
                    "hit_ratio": n.hit_ratio,
                    "cache_size": len(n.cache),
                }
                for n in self.edge_nodes
            },
        }


if __name__ == "__main__":
    cdn = CDN()

    # Add edge nodes around the world
    cdn.add_edge_node(EdgeNode("us-east", GeoLocation(40.7128, -74.0060, "US East")))
    cdn.add_edge_node(EdgeNode("us-west", GeoLocation(37.7749, -122.4194, "US West")))
    cdn.add_edge_node(EdgeNode("eu-west", GeoLocation(51.5074, -0.1278, "EU West")))
    cdn.add_edge_node(EdgeNode("ap-east", GeoLocation(35.6762, 139.6503, "AP East")))

    # Publish content
    cdn.publish("img/logo.png", b"<logo_data>")
    cdn.publish("api/config.json", '{"version": "2.0"}')

    # Users from different locations
    users = [
        ("User NY", GeoLocation(40.7128, -74.0060)),
        ("User LA", GeoLocation(34.0522, -118.2437)),
        ("User London", GeoLocation(51.5074, -0.1278)),
        ("User Tokyo", GeoLocation(35.6762, 139.6503)),
    ]

    for name, loc in users:
        content = cdn.deliver("img/logo.png", loc)
        print(f"{name}: received content (cache_hit={cdn.request_log[-1]['cache_hit']}, "
              f"edge={cdn.request_log[-1]['edge_node']}, "
              f"dist={cdn.request_log[-1]['distance_km']:.0f}km)")

    # Second round - should be all cache hits
    print("\nSecond request round:")
    for name, loc in users:
        content = cdn.deliver("img/logo.png", loc)
        print(f"{name}: cache_hit={cdn.request_log[-1]['cache_hit']}")

    print(f"\nCDN Stats: {cdn.get_stats()['hit_ratio']:.1%} hit ratio")
