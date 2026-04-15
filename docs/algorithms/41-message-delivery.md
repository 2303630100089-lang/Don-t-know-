# 41. Algorithm: Message Delivery

## Overview

Reliable message delivery algorithm ensuring messages reach recipients whether online or offline, with WebSocket push for real-time delivery and exponential backoff retry for failed attempts.

## Algorithm Steps

### Step 1: Input → Queue
- Message created by sender and published to message queue (Kafka/RabbitMQ).
- Message includes: sender_id, recipient_id, content, timestamp, message_id.
- Queue ensures durability and ordering guarantees.

### Step 2: Queue → Delivery Service
- Delivery service consumes messages from the queue.
- Validates message format and permissions.
- Enriches message with metadata (read receipts, encryption keys).

### Step 3: Check Recipient Status
- Query presence service for recipient's online/offline status.
- Presence service backed by Redis with TTL-based session tracking.
- Status categories: Online, Away, Offline, Do Not Disturb.

### Step 4a: If Online → Push via WebSocket
- Route message through WebSocket connection to recipient's active session.
- Acknowledge delivery to sender.
- Store message in conversation history.
- Update read receipt status.

### Step 4b: If Offline → Store + Notify Later
- Store message in persistent database (undelivered messages table).
- Queue push notification via APNs/FCM.
- Mark message for delivery on next login.
- Badge count updated on device.

### Step 5: Retry with Exponential Backoff
- If WebSocket delivery fails, retry with exponential backoff.
- Retry schedule: 1s, 2s, 4s, 8s, 16s (with jitter).
- After max retries, fall back to offline delivery path.
- Log delivery failure for monitoring.

## Pseudocode

```
function deliverMessage(message):
    queue.publish(message)
    
    deliveryService.consume(queue):
        validate(message)
        status = presenceService.getStatus(message.recipient_id)
        
        if status == ONLINE:
            try:
                websocket.send(message.recipient_id, message)
                ack(message.sender_id, DELIVERED)
                db.storeMessage(message, status=DELIVERED)
            catch ConnectionError:
                retryWithBackoff(message, attempt=1)
        else:
            db.storeMessage(message, status=PENDING)
            pushNotification.send(message.recipient_id, message.preview)
    
function retryWithBackoff(message, attempt):
    if attempt > MAX_RETRIES:
        fallbackToOffline(message)
        return
    
    delay = (2 ^ attempt) + random_jitter()
    sleep(delay)
    
    try:
        websocket.send(message.recipient_id, message)
        ack(message.sender_id, DELIVERED)
    catch ConnectionError:
        retryWithBackoff(message, attempt + 1)
```

## Performance Targets

| Metric | Target |
|--------|--------|
| Online delivery latency | < 100ms |
| Offline notification | < 5 seconds |
| Queue throughput | > 100K msg/sec |
| Delivery success rate | > 99.9% |
| Retry max duration | < 31 seconds |
