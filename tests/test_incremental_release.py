#!/usr/bin/env python3

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "incremental_release.py"
CONFIG = ROOT / "config" / "fonts.yaml"


def load_module():
    spec = importlib.util.spec_from_file_location("incremental_release", SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load {SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class IncrementalReleaseTest(unittest.TestCase):
    def setUp(self):
        self.module = load_module()
        self.document = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
        self.family = self.document["families"][0]

    def test_fingerprint_ignores_catalog_only_metadata(self):
        first = self.module.family_fingerprint(self.document, self.family)
        changed = dict(self.family)
        changed["description"] = "Changed catalog description"
        changed["display_names"] = {"en": "Changed", "zh": "Changed", "ja": "Changed"}
        changed["languages"] = ["ja"]
        changed["category"] = "display"
        changed.pop("source_url", None)
        self.assertEqual(first, self.module.family_fingerprint(self.document, changed))

    def test_fingerprint_tracks_inputs_that_change_cpfont_bytes(self):
        first = self.module.family_fingerprint(self.document, self.family)

        source_changed = json.loads(json.dumps(self.family))
        source_changed["source"]["sha256"] = "0" * 64
        self.assertNotEqual(first, self.module.family_fingerprint(self.document, source_changed))

        interval_changed = json.loads(json.dumps(self.family))
        interval_changed["intervals"] = "latin-ext"
        self.assertNotEqual(first, self.module.family_fingerprint(self.document, interval_changed))

        sizes_changed = json.loads(json.dumps(self.document))
        sizes_changed["reader_sizes"] = [14, 16, 18, 20, 22]
        self.assertNotEqual(first, self.module.family_fingerprint(sizes_changed, self.family))

    def test_uploaded_source_cache_key_tracks_content_and_build_options(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as directory:
            path = Path(directory) / "font.zip"
            path.write_bytes(b"font archive")
            relative = path.relative_to(ROOT).as_posix()
            family = {"source": {"path": relative, "archive_member": "a.ttf"}}
            first = self.module.source_cache_key(family)

            changed_member = {"source": {"path": relative, "archive_member": "b.ttf"}}
            changed_axis = {
                "source": {"path": relative, "archive_member": "a.ttf", "variable": {"wght": 400}}
            }
            self.assertNotEqual(first, self.module.source_cache_key(changed_member))
            self.assertNotEqual(first, self.module.source_cache_key(changed_axis))

            path.write_bytes(b"changed archive")
            self.assertNotEqual(first, self.module.source_cache_key(family))

    def test_plan_reuses_matching_family_and_builds_new_family(self):
        previous_manifest = {
            "version": 2,
            "baseUrl": "https://example.invalid/fonts/",
            "families": [],
        }
        for family in self.document["families"]:
            previous_manifest["families"].append(
                {
                    "name": family["name"],
                    "files": [
                        {"name": filename, "size": 1, "sha256": "a" * 64}
                        for filename in self.module.expected_family_filenames(self.document, family["name"])
                    ],
                }
            )
        previous = self.module.build_index_document(self.document, previous_manifest)
        current = json.loads(json.dumps(self.document))
        new_family = json.loads(json.dumps(self.family))
        new_family["name"] = "NewFamily"
        new_family["source"]["filename"] = "new.ttf"
        current["families"].append(new_family)

        plan = self.module.plan_release(current, previous, previous_manifest)
        self.assertEqual(plan["build"], ["NewFamily"])
        self.assertIn(self.family["name"], plan["reuse"])
        self.assertEqual(plan["remove"], [])

    def test_plan_publishes_metadata_changes_without_rebuilding_fonts(self):
        previous_manifest = {
            "version": 2,
            "baseUrl": "https://example.invalid/fonts/",
            "families": [],
        }
        for family in self.document["families"]:
            previous_manifest["families"].append(
                {
                    "name": family["name"],
                    "description": family["description"],
                    "sourceUrl": family.get("source_url"),
                    "license": "commercial-use",
                    "licenseType": "commercial-use",
                    "licenseStatus": "declared",
                    "licenseUrl": "https://example.invalid/terms",
                    "files": [
                        {"name": filename, "size": 1, "sha256": "a" * 64}
                        for filename in self.module.expected_family_filenames(self.document, family["name"])
                    ],
                }
            )
        previous = self.module.build_index_document(self.document, previous_manifest)

        plan = self.module.plan_release(self.document, previous, previous_manifest)

        self.assertEqual(plan["build"], [])
        self.assertEqual(plan["reuse"], [family["name"] for family in self.document["families"]])
        self.assertEqual(plan["metadataChanged"], plan["reuse"])
        self.assertTrue(plan["needsReleaseUpdate"])

    def test_write_manifest_combines_reused_and_built_families(self):
        previous_manifest = {
            "version": 2,
            "baseUrl": "https://example.invalid/fonts/",
            "families": [
                {
                    "name": self.family["name"],
                    "description": "Old description",
                    "styles": ["regular"],
                    "files": [
                        {"name": filename, "size": 3, "sha256": "a" * 64}
                        for filename in self.module.expected_family_filenames(
                            self.document, self.family["name"]
                        )
                    ],
                    "sourceUrl": "https://example.invalid/source",
                }
            ],
        }
        current = json.loads(json.dumps(self.document))
        current["families"] = [json.loads(json.dumps(self.family))]
        new_family = json.loads(json.dumps(self.family))
        new_family["name"] = "NewFamily"
        current["families"].append(new_family)
        built_manifest = {
            "version": 2,
            "baseUrl": previous_manifest["baseUrl"],
            "families": [
                {
                    "name": "NewFamily",
                    "description": "Built",
                    "styles": ["regular"],
                    "files": [
                        {"name": filename, "size": 4, "sha256": "b" * 64}
                        for filename in self.module.expected_family_filenames(current, "NewFamily")
                    ],
                    "sourceUrl": "https://example.invalid/source",
                }
            ],
        }

        manifest = self.module.merge_manifest(current, previous_manifest, built_manifest)
        self.assertEqual([entry["name"] for entry in manifest["families"]], [self.family["name"], "NewFamily"])
        self.assertEqual(manifest["families"][0]["description"], self.family["description"])
        self.assertEqual(manifest["families"][0]["sourceUrl"], self.family["source_url"])
        self.assertEqual(manifest["families"][1]["files"], built_manifest["families"][0]["files"])
        for entry in manifest["families"]:
            self.assertTrue({"license", "licenseType", "licenseStatus", "licenseUrl"}.isdisjoint(entry))

    def test_verify_remote_metadata_checks_every_manifest_file_without_downloading(self):
        manifest = {
            "version": 2,
            "baseUrl": "https://example.invalid/fonts/",
            "families": [
                {
                    "name": "Family",
                    "files": [
                        {"name": "Family_8.cpfont", "size": 7, "sha256": "c" * 64},
                        {"name": "Family_10.cpfont", "size": 9, "sha256": "d" * 64},
                    ],
                }
            ],
        }
        assets = {
            "Family_8.cpfont": {"name": "Family_8.cpfont", "size": 7},
            "Family_10.cpfont": {"name": "Family_10.cpfont", "size": 9},
        }
        self.module.verify_asset_metadata(manifest, assets)
        assets["Family_10.cpfont"]["size"] = 10
        with self.assertRaisesRegex(RuntimeError, "Family_10.cpfont"):
            self.module.verify_asset_metadata(manifest, assets)

    def test_atomic_metadata_write_uses_temporary_files(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            target = output / "fonts.json"
            self.module.write_json_atomic(target, {"version": 2})
            self.assertEqual(json.loads(target.read_text(encoding="utf-8")), {"version": 2})
            self.assertFalse(list(output.glob("*.tmp")))


if __name__ == "__main__":
    unittest.main()
