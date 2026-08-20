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

    def test_build_workflow_declares_custom_sizes_input(self):
        import yaml

        document = yaml.safe_load(BUILD_WORKFLOW.read_text(encoding="utf-8"))
        # YAML 1.1 parses the bare workflow key `on` as boolean True.
        triggers = document[True]
        dispatch_sizes = triggers["workflow_dispatch"]["inputs"]["sizes"]
        call_sizes = triggers["workflow_call"]["inputs"]["sizes"]
        self.assertEqual(dispatch_sizes["default"], "")
        self.assertEqual(call_sizes["default"], "")
        self.assertEqual(call_sizes["type"], "string")

    def test_build_step_passes_custom_sizes_only_when_provided(self):
        text = BUILD_WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("BUILD_SIZES: ${{ inputs.sizes }}", text)
        self.assertIn('args+=(--sizes "$BUILD_SIZES")', text)
        self.assertIn("Validate custom sizes", text)
        self.assertIn("inputs.sizes != ''", text)

    def test_metadata_publish_runs_after_a_skipped_font_build(self):
        text = RELEASE_WORKFLOW.read_text(encoding="utf-8")
        publish_block = text.split("  publish-metadata:\n", 1)[1]
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

    def test_build_workflow_declares_manual_mode_input(self):
        import yaml

        document = yaml.safe_load(BUILD_WORKFLOW.read_text(encoding="utf-8"))
        triggers = document[True]
        dispatch_mode = triggers["workflow_dispatch"]["inputs"]["mode"]
        call_mode = triggers["workflow_call"]["inputs"]["mode"]
        self.assertEqual(dispatch_mode["type"], "choice")
        self.assertEqual(dispatch_mode["default"], "manual")
        self.assertEqual(dispatch_mode["options"], ["manual", "self", "contribute"])
        self.assertEqual(call_mode["default"], "manual")

    def test_self_mode_publishes_to_current_repo_release(self):
        text = BUILD_WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("publish-self:", text)
        self.assertIn("inputs.mode == 'self'", text)
        self.assertIn("gh release create", text)
        self.assertIn("gh release upload", text)
        self.assertIn("--clobber", text)
        self.assertIn("RELEASE_TAG: sd-fonts-m2-b4", text)
        self.assertIn("github.repository", text)

    def test_self_publish_job_requires_the_catalog_artifact(self):
        text = BUILD_WORKFLOW.read_text(encoding="utf-8")
        block = text.split("  publish-self:\n", 1)[1]
        self.assertIn("needs: catalog", block)
        self.assertIn("name: crosspoint-cjk-fonts", block)
        self.assertIn("path: dist", block)

    def test_catalog_job_is_not_gated_on_a_call_only_input(self):
        # publish_catalog only exists as a workflow_call input. Under
        # workflow_dispatch its empty value must not disable the catalog job,
        # otherwise publish-self (which needs: catalog) is skipped too.
        text = BUILD_WORKFLOW.read_text(encoding="utf-8")
        catalog_block = text.split("\n  catalog:\n", 1)[1].split("\n    needs:", 1)[0]
        self.assertNotIn("inputs.publish_catalog != false", catalog_block)
        self.assertIn("inputs.publish_catalog == true", catalog_block)

    def test_contribute_mode_pushes_a_submit_branch(self):
        text = BUILD_WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("push-submit:", text)
        self.assertIn("inputs.mode == 'contribute'", text)
        self.assertIn("needs: [validate, build]", text)
        self.assertIn("community-fonts/ config/", text)
        self.assertIn("submit/${family:-font-submission}", text)
        self.assertIn("git push -u origin \"$branch\" --force", text)
        self.assertIn("compare", text)

    def test_push_submit_survives_when_changes_are_already_in_head(self):
        # The dispatch ref may already carry the font changes in its history
        # (e.g. running from a feature branch). After `git checkout -b` there
        # is then nothing new to stage, so the script must not fail on an
        # empty `git commit` under `set -e`.
        text = BUILD_WORKFLOW.read_text(encoding="utf-8")
        push_block = text.split("  push-submit:\n", 1)[1]
        self.assertIn("if ! git diff --cached --quiet; then", push_block)
        self.assertIn('git commit -m "chore(fonts): submit ${family:-font} for upstream review"', push_block)

    def test_base_url_and_permissions_allow_self_managed_releases(self):
        import yaml

        document = yaml.safe_load(BUILD_WORKFLOW.read_text(encoding="utf-8"))
        self.assertEqual(document["permissions"]["contents"], "write")
        self.assertIn("${{ github.repository }}", document["env"]["FONT_BASE_URL"])

    def test_manual_mode_keeps_the_default_build_only_behavior(self):
        text = BUILD_WORKFLOW.read_text(encoding="utf-8")
        # Default stays manual: no publish/PR jobs run unless mode is explicit.
        self.assertIn("default: manual", text)
        self.assertNotIn("publish-self", text.split("on:\n", 1)[0])


if __name__ == "__main__":
    unittest.main()
