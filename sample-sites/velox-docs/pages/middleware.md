---
title: Middleware
sort: 140
section-id: core-concepts
keywords: middleware, request pipeline, auth middleware, rate limiting, CORS, headers
description: How to use and write Velox middleware for request/response transformation
language: en
---

# Middleware

Middleware in Velox is a function that intercepts HTTP requests before they reach a route handler and can transform both the request and the response. Middleware is composable, typed, and supports async operations.

## How Middleware Works

The Velox request pipeline processes a request in the following order:

1. **Global middleware** — applied to every request
2. **Path-scoped middleware** — applied based on route matching
3. **Route handler** — the actual page or API route
4. **Response middleware** — runs on the way out (in reverse order)

```
Request
  ↓
[Global Middleware 1]
  ↓
[Global Middleware 2]
  ↓
[Path Middleware]
  ↓
[Route Handler]
  ↓
[Response (in reverse)]
```

## Writing Middleware

Create a middleware file in the `middleware/` directory. A middleware function receives the `request` and a `next` function. Call `next()` to pass control to the next middleware or the route handler:

```typescript
// middleware/logger.ts
import { defineMiddleware } from 'velox/server';

export default defineMiddleware(async ({ request, next }) => {
  const start = Date.now();
  const response = await next();
  const duration = Date.now() - start;
  console.log(`${request.method} ${request.url} — ${response.status} (${duration}ms)`);
  return response;
});
```

## Configuring Middleware

Register middleware in `velox.config.ts`:

```typescript
import { defineConfig } from 'velox';

export default defineConfig({
  middleware: [
    { path: '*', handler: './middleware/logger' },
    { path: '/admin/*', handler: './middleware/auth' },
    { path: '/api/*', handler: './middleware/rateLimit' },
  ],
});
```

Or, use a `middleware.ts` file at the project root for global middleware:

```typescript
// middleware.ts (project root — applies to all routes automatically)
import { defineMiddleware } from 'velox/server';

export default defineMiddleware(async ({ request, next }) => {
  // runs on every request
  return next();
});
```

## Authentication Middleware

```typescript
// middleware/auth.ts
import { defineMiddleware, redirect } from 'velox/server';
import { verifyJWT } from '$lib/auth';

export default defineMiddleware(async ({ request, next }) => {
  const token = request.cookies.get('session')?.value
    ?? request.headers.get('Authorization')?.replace('Bearer ', '');

  if (!token) {
    return redirect('/login?next=' + encodeURIComponent(request.url));
  }

  let user;
  try {
    user = await verifyJWT(token);
  } catch {
    return redirect('/login?error=invalid_token');
  }

  // Attach user to request context for downstream handlers
  request.context.set('user', user);

  return next();
});
```

Access the context in your route:

```typescript
// routes/dashboard.velox server block
const user = request.context.get('user');
```

## Rate Limiting Middleware

```typescript
// middleware/rateLimit.ts
import { defineMiddleware } from 'velox/server';

const counters = new Map<string, { count: number; resetAt: number }>();
const WINDOW_MS = 60_000; // 1 minute
const MAX_REQUESTS = 100;

export default defineMiddleware(async ({ request, next }) => {
  const ip = request.headers.get('CF-Connecting-IP')
    ?? request.headers.get('X-Forwarded-For')
    ?? 'unknown';

  const now = Date.now();
  const counter = counters.get(ip) ?? { count: 0, resetAt: now + WINDOW_MS };

  if (now > counter.resetAt) {
    counter.count = 0;
    counter.resetAt = now + WINDOW_MS;
  }

  counter.count++;
  counters.set(ip, counter);

  if (counter.count > MAX_REQUESTS) {
    return new Response('Too Many Requests', {
      status: 429,
      headers: {
        'Retry-After': String(Math.ceil((counter.resetAt - now) / 1000)),
        'X-RateLimit-Limit': String(MAX_REQUESTS),
        'X-RateLimit-Remaining': '0',
      },
    });
  }

  const response = await next();
  response.headers.set('X-RateLimit-Limit', String(MAX_REQUESTS));
  response.headers.set('X-RateLimit-Remaining', String(MAX_REQUESTS - counter.count));
  return response;
});
```

## CORS Middleware

```typescript
// middleware/cors.ts
import { defineMiddleware } from 'velox/server';

const ALLOWED_ORIGINS = process.env.ALLOWED_ORIGINS?.split(',') ?? ['*'];

export default defineMiddleware(async ({ request, next }) => {
  const origin = request.headers.get('Origin') ?? '';
  const isAllowed = ALLOWED_ORIGINS.includes('*') || ALLOWED_ORIGINS.includes(origin);

  if (request.method === 'OPTIONS') {
    // Preflight response
    return new Response(null, {
      status: 204,
      headers: corsHeaders(origin, isAllowed),
    });
  }

  const response = await next();

  if (isAllowed) {
    for (const [key, value] of Object.entries(corsHeaders(origin, true))) {
      response.headers.set(key, value);
    }
  }

  return response;
});

function corsHeaders(origin: string, allowed: boolean) {
  if (!allowed) return {};
  return {
    'Access-Control-Allow-Origin': origin,
    'Access-Control-Allow-Methods': 'GET, POST, PUT, PATCH, DELETE, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type, Authorization',
    'Access-Control-Allow-Credentials': 'true',
    'Access-Control-Max-Age': '86400',
  };
}
```

## Security Headers Middleware

```typescript
// middleware/securityHeaders.ts
import { defineMiddleware } from 'velox/server';

export default defineMiddleware(async ({ next }) => {
  const response = await next();

  response.headers.set('X-Content-Type-Options', 'nosniff');
  response.headers.set('X-Frame-Options', 'DENY');
  response.headers.set('X-XSS-Protection', '1; mode=block');
  response.headers.set('Referrer-Policy', 'strict-origin-when-cross-origin');
  response.headers.set(
    'Permissions-Policy',
    'camera=(), microphone=(), geolocation=()'
  );
  response.headers.set(
    'Content-Security-Policy',
    "default-src 'self'; script-src 'self' 'nonce-{nonce}'; style-src 'self' 'unsafe-inline'"
  );

  return response;
});
```

## Composing Middleware

Combine multiple middleware into a single handler:

```typescript
import { composeMiddleware } from 'velox/server';
import logger from './logger';
import auth from './auth';
import rateLimit from './rateLimit';

export default composeMiddleware(logger, rateLimit, auth);
```

## Middleware Execution Order

In `velox.config.ts`, middleware is applied in the order it is declared for the request path, and in reverse order for the response path. This mirrors the middleware stack pattern found in Express, Koa, and similar frameworks.

| Middleware | On request | On response |
|------------|-----------|------------|
| logger | 1st | 4th (last) |
| rateLimit | 2nd | 3rd |
| auth | 3rd | 2nd |
| route | 4th | 1st |
