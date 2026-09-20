# Unreleased changes

Changes merged into `development` that have not yet been released to `main`.

---

## Features

- **Tab completion for bash, zsh and fish, set up automatically.** The first `mdcms` command you run after installing switches completion on and tells you so; open a new terminal and Tab completes command names, options, and — the main point — your registered site names, so `mdcms build mys<Tab>` finishes to `mysite`. Path arguments (`--path`, and `register`'s PATH) complete directories. `mdcms completion` re-runs the setup by hand; `MDCMS_NO_COMPLETION=1` opts out, and nothing is set up when mdcms is not run from a terminal, so CI/CD is unaffected.

## Fixes

- Markdown tables written with an empty header row (`|||`) now render as a plain grid of rows — the empty header band is no longer shown.
