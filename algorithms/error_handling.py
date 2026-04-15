"""
Algorithm 93: Error Handling

- Exception caught
- Fast retry
- Logged in monitoring
- User notified gracefully
- Root cause analysis
"""

import time
import traceback
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict
from functools import wraps


class ErrorSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ErrorEvent:
    """A recorded error event."""
    error_id: str
    error_type: str
    message: str
    severity: ErrorSeverity
    stack_trace: str = ""
    context: dict = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    retry_count: int = 0
    resolved: bool = False


@dataclass
class UserNotification:
    """A user-friendly error notification."""
    code: str
    message: str
    retry_available: bool = True
    support_link: str = ""


class RetryPolicy:
    """Configurable retry policy with exponential backoff."""

    def __init__(self, max_retries=3, base_delay=0.1, max_delay=10.0,
                 backoff_factor=2.0, retryable_exceptions=None):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.backoff_factor = backoff_factor
        self.retryable_exceptions = retryable_exceptions or (Exception,)

    def get_delay(self, attempt):
        """Calculate delay for a retry attempt."""
        delay = self.base_delay * (self.backoff_factor ** attempt)
        return min(delay, self.max_delay)

    def should_retry(self, exception, attempt):
        """Check if we should retry for this exception."""
        if attempt >= self.max_retries:
            return False
        return isinstance(exception, self.retryable_exceptions)


class ErrorMonitor:
    """Monitor and track errors for root cause analysis."""

    def __init__(self):
        self.errors = []
        self.error_counts = defaultdict(int)
        self.error_timeline = defaultdict(list)

    def log(self, error_event):
        """Log an error event."""
        self.errors.append(error_event)
        self.error_counts[error_event.error_type] += 1
        self.error_timeline[error_event.error_type].append(error_event.timestamp)

    def get_error_rate(self, error_type=None, window_seconds=300):
        """Get error rate within a time window."""
        now = time.time()
        cutoff = now - window_seconds

        if error_type:
            recent = [
                ts for ts in self.error_timeline[error_type] if ts > cutoff
            ]
            return len(recent) / window_seconds
        else:
            total = sum(
                1 for e in self.errors if e.timestamp > cutoff
            )
            return total / window_seconds

    def analyze_root_cause(self, error_type=None):
        """Perform root cause analysis on errors."""
        if error_type:
            errors = [e for e in self.errors if e.type == error_type]
        else:
            errors = self.errors

        if not errors:
            return {"analysis": "No errors found", "patterns": []}

        # Group by error type
        type_groups = defaultdict(list)
        for e in errors:
            type_groups[e.error_type].append(e)

        patterns = []
        for etype, group in type_groups.items():
            pattern = {
                "error_type": etype,
                "count": len(group),
                "first_seen": min(e.timestamp for e in group),
                "last_seen": max(e.timestamp for e in group),
                "severity_distribution": defaultdict(int),
            }
            for e in group:
                pattern["severity_distribution"][e.severity.value] += 1
            patterns.append(pattern)

        patterns.sort(key=lambda p: p["count"], reverse=True)

        return {
            "analysis": f"Found {len(patterns)} error patterns",
            "total_errors": len(errors),
            "patterns": patterns,
        }


class ErrorHandler:
    """
    Comprehensive error handling with retry, monitoring,
    and graceful user notification.
    """

    def __init__(self, retry_policy=None):
        self.retry_policy = retry_policy or RetryPolicy()
        self.monitor = ErrorMonitor()
        self.notifications = []
        self._error_counter = 0

        # User-friendly error messages
        self.error_messages = {
            "ConnectionError": UserNotification(
                "CONN_ERR", "Unable to connect to the service. Please try again.",
                retry_available=True,
            ),
            "TimeoutError": UserNotification(
                "TIMEOUT", "The request timed out. Please try again later.",
                retry_available=True,
            ),
            "ValueError": UserNotification(
                "INVALID_INPUT", "Invalid input provided. Please check and try again.",
                retry_available=False,
            ),
            "PermissionError": UserNotification(
                "ACCESS_DENIED", "You don't have permission to perform this action.",
                retry_available=False,
            ),
        }
        self.default_notification = UserNotification(
            "UNKNOWN", "An unexpected error occurred. Our team has been notified.",
            retry_available=False,
        )

    def handle(self, func, *args, **kwargs):
        """Execute a function with error handling and retry."""
        last_exception = None

        for attempt in range(self.retry_policy.max_retries + 1):
            try:
                result = func(*args, **kwargs)
                return result, None
            except Exception as exc:
                last_exception = exc
                self._error_counter += 1

                severity = self._classify_severity(exc, attempt)
                error_event = ErrorEvent(
                    error_id=f"err-{self._error_counter}",
                    error_type=type(exc).__name__,
                    message=str(exc),
                    severity=severity,
                    stack_trace=traceback.format_exc(),
                    context={"attempt": attempt, "args": str(args)[:200]},
                    retry_count=attempt,
                )
                self.monitor.log(error_event)

                if self.retry_policy.should_retry(exc, attempt):
                    delay = self.retry_policy.get_delay(attempt)
                    time.sleep(delay)
                    continue
                else:
                    break

        notification = self._get_user_notification(last_exception)
        self.notifications.append(notification)
        return None, notification

    def _classify_severity(self, exception, attempt):
        """Classify error severity."""
        if isinstance(exception, (ConnectionError, TimeoutError)):
            if attempt >= 2:
                return ErrorSeverity.HIGH
            return ErrorSeverity.MEDIUM
        elif isinstance(exception, (ValueError, TypeError)):
            return ErrorSeverity.LOW
        elif isinstance(exception, PermissionError):
            return ErrorSeverity.HIGH
        return ErrorSeverity.MEDIUM

    def _get_user_notification(self, exception):
        """Get user-friendly notification for an error."""
        error_type = type(exception).__name__
        return self.error_messages.get(error_type, self.default_notification)

    def with_retry(self, func):
        """Decorator for adding retry behavior to a function."""
        @wraps(func)
        def wrapper(*args, **kwargs):
            return self.handle(func, *args, **kwargs)
        return wrapper


if __name__ == "__main__":
    handler = ErrorHandler(
        retry_policy=RetryPolicy(max_retries=3, base_delay=0.01)
    )

    # Simulate a flaky function
    call_count = 0

    def flaky_function(x):
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise ConnectionError("Connection refused")
        return x * 2

    result, error = handler.handle(flaky_function, 5)
    print(f"Result: {result}, Error: {error}")
    print(f"Function called {call_count} times")

    # Simulate a permanent failure
    def failing_function():
        raise ValueError("Invalid input data")

    result, notification = handler.handle(failing_function)
    print(f"\nPermanent failure:")
    print(f"  Code: {notification.code}")
    print(f"  Message: {notification.message}")
    print(f"  Retry: {notification.retry_available}")

    # Root cause analysis
    analysis = handler.monitor.analyze_root_cause()
    print(f"\nRoot cause analysis: {analysis['analysis']}")
    for pattern in analysis["patterns"]:
        print(f"  {pattern['error_type']}: {pattern['count']} occurrences")
