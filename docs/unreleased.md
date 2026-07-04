# Unreleased changes

Changes merged into `development` that have not yet been released to `main`.

---

## Added

- `toc-section` and `toc-page` table-of-contents tags (renderer, `app/index.html`). `toc-section` renders only one section — the current page's section by default, or `toc-section <section-id>` for a named section. `toc-page` renders an in-page table of contents: an indented, anchor-linked list of the current page's own headings (`h2`–`h6`). The existing site-wide `toc` is unchanged. Re-synced into all sample sites.

---

## Changed

- Sidebar navigation: the dark-mode toggle now sits to the right of the search bar (as a compact, icon-only button) instead of at the bottom of the sidebar, in both the desktop and mobile sidebar views. When search is disabled (`search: no`), the toggle falls back to its previous full-width position in the sidebar footer. Topbar mode is unchanged. Re-synced into all seven sample sites.

---
