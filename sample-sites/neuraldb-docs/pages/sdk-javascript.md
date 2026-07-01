---
title: JavaScript SDK
sort: 110
section-id: client-sdks
keywords: JavaScript, TypeScript, SDK, Node.js, browser, npm, client
description: The NeuralDB JavaScript/TypeScript SDK for Node.js and browser environments
language: en
---

# JavaScript SDK

The NeuralDB JavaScript SDK provides a fully typed client for Node.js and browser environments. It is built on `pg` (node-postgres) for Node.js and a custom HTTP adapter for edge and browser environments.

## Installation

```bash
npm install @neuraldb/client
# or
yarn add @neuraldb/client
# or
pnpm add @neuraldb/client
```

## Basic Setup

### Node.js

```typescript
import { NeuralDB } from '@neuraldb/client';

const client = new NeuralDB({
  connectionString: process.env.NEURALDB_URL!,
  // or individual options:
  host: 'localhost',
  port: 5432,
  user: 'neuraldb',
  password: 'password',
  database: 'mydb',
  ssl: { rejectUnauthorized: true },
});

await client.connect();
```

### Edge / Serverless (HTTP mode)

For Cloudflare Workers, Vercel Edge, and browser environments, use the HTTP adapter:

```typescript
import { NeuralDB, HttpAdapter } from '@neuraldb/client';

const client = new NeuralDB({
  adapter: new HttpAdapter({
    url: process.env.NEURALDB_HTTP_URL!,
    apiKey: process.env.NEURALDB_API_KEY!,
  }),
});
```

### Connection Pool

```typescript
import { NeuralDBPool } from '@neuraldb/client';

const pool = new NeuralDBPool({
  connectionString: process.env.NEURALDB_URL!,
  max: 20,
  idleTimeoutMillis: 30000,
  connectionTimeoutMillis: 5000,
});
```

## Executing Queries

```typescript
// Simple query — returns QueryResult
const result = await client.query('SELECT id, content FROM documents LIMIT 10');
const rows = result.rows;  // typed as any[]

// Parameterised query
const { rows } = await client.query<{ id: string; content: string }>(
  'SELECT id, content FROM documents WHERE source = $1 LIMIT $2',
  ['web-scraper', 20]
);
```

## Vector Operations

### Inserting Vectors

```typescript
import { toVector } from '@neuraldb/client';

const embedding = [0.023, -0.187, 0.412, /* 1536 values */];

await client.query(
  'INSERT INTO documents (content, embedding) VALUES ($1, $2)',
  ['My document content', toVector(embedding)]
);
```

### Similarity Search

```typescript
import OpenAI from 'openai';
import { toVector } from '@neuraldb/client';

const openai = new OpenAI();

async function semanticSearch(query: string, limit = 10) {
  const embeddingResponse = await openai.embeddings.create({
    model: 'text-embedding-3-small',
    input: query,
  });

  const queryVector = embeddingResponse.data[0].embedding;

  const { rows } = await client.query<{
    id: string;
    content: string;
    similarity: number;
  }>(
    `SELECT id, content, 1 - (embedding <=> $1) AS similarity
     FROM documents
     WHERE embedding IS NOT NULL
     ORDER BY embedding <=> $1
     LIMIT $2`,
    [toVector(queryVector), limit]
  );

  return rows;
}
```

### Hybrid Search

```typescript
async function hybridSearch(query: string, filters: Record<string, unknown>, limit = 10) {
  const queryVector = await generateEmbedding(query);

  const conditions: string[] = [];
  const params: unknown[] = [toVector(queryVector)];

  Object.entries(filters).forEach(([key, value]) => {
    params.push(value);
    conditions.push(`${key} = $${params.length}`);
  });

  const whereClause = conditions.length > 0
    ? 'WHERE ' + conditions.join(' AND ')
    : '';

  params.push(limit);

  const { rows } = await client.query(
    `SELECT id, content, 1 - (embedding <=> $1) AS similarity
     FROM documents
     ${whereClause}
     ORDER BY embedding <=> $1
     LIMIT $${params.length}`,
    params
  );

  return rows;
}
```

## High-Level Document API

The SDK includes a higher-level document management API:

```typescript
import { DocumentStore } from '@neuraldb/client';

const store = new DocumentStore(client, {
  table: 'documents',
  embeddingColumn: 'embedding',
  contentColumn: 'content',
  embeddingModel: {
    provider: 'openai',
    model: 'text-embedding-3-small',
    apiKey: process.env.OPENAI_API_KEY!,
  },
});

// Add documents (auto-generates embeddings)
await store.add([
  { content: 'First document', metadata: { source: 'web' } },
  { content: 'Second document', metadata: { source: 'pdf' } },
]);

// Search
const results = await store.search('query text', {
  limit: 10,
  filter: { source: 'web' },
  minSimilarity: 0.7,
});

// Delete
await store.delete({ filter: { source: 'web' } });
```

## Transactions

```typescript
const pgClient = await pool.connect();

try {
  await pgClient.query('BEGIN');

  await pgClient.query(
    'INSERT INTO documents (content, embedding) VALUES ($1, $2)',
    ['Content', toVector(embedding)]
  );

  await pgClient.query(
    'UPDATE stats SET doc_count = doc_count + 1 WHERE id = $1',
    [statsId]
  );

  await pgClient.query('COMMIT');
} catch (error) {
  await pgClient.query('ROLLBACK');
  throw error;
} finally {
  pgClient.release();
}
```

## Streaming Results

For large result sets, stream rows to avoid loading all data into memory:

```typescript
const stream = client.queryStream(
  'SELECT id, content, embedding FROM documents WHERE source = $1',
  ['web-scraper']
);

for await (const row of stream) {
  await processDocument(row);
}
```

## Type Definitions

```typescript
import type { Vector, QueryResult, PoolClient } from '@neuraldb/client';

interface Document {
  id: string;
  content: string;
  embedding: Vector | null;
  created_at: Date;
}

const { rows } = await client.query<Document>(
  'SELECT * FROM documents WHERE id = $1',
  [id]
);
```

## Error Handling

```typescript
import { NeuralDBError, ConnectionError, QueryError } from '@neuraldb/client';

try {
  await client.query('SELECT * FROM nonexistent_table');
} catch (error) {
  if (error instanceof QueryError) {
    console.error('SQL error:', error.message, 'Code:', error.code);
  } else if (error instanceof ConnectionError) {
    console.error('Connection failed:', error.message);
  }
}
```
