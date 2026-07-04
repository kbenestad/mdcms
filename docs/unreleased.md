# Unreleased changes

Changes merged into `development` that have not yet been released to `main`.

---

## Sample sites

- **Revised the `showcase` sample site** to demonstrate the full current tag
  surface and two features it previously didn't touch at all: nested
  (`parent`/`parent-sort`) sections and the category (language) switcher.
  - Callouts: added a custom-icon example and a second `message:`-sourced
    example (`beta`), alongside the existing `preview` one.
  - Components: added the bare `tab`/`accordion` aliases and the
    `title-style` option.
  - New `pages/markdown.md`: footnotes, tables, task lists, strikethrough,
    autolinks, and raw HTML passthrough — including a documented gotcha
    (footnote extraction skips fenced code blocks but not inline code
    spans, so the marker's own syntax can't be shown inline).
  - Blog: added the other reliable `posts-created-*` variant
    (`chronological-byyearmonth`) next to the existing
    `reversechronological` demo, plus four new posts spanning Dec 2025–Jul
    2026 so the grouping has something to show.
  - New `Tutorials` section with two real (non-lorem) walkthrough pages
    (`Quick start`, `Theming`), each its own child section under
    `Tutorials` via `parent`/`parent-sort` — with an overview page
    documenting the exact `nav.yml`, and an accurate note that
    `parent`/`parent-sort` currently has no visible effect in `navigation:
    topbar` (every section, parent or child, still renders as its own flat
    top-level dropdown; only `navigation: sidebar` renders the indented
    tree). Worth a closer look as a possible renderer gap.
  - Enabled `categories-use: yes` with an English/Norsk category pair. Most
    pages deliberately have no `.nb.md` variant, to demonstrate the
    `visibilityifnocontent`/`pagenotfoundmessage` fallback; a few
    (`home`, `about`, and a new `pages/categories.md` guide) do. The guide
    page prints the site's actual `categories-*` config block verbatim, for
    readers who want to see the real thing rather than a generic example.
