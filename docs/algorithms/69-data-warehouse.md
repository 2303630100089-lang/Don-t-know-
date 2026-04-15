# 69. Algorithm: Data Warehouse

## Overview

Data warehouse algorithm covering ETL pipeline design, batch and stream ingestion, Hive/Presto storage, fast query execution, and BI dashboard integration.

## Algorithm Steps

### Step 1: ETL Pipeline
- **Extract**: Pull data from operational databases, APIs, event streams, files.
- **Transform**: Clean, normalize, deduplicate, join, and aggregate data.
- **Load**: Write transformed data to warehouse in optimized format.
- **Orchestration**: Apache Airflow DAGs for scheduling and dependency management.
- **Monitoring**: Pipeline health, data freshness, SLA compliance.

### Step 2: Batch + Stream Ingestion
- **Batch Ingestion**: Daily/hourly full or incremental loads via Spark.
- **Stream Ingestion**: Real-time events via Kafka → Flink → warehouse.
- **Lambda Architecture**: Batch layer (accuracy) + speed layer (freshness).
- **Late Data Handling**: Watermarks and grace periods for late-arriving data.
- **Schema Evolution**: Support adding new fields without breaking queries.

### Step 3: Stored in Hive/Presto
- **Apache Hive**: Metastore for schema management, HiveQL for batch queries.
- **Presto/Trino**: Fast interactive SQL queries across data sources.
- **Storage Format**: Apache Parquet (columnar) for analytical queries.
- **Partitioning**: Date-based partitions (year/month/day) for efficient scans.
- **Bucketing**: Hash-based bucketing for join optimization.

### Step 4: Fast Queries
- **Query Optimization**: Cost-based optimizer in Presto/Trino.
- **Predicate Pushdown**: Filter at storage level to minimize data scanned.
- **Column Pruning**: Read only required columns from Parquet.
- **Caching**: Result caching for repeated queries.
- **Materialized Views**: Pre-computed aggregations for common patterns.

### Step 5: BI Dashboards
- **Tools**: Tableau, Looker, Apache Superset, Metabase.
- **Semantic Layer**: Business-friendly metric definitions.
- **Self-Service**: Drag-and-drop dashboard creation.
- **Scheduled Reports**: Automated report generation and email distribution.
- **Drill-Down**: Interactive exploration from summary to detail.

## Pseudocode

```
// ETL Pipeline (Airflow DAG)
dag = DAG("daily_warehouse_load", schedule="0 2 * * *")

extract_task = SparkTask(
    function extractData():
        users = readFromDB("users", incremental=True, since=yesterday())
        transactions = readFromDB("transactions", since=yesterday())
        events = readFromKafka("user-events", since=yesterday())
        return {users, transactions, events}
)

transform_task = SparkTask(
    function transformData(raw_data):
        // Clean
        users = raw_data.users.dropDuplicates("user_id")
        users = users.fillNA(defaults)
        
        // Join
        user_activity = raw_data.transactions
            .join(users, "user_id")
            .join(raw_data.events, "user_id")
        
        // Aggregate
        daily_summary = user_activity
            .groupBy("user_id", "date")
            .agg(
                count("transaction_id").as("txn_count"),
                sum("amount").as("total_amount"),
                countDistinct("event_type").as("distinct_actions")
            )
        
        return {users, user_activity, daily_summary}
)

load_task = SparkTask(
    function loadToWarehouse(transformed):
        for table_name, data in transformed:
            data.write
                .format("parquet")
                .partitionBy("year", "month", "day")
                .mode("append")
                .saveAsTable(f"warehouse.{table_name}")
        
        // Update Hive metastore
        hive.refreshTable(table_name)
)

quality_check = Task(
    function validateData():
        // Row count check
        assert queryCount("daily_summary WHERE date = today()") > 0
        
        // Null check
        null_rate = queryNullRate("daily_summary", "user_id")
        assert null_rate < 0.01
        
        // Freshness check
        latest = queryMax("daily_summary", "date")
        assert latest == yesterday()
)

extract_task >> transform_task >> load_task >> quality_check

// Fast Query (Presto)
function queryWarehouse(sql_query):
    plan = optimizer.optimize(sql_query)
    
    // Predicate pushdown
    plan = pushdownPredicates(plan)
    
    // Column pruning
    plan = pruneColumns(plan)
    
    // Check materialized view
    mv = findMatchingMaterializedView(plan)
    if mv:
        return queryMaterializedView(mv, plan.predicates)
    
    // Execute
    return presto.execute(plan)
```

## Performance Targets

| Metric | Target |
|--------|--------|
| ETL pipeline (daily) | < 2 hours |
| Stream ingestion latency | < 5 seconds |
| Interactive query (p50) | < 5 seconds |
| Interactive query (p99) | < 30 seconds |
| Dashboard refresh | < 10 seconds |
