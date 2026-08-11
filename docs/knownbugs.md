# Known bugs

Every bug found in MD-CMS, open or fixed, with its symptom, root cause, and fix. Open bugs come first; fixed ones are kept below, grouped by the release that shipped the fix, so the history of what went wrong and why stays searchable.

**Keep this file current in the same commit as the change it describes:**

- **A bug is found** → add an entry under *Open bugs* with **Symptom**, **Root cause** (if known), and **Fix (not yet done)**.
- **A bug is fixed** → move its entry to *Fixed in development (not yet released)*, rewrite **Fix** to describe what actually changed, and add the matching line to `docs/unreleased.md`.
- **A release goes out** → retitle that section to *Fixed in vX.Y.Z* and open a fresh empty *Fixed in development* section above it, at the same time `docs/unreleased.md` is cleared.

---

## Open bugs

### `mdcms fetch-deps` crashes immediately (`NameError`)

**Symptom:** Running `mdcms fetch-deps [name]` or `mdcms fetch-deps --path <path>` aborts with `NameError: name 'CDN_DEPS' is not defined`. The offline-bundling command is completely non-functional.

**Root cause:** `fetch_deps()` in `mdcms.py` references three names — `CDN_DEPS`, `_fetch_bunny_fonts()`, and `_patch_index_html()` — that are used but never defined anywhere in the module. They appear to have been dropped (or never landed) when the command was added.

**Fix (not yet done):** Reintroduce a `CDN_DEPS` list mapping each CDN URL in `app/index.html` (js-yaml, marked, fuse.js, highlight.js + its two stylesheets) to a local `assets/required/vendors/` path, plus `_fetch_bunny_fonts()` (download Bunny Font CSS + font files referenced by `theme.yml`) and `_patch_index_html()` (rewrite the CDN `<script>`/`<link>` URLs and injected Bunny `@font-face` URLs to the local copies). Until then, offline bundling must be done by hand.

---

## Fixed in development (not yet released)

_Nothing awaiting release._

---

## Fixed in v0.9.0

### A missing icon file renders `[missing: foo.svg]` text inside the button

**Symptom:** A UI control — the sidebar panel-close button, the theme toggle, a nav section chevron — shows bracketed placeholder text where its glyph should be, which reads as a rendering bug rather than as a missing file.

**Root cause:** When `loadIcon()` cannot fetch an icon, `iconEl()` falls back to an `<img>` pointing at the same path with `alt="[missing: <filename>.svg]"`. Browsers render a broken image's `alt` text, so the placeholder string is drawn inside the button — typically a 2rem box, so it also overflows or clips. The `alt` was meant as a developer hint, but it surfaces in the UI of every visitor rather than to the person who can fix it.

**Fix:** `iconEl()` now emits the fallback `<img>` with `alt=""`, so a genuinely missing file renders as empty space instead of text, and logs `[mdcms] icon not found: assets/icons/<filename>` to the console once per icon (tracked in a `warnedIcons` set) so the diagnostic is still available where it is useful. The `<img>` itself is kept: when the preload fetch failed but the file exists, it still displays.

---

### Code-fence copy button renders `[missing: content_copy.svg]` instead of an icon

**Symptom:** On a site running the new renderer, the copy button in the corner of a code fence shows broken-image placeholder text rather than a copy glyph. `mdcms build` on such a site also prints `Warning: could not download icon 'content_copy.svg'`.

**Root cause:** The copy button was first built on the shared icon system, with `content_copy` and `check` added to `CORE_ICONS`. Those two `.svg` files only existed on `development`, but `sync_icons()` downloads from `TEMPLATE_BASE_URL`, which points at `main` — so for anyone not running the CLI from a repo checkout (where `_local_repo_root()` short-circuits the download) the fetch 404s and the files never land in `assets/icons/`. `iconEl()` then falls back to an `<img>` whose `alt` is the `[missing: …]` text. The same gap would reopen for any site that picks up a new `index.html` via `mdcms update` without running `mdcms build` afterwards, since `update` does not sync icons.

**Fix:** The copy button no longer uses the icon system. Its two glyphs are inlined in `app/index.html` as the `COPY_SVG` and `CHECK_SVG` constants — the pattern the accordion chevron (`CHEVRON_SVG`) and the scroll-top arrow already use — so the button is self-contained in the renderer and cannot render a placeholder. `content_copy`/`check` were removed from `CORE_ICONS` in both `mdcms.py` and `index.html`, and the two `.svg` files were dropped from `app/assets/icons/` and the sample sites, leaving the icon pack and `app/mdcms.json` exactly as they were before the feature. Both names were added to `LEGACY_ICONS` so `mdcms build` sweeps them out of any site that built against the interim version — unless the site references one by name (e.g. as `categories-selecticon`), in which case it counts as a custom icon and is kept.

---

## Fixed in v0.8.3

### `mdcms register` aborts with HTTP 404 on every new site

**Symptom:** `mdcms register <name>` printed the first few template files and then died with `Error: Download failed: HTTP Error 404: Not Found`, stopping at `assets/icons/dangerous.svg`. No site was registered and the target directory was left half-populated. Every new site was affected, on every platform.

**Root cause:** `app/mdcms.json` — the manifest `register` downloads the starter template by, read straight off `main` — had drifted from the actual contents of `app/`. It is a checked-in static list, and nothing regenerated it when the template's file list changed: it still named the six icons dropped when the stock pack was trimmed (`dangerous`, `exclamation`, `history`, `mobile_arrow_down`, `report`, `text_compare`) and was missing the four panel icons added since (`left_panel_close`, `left_panel_open`, `right_panel_close`, `right_panel_open`). `_apply_manifest()` fetched every listed file with no tolerance for one being absent, so the first dead entry aborted the whole download — and had the download survived, the new site would have been missing the panel-toggle icons the renderer lists in `CORE_ICONS`.

**Fix:** Three parts. `app/mdcms.json` was regenerated from the real `app/` tree. The release workflow's `publish` job now regenerates it (via `generate_site_manifest()`) and commits it alongside the version bump, so it cannot go stale again. And `_apply_manifest()` no longer treats a missing file as fatal: an entry that 404s is skipped, the skipped names are reported in a warning at the end, and the site is still created. `index.html` and `config.yml` (`ESSENTIAL_TEMPLATE_FILES`) remain fatal, as do network errors and any non-404 HTTP status.

---

## Fixed in v0.8.2

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

## Fixed in v0.6.7

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
