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

    def test_reusable_build_runs_for_a_push_caller(self):
        text = BUILD_WORKFLOW.read_text(encoding="utf-8")
        build_block = text.split("  build:\n", 1)[1].split("\n  catalog:\n", 1)[0]
        self.assertIn("inputs.families_json != ''", build_block)
        self.assertNotIn("github.event_name == 'workflow_call'", build_block)
        self.assertIn("publish_catalog: false", RELEASE_WORKFLOW.read_text(encoding="utf-8"))

    def test_release_downloads_per_family_artifacts_from_reusable_workflow(self):
        text = RELEASE_WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("pattern: font-*", text)
        self.assertIn("merge-multiple: true", text)
        self.assertIn("python scripts/generate_manifest.py", text)
        self.assertIn("--output built/fonts.json", text)
        self.assertNotIn("name: crosspoint-cjk-fonts\n          path: built", text)

    def test_release_notes_are_generated_from_the_candidate_manifests(self):
        text = RELEASE_WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("scripts/generate_release_notes.py", text)
        self.assertIn("--previous-manifest state/previous/fonts.json", text)
        self.assertIn("--current-manifest dist/fonts.json", text)
        self.assertIn("--output dist/RELEASE_NOTES.md", text)
        self.assertIn("--notes-file dist/RELEASE_NOTES.md", text)
        template = (ROOT / ".github" / "RELEASE_TEMPLATE.md").read_text(encoding="utf-8")
        self.assertIn("### Added", template)
        self.assertIn("### Updated", template)
        self.assertIn("### Removed", template)

    def test_metadata_publish_runs_after_a_skipped_font_build(self):
        text = RELEASE_WORKFLOW.read_text(encoding="utf-8")
        publish_block = text.split("  publish-metadata:
", 1)[1]
        self.assertIn("if: always()", publish_block)
        self.assertIn("needs.verify-fonts.result == 'success'", publish_block)
        self.assertIn("needs.verify-fonts.result == 'skipped'", publish_block)

    def test_release_updates_changed_assets_and_metadata_only(self):
        text = RELEASE_WORKFLOW.read_text(encoding="utf-8")
        self.assertIn('gh release upload "$RELEASE_TAG"', text)
        self.assertIn("--clobber", text)
        self.assertIn("dist/fonts.json", text)
        self.assertIn("dist/build-index.json", text)
        self.assertIn("dist/FONT-SOURCES.md", text)
        self.assertIn("release_update_needed", text)
        self.assertIn("Remove obsolete Release metadata assets", text)
        self.assertIn("FONT-LICENSES.md OFL-1.1.txt", text)
        self.assertIn("verify-assets", text)


if __name__ == "__main__":
    unittest.main()
