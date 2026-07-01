---
title: Migration
sort: 130
section-id: operations
keywords: migration, import, Postgres, Pinecone, Weaviate, data migration, ETL
description: Migrating data to NeuralDB from PostgreSQL, Pinecone, Weaviate, and other sources
language: en
---

# Migration

This guide covers migrating data into NeuralDB from common sources: PostgreSQL (with or without pgvector), Pinecone, and Weaviate.

## From PostgreSQL (without vectors)

If you are migrating a standard PostgreSQL database to NeuralDB, the simplest path is a logical dump and restore:

```bash
# 1. Dump from source Postgres
pg_dump \
  -h source-host \
  -U source-user \
  -d source-database \
  --format=custom \
  --compress=9 \
  > source-backup.dump

# 2. Create the target database in NeuralDB
psql -h neuraldb-host -U neuraldb -c "CREATE DATABASE myapp;"

# 3. Restore into NeuralDB
pg_restore \
  -h neuraldb-host \
  -U neuraldb \
  -d myapp \
  --jobs=8 \
  --no-owner \
  source-backup.dump
```

### Adding Vector Columns Post-Migration

After restoring the schema and data, add vector columns and generate embeddings:

```sql
-- Add the vector column
ALTER TABLE documents ADD COLUMN embedding VECTOR(1536);

-- Create the index (do this before backfilling on large tables)
CREATE INDEX CONCURRENTLY documents_embedding_idx
ON documents USING hnsw (embedding vector_cosine_ops);
```

Then backfill embeddings in batches:

```python
import openai
from neuraldb import NeuralDB

client = NeuralDB(connection_string)
openai_client = openai.OpenAI()

BATCH_SIZE = 100

while True:
    rows = client.query("""
        SELECT id, content FROM documents
        WHERE embedding IS NULL
        LIMIT %s
    """, [BATCH_SIZE])

    if not rows:
        break

    texts = [row['content'] for row in rows]
    response = openai_client.embeddings.create(
        model="text-embedding-3-small",
        input=texts
    )

    updates = [
        (response.data[i].embedding, rows[i]['id'])
        for i in range(len(rows))
    ]

    client.executemany(
        "UPDATE documents SET embedding = %s WHERE id = %s",
        updates
    )
    print(f"Backfilled {len(rows)} rows")
```

## From PostgreSQL + pgvector

pgvector uses the same `VECTOR` type as NeuralDB. Migration is a direct dump and restore with minimal adjustments.

```bash
# Dump — exclude pgvector extension (NeuralDB has native vector support)
pg_dump \
  -h source-host -U source-user -d source-db \
  --format=custom \
  --exclude-extension=vector \
  > pgvector-backup.dump

pg_restore \
  -h neuraldb-host -U neuraldb -d myapp \
  --jobs=8 \
  pgvector-backup.dump
```

### Re-create HNSW Indexes

pgvector HNSW indexes are not transferred. Recreate them in NeuralDB:

```sql
-- Drop pgvector-created indexes
DROP INDEX IF EXISTS documents_embedding_idx;

-- Create NeuralDB HNSW index (same syntax, better performance)
CREATE INDEX CONCURRENTLY documents_embedding_idx
ON documents USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);
```

## From Pinecone

Pinecone stores vectors with metadata. Export using the Pinecone SDK and ingest into NeuralDB:

```python
import pinecone
from neuraldb import NeuralDB, BulkIngestor

# Source: Pinecone
pc = pinecone.Pinecone(api_key=os.environ["PINECONE_API_KEY"])
index = pc.Index("my-index")

# Target: NeuralDB
client = NeuralDB(os.environ["NEURALDB_URL"])

# Create target table
client.execute("""
    CREATE TABLE IF NOT EXISTS pinecone_migration (
        id TEXT PRIMARY KEY,
        embedding VECTOR(1536),
        metadata JSONB,
        migrated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
    )
""")

client.execute("""
    CREATE INDEX IF NOT EXISTS pinecone_migration_emb_idx
    ON pinecone_migration USING hnsw (embedding vector_cosine_ops)
""")

# Paginate through all Pinecone vectors
ingestor = BulkIngestor(client, table="pinecone_migration", batch_size=500)

with ingestor as ing:
    for ids_batch in paginate_pinecone_ids(index, batch_size=1000):
        fetch_response = index.fetch(ids=ids_batch)

        for vector_id, vector_data in fetch_response.vectors.items():
            ing.add({
                "id": vector_id,
                "embedding": vector_data.values,
                "metadata": vector_data.metadata or {}
            })

print(f"Migrated {ingestor.total_inserted} vectors")
```

### Mapping Pinecone Metadata to Columns

Flatten commonly-queried metadata fields into dedicated columns for better query performance:

```python
# Instead of: metadata JSONB
# Create typed columns for common filter fields:
client.execute("""
    ALTER TABLE pinecone_migration
    ADD COLUMN IF NOT EXISTS category TEXT GENERATED ALWAYS AS (metadata->>'category') STORED,
    ADD COLUMN IF NOT EXISTS created_date DATE GENERATED ALWAYS AS ((metadata->>'date')::DATE) STORED;

    CREATE INDEX ON pinecone_migration (category);
    CREATE INDEX ON pinecone_migration (created_date);
""")
```

## From Weaviate

Export Weaviate data using the Weaviate client SDK:

```python
import weaviate
from neuraldb import NeuralDB, BulkIngestor

weaviate_client = weaviate.connect_to_local()
neuraldb_client = NeuralDB(os.environ["NEURALDB_URL"])

collection = weaviate_client.collections.get("Document")

# Create target schema
neuraldb_client.execute("""
    CREATE TABLE weaviate_documents (
        id UUID PRIMARY KEY,
        content TEXT,
        category TEXT,
        source TEXT,
        embedding VECTOR(1536)
    );
    CREATE INDEX ON weaviate_documents USING hnsw (embedding vector_cosine_ops);
""")

ingestor = BulkIngestor(neuraldb_client, table="weaviate_documents", batch_size=500)

with ingestor as ing:
    for item in collection.iterator(include_vector=True):
        ing.add({
            "id": str(item.uuid),
            "content": item.properties.get("content", ""),
            "category": item.properties.get("category"),
            "source": item.properties.get("source"),
            "embedding": item.vector.get("default"),
        })

weaviate_client.close()
print(f"Migrated {ingestor.total_inserted} objects")
```

## Verifying Migration

After any migration, verify data integrity:

```sql
-- Row count comparison
SELECT COUNT(*) FROM documents;

-- Sample vector similarity (should match source)
SELECT id, content, 1 - (embedding <=> (SELECT embedding FROM documents LIMIT 1)) AS sim
FROM documents
ORDER BY embedding <=> (SELECT embedding FROM documents LIMIT 1)
LIMIT 5;

-- Check for null embeddings
SELECT COUNT(*) FROM documents WHERE embedding IS NULL;

-- Index health
SELECT index_name, hnsw_in_memory, estimated_recall
FROM neuraldb_stat_vector_indexes;
```
