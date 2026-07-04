# Unreleased changes

Changes merged into `development` that have not yet been released to `main`.

---

## Sample sites

- **Removed the theme picker's Branch selector.** It pointed the "development
  (preview)" option at jsDelivr's GitHub CDN, but jsDelivr's cache lags fresh
  pushes by minutes to hours, so newly-added themes on `development` often
  didn't show up even after switching branches. The picker (`sample-sites/index.html`)
  is only deployed to GitHub Pages from `main` anyway, so it now only ever
  reads `main`'s `themes.json` — no branch switching.

## Process

- **Theme changes now go straight to `main`, bypassing `development`.**
  Documented as an exception in `CLAUDE.md`'s Branching convention: since the
  picker only reflects `main` and has no reliable way to preview
  `development`-only themes, keeping new/changed themes on `development`
  just means they're invisible until the next merge. Committing straight to
  `main` keeps the picker in sync immediately.
