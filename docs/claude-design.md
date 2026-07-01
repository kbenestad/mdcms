# mdcms theme authoring guide for Claude Design

This document explains the `theme.yml` format so that Claude Design can produce
complete, correct theme files that render well in all nav configurations and in
both light and dark mode.

---

## Full theme.yml structure

```yaml
# mdcms v0.4 | DO NOT REMOVE THIS COMMENT
# mdcms theme — <theme name>

# ──────────────────────────────────
# Colours
# ──────────────────────────────────
light:
  accent: "#2563EB"           # brand colour; used for links, active nav border, accents
  background: "#FFFFFF"       # main content area background
  nav-background: "#F8FAFC"   # sidebar/nav panel background
  text: "#1E293B"             # body text
  text-muted: "#64748B"       # secondary text, captions
  nav-link: "#1E293B"           # inactive nav link text
  nav-link-active: "#2563EB"    # active (current page) nav link text
  nav-section-heading: "#64748B"  # nav section label text (uppercase, small)
  nav-sitename: "#1E293B"       # site name in sidebar header
  nav-description: "#64748B"    # site description below the site name
  nav-toggle: "#64748B"         # dark/light mode toggle button
  # divider: "#CBD5E1"          # omit to auto-derive via color-mix(background, text)

dark:
  accent: "#60A5FA"
  background: "#0F172A"
  nav-background: "#1E293B"
  text: "#F1F5F9"
  text-muted: "#94A3B8"
  nav-link: "#E2E8F0"
  nav-link-active: "#60A5FA"
  nav-section-heading: "#94A3B8"
  nav-sitename: "#E2E8F0"
  nav-description: "#94A3B8"
  nav-toggle: "#94A3B8"
  # divider: "#334155"          # omit to auto-derive via color-mix(background, text)

# ──────────────────────────────────
# Semantic colours
# colours-semantic applies to both modes.
# colours-semantic-dark overrides for dark mode only.
# ──────────────────────────────────
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

# ──────────────────────────────────
# Callout defaults
# primary-colour  → left border and icon
# background-colour → tinted background (rendered at ~8% opacity)
# ──────────────────────────────────
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

# ──────────────────────────────────
# Typography
# Format: "provider:Font Name:weight"  (provider: bunny | google)
# ──────────────────────────────────
font-body: "bunny:IBM Plex Sans:400"
font-heading: "bunny:IBM Plex Sans:700"
font-size: 1.0        # unitless multiplier (1.0 = 16px base)
line-height: 1.7      # unitless multiplier

# ──────────────────────────────────
# Nav section toggle icons
# expand-icon: shown when section is collapsed
# collapse-icon: shown when section is expanded
# ──────────────────────────────────
nav-section-expand-icon: arrow_right       # default
nav-section-collapse-icon: arrow_drop_down # default

# ──────────────────────────────────
# Layout
# ──────────────────────────────────
main-width: 80em
nav-width: 20em
```

---

## Nav section toggle icons

Sections with `pagesvisibility: hidden` in `nav.yml` are collapsible. The
expand and collapse icons are set independently at the top level of `theme.yml`
(not inside `light:` or `dark:` — they are not per-mode).

| Key | Default | Shown when |
|---|---|---|
| `nav-section-expand-icon` | `arrow_right` | section is collapsed |
| `nav-section-collapse-icon` | `arrow_drop_down` | section is expanded |

**Available pairs and their character:**

| Expand icon | Collapse icon | Character |
|---|---|---|
| `arrow_right` | `arrow_drop_down` | Solid filled triangles — compact, classic |
| `keyboard_arrow_right` | `keyboard_arrow_down` | Chevrons (›/˅) — lighter, more modern |
| `keyboard_double_arrow_right` | `keyboard_double_arrow_down` | Double chevrons (»/⌄) — emphatic |
| `expand_content` | `collapse_content` | Corner-arrows — editorial, spatial |
| `add` | `minimize` | Plus/minus — very minimal, utilitarian |

Mix and match freely — the expand and collapse icons do not have to come from
the same pair, but keeping them visually related (same weight and style)
usually reads better.

**Matching icon style to nav style:** bold high-contrast themes (filled
triangle, plus/minus) suit designs with strong typographic weight. Lighter
themes pair better with chevrons. Editorial or magazine-style designs work
well with `expand_content`/`collapse_content`.

---

## Nav colour keys: when to set them

There are six nav colour keys divided into two groups:

**Nav links and labels** — control the navigation list itself:
- `nav-link` — inactive link text (defaults to `text`)
- `nav-link-active` — active/current page link text (defaults to `accent`)
- `nav-section-heading` — uppercase section labels (defaults to `text-muted`)

**Sidebar header elements** — control the branding area above the nav list:
- `nav-sitename` — site name (defaults to `nav-link`)
- `nav-description` — subtitle below the site name (defaults to `nav-section-heading`)
- `nav-toggle` — dark/light mode toggle button (defaults to `nav-section-heading`)

### When the defaults are fine

On themes where `nav-background` is a neutral near-white (light mode) or
near-black (dark mode), `text` and `text-muted` read well against the nav
background. All six keys can be omitted and the fallback chain works correctly.

### When to set the keys explicitly

Set all six keys whenever `nav-background` is anything other than a neutral:
any saturated brand colour (red, navy, forest green, teal), any noticeably
dark sidebar in an otherwise light design, or any light-but-tinted background.

The two groups can be set independently. On a subtly tinted nav where the
link defaults look fine but the site name needs slightly more weight or a
different shade, set only the header keys (`nav-sitename`, `nav-description`,
`nav-toggle`) and leave the nav link keys to their defaults.

**Rule of thumb:** if `nav-background` has saturation above ~20 % or lightness
below 30 % (dark sidebar) or differs from `background` by more than a slight
tint, set all six explicitly for that mode.

### Pattern: accent-coloured nav (e.g. brand red, navy, forest green)

```yaml
light:
  accent: "#D00C33"
  nav-background: "#D00C33"      # same as accent — all nav keys must be set
  nav-link: "#FFFFFF"
  nav-link-active: "#FFFFFF"
  nav-section-heading: "rgba(255,255,255,0.65)"
  nav-sitename: "#FFFFFF"
  nav-description: "rgba(255,255,255,0.65)"
  nav-toggle: "rgba(255,255,255,0.65)"

dark:
  accent: "#D00C33"
  nav-background: "#000000"
  nav-link: "#E2E2E2"
  nav-link-active: "#FFFFFF"
  nav-section-heading: "#888888"
  nav-sitename: "#FFFFFF"
  nav-description: "#888888"
  nav-toggle: "#888888"
```

### Pattern: dark nav in light mode (sidebar darker than content)

```yaml
light:
  nav-background: "#1E293B"
  nav-link: "#CBD5E1"
  nav-link-active: "#FFFFFF"
  nav-section-heading: "#64748B"
  nav-sitename: "#FFFFFF"
  nav-description: "#64748B"
  nav-toggle: "#64748B"
```

### Pattern: transparent / very light nav (default behaviour)

When `nav-background` is a light neutral, the defaults work fine.
You can omit `nav-link`, `nav-link-active`, and `nav-section-heading`
and the renderer will fall back to `text`, `accent`, and `text-muted`.

---

## Semantic colours and dark mode

`colours-semantic` values are applied globally (both modes). The callout
background is rendered at ~8% opacity, so a colour that looks fine on white
can wash out on a dark background — or conversely, a colour bright enough for
dark mode may be too vivid on white.

The solution is `colours-semantic-dark`: it overrides semantic colours in dark
mode only. Typical approach:

- **`colours-semantic`** — choose saturated but not neon values that work on white
- **`colours-semantic-dark`** — use lighter, more luminous variants of the same hues

```yaml
colours-semantic:
  info: "#1D4ED8"       # deep blue — strong on white
  warning: "#B45309"    # amber — strong on white
  success: "#15803D"    # green — strong on white
  error: "#B91C1C"      # red — strong on white

colours-semantic-dark:
  info: "#93C5FD"       # light blue — visible on dark background
  warning: "#FCD34D"    # light amber
  success: "#6EE7B7"    # light green
  error: "#FCA5A5"      # light red/pink
```

Match `callouts` `primary-colour` / `background-colour` values to
`colours-semantic` (light mode callout values), since the callout block
uses its own per-callout colour settings rather than the semantic variables.

---

## Legibility analysis

Before finalising any theme — and especially when refactoring an existing one —
work through every colour pairing in the design and check that text is
readable against its background.

**Pairs to check:**

| Text | Background |
|---|---|
| `text` | `background` |
| `text-muted` | `background` |
| `nav-link` | `nav-background` |
| `nav-link-active` | `nav-background` |
| `nav-section-heading` | `nav-background` |
| `nav-sitename` | `nav-background` |
| `nav-description` | `nav-background` |
| `nav-toggle` | `nav-background` |
| `accent` | `background` (used for inline links in content) |
| `colours-semantic.*` | `background` (callout borders and tinted backgrounds) |
| `colours-semantic-dark.*` | dark `background` |

**WCAG contrast targets:**
- Body text (`text`) on `background`: aim for **7:1** (AAA). Never go below 4.5:1 (AA).
- Secondary text (`text-muted`, `nav-section-heading`, `nav-description`): minimum **3:1**, aim for 4.5:1.
- Nav links and site name: minimum **4.5:1** against `nav-background`.
- Active/hover states: minimum **3:1** (they are reinforced by other visual cues).

**Common failure modes to look for:**
- A saturated accent on a white background can be vibrant but low-contrast — reds and oranges are frequent offenders.
- `text-muted` on a tinted or coloured background often falls below 3:1.
- Dark-mode `text-muted` on a near-black background is easy to get wrong when porting from a light-mode palette.
- `nav-description` and `nav-toggle` are small and low-weight, so they need more contrast than the minimum to feel comfortable — lean toward the higher targets for these.

When a pairing is marginal, adjust the lighter or darker of the two values by enough to clear the target. Do not simply accept values that are close to failing.

---

## Checklist before finalising a theme

- [ ] All six nav colour keys (`nav-link`, `nav-link-active`, `nav-section-heading`,
      `nav-sitename`, `nav-description`, `nav-toggle`) set for both `light` and
      `dark` whenever `nav-background` is non-neutral
- [ ] All nav colours contrast against `nav-background` (WCAG AA minimum; see Legibility analysis above)
- [ ] `text` on `background` meets 7:1 (AAA); never below 4.5:1
- [ ] `text-muted` and header element colours meet at least 3:1; aim for 4.5:1
- [ ] `accent` on `background` meets 4.5:1 (used for inline links)
- [ ] `colours-semantic-dark` provided with lighter variants of each colour
- [ ] `callouts` `primary-colour` matches `colours-semantic` values for consistency
- [ ] `divider` omitted unless the auto-derived value looks wrong (check hr and table borders)
- [ ] Dark mode `background` is not pure `#000000` unless intentional (use `#0A0A0A`+)
- [ ] `font-size` between `0.85` and `1.15`; `line-height` between `1.5` and `1.9`
- [ ] Version comment on line 1: `# mdcms v0.4 | DO NOT REMOVE THIS COMMENT`
