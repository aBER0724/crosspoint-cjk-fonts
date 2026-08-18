#!/usr/bin/env python3
"""Build the CJK CrossPoint font catalog from a locked source manifest."""

from __future__ import annotations

import argparse
import hashlib
import os
import shutil
import subprocess
import sys
import tempfile
import urllib.request
import zipfile
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "fonts.yaml"
FONTCONVERT = ROOT / "scripts" / "fontconvert_sdcard.py"
FALLBACK_FONT = ROOT / "vendor" / "NotoSans-Regular.ttf"
DOWNLOAD_DIR = ROOT / ".cache" / "sources"
INSTANCE_DIR = ROOT / ".cache" / "instances"
DEFAULT_OUTPUT = ROOT / "dist"
DEFAULT_BASE_URL = "https://github.com/aBER0724/crosspoint-cjk-fonts/releases/download/sd-fonts-m2-b4/"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_sha256(path: Path, expected: str, label: str) -> None:
    actual = sha256(path)
    if actual != expected.lower():
        path.unlink(missing_ok=True)
        raise RuntimeError(f"{label}: SHA-256 {actual} does not match locked {expected}")


def download(url: str, destination: Path, expected_sha256: str, label: str) -> Path:
    if destination.is_file():
        try:
            verify_sha256(destination, expected_sha256, label)
            return destination
        except RuntimeError:
            pass

    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=destination.parent, suffix=".download", delete=False) as temporary:
        temporary_path = Path(temporary.name)
    try:
        print(f"Downloading {label}...", flush=True)
        with urllib.request.urlopen(url, timeout=180) as response, temporary_path.open("wb") as output:
            shutil.copyfileobj(response, output, length=1024 * 1024)
        verify_sha256(temporary_path, expected_sha256, label)
        temporary_path.replace(destination)
    except Exception:
        temporary_path.unlink(missing_ok=True)
        raise
    return destination


def extract_archive_member(archive_path: Path, member: str, family: str) -> Path:
    suffix = Path(member).suffix.lower()
    if suffix not in {".ttf", ".otf"}:
        raise RuntimeError(f"{family}: archive member must be a TTF or OTF file")
    destination = DOWNLOAD_DIR / family / f"extracted{suffix}"
    if destination.is_file() and destination.stat().st_mtime_ns >= archive_path.stat().st_mtime_ns:
        return destination

    destination.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archive_path) as archive:
        try:
            info = archive.getinfo(member)
        except KeyError as error:
            raise RuntimeError(f"{family}: {member} is missing from {archive_path.name}") from error
        with archive.open(info) as source, tempfile.NamedTemporaryFile(
            dir=destination.parent, suffix=suffix, delete=False
        ) as temporary:
            temporary_path = Path(temporary.name)
            shutil.copyfileobj(source, temporary)
    temporary_path.replace(destination)
    return destination


def extract_static_instance(source: Path, axes: dict[str, float], family: str) -> Path:
    from fontTools.ttLib import TTFont
    from fontTools.varLib.instancer import instantiateVariableFont

    axis_key = "_".join(f"{key}{value}" for key, value in sorted(axes.items()))
    destination = INSTANCE_DIR / family / f"regular_{axis_key}_{sha256(source)[:16]}.ttf"
    if destination.is_file():
        return destination

    destination.parent.mkdir(parents=True, exist_ok=True)
    source_font = TTFont(str(source))
    try:
        instance = instantiateVariableFont(source_font, axes, updateFontNames=True, optimize=False)
        try:
            with tempfile.NamedTemporaryFile(dir=destination.parent, suffix=".ttf", delete=False) as temporary:
                temporary_path = Path(temporary.name)
            instance.save(str(temporary_path))
        finally:
            instance.close()
    finally:
        source_font.close()
    temporary_path.replace(destination)
    return destination


def resolve_source(family: dict) -> Path:
    source = family["source"]
    archive = download(
        source["url"],
        DOWNLOAD_DIR / family["name"] / source["filename"],
        source["sha256"],
        family["name"],
    )
    resolved = extract_archive_member(archive, source["archive_member"], family["name"]) if source.get(
        "archive_member"
    ) else archive
    if source.get("variable"):
        resolved = extract_static_instance(resolved, source["variable"], family["name"])
    return resolved


def catalog_sizes(document: dict) -> list[int]:
    """Return the ordered physical files shared by every catalog family."""
    return list(dict.fromkeys([*document["ui_sizes"], *document["reader_sizes"]]))


def build_family(family: dict, output: Path, sizes: list[int]) -> None:
    source = resolve_source(family)
    output.mkdir(parents=True, exist_ok=True)
    command = [
        sys.executable,
        str(FONTCONVERT),
        str(source),
        "--style",
        "regular",
        "--fallback-regular",
        str(FALLBACK_FONT),
        "--intervals",
        family["intervals"],
        "--sizes",
        ",".join(str(size) for size in sizes),
        "--name",
        family["name"],
        "--output-dir",
        str(output) + os.sep,
    ]
    if family.get("force_autohint"):
        command.append("--force-autohint")
    print(f"Building {family['name']}...", flush=True)
    subprocess.run(command, check=True)


def run_manifest(output: Path, base_url: str) -> None:
    subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "generate_manifest.py"),
            "--input",
            str(output),
            "--base-url",
            base_url,
            "--output",
            str(output / "fonts.json"),
            "--descriptions-from",
            str(CONFIG),
        ],
        check=True,
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--only", help="Comma-separated family names")
    parser.add_argument("--clean", action="store_true")
    args = parser.parse_args()

    config = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
    families = config.get("families", [])
    sizes = catalog_sizes(config)
    if args.only:
        selected = {name.strip() for name in args.only.split(",") if name.strip()}
        families = [family for family in families if family["name"] in selected]
        missing = selected - {family["name"] for family in families}
        if missing:
            raise RuntimeError("Unknown families: " + ", ".join(sorted(missing)))
    if not families:
        raise RuntimeError("No font families selected")
    if not FALLBACK_FONT.is_file():
        raise RuntimeError(f"Missing locked fallback font: {FALLBACK_FONT}")

    if args.clean:
        shutil.rmtree(args.output, ignore_errors=True)
    args.output.mkdir(parents=True, exist_ok=True)
    for family in families:
        build_family(family, args.output, sizes)
    run_manifest(args.output, args.base_url)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
