# Unreleased changes

Changes merged into `development` that have not yet been released to `main`.

---

## Added

- The release workflow now maintains `docs/banner/v{version}.txt` automatically: on a tagged release, the file for the version being replaced is overwritten with an "outdated, please run `mdcms upgrade`" message, and a new file is created for the released version reading "This is the latest version (`d Mmmm YYYY`)." These are what `mdcms --version` fetches to show a one-line status message. `.github/workflows/release.yml` change only.

## Fixed

- `mdcms upgrade` on a standalone-binary install crashed with an uncaught `PermissionError` traceback when the binary's install location (e.g. `/usr/local/bin`) wasn't writable by the current user — the download-to-temp-file step wasn't covered by the existing permission-error handling. It now detects this case up front and automatically re-execs itself under `sudo` (prompting for the password), instead of failing or requiring the user to manually retype the command with `sudo`.

---
