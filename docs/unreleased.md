# Unreleased changes

Changes merged into `development` that have not yet been released to `main`.

---

- Running `mdcms` with no subcommand now clears the terminal and shows a status banner (wordmark, version, release date, and an up-to-date/outdated message fetched from `docs/banner/`) above the usual command list.
- Post listings (`posts-created-*` tags) now stack on narrow viewports (≤ 600px): date/time on one line, the title link underneath, with extra space below the link before the next item. Previously the fixed-width date column squeezed titles into a sliver and could overflow the viewport on phones.
- All `posts-created-*` tag variants were verified working end-to-end in-browser (both orders; `byyear`, `byyearmonth`, `lastyear`, `lastmonth` modifiers; `limit`, `paginate: yes/no/none`, year selector, post-link navigation). The "most variants are broken" warnings were removed from `CLAUDE.md` and `docs/reference-pages.md`, and the incorrect `paginate:` mode descriptions in `reference-pages.md` were corrected (`yes` = full page bar, `no` = "Load more", `none` = hard cap).
- `sample-sites/hearth-and-bean/index.html` was re-synced with the canonical renderer — it had missed earlier renderer syncs (no collapsible sidebar) because the re-sync checklist in `CLAUDE.md` still listed seven sites; the list now includes all eight.
