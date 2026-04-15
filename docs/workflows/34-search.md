# 34. Workflow: Search

## Overview

High-performance search system powered by ElasticSearch with full-text indexing, faceted search, query caching, and advanced ranking algorithms.

## Components

### ElasticSearch Cluster
- **Cluster Topology**: Multi-node cluster with dedicated master, data, and coordinating nodes.
- **Sharding**: Index-level sharding for horizontal scaling.
- **Replication**: Replica shards for fault tolerance and read scaling.
- **Index Lifecycle**: Hot-warm-cold architecture for cost-efficient storage.
- **Health Monitoring**: Cluster health checks and automatic shard rebalancing.

### Full-Text Indexing
- **Analyzers**: Custom analyzers with tokenizers, filters, and char filters.
- **Language Support**: Multi-language analyzers (CJK, Latin, Arabic, etc.).
- **Stemming**: Language-specific stemming for root word matching.
- **Synonyms**: Configurable synonym dictionaries.
- **Near Real-Time**: Index refresh interval of 1 second for near-instant search.

### Faceted Search for Filters
- **Aggregations**: Bucket aggregations for category-based filtering.
- **Range Facets**: Price ranges, date ranges, rating ranges.
- **Nested Facets**: Hierarchical category navigation.
- **Post-Filter**: Facet counts unaffected by selected filters.
- **Dynamic Facets**: Auto-generated facets based on document fields.

### Query Caching
- **Node Query Cache**: LRU cache for frequently used filters.
- **Request Cache**: Shard-level caching for aggregation results.
- **Application Cache**: Redis cache for full search response pages.
- **Cache Invalidation**: TTL-based + event-driven invalidation on index updates.
- **Cache Hit Rate**: Target > 80% for common queries.

### Ranking Algorithm: TF-IDF + BM25
- **BM25**: Default scoring algorithm in ElasticSearch.
  - `score(q, d) = Σ IDF(qi) · (f(qi, d) · (k1 + 1)) / (f(qi, d) + k1 · (1 - b + b · |d| / avgdl))`
- **TF-IDF**: Term Frequency–Inverse Document Frequency for term importance.
- **Field Boosting**: Higher weight for title matches vs. body matches.
- **Function Score**: Custom scoring functions (recency, popularity, etc.).
- **Learning to Rank**: ML-based re-ranking for personalized results.

## Flow Diagram

```
Search Query
       │
       ▼
┌──────────────┐     ┌──────────────┐
│ Query Parser │────▶│ Query Cache  │ ── Hit ──▶ Return Cached
└──────┬───────┘     └──────────────┘
       │ Miss
       ▼
┌──────────────┐
│ ElasticSearch│
│   Cluster    │
└──────┬───────┘
       │
       ├──▶ Full-Text Search (BM25)
       │
       ├──▶ Faceted Aggregations
       │
       └──▶ Custom Scoring
              │
              ▼
       ┌──────────────┐
       │  Results +   │
       │  Facet Counts │
       └──────┬───────┘
              │
              ▼
         Cache + Return
```

## Performance Targets

| Metric | Target |
|--------|--------|
| Query latency (p50) | < 20ms |
| Query latency (p99) | < 100ms |
| Index throughput | > 10K docs/sec |
| Cache hit rate | > 80% |
| Facet computation | < 50ms |
