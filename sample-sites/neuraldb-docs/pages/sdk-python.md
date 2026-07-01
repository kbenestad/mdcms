---
title: Python SDK
sort: 100
section-id: client-sdks
keywords: Python, SDK, client, connection, CRUD, vector operations, psycopg
description: Installing and using the NeuralDB Python SDK — connection, CRUD, and vector operations
language: en
---

# Python SDK

The NeuralDB Python SDK provides a high-level client for Python applications. It is built on top of `psycopg3` (the PostgreSQL adapter) with NeuralDB-specific helpers for vector operations, embedding generation, and batch ingestion.

## Installation

```bash
pip install neuraldb
# or
pip install neuraldb[asyncio]    # includes async support
pip install neuraldb[all]        # includes all optional extras
```

### Requirements

- Python 3.10+
- libpq (PostgreSQL client library)

On Ubuntu: `sudo apt install libpq-dev`
On macOS: `brew install libpq`

## Connecting

### Synchronous Client

```python
from neuraldb import NeuralDB

# From connection string
client = NeuralDB("postgresql://neuraldb:password@localhost:5432/mydb")

# From parameters
client = NeuralDB(
    host="localhost",
    port=5432,
    user="neuraldb",
    password="password",
    database="mydb",
    sslmode="require",
)

# Context manager (auto-closes connection)
with NeuralDB("postgresql://...") as client:
    result = client.query("SELECT 1")
```

### Async Client

```python
import asyncio
from neuraldb import AsyncNeuralDB

async def main():
    async with AsyncNeuralDB("postgresql://neuraldb:password@localhost/mydb") as client:
        result = await client.query("SELECT 1")
        print(result)

asyncio.run(main())
```

### Connection Pool

```python
from neuraldb import NeuralDBPool

pool = NeuralDBPool(
    "postgresql://neuraldb:password@localhost/mydb",
    min_size=5,
    max_size=20,
)

with pool.acquire() as client:
    result = client.query("SELECT COUNT(*) FROM documents")
```

## Schema Operations

```python
# Create a table with a vector column
client.execute("""
    CREATE TABLE IF NOT EXISTS documents (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        content TEXT NOT NULL,
        source TEXT,
        embedding VECTOR(1536),
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
    )
""")

# Create a vector index
client.execute("""
    CREATE INDEX IF NOT EXISTS documents_embedding_idx
    ON documents USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64)
""")
```

## CRUD Operations

### Insert

```python
from neuraldb import Vector

# Insert with pre-computed embedding
client.execute(
    "INSERT INTO documents (content, source, embedding) VALUES (%s, %s, %s)",
    ("My document content", "web-scraper", Vector([0.023, -0.187, 0.412, ...]))
)

# Insert many (batched for efficiency)
docs = [
    ("Content A", "source-1", Vector([...])),
    ("Content B", "source-2", Vector([...])),
    ("Content C", "source-1", Vector([...])),
]
client.executemany(
    "INSERT INTO documents (content, source, embedding) VALUES (%s, %s, %s)",
    docs
)
```

### Query

```python
# Standard query — returns list of Row objects
rows = client.query("SELECT id, content FROM documents WHERE source = %s", ("web-scraper",))

for row in rows:
    print(row["id"], row["content"])

# As dicts
rows = client.query(
    "SELECT * FROM documents LIMIT 10",
    row_factory="dict"
)

# As named tuples
rows = client.query(
    "SELECT id, content FROM documents LIMIT 10",
    row_factory="namedtuple"
)
```

### Vector Search

```python
import openai

# Generate query embedding
query_text = "high-performance wireless headphones"
query_embedding = openai.embeddings.create(
    model="text-embedding-3-small",
    input=query_text
).data[0].embedding

# Semantic search
results = client.query("""
    SELECT id, content, 1 - (embedding <=> %s) AS similarity
    FROM documents
    WHERE embedding IS NOT NULL
    ORDER BY embedding <=> %s
    LIMIT 10
""", (Vector(query_embedding), Vector(query_embedding)))

for row in results:
    print(f"{row['similarity']:.3f}: {row['content'][:100]}")
```

### Using the High-Level Search API

```python
from neuraldb import VectorSearch

searcher = VectorSearch(client, table="documents", embedding_column="embedding")

results = searcher.search(
    query_vector=query_embedding,
    limit=10,
    filters={"source": "web-scraper"},
    metric="cosine",
)
```

### Update

```python
client.execute(
    "UPDATE documents SET content = %s, embedding = %s WHERE id = %s",
    ("Updated content", Vector(new_embedding), doc_id)
)
```

### Delete

```python
client.execute("DELETE FROM documents WHERE id = %s", (doc_id,))
```

## Transactions

```python
with client.transaction():
    client.execute("INSERT INTO documents (content, embedding) VALUES (%s, %s)", (content, Vector(embedding)))
    client.execute("UPDATE stats SET count = count + 1")
    # Auto-commits on exit, rolls back on exception
```

Explicit control:

```python
with client.transaction() as txn:
    try:
        client.execute("INSERT ...")
        client.execute("UPDATE ...")
        txn.commit()
    except Exception:
        txn.rollback()
        raise
```

## Bulk Ingestion

For high-throughput ingestion, use the `BulkIngestor`:

```python
from neuraldb import BulkIngestor

ingestor = BulkIngestor(
    client,
    table="documents",
    columns=["content", "source", "embedding"],
    batch_size=1000,         # insert in batches of 1000
    embedding_model="openai/text-embedding-3-small",  # auto-generate embeddings
    embedding_column="embedding",
    text_column="content",
)

docs = [
    {"content": "Document text here", "source": "source-1"},
    {"content": "Another document", "source": "source-2"},
    # ... thousands more
]

with ingestor as ing:
    for doc in docs:
        ing.add(doc)
    # Flushes remaining rows and commits on context exit

print(f"Ingested {ingestor.total_inserted} documents")
```

## Type Handling

The SDK provides type adapters for NeuralDB types:

```python
from neuraldb.types import Vector, HalfVector, SparseVector

# Dense vector
v = Vector([0.1, 0.2, 0.3])

# Half-precision vector (less memory)
hv = HalfVector([0.1, 0.2, 0.3])

# Sparse vector
sv = SparseVector({0: 0.5, 15: 0.3, 200: 0.8}, dimensions=384)
```
