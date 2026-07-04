---
title: Markdown extras
sort: 230
section-id: guides
description: Footnotes, tables, task lists, strikethrough, autolinks and raw HTML.
---

# Markdown extras

Beyond `mdcms` tags, the renderer supports CommonMark plus GFM (GitHub
Flavored Markdown) extensions, and Pandoc-style footnotes.

## Footnotes

Write an inline marker like this (shown here as a fenced block — inline
code spans aren't safe, see the note below):

```text
Some text^[footnote text].
```

The renderer extracts it, numbers it, and appends a "Footnotes" list at the
end of the article with a back-link.

MD-CMS has no build step^[The renderer — `app/index.html` — reads markdown,
`config.yml`, and `nav.yml` at runtime, entirely in the browser.] and no
server component^[`mdcms.py` only runs when you choose to run it: `build`
regenerates `nav.yml` and `search.json`; nothing runs continuously.]. Click
either footnote number to jump down, then use the ↩ to jump back.

**Gotcha:** footnote extraction runs on the raw markdown before it's
parsed, and only skips *fenced* code blocks (triple backtick). A single
inline code span isn't protected — writing the marker's own syntax inside
one (rather than a fenced block) turns it into a real footnote instead of a
code sample. That's exactly what happened the first time this page was
drafted. Use a fenced block, as above, whenever you need to show the
syntax itself rather than use it.

## Tables

| Tag | Options |
|---|---|
| `callout-info` / `-warning` / `-success` / `-error` | `title`, `icon`, `message` |
| `toc` | none |
| `posts-created-*` | `limit`, `paginate` |
| `tab` / `tab-underline` / `tab-filled` | `items` (`title`, `content`, `default`, `title-style`) |
| `accordion` / `accordion-underline` / `accordion-filled` | `items` (`title`, `content`, `default`, `title-style`) |

## Task lists

- [x] Callouts — four types, custom icons, config-sourced messages
- [x] Tabs and accordions — both variants, both aliases
- [x] Table of contents
- [x] Post listings — both reliable `posts-created-*` variants
- [x] Footnotes
- [ ] Whatever ships next

## Strikethrough and autolinks

~~`posts-datetime-*`~~ was the old tag family name; it's `posts-created-*`
now. Bare URLs autolink: https://github.com/kbenestad/mdcms

## Raw HTML passthrough

Raw HTML in a markdown file passes straight through to the DOM:

<div style="padding: 0.75rem 1rem; border-radius: 6px; background: var(--bg-nav); border: 1px solid var(--divider);">
This box is a literal <code>&lt;div&gt;</code> written directly in <code>markdown.md</code> — no <code>mdcms</code> tag involved.
</div>

`<script>` tags are the one exception — the renderer uses `innerHTML`, which
browsers refuse to execute scripts through, so inline scripts in markdown
are inert by design.
