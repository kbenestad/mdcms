---
title: Testing
sort: 120
section-id: guides
keywords: testing, unit tests, integration tests, E2E, Playwright, Vitest, testing strategy
description: Testing Velox applications with unit tests, integration tests, and end-to-end tests using Playwright
language: en
---

# Testing

Velox integrates with Vitest for unit and integration tests, and Playwright for end-to-end tests. The `@velox/test` package provides additional test utilities tailored for Velox's server blocks and API routes.

## Setup

```bash
npm install -D vitest @velox/test @playwright/test
npx playwright install
```

Add test scripts to `package.json`:

```json
{
  "scripts": {
    "test": "vitest",
    "test:ui": "vitest --ui",
    "test:e2e": "playwright test",
    "test:coverage": "vitest --coverage"
  }
}
```

Configure Vitest:

```typescript
// vitest.config.ts
import { defineConfig } from 'vitest/config';
import { veloxTestPlugin } from '@velox/test';

export default defineConfig({
  plugins: [veloxTestPlugin()],
  test: {
    environment: 'node',
    globals: true,
    setupFiles: ['./tests/setup.ts'],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'lcov'],
    },
  },
});
```

## Unit Tests

### Testing Utility Functions

```typescript
// lib/formatters.ts
export function formatCurrency(amount: number, currency = 'USD'): string {
  return new Intl.NumberFormat('en-US', { style: 'currency', currency }).format(amount);
}
```

```typescript
// tests/unit/formatters.test.ts
import { describe, it, expect } from 'vitest';
import { formatCurrency } from '$lib/formatters';

describe('formatCurrency', () => {
  it('formats USD amounts', () => {
    expect(formatCurrency(1000)).toBe('$1,000.00');
    expect(formatCurrency(9.99)).toBe('$9.99');
  });

  it('formats other currencies', () => {
    expect(formatCurrency(1000, 'EUR')).toBe('€1,000.00');
  });

  it('handles zero', () => {
    expect(formatCurrency(0)).toBe('$0.00');
  });
});
```

### Testing Components

```tsx
// tests/unit/Counter.test.tsx
import { describe, it, expect } from 'vitest';
import { render, fireEvent } from '@velox/test';
import Counter from '$components/Counter';

describe('Counter', () => {
  it('renders with initial value', () => {
    const { getByText } = render(<Counter initialValue={5} />);
    expect(getByText('5')).toBeTruthy();
  });

  it('increments on button click', async () => {
    const { getByText, getByRole } = render(<Counter initialValue={0} />);
    await fireEvent.click(getByRole('button', { name: /increment/i }));
    expect(getByText('1')).toBeTruthy();
  });

  it('decrements below initial value', async () => {
    const { getByText, getByRole } = render(<Counter initialValue={3} />);
    await fireEvent.click(getByRole('button', { name: /decrement/i }));
    expect(getByText('2')).toBeTruthy();
  });
});
```

## Integration Tests

### Testing API Routes

The `createTestServer` utility starts a real Velox server for integration testing:

```typescript
// tests/integration/api/users.test.ts
import { describe, it, expect, beforeAll, afterAll } from 'vitest';
import { createTestServer } from '@velox/test';
import { db } from '$lib/db';

let server: Awaited<ReturnType<typeof createTestServer>>;

beforeAll(async () => {
  server = await createTestServer({ seed: true });
});

afterAll(async () => {
  await server.stop();
  await db.$disconnect();
});

describe('GET /api/users', () => {
  it('returns all users', async () => {
    const res = await server.inject({
      method: 'GET',
      url: '/api/users',
      headers: { Authorization: `Bearer ${server.getAdminToken()}` },
    });

    expect(res.status).toBe(200);
    const body = await res.json();
    expect(Array.isArray(body)).toBe(true);
    expect(body.length).toBeGreaterThan(0);
  });

  it('returns 401 without auth', async () => {
    const res = await server.inject({ method: 'GET', url: '/api/users' });
    expect(res.status).toBe(401);
  });
});

describe('POST /api/users', () => {
  it('creates a new user', async () => {
    const res = await server.inject({
      method: 'POST',
      url: '/api/users',
      body: { email: 'new@example.com', name: 'New User' },
      headers: { Authorization: `Bearer ${server.getAdminToken()}` },
    });

    expect(res.status).toBe(201);
    const user = await res.json();
    expect(user.email).toBe('new@example.com');
    expect(user.id).toBeDefined();
  });

  it('rejects duplicate email', async () => {
    await server.inject({
      method: 'POST',
      url: '/api/users',
      body: { email: 'dup@example.com', name: 'First' },
      headers: { Authorization: `Bearer ${server.getAdminToken()}` },
    });

    const res = await server.inject({
      method: 'POST',
      url: '/api/users',
      body: { email: 'dup@example.com', name: 'Second' },
      headers: { Authorization: `Bearer ${server.getAdminToken()}` },
    });

    expect(res.status).toBe(409);
  });
});
```

### Testing Database Operations

```typescript
// tests/integration/db/posts.test.ts
import { describe, it, expect, beforeEach } from 'vitest';
import { db } from '$lib/db';
import { createTestUser, createTestPost } from '../factories';

beforeEach(async () => {
  await db.$executeRaw`TRUNCATE posts, users RESTART IDENTITY CASCADE`;
});

describe('Post queries', () => {
  it('finds published posts only', async () => {
    const user = await createTestUser();
    await createTestPost({ authorId: user.id, published: true });
    await createTestPost({ authorId: user.id, published: false });

    const posts = await db.post.findMany({ where: { published: true } });
    expect(posts).toHaveLength(1);
  });
});
```

## End-to-End Tests with Playwright

```typescript
// playwright.config.ts
import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: './tests/e2e',
  use: {
    baseURL: 'http://localhost:3700',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
  },
  webServer: {
    command: 'npm run dev',
    url: 'http://localhost:3700',
    reuseExistingServer: !process.env.CI,
  },
});
```

```typescript
// tests/e2e/auth.spec.ts
import { test, expect } from '@playwright/test';

test.describe('Authentication', () => {
  test('user can log in', async ({ page }) => {
    await page.goto('/login');
    await page.getByLabel('Email').fill('test@example.com');
    await page.getByLabel('Password').fill('correct-password');
    await page.getByRole('button', { name: 'Log in' }).click();

    await page.waitForURL('/dashboard');
    await expect(page.getByText('Welcome back')).toBeVisible();
  });

  test('shows error for invalid credentials', async ({ page }) => {
    await page.goto('/login');
    await page.getByLabel('Email').fill('test@example.com');
    await page.getByLabel('Password').fill('wrong-password');
    await page.getByRole('button', { name: 'Log in' }).click();

    await expect(page.getByRole('alert')).toContainText('Invalid credentials');
    await expect(page).toHaveURL('/login');
  });
});
```

## Test Factories

Use factories to generate test data consistently:

```typescript
// tests/factories.ts
import { db } from '$lib/db';
import { hashPassword } from '$lib/crypto';

export async function createTestUser(overrides = {}) {
  return db.user.create({
    data: {
      email: `user-${Date.now()}@example.com`,
      name: 'Test User',
      passwordHash: await hashPassword('test-password'),
      ...overrides,
    },
  });
}

export async function createTestPost(overrides = {}) {
  return db.post.create({
    data: {
      title: 'Test Post',
      slug: `test-post-${Date.now()}`,
      content: 'Test content',
      published: true,
      ...overrides,
    },
  });
}
```

## CI Configuration

```yaml
# .github/workflows/test.yml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: test
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: '22' }
      - run: npm ci
      - run: npx prisma migrate deploy
        env:
          DATABASE_URL: postgresql://postgres:postgres@localhost/test
      - run: npm test
      - run: npx playwright install --with-deps
      - run: npm run test:e2e
```
