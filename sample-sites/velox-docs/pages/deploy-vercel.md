---
title: Deploy to Vercel
sort: 100
section-id: deployment
keywords: Vercel, deployment, serverless, edge, CI/CD, deploy
description: Step-by-step guide to deploying a Velox application to Vercel
language: en
---

# Deploy to Vercel

Vercel is the recommended hosting platform for Velox applications. The Velox Vercel adapter handles all configuration automatically — no manual `vercel.json` setup is required for most projects.

## Prerequisites

- A Vercel account ([vercel.com](https://vercel.com))
- The Vercel CLI: `npm install -g vercel`
- A Velox project committed to a Git repository (GitHub, GitLab, or Bitbucket)

## Automatic Deployment via Git Integration

### Step 1 — Push Your Project to Git

```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/your-username/your-project.git
git push -u origin main
```

### Step 2 — Import the Project on Vercel

1. Go to [vercel.com/new](https://vercel.com/new)
2. Click **Add New Project** → **Import Git Repository**
3. Select your repository
4. Vercel automatically detects Velox and sets the correct build settings:
   - **Framework Preset:** Velox
   - **Build Command:** `velox build`
   - **Output Directory:** `.velox/output`
   - **Install Command:** `npm ci`

### Step 3 — Configure Environment Variables

In the Vercel project dashboard:
1. Go to **Settings** → **Environment Variables**
2. Add each variable from your `.env.production` file

Do **not** add `PUBLIC_BASE_URL` manually — Vercel sets `VERCEL_URL` automatically and the Velox Vercel adapter uses it.

### Step 4 — Deploy

Click **Deploy**. Vercel will:
1. Clone your repository
2. Install dependencies
3. Run `velox build`
4. Deploy to its global edge network

Your site is live at `https://your-project.vercel.app`.

## Vercel CLI Deployment

For manual or scripted deployments:

```bash
# Install adapter
npm install @velox/vercel

# Deploy to preview (equivalent to a branch deploy)
vercel

# Deploy to production
vercel --prod
```

## Configuring the Vercel Adapter

Install and configure `@velox/vercel`:

```bash
npm install @velox/vercel
```

```typescript
// velox.config.ts
import { defineConfig } from 'velox';
import { vercel } from '@velox/vercel';

export default defineConfig({
  adapter: vercel({
    // Route-level edge function configuration
    edgeRoutes: ['/api/stream', '/api/realtime'],

    // Override ISR revalidation for specific routes
    isr: {
      expiration: 60,             // default revalidation (seconds)
      bypassToken: process.env.VERCEL_ISR_BYPASS_TOKEN,
    },

    // Enable Vercel Image Optimisation (uses Vercel's CDN)
    images: {
      sizes: [640, 1080, 1920],
    },
  }),
});
```

## Edge Functions

Mark individual routes to run on Vercel Edge instead of Node.js serverless:

```typescript
// routes/api/stream+server.ts
export const config = { edge: true };

export const GET = defineHandler(async (req) => {
  // Runs on Vercel Edge — uses Web APIs only
  return new Response('Hello from edge!');
});
```

Edge functions are deployed globally in ~70 Vercel regions and have ~0ms cold start. Use them for latency-sensitive, stateless handlers.

## Custom Domains

1. Go to your project on Vercel → **Settings** → **Domains**
2. Click **Add Domain**
3. Enter your domain (e.g., `example.com`)
4. Follow the DNS configuration instructions:
   - Add a **CNAME** record: `www` → `cname.vercel-dns.com`
   - Add an **A** record: `@` → `76.76.21.21`
5. SSL certificates are provisioned automatically via Let's Encrypt

Set the canonical base URL environment variable in Vercel:

```
PUBLIC_BASE_URL = https://example.com
```

## Preview Deployments

Every pull request gets an automatic preview deployment at a unique URL (`https://your-project-git-branch-name.vercel.app`). This is configured by default and requires no additional setup.

To share preview deployments with your team, enable **Password Protection** under **Settings** → **Deployment Protection**.

## Build Cache

Velox's Velocitor build cache is automatically persisted across deployments by the Vercel adapter. Subsequent deployments typically build 3–5× faster than the first.

## `vercel.json` Reference

For advanced configuration, create a `vercel.json` at your project root:

```json
{
  "regions": ["iad1", "fra1"],
  "cleanUrls": true,
  "trailingSlash": false,
  "headers": [
    {
      "source": "/assets/(.*)",
      "headers": [
        { "key": "Cache-Control", "value": "public, max-age=31536000, immutable" }
      ]
    }
  ],
  "redirects": [
    { "source": "/old-path", "destination": "/new-path", "permanent": true }
  ]
}
```

## Monitoring and Analytics

Enable Vercel Analytics and Speed Insights in your project dashboard. The Velox adapter hooks into these automatically — no code changes needed.

For custom event tracking:

```typescript
import { track } from '@vercel/analytics';

track('button_clicked', { component: 'Hero', variant: 'primary' });
```
