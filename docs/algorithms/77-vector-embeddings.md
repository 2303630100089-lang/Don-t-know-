# 77. Algorithm: Vector Embeddings

## Overview

Vector embedding algorithm that converts content into dense vector representations, stores them in a vector database, enables fast Approximate Nearest Neighbor (ANN) search, and supports personalized ranking.

## Algorithm Steps

### Step 1: Content → Embedding Model
- Input content: text, images, user profiles, products.
- **Text Embeddings**: Transformer-based models (BERT, Sentence-BERT, E5).
- **Image Embeddings**: Vision models (CLIP, ResNet, ViT).
- **Multi-Modal**: Joint embedding space for text + image (CLIP).
- Embedding dimension: 128-768 dimensions depending on model.

### Step 2: Model → Vector Representation
- Forward pass through neural network produces dense vector.
- Vector normalized to unit length for cosine similarity.
- Batch encoding for throughput: process thousands of items per second.
- GPU acceleration for large-scale embedding generation.
- Quality validation: check embedding distribution and clustering.

### Step 3: Stored in Vector DB
- **Vector Databases**: Pinecone, Milvus, Weaviate, Qdrant, pgvector.
- **Index Types**: HNSW, IVF, PQ (Product Quantization).
- **Metadata**: Store auxiliary data alongside vectors for filtering.
- **Namespaces**: Separate embedding spaces per use case.
- **Versioning**: Track embedding model versions for consistency.

### Step 4: Fast ANN Search
- **Query**: Input query embedded using same model.
- **ANN Algorithms**:
  - HNSW: Hierarchical Navigable Small World graph (best for low-latency).
  - IVF-PQ: Inverted File with Product Quantization (best for large scale).
  - ScaNN: Google's efficient ANN library.
- **Hybrid Search**: Combine vector similarity with metadata filters.
- **Top-K Retrieval**: Return K most similar vectors.

### Step 5: Personalized Ranking
- ANN candidates re-ranked using personalization signals.
- User interaction history influences final ranking.
- Diversity enforcement: avoid too-similar results.
- Context-aware: time, location, device affect ranking.
- Feedback loop: clicks and engagement update user vectors.

## Pseudocode

```
// Embedding generation pipeline
function generateEmbeddings(items, model_name):
    model = loadModel(model_name)
    
    batches = chunk(items, batch_size=256)
    all_embeddings = []
    
    for batch in batches:
        if model.type == "text":
            inputs = tokenizer.encode(batch.map(i => i.text))
        elif model.type == "image":
            inputs = preprocessImages(batch.map(i => i.image))
        elif model.type == "multimodal":
            inputs = preprocessMultiModal(batch)
        
        // GPU-accelerated inference
        embeddings = model.encode(inputs, device="gpu")
        
        // Normalize to unit vectors
        embeddings = normalize(embeddings, dim=1)
        
        all_embeddings.extend(embeddings)
    
    return all_embeddings

function indexEmbeddings(items, embeddings, collection_name):
    vectorDB.createCollection(collection_name, {
        dimension: embeddings[0].length,
        index_type: "HNSW",
        metric: "cosine",
        hnsw_config: { M: 16, ef_construction: 200 }
    })
    
    points = []
    for item, embedding in zip(items, embeddings):
        points.append({
            id: item.id,
            vector: embedding,
            metadata: {
                category: item.category,
                created_at: item.created_at,
                popularity: item.popularity_score
            }
        })
    
    vectorDB.upsert(collection_name, points, batch_size=1000)

// Search pipeline
function search(query, user_id, collection_name, top_k=20, filters=None):
    // Step 1 + 2: Embed query
    query_embedding = model.encode(query)
    query_embedding = normalize(query_embedding)
    
    // Step 4: ANN search
    ann_results = vectorDB.search(
        collection=collection_name,
        query_vector=query_embedding,
        top_k=top_k * 3,  // Retrieve more for re-ranking
        ef_search=100,     // HNSW search parameter
        filters=filters    // Metadata filters
    )
    
    // Step 5: Personalized re-ranking
    user_vector = featureStore.getUserVector(user_id)
    
    re_ranked = []
    for result in ann_results:
        base_score = result.similarity
        
        // Personalization boost
        if user_vector:
            personal_score = cosineSimilarity(user_vector, result.vector)
            final_score = 0.7 * base_score + 0.3 * personal_score
        else:
            final_score = base_score
        
        // Popularity boost
        popularity_boost = log(1 + result.metadata.popularity) * 0.05
        final_score += popularity_boost
        
        re_ranked.append((final_score, result))
    
    // Diversity filter
    diversified = applyDiversity(re_ranked, max_per_category=3)
    
    return diversified[:top_k]

// Real-time vector update
function onUserInteraction(user_id, item_id, action_type):
    item_vector = vectorDB.getVector(item_id)
    user_vector = featureStore.getUserVector(user_id)
    
    // Update user vector incrementally
    weight = ACTION_WEIGHTS[action_type]  // click: 0.1, like: 0.3, purchase: 0.5
    
    updated_user_vector = (1 - weight) * user_vector + weight * item_vector
    updated_user_vector = normalize(updated_user_vector)
    
    featureStore.updateUserVector(user_id, updated_user_vector)
```

## Performance Targets

| Metric | Target |
|--------|--------|
| Embedding generation (per item) | < 5ms |
| ANN search (1M vectors) | < 5ms |
| ANN search (100M vectors) | < 20ms |
| Recall@100 | > 95% |
| Index update | < 10ms |
