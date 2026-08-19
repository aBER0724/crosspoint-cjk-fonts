#!/usr/bin/env python3
"""Build the static GitHub Pages font catalog and real `.cpfont` previews."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path
from urllib.parse import urljoin, urlparse

import yaml

try:
    from .cpfont_v4 import CpfontError, CpfontFile
    from .render_cpfont_preview import render_text
except ImportError:
    from cpfont_v4 import CpfontError, CpfontFile
    from render_cpfont_preview import render_text


WEB_CATALOG_VERSION = 1
MANIFEST_VERSION = 2
EXPECTED_ALL_SIZES = [8, 10, 12, 14, 16, 18, 22]
DISALLOWED_SUFFIXES = {".cpfont", ".ttf", ".otf", ".zip", ".rar", ".7z"}


class CatalogBuildError(RuntimeError):
    pass


def preview_text_for_languages(samples: dict, languages: list[str]) -> str:
    by_language = samples.get("byLanguage")
    symbols = samples.get("symbols")
    latin = samples.get("latin")
    if not isinstance(by_language, dict) or not isinstance(symbols, str) or not symbols:
        raise CatalogBuildError("pages/samples.json must define non-empty byLanguage and symbols samples")
    if not isinstance(latin, str) or not latin:
        raise CatalogBuildError("pages/samples.json must define a non-empty latin sample")

    if not isinstance(languages, list) or not languages:
        raise CatalogBuildError("font family must declare at least one preview language")

    lines = []
    for language in languages:
        line = by_language.get(language)
        if not isinstance(line, str) or not line:
            raise CatalogBuildError(f"pages/samples.json has no sample for language {language}")
        if line not in lines:
            lines.append(line)
    return "\n".join([*lines, symbols, latin])


def _load_yaml(path: Path) -> dict:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise CatalogBuildError(f"invalid YAML document: {path}")
    return value


def _load_json(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise CatalogBuildError(f"invalid JSON document: {path}")
    return value


def _https_url(value: object, label: str, *, trailing_slash: bool = False) -> str:
    if not isinstance(value, str):
        raise CatalogBuildError(f"{label} must be a URL")
    parsed = urlparse(value)
    if parsed.scheme != "https" or not parsed.netloc:
        raise CatalogBuildError(f"{label} must use HTTPS")
    if parsed.username or parsed.password or parsed.fragment:
        raise CatalogBuildError(f"{label} contains unsafe URL components")
    if trailing_slash and not value.endswith("/"):
        raise CatalogBuildError(f"{label} must end with /")
    return value


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _parse_filename(name: object) -> tuple[str, int] | None:
    if not isinstance(name, str) or Path(name).name != name or not name.endswith(".cpfont"):
        return None
    parts = name[: -len(".cpfont")].rsplit("_", 1)
    if len(parts) != 2 or not parts[1].isdigit():
        return None
    return parts[0], int(parts[1])


def _file_entry(entry: dict, family_name: str, base_url: str) -> dict:
    parsed = _parse_filename(entry.get("name"))
    if parsed is None or parsed[0] != family_name:
        raise CatalogBuildError(f"{family_name}: invalid manifest filename")
    name = entry["name"]
    byte_size = entry.get("size")
    digest = entry.get("sha256")
    if not isinstance(byte_size, int) or byte_size <= 0:
        raise CatalogBuildError(f"{name}: invalid manifest metadata size")
    if not isinstance(digest, str) or len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest):
        raise CatalogBuildError(f"{name}: invalid manifest metadata SHA-256")
    return {
        "name": name,
        "physicalSize": parsed[1],
        "byteSize": byte_size,
        "sha256": digest,
        "downloadUrl": _https_url(urljoin(base_url, name), f"{name} download URL"),
    }


def _localized_display_names(value: object, family_name: str) -> dict[str, str]:
    if not isinstance(value, dict):
        raise CatalogBuildError(f"{family_name}: display_names.en must be a non-empty string")
    english = value.get("en")
    if not isinstance(english, str) or not english.strip():
        raise CatalogBuildError(f"{family_name}: display_names.en must be a non-empty string")
    result = {"en": english.strip()}
    for locale in ("zh", "ja"):
        localized = value.get(locale, english)
        if not isinstance(localized, str) or not localized.strip():
            raise CatalogBuildError(
                f"{family_name}: display_names.{locale} must be a non-empty string when provided"
            )
        result[locale] = localized.strip()
    return result


def _copy_static_source(source_dir: Path, output_dir: Path) -> None:
    if output_dir.exists():
        shutil.rmtree(output_dir)
    shutil.copytree(source_dir, output_dir)
    for path in output_dir.rglob("*"):
        if path.is_file() and path.suffix.lower() in DISALLOWED_SUFFIXES:
            raise CatalogBuildError(f"static source contains forbidden payload: {path.name}")


def build_site(
    *,
    config_path: Path,
    manifest_path: Path,
    fonts_dir: Path,
    source_dir: Path,
    output_dir: Path,
    site_url: str,
    manifest_url: str,
    font_maker_url: str,
) -> dict:
    config = _load_yaml(config_path)
    manifest = _load_json(manifest_path)
    samples = _load_json(source_dir / "samples.json")
    if manifest.get("version") != MANIFEST_VERSION:
        raise CatalogBuildError(f"release manifest version must be {MANIFEST_VERSION}")
    if samples.get("schemaVersion") != 1:
        raise CatalogBuildError("pages/samples.json must use schemaVersion 1")

    base_url = _https_url(manifest.get("baseUrl"), "release base URL", trailing_slash=True)
    site_url = _https_url(site_url, "site URL", trailing_slash=True)
    manifest_url = _https_url(manifest_url, "manifest URL")
    font_maker_url = _https_url(font_maker_url, "Font Maker URL")
    preview_sizes = config.get("preview_sizes")
    all_sizes = list(dict.fromkeys(config.get("ui_sizes", []) + config.get("reader_sizes", [])))
    if all_sizes != EXPECTED_ALL_SIZES:
        raise CatalogBuildError(f"catalog physical sizes must be {EXPECTED_ALL_SIZES}")
    if preview_sizes != [14, 18, 22]:
        raise CatalogBuildError("catalog preview sizes must be [14, 18, 22]")

    config_families = {family.get("name"): family for family in config.get("families", [])}
    manifest_families = {family.get("name"): family for family in manifest.get("families", [])}
    if not config_families or set(config_families) != set(manifest_families):
        raise CatalogBuildError("config and release manifest family sets do not match")

    _copy_static_source(source_dir, output_dir)
    previews_dir = output_dir / "previews"
    previews_dir.mkdir(parents=True)
    catalog_families = []
    try:
        for family_name in sorted(config_families):
            editorial = config_families[family_name]
            published = manifest_families[family_name]
            if editorial.get("description") != published.get("description"):
                raise CatalogBuildError(
                    f"{family_name}: config and manifest metadata disagree for description"
                )
            if editorial.get("source_url") != published.get("sourceUrl"):
                raise CatalogBuildError(
                    f"{family_name}: config and manifest metadata disagree for source_url"
                )

            files = [_file_entry(entry, family_name, base_url) for entry in published.get("files", [])]
            files.sort(key=lambda entry: entry["physicalSize"])
            if [entry["physicalSize"] for entry in files] != all_sizes:
                raise CatalogBuildError(f"{family_name}: manifest physical sizes do not match catalog")

            languages = editorial.get("languages", [])
            display_names = _localized_display_names(editorial.get("display_names"), family_name)
            preview_text = preview_text_for_languages(samples, languages)
            previews = {}
            entries_by_size = {entry["physicalSize"]: entry for entry in files}
            for size in preview_sizes:
                entry = entries_by_size[size]
                font_path = fonts_dir / entry["name"]
                if not font_path.is_file():
                    raise CatalogBuildError(f"{family_name}: missing preview file {entry['name']}")
                if font_path.stat().st_size != entry["byteSize"] or _sha256(font_path) != entry["sha256"]:
                    raise CatalogBuildError(f"{family_name}: preview file disagrees with manifest metadata")
                try:
                    font = CpfontFile.from_path(font_path)
                    result = render_text(
                        font,
                        preview_text,
                        canvas_width=880,
                        padding=24,
                        transparent_background=True,
                    )
                except (CpfontError, ValueError) as error:
                    raise CatalogBuildError(f"{family_name}: cannot render {entry['name']}: {error}") from error
                preview_name = f"{family_name}_{size}.png"
                result.image.save(previews_dir / preview_name, format="PNG", optimize=True)
                previews[str(size)] = urljoin(site_url, f"previews/{preview_name}")

            family_entry = {
                "name": family_name,
                "displayNames": display_names,
                "category": editorial.get("category", "other"),
                "languages": languages,
                "styles": published.get("styles", []),
                "files": files,
                "previews": previews,
            }
            if editorial.get("description"):
                family_entry["description"] = editorial["description"]
            if editorial.get("source_url"):
                family_entry["sourceUrl"] = _https_url(
                    editorial["source_url"], f"{family_name} source URL"
                )
            catalog_families.append(family_entry)

        catalog = {
            "schemaVersion": WEB_CATALOG_VERSION,
            "cpfontVersion": 4,
            "manifestVersion": MANIFEST_VERSION,
            "siteUrl": site_url,
            "manifestUrl": manifest_url,
            "fontMakerUrl": font_maker_url,
            "previewSizes": preview_sizes,
            "families": catalog_families,
        }
        (output_dir / "catalog.json").write_text(
            json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        return catalog
    except Exception:
        shutil.rmtree(output_dir, ignore_errors=True)
        raise


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="config/fonts.yaml", type=Path)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--fonts", required=True, type=Path)
    parser.add_argument("--source", default="pages", type=Path)
    parser.add_argument("--output", default="site-dist", type=Path)
    parser.add_argument("--site-url", default="https://aber0724.github.io/crosspoint-cjk-fonts/")
    parser.add_argument(
        "--manifest-url",
        default="https://github.com/aBER0724/crosspoint-cjk-fonts/releases/download/sd-fonts-m2-b4/fonts.json",
    )
    parser.add_argument("--font-maker-url", default="https://crosspoint-cjk-font-maker.onrender.com/")
    args = parser.parse_args()

    catalog = build_site(
        config_path=args.config,
        manifest_path=args.manifest,
        fonts_dir=args.fonts,
        source_dir=args.source,
        output_dir=args.output,
        site_url=args.site_url,
        manifest_url=args.manifest_url,
        font_maker_url=args.font_maker_url,
    )
    print(f"Built {len(catalog['families'])} families in {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
