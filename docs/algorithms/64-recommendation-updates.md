# 64. Algorithm: Recommendation Updates

## Overview

Real-time recommendation update algorithm that processes user actions into events, extracts features, updates models, runs inference, and delivers fast personalized results.

## Algorithm Steps

### Step 1: User Action → Event Log
- User interaction captured: click, view, like, purchase, share.
- Event schema: user_id, item_id, action_type, timestamp, context.
- Events published to Kafka topic for real-time processing.
- Events also stored in data lake for batch retraining.
- Event deduplication via idempotency keys.

### Step 2: Event → Feature Extraction
- Streaming processor (Flink/Spark Streaming) consumes events.
- Real-time features computed: session activity, recent preferences, trending items.
- Aggregated features: 1h/24h/7d interaction counts, category distributions.
- Features written to online feature store (Redis-backed).
- Feature versioning for reproducibility and rollback.

### Step 3: Features → Model Update
- Online learning: model parameters updated incrementally with new data.
- User embedding updated with latest interaction signals.
- Item popularity scores recalculated in real-time.
- Batch retraining: full model retrained daily on complete dataset.
- Model versioning: new models deployed via A/B testing.

### Step 4: Model → Inference
- Updated model serves predictions for next user request.
- Inference pipeline: feature lookup → model predict → post-process.
- Model serving via TensorFlow Serving or TorchServe.
- Batch pre-computation for popular user-item pairs.
- Caching: inference results cached for 5 minutes.

### Step 5: Fast Personalization
- Recommendations refreshed within seconds of user action.
- Diversity enforcement: no more than 3 items from same category.
- Novelty injection: 10% of recommendations from exploration pool.
- Context-aware: time of day, device, location influence results.
- Feedback loop: recommendation clicks further refine model.

## Pseudocode

```
function onUserAction(event):
    // Step 1: Log event
    kafka.publish("user-actions", event)
    
    // Step 2: Update features (streaming)
    features = extractFeatures(event)
    featureStore.updateOnlineFeatures(event.user_id, features)
    
    // Step 3: Update model
    user_embedding = embeddingModel.updateIncremental(
        event.user_id, event.item_id, event.action_type
    )
    featureStore.updateUserEmbedding(event.user_id, user_embedding)
    
    // Invalidate cached recommendations
    cache.invalidate(f"recs:{event.user_id}")

function getRecommendations(user_id, context, N=20):
    // Check cache
    cached = cache.get(f"recs:{user_id}")
    if cached and cached.age < CACHE_TTL:
        return cached.recommendations
    
    // Step 4: Inference
    user_features = featureStore.getUserFeatures(user_id)
    user_embedding = featureStore.getUserEmbedding(user_id)
    
    candidates = candidateGeneration(user_embedding, top_k=500)
    
    scored = []
    for item in candidates:
        item_features = featureStore.getItemFeatures(item.id)
        score = model.predict(user_features, item_features, context)
        scored.append((score, item))
    
    // Step 5: Post-processing
    ranked = topN(scored, N * 2)  // Get extra for diversity
    diversified = applyDiversity(ranked, max_per_category=3)
    with_exploration = injectNovelty(diversified, exploration_rate=0.1)
    final = with_exploration[:N]
    
    // Cache results
    cache.set(f"recs:{user_id}", final, ttl=CACHE_TTL)
    
    return final

// Batch retraining (runs daily)
function batchRetrain():
    training_data = dataLake.getInteractions(last_30_days)
    new_model = trainModel(training_data)
    
    // A/B test new model
    abTest.deploy(new_model, traffic_percentage=10)
    
    if abTest.isWinner(new_model, metric="engagement"):
        abTest.promote(new_model, traffic_percentage=100)
```

## Performance Targets

| Metric | Target |
|--------|--------|
| Feature update latency | < 1 second |
| Model inference | < 20ms |
| Recommendation refresh | < 5 seconds |
| Cache hit rate | > 70% |
| Engagement improvement | > 5% vs. baseline |
