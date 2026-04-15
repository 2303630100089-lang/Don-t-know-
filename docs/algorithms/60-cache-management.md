# 60. Algorithm: Cache Management

## Overview

High-performance cache management algorithm using Redis for frequently accessed data, with TTL-based expiry, write-through caching, LRU eviction, and distributed cache clusters.

## Algorithm Steps

### Step 1: Frequently Accessed Data → Redis
- **Hot Data Identification**: Access frequency tracking for cache promotion.
- **Cache Population**: On first access, data loaded from DB and cached.
- **Data Types**: Strings, hashes, sorted sets, lists — matched to access patterns.
- **Serialization**: MessagePack or Protobuf for compact storage.
- **Compression**: LZ4 compression for values > 1KB.

### Step 2: TTL for Cache Entries
- **Static TTL**: Default TTL per data type (user profile: 1h, config: 5min).
- **Dynamic TTL**: TTL adjusted based on access frequency (popular items get longer TTL).
- **TTL Jitter**: Random jitter (±10%) to prevent cache stampede.
- **No-Expire**: Critical configuration data cached without expiry.
- **Lazy Expiry**: Redis handles expiry asynchronously.

### Step 3: Write-Through Caching
- **Write Path**: Write to cache AND database simultaneously.
- **Consistency**: Cache always reflects latest state.
- **Async Write-Behind**: Optional async DB write for non-critical data.
- **Write Coalescing**: Batch multiple writes to same key.
- **Conflict Resolution**: Last-write-wins for concurrent updates.

### Step 4: Fast Eviction Policy (LRU)
- **LRU (Least Recently Used)**: Default eviction policy.
- **Approximate LRU**: Redis samples 5-10 keys and evicts least recent.
- **LFU Alternative**: Least Frequently Used for stable access patterns.
- **MaxMemory Policy**: Configurable max memory per instance.
- **Eviction Threshold**: Start eviction at 90% memory utilization.

### Step 5: Distributed Cache Clusters
- **Redis Cluster**: 16384 hash slots distributed across nodes.
- **Replication**: Each primary has 1+ replicas for fault tolerance.
- **Automatic Failover**: Redis Sentinel or Cluster mode for HA.
- **Cross-Region**: Read replicas in multiple regions for geo-distributed access.
- **Monitoring**: Memory usage, hit rate, latency per node.

## Pseudocode

```
function cacheGet(key):
    value = redis.get(key)
    
    if value != null:
        metrics.cacheHit(key)
        return deserialize(value)
    
    // Cache miss
    metrics.cacheMiss(key)
    value = database.get(key)
    
    if value != null:
        ttl = computeTTL(key, accessFrequency(key))
        ttl_with_jitter = ttl + random(-ttl*0.1, ttl*0.1)
        redis.setex(key, ttl_with_jitter, serialize(value))
    
    return value

function cacheSet(key, value):
    // Write-through: update cache and DB
    serialized = serialize(value)
    ttl = computeTTL(key, accessFrequency(key))
    
    pipeline:
        redis.setex(key, ttl, serialized)
        database.set(key, value)
    
    return OK

function evictionPolicy():
    if redis.memoryUsage() > MAX_MEMORY * 0.9:
        // Redis approximate LRU
        samples = redis.randomKeys(SAMPLE_SIZE)
        lru_key = selectLeastRecentlyUsed(samples)
        redis.del(lru_key)

function computeTTL(key, frequency):
    base_ttl = getTTLConfig(key.type)
    
    if frequency > HIGH_FREQUENCY_THRESHOLD:
        return base_ttl * 2  // Popular items cached longer
    elif frequency < LOW_FREQUENCY_THRESHOLD:
        return base_ttl / 2  // Rare items cached shorter
    else:
        return base_ttl
```

## Performance Targets

| Metric | Target |
|--------|--------|
| Cache read latency | < 1ms |
| Cache write latency | < 2ms |
| Cache hit rate | > 90% |
| Eviction rate | < 5% of capacity/hour |
| Cluster failover | < 5 seconds |
