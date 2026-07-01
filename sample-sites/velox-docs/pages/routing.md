---
title: Routing
sort: 100
section-id: core-concepts
keywords: routing, file-based routing, dynamic routes, catch-all, nested routes, navigation
description: How Velox's file-based routing works, including dynamic segments, catch-all routes, and nested layouts
language: en
---

# Routing

Velox uses a file-based routing system. The file tree under the `routes/` directory maps one-to-one to the URL structure of your application. There is no router configuration file — the filesystem is the configuration.

## Basic Routes

Any `.velox` or `.tsx` file placed inside `routes/` becomes a page route:

| File | URL |
|------|-----|
| `routes/index.velox` | `/` |
| `routes/about.velox` | `/about` |
| `routes/blog/index.velox` | `/blog` |
| `routes/blog/my-post.velox` | `/blog/my-post` |
| `routes/shop/shoes/index.velox` | `/shop/shoes` |

## Dynamic Segments

Wrap a path segment in square brackets to make it dynamic:

```
routes/
└── blog/
    └── [slug].velox   →  /blog/:slug
```

Inside the route, access the parameter via the `params` object in the server block:

```tsx
---
const { slug } = params;
const post = await db.posts.findBySlug(slug);

if (!post) {
  throw new NotFound();
}

export const meta = { title: post.title };
---

<article>
  <h1>{post.title}</h1>
  <div innerHTML={post.htmlContent} />
</article>
```

### Multiple Dynamic Segments

You can nest multiple dynamic segments:

```
routes/
└── [category]/
    └── [slug].velox   →  /:category/:slug
```

## Optional Dynamic Segments

Wrap a segment in double square brackets to make it optional:

```
routes/
└── blog/
    └── [[page]].velox   →  /blog  and  /blog/:page
```

Inside the route, `params.page` will be `undefined` when the segment is not present.

## Catch-All Routes

Use the spread syntax `[...rest]` to match any number of path segments:

```
routes/
└── docs/
    └── [...path].velox   →  /docs/  and  /docs/a/b/c/d
```

`params.path` is an array of path segments: `['a', 'b', 'c', 'd']`.

### Optional Catch-All

`[[...rest]]` matches zero or more segments (i.e., the base path also matches):

```
routes/
└── [[...slug]].velox   →  /  and  /anything/at/all
```

## API Routes

Files with a `+server.ts` or `+server.js` suffix define API endpoints. They export HTTP method handlers named `GET`, `POST`, `PUT`, `PATCH`, `DELETE`, or `OPTIONS`:

```typescript
// routes/api/users+server.ts
import { defineHandler } from 'velox/server';
import { db } from '$lib/db';

export const GET = defineHandler(async (req) => {
  const users = await db.users.findMany();
  return Response.json(users);
});

export const POST = defineHandler(async (req) => {
  const body = await req.json();
  const user = await db.users.create({ data: body });
  return Response.json(user, { status: 201 });
});
```

## Route Groups

Wrap a directory name in parentheses to create a route group. Groups do not affect the URL — they are purely an organisational tool:

```
routes/
└── (marketing)/
    ├── index.velox       →  /
    ├── about.velox       →  /about
    └── pricing.velox     →  /pricing
    └── _layout.velox     ← layout applied only to marketing routes
```

This is useful when you want different layouts for different sections of your site without adding URL segments.

## Special Files

### `_layout.velox`

A `_layout.velox` file wraps all sibling routes and nested route directories. Layouts receive a `<slot />` where child content is injected:

```tsx
// routes/blog/_layout.velox
---
import Sidebar from '../../components/Sidebar.tsx';
---

<div class="blog-layout">
  <Sidebar />
  <main>
    <slot />
  </main>
</div>
```

Layouts nest automatically — a deeply nested `_layout.velox` wraps its subtree, and the tree up to the root layout wraps the whole thing.

### `_error.velox`

Renders when an unhandled error occurs or when a `NotFound` is thrown. Receives `error` and `status` as props.

### `_loading.velox`

Shown as an immediate placeholder during route transitions (client-side navigation) while the next route is loading.

## Programmatic Navigation

Use the `useRouter` hook for client-side navigation in interactive components:

```typescript
import { useRouter } from 'velox/client';

export default function LoginButton() {
  const router = useRouter();

  async function handleLogin() {
    await performLogin();
    router.navigate('/dashboard');
  }

  return <button onClick={handleLogin}>Log in</button>;
}
```

### The `<Link>` Component

For declarative navigation, use the `<Link>` component. It renders an `<a>` tag with client-side navigation and prefetching:

```tsx
import { Link } from 'velox/client';

<Link href="/about">About Us</Link>
<Link href="/blog/my-post" prefetch="hover">My Post</Link>
```

The `prefetch` prop accepts `"hover"` (prefetch on hover), `"viewport"` (prefetch when link enters viewport), or `false` (no prefetch).

## Redirects

Return a redirect from a server block or API handler:

```typescript
import { redirect } from 'velox/server';

// In a server block
if (!user) {
  throw redirect('/login', 302);
}

// In an API route
export const GET = defineHandler(async () => {
  return redirect('/new-location', 301);
});
```

## Route Metadata

Export `meta` from a route's server block to set page metadata:

```typescript
export const meta = {
  title: 'Page Title',
  description: 'Page description for SEO',
  openGraph: {
    image: 'https://example.com/og.png',
  },
  robots: 'index, follow',
};
```

For dynamic metadata, use a function:

```typescript
export const meta = () => ({
  title: post.title,
  description: post.excerpt,
});
```
