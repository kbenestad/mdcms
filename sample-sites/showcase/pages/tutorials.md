---
title: Tutorials
sort: 100
section-id: tutorials
description: Two short walkthroughs, nested as child sections of this page.
---

# Tutorials

*Quick start* and *Theming* (in the nav) are both **child sections** of this
one, declared with `parent`/`parent-sort` in `nav.yml`. On a
**sidebar** site, that renders as an indented tree — see the picker's
`velox-docs` or `modern-philosophy` sample for the real thing.

On this **topbar** site, it deliberately doesn't look nested: every
section, parent or child, gets its own flat top-level dropdown, positioned
by its own `sort` value — `parent`/`parent-sort` don't currently affect a
topbar's layout at all, on desktop or in the mobile menu. That's why *Quick
start* and *Theming* sit next to *Tutorials* here instead of inside it —
their `sort: 91` / `sort: 92` (chosen to land right after `Tutorials`'
`sort: 90`) is doing the visible work, not the parent link. The `parent`
link is still there in `nav.yml`, real and inspectable, it just has no
topbar-visible effect yet.

This structure is declared in `nav.yml`, not in the folder layout — both
tutorial pages live flat in `pages/`, right next to every other page:

```yaml
sections:
  - code: tutorials
    defaultname: Tutorials
    sort: 90

  - code: tutorials-quickstart
    defaultname: Quick start
    sort: 91          # topbar position — see note above
    parent: tutorials
    parent-sort: 10   # sidebar position under its parent

  - code: tutorials-theming
    defaultname: Theming
    sort: 92
    parent: tutorials
    parent-sort: 20

pages:
  - file: pages/tutorials.md
    section-id: tutorials

  - file: pages/tutorial-quickstart.md
    section-id: tutorials-quickstart

  - file: pages/tutorial-theming.md
    section-id: tutorials-theming
```

`parent` points a child section at its parent's `code`; `parent-sort`
orders siblings under that parent. On a sidebar site you can nest as many
levels as you like — the tree is built recursively — and `sort` on a child
section is irrelevant there, since `parent-sort` takes over. On this
topbar site, give child sections their own `sort` too (as above) if you
want them to at least land in a sensible place in the flat list.
