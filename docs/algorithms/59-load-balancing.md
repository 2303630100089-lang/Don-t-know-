# 59. Algorithm: Load Balancing

## Overview

Intelligent load balancing algorithm that distributes requests to the least-loaded server, performs health checks, enables fast failover, and supports geo-routing for global deployments.

## Algorithm Steps

### Step 1: Requests → Load Balancer
- All incoming requests received by load balancer.
- L4 (TCP) or L7 (HTTP) load balancing based on requirements.
- TLS termination at load balancer for centralized certificate management.
- Request metadata extracted: source IP, headers, path.

### Step 2: Balancer Selects Least-Loaded Server
- **Least Connections**: Route to server with fewest active connections.
- **Weighted Least Connections**: Factor in server capacity weights.
- **Least Response Time**: Route to server with fastest recent response times.
- **Round Robin**: Fallback when servers are equally loaded.
- Selection algorithm runs in O(log N) using min-heap.

### Step 3: Health Checks for Servers
- **Active Health Checks**: Periodic HTTP/TCP probes (every 5 seconds).
- **Passive Health Checks**: Monitor response codes and latency from real traffic.
- **Health Thresholds**: Mark unhealthy after 3 consecutive failures.
- **Recovery**: Mark healthy after 2 consecutive successes.
- **Graceful Degradation**: Reduce traffic before full removal.

### Step 4: Fast Failover
- Unhealthy server removed from rotation immediately.
- In-flight requests retried on healthy server (if idempotent).
- Connection draining for graceful shutdown.
- Failover detection time: < 10 seconds.
- Automatic recovery when server becomes healthy.

### Step 5: Geo-Routing
- DNS-based or anycast routing to nearest data center.
- Latency-based routing for optimal performance.
- Geo-fencing for data sovereignty compliance.
- Cross-region failover for disaster recovery.
- Traffic splitting for gradual region migration.

## Pseudocode

```
function routeRequest(request):
    // Step 5: Geo-routing
    region = geoRoute(request.source_ip)
    server_pool = getHealthyServers(region)
    
    if server_pool.isEmpty():
        server_pool = getHealthyServers(FAILOVER_REGION)
    
    // Step 2: Select least-loaded server
    server = selectServer(server_pool, algorithm=LEAST_CONNECTIONS)
    
    // Route request
    try:
        response = forward(request, server)
        updateMetrics(server, response.latency, response.status)
        return response
    catch ConnectionError:
        markUnhealthy(server)
        // Retry on another server
        return routeRequest(request)  // Recursive retry

function healthCheck():
    while true:
        for server in all_servers:
            result = probe(server, endpoint="/health")
            
            if result.success:
                server.consecutive_successes++
                server.consecutive_failures = 0
                if server.status == UNHEALTHY and
                   server.consecutive_successes >= RECOVERY_THRESHOLD:
                    markHealthy(server)
            else:
                server.consecutive_failures++
                server.consecutive_successes = 0
                if server.consecutive_failures >= FAILURE_THRESHOLD:
                    markUnhealthy(server)
                    removeFromPool(server)
        
        sleep(HEALTH_CHECK_INTERVAL)

function selectServer(pool, algorithm):
    if algorithm == LEAST_CONNECTIONS:
        return pool.minHeap.peek()  // O(1) retrieval
    elif algorithm == LEAST_RESPONSE_TIME:
        return pool.sortByAvgLatency().first()
    else:
        return pool.roundRobin()
```

## Performance Targets

| Metric | Target |
|--------|--------|
| Routing decision | < 0.5ms |
| Health check interval | 5 seconds |
| Failover detection | < 10 seconds |
| Geo-routing accuracy | > 99% |
| Load variance across servers | < 15% |
