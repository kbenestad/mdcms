---
title: Hooks API
sort: 140
section-id: api-reference
keywords: hooks, useRequest, useSession, useCookies, useEnv, server hooks
description: Reference for Velox server-side hooks — useRequest, useSession, useCookies, and useEnv
language: en
---

# Hooks API

Velox provides server-side hooks for accessing request context, sessions, cookies, and environment variables within route server blocks and middleware. These hooks are only available in server-side contexts.

## `useRequest()`

Returns the current `VeloxRequest` object:

```typescript
import { useRequest } from 'velox/server';

const request = useRequest();

const method = request.method;
const pathname = new URL(request.url).pathname;
const userAgent = request.headers.get('User-Agent');
```

This is equivalent to the `request` variable that is automatically available in server blocks, but `useRequest()` is useful in helper functions that are called from a server block without threading `request` through manually.

### Full Request Object Reference

```typescript
interface VeloxRequest extends Request {
  params: Record<string, string>;         // route dynamic params
  query: URLSearchParams;                 // parsed query string
  cookies: RequestCookies;               // parsed cookies
  context: Map<string, unknown>;         // middleware-set values
  ip: string | null;                      // client IP address
  geo: GeoInfo | null;                   // geographic info (if available)
}
```

## `useSession()`

Reads and writes the server-managed session. Sessions are stored server-side (in memory, Redis, or a database depending on your `session.store` configuration) and identified by a signed cookie.

```typescript
import { useSession } from 'velox/server';

const session = await useSession<{ userId: string; role: string }>();

// Read
const userId = session.data.userId;
const role = session.data.role;

// Write — persists changes to the session store
await session.set('userId', '123');
await session.set('role', 'admin');

// Update multiple at once
await session.update({ userId: '123', role: 'admin' });

// Destroy the session (logout)
await session.destroy();

// Regenerate session ID (after privilege change — prevents fixation)
await session.regenerate();
```

### Session Configuration

Configure the session store in `velox.config.ts`:

```typescript
import { defineConfig } from 'velox';
import { RedisSessionStore } from '@velox/session-redis';

export default defineConfig({
  session: {
    secret: process.env.SESSION_SECRET!,
    cookieName: 'velox.session',
    maxAge: 60 * 60 * 24 * 7,       // 7 days
    httpOnly: true,
    secure: process.env.NODE_ENV === 'production',
    sameSite: 'lax',
    store: new RedisSessionStore({
      url: process.env.REDIS_URL!,
    }),
  },
});
```

## `useCookies()`

Read and write cookies. Returns a `CookieJar` object:

```typescript
import { useCookies } from 'velox/server';

const cookies = useCookies();

// Read
const theme = cookies.get('theme')?.value ?? 'light';
const hasConsented = cookies.get('consent')?.value === 'true';

// Write (adds Set-Cookie header to the response)
cookies.set('theme', 'dark', {
  path: '/',
  maxAge: 365 * 24 * 60 * 60,  // 1 year
  sameSite: 'lax',
});

// Delete
cookies.delete('old-cookie', { path: '/' });
```

### Cookie Options

| Option | Type | Description |
|--------|------|-------------|
| `domain` | `string` | Cookie domain |
| `path` | `string` | Cookie path. Default: `/` |
| `maxAge` | `number` | Expiry in seconds |
| `expires` | `Date` | Expiry as a date |
| `httpOnly` | `boolean` | Prevent JavaScript access |
| `secure` | `boolean` | HTTPS only |
| `sameSite` | `'strict' \| 'lax' \| 'none'` | SameSite policy |

## `useEnv(key, defaultValue?)`

Type-safe environment variable access:

```typescript
import { useEnv } from 'velox/server';

const dbUrl = useEnv('DATABASE_URL');           // throws if not set
const port = useEnv('PORT', '3700');            // returns default if not set
const debug = useEnv.boolean('DEBUG', false);  // parse as boolean
const timeout = useEnv.number('TIMEOUT', 30);  // parse as number
```

### `useEnv` Methods

| Method | Description |
|--------|-------------|
| `useEnv(key)` | Return string value, throw if missing |
| `useEnv(key, default)` | Return string value or default |
| `useEnv.boolean(key, default?)` | Parse as boolean (`'true'` / `'1'` = `true`) |
| `useEnv.number(key, default?)` | Parse as float |
| `useEnv.json(key, default?)` | Parse as JSON |
| `useEnv.url(key, default?)` | Validate and return as URL string |

## `useHeaders()`

Access and modify response headers from within a server block or middleware:

```typescript
import { useHeaders } from 'velox/server';

const headers = useHeaders();

// Read request headers
const accept = headers.request.get('Accept');

// Set response headers
headers.response.set('Cache-Control', 'public, max-age=3600');
headers.response.set('X-Custom-Header', 'value');
```

## `useLocale()`

Returns the current request locale (resolved by the i18n middleware):

```typescript
import { useLocale } from 'velox/server';

const { locale, locales, defaultLocale } = useLocale();

// locale: 'fr'  (current request locale)
// locales: ['en', 'fr', 'de']  (all supported locales)
// defaultLocale: 'en'
```

## `useAuth()`

A convenience hook that reads the current user from the session. Returns `null` if not authenticated:

```typescript
import { useAuth } from '$lib/auth';  // project-defined hook

const user = await useAuth();

if (!user) {
  throw redirect('/login');
}

// user: { id: string, email: string, role: string }
```

The `useAuth` hook is not provided by Velox itself — you define it in your project using `useSession` and your own user model. The [Authentication guide](guide-auth.md) shows a complete implementation.

## `useCache()`

Interact with Velox's built-in server-side cache:

```typescript
import { useCache } from 'velox/server';

const cache = useCache();

// Get from cache
const cached = await cache.get<User[]>('users:all');
if (cached) return cached;

// Set with TTL (seconds)
const users = await db.users.findMany();
await cache.set('users:all', users, { ttl: 300 });

// Invalidate
await cache.delete('users:all');
await cache.deletePattern('users:*');
```
