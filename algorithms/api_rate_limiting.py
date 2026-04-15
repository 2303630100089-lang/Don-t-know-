"""
Algorithm 89: API Rate Limiting

- Request counter per user
- Fast check via Redis
- Threshold enforcement
- Retry after cooldown
- Prevent abuse
"""

import time
from dataclasses import dataclass, field
from collections import defaultdict
from enum import Enum


class RateLimitResult(Enum):
    ALLOWED = "allowed"
    LIMITED = "limited"
    BLOCKED = "blocked"


@dataclass
class RateLimitResponse:
    """Response from the rate limiter."""
    result: RateLimitResult
    remaining: int
    limit: int
    retry_after: float = 0.0
    reset_at: float = 0.0


@dataclass
class RateLimitRule:
    """A rate limiting rule."""
    name: str
    max_requests: int
    window_seconds: float
    block_duration: float = 0.0  # additional block time after limit hit


class TokenBucketLimiter:
    """Token bucket rate limiter."""

    def __init__(self, max_tokens, refill_rate):
        self.max_tokens = max_tokens
        self.refill_rate = refill_rate  # tokens per second
        self.buckets = {}

    def _get_bucket(self, key):
        now = time.time()
        if key not in self.buckets:
            self.buckets[key] = {"tokens": self.max_tokens, "last_refill": now}

        bucket = self.buckets[key]
        elapsed = now - bucket["last_refill"]
        refill = elapsed * self.refill_rate
        bucket["tokens"] = min(self.max_tokens, bucket["tokens"] + refill)
        bucket["last_refill"] = now
        return bucket

    def allow(self, key, tokens=1):
        """Check if request is allowed and consume tokens."""
        bucket = self._get_bucket(key)
        if bucket["tokens"] >= tokens:
            bucket["tokens"] -= tokens
            return True, bucket["tokens"]
        return False, bucket["tokens"]


class SlidingWindowLimiter:
    """Sliding window rate limiter."""

    def __init__(self, max_requests, window_seconds):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.windows = defaultdict(list)

    def allow(self, key):
        """Check if request is allowed within the sliding window."""
        now = time.time()
        window_start = now - self.window_seconds

        # Remove expired entries
        self.windows[key] = [
            ts for ts in self.windows[key] if ts > window_start
        ]

        count = len(self.windows[key])
        if count < self.max_requests:
            self.windows[key].append(now)
            remaining = self.max_requests - count - 1
            return True, remaining
        else:
            oldest = self.windows[key][0] if self.windows[key] else now
            retry_after = oldest + self.window_seconds - now
            return False, retry_after


class RateLimiter:
    """
    Comprehensive rate limiter with multiple strategies,
    per-user tracking, and abuse prevention.
    """

    def __init__(self):
        self.rules = {}
        self.limiters = {}
        self.blocked_users = {}  # user_id -> unblock_time
        self.abuse_counters = defaultdict(int)
        self.abuse_threshold = 10  # consecutive limit hits before block

    def add_rule(self, rule, strategy="sliding_window"):
        """Add a rate limiting rule."""
        self.rules[rule.name] = rule
        if strategy == "token_bucket":
            self.limiters[rule.name] = TokenBucketLimiter(
                rule.max_requests,
                rule.max_requests / rule.window_seconds,
            )
        else:
            self.limiters[rule.name] = SlidingWindowLimiter(
                rule.max_requests,
                rule.window_seconds,
            )

    def check(self, user_id, rule_name="default"):
        """Check if a request from user is allowed."""
        # Check if user is blocked
        if user_id in self.blocked_users:
            if time.time() < self.blocked_users[user_id]:
                retry_after = self.blocked_users[user_id] - time.time()
                return RateLimitResponse(
                    result=RateLimitResult.BLOCKED,
                    remaining=0,
                    limit=0,
                    retry_after=retry_after,
                )
            else:
                del self.blocked_users[user_id]
                self.abuse_counters[user_id] = 0

        if rule_name not in self.limiters:
            return RateLimitResponse(
                result=RateLimitResult.ALLOWED,
                remaining=-1,
                limit=-1,
            )

        rule = self.rules[rule_name]
        limiter = self.limiters[rule_name]
        key = f"{user_id}:{rule_name}"

        if isinstance(limiter, TokenBucketLimiter):
            allowed, remaining = limiter.allow(key)
            if allowed:
                self.abuse_counters[user_id] = 0
                return RateLimitResponse(
                    result=RateLimitResult.ALLOWED,
                    remaining=int(remaining),
                    limit=rule.max_requests,
                )
            else:
                return self._handle_limited(user_id, rule, remaining)
        else:
            allowed, value = limiter.allow(key)
            if allowed:
                self.abuse_counters[user_id] = 0
                return RateLimitResponse(
                    result=RateLimitResult.ALLOWED,
                    remaining=int(value),
                    limit=rule.max_requests,
                )
            else:
                return self._handle_limited(user_id, rule, value)

    def _handle_limited(self, user_id, rule, retry_or_remaining):
        """Handle a rate-limited request."""
        self.abuse_counters[user_id] += 1

        if self.abuse_counters[user_id] >= self.abuse_threshold:
            block_duration = max(rule.block_duration, 60)
            self.blocked_users[user_id] = time.time() + block_duration
            return RateLimitResponse(
                result=RateLimitResult.BLOCKED,
                remaining=0,
                limit=rule.max_requests,
                retry_after=block_duration,
            )

        retry_after = max(0, retry_or_remaining if isinstance(retry_or_remaining, float) else rule.window_seconds)
        return RateLimitResponse(
            result=RateLimitResult.LIMITED,
            remaining=0,
            limit=rule.max_requests,
            retry_after=retry_after,
            reset_at=time.time() + retry_after,
        )


if __name__ == "__main__":
    limiter = RateLimiter()

    # Add rate limiting rules
    limiter.add_rule(RateLimitRule(
        name="api",
        max_requests=5,
        window_seconds=10.0,
        block_duration=30.0,
    ))

    # Simulate requests
    user = "user-1"
    for i in range(8):
        response = limiter.check(user, "api")
        print(f"Request {i+1}: {response.result.value} "
              f"(remaining={response.remaining}, "
              f"retry_after={response.retry_after:.1f}s)")
