# theme.yml reference

`theme.yml` controls the visual presentation of your site. It is separate from `config.yml` so you can update colours and fonts without touching site settings, and vice versa. `index.html` loads it at runtime — no build step required.

Point `config.yml` at it with:

```yaml
theme: theme.yml
```

---

## Colours — the palette

Colours are declared under a single `palette:` key with `light:` and `dark:` blocks. Both blocks use the **same fixed, neutral token names** — only the values differ. mdcms switches between them based on the user's system preference or the theme toggle. Every token maps to one or more rendered features (the mapping lives in the renderer, not the theme).

### Core tokens (required)

```yaml
palette:
  light:
    primary: "#2563EB"      # Brand colour — headings, content links, active nav, tab underline, focus rings.
    surface: "#F8FAFC"      # Nav / panel background (sidebar or topbar).
    page: "#FFFFFF"         # Page (content) background.
    ink: "#1E293B"          # Body text.
    ink-muted: "#64748B"    # Secondary text — descriptions, timestamps, captions.
  dark:
    primary: "#60A5FA"
    surface: "#1E293B"
    page: "#0F172A"
    ink: "#F1F5F9"
    ink-muted: "#94A3B8"
```

All values are CSS colour strings (hex, `rgb()`, `hsl()`, named colours, `rgba()`).

The relationship between these three tells you the theme's style:

- `surface` **≈** `page` → subtle nav that blends into the page (`primary` carries the look).
- `surface` a distinct colour → a two-tone theme (a separate nav surface + `primary` accent).
- `surface` **==** `primary` → a single bold colour drives both the nav and the accent.

### Nav-on-surface tokens (optional)

These colour the text/controls **inside** the nav surface. Omit the whole group when `surface` is a neutral near-white or near-black — the defaults (derived from `ink` / `primary`) are legible. Set them when `surface` is a strong/dark/brand colour. Set the group together.

```yaml
palette:
  light:
    on-surface: "#1E293B"         # Inactive nav link text.
    on-surface-active: "#2563EB"  # Active (current page) nav link.
    on-surface-title: "#1E293B"   # Site name in the nav header.
    on-surface-heading: "#64748B" # Section-heading labels (uppercase, small).
    on-surface-note: "#64748B"    # Site description below the title.
    on-surface-icon: "#64748B"    # Dark/light toggle button.
    # divider: "#CBD5E1"          # Borders / rules. Omit to auto-derive: color-mix(page 85%, ink).
```

The same tokens apply in the `dark:` block.

**When `surface` is a bold colour** (brand red, navy, deep green), a common pattern is white (`#FFFFFF`) for `on-surface-active` / `on-surface-title` and a semi-transparent white (e.g. `rgba(255,255,255,0.65)`) for `on-surface-heading` / `on-surface-note` / `on-surface-icon`.

### Token → feature reference

| Token | Feature(s) it colours |
|---|---|
| `primary` | headings, content links, active nav item, tab underline / accordion bar (subtle nav), table-header tint, focus rings |
| `surface` | nav / panel background; filled tab & accordion surface (bold nav) |
| `page` | page background, search field background |
| `ink` | body text, code text |
| `ink-muted` | muted text; nav headings/description (unless `on-surface-*` set) |
| `on-surface` | inactive nav link |
| `on-surface-active` | active nav link |
| `on-surface-title` | site name in nav header |
| `on-surface-heading` | nav section-heading labels |
| `on-surface-note` | site description |
| `on-surface-icon` | theme toggle |
| `divider` | borders / rules (auto-derived if omitted) |

---

## Semantic colours

Used by callout tags (`callout-info`, `callout-warning`, `callout-success`, `callout-error`). `colours-semantic` applies to both modes. `colours-semantic-dark` overrides for dark mode only — use lighter, more luminous variants so callout borders and tinted backgrounds remain legible on dark page backgrounds.

```yaml
colours-semantic:
  info: "#2563EB"
  warning: "#D97706"
  success: "#16A34A"
  error: "#DC2626"

colours-semantic-dark:
  info: "#60A5FA"      # Lighter blue — visible on dark background
  warning: "#F59E0B"
  success: "#34D399"
  error: "#F87171"
```

If `colours-semantic-dark` is omitted, the `colours-semantic` values are used in both modes.

---

## Callout defaults

Overrides the icon and colour used for each callout type. `primary-colour` sets the left border; `background-colour` sets the tinted background fill (applied at ~8% opacity by the renderer).

```yaml
callouts:
  info:
    icon: info                    # SVG icon name from assets/icons/ (without .svg)
    primary-colour: "#2563EB"     # Left border colour
    background-colour: "#2563EB"  # Background tint colour

  warning:
    icon: warning
    primary-colour: "#D97706"
    background-colour: "#D97706"

  success:
    icon: success
    primary-colour: "#16A34A"
    background-colour: "#16A34A"

  error:
    icon: error
    primary-colour: "#DC2626"
    background-colour: "#DC2626"
```

Individual callout blocks in markdown can override the icon with `icon: <name>`.

---

## Nav section toggle icons

Sections with `pagesvisibility: hidden` in `nav.yml` are collapsible. These two top-level keys (not inside `light:`/`dark:`) set the icons used for the toggle.

```yaml
nav-section-expand-icon: arrow_right       # Shown when section is collapsed. Default: arrow_right.
nav-section-collapse-icon: arrow_drop_down # Shown when section is expanded. Default: arrow_drop_down.
```

Available icon names:

| Expand | Collapse | Style |
|---|---|---|
| `arrow_right` | `arrow_drop_down` | Solid filled triangles (default) |
| `keyboard_arrow_right` | `keyboard_arrow_down` | Chevrons — lighter, more modern |
| `keyboard_double_arrow_right` | `keyboard_double_arrow_down` | Double chevrons — emphatic |
| `expand_content` | `collapse_content` | Corner arrows — editorial |
| `add` | `minimize` | Plus / minus — minimal |

The two keys are independent — expand and collapse do not have to use icons from the same pair, though keeping a consistent visual weight reads better.

---

## Typography

Font format: `"provider:Font Name:weight"`

- `provider`: `bunny` (privacy-friendly, GDPR-safe) or `google`
- `Font Name`: exact font family name as listed on the font provider
- `weight`: numeric CSS weight (`400`, `700`, etc.)

```yaml
font-body: "bunny:Noto Sans:400"      # Body text font
font-heading: "bunny:Noto Sans:700"   # Headings (h1–h6) font
font-code: "bunny:Fira Code:400"      # Code blocks and inline code
```

System fonts (no external request):

```yaml
font-body: "system-ui:400"
```

Shorthand without provider defaults to Bunny Fonts:

```yaml
font-body: "Noto Sans:400"    # equivalent to bunny:Noto Sans:400
```

Size and spacing:

```yaml
font-size: 1.0      # Unitless multiplier. 1.0 = 16px base. 1.125 = 18px.
line-height: 1.7    # Unitless multiplier for body text line spacing.
```

---

## Layout

```yaml
main-width: 80em    # Maximum width of the content column. Any CSS length unit.
nav-width: 20em     # Width of the sidebar. Any CSS length unit.
```

---

## Full example

```yaml
# mdcms v0.4 | DO NOT REMOVE THIS COMMENT
# MD-CMS v0.4 — Theme configuration

light:
  accent: "#2563EB"
  background: "#FFFFFF"
  nav-background: "#F8FAFC"
  text: "#1E293B"
  text-muted: "#64748B"
  # nav-link, nav-link-active, nav-section-heading, nav-sitename,
  # nav-description, nav-toggle — omit when nav-background is neutral.
  # divider — omit to auto-derive from background + text.

dark:
  accent: "#60A5FA"
  background: "#0F172A"
  nav-background: "#1E293B"
  text: "#F1F5F9"
  text-muted: "#94A3B8"

colours-semantic:
  info: "#2563EB"
  warning: "#D97706"
  success: "#16A34A"
  error: "#DC2626"

colours-semantic-dark:
  info: "#60A5FA"
  warning: "#F59E0B"
  success: "#34D399"
  error: "#F87171"

callouts:
  info:
    icon: info
    primary-colour: "#2563EB"
    background-colour: "#2563EB"
  warning:
    icon: warning
    primary-colour: "#D97706"
    background-colour: "#D97706"
  success:
    icon: success
    primary-colour: "#16A34A"
    background-colour: "#16A34A"
  error:
    icon: error
    primary-colour: "#DC2626"
    background-colour: "#DC2626"

# nav-section-expand-icon: arrow_right
# nav-section-collapse-icon: arrow_drop_down

font-body: "bunny:Noto Sans:400"
font-heading: "bunny:Noto Sans:700"
font-code: "bunny:Fira Code:400"
font-size: 1.0
line-height: 1.7

main-width: 80em
nav-width: 20em
```

---

## Bold nav background example

When `nav-background` matches or is close to `accent`, set all nav colour keys explicitly:

```yaml
light:
  accent: "#D00C33"
  background: "#FFFFFF"
  nav-background: "#D00C33"
  text: "#1A1A1A"
  text-muted: "#5C5C5C"
  nav-link: "#FFFFFF"
  nav-link-active: "#FFFFFF"
  nav-section-heading: "rgba(255,255,255,0.65)"
  nav-sitename: "#FFFFFF"
  nav-description: "rgba(255,255,255,0.65)"
  nav-toggle: "rgba(255,255,255,0.65)"

dark:
  accent: "#D00C33"
  background: "#0A0A0A"
  nav-background: "#000000"
  text: "#FFFFFF"
  text-muted: "#A89090"
  nav-link: "#E2E2E2"
  nav-link-active: "#FFFFFF"
  nav-section-heading: "#888888"
  nav-sitename: "#FFFFFF"
  nav-description: "#888888"
  nav-toggle: "#888888"

colours-semantic:
  info: "#D00C33"
  warning: "#B26A1F"
  success: "#2F7A4A"
  error: "#D00C33"

colours-semantic-dark:
  info: "#FF6B6B"
  warning: "#F59E0B"
  success: "#34D399"
  error: "#FF6B6B"
```
