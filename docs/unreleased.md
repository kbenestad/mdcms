# Unreleased changes

Changes merged into `development` that have not yet been released to `main`.

---

- Topbar navigation: the active/hover tab highlight now fills the full height of
  the navigation bar (edge to edge, bottom to top) with a straight, thick
  bottom border, replacing the previous shallow pill with a curved
  `box-shadow` border-bottom. Applies to both leaf nav items and dropdown
  group triggers. All seven `sample-sites/*/index.html` copies re-synced with
  `app/index.html`.
- Fixed Pandoc-style inline footnotes (`^[...]`) not rendering at all — the
  renderer previously had no footnote support, so the raw `^[...]` markup
  appeared verbatim in the article body (visible on the Modern Philosophy
  sample site's `meta-01-existence.md`). Footnotes are now extracted before
  markdown parsing (fenced code blocks are left untouched), rendered as
  superscript reference links, and collected into a numbered "Footnotes" list
  at the end of the article with back-links. Also fixed same-document
  fragment navigation (used by the new footnote links) being swallowed by the
  hash-based page router — clicking a footnote reference or back-link
  previously triggered a page navigation to a nonexistent page (e.g. `#fn-1`)
  and blanked the article, because `popstate` fires before `hashchange` on
  same-page anchor jumps and had no guard against this. Both listeners now
  recognise in-page anchors and let the browser handle the scroll natively.
- Fixed the underline accordion variant's header text rendering smaller
  (0.75rem) than the filled variant's header (inherited body size) — both now
  share the same font size. All seven `sample-sites/*/index.html` copies
  re-synced with `app/index.html`.
