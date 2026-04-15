"""
Algorithms 116-131: AI/ML Algorithms

116. AI Chatbot
117. AI Vision
118. AI Speech
119. AI Translation
120. AI Summarization
121. AI Personalization
122. AI Prediction
123. AI Clustering
124. AI Classification
125. AI Regression
126. AI Embedding
127. AI Ranking
128. AI Matching
129. AI Optimization
130. AI Reinforcement
131. AI Anomaly Detection
"""

import math
import random
import time
from dataclasses import dataclass, field
from collections import defaultdict
from enum import Enum


# ============================================================
# Algorithm 116: AI Chatbot
# ============================================================

class AIChatbot:
    """NLP-based chatbot with intent detection and response generation."""

    def __init__(self):
        self.intents = {
            "greeting": {
                "patterns": ["hello", "hi", "hey", "good morning"],
                "responses": ["Hello! How can I help?", "Hi there!", "Hey! What can I do for you?"],
            },
            "farewell": {
                "patterns": ["bye", "goodbye", "see you"],
                "responses": ["Goodbye!", "See you later!", "Take care!"],
            },
            "help": {
                "patterns": ["help", "support", "assist", "problem"],
                "responses": ["I'm here to help! What do you need?", "How can I assist you?"],
            },
            "status": {
                "patterns": ["status", "order", "tracking"],
                "responses": ["Let me check your status.", "I'll look that up for you."],
            },
        }
        self.conversation_log = []
        self.analytics = defaultdict(int)

    def detect_intent(self, text):
        """Detect user intent from text."""
        text_lower = text.lower()
        best_intent = "unknown"
        best_score = 0

        for intent, data in self.intents.items():
            score = sum(1 for p in data["patterns"] if p in text_lower)
            if score > best_score:
                best_score = score
                best_intent = intent

        return best_intent, best_score

    def respond(self, user_input):
        """Generate a response to user input."""
        intent, confidence = self.detect_intent(user_input)
        self.analytics[intent] += 1

        if intent in self.intents:
            response = random.choice(self.intents[intent]["responses"])
        else:
            response = "I'm not sure I understand. Can you rephrase?"

        self.conversation_log.append({
            "input": user_input, "intent": intent,
            "response": response, "timestamp": time.time(),
        })
        return response, intent


# ============================================================
# Algorithm 117: AI Vision
# ============================================================

class AIVision:
    """Computer vision model for feature extraction and violation detection."""

    def __init__(self):
        self.labels = ["safe", "text", "face", "object", "scene", "violation"]
        self.log = []

    def extract_features(self, image_data):
        """Extract features from image (simulated)."""
        seed = hash(str(image_data)) % 10000
        random.seed(seed)
        features = [random.gauss(0, 1) for _ in range(128)]
        return features

    def classify(self, image_data):
        """Classify image content."""
        features = self.extract_features(image_data)
        feature_sum = sum(abs(f) for f in features[:10])

        if feature_sum > 12:
            label = "violation"
            confidence = min(0.95, feature_sum / 15)
        else:
            label = "safe"
            confidence = max(0.5, 1.0 - feature_sum / 15)

        result = {"label": label, "confidence": confidence, "features_dim": len(features)}
        self.log.append(result)
        return result


# ============================================================
# Algorithm 118: AI Speech
# ============================================================

class AISpeech:
    """Automatic Speech Recognition (ASR) model."""

    def __init__(self):
        self.vocabulary = set("abcdefghijklmnopqrstuvwxyz ")
        self.log = []

    def transcribe(self, audio_data):
        """Transcribe audio to text (simulated)."""
        # Simulate ASR output
        seed = hash(str(audio_data)[:100]) % 10000
        random.seed(seed)
        words = ["the", "quick", "brown", "fox", "jumps", "over", "lazy", "dog",
                 "hello", "world", "how", "are", "you", "today", "thank", "please"]
        length = random.randint(3, 10)
        text = " ".join(random.choices(words, k=length))

        result = {"text": text, "confidence": random.uniform(0.7, 0.99),
                  "duration_ms": len(str(audio_data)) * 0.1}
        self.log.append(result)
        return result


# ============================================================
# Algorithm 119: AI Translation
# ============================================================

class AITranslation:
    """Text translation model."""

    def __init__(self):
        self.cache = {}
        self.log = []

    def translate(self, text, source_lang="en", target_lang="es"):
        """Translate text (simulated with reversal for demo)."""
        cache_key = f"{source_lang}:{target_lang}:{text}"
        if cache_key in self.cache:
            return self.cache[cache_key]

        # Simulated translation: reverse words and add language tag
        words = text.split()
        translated = " ".join(w[::-1] for w in words)
        translated = f"[{target_lang}] {translated}"

        result = {"original": text, "translated": translated,
                  "source": source_lang, "target": target_lang}
        self.cache[cache_key] = result
        self.log.append(result)
        return result


# ============================================================
# Algorithm 120: AI Summarization
# ============================================================

class AISummarization:
    """Text summarization model."""

    def __init__(self, ratio=0.3):
        self.ratio = ratio
        self.log = []

    def summarize(self, text):
        """Summarize text by extracting key sentences."""
        sentences = [s.strip() for s in text.replace("!", ".").replace("?", ".").split(".") if s.strip()]
        if not sentences:
            return ""

        # Score sentences by word importance
        word_freq = defaultdict(int)
        for sentence in sentences:
            for word in sentence.lower().split():
                word_freq[word] += 1

        scores = []
        for i, sentence in enumerate(sentences):
            words = sentence.lower().split()
            score = sum(word_freq[w] for w in words) / max(len(words), 1)
            # Boost first sentences
            if i == 0:
                score *= 1.5
            scores.append((score, i, sentence))

        scores.sort(reverse=True)
        num_sentences = max(1, int(len(sentences) * self.ratio))
        selected = sorted(scores[:num_sentences], key=lambda x: x[1])
        summary = ". ".join(s[2] for s in selected) + "."

        self.log.append({"original_length": len(text), "summary_length": len(summary)})
        return summary


# ============================================================
# Algorithm 121: AI Personalization
# ============================================================

class AIPersonalization:
    """Personalization engine using user profile vectors."""

    def __init__(self, dim=32):
        self.dim = dim
        self.user_vectors = {}
        self.item_vectors = {}

    def update_user(self, user_id, interactions):
        """Update user vector from interactions."""
        vector = [0.0] * self.dim
        for item_id, weight in interactions:
            item_vec = self.item_vectors.get(item_id, [random.gauss(0, 1) for _ in range(self.dim)])
            for d in range(self.dim):
                vector[d] += item_vec[d] * weight
        # Normalize
        norm = math.sqrt(sum(v * v for v in vector))
        if norm > 0:
            vector = [v / norm for v in vector]
        self.user_vectors[user_id] = vector

    def add_item(self, item_id, vector=None):
        self.item_vectors[item_id] = vector or [random.gauss(0, 1) for _ in range(self.dim)]

    def recommend(self, user_id, top_k=5):
        user_vec = self.user_vectors.get(user_id)
        if not user_vec:
            return []
        scores = []
        for item_id, item_vec in self.item_vectors.items():
            sim = sum(a * b for a, b in zip(user_vec, item_vec))
            scores.append((item_id, sim))
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:top_k]


# ============================================================
# Algorithm 122: AI Prediction
# ============================================================

class AIPrediction:
    """ML prediction model (simple linear regression)."""

    def __init__(self):
        self.weights = None
        self.bias = 0
        self.log = []

    def fit(self, X, y, lr=0.01, epochs=100):
        """Train the model."""
        n_features = len(X[0]) if X else 0
        self.weights = [0.0] * n_features
        self.bias = 0.0

        for _ in range(epochs):
            for xi, yi in zip(X, y):
                pred = sum(w * x for w, x in zip(self.weights, xi)) + self.bias
                error = pred - yi
                for j in range(n_features):
                    self.weights[j] -= lr * error * xi[j]
                self.bias -= lr * error

    def predict(self, X):
        """Make predictions."""
        predictions = []
        for xi in X:
            pred = sum(w * x for w, x in zip(self.weights, xi)) + self.bias
            predictions.append(pred)
            self.log.append({"input": xi, "prediction": pred})
        return predictions


# ============================================================
# Algorithm 123: AI Clustering
# ============================================================

class AIClustering:
    """K-Means clustering algorithm."""

    def __init__(self, k=3, max_iter=100):
        self.k = k
        self.max_iter = max_iter
        self.centroids = []
        self.labels = []

    def fit(self, data):
        """Fit K-Means clustering."""
        if not data:
            return

        # Initialize centroids randomly
        self.centroids = random.sample(data, min(self.k, len(data)))
        dim = len(data[0])

        for _ in range(self.max_iter):
            # Assign labels
            self.labels = [self._nearest_centroid(point) for point in data]

            # Update centroids
            new_centroids = []
            for c in range(self.k):
                members = [data[i] for i in range(len(data)) if self.labels[i] == c]
                if members:
                    centroid = [sum(m[d] for m in members) / len(members) for d in range(dim)]
                    new_centroids.append(centroid)
                else:
                    new_centroids.append(self.centroids[c])

            if new_centroids == self.centroids:
                break
            self.centroids = new_centroids

    def _nearest_centroid(self, point):
        distances = [
            sum((p - c) ** 2 for p, c in zip(point, centroid))
            for centroid in self.centroids
        ]
        return distances.index(min(distances))

    def predict(self, points):
        return [self._nearest_centroid(p) for p in points]


# ============================================================
# Algorithm 124: AI Classification
# ============================================================

class AIClassification:
    """Simple Naive Bayes classifier."""

    def __init__(self):
        self.class_priors = {}
        self.feature_probs = defaultdict(lambda: defaultdict(float))
        self.classes = set()
        self.log = []

    def fit(self, X, y):
        """Train classifier."""
        n = len(y)
        class_counts = defaultdict(int)
        for label in y:
            class_counts[label] += 1
            self.classes.add(label)

        for c in self.classes:
            self.class_priors[c] = class_counts[c] / n

        for xi, yi in zip(X, y):
            for j, val in enumerate(xi):
                self.feature_probs[(yi, j)][val] += 1

        for key in self.feature_probs:
            total = sum(self.feature_probs[key].values())
            for val in self.feature_probs[key]:
                self.feature_probs[key][val] /= total

    def predict(self, X):
        predictions = []
        for xi in X:
            best_class = None
            best_score = float('-inf')
            for c in self.classes:
                score = math.log(self.class_priors.get(c, 1e-10))
                for j, val in enumerate(xi):
                    prob = self.feature_probs[(c, j)].get(val, 1e-10)
                    score += math.log(prob)
                if score > best_score:
                    best_score = score
                    best_class = c
            predictions.append(best_class)
            self.log.append({"input": xi, "label": best_class})
        return predictions


# ============================================================
# Algorithm 125: AI Regression
# ============================================================

class AIRegression:
    """Gradient descent regression model."""

    def __init__(self):
        self.weights = None
        self.bias = 0
        self.training_log = []

    def fit(self, X, y, lr=0.001, epochs=200):
        n_features = len(X[0])
        self.weights = [0.0] * n_features
        self.bias = 0.0

        for epoch in range(epochs):
            total_loss = 0
            for xi, yi in zip(X, y):
                pred = sum(w * x for w, x in zip(self.weights, xi)) + self.bias
                error = pred - yi
                total_loss += error ** 2
                for j in range(n_features):
                    self.weights[j] -= lr * error * xi[j] / len(X)
                self.bias -= lr * error / len(X)

            if epoch % 50 == 0:
                self.training_log.append({"epoch": epoch, "loss": total_loss / len(X)})

    def predict(self, X):
        return [sum(w * x for w, x in zip(self.weights, xi)) + self.bias for xi in X]


# ============================================================
# Algorithm 126: AI Embedding
# ============================================================

class AIEmbedding:
    """Embedding model for converting inputs to vectors."""

    def __init__(self, vocab_size=10000, dim=64):
        self.dim = dim
        self.embeddings = {}
        self.vocab_size = vocab_size

    def encode(self, text):
        """Encode text to a vector."""
        if text in self.embeddings:
            return self.embeddings[text]

        # Hash-based embedding
        vector = []
        for d in range(self.dim):
            h = hash(f"{text}_{d}") % 10000 / 10000.0
            vector.append(h * 2 - 1)

        # Normalize
        norm = math.sqrt(sum(v * v for v in vector))
        if norm > 0:
            vector = [v / norm for v in vector]

        self.embeddings[text] = vector
        return vector

    def similarity(self, text_a, text_b):
        vec_a = self.encode(text_a)
        vec_b = self.encode(text_b)
        return sum(a * b for a, b in zip(vec_a, vec_b))


# ============================================================
# Algorithm 127: AI Ranking
# ============================================================

class AIRanking:
    """Learning-to-rank model."""

    def __init__(self):
        self.feature_weights = {}
        self.log = []

    def set_weights(self, weights):
        self.feature_weights = weights

    def score(self, item_features):
        score = sum(
            self.feature_weights.get(f, 0) * v
            for f, v in item_features.items()
        )
        return score

    def rank(self, items):
        """Rank items by score."""
        scored = [(item_id, self.score(features)) for item_id, features in items]
        scored.sort(key=lambda x: x[1], reverse=True)
        self.log.append({"ranked_count": len(scored)})
        return scored


# ============================================================
# Algorithm 128: AI Matching
# ============================================================

class AIMatching:
    """Vector-based matching system."""

    def __init__(self, dim=32):
        self.dim = dim
        self.entities = {}

    def add_entity(self, entity_id, vector):
        self.entities[entity_id] = vector

    def find_matches(self, query_vector, top_k=5, exclude=None):
        exclude = exclude or set()
        scores = []
        for eid, vec in self.entities.items():
            if eid in exclude:
                continue
            sim = sum(a * b for a, b in zip(query_vector, vec))
            scores.append((eid, sim))
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:top_k]


# ============================================================
# Algorithm 129: AI Optimization
# ============================================================

class AIOptimization:
    """Gradient-based parameter optimization."""

    def __init__(self, lr=0.01, max_iter=1000, tolerance=1e-6):
        self.lr = lr
        self.max_iter = max_iter
        self.tolerance = tolerance
        self.log = []

    def minimize(self, objective_fn, gradient_fn, initial_params):
        """Minimize an objective function."""
        params = list(initial_params)

        for i in range(self.max_iter):
            loss = objective_fn(params)
            grads = gradient_fn(params)

            new_params = [p - self.lr * g for p, g in zip(params, grads)]

            if all(abs(n - p) < self.tolerance for n, p in zip(new_params, params)):
                self.log.append({"iteration": i, "loss": loss, "converged": True})
                return new_params

            params = new_params

            if i % 100 == 0:
                self.log.append({"iteration": i, "loss": loss, "converged": False})

        return params


# ============================================================
# Algorithm 130: AI Reinforcement
# ============================================================

class AIReinforcement:
    """Q-learning reinforcement learning agent."""

    def __init__(self, n_states, n_actions, lr=0.1, gamma=0.99, epsilon=0.1):
        self.n_states = n_states
        self.n_actions = n_actions
        self.lr = lr
        self.gamma = gamma
        self.epsilon = epsilon
        self.q_table = [[0.0] * n_actions for _ in range(n_states)]
        self.log = []

    def choose_action(self, state):
        if random.random() < self.epsilon:
            return random.randint(0, self.n_actions - 1)
        return self.q_table[state].index(max(self.q_table[state]))

    def update(self, state, action, reward, next_state):
        best_next = max(self.q_table[next_state])
        td_target = reward + self.gamma * best_next
        td_error = td_target - self.q_table[state][action]
        self.q_table[state][action] += self.lr * td_error

        self.log.append({
            "state": state, "action": action,
            "reward": reward, "td_error": td_error,
        })

    def get_policy(self):
        return [q.index(max(q)) for q in self.q_table]


# ============================================================
# Algorithm 131: AI Anomaly Detection
# ============================================================

class AIAnomalyDetection:
    """Statistical and model-based anomaly detection."""

    def __init__(self, contamination=0.05):
        self.contamination = contamination
        self.mean = None
        self.std = None
        self.threshold = None
        self.log = []

    def fit(self, data):
        """Fit the anomaly detector on normal data."""
        if not data:
            return

        if isinstance(data[0], (list, tuple)):
            # Multivariate
            dim = len(data[0])
            self.mean = [sum(d[i] for d in data) / len(data) for i in range(dim)]
            self.std = [
                math.sqrt(sum((d[i] - self.mean[i]) ** 2 for d in data) / len(data))
                for i in range(dim)
            ]
        else:
            # Univariate
            self.mean = sum(data) / len(data)
            self.std = math.sqrt(sum((d - self.mean) ** 2 for d in data) / len(data))

        # Set threshold based on contamination ratio
        scores = [self._score(d) for d in data]
        scores.sort(reverse=True)
        idx = max(0, int(len(scores) * self.contamination) - 1)
        self.threshold = scores[idx] if idx < len(scores) else float('inf')

    def _score(self, point):
        """Compute anomaly score (Mahalanobis-like distance)."""
        if isinstance(point, (list, tuple)):
            return math.sqrt(sum(
                ((p - m) / max(s, 1e-10)) ** 2
                for p, m, s in zip(point, self.mean, self.std)
            ))
        else:
            return abs(point - self.mean) / max(self.std, 1e-10)

    def predict(self, data):
        """Predict anomalies. Returns list of (is_anomaly, score)."""
        results = []
        for point in data:
            score = self._score(point)
            is_anomaly = score > self.threshold if self.threshold else False
            results.append((is_anomaly, score))
            self.log.append({"point": point, "score": score, "anomaly": is_anomaly})
        return results


# ============================================================
# Main demonstration
# ============================================================

if __name__ == "__main__":
    # 116: AI Chatbot
    chatbot = AIChatbot()
    response, intent = chatbot.respond("Hello, I need help!")
    print(f"116 Chatbot: '{response}' (intent={intent})")

    # 117: AI Vision
    vision = AIVision()
    result = vision.classify(b"test_image_data")
    print(f"117 Vision: {result['label']} ({result['confidence']:.2f})")

    # 118: AI Speech
    speech = AISpeech()
    result = speech.transcribe(b"audio_data_sample")
    print(f"118 Speech: '{result['text']}' (conf={result['confidence']:.2f})")

    # 119: AI Translation
    translator = AITranslation()
    result = translator.translate("Hello world", "en", "es")
    print(f"119 Translation: {result['translated']}")

    # 120: AI Summarization
    summarizer = AISummarization()
    text = "Machine learning is a subset of AI. It uses data to learn patterns. Deep learning is a branch of ML. Neural networks are fundamental to deep learning. Applications include vision and NLP."
    summary = summarizer.summarize(text)
    print(f"120 Summary: {summary[:80]}...")

    # 121: AI Personalization
    perso = AIPersonalization()
    for i in range(10):
        perso.add_item(f"item-{i}")
    perso.update_user("user1", [("item-0", 5), ("item-3", 3)])
    recs = perso.recommend("user1", top_k=3)
    print(f"121 Personalization: {recs}")

    # 122: AI Prediction
    predictor = AIPrediction()
    X = [[1, 2], [2, 3], [3, 4], [4, 5]]
    y = [3, 5, 7, 9]
    predictor.fit(X, y)
    preds = predictor.predict([[5, 6]])
    print(f"122 Prediction: {preds[0]:.2f}")

    # 123: AI Clustering
    clustering = AIClustering(k=2)
    data = [[1, 1], [1.5, 2], [2, 1], [8, 8], [9, 9], [8.5, 9]]
    clustering.fit(data)
    print(f"123 Clustering: labels={clustering.labels}")

    # 124: AI Classification
    classifier = AIClassification()
    X = [["sunny", "hot"], ["rainy", "cool"], ["sunny", "warm"], ["rainy", "cold"]]
    y = ["no", "yes", "no", "yes"]
    classifier.fit(X, y)
    pred = classifier.predict([["sunny", "cool"]])
    print(f"124 Classification: {pred}")

    # 125: AI Regression
    regressor = AIRegression()
    X = [[1], [2], [3], [4], [5]]
    y = [2, 4, 6, 8, 10]
    regressor.fit(X, y)
    pred = regressor.predict([[6]])
    print(f"125 Regression: {pred[0]:.2f}")

    # 126: AI Embedding
    embedder = AIEmbedding()
    sim = embedder.similarity("machine learning", "deep learning")
    print(f"126 Embedding similarity: {sim:.3f}")

    # 127: AI Ranking
    ranker = AIRanking()
    ranker.set_weights({"relevance": 2.0, "freshness": 1.0, "popularity": 0.5})
    items = [
        ("a", {"relevance": 0.9, "freshness": 0.5, "popularity": 0.8}),
        ("b", {"relevance": 0.7, "freshness": 0.9, "popularity": 0.3}),
        ("c", {"relevance": 0.8, "freshness": 0.7, "popularity": 0.9}),
    ]
    ranked = ranker.rank(items)
    print(f"127 Ranking: {[(item, f'{score:.2f}') for item, score in ranked]}")

    # 128: AI Matching
    matcher = AIMatching(dim=3)
    matcher.add_entity("a", [1.0, 0.5, 0.2])
    matcher.add_entity("b", [0.1, 0.9, 0.3])
    matcher.add_entity("c", [0.9, 0.4, 0.1])
    matches = matcher.find_matches([1.0, 0.5, 0.2], top_k=2)
    print(f"128 Matching: {matches}")

    # 129: AI Optimization
    optimizer = AIOptimization(lr=0.1, max_iter=1000)
    result = optimizer.minimize(
        lambda p: (p[0] - 3) ** 2 + (p[1] - 5) ** 2,
        lambda p: [2 * (p[0] - 3), 2 * (p[1] - 5)],
        [0.0, 0.0],
    )
    print(f"129 Optimization: [{result[0]:.3f}, {result[1]:.3f}]")

    # 130: AI Reinforcement
    agent = AIReinforcement(n_states=5, n_actions=3)
    for _ in range(100):
        state = random.randint(0, 4)
        action = agent.choose_action(state)
        reward = 1.0 if action == state % 3 else -0.5
        next_state = (state + 1) % 5
        agent.update(state, action, reward, next_state)
    print(f"130 RL Policy: {agent.get_policy()}")

    # 131: AI Anomaly Detection
    detector = AIAnomalyDetection(contamination=0.1)
    normal_data = [random.gauss(50, 5) for _ in range(100)]
    detector.fit(normal_data)
    test_data = [50, 52, 48, 100, 51, -10]
    results = detector.predict(test_data)
    anomalies = [(test_data[i], r[1]) for i, r in enumerate(results) if r[0]]
    print(f"131 Anomalies: {anomalies}")
