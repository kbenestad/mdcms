---
title: Storage Config
sort: 120
section-id: configuration
keywords: storage, memory, disk, SSD tiers, compression, tablespace, IOPS
description: Configuring NeuralDB storage — memory tiers, disk layout, compression, and tablespaces
language: en
---

# Storage Config

NeuralDB's performance depends heavily on storage configuration. This page covers how to optimise disk layout, configure memory tiers, enable compression, and use tablespaces for data tiering.

## Disk Layout Recommendations

Separate the data directory, WAL, and vector files onto different physical disks (or at least different volumes with guaranteed IOPS):

| Directory | Recommended storage | IOPS requirement |
|-----------|--------------------|--------------------|
| `$DATADIR/base/` | NVMe SSD | High random read/write |
| `$DATADIR/wal/` | NVMe SSD (separate) | High sequential write |
| `$DATADIR/vectors/` | NVMe SSD or RAM disk | High random read |
| `$DATADIR/archive/` | HDD or object storage | Low (sequential write) |

Configure separate paths in `neuraldb.conf`:

```ini
# Separate WAL onto a dedicated volume
wal_directory = '/mnt/nvme-wal/neuraldb/wal'

# Separate vector storage
vector_data_directory = '/mnt/nvme-fast/neuraldb/vectors'

# Archive destination for WAL shipping
archive_status_directory = '/var/lib/neuraldb/archive_status'
```

## Memory Tiers

NeuralDB has three distinct memory pools:

### shared_buffers (Row Store Cache)

The page cache for relational data. Sized at 25% of available RAM for a dedicated database server:

```ini
shared_buffers = 32GB    # for a 128 GB server
```

### vector_buffer (Vector Index Cache)

Holds the HNSW graph in memory. The entire active HNSW graph must fit in `vector_buffer` for optimal performance. When the graph doesn't fit, NeuralDB falls back to disk-based graph traversal, which is 10–50× slower.

Calculate the required size:

```
vector_buffer = num_vectors × dimensions × 4 bytes × hnsw_overhead_factor
```

Where `hnsw_overhead_factor` ≈ 1.3 for default HNSW parameters (m=16).

```sql
-- Check current vector index memory usage
SELECT table_name, index_name,
       pg_size_pretty(hnsw_graph_size_bytes) AS graph_memory,
       pg_size_pretty(vector_data_size_bytes) AS data_size
FROM neuraldb_stat_vector_indexes;
```

### work_mem (Per-Query Buffer)

Used for in-memory sorts, hash joins, and bitmap operations. Set conservatively — each query can allocate multiple `work_mem` buffers:

```ini
# For 200 connections with typical 2 buffers per query:
# Max memory consumption: 200 × 2 × 128MB = 51 GB
work_mem = 128MB
```

Override per-session for analytical queries:

```sql
SET work_mem = '2GB';
SELECT ... complex analytical query ...
```

## Compression

### Row Store Compression

NeuralDB compresses SSTables on disk. Choose the algorithm based on your priorities:

```ini
# Compression algorithm for row data
# 'none': no compression (fastest reads/writes, most disk)
# 'lz4': fast, moderate compression ratio (~2-3×) — default
# 'zstd': slower compression, better ratio (~3-5×)
# 'zstd-9': high compression for archival (slow, ~6-8×)
storage_compression = lz4

# Compression level (for zstd only), 1-19
storage_compression_level = 3
```

### Vector Compression

```ini
# Vector data compression
# 'none': full precision, largest storage
# 'lz4': fast, minimal precision loss
# 'scalar_quantize': reduce to 8-bit (4× smaller, ~1% recall loss)
# 'product_quantize': very high compression, higher recall loss
vector_compression = lz4
```

To enable scalar quantisation for a specific index:

```sql
CREATE INDEX ON documents
USING hnsw (embedding vector_cosine_ops)
WITH (quantization = 'scalar');
```

Scalar-quantised indexes use 4× less memory and may be faster due to better cache utilisation, at a typical recall cost of 0.5–2%.

## Tablespaces

Use tablespaces to store different tables or indexes on different volumes:

```sql
-- Create tablespaces pointing to different mount points
CREATE TABLESPACE fast_ssd LOCATION '/mnt/nvme-fast';
CREATE TABLESPACE bulk_hdd LOCATION '/mnt/hdd-storage';

-- Create a table on fast SSD
CREATE TABLE hot_documents (
  id UUID PRIMARY KEY,
  content TEXT,
  embedding VECTOR(1536)
) TABLESPACE fast_ssd;

-- Move an index to a specific tablespace
CREATE INDEX ON hot_documents USING hnsw (embedding vector_cosine_ops)
TABLESPACE fast_ssd;

-- Move old partitions to cheaper storage
ALTER TABLE documents_2024_q1 SET TABLESPACE bulk_hdd;
```

## Table Partitioning

Partition large tables by time or tenant to improve query performance and manageability:

```sql
-- Partition documents by month
CREATE TABLE documents (
  id UUID NOT NULL DEFAULT gen_random_uuid(),
  content TEXT,
  embedding VECTOR(1536),
  tenant_id UUID,
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
) PARTITION BY RANGE (created_at);

CREATE TABLE documents_2026_01
  PARTITION OF documents
  FOR VALUES FROM ('2026-01-01') TO ('2026-02-01')
  TABLESPACE fast_ssd;

CREATE TABLE documents_2025_archive
  PARTITION OF documents
  FOR VALUES FROM ('2025-01-01') TO ('2026-01-01')
  TABLESPACE bulk_hdd;
```

## VACUUM and Autovacuum

NeuralDB inherits PostgreSQL's MVCC-based VACUUM system:

```ini
# Autovacuum settings
autovacuum = on
autovacuum_naptime = 1min
autovacuum_vacuum_threshold = 50
autovacuum_vacuum_scale_factor = 0.05    # vacuum when 5% of rows are dead
autovacuum_analyze_threshold = 50
autovacuum_analyze_scale_factor = 0.02   # analyse when 2% of rows change

# For high-write tables, increase autovacuum aggressiveness
autovacuum_vacuum_cost_delay = 2ms       # default: 20ms
autovacuum_vacuum_cost_limit = 400       # default: 200
```

Manually vacuum a table:

```sql
VACUUM ANALYZE documents;         -- reclaim space + update statistics
VACUUM FULL documents;            -- full rewrite (blocking, very thorough)
```

## Monitoring Disk Usage

```sql
-- Table sizes
SELECT table_name,
       pg_size_pretty(pg_total_relation_size(quote_ident(table_name))) AS total,
       pg_size_pretty(pg_relation_size(quote_ident(table_name))) AS table,
       pg_size_pretty(pg_total_relation_size(quote_ident(table_name))
         - pg_relation_size(quote_ident(table_name))) AS indexes
FROM information_schema.tables
WHERE table_schema = 'public'
ORDER BY pg_total_relation_size(quote_ident(table_name)) DESC;

-- Vector index sizes
SELECT * FROM neuraldb_stat_vector_indexes
ORDER BY hnsw_graph_size_bytes DESC;

-- Bloat estimate
SELECT tablename, n_dead_tup, last_vacuum, last_autovacuum
FROM pg_stat_user_tables
ORDER BY n_dead_tup DESC;
```
