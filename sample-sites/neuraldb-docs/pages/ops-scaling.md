---
title: Scaling
sort: 120
section-id: operations
keywords: scaling, sharding, read replicas, horizontal scaling, capacity planning, performance
description: Scaling NeuralDB horizontally with sharding, read replicas, and capacity planning
language: en
---

# Scaling

NeuralDB is designed to scale horizontally. This page covers adding read replicas for query throughput, sharding for data volume, and capacity planning to avoid resource exhaustion.

## Vertical Scaling (Scale Up)

Before adding nodes, ensure you have maximised single-node performance:

### Memory

The biggest lever for NeuralDB performance is memory. Ensure:
- `vector_buffer` is large enough to hold all active HNSW graphs
- `shared_buffers` is set to 25% of RAM
- `work_mem` is appropriate for your query patterns

```sql
-- Check if vectors are being served from disk (slow) vs memory (fast)
SELECT index_name, hnsw_graph_size_bytes, hnsw_in_memory
FROM neuraldb_stat_vector_indexes
ORDER BY hnsw_graph_size_bytes DESC;
```

If `hnsw_in_memory = false`, increase `vector_buffer`.

### CPU

Vector ANN searches are CPU-bound. Enable parallel query:

```ini
max_parallel_workers_per_gather = 8
max_parallel_workers = 16
```

```sql
-- Allow parallel ANN queries for large tables
SET max_parallel_workers_per_gather = 8;
SELECT * FROM large_table ORDER BY embedding <=> $1 LIMIT 10;
```

### Storage I/O

Use NVMe SSDs with high IOPS. Configure the OS:

```bash
# Increase read-ahead for sequential I/O
sudo blockdev --setra 1024 /dev/nvme0n1

# Use deadline/mq-deadline I/O scheduler
echo "mq-deadline" | sudo tee /sys/block/nvme0n1/queue/scheduler

# Disable transparent huge pages (reduces latency variability)
echo never | sudo tee /sys/kernel/mm/transparent_hugepage/enabled
```

## Read Replicas

Add read replicas to distribute query load.

### Setting Up Read Replicas

Follow the [Replication guide](config-replication.md) to add replicas. Each replica can independently serve `SELECT` queries, including vector similarity searches.

### Client-Side Read Splitting

Configure your application to route reads to replicas:

**Python:**
```python
from neuraldb import NeuralDB

primary = NeuralDB("postgresql://neuraldb:pass@primary:5432/mydb")
replica = NeuralDB("postgresql://neuraldb:pass@replica:5432/mydb")

def search(query_vector):
    # Read goes to replica
    return replica.query("SELECT * FROM docs ORDER BY embedding <=> %s LIMIT 10", [query_vector])

def insert(content, embedding):
    # Write goes to primary
    return primary.execute("INSERT INTO docs (content, embedding) VALUES (%s, %s)", [content, embedding])
```

**Connection string with `target_session_attrs`:**
```
postgresql://neuraldb:pass@primary:5432,replica:5432/mydb?target_session_attrs=prefer-standby
```

### Read Replica Scaling Targets

| Replicas | Approximate peak QPS (1536-dim, 10M vectors) |
|---------|----------------------------------------------|
| 1 primary | 8,000 |
| 1 primary + 2 replicas | 24,000 |
| 1 primary + 4 replicas | 48,000 |
| 1 primary + 8 replicas | 96,000 |

## Horizontal Sharding

For datasets exceeding single-node capacity (>50M vectors or >5 TB), shard across multiple primary nodes.

### Shard Configuration

```sql
-- Create a sharded cluster (requires NeuralDB Cluster Edition)
SELECT neuraldb_cluster.init_cluster(
  shards => 8,
  replication_factor => 2
);

-- Create a sharded table
CREATE TABLE documents (
  id UUID NOT NULL DEFAULT gen_random_uuid(),
  tenant_id UUID NOT NULL,
  content TEXT,
  embedding VECTOR(1536)
) SHARD BY tenant_id;

-- Each shard holds ~1/8 of the data
-- All rows with the same tenant_id are colocated on the same shard
```

### Cross-Shard Queries

Cross-shard queries (where the filter doesn't align with the shard key) are automatically parallelised across shards:

```sql
-- This query executes on all 8 shards in parallel
SELECT id, content, 1 - (embedding <=> $1) AS similarity
FROM documents
ORDER BY embedding <=> $1
LIMIT 10;
-- Results are merged and re-ranked by the coordinator
```

Performance with 8 shards: near-linear scaling. An 8-shard cluster serves ~8× the QPS of a single node for cross-shard searches, with ~20% overhead for coordination.

### Shard Rebalancing

When adding new shard nodes, rebalance data:

```sql
-- Rebalance shards (online, non-blocking)
SELECT neuraldb_cluster.rebalance_shards();

-- Monitor progress
SELECT * FROM neuraldb_cluster.rebalance_status;
```

## Capacity Planning

### Storage Capacity

Estimate required storage:

```
Row data ≈ avg_row_size_bytes × num_rows × 1.3 (index overhead)
Vector data ≈ dimensions × 4 bytes × num_vectors
HNSW graph ≈ dimensions × 4 bytes × num_vectors × 1.3
WAL ≈ daily_write_volume × wal_retention_days

Total ≈ row_data + vector_data + HNSW_graph + WAL + 20% buffer
```

Example: 100M rows, 1536 dimensions, 500 bytes average row size:
- Row data: 500B × 100M × 1.3 ≈ **65 GB**
- Vector data: 1536 × 4B × 100M ≈ **614 GB**
- HNSW graph: 614 GB × 1.3 ≈ **800 GB** (must fit in `vector_buffer`)
- WAL (7 days): 10 GB/day × 7 = **70 GB**
- **Total: ~1.6 TB storage, 800 GB RAM for HNSW**

### Connection Capacity

```
max_connections = max_app_connections + pgbouncer_pool_size + replication_slots + 3 (superuser)
```

For 500 app connections through PgBouncer with pool size 20:
```
max_connections = 20 + 10 (replicas) + 3 = 33
```

PgBouncer multiplexes 500 app connections → 20 database connections.

### Alert Thresholds

| Resource | Warning | Critical |
|---------|---------|---------|
| Connections | 80% of max | 95% of max |
| Storage | 70% full | 85% full |
| vector_buffer utilisation | 80% | 90% |
| Replication lag | 30s | 120s |
| Query p99 latency | 500ms | 2000ms |
