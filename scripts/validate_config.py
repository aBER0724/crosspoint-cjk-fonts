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
ALLOWED_LANGUAGES = {"zh-Hans", "zh-Hant", "ja"}
ALLOWED_CATEGORIES = {"sans-serif", "serif", "rounded-sans", "handwriting", "fangsong", "display"}
ALLOWED_LICENSE_TYPES = {"commercial-use", "personal-use"}
ALLOWED_SOURCE_SUFFIXES = {".ttf", ".otf", ".zip"}
MAX_UPLOADED_SOURCE_BYTES = 100 * 1024 * 1024
NAME_RE = re.compile(r"^[A-Za-z0-9_-]{1,31}$")
SHA_RE = re.compile(r"^[0-9a-f]{64}$")


def _uploaded_path(root: Path, value: object) -> Path | None:
    if not isinstance(value, str) or not value.strip():
        return None
    relative = Path(value)
    if relative.is_absolute() or ".." in relative.parts or not relative.parts or relative.parts[0] != "community-fonts":
        return None
    return root / relative


def validate_document(document: dict, *, root: Path = ROOT) -> list[str]:
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
    if not isinstance(families, list) or not families:
        errors.append("families must be a non-empty list")
        return errors

    for family in families:
        if not isinstance(family, dict):
            errors.append("family entries must be objects")
            continue
        name = str(family.get("name", ""))
        if not NAME_RE.fullmatch(name):
            errors.append(f"invalid family name: {name!r}")
        if name in names:
            errors.append(f"duplicate family: {name}")
        names.add(name)
        for key in ("description", "category", "intervals"):
            if not family.get(key):
                errors.append(f"{name}: missing {key}")
        if family.get("category") not in ALLOWED_CATEGORIES:
            errors.append(f"{name}: invalid category")
        display_names = family.get("display_names")
        if not isinstance(display_names, dict) or set(display_names) != {"en", "zh", "ja"}:
            errors.append(f"{name}: display_names must define exactly en, zh, and ja")
        elif not all(isinstance(value, str) and value.strip() for value in display_names.values()):
            errors.append(f"{name}: display_names values must be non-empty strings")
        languages = family.get("languages")
        if not isinstance(languages, list) or not languages or not all(isinstance(value, str) and value for value in languages):
            errors.append(f"{name}: languages must be a non-empty string list")
        elif any(value not in ALLOWED_LANGUAGES for value in languages):
            errors.append(f"{name}: unsupported language")
        license_type = family.get("license_type")
        if license_type is not None and license_type not in ALLOWED_LICENSE_TYPES:
            errors.append(f"{name}: license_type must be commercial-use or personal-use when provided")
        for key in ("license_url", "source_url"):
            value = family.get(key)
            if value is not None and (not isinstance(value, str) or not value.strip()):
                errors.append(f"{name}: {key} must be a non-empty string when provided")
        if "sizes" in family:
            errors.append(f"{name}: sizes are catalog-wide; remove the family override")

        source = family.get("source")
        if not isinstance(source, dict):
            errors.append(f"{name}: source must be an object")
            continue
        uploaded = "path" in source
        remote = any(key in source for key in ("url", "filename", "sha256"))
        if uploaded and remote:
            errors.append(f"{name}: source must use either path or url/filename/sha256, not both")
        elif uploaded:
            path = _uploaded_path(root, source.get("path"))
            if path is None:
                errors.append(f"{name}: uploaded source path must stay under community-fonts/{name}/")
            else:
                expected_prefix = root / "community-fonts" / name
                try:
                    path.relative_to(expected_prefix)
                except ValueError:
                    errors.append(f"{name}: uploaded source path must stay under community-fonts/{name}/")
                if path.suffix.lower() not in ALLOWED_SOURCE_SUFFIXES:
                    errors.append(f"{name}: uploaded source must be a TTF, OTF, or ZIP file")
                if not path.is_file():
                    errors.append(f"{name}: uploaded source file does not exist: {source.get('path')}")
                elif path.stat().st_size > MAX_UPLOADED_SOURCE_BYTES:
                    errors.append(f"{name}: uploaded source exceeds the 100 MiB repository file limit")
        else:
            for key in ("url", "filename", "sha256"):
                if not source.get(key):
                    errors.append(f"{name}: source missing {key}")
            if source.get("sha256") and not SHA_RE.fullmatch(str(source["sha256"])):
                errors.append(f"{name}: invalid source SHA-256")

        member = source.get("archive_member")
        if member and Path(member).suffix.lower() not in {".ttf", ".otf"}:
            errors.append(f"{name}: archive_member must be a TTF or OTF")
        source_suffix = Path(str(source.get("path") or source.get("filename") or "")).suffix.lower()
        if source_suffix == ".zip" and not member:
            errors.append(f"{name}: ZIP source requires archive_member")
        if source_suffix != ".zip" and member:
            errors.append(f"{name}: archive_member is only valid for ZIP sources")

    return errors


def main() -> int:
    document = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
    if not isinstance(document, dict):
        print("ERROR: config/fonts.yaml must contain an object", file=sys.stderr)
        return 1
    errors = validate_document(document)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(f"Validated {len(document.get('families', []))} font families.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
