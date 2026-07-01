---
title: Hybrid Queries
sort: 120
section-id: query-language
keywords: hybrid queries, vector, relational, filters, combined, semantic search, metadata
description: Combining vector similarity and relational filters in NQL hybrid queries
language: en
---

# Hybrid Queries

Hybrid queries combine vector similarity search with relational filter predicates in a single SQL statement. The NeuralDB query planner handles the execution strategy — you write normal SQL with vector operators.

## Basic Hybrid Query

Find the 10 most semantically similar products that are in the "electronics" category and in stock:

```sql
SELECT id, name, price, 1 - (embedding <=> $1) AS similarity
FROM products
WHERE category = 'electronics'
  AND stock > 0
  AND price < 500
ORDER BY embedding <=> $1
LIMIT 10;
```

NeuralDB automatically determines whether to:
1. **Pre-filter**: apply relational conditions first, then search the filtered set
2. **Post-filter**: run ANN search, then apply conditions to the top-k results

The decision is based on the selectivity of the relational predicates.

## Query Planner Hints

Override the planner's strategy:

```sql
-- Force pre-filter (good when relational filter is very selective)
SELECT /*+ PREFILTER */ id, name, score
FROM (
  SELECT id, name, 1 - (embedding <=> $1) AS score
  FROM products
  WHERE category = 'electronics'  -- very selective: 2% of rows
) sub
ORDER BY score DESC
LIMIT 10;

-- Force post-filter (good when relational filter is weakly selective)
SELECT /*+ POSTFILTER */ id, name, 1 - (embedding <=> $1) AS score
FROM products
WHERE price < 500   -- weakly selective: 80% of rows
ORDER BY embedding <=> $1
LIMIT 10;
```

## Filtering by Multiple Conditions

```sql
SELECT id, name, description,
       1 - (embedding <=> $1) AS similarity,
       price,
       rating
FROM products
WHERE category = ANY($2)          -- multi-category filter
  AND price BETWEEN $3 AND $4
  AND rating >= 4.0
  AND discontinued = false
  AND created_at > NOW() - INTERVAL '1 year'
ORDER BY embedding <=> $1
LIMIT 20;
-- $1 = query embedding
-- $2 = ['electronics', 'computers']
-- $3 = 50, $4 = 1000
```

## Hybrid Full-Text + Vector (BM25)

Combine traditional full-text search with vector similarity using Reciprocal Rank Fusion (RRF):

```sql
WITH vector_search AS (
  SELECT id, ROW_NUMBER() OVER (ORDER BY embedding <=> $1) AS rank
  FROM documents
  ORDER BY embedding <=> $1
  LIMIT 100
),
fts_search AS (
  SELECT id, ROW_NUMBER() OVER (ORDER BY ts_rank_cd(tsv, query) DESC) AS rank
  FROM documents, to_tsquery('english', $2) query
  WHERE tsv @@ query
  ORDER BY ts_rank_cd(tsv, query) DESC
  LIMIT 100
),
rrf AS (
  SELECT
    COALESCE(v.id, f.id) AS id,
    (COALESCE(1.0 / (60 + v.rank), 0) + COALESCE(1.0 / (60 + f.rank), 0)) AS rrf_score
  FROM vector_search v
  FULL OUTER JOIN fts_search f ON v.id = f.id
)
SELECT d.id, d.content, rrf.rrf_score
FROM rrf
JOIN documents d ON d.id = rrf.id
ORDER BY rrf_score DESC
LIMIT 10;
```

NQL also provides a built-in `HYBRID_SEARCH` function:

```sql
SELECT id, content, score
FROM HYBRID_SEARCH(
  table     := 'documents',
  vector_column := 'embedding',
  tsv_column := 'tsv',
  query_vector := $1,
  query_text := $2,
  top_k := 10,
  rrf_k := 60,
  vector_weight := 0.6,
  text_weight := 0.4
);
```

## Joining Vector Results with Other Tables

```sql
SELECT
  p.id,
  p.name,
  p.price,
  c.name AS category_name,
  u.display_name AS seller,
  1 - (p.embedding <=> $1) AS similarity
FROM products p
JOIN categories c ON c.id = p.category_id
JOIN users u ON u.id = p.seller_id
WHERE p.available = true
  AND c.slug = ANY($2)
  AND u.verified = true
ORDER BY p.embedding <=> $1
LIMIT 15;
```

## Subquery Vectors

Use a subquery to dynamically compute a query vector from existing data:

```sql
-- Find products similar to product #123
SELECT id, name, 1 - (embedding <=> ref.embedding) AS similarity
FROM products,
     (SELECT embedding FROM products WHERE id = $1) ref
WHERE id != $1
ORDER BY embedding <=> ref.embedding
LIMIT 10;
```

## Tenant-Scoped Search

For multi-tenant applications, always include tenant filters:

```sql
SELECT id, content, 1 - (embedding <=> $1) AS similarity
FROM documents
WHERE tenant_id = $2       -- partition pruning if SHARD BY tenant_id
  AND embedding IS NOT NULL
ORDER BY embedding <=> $1
LIMIT 10;
```

If the table is sharded by `tenant_id`, this query runs entirely on the correct shard without cross-shard coordination.

## Composite Scoring

Combine vector similarity with relational signals:

```sql
SELECT
  id,
  name,
  price,
  rating,
  -- Weighted composite score: 70% semantic, 20% rating, 10% recency
  (0.7 * (1 - (embedding <=> $1))
   + 0.2 * (rating / 5.0)
   + 0.1 * (1 - EXTRACT(DAYS FROM NOW() - created_at) / 365.0)
  ) AS composite_score
FROM products
WHERE available = true
  AND price < $2
ORDER BY composite_score DESC
LIMIT 20;
```

## Pagination

Cursor-based pagination for vector results:

```sql
-- Page 1
SELECT id, name, (embedding <=> $1) AS dist
FROM products
WHERE available = true
ORDER BY dist, id    -- secondary sort by id for stable pagination
LIMIT 20;

-- Page 2 (cursor: last dist and id from page 1)
SELECT id, name, (embedding <=> $1) AS dist
FROM products
WHERE available = true
  AND ((embedding <=> $1) > $2 OR ((embedding <=> $1) = $2 AND id > $3))
ORDER BY dist, id
LIMIT 20;
```
