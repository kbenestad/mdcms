# Unreleased changes

Changes merged into `development` that have not yet been released to `main`.

---

## Added

- Section pagination: setting `pagination: on` on a section in `nav.yml` adds Previous/Next controls to that section's pages — at the bottom of the page, and again in the upper right beneath the category selector (on its own if categories are disabled). Order follows the same sort used elsewhere for nav (page `sort`, then filename). `mdcms.py` now preserves and re-emits the `pagination` field on rebuild alongside the other manually-edited section metadata. Renderer-only + CLI round-trip change (`app/index.html`, `mdcms.py`); re-synced into all sample sites.
- `toc-section` and `toc-page` table-of-contents tags (renderer, `app/index.html`). `toc-section` renders only one section — the current page's section by default, or `toc-section <section-id>` for a named section. `toc-page` renders an in-page table of contents: an indented, anchor-linked list of the current page's own headings (`h2`–`h6`). The existing site-wide `toc` is unchanged. Re-synced into all sample sites.

## Fixed

- Browser Back/Forward buttons now work as expected. In-app navigation previously replaced the single history entry on every page change (`history.replaceState`), so the Back button had nothing to return to — it was effectively disabled. `navigateTo()` now pushes a new history entry for user-initiated navigation, replaces on first paint (so the first Back leaves the site instead of cycling on the landing page), and leaves history untouched when the navigation is itself a Back/Forward (popstate/hashchange). Re-navigating to the page already showing no longer stacks a dead duplicate entry. Re-synced into all seven sample sites.

## Changed

- Sidebar navigation: the dark-mode toggle now sits to the right of the search bar (as a compact, icon-only button) instead of at the bottom of the sidebar, in both the desktop and mobile sidebar views. When search is disabled (`search: no`), the toggle falls back to its previous full-width position in the sidebar footer. Topbar mode is unchanged. Re-synced into all seven sample sites.

---
