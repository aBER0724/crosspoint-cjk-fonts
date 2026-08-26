#!/usr/bin/env python3

import hashlib
import json
import struct
import tempfile
import unittest
from pathlib import Path

import yaml
from PIL import Image

from scripts.build_pages import CatalogBuildError, build_site, preview_text_from_preset
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
                    "schemaVersion": 2,
                    "source": "crosspoint-cjk-font-maker/web/app.js#DEFAULT_PREVIEW_TEXT",
                    "presetText": "A",
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
                    "role": "ui",
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
            "updatedAt": "2026-08-20T06:11:03Z",
            "families": [
                {
                    "name": "ExampleCJK",
                    "description": "Example catalog font",
                    "styles": ["regular"],
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
        self.assertEqual(catalog["updatedAt"], "2026-08-20T06:11:03Z")
        family = catalog["families"][0]
        self.assertEqual(family["name"], "ExampleCJK")
        self.assertEqual(
            family["displayNames"],
            {"en": "Example CJK", "zh": "示例字体", "ja": "サンプル書体"},
        )
        self.assertNotIn("license", family)
        self.assertNotIn("licenseStatus", family)
        self.assertNotIn("licenseType", family)
        self.assertEqual(family["sourceUrl"], "https://example.com/source")
        self.assertEqual(family["languages"], ["zh-Hans", "ja"])
        self.assertEqual(family["role"], "ui")
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

    def test_catalog_omits_updated_at_when_manifest_lacks_it(self):
        del self.manifest["updatedAt"]
        self.manifest_path.write_text(json.dumps(self.manifest), encoding="utf-8")
        catalog = self.build()
        self.assertNotIn("updatedAt", catalog)

    def test_preview_sample_uses_maker_preset_text(self):
        samples = {
            "schemaVersion": 2,
            "source": "crosspoint-cjk-font-maker/web/app.js#DEFAULT_PREVIEW_TEXT",
            "presetText": "中文测试\n日本語テスト\nEnglish test",
        }

        self.assertEqual(
            preview_text_from_preset(samples),
            "中文测试\n日本語テスト\nEnglish test",
        )
        with self.assertRaisesRegex(CatalogBuildError, "non-empty Maker presetText"):
            preview_text_from_preset({"schemaVersion": 2, "presetText": ""})

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

    def test_optional_localized_names_fall_back_to_english_and_description_may_be_omitted(self):
        minimal = yaml.safe_load(self.config_path.read_text(encoding="utf-8"))
        minimal["families"][0]["display_names"] = {"en": "Example CJK"}
        minimal["families"][0].pop("description")
        self.config_path.write_text(yaml.safe_dump(minimal, sort_keys=False, allow_unicode=True), encoding="utf-8")
        self.manifest["families"][0].pop("description")
        self.manifest_path.write_text(json.dumps(self.manifest), encoding="utf-8")

        family = self.build()["families"][0]

        self.assertEqual(family["displayNames"], {"en": "Example CJK", "zh": "Example CJK", "ja": "Example CJK"})
        self.assertNotIn("description", family)

    def test_rejects_missing_or_blank_english_display_name(self):
        invalid = yaml.safe_load(yaml.safe_dump(self.config, sort_keys=False, allow_unicode=True))
        invalid["families"][0]["display_names"] = {"zh": "示例字体"}
        self.config_path.write_text(yaml.safe_dump(invalid, sort_keys=False, allow_unicode=True), encoding="utf-8")
        with self.assertRaisesRegex(CatalogBuildError, "display_names.en"):
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
