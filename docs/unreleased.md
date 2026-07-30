# Unreleased changes

Changes merged into `development` that have not yet been released to `main`.

---

- Re-released v0.6.13 as v0.7.0 — it shipped new features (`mdcms bundle`, theme-file versioning, etc.) and per the newly-documented semver policy in `CLAUDE.md` (major = breaking, minor = features, patch = fixes), a feature release must bump the minor version, not the patch version. No functional changes beyond the version number itself.
- Fixed `docs/banner/v0.6.12.txt` still claiming to be "the latest version" after v0.6.13 shipped. Root cause: the release workflow's "mark the old version outdated" step compared `mdcms.py`'s `CLI_VERSION` before/after the version bump on `main`, but that bump normally already happened in the commit that merged to `main` (per `CLAUDE.md`'s versioning rule), so old/new compared equal and the flip silently no-opped. Replaced with a self-healing scan of all `docs/banner/v*.txt` files that flips any stale "latest version" banner other than the one just released.
- Documented the `docs/banner/vX.Y.Z.txt` version-status-banner mechanism and the X.Y.Z semver policy in `CLAUDE.md` — neither was written down before.
