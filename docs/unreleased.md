# Unreleased changes

Changes merged into `development` that have not yet been released to `main`.

---

## Renderer

- **Topbar navigation now uses the same colours as sidebar navigation.** Topbar nav text, the site name, section/toggle icons, and active-link styling previously fell back to generic `--font-colour` / `--font-colour-muted` values, so on themes with a strong or dark `surface` the topbar text could become illegible and active items lost their accent colour. Topbar (desktop, dropdowns, and the mobile panel) now reads the same `--nav-link-colour`, `--nav-sitename-colour`, `--nav-toggle-colour`, `--nav-section-heading-colour`, and active `--nav-link-active-colour` variables the sidebar uses. Active items get the matching accent text, tinted background, and an edge marker in the accent colour (a left border for vertical dropdown/mobile items, a bottom border for the horizontal top bar).
