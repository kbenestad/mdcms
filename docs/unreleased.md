# Unreleased changes

Changes merged into `development` that have not yet been released to `main`.

---

## Themes

- **Rewrote `gotham`, `manhattan`, `city` to match the real mastheads,
  scraped from live nytimes.com/wsj.com/ft.com CSS instead of guessing.**
  - `gotham` (NYT) — heading font swapped to Domine (a purpose-built
    Cheltenham alternative) and body to Gelasio (a purpose-built Georgia
    alternative); ink/muted tightened to the site's actual `#121212` /
    `#727272`. `#326891` accent confirmed correct.
  - `manhattan` (WSJ) — corrected from an invented cream/serif-body look to
    the real site: white page, light-gray nav surface, Zilla Slab bold
    headlines over a **light-weight sans body** (Work Sans 300, not serif —
    WSJ's body copy is actually sans), red accent retuned to `#AE1917`.
  - `city` (FT) — heading swapped to Fraunces at weight 300 (FT's real
    headline weight is light, not bold) as a Financier Display alternative;
    body to Public Sans; nav surface now uses FT's actual darker "FT pink"
    label colour `#fcd0b1` (page stays the true paper `#fff1e5`); accent
    tightened to FT's real teal `#0d7680`.
