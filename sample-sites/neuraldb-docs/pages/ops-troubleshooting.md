---
title: Troubleshooting
sort: 140
section-id: operations
keywords: troubleshooting, errors, diagnostics, FAQ, common problems, debug
description: Common NeuralDB errors, diagnostic techniques, and frequently asked questions
language: en
---

# Troubleshooting

This page covers common NeuralDB errors and how to diagnose and resolve them.

## Connection Issues

### `FATAL: password authentication failed for user "neuraldb"`

The password is incorrect or the user doesn't exist.

```bash
# Reset the password as the OS postgres user
sudo -u neuraldb neuraldb-cli
```

```sql
ALTER USER neuraldb PASSWORD 'new-password';
```

Check `pg_hba.conf` — ensure the correct authentication method is used for the client's IP address.

### `FATAL: no pg_hba.conf entry for host "x.x.x.x", user "neuraldb"`

The client's IP is not in `pg_hba.conf`:

```
# Add to pg_hba.conf
host  all  all  x.x.x.x/32  scram-sha-256
```

Reload: `SELECT pg_reload_conf();`

### `could not connect to server: Connection refused`

NeuralDB is not running on the expected host/port:

```bash
# Check process
systemctl status neuraldb
# or
ps aux | grep neuraldb

# Check listening port
ss -tlnp | grep 5432

# Check logs
journalctl -u neuraldb -n 50
```

### `FATAL: remaining connection slots are reserved for non-replication superuser connections`

All available connections are consumed. Use PgBouncer to pool connections, or increase `max_connections`:

```sql
-- Check current connections
SELECT count(*), state, wait_event_type FROM pg_stat_activity GROUP BY state, wait_event_type;

-- Kill idle connections
SELECT pg_terminate_backend(pid) FROM pg_stat_activity
WHERE state = 'idle' AND state_change < NOW() - INTERVAL '10 minutes';
```

## Vector Query Issues

### Slow Vector Searches

If vector queries are slow, check whether the HNSW index is being used:

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT id, embedding <=> '[...]' AS dist
FROM documents
ORDER BY embedding <=> '[...]'
LIMIT 10;
```

Look for `Index Scan using documents_embedding_idx` in the plan. If you see `Seq Scan`, the planner may have decided the index is not beneficial.

Common causes:
1. **Missing LIMIT clause**: The planner only uses the HNSW index for `ORDER BY ... LIMIT` queries.
2. **Too few rows**: For small tables, a sequential scan may be faster.
3. **HNSW graph not in memory**: Check `SELECT * FROM neuraldb_stat_vector_indexes` — if `hnsw_in_memory = false`, increase `vector_buffer`.
4. **ef_search too low**: Increase for better recall at the cost of speed.

```sql
-- Force index use for debugging
SET enable_seqscan = off;
EXPLAIN ANALYZE SELECT ... ORDER BY embedding <=> $1 LIMIT 10;
SET enable_seqscan = on;
```

### `ERROR: expected 1536 dimensions, not 768`

The vector you are inserting has a different number of dimensions than the column definition:

```sql
-- Check column definition
\d documents
-- embedding column shows VECTOR(1536)

-- You are inserting a 768-dimensional vector — check your embedding model
```

Ensure your embedding model is consistent. If you need to change models, you must re-embed all existing data.

### Low Recall on ANN Queries

If approximate queries are not returning expected results:

```sql
-- Increase ef_search for higher recall
SET hnsw.ef_search = 200;
SELECT id, content, 1 - (embedding <=> $1) AS similarity
FROM documents
ORDER BY embedding <=> $1
LIMIT 10;
```

Compare against exact search:

```sql
SET neuraldb.vector_scan = 'exact';
SELECT id, content FROM documents ORDER BY embedding <=> $1 LIMIT 10;
```

If exact search finds results that approximate search misses, increase `ef_search` or rebuild the index with a higher `m` value.

## Performance Issues

### High Memory Usage

```sql
-- Check vector index memory consumption
SELECT index_name, pg_size_pretty(hnsw_graph_size_bytes) AS graph_memory
FROM neuraldb_stat_vector_indexes
ORDER BY hnsw_graph_size_bytes DESC;

-- Check for shared_buffers usage
SELECT name, setting, unit FROM pg_settings
WHERE name IN ('shared_buffers', 'vector_buffer', 'work_mem');
```

### Disk Space Exhaustion

```sql
-- Identify large tables and indexes
SELECT tablename, pg_size_pretty(pg_total_relation_size(tablename::regclass)) AS size
FROM pg_tables WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(tablename::regclass) DESC
LIMIT 20;

-- Check WAL accumulation (often caused by idle replication slots)
SELECT slot_name, active, pg_size_pretty(pg_wal_lsn_diff(pg_current_wal_lsn(), restart_lsn)) AS lag
FROM pg_replication_slots
ORDER BY pg_wal_lsn_diff(pg_current_wal_lsn(), restart_lsn) DESC;
```

Drop inactive replication slots:

```sql
SELECT pg_drop_replication_slot('orphaned_slot_name');
```

### Long-Running Queries

```sql
-- Find queries running longer than 30 seconds
SELECT pid, now() - pg_stat_activity.query_start AS duration, query, state
FROM pg_stat_activity
WHERE state != 'idle'
  AND (now() - pg_stat_activity.query_start) > INTERVAL '30 seconds'
ORDER BY duration DESC;

-- Terminate a specific query
SELECT pg_cancel_backend(pid);    -- send SIGINT (graceful)
SELECT pg_terminate_backend(pid); -- send SIGTERM (forceful)
```

## Replication Issues

### Replication Lag Growing

```sql
-- Check lag on primary
SELECT client_addr, state, sent_lsn - replay_lsn AS lag_bytes
FROM pg_stat_replication;

-- On replica: check replay lag
SELECT now() - pg_last_xact_replay_timestamp() AS lag;
```

Causes: high write load, slow replica hardware, network saturation. Solutions: increase replica hardware, add more replicas, use async replication.

### `FATAL: the database system is not accepting connections — the database system is starting up`

NeuralDB is replaying WAL after a crash. Wait for it to complete. Check progress:

```bash
tail -f /var/log/neuraldb/neuraldb.log
```

## FAQ

**Q: Can I use NeuralDB as a drop-in replacement for PostgreSQL?**
Yes. NeuralDB implements the PostgreSQL wire protocol. Any psql-compatible client, ORM, or tool that works with PostgreSQL will work with NeuralDB.

**Q: How do I know if my HNSW index is working correctly?**
Run `EXPLAIN ANALYZE` on your vector query and look for `Index Scan using ... hnsw`. Also check `neuraldb_stat_vector_indexes` for `estimated_recall`.

**Q: What should `vector_buffer` be set to?**
Set it large enough to hold the sum of all HNSW graph sizes. Query `SELECT SUM(hnsw_graph_size_bytes) FROM neuraldb_stat_vector_indexes` to see the current total.

**Q: Can I store vectors from different embedding models in the same table?**
Only if they have the same dimensionality. Otherwise, use separate columns (e.g., `embedding_openai VECTOR(1536)` and `embedding_cohere VECTOR(1024)`).

**Q: Is NeuralDB compatible with pgvector extensions?**
NeuralDB includes native support for all pgvector data types (`VECTOR`, `HALFVEC`, `SPARSEVEC`) and operators (`<=>`, `<->`, `<#>`). Applications written for pgvector work without modification.
