#!/usr/bin/env python3
"""Generate repeatable GitHub Release notes from manifest and build plan data."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def load_json(path: Path | None) -> dict | None:
    if path is None or not path.is_file():
        return None
    document = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(document, dict):
        raise RuntimeError(f"Expected a JSON object: {path}")
    return document


def family_map(manifest: dict | None) -> dict[str, dict]:
    if manifest is None:
        return {}
    families = manifest.get("families", [])
    if not isinstance(families, list):
        raise RuntimeError("Manifest families must be a list")
    result: dict[str, dict] = {}
    for entry in families:
        name = entry.get("name")
        if not isinstance(name, str) or not name:
            raise RuntimeError("Manifest contains an unnamed family")
        result[name] = entry
    return result


def format_bytes(size: int) -> str:
    value = float(size)
    for unit in ("B", "KiB", "MiB", "GiB"):
        if value < 1024 or unit == "GiB":
            if unit == "B":
                return f"{int(value)} {unit}"
            return f"{value:.1f} {unit}"
        value /= 1024
    raise AssertionError("unreachable")


def family_line(name: str, current: dict[str, dict], previous: dict[str, dict]) -> str:
    entry = current.get(name) or previous.get(name) or {}
    description = str(entry.get("description", "")).strip()
    return f"- **{name}**" + (f" — {description}" if description else "")


def render_notes(previous_manifest: dict | None, current_manifest: dict, plan: dict, tag: str) -> str:
    previous = family_map(previous_manifest)
    current = family_map(current_manifest)
    added = list(plan.get("new", []))
    updated = list(plan.get("changedExisting", []))
    removed = list(plan.get("remove", []))
    files = [file for entry in current.values() for file in entry.get("files", [])]
    total_bytes = sum(int(file.get("size", 0)) for file in files)

    lines = [
        "## Catalog update",
        "",
        f"This update keeps the stable `{tag}` compatibility channel and publishes a complete catalog of "
        f"**{len(current)} font families** and **{len(files)} `.cpfont` files** ({format_bytes(total_bytes)}).",
        "",
        "All families provide physical **8, 10, and 12 pt UI files** plus **14, 16, 18, and 22 pt reader files**. "
        "CrossPoint Reader selects a real installed size and does not scale CJK glyphs on the device.",
    ]

    for heading, names in (("Added", added), ("Updated", updated), ("Removed", removed)):
        if names:
            lines.extend(["", f"### {heading}", ""])
            lines.extend(family_line(name, current, previous) for name in names)

    if not added and not updated and not removed:
        lines.extend(["", "### Changes", "", "- Release metadata and reproducibility records were refreshed; font family membership is unchanged."])

    lines.extend(
        [
            "",
            "### Installation",
            "",
            "Browse previews and download individual physical sizes from the "
            "[CrossPoint CJK font catalog](https://aber0724.github.io/crosspoint-cjk-fonts/). "
            "Device downloads continue to use this GitHub Release directly.",
            "",
            "### Verification and licensing",
            "",
            "- `fonts.json` is the complete firmware manifest (schema 2).",
            "- `build-index.json` records the reproducible per-family build fingerprints and file hashes.",
            "- Every published `.cpfont` uses binary format 4 and is checked for size, SHA-256, and structure before metadata is updated.",
            "- See `FONT-LICENSES.md` and `OFL-1.1.txt` in the Release assets for attribution and redistribution terms.",
            "",
        ]
    )
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--previous-manifest", type=Path)
    parser.add_argument("--current-manifest", type=Path, required=True)
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--tag", required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    previous = load_json(args.previous_manifest)
    current = load_json(args.current_manifest)
    plan = load_json(args.plan)
    if current is None or plan is None:
        raise RuntimeError("Current manifest and plan are required")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(render_notes(previous, current, plan, args.tag), encoding="utf-8", newline="\n")
    print(f"Generated Release notes for {len(current.get('families', []))} families.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
