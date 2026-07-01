# MD-CMS sample sites

Reference sites built with MD-CMS, plus a picker to browse them under any theme.

Open **`index.html`** (served over HTTP — see below) for a gallery that lists
every site and lets you preview it with any theme from the [`../themes/`](../themes)
library before opening it.

## Sites

| Folder | Navigation | What it shows |
|---|---|---|
| `showcase/` | topbar | Feature tour — callouts, tabs, accordions, `toc`, paginated posts |
| `techpulse/` | topbar | News site with a large paginated post archive |
| `kitchen-table/` | topbar | Recipe/blog site with posts |
| `neuraldb-docs/` | topbar | Product documentation |
| `modern-philosophy/` | sidebar | Long-form textbook with nested sidebar sections |
| `velox-docs/` | sidebar | Developer documentation |
| `wandering-algorithm/` | sidebar | A novel, chapter by chapter |

Each folder is a complete, self-contained MD-CMS site (`index.html`, `config.yml`,
`theme.yml`, generated `nav.yml`/`search.json`, and `pages/`, `posts/`, `assets/`).

## How the theme picker works

`index.html` reads `themes.json` (a generated manifest of every file under
`../themes/`) and, when you pick a theme, appends `?theme=<relative-path>` to the
site's launch link. The renderer honours that override in place of the theme named
in the site's `config.yml`, so the same markdown is shown in a different palette.
"Default" always opens a site with its own `theme.yml`.

## Running locally

These are static sites but must be served over HTTP (browsers block `file://`
fetches). From the repository root:

```bash
python3 -m http.server 8800
# then open http://localhost:8800/sample-sites/
```

## Regenerating

- Rebuild a site after editing its content: `mdcms build --path sample-sites/<name>`
- Regenerate the theme manifest after adding/removing themes: re-run the small
  generator that writes `themes.json` (walks `../themes/` for `*.yml`/`*.yaml`).

Content and themes here are in the public domain via
[CC0](https://creativecommons.org/publicdomain/zero/1.0/) — use and remix freely.
