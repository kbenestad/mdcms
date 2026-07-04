---
title: Parent sections, without nesting your files
created: 2026-03-10 09:30
author: MD-CMS
description: Two-level nav grouping with parent and parent-sort.
---

# Parent sections, without nesting your files

A section in `nav.yml` can declare `parent: <other-section-code>` and
`parent-sort: <n>` to become a child of another section in the nav — no
change to where the markdown files actually live in `pages/`. This
showcase's **Tutorials** section uses it: *Quick start* and *Theming* are
both children of *Tutorials*, ordered by `parent-sort`. See the *Tutorials*
overview page for the exact `nav.yml` snippet.
