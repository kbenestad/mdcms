# Unreleased changes

Changes merged into `development` that have not yet been released to `main`.

---

## Themes

- **Four new Newspaper-inspired themes: `gazette`, `tabloid`, `chronicle`, `folio`.**
  Rounds out the family (previously just `broadsheet` and `ledger`) with more
  variety in heading/body pairing and background tint:
  - `gazette` — Montserrat headings over a Lora body, cream surface, white page.
  - `tabloid` — bold Montserrat headings, Source Serif 4 body, salmon surface,
    crimson accent.
  - `chronicle` — all-serif (Playfair Display headings, PT Serif body), dusty
    pink surface, wine accent.
  - `folio` — understated Montserrat headings, Merriweather body, all-cream
    (surface ≈ page) for a subtle two-tone look.
  Registered in `sample-sites/themes.json` alongside the existing entries.

## Sample sites

- **Fixed: theme picker's branch switcher didn't actually switch theme data.**
  `sample-sites/index.html` is only deployed to GitHub Pages from `main`, so its
  `fetch("themes.json")` always read `main`'s manifest — picking "development
  (preview)" in the Branch selector rewrote the site preview links to jsDelivr
  but left the theme family/list populated from `main`, so themes added only on
  `development` (like the four above) never appeared. `themes.json` is now
  fetched from the same jsDelivr branch URL used for site links, and the fetch
  re-runs (preserving the current family/theme selection where possible)
  whenever the branch selector or the Reset button changes branches.
