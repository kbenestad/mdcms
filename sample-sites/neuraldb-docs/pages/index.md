---
title: What is NeuralDB?
sort: 100
section-id: overview
keywords: NeuralDB, introduction, AI database, vector database, overview
description: What NeuralDB is, its key use cases, and a high-level architecture overview
language: en
---

# What is NeuralDB?

![NeuralDB Platform](assets/images/hero.jpg)

NeuralDB is an AI-native database that unifies vector storage, semantic search, and relational data management in a single, horizontally scalable system. It is designed for applications that need to combine structured data queries with the semantic understanding that modern AI models provide.

Traditional databases store and retrieve data based on exact matches and range queries. NeuralDB adds a third dimension: **semantic proximity**. You can ask "find the 20 products most similar to this description" at the same time as "where inventory > 0 and price < 100" — in a single, atomic query with full ACID guarantees.

## Why NeuralDB Exists

The AI application stack of 2024–2026 exposed a fundamental tension in data architecture. Teams building retrieval-augmented generation (RAG) systems, recommendation engines, and semantic search needed:

- A **vector database** (Pinecone, Weaviate, Qdrant) for embedding storage and similarity search
- A **relational database** (PostgreSQL, MySQL) for structured metadata and transactions
- A **synchronisation layer** to keep the two in sync — a constant source of bugs and operational overhead

NeuralDB replaces all three with a single system. Vectors and relational data share the same storage engine, the same transaction log, and the same query planner. There is no synchronisation problem because there is no synchronisation needed.

## Key Capabilities

### Hybrid Vector + Relational Queries

```sql
SELECT id, name, price, SIMILARITY(embedding, :query_embedding) AS score
FROM products
WHERE category = 'electronics'
  AND price BETWEEN 50 AND 500
  AND stock > 0
ORDER BY score DESC
LIMIT 10;
```

This query uses a vector index for semantic ranking and a B-tree index for the relational filters, with the query planner choosing the optimal execution order.

### Multiple Vector Index Types

NeuralDB supports three similarity metrics out of the box:

| Metric | Use case |
|--------|----------|
| Cosine similarity | Text embeddings, normalised vectors |
| Dot product | Recommendation systems (unnormalised) |
| Euclidean (L2) | Image embeddings, spatial data |

### Full ACID Transactions

Unlike most vector databases, NeuralDB provides full ACID guarantees — including transactional upserts of both the relational row and the vector embedding simultaneously.

### Automatic Embedding Updates

Configure NeuralDB to call an embedding API whenever a text column changes:

```sql
ALTER TABLE documents
ADD COLUMN embedding VECTOR(1536)
GENERATED ALWAYS AS EMBEDDING OF content
USING openai_ada_002;
```

NeuralDB handles the embedding pipeline automatically — no application-level embedding code required.

### Multi-Modal Vectors

Store and query vectors from any modality — text, image, audio, or custom — in the same table:

```sql
CREATE TABLE media_items (
  id UUID PRIMARY KEY,
  title TEXT,
  text_embedding VECTOR(1536),
  image_embedding VECTOR(512),
  created_at TIMESTAMP DEFAULT NOW()
);
```

## Use Cases

**Retrieval-Augmented Generation (RAG)** — Store your document corpus with embeddings. Query the most relevant chunks in a single round-trip and inject them into your LLM prompt.

**Semantic Product Search** — Replace keyword search with semantic search. Find products matching "comfortable running shoes for flat feet" even if those exact words don't appear in any product description.

**Recommendation Engines** — Store user preference vectors alongside item vectors. Compute collaborative-filtering recommendations with a single NQL query.

**Anomaly Detection** — Flag records whose vectors are distant from the cluster of "normal" data.

**Duplicate Detection** — Find near-duplicate records across millions of rows using approximate nearest-neighbour (ANN) search.

**Knowledge Graphs** — Store entity embeddings alongside relationship metadata for graph-enhanced retrieval.

## NeuralDB vs Traditional Approaches

| Capability | NeuralDB | Postgres + pgvector | Pinecone + Postgres |
|-----------|---------|---------------------|---------------------|
| Vector search | Native, HNSW | Extension, limited | Native |
| Relational queries | Full SQL | Full SQL | None (separate DB) |
| Hybrid queries | Single query | Single query | Application-layer join |
| ACID transactions | Yes | Yes | Partial |
| Horizontal sharding | Built-in | Manual (Citus) | Managed |
| Automatic embeddings | Yes | No | No |
| Streaming ingestion | Yes | No | Partial |

## Getting Started

The fastest way to try NeuralDB is with Docker:

```bash
docker run -p 5432:5432 -e NEURALDB_PASSWORD=mypassword neuraldb/neuraldb:latest
```

Connect with any PostgreSQL-compatible client:

```bash
psql -h localhost -U neuraldb -d neuraldb
```

Then read the [Core Concepts](pages/concepts.md) to understand the NeuralDB data model, or jump to [NQL Basics](pages/nql-basics.md) to start writing queries.
