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

## Custom icon

Any callout can override its default icon with `icon: <name>`, using an SVG
name from `assets/icons/`:

```mdcms callout-info
title: Custom icon
icon: history
This callout uses `icon: history` instead of the default info icon.
```

## Reusable, config-sourced messages

A callout can pull its title and body from the `callouts:` block in
`config.yml` with `message: <key>`, which keeps repeated notices (translation
notices, disclaimers) consistent across pages. `message:` overrides any
inline `title:` — the body below is ignored once a matching key is found.

```mdcms callout-warning
message: beta
```

That block resolves to this in `config.yml`:

```yaml
callouts:
  beta:
    type: warning
    en:
      title: "Config-sourced message"
      text: This callout's title and body came from the `callouts.beta`
        block in `config.yml`, not from the markdown you're reading.
```

The Home page uses the same mechanism with a `preview` key. Switch to the
Norsk category (top bar, right side) and come back — this callout's title
and body stay in English because `beta` has no `nb:` entry, but the site's
own `translation` message (used on the Norwegian pages) does.
