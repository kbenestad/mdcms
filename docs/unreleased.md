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
