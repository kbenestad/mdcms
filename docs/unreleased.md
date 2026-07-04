# Unreleased changes

Changes merged into `development` that have not yet been released to `main`.

---

## Renderer (`app/index.html`)

- **Fixed: Bunny Fonts only ever loaded one of a theme's fonts.** `loadFonts()`
  built the Bunny stylesheet URL as `?family=Font1:weight&family=Font2:weight`
  — the Google Fonts v2 convention — but Bunny Fonts requires multiple
  families to be pipe-separated inside a single `family=` parameter
  (`?family=Font1:weight|Font2:weight`). With the old syntax Bunny silently
  served only the *first* family (always `font-body`, since `font-heading`
  and `font-code` are appended after it) and dropped the rest, so any theme
  with a distinct heading font — the vast majority of the library — silently
  fell back to the system sans-serif for headings. Nobody noticed for
  themes whose heading font happened to look close to the fallback; it
  became obvious with the Newspaper-inspired themes' serif headlines.
  Google Fonts requests are unaffected — that provider's v2 API genuinely
  does use repeated `family=` params, which is what led the original code
  to (incorrectly) assume Bunny worked the same way.
- **Re-synced all seven sample sites' bundled `index.html`** with the
  current `app/index.html`. They'd drifted since the last sync (missing
  both the font-loading fix above and the `heading` palette token from the
  previous change) — each sample site carries its own static copy of the
  renderer rather than a live link to `app/index.html`, so this fix (and
  the earlier heading-colour one) wouldn't have been visible in the
  sample-site picker without it.
