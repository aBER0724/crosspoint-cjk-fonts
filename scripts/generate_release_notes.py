#!/usr/bin/env python3
"""Generate repeatable GitHub Release notes from manifest and build plan data.

Notes accumulate an append-only, per-date, collapsible Changelog so each
release visibly records what changed and when (optionally tied to the PR that
contributed the fonts).
"""

from __future__ import annotations

import argparse
import datetime
import json
import re
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


def change_item(prefix: str, name: str, current: dict[str, dict], previous: dict[str, dict], pr_link: str) -> str:
    entry = current.get(name) or previous.get(name) or {}
    description = str(entry.get("description", "")).strip()
    return f"- {prefix} **{name}**" + (f" — {description}" if description else "") + pr_link


def extract_changelog(notes: str) -> str:
    """Return the existing collapsible changelog block (without the heading)."""
    start = notes.find("## Changelog")
    if start == -1:
        return ""
    end = notes.find("### Installation", start)
    body = notes[start + len("## Changelog"):] if end == -1 else notes[start + len("## Changelog"):end]
    return body.strip()


_CHANGELOG_ENTRY_RE = re.compile(r"<details>\s*<summary>([^<]+)</summary>\s*(.*?)\s*</details>", re.S)


def parse_changelog(notes: str) -> list[dict]:
    """Parse a changelog block (heading already stripped) into [{date, items}], newest first."""
    entries: list[dict] = []
    for match in _CHANGELOG_ENTRY_RE.finditer(notes):
        items = [line for line in match.group(2).splitlines() if line.strip()]
        entries.append({"date": match.group(1).strip(), "items": items})
    return entries


def serialize_changelog(entries: list[dict]) -> str:
    """Render parsed changelog entries back to a collapsible block (no heading)."""
    blocks = []
    for entry in entries:
        blocks.append(
            "\n".join(
                ["<details>", f"<summary>{entry['date']}</summary>", ""] + entry["items"] + ["", "</details>"]
            )
        )
    return "\n\n".join(blocks)


def change_item_key(item: str) -> str:
    """Normalize a change item to its (prefix, family) key for same-day dedup."""
    text = item.strip()
    for prefix in ("Add", "Update", "Remove"):
        marker = f"- {prefix} **"
        if text.startswith(marker):
            rest = text[len(marker):]
            return f"{prefix} {rest.split('**', 1)[0]}"
    return text


def changelog_entry(change_items: list[str], date: str) -> str:
    return "\n".join(["<details>", f"<summary>{date}</summary>", ""] + change_items + ["", "</details>"])


def merge_same_day_changelog(change_items: list[str], date: str, previous_changelog: str) -> str:
    """Merge today's changes into the newest changelog entry when it is for the same date.

    Rebuilding the same families several times in one day (e.g. a forced full
    re-publish) would otherwise stack near-identical per-date entries. When the
    newest entry already covers every changed family, the existing entry is kept
    as-is; when new families appear, they are appended to that entry.
    """
    entries = parse_changelog(previous_changelog)
    if not entries or entries[0]["date"] != date:
        block = changelog_entry(change_items, date)
        if previous_changelog:
            block += "\n\n" + previous_changelog
        return block
    existing_items = entries[0]["items"]
    existing_keys = {change_item_key(item) for item in existing_items}
    new_items = [item for item in change_items if change_item_key(item) not in existing_keys]
    if not new_items:
        return previous_changelog
    entries[0]["items"] = existing_items + new_items
    return serialize_changelog(entries)

def render_notes(
    previous_manifest: dict | None,
    current_manifest: dict,
    plan: dict,
    tag: str,
    previous_notes: str = "",
    date: str | None = None,
    pr: str | None = None,
) -> str:
    previous = family_map(previous_manifest)
    current = family_map(current_manifest)
    added = list(plan.get("new", []))
    updated = list(plan.get("changedExisting", []))
    removed = list(plan.get("remove", []))
    files = [file for entry in current.values() for file in entry.get("files", [])]
    total_bytes = sum(int(file.get("size", 0)) for file in files)

    if date is None:
        date = datetime.datetime.now(datetime.timezone.utc).date().isoformat()
    pr_link = ""
    if pr:
        pr_link = f" (via [PR #{pr}](https://github.com/aBER0724/crosspoint-cjk-fonts/pull/{pr}))"

    lines = [
        "## Catalog update",
        "",
        f"This update keeps the stable `{tag}` compatibility channel and publishes a complete catalog of "
        f"**{len(current)} font families** and **{len(files)} `.cpfont` files** ({format_bytes(total_bytes)}).",
        "",
        "All families provide physical **8, 10, and 12 pt UI files** plus **14, 16, 18, and 22 pt reader files**. "
        "CrossPoint Reader selects a real installed size and does not scale CJK glyphs on the device.",
    ]

    change_items = [change_item("Add", name, current, previous, pr_link) for name in added]
    change_items += [change_item("Update", name, current, previous, pr_link) for name in updated]
    change_items += [change_item("Remove", name, current, previous, pr_link) for name in removed]

    previous_changelog = extract_changelog(previous_notes)
    if change_items:
        block = merge_same_day_changelog(change_items, date, previous_changelog)
        lines.extend(["", "## Changelog", "", block])
    elif previous_changelog:
        lines.extend(["", "## Changelog", "", previous_changelog])

    lines.extend(
        [
            "",
            "### Installation",
            "",
            "Browse previews and download individual physical sizes from the "
            "[CrossPoint CJK font catalog](https://aber0724.github.io/crosspoint-cjk-fonts/). "
            "Device downloads continue to use this GitHub Release directly.",
            "",
            "### Verification",
            "",
            "- `fonts.json` is the complete firmware manifest (schema 2).",
            "- `build-index.json` records the reproducible per-family build fingerprints and file hashes.",
            "- Every published `.cpfont` uses binary format 4 and is checked for size, SHA-256, and structure before metadata is updated.",
            "- Source links recorded for each family are available in `FONT-SOURCES.md`.",
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
    parser.add_argument("--previous-notes", type=Path)
    parser.add_argument("--date")
    parser.add_argument("--pr")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    previous = load_json(args.previous_manifest)
    current = load_json(args.current_manifest)
    plan = load_json(args.plan)
    if current is None or plan is None:
        raise RuntimeError("Current manifest and plan are required")
    previous_notes = ""
    if args.previous_notes is not None and args.previous_notes.is_file():
        previous_notes = args.previous_notes.read_text(encoding="utf-8")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        render_notes(previous, current, plan, args.tag, previous_notes=previous_notes, date=args.date, pr=args.pr),
        encoding="utf-8",
        newline="\n",
    )
    print(f"Generated Release notes for {len(current.get('families', []))} families.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
