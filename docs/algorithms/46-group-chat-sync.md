# 46. Algorithm: Group Chat Sync

## Overview

Efficient group chat message synchronization using a Pub/Sub model with Kafka-based fast fan-out, ensuring all group members receive messages reliably and in order.

## Algorithm

### Pub/Sub Model
- **Publisher**: Message sender publishes to a group topic.
- **Subscribers**: All group members subscribe to the group topic.
- **Topic**: Each group has a dedicated Kafka topic.
- **Decoupling**: Sender doesn't need to know recipient status.
- **Scalability**: Supports groups of any size.

### Publisher = Sender
- Sender creates message with content, timestamp, and message_id.
- Message published to group's Kafka topic.
- Server assigns a monotonically increasing sequence number.
- Publisher receives acknowledgment once message is persisted.
- Message stored in group's message history.

### Subscribers = Group Members
- Each member has a consumer tracking their read position.
- Online members receive messages in real-time via WebSocket.
- Offline members sync on reconnection from last known position.
- Read receipts tracked per member per message.
- Member can mute notifications while still receiving messages.

### Messages Delivered via Topic Channels
- Each group topic ensures strict ordering of messages.
- Messages include: sender_id, content, timestamp, seq_num, type.
- Support for text, media, reactions, system messages.
- Message threading via parent_message_id.
- End-to-end encryption optional per group setting.

### Fast Fan-Out Using Kafka Partitions
- Large groups: multiple partitions for parallel processing.
- Partition key: group_id (ensures ordering within a group).
- Consumer groups: one consumer per active member's connection.
- Fan-out service distributes messages to WebSocket connections.
- Batch delivery for catching up offline members.

## Pseudocode

```
function sendGroupMessage(sender_id, group_id, content):
    message = {
        id: generateId(),
        sender_id: sender_id,
        group_id: group_id,
        content: content,
        timestamp: now(),
        seq_num: getNextSequence(group_id)
    }
    
    // Publish to Kafka topic
    kafka.publish(
        topic=f"group-{group_id}",
        key=group_id,
        value=message
    )
    
    // Store in message history
    db.storeMessage(message)
    
    return ack(message.id, message.seq_num)

function fanOutService():
    for group_topic in kafka.subscribe("group-*"):
        message = kafka.consume(group_topic)
        members = groupService.getMembers(message.group_id)
        
        for member in members:
            if member.id == message.sender_id:
                continue  // Skip sender
            
            if presenceService.isOnline(member.id):
                websocket.send(member.id, message)
            else:
                pendingDelivery.enqueue(member.id, message)
                pushNotification.send(member.id, message.preview)

function syncOnReconnect(user_id, group_id, last_seq_num):
    missed_messages = db.getMessages(
        group_id, 
        seq_num > last_seq_num,
        limit=100
    )
    
    websocket.sendBatch(user_id, missed_messages)
    
    return missed_messages.last().seq_num
```

## Performance Targets

| Metric | Target |
|--------|--------|
| Message publish | < 10ms |
| Fan-out latency (1K members) | < 100ms |
| Fan-out latency (10K members) | < 500ms |
| Kafka throughput | > 1M msg/sec |
| Sync on reconnect | < 200ms |
