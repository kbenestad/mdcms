#!/usr/bin/env python3
#
# MD-CMS - Markdown Content Management System
# kbenestad/mdcms - https://github.com/kbenestad/mdcms
#
# Licensed under Apache 2.0 licence.
#
# Set the release version across every file that carries it, in one shot.
#
# Usage:
#   python scripts/bump_version.py <version> [--date "3 July 2026"]
#
# <version> may include a leading 'v' and/or a pre-release suffix
# (e.g. v0.6.6-beta.1); only the numeric core (0.6.6) is written into the
# files, so version comparisons in mdcms.py stay well-defined. The release
# workflow calls this with the pushed tag; you can also run it locally.
#
# Files updated:
#   mdcms.py         CURRENT VERSION banner + CLI_VERSION + CLI_RELEASE_DATE
#   pyproject.toml   version
#   app/config.yml   CURRENT VERSION banner
#   app/index.html   CURRENT VERSION banner

import argparse
import datetime
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

BANNER_RE = re.compile(r"CURRENT VERSION:\s*\d+\.\d+(?:\.\d+)?\s*-\s*.*")


def numeric_version(raw: str) -> str:
    m = re.match(r"v?(\d+\.\d+(?:\.\d+)?)", raw.strip())
    if not m:
        sys.exit(f"Not a recognisable version: {raw!r} (expected e.g. 0.6.6 or v0.6.6)")
    return m.group(1)


def human_date() -> str:
    d = datetime.date.today()
    return f"{d.day} {d:%B %Y}"


def replace_once(rel_path: str, pattern: re.Pattern, replacement: str) -> None:
    path = ROOT / rel_path
    text = path.read_text(encoding="utf-8")
    new_text, n = pattern.subn(lambda _m: replacement, text, count=1)
    if n == 0:
        sys.exit(f"Pattern {pattern.pattern!r} not found in {rel_path}")
    path.write_text(new_text, encoding="utf-8")
    print(f"  {rel_path}: {replacement}")


def main() -> None:
    ap = argparse.ArgumentParser(description="Set the MD-CMS release version everywhere.")
    ap.add_argument("version", help="Release version, e.g. 0.6.6 or v0.6.6")
    ap.add_argument("--date", default=None, help='Release date string, e.g. "3 July 2026" (default: today)')
    args = ap.parse_args()

    version = numeric_version(args.version)
    date = args.date or human_date()
    banner = f"CURRENT VERSION: {version} - {date}"

    print(f"Bumping MD-CMS to {version} ({date}):")
    # Version banner in the three carrier files.
    for rel in ("mdcms.py", "app/config.yml", "app/index.html"):
        replace_once(rel, BANNER_RE, banner)
    # Source-of-truth constants.
    replace_once("mdcms.py", re.compile(r'CLI_VERSION = "[^"]*"'), f'CLI_VERSION = "{version}"')
    replace_once("mdcms.py", re.compile(r'CLI_RELEASE_DATE = "[^"]*"'), f'CLI_RELEASE_DATE = "{date}"')
    replace_once("pyproject.toml", re.compile(r'(?m)^version = "[^"]*"'), f'version = "{version}"')


if __name__ == "__main__":
    main()
