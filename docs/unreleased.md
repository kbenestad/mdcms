# Unreleased changes

Changes merged into `development` that have not yet been released to `main`.

---

## Added

- The release workflow now maintains `docs/banner/v{version}.txt` automatically: on a tagged release, the file for the version being replaced is overwritten with an "outdated, please run `mdcms upgrade`" message, and a new file is created for the released version reading "This is the latest version (`d Mmmm YYYY`)." These are what `mdcms --version` fetches to show a one-line status message. `.github/workflows/release.yml` change only.
- Sidebar collapse toggle: whenever a sidebar nav surface is shown (`navigation: sidebar`, or a narrow viewport falling back from `navigation: topbar`), a panel-toggle button now sits next to the dark-mode toggle (`left_panel_close`/`right_panel_close`, mirrored to `left_panel_open`/`right_panel_open` when collapsed, depending on `nav-position`). On desktop it collapses the sidebar out of view entirely, leaving a small fixed reopen button at the edge; on narrow viewports it closes the open drawer, same as the overlay. `navigation: topbar`'s narrow-viewport nav panel is now restyled to look and behave like the sidebar (same off-canvas slide, search/dark-mode/panel-toggle row, nav-item styling) instead of the old top-down dropdown. When `nav-position` isn't set explicitly, the standard side now follows the site's default-category direction — right for `direction: rtl`, left otherwise — instead of always defaulting to left; this also decides which edge `navigation: topbar`'s narrow-viewport panel slides in from.

## Fixed

- `mdcms upgrade` on a standalone-binary install crashed with an uncaught `PermissionError` traceback when the binary's install location (e.g. `/usr/local/bin`) wasn't writable by the current user — the download-to-temp-file step wasn't covered by the existing permission-error handling. It now detects this case up front and automatically re-execs itself under `sudo` (prompting for the password), instead of failing or requiring the user to manually retype the command with `sudo`.
- Markdown task list items (`- [ ] foo`, `- [x] done`) rendered with a bullet point next to the checkbox. The renderer now tags task-list `<li>` elements and suppresses their `list-style`, so only the checkbox shows.

---
