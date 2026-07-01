---
title: Core Concepts
sort: 110
section-id: overview
keywords: concepts, vectors, embeddings, hybrid queries, nodes, HNSW, ANN
description: Core NeuralDB concepts — vectors, embeddings, hybrid queries, and the node model
language: en
---

# Core Concepts

Understanding these fundamental concepts will help you use NeuralDB effectively and make good architectural decisions for your application.

## Vectors and Embeddings

A **vector** is an ordered list of floating-point numbers — a point in high-dimensional space. In NeuralDB, vectors are used to represent the semantic meaning of data.

An **embedding** is a vector produced by a machine learning model that encodes the semantic meaning of its input. Similar inputs produce vectors that are close together in the embedding space. For example, the sentences "I love dogs" and "I adore canines" will produce embeddings that are close to each other, even though they share no words.

NeuralDB stores embeddings as `VECTOR(n)` columns, where `n` is the dimensionality (the number of float32 values). Common dimensionalities:

| Model | Dimensions |
|-------|-----------|
| OpenAI text-embedding-3-small | 1536 |
| OpenAI text-embedding-3-large | 3072 |
| Cohere embed-english-v3.0 | 1024 |
| Google text-embedding-004 | 768 |
| BAAI/bge-m3 | 1024 |

## Distance Metrics

NeuralDB computes similarity between two vectors using one of three distance metrics:

### Cosine Similarity

Measures the angle between two vectors. Ranges from -1 (opposite) to 1 (identical). Ideal for text embeddings produced by models trained with cosine objectives:

```
cosine_similarity(a, b) = (a · b) / (|a| × |b|)
```

In NQL, use the `<=>` operator or `COSINE_SIMILARITY()` function.

### Dot Product

Measures the product of vector magnitudes and the angle between them. Used when vectors are not normalised and magnitude carries information (e.g., collaborative filtering):

```
dot_product(a, b) = Σ(aᵢ × bᵢ)
```

In NQL, use the `<#>` operator or `DOT_PRODUCT()` function.

### Euclidean Distance (L2)

Measures straight-line distance between two points. Lower is more similar. Useful for spatial data and image embeddings:

```
l2_distance(a, b) = √(Σ(aᵢ - bᵢ)²)
```

In NQL, use the `<->` operator or `L2_DISTANCE()` function.

## Vector Indexes

NeuralDB builds vector indexes using the **HNSW (Hierarchical Navigable Small World)** algorithm. HNSW provides:

- Sub-linear approximate nearest neighbour (ANN) search
- Configurable trade-off between speed and recall
- Incremental updates (no full rebuild needed when inserting)

### HNSW Parameters

When creating a vector index:

```sql
CREATE INDEX ON documents
USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);
```

| Parameter | Description | Default |
|-----------|-------------|---------|
| `m` | Number of bi-directional links per node. Higher = better recall, more memory | 16 |
| `ef_construction` | Size of candidate set during index construction. Higher = better quality, slower build | 64 |
| `ef_search` | Size of candidate set at query time. Set per-query with `SET hnsw.ef_search = 100` | 40 |

### Exact vs Approximate Search

By default, vector queries use the HNSW index (approximate). For exact results (slower but 100% recall), use:

```sql
SET neuraldb.vector_scan = 'exact';
SELECT * FROM documents ORDER BY embedding <=> :query LIMIT 10;
```

## Hybrid Queries

A hybrid query combines vector similarity with relational predicates in a single query plan. The NeuralDB query planner evaluates two strategies and picks the cheaper one:

1. **Pre-filter then search** — apply relational filters first to reduce the candidate set, then run ANN search on the filtered set
2. **Post-filter** — run ANN search to get top-k candidates, then apply relational filters

NeuralDB automatically selects the optimal strategy based on selectivity estimates. You can hint the planner:

```sql
SELECT * FROM documents
WHERE /*+ PREFILTER */ category = 'news'
ORDER BY embedding <=> :query
LIMIT 10;
```

## Tables and Schemas

NeuralDB is schema-based, like PostgreSQL. Everything lives inside a database → schema → table hierarchy:

```sql
CREATE DATABASE my_app;
\c my_app

CREATE SCHEMA vectors;
CREATE SCHEMA metadata;

CREATE TABLE vectors.documents (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  content TEXT NOT NULL,
  embedding VECTOR(1536),
  schema_id TEXT REFERENCES metadata.schemas(id),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

## Nodes

NeuralDB is a distributed system. A **node** is a single NeuralDB process. Nodes have one of three roles:

| Role | Responsibilities |
|------|----------------|
| **Primary** | Accepts reads and writes, coordinates transactions |
| **Replica** | Accepts reads, replicates writes from primary |
| **Index** | Maintains vector indexes for shard(s), offloads ANN queries |

In a single-node deployment, one process takes all three roles.

## Sharding

NeuralDB shards data by `shard_key`. By default, the primary key is used as the shard key:

```sql
CREATE TABLE events (
  id UUID PRIMARY KEY,
  tenant_id UUID NOT NULL,
  event_type TEXT,
  embedding VECTOR(768)
) SHARD BY tenant_id;
```

All rows with the same `tenant_id` are guaranteed to reside on the same shard, which enables efficient tenant-scoped queries without cross-shard joins.

## Transactions

NeuralDB uses multi-version concurrency control (MVCC) for transaction isolation, identical to PostgreSQL:

```sql
BEGIN;
  INSERT INTO documents (content, embedding) VALUES ($1, $2);
  UPDATE document_counts SET count = count + 1 WHERE id = $3;
COMMIT;
```

Both the vector data and the relational data are committed atomically. If the transaction rolls back, neither the row nor the vector index entry is committed.
