# Known bugs

Bugs that have been identified but not yet fixed. Fixed bugs are moved to the release notes.

---

## Fixed in development (not yet released)

### `mdcms build` writes an unparseable `nav.yml` for some page titles

**Symptom:** After a build, the site's navigation stops working entirely and `mdcms config` reports no sections. Editing sections through `mdcms config` appears to do nothing — or worse, silently throws away every section and page already in `nav.yml`.

**Root cause:** `_emit_value()` — the scalar emitter behind `generate_nav_yml()` — quoted a value only when it was empty, contained `:`, `"`, `'` or `#`, or spelled `true`/`false`/`null`, and when quoting it escaped `"` but not `\`. Two failure modes followed:

- A title containing a backslash (e.g. `C:\Users\me — setup`) was quoted because of the colon, but the backslash was left as-is, producing `"C:\Users\me — setup"` — an invalid YAML escape sequence, so the whole file failed to parse.
- A title starting with a YAML indicator character (`[2026] Roadmap`, `- dash lead`, `@handle`, `%share`) was emitted bare and parsed back as a flow sequence, a block sequence, or a parse error rather than as a string. Purely numeric titles (`2026`) and YAML 1.1 booleans (`yes`, `on`) came back as an int/bool.

Once `nav.yml` was unparseable, the renderer's js-yaml load failed and the nav went blank, which is what "the build stopped working" looks like from the browser.

**Fix:** `_emit_value()` now escapes backslashes, quotes, and control characters, and decides whether quoting is needed by round-tripping the string through the parser — anything that fails to parse or comes back as a different value (or a different type) is double-quoted. `_emit_code()` shares the same logic. Values that were already emitted bare are unchanged, so existing `nav.yml` files do not churn.

---

### `mdcms config` silently deletes `nav.yml` contents when the file is unparseable

**Symptom:** Adding a section, changing a sort order, or setting a parent through `mdcms config` → Manage sections wiped every other section and every page entry out of `nav.yml`, leaving only the section just edited. The menu had shown "(none yet)" beforehand, with no indication anything was wrong.

**Root cause:** The section editors read the file with `read_nav_yml()`, which deliberately degrades to an empty nav on a parse error so `mdcms build` can recover (it regenerates page entries from disk anyway). The editors do not regenerate anything — they write back what they read — so an empty read plus a save meant deletion. The `warning` field `read_nav_yml()` returns for exactly this case was never surfaced.

**Fix:** Added `read_nav_yml_for_edit()`, which raises instead of returning an empty nav, and switched every section editor to it. `mdcms config`'s summary now prints `sections: unreadable — <reason>` rather than `sections: 0`, and the Manage sections menu reports the error and returns instead of offering to edit a file it cannot read.

---

### A page's frontmatter `sort:` is ignored once it is in `nav.yml`

**Symptom:** Changing a page's `sort:` — in the markdown file or through `mdcms config` → Manage pages → Edit a page — and rebuilding left the page exactly where it was in the nav. The frontmatter showed the new value; `nav.yml` kept the old one indefinitely.

**Root cause:** `build_page_nav()` computed `sort = existing.get("sort") or primary.get("sort") or 100`, preferring whatever was already in `nav.yml`. Since the first build writes the frontmatter value there, that value was pinned forever. This contradicts `docs/reference-nav.md`, which states that page `title`, `sort` and `section-id` "are always taken from frontmatter".

**Fix:** The order is reversed — `primary.get("sort") or existing.get("sort") or 100`. The `nav.yml` value now only applies to pages that declare no `sort:` at all.

---

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

---

## Open bugs

### `mdcms fetch-deps` crashes immediately (`NameError`)

**Symptom:** Running `mdcms fetch-deps [name]` or `mdcms fetch-deps --path <path>` aborts with `NameError: name 'CDN_DEPS' is not defined`. The offline-bundling command is completely non-functional.

**Root cause:** `fetch_deps()` in `mdcms.py` references three names — `CDN_DEPS`, `_fetch_bunny_fonts()`, and `_patch_index_html()` — that are used but never defined anywhere in the module. They appear to have been dropped (or never landed) when the command was added.

**Fix (not yet done):** Reintroduce a `CDN_DEPS` list mapping each CDN URL in `app/index.html` (js-yaml, marked, fuse.js, highlight.js + its two stylesheets) to a local `assets/required/vendors/` path, plus `_fetch_bunny_fonts()` (download Bunny Font CSS + font files referenced by `theme.yml`) and `_patch_index_html()` (rewrite the CDN `<script>`/`<link>` URLs and injected Bunny `@font-face` URLs to the local copies). Until then, offline bundling must be done by hand.
