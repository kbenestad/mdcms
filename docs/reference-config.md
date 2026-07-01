# config.yml reference

`config.yml` is the site configuration file. Only `sitename` and `navigation` are required — everything else is optional. `mdcms build` reads this file; so does `index.html` at runtime.

The first line must not be changed:

```yaml
# mdcms v0.4 | DO NOT REMOVE THIS COMMENT
```

---

## Required

```yaml
sitename: My Site              # Displayed in the browser tab, nav header, and meta tags.
navigation: sidebar            # Layout mode. sidebar or topbar. NOTE: topbar is currently broken — always use sidebar.
```

---

## Presentation

```yaml
theme: theme.yml               # Path to theme file (relative to site root). Controls colours, fonts, layout.
                               # Omit to use built-in defaults.

logo: logo.png                 # Filename in assets/images/. Shown in the nav header above the site name.
favicon: favicon.png           # Filename in assets/images/. Shown in the browser tab.
                               # Falls back to logo if not set. Required for PWA install icons.

sitedescription: A short description   # Shown below the site name in the sidebar.
                                       # Also used as the default meta description tag.

footer: "© 2026 Your Name"     # Shown at the bottom of the nav. Supports inline markdown (bold, links, etc.).
```

---

## Navigation

```yaml
homepage: pages/home.md        # Override the default landing page. Path relative to site root.
                               # Default: pages/home.md

nav-position: left             # Sidebar position. left or right. Default: left.
                               # Only applies when navigation: sidebar.

search: true                   # Show the search box. Set to false to hide it.
                               # Default: true (search is on unless explicitly disabled).
```

---

## Theme mode

```yaml
default-theme: system          # Starting colour mode. light, dark, or system.
                               # system follows the user's OS preference.
                               # Default: system.
```

---

## Layout overrides

These can also be set in theme.yml. Values here apply on top of theme.yml.

```yaml
main-width: 80em               # Maximum width of the content column. Any CSS length unit.
nav-width: 20em                # Width of the sidebar. Any CSS length unit.
```

---

## Typography overrides

These can also be set in theme.yml. Values here apply on top of theme.yml.

```yaml
font-body: "bunny:Noto Sans:400"      # Body font. Format: "provider:Font Name:weight"
font-title: "bunny:Noto Sans:700"     # Heading font.
font-code: "bunny:Fira Code:400"      # Code font.
```

Provider options: `bunny` (GDPR-safe) or `google`. Omitting the provider defaults to Bunny Fonts.

---

## Localisation

```yaml
language: en                   # BCP 47 language code. Used for date formatting fallback.

date: system                   # Date format for post dates. system uses the browser locale.
                               # Or provide a format string, e.g. DD.MM.YYYY

time: system                   # Time format. system uses the browser locale.

monthnames: January, February, March, April, May, June, July, August, September, October, November, December
                               # Override month names (comma-separated, 12 values).

monthnamesabbreviated: Jan, Feb, Mar, Apr, May, Jun, Jul, Aug, Sep, Oct, Nov, Dec
                               # Override abbreviated month names (comma-separated, 12 values).

pagenotfoundmessage: "Page not found."   # Message shown when a page cannot be loaded.
```

---

## PWA (Progressive Web App)

`mdcms build` generates `manifest.json` and `service-worker.js` when `pwa: yes`.

```yaml
pwa: yes                       # Enable PWA. Generates manifest.json and service-worker.js on build.

pwa-name: "My Site"            # Full app name shown on the install prompt and splash screen.
                               # Required when pwa: yes.

pwa-shortname: "MySite"        # Short name for home screen icon labels (keep under ~12 chars).
                               # Falls back to pwa-name if omitted.

pwa-colour: "#2563EB"          # Browser chrome colour (address bar on Android Chrome).

offline-message: "You are offline. Connect and reload."
                               # Shown when a page cannot be fetched and no cached version exists.
                               # Supports per-language values (see below).
```

Multi-language offline message:

```yaml
offline-message:
  en: "You are offline. Connect and reload."
  nb: "Du er frakoblet. Koble til og last inn på nytt."
```

The renderer picks the entry matching the active category's language, then falls back to `en`, then the first entry.

Requires a `favicon.png` (192×192 px recommended) at `assets/images/favicon.png` for the PWA install icon.

---

## Categories

Categories allow one site to serve multiple language or audience variants of the same content. Each page can have a variant per category using the filename suffix convention (`page.nb.md` for Norwegian).

```yaml
categories-use: yes            # Enable the category system. Default: no.

default-category:              # The category used when no ?cat= parameter is in the URL.
  code: en                     # Short code. Used in filenames (page.en.md) and URL params.
  name: English                # Display name shown in the category dropdown list.
  message: English             # Label shown on the selector bar (trigger button). Falls back to name.
  name-latin: English          # Secondary label shown in the dropdown alongside name. Use when name
                               # is in a non-Latin script (e.g. Arabic, Devanagari) to aid recognition.
                               # Omit if name is already Latin or identical to name.
  direction: ltr               # Text direction. ltr or rtl. Default: ltr.
                               # rtl flips the nav position and content text direction.
  notfoundmessage: "Not available in this language"
                               # Short note shown in the dropdown when no variant exists for the
                               # current page. Also enables fallback: the renderer will fall back to
                               # the default-category content instead of hiding the page.
                               # Omit to hide the category from the dropdown when no variant exists.
  visibilityifnocontent: hidden  # hidden (default) or visible.
                               # hidden: category disappears from the selector when no variant exists
                               #   for the current page (unless notfoundmessage is also set).
                               # visible: category stays in the selector regardless. When the user
                               #   navigates to a page with no variant, pagenotfoundmessage is shown
                               #   in the content area. No fallback to default-category content.
  pagenotfoundmessage: "This page is not yet available in English."
                               # Message shown in the content area when a page cannot be fetched for
                               # this category. Overrides the top-level pagenotfoundmessage.
  font: NotoNastaliqUrdu-Regular.ttf
                               # Font filename inside assets/fonts/. Loaded on demand when this
                               # category is activated. Useful for scripts that need a specific font.
  line-height: 2.8             # Line height override for this category. Useful for scripts like
                               # Nastaliq that need extra vertical space. Restores to theme default
                               # when switching away.

categories:                    # Additional categories. Each entry supports the same keys as
                               # default-category above.
  - code: nb
    name: Norsk
    direction: ltr
  - code: ar
    name: عربي
    name-latin: Arabic
    direction: rtl
    notfoundmessage: "غير متاح"
    font: NotoNastaliqUrdu-Regular.ttf
    line-height: 2.8

categories-sectionnames: same  # How section names are shown per category.
                               # same: all categories share one section name (defaultname in nav.yml).
                               # per-category: each section has a name per category (categorynames in nav.yml).

categories-selecticon: globe   # Icon shown in the category selector bar. SVG name from assets/icons/.
categories-selecttext: "Language"  # Label shown next to the icon in the category selector bar.
```

### Per-category keys summary

| Key | Required | Description |
|---|---|---|
| `code` | Yes | Short identifier used in filenames (`page.nb.md`) and the `?cat=` URL param. |
| `name` | Yes | Display name shown in the dropdown list. |
| `message` | No | Label shown on the selector trigger button. Falls back to `name`. |
| `name-latin` | No | Secondary label in the dropdown, shown alongside `name` when `name` uses a non-Latin script. |
| `direction` | No | `ltr` or `rtl`. Default: `ltr`. RTL flips nav and content direction. |
| `notfoundmessage` | No | Short note shown in the dropdown when no variant exists for the current page. Also enables fallback to default-category content. |
| `visibilityifnocontent` | No | `hidden` (default) or `visible`. `visible` keeps the category in the selector when no variant exists; navigating to it shows `pagenotfoundmessage` with no fallback to default content. |
| `pagenotfoundmessage` | No | Message shown in the content area when a page cannot be fetched for this category. Overrides the top-level `pagenotfoundmessage`. |
| `font` | No | Font filename from `assets/fonts/`. Loaded on demand when this category is activated. |
| `line-height` | No | Body line height override for this category. Restores to theme default when switching away. |

---

## Reusable callout messages

Define named messages in config.yml and reference them in markdown with `message: <key>`. Useful for standard notices (e.g. AI translation warnings) used across many pages.

```yaml
callouts:
  aitranslation:               # Key name — used as message: aitranslation in markdown.
    type: warning              # Callout type: info, warning, success, error.
    en:
      title: "PLEASE NOTE:"
      text: This page has been translated with artificial intelligence.
    nb:
      title: "VENNLIGST MERK:"
      text: Denne siden er maskinoversatt.
```

Usage in a markdown page:

````markdown
```mdcms
callout-warning
message: aitranslation
```
````

---

## Full example

```yaml
# mdcms v0.4 | DO NOT REMOVE THIS COMMENT
# MD-CMS v0.4 — Site configuration

sitename: My Documentation
navigation: sidebar
theme: theme.yml

logo: logo.png
favicon: favicon.png
sitedescription: Reference documentation for My Project
footer: "© 2026 My Name — [Apache 2.0](https://www.apache.org/licenses/LICENSE-2.0)"

homepage: pages/home.md
nav-position: left
search: true
default-theme: system

pwa: yes
pwa-name: "My Documentation"
pwa-shortname: "MyDocs"
pwa-colour: "#2563EB"
offline-message:
  en: "You are offline. Connect to the internet and reload."
  nb: "Du er frakoblet. Koble til og last inn på nytt."

language: en
pagenotfoundmessage: "Please select a page to continue."

categories-use: yes
default-category:
  code: en
  name: English
  direction: ltr
categories:
  - code: nb
    name: Norsk
    direction: ltr
    visibilityifnocontent: visible
    pagenotfoundmessage: "Denne siden er ikke tilgjengelig på norsk ennå."
  - code: ar
    name: عربي
    name-latin: Arabic
    direction: rtl
    notfoundmessage: "غير متاح"
    pagenotfoundmessage: "هذه الصفحة غير متاحة."
    font: NotoNastaliqUrdu-Regular.ttf
    line-height: 2.8
categories-sectionnames: same
categories-selecticon: globe
categories-selecttext: "Language"

callouts:
  aitranslation:
    type: warning
    en:
      title: "PLEASE NOTE:"
      text: This page has been translated with artificial intelligence. It has not been reviewed by staff.
    nb:
      title: "VENNLIGST MERK:"
      text: Denne siden er maskinoversatt og ikke gjennomgått av redaksjonen.
```
