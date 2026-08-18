#!/usr/bin/env python3
"""Validate the declarative font catalog before a long CI build starts."""

from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "fonts.yaml"
EXPECTED_SIZES = [8, 10, 12, 14, 16, 18]
NAME_RE = re.compile(r"^[A-Za-z0-9_-]{1,31}$")
SHA_RE = re.compile(r"^[0-9a-f]{64}$")


def main() -> int:
    document = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
    families = document.get("families", [])
    errors: list[str] = []
    names: set[str] = set()

    for family in families:
        name = str(family.get("name", ""))
        if not NAME_RE.fullmatch(name):
            errors.append(f"invalid family name: {name!r}")
        if name in names:
            errors.append(f"duplicate family: {name}")
        names.add(name)
        for key in ("description", "license", "license_url", "source_url", "intervals"):
            if not family.get(key):
                errors.append(f"{name}: missing {key}")
        if family.get("license") != "OFL-1.1":
            errors.append(f"{name}: only the reviewed OFL-1.1 catalog is accepted")
        if family.get("sizes") != EXPECTED_SIZES:
            errors.append(f"{name}: sizes must be {EXPECTED_SIZES}")
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
