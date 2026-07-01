# Known bugs

Bugs that have been identified but not yet fixed. Fixed bugs are moved to the release notes.

---

## Fixed in development (not yet released)

### Category-variant pages fail to load on servers with SPA routing

**Symptom:** On Cloudflare Pages (and any other server configured to serve `index.html` with HTTP 200 for missing paths), clicking a nav item whose page only exists as a category-variant file (e.g. `page.current.md`, no plain `page.md`) showed garbled content — the raw HTML of `index.html` rendered as markdown, with the site's `<title>` text visible in the content area.

**Root cause:** `fetchPageFile` tried the base filename (`pages/page.md`) first. Servers with SPA routing return this with HTTP 200 (serving `index.html`), so `r.ok` was true and the function returned without trying the actual variant file (`pages/page.current.md`).

**Fix:** `fetchPageFile` now checks the `Content-Type` response header and skips any response with `text/html`, continuing to the next candidate URL.

---

### Stale service worker not removed when `pwa: no`

**Symptom:** After changing a site from `pwa: yes` to `pwa: no` and rebuilding, the old service worker remained active in browsers that had previously visited the site. Cached responses from the old build continued to be served.

**Root cause:** `mdcms build` stopped generating PWA files when `pwa: no`, but `index.html` unconditionally registers `service-worker.js` on every page load. With no new SW to replace it, the old worker stayed installed indefinitely.

**Fix:** `mdcms build` now writes a self-unregistering stub `service-worker.js` when `pwa: no`. On the visitor's next visit, the browser installs the stub which immediately calls `self.registration.unregister()`, evicting the stale worker. `manifest.json` is also deleted if present.

---

### `config.yml` YAML parse errors were silently swallowed

**Symptom:** A malformed `config.yml` (e.g. a stray tab character, which YAML forbids as a token starter) caused `read_config` to catch the `YAMLError` and return an empty dict. The build would proceed with no config — categories disabled, no default category code — producing a `nav.yml` that omitted `variants` fields and listed category variant files (e.g. `page.current.md`) as plain pages. Pages with category variants would not appear in the sidebar.

**Root cause:** `read_config` caught `(OSError, yaml.YAMLError)` in a single block and silently returned `{}` on any error.

**Fix:** `read_config` now raises `click.ClickException` on both `OSError` and `yaml.YAMLError`, aborting the build with a descriptive error message instead of continuing with an empty config.
