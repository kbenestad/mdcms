---
title: Layouts
sort: 150
section-id: core-concepts
keywords: layouts, nested layouts, shared layouts, layout groups, _layout, slots
description: How to use nested layouts, shared layouts, and layout groups in Velox
language: en
---

# Layouts

Layouts define the structural shell around your page content — navigation headers, sidebars, footers, and anything else that persists across multiple pages. Velox provides a flexible, composable layout system built directly into the file-based router.

## Default Layout

The file `layouts/default.velox` is the root layout applied to all routes unless overridden:

```tsx
// layouts/default.velox
---
import Header from '../components/Header.tsx';
import Footer from '../components/Footer.tsx';
---

<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>{meta.title} — My App</title>
    <meta name="description" content={meta.description} />
    <link rel="stylesheet" href="/styles/global.css" />
  </head>
  <body>
    <Header />
    <main id="main-content">
      <slot />
    </main>
    <Footer />
  </body>
</html>
```

The `<slot />` element is where the current page's content is injected. Layout files receive `meta` (the exports from the route's server block) and `params` automatically.

## Route-Level Layout Override

A route can specify a different layout using the `layout` export in its server block:

```tsx
---
export const layout = 'minimal'; // uses layouts/minimal.velox
export const meta = { title: 'Login' };
---

<div class="login-container">
  <LoginForm />
</div>
```

Set `layout` to `false` to render the page with no layout at all:

```tsx
---
export const layout = false; // bare HTML response
---

<!DOCTYPE html>
<html>...</html>
```

## `_layout.velox` — Directory Scoped Layouts

Place a `_layout.velox` file inside any `routes/` subdirectory to apply a layout to all routes in that directory and its subdirectories:

```
routes/
├── _layout.velox            ← root layout (all routes)
├── index.velox
├── about.velox
└── admin/
    ├── _layout.velox        ← admin layout (only /admin/* routes)
    ├── index.velox
    └── users/
        ├── _layout.velox    ← users layout (only /admin/users/* routes)
        └── index.velox
```

Layouts nest — the admin layout wraps its content inside the root layout's `<slot />`, and the users layout wraps inside the admin layout's `<slot />`:

```
Root Layout
  └── Admin Layout
        └── Users Layout
              └── Page Content
```

### Admin Layout Example

```tsx
// routes/admin/_layout.velox
---
import AdminNav from '../../components/AdminNav.tsx';

const user = request.context.get('user');
export const meta = { title: 'Admin' };
---

<div class="admin-shell">
  <AdminNav user={user} />
  <div class="admin-content">
    <slot />
  </div>
</div>
```

## Layout Groups

Wrap a directory in parentheses to create a **route group** that applies a shared layout without affecting the URL:

```
routes/
├── (public)/
│   ├── _layout.velox    ← marketing/public layout
│   ├── index.velox      →  /
│   └── pricing.velox    →  /pricing
└── (app)/
    ├── _layout.velox    ← application layout (requires auth)
    ├── dashboard.velox  →  /dashboard
    └── settings.velox   →  /settings
```

Both `/` and `/pricing` use the public layout. Both `/dashboard` and `/settings` use the app layout. The group name `(public)` and `(app)` never appear in the URL.

## Shared Layout Components

For UI elements shared between multiple layouts (a navigation bar used by both the public and admin layouts, for example), extract them as regular components:

```tsx
// components/TopNav.tsx
interface TopNavProps {
  links: { label: string; href: string }[];
  user?: User | null;
}

export default function TopNav({ links, user }: TopNavProps) {
  return (
    <nav class="top-nav">
      <ul>
        {links.map(link => (
          <li><a href={link.href}>{link.label}</a></li>
        ))}
      </ul>
      {user ? <UserMenu user={user} /> : <a href="/login">Log in</a>}
    </nav>
  );
}
```

Use it in both layouts:

```tsx
// layouts/default.velox
<TopNav links={publicLinks} user={null} />

// routes/admin/_layout.velox
<TopNav links={adminLinks} user={user} />
```

## Data in Layouts

`_layout.velox` files have their own server block and can fetch data independently:

```tsx
// routes/dashboard/_layout.velox
---
import { db } from '$lib/db';

const user = request.context.get('user');
const notifications = await db.notifications.findUnread(user.id);
---

<div class="dashboard-shell">
  <DashboardNav notifications={notifications} />
  <slot />
</div>
```

Layout data is fetched in parallel with page data — there is no waterfall.

## Parallel Slots

For complex layouts with multiple content regions, use named parallel slots:

```tsx
// A layout that accepts both main content and a sidebar
---
export const slots = ['default', 'sidebar'];
---

<div class="two-column">
  <aside class="sidebar">
    <slot name="sidebar" />
  </aside>
  <main>
    <slot />
  </main>
</div>
```

Fill the named slot from the page:

```tsx
---
export const layout = 'two-column';
---

<!-- Default slot content -->
<article>Main content here</article>

<!-- Named slot -->
<velox:slot name="sidebar">
  <TableOfContents />
</velox:slot>
```

## `<Head>` Management

Layouts and pages can both add content to the HTML `<head>` using the `<Head>` component:

```tsx
import { Head } from 'velox';

<Head>
  <link rel="canonical" href={canonicalUrl} />
  <meta property="og:title" content={meta.title} />
  <meta property="og:image" content={meta.ogImage} />
  <script type="application/ld+json">{JSON.stringify(structuredData)}</script>
</Head>
```

`<Head>` insertions from nested layouts and pages are all collected and deduplicated before the final HTML is emitted.
