---
title: Language switcher
sort: 240
section-id: guides
description: How the category switcher works, with the exact config behind it.
---

# Language switcher

This site has two categories: **English** (the default) and **Norsk**. Open
the switcher in the top bar (the globe-and-text control, right side) and
pick **Norsk** — the page you're on swaps to its Norwegian variant if one
exists, and this exact page does.

```mdcms callout-info
message: translation
```

## The filename convention

A category variant is just a suffix on the filename: `categories.md` (this
page, default/English) and `categories.nb.md` (Norwegian) are variants of
the same page. No frontmatter field marks them as related — the suffix is
the whole mechanism, and `nb` only counts as a suffix because it's declared
in `config.yml` below.

## The exact config

This is the live `categories-*` block from this site's `config.yml` — not a
generic example:

```yaml
categories-use: yes
default-category:
  code: en
  name: English
  direction: ltr
categories:
  - code: nb
    name: Norsk
    direction: ltr
    visibilityifnocontent: visible
    pagenotfoundmessage: "Denne siden finnes ikke på norsk ennå — men strukturen er den samme."
categories-sectionnames: same
categories-selecticon: language
categories-selecttext: "Language"
```

## Try the fallback

Most pages on this site — *Callouts*, *Components*, *Blog*, the whole
*Tutorials* section — have **no** `.nb.md` variant. Switch to Norsk and open
any of them anyway: because `visibilityifnocontent: visible` is set, the
page stays in the nav and shows `pagenotfoundmessage` instead of silently
falling back to the English content. Set `visibilityifnocontent: hidden`
(the default) to hide such pages from the nav entirely while on that
category, or add `notfoundmessage:` to fall back to the default category's
content with a short note in the dropdown instead.

## Per-category section names

`categories-sectionnames: same` (set above) means every category shares one
section name — *Guides*, *Tutorials*, *Reference* stay in English even in
Norsk. Set it to `per-category` to translate section headings too; each
section in `nav.yml` then needs a `categorynames:` block:

```yaml
sections:
  - code: guides
    defaultname: Guides
    categorynames:
      en: Guides
      nb: Veiledninger
```

This site keeps `same` so the nav stays legible without translating every
heading for a two-category demo.
