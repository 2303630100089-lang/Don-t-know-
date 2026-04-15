"""
Algorithm 79: Content Moderation

- Text → NLP classifier
- Image → CV model
- Video → frame sampling + CV
- Fast inference pipeline
- Flagged content logged
"""

import re
import time
import hashlib
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class ContentType(Enum):
    TEXT = "text"
    IMAGE = "image"
    VIDEO = "video"


class ModerationResult(Enum):
    SAFE = "safe"
    FLAGGED = "flagged"
    REVIEW = "needs_review"


@dataclass
class ModerationReport:
    """Result of content moderation."""
    content_id: str
    content_type: ContentType
    result: ModerationResult
    confidence: float
    categories: list = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)
    details: str = ""


class TextClassifier:
    """NLP-based text content classifier."""

    def __init__(self):
        self.blocked_patterns = [
            r'\b(spam|scam)\b',
            r'\b(abuse|threat)\b',
        ]
        self.suspicious_patterns = [
            r'\b(click here|free money|act now)\b',
            r'(.)\1{5,}',  # repeated characters
        ]

    def classify(self, text):
        """Classify text content for moderation."""
        text_lower = text.lower()
        categories = []
        max_score = 0.0

        for pattern in self.blocked_patterns:
            if re.search(pattern, text_lower):
                categories.append("blocked_content")
                max_score = max(max_score, 0.95)

        for pattern in self.suspicious_patterns:
            if re.search(pattern, text_lower):
                categories.append("suspicious_content")
                max_score = max(max_score, 0.6)

        if max_score >= 0.8:
            result = ModerationResult.FLAGGED
        elif max_score >= 0.5:
            result = ModerationResult.REVIEW
        else:
            result = ModerationResult.SAFE

        return result, max_score, categories


class ImageClassifier:
    """CV-based image content classifier (simulated)."""

    def classify(self, image_data):
        """Classify image content using a simulated CV model."""
        image_hash = hashlib.md5(
            image_data if isinstance(image_data, bytes)
            else image_data.encode()
        ).hexdigest()

        score = int(image_hash[:2], 16) / 255.0
        categories = []

        if score > 0.9:
            categories.append("explicit_content")
            return ModerationResult.FLAGGED, score, categories
        elif score > 0.7:
            categories.append("potentially_unsafe")
            return ModerationResult.REVIEW, score, categories
        else:
            return ModerationResult.SAFE, 1.0 - score, categories


class VideoModerator:
    """Video content moderation via frame sampling."""

    def __init__(self, image_classifier=None, sample_rate=1.0):
        self.image_classifier = image_classifier or ImageClassifier()
        self.sample_rate = sample_rate  # frames per second to sample

    def moderate(self, video_frames):
        """Moderate video by sampling frames."""
        results = []
        step = max(1, int(1.0 / self.sample_rate)) if self.sample_rate < 1 else 1

        for i in range(0, len(video_frames), step):
            frame = video_frames[i]
            result, confidence, categories = self.image_classifier.classify(frame)
            results.append((i, result, confidence, categories))

        worst_result = ModerationResult.SAFE
        max_confidence = 0.0
        all_categories = []

        for _, result, confidence, categories in results:
            all_categories.extend(categories)
            if result == ModerationResult.FLAGGED:
                worst_result = ModerationResult.FLAGGED
                max_confidence = max(max_confidence, confidence)
            elif result == ModerationResult.REVIEW and worst_result != ModerationResult.FLAGGED:
                worst_result = ModerationResult.REVIEW
                max_confidence = max(max_confidence, confidence)

        return worst_result, max_confidence, list(set(all_categories))


class ModerationPipeline:
    """Fast inference pipeline for content moderation."""

    def __init__(self):
        self.text_classifier = TextClassifier()
        self.image_classifier = ImageClassifier()
        self.video_moderator = VideoModerator(self.image_classifier)
        self.log = []

    def moderate(self, content_id, content_type, content, metadata=None):
        """Run content through the moderation pipeline."""
        if content_type == ContentType.TEXT:
            result, confidence, categories = self.text_classifier.classify(content)
        elif content_type == ContentType.IMAGE:
            result, confidence, categories = self.image_classifier.classify(content)
        elif content_type == ContentType.VIDEO:
            result, confidence, categories = self.video_moderator.moderate(content)
        else:
            raise ValueError(f"Unsupported content type: {content_type}")

        report = ModerationReport(
            content_id=content_id,
            content_type=content_type,
            result=result,
            confidence=confidence,
            categories=categories,
        )

        if result in (ModerationResult.FLAGGED, ModerationResult.REVIEW):
            self._log_flagged(report)

        return report

    def _log_flagged(self, report):
        """Log flagged content for review."""
        self.log.append(report)

    def get_flagged_log(self):
        """Retrieve all flagged content reports."""
        return list(self.log)


if __name__ == "__main__":
    pipeline = ModerationPipeline()

    text_report = pipeline.moderate("t1", ContentType.TEXT, "Hello, how are you?")
    print(f"Text moderation: {text_report.result.value} (confidence: {text_report.confidence:.2f})")

    spam_report = pipeline.moderate("t2", ContentType.TEXT, "Click here for free money! Act now!")
    print(f"Spam text: {spam_report.result.value} (confidence: {spam_report.confidence:.2f})")

    img_report = pipeline.moderate("i1", ContentType.IMAGE, b"sample_image_data")
    print(f"Image moderation: {img_report.result.value} (confidence: {img_report.confidence:.2f})")

    print(f"\nFlagged content count: {len(pipeline.get_flagged_log())}")
