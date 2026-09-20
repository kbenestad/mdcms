# Unreleased changes

Changes merged into `development` that have not yet been released to `main`.

---

## Features

- **Scoped categories (`section-id` on a category).** A category may now declare
  `section-id:` in `config.yml` — one nav section code, a comma-separated
  string, or a list. The category then applies only to pages in those sections:
  inside them it behaves as before, and everywhere else the site falls back to
  `default-category` (full page list, default titles and section names, default
  search results). The category is not offered in the selector outside its
  sections, and navigating out of them switches the selector back to
  `default-category`. A category with no `section-id:` is unchanged — site-wide.
  `mdcms build` warns when a category's `section-id` names no section in
  `nav.yml`.
