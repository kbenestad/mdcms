---
title: Docker
sort: 120
section-id: deployment
keywords: Docker, Dockerfile, docker-compose, container, containerisation, deployment
description: Containerising a Velox application with Docker and docker-compose
language: en
---

# Docker

Containerising your Velox application with Docker makes it portable across any infrastructure — from a simple VPS to a Kubernetes cluster. This guide covers building optimised Docker images and running multi-service stacks with docker-compose.

## Dockerfile

A production-grade multi-stage Dockerfile:

```dockerfile
# Stage 1: Install dependencies
FROM node:22-alpine AS deps
WORKDIR /app

# Copy package manifests only — enables Docker layer caching
COPY package.json package-lock.json ./
RUN npm ci --frozen-lockfile

# Stage 2: Build the application
FROM node:22-alpine AS builder
WORKDIR /app

COPY --from=deps /app/node_modules ./node_modules
COPY . .

# Build args — pass at build time
ARG PUBLIC_BASE_URL
ARG NODE_ENV=production
ENV PUBLIC_BASE_URL=$PUBLIC_BASE_URL
ENV NODE_ENV=$NODE_ENV

RUN npm run build

# Stage 3: Production runtime
FROM node:22-alpine AS runner
WORKDIR /app

ENV NODE_ENV=production
ENV PORT=3700

# Create non-root user for security
RUN addgroup --system --gid 1001 veloxgroup && \
    adduser --system --uid 1001 veloxuser

# Copy only production artefacts
COPY --from=builder --chown=veloxuser:veloxgroup /app/.velox/output ./
COPY --from=builder --chown=veloxuser:veloxgroup /app/package.json ./

# Install production dependencies only
RUN npm ci --omit=dev --frozen-lockfile

USER veloxuser

EXPOSE 3700

CMD ["node", "server.js"]
```

## Building and Running

```bash
# Build the image
docker build \
  --build-arg PUBLIC_BASE_URL=https://example.com \
  -t my-velox-app:latest .

# Run the container
docker run \
  --env-file .env.production \
  -p 3700:3700 \
  --name velox-app \
  my-velox-app:latest

# Run in background
docker run -d \
  --env-file .env.production \
  -p 3700:3700 \
  --restart unless-stopped \
  --name velox-app \
  my-velox-app:latest
```

## `.dockerignore`

Exclude files from the build context to speed up builds:

```
node_modules
.velox
.git
.gitignore
*.md
.env
.env.*
!.env.example
tests
*.test.*
*.spec.*
coverage
```

## docker-compose

A complete stack with the app, PostgreSQL, and Redis:

```yaml
# docker-compose.yml
version: '3.9'

services:
  app:
    build:
      context: .
      args:
        PUBLIC_BASE_URL: ${PUBLIC_BASE_URL:-http://localhost:3700}
    image: my-velox-app:latest
    ports:
      - "3700:3700"
    environment:
      NODE_ENV: production
      DATABASE_URL: postgresql://velox:${DB_PASSWORD}@db:5432/velox
      REDIS_URL: redis://redis:6379
      SESSION_SECRET: ${SESSION_SECRET}
      JWT_SECRET: ${JWT_SECRET}
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "wget", "-qO-", "http://localhost:3700/api/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: velox
      POSTGRES_PASSWORD: ${DB_PASSWORD}
      POSTGRES_DB: velox
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U velox"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    command: redis-server --requirepass ${REDIS_PASSWORD} --appendonly yes
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "--no-auth-warning", "-a", "${REDIS_PASSWORD}", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/ssl:/etc/nginx/ssl:ro
      - nginx_cache:/var/cache/nginx
    depends_on:
      - app
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
  nginx_cache:
```

## Nginx Reverse Proxy

```nginx
# nginx/nginx.conf
events { worker_connections 1024; }

http {
  upstream velox_app {
    server app:3700;
    keepalive 64;
  }

  # Redirect HTTP → HTTPS
  server {
    listen 80;
    server_name example.com www.example.com;
    return 301 https://$host$request_uri;
  }

  server {
    listen 443 ssl http2;
    server_name example.com www.example.com;

    ssl_certificate     /etc/nginx/ssl/fullchain.pem;
    ssl_certificate_key /etc/nginx/ssl/privkey.pem;
    ssl_protocols       TLSv1.2 TLSv1.3;
    ssl_ciphers         HIGH:!aNULL:!MD5;

    # Static assets with long cache
    location /assets/ {
      proxy_pass http://velox_app;
      add_header Cache-Control "public, max-age=31536000, immutable";
    }

    # Application
    location / {
      proxy_pass http://velox_app;
      proxy_http_version 1.1;
      proxy_set_header Upgrade $http_upgrade;
      proxy_set_header Connection 'upgrade';
      proxy_set_header Host $host;
      proxy_set_header X-Real-IP $remote_addr;
      proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
      proxy_set_header X-Forwarded-Proto $scheme;
      proxy_cache_bypass $http_upgrade;
    }
  }
}
```

## Health Check Endpoint

Add a health check to your application for Docker and load balancers:

```typescript
// routes/api/health+server.ts
import { defineHandler, json } from 'velox/server';
import { db } from '$lib/db';

export const GET = defineHandler(async () => {
  try {
    await db.$queryRaw`SELECT 1`;
    return json({ status: 'ok', timestamp: new Date().toISOString() });
  } catch (error) {
    return json({ status: 'error', error: String(error) }, { status: 503 });
  }
});
```

## Running Database Migrations

Run migrations as a separate one-shot container before starting the app:

```yaml
# docker-compose.yml — add this service
  migrate:
    image: my-velox-app:latest
    command: npx prisma migrate deploy
    environment:
      DATABASE_URL: postgresql://velox:${DB_PASSWORD}@db:5432/velox
    depends_on:
      db:
        condition: service_healthy
    restart: "no"
```

## Container Best Practices

| Practice | Why |
|----------|-----|
| Multi-stage builds | Reduces final image size by 60–80% |
| Non-root user | Limits damage if the container is compromised |
| Read-only filesystem | Mount only what needs to be writable |
| `--restart unless-stopped` | Survives host reboots |
| Resource limits | Prevents a runaway container from affecting neighbours |
| Health checks | Enables zero-downtime rolling updates |

Set resource limits:

```yaml
app:
  deploy:
    resources:
      limits:
        cpus: '1.0'
        memory: 512M
      reservations:
        cpus: '0.25'
        memory: 128M
```
