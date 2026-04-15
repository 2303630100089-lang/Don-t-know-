"""
Algorithm 87: Queue Management

- Messages → queue
- Queue → consumer
- Fast acknowledgment
- Retry on failure
- Dead-letter queue
"""

import time
import threading
from dataclasses import dataclass, field
from enum import Enum
from collections import deque


class MessageStatus(Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    ACKNOWLEDGED = "acknowledged"
    FAILED = "failed"
    DEAD_LETTER = "dead_letter"


@dataclass
class QueueMessage:
    """A message in the queue."""
    message_id: str
    payload: dict
    status: MessageStatus = MessageStatus.QUEUED
    retry_count: int = 0
    max_retries: int = 3
    created_at: float = field(default_factory=time.time)
    processed_at: float = 0.0
    error: str = ""


class MessageQueue:
    """A message queue with acknowledgment, retry, and dead-letter support."""

    def __init__(self, name, max_retries=3):
        self.name = name
        self.max_retries = max_retries
        self.queue = deque()
        self.processing = {}
        self.acknowledged = {}
        self.dead_letter_queue = deque()
        self.lock = threading.Lock()
        self.stats = {
            "enqueued": 0,
            "processed": 0,
            "failed": 0,
            "dead_lettered": 0,
        }

    def enqueue(self, message_id, payload):
        """Add a message to the queue."""
        with self.lock:
            msg = QueueMessage(
                message_id=message_id,
                payload=payload,
                max_retries=self.max_retries,
            )
            self.queue.append(msg)
            self.stats["enqueued"] += 1
            return msg

    def dequeue(self):
        """Get the next message from the queue for processing."""
        with self.lock:
            if not self.queue:
                return None
            msg = self.queue.popleft()
            msg.status = MessageStatus.PROCESSING
            msg.processed_at = time.time()
            self.processing[msg.message_id] = msg
            return msg

    def acknowledge(self, message_id):
        """Acknowledge successful processing of a message."""
        with self.lock:
            if message_id in self.processing:
                msg = self.processing.pop(message_id)
                msg.status = MessageStatus.ACKNOWLEDGED
                self.acknowledged[message_id] = msg
                self.stats["processed"] += 1
                return True
            return False

    def reject(self, message_id, error=""):
        """Reject a message (will retry or move to dead-letter queue)."""
        with self.lock:
            if message_id not in self.processing:
                return False

            msg = self.processing.pop(message_id)
            msg.retry_count += 1
            msg.error = error

            if msg.retry_count >= msg.max_retries:
                msg.status = MessageStatus.DEAD_LETTER
                self.dead_letter_queue.append(msg)
                self.stats["dead_lettered"] += 1
                self.stats["failed"] += 1
            else:
                msg.status = MessageStatus.QUEUED
                self.queue.appendleft(msg)  # priority re-queue

            return True

    def peek(self):
        """Peek at the next message without removing it."""
        with self.lock:
            if self.queue:
                return self.queue[0]
            return None

    def size(self):
        """Get queue size."""
        return len(self.queue)

    def dead_letter_size(self):
        """Get dead-letter queue size."""
        return len(self.dead_letter_queue)

    def get_dead_letters(self):
        """Retrieve dead-letter messages."""
        return list(self.dead_letter_queue)

    def reprocess_dead_letters(self):
        """Move dead-letter messages back to main queue."""
        with self.lock:
            count = 0
            while self.dead_letter_queue:
                msg = self.dead_letter_queue.popleft()
                msg.status = MessageStatus.QUEUED
                msg.retry_count = 0
                msg.error = ""
                self.queue.append(msg)
                count += 1
            return count

    def get_stats(self):
        """Get queue statistics."""
        return {
            **self.stats,
            "queue_size": self.size(),
            "processing": len(self.processing),
            "dead_letter_size": self.dead_letter_size(),
        }


class Consumer:
    """A message consumer that processes messages from a queue."""

    def __init__(self, consumer_id, queue, handler=None):
        self.consumer_id = consumer_id
        self.queue = queue
        self.handler = handler or self._default_handler
        self.processed = 0
        self.failed = 0

    @staticmethod
    def _default_handler(message):
        """Default message handler."""
        return True

    def consume_one(self):
        """Consume and process one message."""
        msg = self.queue.dequeue()
        if msg is None:
            return None

        try:
            success = self.handler(msg)
            if success:
                self.queue.acknowledge(msg.message_id)
                self.processed += 1
            else:
                self.queue.reject(msg.message_id, "Handler returned False")
                self.failed += 1
        except Exception as e:
            self.queue.reject(msg.message_id, str(e))
            self.failed += 1

        return msg

    def consume_all(self):
        """Consume all available messages."""
        results = []
        while self.queue.size() > 0 or self.queue.processing:
            msg = self.consume_one()
            if msg is None:
                break
            results.append(msg)
        return results


if __name__ == "__main__":
    queue = MessageQueue("task-queue", max_retries=3)

    # Enqueue messages
    for i in range(10):
        queue.enqueue(f"msg-{i}", {"task": f"process_item_{i}"})

    print(f"Queue size: {queue.size()}")

    # Create consumer that fails on specific messages
    fail_ids = {"msg-2", "msg-5"}

    def handler(msg):
        if msg.message_id in fail_ids:
            raise ValueError(f"Failed to process {msg.message_id}")
        return True

    consumer = Consumer("consumer-1", queue, handler)
    results = consumer.consume_all()

    print(f"\nProcessed: {consumer.processed}")
    print(f"Failed: {consumer.failed}")
    print(f"Dead letters: {queue.dead_letter_size()}")

    stats = queue.get_stats()
    print(f"\nQueue stats: {stats}")
