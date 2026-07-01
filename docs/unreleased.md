# Unreleased changes

Changes merged into `development` that have not yet been released to `main`.

---

## Tabs & Accordions (`app/index.html`)

Four new `mdcms` fenced-block types for rich content layout. All four variants read from the active theme automatically — no new config keys, no per-theme overrides needed.

### Block types

| Language tag | Alias for | Renders as |
|---|---|---|
| `tab-underline` | — | Tab strip, active tab marked with underline |
| `tab` | `tab-underline` | (same) |
| `tab-filled` | — | Tab strip, tabs as filled chips |
| `accordion-underline` | — | Stacked accordion, header underline style |
| `accordion` | `accordion-underline` | (same) |
| `accordion-filled` | — | Stacked accordion, filled card style |

### Authoring syntax

Open a fenced block with the language tag `mdcms <type>`. The body is YAML with a single top-level key `items:`, whose value is a list of item objects.

~~~markdown
```mdcms tab-underline
items:
  - title: Install
    default: selected
    content: |
      Install with `npm i mdcms` or `pnpm add mdcms`.
  - title: Configure
    content: |
      Drop a `mdcms.config.yaml` next to your content folder.
  - title: Deploy
    content: |
      Any static host. The build emits plain HTML.
```
~~~

### Per-item keys

| Key | Required | Type | Notes |
|---|---|---|---|
| `title` | yes | plain string | Label shown on the tab button or accordion header. Plain text only — no Markdown. |
| `content` | yes | Markdown block | Body content. Use the YAML literal block scalar (`\|`) for multi-line Markdown. Rendered with the same pipeline as the surrounding page (GFM, syntax highlighting, internal links). |
| `default` | no | string | **Tabs:** `selected` marks the tab that is open on load; if no item has `selected`, the first item is used. `notselected` (or omitting the key) leaves the tab inactive. Exactly one tab should be `selected`. **Accordions:** `open` makes the item expanded on load; `closed` (or omitting) leaves it collapsed. Any number of accordion items may be `open`. |
| `title-style` | no | string | Heading level for screen readers and external TOC tools. One of `"#"`, `"##"`, `"###"`, `"####"`, `"#####"`, `"######"`, or `""` (default). Visual size is always fixed by the component — this only changes the underlying ARIA role and level. Use a value when you want the item to be picked up as a heading by assistive technology. |

### Examples

**Tabs — underline (default)**

~~~markdown
```mdcms tab
items:
  - title: npm
    default: selected
    content: |
      ```bash
      npm install mdcms
      ```
  - title: pnpm
    content: |
      ```bash
      pnpm add mdcms
      ```
  - title: yarn
    content: |
      ```bash
      yarn add mdcms
      ```
```
~~~

**Tabs — filled chips**

~~~markdown
```mdcms tab-filled
items:
  - title: Overview
    default: selected
    content: |
      MD-CMS is a markdown-based static site system with no build step.
  - title: Features
    content: |
      - Sidebar navigation
      - Full-text search
      - PWA + offline support
      - Dark / light theme
```
~~~

**Accordion — underline (default)**

~~~markdown
```mdcms accordion
items:
  - title: What is MD-CMS?
    default: open
    content: |
      A single-file browser renderer. No build pipeline, no compilation,
      no server required.
  - title: How do I install it?
    content: |
      Run `pip install mdcms` or download a binary from the GitHub releases page.
  - title: Does it work offline?
    content: |
      Yes — run `mdcms fetch-deps` to bundle vendor assets locally, then enable
      `pwa: yes` in `config.yml` for full offline support.
```
~~~

**Accordion — filled cards**

~~~markdown
```mdcms accordion-filled
items:
  - title: Can I use custom themes?
    default: open
    content: |
      Yes. Create a `theme.yml` and reference it with `theme: theme.yml` in
      `config.yml`. The theme controls colours, fonts, and layout.
  - title: title-style example
    title-style: "##"
    content: |
      This header is announced as an `<h2>` to screen readers, even though
      its visual size is set by the accordion component.
```
~~~

### How the appearance adapts to themes

The components derive their fill colours and bar/border colours from the active theme at runtime. No new keys in `config.yml` or `theme.yml` are needed.

**Bold themes** (nav background is visually distinct from the page — e.g. a dark sidebar on a light page, or a coloured nav like red or navy): filled tabs and accordion headers use the nav background colour as their fill; the bar/border uses the nav colour. This makes the components look like an extension of the sidebar chrome.

**Subtle themes** (nav background is almost identical to the page — e.g. both near-white or both near-dark): filled tabs use a light tint of the accent colour; the bar and border use the accent colour directly. This keeps the components visible without a strong nav background to borrow from.

The switch between bold and subtle is automatic. The algorithm uses HSL chroma (`S × (1−|2L−1|)`) rather than raw HSL saturation, which would give false "bold" readings for near-white or near-black nav backgrounds.

---

## `mdcms build` patches `<title>` with sitename

`mdcms build` now rewrites the `<title>` tag in `index.html` with the value of `sitename` from `config.yml`. Previously the tag was hardcoded (`MD-CMS`) in older templates, or blank in the starter template, so link previews in WhatsApp, Slack, and other crawlers that read static HTML showed the wrong name.

---

## Untranslated posts now visible in all categories

**Status:** On `development`, pending release.

### What was broken

When the category system is enabled, a post file without a category suffix (e.g. `posts/my-post.md`) was silently assigned to the default category only. Switching to any other category caused those posts to disappear from the nav and from `posts-*` tag listings — even though no translated version existed. If you wrote posts without a language suffix, they simply vanished the moment a visitor switched category.

Pages without a category suffix are unaffected: they continue to be assigned to the default category, which is the correct behaviour for pages.

### What it does now

Posts without a category suffix are treated as uncategorised — meaning they appear in every category. A post called `my-post.md` now shows up regardless of which category is active. A post called `my-post.en.md` still appears only in the `en` category as before.

Mixed situations work as expected: if you have both `my-post.md` and `my-post.nb.md`, the Norwegian variant is shown when the `nb` category is active, and the bare `my-post.md` is shown for every other category.

### What changes in the build output

After rebuilding a site with `mdcms build`, affected post entries in `nav.yml` gain an `uncategorized: true` field:

```yaml
- file: posts/my-post.md
  title: My Post
  sort: 100
  uncategorized: true
```

In `search.json`, these entries carry `"category": null` instead of the default category code. This is what tells the renderer to include them universally.

A rebuild is required for existing sites to pick up the change.

---

## Fix: category-variant pages fail to load on servers with SPA routing (e.g. Cloudflare Pages)

When a site uses category-suffixed page files (e.g. `page.current.md`) and is hosted on a server configured with SPA fallback routing (serving `index.html` with HTTP 200 for any unknown path), the renderer's `fetchPageFile` mistook the HTML fallback for a found markdown file. It returned `index.html` content instead of falling through to try the `.current.md` variant. The page rendered the raw HTML of `index.html` as markdown, showing the `<title>` text (`sitename`) in the content area.

`fetchPageFile` now checks the `Content-Type` response header and rejects any response with `text/html`, continuing to the next candidate URL instead.

---

## Fix: stale service worker not removed when `pwa: no`

`index.html` unconditionally registers `service-worker.js` on every page load. When a site switched from `pwa: yes` to `pwa: no`, `mdcms build` stopped generating a new service worker, but the old one remained active in browsers that had visited the site before. The stale worker continued to serve cached responses from the old build.

`mdcms build` now writes a self-unregistering `service-worker.js` when `pwa: no`. On the visitor's next page load, the browser installs this stub worker, which immediately unregisters itself and evicts any previously cached content. `manifest.json` is also removed if present.

---

## Manifest-driven download and URL-based register (`mdcms.py`, `app/mdcms.json`)

`mdcms build` now writes `mdcms.json` to the site root on every build. `mdcms register` can accept a GitHub repo URL or a plain HTTPS URL as the source to download from.

### `mdcms build` writes `mdcms.json`

At the end of each build, `generate_site_manifest()` walks the site directory, lists every non-hidden file (excluding `mdcms.json` itself), records any empty directories, and writes `mdcms.json`. This file is deployed alongside the rest of the site — it is the machine-readable index of what the site contains.

Format:

```json
{
  "mdcms": "0.4",
  "files": ["index.html", "config.yml", "assets/icons/add.svg", ...],
  "dirs":  ["assets/fonts", "posts"]
}
```

`files` — all deployable files, paths relative to the site root.  
`dirs` — empty directories to create on download (no file needed to keep them alive).

### `mdcms register` accepts URLs

`PATH` can now be a GitHub repo URL or a plain HTTPS URL pointing to a deployed mdcms site. A `--from URL` option is also available as an explicit override.

```
mdcms register mysite                                        # existing behaviour
mdcms register mysite ./mydir                                # local path
mdcms register mysite https://github.com/owner/repo          # GitHub repo
mdcms register mysite https://github.com/owner/repo/tree/main/subdir
mdcms register mysite --from https://example.com/mysite      # deployed site
```

**GitHub URL** — tries `mdcms.json` from the raw content URL first; falls back to the GitHub Contents API tree-walk if no manifest is found.  
**Plain HTTPS URL** — fetches `{url}/mdcms.json`; if not found, reports an error with guidance.

### `app/mdcms.json`

The starter template now ships with its own `mdcms.json`. This means `mdcms register mysite https://github.com/kbenestad/mdcms/tree/main/app` works via the manifest path with no API calls.

### `_http_get` / `_http_get_github`

`_http_get(url)` — generic SSL-verified GET, no vendor headers. Used for raw file downloads and manifest fetches.  
`_http_get_github(url)` — adds `Accept: application/vnd.github.v3+json` for Contents API responses (only needed in the fallback tree-walk path).

---

## Clean URLs for section-id pages (`app/index.html`, `app/404.html`)

Pages whose filename matches a nav section-id can now be accessed at a clean URL path (e.g. `example.com/timesheet`) instead of the hash-based URL (`example.com/#pages/timesheet.md`).

### How it works

When you navigate to a page whose base filename (`timesheet`) matches a `code` entry in the `sections:` block of `nav.yml`, the renderer uses `history.replaceState` to rewrite the URL from `/#pages/timesheet.md` to `/timesheet`. All other pages continue to use hash-based URLs unchanged.

On startup, if the URL pathname already contains a section-id slug (because the user typed or was linked to `example.com/timesheet` directly), the renderer detects it, sets the correct base path, and loads the matching page.

Subpath deployments (e.g. `example.com/mysite/`) are handled automatically: the renderer determines the base from the initial pathname.

### 404.html for GitHub Pages

A new `app/404.html` file enables direct clean-URL access on GitHub Pages. When GitHub Pages serves the 404 page for an unknown path (e.g. `/timesheet`), `404.html` encodes the path as `?_route=/timesheet` and redirects to the app root. `index.html` reads `_route`, cleans up the URL, and routes to the right page. For other static hosts (Netlify, Cloudflare Pages, etc.) a `/*` → `/index.html` rewrite rule in the host's config achieves the same result.

### Condition

Only pages files that are both:
1. located in `pages/` with a name matching a section `code` in `nav.yml`, and
2. present in the `pages:` list in `nav.yml`

…get a clean URL. All other pages continue to use `#` routing.

---

## Fix: `config.yml` YAML parse errors now abort the build with a clear message

A malformed `config.yml` (e.g. a stray tab character, which YAML forbids as a token starter) previously caused `read_config` to silently return an empty dict. The build would proceed with no config — categories disabled, no default category code — producing a broken `nav.yml` with wrong filenames and missing `variants` fields, so category-variant pages would not appear in the sidebar.

`read_config` now raises `ClickException` on both `OSError` and `yaml.YAMLError`, aborting the build with a descriptive error message instead of continuing silently with an empty config.
