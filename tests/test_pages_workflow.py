#!/usr/bin/env python3

import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
BUILD_WORKFLOW = ROOT / ".github" / "workflows" / "build-fonts.yml"
PAGES_WORKFLOW = ROOT / ".github" / "workflows" / "deploy-pages.yml"
CONFIG = ROOT / "config" / "fonts.yaml"
PAGE_HTML = ROOT / "pages" / "index.html"
PAGE_CSS = ROOT / "pages" / "assets" / "app.css"


class PagesWorkflowTest(unittest.TestCase):
    def test_pages_workflow_uses_trusted_release_data_and_minimal_permissions(self):
        text = PAGES_WORKFLOW.read_text(encoding="utf-8")

        self.assertIn("workflow_dispatch:", text)
        self.assertIn("workflow_run:", text)
        self.assertIn('workflows: ["Publish font release"]', text)
        self.assertIn("contents: read", text)
        self.assertIn("pages: write", text)
        self.assertIn("id-token: write", text)
        self.assertIn("actions/configure-pages@v5", text)
        self.assertIn("actions/upload-pages-artifact@v3", text)
        self.assertIn("actions/deploy-pages@v4", text)
        self.assertIn("scripts/fetch_release_previews.py", text)
        self.assertIn("--sizes 14,18,22", text)
        self.assertIn("scripts/build_pages.py", text)
        self.assertNotIn("pull_request_target", text)
        self.assertNotIn("dist/*.cpfont", text)

    def test_pull_requests_validate_pages_without_main_page_push_triggering_font_build(self):
        text = BUILD_WORKFLOW.read_text(encoding="utf-8")
        pull_request_block, push_block = text.split("  push:", 1)

        self.assertIn("pages/**", pull_request_block)
        self.assertIn("tests/**", pull_request_block)
        self.assertNotIn("pages/**", push_block.split("  workflow_dispatch:", 1)[0])
        self.assertIn("github.event_name != 'push'", text)
        self.assertIn("python -m unittest discover -s tests -v", text)

    def test_pages_source_keeps_runtime_hooks_and_font_maker_visual_tokens(self):
        html = PAGE_HTML.read_text(encoding="utf-8")
        css = PAGE_CSS.read_text(encoding="utf-8")

        for hook in (
            'id="catalog"',
            'id="status"',
            'id="search"',
            'id="language-filter"',
            'id="category-filter"',
            'id="preview-size"',
            'id="font-card-template"',
            'id="manifest-link"',
            'id="maker-link"',
        ):
            self.assertIn(hook, html)
        for selector in ('class="description"', 'class="license-status"', 'class="preview"', 'class="tags"', 'class="license"', 'class="downloads"', 'class="source-link"', 'class="license-link"'):
            self.assertIn(selector, html)

        self.assertIn('--font-sans: "DM Sans", ui-sans-serif, sans-serif, system-ui;', css)
        self.assertIn("--radius: 1rem;", css)
        self.assertIn("--background: #ffffff;", css)
        self.assertIn("--primary: #171717;", css)
        self.assertIn("grid-template-columns: repeat(3, minmax(0, 1fr));", css)
        self.assertIn('.locale-switcher button[aria-pressed="true"]', css)
        self.assertNotIn("font-family: Georgia", css)
        self.assertNotIn("#f4f1e8", css)

    def test_every_family_declares_filter_metadata(self):
        document = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))

        for family in document["families"]:
            self.assertIsInstance(family.get("languages"), list, family["name"])
            self.assertTrue(family["languages"], family["name"])
            self.assertIsInstance(family.get("category"), str, family["name"])
            self.assertTrue(family["category"], family["name"])


if __name__ == "__main__":
    unittest.main()
