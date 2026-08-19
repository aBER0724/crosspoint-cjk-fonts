#!/usr/bin/env python3
"""Validate the declarative font catalog before a long CI build starts."""

from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "fonts.yaml"
EXPECTED_UI_SIZES = [8, 10, 12]
EXPECTED_READER_SIZES = [14, 16, 18, 22]
EXPECTED_PREVIEW_SIZES = [14, 18, 22]
NAME_RE = re.compile(r"^[A-Za-z0-9_-]{1,31}$")
SHA_RE = re.compile(r"^[0-9a-f]{64}$")


def main() -> int:
    document = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
    families = document.get("families", [])
    errors: list[str] = []
    names: set[str] = set()

    ui_sizes = document.get("ui_sizes")
    reader_sizes = document.get("reader_sizes")
    preview_sizes = document.get("preview_sizes")
    if ui_sizes != EXPECTED_UI_SIZES:
        errors.append(f"ui_sizes must be {EXPECTED_UI_SIZES}")
    if reader_sizes != EXPECTED_READER_SIZES:
        errors.append(f"reader_sizes must be {EXPECTED_READER_SIZES}")
    if preview_sizes != EXPECTED_PREVIEW_SIZES:
        errors.append(f"preview_sizes must be {EXPECTED_PREVIEW_SIZES}")
    if (
        isinstance(preview_sizes, list)
        and isinstance(reader_sizes, list)
        and not set(preview_sizes).issubset(reader_sizes)
    ):
        errors.append("preview_sizes must be a subset of reader_sizes")

    for family in families:
        name = str(family.get("name", ""))
        if not NAME_RE.fullmatch(name):
            errors.append(f"invalid family name: {name!r}")
        if name in names:
            errors.append(f"duplicate family: {name}")
        names.add(name)
        for key in ("description", "category", "license", "license_url", "source_url", "intervals"):
            if not family.get(key):
                errors.append(f"{name}: missing {key}")
        display_names = family.get("display_names")
        if not isinstance(display_names, dict) or set(display_names) != {"en", "zh", "ja"}:
            errors.append(f"{name}: display_names must define exactly en, zh, and ja")
        elif not all(isinstance(value, str) and value.strip() for value in display_names.values()):
            errors.append(f"{name}: display_names values must be non-empty strings")
        languages = family.get("languages")
        if not isinstance(languages, list) or not languages or not all(isinstance(value, str) and value for value in languages):
            errors.append(f"{name}: languages must be a non-empty string list")
        if family.get("license") != "OFL-1.1":
            errors.append(f"{name}: only the reviewed OFL-1.1 catalog is accepted")
        if "sizes" in family:
            errors.append(f"{name}: sizes are catalog-wide; remove the family override")
        source = family.get("source", {})
        for key in ("url", "filename", "sha256"):
            if not source.get(key):
                errors.append(f"{name}: source missing {key}")
        if source.get("sha256") and not SHA_RE.fullmatch(str(source["sha256"])):
            errors.append(f"{name}: invalid source SHA-256")
        member = source.get("archive_member")
        if member and Path(member).suffix.lower() not in {".ttf", ".otf"}:
            errors.append(f"{name}: archive_member must be a TTF or OTF")

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(f"Validated {len(families)} locked font families.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
