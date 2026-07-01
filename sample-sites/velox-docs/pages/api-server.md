---
title: Server API
sort: 120
section-id: api-reference
keywords: server API, createServer, defineHandler, Response helpers, server-side
description: Reference for Velox server-side APIs — createServer, defineHandler, and Response helpers
language: en
---

# Server API

The Velox server API provides utilities for API route handlers, middleware, and server-side logic. All exports documented here come from `velox/server`.

## `defineHandler(fn)`

Wraps an API route handler with type inference and error handling:

```typescript
import { defineHandler } from 'velox/server';

export const GET = defineHandler(async (request) => {
  return Response.json({ status: 'ok' });
});
```

The handler receives a `VeloxRequest` object (an extension of the standard `Request`) and must return a `Response` or `Promise<Response>`.

### `VeloxRequest`

The enhanced request object passed to handlers:

| Property | Type | Description |
|----------|------|-------------|
| `url` | `string` | Full request URL |
| `method` | `string` | HTTP method (uppercase) |
| `headers` | `Headers` | Request headers |
| `params` | `Record<string, string>` | URL route parameters |
| `query` | `URLSearchParams` | Parsed query string |
| `cookies` | `RequestCookies` | Parsed cookies |
| `context` | `Map<string, unknown>` | Values set by middleware |
| `json()` | `Promise<unknown>` | Parse body as JSON |
| `text()` | `Promise<string>` | Parse body as text |
| `formData()` | `Promise<FormData>` | Parse body as form data |
| `arrayBuffer()` | `Promise<ArrayBuffer>` | Parse body as binary |

## Response Helpers

Velox exports a set of `Response` factory helpers for common responses:

### `json(data, init?)`

Return a JSON response with appropriate `Content-Type` header:

```typescript
import { json } from 'velox/server';

return json({ users }, { status: 200 });
return json({ error: 'Not found' }, { status: 404 });
```

### `text(body, init?)`

Return a plain text response:

```typescript
import { text } from 'velox/server';

return text('Hello, World!');
return text('Not Found', { status: 404 });
```

### `html(body, init?)`

Return an HTML response:

```typescript
import { html } from 'velox/server';

return html('<h1>Hello</h1>');
```

### `redirect(url, status?, headers?)`

Return a redirect response:

```typescript
import { redirect } from 'velox/server';

return redirect('/login', 302);
return redirect('/new-location', 301);
```

### `notFound(message?)`

Return a 404 response:

```typescript
import { notFound } from 'velox/server';

return notFound('User not found');
// Returns: Response with status 404 and JSON body
```

### `unauthorized(message?)`

Return a 401 response:

```typescript
import { unauthorized } from 'velox/server';

return unauthorized('Please log in');
```

### `forbidden(message?)`

Return a 403 response:

```typescript
import { forbidden } from 'velox/server';

return forbidden('You do not have access to this resource');
```

### `badRequest(message?, details?)`

Return a 400 response with optional validation details:

```typescript
import { badRequest } from 'velox/server';

return badRequest('Validation failed', { field: 'email', message: 'Invalid format' });
```

### `stream(generator, init?)`

Stream a response body using an async generator:

```typescript
import { stream } from 'velox/server';

export const GET = defineHandler(async () => {
  return stream(async function* () {
    for await (const chunk of getLargeDataset()) {
      yield JSON.stringify(chunk) + '\n';
    }
  });
});
```

## `createServer(options)`

Bootstrap a standalone Velox server programmatically (useful for testing):

```typescript
import { createServer } from 'velox/server';

const server = await createServer({
  root: '/path/to/project',
  port: 3700,
  mode: 'development',
});

await server.start();
console.log(`Server running on port ${server.port}`);

// Later:
await server.stop();
```

### `VeloxServer` Methods

| Method | Description |
|--------|-------------|
| `start()` | Start the HTTP server |
| `stop()` | Gracefully shut down the server |
| `getUrl()` | Returns the server base URL as a string |
| `inject(request)` | Inject a synthetic request for testing without a network |

## Cookies

### Reading Cookies

```typescript
const session = request.cookies.get('session');
const userId = request.cookies.get('userId')?.value;
```

### Setting Cookies

Use the `ResponseCookies` API on the response object, or the `setCookie` helper:

```typescript
import { setCookie, deleteCookie } from 'velox/server';

const response = json({ ok: true });
setCookie(response, 'session', token, {
  httpOnly: true,
  secure: true,
  sameSite: 'lax',
  path: '/',
  maxAge: 60 * 60 * 24 * 7, // 7 days
});

return response;
```

### Deleting Cookies

```typescript
const response = redirect('/login');
deleteCookie(response, 'session');
return response;
```

## `useEnv(key, defaultValue?)`

Type-safe environment variable access with optional validation:

```typescript
import { useEnv } from 'velox/server';

const dbUrl = useEnv('DATABASE_URL');           // throws if missing
const port = useEnv('PORT', '3700');            // returns defaultValue if missing
const apiKey = useEnv.required('SECRET_KEY');   // alias for useEnv(key)
```

## Error Handling

Velox catches thrown errors in route handlers and middleware. Define a custom error handler in `velox.config.ts`:

```typescript
import { defineConfig } from 'velox';

export default defineConfig({
  errorHandler: async (error, request) => {
    if (error.status === 404) {
      return json({ error: 'Not Found' }, { status: 404 });
    }
    console.error(error);
    return json({ error: 'Internal Server Error' }, { status: 500 });
  },
});
```
