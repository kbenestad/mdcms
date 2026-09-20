# Unreleased changes

Changes merged into `development` that have not yet been released to `main`.

---

## Features

- **Tab completion for bash, zsh and fish.** `mdcms completion` prints the one-off setup commands for your shell. Once set up, Tab completes command names, options, and — the main point — your registered site names, so `mdcms build <Tab>` offers the sites you have registered. Path arguments (`--path`, and `register`'s PATH) complete directories.

## Fixes

- Markdown tables written with an empty header row (`|||`) now render as a plain grid of rows — the empty header band is no longer shown.
