#!/usr/bin/env python3
"""Verify a CrossPoint font release directory against fonts.json."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("directory", type=Path)
    args = parser.parse_args()

    manifest_path = args.directory / "fonts.json"
    if not manifest_path.is_file():
        print(f"ERROR: missing {manifest_path}", file=sys.stderr)
        return 1

    with manifest_path.open(encoding="utf-8") as source:
        manifest = json.load(source)

    if manifest.get("version") != 2:
        print("ERROR: manifest version must be 2", file=sys.stderr)
        return 1
    if not str(manifest.get("baseUrl", "")).endswith("/"):
        print("ERROR: baseUrl must end with /", file=sys.stderr)
        return 1

    errors: list[str] = []
    expected: set[str] = {"fonts.json"}
    families = manifest.get("families", [])
    for family in families:
        name = family.get("name", "<unnamed>")
        for key in ("description", "license", "licenseUrl", "sourceUrl"):
            if not family.get(key):
                errors.append(f"{name}: missing {key}")
        for entry in family.get("files", []):
            filename = entry.get("name", "")
            expected.add(filename)
            path = args.directory / filename
            if not path.is_file():
                errors.append(f"{name}: missing {filename}")
                continue
            actual_size = path.stat().st_size
            if actual_size != entry.get("size"):
                errors.append(f"{filename}: size {actual_size} != {entry.get('size')}")
            actual_hash = sha256(path)
            if actual_hash != entry.get("sha256"):
                errors.append(f"{filename}: sha256 mismatch")

    extras = sorted(
        path.name
        for path in args.directory.iterdir()
        if path.is_file() and path.name not in expected and path.name != ".gitkeep"
    )
    if extras:
        errors.append("unlisted files: " + ", ".join(extras))

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    file_count = sum(len(family.get("files", [])) for family in families)
    print(f"Verified {len(families)} families and {file_count} font files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
