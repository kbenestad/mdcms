---
title: Theming
sort: 100
section-id: tutorials-theming
description: Browse the theme library, install one, and override a token.
---

# Theming

## Browse the library

```bash
mdcms config my-docs --list-themes
```

Prints every theme in the library by family and label — the same list the
sample-site picker's theme dropdown draws from.

## Install one

```bash
mdcms config my-docs --theme "term-vt100"
```

Downloads the theme file into an `assets`/`themes` subfolder and sets
`theme:` in `config.yml` to point at it. Themes can also be browsed and
installed interactively with `mdcms config my-docs` (no flags).

## Override a token

Every theme is a `palette:` block with `light:` and `dark:` sub-blocks, five
required tokens each (`primary`, `page`, `surface`, `ink`, `ink-muted`) plus
optional `on-surface-*` tokens for nav legibility on strong surface colours:

```yaml
palette:
  light:
    primary: "#2563EB"
    surface: "#F8FAFC"
    page: "#FFFFFF"
    ink: "#1E293B"
    ink-muted: "#64748B"
  dark:
    primary: "#60A5FA"
    surface: "#1E293B"
    page: "#0F172A"
    ink: "#F1F5F9"
    ink-muted: "#94A3B8"
```

Edit the installed theme file directly, or set overrides in `config.yml` —
values there (`font-body`, `main-width`, `nav-width`, and friends) win over
`theme.yml` without touching the theme file itself.
