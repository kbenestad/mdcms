---
title: Quick Start
sort: 120
section-id: getting-started
keywords: quick start, first app, hello world, dev server, file structure
description: Build your first Velox application from scratch in minutes
language: en
---

# Quick Start

This guide walks you through creating a working Velox application from zero. By the end you will have a running dev server, a couple of pages with navigation between them, and an API route returning JSON.

## Step 1 — Scaffold the Project

```bash
npm create velox@latest my-first-app -- --template minimal --ts --pm npm
cd my-first-app
```

The scaffolder creates the following structure:

```
my-first-app/
├── routes/
│   ├── index.velox        ← homepage route
│   └── about.velox        ← about page route
├── layouts/
│   └── default.velox      ← wraps all routes by default
├── public/
│   └── favicon.svg
├── velox.config.ts
├── tsconfig.json
└── package.json
```

## Step 2 — Start the Development Server

```bash
npm run dev
```

Velox starts the development server on port 3700 by default:

```
  ⚡ Velox v1.4.0 — development server
  ┌─────────────────────────────────────┐
  │  Local:    http://localhost:3700    │
  │  Network:  http://192.168.1.5:3700  │
  └─────────────────────────────────────┘
  Ready in 312ms
```

Open `http://localhost:3700` in your browser. You should see the default Velox welcome page.

## Step 3 — Understand the Default Page

Open `routes/index.velox`. A `.velox` file is a superset of TSX with some Velox-specific features:

```tsx
---
// Server-side frontmatter block — runs only on the server
export const meta = {
  title: 'Home',
  description: 'My first Velox app',
};
---

<main>
  <h1>Welcome to Velox!</h1>
  <p>Edit <code>routes/index.velox</code> to get started.</p>
  <a href="/about">About</a>
</main>
```

The `---` fenced block at the top is the **server block** — it runs exclusively during server-side rendering or static generation. Exports from the server block (like `meta`) are available as template variables in the HTML section below.

## Step 4 — Add a New Route

Create a new file at `routes/contact.velox`:

```tsx
---
export const meta = {
  title: 'Contact',
  description: 'Get in touch with us',
};
---

<main>
  <h1>Contact Us</h1>
  <p>Send us a message at <a href="mailto:hello@example.com">hello@example.com</a></p>
</main>
```

Save the file. Velox automatically picks up the new route — navigate to `http://localhost:3700/contact` and you will see your new page without restarting the server.

## Step 5 — Create an API Route

API routes live in the `routes/` directory alongside page routes, but are named with a `+` prefix to distinguish them.

Create `routes/api/hello+server.ts`:

```typescript
import { defineHandler } from 'velox/server';

export const GET = defineHandler(async (req) => {
  const name = new URL(req.url).searchParams.get('name') ?? 'World';
  return Response.json({ message: `Hello, ${name}!` });
});
```

Test it at `http://localhost:3700/api/hello?name=Velox`. You should receive:

```json
{ "message": "Hello, Velox!" }
```

## Step 6 — Fetch Data on the Server

Update `routes/index.velox` to fetch data server-side:

```tsx
---
import { fetch } from 'velox/server';

export const meta = {
  title: 'Home',
};

// This runs on the server only
const res = await fetch('https://jsonplaceholder.typicode.com/todos/1');
const todo = await res.json();
---

<main>
  <h1>Welcome to Velox!</h1>
  <p>Todo from API: {todo.title}</p>
</main>
```

## Step 7 — Add Interactivity (Islands)

By default, Velox ships zero client-side JavaScript. To add a client-side interactive component, create a component and opt into hydration:

Create `components/Counter.tsx`:

```tsx
import { signal } from 'velox/client';

export default function Counter() {
  const count = signal(0);
  return (
    <div>
      <p>Count: {count.value}</p>
      <button onClick={() => count.value++}>Increment</button>
    </div>
  );
}
```

Use it in your page with the `client:load` directive:

```tsx
---
import Counter from '../components/Counter.tsx';
---

<main>
  <h1>Home</h1>
  <Counter client:load />
</main>
```

The `client:load` directive tells Velox to hydrate this component immediately when the page loads. Other directives include `client:idle` (hydrate when browser is idle) and `client:visible` (hydrate when the component enters the viewport).

## Step 8 — Build for Production

```bash
npm run build
```

Velocitor compiles a production-ready build into the `.velox/output/` directory. Review the build output:

```
  ⚡ Velox — production build
  Compiled 4 routes in 1.8s
  ┌─────────────────────────────────────────┐
  │  /            →  SSR   (0 KB JS)        │
  │  /about       →  SSG   (0 KB JS)        │
  │  /contact     →  SSG   (0 KB JS)        │
  │  /api/hello   →  Edge handler           │
  └─────────────────────────────────────────┘
  Total JS shipped to client: 2.1 KB (Counter island only)
```

To preview the production build locally:

```bash
npm run preview
```

## Next Steps

- Read about [Project Structure](project-structure.md) to understand every directory and file
- Explore [Routing](routing.md) for dynamic routes and catch-all patterns
- Learn about [Data Fetching](data-fetching.md) for SSR, SSG, and ISR patterns
- Check the [Configuration](configuration.md) reference for `velox.config.ts` options
