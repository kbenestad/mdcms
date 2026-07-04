---
title: Static by default
created: 2025-12-15 10:00
author: MD-CMS
description: No server, no database, no build step — just files.
---

# Static by default

A site built with MD-CMS is markdown files, a `config.yml`, and a
`theme.yml`. There is no database and no server-side process — `index.html`
reads everything at runtime. Deploy the folder anywhere that serves static
files: GitHub Pages, Cloudflare Pages, a plain web server, even a `file://`
URL once you run a local static server for CORS.
