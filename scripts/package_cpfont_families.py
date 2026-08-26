#!/usr/bin/env python3
"""Package each built .cpfont family into an installable .cpfontpkg ZIP."""

from __future__ import annotations

import argparse
import hashlib
import json
import zipfile
from pathlib import Path

import yaml

UI_SIZES = (8, 10, 12)
FIXED_ZIP_TIME = (1980, 1, 1, 0, 0, 0)


def zip_info(path: str) -> zipfile.ZipInfo:
    info = zipfile.ZipInfo(path, FIXED_ZIP_TIME)
    info.compress_type = zipfile.ZIP_DEFLATED
    info.external_attr = 0o100644 << 16
    return info


def write_entry(archive: zipfile.ZipFile, path: str, data: bytes) -> None:
    archive.writestr(zip_info(path), data, compresslevel=6)


def package_families(directory: Path, config_path: Path, only: set[str] | None = None) -> list[Path]:
    catalog = json.loads((directory / "fonts.json").read_text(encoding="utf-8"))
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    roles = {family["name"]: family.get("role", "reader") for family in config.get("families", [])}
    outputs: list[Path] = []

    for family in catalog.get("families", []):
        family_id = family["name"]
        if only is not None and family_id not in only:
            continue
        files = sorted(family["files"], key=lambda item: item["physicalSize"])
        sizes = [item["physicalSize"] for item in files]
        missing_ui = sorted(set(UI_SIZES) - set(sizes))
        if missing_ui:
            raise RuntimeError(f"{family_id}: missing UI sizes {missing_ui}")

        role = roles.get(family_id, "reader")
        reader_sizes = [] if role == "ui" else [size for size in sizes if size not in UI_SIZES]
        manifest_files = []
        sums = []
        payloads: list[tuple[str, bytes]] = []
        for item in files:
            source = directory / item["name"]
            data = source.read_bytes()
            digest = hashlib.sha256(data).hexdigest()
            if len(data) != item["byteSize"] or digest != item["sha256"]:
                raise RuntimeError(f"{family_id}: manifest mismatch for {source.name}")
            payloads.append((source.name, data))
            sums.append(f"{digest}  {source.name}")
            manifest_files.append({
                "size": item["physicalSize"],
                "role": "ui" if item["physicalSize"] in UI_SIZES else "reader",
                "file": source.name,
                "styles": family.get("styles", ["regular"]),
                "sizeBytes": len(data),
                "sha256": digest,
            })

        manifest = {
            "format": 1,
            "family": family_id,
            "id": family_id,
            "role": "ui" if role == "ui" else "family",
            "cpfontVersion": 4,
            "uiSizes": list(UI_SIZES),
            "readerSizes": reader_sizes,
            "styles": family.get("styles", ["regular"]),
            "fonts": manifest_files,
        }
        build = {
            "schemaVersion": 1,
            "cpfontVersion": 4,
            "physicalSizes": sizes,
            "uiSizes": list(UI_SIZES),
            "readerSizes": reader_sizes,
            "source": "crosspoint-cjk-fonts GitHub Actions",
            "files": manifest_files,
        }
        output = directory / f"{family_id}.cpfontpkg"
        prefix = f"{family_id}/"
        with zipfile.ZipFile(output, "w") as archive:
            for name, data in payloads:
                write_entry(archive, prefix + name, data)
            write_entry(archive, prefix + "SHA256SUMS", ("\n".join(sums) + "\n").encode())
            write_entry(archive, prefix + "manifest.json", (json.dumps(manifest, ensure_ascii=False, indent=2) + "\n").encode())
            write_entry(archive, prefix + "build.json", (json.dumps(build, ensure_ascii=False, indent=2) + "\n").encode())
        outputs.append(output)

    return outputs


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--directory", type=Path, required=True)
    parser.add_argument("--config", type=Path, default=Path("config/fonts.yaml"))
    parser.add_argument("--only", help="Comma-separated family names to package")
    args = parser.parse_args()
    only = {name.strip() for name in args.only.split(",") if name.strip()} if args.only else None
    for output in package_families(args.directory, args.config, only):
        print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
