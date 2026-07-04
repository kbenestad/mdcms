---
title: Contents
sort: 220
section-id: guides
description: An auto-generated table of contents for this site.
---

# Table of contents

The `toc` tag renders every visible, non-draft page grouped by nav section. It
updates automatically as pages are added — no manual list to maintain.

```mdcms
toc
```

## One section only

`toc-section` lists just one section. With no argument it uses the section of
the page it sits on; this page is in **Guides**, so the block below shows the
Guides pages. Add a section id (`toc-section reference`) to target another one.

```mdcms
toc-section
```

## This page's headings

`toc-page` builds an in-page table of contents from the current page's own
headings, with anchor links that jump straight to each one.

```mdcms
toc-page
```
