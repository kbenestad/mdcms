---
title: Vector Queries
sort: 110
section-id: query-language
keywords: vector queries, NEAREST, SIMILAR, cosine, dot product, euclidean, ANN
description: Writing vector similarity queries in NQL — NEAREST, SIMILAR, distance operators, and recall tuning
language: en
---

# Vector Queries

NQL extends standard SQL with operators and functions for vector similarity search. This page covers every method for querying vectors, from basic nearest-neighbour lookups to advanced recall tuning.

## Distance Operators

NQL provides three distance operators that double as index-acceleration hints:

```sql
-- Cosine distance (returns 0 to 2, lower = more similar)
embedding <=> query_vector

-- Euclidean (L2) distance (returns 0 to ∞, lower = more similar)
embedding <-> query_vector

-- Negative dot product (higher inner product = more similar → negate for ORDER BY)
embedding <#> query_vector
```

Always pair `ORDER BY` with `LIMIT` when using distance operators — the planner uses the HNSW index only when there is an explicit `ORDER BY ... LIMIT`:

```sql
-- ✅ Uses HNSW index
SELECT id, content FROM documents
ORDER BY embedding <=> '[0.1, 0.2, ...]'
LIMIT 10;

-- ❌ Full scan (no ORDER BY ... LIMIT)
SELECT id, content FROM documents
WHERE (embedding <=> '[0.1, 0.2, ...]') < 0.3;
```

## NEAREST Clause

NQL provides a syntactic alternative to `ORDER BY ... LIMIT` for nearest-neighbour queries:

```sql
SELECT id, content, score
FROM documents
NEAREST TO embedding = '[0.1, 0.2, ...]' USING COSINE
TOP 10;
```

This is equivalent to:

```sql
SELECT id, content, 1 - (embedding <=> '[0.1, 0.2, ...]') AS score
FROM documents
ORDER BY embedding <=> '[0.1, 0.2, ...]'
LIMIT 10;
```

The `NEAREST TO` clause is more readable and allows NeuralDB to apply additional optimisations.

### Distance Metrics in NEAREST

```sql
NEAREST TO embedding = $1 USING COSINE TOP 10
NEAREST TO embedding = $1 USING EUCLIDEAN TOP 10
NEAREST TO embedding = $1 USING DOT_PRODUCT TOP 10
```

## SIMILAR Clause

`SIMILAR` returns results above a similarity threshold rather than a fixed count. Because the threshold is checked after the ANN search, NeuralDB must retrieve an initial candidate set. Use `LIMIT` to cap the candidates:

```sql
SELECT id, content, score
FROM documents
SIMILAR TO embedding = $1 USING COSINE THRESHOLD 0.75
LIMIT 100;
```

This returns up to 100 documents with cosine similarity ≥ 0.75.

## Returning Scores

Include the distance or similarity score in results:

```sql
-- Distance (lower = more similar)
SELECT id, content, (embedding <=> $1) AS distance
FROM documents
ORDER BY embedding <=> $1
LIMIT 10;

-- Similarity (higher = more similar, cosine)
SELECT id, content, 1 - (embedding <=> $1) AS similarity
FROM documents
ORDER BY embedding <=> $1
LIMIT 10;
```

## Querying With a Vector Literal

Pass vectors as SQL parameters (recommended) or literals:

```sql
-- Parameterised (prevents injection, preferred)
SELECT id, content FROM documents
ORDER BY embedding <=> $1
LIMIT 10;
-- $1 = '[0.023, -0.187, 0.412, ...]'

-- Inline literal (useful in SQL shells)
SELECT id, content FROM documents
ORDER BY embedding <=> '[0.023, -0.187, 0.412]'::VECTOR(3)
LIMIT 5;
```

## Recall Tuning

The HNSW index trades recall for performance. By default, `hnsw.ef_search = 40`, which provides ~95% recall at ~1ms latency for 10M vectors.

Increase `ef_search` for higher recall:

```sql
-- Set for the current session
SET hnsw.ef_search = 200;

-- Set for the current transaction
BEGIN;
SET LOCAL hnsw.ef_search = 200;
SELECT * FROM documents ORDER BY embedding <=> $1 LIMIT 10;
COMMIT;
```

Typical recall vs performance trade-off (10M 1536-dim vectors, 32 vCPU):

| ef_search | Recall@10 | p50 latency | QPS |
|-----------|-----------|-------------|-----|
| 20 | 89% | 0.7ms | 12,000 |
| 40 | 95% | 1.2ms | 8,400 |
| 80 | 98% | 2.1ms | 4,800 |
| 200 | 99.5% | 4.8ms | 2,100 |
| exact | 100% | 45ms | 220 |

## Exact Search

Force exact (brute-force) nearest-neighbour search, ignoring the HNSW index:

```sql
SET neuraldb.vector_scan = 'exact';
SELECT * FROM documents ORDER BY embedding <=> $1 LIMIT 10;
RESET neuraldb.vector_scan;
```

Use exact search when:
- You need 100% recall (e.g., de-duplication, exact compliance checks)
- The table has fewer than ~100k rows (exact is competitive)
- You are benchmarking ANN recall

## Bulk Vector Operations

### Batch Insert

Use `COPY` for high-throughput ingestion:

```bash
# Format: id\tcontent\tembedding
psql -c "\COPY documents (id, content, embedding) FROM '/data/vectors.tsv'"
```

### Updating Embeddings in Bulk

```sql
UPDATE documents
SET embedding = new_embeddings.embedding
FROM (VALUES
  ('uuid-1', '[...]'::VECTOR(1536)),
  ('uuid-2', '[...]'::VECTOR(1536))
) AS new_embeddings(id, embedding)
WHERE documents.id = new_embeddings.id::UUID;
```

## Multi-Vector Queries

Find documents closest to ANY of multiple query vectors (OR semantics):

```sql
WITH queries AS (
  SELECT UNNEST(ARRAY['[...]'::VECTOR(1536), '[...]'::VECTOR(1536)]) AS qv
),
ranked AS (
  SELECT d.id, d.content, MIN(d.embedding <=> q.qv) AS best_distance
  FROM documents d, queries q
  GROUP BY d.id, d.content
)
SELECT * FROM ranked
ORDER BY best_distance
LIMIT 20;
```

## Vector Arithmetic

NQL supports vector arithmetic for query expansion and centroid computation:

```sql
-- Average embedding of a result set (cluster centroid)
SELECT AVG(embedding) FROM documents WHERE category = 'technology';

-- Find documents similar to the average
SELECT id, content FROM documents
ORDER BY embedding <=> (SELECT AVG(embedding) FROM documents WHERE category = 'tech')
LIMIT 10;
```
