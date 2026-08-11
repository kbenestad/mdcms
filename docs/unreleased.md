# Unreleased changes

Changes merged into `development` that have not yet been released to `main`.

---

## New

- **Copy button on code fences.** Every fenced code block now renders a copy
  button in its top-right corner — on hover on pointer devices, always visible
  on touch. It copies the block's plain text (no syntax-highlighting markup) and
  briefly turns into a checkmark to confirm. Works for code fences anywhere a
  page renders markdown, including inside callouts, tabs, and accordions, and in
  a `mdcms bundle` file opened straight off disk. Set `code-copy: no` in
  `config.yml` to turn it off. Adds two icons to the core set,
  `content_copy` and `check`, which `mdcms build` downloads automatically.
