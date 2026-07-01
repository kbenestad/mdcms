---
title: Architecture
sort: 120
section-id: overview
keywords: architecture, storage engine, query planner, replication, WAL, HNSW
description: NeuralDB internal architecture — storage engine, query planner, and replication
language: en
---

# Architecture

![NeuralDB Architecture](assets/images/architecture.jpg)

NeuralDB is built on a custom storage engine that co-locates relational and vector data, with a query planner that understands both SQL predicates and vector similarity operations natively.

## High-Level Architecture

```
Client (psql / SDK / REST)
         │
         ▼
┌─────────────────────────────────────────┐
│            Connection Layer             │
│  (PostgreSQL Wire Protocol compatible)  │
└───────────────────┬─────────────────────┘
                    │
         ┌──────────▼──────────┐
         │    Query Parser     │
         │  (SQL + NQL ext.)   │
         └──────────┬──────────┘
                    │
         ┌──────────▼──────────┐
         │   Semantic Planner  │◄── Statistics + Index Metadata
         │ (hybrid cost model) │
         └──────────┬──────────┘
                    │
         ┌──────────▼──────────┐
         │   Execution Engine  │
         │  ┌────────────────┐ │
         │  │ SQL Executor   │ │
         │  └────────────────┘ │
         │  ┌────────────────┐ │
         │  │ ANN Executor   │ │
         │  └────────────────┘ │
         └──────────┬──────────┘
                    │
         ┌──────────▼──────────┐
         │   Storage Engine    │
         │  ┌────────────────┐ │
         │  │ Row Store      │ │◄── SST Files (columnar)
         │  └────────────────┘ │
         │  ┌────────────────┐ │
         │  │ Vector Store   │ │◄── HNSW Graph Files
         │  └────────────────┘ │
         │  ┌────────────────┐ │
         │  │ WAL            │ │◄── Write-Ahead Log
         │  └────────────────┘ │
         └─────────────────────┘
```

## Storage Engine

### Row Store

NeuralDB's row store uses a Log-Structured Merge-tree (LSM) architecture inspired by RocksDB. Data is written to an in-memory write buffer (MemTable), which is periodically flushed to sorted string tables (SSTables) on disk. Background compaction merges SSTables and reclaims space.

Key properties:
- **Write-optimised**: writes are sequential, not random — excellent NVMe utilisation
- **Columnar format**: SSTables store data column-by-column for fast analytical scans
- **Compression**: LZ4 by default, Zstd for archival storage — typically 3–6× compression ratio

### Vector Store

Vectors are stored separately from rows in a Vector Store. The Vector Store maintains:

1. **Raw vector data** — the float32 arrays, stored in compressed pages
2. **HNSW graph** — the in-memory navigation graph for ANN search

The HNSW graph is loaded into memory on startup and kept warm. Memory required ≈ `num_vectors × dimensions × 4 bytes × 1.3` (1.3× overhead for the graph structure).

For a 10M-row table with 1536-dimensional embeddings: `10M × 1536 × 4 × 1.3 ≈ 80 GB`. Plan memory accordingly.

### Write-Ahead Log (WAL)

All writes (row and vector) are first written to the WAL before being applied to the storage engine. The WAL provides:

- **Durability**: committed transactions survive crashes
- **Replication**: replicas apply the WAL stream from the primary
- **Point-in-time recovery (PITR)**: archive the WAL to recover to any point in time

WAL segments are 128 MB by default and are archived to the configured storage backend (local disk, S3, GCS) upon rotation.

## Query Planner

The Semantic Planner extends a PostgreSQL-compatible query planner with understanding of vector operations.

### Hybrid Cost Model

For hybrid queries (vector + relational), the planner considers two physical plans:

**Plan A: Pre-filter**
```
Filter(price < 100) → ANN(embedding, k=10)
```
Cost: selectivity × full_scan_cost + ANN_cost(filtered_set)

**Plan B: Post-filter**
```
ANN(embedding, k=10×estimated_filter_ratio) → Filter(price < 100)
```
Cost: ANN_cost(full_index) + filter_cost

The planner uses column statistics (histogram, null fraction, distinct values) and vector index parameters to estimate costs. It picks the plan with the lower estimated cost.

### Index Types

NeuralDB supports the following index types:

| Index | Data | Purpose |
|-------|------|---------|
| B-tree | Scalar columns | Equality, range queries |
| Hash | Scalar columns | Equality only (faster than B-tree) |
| GIN | JSON, arrays | Containment queries |
| HNSW | VECTOR columns | Approximate nearest neighbour |
| IVF-Flat | VECTOR columns | High-recall exact-ish search |
| BRIN | Timestamp columns | Range scans on append-only data |

## Replication

NeuralDB uses streaming replication. The primary continuously ships WAL segments to replicas, which apply them in order.

### Synchronous vs Asynchronous Replication

```sql
-- Set replication mode per-transaction
SET synchronous_commit = 'on';    -- wait for WAL to reach all sync replicas (safest)
SET synchronous_commit = 'local'; -- wait for local WAL flush only (faster)
SET synchronous_commit = 'off';   -- don't wait (fastest, small durability window)
```

### Read Replicas

Replicas accept `SELECT` queries. Direct read-heavy workloads to replicas:

```
primary:   write queries + critical reads
replica-1: analytical queries, reporting
replica-2: search API traffic
```

The client SDK supports automatic read/write splitting:

```python
client = NeuralDB(
    primary="primary.example.com:5432",
    replicas=["replica1.example.com:5432", "replica2.example.com:5432"],
    read_from="replicas",
    replica_selection="round-robin",
)
```

## Memory Architecture

NeuralDB divides available memory into three pools:

| Pool | Purpose | Default |
|------|---------|---------|
| `shared_buffers` | Row store page cache | 25% of RAM |
| `vector_buffer` | HNSW graph warm cache | 40% of RAM |
| `work_mem` | Per-query sort and hash buffers | 64 MB |

Tune these in `neuraldb.conf`:

```ini
shared_buffers = 8GB
vector_buffer = 16GB
work_mem = 128MB
```

## Consistency Model

NeuralDB provides **strong consistency** for primary reads and **eventual consistency** for replica reads (with a configurable replication lag threshold).

Reads on the primary always see the latest committed data. Reads on replicas may lag behind the primary by the `max_replication_lag` setting (default: 1 second). To force a replica to wait until it is caught up:

```sql
SELECT pg_wait_for_replica_replay('0/1234ABCD');
```
