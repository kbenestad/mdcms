---
title: Performance
sort: 140
section-id: guides
keywords: performance, code splitting, lazy loading, caching, optimisation, Core Web Vitals
description: Performance optimisation strategies for Velox apps — code splitting, lazy loading, and caching
language: en
---

# Performance

![Performance Dashboard](assets/images/performance.jpg)

Velox is designed to be fast by default. The Rust-based compiler handles tree-shaking, code splitting, and asset optimisation automatically. This guide covers the additional strategies you can apply to push your application to peak performance.

## Core Web Vitals Targets

Before optimising, establish baselines. Aim for:

| Metric | Good | Needs Work |
|--------|------|-----------|
| LCP (Largest Contentful Paint) | ≤ 2.5s | > 4.0s |
| FID / INP (Interaction to Next Paint) | ≤ 200ms | > 500ms |
| CLS (Cumulative Layout Shift) | ≤ 0.1 | > 0.25 |
| TTFB (Time to First Byte) | ≤ 800ms | > 1800ms |

Use Velox's built-in analytics to monitor these in production:

```typescript
// velox.config.ts
export default defineConfig({
  analytics: {
    webVitals: true,
    endpoint: '/api/analytics/vitals',
  },
});
```

## Code Splitting

Velox automatically splits your JavaScript bundle by route. Every route gets its own chunk, and shared code is extracted into a common chunk. You do not need to configure this.

For further control, use dynamic imports:

```typescript
// Only loads when the user clicks "Open"
const HeavyEditor = lazy(() => import('./HeavyEditor'));

function PostPage() {
  const isEditing = signal(false);
  return (
    <div>
      <h1>{post.title}</h1>
      {isEditing.value && (
        <Suspense fallback={<Skeleton />}>
          <HeavyEditor post={post} />
        </Suspense>
      )}
      <button onClick={() => isEditing.value = true}>Edit</button>
    </div>
  );
}
```

## Lazy Hydration

Delay hydration of interactive components until they are needed:

```tsx
<!-- Hydrate only when the component scrolls into view -->
<CommentSection client:visible postId={post.id} />

<!-- Hydrate only when the browser is idle -->
<AnalyticsWidget client:idle />

<!-- Hydrate only when a CSS media query matches -->
<MobileNav client:media="(max-width: 768px)" />

<!-- Never hydrate — purely server-rendered, no JS -->
<StaticSidebar />
```

The less JavaScript you ship to the client, the better the INP score.

## Image Optimisation

Enable image optimisation in `velox.config.ts`:

```typescript
assets: {
  imageOptimisation: {
    enabled: true,
    formats: ['webp', 'avif'],
    quality: 85,
    maxWidth: 2000,
  },
},
```

Use the `<Image>` component for automatic width/height and format negotiation:

```tsx
import { Image } from 'velox';

<Image
  src="/assets/images/hero.jpg"
  alt="Hero image"
  width={1200}
  height={400}
  priority        // preload this image (use for above-the-fold images)
  sizes="(max-width: 768px) 100vw, 1200px"
/>
```

The `priority` prop adds a `<link rel="preload">` tag to the document head and marks the image as `fetchpriority="high"`, which is the single biggest LCP improvement for image-heavy pages.

## HTTP Caching

Set appropriate `Cache-Control` headers for your routes:

```typescript
// In a route server block
response.headers.set('Cache-Control', 'public, max-age=3600, stale-while-revalidate=86400');

// Or via config for specific paths
export default defineConfig({
  headers: [
    {
      source: '/assets/*',
      headers: [
        { key: 'Cache-Control', value: 'public, max-age=31536000, immutable' },
      ],
    },
    {
      source: '/',
      headers: [
        { key: 'Cache-Control', value: 'public, max-age=0, s-maxage=3600, stale-while-revalidate=86400' },
      ],
    },
  ],
});
```

## Server-Side Caching

Cache expensive computations and database queries:

```typescript
import { useCache } from 'velox/server';

const cache = useCache();

async function getPopularPosts() {
  const cached = await cache.get<Post[]>('posts:popular');
  if (cached) return cached;

  const posts = await db.posts.findMany({
    where: { published: true },
    orderBy: { viewCount: 'desc' },
    take: 10,
  });

  await cache.set('posts:popular', posts, { ttl: 300 }); // 5 minutes
  return posts;
}
```

## Database Query Optimisation

Common patterns that prevent N+1 queries:

```typescript
// Bad: N+1 query
const posts = await db.post.findMany();
const postsWithAuthors = await Promise.all(
  posts.map(p => db.user.findById(p.authorId)) // N extra queries!
);

// Good: single query with include
const postsWithAuthors = await db.post.findMany({
  include: { author: { select: { id: true, name: true } } },
});
```

Add indexes for commonly filtered columns:

```sql
-- In a migration
CREATE INDEX CONCURRENTLY idx_posts_published_created
  ON posts (published, created_at DESC)
  WHERE published = true;
```

## Edge Deployment

Deploy to edge locations close to your users:

```typescript
// velox.config.ts
export default defineConfig({
  build: {
    target: 'edge',
  },
});
```

Edge-compatible routes must use Web APIs only:

```typescript
// ✅ Edge-compatible
import { defineHandler } from 'velox/server';
export const GET = defineHandler(async (req) => {
  const data = await fetch('https://api.example.com/data');
  return Response.json(await data.json());
});

// ❌ Not edge-compatible (uses Node.js built-ins)
import fs from 'node:fs';
```

## Bundle Analysis

Generate and review a bundle analysis report:

```bash
ANALYZE=1 npm run build
# Opens .velox/output/analyze.html in your browser
```

Look for:
- Unexpectedly large dependencies (replace with smaller alternatives)
- Duplicate dependencies at different versions
- Client-side imports of server-only packages

## Prefetching

Configure link prefetching globally:

```typescript
export default defineConfig({
  prefetch: {
    defaultStrategy: 'hover',   // 'hover' | 'viewport' | false
    concurrency: 2,             // max concurrent prefetch requests
    ignore: ['/admin/*', '/api/*'],
  },
});
```

## Font Loading

Avoid layout shift from font loading:

```css
/* styles/global.css */
@font-face {
  font-family: 'Inter';
  src: url('/fonts/inter-var.woff2') format('woff2');
  font-weight: 100 900;
  font-display: swap;  /* show fallback text immediately */
}
```

```tsx
// layouts/default.velox
<Head>
  <link rel="preload" href="/fonts/inter-var.woff2" as="font" type="font/woff2" crossOrigin="" />
</Head>
```

## Performance Monitoring

Integrate with monitoring services:

```typescript
// lib/monitoring.ts
export function reportWebVitals({ name, value, id }: Metric) {
  fetch('/api/analytics/vitals', {
    method: 'POST',
    body: JSON.stringify({ name, value, id, page: window.location.pathname }),
    keepalive: true,
  });
}
```
