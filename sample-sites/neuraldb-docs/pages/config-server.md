---
title: Server Config
sort: 100
section-id: configuration
keywords: neuraldb.conf, server configuration, settings, parameters, tuning
description: Complete reference for neuraldb.conf — all server configuration settings explained
language: en
---

# Server Config

NeuralDB is configured through `neuraldb.conf`, a key-value text file. This page documents all configuration parameters.

## Locating the Config File

```bash
# Show the active config file path
neuraldb-cli -c "SHOW config_file;"
```

Default locations:
- Linux: `/etc/neuraldb/neuraldb.conf`
- macOS Homebrew: `$(brew --prefix)/etc/neuraldb/neuraldb.conf`
- Docker: `/var/lib/neuraldb/data/neuraldb.conf`

Changes to `neuraldb.conf` require a reload (for most parameters) or a restart:

```bash
# Reload without restart (applies most parameters)
neuraldb-cli -c "SELECT pg_reload_conf();"

# Full restart (required for listen_addresses, port, shared_buffers, etc.)
systemctl restart neuraldb
```

## Connection Settings

```ini
# Network interface to listen on
# '*' = all interfaces, 'localhost' = local only
listen_addresses = '*'

# TCP port
port = 5432

# Maximum simultaneous connections
# Each connection uses ~5 MB of memory
max_connections = 100

# Unix domain socket directory (Linux/macOS only)
unix_socket_directories = '/var/run/neuraldb'

# Superuser reserved connections
# Reserves this many connections exclusively for superusers
superuser_reserved_connections = 3
```

## Memory Settings

These are the most impactful parameters for performance.

```ini
# Page cache for relational data (row store)
# Recommended: 25% of available RAM
shared_buffers = 4GB

# Memory for HNSW vector indexes
# Recommended: 40-60% of available RAM for vector-heavy workloads
# Must be large enough to fit all active HNSW graphs
vector_buffer = 8GB

# Per-query working memory (sorts, hash joins)
# Recommended: 64MB–256MB for OLTP, more for analytical queries
# Be conservative: (max_connections × work_mem) should fit in RAM
work_mem = 128MB

# Memory for DDL maintenance (CREATE INDEX, VACUUM, etc.)
maintenance_work_mem = 2GB

# Shared memory for parallel query workers
parallel_query_mem = 512MB
```

## Vector Settings

```ini
# Default HNSW ef_search parameter (candidates evaluated per query)
# Higher = better recall, slower queries
hnsw.ef_search = 40

# Maximum number of vectors per shard before auto-splitting
vector_shard_size = 10000000

# Enable approximate nearest neighbour by default (true = HNSW index)
# Set to 'exact' to always use exact search (ignores vector indexes)
vector_scan = 'approximate'

# Number of parallel threads for HNSW index builds
hnsw.build_threads = 4

# Compression algorithm for stored vector data
# 'none', 'lz4', 'scalar_quantize' (lossy but 4× smaller)
vector_compression = 'lz4'
```

## WAL Settings

```ini
# WAL logging level
# 'minimal': minimum for crash recovery
# 'replica': enables streaming replication (default)
# 'logical': enables logical replication and CDC
wal_level = replica

# WAL segment size (change requires initdb)
wal_segment_size = 128MB

# Maximum number of concurrent WAL sender processes
max_wal_senders = 10

# Number of WAL segments to keep for standby catching up
wal_keep_size = 1GB

# Synchronise WAL to disk before acknowledging commit
# 'on': safest; 'local': only local disk; 'off': async (fastest, tiny durability risk)
synchronous_commit = on

# Interval between WAL checkpoints
checkpoint_timeout = 5min
checkpoint_completion_target = 0.9
max_wal_size = 4GB
```

## Replication Settings

```ini
# Comma-separated list of standby names that must acknowledge writes
# Leave empty for asynchronous replication
synchronous_standby_names = ''

# Maximum lag allowed before primary throttles writes
max_standby_lag = 30s

# Hot standby: allow reads on replicas
hot_standby = on
```

## Query Planner

```ini
# Estimated cost of a random page fetch (tune based on SSD vs HDD)
# Lower values favour index scans; higher values favour sequential scans
random_page_cost = 1.1    # NVMe SSD (default is 4.0 for HDD)

# Effective size of the disk cache (affects planner estimates)
effective_cache_size = 24GB   # ~75% of RAM

# Enable parallel query
max_parallel_workers_per_gather = 4
max_parallel_workers = 8
max_worker_processes = 16

# Hybrid query planner behaviour
# 'auto': planner decides pre-filter vs post-filter
# 'pre-filter': always pre-filter
# 'post-filter': always post-filter
vector_hybrid_strategy = 'auto'
```

## Logging

```ini
# Log destination
log_destination = 'stderr'    # 'stderr', 'csvlog', 'jsonlog', 'syslog'

# Minimum severity to log
# 'DEBUG5' (verbose) → 'INFO' → 'WARNING' → 'ERROR' → 'FATAL'
log_min_messages = WARNING

# Log all SQL statements with duration above this threshold (ms)
# -1 = disable; 0 = log everything; 250 = log slow queries only
log_min_duration_statement = 250

# Log query parameters
log_parameters = off

# Log connection events
log_connections = on
log_disconnections = on

# Log lock waits longer than this (ms)
deadlock_timeout = 1s
log_lock_waits = on
```

## Full Configuration Example

```ini
# neuraldb.conf — Production settings for a 32 vCPU / 128 GB server

listen_addresses = '*'
port = 5432
max_connections = 500
superuser_reserved_connections = 5

shared_buffers = 32GB
vector_buffer = 64GB
work_mem = 128MB
maintenance_work_mem = 4GB

wal_level = replica
max_wal_senders = 10
wal_keep_size = 2GB
synchronous_commit = on
checkpoint_timeout = 10min
max_wal_size = 8GB

random_page_cost = 1.1
effective_cache_size = 96GB
max_parallel_workers_per_gather = 8
max_parallel_workers = 16

hnsw.ef_search = 80
vector_compression = lz4

log_min_duration_statement = 500
log_connections = on
```
