#!/usr/bin/env python3

import importlib.util
import unittest
from pathlib import Path
from unittest import mock

import yaml

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "fonts.yaml"
BUILD_SCRIPT = ROOT / "scripts" / "build_fonts.py"


def load_build_module():
    spec = importlib.util.spec_from_file_location("build_fonts", BUILD_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load {BUILD_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class CatalogSizeContractTest(unittest.TestCase):
    def setUp(self):
        self.document = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))

    def test_catalog_declares_ui_reader_and_preview_sizes_once(self):
        self.assertEqual(self.document["ui_sizes"], [8, 10, 12])
        self.assertEqual(self.document["reader_sizes"], [14, 16, 18, 22])
        self.assertEqual(self.document["preview_sizes"], [14, 18, 22])
        self.assertTrue(set(self.document["preview_sizes"]).issubset(self.document["reader_sizes"]))
        for family in self.document["families"]:
            self.assertNotIn("sizes", family)

    def test_catalog_records_only_optional_source_metadata(self):
        for family in self.document["families"]:
            self.assertTrue({"license_type", "license_url"}.isdisjoint(family), family["name"])
            if "source_url" in family:
                self.assertTrue(family["source_url"].startswith("https://"), family["name"])

    def test_build_uses_ordered_union_of_ui_and_reader_sizes(self):
        module = load_build_module()
        sizes = module.catalog_sizes(self.document)
        self.assertEqual(sizes, [8, 10, 12, 14, 16, 18, 22])

        family = self.document["families"][0]
        with mock.patch.object(module, "resolve_source", return_value=ROOT / "source.ttf"), mock.patch.object(
            module.subprocess, "run"
        ) as run:
            module.build_family(family, ROOT / "dist-test", sizes)

        command = run.call_args.args[0]
        self.assertEqual(command[command.index("--sizes") + 1], "8,10,12,14,16,18,22")


if __name__ == "__main__":
    unittest.main()
