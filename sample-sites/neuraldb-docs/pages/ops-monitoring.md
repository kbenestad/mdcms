---
title: Monitoring
sort: 100
section-id: operations
keywords: monitoring, Prometheus, Grafana, metrics, alerts, observability, dashboards
description: Monitoring NeuralDB with Prometheus metrics, Grafana dashboards, and alert configuration
language: en
---

# Monitoring

![NeuralDB Dashboard](assets/images/dashboard.jpg)

Observability is critical for database operations. NeuralDB exposes Prometheus-compatible metrics and provides an official Grafana dashboard for real-time monitoring.

## Prometheus Metrics

NeuralDB exposes metrics at `http://localhost:9187/metrics` (via the bundled exporter).

Enable the metrics exporter:

```ini
# neuraldb.conf
metrics.enabled = true
metrics.port = 9187
metrics.path = /metrics
```

Or run the standalone exporter:

```bash
neuraldb_exporter \
  --web.listen-address=:9187 \
  --db.uri="postgresql://monitor:password@localhost:5432/neuraldb?sslmode=disable"
```

### Key Metrics

#### Connection Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `neuraldb_connections_total` | Gauge | Current connections by state |
| `neuraldb_connections_max` | Gauge | `max_connections` setting |
| `neuraldb_connection_pool_waiting` | Gauge | Queries waiting for a connection |

#### Query Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `neuraldb_queries_total` | Counter | Total queries by database and status |
| `neuraldb_query_duration_seconds` | Histogram | Query duration (p50, p95, p99) |
| `neuraldb_slow_queries_total` | Counter | Queries exceeding `log_min_duration_statement` |
| `neuraldb_deadlocks_total` | Counter | Deadlocks detected |

#### Vector Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `neuraldb_vector_queries_total` | Counter | Vector similarity queries by index |
| `neuraldb_vector_query_duration_seconds` | Histogram | ANN query latency |
| `neuraldb_hnsw_index_size_bytes` | Gauge | In-memory size of HNSW graphs |
| `neuraldb_hnsw_build_duration_seconds` | Histogram | Time to build HNSW indexes |
| `neuraldb_vector_recall_ratio` | Gauge | Estimated recall for ANN queries |

#### Replication Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `neuraldb_replication_lag_bytes` | Gauge | WAL lag per replica |
| `neuraldb_replication_lag_seconds` | Gauge | Time lag per replica |
| `neuraldb_wal_size_bytes` | Gauge | Current WAL on-disk size |

#### Storage Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `neuraldb_database_size_bytes` | Gauge | Total database size |
| `neuraldb_table_size_bytes` | Gauge | Size per table |
| `neuraldb_bloat_ratio` | Gauge | Estimated dead row ratio |
| `neuraldb_checkpoint_duration_seconds` | Histogram | Checkpoint write time |

## Prometheus Configuration

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'neuraldb'
    static_configs:
      - targets: ['localhost:9187']
    scrape_interval: 15s
    metrics_path: /metrics
```

## Grafana Dashboard

Import the official NeuralDB dashboard from Grafana.com (Dashboard ID: **18921**):

```bash
# Import via Grafana API
curl -X POST \
  http://admin:password@localhost:3000/api/dashboards/import \
  -H "Content-Type: application/json" \
  -d '{ "gnetId": 18921, "overwrite": true, "inputs": [{"name": "DS_PROMETHEUS", "type": "datasource", "pluginId": "prometheus", "value": "Prometheus"}] }'
```

The dashboard includes panels for:
- Query rate and error rate
- Query latency percentiles (p50, p95, p99)
- Active connections vs max connections
- Vector index memory usage
- Replication lag
- Database and table sizes
- Cache hit ratio
- Checkpoint frequency

## Alerting Rules

Create Prometheus alerting rules for critical conditions:

```yaml
# neuraldb-alerts.yml
groups:
  - name: neuraldb
    rules:

      - alert: NeuralDBConnectionsHigh
        expr: neuraldb_connections_total{state="active"} / neuraldb_connections_max > 0.85
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "NeuralDB connections above 85%"
          description: "{{ $value | humanizePercentage }} of max connections in use"

      - alert: NeuralDBConnectionsExhausted
        expr: neuraldb_connections_total{state="active"} / neuraldb_connections_max > 0.98
        for: 30s
        labels:
          severity: critical
        annotations:
          summary: "NeuralDB connections nearly exhausted"

      - alert: NeuralDBHighQueryLatency
        expr: histogram_quantile(0.99, rate(neuraldb_query_duration_seconds_bucket[5m])) > 1.0
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "P99 query latency above 1 second"

      - alert: NeuralDBReplicationLagHigh
        expr: neuraldb_replication_lag_seconds > 30
        for: 1m
        labels:
          severity: warning
        annotations:
          summary: "Replication lag above 30 seconds"

      - alert: NeuralDBDiskSpaceHigh
        expr: (neuraldb_database_size_bytes / disk_total_bytes) > 0.80
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Database storage above 80% capacity"

      - alert: NeuralDBVectorBufferExhausted
        expr: neuraldb_hnsw_index_size_bytes > (neuraldb_vector_buffer_size_bytes * 0.90)
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "HNSW indexes using >90% of vector_buffer"
```

## Built-In Query Statistics

```sql
-- Top 10 slowest queries
SELECT query,
       calls,
       round(mean_exec_time::numeric, 2) AS avg_ms,
       round(total_exec_time::numeric, 2) AS total_ms,
       round(stddev_exec_time::numeric, 2) AS stddev_ms
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 10;

-- Cache hit ratio (should be >99%)
SELECT
  sum(blks_hit) * 100.0 / sum(blks_hit + blks_read) AS cache_hit_ratio
FROM pg_stat_database
WHERE datname != 'template0';

-- Lock waits
SELECT pid, query, state, wait_event_type, wait_event, query_start
FROM pg_stat_activity
WHERE wait_event_type = 'Lock'
ORDER BY query_start;
```

## Log-Based Alerting

Forward slow query logs to your SIEM or log aggregation system:

```ini
# neuraldb.conf
log_destination = 'jsonlog'
log_min_duration_statement = 500   # log queries slower than 500ms
log_line_prefix = '%t [%p] %u@%d '
```

Parse JSON logs in Loki or Elasticsearch and alert when the rate of slow queries exceeds a threshold.
