---
title: Introduction
sort: 100
section-id: getting-started
keywords: velox, framework, typescript, javascript, full-stack, introduction
description: An introduction to Velox, the high-performance TypeScript web framework
language: en
---

# Introduction to Velox

![Velox Framework Hero](assets/images/hero.jpg)

Velox is a high-performance, full-stack TypeScript and JavaScript web framework built for developers who refuse to compromise between developer experience and production performance. Combining a file-based routing model inspired by the best parts of Next.js, an island-based rendering architecture inspired by Astro, and a Rust-powered build toolchain that makes cold starts and hot reloads feel instantaneous, Velox occupies a unique position in the modern web ecosystem.

## Why Velox?

The JavaScript ecosystem is rich, yet fragmented. Some frameworks offer outstanding developer experience but struggle with raw performance at scale. Others are extremely fast but require significant configuration overhead before you can write your first component. Velox was created to close that gap.

The core philosophy of Velox can be summarised in three words: **fast by default**. Every architectural decision — from the Rust-based bundler (Velocitor) to the zero-runtime component model — is made to ensure that your production application runs as efficiently as possible without requiring manual intervention from the developer.

## Key Features

### Rust-Powered Toolchain (Velocitor)

The Velox build system, internally called Velocitor, is written in Rust. It handles TypeScript transpilation, module bundling, tree-shaking, code splitting, and asset optimisation in a single pass. On modern hardware, a full production build of a medium-sized application typically completes in under three seconds. Incremental rebuilds during development are sub-50ms for most file changes.

### File-Based Routing

Velox uses a file-based routing system. Any `.velox` or `.tsx` file placed under the `routes/` directory automatically becomes a route. Dynamic segments use `[param]` notation, optional segments use `[[param]]`, and catch-all routes use `[...rest]`. No manual route registration is ever required.

### Islands Architecture

By default, Velox renders pages entirely on the server. Interactive components are "islands" — explicitly opt-in to client-side hydration using the `client:*` directive. This means your pages ship zero JavaScript by default; you add interactivity exactly where it is needed.

### Hybrid Rendering Modes

Velox supports four rendering strategies per route:
- **SSR (Server-Side Rendering)** — rendered fresh on every request
- **SSG (Static Site Generation)** — pre-rendered at build time
- **ISR (Incremental Static Regeneration)** — statically generated but revalidated on a schedule
- **CSR (Client-Side Rendering)** — fully client-rendered for dashboard-style pages

You can mix rendering modes across routes within a single project.

### TypeScript First

Velox is written in TypeScript and treats TypeScript as a first-class citizen. Configuration files, route handlers, middleware, and components all benefit from full type inference. There is no separate type-generation step required.

### Edge-Ready

Velox applications are deployable to Cloudflare Workers, Vercel Edge, and similar runtimes out of the box. The framework's core HTTP runtime has no Node.js-specific dependencies and operates on standard Web APIs (`Request`, `Response`, `fetch`, `crypto`), making edge deployment trivially simple.

### Built-In Middleware System

The middleware system allows you to intercept and transform requests and responses at multiple points in the pipeline. Auth, rate limiting, logging, CORS, and header manipulation are all achievable through composable middleware functions.

## How Velox Compares

| Feature | Velox | Next.js | Astro | Remix |
|---|---|---|---|---|
| Build system | Rust (Velocitor) | Webpack/Turbopack | Vite | Vite |
| Default JS shipped | Zero | Varies | Zero | Varies |
| Rendering modes | SSR/SSG/ISR/CSR | SSR/SSG/ISR | SSG/SSR | SSR |
| Full-stack API routes | Yes | Yes | Yes | Yes |
| File-based routing | Yes | Yes | Yes | No |
| TypeScript support | First-class | First-class | First-class | First-class |
| Edge runtime | Native | Adapter | Adapter | Adapter |

## Who Is Velox For?

Velox is well suited for:

- Teams building content-heavy marketing sites that need fast initial load times with selective interactivity
- Full-stack application teams who want a unified framework for frontend and backend
- Engineers at high-scale companies who need ISR and edge caching to serve global audiences
- Developers migrating from Next.js who want faster build times without giving up the Next.js mental model

Velox is perhaps not the best choice if you are building a highly stateful single-page application that is mostly client-rendered — in that case a pure SPA framework may be simpler.

## Getting Started

The quickest way to get started with Velox is to install the CLI and scaffold a new project:

```bash
npm create velox@latest my-app
cd my-app
npm run dev
```

Your new project will be running at `http://localhost:3700` in under ten seconds.

Read on to the [Installation](pages/installation.md) guide for full setup instructions, or jump directly to the [Quick Start](pages/quick-start.md) if you prefer to learn by doing.
