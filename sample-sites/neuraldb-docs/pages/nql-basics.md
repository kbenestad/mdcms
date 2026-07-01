---
title: NQL Basics
sort: 100
section-id: query-language
keywords: NQL, NeuralDB Query Language, SQL, syntax, basics, queries
description: Introduction to NeuralDB Query Language (NQL) — syntax, data types, and basic operations
language: en
---

# NQL Basics

NQL (NeuralDB Query Language) is a superset of standard SQL. Every valid SQL statement is also valid NQL. NQL adds extensions for vector operations, embedding generation, and semantic search primitives.

If you know SQL, you already know most of NQL. This page covers the NQL-specific additions and the data types introduced for AI workloads.

## Connecting

NeuralDB speaks the PostgreSQL wire protocol. Connect with any PostgreSQL client:

```bash
# psql
psql -h localhost -p 5432 -U neuraldb -d mydb

# neuraldb-cli (enhanced interactive shell)
neuraldb-cli -h localhost
```

Connection string format:

```
postgresql://[user[:password]@][host][:port][/dbname][?param=value...]
```

## Data Types

### VECTOR(n)

The core NQL extension. Stores a fixed-length array of 32-bit floats representing a vector embedding:

```sql
-- Declare a vector column with 1536 dimensions (OpenAI ada-002 output)
CREATE TABLE documents (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  content TEXT NOT NULL,
  embedding VECTOR(1536)
);
```

Insert a vector by providing a bracketed float array:

```sql
INSERT INTO documents (content, embedding)
VALUES ('Hello, world', '[0.1, 0.2, 0.3, ...]');  -- 1536 values
```

### HALFVEC(n)

A 16-bit float variant of VECTOR. Half the memory, slight precision loss. Useful when vector_buffer is a constraint:

```sql
embedding HALFVEC(1536)
```

### SPARSEVEC(n)

Sparse vector representation — stores only non-zero elements. Efficient for high-dimensional but sparse vectors (e.g., BM25 term-frequency vectors):

```sql
bm25_vector SPARSEVEC(30000)
```

## Basic CRUD

### Creating Tables

```sql
CREATE TABLE products (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL,
  description TEXT,
  category TEXT,
  price DECIMAL(10, 2),
  stock INTEGER DEFAULT 0,
  embedding VECTOR(1536),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### Inserting Data

```sql
INSERT INTO products (name, description, category, price, stock, embedding)
VALUES (
  'Wireless Headphones',
  'Premium noise-cancelling wireless headphones with 30-hour battery',
  'electronics',
  299.99,
  150,
  '[0.023, -0.187, 0.412, ...]'  -- 1536 floats from your embedding model
);
```

### Reading Data

Standard SQL SELECT works as expected:

```sql
SELECT id, name, price FROM products WHERE category = 'electronics';
SELECT * FROM products WHERE price BETWEEN 50 AND 300 AND stock > 0;
```

### Updating Data

```sql
UPDATE products SET price = 279.99, embedding = '[...]' WHERE id = $1;
```

When updating the `embedding` column, the HNSW index is updated atomically.

### Deleting Data

```sql
DELETE FROM products WHERE id = $1;
```

## Creating Vector Indexes

Without an index, vector similarity queries perform exact linear scans (O(n)). Create an HNSW index for sub-linear performance:

```sql
-- Cosine similarity (most common for text embeddings)
CREATE INDEX ON documents USING hnsw (embedding vector_cosine_ops);

-- Euclidean distance
CREATE INDEX ON documents USING hnsw (embedding vector_l2_ops);

-- Dot product (for recommendation systems)
CREATE INDEX ON documents USING hnsw (embedding vector_ip_ops);
```

Build an index on an existing large table in parallel:

```sql
SET max_parallel_maintenance_workers = 8;
CREATE INDEX CONCURRENTLY ON documents USING hnsw (embedding vector_cosine_ops);
```

## Basic Vector Queries

### Find Similar Documents

```sql
SELECT id, content, 1 - (embedding <=> $1) AS similarity
FROM documents
ORDER BY embedding <=> $1
LIMIT 10;
```

The `<=>` operator is cosine distance (lower = more similar). Subtract from 1 for a similarity score (higher = more similar).

### Distance Operators

| Operator | Distance metric | Index ops |
|----------|----------------|-----------|
| `<=>` | Cosine distance | `vector_cosine_ops` |
| `<->` | Euclidean (L2) distance | `vector_l2_ops` |
| `<#>` | Negative dot product | `vector_ip_ops` |

### Distance Threshold

```sql
-- Only return results with cosine similarity > 0.8
SELECT id, content, 1 - (embedding <=> $1) AS similarity
FROM documents
WHERE 1 - (embedding <=> $1) > 0.8
ORDER BY embedding <=> $1
LIMIT 20;
```

**Note:** The `WHERE 1 - (embedding <=> $1) > 0.8` condition is evaluated after the ANN search, not before. Use `LIMIT` generously enough to capture all relevant results before the threshold filter.

## NQL Functions

### `to_vector(text)`

Convert a string literal to a VECTOR:

```sql
SELECT to_vector('[0.1, 0.2, 0.3]')::VECTOR(3);
```

### `vector_dims(v)`

Return the number of dimensions:

```sql
SELECT vector_dims(embedding) FROM documents LIMIT 1;
-- Returns: 1536
```

### `vector_norm(v)`

Return the L2 norm of a vector:

```sql
SELECT vector_norm(embedding) FROM documents LIMIT 5;
```

### `cosine_similarity(a, b)`, `l2_distance(a, b)`, `dot_product(a, b)`

Named function alternatives to the operators:

```sql
SELECT cosine_similarity(embedding, $1) AS similarity
FROM documents
ORDER BY similarity DESC
LIMIT 10;
```

## Transactions

NQL supports full ACID transactions:

```sql
BEGIN;

INSERT INTO documents (content, embedding) VALUES ($1, $2);
UPDATE document_stats SET total_count = total_count + 1;

COMMIT;
```

On error, roll back:

```sql
BEGIN;
-- ... operations ...
ROLLBACK;
```
