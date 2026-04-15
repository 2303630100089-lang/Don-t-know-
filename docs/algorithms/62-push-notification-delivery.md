# 62. Algorithm: Push Notification Delivery

## Overview

Reliable push notification delivery algorithm routing messages through a notification service, queue, and platform-specific delivery channels (APNs/FCM) with retry and fast delivery confirmation.

## Algorithm Steps

### Step 1: Message → Notification Service
- Application event triggers notification (new message, order update, alert).
- Notification service receives event with payload, recipient, and priority.
- Template engine renders notification content (title, body, data payload).
- De-duplication check prevents repeated notifications.

### Step 2: Service → Queue
- Notification enqueued in priority queue (Kafka/SQS).
- Priority levels: Critical (0), High (1), Normal (2), Low (3).
- Critical notifications skip queue and deliver immediately.
- Queue ensures at-least-once delivery semantics.

### Step 3: Queue → APNs/FCM
- Consumer dequeues notification and routes to appropriate platform.
- **APNs**: HTTP/2 multiplexed connection to Apple servers.
- **FCM**: HTTP v1 API with OAuth 2.0 authentication.
- Platform-specific payload formatting applied.
- Connection pooling for high throughput.

### Step 4: Retry with Backoff
- Transient failures retried with exponential backoff.
- Schedule: 1s, 2s, 4s, 8s, 16s (with jitter).
- Permanent failures (invalid token) → mark device token for cleanup.
- Max retries: 5 attempts before moving to dead letter queue.
- Rate limiting per platform to respect APNs/FCM limits.

### Step 5: Fast Delivery Confirmation
- APNs/FCM returns delivery acknowledgment.
- Delivery status recorded: sent, delivered, failed, expired.
- Client-side delivery receipt sent back to server.
- Analytics updated with delivery metrics.
- Failed tokens queued for re-registration prompt.

## Pseudocode

```
function sendNotification(event):
    notification = {
        id: generateId(),
        recipient: event.user_id,
        title: renderTemplate(event.type, "title", event.data),
        body: renderTemplate(event.type, "body", event.data),
        data: event.payload,
        priority: event.priority or NORMAL,
        platform: getUserPlatform(event.user_id)
    }
    
    if isDuplicate(notification):
        return SKIPPED
    
    if notification.priority == CRITICAL:
        return deliverImmediately(notification)
    
    queue.enqueue(notification, priority=notification.priority)

function processQueue():
    while true:
        notification = queue.dequeue()
        deliverWithRetry(notification, attempt=0)

function deliverWithRetry(notification, attempt):
    try:
        if notification.platform == IOS:
            result = apns.send(notification)
        elif notification.platform == ANDROID:
            result = fcm.send(notification)
        
        // Step 5: Confirm delivery
        recordDelivery(notification.id, status=SENT, platform_id=result.id)
        metrics.increment("notifications.sent")
        
    catch TransientError:
        if attempt < MAX_RETRIES:
            delay = (2 ^ attempt) + randomJitter()
            scheduleRetry(notification, attempt + 1, delay)
        else:
            deadLetterQueue.enqueue(notification)
            metrics.increment("notifications.failed")
            
    catch InvalidTokenError:
        markTokenInvalid(notification.recipient, notification.platform)
        metrics.increment("notifications.invalid_token")
```

## Performance Targets

| Metric | Target |
|--------|--------|
| Queue to delivery | < 1 second |
| Critical notification | < 200ms |
| APNs delivery | < 500ms |
| FCM delivery | < 500ms |
| Delivery success rate | > 98% |
