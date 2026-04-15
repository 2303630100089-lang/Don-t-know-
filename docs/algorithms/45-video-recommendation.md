# 45. Algorithm: Video Recommendation

## Overview

Video recommendation algorithm using input features, embedding models, Approximate Nearest Neighbor (ANN) search, reinforcement learning ranking, and real-time model updates.

## Algorithm Steps

### Step 1: Input Features
- **Watch Time**: Duration viewed relative to total video length.
- **Likes**: Binary like/dislike signal with recency weighting.
- **Shares**: Strong positive signal indicating high user interest.
- **Additional Features**: Click-through rate, replay count, comment engagement.
- **Context Features**: Time of day, device type, viewing history.

### Step 2: Embedding Model Generates Vector
- User interaction history → user embedding vector (128-dim).
- Video metadata + features → video embedding vector (128-dim).
- Two-tower neural network architecture.
- Training: Contrastive learning on positive/negative interaction pairs.
- Model updated via periodic retraining (daily batch + online fine-tuning).

### Step 3: ANN (Approximate Nearest Neighbor) Search
- User embedding → ANN index query → top-K candidate videos.
- ANN libraries: FAISS, ScaNN, or Annoy for fast retrieval.
- Index structure: HNSW (Hierarchical Navigable Small World) graph.
- Candidate pool size: 500-1000 videos from billions.
- Trade-off: recall vs. latency (target >95% recall at <10ms).

### Step 4: Ranking with Reinforcement Learning
- Candidates re-ranked using detailed scoring model.
- Multi-objective optimization: engagement, diversity, freshness.
- Contextual bandits for exploration (discover new content).
- Reward signal: weighted combination of watch time, likes, shares.
- Policy gradient methods for continuous optimization.

### Step 5: Real-Time Updates
- User actions trigger real-time feature updates.
- Streaming pipeline updates user embeddings incrementally.
- ANN index refreshed periodically (every few minutes).
- Model parameters updated via online learning.
- A/B testing framework for comparing model versions.

## Pseudocode

```
function recommendVideos(user_id, context, N=20):
    // Step 1: Extract features
    user_features = featureStore.getUserFeatures(user_id)
    context_features = extractContext(context)
    
    // Step 2: Generate embedding
    user_embedding = embeddingModel.encode(user_features, context_features)
    
    // Step 3: ANN retrieval
    candidates = annIndex.search(
        query=user_embedding,
        top_k=500,
        ef_search=200  // HNSW search parameter
    )
    
    // Step 4: Re-rank with RL
    scored_candidates = []
    for video in candidates:
        video_features = featureStore.getVideoFeatures(video.id)
        
        engagement_score = rlModel.predict(
            user_embedding, video.embedding,
            video_features, context_features
        )
        
        diversity_bonus = computeDiversityBonus(video, scored_candidates)
        freshness_bonus = computeFreshnessBonus(video.upload_time)
        
        final_score = (0.7 * engagement_score +
                       0.2 * diversity_bonus +
                       0.1 * freshness_bonus)
        
        scored_candidates.append((final_score, video))
    
    // Step 5: Exploration
    top_results = topN(scored_candidates, N - 2)
    explore_results = rlModel.explore(candidates, k=2)
    
    return interleave(top_results, explore_results)

function onUserAction(user_id, video_id, action):
    // Real-time update
    featureStore.updateUserFeatures(user_id, video_id, action)
    embeddingModel.updateOnline(user_id, action)
    rlModel.updateReward(user_id, video_id, action)
```

## Performance Targets

| Metric | Target |
|--------|--------|
| ANN retrieval | < 10ms |
| Re-ranking (500 candidates) | < 30ms |
| End-to-end latency | < 50ms |
| ANN recall@500 | > 95% |
| User engagement lift | > 10% vs. baseline |
