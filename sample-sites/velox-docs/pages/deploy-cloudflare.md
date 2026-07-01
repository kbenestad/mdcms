---
title: Deploy to Cloudflare
sort: 110
section-id: deployment
keywords: Cloudflare, Pages, Workers, deployment, edge, CDN, Wrangler
description: Deploying a Velox application to Cloudflare Pages and Workers
language: en
---

# Deploy to Cloudflare

Velox runs natively on Cloudflare Workers. By combining Cloudflare Pages for static assets and Cloudflare Workers for server-side rendering, you get a globally distributed application with sub-millisecond cold starts.

## Architecture

Velox on Cloudflare uses:
- **Cloudflare Pages** — serves static assets from the CDN edge
- **Cloudflare Workers** — handles SSR requests at the edge
- **KV** — used for ISR page caching
- **D1** — SQLite-at-the-edge database (optional)
- **R2** — object storage for user uploads (optional)

## Setup

Install the Cloudflare adapter:

```bash
npm install @velox/cloudflare
npm install -D wrangler
```

Configure the adapter:

```typescript
// velox.config.ts
import { defineConfig } from 'velox';
import { cloudflare } from '@velox/cloudflare';

export default defineConfig({
  adapter: cloudflare({
    kvNamespace: 'VELOX_CACHE',   // KV namespace for ISR cache
    routes: {
      exclude: ['/admin/*'],       // serve these from Pages CDN only
    },
  }),
  build: {
    target: 'edge',
  },
});
```

## Wrangler Configuration

Create `wrangler.toml`:

```toml
name = "my-velox-app"
compatibility_date = "2026-01-01"
compatibility_flags = ["nodejs_compat"]
pages_build_output_dir = ".velox/output"

[[kv_namespaces]]
binding = "VELOX_CACHE"
id = "your-kv-namespace-id"

[[d1_databases]]
binding = "DB"
database_name = "my-database"
database_id = "your-database-id"

[vars]
NODE_ENV = "production"
```

## Deployment Steps

### Option 1: Cloudflare Pages Dashboard

1. Go to [dash.cloudflare.com](https://dash.cloudflare.com) → **Pages** → **Create a project**
2. Connect your Git provider and select your repository
3. Set build settings:
   - **Framework preset:** Velox
   - **Build command:** `npm run build`
   - **Build output directory:** `.velox/output`
4. Add environment variables
5. Click **Save and Deploy**

### Option 2: Wrangler CLI

```bash
# Log in
npx wrangler login

# Build
npm run build

# Deploy
npx wrangler pages deploy .velox/output --project-name my-velox-app

# Or deploy as a Worker
npx wrangler deploy
```

## Using Cloudflare D1 (SQLite at the Edge)

Cloudflare D1 is a serverless SQLite database that runs at the edge alongside your Workers.

### Create a Database

```bash
npx wrangler d1 create my-database
npx wrangler d1 execute my-database --file=./migrations/001_init.sql
```

### Query D1 in Velox

```typescript
// routes/api/posts+server.ts
import { defineHandler } from 'velox/server';

export const GET = defineHandler(async (req) => {
  // env.DB is automatically injected by the Cloudflare adapter
  const { DB } = process.env as any;
  const { results } = await DB.prepare('SELECT * FROM posts WHERE published = 1').all();
  return Response.json(results);
});
```

Or with Drizzle's D1 driver:

```typescript
import { drizzle } from 'drizzle-orm/d1';
import * as schema from '$lib/schema';

export function getDB(env: Env) {
  return drizzle(env.DB, { schema });
}
```

## Using Cloudflare KV

For key-value storage (feature flags, cached responses):

```typescript
const value = await env.MY_KV.get('my-key');
await env.MY_KV.put('my-key', JSON.stringify(data), { expirationTtl: 3600 });
await env.MY_KV.delete('my-key');
```

## Using Cloudflare R2

For file uploads and object storage:

```typescript
// routes/api/upload+server.ts
import { defineHandler } from 'velox/server';

export const POST = defineHandler(async (req) => {
  const formData = await req.formData();
  const file = formData.get('file') as File;

  const key = `uploads/${Date.now()}-${file.name}`;
  await env.R2_BUCKET.put(key, file.stream(), {
    httpMetadata: { contentType: file.type },
  });

  return Response.json({ url: `https://assets.example.com/${key}` });
});
```

## Custom Domains

1. Add your domain in Cloudflare's DNS settings (it should already be proxied through Cloudflare)
2. Go to Pages → Your project → **Custom domains**
3. Click **Set up a custom domain** and enter your domain
4. Cloudflare provisions SSL automatically

For Workers, add a route in `wrangler.toml`:

```toml
[[routes]]
pattern = "example.com/*"
zone_name = "example.com"
```

## Environment Variables

Set secrets securely:

```bash
npx wrangler secret put DATABASE_URL
npx wrangler secret put SESSION_SECRET
npx wrangler secret put JWT_SECRET
```

Non-secret variables go in `wrangler.toml` under `[vars]` or in the Pages dashboard.

## Performance Tips

- Use **Cache Rules** in the Cloudflare dashboard to cache SSR pages at the CDN layer
- Enable **Argo Smart Routing** for improved global routing
- Use **Tiered Cache** to reduce origin requests
- Set `Cache-Control: public, max-age=0, s-maxage=3600` on ISR pages to let Cloudflare cache them

## Limits

| Feature | Limit |
|---------|-------|
| Worker request timeout | 30s (CPU time) |
| Worker memory | 128 MB |
| KV value size | 25 MB |
| D1 database size | 2 GB |
| R2 object size | 5 GB |
