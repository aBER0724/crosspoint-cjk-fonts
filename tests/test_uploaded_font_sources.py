#!/usr/bin/env python3

import importlib.util
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import yaml

ROOT = Path(__file__).resolve().parents[1]
VALIDATE_SCRIPT = ROOT / "scripts" / "validate_config.py"
BUILD_SCRIPT = ROOT / "scripts" / "build_fonts.py"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class UploadedFontSourceTest(unittest.TestCase):
    def setUp(self):
        self.validate = load_module("validate_config", VALIDATE_SCRIPT)
        self.build = load_module("build_fonts_uploaded", BUILD_SCRIPT)
        self.base_family = {
            "name": "UploadedCJK",
            "display_names": {"en": "Uploaded CJK", "zh": "上传字体", "ja": "投稿フォント"},
            "description": "Uploaded CJK test font",
            "category": "sans-serif",
            "languages": ["zh-Hans"],
            "license_type": "personal-use",
            "intervals": "latin-ext,cjk",
            "source": {"path": "community-fonts/UploadedCJK/UploadedCJK-Regular.ttf"},
        }

    def document(self, family: dict) -> dict:
        return {
            "ui_sizes": [8, 10, 12],
            "reader_sizes": [14, 16, 18, 22],
            "preview_sizes": [14, 18, 22],
            "families": [family],
        }

    def test_uploaded_source_accepts_optional_license_types(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            font_path = root / "community-fonts" / "UploadedCJK" / "UploadedCJK-Regular.ttf"
            font_path.parent.mkdir(parents=True)
            font_path.write_bytes(b"font")

            for license_type in ("commercial-use", "personal-use", None):
                family = dict(self.base_family)
                if license_type is None:
                    family.pop("license_type", None)
                else:
                    family["license_type"] = license_type
                self.assertEqual(self.validate.validate_document(self.document(family), root=root), [])

    def test_uploaded_source_rejects_paths_outside_community_fonts(self):
        family = dict(self.base_family)
        family["source"] = {"path": "../private-font.ttf"}
        errors = self.validate.validate_document(self.document(family), root=ROOT)
        self.assertTrue(any("community-fonts" in error for error in errors), errors)

    def test_uploaded_source_rejects_repository_oversize_file(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            font_path = root / "community-fonts" / "UploadedCJK" / "UploadedCJK-Regular.ttf"
            font_path.parent.mkdir(parents=True)
            font_path.write_bytes(b"font")
            original_stat = font_path.stat()
            oversized_stat = type(
                "Stat",
                (),
                {"st_mode": original_stat.st_mode, "st_size": 101 * 1024 * 1024},
            )()
            original_path_stat = self.validate.Path.stat

            def fake_stat(path, *args, **kwargs):
                return oversized_stat if path == font_path else original_path_stat(path, *args, **kwargs)

            with mock.patch.object(self.validate.Path, "stat", fake_stat):
                errors = self.validate.validate_document(self.document(self.base_family), root=root)
            self.assertTrue(any("100 MiB" in error for error in errors), errors)

    def test_build_resolves_uploaded_font_and_zip_member(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as directory:
            direct = Path(directory) / "UploadedCJK-Regular.ttf"
            direct.write_bytes(b"font")
            relative = direct.relative_to(ROOT).as_posix()
            self.assertEqual(self.build.resolve_source_path({"path": relative}, "UploadedCJK"), direct)


if __name__ == "__main__":
    unittest.main()
