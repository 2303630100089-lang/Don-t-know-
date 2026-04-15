# 42. Algorithm: Feed Ranking

## Overview

Content feed ranking algorithm that combines recency, engagement metrics, and user relevance using vector embeddings for fast, personalized feed generation with heap-optimized Top-N selection.

## Algorithm

### Scoring Formula

```
Score = α × Recency + β × Engagement + γ × Relevance
```

Where:
- **α, β, γ** are tunable weights (default: α=0.3, β=0.3, γ=0.4)
- All components normalized to [0, 1] range

### Recency Score
```
Recency = exp(-λ × age_hours)
```
- **λ**: Decay factor (default 0.1, tunable per content type)
- Recently posted content scores higher
- Different decay rates for news (fast) vs. evergreen content (slow)

### Engagement Score
```
Engagement = w1 × norm(likes) + w2 × norm(comments) + w3 × norm(shares)
```
- **w1=0.3, w2=0.5, w3=0.2** (comments weighted highest for quality signal)
- Normalized using min-max scaling per time window
- Engagement velocity (rate of change) as additional signal

### Relevance Score
```
Relevance = cosine_similarity(user_vector, content_vector)
```
- **User vector**: Embedding of user interests derived from interaction history
- **Content vector**: Embedding of content features (text, topics, creator)
- Computed via pre-trained deep learning embedding model
- Updated in real-time with each user interaction

### Top-N Selection with Heap Optimization
```
TopN = min_heap(size=N) over all scored items
```
- Use min-heap of size N to maintain top-scoring items
- Time complexity: O(M × log N) where M = total items, N = feed size
- Space complexity: O(N)
- Avoids full sort of entire candidate set

## Pseudocode

```
function rankFeed(user_id, candidates, N):
    user_vector = embeddingService.getUserVector(user_id)
    min_heap = MinHeap(capacity=N)
    
    for item in candidates:
        recency = exp(-LAMBDA * item.age_hours)
        
        engagement = (W1 * normalize(item.likes) +
                      W2 * normalize(item.comments) +
                      W3 * normalize(item.shares))
        
        content_vector = embeddingService.getContentVector(item.id)
        relevance = cosineSimilarity(user_vector, content_vector)
        
        score = ALPHA * recency + BETA * engagement + GAMMA * relevance
        
        if min_heap.size < N:
            min_heap.push(score, item)
        elif score > min_heap.peek():
            min_heap.popAndPush(score, item)
    
    return min_heap.toSortedList()  // descending order
```

## Performance Targets

| Metric | Target |
|--------|--------|
| Scoring per item | < 0.1ms |
| Feed generation (1000 candidates) | < 50ms |
| Embedding lookup | < 5ms |
| Heap operations | O(log N) per item |
| Feed freshness | < 1 minute from post |
