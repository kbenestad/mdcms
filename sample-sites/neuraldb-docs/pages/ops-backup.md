---
title: Backup & Restore
sort: 110
section-id: operations
keywords: backup, restore, snapshot, WAL archiving, PITR, point-in-time recovery
description: Backup and restore strategies for NeuralDB — snapshots, WAL archiving, and point-in-time recovery
language: en
---

# Backup & Restore

A comprehensive backup strategy for NeuralDB combines base snapshots with continuous WAL archiving, enabling point-in-time recovery (PITR) to any moment within your retention window.

## Backup Strategies

| Strategy | Recovery point objective | Recovery time | Storage |
|----------|--------------------------|---------------|---------|
| Snapshot only | Time of last snapshot | Fast | Medium |
| WAL archiving only | Continuous (any point) | Slow | High |
| Snapshot + WAL | Best of both | Fast | High |

**Recommendation:** Use snapshot + WAL archiving in production. Take daily base snapshots and archive WAL continuously.

## Physical Snapshot (pg_basebackup)

`pg_basebackup` creates a consistent physical copy of the data directory:

```bash
# Full backup — local filesystem
pg_basebackup \
  --host=localhost \
  --port=5432 \
  --username=backup_user \
  --pgdata=/backups/neuraldb/$(date +%Y%m%d) \
  --wal-method=stream \
  --checkpoint=fast \
  --compress=lz4 \
  --progress \
  --verbose

# Full backup — tar format (smaller, easier to upload to S3)
pg_basebackup \
  --host=localhost \
  --pgdata=- \
  --format=tar \
  --wal-method=stream \
  --compress=lz4 \
  | aws s3 cp - s3://my-backups/neuraldb/base-$(date +%Y%m%d).tar.lz4
```

Create a dedicated backup user:

```sql
CREATE USER backup_user WITH REPLICATION PASSWORD 'backup-password';
GRANT CONNECT ON DATABASE neuraldb TO backup_user;
```

## WAL Archiving

WAL archiving copies each WAL segment to a secure location as it is completed. Combined with a base snapshot, this enables PITR.

Enable WAL archiving:

```ini
# neuraldb.conf
wal_level = replica
archive_mode = on
archive_command = 'aws s3 cp %p s3://my-backups/neuraldb/wal/%f'
archive_timeout = 60   # archive at least every 60 seconds even if no WAL activity
```

Verify archiving is working:

```sql
SELECT last_archived_wal, last_archived_time,
       last_failed_wal, last_failed_time,
       archived_count, failed_count
FROM pg_stat_archiver;
```

### S3 Archive Command

```bash
#!/bin/bash
# /usr/local/bin/neuraldb-archive.sh
# Usage: %p = source file path, %f = file name

set -e
SOURCE="$1"
DEST_FILE="$2"
S3_BUCKET="${ARCHIVE_S3_BUCKET}"
S3_PREFIX="${ARCHIVE_S3_PREFIX:-neuraldb/wal/}"

aws s3 cp "$SOURCE" "s3://${S3_BUCKET}/${S3_PREFIX}${DEST_FILE}" \
  --storage-class STANDARD_IA \
  --sse aws:kms
```

```ini
archive_command = '/usr/local/bin/neuraldb-archive.sh %p %f'
```

## Automated Backups with pgBackRest

pgBackRest is the recommended tool for production NeuralDB backups:

```bash
# Install
sudo apt install pgbackrest

# Configure
sudo tee /etc/pgbackrest/pgbackrest.conf <<'EOF'
[global]
repo1-path=/var/lib/pgbackrest
repo1-retention-full=7
repo1-retention-diff=14
repo1-type=s3
repo1-s3-bucket=my-neuraldb-backups
repo1-s3-endpoint=s3.amazonaws.com
repo1-s3-region=us-east-1
compress-type=lz4
start-fast=y
backup-standby=y

[neuraldb]
pg1-path=/var/lib/neuraldb/data
pg1-port=5432
pg1-user=backup_user
EOF

# Initialise
sudo -u postgres pgbackrest --stanza=neuraldb stanza-create

# Full backup
sudo -u postgres pgbackrest --stanza=neuraldb backup --type=full

# Differential backup (only changes since last full)
sudo -u postgres pgbackrest --stanza=neuraldb backup --type=diff

# Incremental (only changes since last backup of any type)
sudo -u postgres pgbackrest --stanza=neuraldb backup --type=incr
```

Schedule backups with cron:

```cron
# /etc/cron.d/neuraldb-backup
0 1 * * 0  postgres pgbackrest --stanza=neuraldb backup --type=full
0 1 * * 1-6 postgres pgbackrest --stanza=neuraldb backup --type=diff
```

## Point-in-Time Recovery (PITR)

To restore to a specific point in time:

```bash
# Stop NeuralDB
systemctl stop neuraldb

# Restore a base backup
pgbackrest --stanza=neuraldb restore \
  --target="2026-05-15 14:30:00+00" \
  --target-action=promote \
  --delta

# Or restore to just before a specific transaction
pgbackrest --stanza=neuraldb restore \
  --target-name="before_accidental_delete" \
  --target-action=promote

# Start NeuralDB — it will replay WAL up to the target point
systemctl start neuraldb
```

Create named restore points before risky operations:

```sql
-- Before running a migration
SELECT pg_create_restore_point('before_migration_20260515');
```

## Logical Backup (pg_dump)

For smaller databases or table-level backups, `pg_dump` provides a logical backup:

```bash
# Dump entire database
pg_dump -h localhost -U neuraldb mydb | \
  lz4 | \
  aws s3 cp - s3://my-backups/neuraldb/logical-$(date +%Y%m%d).sql.lz4

# Dump specific table
pg_dump -h localhost -U neuraldb -t documents mydb > documents-backup.sql

# Dump in custom format (best compression, selective restore)
pg_dump -Fc -h localhost -U neuraldb mydb > mydb-$(date +%Y%m%d).dump
```

**Note:** Logical backups do not include vector index data — only the raw vector column values. After restore, recreate indexes manually.

## Restoring from pg_dump

```bash
# Restore entire database
lz4 -d backup.sql.lz4 | psql -h localhost -U neuraldb -d mydb_restore

# Restore custom format
pg_restore -h localhost -U neuraldb -d mydb_restore --jobs=8 mydb.dump

# Restore a single table
pg_restore -h localhost -U neuraldb -d mydb -t documents mydb.dump
```

## Testing Backups

Never trust backups you haven't tested. Automate monthly restore tests:

```bash
#!/bin/bash
# Test backup restore in a separate environment
pgbackrest --stanza=neuraldb restore --pg1-path=/tmp/restore-test --delta
pg_ctl -D /tmp/restore-test start
psql -h /tmp/restore-test -c "SELECT COUNT(*) FROM documents;" neuraldb
pg_ctl -D /tmp/restore-test stop
rm -rf /tmp/restore-test
echo "Restore test passed: $(date)"
```
