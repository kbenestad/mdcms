# Unreleased changes

Changes merged into `development` that have not yet been released to `main`.

---

## CLI v0.6.6

### Changed
- **Unified, tag-driven versioning.** Retired the separate CLI-version / site-format-version
  split in favour of a single version stream. Every version-bearing file now carries a common
  header banner ending in `CURRENT VERSION: X.Y.Z - <date>`:
  ```
  MD-CMS - Markdown Content Management System
  kbenestad/mdcms - https://github.com/kbenestad/mdcms

  Licensed under Apache 2.0 licence.

  CURRENT VERSION: 0.6.6 - 3 July 2026
  ```
  Applied to `mdcms.py`, `app/config.yml`, and `app/index.html` (the old
  `# mdcms vX.Y | DO NOT REMOVE THIS COMMENT` markers are gone).
- **`read_site_version()` now reads the `CURRENT VERSION:` line** from the `config.yml` header
  instead of a fixed line-1 marker. It still recognises the legacy `mdcms vX.Y` marker, so sites
  created before this change keep building. `_parse_ver` tolerates `v` prefixes and pre-release
  suffixes.

### Added
- **`scripts/bump_version.py`** — sets the release version across `mdcms.py` (`CLI_VERSION`,
  `CLI_RELEASE_DATE`, banner), `pyproject.toml`, and the `app/config.yml` / `app/index.html`
  banners in one shot. Strips a leading `v` and any pre-release suffix.
- **Release workflow now bumps the version from the tag.** Pushing `v0.6.7` makes every build job
  stamp `0.6.7` before building (so binaries report it) and the `publish` job commit the bump to
  `main` alongside the `latest/` binaries. No manual version editing before tagging.

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

## CI / release

- **Fixed: release runs stalled forever on the retired `macos-13` runner.** The
  macOS Intel build targeted `macos-13`, which GitHub retired in December 2025 —
  the job never got a runner, and because `publish` needed every build job, the
  binaries were never committed to `latest/` and never attached to the GitHub
  release. The Intel build now runs on `macos-15-intel` (GitHub's last Intel
  image, supported until Fall 2027).
- **Split macOS Intel out of the release critical path.** The Intel build is now
  its own `build-intel` job, and `publish` no longer waits for it: `latest/` is
  committed and the GitHub release is created as soon as the four fast builds
  finish (typically ~3 minutes). A new `publish-intel` job appends the Intel
  binary to `latest/macos/intel/` and uploads it to the release whenever the
  Intel runner completes — a slow (or failed) Intel job can no longer block a
  release. `publish` preserves the previously published Intel binary in
  `latest/` so its download URL keeps working until the new one lands.
- **New `release.yml` workflow — multi-platform binaries that land in `latest/`.**
  Builds standalone PyInstaller binaries for five targets on a runner matrix and
  commits them into `latest/` on `main` (the source of the
  `raw.githubusercontent.com/.../main/latest/...` download URLs), and additionally
  attaches them to a GitHub release when triggered by a `v*` tag.
  - Targets: `linux/amd64` (binary + `.deb`), `linux/arm64` (binary + `.deb`,
    **native ARM64 build for Raspberry Pi 3/4/5** on the free `ubuntu-24.04-arm`
    runner), `macos/silicon` (Apple Silicon), `macos/intel`, and `windows`.
  - Triggers on `v*` tags and on manual `workflow_dispatch`.
- **Install docs updated** (`install.md`, `workflows.md`, `README.md`,
  `dev-release.md`) for the new per-architecture `latest/` layout and the
  Raspberry Pi / Apple Silicon / Intel choices.

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
- **south-africa-bold — readable section headings.** Its muted `#9A9A9A` heading/note/icon
  labels (dim on the black nav surface) now point at `var(--nav-link-colour)`.

## Sample sites

- **Refreshed the bundled renderer in all seven sample sites.** Their copies of
  `index.html` were stale, predating the topbar/mobile-nav colour variables: the topbar
  site title and dropdown triggers were hardcoded to `var(--font-colour)` (page ink),
  so on bold themes with a dark nav surface they rendered ink-on-dark ("black on black")
  regardless of the theme's nav-surface tokens. Recopied `app/index.html` so the topbar
  and mobile nav honour `--nav-sitename-colour`, `--nav-link-colour`,
  `--nav-link-active-colour` and `--nav-toggle-colour`, matching the sidebar. This only
  affected the sample-site previews; the canonical `app/index.html` renderer was already
  correct.
