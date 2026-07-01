---
title: REST API
sort: 130
section-id: client-sdks
keywords: REST API, HTTP, endpoints, authentication, JSON, API
description: NeuralDB REST API reference — all endpoints, authentication headers, and response formats
language: en
---

# REST API

NeuralDB provides an HTTP REST API for environments where a direct database connection is not practical (browser clients, third-party integrations, webhooks). The REST API is a thin HTTP wrapper over NQL.

## Base URL

```
https://your-neuraldb-host:8080/api/v1
```

For NeuralDB Cloud:

```
https://[cluster-id].cloud.neuraldb.io/api/v1
```

## Authentication

All REST API requests require an API key in the `Authorization` header:

```
Authorization: Bearer ndb_live_your_api_key_here
```

Or as a query parameter (less secure, avoid in production):

```
?api_key=ndb_live_your_api_key_here
```

Create API keys in the NeuralDB CLI or the Cloud dashboard:

```bash
neuraldb-cli -c "SELECT neuraldb_apikeys.create_key(label => 'my-app', role => 'app_readwrite')"
```

## Query Endpoint

Execute any NQL query:

### `POST /query`

```http
POST /api/v1/query
Content-Type: application/json
Authorization: Bearer ndb_live_...

{
  "query": "SELECT id, content, 1 - (embedding <=> $1) AS similarity FROM documents ORDER BY embedding <=> $1 LIMIT 5",
  "params": [[0.023, -0.187, 0.412]],
  "database": "mydb"
}
```

**Response:**

```json
{
  "rows": [
    { "id": "uuid-1", "content": "First document", "similarity": 0.923 },
    { "id": "uuid-2", "content": "Second document", "similarity": 0.891 }
  ],
  "rowCount": 2,
  "fields": [
    { "name": "id", "dataTypeID": 2950 },
    { "name": "content", "dataTypeID": 25 },
    { "name": "similarity", "dataTypeID": 701 }
  ],
  "executionTimeMs": 3.2
}
```

### Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `query` | string | Yes | NQL query string |
| `params` | array | No | Query parameters (replaces $1, $2, ...) |
| `database` | string | No | Target database (default: `neuraldb`) |
| `timeout_ms` | integer | No | Query timeout in milliseconds |
| `explain` | boolean | No | Return query execution plan |

## Document Endpoints

Higher-level CRUD endpoints for document management:

### `POST /collections/:collection/documents`

Insert documents (auto-generates embeddings if configured):

```http
POST /api/v1/collections/my_docs/documents
Content-Type: application/json
Authorization: Bearer ndb_live_...

{
  "documents": [
    {
      "content": "NeuralDB is an AI-native database",
      "metadata": { "source": "blog", "category": "technology" }
    }
  ],
  "embedding_model": "openai/text-embedding-3-small"
}
```

**Response:**

```json
{
  "inserted": 1,
  "ids": ["550e8400-e29b-41d4-a716-446655440000"]
}
```

### `POST /collections/:collection/search`

Vector similarity search:

```http
POST /api/v1/collections/my_docs/search
Content-Type: application/json
Authorization: Bearer ndb_live_...

{
  "query": "AI-native database for semantic search",
  "limit": 10,
  "min_similarity": 0.7,
  "filters": {
    "category": "technology"
  },
  "embedding_model": "openai/text-embedding-3-small",
  "include_metadata": true
}
```

**Response:**

```json
{
  "results": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "content": "NeuralDB is an AI-native database",
      "similarity": 0.956,
      "metadata": { "source": "blog", "category": "technology" }
    }
  ],
  "query_embedding_model": "openai/text-embedding-3-small",
  "latency_ms": 2.8
}
```

### `GET /collections/:collection/documents/:id`

Retrieve a document by ID:

```http
GET /api/v1/collections/my_docs/documents/550e8400-e29b-41d4-a716-446655440000
Authorization: Bearer ndb_live_...
```

### `PUT /collections/:collection/documents/:id`

Update a document:

```http
PUT /api/v1/collections/my_docs/documents/550e8400-...
Content-Type: application/json
Authorization: Bearer ndb_live_...

{
  "content": "Updated content",
  "metadata": { "source": "blog", "updated": true },
  "regenerate_embedding": true
}
```

### `DELETE /collections/:collection/documents/:id`

Delete a document:

```http
DELETE /api/v1/collections/my_docs/documents/550e8400-...
Authorization: Bearer ndb_live_...
```

## Batch Operations

### `POST /collections/:collection/documents/batch`

Insert up to 1,000 documents in a single request:

```http
POST /api/v1/collections/my_docs/documents/batch
Content-Type: application/json

{
  "documents": [
    { "content": "Document 1", "metadata": {} },
    { "content": "Document 2", "metadata": {} }
  ]
}
```

## Error Responses

All errors return a consistent JSON structure:

```json
{
  "error": {
    "code": "QUERY_ERROR",
    "message": "relation \"nonexistent\" does not exist",
    "detail": "ERROR: relation \"nonexistent\" does not exist at character 15",
    "status": 400
  }
}
```

### Error Codes

| HTTP Status | Error Code | Description |
|-------------|-----------|-------------|
| 400 | `QUERY_ERROR` | Invalid NQL query |
| 400 | `VALIDATION_ERROR` | Request body validation failed |
| 401 | `UNAUTHORIZED` | Missing or invalid API key |
| 403 | `FORBIDDEN` | Insufficient role permissions |
| 404 | `NOT_FOUND` | Document or collection not found |
| 429 | `RATE_LIMITED` | Too many requests |
| 500 | `INTERNAL_ERROR` | Server error |
| 503 | `DATABASE_UNAVAILABLE` | NeuralDB is unreachable |

## Rate Limits

| Plan | Queries/min | Documents/min |
|------|------------|--------------|
| Starter | 30 | 100 |
| Developer | 300 | 1,000 |
| Business | 3,000 | 10,000 |
| Business Plus | 10,000 | 50,000 |

Rate limit headers are included in all responses:

```
X-RateLimit-Limit: 3000
X-RateLimit-Remaining: 2847
X-RateLimit-Reset: 1716998460
```

## Pagination

Use `limit` and `offset` (or cursor-based pagination for large datasets):

```json
{
  "query": "SELECT * FROM documents WHERE source = $1 ORDER BY created_at DESC",
  "params": ["web-scraper"],
  "limit": 20,
  "offset": 40
}
```

Response includes pagination metadata:

```json
{
  "rows": [...],
  "rowCount": 20,
  "totalCount": 1500,
  "hasMore": true,
  "nextCursor": "eyJpZCI6Ii4uLiIsImNyZWF0ZWRfYXQiOiIuLi4ifQ=="
}
```
