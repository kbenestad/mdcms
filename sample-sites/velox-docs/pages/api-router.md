---
title: Router API
sort: 100
section-id: api-reference
keywords: router, useRouter, navigate, Link, createRouter, programmatic navigation
description: Complete API reference for the Velox router — createRouter, useRouter, navigate, and Link
language: en
---

# Router API

The Velox router provides both declarative and programmatic navigation. This page documents the full public API surface of `@velox/router`.

## `useRouter()`

The `useRouter` hook returns the current router instance. It is available inside any client-side component:

```typescript
import { useRouter } from 'velox/client';

const router = useRouter();
```

### Router Instance Properties

| Property | Type | Description |
|----------|------|-------------|
| `pathname` | `string` | Current URL pathname, e.g. `/blog/my-post` |
| `search` | `string` | Current query string including `?`, e.g. `?page=2` |
| `hash` | `string` | Current hash fragment including `#` |
| `params` | `Record<string, string>` | Dynamic route parameters |
| `query` | `URLSearchParams` | Parsed query parameters |
| `state` | `unknown` | History state object (if provided to `navigate`) |

### Router Instance Methods

#### `navigate(href, options?)`

Performs client-side navigation to the given href:

```typescript
router.navigate('/dashboard');

// With options:
router.navigate('/profile/edit', {
  replace: true,           // replace current history entry
  state: { from: '/dashboard' }, // pass arbitrary state
  scroll: false,           // don't scroll to top after navigation
});
```

#### `back()` / `forward()`

Navigate through the browser history stack:

```typescript
router.back();
router.forward();
```

#### `prefetch(href)`

Manually prefetch a route (downloads the JS bundle and optionally data):

```typescript
router.prefetch('/heavy-page');
```

#### `refresh()`

Re-run the current route's server block and update the page without a full navigation:

```typescript
router.refresh();
```

## `<Link>` Component

The `<Link>` component renders an accessible `<a>` element with client-side navigation and built-in prefetching:

```tsx
import { Link } from 'velox/client';

<Link href="/about">About</Link>
```

### Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `href` | `string` | required | Destination URL |
| `prefetch` | `'hover' \| 'viewport' \| false` | `'hover'` | Prefetch strategy |
| `replace` | `boolean` | `false` | Replace history entry instead of pushing |
| `scroll` | `boolean` | `true` | Scroll to top after navigation |
| `state` | `unknown` | `undefined` | History state object |
| `activeClass` | `string` | `'active'` | CSS class applied when href matches current pathname |
| `exactActiveClass` | `string` | `'exact-active'` | CSS class applied only on exact pathname match |

```tsx
<Link
  href="/blog"
  prefetch="viewport"
  activeClass="nav-link--active"
  exactActiveClass="nav-link--exact"
>
  Blog
</Link>
```

## `createRouter()`

For testing or server-side use, create a router instance manually:

```typescript
import { createRouter } from 'velox/router';

const router = createRouter({
  base: '/app',               // base path prefix
  history: 'hash',            // 'browser' (default) | 'hash' | 'memory'
  scrollRestoration: 'auto',  // 'auto' | 'manual'
});
```

## `useParams()`

Access current route parameters in any component:

```typescript
import { useParams } from 'velox/client';

const { slug, category } = useParams<{ slug: string; category: string }>();
```

## `useSearchParams()`

Read and update the URL search parameters reactively:

```typescript
import { useSearchParams } from 'velox/client';

const [searchParams, setSearchParams] = useSearchParams();

// Read
const page = searchParams.get('page') ?? '1';

// Update (triggers navigation without full page reload)
setSearchParams({ page: String(currentPage + 1) });

// Merge with existing params
setSearchParams(prev => {
  prev.set('sort', 'date');
  return prev;
});
```

## `usePathname()`

Reactively access the current pathname:

```typescript
import { usePathname } from 'velox/client';

const pathname = usePathname();
// pathname is a Signal<string>
```

## `useNavigate()`

A lightweight hook that returns only the `navigate` function, without the full router object:

```typescript
import { useNavigate } from 'velox/client';

const navigate = useNavigate();
navigate('/login');
```

## Navigation Events

Subscribe to router lifecycle events:

```typescript
import { useRouter } from 'velox/client';

const router = useRouter();

const unsubscribe = router.on('beforeNavigate', ({ to, from, cancel }) => {
  if (hasUnsavedChanges && !confirm('Leave without saving?')) {
    cancel();
  }
});

// Clean up
onCleanup(unsubscribe);
```

Available events: `beforeNavigate`, `afterNavigate`, `navigationError`.

## `redirect()` (Server)

Used inside server blocks and API route handlers:

```typescript
import { redirect } from 'velox/server';

// Temporary redirect (302)
throw redirect('/login');

// Permanent redirect (301)
throw redirect('/new-url', 301);

// With custom headers
throw redirect('/dashboard', 302, {
  'Set-Cookie': 'session=...; Path=/',
});
```

## `notFound()` (Server)

Trigger the nearest `_error.velox` with a 404 status:

```typescript
import { notFound } from 'velox/server';

const post = await db.posts.find(id);
if (!post) throw notFound();
```
