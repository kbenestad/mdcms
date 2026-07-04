---
title: Home
sort: 100
description: Overview of the MD-CMS feature showcase.
---

# MD-CMS Showcase

Welcome. This sample site is a working tour of the MD-CMS renderer. It uses
**topbar navigation** and demonstrates the tags and layout features added in
v0.4–v0.6, all rendered client-side from plain markdown.

```mdcms callout-info
message: preview
```

## What you can explore

- **Callouts** — coloured info / warning / success / error blocks, custom
  icons, and config-sourced messages. See *Callouts*.
- **Tabs & accordions** — interactive content panels, both variants and both
  bare aliases. See *Components*.
- **Markdown extras** — footnotes, tables, task lists, strikethrough,
  autolinks, raw HTML. See *Markdown extras*.
- **Table of contents** — an auto-generated page index. See *Contents*.
- **Posts** — both reliable `posts-created-*` variants, with pagination and
  year-month grouping. See *Blog*.
- **Nested sections** — *Tutorials*, *Quick start* and *Theming* are
  configured with `parent`/`parent-sort` in `nav.yml`. See *Tutorials* for
  what that does (and doesn't) render as on a topbar site like this one.
- **Categories** — a language switcher (English / Norsk). See
  *Language switcher*, or use the switcher in the top bar right now.

Use the search box in the top bar to jump to any page, or the theme toggle to
switch between light and dark.

## Why topbar?

This site sets `navigation: topbar` in `config.yml`. Sections become dropdown
menus and unsectioned pages sit inline. Try the **Guides** dropdown above.
