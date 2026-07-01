---
title: Aggregations
sort: 130
section-id: query-language
keywords: aggregations, GROUP BY, COUNT, SUM, vectors, AVG, centroid, analytics
description: Aggregating data in NQL including GROUP BY, COUNT, SUM, and vector-specific aggregation functions
language: en
---

# Aggregations

NQL supports the full SQL aggregation toolkit, extended with vector-specific aggregate functions for centroid computation, clustering, and semantic analytics.

## Standard Aggregations

All standard SQL aggregate functions work as expected:

```sql
-- Count documents by category
SELECT category, COUNT(*) AS doc_count
FROM documents
GROUP BY category
ORDER BY doc_count DESC;

-- Average price by category
SELECT category,
       COUNT(*) AS products,
       AVG(price) AS avg_price,
       MIN(price) AS min_price,
       MAX(price) AS max_price,
       SUM(stock * price) AS inventory_value
FROM products
WHERE available = true
GROUP BY category
ORDER BY inventory_value DESC;
```

## Vector Aggregations

### `AVG(embedding)` — Centroid Computation

Compute the centroid (average vector) of a group:

```sql
-- Centroid of all "technology" documents
SELECT AVG(embedding) AS centroid
FROM documents
WHERE category = 'technology';
```

Use centroids to find documents representative of a cluster:

```sql
WITH centroid AS (
  SELECT AVG(embedding) AS c FROM documents WHERE category = 'technology'
)
SELECT id, title, 1 - (embedding <=> centroid.c) AS similarity_to_centroid
FROM documents, centroid
WHERE category = 'technology'
ORDER BY embedding <=> centroid.c
LIMIT 10;
```

### `vector_centroid(embedding)` — Weighted Centroid

Compute a weighted centroid using a score column:

```sql
-- Weighted centroid by rating (higher-rated items pull more)
SELECT vector_centroid(embedding, rating) AS weighted_centroid
FROM products
WHERE category = 'electronics';
```

### `vector_agg_concat(embedding)` — Vector Array

Collect vectors into an array for downstream processing:

```sql
SELECT category, vector_agg_concat(embedding) AS all_embeddings
FROM documents
GROUP BY category;
```

## GROUP BY with Vector Search

Find the best document in each category for a given query:

```sql
SELECT DISTINCT ON (category)
  id, category, title, 1 - (embedding <=> $1) AS similarity
FROM documents
WHERE embedding IS NOT NULL
ORDER BY category, embedding <=> $1;
```

Or using a lateral join for more control:

```sql
SELECT cat.category, top_doc.id, top_doc.title, top_doc.similarity
FROM (SELECT DISTINCT category FROM documents) cat,
LATERAL (
  SELECT id, title, 1 - (embedding <=> $1) AS similarity
  FROM documents
  WHERE category = cat.category
  ORDER BY embedding <=> $1
  LIMIT 1
) top_doc;
```

## Window Functions

Use window functions to rank results within partitions:

```sql
-- Rank documents by similarity within each category
SELECT
  id, title, category,
  1 - (embedding <=> $1) AS similarity,
  RANK() OVER (
    PARTITION BY category
    ORDER BY embedding <=> $1
  ) AS rank_in_category
FROM documents
WHERE 1 - (embedding <=> $1) > 0.5
ORDER BY category, rank_in_category;
```

Rolling average similarity over time:

```sql
SELECT
  date_trunc('day', created_at) AS day,
  AVG(1 - (embedding <=> $1)) AS avg_daily_similarity,
  AVG(AVG(1 - (embedding <=> $1))) OVER (
    ORDER BY date_trunc('day', created_at)
    ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
  ) AS rolling_7d_avg
FROM documents
GROUP BY day
ORDER BY day;
```

## Clustering with GROUP BY

Perform k-means style clustering by assigning documents to their nearest centroid:

```sql
-- Given pre-computed centroids in a centroids table:
SELECT d.id, d.content,
       c.cluster_id,
       (d.embedding <=> c.centroid) AS distance_to_centroid
FROM documents d
CROSS JOIN LATERAL (
  SELECT cluster_id, centroid
  FROM centroids
  ORDER BY d.embedding <=> centroid
  LIMIT 1
) c;
```

## HAVING with Vector Conditions

```sql
-- Categories where the average intra-category similarity is high (tight clusters)
SELECT category,
       COUNT(*) AS doc_count,
       1 - AVG(embedding <=> (SELECT AVG(e2.embedding) FROM documents e2 WHERE e2.category = e.category)) AS cohesion
FROM documents e
GROUP BY category
HAVING COUNT(*) > 10
ORDER BY cohesion DESC;
```

## Time-Series Analytics

Analyse how semantic content shifts over time:

```sql
-- Daily semantic drift: how different is today's content from last week's?
WITH weekly_centroids AS (
  SELECT
    date_trunc('week', created_at) AS week,
    AVG(embedding) AS centroid
  FROM documents
  GROUP BY week
)
SELECT
  w1.week,
  1 - (w1.centroid <=> w2.centroid) AS similarity_to_prev_week
FROM weekly_centroids w1
LEFT JOIN weekly_centroids w2
  ON w2.week = w1.week - INTERVAL '1 week'
ORDER BY w1.week;
```

## JSON Aggregation with Vectors

Combine JSON aggregation with vector results:

```sql
SELECT
  category,
  COUNT(*) AS total,
  AVG(price) AS avg_price,
  JSON_AGG(
    JSON_BUILD_OBJECT('id', id, 'name', name, 'similarity', 1 - (embedding <=> $1))
    ORDER BY embedding <=> $1
  ) FILTER (WHERE ROW_NUMBER() OVER (PARTITION BY category ORDER BY embedding <=> $1) <= 3)
    AS top_3_per_category
FROM products
WHERE available = true
GROUP BY category;
```

## ROLLUP and CUBE

Standard SQL ROLLUP and CUBE work for hierarchical aggregation:

```sql
SELECT
  region,
  category,
  COUNT(*) AS count,
  AVG(price) AS avg_price
FROM products
GROUP BY ROLLUP(region, category)
ORDER BY region NULLS LAST, category NULLS LAST;
```
