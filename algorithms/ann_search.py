"""
Algorithm 78: ANN Search (Approximate Nearest Neighbor)

- Input vector → ANN index
- Index → nearest neighbors
- Fast retrieval via HNSW (Hierarchical Navigable Small World)
- Top-K results returned
- Personalized ranking applied
"""

import heapq
import math
import random
from dataclasses import dataclass, field


@dataclass
class HNSWNode:
    """A node in the HNSW graph."""
    node_id: int
    vector: list
    neighbors: dict = field(default_factory=dict)  # level -> list of neighbor ids


class HNSWIndex:
    """
    Hierarchical Navigable Small World (HNSW) index for fast
    approximate nearest neighbor search.
    """

    def __init__(self, dim, m=16, ef_construction=200, max_level=4):
        self.dim = dim
        self.m = m  # max neighbors per node per level
        self.ef_construction = ef_construction
        self.max_level = max_level
        self.nodes = {}
        self.entry_point = None

    @staticmethod
    def _euclidean_distance(vec_a, vec_b):
        return math.sqrt(sum((a - b) ** 2 for a, b in zip(vec_a, vec_b)))

    @staticmethod
    def _cosine_similarity(vec_a, vec_b):
        dot = sum(a * b for a, b in zip(vec_a, vec_b))
        norm_a = math.sqrt(sum(a * a for a in vec_a))
        norm_b = math.sqrt(sum(b * b for b in vec_b))
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)

    def _random_level(self):
        level = 0
        while random.random() < 0.5 and level < self.max_level - 1:
            level += 1
        return level

    def insert(self, node_id, vector):
        """Insert a vector into the HNSW index."""
        level = self._random_level()
        node = HNSWNode(node_id=node_id, vector=vector)

        for lvl in range(level + 1):
            node.neighbors[lvl] = []

        self.nodes[node_id] = node

        if self.entry_point is None:
            self.entry_point = node_id
            return

        current = self.entry_point

        # Traverse from top level down to node's level
        for lvl in range(self.max_level - 1, level, -1):
            current = self._greedy_search(vector, current, lvl)

        # Insert at each level from node's level down to 0
        for lvl in range(min(level, self.max_level - 1), -1, -1):
            neighbors = self._search_layer(vector, current, self.ef_construction, lvl)
            selected = self._select_neighbors(vector, neighbors, self.m)

            node.neighbors[lvl] = selected

            for neighbor_id in selected:
                neighbor_node = self.nodes[neighbor_id]
                if lvl not in neighbor_node.neighbors:
                    neighbor_node.neighbors[lvl] = []
                neighbor_node.neighbors[lvl].append(node_id)

                if len(neighbor_node.neighbors[lvl]) > self.m:
                    neighbor_node.neighbors[lvl] = self._select_neighbors(
                        neighbor_node.vector, neighbor_node.neighbors[lvl], self.m
                    )

            if neighbors:
                current = neighbors[0]

    def _greedy_search(self, query, entry_id, level):
        """Greedy search at a single level."""
        current = entry_id
        current_dist = self._euclidean_distance(query, self.nodes[current].vector)

        while True:
            best_neighbor = current
            best_dist = current_dist

            neighbors = self.nodes[current].neighbors.get(level, [])
            for neighbor_id in neighbors:
                dist = self._euclidean_distance(query, self.nodes[neighbor_id].vector)
                if dist < best_dist:
                    best_dist = dist
                    best_neighbor = neighbor_id

            if best_neighbor == current:
                break
            current = best_neighbor
            current_dist = best_dist

        return current

    def _search_layer(self, query, entry_id, ef, level):
        """Search within a single layer, returning ef nearest neighbors."""
        visited = {entry_id}
        dist = self._euclidean_distance(query, self.nodes[entry_id].vector)
        candidates = [(dist, entry_id)]
        results = [(-dist, entry_id)]

        while candidates:
            c_dist, c_id = heapq.heappop(candidates)
            f_dist = -results[0][1] if results else float('inf')

            if c_dist > f_dist and len(results) >= ef:
                break

            for neighbor_id in self.nodes[c_id].neighbors.get(level, []):
                if neighbor_id not in visited:
                    visited.add(neighbor_id)
                    n_dist = self._euclidean_distance(
                        query, self.nodes[neighbor_id].vector
                    )
                    if len(results) < ef or n_dist < -results[0][0]:
                        heapq.heappush(candidates, (n_dist, neighbor_id))
                        heapq.heappush(results, (-n_dist, neighbor_id))
                        if len(results) > ef:
                            heapq.heappop(results)

        return [node_id for _, node_id in sorted(results, key=lambda x: -x[0])]

    def _select_neighbors(self, query, candidate_ids, m):
        """Select the m closest neighbors from candidates."""
        if not candidate_ids:
            return []
        distances = [
            (self._euclidean_distance(query, self.nodes[cid].vector), cid)
            for cid in candidate_ids
        ]
        distances.sort()
        return [cid for _, cid in distances[:m]]

    def search(self, query_vector, k=10, ef_search=50):
        """Search for the k approximate nearest neighbors."""
        if self.entry_point is None:
            return []

        current = self.entry_point

        for lvl in range(self.max_level - 1, 0, -1):
            current = self._greedy_search(query_vector, current, lvl)

        candidates = self._search_layer(query_vector, current, max(ef_search, k), 0)

        results = []
        for node_id in candidates[:k]:
            dist = self._euclidean_distance(query_vector, self.nodes[node_id].vector)
            results.append((node_id, dist))

        results.sort(key=lambda x: x[1])
        return results[:k]


def personalized_ranking(results, user_preferences=None):
    """Apply personalized ranking to ANN search results."""
    if not user_preferences:
        return results

    ranked = []
    for node_id, distance in results:
        boost = user_preferences.get(node_id, 0.0)
        adjusted_score = 1.0 / (1.0 + distance) + boost
        ranked.append((node_id, adjusted_score))

    ranked.sort(key=lambda x: x[1], reverse=True)
    return ranked


if __name__ == "__main__":
    # Example usage
    index = HNSWIndex(dim=3, m=4, ef_construction=20, max_level=3)

    vectors = {
        0: [1.0, 2.0, 3.0],
        1: [4.0, 5.0, 6.0],
        2: [1.1, 2.1, 3.1],
        3: [7.0, 8.0, 9.0],
        4: [1.0, 2.0, 3.5],
    }

    for vid, vec in vectors.items():
        index.insert(vid, vec)

    query = [1.0, 2.0, 3.0]
    results = index.search(query, k=3)
    print(f"Top-3 nearest neighbors for {query}:")
    for node_id, dist in results:
        print(f"  Node {node_id}: distance={dist:.4f}")

    preferences = {2: 0.5, 4: 0.3}
    ranked = personalized_ranking(results, preferences)
    print(f"\nPersonalized ranking:")
    for node_id, score in ranked:
        print(f"  Node {node_id}: score={score:.4f}")
