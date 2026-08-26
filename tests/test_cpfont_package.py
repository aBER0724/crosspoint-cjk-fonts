#!/usr/bin/env python3

import hashlib
import json
import tempfile
import unittest
import zipfile
from pathlib import Path

import yaml

from scripts.package_cpfont_families import package_families


class CpfontPackageTest(unittest.TestCase):
    def test_packages_reader_family_with_ui_and_reader_sizes(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            files = []
            for size in (8, 10, 12, 14):
                name = f"Example_{size}.cpfont"
                data = bytes([size])
                (root / name).write_bytes(data)
                files.append({
                    "name": name,
                    "physicalSize": size,
                    "byteSize": len(data),
                    "sha256": hashlib.sha256(data).hexdigest(),
                })
            (root / "fonts.json").write_text(json.dumps({
                "version": 2,
                "families": [{"name": "Example", "styles": ["regular"], "files": files}],
            }), encoding="utf-8")
            config = root / "fonts.yaml"
            config.write_text(yaml.safe_dump({"families": [{"name": "Example", "role": "reader"}]}), encoding="utf-8")

            outputs = package_families(root, config)
            self.assertEqual([output.name for output in outputs], ["Example-ui.cpfontpkg", "Example.cpfontpkg"])
            with zipfile.ZipFile(root / "Example-ui.cpfontpkg") as archive:
                manifest = json.loads(archive.read("Example/manifest.json"))
                self.assertEqual(manifest["role"], "ui")
                self.assertEqual(manifest["readerSizes"], [])
                self.assertEqual(len([name for name in archive.namelist() if name.endswith(".cpfont")]), 3)
            with zipfile.ZipFile(root / "Example.cpfontpkg") as archive:
                manifest = json.loads(archive.read("Example/manifest.json"))
                self.assertEqual(manifest["role"], "family")
                self.assertEqual(manifest["uiSizes"], [8, 10, 12])
                self.assertEqual(manifest["readerSizes"], [14])
                self.assertEqual(len([name for name in archive.namelist() if name.endswith(".cpfont")]), 4)


if __name__ == "__main__":
    unittest.main()
