# 58. Algorithm: Auto-Scaling

## Overview

Intelligent auto-scaling algorithm that monitors resource utilization, triggers scale-out/scale-in decisions, and leverages cloud-native orchestration for fast, cost-effective scaling.

## Algorithm Steps

### Step 1: Monitor CPU/Memory
- Collect CPU utilization, memory usage, request rate, queue depth.
- Metrics aggregated over sliding window (default: 5 minutes).
- Data sources: Prometheus, CloudWatch, or custom metrics API.
- Sampling interval: 15 seconds for fine-grained monitoring.

### Step 2: If Threshold Exceeded → Scale Out
- **Scale-Out Trigger**: CPU > 70% OR memory > 80% OR queue depth > 1000.
- Calculate desired instances: `desired = ceil(current_load / target_utilization)`.
- Respect maximum instance limit.
- Provision new instances from pre-warmed pool when available.

### Step 3: If Underutilized → Scale In
- **Scale-In Trigger**: CPU < 30% AND memory < 40% for sustained period (10 min).
- Gradual scale-in: remove one instance at a time.
- Drain connections before termination.
- Respect minimum instance count.

### Step 4: Fast Decision via Autoscaler
- Cool-down period between scaling events (default: 3 minutes).
- Predictive scaling: ML model forecasts traffic patterns.
- Schedule-based scaling for known traffic spikes.
- Decision latency: < 1 second from metric evaluation to action.

### Step 5: Cloud-Native Orchestration
- Kubernetes HPA (Horizontal Pod Autoscaler) for container scaling.
- Cloud provider auto-scaling groups (ASG) for VM scaling.
- Cluster autoscaler for node-level scaling.
- Multi-zone deployment for high availability during scaling.

## Pseudocode

```
function autoScale():
    while true:
        metrics = collectMetrics(window=5min)
        current_instances = getInstanceCount()
        
        // Scale out check
        if metrics.cpu_avg > SCALE_OUT_CPU_THRESHOLD or
           metrics.memory_avg > SCALE_OUT_MEM_THRESHOLD or
           metrics.queue_depth > SCALE_OUT_QUEUE_THRESHOLD:
            
            if timeSinceLastScale() > COOL_DOWN_PERIOD:
                desired = ceil(metrics.current_load / TARGET_UTILIZATION)
                desired = min(desired, MAX_INSTANCES)
                
                if desired > current_instances:
                    scaleOut(desired - current_instances)
                    recordScaleEvent(SCALE_OUT, desired)
        
        // Scale in check
        elif metrics.cpu_avg < SCALE_IN_CPU_THRESHOLD and
             metrics.memory_avg < SCALE_IN_MEM_THRESHOLD and
             metrics.sustained_low_duration > SCALE_IN_WAIT:
            
            if current_instances > MIN_INSTANCES:
                instance = selectLeastLoadedInstance()
                drainConnections(instance)
                terminate(instance)
                recordScaleEvent(SCALE_IN, current_instances - 1)
        
        sleep(EVALUATION_INTERVAL)
```

## Performance Targets

| Metric | Target |
|--------|--------|
| Decision latency | < 1 second |
| Scale-out time (new pod) | < 30 seconds |
| Scale-out time (new VM) | < 2 minutes |
| Connection drain | < 30 seconds |
| Prediction accuracy | > 85% |
