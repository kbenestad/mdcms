---
title: Docker Install
sort: 100
section-id: installation
keywords: Docker, install, docker run, docker-compose, volumes, container
description: Installing NeuralDB using Docker — single container and docker-compose setups
language: en
---

# Docker Install

Docker is the fastest way to run NeuralDB locally or in a single-server deployment. NeuralDB's official Docker image is published to Docker Hub as `neuraldb/neuraldb`.

## Quick Start

Run a single NeuralDB instance:

```bash
docker run -d \
  --name neuraldb \
  -p 5432:5432 \
  -e NEURALDB_PASSWORD=mypassword \
  -e NEURALDB_DB=mydb \
  -v neuraldb_data:/var/lib/neuraldb/data \
  neuraldb/neuraldb:latest
```

Connect with psql:

```bash
psql -h localhost -p 5432 -U neuraldb -d mydb
# Password: mypassword
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `NEURALDB_PASSWORD` | required | Password for the `neuraldb` superuser |
| `NEURALDB_USER` | `neuraldb` | Superuser username |
| `NEURALDB_DB` | `neuraldb` | Default database name |
| `NEURALDB_PORT` | `5432` | TCP port |
| `NEURALDB_MAX_CONNECTIONS` | `100` | Maximum concurrent connections |
| `NEURALDB_SHARED_BUFFERS` | `256MB` | Row store page cache |
| `NEURALDB_VECTOR_BUFFER` | `512MB` | Vector index memory |
| `NEURALDB_WAL_LEVEL` | `replica` | WAL level (`minimal`, `replica`, `logical`) |

## Available Tags

| Tag | Description |
|-----|-------------|
| `latest` | Latest stable release |
| `1.0` | Specific major version |
| `1.0.3` | Specific patch version |
| `nightly` | Nightly build from main branch |
| `1.0-alpine` | Alpine-based image (smaller, less glibc compat) |

## Volumes

NeuralDB stores data in `/var/lib/neuraldb/data` inside the container. Always mount a named volume or bind mount to persist data:

```bash
# Named volume (recommended)
docker volume create neuraldb_data
docker run -v neuraldb_data:/var/lib/neuraldb/data neuraldb/neuraldb:latest

# Bind mount
docker run -v /srv/neuraldb:/var/lib/neuraldb/data neuraldb/neuraldb:latest
```

The data directory includes:
- `base/` — table and index data
- `vectors/` — HNSW graph files and raw vector data
- `wal/` — write-ahead log segments
- `neuraldb.conf` — runtime configuration (editable)

## docker-compose Setup

A production-grade docker-compose file for NeuralDB with automatic backup:

```yaml
# docker-compose.yml
version: '3.9'

services:
  neuraldb:
    image: neuraldb/neuraldb:1.0
    container_name: neuraldb
    restart: unless-stopped
    ports:
      - "127.0.0.1:5432:5432"   # bind to localhost only — use nginx for external access
    environment:
      NEURALDB_PASSWORD: ${NEURALDB_PASSWORD}
      NEURALDB_USER: ${NEURALDB_USER:-neuraldb}
      NEURALDB_DB: ${NEURALDB_DB:-neuraldb}
      NEURALDB_SHARED_BUFFERS: "4GB"
      NEURALDB_VECTOR_BUFFER: "8GB"
      NEURALDB_MAX_CONNECTIONS: "200"
    volumes:
      - neuraldb_data:/var/lib/neuraldb/data
      - neuraldb_wal:/var/lib/neuraldb/wal
      - ./neuraldb.conf:/etc/neuraldb/neuraldb.conf:ro   # optional custom config
    shm_size: '2gb'    # increase shared memory for large sort operations
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${NEURALDB_USER:-neuraldb}"]
      interval: 10s
      timeout: 5s
      retries: 5
    deploy:
      resources:
        limits:
          memory: 16G
        reservations:
          memory: 8G

  neuraldb-backup:
    image: neuraldb/neuraldb-backup:latest
    environment:
      NEURALDB_HOST: neuraldb
      NEURALDB_PASSWORD: ${NEURALDB_PASSWORD}
      S3_BUCKET: ${BACKUP_S3_BUCKET}
      S3_PREFIX: backups/neuraldb/
      SCHEDULE: "0 2 * * *"    # 2am daily
    depends_on:
      neuraldb:
        condition: service_healthy

volumes:
  neuraldb_data:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: /srv/neuraldb/data
  neuraldb_wal:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: /srv/neuraldb/wal
```

Start with:

```bash
echo "NEURALDB_PASSWORD=$(openssl rand -base64 32)" > .env
docker-compose up -d
```

## Initialisation Scripts

Place `.sql` or `.sh` scripts in `/docker-entrypoint-initdb.d/` to run them on first startup:

```bash
docker run \
  -v ./init-scripts:/docker-entrypoint-initdb.d:ro \
  -e NEURALDB_PASSWORD=mypassword \
  neuraldb/neuraldb:latest
```

```sql
-- init-scripts/01-schema.sql
CREATE TABLE documents (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  content TEXT NOT NULL,
  embedding VECTOR(1536),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX ON documents USING hnsw (embedding vector_cosine_ops);
```

## Memory Tuning

For production, size the container memory based on your dataset:

```
Recommended memory = shared_buffers + vector_buffer + (max_connections × work_mem) + OS overhead
```

For a typical RAG application (5M documents, 1536 dimensions):
- `vector_buffer` ≈ 5M × 1536 × 4B × 1.3 = ~40 GB
- `shared_buffers` = 8 GB
- `work_mem` × connections = 128MB × 50 = 6.4 GB
- **Total**: ~56 GB — provision a 64 GB container

## Upgrading

```bash
# Pull the new image
docker pull neuraldb/neuraldb:1.1

# Stop the current container (data is safe in the volume)
docker stop neuraldb && docker rm neuraldb

# Start with the new image
docker run -d --name neuraldb \
  -v neuraldb_data:/var/lib/neuraldb/data \
  -e NEURALDB_PASSWORD=mypassword \
  neuraldb/neuraldb:1.1

# Run any pending migrations
docker exec neuraldb neuraldb-migrate
```
