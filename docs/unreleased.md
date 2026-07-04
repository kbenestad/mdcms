# Unreleased changes

Changes merged into `development` that have not yet been released to `main`.

---

## Added

- `mdcms update [name]` — refreshes a registered (or `--path`-given) site's `index.html` to the version this CLI ships, preserving the site's `<title>` and bumping the `CURRENT VERSION` marker in `config.yml`. Automates the manual "download the latest index.html and overwrite it" step from `docs/workflows.md`.
- `mdcms upgrade` — upgrades the `mdcms` CLI itself to the latest release. Auto-detects pip, pipx, or standalone-binary installs; binary installs are downloaded and swapped in place, with a dpkg-ownership check so a Debian package install isn't silently desynced from `dpkg`'s records.

---
