---
title: Quick start
sort: 100
section-id: tutorials-quickstart
description: Register a site, add a page, build, and preview it locally.
---

# Quick start

## 1. Register a site

```bash
mdcms register my-docs
```

With no existing MD-CMS site at the path, this downloads the starter
template (the same `app/` you're browsing right now, minus the demo
content) and adds `my-docs` to your local registry.

## 2. Add a page

Drop a markdown file in `pages/`:

```markdown
---
title: Getting started
sort: 100
---

# Getting started

Welcome to my docs.
```

## 3. Build

```bash
mdcms build my-docs
```

This regenerates `nav.yml` (adding your new page under the right section)
and `search.json` (so it's searchable).

## 4. Preview

```bash
cd my-docs
python3 -m http.server 8800
```

Open `http://localhost:8800`. Don't open `index.html` directly — browsers
block local file access with CORS errors, so the file loads but the
markdown never does.
