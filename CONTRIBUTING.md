# Contributing to mdcms

Thanks for your interest in contributing. This is a small, focused project — contributions that fit the existing scope and style are welcome.

## What to work on

Check the [open issues](https://github.com/kbenestad/mdcms/issues) for bugs and planned work. If you want to add something new, open an issue first to discuss it before writing code — this avoids wasted effort if the feature doesn't fit the project direction.

## Getting started

```bash
git clone https://github.com/kbenestad/mdcms.git
cd mdcms
pip install -e ".[dev]"   # or: pip install click PyYAML certifi
```

Run the CLI directly during development:

```bash
python3 mdcms.py --help
```

For local site preview, run `python3 -m http.server 8800` inside a site directory and open `http://localhost:8800`. Do not open `index.html` directly — browsers block local file access.

## Making changes

- **CLI changes** (`mdcms.py`, `pyproject.toml`, `app/`, `.github/`) — branch from `main`, PR back to `main`.
- **Docs only** (`docs/`) — can go directly to `main`.
- Keep commits focused. One logical change per commit.
- Match the existing code style — single-file script, stdlib where possible, no unnecessary dependencies.

## Submitting a pull request

1. Fork the repo and create a branch from `main`.
2. Make your changes.
3. Test manually against a real site directory.
4. Open a PR with a clear description of what changed and why.

There are no automated tests yet, so describe what you tested in the PR description.

## Reporting bugs

Open a GitHub issue with:
- mdcms version (`mdcms --version`)
- OS and Python version
- The command you ran and the full output

## License

By contributing, you agree that your contributions will be licensed under the [Apache 2.0 License](LICENSE).
