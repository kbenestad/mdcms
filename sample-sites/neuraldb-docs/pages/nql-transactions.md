---
title: Transactions
sort: 140
section-id: query-language
keywords: transactions, ACID, isolation levels, MVCC, BEGIN, COMMIT, ROLLBACK
description: ACID transactions in NeuralDB — isolation levels, MVCC, savepoints, and advisory locks
language: en
---

# Transactions

NeuralDB provides full ACID transactions with MVCC (Multi-Version Concurrency Control). Unlike most vector databases, NeuralDB guarantees atomicity across both relational and vector data within a single transaction.

## ACID Guarantees

| Property | Guarantee |
|----------|---------|
| **Atomicity** | All operations in a transaction succeed or all are rolled back — including vector index updates |
| **Consistency** | Constraints (foreign keys, unique indexes, not null) are enforced at commit time |
| **Isolation** | Concurrent transactions do not see each other's uncommitted changes |
| **Durability** | Committed transactions survive crashes via the WAL |

## Basic Transaction Syntax

```sql
BEGIN;

-- Your operations here
INSERT INTO documents (content, embedding) VALUES ($1, $2);
UPDATE document_stats SET total_count = total_count + 1;
INSERT INTO audit_log (action, data) VALUES ('insert', $3);

COMMIT;
```

On error, roll back:

```sql
BEGIN;

INSERT INTO documents (content, embedding) VALUES ($1, $2);

-- Something went wrong
ROLLBACK;
```

## Isolation Levels

NeuralDB supports four isolation levels. Set them with `SET TRANSACTION ISOLATION LEVEL`:

```sql
BEGIN;
SET TRANSACTION ISOLATION LEVEL READ COMMITTED;
-- ... your queries ...
COMMIT;
```

### Read Committed (Default)

Each statement sees only rows committed before that statement began. Two successive reads within the same transaction may see different data if another transaction commits between them.

```sql
BEGIN;
-- Sees all rows committed before this SELECT
SELECT COUNT(*) FROM documents;  -- Returns 1000

-- Another transaction inserts and commits a row here

-- Sees the new row (non-repeatable read)
SELECT COUNT(*) FROM documents;  -- Returns 1001
COMMIT;
```

### Repeatable Read

A transaction sees only rows committed before the transaction began. Reads are stable throughout the transaction.

```sql
BEGIN ISOLATION LEVEL REPEATABLE READ;
SELECT COUNT(*) FROM documents;  -- Returns 1000

-- Another transaction inserts and commits

SELECT COUNT(*) FROM documents;  -- Still 1000 — repeatable read
COMMIT;
```

### Serializable

The strictest level. Transactions execute as if they ran serially one after another. NeuralDB uses Serializable Snapshot Isolation (SSI) — it allows concurrent execution but detects and aborts transactions that would produce a non-serializable outcome.

```sql
BEGIN ISOLATION LEVEL SERIALIZABLE;
-- ... complex read-modify-write patterns ...
COMMIT;
-- May raise: ERROR: could not serialize access — retry the transaction
```

### Read Uncommitted

NeuralDB maps this to Read Committed (it does not implement dirty reads).

## Retry Logic

Serializable transactions can fail with serialization errors. Always retry:

```python
from psycopg2 import errors

MAX_RETRIES = 5

for attempt in range(MAX_RETRIES):
    try:
        with conn.cursor() as cur:
            cur.execute("BEGIN ISOLATION LEVEL SERIALIZABLE")
            # ... your operations ...
            cur.execute("COMMIT")
        break
    except errors.SerializationFailure:
        conn.rollback()
        if attempt == MAX_RETRIES - 1:
            raise
        time.sleep(0.1 * (2 ** attempt))  # exponential backoff
```

## Savepoints

Savepoints allow partial rollbacks within a transaction:

```sql
BEGIN;

INSERT INTO documents (content, embedding) VALUES ($1, $2);

SAVEPOINT after_insert;

-- Risky operation
UPDATE document_stats SET count = count + 1 WHERE id = $3;

-- Oh no, something went wrong — roll back to the savepoint
ROLLBACK TO SAVEPOINT after_insert;

-- The INSERT is still pending — we can try a different approach
UPDATE document_stats SET count = count + 1 WHERE id = $4;

COMMIT;
```

## Vector Transactions

Vector index updates are transactional in NeuralDB. An HNSW index entry is added atomically with the row:

```sql
BEGIN;

-- Both the row and the vector index entry are inserted atomically
INSERT INTO documents (id, content, embedding) VALUES ($1, $2, $3);

-- If we ROLLBACK, neither the row nor the index entry will exist
ROLLBACK;

-- After rollback, a similarity search will NOT find $1
SELECT id FROM documents ORDER BY embedding <=> $3 LIMIT 1;
-- $1 is not returned
```

## Long-Running Transactions

Avoid long-running transactions — they:
- Hold row-level locks, blocking other writes
- Prevent VACUUM from reclaiming dead rows (bloat)
- Increase the risk of deadlocks

Set a statement timeout to kill runaway queries:

```sql
SET statement_timeout = '30s';
```

Set a transaction timeout:

```sql
SET idle_in_transaction_session_timeout = '5min';
```

## Deadlock Detection

NeuralDB automatically detects deadlocks and aborts one of the transactions:

```
ERROR: deadlock detected
DETAIL: Process 12345 waits for ShareLock on transaction 67890; blocked by process 99999.
Hint: See server log for query details.
```

Minimise deadlock risk by always acquiring locks in the same order across all transactions.

## Advisory Locks

For application-level locking (e.g., ensuring only one worker processes a job):

```sql
-- Acquire a session-level advisory lock (blocks until acquired)
SELECT pg_advisory_lock(42);

-- Try to acquire (returns false if already held)
SELECT pg_try_advisory_lock(42);  -- returns boolean

-- Release
SELECT pg_advisory_unlock(42);

-- Transaction-level (auto-released at commit/rollback)
SELECT pg_advisory_xact_lock(42);
```

## Two-Phase Commit (2PC)

For distributed transactions spanning multiple systems:

```sql
-- Phase 1: Prepare
BEGIN;
-- ... operations ...
PREPARE TRANSACTION 'my-distributed-txn-id';

-- Phase 2: Commit or rollback
COMMIT PREPARED 'my-distributed-txn-id';
-- or
ROLLBACK PREPARED 'my-distributed-txn-id';
```

Check pending prepared transactions:

```sql
SELECT gid, prepared, owner, database
FROM pg_prepared_xacts;
```
