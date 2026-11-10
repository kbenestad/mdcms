# Unreleased changes

Changes merged into `development` that have not yet been released to `main`.

---

## Fixes

- **PWA sites now actually serve updated content.** With `pwa: yes`, readers who had visited before were served the pages they saw the first time, forever — rebuilding and redeploying changed nothing for them, and a reload did not help. The service worker is now versioned by a content hash of every file in the site, so a rebuild always produces a new worker; pages, config, nav and the search index are fetched network-first with the cache as the offline fallback instead of cache-first-forever; and one unfetchable file no longer aborts the whole install and freezes the site on its old content.
- **Turning `pwa: no` back off now clears the caches** the worker had filled, instead of only unregistering it.
- **Non-PWA sites refresh reliably too.** Content is fetched with revalidation when no service worker is present, so a host's own `Cache-Control` (GitHub Pages sends `max-age=600`) can't keep showing a reader content the server has already replaced.

## Features

- **A site left open updates itself.** Every site now gets a generated `site-version.json` (a content hash plus the build time). The renderer polls it on load, when the tab regains focus, when the browser comes back online, and every 15 minutes; when the hash changes it pulls the new service worker and reloads into the new content. No config key — this is on for every site.
- **New `last-updated: yes` config key** adds a button at the bottom of the nav reading `Last updated: 10 November 2026 14:32` (the build time, in the reader's own time zone). Clicking it re-downloads every page and asset past both the service-worker cache and the browser's HTTP cache, then reloads. Off by default; also offered by `mdcms config` under *PWA and update settings*.
- **New optional `last-updated-label` config key** overrides the `Last updated` text, either as a plain string or as a per-category map (same shape as `offline-message`).
- `mdcms build` now reports the build id and writes `site-version.json` on every build, PWA or not.
