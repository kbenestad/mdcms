---
title: Data Fetching
sort: 130
section-id: core-concepts
keywords: data fetching, SSR, SSG, ISR, server-side rendering, static generation, fetch, async
description: How to fetch data in Velox using SSR, SSG, ISR, and client-side fetching patterns
language: en
---

# Data Fetching

Velox provides multiple data-fetching patterns depending on when and how often your data changes. You can mix strategies freely across routes in the same project.

## Server-Side Rendering (SSR)

In SSR mode, data is fetched fresh on every request. Use `await` directly in the server block of a `.velox` route:

```tsx
---
// routes/blog/[slug].velox
import { db } from '$lib/db';
import { NotFound } from 'velox/server';

const { slug } = params;
const post = await db.posts.findBySlug(slug);

if (!post) throw new NotFound();

export const meta = {
  title: post.title,
  description: post.excerpt,
};
export const config = { render: 'ssr' };
---

<article>
  <h1>{post.title}</h1>
  <p class="byline">By {post.author} on {post.publishedAt}</p>
  <div innerHTML={post.htmlContent} />
</article>
```

The `render: 'ssr'` export is optional — SSR is the default for routes that contain `await` expressions.

### Request Context in SSR

In SSR mode, the `request` object is available in the server block:

```typescript
const authHeader = request.headers.get('Authorization');
const userAgent = request.headers.get('User-Agent');
const cookieHeader = request.headers.get('Cookie');
```

## Static Site Generation (SSG)

SSG routes are rendered once at build time. They are ideal for content that rarely changes.

```tsx
---
export const config = { render: 'ssg' };

const features = await fetch('https://api.example.com/features').then(r => r.json());
---

<section>
  <h1>Features</h1>
  <ul>
    {features.map(f => <li>{f.name}: {f.description}</li>)}
  </ul>
</section>
```

### Dynamic SSG Routes

For SSG routes with dynamic segments, export a `paths` function to tell Velox which parameter values to pre-render:

```tsx
---
import { db } from '$lib/db';

export const config = { render: 'ssg' };

// Called at build time to enumerate all slugs
export async function paths() {
  const slugs = await db.posts.findManySlugs();
  return slugs.map(slug => ({ slug }));
}

const { slug } = params;
const post = await db.posts.findBySlug(slug);
export const meta = { title: post.title };
---

<article>
  <h1>{post.title}</h1>
  <div innerHTML={post.htmlContent} />
</article>
```

## Incremental Static Regeneration (ISR)

ISR generates pages statically but revalidates them in the background after a configurable interval:

```tsx
---
export const config = {
  render: 'isr',
  revalidate: 3600, // regenerate at most once per hour
};

const products = await db.products.findMany({ orderBy: 'created_at' });
---

<section>
  {products.map(p => <ProductCard product={p} />)}
</section>
```

On a cache miss (first request, or after `revalidate` seconds), Velox serves the stale page immediately while regenerating the fresh version in the background. The next request gets the fresh version.

### Manual Revalidation

Trigger revalidation programmatically (e.g., from a webhook):

```typescript
// routes/api/revalidate+server.ts
import { revalidatePath, revalidateTag } from 'velox/server';

export const POST = defineHandler(async (req) => {
  const { path, secret } = await req.json();

  if (secret !== process.env.REVALIDATE_SECRET) {
    return Response.json({ error: 'Unauthorized' }, { status: 401 });
  }

  await revalidatePath(path);
  return Response.json({ revalidated: true });
});
```

Tag-based revalidation:

```typescript
// When fetching, attach cache tags:
const data = await fetch('/api/products', {
  next: { tags: ['products'] }
});

// Later, invalidate all pages that used the 'products' tag:
await revalidateTag('products');
```

## Client-Side Fetching

For data that must be fresh on the client (user-specific dashboards, real-time data), use client-side fetching in an interactive component:

```tsx
import { signal, onMount } from 'velox/client';

export default function UserDashboard() {
  const stats = signal<DashboardStats | null>(null);
  const error = signal<string | null>(null);
  const loading = signal(true);

  onMount(async () => {
    try {
      const res = await fetch('/api/dashboard/stats', {
        credentials: 'include',
      });
      if (!res.ok) throw new Error('Failed to fetch stats');
      stats.value = await res.json();
    } catch (e: any) {
      error.value = e.message;
    } finally {
      loading.value = false;
    }
  });

  return (
    <div>
      {loading.value && <Spinner />}
      {error.value && <ErrorMessage message={error.value} />}
      {stats.value && <StatsGrid stats={stats.value} />}
    </div>
  );
}
```

### Using `@velox/query`

For production client-side data fetching, `@velox/query` handles caching, deduplication, background refetch, and stale-while-revalidate:

```typescript
import { useQuery } from '@velox/query';

export default function ProductList() {
  const { data, status, error, refetch } = useQuery({
    key: ['products'],
    fetcher: () => fetch('/api/products').then(r => r.json()),
    staleTime: 30_000,
    refetchOnWindowFocus: true,
  });

  if (status === 'loading') return <Spinner />;
  if (status === 'error') return <p>Error: {error.message}</p>;

  return (
    <ul>
      {data.map(p => <li key={p.id}>{p.name}</li>)}
    </ul>
  );
}
```

## Parallel Data Fetching

Fetch multiple data sources in parallel using `Promise.all`:

```tsx
---
const [user, posts, categories] = await Promise.all([
  db.users.findById(userId),
  db.posts.findByUser(userId),
  db.categories.findAll(),
]);
---
```

## Streaming

For pages with slow data, use streaming to send the page shell immediately and stream in the slow parts:

```tsx
---
import { Suspense } from 'velox';

const fastData = await db.pageConfig.find();

// Slow query wrapped in Suspense — the page shell renders immediately
const slowPostsPromise = db.posts.findMany({ include: { comments: true } });
---

<main>
  <h1>{fastData.title}</h1>
  <Suspense fallback={<Spinner />}>
    <PostList postsPromise={slowPostsPromise} />
  </Suspense>
</main>
```

The `<Suspense>` boundary renders its fallback immediately while the async data resolves, then streams the final HTML to the client.

## Fetch Utilities

Velox wraps the global `fetch` with several quality-of-life additions in server contexts:

```typescript
import { fetch } from 'velox/server';

// Automatic base URL resolution for relative paths
const data = await fetch('/api/internal-endpoint');

// Request deduplication — concurrent identical fetches share one in-flight request
const [a, b] = await Promise.all([fetch('/api/same'), fetch('/api/same')]);
// ^ only one HTTP request is made
```
