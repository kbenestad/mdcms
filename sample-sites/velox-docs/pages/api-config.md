---
title: Config API
sort: 130
section-id: api-reference
keywords: config API, velox.config.ts, defineConfig, types, TypeScript reference
description: Full TypeScript type reference for velox.config.ts and all configuration options
language: en
---

# Config API

This page provides the complete TypeScript type reference for `velox.config.ts`. All types are exported from the `velox` package.

## `defineConfig(config)`

The primary export. Accepts a `VeloxConfig` object and returns it with full type checking:

```typescript
import { defineConfig } from 'velox';

export default defineConfig({
  // VeloxConfig object
});
```

You can also pass a function for dynamic configuration:

```typescript
export default defineConfig(async (env) => {
  const secrets = await loadSecrets();
  return {
    app: {
      name: 'My App',
      baseUrl: secrets.BASE_URL,
    },
  };
});
```

## `VeloxConfig`

```typescript
interface VeloxConfig {
  app?: AppConfig;
  server?: ServerConfig;
  build?: BuildConfig;
  routes?: RoutesConfig;
  assets?: AssetsConfig;
  css?: CSSConfig;
  i18n?: I18nConfig;
  middleware?: MiddlewareConfig[];
  plugins?: VeloxPlugin[];
  experimental?: ExperimentalConfig;
  errorHandler?: ErrorHandler;
}
```

## `AppConfig`

```typescript
interface AppConfig {
  /** Application display name. Used in page titles and error pages. */
  name: string;

  /** Canonical base URL. Required in production. Example: 'https://example.com' */
  baseUrl: string;

  /** Default locale for i18n. Default: 'en' */
  defaultLocale?: string;

  /** Whether to append trailing slashes to all routes. Default: false */
  trailingSlash?: boolean;

  /** Custom 404 page route. Default: '_error' */
  notFoundPage?: string;
}
```

## `ServerConfig`

```typescript
interface ServerConfig {
  /** TCP port. Default: 3700 */
  port?: number;

  /** Bind hostname. Default: 'localhost' */
  host?: string;

  /** HTTPS configuration for the development server */
  https?: {
    cert: string;   // path to PEM certificate
    key: string;    // path to PEM private key
  };

  /** CORS policy */
  cors?: {
    origin: string | string[] | ((origin: string) => boolean);
    credentials?: boolean;
    methods?: string[];
    allowedHeaders?: string[];
    exposedHeaders?: string[];
    maxAge?: number;
  };

  /** Compression. Default: true in production */
  compress?: boolean;

  /** Trust proxy headers (X-Forwarded-For, etc.). Default: false */
  trustProxy?: boolean | number;
}
```

## `BuildConfig`

```typescript
interface BuildConfig {
  /**
   * Deployment target.
   * - 'node': Outputs a Node.js server (default)
   * - 'edge': Outputs a Web-API-compatible edge bundle
   * - 'static': Full static export — no server required
   */
  target: 'node' | 'edge' | 'static';

  /** Output directory. Default: '.velox/output' */
  outDir?: string;

  /** Source map generation. Default: false in production */
  sourcemap?: boolean | 'external' | 'inline';

  /** Minify output. Default: true in production */
  minify?: boolean;

  /** Enable code splitting. Default: true */
  splitting?: boolean;

  /** Emit a bundle analysis HTML report */
  analyze?: boolean;

  /**
   * Routes to explicitly pre-render as static HTML.
   * Supports globs. e.g. ['/blog/*', '/about']
   */
  prerender?: string[];

  /** External dependencies (not bundled). */
  external?: string[];

  /** Environment variables to inline into the client bundle */
  define?: Record<string, string>;
}
```

## `RoutesConfig`

```typescript
interface RoutesConfig {
  /** Routes directory relative to project root. Default: 'routes' */
  dir?: string;

  /** File extensions treated as routes. Default: ['.velox', '.tsx'] */
  extensions?: string[];

  /** Glob patterns to exclude from routing */
  exclude?: string[];

  /** Prefix all generated routes with this base path */
  base?: string;
}
```

## `AssetsConfig`

```typescript
interface AssetsConfig {
  /** Static assets directory. Default: 'public' */
  publicDir?: string;

  imageOptimisation?: {
    enabled: boolean;
    /** Output formats to generate. Default: ['webp'] */
    formats?: ('webp' | 'avif' | 'jpeg' | 'png')[];
    /** JPEG/WebP/AVIF quality 1–100. Default: 80 */
    quality?: number;
    /** Maximum width in pixels before downscaling */
    maxWidth?: number;
  };

  fonts?: {
    /** Emit <link rel="preload"> for fonts. Default: true */
    preload?: boolean;
    /** Unicode range subsets. Example: ['latin', 'latin-ext'] */
    subsets?: string[];
  };
}
```

## `I18nConfig`

```typescript
interface I18nConfig {
  /** Supported locale codes. Example: ['en', 'fr', 'de'] */
  locales: string[];

  /** Default locale. Default: 'en' */
  defaultLocale: string;

  /** Strategy for locale in URL. Default: 'prefix-except-default' */
  routing?: 'prefix' | 'prefix-except-default' | 'domain';

  /** Domain mapping for 'domain' routing strategy */
  domains?: Record<string, string>;

  /** Path to translation files. Default: 'messages' */
  messagesDir?: string;
}
```

## `MiddlewareConfig`

```typescript
interface MiddlewareConfig {
  /** Route path glob to match. Use '*' for global middleware */
  path: string;

  /** Path to the middleware module (relative to project root) */
  handler: string;

  /** Execution order (lower runs first). Default: 0 */
  order?: number;
}
```

## `ExperimentalConfig`

```typescript
interface ExperimentalConfig {
  /** Enable CSS View Transitions for route changes */
  viewTransitions?: boolean;

  /** Enable fine-grained island hydration */
  partialHydration?: boolean;

  /** Enable compatibility shim for React components */
  reactCompat?: boolean;

  /** Enable server actions (form + RPC) */
  serverActions?: boolean;
}
```

## Plugin API

```typescript
interface VeloxPlugin {
  name: string;
  setup?(build: VeloxBuild): void | Promise<void>;
  transform?(code: string, id: string): string | { code: string; map?: string } | null;
  resolveId?(id: string, importer?: string): string | null;
  load?(id: string): string | null;
}
```

Create a plugin:

```typescript
function myPlugin(): VeloxPlugin {
  return {
    name: 'my-plugin',
    transform(code, id) {
      if (!id.endsWith('.myext')) return null;
      return { code: transformMyExtension(code) };
    },
  };
}
```
