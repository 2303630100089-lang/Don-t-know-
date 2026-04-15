# 50. Algorithm: Search Ranking

## Overview

Search ranking algorithm that parses queries into tokens, performs index lookups, applies BM25 scoring, adds a personalization layer, and uses fast Top-K retrieval for results.

## Algorithm Steps

### Step 1: Query Parsed → Tokens
- Raw query string cleaned and normalized.
- Tokenization: split into individual terms.
- Stop word removal: filter common words (the, is, and).
- Stemming/Lemmatization: reduce words to root form.
- Synonym expansion: add equivalent terms from synonym dictionary.
- Query intent detection: navigational, informational, transactional.

### Step 2: Index Lookup
- Each token looked up in inverted index.
- Inverted index: term → list of (document_id, term_frequency, positions).
- Boolean operations: AND/OR between term posting lists.
- Position-based matching for phrase queries.
- Index stored in memory-mapped files for fast access.

### Step 3: BM25 Scoring
```
BM25(q, d) = Σ IDF(qi) × (f(qi, d) × (k1 + 1)) / (f(qi, d) + k1 × (1 - b + b × |d|/avgdl))
```
- **IDF(qi)**: Inverse Document Frequency — rare terms score higher.
- **f(qi, d)**: Term frequency of qi in document d.
- **k1**: Term frequency saturation parameter (default 1.2).
- **b**: Length normalization parameter (default 0.75).
- **|d|**: Document length.
- **avgdl**: Average document length across the corpus.

### Step 4: Personalization Layer
- User profile influences ranking:
  - Recently viewed topics boosted.
  - Preferred content sources prioritized.
  - Language and locale preferences applied.
- Click-through rate (CTR) model: predicts likelihood of user clicking each result.
- Diversity injection: avoid too many results from same source.
- Freshness boost for time-sensitive queries.

### Step 5: Fast Top-K Retrieval
- Block-Max WAND (BMW) algorithm for early termination.
- Skip documents that can't make it to Top-K.
- Maintains a min-heap of size K for current top results.
- Orders posting lists by impact score for efficiency.
- Achieves sub-linear time complexity for most queries.

## Pseudocode

```
function searchAndRank(query_string, user_id, K=10):
    // Step 1: Parse query
    tokens = tokenize(query_string)
    tokens = removeStopWords(tokens)
    tokens = stem(tokens)
    tokens = expandSynonyms(tokens)
    intent = detectIntent(query_string)
    
    // Step 2: Index lookup
    posting_lists = []
    for token in tokens:
        posting_lists.append(invertedIndex.lookup(token))
    
    // Step 3 + Step 5: BM25 scoring with BMW early termination
    topK_heap = MinHeap(capacity=K)
    threshold = 0
    
    // BMW algorithm
    sorted_lists = sortByMaxImpact(posting_lists)
    
    while not allExhausted(sorted_lists):
        doc_id = nextCandidate(sorted_lists)
        upper_bound = computeUpperBound(doc_id, sorted_lists)
        
        if upper_bound <= threshold:
            skipTo(sorted_lists, nextPivot())
            continue
        
        // Full BM25 scoring
        score = 0
        for list in sorted_lists:
            if list.contains(doc_id):
                tf = list.getTermFreq(doc_id)
                idf = computeIDF(list.term, totalDocs)
                dl = getDocLength(doc_id)
                score += idf * (tf * (K1 + 1)) / (tf + K1 * (1 - B + B * dl / AVGDL))
        
        if topK_heap.size < K:
            topK_heap.push(score, doc_id)
            threshold = topK_heap.peek().score
        elif score > threshold:
            topK_heap.popAndPush(score, doc_id)
            threshold = topK_heap.peek().score
    
    // Step 4: Personalization re-ranking
    results = topK_heap.toList()
    user_profile = featureStore.getUserProfile(user_id)
    
    for result in results:
        personalization_boost = computePersonalization(user_profile, result)
        ctr_prediction = ctrModel.predict(user_profile, result)
        result.final_score = (0.7 * result.score + 
                              0.2 * personalization_boost +
                              0.1 * ctr_prediction)
    
    return sortByFinalScore(results)
```

## Performance Targets

| Metric | Target |
|--------|--------|
| Query parsing | < 1ms |
| Index lookup | < 5ms |
| BM25 scoring (Top-10) | < 10ms |
| Personalization | < 5ms |
| End-to-end search | < 30ms |
