"""
Algorithm 80: Spam Detection

- Message features extracted
- ML model scores spam probability
- Threshold check
- Fast quarantine
- User notified
"""

import math
import re
import time
from dataclasses import dataclass, field
from enum import Enum
from collections import Counter


class SpamVerdict(Enum):
    HAM = "ham"
    SPAM = "spam"
    QUARANTINED = "quarantined"


@dataclass
class SpamResult:
    """Result of spam detection."""
    message_id: str
    verdict: SpamVerdict
    spam_probability: float
    features: dict = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)


class FeatureExtractor:
    """Extract features from a message for spam classification."""

    def extract(self, message):
        """Extract features from message text."""
        features = {}

        features["length"] = len(message)
        features["word_count"] = len(message.split())

        upper_chars = sum(1 for c in message if c.isupper())
        features["caps_ratio"] = upper_chars / max(len(message), 1)

        features["exclamation_count"] = message.count("!")
        features["question_count"] = message.count("?")

        urls = re.findall(r'https?://\S+', message)
        features["url_count"] = len(urls)

        spam_words = [
            "free", "winner", "click", "subscribe", "offer",
            "deal", "discount", "limited", "urgent", "act now",
            "buy", "cheap", "earn", "cash", "prize",
        ]
        message_lower = message.lower()
        features["spam_word_count"] = sum(
            1 for word in spam_words if word in message_lower
        )

        features["special_char_ratio"] = sum(
            1 for c in message if not c.isalnum() and not c.isspace()
        ) / max(len(message), 1)

        features["digit_ratio"] = sum(
            1 for c in message if c.isdigit()
        ) / max(len(message), 1)

        words = message_lower.split()
        if words:
            word_counts = Counter(words)
            features["max_word_repeat"] = max(word_counts.values())
        else:
            features["max_word_repeat"] = 0

        return features


class SpamClassifier:
    """ML-based spam classifier using logistic regression-like scoring."""

    def __init__(self):
        self.weights = {
            "caps_ratio": 2.0,
            "exclamation_count": 0.3,
            "url_count": 1.5,
            "spam_word_count": 1.8,
            "special_char_ratio": 1.2,
            "digit_ratio": 0.8,
            "max_word_repeat": 0.5,
        }
        self.bias = -2.0

    @staticmethod
    def _sigmoid(x):
        x = max(min(x, 500), -500)
        return 1.0 / (1.0 + math.exp(-x))

    def predict(self, features):
        """Score spam probability."""
        score = self.bias
        for feature_name, weight in self.weights.items():
            value = features.get(feature_name, 0)
            score += weight * value
        return self._sigmoid(score)


class SpamDetector:
    """Complete spam detection pipeline."""

    def __init__(self, spam_threshold=0.7, quarantine_threshold=0.5):
        self.feature_extractor = FeatureExtractor()
        self.classifier = SpamClassifier()
        self.spam_threshold = spam_threshold
        self.quarantine_threshold = quarantine_threshold
        self.quarantine = []
        self.notifications = []

    def detect(self, message_id, message_text):
        """Detect if a message is spam."""
        features = self.feature_extractor.extract(message_text)

        spam_probability = self.classifier.predict(features)

        if spam_probability >= self.spam_threshold:
            verdict = SpamVerdict.SPAM
            self._quarantine_message(message_id, message_text)
            self._notify_user(message_id, "Message identified as spam.")
        elif spam_probability >= self.quarantine_threshold:
            verdict = SpamVerdict.QUARANTINED
            self._quarantine_message(message_id, message_text)
            self._notify_user(message_id, "Message quarantined for review.")
        else:
            verdict = SpamVerdict.HAM

        return SpamResult(
            message_id=message_id,
            verdict=verdict,
            spam_probability=spam_probability,
            features=features,
        )

    def _quarantine_message(self, message_id, message_text):
        """Fast quarantine of suspicious messages."""
        self.quarantine.append({
            "message_id": message_id,
            "text": message_text,
            "timestamp": time.time(),
        })

    def _notify_user(self, message_id, notification):
        """Notify user about spam action."""
        self.notifications.append({
            "message_id": message_id,
            "notification": notification,
            "timestamp": time.time(),
        })

    def get_quarantined(self):
        """Retrieve quarantined messages."""
        return list(self.quarantine)


if __name__ == "__main__":
    detector = SpamDetector()

    messages = [
        ("m1", "Hey, want to grab lunch tomorrow?"),
        ("m2", "FREE!!! Click here to WIN a PRIZE!!! Act now! Limited offer!!!"),
        ("m3", "Meeting at 3pm in conference room B."),
        ("m4", "Buy cheap products at https://spam.example.com discount!!!"),
    ]

    for msg_id, text in messages:
        result = detector.detect(msg_id, text)
        print(f"[{result.verdict.value:>12}] ({result.spam_probability:.3f}) {text[:60]}")

    print(f"\nQuarantined: {len(detector.get_quarantined())} messages")
