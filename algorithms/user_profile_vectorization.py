"""
Algorithm 97: User Profile Vectorization

- User actions → features
- Features → embedding model
- Vector stored in DB
- Fast ANN search
- Personalization layer
"""

import math
import time
from dataclasses import dataclass, field
from collections import defaultdict


@dataclass
class UserAction:
    """A user action event."""
    user_id: str
    action_type: str  # "view", "like", "share", "purchase", "search"
    item_id: str
    item_category: str = ""
    timestamp: float = field(default_factory=time.time)
    metadata: dict = field(default_factory=dict)


@dataclass
class UserProfile:
    """A user profile with feature vector."""
    user_id: str
    features: dict = field(default_factory=dict)
    vector: list = field(default_factory=list)
    last_updated: float = field(default_factory=time.time)


class FeatureExtractor:
    """Extract features from user actions."""

    ACTION_WEIGHTS = {
        "view": 1.0,
        "like": 3.0,
        "share": 5.0,
        "purchase": 10.0,
        "search": 2.0,
    }

    def extract(self, actions):
        """Extract feature dictionary from user actions."""
        features = {}

        # Action frequency features
        action_counts = defaultdict(int)
        for action in actions:
            action_counts[action.action_type] += 1
        total_actions = sum(action_counts.values()) or 1

        for action_type, count in action_counts.items():
            features[f"action_freq_{action_type}"] = count / total_actions

        # Category preference features
        category_scores = defaultdict(float)
        for action in actions:
            if action.item_category:
                weight = self.ACTION_WEIGHTS.get(action.action_type, 1.0)
                # Time decay
                age_days = (time.time() - action.timestamp) / 86400
                decay = math.exp(-0.1 * age_days)
                category_scores[action.item_category] += weight * decay

        total_score = sum(category_scores.values()) or 1
        for category, score in category_scores.items():
            features[f"cat_pref_{category}"] = score / total_score

        # Engagement features
        if actions:
            timestamps = [a.timestamp for a in actions]
            features["recency"] = max(timestamps)
            features["frequency"] = len(actions)
            time_span = max(timestamps) - min(timestamps) if len(timestamps) > 1 else 1
            features["regularity"] = len(actions) / max(time_span / 86400, 1)

        # Diversity features
        unique_items = len(set(a.item_id for a in actions))
        unique_categories = len(set(a.item_category for a in actions if a.item_category))
        features["item_diversity"] = unique_items / max(len(actions), 1)
        features["category_diversity"] = unique_categories / max(len(actions), 1)

        return features


class EmbeddingModel:
    """Simple embedding model to convert features to vectors."""

    def __init__(self, embedding_dim=64):
        self.embedding_dim = embedding_dim
        self.feature_index = {}
        self._next_idx = 0

    def _get_feature_idx(self, feature_name):
        if feature_name not in self.feature_index:
            self.feature_index[feature_name] = self._next_idx
            self._next_idx += 1
        return self.feature_index[feature_name]

    def encode(self, features):
        """Encode features into a fixed-size vector."""
        vector = [0.0] * self.embedding_dim

        for feature_name, value in features.items():
            idx = self._get_feature_idx(feature_name)
            # Hash-based projection into embedding space
            for d in range(self.embedding_dim):
                hash_val = hash(f"{feature_name}_{d}") % 1000 / 1000.0
                vector[d] += value * (hash_val - 0.5) * 2

        # L2 normalize
        norm = math.sqrt(sum(v * v for v in vector))
        if norm > 0:
            vector = [v / norm for v in vector]

        return vector


class VectorStore:
    """Store and search user profile vectors."""

    def __init__(self):
        self.vectors = {}  # user_id -> vector
        self.profiles = {}  # user_id -> UserProfile

    def store(self, profile):
        """Store a user profile vector."""
        self.vectors[profile.user_id] = profile.vector
        self.profiles[profile.user_id] = profile

    def search(self, query_vector, k=10, exclude_ids=None):
        """Search for similar users via cosine similarity."""
        exclude = exclude_ids or set()
        results = []

        for user_id, vector in self.vectors.items():
            if user_id in exclude:
                continue
            sim = self._cosine_similarity(query_vector, vector)
            results.append((user_id, sim))

        results.sort(key=lambda x: x[1], reverse=True)
        return results[:k]

    @staticmethod
    def _cosine_similarity(a, b):
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = math.sqrt(sum(x * x for x in a))
        norm_b = math.sqrt(sum(x * x for x in b))
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)


class PersonalizationLayer:
    """Apply personalization based on user vectors."""

    def __init__(self, vector_store):
        self.vector_store = vector_store

    def get_similar_users(self, user_id, k=5):
        """Find users with similar profiles."""
        profile = self.vector_store.profiles.get(user_id)
        if not profile or not profile.vector:
            return []
        return self.vector_store.search(profile.vector, k, exclude_ids={user_id})

    def personalize_items(self, user_id, item_vectors, k=10):
        """Rank items based on user profile similarity."""
        profile = self.vector_store.profiles.get(user_id)
        if not profile or not profile.vector:
            return list(item_vectors.keys())[:k]

        scores = []
        for item_id, item_vec in item_vectors.items():
            sim = self.vector_store._cosine_similarity(profile.vector, item_vec)
            scores.append((item_id, sim))

        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:k]


class UserProfileVectorizer:
    """End-to-end user profile vectorization pipeline."""

    def __init__(self, embedding_dim=64):
        self.feature_extractor = FeatureExtractor()
        self.embedding_model = EmbeddingModel(embedding_dim)
        self.vector_store = VectorStore()
        self.personalization = PersonalizationLayer(self.vector_store)
        self.user_actions = defaultdict(list)

    def record_action(self, action):
        """Record a user action."""
        self.user_actions[action.user_id].append(action)

    def update_profile(self, user_id):
        """Update user profile vector from recent actions."""
        actions = self.user_actions.get(user_id, [])
        if not actions:
            return None

        features = self.feature_extractor.extract(actions)
        vector = self.embedding_model.encode(features)

        profile = UserProfile(
            user_id=user_id,
            features=features,
            vector=vector,
        )

        self.vector_store.store(profile)
        return profile

    def find_similar(self, user_id, k=5):
        """Find similar users."""
        return self.personalization.get_similar_users(user_id, k)


if __name__ == "__main__":
    vectorizer = UserProfileVectorizer(embedding_dim=32)

    # Simulate user actions
    users_actions = {
        "alice": [
            ("view", "item1", "tech"), ("like", "item2", "tech"),
            ("purchase", "item3", "tech"), ("view", "item4", "science"),
        ],
        "bob": [
            ("view", "item5", "sports"), ("like", "item6", "sports"),
            ("share", "item7", "sports"), ("view", "item8", "music"),
        ],
        "charlie": [
            ("view", "item1", "tech"), ("purchase", "item9", "tech"),
            ("like", "item10", "science"), ("search", "item11", "tech"),
        ],
    }

    for user_id, actions in users_actions.items():
        for action_type, item_id, category in actions:
            vectorizer.record_action(UserAction(
                user_id=user_id, action_type=action_type,
                item_id=item_id, item_category=category,
            ))
        vectorizer.update_profile(user_id)

    # Find similar users
    for user_id in users_actions:
        similar = vectorizer.find_similar(user_id, k=2)
        print(f"{user_id} similar to: {[(uid, f'{sim:.3f}') for uid, sim in similar]}")
