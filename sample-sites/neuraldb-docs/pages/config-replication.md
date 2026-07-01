---
title: Replication
sort: 130
section-id: configuration
keywords: replication, primary, replica, streaming replication, multi-region, consistency
description: Configuring NeuralDB replication — primary/replica setup, multi-region, and consistency levels
language: en
---

# Replication

NeuralDB replication is based on streaming replication: the primary continuously ships WAL records to replicas, which apply them in real time. This page explains how to set up and configure replication.

## Prerequisites

- The primary must have `wal_level = replica` or higher
- `max_wal_senders` must be greater than the number of replicas
- A replication user must exist

## Setting Up a Primary

Configure `neuraldb.conf` on the primary:

```ini
# neuraldb.conf (primary)
wal_level = replica
max_wal_senders = 10
max_replication_slots = 10
wal_keep_size = 1GB
hot_standby_feedback = on    # prevents primary from vacuuming rows still needed by replicas
```

Create a replication user:

```sql
CREATE USER replicator WITH REPLICATION PASSWORD 'repl-password';
```

Allow the replica to connect:

```
# pg_hba.conf (primary)
host  replication  replicator  replica-ip/32  scram-sha-256
```

## Setting Up a Replica

On the replica server, use `pg_basebackup` to clone the primary:

```bash
# On the replica server
pg_basebackup \
  --host=primary.example.com \
  --port=5432 \
  --username=replicator \
  --pgdata=/var/lib/neuraldb/data \
  --wal-method=stream \
  --checkpoint=fast \
  --progress \
  --write-recovery-conf
```

The `--write-recovery-conf` flag creates a `standby.signal` file and writes connection info to `postgresql.auto.conf`, which tells NeuralDB to start in standby mode.

Configure `neuraldb.conf` on the replica:

```ini
# neuraldb.conf (replica)
hot_standby = on                    # allow read queries
hot_standby_feedback = on           # send feedback to primary
wal_receiver_timeout = 60s
recovery_min_apply_delay = 0        # apply WAL immediately (increase for delayed replicas)
```

Start the replica:

```bash
systemctl start neuraldb
```

Verify replication is working:

```sql
-- On the primary
SELECT client_addr, state, sent_lsn, write_lsn, flush_lsn, replay_lsn,
       (sent_lsn - replay_lsn) AS replication_lag_bytes
FROM pg_stat_replication;
```

## Replication Slots

Replication slots ensure the primary retains WAL until the replica has consumed it. This prevents the replica from falling too far behind, but also prevents WAL from being cleaned up if the replica disconnects.

```sql
-- Create a replication slot
SELECT pg_create_physical_replication_slot('replica_1');

-- List slots and their lag
SELECT slot_name, active, pg_size_pretty(pg_wal_lsn_diff(pg_current_wal_lsn(), restart_lsn)) AS lag
FROM pg_replication_slots;

-- Drop a slot (do this if a replica is permanently removed)
SELECT pg_drop_replication_slot('replica_1');
```

**Warning:** Monitor slot lag. An inactive slot with large lag will cause unbounded WAL accumulation and can fill your disk.

## Synchronous Replication

By default, replication is asynchronous — the primary does not wait for replicas to acknowledge writes. For zero data loss, configure synchronous replication:

```ini
# neuraldb.conf (primary)
synchronous_standby_names = 'FIRST 1 (replica1, replica2)'
# ^ Wait for at least 1 of the listed standbys to acknowledge each commit
```

Modes:
- `FIRST n (list)` — wait for the first n standbys in the list
- `ANY n (list)` — wait for any n standbys from the list
- `*` — wait for all standbys

Per-transaction override:

```sql
SET synchronous_commit = 'local';   -- this transaction doesn't wait for replicas
```

## Multi-Region Replication

For global deployments, replicate to remote regions. The configuration is identical to local replication, but network latency affects synchronous commit performance.

Recommended approach for multi-region:

```
Primary (us-east-1)
├── Sync replica (us-east-1-az2)    ← HA within region, ~2ms latency
├── Async replica (eu-west-1)       ← EU reads, ~80ms latency
└── Async replica (ap-northeast-1)  ← APAC reads, ~170ms latency
```

```ini
# Synchronous only within region; async to remote regions
synchronous_standby_names = 'FIRST 1 (local_replica)'
```

Configure the remote replicas with a `primary_conninfo` pointing to the primary:

```ini
# standby.signal (on replica)
primary_conninfo = 'host=primary.us-east-1.example.com port=5432 user=replicator password=repl-password sslmode=require'
```

## Failover

NeuralDB does not include automatic failover out of the box. Use one of:

- **Patroni** — industry-standard HA manager for PostgreSQL-compatible databases
- **NeuralDB HA Operator** — Kubernetes operator with automatic failover (see [Kubernetes docs](install-kubernetes.md))
- **repmgr** — lightweight failover manager

Manual failover:

```bash
# On the replica that will become the new primary
neuraldb-cli -c "SELECT pg_promote();"
```

After promotion, update `primary_conninfo` on all other replicas to point to the new primary.

## Monitoring Replication

```sql
-- Replication lag in bytes and seconds
SELECT client_addr, state,
  pg_size_pretty(sent_lsn - replay_lsn) AS lag_bytes,
  now() - pg_last_xact_replay_timestamp() AS lag_time
FROM pg_stat_replication;

-- On a replica: check its own lag
SELECT now() - pg_last_xact_replay_timestamp() AS lag,
       pg_is_in_recovery() AS is_replica;
```

Set up an alert when replication lag exceeds 30 seconds.
