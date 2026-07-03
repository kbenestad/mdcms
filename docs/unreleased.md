# Unreleased changes

Changes merged into `development` that have not yet been released to `main`.

---

## CLI v0.6.5

### Added
- **`mdcms config` command** — configure a site's `config.yml` and install themes.
  - Interactive by default: a menu for the most-used settings (sitename, navigation
    style, theme, homepage, site description, footer, default colour mode, nav
    position, and PWA settings). Runs against a registered site name, `--path`, or
    the current directory.
  - **Theme browser/installer**: browse the theme library by family or keyword,
    download the chosen theme into `assets/themes/`, and set `theme:` in
    `config.yml` automatically. The theme index is read from the local checkout
    when present, otherwise fetched from the repository.
  - Non-interactive/scriptable: `--set KEY=VALUE` (repeatable), `--theme NAME`,
    and `--list-themes`.
  - Config edits are surgical — comments and file structure in `config.yml` are
    preserved, commented example keys are uncommented in place, and structured
    blocks (e.g. dict-form `offline-message`) are left untouched.

## Themes

- **Bold themes — readable nav surface colours.** Fixed 21 `*-bold` themes whose nav
  text (site title, links, section headings) was hardcoded to white/near-white and
  became unreadable on light or bright surfaces. Nav-surface text tokens now reference
  the theme's CSS variables instead of literal colours: light-surface themes point the
  whole `on-surface` group at `var(--font-colour)` / `var(--nav-link-colour)` (dark ink),
  and dark-surface themes point their faint muted labels at `var(--nav-link-colour)`.
  All bold themes now clear a 3:1 contrast floor for every nav-surface token.
  Affected: air-klm, air-norse, air-emirates, air-swiss, lit-pentecost, lit-rose,
  canada, china, ireland, italy, med-wellness, greenland, map-osm, map-paris-metro,
  map-swisstopo, map-tokyo-metro, map-tunnelbana, tx-db, tx-hapag, tx-maersk, un-blue.
