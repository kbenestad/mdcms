---
title: Callouts
sort: 200
section-id: guides
description: Coloured callout blocks for info, warnings, success and errors.
---

# Callouts

Callouts are fenced `mdcms` blocks. Each type has its own colour, drawn from the
active theme's semantic colours, so they restyle automatically when you change
theme.

```mdcms callout-info
title: Heads up
Callouts support **full markdown** in the body — including lists, `code`, and
[links](home.md).
```

```mdcms callout-success
title: It worked
The build completed and every page was indexed for search.
```

```mdcms callout-warning
title: Take care
Most `posts-*` tag variants were experimental in earlier releases. Prefer the
reverse-chronological listing shown on the Blog page.
```

```mdcms callout-error
title: Something broke
Use error callouts for destructive or blocking conditions the reader must not miss.
```

## Reusable messages

A callout can pull its title and body from the `callouts:` block in `config.yml`
with `message: <key>`, which keeps repeated notices (translation notices,
disclaimers) consistent across pages.
