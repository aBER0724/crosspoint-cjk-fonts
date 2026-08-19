#!/usr/bin/env python3
"""Download only the `.cpfont` files required for static preview generation."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import urllib.request
from pathlib import Path
from typing import Callable
from urllib.parse import urljoin, urlparse


class PreviewDownloadError(RuntimeError):
    pass


def _require_https(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme != "https" or not parsed.netloc:
        raise PreviewDownloadError(f"preview download URL must be HTTPS: {url}")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _verify(path: Path, entry: dict) -> None:
    expected_size = entry.get("size")
    expected_sha = entry.get("sha256")
    if not isinstance(expected_size, int) or expected_size < 0:
        raise PreviewDownloadError(f"invalid manifest size for {entry.get('name')}")
    if not isinstance(expected_sha, str) or len(expected_sha) != 64:
        raise PreviewDownloadError(f"invalid manifest SHA-256 for {entry.get('name')}")
    if path.stat().st_size != expected_size:
        raise PreviewDownloadError(f"download size mismatch for {entry.get('name')}")
    if _sha256(path) != expected_sha:
        raise PreviewDownloadError(f"download SHA-256 mismatch for {entry.get('name')}")


def _download(url: str, target: Path) -> None:
    request = urllib.request.Request(url, headers={"User-Agent": "crosspoint-cjk-fonts-pages/1"})
    with urllib.request.urlopen(request, timeout=120) as response, target.open("wb") as output:
        while chunk := response.read(1024 * 1024):
            output.write(chunk)


def _physical_size(name: str) -> int | None:
    if not isinstance(name, str) or not name.endswith(".cpfont"):
        return None
    stem = name[: -len(".cpfont")]
    parts = stem.rsplit("_", 1)
    if len(parts) != 2 or not parts[1].isdigit():
        return None
    return int(parts[1])


def download_preview_assets(
    manifest: dict,
    preview_sizes: list[int],
    output_dir: Path,
    *,
    downloader: Callable[[str, Path], None] = _download,
) -> list[Path]:
    if manifest.get("version") != 2:
        raise PreviewDownloadError("release manifest version must be 2")
    base_url = manifest.get("baseUrl")
    if not isinstance(base_url, str):
        raise PreviewDownloadError("release manifest has no baseUrl")
    _require_https(base_url)
    if not base_url.endswith("/"):
        raise PreviewDownloadError("release manifest baseUrl must end with /")

    requested_sizes = set(preview_sizes)
    output_dir.mkdir(parents=True, exist_ok=True)
    downloaded: list[Path] = []
    for family in manifest.get("families", []):
        family_name = family.get("name", "unknown")
        entries = {
            _physical_size(entry.get("name")): entry
            for entry in family.get("files", [])
            if _physical_size(entry.get("name")) in requested_sizes
        }
        if set(entries) != requested_sizes:
            raise PreviewDownloadError(f"{family_name}: manifest is missing preview sizes")
        for size in preview_sizes:
            entry = entries[size]
            name = entry["name"]
            if Path(name).name != name:
                raise PreviewDownloadError(f"unsafe preview filename: {name}")
            target = output_dir / name
            if target.exists():
                try:
                    _verify(target, entry)
                    downloaded.append(target)
                    continue
                except PreviewDownloadError:
                    target.unlink()
            temporary = target.with_name(f".{target.name}.{os.getpid()}.tmp")
            temporary.unlink(missing_ok=True)
            url = urljoin(base_url, name)
            _require_https(url)
            try:
                downloader(url, temporary)
                _verify(temporary, entry)
                temporary.replace(target)
            finally:
                temporary.unlink(missing_ok=True)
            downloaded.append(target)
    return downloaded


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--sizes", default="14,18,22")
    args = parser.parse_args()

    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    sizes = [int(value) for value in args.sizes.split(",") if value]
    files = download_preview_assets(manifest, sizes, args.output)
    print(f"Verified {len(files)} preview font files in {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
