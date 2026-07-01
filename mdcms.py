#!/usr/bin/env python3
#
# mdcms v0.6.0 — CLI companion
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

"""MD-CMS v0.6.0 — CLI tool for managing and building MD-CMS sites."""

import json
import os
import re
import ssl
import time
import urllib.error
import urllib.request
from pathlib import Path

import certifi

import click
import yaml

CLI_VERSION = "0.6.1"
CLI_RELEASE_DATE = "1 July 2026"
MIN_SUPPORTED_VERSION = "0.3"

MARKER_RE = re.compile(r"mdcms v(\d+\.\d+)", re.IGNORECASE)
CATEGORY_CODE_RE = re.compile(r"^[a-zA-Z0-9\-]+$")

REGISTRY_FILE = Path.home() / ".config" / "mdcms" / "sites.json"
TEMPLATE_BASE_URL = "https://raw.githubusercontent.com/kbenestad/mdcms/main/app"
MANIFEST_FILENAME = "mdcms.json"

GITHUB_URL_RE = re.compile(
    r"https?://github\.com/([^/]+)/([^/]+?)(?:\.git)?"
    r"(?:/tree/([^/]+?)(?:/(.+?))?)?/?$"
)


# ─── Version helpers ──────────────────────────────────────────

def _parse_ver(v: str) -> tuple:
    return tuple(int(x) for x in v.split("."))


def read_site_version(site_path: Path) -> "str | None":
    config = site_path / "config.yml"
    if not config.exists():
        return None
    try:
        first_line = config.read_text(encoding="utf-8").split("\n", 1)[0]
        m = MARKER_RE.search(first_line)
        return m.group(1) if m else None
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


# ─── Scanner ─────────────────────────────────────────────────

def identify_variant(rel: str, known_codes: set) -> "tuple[str | None, str | None]":
    if not rel.endswith(".md"):
        return None, None
    stem = rel[:-3]
    base_name = os.path.basename(stem)
    if "." in base_name:
        head, _, suffix = stem.rpartition(".")
        if suffix in known_codes:
            return head, suffix
    return stem, None


def scan_and_categorize(directory: Path, site_root: Path, known_codes: set) -> list:
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
            base, code = identify_variant(rel, known_codes)
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

def _emit_value(v) -> str:
    if v is None:
        return ""
    s = str(v)
    if s == "" or any(c in s for c in ':"\'#') or s.lower() in ("true", "false", "null"):
        return '"' + s.replace('"', '\\"') + '"'
    return s


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
        sort = existing.get("sort") or primary.get("sort") or 100
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


def generate_nav_yml(sections: list, pages: list, categories_use: bool = False) -> str:
    lines = [
        "# nav.yml — generated by mdcms",
        "# Manual edits to section metadata (defaultname, sort, parent, parent-sort,",
        "# pagesvisibility, categorynames) are preserved on rebuild.",
        "",
        "sections:",
    ]
    if not sections:
        lines.append("  # (none yet — add section-id to page frontmatter to auto-create)")
    else:
        for s in sections:
            lines.append(f"  - code: {s['code']}")
            lines.append(f"    defaultname: {_emit_value(s.get('defaultname', s['code']))}")
            lines.append(f"    sort: {s.get('sort', 100)}")
            if s.get("parent"):
                lines.append(f"    parent: {s['parent']}")
                lines.append(f"    parent-sort: {s.get('parent-sort', 100)}")
            lines.append(f"    pagesvisibility: {s.get('pagesvisibility', 'visible')}")
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
                lines.append(f"    section-id: {p['section-id']}")
            lines.append(f"    sort: {p.get('sort', 100)}")
            if categories_use and p.get("uncategorized"):
                lines.append("    uncategorized: true")
            if categories_use and p.get("variants"):
                lines.append(f"    variants: [{', '.join(p['variants'])}]")
            if categories_use and p.get("titles"):
                lines.append("    titles:")
                for code, title in p["titles"].items():
                    lines.append(f"      {code}: {_emit_value(title)}")
            lines.append("")
    return "\n".join(lines)


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
    cat = get_category_info(cfg)

    all_codes = [c for c in ([cat["default_code"]] + cat["codes"]) if c]
    invalid = [c for c in all_codes if not CATEGORY_CODE_RE.match(c)]
    if invalid:
        raise click.ClickException(f"Invalid category code(s): {invalid}")
    if cat["use"] and not cat["default_code"]:
        raise click.ClickException("categories-use: yes but no default-category.code defined.")

    known_codes = set(all_codes) if cat["use"] else set()

    page_records = scan_and_categorize(site_path / "pages", site_path, known_codes)
    post_records = scan_and_categorize(site_path / "posts", site_path, known_codes)
    click.echo(f"  pages/  {len(page_records)} file(s)")
    click.echo(f"  posts/  {len(post_records)} file(s)")

    page_groups = group_by_base(page_records)

    existing_sections: list = []
    existing_pages: list = []
    nav_file = site_path / "nav.yml"
    if nav_file.exists():
        try:
            nav_data = yaml.safe_load(nav_file.read_text(encoding="utf-8")) or {}
            existing_sections = [s for s in (nav_data.get("sections") or []) if isinstance(s, dict)]
            existing_pages = [p for p in (nav_data.get("pages") or []) if isinstance(p, dict)]
        except (OSError, yaml.YAMLError) as e:
            click.echo(click.style(f"Warning: could not parse nav.yml ({e}); starting fresh.", fg="yellow"))

    primary_entries = [select_primary(v, cat["default_code"]) for v in page_groups.values()]
    sections, auto_created = merge_sections(primary_entries, existing_sections)

    page_nav = build_page_nav(
        page_groups, existing_pages,
        categories_use=cat["use"],
        default_code=cat["default_code"],
    )

    nav_file.write_text(
        generate_nav_yml(sections, page_nav, categories_use=cat["use"]),
        encoding="utf-8",
    )
    click.echo("  Wrote nav.yml")

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


# ─── CLI commands ─────────────────────────────────────────────

def _version_callback(ctx, param, value):
    if not value or ctx.resilient_parsing:
        return
    click.echo(f"mdcms v{CLI_VERSION} (released {CLI_RELEASE_DATE})")
    url = f"https://raw.githubusercontent.com/kbenestad/mdcms/refs/heads/main/docs/banner/v{CLI_VERSION}.txt?t={int(time.time())}"
    try:
        ssl_ctx = ssl.create_default_context(cafile=certifi.where())
        req = urllib.request.Request(url, headers={"User-Agent": f"mdcms/{CLI_VERSION}"})
        with urllib.request.urlopen(req, context=ssl_ctx, timeout=5) as resp:
            click.echo(resp.read().decode("utf-8").strip())
    except urllib.error.HTTPError as e:
        if e.code == 404:
            click.echo("There is no online information defined for this version.")
        else:
            click.echo("There is no online information defined for this version.")
    except Exception:
        click.echo("There is no online information defined for this version.")
    ctx.exit()


@click.group()
@click.option("--version", is_flag=True, is_eager=True, expose_value=False,
              callback=_version_callback, help="Show version and exit.")
def cli():
    """MD-CMS — Markdown-based CMS companion CLI.

    Manage and build MD-CMS sites locally or in CI/CD pipelines.
    """


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
@click.argument("name")
def delete_site(name):
    """Remove a registered site. Does not delete any files."""
    reg = load_registry()
    if name not in reg["sites"]:
        raise click.ClickException(f"Site '{name}' not found.")

    info = reg["sites"][name]
    click.echo(f"Site: {name}")
    click.echo(f"Path: {info['path']}")
    click.confirm("\nRemove this registration? (Site files will not be deleted.)", abort=True)

    del reg["sites"][name]
    save_registry(reg)
    click.echo(click.style(f"Removed '{name}'.", fg="green"))


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

    sections = []
    nav_file = site_path / "nav.yml"
    if nav_file.exists():
        try:
            nav_data = yaml.safe_load(nav_file.read_text(encoding="utf-8")) or {}
            sections = [
                s.get("code", "?")
                for s in (nav_data.get("sections") or [])
                if isinstance(s, dict)
            ]
        except (OSError, yaml.YAMLError):
            pass

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


# ─── Entry point ─────────────────────────────────────────────

def main():
    cli()


if __name__ == "__main__":
    main()
