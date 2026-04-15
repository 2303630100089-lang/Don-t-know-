# 67. Algorithm: Monitoring

## Overview

Comprehensive monitoring algorithm that collects metrics, aggregates them in Prometheus, visualizes in Grafana, triggers alerts, and detects anomalies automatically.

## Algorithm Steps

### Step 1: Metrics Collected
- **Application Metrics**: Request rate, error rate, latency (p50, p95, p99).
- **Infrastructure Metrics**: CPU, memory, disk I/O, network I/O.
- **Business Metrics**: Active users, transactions, revenue.
- **Custom Metrics**: Application-specific counters, gauges, histograms.
- **Collection**: Pull model (Prometheus scrapes endpoints) every 15 seconds.

### Step 2: Aggregated in Prometheus
- **Time Series DB**: Prometheus stores metrics as time series.
- **Labels**: Key-value pairs for metric dimensionality (service, instance, region).
- **PromQL**: Powerful query language for metric analysis.
- **Recording Rules**: Pre-computed aggregations for complex queries.
- **Retention**: Configurable retention (default 15 days), long-term in Thanos/Cortex.

### Step 3: Fast Visualization in Grafana
- **Dashboards**: Pre-built dashboards per service and infrastructure.
- **Panels**: Graphs, gauges, tables, heatmaps, stat panels.
- **Variables**: Template variables for filtering by service, region, instance.
- **Auto-Refresh**: Dashboard auto-refreshes every 5-30 seconds.
- **Drill-Down**: Click-through from summary to detailed views.

### Step 4: Alerts Triggered
- **Alerting Rules**: Defined in Prometheus using PromQL expressions.
- **Alert Routing**: Alertmanager routes alerts by severity and team.
- **Notification Channels**: Slack, PagerDuty, email, SMS, webhooks.
- **Silencing**: Temporary silence during maintenance windows.
- **Grouping**: Related alerts grouped to reduce noise.

### Step 5: Anomaly Detection
- **Statistical Detection**: Z-score based detection for metric deviations.
- **Seasonal Awareness**: Accounts for daily/weekly traffic patterns.
- **ML-Based**: Trained models for complex anomaly patterns.
- **Correlation**: Cross-metric correlation for root cause analysis.
- **Auto-Recovery**: Trigger automated remediation for known issues.

## Pseudocode

```
function collectMetrics():
    // Prometheus scrape cycle (every 15s)
    for target in service_discovery.getTargets():
        metrics = httpGet(f"{target}/metrics")
        prometheus.ingest(metrics, labels={
            instance: target.address,
            service: target.service_name,
            region: target.region
        })

function evaluateAlerts():
    // Runs every evaluation_interval (default 15s)
    for rule in alerting_rules:
        result = prometheus.query(rule.expression)
        
        if result.value > rule.threshold:
            if rule.for_duration > 0:
                // Wait for sustained violation
                if sustained(rule, result, rule.for_duration):
                    fireAlert(rule, result)
            else:
                fireAlert(rule, result)

function fireAlert(rule, result):
    alert = {
        name: rule.name,
        severity: rule.severity,
        description: rule.template.render(result),
        labels: result.labels,
        value: result.value,
        started_at: now()
    }
    
    alertmanager.send(alert)
    
    // Alertmanager routes based on severity
    // Critical → PagerDuty (immediate)
    // Warning → Slack (within 5 min)
    // Info → Email (daily digest)

function detectAnomalies(metric, window=1h):
    current = prometheus.query(f"avg({metric})[5m]")
    historical = prometheus.query(f"avg({metric})[{window}]")
    
    mean = historical.mean()
    stddev = historical.stddev()
    z_score = (current - mean) / stddev
    
    if abs(z_score) > ANOMALY_THRESHOLD:
        // Check seasonal pattern
        same_time_yesterday = prometheus.query(f"{metric}[5m] offset 1d")
        if not withinExpectedRange(current, same_time_yesterday):
            fireAlert(ANOMALY_ALERT, {
                metric, z_score, current, expected: mean
            })

function correlateAnomalies(anomalies):
    // Group anomalies by time window
    groups = groupByTimeProximity(anomalies, window=5min)
    
    for group in groups:
        // Find common cause
        root_cause = analyzeCorrelation(group)
        if root_cause.confidence > 0.8:
            enrichAlert(group, root_cause)
```

## Performance Targets

| Metric | Target |
|--------|--------|
| Scrape interval | 15 seconds |
| Query latency (simple) | < 100ms |
| Query latency (complex) | < 1 second |
| Alert detection | < 1 minute |
| Dashboard refresh | < 5 seconds |
