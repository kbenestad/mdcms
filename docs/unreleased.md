# Unreleased changes

Changes merged into `development` that have not yet been released to `main`.

---

## Added

- `mdcms config` gains three new interactive submenus — *Manage pages* (create/edit/delete markdown files, including title, section-id, sort, and draft), *Manage sections* (add/rename/reorder/reparent/set visibility/toggle pagination/delete `nav.yml` sections, with cycle detection on reparenting), and *Manage categories* (toggle `categories-use`/`categories-dates`, add/edit/remove categories, set the default category) — so none of `nav.yml`, `config.yml`'s category blocks, or page frontmatter need hand-editing. All new flows validate input and recover gracefully from mistakes (invalid codes, non-integer sort values, cancelled prompts) instead of crashing the session. `mdcms.py` gains supporting helpers: `read_nav_yml`/`write_nav_yml`, `set_config_block` (structured-block editing for `default-category`/`categories`, mirroring the existing surgical scalar editor), and `list_markdown_files`/`write_page_file` for page CRUD.
- Date categories: setting `categories-dates: yes` in `config.yml` makes `mdcms build` auto-detect `<base>.YYYYMMDD.md` page/post variants (e.g. `report.20260704.md`) as categories, without declaring each date in `categories:`. Detected dates are written to `nav.yml` as a generated `date-categories` list, newest first, and the renderer displays each as `d Mmmm YYYY` (e.g. "4 July 2026") in the category dropdown. Because a dated variant is a historical record of one page and not a snapshot of the whole site, the nav (sidebar/topbar tree, TOC tags, pagination labels, and search) always reflects `default-category` once any date category exists — even while viewing an older date — regardless of whether the default itself is a date or a declared code, or the set is mixed. Renderer + CLI change (`app/index.html`, `mdcms.py`); re-synced into all sample sites. Also fixes a related nav.yml round-trip bug: all-digit category/section/variant codes are now always quoted on write, since an unquoted one (e.g. `20260704`) parses back as a YAML integer and previously broke on rebuild.
- Section pagination: setting `pagination: on` on a section in `nav.yml` adds Previous/Next controls to that section's pages — at the bottom of the page, and again in the upper right beneath the category selector (on its own if categories are disabled). Order follows the same sort used elsewhere for nav (page `sort`, then filename). `mdcms.py` now preserves and re-emits the `pagination` field on rebuild alongside the other manually-edited section metadata. Renderer-only + CLI round-trip change (`app/index.html`, `mdcms.py`); re-synced into all sample sites.
- `toc-section` and `toc-page` table-of-contents tags (renderer, `app/index.html`). `toc-section` renders only one section — the current page's section by default, or `toc-section <section-id>` for a named section. `toc-page` renders an in-page table of contents: an indented, anchor-linked list of the current page's own headings (`h2`–`h6`). The existing site-wide `toc` is unchanged. Re-synced into all sample sites.

## Fixed

- Browser Back/Forward buttons now work as expected. In-app navigation previously replaced the single history entry on every page change (`history.replaceState`), so the Back button had nothing to return to — it was effectively disabled. `navigateTo()` now pushes a new history entry for user-initiated navigation, replaces on first paint (so the first Back leaves the site instead of cycling on the landing page), and leaves history untouched when the navigation is itself a Back/Forward (popstate/hashchange). Re-navigating to the page already showing no longer stacks a dead duplicate entry. Re-synced into all seven sample sites.

## Changed

- Sidebar navigation: the dark-mode toggle now sits to the right of the search bar (as a compact, icon-only button) instead of at the bottom of the sidebar, in both the desktop and mobile sidebar views. When search is disabled (`search: no`), the toggle falls back to its previous full-width position in the sidebar footer. Topbar mode is unchanged. Re-synced into all seven sample sites.

---
