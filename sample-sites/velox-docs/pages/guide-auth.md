---
title: Authentication
sort: 100
section-id: guides
keywords: authentication, JWT, OAuth2, session, login, auth, security
description: Implementing authentication in Velox using JWT, OAuth2, and session-based strategies
language: en
---

# Authentication

This guide covers the three most common authentication patterns for Velox applications: session-based auth, JWT-based auth, and OAuth2 with third-party providers.

## Session-Based Authentication

Session auth stores user state server-side. The client holds only a signed session cookie. This is the simplest and most secure approach for most web applications.

### Setup

Install the session plugin:

```bash
npm install @velox/session @velox/session-redis
```

Configure in `velox.config.ts`:

```typescript
import { RedisSessionStore } from '@velox/session-redis';

export default defineConfig({
  session: {
    secret: process.env.SESSION_SECRET!,
    cookieName: 'app.session',
    maxAge: 60 * 60 * 24 * 7,  // 7 days
    httpOnly: true,
    secure: process.env.NODE_ENV === 'production',
    sameSite: 'lax',
    store: new RedisSessionStore({ url: process.env.REDIS_URL! }),
  },
});
```

### Login Handler

```typescript
// routes/api/auth/login+server.ts
import { defineHandler, json, redirect } from 'velox/server';
import { useSession } from 'velox/server';
import { db } from '$lib/db';
import { verifyPassword } from '$lib/crypto';

export const POST = defineHandler(async (req) => {
  const { email, password } = await req.json();

  if (!email || !password) {
    return json({ error: 'Email and password are required' }, { status: 400 });
  }

  const user = await db.users.findByEmail(email);
  if (!user || !(await verifyPassword(password, user.passwordHash))) {
    return json({ error: 'Invalid credentials' }, { status: 401 });
  }

  const session = await useSession();
  await session.regenerate();  // prevent session fixation
  await session.update({ userId: user.id, role: user.role });

  return json({ ok: true, redirectTo: '/dashboard' });
});
```

### Auth Middleware

```typescript
// middleware/auth.ts
import { defineMiddleware, redirect } from 'velox/server';
import { useSession } from 'velox/server';

const PUBLIC_PATHS = ['/login', '/register', '/api/auth'];

export default defineMiddleware(async ({ request, next }) => {
  const pathname = new URL(request.url).pathname;

  if (PUBLIC_PATHS.some(p => pathname.startsWith(p))) {
    return next();
  }

  const session = await useSession<{ userId: string }>();

  if (!session.data.userId) {
    return redirect(`/login?next=${encodeURIComponent(pathname)}`);
  }

  request.context.set('userId', session.data.userId);
  return next();
});
```

## JWT Authentication

JWT is stateless and ideal for API-first applications or mobile/SPA backends.

### Generating Tokens

```typescript
// lib/jwt.ts
import { SignJWT, jwtVerify } from 'jose';

const secret = new TextEncoder().encode(process.env.JWT_SECRET!);

export interface JWTPayload {
  sub: string;   // user ID
  role: string;
  iat: number;
  exp: number;
}

export async function signToken(userId: string, role: string): Promise<string> {
  return new SignJWT({ sub: userId, role })
    .setProtectedHeader({ alg: 'HS256' })
    .setIssuedAt()
    .setExpirationTime('15m')
    .sign(secret);
}

export async function signRefreshToken(userId: string): Promise<string> {
  return new SignJWT({ sub: userId, type: 'refresh' })
    .setProtectedHeader({ alg: 'HS256' })
    .setIssuedAt()
    .setExpirationTime('30d')
    .sign(secret);
}

export async function verifyToken(token: string): Promise<JWTPayload> {
  const { payload } = await jwtVerify(token, secret);
  return payload as JWTPayload;
}
```

### Login + Refresh Endpoints

```typescript
// routes/api/auth/token+server.ts
import { defineHandler, json, badRequest, unauthorized } from 'velox/server';
import { signToken, signRefreshToken, verifyToken } from '$lib/jwt';
import { db } from '$lib/db';
import { verifyPassword } from '$lib/crypto';

export const POST = defineHandler(async (req) => {
  const { grant_type, email, password, refresh_token } = await req.json();

  if (grant_type === 'password') {
    const user = await db.users.findByEmail(email);
    if (!user || !(await verifyPassword(password, user.passwordHash))) {
      return unauthorized('Invalid credentials');
    }
    return json({
      access_token: await signToken(user.id, user.role),
      refresh_token: await signRefreshToken(user.id),
      token_type: 'Bearer',
      expires_in: 900,
    });
  }

  if (grant_type === 'refresh_token') {
    const payload = await verifyToken(refresh_token).catch(() => null);
    if (!payload || payload.type !== 'refresh') {
      return unauthorized('Invalid refresh token');
    }
    const user = await db.users.findById(payload.sub);
    return json({
      access_token: await signToken(user.id, user.role),
      token_type: 'Bearer',
      expires_in: 900,
    });
  }

  return badRequest('Unsupported grant_type');
});
```

## OAuth2 with Third-Party Providers

### Using `@velox/auth`

```bash
npm install @velox/auth
```

Configure providers:

```typescript
// lib/auth.ts
import { createAuth } from '@velox/auth';

export const auth = createAuth({
  providers: [
    {
      id: 'github',
      clientId: process.env.GITHUB_CLIENT_ID!,
      clientSecret: process.env.GITHUB_CLIENT_SECRET!,
      authorizationUrl: 'https://github.com/login/oauth/authorize',
      tokenUrl: 'https://github.com/login/oauth/access_token',
      userInfoUrl: 'https://api.github.com/user',
      scopes: ['user:email'],
    },
    {
      id: 'google',
      clientId: process.env.GOOGLE_CLIENT_ID!,
      clientSecret: process.env.GOOGLE_CLIENT_SECRET!,
      // Google uses OpenID Connect — most fields are auto-discovered
    },
  ],
  callbacks: {
    async onUserInfo(provider, userInfo) {
      const user = await db.users.upsert({
        where: { email: userInfo.email },
        create: { email: userInfo.email, name: userInfo.name, provider },
        update: { name: userInfo.name },
      });
      return { id: user.id, role: user.role };
    },
  },
});
```

OAuth callback route:

```typescript
// routes/auth/[provider]/callback+server.ts
import { defineHandler } from 'velox/server';
import { auth } from '$lib/auth';

export const GET = defineHandler(async (req) => {
  return auth.handleCallback(req);
});
```

## Password Hashing

Always use a slow hashing algorithm. Velox recommends Argon2:

```typescript
// lib/crypto.ts
import { hash, verify } from '@node-rs/argon2';

export async function hashPassword(password: string): Promise<string> {
  return hash(password, {
    memoryCost: 19456,
    timeCost: 2,
    outputLen: 32,
    parallelism: 1,
  });
}

export async function verifyPassword(password: string, hash: string): Promise<boolean> {
  return verify(hash, password);
}
```

## Role-Based Access Control

```typescript
// middleware/rbac.ts
import { defineMiddleware, forbidden } from 'velox/server';

const ROUTE_ROLES: Record<string, string[]> = {
  '/admin': ['admin'],
  '/api/admin': ['admin'],
  '/api/reports': ['admin', 'analyst'],
};

export default defineMiddleware(async ({ request, next }) => {
  const pathname = new URL(request.url).pathname;
  const requiredRoles = Object.entries(ROUTE_ROLES)
    .find(([path]) => pathname.startsWith(path))?.[1];

  if (!requiredRoles) return next();

  const user = request.context.get('user') as { role: string } | undefined;
  if (!user || !requiredRoles.includes(user.role)) {
    return forbidden('Insufficient permissions');
  }

  return next();
});
```
