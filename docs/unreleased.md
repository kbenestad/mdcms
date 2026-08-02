# Unreleased changes

Changes merged into `development` that have not yet been released to `main`.

---

- `mdcms upgrade` now handles dpkg-managed `.deb` installs itself instead of just printing manual instructions: it downloads the new `.deb` for the platform and installs it via `dpkg -i` (re-execing under `sudo` when not already root), keeping the package database in sync with the file on disk.
- `mdcms update`'s "Could not find a CURRENT VERSION banner" warning (shown for pre-0.6.6 legacy-marker sites) now names the exact `config.yml` path to edit and shows the banner line to add, instead of a bare "update it by hand."
