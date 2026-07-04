# Unreleased changes

Changes merged into `development` that have not yet been released to `main`.

---

## Renderer (`app/index.html`)

- **New optional `heading` palette token, decoupling headline colour from
  the accent.** `.md-content h1`–`h6` were hardcoded to `var(--accent)`, so
  every article heading rendered in whatever colour a theme used for links,
  tabs, and accordions — e.g. the Newspaper-inspired themes' headlines came
  out blue/red/teal instead of the near-black real mastheads use. Headings
  now read `var(--heading-colour, var(--accent))`: themes that don't set
  `heading` are pixel-identical to before (still fall back to `primary`),
  and themes that do set it (typically equal to `ink`) get accent-free
  headlines while tabs, accordions, and links keep the accent colour.

## Themes

- **All nine Newspaper-inspired themes now set `heading` to their own
  `ink`**, so headlines render in body-ink black/near-black instead of the
  theme's accent colour — matching how real newspaper mastheads keep
  colour for links only. Affected: `broadsheet`, `chronicle`, `city`,
  `folio`, `gazette`, `gotham`, `ledger`, `manhattan`, `tabloid`.
- **`gotham`'s accent corrected to NYT's actual byline grey (`#727272`
  light / `#9A9A9A` dark)**, not the newsprint blue — the blue was never a
  prominent UI colour on the real site (it isn't the subscribe button or
  any other visible affordance); the grey used for bylines is what's
  actually pervasive. The `colours-semantic`/callout `info` colour keeps
  the real NYT blue, since that's still an authentic accent worth keeping
  for the info callout specifically.
