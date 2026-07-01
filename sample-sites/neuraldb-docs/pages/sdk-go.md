---
title: Go SDK
sort: 120
section-id: client-sdks
keywords: Go, Golang, SDK, client, connection pool, query builder, pgx
description: The NeuralDB Go SDK — installation, connection pooling, and vector query builder
language: en
---

# Go SDK

The NeuralDB Go SDK provides idiomatic Go bindings built on top of `pgx`, the high-performance PostgreSQL driver for Go.

## Installation

```bash
go get github.com/neuraldb/neuraldb-go
```

Requires Go 1.21+.

## Connecting

### Single Connection

```go
package main

import (
    "context"
    "fmt"
    "log"

    "github.com/neuraldb/neuraldb-go"
)

func main() {
    ctx := context.Background()

    client, err := neuraldb.Connect(ctx, "postgresql://neuraldb:password@localhost:5432/mydb")
    if err != nil {
        log.Fatal("connection failed:", err)
    }
    defer client.Close(ctx)

    var count int64
    err = client.QueryRow(ctx, "SELECT COUNT(*) FROM documents").Scan(&count)
    if err != nil {
        log.Fatal(err)
    }
    fmt.Println("Documents:", count)
}
```

### Connection Pool (Recommended)

```go
import (
    "github.com/neuraldb/neuraldb-go"
    "github.com/jackc/pgx/v5/pgxpool"
)

func NewPool(ctx context.Context) (*neuraldb.Pool, error) {
    config, err := pgxpool.ParseConfig(os.Getenv("NEURALDB_URL"))
    if err != nil {
        return nil, err
    }

    config.MaxConns = 20
    config.MinConns = 5
    config.MaxConnIdleTime = 30 * time.Minute
    config.MaxConnLifetime = time.Hour

    return neuraldb.NewPool(ctx, config)
}
```

## Working with Vectors

### Defining Vector Types

```go
package main

import "github.com/neuraldb/neuraldb-go/types"

// Create a vector from a float32 slice
v := types.NewVector([]float32{0.023, -0.187, 0.412})

// Create from float64 (auto-converted)
v2 := types.NewVectorFromFloat64([]float64{0.023, -0.187, 0.412})

// Access the underlying data
floats := v.Slice()   // []float32
dims := v.Dims()      // int
```

### Inserting a Document with a Vector

```go
type Document struct {
    ID        string
    Content   string
    Embedding types.Vector
}

func InsertDocument(ctx context.Context, pool *neuraldb.Pool, doc Document) error {
    _, err := pool.Exec(ctx,
        `INSERT INTO documents (id, content, embedding) VALUES ($1, $2, $3)`,
        doc.ID, doc.Content, doc.Embedding,
    )
    return err
}
```

### Vector Similarity Search

```go
func SemanticSearch(ctx context.Context, pool *neuraldb.Pool, queryEmbedding []float32, limit int) ([]SearchResult, error) {
    qv := types.NewVector(queryEmbedding)

    rows, err := pool.Query(ctx, `
        SELECT id, content, 1 - (embedding <=> $1) AS similarity
        FROM documents
        WHERE embedding IS NOT NULL
        ORDER BY embedding <=> $1
        LIMIT $2
    `, qv, limit)
    if err != nil {
        return nil, fmt.Errorf("query failed: %w", err)
    }
    defer rows.Close()

    var results []SearchResult
    for rows.Next() {
        var r SearchResult
        err := rows.Scan(&r.ID, &r.Content, &r.Similarity)
        if err != nil {
            return nil, err
        }
        results = append(results, r)
    }

    return results, rows.Err()
}
```

## Query Builder

The SDK includes an optional query builder for type-safe query construction:

```go
import "github.com/neuraldb/neuraldb-go/qb"

// Build a hybrid query
query, args := qb.New().
    Select("id", "name", "price").
    Expr("1 - (embedding <=> $?) AS similarity", queryVector).
    From("products").
    Where(qb.Eq("category", "electronics")).
    Where(qb.GTE("price", 50)).
    Where(qb.LTE("price", 500)).
    Where(qb.GT("stock", 0)).
    OrderByExpr("embedding <=> $?", queryVector).
    Limit(20).
    Build()

rows, err := pool.Query(ctx, query, args...)
```

## Batch Operations

```go
import "github.com/jackc/pgx/v5"

func BatchInsert(ctx context.Context, pool *neuraldb.Pool, docs []Document) error {
    batch := &pgx.Batch{}

    for _, doc := range docs {
        batch.Queue(
            `INSERT INTO documents (content, embedding) VALUES ($1, $2)`,
            doc.Content, doc.Embedding,
        )
    }

    results := pool.SendBatch(ctx, batch)
    defer results.Close()

    for range docs {
        _, err := results.Exec()
        if err != nil {
            return fmt.Errorf("batch insert error: %w", err)
        }
    }

    return results.Close()
}
```

## Transactions

```go
func TransactionalInsert(ctx context.Context, pool *neuraldb.Pool, docs []Document) error {
    return pool.BeginTxFunc(ctx, pgx.TxOptions{
        IsoLevel: pgx.ReadCommitted,
    }, func(tx pgx.Tx) error {
        for _, doc := range docs {
            _, err := tx.Exec(ctx,
                `INSERT INTO documents (content, embedding) VALUES ($1, $2)`,
                doc.Content, doc.Embedding,
            )
            if err != nil {
                return err // auto-rolled back by BeginTxFunc
            }
        }

        _, err := tx.Exec(ctx,
            `UPDATE stats SET doc_count = doc_count + $1`,
            len(docs),
        )
        return err
    })
}
```

## Scanning Results into Structs

```go
import "github.com/jackc/pgx/v5/pgxscan"

type Product struct {
    ID         string       `db:"id"`
    Name       string       `db:"name"`
    Price      float64      `db:"price"`
    Similarity float64      `db:"similarity"`
}

func SearchProducts(ctx context.Context, pool *neuraldb.Pool, qv types.Vector) ([]Product, error) {
    var products []Product
    err := pgxscan.Select(ctx, pool, &products, `
        SELECT id, name, price, 1 - (embedding <=> $1) AS similarity
        FROM products
        WHERE available = true
        ORDER BY embedding <=> $1
        LIMIT 10
    `, qv)
    return products, err
}
```

## Context and Cancellation

All SDK methods accept a `context.Context`. Use it for timeout and cancellation:

```go
// Set a 5-second query deadline
ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
defer cancel()

rows, err := pool.Query(ctx, "SELECT ...", args...)
```

## Error Handling

```go
import (
    "github.com/jackc/pgx/v5/pgconn"
    "errors"
)

_, err := pool.Exec(ctx, "INSERT INTO ...", args...)
if err != nil {
    var pgErr *pgconn.PgError
    if errors.As(err, &pgErr) {
        switch pgErr.Code {
        case "23505":  // unique_violation
            return ErrDuplicate
        case "23503":  // foreign_key_violation
            return ErrForeignKey
        default:
            return fmt.Errorf("database error %s: %s", pgErr.Code, pgErr.Message)
        }
    }
    return err
}
```
