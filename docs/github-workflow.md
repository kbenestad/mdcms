# Automatic generation of `nav.yml` and `search.json`
This document covers

## Enable GitHub Actions
Before you can set up the automation workflow you need to ensure that it has write access:

1. Go to your repository on GitHub
2. Go to **Settings → Actions → General**
3. Scroll to **Workflow permissions**
4. Select **Read and write permissions**
5. Click **Save**

That's the only setup required. No secrets, no tokens, no third-party services.

## Enable workflow on single site
Create  `.github/workflows/build.yml` in your repository.

Assuming that the MD-CMS site is hosted at the repository root, you just need to paste the following into `build.yml`

```bash
name: Build

on:
  push:
    branches:
      - main
    paths:
      - "pages/**"
      - "posts/**"
      - "config.yml"

jobs:
  build:
    runs-on: ubuntu-latest
    permissions:
      contents: write
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install mdcms
        run: pip install mdcms

      - name: Build
        run: mdcms build

      - name: Commit updated files
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add nav.yml search.json
          git diff --staged --quiet || git commit -m "Build: update nav.yml and search.json"
          git push
```

If your MD-CMS instance is served from a directory within the repository (e.g., `docs`), you need to adjust `paths` and `git add` accordingly:

```bash
    paths:
      - "[PATH TO SITE]/pages/**"
      - "[PATH TO SITE]/posts/**"
      - "[PATH TO SITE]/config.yml"
```

and 

```bash
          git add [PATH TO SITE]/nav.yml [PATH TO SITE]/search.json
```

## Enable workflow on multisites
If you serve multiple MD-CMS instances from the same repository, you need to use a customised version of the script.

Create `.github/workflows/build.yml` in your repository.

Review the script below. It has been set up with four different directories (`DIRECTORY`, `DIRECTORY2`, `DIRECTORY3`, and `DIRECTORY4`). Change `paths` and `for section in` to your own directories:

```bash
name: Build

on:
  push:
    branches:
      - main
    paths:
      - "[DIRECTORY1]/pages/**"
      - "[DIRECTORY1]/posts/**"
      - "[DIRECTORY1]/config.yml"
      - "[DIRECTORY2]/pages/**"
      - "[DIRECTORY2]/posts/**"
      - "[DIRECTORY2]/config.yml"
      - "[DIRECTORY3]/pages/**"
      - "[DIRECTORY3]/posts/**"
      - "[DIRECTORY3]/config.yml"
      - "[DIRECTORY4]/pages/**"
      - "[DIRECTORY4]/posts/**"
      - "[DIRECTORY4]/config.yml"

jobs:
  build:
    runs-on: ubuntu-latest
    permissions:
      contents: write
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install mdcms
        run: pip install git+https://github.com/kbenestad/mdcms.git

      - name: Build all sections
        run: |
          for section in docs legal learning reception sysadmin; do
            cd $section
            mdcms build
            cd ..
          done

      - name: Commit updated files
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          for section in [DIRECTORY2] [DIRECTORY2] [DIRECTORY3] [DIRECTORY4]; do
            git add $section/nav.yml $section/search.json
          done
          git diff --staged --quiet || git commit -m "Build: update nav.yml and search.json"
          git push
```



This is different from the single site workflow. If you move from single site to multisite you need to updated the entire script -- it is not sufficient to just list the paths!
