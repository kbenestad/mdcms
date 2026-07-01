---
title: Installation
sort: 110
section-id: getting-started
keywords: install, setup, npm, yarn, pnpm, bun, node, requirements
description: How to install Velox and set up your development environment
language: en
---

# Installation

This page covers everything you need to install Velox and get your development environment ready to build production applications.

## System Requirements

Before installing Velox, ensure your system meets the following requirements:

| Requirement | Minimum Version | Recommended |
|---|---|---|
| Node.js | 20.0.0 | 22.x LTS |
| npm | 9.0.0 | 10.x |
| Operating system | macOS 12, Ubuntu 22.04, Windows 10 | Latest stable |
| RAM | 2 GB | 8 GB+ |
| Disk space | 500 MB | 2 GB (for caches) |

Velox's Rust-based build system (Velocitor) ships as a pre-compiled binary for macOS (arm64 + x86_64), Linux (x86_64 + aarch64), and Windows (x86_64). You do **not** need a Rust toolchain installed on your machine.

## Installing the Velox CLI

The Velox CLI (`velox`) is the primary tool for scaffolding projects, running the development server, and triggering builds. Install it globally with your preferred package manager:

```bash
# npm
npm install -g velox-cli

# yarn
yarn global add velox-cli

# pnpm
pnpm add -g velox-cli

# bun
bun add -g velox-cli
```

After installation, verify the CLI is available:

```bash
velox --version
# velox-cli v1.4.0
```

## Creating a New Project

### Using `create-velox` (Recommended)

The easiest way to start a new Velox project is through the `create-velox` initialiser. It interactively walks you through project setup:

```bash
npm create velox@latest
```

You will be asked:
1. **Project name** — used as the directory name and initial package name
2. **Template** — choose from `minimal`, `blog`, `docs`, `dashboard`, or `e-commerce`
3. **TypeScript or JavaScript** — TypeScript is strongly recommended
4. **Package manager** — the scaffolder will use this for the initial install

For non-interactive use, pass flags directly:

```bash
npm create velox@latest my-app -- --template minimal --ts --pm pnpm
```

### Manual Installation

If you prefer to configure everything from scratch:

```bash
mkdir my-app && cd my-app
npm init -y
npm install velox
npm install -D velox-cli typescript @types/node
```

Create a minimal `velox.config.ts`:

```typescript
import { defineConfig } from 'velox';

export default defineConfig({
  app: {
    name: 'my-app',
  },
});
```

## Installing Dependencies in an Existing Project

If you are adding Velox to an existing TypeScript project:

```bash
npm install velox
npm install -D velox-cli
```

Then add the following scripts to your `package.json`:

```json
{
  "scripts": {
    "dev": "velox dev",
    "build": "velox build",
    "start": "velox start",
    "preview": "velox preview"
  }
}
```

## Node Version Management

We recommend using a Node version manager to ensure you always have the correct version. Popular options:

```bash
# nvm (macOS/Linux)
nvm install 22
nvm use 22

# fnm (fast, cross-platform)
fnm install 22
fnm use 22

# volta (pins versions per project)
volta install node@22
```

You can also pin the Node version for your project by adding a `.nvmrc` or `.node-version` file:

```
22
```

## Environment Variables

Velox reads environment variables from `.env` files at the project root. The following files are loaded in order (later files override earlier ones):

| File | Loaded in | Committed to git? |
|---|---|---|
| `.env` | All environments | Usually yes (no secrets) |
| `.env.local` | All environments | No (gitignored) |
| `.env.development` | `velox dev` only | Usually yes |
| `.env.production` | `velox build` / `velox start` | Usually yes |
| `.env.test` | Test runs | Usually yes |

Variables prefixed with `PUBLIC_` are exposed to the browser. All other variables remain server-side only.

```bash
# .env
PUBLIC_APP_NAME=My Velox App
DATABASE_URL=postgres://localhost:5432/mydb
SECRET_API_KEY=do-not-expose-this
```

## Updating Velox

To update Velox to the latest version within your project:

```bash
npm install velox@latest
npm install -D velox-cli@latest
```

To check whether updates are available without applying them:

```bash
velox upgrade --check
```

## Troubleshooting Installation

**`velox` command not found after global install**
Ensure your package manager's global bin directory is in your `PATH`. For npm, run `npm config get prefix` and add the `bin` subdirectory to your shell profile.

**Velocitor binary fails to run on Linux**
Some minimal Linux environments (e.g., Alpine Linux) may be missing the `glibc` version Velocitor requires. Install `glibc` compatibility libraries or use the musl build:

```bash
npm install velox@latest --velox-binary-variant=musl
```

**Windows Defender flags the Velocitor binary**
This is a false positive. Add an exclusion for your project's `node_modules/.velox-bin/` directory.

Next, follow the [Quick Start](quick-start.md) guide to build your first Velox application.
