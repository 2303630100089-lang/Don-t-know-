# 68. Algorithm: Logging Pipeline

## Overview

Scalable logging pipeline that collects logs from services, streams through Kafka, processes and indexes in the ELK stack, and provides fast query access.

## Algorithm Steps

### Step 1: Logs → Log Collector
- Applications emit structured JSON logs to stdout/files.
- Log collectors (Filebeat, Fluentd) tail log files in real-time.
- Collectors add metadata: hostname, service name, environment.
- Log buffering at collector level for resilience.
- Multi-line log merging for stack traces.

### Step 2: Collector → Kafka
- Collectors publish logs to Kafka topics (one per service or environment).
- Kafka provides durable buffering between collection and processing.
- Partitioning by service name for parallel processing.
- Retention: 3 days in Kafka for reprocessing capability.
- Back-pressure handling: slow consumers don't block producers.

### Step 3: Kafka → ELK Stack
- Logstash consumers read from Kafka topics.
- **Parsing**: Grok patterns, JSON parsing, regex extraction.
- **Enrichment**: GeoIP lookup, user agent parsing, field mapping.
- **Filtering**: Drop debug logs in production, sample high-volume logs.
- **Output**: Processed logs sent to Elasticsearch.

### Step 4: Indexed in ElasticSearch
- Logs indexed in date-based indices (logs-YYYY.MM.DD).
- Index templates define field mappings and settings.
- ILM (Index Lifecycle Management): hot → warm → cold → delete.
- Shard allocation: hot nodes (SSD) for recent, warm nodes (HDD) for older.
- Replica shards for read scaling and fault tolerance.

### Step 5: Fast Query Access
- Kibana provides search interface for log exploration.
- KQL (Kibana Query Language) for user-friendly queries.
- Saved searches and dashboards for common investigations.
- Alerting: Watcher/ElastAlert for automated log-based alerts.
- Export: CSV/JSON export for offline analysis.

## Pseudocode

```
// Step 1: Log Collector (Filebeat)
function collectLogs():
    for log_file in configured_files:
        tailer = FileTailer(log_file)
        
        while true:
            lines = tailer.readNewLines()
            for line in lines:
                log_entry = parseLine(line)
                log_entry.metadata = {
                    hostname: os.hostname(),
                    service: config.service_name,
                    environment: config.environment
                }
                outputBuffer.add(log_entry)
            
            if outputBuffer.isFull() or timer.elapsed() > FLUSH_INTERVAL:
                kafka.publishBatch(
                    topic=f"logs-{config.service_name}",
                    messages=outputBuffer.drain()
                )

// Step 3: Logstash Processing
function processLogs():
    consumer = kafka.createConsumer(topics=["logs-*"])
    
    while true:
        batch = consumer.poll(timeout=1s)
        
        for log_entry in batch:
            // Parse
            parsed = parseJSON(log_entry.value)
            
            // Enrich
            if parsed.ip:
                parsed.geo = geoIP.lookup(parsed.ip)
            if parsed.user_agent:
                parsed.browser = parseUserAgent(parsed.user_agent)
            
            // Filter
            if parsed.level == "DEBUG" and config.env == "production":
                continue  // Drop debug logs in prod
            
            if parsed.service in HIGH_VOLUME_SERVICES:
                if random() > SAMPLE_RATE:
                    continue  // Sample high-volume logs
            
            // Output to Elasticsearch
            index_name = f"logs-{parsed.service}-{today()}"
            elasticsearch.index(index_name, parsed)
        
        consumer.commit()

// Step 5: Query
function searchLogs(query, timeRange, filters):
    es_query = buildESQuery(query, timeRange, filters)
    
    results = elasticsearch.search(
        index="logs-*",
        body=es_query,
        size=100,
        sort=[{"@timestamp": "desc"}]
    )
    
    return results.hits
```

## Performance Targets

| Metric | Target |
|--------|--------|
| Collection latency | < 5 seconds |
| Kafka throughput | > 100K events/sec |
| Processing latency | < 10 seconds |
| Index throughput | > 50K docs/sec |
| Search query latency | < 2 seconds |
