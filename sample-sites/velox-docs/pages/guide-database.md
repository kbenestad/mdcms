---
title: Database Integration
sort: 110
section-id: guides
keywords: database, Prisma, DrizzleORM, SQL, ORM, PostgreSQL, database integration
description: How to integrate databases in Velox using Prisma, DrizzleORM, or raw SQL
language: en
---

# Database Integration

Velox is database-agnostic. This guide covers the three most popular approaches: Prisma (full-featured ORM), DrizzleORM (lightweight TypeScript-first ORM), and raw SQL with a typed query builder.

## Prisma

Prisma is the most popular ORM in the Node.js ecosystem. It provides a schema-first approach, auto-generated type-safe client, and powerful migrations.

### Setup

```bash
npm install prisma @prisma/client
npx prisma init
```

This creates a `prisma/schema.prisma` file. Example schema:

```prisma
// prisma/schema.prisma
generator client {
  provider = "prisma-client-js"
}

datasource db {
  provider = "postgresql"
  url      = env("DATABASE_URL")
}

model User {
  id        String   @id @default(cuid())
  email     String   @unique
  name      String?
  role      Role     @default(USER)
  posts     Post[]
  createdAt DateTime @default(now())
  updatedAt DateTime @updatedAt
}

model Post {
  id          String   @id @default(cuid())
  title       String
  slug        String   @unique
  content     String
  published   Boolean  @default(false)
  author      User     @relation(fields: [authorId], references: [id])
  authorId    String
  createdAt   DateTime @default(now())
  updatedAt   DateTime @updatedAt
}

enum Role {
  USER
  ADMIN
  ANALYST
}
```

Generate and run the initial migration:

```bash
npx prisma migrate dev --name init
npx prisma generate
```

### Database Client Singleton

In a server environment, always reuse a single Prisma client instance:

```typescript
// lib/db.ts
import { PrismaClient } from '@prisma/client';

const globalForPrisma = globalThis as unknown as { prisma: PrismaClient };

export const db = globalForPrisma.prisma ?? new PrismaClient({
  log: process.env.NODE_ENV === 'development' ? ['query', 'warn', 'error'] : ['error'],
});

if (process.env.NODE_ENV !== 'production') globalForPrisma.prisma = db;
```

### Usage in Routes

```typescript
// routes/blog/[slug].velox server block
import { db } from '$lib/db';

const post = await db.post.findUnique({
  where: { slug: params.slug, published: true },
  include: { author: { select: { name: true } } },
});

if (!post) throw notFound();
```

### Transactions

```typescript
const result = await db.$transaction(async (tx) => {
  const user = await tx.user.create({ data: { email, name } });
  const profile = await tx.profile.create({ data: { userId: user.id } });
  return { user, profile };
});
```

## DrizzleORM

DrizzleORM is a TypeScript-first ORM with a SQL-like query API and zero overhead.

### Setup

```bash
npm install drizzle-orm postgres
npm install -D drizzle-kit
```

Define your schema in TypeScript:

```typescript
// lib/schema.ts
import { pgTable, text, boolean, timestamp, pgEnum } from 'drizzle-orm/pg-core';

export const roleEnum = pgEnum('role', ['user', 'admin', 'analyst']);

export const users = pgTable('users', {
  id: text('id').primaryKey().$defaultFn(() => crypto.randomUUID()),
  email: text('email').notNull().unique(),
  name: text('name'),
  role: roleEnum('role').default('user').notNull(),
  createdAt: timestamp('created_at').defaultNow().notNull(),
  updatedAt: timestamp('updated_at').defaultNow().notNull(),
});

export const posts = pgTable('posts', {
  id: text('id').primaryKey().$defaultFn(() => crypto.randomUUID()),
  title: text('title').notNull(),
  slug: text('slug').notNull().unique(),
  content: text('content').notNull(),
  published: boolean('published').default(false).notNull(),
  authorId: text('author_id').notNull().references(() => users.id),
  createdAt: timestamp('created_at').defaultNow().notNull(),
});
```

### Database Client

```typescript
// lib/db.ts
import { drizzle } from 'drizzle-orm/postgres-js';
import postgres from 'postgres';
import * as schema from './schema';

const client = postgres(process.env.DATABASE_URL!);
export const db = drizzle(client, { schema });
```

### Querying

```typescript
import { db } from '$lib/db';
import { posts, users } from '$lib/schema';
import { eq, and, desc } from 'drizzle-orm';

// Find one
const post = await db.query.posts.findFirst({
  where: and(eq(posts.slug, slug), eq(posts.published, true)),
  with: { author: { columns: { name: true } } },
});

// Find many with ordering
const recentPosts = await db
  .select()
  .from(posts)
  .where(eq(posts.published, true))
  .orderBy(desc(posts.createdAt))
  .limit(10);

// Insert
const [newPost] = await db
  .insert(posts)
  .values({ title, slug, content, authorId })
  .returning();

// Update
await db
  .update(posts)
  .set({ published: true, updatedAt: new Date() })
  .where(eq(posts.id, postId));

// Delete
await db.delete(posts).where(eq(posts.id, postId));
```

### Migrations

Configure Drizzle Kit:

```typescript
// drizzle.config.ts
import { defineConfig } from 'drizzle-kit';

export default defineConfig({
  schema: './lib/schema.ts',
  out: './drizzle',
  dialect: 'postgresql',
  dbCredentials: { url: process.env.DATABASE_URL! },
});
```

```bash
npx drizzle-kit generate
npx drizzle-kit migrate
```

## Raw SQL with `postgres.js`

For maximum control and performance with complex queries:

```typescript
// lib/db.ts
import postgres from 'postgres';

export const sql = postgres(process.env.DATABASE_URL!, {
  max: 20,                    // connection pool size
  idle_timeout: 20,           // seconds before idle connection closes
  connect_timeout: 10,        // connection timeout
  types: {
    bigint: postgres.BigInt,  // return BigInt instead of string
  },
});
```

Usage:

```typescript
import { sql } from '$lib/db';

// Parameterised query (safe from SQL injection)
const users = await sql<User[]>`
  SELECT id, email, name, role
  FROM users
  WHERE role = ${role}
  ORDER BY created_at DESC
  LIMIT ${limit}
`;

// Transaction
const result = await sql.begin(async (sql) => {
  const [user] = await sql`
    INSERT INTO users (email, name)
    VALUES (${email}, ${name})
    RETURNING *
  `;
  await sql`
    INSERT INTO audit_log (user_id, action)
    VALUES (${user.id}, 'register')
  `;
  return user;
});
```

## Connection Pooling in Production

For serverless or edge deployments, use a connection pooler:

- **PgBouncer** — a lightweight PostgreSQL connection pooler for VPS deployments
- **Supabase Supavisor** — serverless-aware pooler built for transactional workloads
- **Neon / PlanetScale** — managed databases with built-in HTTP-based connection pooling

```typescript
// For serverless (e.g. Vercel, Cloudflare) — use HTTP-based driver
import { neon } from '@neondatabase/serverless';

const sql = neon(process.env.DATABASE_URL!);
const users = await sql`SELECT * FROM users LIMIT 10`;
```
