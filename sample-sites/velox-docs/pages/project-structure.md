---
title: Project Structure
sort: 130
section-id: getting-started
keywords: project structure, directory layout, files, folders, architecture
description: A detailed explanation of every file and folder in a Velox project
language: en
---

# Project Structure

![Velox Architecture](assets/images/architecture.jpg)

Understanding the Velox project structure is key to working effectively with the framework. This page explains the purpose of every directory and file you will encounter in a standard Velox project.

## Top-Level Layout

```
my-velox-app/
├── routes/              ← all pages and API routes
├── layouts/             ← shared page layouts
├── components/          ← reusable UI components
├── lib/                 ← shared server-side utilities
├── middleware/          ← request/response interceptors
├── public/              ← static assets (copied verbatim)
├── styles/              ← global CSS and design tokens
├── tests/               ← test files
├── .velox/              ← build cache and output (gitignored)
├── velox.config.ts      ← framework configuration
├── tsconfig.json        ← TypeScript configuration
├── package.json
└── .env                 ← environment variables
```

## `routes/`

This is the most important directory. Every file in `routes/` maps to a URL path unless prefixed with `_` (underscore files are ignored by the router).

### Page Routes

Files ending in `.velox` or `.tsx` become page routes:

```
routes/
├── index.velox          →  /
├── about.velox          →  /about
├── blog/
│   ├── index.velox      →  /blog
│   └── [slug].velox     →  /blog/:slug
├── docs/
│   └── [...path].velox  →  /docs/* (catch-all)
└── _components/         ← underscore prefix: ignored by router
    └── Header.tsx
```

### API Routes

Files suffixed with `+server.ts` become API routes. They export HTTP method handlers:

```
routes/
└── api/
    ├── users+server.ts          →  /api/users
    └── users/[id]+server.ts     →  /api/users/:id
```

### Special Files

| File | Purpose |
|---|---|
| `_error.velox` | Custom error page (404, 500) in any directory |
| `_loading.velox` | Loading state shown during route transitions |
| `_layout.velox` | Layout that wraps all sibling routes |

## `layouts/`

Layout files define the shell that wraps your page content. A layout receives a `<slot />` where the page content is injected.

```tsx
// layouts/default.velox
---
import Header from '../components/Header.tsx';
import Footer from '../components/Footer.tsx';
---

<html lang="en">
  <head>
    <meta charset="utf-8" />
    <title>{meta.title}</title>
  </head>
  <body>
    <Header />
    <slot />
    <Footer />
  </body>
</html>
```

The default layout (`layouts/default.velox`) wraps all routes unless a route specifies a different layout via the `layout` frontmatter property.

## `components/`

Reusable UI components that can be used in routes and layouts. Components do not have server blocks — they are purely presentational (though they can accept server-fetched data as props).

```
components/
├── Header.tsx
├── Footer.tsx
├── Button.tsx
├── ui/
│   ├── Card.tsx
│   └── Modal.tsx
└── forms/
    ├── Input.tsx
    └── Select.tsx
```

## `lib/`

Server-side utility modules — database clients, external API helpers, auth utilities. Code in `lib/` is never bundled for the client unless explicitly imported from a client-side component.

```
lib/
├── db.ts           ← database connection
├── auth.ts         ← authentication helpers
├── email.ts        ← email sending
└── cache.ts        ← caching utilities
```

## `middleware/`

Middleware functions execute on every matching request before the route handler runs. Middleware files are auto-loaded based on path:

```
middleware/
├── auth.ts          ← applies to all routes (no path suffix)
└── admin.ts         ← must be explicitly referenced in velox.config.ts
```

## `public/`

Static files in `public/` are served at the root path without transformation. A file at `public/robots.txt` is served at `/robots.txt`. Use this for favicons, `manifest.json`, `sitemap.xml`, and static images that do not need optimisation.

## `styles/`

Global stylesheets. Velox supports CSS Modules (`.module.css`), plain CSS, and Sass (`.scss`) if the `@velox/sass` plugin is installed. The file `styles/global.css` is automatically injected into every page.

```
styles/
├── global.css       ← injected automatically
├── tokens.css       ← CSS custom properties / design tokens
└── reset.css        ← CSS reset or normalise
```

## `.velox/`

Generated directory — **never commit this to git**. Contains:

- `.velox/cache/` — Velocitor's incremental build cache (keyed by content hash)
- `.velox/output/` — production build output
- `.velox/tmp/` — temporary files used during development

Add `.velox/` to your `.gitignore`:

```
# .gitignore
.velox/
.env.local
node_modules/
```

## `velox.config.ts`

The central configuration file for the framework. See the full [Configuration](pages/configuration.md) reference for every available option. A minimal example:

```typescript
import { defineConfig } from 'velox';

export default defineConfig({
  app: {
    name: 'my-velox-app',
    baseUrl: process.env.PUBLIC_BASE_URL ?? 'http://localhost:3700',
  },
  build: {
    target: 'node',
  },
});
```

## `tsconfig.json`

Velox requires certain TypeScript compiler options to function correctly. The scaffolder generates an appropriate `tsconfig.json` automatically. Key options:

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "ESNext",
    "moduleResolution": "bundler",
    "jsx": "preserve",
    "jsxImportSource": "velox",
    "strict": true,
    "paths": {
      "$lib/*": ["./lib/*"],
      "$components/*": ["./components/*"]
    }
  }
}
```

The `$lib` and `$components` path aliases are available throughout your project without needing to calculate relative paths.

## Generated Files

Velox generates a small number of type definition files in `.velox/types/` that provide type-safe access to environment variables, route params, and other framework internals. These are referenced automatically by the `tsconfig.json` generated by the scaffolder.

Understanding this structure will help you navigate any Velox project confidently. Next, explore the [Configuration](pages/configuration.md) reference to learn all available options.
