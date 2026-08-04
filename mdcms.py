#!/usr/bin/env python3
#
# MD-CMS - Markdown Content Management System
# kbenestad/mdcms - https://github.com/kbenestad/mdcms
#
# Licensed under Apache 2.0 licence.
#
# CURRENT VERSION: 0.8.2 - 4 August 2026
#
# Copyright 2026 Kristian Benestad
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""MD-CMS — CLI tool for managing and building MD-CMS sites."""

import base64
import datetime
import json
import mimetypes
import os
import platform
import re
import shutil
import ssl
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path

import certifi

import click
import yaml

CLI_VERSION = "0.8.2"
CLI_RELEASE_DATE = "4 August 2026"
MIN_SUPPORTED_VERSION = "0.3"

# Minimum theme-file format the renderer/build supports. Theme files carry their
# own marker (`# mdcms theme vX.Y[.Z]`) independent of the site version; older
# themes are auto-refreshed from the library on build (see _ensure_theme_current).
MIN_SUPPORTED_THEME_VERSION = "0.6.0"

# Version detection in a site's config.yml. The current header carries the
# version on a `CURRENT VERSION: X.Y[.Z] - <date>` line; older sites (still in
# the wild) carry a legacy `mdcms vX.Y | DO NOT REMOVE THIS COMMENT` marker.
# Both are recognised so existing sites keep building after this format change.
VERSION_LINE_RE = re.compile(r"CURRENT VERSION:\s*v?(\d+\.\d+(?:\.\d+)?)", re.IGNORECASE)
MARKER_RE = re.compile(r"mdcms v(\d+\.\d+(?:\.\d+)?)", re.IGNORECASE)
# Theme files carry `# mdcms theme vX.Y[.Z]`; the legacy `mdcms vX.Y` marker
# (MARKER_RE) is still accepted as a fallback for themes installed before 0.6.0.
THEME_VERSION_RE = re.compile(r"mdcms theme v(\d+\.\d+(?:\.\d+)?)", re.IGNORECASE)
CATEGORY_CODE_RE = re.compile(r"^[a-zA-Z0-9\-]+$")

REGISTRY_FILE = Path.home() / ".config" / "mdcms" / "sites.json"
TEMPLATE_BASE_URL = "https://raw.githubusercontent.com/kbenestad/mdcms/main/app"
MANIFEST_FILENAME = "mdcms.json"

REPO_RAW_BASE = "https://raw.githubusercontent.com/kbenestad/mdcms/main"
THEMES_MANIFEST_PATH = "sample-sites/themes.json"

# Mirrors CORE_ICONS in app/index.html — those are rendered unconditionally, so every
# site needs them. OPTIONAL_ICONS is the rest of the stock icon pack: only pulled in
# when a site's config.yml/theme.yml actually names one (categories-selecticon,
# nav-section-expand-icon, nav-section-collapse-icon, or a theme.yml callout icon
# override) — see compute_referenced_icons().
CORE_ICONS = [
    "dark_mode", "light_mode", "menu", "search", "arrow_right", "arrow_drop_down",
    "info", "warning", "error", "success", "keyboard_arrow_right",
    "left_panel_close", "left_panel_open", "right_panel_close", "right_panel_open",
]
OPTIONAL_ICONS = [
    "keyboard_arrow_down", "keyboard_double_arrow_right", "keyboard_double_arrow_down",
    "expand_content", "collapse_content", "add", "minimize", "language",
]
ALL_KNOWN_ICONS = frozenset(CORE_ICONS) | frozenset(OPTIONAL_ICONS)

# Icons that used to ship in the stock pack but were never actually referenced by
# anything (index.html, config.yml, or any theme in themes/) and were dropped from
# it. Never downloaded — only cleaned up from assets/icons/ if a site still has one
# left over from before the pack was trimmed and it's unreferenced.
LEGACY_ICONS = frozenset({
    "mobile_arrow_down", "exclamation", "dangerous", "report", "history", "text_compare",
})

GITHUB_URL_RE = re.compile(
    r"https?://github\.com/([^/]+)/([^/]+?)(?:\.git)?"
    r"(?:/tree/([^/]+?)(?:/(.+?))?)?/?$"
)


# ─── Version helpers ──────────────────────────────────────────

def _parse_ver(v: str) -> tuple:
    core = v.strip().lstrip("vV").split("-", 1)[0].split("+", 1)[0]
    return tuple(int(x) for x in re.findall(r"\d+", core))


def read_site_version(site_path: Path) -> "str | None":
    config = site_path / "config.yml"
    if not config.exists():
        return None
    try:
        # The version lives in the leading comment header. Scan the first lines
        # so both the `CURRENT VERSION:` banner and the legacy first-line marker
        # are found, without matching anything in the config body below.
        header = "\n".join(config.read_text(encoding="utf-8").splitlines()[:25])
    except OSError:
        return None
    m = VERSION_LINE_RE.search(header) or MARKER_RE.search(header)
    return m.group(1) if m else None


def theme_version_from_text(text: str) -> "str | None":
    """Extract a theme version marker from a theme file's leading comment header.

    Recognises the current `# mdcms theme vX.Y[.Z]` marker and, as a fallback,
    the legacy `# mdcms vX.Y | DO NOT REMOVE THIS COMMENT` marker themes carried
    before 0.6.0. Returns the version string, or None when no marker is present.
    """
    header = "\n".join(text.splitlines()[:25])
    m = THEME_VERSION_RE.search(header) or MARKER_RE.search(header)
    return m.group(1) if m else None


def read_theme_version(theme_path: Path) -> "str | None":
    """Read the version marker from a theme file, or None if it can't be read."""
    try:
        return theme_version_from_text(theme_path.read_text(encoding="utf-8"))
    except OSError:
        return None


def version_status(site_version: str) -> "tuple[str, str]":
    """Returns (status_code, display_message). status_code: 'ok', 'outdated', 'unsupported', 'newer'."""
    sv = _parse_ver(site_version)
    min_sv = _parse_ver(MIN_SUPPORTED_VERSION)
    cur = _parse_ver(CLI_VERSION)
    if sv < min_sv:
        return "unsupported", f"v{site_version} — below minimum supported v{MIN_SUPPORTED_VERSION}"
    if sv < cur:
        return "outdated", f"v{site_version} — update available (CLI is v{CLI_VERSION})"
    if sv > cur:
        return "newer", f"v{site_version} — site newer than CLI (consider upgrading mdcms)"
    return "ok", f"v{site_version}"


# ─── Registry ─────────────────────────────────────────────────

def load_registry() -> dict:
    if REGISTRY_FILE.exists():
        try:
            return json.loads(REGISTRY_FILE.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            pass
    return {"sites": {}}


def save_registry(reg: dict):
    REGISTRY_FILE.parent.mkdir(parents=True, exist_ok=True)
    REGISTRY_FILE.write_text(json.dumps(reg, indent=2), encoding="utf-8")


def resolve_site_path(name: "str | None", path_override: "str | None") -> Path:
    """Resolve a site path from name (registry), --path override, or CWD."""
    if path_override:
        return Path(path_override).resolve()
    if name:
        reg = load_registry()
        if name not in reg["sites"]:
            raise click.ClickException(
                f"Site '{name}' not found. Use 'mdcms view' to list registered sites."
            )
        return Path(reg["sites"][name]["path"])
    return Path.cwd()


# ─── Config reading ───────────────────────────────────────────

def read_config(site_path: Path) -> dict:
    config_file = site_path / "config.yml"
    if not config_file.exists():
        return {}
    try:
        text = config_file.read_text(encoding="utf-8")
    except OSError as e:
        raise click.ClickException(f"Could not read config.yml: {e}")
    try:
        return yaml.safe_load(text) or {}
    except yaml.YAMLError as e:
        raise click.ClickException(f"config.yml is not valid YAML: {e}")


def get_category_info(cfg: dict) -> dict:
    use = str(cfg.get("categories-use", "no")).lower() in ("yes", "true")
    default_cat = cfg.get("default-category") or {}
    raw_default = default_cat.get("code") if isinstance(default_cat, dict) else None
    default_code = str(raw_default) if raw_default is not None else None
    cats = cfg.get("categories") or []
    codes = [str(c["code"]) for c in cats if isinstance(c, dict) and "code" in c]
    return {"use": use, "default_code": default_code, "codes": codes}


def read_nav_yml(site_path: Path) -> dict:
    """Read nav.yml, tolerating a missing or unparseable file.

    Returns {"sections": [...], "pages": [...], "date_categories": [...], "warning": str|None}.
    Callers that need to surface the warning (e.g. `mdcms build`) can echo it themselves.
    """
    empty = {"sections": [], "pages": [], "date_categories": [], "warning": None}
    nav_file = site_path / "nav.yml"
    if not nav_file.exists():
        return empty
    try:
        nav_data = yaml.safe_load(nav_file.read_text(encoding="utf-8")) or {}
    except (OSError, yaml.YAMLError) as e:
        empty["warning"] = f"could not parse nav.yml ({e})"
        return empty
    return {
        "sections": [s for s in (nav_data.get("sections") or []) if isinstance(s, dict)],
        "pages": [p for p in (nav_data.get("pages") or []) if isinstance(p, dict)],
        "date_categories": [c for c in (nav_data.get("date-categories") or []) if c is not None],
        "warning": None,
    }


def read_nav_yml_for_edit(site_path: Path) -> dict:
    """Read nav.yml for an in-place edit, refusing to proceed on a parse error.

    `read_nav_yml` degrades to an empty nav so `mdcms build` — which regenerates
    every page entry from disk anyway — can recover from a damaged file. Editing
    commands must not do that: they write back what they read, so treating an
    unparseable nav.yml as empty would silently delete every section and page it
    still contains.
    """
    nav = read_nav_yml(site_path)
    if nav["warning"]:
        raise click.ClickException(
            f"{nav['warning']}.\nRefusing to edit it — saving now would discard every section "
            f"and page still in the file. Fix {site_path / 'nav.yml'} by hand, or delete it and "
            "run 'mdcms build' to regenerate it (section metadata such as defaultname, sort, "
            "parent and pagination would be lost)."
        )
    return nav


# ─── Frontmatter parsing ─────────────────────────────────────

def parse_frontmatter(filepath: Path) -> "tuple[dict, str]":
    try:
        content = filepath.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return {}, ""
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n", content, re.DOTALL)
    if not match:
        return {}, content
    try:
        meta = yaml.safe_load(match.group(1)) or {}
    except yaml.YAMLError:
        meta = {}
    return meta, content[match.end():]


_FRONTMATTER_KEY_ORDER = [
    "title", "section-id", "sort", "draft", "author", "created", "modified",
    "description", "keywords", "language",
]


def _emit_frontmatter_value(v) -> str:
    if v is None:
        return "null"
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, float)):
        return str(v)
    s = str(v)
    if s == "" or any(c in s for c in ':"\'#') or s.lower() in ("true", "false", "null", "yes", "no", "on", "off"):
        return '"' + s.replace('"', '\\"') + '"'
    return s


def write_page_file(filepath: Path, meta: dict, body: str) -> None:
    """Write a markdown file with a YAML frontmatter block, preserving `body` verbatim."""
    ordered_keys = [k for k in _FRONTMATTER_KEY_ORDER if k in meta] + \
                   [k for k in meta if k not in _FRONTMATTER_KEY_ORDER]
    lines = ["---"]
    for k in ordered_keys:
        if meta[k] is None:
            continue
        lines.append(f"{k}: {_emit_frontmatter_value(meta[k])}")
    lines.append("---")
    lines.append("")
    text = "\n".join(lines) + body.lstrip("\n")
    filepath.parent.mkdir(parents=True, exist_ok=True)
    filepath.write_text(text, encoding="utf-8")


def list_markdown_files(site_path: Path) -> list:
    """List every .md file under pages/ and posts/ with its key frontmatter fields."""
    out = []
    for folder in ("pages", "posts"):
        d = site_path / folder
        if not d.is_dir():
            continue
        for f in sorted(d.rglob("*.md")):
            rel = str(f.relative_to(site_path)).replace("\\", "/")
            meta, _ = parse_frontmatter(f)
            out.append({
                "file": rel,
                "title": meta.get("title") or Path(rel).stem.replace("_", " ").replace("-", " ").title(),
                "section-id": meta.get("section-id"),
                "sort": meta.get("sort"),
                "draft": bool(meta.get("draft", False)),
            })
    return out


# ─── Scanner ─────────────────────────────────────────────────

# A category code auto-detected from a page filename suffix like
# `pagename.20260704.md`. Enabled per-site via `categories-dates: yes`.
DATE_SUFFIX_RE = re.compile(r"^\d{8}$")

_MONTH_NAMES = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]


def is_date_category_code(suffix: "str | None") -> bool:
    """True if `suffix` is a real calendar date in YYYYMMDD form."""
    if not suffix or not DATE_SUFFIX_RE.match(suffix):
        return False
    try:
        datetime.datetime.strptime(suffix, "%Y%m%d")
        return True
    except ValueError:
        return False


def format_date_category(code: str) -> str:
    """Render a YYYYMMDD code as 'd Mmmm YYYY', e.g. '4 July 2026'."""
    year, month, day = int(code[:4]), int(code[4:6]), int(code[6:8])
    return f"{day} {_MONTH_NAMES[month - 1]} {year}"


def identify_variant(rel: str, known_codes: set, dates_enabled: bool = False) -> "tuple[str | None, str | None]":
    if not rel.endswith(".md"):
        return None, None
    stem = rel[:-3]
    base_name = os.path.basename(stem)
    if "." in base_name:
        head, _, suffix = stem.rpartition(".")
        if suffix in known_codes or (dates_enabled and is_date_category_code(suffix)):
            return head, suffix
    return stem, None


def scan_and_categorize(
    directory: Path, site_root: Path, known_codes: set, dates_enabled: bool = False
) -> list:
    records = []
    if not directory.is_dir():
        return records
    for root, dirs, files in os.walk(directory):
        dirs.sort()
        for name in sorted(files):
            if not name.endswith(".md"):
                continue
            full = Path(root) / name
            rel = str(full.relative_to(site_root)).replace("\\", "/")
            base, code = identify_variant(rel, known_codes, dates_enabled)
            if base is None:
                continue
            meta, body = parse_frontmatter(full)
            if meta.get("draft", False):
                continue
            records.append({
                "file": rel,
                "base": base,
                "code": code,
                "title": (
                    meta.get("title")
                    or Path(base).name.replace("_", " ").replace("-", " ").title()
                ),
                "sort": meta.get("sort"),
                "section-id": meta.get("section-id"),
                "author": meta.get("author"),
                "created": str(meta.get("created", "")),
                "modified": str(meta.get("modified", "")),
                "language": meta.get("language", "en"),
                "keywords": meta.get("keywords", ""),
                "description": meta.get("description", ""),
                "body": body[:5000],
            })
    return records


def group_by_base(records: list) -> dict:
    groups: dict = {}
    for r in records:
        groups.setdefault(r["base"], {})[r["code"]] = r
    return groups


def select_primary(variants: dict, default_code: "str | None") -> dict:
    if default_code and default_code in variants:
        return variants[default_code]
    if None in variants:
        return variants[None]
    return next(iter(variants.values()))


# ─── Nav / search generators ─────────────────────────────────

def _yaml_double_quote(s: str) -> str:
    """Render `s` as a YAML double-quoted scalar.

    Backslashes must be escaped first: inside double quotes YAML treats `\\`
    as an escape introducer, so an unescaped one from the source string (a
    Windows path in a page title, say) produces an invalid escape sequence and
    makes the whole file unparseable.
    """
    out = []
    for ch in s:
        if ch == "\\":
            out.append("\\\\")
        elif ch == '"':
            out.append('\\"')
        elif ch == "\n":
            out.append("\\n")
        elif ch == "\r":
            out.append("\\r")
        elif ch == "\t":
            out.append("\\t")
        elif ord(ch) < 0x20 or ord(ch) == 0x7F:
            out.append("\\x%02x" % ord(ch))
        else:
            out.append(ch)
    return '"' + "".join(out) + '"'


def _yaml_needs_quoting(s: str) -> bool:
    """True if `s` cannot be emitted as a bare YAML plain scalar.

    Beyond the obvious cases (empty, surrounding whitespace, control characters,
    characters that start a comment or a quoted/escaped run) the string is round-
    tripped through the parser: anything that fails to parse, or that parses back
    as something other than the same string — a list (`- dash lead`), a flow
    sequence (`[2026] Roadmap`), a number (`2026`), a YAML 1.1 boolean (`yes`) —
    has to be quoted.
    """
    if s == "" or s != s.strip():
        return True
    if any(ord(c) < 0x20 or ord(c) == 0x7F for c in s):
        return True
    if any(c in s for c in ':"\'#\\'):
        return True
    try:
        return yaml.safe_load(s) != s
    except yaml.YAMLError:
        return True


def _emit_value(v) -> str:
    if v is None:
        return ""
    s = str(v)
    return _yaml_double_quote(s) if _yaml_needs_quoting(s) else s


def _emit_code(code) -> str:
    """Quote a category or section code so it round-trips as a string —
    all-digit date codes (e.g. "20260704") parse back as integers otherwise,
    breaking string joins/comparisons on rebuild."""
    return _emit_value(str(code))


def merge_sections(page_entries: list, existing_sections: list) -> "tuple[list, list]":
    by_code = {s["code"]: dict(s) for s in existing_sections if s.get("code")}
    referenced = sorted({p.get("section-id") for p in page_entries if p.get("section-id")})
    auto_created = []
    for code in referenced:
        if code in by_code:
            continue
        used_sorts = {s.get("sort") for s in by_code.values() if isinstance(s.get("sort"), int)}
        next_sort = 100
        while next_sort in used_sorts:
            next_sort += 10
        by_code[code] = {
            "code": code,
            "defaultname": code.replace("-", " ").replace("_", " ").title(),
            "sort": next_sort,
            "pagesvisibility": "visible",
        }
        auto_created.append(code)
    merged = sorted(by_code.values(), key=lambda s: (s.get("sort") or 999, s["code"]))
    return merged, auto_created


def build_page_nav(
    page_groups: dict,
    existing_pages: list,
    categories_use: bool = False,
    default_code: "str | None" = None,
) -> list:
    existing_by_file = {p["file"]: p for p in existing_pages if p.get("file")}
    out = []
    for base, variants in sorted(page_groups.items()):
        file = base + ".md"
        primary = select_primary(variants, default_code)
        existing = existing_by_file.get(file, {})
        # Frontmatter wins. nav.yml's own value is only a fallback for pages
        # that declare no `sort:` at all — otherwise editing a page's sort (by
        # hand or via `mdcms config`) would never reach nav.yml, because the
        # value written on the very first build would keep overriding it.
        sort = primary.get("sort") or existing.get("sort") or 100
        entry: dict = {
            "file": file,
            "title": primary.get("title", ""),
            "section-id": primary.get("section-id"),
            "sort": sort,
        }
        if categories_use:
            is_post = file.startswith("posts/")
            covered = {}
            has_uncategorized = False
            for code, record in variants.items():
                if code is None:
                    if is_post:
                        has_uncategorized = True
                    elif default_code:
                        covered[default_code] = record.get("title", "")
                else:
                    covered[code] = record.get("title", "")
            if has_uncategorized:
                entry["uncategorized"] = True
            entry["variants"] = sorted(covered.keys())
            entry["titles"] = covered
        out.append(entry)
    out.sort(key=lambda p: (p["sort"], p["file"]))
    return out


def generate_nav_yml(
    sections: list, pages: list, categories_use: bool = False, date_categories: "list | None" = None
) -> str:
    lines = [
        "# nav.yml — generated by mdcms",
        "# Manual edits to section metadata (defaultname, sort, parent, parent-sort,",
        "# pagesvisibility, categorynames, pagination) are preserved on rebuild.",
        "",
    ]
    if date_categories:
        lines.append("# date-categories is generated — do not edit by hand. It lists every")
        lines.append("# YYYYMMDD category code found on disk, newest first (categories-dates: yes).")
        lines.append("date-categories:")
        for code in date_categories:
            lines.append(f"  - \"{code}\"")
        lines.append("")
    lines.append("sections:")
    if not sections:
        lines.append("  # (none yet — add section-id to page frontmatter to auto-create)")
    else:
        for s in sections:
            lines.append(f"  - code: {_emit_code(s['code'])}")
            lines.append(f"    defaultname: {_emit_value(s.get('defaultname', s['code']))}")
            lines.append(f"    sort: {s.get('sort', 100)}")
            if s.get("parent"):
                lines.append(f"    parent: {_emit_code(s['parent'])}")
                lines.append(f"    parent-sort: {s.get('parent-sort', 100)}")
            lines.append(f"    pagesvisibility: {s.get('pagesvisibility', 'visible')}")
            if s.get("pagination") in (True, "on", "yes"):
                lines.append("    pagination: on")
            cn = s.get("categorynames") or {}
            if cn:
                lines.append("    categorynames:")
                for k, v in cn.items():
                    lines.append(f"      {k}: {_emit_value(v)}")
            lines.append("")

    lines.append("pages:")
    if not pages:
        lines.append("  # (no pages)")
    else:
        for p in pages:
            lines.append(f"  - file: {p['file']}")
            lines.append(f"    title: {_emit_value(p['title'])}")
            if p.get("section-id"):
                lines.append(f"    section-id: {_emit_code(p['section-id'])}")
            lines.append(f"    sort: {p.get('sort', 100)}")
            if categories_use and p.get("uncategorized"):
                lines.append("    uncategorized: true")
            if categories_use and p.get("variants"):
                lines.append(f"    variants: [{', '.join(_emit_code(v) for v in p['variants'])}]")
            if categories_use and p.get("titles"):
                lines.append("    titles:")
                for code, title in p["titles"].items():
                    lines.append(f"      {_emit_code(code)}: {_emit_value(title)}")
            lines.append("")
    return "\n".join(lines)


def write_nav_yml(
    site_path: Path, sections: list, pages: list,
    categories_use: bool = False, date_categories: "list | None" = None,
) -> None:
    (site_path / "nav.yml").write_text(
        generate_nav_yml(sections, pages, categories_use=categories_use, date_categories=date_categories),
        encoding="utf-8",
    )


def generate_search_json(
    records: list,
    categories_use: bool = False,
    default_code: "str | None" = None,
) -> str:
    out = []
    for r in records:
        file_path = (r["base"] + ".md") if "base" in r else r.get("file", "")
        entry: dict = {
            "file": file_path,
            "title": r.get("title", ""),
            "section-id": r.get("section-id"),
            "keywords": r.get("keywords", ""),
            "description": r.get("description", ""),
            "author": r.get("author"),
            "created": r.get("created", ""),
            "modified": r.get("modified", ""),
            "language": r.get("language", "en"),
            "body": r.get("body", ""),
        }
        if categories_use:
            code = r.get("code")
            is_post = r.get("file", "").startswith("posts/")
            if code is not None:
                entry["category"] = code
            elif is_post:
                entry["category"] = None  # null = show in all categories
            else:
                entry["category"] = default_code
        out.append(entry)
    return json.dumps(out, indent=2, ensure_ascii=False)


# ─── Asset validation ─────────────────────────────────────────

_ASSET_RE = re.compile(r'assets/[\w.\-/]+')


def _collect_yaml_assets(val, source: str, out: list):
    if isinstance(val, str):
        if val.startswith("assets/"):
            out.append((val, source))
    elif isinstance(val, dict):
        for v in val.values():
            _collect_yaml_assets(v, source, out)
    elif isinstance(val, list):
        for item in val:
            _collect_yaml_assets(item, source, out)


def validate_assets(site_path: Path, cfg: dict) -> list:
    """Return list of warning strings for assets/ references that don't exist on disk."""
    refs: list = []

    _collect_yaml_assets(cfg, "config.yml", refs)

    theme_file = cfg.get("theme")
    if theme_file:
        theme_path = site_path / theme_file
        if theme_path.exists():
            try:
                theme_data = yaml.safe_load(theme_path.read_text(encoding="utf-8")) or {}
                _collect_yaml_assets(theme_data, theme_file, refs)
            except (OSError, yaml.YAMLError):
                pass

    for folder in ("pages", "posts"):
        d = site_path / folder
        if not d.is_dir():
            continue
        for md_file in sorted(d.rglob("*.md")):
            try:
                content = md_file.read_text(encoding="utf-8")
                rel = str(md_file.relative_to(site_path)).replace("\\", "/")
                for m in _ASSET_RE.finditer(content):
                    refs.append((m.group(), rel))
            except OSError:
                pass

    warnings = []
    seen: set = set()
    for asset_path, source in refs:
        key = (asset_path, source)
        if key in seen:
            continue
        seen.add(key)
        if not (site_path / asset_path).exists():
            warnings.append(
                f"Warning: asset not found: {asset_path}\n  Referenced in: {source}"
            )
    return warnings


# The renderer parses config.yml/theme.yml/nav.yml and page frontmatter with js-yaml
# in the browser, which enforces the full YAML spec's restriction on which characters
# may appear in a document at all. PyYAML (used by this CLI) is far more lenient and
# accepts things like a stray non-breaking space without complaint, so a file that
# builds cleanly here can still fail at runtime with "the stream contains non-printable
# characters" — usually from copy-pasting text out of a webpage or word processor.
def _is_yaml_printable(cp: int) -> bool:
    return (
        cp in (0x09, 0x0A, 0x0D)
        or (0x20 <= cp <= 0x7E)
        or (0xA1 <= cp <= 0xD7FF and cp not in (0x2028, 0x2029))
        or (0xE000 <= cp <= 0xFFFD and cp != 0xFEFF)
        or (0x10000 <= cp <= 0x10FFFF)
    )


def _find_yaml_unprintable(text: str, start_line: int = 1) -> list:
    """Return [(line, col, codepoint)] — line/col match js-yaml's own 1-indexed
    error-message numbering, so a warning here points at the same spot the
    renderer's runtime error would."""
    problems: list = []
    line, col = start_line, 1
    for ch in text:
        cp = ord(ch)
        if not _is_yaml_printable(cp):
            problems.append((line, col, cp))
        if ch == "\n":
            line += 1
            col = 1
        else:
            col += 1
    return problems


def validate_yaml_printable(site_path: Path, cfg: dict) -> list:
    """Return warning strings for characters that will make the renderer's
    stricter YAML parser fail at runtime, even though this CLI's own YAML
    parsing accepted the file without complaint."""
    warnings: list = []

    def _check(text: str, source: str, start_line: int = 1):
        for line, col, cp in _find_yaml_unprintable(text, start_line):
            warnings.append(
                f"Warning: {source} has a character the renderer's YAML parser will "
                f"reject at ({line}:{col}) — likely a non-breaking space or other "
                f"invisible character from a copy-paste (U+{cp:04X})."
            )

    config_file = site_path / "config.yml"
    if config_file.exists():
        _check(config_file.read_text(encoding="utf-8"), "config.yml")

    theme_name = cfg.get("theme")
    if theme_name:
        theme_file = site_path / theme_name
        if theme_file.exists():
            _check(theme_file.read_text(encoding="utf-8"), theme_name)

    for folder in ("pages", "posts"):
        d = site_path / folder
        if not d.is_dir():
            continue
        for md_file in sorted(d.rglob("*.md")):
            try:
                content = md_file.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                continue
            m = re.match(r"^---\s*\n(.*?)\n---\s*\n", content, re.DOTALL)
            if m:
                rel = str(md_file.relative_to(site_path)).replace("\\", "/")
                _check(m.group(1), f"{rel} frontmatter", start_line=2)

    return warnings


# ─── Icon sync ─────────────────────────────────────────────────

def compute_referenced_icons(site_path: Path, cfg: dict) -> set:
    """Return the set of icon names (without .svg) this site actually needs.

    Starts from CORE_ICONS (rendered unconditionally by index.html) and adds any
    icon named by config.yml/theme.yml: categories-selecticon, nav-section-expand-icon,
    nav-section-collapse-icon, and per-type callout icon overrides. Mirrors the
    preload logic in app/index.html — keep the two in sync.
    """
    icons = set(CORE_ICONS)

    selecticon = cfg.get("categories-selecticon")
    if selecticon:
        icons.add(selecticon)

    theme_file = cfg.get("theme")
    theme_data: dict = {}
    if theme_file:
        theme_path = site_path / theme_file
        if theme_path.exists():
            try:
                theme_data = yaml.safe_load(theme_path.read_text(encoding="utf-8")) or {}
            except (OSError, yaml.YAMLError):
                theme_data = {}

    for key in ("nav-section-expand-icon", "nav-section-collapse-icon"):
        val = theme_data.get(key)
        if val:
            icons.add(val)

    theme_callouts = theme_data.get("callouts") or {}
    for callout_type in ("info", "warning", "success", "error"):
        icon_override = (theme_callouts.get(callout_type) or {}).get("icon")
        if icon_override:
            icons.add(icon_override)

    return icons


def sync_icons(site_path: Path, cfg: dict) -> None:
    """Download any missing referenced icons into assets/icons/, and remove any
    stock icon (from ALL_KNOWN_ICONS) that's no longer referenced. Icons with
    names outside ALL_KNOWN_ICONS are left alone — they may be custom additions.
    """
    icons_dir = site_path / "assets" / "icons"
    referenced = compute_referenced_icons(site_path, cfg)

    added, removed, failed = [], [], []
    root = _local_repo_root()

    for name in sorted(referenced):
        dest = icons_dir / f"{name}.svg"
        if dest.exists():
            continue
        try:
            if root:
                src = root / "app" / "assets" / "icons" / f"{name}.svg"
                data = src.read_bytes() if src.exists() else _http_get(f"{TEMPLATE_BASE_URL}/assets/icons/{name}.svg")
            else:
                data = _http_get(f"{TEMPLATE_BASE_URL}/assets/icons/{name}.svg")
        except (OSError, urllib.error.URLError):
            failed.append(name)
            continue
        icons_dir.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)
        added.append(name)

    if icons_dir.is_dir():
        for f in sorted(icons_dir.glob("*.svg")):
            if f.stem in (ALL_KNOWN_ICONS | LEGACY_ICONS) and f.stem not in referenced:
                f.unlink()
                removed.append(f.stem)

    if added:
        click.echo(f"  Icons downloaded: {', '.join(added)}")
    if removed:
        click.echo(f"  Icons removed (unreferenced): {', '.join(removed)}")
    for name in failed:
        click.echo(click.style(f"  Warning: could not download icon '{name}.svg'", fg="yellow"))


# ─── Core build logic ─────────────────────────────────────────

_TITLE_RE = re.compile(r"<title>[^<]*</title>")


def _patch_html_title(site_path: Path, sitename: str) -> None:
    index = site_path / "index.html"
    if not index.exists():
        return
    html = index.read_text(encoding="utf-8")
    new_html = _TITLE_RE.sub(f"<title>{sitename}</title>", html, count=1)
    if new_html != html:
        index.write_text(new_html, encoding="utf-8")


_SITE_VERSION_BANNER_RE = re.compile(r"CURRENT VERSION:\s*\d+\.\d+(?:\.\d+)?\s*-\s*.*")


def _bump_config_version_marker(site_path: Path) -> bool:
    """Rewrite the CURRENT VERSION banner in a site's config.yml to the running CLI's version.

    Returns True if a banner was found and updated. Returns False if the site
    only carries the legacy first-line marker (predates the banner format) —
    the caller should tell the user to update it by hand.
    """
    config_file = site_path / "config.yml"
    text = config_file.read_text(encoding="utf-8")
    today = datetime.date.today()
    banner = f"CURRENT VERSION: {CLI_VERSION} - {today.day} {today:%B %Y}"
    new_text, n = _SITE_VERSION_BANNER_RE.subn(banner, text, count=1)
    if n == 0:
        return False
    config_file.write_text(new_text, encoding="utf-8")
    return True


def run_build(site_path: Path):
    """Scan pages/ and posts/, write nav.yml and search.json. Raises ClickException on failure."""
    if not site_path.is_dir():
        raise click.ClickException(f"Directory not found: {site_path}")

    site_version = read_site_version(site_path)
    if site_version is None:
        raise click.ClickException(
            "No mdcms version marker found in config.yml. "
            "Is this an mdcms site? Run 'mdcms register' to initialise one."
        )

    status, msg = version_status(site_version)
    if status == "unsupported":
        raise click.ClickException(f"Site version not supported: {msg}")
    if status in ("outdated", "newer"):
        click.echo(click.style(f"Warning: {msg}", fg="yellow"))

    if not (site_path / "pages").is_dir():
        raise click.ClickException("pages/ directory not found in site.")

    cfg = read_config(site_path)

    _ensure_theme_current(site_path, cfg)
    sync_icons(site_path, cfg)

    cat = get_category_info(cfg)

    all_codes = [c for c in ([cat["default_code"]] + cat["codes"]) if c]
    invalid = [c for c in all_codes if not CATEGORY_CODE_RE.match(c)]
    if invalid:
        raise click.ClickException(f"Invalid category code(s): {invalid}")
    if cat["use"] and not cat["default_code"]:
        raise click.ClickException("categories-use: yes but no default-category.code defined.")

    known_codes = set(all_codes) if cat["use"] else set()
    dates_enabled = cat["use"] and str(cfg.get("categories-dates", "no")).lower() in ("yes", "true")

    page_records = scan_and_categorize(site_path / "pages", site_path, known_codes, dates_enabled)
    post_records = scan_and_categorize(site_path / "posts", site_path, known_codes, dates_enabled)
    click.echo(f"  pages/  {len(page_records)} file(s)")
    click.echo(f"  posts/  {len(post_records)} file(s)")

    date_categories: list = []
    if dates_enabled:
        date_categories = sorted(
            {r["code"] for r in page_records + post_records if is_date_category_code(r.get("code"))},
            reverse=True,
        )

    page_groups = group_by_base(page_records)

    existing_nav = read_nav_yml(site_path)
    if existing_nav["warning"]:
        click.echo(click.style(
            f"Warning: {existing_nav['warning']}; starting fresh. Page entries are rebuilt from "
            "frontmatter, but any section metadata the file held (defaultname, sort, parent, "
            "parent-sort, pagesvisibility, categorynames, pagination) is lost — sections will be "
            "re-created with default values.", fg="yellow"))
    existing_sections = existing_nav["sections"]
    existing_pages = existing_nav["pages"]

    primary_entries = [select_primary(v, cat["default_code"]) for v in page_groups.values()]
    sections, auto_created = merge_sections(primary_entries, existing_sections)

    page_nav = build_page_nav(
        page_groups, existing_pages,
        categories_use=cat["use"],
        default_code=cat["default_code"],
    )

    write_nav_yml(site_path, sections, page_nav, categories_use=cat["use"], date_categories=date_categories)
    click.echo("  Wrote nav.yml")
    if date_categories:
        newest = format_date_category(date_categories[0])
        click.echo(click.style(
            f"  {len(date_categories)} date categor{'y' if len(date_categories) == 1 else 'ies'} detected "
            f"(newest: {newest}) — nav will follow default-category regardless of the active date.",
            fg="cyan",
        ))

    draft_codes = {s["code"] for s in sections if s.get("pagesvisibility") == "draft"}
    live_pages = [r for r in page_records if r.get("section-id") not in draft_codes]

    (site_path / "search.json").write_text(
        generate_search_json(
            live_pages + post_records,
            categories_use=cat["use"],
            default_code=cat["default_code"],
        ),
        encoding="utf-8",
    )
    click.echo(f"  Wrote search.json ({len(live_pages) + len(post_records)} entries)")

    _patch_html_title(site_path, cfg.get("sitename", ""))

    pwa_enabled = str(cfg.get("pwa", "no")).lower() in ("yes", "true")
    if pwa_enabled:
        generate_pwa(site_path, cfg)
    else:
        cleanup_pwa(site_path)

    asset_warnings = validate_assets(site_path, cfg)
    for w in asset_warnings:
        click.echo(click.style(w, fg="yellow"))

    yaml_char_warnings = validate_yaml_printable(site_path, cfg)
    for w in yaml_char_warnings:
        click.echo(click.style(w, fg="yellow"))

    if auto_created:
        click.echo(click.style(
            f"\nNotice: {len(auto_created)} section(s) auto-created: {', '.join(auto_created)}\n"
            "Edit nav.yml to set defaultname, sort, parent, or pagesvisibility.",
            fg="cyan",
        ))

    generate_site_manifest(site_path)


# ─── PWA generation ───────────────────────────────────────────

def cleanup_pwa(site_path: Path):
    """When pwa: no, write a self-unregistering service worker and remove manifest.json.

    Browsers keep the previously installed service worker active until a new one is
    installed. Writing a stub that immediately unregisters itself ensures any stale
    caching worker is evicted on the next visit after a pwa: yes → pwa: no change.
    """
    sw = site_path / "service-worker.js"
    sw.write_text(
        "// mdcms: PWA disabled — unregisters any previously installed service worker.\n"
        "self.addEventListener('install', () => self.skipWaiting());\n"
        "self.addEventListener('activate', event => {\n"
        "  event.waitUntil(self.registration.unregister());\n"
        "});\n",
        encoding="utf-8",
    )
    manifest = site_path / "manifest.json"
    if manifest.exists():
        manifest.unlink()
        click.echo("  Removed manifest.json (pwa: no)")
    click.echo("  Wrote service-worker.js (self-unregistering stub, pwa: no)")


def generate_pwa(site_path: Path, cfg: dict):
    """Generate manifest.json and service-worker.js when pwa: yes."""
    pwa_name      = cfg.get("pwa-name", cfg.get("sitename", "MD-CMS Site"))
    pwa_shortname = cfg.get("pwa-shortname", pwa_name)
    pwa_colour    = cfg.get("pwa-colour", "#2563EB")
    favicon       = cfg.get("favicon", "favicon.png")
    icon_src      = f"assets/images/{favicon}"

    icons = []
    if (site_path / icon_src).exists():
        icons = [
            {"src": icon_src, "sizes": "192x192", "type": "image/png", "purpose": "any"},
            {"src": icon_src, "sizes": "512x512", "type": "image/png", "purpose": "any"},
        ]

    # manifest.json
    manifest = {
        "id": "/",
        "name": pwa_name,
        "short_name": pwa_shortname,
        "start_url": "./",
        "display": "standalone",
        "background_color": "#ffffff",
        "theme_color": pwa_colour,
        "icons": icons,
    }
    (site_path / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    click.echo("  Wrote manifest.json")

    # Collect all files to precache
    precache: list = [
        "index.html", "config.yml", "nav.yml", "search.json",
    ]
    theme_file = cfg.get("theme")
    if theme_file and (site_path / theme_file).exists():
        precache.append(theme_file)

    for folder in ("pages", "posts", "assets"):
        d = site_path / folder
        if not d.is_dir():
            continue
        for f in sorted(d.rglob("*")):
            if f.is_file():
                precache.append(str(f.relative_to(site_path)).replace("\\", "/"))

    # Version hash — deterministic from sorted file list
    cache_hash = format(hash(tuple(sorted(precache))) & 0xFFFFFFFF, "08x")
    cache_name = f"mdcms-{cache_hash}"

    urls_js = json.dumps(precache, indent=2, ensure_ascii=False)
    sw = f"""// mdcms service worker — generated by mdcms build
const CACHE_NAME = '{cache_name}';
const PRECACHE_URLS = {urls_js};

self.addEventListener('install', event => {{
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => cache.addAll(PRECACHE_URLS))
  );
  self.skipWaiting();
}});

self.addEventListener('activate', event => {{
  event.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.filter(k => k !== CACHE_NAME).map(k => caches.delete(k)))
    )
  );
  self.clients.claim();
}});

self.addEventListener('fetch', event => {{
  if (event.request.method !== 'GET') return;
  event.respondWith(
    caches.match(event.request).then(cached => cached || fetch(event.request))
  );
}});
"""
    (site_path / "service-worker.js").write_text(sw, encoding="utf-8")
    click.echo(f"  Wrote service-worker.js (cache: {cache_name})")

# ─── HTTP helpers ─────────────────────────────────────────────

def _http_get(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": f"mdcms/{CLI_VERSION}"})
    ctx = ssl.create_default_context(cafile=certifi.where())
    with urllib.request.urlopen(req, timeout=15, context=ctx) as resp:
        return resp.read()


def _http_get_github(url: str) -> bytes:
    """HTTP GET with GitHub API Accept header (for Contents API responses)."""
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": f"mdcms/{CLI_VERSION}",
            "Accept": "application/vnd.github.v3+json",
        },
    )
    ctx = ssl.create_default_context(cafile=certifi.where())
    with urllib.request.urlopen(req, timeout=15, context=ctx) as resp:
        return resp.read()


# ─── Site manifest generation ─────────────────────────────────

def generate_site_manifest(site_path: Path):
    """Write mdcms.json to site_path listing all deployable files and empty dirs."""
    files = []
    empty_dirs = []
    for entry in sorted(site_path.rglob("*")):
        rel = entry.relative_to(site_path)
        # Skip anything inside a hidden directory or with a hidden name
        if any(p.startswith(".") for p in rel.parts):
            continue
        if entry.is_file():
            rel_str = str(rel).replace("\\", "/")
            if rel_str != MANIFEST_FILENAME:
                files.append(rel_str)
        elif entry.is_dir():
            # Only list dirs that have no non-hidden children
            visible = [c for c in entry.iterdir() if not c.name.startswith(".")]
            if not visible:
                empty_dirs.append(str(rel).replace("\\", "/"))

    manifest: dict = {
        "mdcms": read_site_version(site_path) or "0.4",
        "files": files,
    }
    if empty_dirs:
        manifest["dirs"] = empty_dirs

    (site_path / MANIFEST_FILENAME).write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    click.echo(f"  Wrote {MANIFEST_FILENAME} ({len(files)} files)")


# ─── Single-file bundle ────────────────────────────────────────
#
# Produces one self-contained HTML file that embeds config.yml, theme.yml,
# nav.yml, search.json, every page/post, and referenced assets, so the site
# can be opened from any storage medium with no sibling files and no server.
#
# Mechanism: a small shim monkey-patches window.fetch to serve embedded
# content for the paths the renderer already fetches (config/theme/nav/
# search/pages/icons) — the renderer's own JS is untouched. A handful of
# other call sites (favicon, logo, category fonts) build asset paths by
# string-concatenation rather than fetch(), so those specific lines are
# patched, verbatim-match-or-skip, to consult the same embedded map.

_FONT_MIME_BY_EXT = {
    ".woff2": "font/woff2",
    ".woff": "font/woff",
    ".ttf": "font/ttf",
    ".otf": "font/otf",
}

_BUNDLE_LOGO_IMG_SRC = 'src: `assets/images/${config.logo}`'
_BUNDLE_FAVICON_LINE = 'if (link) link.href = `assets/images/${config.favicon}`;'
_BUNDLE_LOGO_FAVICON_LINE = 'if (link) link.href = `assets/images/${config.logo}`;'
_BUNDLE_FONT_FACE_LINE = (
    'const css = `@font-face { font-family: "${family}"; '
    'src: url("assets/fonts/${cat.font}"); }`;'
)
_BUNDLE_FONT_FACE_OBJ_LINE = "const face = new FontFace(family, `url(assets/fonts/${cat.font})`);"
_BUNDLE_BUNNY_GUARD = "if (bunnyFonts.length) {"
_BUNDLE_GOOGLE_GUARD = "if (googleFonts.length) {"

# navigateTo() rewrites window.location's pathname to `basePath + slug` for
# clean-URL pages. basePath is derived from wherever the page was opened, which
# for a bundle opened straight off disk is a directory that doesn't contain the
# bundle file itself — pushState/replaceState to that URL throws a SecurityError
# in any scheme that isn't a real served origin: file:// on desktop, but also
# content:// (Android's "open with browser" from a file manager/download list
# hands the page a content://media/external/... URL, not file://) and likely
# blob:// too. Rather than block-list every opaque scheme a browser might use,
# allow-list the two schemes a real server can actually be reached at — skip
# all three history calls otherwise, so the bundle degrades to in-memory-only
# routing (no address-bar URL, no Back/Forward) instead of throwing and
# aborting navigation.
_BUNDLE_HISTORY_BLOCK_OLD = """    if (historyMode === 'push') {
      // Re-navigating to the URL already showing (e.g. clicking the current
      // nav link again) must not stack a duplicate entry that Back would land
      // on with nothing visibly changing.
      if (u.href === window.location.href) {
        window.history.replaceState(null, '', u);
      } else {
        window.history.pushState(null, '', u);
      }
    } else if (historyMode === 'replace') {
      window.history.replaceState(null, '', u);
    }"""
_BUNDLE_HISTORY_BLOCK_NEW = """    if (window.location.protocol === 'http:' || window.location.protocol === 'https:') {
      if (historyMode === 'push') {
        // Re-navigating to the URL already showing (e.g. clicking the current
        // nav link again) must not stack a duplicate entry that Back would land
        // on with nothing visibly changing.
        if (u.href === window.location.href) {
          window.history.replaceState(null, '', u);
        } else {
          window.history.pushState(null, '', u);
        }
      } else if (historyMode === 'replace') {
        window.history.replaceState(null, '', u);
      }
    }"""

_SCRIPT_SRC_RE = re.compile(r'<script src="(https://[^"]+)"></script>')
_LINK_CSS_RE = re.compile(r'<link rel="stylesheet" href="(https://[^"]+)"([^>]*)>')
_FONT_CSS_URL_RE = re.compile(r'url\((["\']?)(https?://[^)"\']+)\1\)')
_CONTROL_CHAR_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")


def _bundle_escape_js_control_chars(text: str) -> str:
    """Escape raw control bytes as \\xNN — some mobile file-type sniffers (observed:
    NextCloud/OneDrive) misdetect a literal control byte as binary/corrupt content and
    refuse to preview an otherwise-valid text file. A real CDN library can legitimately
    contain one (js-yaml's minified escape-sequence table has a literal BEL and ESC byte)
    when inlined verbatim for --offline. \\xNN is semantically identical inside any JS
    string or regex literal, which is the only place a raw control byte can validly sit
    in already-valid JS source, so this is safe for arbitrary downloaded script content."""
    return _CONTROL_CHAR_RE.sub(lambda m: f"\\x{ord(m.group()):02x}", text)


def _bundle_strip_control_chars(text: str) -> str:
    """Drop stray control bytes from CSS content — CSS has no equivalent short escape
    worth relying on here, and legitimate CSS should never contain one anyway."""
    return _CONTROL_CHAR_RE.sub("", text)


def _bundle_mime_for(path: Path) -> str:
    ext = path.suffix.lower()
    if ext in _FONT_MIME_BY_EXT:
        return _FONT_MIME_BY_EXT[ext]
    mime, _ = mimetypes.guess_type(path.name)
    return mime or "application/octet-stream"


def _bundle_data_uri(path: Path) -> str:
    mime = _bundle_mime_for(path)
    b64 = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{b64}"


def _bundle_collect_asset_refs(site_path: Path, cfg: dict, theme_text: "str | None") -> list:
    """Every 'assets/...' path referenced from config.yml, theme.yml, or page/post bodies."""
    refs: list = []
    _collect_yaml_assets(cfg, "config.yml", refs)
    if theme_text:
        try:
            theme_data = yaml.safe_load(theme_text) or {}
            _collect_yaml_assets(theme_data, "theme.yml", refs)
        except yaml.YAMLError:
            pass
    for folder in ("pages", "posts"):
        d = site_path / folder
        if not d.is_dir():
            continue
        for md_file in sorted(d.rglob("*.md")):
            content = md_file.read_text(encoding="utf-8")
            for m in _ASSET_RE.finditer(content):
                refs.append((m.group(), str(md_file)))
    seen: set = set()
    ordered: list = []
    for asset_path, _source in refs:
        if asset_path in seen:
            continue
        seen.add(asset_path)
        ordered.append(asset_path)
    return ordered


def _bundle_patch_literal(html: str, old: str, new: str, warnings: list, label: str) -> str:
    if old not in html:
        warnings.append(f"bundle: could not find expected snippet for {label} — skipping that patch.")
        return html
    return html.replace(old, new)


def _bundle_parse_font_spec(spec: "str | None") -> "dict | None":
    if not spec:
        return None
    parts = str(spec).split(":")
    if len(parts) >= 3:
        return {"provider": parts[0].strip(), "name": ":".join(parts[1:-1]).strip(), "weight": parts[-1].strip()}
    if len(parts) == 2:
        return {"provider": "bunny", "name": parts[0].strip(), "weight": parts[1].strip()}
    return {"provider": "bunny", "name": parts[0].strip(), "weight": "400"}


def _bundle_inline_webfont_css(css_text: str, warnings: list) -> str:
    def repl(m):
        font_url = m.group(2)
        try:
            font_bytes = _http_get(font_url)
        except Exception as e:
            warnings.append(f"bundle: failed to download web font {font_url}: {e}")
            return m.group(0)
        mime = _bundle_mime_for(Path(font_url.split("?")[0]))
        b64 = base64.b64encode(font_bytes).decode("ascii")
        return f"url(data:{mime};base64,{b64})"
    return _bundle_strip_control_chars(_FONT_CSS_URL_RE.sub(repl, css_text))


def _bundle_offline_webfont_style(cfg: dict, theme_data: dict, warnings: list) -> str:
    """Fetch Bunny/Google web-font CSS + font files, return an inlined <style> block (or '')."""
    src = theme_data or {}
    body = _bundle_parse_font_spec(src.get("font-body") or cfg.get("font-body"))
    heading = _bundle_parse_font_spec(src.get("font-heading") or src.get("font-title") or cfg.get("font-title"))
    code = _bundle_parse_font_spec(src.get("font-code") or cfg.get("font-code"))
    all_fonts = [f for f in (body, heading, code) if f]
    bunny_fonts = [f for f in all_fonts if f["provider"] == "bunny"]
    google_fonts = [f for f in all_fonts if f["provider"] == "google"]

    css_blocks = []
    if bunny_fonts:
        family = "|".join(f"{f['name'].replace(' ', '+')}:{f['weight']}" for f in bunny_fonts)
        url = f"https://fonts.bunny.net/css?family={family}"
        try:
            css_blocks.append(_bundle_inline_webfont_css(_http_get(url).decode("utf-8"), warnings))
        except Exception as e:
            warnings.append(f"bundle: failed to download Bunny Fonts CSS: {e}")
    if google_fonts:
        family = "&".join(f"family={f['name'].replace(' ', '+')}:wght@{f['weight']}" for f in google_fonts)
        url = f"https://fonts.googleapis.com/css2?{family}&display=swap"
        try:
            css_blocks.append(_bundle_inline_webfont_css(_http_get(url).decode("utf-8"), warnings))
        except Exception as e:
            warnings.append(f"bundle: failed to download Google Fonts CSS: {e}")

    if not css_blocks:
        return ""
    return '<style id="mdcms-bundle-webfonts">\n' + "\n".join(css_blocks) + "\n</style>"


def _bundle_inline_vendor_deps(html: str, warnings: list) -> str:
    def script_repl(m):
        url = m.group(1)
        try:
            content = _bundle_escape_js_control_chars(_http_get(url).decode("utf-8"))
            return f"<script>{content}</script>"
        except Exception as e:
            warnings.append(f"bundle: failed to download {url}: {e}")
            return m.group(0)
    html = _SCRIPT_SRC_RE.sub(script_repl, html)

    def link_repl(m):
        url, attrs = m.group(1), m.group(2)
        try:
            content = _bundle_strip_control_chars(_http_get(url).decode("utf-8"))
            return f"<style{attrs}>{content}</style>"
        except Exception as e:
            warnings.append(f"bundle: failed to download {url}: {e}")
            return m.group(0)
    return _LINK_CSS_RE.sub(link_repl, html)


def generate_bundle(site_path: Path, cfg: dict, output: Path, offline: bool) -> list:
    """Assemble a single self-contained HTML file for site_path. Returns a list of warnings."""
    warnings: list = []
    index_file = site_path / "index.html"
    if not index_file.exists():
        raise click.ClickException(f"No index.html found at {site_path}")
    for required in ("nav.yml", "search.json"):
        if not (site_path / required).exists():
            raise click.ClickException(f"{required} not found — run 'mdcms build' first.")

    config_text = (site_path / "config.yml").read_text(encoding="utf-8")
    nav_text = (site_path / "nav.yml").read_text(encoding="utf-8")
    search_text = (site_path / "search.json").read_text(encoding="utf-8")

    theme_file = cfg.get("theme")
    theme_text = None
    if theme_file and (site_path / theme_file).exists():
        theme_text = (site_path / theme_file).read_text(encoding="utf-8")

    bundle_map: dict = {
        "config.yml": config_text,
        "nav.yml": nav_text,
        "search.json": search_text,
    }
    if theme_file and theme_text is not None:
        bundle_map[theme_file] = theme_text

    # Referenced binary/text assets (favicon, logo, category fonts, markdown images) as data: URIs.
    asset_refs = _bundle_collect_asset_refs(site_path, cfg, theme_text)
    for rel in asset_refs:
        asset_path = site_path / rel
        if asset_path.is_file():
            bundle_map[rel] = _bundle_data_uri(asset_path)
        elif not asset_path.is_dir():
            warnings.append(f"bundle: referenced asset not found, left as a broken link: {rel}")

    # Icons: embed every svg under assets/icons/ verbatim (loadIcon() expects raw SVG
    # text, not a data: URI) — wins over any data: URI an icon path also picked up above.
    icons_dir = site_path / "assets" / "icons"
    if icons_dir.is_dir():
        for f in sorted(icons_dir.iterdir()):
            if f.is_file() and f.suffix.lower() == ".svg":
                bundle_map[f"assets/icons/{f.name}"] = f.read_text(encoding="utf-8")

    # Pages/posts: embed raw markdown, with in-body asset references swapped for data: URIs.
    for folder in ("pages", "posts"):
        d = site_path / folder
        if not d.is_dir():
            continue
        for md_file in sorted(d.rglob("*.md")):
            rel = str(md_file.relative_to(site_path)).replace("\\", "/")
            text = md_file.read_text(encoding="utf-8")
            bundle_map[rel] = _ASSET_RE.sub(lambda m: bundle_map.get(m.group(), m.group()), text)

    html = index_file.read_text(encoding="utf-8")

    # Bundle never ships PWA install/service-worker plumbing — a single file has
    # no separate origin for a service worker to manage.
    html = html.replace('<link rel="manifest" href="manifest.json">\n', "")
    html = re.sub(
        r"<script>\nif \('serviceWorker' in navigator\) \{.*?\n</script>\n\n?",
        "",
        html,
        count=1,
        flags=re.DOTALL,
    )

    # Patch the handful of call sites that build asset paths by string
    # concatenation instead of fetch() — point them at the same embedded map.
    html = _bundle_patch_literal(
        html, _BUNDLE_LOGO_IMG_SRC,
        "src: (window.__MDCMS_BUNDLE__ && window.__MDCMS_BUNDLE__['assets/images/' + config.logo]) "
        "|| `assets/images/${config.logo}`",
        warnings, "sidebar/topbar logo image",
    )
    html = _bundle_patch_literal(
        html, _BUNDLE_FAVICON_LINE,
        "if (link) link.href = (window.__MDCMS_BUNDLE__ && "
        "window.__MDCMS_BUNDLE__['assets/images/' + config.favicon]) || `assets/images/${config.favicon}`;",
        warnings, "favicon override (config.favicon)",
    )
    html = _bundle_patch_literal(
        html, _BUNDLE_LOGO_FAVICON_LINE,
        "if (link) link.href = (window.__MDCMS_BUNDLE__ && "
        "window.__MDCMS_BUNDLE__['assets/images/' + config.logo]) || `assets/images/${config.logo}`;",
        warnings, "favicon override (config.logo)",
    )
    html = _bundle_patch_literal(
        html, _BUNDLE_FONT_FACE_LINE,
        'const css = `@font-face { font-family: "${family}"; src: url("'
        '${(window.__MDCMS_BUNDLE__ && window.__MDCMS_BUNDLE__["assets/fonts/" + cat.font]) '
        '|| ("assets/fonts/" + cat.font)}"); }`;',
        warnings, "category font @font-face rule",
    )
    html = _bundle_patch_literal(
        html, _BUNDLE_FONT_FACE_OBJ_LINE,
        'const face = new FontFace(family, `url(${(window.__MDCMS_BUNDLE__ && '
        'window.__MDCMS_BUNDLE__["assets/fonts/" + cat.font]) || ("assets/fonts/" + cat.font)})`);',
        warnings, "category font FontFace object",
    )
    html = _bundle_patch_literal(
        html, _BUNDLE_HISTORY_BLOCK_OLD, _BUNDLE_HISTORY_BLOCK_NEW,
        warnings, "URL history updates (disabled under file://)",
    )

    offline_marker = "true" if offline else "false"
    if offline:
        theme_data = {}
        if theme_text:
            try:
                theme_data = yaml.safe_load(theme_text) or {}
            except yaml.YAMLError:
                theme_data = {}
        webfont_style = _bundle_offline_webfont_style(cfg, theme_data, warnings)
        if webfont_style:
            html = html.replace("</head>", webfont_style + "\n</head>", 1)
        html = _bundle_patch_literal(
            html, _BUNDLE_BUNNY_GUARD,
            "if (bunnyFonts.length && !window.__MDCMS_BUNDLE_OFFLINE__) {",
            warnings, "Bunny Fonts CDN guard",
        )
        html = _bundle_patch_literal(
            html, _BUNDLE_GOOGLE_GUARD,
            "if (googleFonts.length && !window.__MDCMS_BUNDLE_OFFLINE__) {",
            warnings, "Google Fonts CDN guard",
        )
        html = _bundle_inline_vendor_deps(html, warnings)

    # Escape "</" so embedded content (e.g. markdown containing a literal "</script>")
    # can't prematurely close this <script> tag when the browser's HTML parser runs.
    bundle_json = json.dumps(bundle_map, ensure_ascii=False).replace("</", "<\\/")

    shim = (
        "<script>\n"
        f"window.__MDCMS_BUNDLE__ = {bundle_json};\n"
        f"window.__MDCMS_BUNDLE_OFFLINE__ = {offline_marker};\n"
        "(function() {\n"
        "  var bundle = window.__MDCMS_BUNDLE__;\n"
        "  var realFetch = window.fetch.bind(window);\n"
        "  window.fetch = function(input, init) {\n"
        "    var url = (typeof input === 'string' ? input : input.url).replace(/^\\.?\\//, '');\n"
        "    if (Object.prototype.hasOwnProperty.call(bundle, url)) {\n"
        "      return Promise.resolve(new Response(bundle[url], { status: 200 }));\n"
        "    }\n"
        "    return realFetch(input, init);\n"
        "  };\n"
        "})();\n"
        "</script>\n"
    )
    html = html.replace("<head>\n", "<head>\n" + shim, 1)

    # A leading UTF-8 BOM is valid before <!doctype html> (browsers strip it) and
    # helps naive file-type/encoding sniffers used by some mobile cloud-storage
    # previewers (observed misbehaviour: OneDrive) correctly identify the file as
    # UTF-8 text instead of misdetecting ordinary multi-byte characters as binary.
    output.write_bytes(b"\xef\xbb\xbf" + html.encode("utf-8"))
    return warnings


# ─── Template download ────────────────────────────────────────

def _parse_github_url(url: str) -> "tuple | None":
    """Return (owner, repo, branch, subpath) for a GitHub URL, else None."""
    m = GITHUB_URL_RE.match(url.strip())
    if not m:
        return None
    owner = m.group(1)
    repo = m.group(2)
    branch = m.group(3) or "main"
    subpath = (m.group(4) or "").strip("/")
    return owner, repo, branch, subpath


def _fetch_manifest(base_url: str) -> "dict | None":
    """Fetch mdcms.json from base_url. Returns parsed dict or None if not found."""
    url = base_url.rstrip("/") + "/" + MANIFEST_FILENAME
    try:
        data = _http_get(url)
        manifest = json.loads(data.decode("utf-8"))
        if isinstance(manifest.get("files"), list):
            return manifest
    except Exception:
        pass
    return None


def _safe_dest(dest_root: Path, rel: str) -> Path:
    """Resolve `rel` under `dest_root`, refusing any path that escapes it.

    The manifest (mdcms.json) and the GitHub Contents API responses are remote,
    attacker-controllable input when `register --from <url>` is used. Without
    this guard an absolute path or `../` traversal in a manifest would let a
    malicious template write files anywhere on disk (`dest / "/etc/x"` resolves
    to `/etc/x` in pathlib).
    """
    rel_str = str(rel)
    rel_path = Path(rel_str)
    if (
        rel_path.is_absolute()
        or rel_str.startswith(("/", "\\"))
        or "\\" in rel_str
        or ".." in rel_path.parts
    ):
        raise click.ClickException(f"Refusing unsafe path in template: {rel_str!r}")
    root = dest_root.resolve()
    target = (root / rel_path).resolve()
    if target != root and root not in target.parents:
        raise click.ClickException(f"Refusing path outside destination: {rel_str!r}")
    return target


def _apply_manifest(manifest: dict, base_url: str, dest: Path):
    """Download all files in manifest from base_url into dest."""
    base = base_url.rstrip("/")
    for rel in manifest.get("files", []):
        file_dest = _safe_dest(dest, rel)
        file_dest.parent.mkdir(parents=True, exist_ok=True)
        click.echo(f"  {rel}")
        file_dest.write_bytes(_http_get(f"{base}/{rel}"))
    for rel in manifest.get("dirs", []):
        _safe_dest(dest, rel).mkdir(parents=True, exist_ok=True)


def _download_tree_api(api_url: str, dest: Path, depth: int = 0):
    """Recursively download from the GitHub Contents API (fallback when no manifest)."""
    items = json.loads(_http_get_github(api_url).decode("utf-8"))
    for item in items:
        # item["name"] is a single path component from the API; refuse anything
        # that isn't (defence in depth against a spoofed/hostile response).
        item_dest = _safe_dest(dest, item["name"])
        if item["type"] == "dir":
            item_dest.mkdir(parents=True, exist_ok=True)
            _download_tree_api(item["url"], item_dest, depth + 1)
        elif item["type"] == "file":
            click.echo(f"  {'  ' * depth}{item['name']}")
            item_dest.parent.mkdir(parents=True, exist_ok=True)
            item_dest.write_bytes(_http_get(item["download_url"]))


def download_template(dest: Path, source: str = None):
    """Download a site template from a URL or GitHub address.

    source may be:
      - A GitHub repo URL (https://github.com/owner/repo or .../tree/branch/path)
      - Any HTTPS URL pointing to a deployed mdcms site that has mdcms.json
      - None — uses the built-in mdcms starter template
    """
    effective = (source or TEMPLATE_BASE_URL).rstrip("/")
    click.echo(f"Downloading site template into {dest} ...")
    try:
        github = _parse_github_url(effective)
        if github:
            owner, repo, branch, subpath = github
            raw_base = f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}"
            if subpath:
                raw_base = f"{raw_base}/{subpath}"
            manifest = _fetch_manifest(raw_base)
            if manifest is not None:
                _apply_manifest(manifest, raw_base, dest)
            else:
                # No manifest — fall back to GitHub Contents API tree walk
                api_url = f"https://api.github.com/repos/{owner}/{repo}/contents"
                if subpath:
                    api_url = f"{api_url}/{subpath}"
                if branch not in ("main", "master"):
                    api_url += f"?ref={branch}"
                _download_tree_api(api_url, dest)
        else:
            manifest = _fetch_manifest(effective)
            if manifest is None:
                if source:
                    raise click.ClickException(
                        f"No {MANIFEST_FILENAME} found at {effective}.\n"
                        "The URL must point to a deployed mdcms site with a manifest, "
                        "or to a GitHub repository."
                    )
                raise click.ClickException(
                    f"Could not fetch template manifest from {effective}"
                )
            _apply_manifest(manifest, effective, dest)
        click.echo(click.style("Template downloaded successfully.", fg="green"))
    except urllib.error.URLError as e:
        raise click.ClickException(f"Download failed: {e}")


# ─── Config editing ───────────────────────────────────────────

# Top-level scalar keys the `config` command may edit. Structured blocks
# (categories, callouts, and dict-form offline-message) are intentionally
# excluded — they are edited by hand.
EDITABLE_KEYS = [
    "sitename", "navigation", "theme", "homepage", "sitedescription",
    "logo", "favicon", "footer", "nav-position", "search", "default-theme",
    "pwa", "pwa-name", "pwa-shortname", "pwa-colour", "offline-message",
    "categories-use", "categories-dates", "categories-sectionnames",
]

_NAV_CHOICES = ["sidebar", "topbar"]
_THEME_MODE_CHOICES = ["light", "dark", "system"]
_NAV_POS_CHOICES = ["left", "right"]

_CONFIG_KEY_RE = re.compile(r"^(#\s*)?([A-Za-z][\w-]*):(\s*)(.*)$")


def _format_config_scalar(value) -> str:
    """Render a Python value as a YAML scalar, quoting only when necessary."""
    s = str(value)
    if s == "":
        return '""'
    if s.lower() in ("yes", "no", "true", "false", "null", "on", "off"):
        return s  # keep boolean/keyword words bare
    if (
        s != s.strip()
        or any(c in s for c in ":#'\"")
        or s[0] in "!&*[]{}|>@`%,?-"
    ):
        return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'
    return s


def set_config_keys(site_path: Path, updates: dict) -> list:
    """Update or insert top-level scalar keys in config.yml, preserving comments.

    `updates` maps key -> value (a value of None deletes the key line if present).
    Existing lines — including commented example lines — are replaced in place so
    the file's structure and surrounding comments survive. Keys not found are
    appended at the end. Keys whose current value is a structured block (a mapping
    or list) are left untouched and returned in the skipped list.
    """
    config_file = site_path / "config.yml"
    lines = config_file.read_text(encoding="utf-8").split("\n")
    remaining = dict(updates)
    skipped: list = []
    out: list = []
    i = 0
    while i < len(lines):
        line = lines[i]
        m = _CONFIG_KEY_RE.match(line)
        if m and m.group(2) in remaining:
            key = m.group(2)
            after = m.group(4).strip()
            commented = m.group(1) is not None
            next_indented = i + 1 < len(lines) and re.match(r"^\s+\S", lines[i + 1])
            if not commented and after == "" and next_indented:
                # Active key introducing a block mapping/list — don't clobber it.
                remaining.pop(key)
                skipped.append(key)
                out.append(line)
                i += 1
                continue
            val = remaining.pop(key)
            if val is not None:
                out.append(f"{key}: {_format_config_scalar(val)}")
            i += 1
            continue
        out.append(line)
        i += 1

    leftover = {k: v for k, v in remaining.items() if v is not None}
    if leftover:
        if out and out[-1].strip() != "":
            out.append("")
        for k, v in leftover.items():
            out.append(f"{k}: {_format_config_scalar(v)}")

    config_file.write_text("\n".join(out), encoding="utf-8")
    return skipped


def set_config_block(site_path: Path, key: str, block_lines: list) -> None:
    """Replace (or append) a top-level structured block in config.yml.

    `block_lines` is the full replacement for the block, starting with the
    `key:` line itself and including all of its indented children. Any
    existing occurrence of the key — active or commented-out — and its
    indented body are dropped first. Used for blocks `set_config_keys`
    intentionally won't touch (`default-category`, `categories`).
    """
    config_file = site_path / "config.yml"
    lines = config_file.read_text(encoding="utf-8").split("\n")
    out: list = []
    i = 0
    replaced = False
    while i < len(lines):
        line = lines[i]
        m = _CONFIG_KEY_RE.match(line)
        if m and m.group(2) == key:
            i += 1
            while i < len(lines) and re.match(r"^\s+\S", lines[i]):
                i += 1
            if not replaced:
                out.extend(block_lines)
                replaced = True
            continue
        out.append(line)
        i += 1

    if not replaced:
        if out and out[-1].strip() != "":
            out.append("")
        out.extend(block_lines)

    if out and out[-1] != "":
        out.append("")  # keep the file newline-terminated
    config_file.write_text("\n".join(out), encoding="utf-8")


def _top_level_key_lines(text: str) -> dict:
    """Map each top-level config key (active or commented-out example) to its line index."""
    keys: dict = {}
    for i, line in enumerate(text.split("\n")):
        m = _CONFIG_KEY_RE.match(line)
        if m:
            keys.setdefault(m.group(2), i)
    return keys


def sync_config_keys(site_path: Path, template_text: str) -> list:
    """Append config.yml keys the latest template declares (active or commented-out)
    that the site's config.yml doesn't mention at all yet — new features introduced
    since the site was last updated.

    Every key, value, and comment already in the site's config.yml is left exactly
    as-is; only wholly new top-level keys are appended, copied verbatim (including
    whether the template leaves them commented-out) at the end of the file. Returns
    the list of key names added, in the order the template declares them.
    """
    config_file = site_path / "config.yml"
    site_text = config_file.read_text(encoding="utf-8")
    site_keys = _top_level_key_lines(site_text)

    template_lines = template_text.split("\n")
    template_keys = _top_level_key_lines(template_text)

    missing = [k for k in template_keys if k not in site_keys]
    if not missing:
        return []

    new_lines: list = []
    for key in missing:
        start = template_keys[key]
        new_lines.append(template_lines[start])
        j = start + 1
        while j < len(template_lines) and re.match(r"^\s+\S", template_lines[j]):
            new_lines.append(template_lines[j])
            j += 1

    out = site_text.rstrip("\n").split("\n")
    out.append("")
    out.append(f"# ── New since v{CLI_VERSION}, added by `mdcms update` — review and uncomment as needed ──")
    out.extend(new_lines)
    out.append("")
    config_file.write_text("\n".join(out), encoding="utf-8")
    return missing


def _validate_updates(updates: dict):
    choices = {
        "navigation": _NAV_CHOICES,
        "default-theme": _THEME_MODE_CHOICES,
        "nav-position": _NAV_POS_CHOICES,
        "categories-sectionnames": ["same", "per-category"],
    }
    for key, allowed in choices.items():
        if key in updates and str(updates[key]) not in allowed:
            raise click.ClickException(
                f"Invalid value for {key}: '{updates[key]}'. Allowed: {', '.join(allowed)}"
            )
    for key in ("pwa", "categories-use", "categories-dates"):
        if key in updates and str(updates[key]).lower() not in ("yes", "no", "true", "false"):
            raise click.ClickException(f"{key} must be 'yes' or 'no'.")


# ─── Category editing ──────────────────────────────────────────

# Preferred key order when re-emitting a category entry. Any keys beyond
# these (set by hand — font, line-height, etc.) are kept, just appended after.
_CATEGORY_FIELD_ORDER = [
    "code", "name", "message", "name-latin", "direction",
    "notfoundmessage", "visibilityifnocontent", "pagenotfoundmessage",
    "font", "line-height",
]


def _ordered_category_keys(cat: dict) -> list:
    return [k for k in _CATEGORY_FIELD_ORDER if k in cat] + \
           [k for k in cat if k not in _CATEGORY_FIELD_ORDER]


def _emit_default_category_block(cat: dict) -> list:
    lines = ["default-category:"]
    for k in _ordered_category_keys(cat):
        lines.append(f"  {k}: {_emit_value(cat[k])}")
    return lines


def _emit_categories_list_block(categories: list) -> list:
    lines = ["categories:"]
    for cat in categories:
        first = True
        for k in _ordered_category_keys(cat):
            bullet = "  - " if first else "    "
            lines.append(f"{bullet}{k}: {_emit_value(cat[k])}")
            first = False
    return lines


def write_default_category(site_path: Path, cat: dict) -> None:
    set_config_block(site_path, "default-category", _emit_default_category_block(cat))


def write_categories_list(site_path: Path, categories: list) -> None:
    set_config_block(site_path, "categories", _emit_categories_list_block(categories))


def validate_category_code(code: str, existing_codes: "set | None" = None) -> None:
    """Raise ClickException if `code` isn't usable as a manually-declared category code."""
    if not code:
        raise click.ClickException("Category code cannot be blank.")
    if not CATEGORY_CODE_RE.match(code):
        raise click.ClickException(
            f"Invalid category code '{code}'. Use only letters, numbers, and hyphens."
        )
    if is_date_category_code(code):
        raise click.ClickException(
            f"'{code}' looks like a YYYYMMDD date and is reserved for auto-detected date "
            "categories (categories-dates: yes) — pick a non-numeric code."
        )
    if existing_codes and code in existing_codes:
        raise click.ClickException(f"Category code '{code}' already exists.")


# ─── Theme library ────────────────────────────────────────────

def _local_repo_root() -> "Path | None":
    """If mdcms.py is running from a checkout that ships the theme library, return its root."""
    root = Path(__file__).resolve().parent
    if (root / THEMES_MANIFEST_PATH).exists() and (root / "themes").is_dir():
        return root
    return None


def load_theme_index() -> list:
    """Return the theme manifest as a list of {family, file, path, label} dicts.

    Uses the local checkout when available (development), otherwise fetches the
    manifest published on the repository's main branch.
    """
    root = _local_repo_root()
    try:
        if root:
            raw = (root / THEMES_MANIFEST_PATH).read_text(encoding="utf-8")
        else:
            raw = _http_get(f"{REPO_RAW_BASE}/{THEMES_MANIFEST_PATH}").decode("utf-8")
    except (OSError, urllib.error.URLError) as e:
        raise click.ClickException(f"Could not load theme index: {e}")
    try:
        entries = json.loads(raw)
    except json.JSONDecodeError as e:
        raise click.ClickException(f"Theme index is not valid JSON: {e}")
    return [
        e for e in entries
        if isinstance(e, dict) and e.get("path") and e.get("file") and e.get("family")
    ]


def _fetch_theme_bytes(entry: dict) -> bytes:
    root = _local_repo_root()
    if root:
        local = root / entry["path"]
        if local.exists():
            return local.read_bytes()
    return _http_get(f"{REPO_RAW_BASE}/{entry['path']}")


def install_theme(site_path: Path, entry: dict) -> str:
    """Download a theme into assets/themes/ and point config.yml's theme: at it.

    Returns the site-relative path written to config.yml.
    """
    dest_dir = site_path / "assets" / "themes"
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / entry["file"]
    dest.write_bytes(_fetch_theme_bytes(entry))
    rel = f"assets/themes/{entry['file']}"
    set_config_keys(site_path, {"theme": rel})
    return rel


def _ensure_theme_current(site_path: Path, cfg: dict):
    """Check the site's installed theme against MIN_SUPPORTED_THEME_VERSION.

    Themes carry their own `# mdcms theme vX.Y[.Z]` marker. When the file a
    site's `theme:` points at is unmarked or older than the minimum, fetch a
    fresh copy of the same theme from the library and write it back to the very
    path config.yml names — leaving the site's `theme:` key untouched. Library
    themes (`assets/themes/<file>.yaml`) refresh in place; a starter `theme.yml`
    is not in the library, so it only warns (reinstall via `mdcms config`).
    Never fatal: any problem is reported as a warning so the build still runs.
    """
    theme_rel = cfg.get("theme")
    if not theme_rel:
        return
    theme_path = site_path / theme_rel
    if not theme_path.exists():
        return

    tv = read_theme_version(theme_path)
    if tv is not None and _parse_ver(tv) >= _parse_ver(MIN_SUPPORTED_THEME_VERSION):
        return  # already current

    filename = Path(theme_rel).name
    old = f"v{tv}" if tv else "unversioned"
    try:
        entries = load_theme_index()
    except click.ClickException as e:
        click.echo(click.style(
            f"Warning: theme '{filename}' is {old} (needs v{MIN_SUPPORTED_THEME_VERSION}); "
            f"could not reach the theme library to refresh it: {e}", fg="yellow"))
        return

    match = next((e for e in entries if e["file"].lower() == filename.lower()), None)
    if not match:
        click.echo(click.style(
            f"Warning: theme '{filename}' is {old} (needs v{MIN_SUPPORTED_THEME_VERSION}) "
            f"but is not in the theme library, so it can't be auto-refreshed. "
            f"Install a current theme with 'mdcms config --theme <name>' "
            f"or bring its marker up to date manually.", fg="yellow"))
        return

    try:
        new_bytes = _fetch_theme_bytes(match)
    except (OSError, urllib.error.URLError) as e:
        click.echo(click.style(
            f"Warning: theme '{filename}' is {old} but could not be refreshed: {e}", fg="yellow"))
        return

    # Only overwrite when the library copy is actually newer. When the source
    # itself is stale (e.g. building from a checkout whose themes/ hasn't been
    # synced), rewriting would be a no-op that repeats on every build — warn
    # about the library instead of claiming a bogus "v0.4 → v0.4" update.
    new_v = theme_version_from_text(new_bytes.decode("utf-8", "replace"))
    if new_v is None or _parse_ver(new_v) < _parse_ver(MIN_SUPPORTED_THEME_VERSION):
        src = f"v{new_v}" if new_v else "unversioned"
        click.echo(click.style(
            f"Warning: theme '{filename}' is {old}, but the copy in the theme library "
            f"is itself {src} (below v{MIN_SUPPORTED_THEME_VERSION}) — not refreshing. "
            f"The theme library needs updating.", fg="yellow"))
        return

    theme_path.write_bytes(new_bytes)
    click.echo(click.style(
        f"  Updated theme '{filename}' ({old} → v{new_v}) — refreshed from the theme library.",
        fg="cyan"))


def _resolve_theme_query(entries: list, query: str) -> dict:
    """Resolve a non-interactive --theme query to exactly one theme entry."""
    q = query.strip().lower()
    exact = [
        e for e in entries
        if q in (e["file"].lower(), e["file"].lower().rsplit(".", 1)[0],
                 e["label"].lower(), e["path"].lower())
    ]
    matches = exact or [
        e for e in entries
        if q in e["label"].lower() or q in e["file"].lower() or q in e["family"].lower()
    ]
    if not matches:
        raise click.ClickException(
            f"No theme matched '{query}'. Run 'mdcms config --list-themes' to browse."
        )
    if len(matches) > 1:
        listing = "\n".join(
            f"  - {e['family']} — {e['label']}  [{e['file']}]" for e in matches[:15]
        )
        extra = "" if len(matches) <= 15 else f"\n  ... and {len(matches) - 15} more"
        raise click.ClickException(
            f"'{query}' matches {len(matches)} themes:\n{listing}{extra}\nBe more specific."
        )
    return matches[0]


def _print_theme_list(entries: list):
    current_family = None
    for e in sorted(entries, key=lambda x: (x["family"].lower(), x["label"].lower())):
        if e["family"] != current_family:
            current_family = e["family"]
            click.echo(click.style(f"\n{current_family}", bold=True))
        click.echo(f"  {e['label']:<34} {e['file']}")
    click.echo(f"\n{len(entries)} themes available.")


def _pick_and_install_theme(site_path: Path):
    entries = load_theme_index()
    families = sorted({e["family"] for e in entries})
    click.echo("\nTheme families:")
    for idx, fam in enumerate(families, 1):
        count = sum(1 for e in entries if e["family"] == fam)
        click.echo(f"  {idx:>2}. {fam} ({count})")

    sel = click.prompt(
        "\nEnter a family number, a search keyword, or blank to cancel",
        default="", show_default=False,
    ).strip()
    if sel == "":
        click.echo("Cancelled.")
        return

    if sel.isdigit() and 1 <= int(sel) <= len(families):
        subset = [e for e in entries if e["family"] == families[int(sel) - 1]]
    else:
        q = sel.lower()
        subset = [
            e for e in entries
            if q in e["label"].lower() or q in e["family"].lower() or q in e["file"].lower()
        ]
    if not subset:
        click.echo("No themes matched.")
        return

    click.echo("")
    for idx, e in enumerate(subset, 1):
        click.echo(f"  {idx:>2}. {e['family']} — {e['label']}  [{e['file']}]")
    pick = click.prompt(
        "\nEnter a theme number to install (blank to cancel)",
        default="", show_default=False,
    ).strip()
    if not (pick.isdigit() and 1 <= int(pick) <= len(subset)):
        click.echo("Cancelled.")
        return

    entry = subset[int(pick) - 1]
    click.echo(f"Downloading '{entry['label']}' ...")
    rel = install_theme(site_path, entry)
    click.echo(click.style(f"Installed → {rel}", fg="green"))
    click.echo(click.style(f"Set theme: {rel} in config.yml", fg="green"))


# ─── Interactive config editor ────────────────────────────────

def _prompt_scalar(site_path: Path, cfg: dict, key: str, label: str, choices=None):
    current = cfg.get(key)
    if choices:
        default = str(current) if current in choices else choices[0]
        val = click.prompt(label, default=default, type=click.Choice(choices))
    else:
        default = str(current) if current is not None else ""
        val = click.prompt(f"{label} (blank = keep current)", default=default,
                           show_default=bool(default)).strip()
        if val == "":
            click.echo("  (unchanged)")
            return
    set_config_keys(site_path, {key: val})
    click.echo(click.style(f"  {key} = {val}", fg="green"))


def _edit_pwa(site_path: Path, cfg: dict):
    enabled = str(cfg.get("pwa", "no")).lower() in ("yes", "true")
    new_enabled = click.confirm("Enable PWA (installable / offline app)?", default=enabled)
    updates = {"pwa": "yes" if new_enabled else "no"}
    if new_enabled:
        name = click.prompt("PWA name", default=str(cfg.get("pwa-name", cfg.get("sitename", ""))))
        updates["pwa-name"] = name
        updates["pwa-shortname"] = click.prompt(
            "PWA short name", default=str(cfg.get("pwa-shortname", name))
        )
        updates["pwa-colour"] = click.prompt(
            "PWA theme colour (hex)", default=str(cfg.get("pwa-colour", "#2563EB"))
        )
    set_config_keys(site_path, updates)
    click.echo(click.style("  PWA settings updated.", fg="green"))
    if new_enabled and not (site_path / "assets" / "images" / str(cfg.get("favicon", "favicon.png"))).exists():
        click.echo(click.style(
            "  Note: add a 192×192 favicon.png in assets/images/ for the install icon.",
            fg="yellow",
        ))


def _prompt_category_fields(existing: dict) -> dict:
    """Prompt for the common category fields, merged onto `existing` so any
    hand-set fields this prompt doesn't cover (font, line-height, ...) survive."""
    entry = dict(existing)
    name = click.prompt("Display name", default=existing.get("name", "")).strip()
    if not name:
        raise click.ClickException("Display name cannot be blank.")
    entry["name"] = name
    name_latin = click.prompt(
        "Latin-script name (blank = none)", default=existing.get("name-latin", ""), show_default=False
    ).strip()
    if name_latin:
        entry["name-latin"] = name_latin
    else:
        entry.pop("name-latin", None)
    entry["direction"] = click.prompt(
        "Text direction", type=click.Choice(["ltr", "rtl"]), default=existing.get("direction", "ltr")
    )
    return entry


def _pick_category(categories: list, prompt_label: str) -> "dict | None":
    if not categories:
        click.echo("No categories to pick from.")
        return None
    for idx, c in enumerate(categories, 1):
        click.echo(f"  {idx}. {c.get('code')} — {c.get('name', '')}")
    pick = click.prompt(prompt_label, type=int, default=0)
    if not (1 <= pick <= len(categories)):
        click.echo("Cancelled.")
        return None
    return categories[pick - 1]


def _toggle_categories_use(site_path: Path):
    cfg = read_config(site_path)
    currently_on = str(cfg.get("categories-use", "no")).lower() in ("yes", "true")
    new_on = click.confirm("Enable the category system (categories-use)?", default=currently_on)
    if new_on and not currently_on and not (cfg.get("default-category") or {}).get("code"):
        click.echo("No default-category is set yet — let's set one now.")
        _set_default_category(site_path)
    set_config_keys(site_path, {"categories-use": "yes" if new_on else "no"})
    click.echo(click.style(f"  categories-use = {'yes' if new_on else 'no'}", fg="green"))


def _toggle_categories_dates(site_path: Path):
    cfg = read_config(site_path)
    currently_on = str(cfg.get("categories-dates", "no")).lower() in ("yes", "true")
    new_on = click.confirm(
        "Auto-detect page.YYYYMMDD.md filename suffixes as date categories?", default=currently_on
    )
    set_config_keys(site_path, {"categories-dates": "yes" if new_on else "no"})
    click.echo(click.style(f"  categories-dates = {'yes' if new_on else 'no'}", fg="green"))
    if new_on and not currently_on:
        click.echo("  Run 'mdcms build' to detect existing date-suffixed pages.")


def _set_default_category(site_path: Path):
    cfg = read_config(site_path)
    default_cat = cfg.get("default-category") or {}
    categories = [c for c in (cfg.get("categories") or []) if isinstance(c, dict)]
    old_code = default_cat.get("code")

    code = click.prompt("Default category code", default=old_code or "").strip()
    validate_category_code(code)

    entry = _prompt_category_fields(default_cat if old_code == code else {})
    entry["code"] = code

    if old_code and old_code != code and not any(c.get("code") == old_code for c in categories):
        click.echo(click.style(
            f"  Note: '{old_code}' was the previous default and isn't in the categories list — "
            f"keeping it as a regular category so existing *.{old_code}.md pages stay recognised.",
            fg="yellow",
        ))
        write_categories_list(site_path, categories + [dict(default_cat)])

    write_default_category(site_path, entry)
    click.echo(click.style(f"  default-category = {code} ({entry['name']})", fg="green"))


def _add_category(site_path: Path):
    cfg = read_config(site_path)
    default_cat = cfg.get("default-category") or {}
    categories = [c for c in (cfg.get("categories") or []) if isinstance(c, dict)]
    existing_codes = {default_cat.get("code")} | {c.get("code") for c in categories}

    code = click.prompt("New category code").strip()
    validate_category_code(code, existing_codes)

    entry = _prompt_category_fields({"code": code})
    entry["code"] = code
    write_categories_list(site_path, categories + [entry])
    click.echo(click.style(f"  Added category '{code}' ({entry['name']}).", fg="green"))


def _edit_category(site_path: Path):
    cfg = read_config(site_path)
    categories = [c for c in (cfg.get("categories") or []) if isinstance(c, dict)]
    target = _pick_category(categories, "Category number to edit (0 = cancel)")
    if target is None:
        return
    updated = _prompt_category_fields(target)
    new_list = [updated if c.get("code") == target.get("code") else c for c in categories]
    write_categories_list(site_path, new_list)
    click.echo(click.style(f"  Updated category '{target['code']}'.", fg="green"))


def _remove_category(site_path: Path):
    cfg = read_config(site_path)
    categories = [c for c in (cfg.get("categories") or []) if isinstance(c, dict)]
    target = _pick_category(categories, "Category number to remove (0 = cancel)")
    if target is None:
        return
    click.confirm(
        f"Remove category '{target['code']}'? Existing .{target['code']}.md page files "
        "are left on disk untouched.",
        abort=True,
    )
    new_list = [c for c in categories if c.get("code") != target.get("code")]
    write_categories_list(site_path, new_list)
    click.echo(click.style(f"  Removed category '{target['code']}'.", fg="green"))


def _manage_categories(site_path: Path):
    click.echo(click.style(f"\nCategories — {site_path}", bold=True))
    while True:
        cfg = read_config(site_path)
        use = str(cfg.get("categories-use", "no")).lower() in ("yes", "true")
        dates = str(cfg.get("categories-dates", "no")).lower() in ("yes", "true")
        default_cat = cfg.get("default-category") or {}
        categories = [c for c in (cfg.get("categories") or []) if isinstance(c, dict)]

        click.echo("\nCurrent settings:")
        click.echo(f"   categories-use   : {'yes' if use else 'no'}")
        click.echo(f"   categories-dates : {'yes' if dates else 'no'} (auto-detect page.YYYYMMDD.md as categories)")
        if use:
            click.echo(f"   default          : {default_cat.get('code', '(not set)')} — {default_cat.get('name', '')}")
            if categories:
                click.echo("   categories       :")
                for c in categories:
                    click.echo(f"       {c.get('code', '?'):<10} {c.get('name', '')}")
            else:
                click.echo("   categories       : (none besides the default)")

        menu = [
            ("Enable/disable categories", lambda: _toggle_categories_use(site_path)),
            ("Enable/disable date categories", lambda: _toggle_categories_dates(site_path)),
            ("Set default category", lambda: _set_default_category(site_path)),
            ("Add a category", lambda: _add_category(site_path)),
            ("Edit a category", lambda: _edit_category(site_path)),
            ("Remove a category", lambda: _remove_category(site_path)),
        ]
        click.echo("\nWhat would you like to change?")
        for idx, (label, _) in enumerate(menu, 1):
            click.echo(f"  {idx}. {label}")
        click.echo("  0. Back")

        choice = click.prompt("Select", type=int, default=0)
        if choice == 0:
            break
        if 1 <= choice <= len(menu):
            try:
                menu[choice - 1][1]()
            except click.Abort:
                click.echo("\nCancelled.")
            except click.ClickException as e:
                click.echo(click.style(f"  Error: {e.format_message()}", fg="red"))
        else:
            click.echo("Invalid selection.")


# ─── Section editing (nav.yml) ─────────────────────────────────

def _sorted_sections(sections: list) -> list:
    return sorted(sections, key=lambda s: (s.get("sort") or 999, s.get("code", "")))


def _pick_section(sections: list, prompt_label: str) -> "dict | None":
    if not sections:
        click.echo("No sections yet.")
        return None
    ordered = _sorted_sections(sections)
    for idx, s in enumerate(ordered, 1):
        parent = f" (child of {s['parent']})" if s.get("parent") else ""
        click.echo(f"  {idx}. {s.get('code')} — {s.get('defaultname', s.get('code'))}{parent}")
    pick = click.prompt(prompt_label, type=int, default=0)
    if not (1 <= pick <= len(ordered)):
        click.echo("Cancelled.")
        return None
    return ordered[pick - 1]


def _next_section_sort(sections: list) -> int:
    used = {s.get("sort") for s in sections if isinstance(s.get("sort"), int)}
    sort = 100
    while sort in used:
        sort += 10
    return sort


def _save_sections(site_path: Path, sections: list, nav: dict) -> None:
    cat = get_category_info(read_config(site_path))
    write_nav_yml(
        site_path, sections, nav["pages"],
        categories_use=cat["use"], date_categories=nav["date_categories"],
    )


def _add_section(site_path: Path):
    nav = read_nav_yml_for_edit(site_path)
    sections = nav["sections"]
    code = click.prompt("New section code (letters, numbers, hyphens)").strip()
    if not code:
        raise click.ClickException("Section code cannot be blank.")
    if not CATEGORY_CODE_RE.match(code):
        raise click.ClickException(f"Invalid section code '{code}'. Use only letters, numbers, and hyphens.")
    if any(s.get("code") == code for s in sections):
        raise click.ClickException(f"Section '{code}' already exists.")
    default_name = code.replace("-", " ").replace("_", " ").title()
    name = click.prompt("Display name", default=default_name).strip() or default_name
    sort = click.prompt("Sort order (lower = higher)", type=int, default=_next_section_sort(sections))
    new_section = {"code": code, "defaultname": name, "sort": sort, "pagesvisibility": "visible"}
    _save_sections(site_path, sections + [new_section], nav)
    click.echo(click.style(f"  Added section '{code}' ({name}).", fg="green"))


def _rename_section(site_path: Path):
    nav = read_nav_yml_for_edit(site_path)
    sections = nav["sections"]
    target = _pick_section(sections, "Section number to rename (0 = cancel)")
    if target is None:
        return
    name = click.prompt("New display name", default=target.get("defaultname", target["code"])).strip()
    if not name:
        raise click.ClickException("Display name cannot be blank.")
    target["defaultname"] = name
    _save_sections(site_path, sections, nav)
    click.echo(click.style(f"  Renamed to '{name}'.", fg="green"))


def _resort_section(site_path: Path):
    nav = read_nav_yml_for_edit(site_path)
    sections = nav["sections"]
    target = _pick_section(sections, "Section number to reorder (0 = cancel)")
    if target is None:
        return
    sort = click.prompt("New sort value (lower = higher)", type=int, default=target.get("sort", 100))
    target["sort"] = sort
    _save_sections(site_path, sections, nav)
    click.echo(click.style(f"  Sort set to {sort}.", fg="green"))


def _set_section_visibility(site_path: Path):
    nav = read_nav_yml_for_edit(site_path)
    sections = nav["sections"]
    target = _pick_section(sections, "Section number (0 = cancel)")
    if target is None:
        return
    vis = click.prompt(
        "Visibility", type=click.Choice(["visible", "hidden", "draft"]),
        default=target.get("pagesvisibility", "visible"),
    )
    target["pagesvisibility"] = vis
    _save_sections(site_path, sections, nav)
    click.echo(click.style(f"  pagesvisibility = {vis}.", fg="green"))


def _toggle_section_pagination(site_path: Path):
    nav = read_nav_yml_for_edit(site_path)
    sections = nav["sections"]
    target = _pick_section(sections, "Section number (0 = cancel)")
    if target is None:
        return
    current = target.get("pagination") in (True, "on", "yes")
    new_on = click.confirm(
        f"Enable Previous/Next pagination for '{target['code']}'?", default=current
    )
    if new_on:
        target["pagination"] = "on"
    else:
        target.pop("pagination", None)
    _save_sections(site_path, sections, nav)
    click.echo(click.style(f"  pagination = {'on' if new_on else 'off'}.", fg="green"))


def _set_section_parent(site_path: Path):
    nav = read_nav_yml_for_edit(site_path)
    sections = nav["sections"]
    target = _pick_section(sections, "Section number (0 = cancel)")
    if target is None:
        return
    click.echo("  (blank = no parent / top-level)")
    parent_code = click.prompt(
        "Parent section code", default=target.get("parent", ""), show_default=bool(target.get("parent"))
    ).strip()
    if not parent_code:
        target.pop("parent", None)
        target.pop("parent-sort", None)
    else:
        if parent_code == target.get("code"):
            raise click.ClickException("A section cannot be its own parent.")
        by_code = {s["code"]: s for s in sections if s.get("code")}
        if parent_code not in by_code:
            raise click.ClickException(f"No section with code '{parent_code}'.")
        seen: set = set()
        cursor = parent_code
        while cursor:
            if cursor == target.get("code"):
                raise click.ClickException(
                    f"'{parent_code}' is a descendant of '{target['code']}' — this would create a cycle."
                )
            if cursor in seen:
                break
            seen.add(cursor)
            cursor = by_code.get(cursor, {}).get("parent")
        target["parent"] = parent_code
        target["parent-sort"] = click.prompt(
            "Sort within parent", type=int, default=target.get("parent-sort", 100)
        )
    _save_sections(site_path, sections, nav)
    click.echo(click.style("  Parent updated.", fg="green"))


def _delete_section(site_path: Path):
    nav = read_nav_yml_for_edit(site_path)
    sections = nav["sections"]
    target = _pick_section(sections, "Section number to delete (0 = cancel)")
    if target is None:
        return
    code = target["code"]
    children = [s for s in sections if s.get("parent") == code]
    referencing_pages = [p for p in nav["pages"] if p.get("section-id") == code]
    notes = []
    if children:
        notes.append(f"{len(children)} child section(s) ({', '.join(c['code'] for c in children)}) will become top-level")
    if referencing_pages:
        notes.append(
            f"{len(referencing_pages)} page(s) still reference this section-id in frontmatter — "
            "mdcms build will recreate the section automatically unless you also update those pages"
        )
    if notes:
        click.echo(click.style("  Note: " + "; ".join(notes) + ".", fg="yellow"))
    click.confirm(f"Delete section '{code}'?", abort=True)
    new_sections = [s for s in sections if s.get("code") != code]
    for s in new_sections:
        if s.get("parent") == code:
            s.pop("parent", None)
            s.pop("parent-sort", None)
    _save_sections(site_path, new_sections, nav)
    click.echo(click.style(f"  Deleted section '{code}'.", fg="green"))


def _manage_sections(site_path: Path):
    click.echo(click.style(f"\nSections — {site_path}", bold=True))
    while True:
        try:
            nav = read_nav_yml_for_edit(site_path)
        except click.ClickException as e:
            click.echo(click.style(f"  Error: {e.format_message()}", fg="red"))
            return
        sections = nav["sections"]
        click.echo("\nCurrent sections:")
        if not sections:
            click.echo("   (none yet — sections are also auto-created from section-id in page frontmatter)")
        else:
            for s in _sorted_sections(sections):
                bits = [f"sort={s.get('sort', 100)}"]
                if s.get("parent"):
                    bits.append(f"parent={s['parent']}")
                bits.append(f"visibility={s.get('pagesvisibility', 'visible')}")
                if s.get("pagination") in (True, "on", "yes"):
                    bits.append("pagination=on")
                click.echo(f"   {s['code']:<16} {s.get('defaultname', s['code']):<24} ({', '.join(bits)})")

        menu = [
            ("Add a section", lambda: _add_section(site_path)),
            ("Rename a section", lambda: _rename_section(site_path)),
            ("Change sort order", lambda: _resort_section(site_path)),
            ("Set parent section", lambda: _set_section_parent(site_path)),
            ("Set visibility (visible/hidden/draft)", lambda: _set_section_visibility(site_path)),
            ("Enable/disable pagination", lambda: _toggle_section_pagination(site_path)),
            ("Delete a section", lambda: _delete_section(site_path)),
        ]
        click.echo("\nWhat would you like to change?")
        for idx, (label, _) in enumerate(menu, 1):
            click.echo(f"  {idx}. {label}")
        click.echo("  0. Back")

        choice = click.prompt("Select", type=int, default=0)
        if choice == 0:
            break
        if 1 <= choice <= len(menu):
            try:
                menu[choice - 1][1]()
            except click.Abort:
                click.echo("\nCancelled.")
            except click.ClickException as e:
                click.echo(click.style(f"  Error: {e.format_message()}", fg="red"))
        else:
            click.echo("Invalid selection.")


# ─── Page editing (markdown files) ─────────────────────────────

def _pick_page(pages: list, prompt_label: str) -> "dict | None":
    if not pages:
        click.echo("No pages found.")
        return None
    for idx, p in enumerate(pages, 1):
        flags = []
        if p.get("draft"):
            flags.append("draft")
        if p.get("section-id"):
            flags.append(f"section={p['section-id']}")
        suffix = f" ({', '.join(flags)})" if flags else ""
        click.echo(f"  {idx}. {p['file']:<40} {p.get('title', '')}{suffix}")
    pick = click.prompt(prompt_label, type=int, default=0)
    if not (1 <= pick <= len(pages)):
        click.echo("Cancelled.")
        return None
    return pages[pick - 1]


def _confirm_new_section_id(section_id: str, section_codes: set) -> None:
    if section_codes and section_id not in section_codes:
        click.confirm(
            f"'{section_id}' isn't an existing section — it will be auto-created on the next "
            "build. Continue?",
            abort=True,
        )


def _new_page(site_path: Path):
    nav = read_nav_yml(site_path)
    folder = click.prompt("Folder", type=click.Choice(["pages", "posts"]), default="pages")
    slug = click.prompt(f"Filename (without .md, under {folder}/)").strip()
    if not slug:
        raise click.ClickException("Filename cannot be blank.")
    filepath = _safe_dest(site_path, f"{folder}/{slug}.md")
    if filepath.exists():
        raise click.ClickException(f"{folder}/{slug}.md already exists.")

    title = click.prompt("Title").strip()
    if not title:
        raise click.ClickException("Title cannot be blank.")
    meta: dict = {"title": title}

    section_codes = {s["code"] for s in nav["sections"] if s.get("code")}
    section_id = click.prompt("Section-id (blank = unsectioned)", default="", show_default=False).strip()
    if section_id:
        _confirm_new_section_id(section_id, section_codes)
        meta["section-id"] = section_id

    meta["sort"] = click.prompt("Sort order (lower = higher)", type=int, default=100)

    if folder == "posts":
        created = click.prompt(
            "Created (YYYY-MM-DD HH:MM, blank = now)", default="", show_default=False
        ).strip()
        meta["created"] = created or datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

    if click.confirm("Mark as draft?", default=False):
        meta["draft"] = True

    try:
        write_page_file(filepath, meta, f"\n# {title}\n\nContent goes here.\n")
    except OSError as e:
        raise click.ClickException(f"Could not write {folder}/{slug}.md: {e}")
    click.echo(click.style(f"  Created {folder}/{slug}.md.", fg="green"))
    click.echo("  Run 'mdcms build' to add it to nav.yml and search.json.")


def _edit_page(site_path: Path):
    pages = list_markdown_files(site_path)
    target = _pick_page(pages, "Page number to edit (0 = cancel)")
    if target is None:
        return
    filepath = site_path / target["file"]
    meta, body = parse_frontmatter(filepath)
    nav = read_nav_yml(site_path)
    section_codes = {s["code"] for s in nav["sections"] if s.get("code")}

    title = click.prompt("Title", default=meta.get("title", "")).strip()
    if not title:
        raise click.ClickException("Title cannot be blank.")
    meta["title"] = title

    section_id = click.prompt(
        "Section-id (blank = unsectioned)", default=meta.get("section-id") or "", show_default=False
    ).strip()
    if section_id:
        _confirm_new_section_id(section_id, section_codes)
        meta["section-id"] = section_id
    else:
        meta.pop("section-id", None)

    meta["sort"] = click.prompt("Sort order", type=int, default=meta.get("sort", 100))

    if click.confirm("Mark as draft?", default=bool(meta.get("draft", False))):
        meta["draft"] = True
    else:
        meta.pop("draft", None)

    try:
        write_page_file(filepath, meta, body)
    except OSError as e:
        raise click.ClickException(f"Could not write {target['file']}: {e}")
    click.echo(click.style(f"  Updated {target['file']}.", fg="green"))
    click.echo("  Run 'mdcms build' to refresh nav.yml and search.json.")


def _delete_page(site_path: Path):
    pages = list_markdown_files(site_path)
    target = _pick_page(pages, "Page number to delete (0 = cancel)")
    if target is None:
        return
    click.confirm(f"Delete {target['file']}? This cannot be undone.", abort=True)
    try:
        (site_path / target["file"]).unlink()
    except OSError as e:
        raise click.ClickException(f"Could not delete {target['file']}: {e}")
    click.echo(click.style(f"  Deleted {target['file']}.", fg="green"))
    click.echo("  Run 'mdcms build' to update nav.yml and search.json.")


def _manage_pages(site_path: Path):
    click.echo(click.style(f"\nPages — {site_path}", bold=True))
    while True:
        pages = list_markdown_files(site_path)
        click.echo(f"\n{len(pages)} page(s)/post(s):")
        if pages:
            for p in pages:
                flags = []
                if p.get("draft"):
                    flags.append("draft")
                if p.get("section-id"):
                    flags.append(f"section={p['section-id']}")
                suffix = f" ({', '.join(flags)})" if flags else ""
                click.echo(f"   {p['file']:<40} {p.get('title', '')}{suffix}")
        else:
            click.echo("   (none yet)")

        menu = [
            ("New page", lambda: _new_page(site_path)),
            ("Edit a page", lambda: _edit_page(site_path)),
            ("Delete a page", lambda: _delete_page(site_path)),
        ]
        click.echo("\nWhat would you like to do?")
        for idx, (label, _) in enumerate(menu, 1):
            click.echo(f"  {idx}. {label}")
        click.echo("  0. Back")

        choice = click.prompt("Select", type=int, default=0)
        if choice == 0:
            break
        if 1 <= choice <= len(menu):
            try:
                menu[choice - 1][1]()
            except click.Abort:
                click.echo("\nCancelled.")
            except click.ClickException as e:
                click.echo(click.style(f"  Error: {e.format_message()}", fg="red"))
        else:
            click.echo("Invalid selection.")


def _interactive_config(site_path: Path):
    click.echo(click.style(f"\nmdcms config — {site_path}", bold=True))
    while True:
        cfg = read_config(site_path)
        click.echo("\nCurrent settings:")
        click.echo(f"   sitename        : {cfg.get('sitename', '(not set)')}")
        click.echo(f"   navigation      : {cfg.get('navigation', '(not set)')}")
        click.echo(f"   theme           : {cfg.get('theme', '(not set)')}")
        click.echo(f"   homepage        : {cfg.get('homepage', '(default: pages/home.md)')}")
        click.echo(f"   sitedescription : {cfg.get('sitedescription', '(not set)')}")
        click.echo(f"   footer          : {cfg.get('footer', '(not set)')}")
        click.echo(f"   default-theme   : {cfg.get('default-theme', '(system)')}")
        click.echo(f"   pwa             : {cfg.get('pwa', 'no')}")
        cat_info = get_category_info(cfg)
        pages_count = len(list_markdown_files(site_path))
        nav_state = read_nav_yml(site_path)
        click.echo(f"   categories      : {'yes' if cat_info['use'] else 'no'} "
                   f"({len(cat_info['codes'])} declared, {'default: ' + cat_info['default_code'] if cat_info['default_code'] else 'no default'})")
        click.echo(f"   pages/posts     : {pages_count} file(s)")
        if nav_state["warning"]:
            click.echo(f"   sections        : {click.style('unreadable', fg='red')} — {nav_state['warning']}")
        else:
            click.echo(f"   sections        : {len(nav_state['sections'])}")

        menu = [
            ("Site name", lambda c: _prompt_scalar(site_path, c, "sitename", "Site name")),
            ("Navigation style (sidebar/topbar)",
             lambda c: _prompt_scalar(site_path, c, "navigation", "Navigation", choices=_NAV_CHOICES)),
            ("Theme — browse & install", lambda c: _pick_and_install_theme(site_path)),
            ("Homepage", lambda c: _prompt_scalar(site_path, c, "homepage", "Homepage (e.g. pages/home.md)")),
            ("Site description", lambda c: _prompt_scalar(site_path, c, "sitedescription", "Site description")),
            ("Footer", lambda c: _prompt_scalar(site_path, c, "footer", "Footer text")),
            ("Default colour mode (light/dark/system)",
             lambda c: _prompt_scalar(site_path, c, "default-theme", "Default mode", choices=_THEME_MODE_CHOICES)),
            ("Navigation position (left/right)",
             lambda c: _prompt_scalar(site_path, c, "nav-position", "Nav position", choices=_NAV_POS_CHOICES)),
            ("PWA settings", lambda c: _edit_pwa(site_path, c)),
            ("Manage pages", lambda c: _manage_pages(site_path)),
            ("Manage sections", lambda c: _manage_sections(site_path)),
            ("Manage categories", lambda c: _manage_categories(site_path)),
        ]
        click.echo("\nWhat would you like to change?")
        for idx, (label, _) in enumerate(menu, 1):
            click.echo(f"  {idx}. {label}")
        click.echo("  0. Quit")

        choice = click.prompt("Select", type=int, default=0)
        if choice == 0:
            break
        if 1 <= choice <= len(menu):
            try:
                menu[choice - 1][1](cfg)
            except click.Abort:
                click.echo("\nCancelled.")
        else:
            click.echo("Invalid selection.")
    click.echo(click.style("Config saved to config.yml.", fg="green"))


# ─── CLI commands ─────────────────────────────────────────────

def _fetch_banner_message() -> str:
    """Fetch this version's one-line status message from docs/banner/v{CLI_VERSION}.txt."""
    url = f"https://raw.githubusercontent.com/kbenestad/mdcms/refs/heads/main/docs/banner/v{CLI_VERSION}.txt?t={int(time.time())}"
    try:
        ssl_ctx = ssl.create_default_context(cafile=certifi.where())
        req = urllib.request.Request(url, headers={"User-Agent": f"mdcms/{CLI_VERSION}"})
        with urllib.request.urlopen(req, context=ssl_ctx, timeout=5) as resp:
            return resp.read().decode("utf-8").strip()
    except Exception:
        return "There is no online information defined for this version."


def _version_callback(ctx, param, value):
    if not value or ctx.resilient_parsing:
        return
    click.echo(f"mdcms v{CLI_VERSION} (released {CLI_RELEASE_DATE})")
    click.echo(_fetch_banner_message())
    ctx.exit()


def _print_startup_banner() -> None:
    """Print the boxed MD-CMS wordmark/version/status banner shown before the bare-command help."""
    width = 80
    left, right = "MD-CMS", "kbenestad/mdcms"
    padding = " " * (width - len(left) - len(right))
    click.echo("=" * width)
    click.echo(click.style(left, bold=True) + padding + click.style(right, fg="bright_black"))
    click.echo(click.style(f"v{CLI_VERSION} • {CLI_RELEASE_DATE}".rjust(width), fg="bright_black"))
    message = _fetch_banner_message()
    click.echo(click.style(message, fg="green" if "latest version" in message.lower() else "yellow"))
    click.echo("=" * width)
    click.echo()


_REMOTE_VERSION_RE = re.compile(r'CLI_VERSION = "([^"]+)"')


def _fetch_latest_version() -> str:
    text = _http_get(f"{REPO_RAW_BASE}/mdcms.py").decode("utf-8")
    m = _REMOTE_VERSION_RE.search(text)
    if not m:
        raise click.ClickException("Could not determine the latest mdcms version from GitHub.")
    return m.group(1)


def _install_kind() -> str:
    """Return 'frozen' (standalone binary), 'pipx', or 'pip' for the running mdcms."""
    if getattr(sys, "frozen", False):
        return "frozen"
    if "pipx" in sys.prefix.replace("\\", "/").lower():
        return "pipx"
    return "pip"


def _binary_release_asset() -> str:
    """Return this platform's binary path under the repo's latest/ directory."""
    system = platform.system()
    machine = platform.machine().lower()
    if system == "Linux":
        arch = "arm64" if machine in ("aarch64", "arm64") else "amd64"
        return f"linux/{arch}/mdcms"
    if system == "Darwin":
        variant = "silicon" if machine in ("arm64", "aarch64") else "intel"
        return f"macos/{variant}/mdcms"
    if system == "Windows":
        return "windows/mdcms.exe"
    raise click.ClickException(f"No standalone binary is published for this platform: {system}")


def _dpkg_owner_of(path: Path) -> "str | None":
    """Return the dpkg package name owning `path`, or None (not Linux / not dpkg-managed)."""
    if platform.system() != "Linux" or not shutil.which("dpkg"):
        return None
    try:
        result = subprocess.run(
            ["dpkg", "-S", str(path)], capture_output=True, timeout=5, text=True
        )
    except OSError:
        return None
    if result.returncode != 0:
        return None
    return result.stdout.split(":", 1)[0].strip() or None


def _upgrade_package(kind: str) -> None:
    cmd = (
        ["pipx", "upgrade", "mdcms"] if kind == "pipx"
        else [sys.executable, "-m", "pip", "install", "--upgrade", "mdcms"]
    )
    click.echo(f"Running: {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd)
    except OSError as e:
        raise click.ClickException(f"Could not run {cmd[0]}: {e}")
    if result.returncode != 0:
        raise click.ClickException("Upgrade command failed — see output above.")


def _reexec_with_sudo() -> None:
    """Re-invoke the current upgrade command under sudo. Does not return."""
    exe_path = Path(sys.executable).resolve()
    click.echo(click.style(
        "Upgrading mdcms requires sudo privileges. Please enter your password or re-run as a sudo user.",
        fg="yellow"
    ))
    os.execvp("sudo", ["sudo", str(exe_path)] + sys.argv[1:])


def _permission_denied(exe_path: Path) -> "click.ClickException":
    return click.ClickException(
        f"Permission denied writing to {exe_path}. Re-run with elevated permissions, "
        f"e.g.: sudo mdcms upgrade"
    )


def _upgrade_dpkg(latest: str, pkg: str) -> None:
    """Download the .deb for this platform and install it via dpkg, keeping the
    package database in sync (a raw binary swap would leave dpkg's record stale)."""
    deb_dir = _binary_release_asset().rsplit("/", 1)[0]
    deb_url = f"{REPO_RAW_BASE}/latest/{deb_dir}/mdcms.deb"
    click.echo(f"Downloading v{latest} .deb package for this platform ...")
    data = _http_get(deb_url)
    if not data:
        raise click.ClickException("Downloaded .deb package was empty — aborting.")

    tmp_path = Path(tempfile.gettempdir()) / "mdcms.deb"
    tmp_path.write_bytes(data)

    cmd = ["dpkg", "-i", str(tmp_path)]
    if os.geteuid() != 0:
        if not shutil.which("sudo"):
            raise click.ClickException(
                f"Downloaded {tmp_path}, but installing it requires root and no 'sudo' is "
                f"available on this system. Install it manually: dpkg -i {tmp_path}"
            )
        cmd = ["sudo"] + cmd

    click.echo(f"Running: {' '.join(cmd)}")
    try:
        try:
            result = subprocess.run(cmd)
        except OSError as e:
            raise click.ClickException(f"Could not run dpkg: {e}")
        if result.returncode != 0:
            raise click.ClickException("dpkg install failed — see output above.")
    finally:
        tmp_path.unlink(missing_ok=True)

    click.echo(click.style(f"Upgraded to v{latest} (package '{pkg}').", fg="green"))


def _upgrade_binary(latest: str) -> None:
    exe_path = Path(sys.executable).resolve()

    # Linux/macOS binaries are commonly installed to a root-owned location
    # (e.g. /usr/local/bin). Detect that up front and re-exec under sudo
    # instead of downloading the binary only to fail to write it.
    if (platform.system() != "Windows" and os.geteuid() != 0
            and not os.access(exe_path, os.W_OK)):
        if shutil.which("sudo"):
            _reexec_with_sudo()
        raise _permission_denied(exe_path)

    asset = _binary_release_asset()
    click.echo(f"Downloading v{latest} binary for this platform ...")
    data = _http_get(f"{REPO_RAW_BASE}/latest/{asset}")
    if not data:
        raise click.ClickException("Downloaded binary was empty — aborting.")

    tmp_path = exe_path.with_name(exe_path.name + ".new")

    if platform.system() == "Windows":
        tmp_path.write_bytes(data)
        # The running .exe is locked, so hand the swap off to a detached helper
        # script that waits for this process to exit before replacing it.
        bat_path = exe_path.with_name("mdcms_upgrade.bat")
        bat_path.write_text(
            "@echo off\r\n"
            "ping -n 3 127.0.0.1 >nul\r\n"
            f'move /y "{tmp_path}" "{exe_path}"\r\n'
            f'del "{bat_path}"\r\n',
            encoding="utf-8",
        )
        subprocess.Popen(
            ["cmd", "/c", "start", "/min", "", str(bat_path)],
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS,
        )
        click.echo(click.style(
            f"Downloaded v{latest}. It will replace {exe_path.name} in a couple of seconds — "
            "re-run mdcms once this process has exited.", fg="green"
        ))
        return

    try:
        tmp_path.write_bytes(data)
        tmp_path.chmod(0o755)
        os.replace(tmp_path, exe_path)
    except PermissionError:
        tmp_path.unlink(missing_ok=True)
        if shutil.which("sudo"):
            _reexec_with_sudo()
        raise _permission_denied(exe_path)
    click.echo(click.style(f"Upgraded to v{latest}.", fg="green"))


@click.group(invoke_without_command=True,
             epilog="Use --help at any command for more information")
@click.option("--version", is_flag=True, is_eager=True, expose_value=False,
              callback=_version_callback, help="Show version and exit.")
@click.pass_context
def cli(ctx):
    """MD-CMS — Markdown-based CMS companion CLI.

    Manage and build MD-CMS sites locally or in CI/CD pipelines.
    """
    if ctx.invoked_subcommand is None:
        click.clear()
        _print_startup_banner()
        click.echo(ctx.get_help())
        ctx.exit()


@cli.command()
@click.option("--force", is_flag=True, help="Reinstall even if already on the latest version.")
def upgrade(force):
    """Upgrade the mdcms CLI itself to the latest released version.

    Detects how this copy of mdcms was installed — pip, pipx, a dpkg-managed
    .deb, or a standalone binary — and upgrades it the matching way: `pip
    install --upgrade` / `pipx upgrade` for package installs; downloading and
    installing the new .deb via `dpkg -i` (re-execing under sudo if needed)
    for a dpkg-managed install, so the package database stays in sync; or
    downloading and swapping the executable for a standalone binary install.
    """
    click.echo(f"Current version: v{CLI_VERSION}")
    try:
        latest = _fetch_latest_version()
    except urllib.error.URLError as e:
        raise click.ClickException(f"Could not check for updates: {e}")

    if not force and _parse_ver(latest) <= _parse_ver(CLI_VERSION):
        click.echo(click.style(f"Already up to date (latest is v{latest}).", fg="green"))
        return

    click.echo(f"Latest version:  v{latest}")

    kind = _install_kind()
    if kind in ("pip", "pipx"):
        _upgrade_package(kind)
        click.echo(click.style(f"Upgraded to v{latest}.", fg="green"))
        return

    pkg = _dpkg_owner_of(Path(sys.executable).resolve())
    if pkg:
        _upgrade_dpkg(latest, pkg)
        return

    _upgrade_binary(latest)


@cli.command()
@click.argument("name")
@click.argument("path", required=False, default=None)
@click.option("--from", "source", default=None, metavar="URL",
              help="Download template from a GitHub repo or deployed site URL.")
def register(name, path, source):
    """Register a site by NAME at PATH (default: current directory).

    PATH may be a local directory or a URL to download from. If no mdcms
    site is found at the local path, the template is downloaded from --from
    (or PATH if it is a URL, or the built-in mdcms starter by default).

    \b
    Examples:
      mdcms register mysite
      mdcms register mysite ./mydir
      mdcms register mysite https://github.com/owner/repo
      mdcms register mysite --from https://example.com/deployed-site
    """
    reg = load_registry()

    if name in reg["sites"]:
        raise click.ClickException(
            f"'{name}' is already registered. Use 'mdcms delete {name}' to remove it first."
        )

    # If PATH looks like a URL, treat it as the download source rather than a local path.
    if path and path.startswith(("http://", "https://", "git://")):
        if source is None:
            source = path
        path = None

    site_path = Path(path).resolve() if path else Path.cwd()

    if not site_path.is_dir():
        raise click.ClickException(f"Directory not found: {site_path}")

    # Warn if path is already registered under a different name
    for existing_name, info in reg["sites"].items():
        if Path(info["path"]).resolve() == site_path:
            click.echo(click.style(
                f"Warning: this path is already registered as '{existing_name}'.",
                fg="yellow",
            ))

    site_version = read_site_version(site_path)

    if site_version is None:
        click.echo(f"No mdcms site found at {site_path}.")
        download_template(site_path, source)
        site_version = read_site_version(site_path)
        if site_version is None:
            raise click.ClickException(
                "Downloaded template but could not read version marker. Please check config.yml."
            )

    status, msg = version_status(site_version)
    if status == "unsupported":
        raise click.ClickException(f"Site version not supported: {msg}")
    if status in ("outdated", "newer"):
        click.echo(click.style(f"Warning: {msg}", fg="yellow"))

    reg["sites"][name] = {"path": str(site_path), "version": site_version}
    save_registry(reg)
    click.echo(click.style(f"Registered '{name}' → {site_path}", fg="green"))


@cli.command("delete")
@click.argument("names", nargs=-1, required=True)
@click.option("-y", "--yes", is_flag=True, help="Skip the confirmation prompt.")
def delete_site(names, yes):
    """Remove one or more registered sites. Does not delete any files."""
    reg = load_registry()

    missing = [name for name in names if name not in reg["sites"]]
    if missing:
        raise click.ClickException(f"Site(s) not found: {', '.join(missing)}")

    click.echo("Sites to remove:")
    for name in names:
        click.echo(f"  {name}  ({reg['sites'][name]['path']})")

    if not yes:
        click.confirm("\nRemove these registrations? (Site files will not be deleted.)", abort=True)

    for name in names:
        del reg["sites"][name]
    save_registry(reg)
    click.echo(click.style(f"Removed: {', '.join(names)}.", fg="green"))


@cli.command()
@click.argument("name", required=False)
def view(name):
    """List all registered sites, or show details for NAME."""
    reg = load_registry()

    if not name:
        if not reg["sites"]:
            click.echo("No sites registered. Use 'mdcms register <name> [path]'.")
            return
        click.echo(f"{'NAME':<20} {'VERSION':<12} {'STATUS':<12} PATH")
        click.echo("─" * 72)
        for site_name, info in sorted(reg["sites"].items()):
            site_path = Path(info["path"])
            site_version = read_site_version(site_path)
            if site_version is None:
                ver_str = "?"
                status_label = click.style("no marker", fg="red")
            else:
                status, _ = version_status(site_version)
                ver_str = f"v{site_version}"
                if status == "unsupported":
                    status_label = click.style("unsupported", fg="red")
                elif status == "outdated":
                    status_label = click.style("outdated", fg="yellow")
                elif status == "newer":
                    status_label = click.style("site newer", fg="cyan")
                else:
                    status_label = click.style("current", fg="green")
            click.echo(f"{site_name:<20} {ver_str:<12} {status_label:<12} {info['path']}")
        return

    if name not in reg["sites"]:
        raise click.ClickException(f"Site '{name}' not found.")

    info = reg["sites"][name]
    site_path = Path(info["path"])
    cfg = read_config(site_path)
    cat = get_category_info(cfg)
    site_version = read_site_version(site_path)

    if site_version:
        _, ver_display = version_status(site_version)
    else:
        ver_display = "unknown (no version marker in config.yml)"

    pages_dir = site_path / "pages"
    posts_dir = site_path / "posts"
    page_count = sum(1 for _ in pages_dir.rglob("*.md")) if pages_dir.is_dir() else 0
    post_count = sum(1 for _ in posts_dir.rglob("*.md")) if posts_dir.is_dir() else 0

    nav = read_nav_yml(site_path)
    sections = [s.get("code", "?") for s in nav["sections"]]

    click.echo(f"Site:        {name}")
    click.echo(f"Path:        {site_path}")
    click.echo(f"Version:     {ver_display}")
    click.echo(f"Site name:   {cfg.get('sitename', '(not set)')}")
    click.echo(f"Navigation:  {cfg.get('navigation', '(not set)')}")
    click.echo(f"Pages:       {page_count}")
    click.echo(f"Posts:       {post_count}")
    if cat["use"]:
        all_codes = [cat["default_code"]] + cat["codes"]
        click.echo(f"Categories:  enabled — {', '.join(c for c in all_codes if c)}")
        if nav["date_categories"]:
            newest = format_date_category(nav["date_categories"][0])
            click.echo(f"             + {len(nav['date_categories'])} date categor"
                       f"{'y' if len(nav['date_categories']) == 1 else 'ies'} (newest: {newest})")
    else:
        click.echo("Categories:  disabled")
    click.echo(f"Sections:    {', '.join(sections) if sections else '(none)'}")


@cli.command()
@click.argument("name", required=False)
@click.option(
    "--path", "path_override",
    type=click.Path(),
    default=None,
    help="Path to site root. Overrides NAME and current directory. Use this in CI/CD.",
)
def build(name, path_override):
    """Build nav.yml and search.json for a site.

    \b
    Examples:
      mdcms build mysite          # registered site by name
      mdcms build --path ./site   # explicit path (no registry needed)
      mdcms build                 # uses current directory (ideal for GitHub Actions)
    """
    site_path = resolve_site_path(name, path_override)
    click.echo(f"Building: {site_path}")
    run_build(site_path)
    click.echo(click.style("Build complete.", fg="green"))


@cli.command()
@click.argument("name", required=False)
@click.option(
    "--path", "path_override",
    type=click.Path(),
    default=None,
    help="Explicit site path (no registry lookup).",
)
@click.option("--force", is_flag=True, help="Re-download index.html even if the site is already current.")
def update(name, path_override, force):
    """Update a site's renderer (index.html) and config.yml to the version this CLI ships.

    Downloads the current app/index.html and overwrites the site's copy (keeping
    its existing <title>). Then appends any config.yml keys the template has
    gained since the site was last updated — new optional features, added
    verbatim (active or commented-out, exactly as the template declares them) —
    without touching a single key, value, or comment the site already has.
    Finally bumps the CURRENT VERSION marker in config.yml. Site content —
    pages, posts, nav.yml, theme.yml — is left untouched.

    \b
    Examples:
      mdcms update mysite
      mdcms update --path ./site
    """
    site_path = resolve_site_path(name, path_override)
    index_file = site_path / "index.html"
    if not index_file.exists():
        raise click.ClickException(f"No index.html found at {site_path}")

    site_version = read_site_version(site_path)
    if site_version is None:
        raise click.ClickException(
            "No mdcms version marker found in config.yml. Is this an mdcms site?"
        )

    status, msg = version_status(site_version)
    if status == "newer":
        click.echo(click.style(
            f"{msg}. Nothing to update — upgrade the mdcms CLI itself instead.", fg="yellow"
        ))
        return
    if status == "ok" and not force:
        click.echo(f"Already up to date ({msg}). Use --force to re-download anyway.")
        return
    if status == "unsupported":
        click.echo(click.style(
            f"Warning: {msg}. config.yml may need manual review after this update — "
            "its format may have changed significantly since that version.",
            fg="yellow",
        ))

    click.echo(f"Updating renderer: v{site_version} -> v{CLI_VERSION}")

    root = _local_repo_root()
    if root:
        new_html = (root / "app" / "index.html").read_text(encoding="utf-8")
    else:
        new_html = _http_get(f"{TEMPLATE_BASE_URL}/index.html").decode("utf-8")
    index_file.write_text(new_html, encoding="utf-8")
    click.echo("  index.html")

    cfg = read_config(site_path)
    if cfg.get("sitename"):
        _patch_html_title(site_path, cfg["sitename"])

    if root:
        template_config_text = (root / "app" / "config.yml").read_text(encoding="utf-8")
    else:
        template_config_text = _http_get(f"{TEMPLATE_BASE_URL}/config.yml").decode("utf-8")
    added_keys = sync_config_keys(site_path, template_config_text)
    if added_keys:
        click.echo(f"  config.yml — added new key(s): {', '.join(added_keys)}")
    else:
        click.echo("  config.yml — no new keys to add")

    if _bump_config_version_marker(site_path):
        click.echo(f"  config.yml version marker -> {CLI_VERSION}")
    else:
        today = datetime.date.today()
        config_file = site_path / "config.yml"
        click.echo(click.style(
            f"  Could not find a CURRENT VERSION banner in config.yml — update it by hand in {config_file}:\n"
            f"    # CURRENT VERSION: {CLI_VERSION} - {today.day} {today:%B %Y}",
            fg="yellow",
        ))

    click.echo(click.style("Renderer updated.", fg="green"))


@cli.command("fetch-deps")
@click.argument("name", required=False, default=None)
@click.option("--path", "path_override", default=None, type=click.Path(),
              help="Explicit site path (no registry lookup).")
def fetch_deps(name, path_override):
    """Download external JS/CSS dependencies and patch index.html for offline use."""
    site_path = resolve_site_path(name, path_override)
    if not (site_path / "index.html").exists():
        raise click.ClickException(f"No index.html found at {site_path}")

    click.echo(f"Fetching dependencies for {site_path} ...")

    vendors_dir = site_path / "assets" / "required" / "vendors"
    vendors_dir.mkdir(parents=True, exist_ok=True)

    for cdn_url, rel_dest in CDN_DEPS:
        dest = site_path / rel_dest
        click.echo(f"  {rel_dest}")
        try:
            dest.write_bytes(_http_get(cdn_url))
        except Exception as e:
            raise click.ClickException(f"Failed to download {cdn_url}: {e}")

    cfg = read_config(site_path)
    local_font_css: list = []
    if cfg.get("theme"):
        local_font_css = _fetch_bunny_fonts(site_path, cfg["theme"])

    _patch_index_html(site_path, local_font_css)

    click.echo(click.style("Done. Site is ready for offline use.", fg="green"))


@cli.command()
@click.argument("name", required=False, default=None)
@click.option("--path", "path_override", default=None, type=click.Path(),
              help="Explicit site path (no registry lookup).")
@click.option("--output", "output_override", default=None, type=click.Path(),
              help="Output file path. Defaults to bundle.html in the site root.")
@click.option("--offline", is_flag=True,
              help="Also inline vendor JS/CSS libraries and web fonts, so the bundle needs "
                   "zero network access ever. Without this flag those still load from CDN.")
def bundle(name, path_override, output_override, offline):
    """Build a single self-contained HTML file (config, nav, search, pages, assets all embedded).

    The result can be opened directly from any storage — a USB stick, an email
    attachment, a wiki upload — with no server and no sibling files. Requires
    nav.yml and search.json to already exist; run 'mdcms build' first.

    \b
    Examples:
      mdcms bundle mysite                  # bundle.html, CDN libs/fonts still need internet
      mdcms bundle mysite --offline        # fully self-contained, zero network access
      mdcms bundle --path ./site --output dist/site.html
    """
    site_path = resolve_site_path(name, path_override)
    output = Path(output_override) if output_override else site_path / "bundle.html"

    cfg = read_config(site_path)
    click.echo(f"Bundling: {site_path}" + (" (offline)" if offline else ""))
    warnings = generate_bundle(site_path, cfg, output, offline)
    for w in warnings:
        click.echo(click.style(w, fg="yellow"))

    size_mb = output.stat().st_size / (1024 * 1024)
    click.echo(f"  Wrote {output} ({size_mb:.1f} MB)")
    if size_mb > 25:
        click.echo(click.style(
            "  Warning: this is a large single file — fine for browsers, but consider "
            "whether a regular multi-file build suits this site better.", fg="yellow",
        ))
    click.echo(click.style("Bundle complete.", fg="green"))


@cli.command()
@click.argument("name", required=False)
@click.option("--path", "path_override", type=click.Path(), default=None,
              help="Explicit site path (no registry lookup).")
@click.option("--set", "sets", multiple=True, metavar="KEY=VALUE",
              help="Set a config key non-interactively (repeatable).")
@click.option("--theme", "theme_query", default=None, metavar="NAME",
              help="Download and set a theme non-interactively (by label or filename).")
@click.option("--list-themes", is_flag=True, help="List all available themes and exit.")
def config(name, path_override, sets, theme_query, list_themes):
    """Configure a site's config.yml and install themes.

    With no options this launches an interactive editor for the most common
    settings. Use --set / --theme for scripted, non-interactive changes.

    \b
    Examples:
      mdcms config mysite                     # interactive
      mdcms config --path ./site              # interactive, explicit path
      mdcms config mysite --set navigation=topbar --set sitename="My Docs"
      mdcms config mysite --theme "blue · charcoal"
      mdcms config --list-themes
    """
    if list_themes:
        _print_theme_list(load_theme_index())
        return

    site_path = resolve_site_path(name, path_override)
    if not (site_path / "config.yml").exists():
        raise click.ClickException(f"No config.yml found at {site_path}.")
    if read_site_version(site_path) is None:
        raise click.ClickException(
            "No mdcms version marker in config.yml — is this an mdcms site?"
        )

    non_interactive = bool(sets) or theme_query is not None
    if not non_interactive:
        _interactive_config(site_path)
        return

    if sets:
        updates: dict = {}
        for pair in sets:
            if "=" not in pair:
                raise click.ClickException(f"Invalid --set '{pair}'. Use KEY=VALUE.")
            key, val = pair.split("=", 1)
            key = key.strip()
            if key not in EDITABLE_KEYS:
                raise click.ClickException(
                    f"Unsupported key '{key}'. Editable keys: {', '.join(EDITABLE_KEYS)}"
                )
            updates[key] = val.strip()
        _validate_updates(updates)
        skipped = set_config_keys(site_path, updates)
        for key, val in updates.items():
            if key not in skipped:
                click.echo(click.style(f"  {key} = {val}", fg="green"))
        for key in skipped:
            click.echo(click.style(
                f"  Skipped '{key}' — it holds a structured block; edit config.yml by hand.",
                fg="yellow",
            ))

    if theme_query is not None:
        entry = _resolve_theme_query(load_theme_index(), theme_query)
        rel = install_theme(site_path, entry)
        click.echo(click.style(f"  theme = {rel}  ({entry['label']})", fg="green"))

    click.echo(click.style("config.yml updated.", fg="green"))


# ─── Entry point ─────────────────────────────────────────────

def main():
    cli()


if __name__ == "__main__":
    main()
