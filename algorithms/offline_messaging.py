"""
Algorithm 82: Offline Messaging

- Message stored in DB
- Recipient offline flag set
- Fast push when online
- Retry mechanism
- Delivery confirmation
"""

import time
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict


class DeliveryStatus(Enum):
    PENDING = "pending"
    DELIVERED = "delivered"
    READ = "read"
    FAILED = "failed"


@dataclass
class Message:
    """A message in the offline messaging system."""
    message_id: str
    sender_id: str
    recipient_id: str
    content: str
    timestamp: float = field(default_factory=time.time)
    status: DeliveryStatus = DeliveryStatus.PENDING
    retry_count: int = 0
    max_retries: int = 3


@dataclass
class DeliveryReceipt:
    """Confirmation of message delivery."""
    message_id: str
    recipient_id: str
    status: DeliveryStatus
    delivered_at: float = field(default_factory=time.time)


class MessageStore:
    """Database for message persistence."""

    def __init__(self):
        self.messages = {}
        self.user_inbox = defaultdict(list)

    def store(self, message):
        """Store a message in the database."""
        self.messages[message.message_id] = message
        self.user_inbox[message.recipient_id].append(message.message_id)

    def get(self, message_id):
        return self.messages.get(message_id)

    def get_pending(self, recipient_id):
        """Get all pending messages for a user."""
        pending = []
        for msg_id in self.user_inbox.get(recipient_id, []):
            msg = self.messages.get(msg_id)
            if msg and msg.status == DeliveryStatus.PENDING:
                pending.append(msg)
        return pending

    def update_status(self, message_id, status):
        """Update delivery status of a message."""
        if message_id in self.messages:
            self.messages[message_id].status = status


class UserPresenceTracker:
    """Track user online/offline status."""

    def __init__(self):
        self.online_users = set()
        self.last_seen = {}

    def set_online(self, user_id):
        self.online_users.add(user_id)
        self.last_seen[user_id] = time.time()

    def set_offline(self, user_id):
        self.online_users.discard(user_id)
        self.last_seen[user_id] = time.time()

    def is_online(self, user_id):
        return user_id in self.online_users

    def get_last_seen(self, user_id):
        return self.last_seen.get(user_id, 0)


class OfflineMessagingService:
    """Complete offline messaging system with retry and delivery confirmation."""

    def __init__(self, max_retries=3):
        self.store = MessageStore()
        self.presence = UserPresenceTracker()
        self.max_retries = max_retries
        self.delivery_receipts = []
        self.push_log = []

    def send_message(self, message):
        """Send a message, storing it if recipient is offline."""
        message.max_retries = self.max_retries
        self.store.store(message)

        if self.presence.is_online(message.recipient_id):
            return self._push_message(message)
        else:
            return DeliveryReceipt(
                message_id=message.message_id,
                recipient_id=message.recipient_id,
                status=DeliveryStatus.PENDING,
            )

    def _push_message(self, message):
        """Push message to online recipient."""
        self.push_log.append({
            "message_id": message.message_id,
            "recipient_id": message.recipient_id,
            "pushed_at": time.time(),
        })
        self.store.update_status(message.message_id, DeliveryStatus.DELIVERED)

        receipt = DeliveryReceipt(
            message_id=message.message_id,
            recipient_id=message.recipient_id,
            status=DeliveryStatus.DELIVERED,
        )
        self.delivery_receipts.append(receipt)
        return receipt

    def user_comes_online(self, user_id):
        """Handle user coming online - deliver pending messages."""
        self.presence.set_online(user_id)
        pending = self.store.get_pending(user_id)
        receipts = []

        for message in pending:
            receipt = self._push_with_retry(message)
            receipts.append(receipt)

        return receipts

    def _push_with_retry(self, message):
        """Push with retry mechanism."""
        while message.retry_count < message.max_retries:
            try:
                receipt = self._push_message(message)
                return receipt
            except Exception:
                message.retry_count += 1
                if message.retry_count >= message.max_retries:
                    self.store.update_status(
                        message.message_id, DeliveryStatus.FAILED
                    )
                    return DeliveryReceipt(
                        message_id=message.message_id,
                        recipient_id=message.recipient_id,
                        status=DeliveryStatus.FAILED,
                    )

        return self._push_message(message)

    def confirm_read(self, message_id):
        """Confirm that a message has been read."""
        self.store.update_status(message_id, DeliveryStatus.READ)
        return DeliveryReceipt(
            message_id=message_id,
            recipient_id="",
            status=DeliveryStatus.READ,
        )

    def user_goes_offline(self, user_id):
        """Handle user going offline."""
        self.presence.set_offline(user_id)


if __name__ == "__main__":
    service = OfflineMessagingService()

    # User B is offline
    service.presence.set_offline("userB")

    # User A sends messages to offline User B
    msg1 = Message(
        message_id="m1", sender_id="userA",
        recipient_id="userB", content="Hello!"
    )
    msg2 = Message(
        message_id="m2", sender_id="userA",
        recipient_id="userB", content="Are you there?"
    )

    r1 = service.send_message(msg1)
    r2 = service.send_message(msg2)
    print(f"Message 1 status: {r1.status.value}")
    print(f"Message 2 status: {r2.status.value}")

    # User B comes online - pending messages delivered
    receipts = service.user_comes_online("userB")
    print(f"\nUser B online - delivered {len(receipts)} messages:")
    for r in receipts:
        print(f"  {r.message_id}: {r.status.value}")

    # User B reads message
    read_receipt = service.confirm_read("m1")
    print(f"\nMessage m1 read confirmation: {read_receipt.status.value}")
