# Unreleased changes

Changes merged into `development` that have not yet been released to `main`.

---

## Added

- `mdcms update [name]` — refreshes a registered (or `--path`-given) site's `index.html` to the version this CLI ships, preserving the site's `<title>`. Also appends any config.yml keys the template has gained since the site was last updated (verbatim, active or commented-out, without touching a single existing key/value/comment), then bumps the `CURRENT VERSION` marker in `config.yml`. Automates the manual "download the latest index.html and overwrite it" step from `docs/workflows.md`, plus config migration.
- `mdcms upgrade` — upgrades the `mdcms` CLI itself to the latest release. Auto-detects pip, pipx, or standalone-binary installs; binary installs are downloaded and swapped in place, with a dpkg-ownership check so a Debian package install isn't silently desynced from `dpkg`'s records.

---
