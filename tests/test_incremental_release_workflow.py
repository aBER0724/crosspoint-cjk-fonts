#!/usr/bin/env python3

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUILD_WORKFLOW = ROOT / ".github" / "workflows" / "build-fonts.yml"
RELEASE_WORKFLOW = ROOT / ".github" / "workflows" / "release-fonts.yml"


class IncrementalReleaseWorkflowTest(unittest.TestCase):
    def test_main_push_dispatches_incremental_release(self):
        text = RELEASE_WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("push:", text)
        self.assertIn("branches: [main]", text)
        self.assertIn("scripts/incremental_release.py", text)
        self.assertIn("plan", text)
        self.assertNotIn('gh release delete "$RELEASE_TAG"', text)

    def test_build_matrix_comes_from_incremental_plan(self):
        text = BUILD_WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("families_json", text)
        self.assertIn("fromJson(needs.validate.outputs.families)", text)
        self.assertNotIn("hashFiles('config/fonts.yaml'", text)
        self.assertIn("source-${{ matrix.family }}-${{ steps.source.outputs.sha256 }}", text)

    def test_release_updates_changed_assets_and_metadata_only(self):
        text = RELEASE_WORKFLOW.read_text(encoding="utf-8")
        self.assertIn('gh release upload "$RELEASE_TAG"', text)
        self.assertIn("--clobber", text)
        self.assertIn("dist/fonts.json", text)
        self.assertIn("dist/build-index.json", text)
        self.assertIn("verify-assets", text)


if __name__ == "__main__":
    unittest.main()
