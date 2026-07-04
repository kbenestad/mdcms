---
title: Components
sort: 210
section-id: guides
description: Interactive tab and accordion panels.
---

# Tabs & Accordions

## Tab — Underline variant

```mdcms tab-underline
items:
  - title: Install
    default: selected
    content: |
      Install with `npm i mdcms` or `pnpm add mdcms`.
  - title: Configure
    content: |
      Drop a `mdcms.config.yaml` next to your content folder.
  - title: Deploy
    content: |
      Any static host. The build emits plain HTML.
```

## Tab — Filled variant

```mdcms tab-filled
items:
  - title: Overview
    default: selected
    content: |
      MD-CMS is a markdown-based static site system with no build step.
  - title: Features
    content: |
      - Sidebar navigation with sections
      - Full-text search via Fuse.js
      - PWA support with offline caching
      - Dark / light theme toggle
  - title: Architecture
    content: |
      Two parts: `mdcms.py` (CLI) and `app/index.html` (browser renderer).
```

## Tab — bare alias + `title-style`

`tab` is an alias for `tab-underline`. `title-style` sets the heading level
used for each tab's label for screen readers — it doesn't change how the
label looks.

```mdcms tab
items:
  - title: mdcms.py
    default: selected
    title-style: "###"
    content: |
      The CLI: registry, scanning, `nav.yml`/`search.json` generation.
  - title: index.html
    title-style: "###"
    content: |
      The renderer: reads markdown, config, and nav at runtime. No build step.
```

## Accordion — Underline variant

```mdcms accordion-underline
items:
  - title: What is MD-CMS?
    default: open
    content: |
      MD-CMS is a single-file browser renderer that reads markdown, config,
      and nav at runtime entirely client-side. No build pipeline, no compilation.
  - title: How do I install it?
    content: |
      Run `pip install mdcms` or download a binary from the GitHub releases page.
  - title: Does it work offline?
    content: |
      Yes — run `mdcms fetch-deps` to bundle all vendor assets locally, then
      enable `pwa: yes` in `config.yml` for full offline support.
```

## Accordion — Filled variant

```mdcms accordion-filled
items:
  - title: Can I use custom themes?
    default: open
    content: |
      Yes. Create a `theme.yml` file and point to it with `theme: theme.yml` in
      your `config.yml`. The theme controls colours, fonts, and layout.
  - title: What markdown features are supported?
    content: |
      GFM (GitHub Flavored Markdown): tables, task lists, fenced code blocks,
      strikethrough, and autolinks. See the *Markdown extras* page for a
      full tour, including footnotes.
  - title: Can I nest categories?
    content: |
      Categories are flat (no nesting), but nav sections support a `parent:`
      key for two-level grouping. See *Tutorials* for what that looks like
      on a topbar site (this one) versus a sidebar site.
```

## Accordion — bare alias

`accordion` is an alias for `accordion-underline`:

```mdcms accordion
items:
  - title: Does this alias behave any differently?
    default: open
    content: |
      No — `accordion` and `accordion-underline` render identically. The
      bare names (`tab`, `accordion`) exist so a page can start simple and
      you can add `-underline` or `-filled` later without renaming the tag.
```
