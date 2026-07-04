---
title: Configuration
sort: 140
section-id: getting-started
keywords: configuration, velox.config.ts, settings, options, defineConfig
description: Complete reference for velox.config.ts and all available configuration options
language: en
---

# Configuration

Velox is configured through a single `velox.config.ts` file at the root of your project. This file is evaluated at build time (and at dev-server startup) to determine how Velox should compile and serve your application.

## Creating the Config File

If you used `create-velox` to scaffold your project, a `velox.config.ts` is generated for you. To create one manually:

```typescript
import { defineConfig } from 'velox';

export default defineConfig({
  // options go here
});
```

`defineConfig` is a helper that provides full TypeScript type inference over the configuration object — use it rather than exporting a plain object.

## Top-Level Options

### `app`

General application metadata.

```typescript
app: {
  name: string;               // used in HTML <title> and meta tags
  baseUrl: string;            // canonical base URL (e.g. https://example.com)
  defaultLocale?: string;     // default locale for i18n (default: 'en')
  trailingSlash?: boolean;    // append trailing slash to all routes (default: false)
}
```

Example:

```typescript
app: {
  name: 'My Velox App',
  baseUrl: process.env.PUBLIC_BASE_URL ?? 'http://localhost:3700',
  defaultLocale: 'en',
  trailingSlash: false,
},
```

### `server`

Development and production server settings.

```typescript
server: {
  port?: number;              // dev server port (default: 3700)
  host?: string;              // bind address (default: 'localhost')
  https?: {                   // enable HTTPS for the dev server
    cert: string;             // path to certificate file
    key: string;              // path to key file
  };
  cors?: {
    origin: string | string[] | '*';
    credentials?: boolean;
    methods?: string[];
  };
}
```

### `build`

Build system options.

```typescript
build: {
  target: 'node' | 'edge' | 'static';  // deployment target
  outDir?: string;                       // output directory (default: '.velox/output')
  sourcemap?: boolean | 'external';      // generate source maps
  minify?: boolean;                      // minify output (default: true in production)
  splitting?: boolean;                   // enable code splitting (default: true)
  analyze?: boolean;                     // emit a bundle analysis report
  prerender?: string[];                  // explicit list of routes to pre-render
}
```

### `routes`

Fine-grained routing options.

```typescript
routes: {
  dir?: string;                // routes directory (default: 'routes')
  extensions?: string[];       // file extensions treated as routes
  // default: ['.velox', '.tsx', '.ts']
  exclude?: string[];          // glob patterns to exclude
}
```

### `assets`

Asset handling and optimisation.

```typescript
assets: {
  publicDir?: string;          // static assets directory (default: 'public')
  imageOptimisation?: {
    enabled: boolean;
    formats?: ('webp' | 'avif')[];
    quality?: number;          // 1–100, default 80
  };
  fonts?: {
    preload?: boolean;
    subsets?: string[];
  };
}
```

### `css`

Stylesheet handling.

```typescript
css: {
  modules?: {
    localsConvention?: 'camelCase' | 'camelCaseOnly' | 'dashes';
    generateScopedName?: string;
  };
  preprocessors?: {
    sass?: boolean;            // enable Sass (requires @velox/sass)
    less?: boolean;
    stylus?: boolean;
  };
  postcss?: {
    plugins?: any[];
  };
}
```

### `plugins`

The plugin array lets you extend Velox with first-party and community plugins.

```typescript
import { defineConfig } from 'velox';
import { veloxMDX } from '@velox/mdx';
import { veloxSass } from '@velox/sass';
import { veloxPWA } from '@velox/pwa';

export default defineConfig({
  plugins: [
    veloxMDX(),
    veloxSass(),
    veloxPWA({
      name: 'My App',
      themeColor: '#3a7bd5',
    }),
  ],
});
```

### `experimental`

Opt-in to experimental features that are not yet stable.

```typescript
experimental: {
  viewTransitions?: boolean;   // CSS View Transitions API support
  partialHydration?: boolean;  // fine-grained component hydration
  reactCompat?: boolean;       // React component compatibility shim
}
```

## Environment-Specific Configuration

You can provide environment-specific overrides:

```typescript
import { defineConfig } from 'velox';

export default defineConfig({
  app: {
    name: 'My App',
    baseUrl: process.env.PUBLIC_BASE_URL!,
  },
  server: {
    port: parseInt(process.env.PORT ?? '3700'),
  },
  build: {
    target: process.env.VELOX_TARGET as 'node' | 'edge' ?? 'node',
    sourcemap: process.env.NODE_ENV !== 'production',
  },
});
```

## Per-Route Rendering Configuration

You can override the rendering mode for individual routes from within the route file:

```typescript
// routes/dashboard.velox server block
export const config = {
  render: 'ssr',       // 'ssr' | 'ssg' | 'isr' | 'csr'
  revalidate: 60,      // ISR: revalidate every 60 seconds
  edge: true,          // run on edge runtime
};
```

## Full Example

A production-ready `velox.config.ts` for a large application:

```typescript
import { defineConfig } from 'velox';
import { veloxMDX } from '@velox/mdx';

export default defineConfig({
  app: {
    name: 'Acme Corp',
    baseUrl: process.env.PUBLIC_BASE_URL!,
    defaultLocale: 'en',
  },
  server: {
    port: 3700,
    cors: {
      origin: process.env.ALLOWED_ORIGINS?.split(',') ?? '*',
      credentials: true,
    },
  },
  build: {
    target: 'edge',
    sourcemap: 'external',
    analyze: process.env.ANALYZE === '1',
  },
  assets: {
    imageOptimisation: {
      enabled: true,
      formats: ['webp', 'avif'],
      quality: 85,
    },
  },
  plugins: [veloxMDX()],
});
```

For the complete type definitions, see the [Config API](pages/api-config.md) reference.
