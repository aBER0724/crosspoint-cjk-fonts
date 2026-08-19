#!/usr/bin/env python3

import hashlib
import json
import struct
import tempfile
import unittest
from pathlib import Path

import yaml
from PIL import Image

from scripts.build_pages import CatalogBuildError, build_site, preview_text_for_languages
from scripts.fetch_release_previews import download_preview_assets


GLOBAL_HEADER = struct.Struct("<8sHHB19s")
STYLE_TOC = struct.Struct("<B3xIIBhhHHBBBI4x")
INTERVAL = struct.Struct("<III")
GLYPH = struct.Struct("<BBHhhH2xI")


def tiny_cpfont() -> bytes:
    interval = INTERVAL.pack(0x41, 0x41, 0)
    glyph = GLYPH.pack(1, 1, 16, 0, 1, 1, 0)
    bitmap = b"\xc0"
    style_data = interval + glyph + bitmap
    data_offset = GLOBAL_HEADER.size + STYLE_TOC.size
    header = GLOBAL_HEADER.pack(b"CPFONT\x00\x00", 4, 1, 1, bytes(19))
    toc = STYLE_TOC.pack(0, 1, 1, 4, 3, -1, 0, 0, 0, 0, 0, data_offset)
    return header + toc + style_data


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class PagesCatalogTest(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name)
        self.config_path = self.root / "fonts.yaml"
        self.manifest_path = self.root / "fonts.json"
        self.fonts_dir = self.root / "fonts"
        self.source_dir = self.root / "pages"
        self.output_dir = self.root / "site-dist"
        self.fonts_dir.mkdir()
        (self.source_dir / "assets").mkdir(parents=True)
        (self.source_dir / "index.html").write_text(
            '<!doctype html><script type="module" src="assets/app.js"></script>', encoding="utf-8"
        )
        (self.source_dir / "assets" / "app.js").write_text("fetch('catalog.json')", encoding="utf-8")
        (self.source_dir / "assets" / "app.css").write_text("body { color: #111; }", encoding="utf-8")
        (self.source_dir / "samples.json").write_text(
            json.dumps(
                {
                    "schemaVersion": 1,
                    "byLanguage": {"zh-Hans": "A", "ja": "A"},
                    "symbols": "A",
                    "latin": "A",
                }
            ),
            encoding="utf-8",
        )

        self.font_bytes = tiny_cpfont()
        all_sizes = [8, 10, 12, 14, 16, 18, 22]
        preview_sizes = [14, 18, 22]
        self.config = {
            "ui_sizes": [8, 10, 12],
            "reader_sizes": [14, 16, 18, 22],
            "preview_sizes": preview_sizes,
            "families": [
                {
                    "name": "ExampleCJK",
                    "display_names": {
                        "en": "Example CJK",
                        "zh": "示例字体",
                        "ja": "サンプル書体",
                    },
                    "description": "Example catalog font",
                    "category": "sans-serif",
                    "languages": ["zh-Hans", "ja"],
                    "license": "OFL-1.1",
                    "license_url": "https://example.com/license",
                    "source_url": "https://example.com/source",
                    "intervals": "latin-ext,cjk",
                    "source": {
                        "url": "https://example.com/font.ttf",
                        "filename": "font.ttf",
                        "sha256": "0" * 64,
                    },
                }
            ],
        }
        self.config_path.write_text(yaml.safe_dump(self.config, sort_keys=False), encoding="utf-8")

        files = []
        for size in all_sizes:
            name = f"ExampleCJK_{size}.cpfont"
            files.append(
                {
                    "name": name,
                    "size": len(self.font_bytes),
                    "sha256": sha256(self.font_bytes),
                }
            )
            if size in preview_sizes:
                (self.fonts_dir / name).write_bytes(self.font_bytes)
        self.manifest = {
            "version": 2,
            "baseUrl": "https://github.com/aBER0724/crosspoint-cjk-fonts/releases/download/sd-fonts-m2-b4/",
            "families": [
                {
                    "name": "ExampleCJK",
                    "description": "Example catalog font",
                    "styles": ["regular"],
                    "license": "OFL-1.1",
                    "licenseUrl": "https://example.com/license",
                    "sourceUrl": "https://example.com/source",
                    "files": files,
                }
            ],
        }
        self.manifest_path.write_text(json.dumps(self.manifest), encoding="utf-8")

    def tearDown(self):
        self.tempdir.cleanup()

    def build(self):
        return build_site(
            config_path=self.config_path,
            manifest_path=self.manifest_path,
            fonts_dir=self.fonts_dir,
            source_dir=self.source_dir,
            output_dir=self.output_dir,
            site_url="https://fonts.example/",
            manifest_url="https://github.com/example/release/fonts.json",
            font_maker_url="https://maker.example/",
        )

    def test_builds_strict_web_catalog_and_real_previews(self):
        catalog = self.build()

        self.assertEqual(catalog["schemaVersion"], 1)
        self.assertEqual(catalog["cpfontVersion"], 4)
        self.assertEqual(catalog["manifestVersion"], 2)
        self.assertEqual(catalog["previewSizes"], [14, 18, 22])
        family = catalog["families"][0]
        self.assertEqual(family["name"], "ExampleCJK")
        self.assertEqual(
            family["displayNames"],
            {"en": "Example CJK", "zh": "示例字体", "ja": "サンプル書体"},
        )
        self.assertEqual(family["licenseStatus"], "verified")
        self.assertEqual(family["languages"], ["zh-Hans", "ja"])
        self.assertEqual(family["category"], "sans-serif")
        self.assertEqual([entry["physicalSize"] for entry in family["files"]], [8, 10, 12, 14, 16, 18, 22])
        self.assertTrue(all(entry["downloadUrl"].startswith(self.manifest["baseUrl"]) for entry in family["files"]))
        self.assertEqual(sorted(family["previews"]), ["14", "18", "22"])
        self.assertTrue(all(url.startswith("https://fonts.example/previews/") for url in family["previews"].values()))

        written = json.loads((self.output_dir / "catalog.json").read_text(encoding="utf-8"))
        self.assertEqual(written, catalog)
        preview = Image.open(self.output_dir / "previews" / "ExampleCJK_14.png")
        self.assertEqual(preview.mode, "RGBA")
        self.assertEqual(preview.getextrema()[3], (0, 255))
        self.assertEqual(preview.getpixel((0, 0)), (255, 255, 255, 0))

    def test_preview_sample_follows_declared_languages_and_adds_symbols(self):
        samples = {
            "schemaVersion": 1,
            "byLanguage": {"zh-Hans": "简体", "zh-Hant": "繁體", "ja": "日本語"},
            "symbols": "，。！？—…· @#$%&*+-=/",
            "latin": "CrossPoint Reader · 1234567890",
        }

        self.assertEqual(
            preview_text_for_languages(samples, ["zh-Hans", "ja"]),
            "简体\n日本語\n，。！？—…· @#$%&*+-=/\nCrossPoint Reader · 1234567890",
        )
        self.assertEqual(
            preview_text_for_languages(samples, ["zh-Hant"]),
            "繁體\n，。！？—…· @#$%&*+-=/\nCrossPoint Reader · 1234567890",
        )
        with self.assertRaisesRegex(CatalogBuildError, "at least one preview language"):
            preview_text_for_languages(samples, [])
        with self.assertRaisesRegex(CatalogBuildError, "no sample for language ko"):
            preview_text_for_languages(samples, ["ko"])

    def test_pages_artifact_contains_no_font_or_archive_payloads(self):
        self.build()

        suffixes = {path.suffix.lower() for path in self.output_dir.rglob("*") if path.is_file()}
        self.assertTrue(suffixes.isdisjoint({".cpfont", ".ttf", ".otf", ".zip", ".rar", ".7z"}))
        html = (self.output_dir / "index.html").read_text(encoding="utf-8")
        self.assertNotIn('src="http', html)
        self.assertNotIn('href="http', html)

    def test_rejects_manifest_mismatch_and_missing_preview(self):
        bad_manifest = json.loads(json.dumps(self.manifest))
        preview_entry = next(
            entry for entry in bad_manifest["families"][0]["files"] if entry["name"].endswith("_14.cpfont")
        )
        preview_entry["sha256"] = "f" * 64
        self.manifest_path.write_text(json.dumps(bad_manifest), encoding="utf-8")
        with self.assertRaisesRegex(CatalogBuildError, "manifest metadata"):
            self.build()

        self.manifest_path.write_text(json.dumps(self.manifest), encoding="utf-8")
        (self.fonts_dir / "ExampleCJK_18.cpfont").unlink()
        with self.assertRaisesRegex(CatalogBuildError, "preview file"):
            self.build()

    def test_rejects_missing_or_invalid_localized_display_names(self):
        missing = yaml.safe_load(self.config_path.read_text(encoding="utf-8"))
        del missing["families"][0]["display_names"]["zh"]
        self.config_path.write_text(yaml.safe_dump(missing, sort_keys=False, allow_unicode=True), encoding="utf-8")
        with self.assertRaisesRegex(CatalogBuildError, "localized display names"):
            self.build()

        invalid = yaml.safe_load(yaml.safe_dump(self.config, sort_keys=False, allow_unicode=True))
        invalid["families"][0]["display_names"]["ja"] = ""
        self.config_path.write_text(yaml.safe_dump(invalid, sort_keys=False, allow_unicode=True), encoding="utf-8")
        with self.assertRaisesRegex(CatalogBuildError, "localized display names"):
            self.build()

    def test_rejects_unsafe_urls_and_unexpected_size_set(self):
        unsafe = json.loads(json.dumps(self.manifest))
        unsafe["baseUrl"] = "http://example.com/fonts/"
        self.manifest_path.write_text(json.dumps(unsafe), encoding="utf-8")
        with self.assertRaisesRegex(CatalogBuildError, "HTTPS"):
            self.build()

        wrong_sizes = json.loads(json.dumps(self.manifest))
        wrong_sizes["families"][0]["files"].pop()
        self.manifest_path.write_text(json.dumps(wrong_sizes), encoding="utf-8")
        with self.assertRaisesRegex(CatalogBuildError, "physical sizes"):
            self.build()


class PreviewDownloadTest(unittest.TestCase):
    def test_downloads_only_preview_sizes_and_verifies_hashes(self):
        font_bytes = tiny_cpfont()
        manifest = {
            "version": 2,
            "baseUrl": "https://example.com/fonts/",
            "families": [
                {
                    "name": "ExampleCJK",
                    "files": [
                        {
                            "name": f"ExampleCJK_{size}.cpfont",
                            "size": len(font_bytes),
                            "sha256": sha256(font_bytes),
                        }
                        for size in (8, 10, 12, 14, 16, 18, 22)
                    ],
                }
            ],
        }
        requested = []

        def downloader(url: str, target: Path) -> None:
            requested.append(url)
            target.write_bytes(font_bytes)

        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            download_preview_assets(manifest, [14, 18, 22], output, downloader=downloader)
            self.assertEqual(
                requested,
                [
                    "https://example.com/fonts/ExampleCJK_14.cpfont",
                    "https://example.com/fonts/ExampleCJK_18.cpfont",
                    "https://example.com/fonts/ExampleCJK_22.cpfont",
                ],
            )
            self.assertEqual(
                sorted(path.name for path in output.glob("*.cpfont")),
                ["ExampleCJK_14.cpfont", "ExampleCJK_18.cpfont", "ExampleCJK_22.cpfont"],
            )


if __name__ == "__main__":
    unittest.main()
