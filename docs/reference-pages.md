# Page reference — frontmatter and mdcms tags

All keys you can use inside a markdown page in `pages/` or `posts/`.

A page has two parts:

````markdown
---
# Frontmatter (YAML, optional except for title)
title: My Page
---

Markdown body goes here.

```mdcms
toc
```

Regular markdown, plus mdcms code blocks for callouts, table of contents, post lists.

````

---

## Frontmatter

The YAML block delimited by `---` at the top of the file. Read by `mdcms build` to populate `nav.yml` and `search.json`, and by `index.html` at runtime to set the page title, dates, and meta tags.

```yaml
---
title: Page Title              # REQUIRED. Browser tab title, nav label, h1 fallback.
                               # Without this, the page is skipped from nav.yml.

sort: 100                      # Position in the nav within its section. Lower = higher.
                               # Default: 100. Tiebreaker is filename.

section-id: guides             # Assigns this page to a section. Must match (or auto-create)
                               # a code: in nav.yml. Omit to leave unsectioned.

draft: true                    # Excludes the page from nav.yml AND search.json.
                               # Default: false.

author: Jane Doe               # Shown in the meta line under the page title (pages with author or created).

created: 2026-05-18 14:30      # Publish date. Format: YYYY-MM-DD or YYYY-MM-DD HH:MM.
                               # Required for posts to appear in posts-* tag listings.
                               # Used as the sort key in chronological/reverse-chronological lists.

modified: 2026-05-19 09:15     # Last-modified date. Shown next to created date if set.

description: Short summary     # Used for the <meta name="description"> tag.
                               # Falls back to config.yml sitedescription if omitted.

keywords: foo, bar, baz        # Comma-separated. Indexed in search.json.

language: en                   # BCP 47 code. Sets the <html lang=""> attribute when this page is loaded.
                               # Doesn't filter pages — that's what categories are for.
---
```

**Category variants** are not a frontmatter field — they are encoded in the filename. `about.nb.md` is the Norwegian variant of `about.md`, provided `nb` is declared in `config.yml` under `categories:`. Alternatively, `about.20260704.md` is a *date* category — no declaration needed, just `categories-dates: yes`; see `reference-config.md`'s Categories section.

Pages and posts can also be created, edited, and deleted interactively via `mdcms config` → *Manage pages*, instead of hand-writing files.

---

## mdcms code blocks

Fenced blocks with the `mdcms` language tag are intercepted by the renderer and replaced with dynamic HTML. The tag name goes either on the fence line or on the first line of the block:

````markdown
```mdcms callout-info
title: Heads up
This is the body.
```
````

…is equivalent to:

````markdown
```mdcms
callout-info
title: Heads up
This is the body.
```
````

Inside the block, lines matching `key: value` are parsed as options. The first non-matching line begins the body.

---

### Callout tags — `callout-info`, `callout-warning`, `callout-success`, `callout-error`

A bordered, tinted box for notes, warnings, success messages, errors. Colour and icon come from `theme.yml` (`callouts:` block); fall back to built-in defaults.

````markdown
```mdcms callout-info
title: Note                    # Optional. Bold title row with icon. Omit for a body-only callout.
icon: lightbulb                # Optional. Override the default icon. Use an SVG name from assets/icons/.
message: aitranslation         # Optional. Resolves title + body from config.yml callouts: block.
                               # Takes precedence over inline title/body.

Body text supports **full markdown** — bold, *italics*, `code`,
[links](https://example.com), lists, etc.

- item one
- item two
```
````

**Behaviour:**
- Type comes from the tag name suffix (`info`/`warning`/`success`/`error`).
- `message: <key>` looks up the named block in `config.yml`. When matched, the message's title and body override any inline values. The message's `type:` also overrides the tag type.
- For multi-language messages, the renderer picks the entry for the active category, then the default category, then the first key.

---

### Table of contents — `toc`, `toc-section`, `toc-page`

Three related tags render a table of contents. All exclude the page containing the tag from any page list and only list visible, non-draft pages in the active category.

**`toc`** — every section, grouped and sorted.

````markdown
```mdcms
toc
```
````

Output is grouped by nav section in section sort order; pages within each section follow their own `sort:`.

**`toc-section`** — a single section only.

````markdown
```mdcms
toc-section
```
````

With no argument, it lists the pages of the section the current page belongs to (or the unsectioned pages, if the current page has no `section-id`). Pass a section id to list a specific section regardless of the current page:

````markdown
```mdcms
toc-section reference
```
````

**`toc-page`** — an in-page table of contents: a linked, indented list of the current page's own headings (`h2`–`h6`). Each entry is an anchor that jumps to that heading; deeper headings are indented under their parents.

````markdown
```mdcms
toc-page
```
````

None of these take options.

---

### Post listings — `posts-created-*`

Generate a chronologically sorted list of posts (files in `posts/`). Requires each post to have a `created:` value in frontmatter.

The grammar:

```
posts-created-<order>[-<modifier>]
  order:    chronological | reversechronological
  modifier: byyear | byyearmonth | lastyear | lastmonth   (optional)
```

- `byyear` / `byyearmonth` — group output by year, or by year-and-month. A year
  dropdown is shown when more than one year has posts (`selectyear: no` hides
  it; `defaultyear: 2025` picks the initially shown year — default is the
  current year, falling back to the newest year with posts).
- `lastyear` / `lastmonth` — filter to posts from the last 365/30 days.
- No modifier — flat list of all posts.

All variants work (verified in-browser, July 2026).

````markdown
```mdcms
posts-created-reversechronological
limit: 10                      # Batch/page size. Default: all (batches of 20).

paginate: yes                  # Pagination mode:
                               # yes   — full pagination bar: "Page x/y",
                               #         Previous/Next buttons, jump-to-page.
                               # no    — show <limit> posts with a "Load more"
                               #         button (default).
                               # none  — show only the first <limit> posts,
                               #         no controls.
```
````

On narrow viewports (≤ 600px) each list item stacks into two lines — date and
time on top, the title link underneath — with extra space below the link to
separate it from the next item.

**Category filtering:** When `categories-use: yes`, the listing automatically filters to the active category.

---

### Tabs — `tab-underline`, `tab-filled`, `tab`

A horizontal tab strip with a single visible content panel. The active tab is set with `default: selected`; if no item carries that value the first item is selected automatically.

| Tag name | Appearance |
|---|---|
| `tab-underline` | Labels in a row; active tab marked with a 2 px underline in the accent colour. |
| `tab` | Alias for `tab-underline`. |
| `tab-filled` | Each label is a chip with a filled background; active chip inverts to the page background with an accent border. |

The body of the block is YAML. It must start with `items:` followed by a list of item objects.

````markdown
```mdcms tab-underline
items:
  - title: npm
    default: selected
    content: |
      ```bash
      npm install mdcms
      ```
  - title: pnpm
    content: |
      ```bash
      pnpm add mdcms
      ```
  - title: yarn
    content: |
      ```bash
      yarn add mdcms
      ```
```
````

**Per-item keys:**

| Key | Required | Notes |
|---|---|---|
| `title` | yes | Label on the tab button. Plain text only. |
| `content` | yes | Tab panel body. Full Markdown, use `\|` for multi-line. |
| `default` | no | `selected` — open on load. If no item is `selected`, the first item is used. |
| `title-style` | no | Heading level for screen readers. One of `"#"` … `"######"` or `""` (default). Does not affect visual size. |

---

### Accordions — `accordion-underline`, `accordion-filled`, `accordion`

Stacked collapsible items. Each item has a clickable header and a body that expands below it. Any number of items can be open simultaneously.

| Tag name | Appearance |
|---|---|
| `accordion-underline` | Header separated from the content by a 2 px bar in the accent or nav colour; open content has a matching 1 px border on three sides. |
| `accordion` | Alias for `accordion-underline`. |
| `accordion-filled` | Closed header is a filled chip; when open the item becomes a single bordered card with the header fill at the top and the page background below. |

````markdown
```mdcms accordion
items:
  - title: What is MD-CMS?
    default: open
    content: |
      A single-file browser renderer. No build pipeline, no compilation,
      no server required.
  - title: How do I install it?
    content: |
      Run `pip install mdcms` or download a binary from the GitHub releases page.
  - title: Does it work offline?
    content: |
      Yes — run `mdcms fetch-deps` to bundle vendor assets locally, then enable
      `pwa: yes` in `config.yml` for full offline support.
```
````

**Per-item keys:**

| Key | Required | Notes |
|---|---|---|
| `title` | yes | Header label. Plain text only. |
| `content` | yes | Body shown when expanded. Full Markdown, use `\|` for multi-line. |
| `default` | no | `open` — expanded on load. `closed` or omitted — collapsed. Multiple items may be `open`. |
| `title-style` | no | Heading level for screen readers. One of `"#"` … `"######"` or `""` (default). Does not affect visual size. |

**How the colour adapts to themes:** The bar/border colour and the chip fill are derived automatically from the active theme. On themes where the sidebar background is visually distinct from the page (dark nav on a light page, or a coloured nav), the components use the nav colour as their fill. On subtle themes where sidebar and page backgrounds are near-identical, the accent colour is used instead. No per-theme config is needed.

---

## Markdown features

Standard CommonMark plus GFM (GitHub-flavoured) extensions:

- Tables
- Strikethrough (`~~text~~`)
- Task lists (`- [ ]` / `- [x]`)
- Fenced code blocks with syntax language hints (`` ```python ``)
- Autolinks

**Raw HTML** passes through to the DOM. You can embed HTML directly:

```markdown
<meta http-equiv="refresh" content="0; url=docs/">
```

**Scripts injected via `<script>` tags in markdown do not execute** — the renderer uses `innerHTML`, which browsers block from running script tags. Use `<meta http-equiv="refresh">` for redirects.

**Links to other pages** can use either:

```markdown
[Docs](pages/docs.md)          # Internal link — rewritten to a client-side route.
[External](https://example.com)  # External — opens in new tab automatically.
```

---

## Full example

````markdown
---
title: Quick Start
sort: 100
section-id: getting-started
author: Jane Doe
created: 2026-05-18 14:30
description: How to install and run MD-CMS in five minutes.
keywords: install, setup, quickstart
---

# Quick start

Welcome. This page walks you through installing MD-CMS.

```mdcms callout-info
title: Before you begin
Make sure you have Python 3.9 or newer.
```

## Table of contents

```mdcms
toc
```

## Recent posts

```mdcms
posts-created-reversechronological
limit: 5
paginate: yes
```

## Translation notice

```mdcms callout-warning
message: aitranslation
```
````
