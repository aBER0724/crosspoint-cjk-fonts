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
PAGE_JS = ROOT / "pages" / "assets" / "app.js"


class PagesWorkflowTest(unittest.TestCase):
    def test_pages_workflow_uses_trusted_release_data_and_minimal_permissions(self):
        text = PAGES_WORKFLOW.read_text(encoding="utf-8")

        self.assertIn("workflow_dispatch:", text)
        self.assertIn("workflow_run:", text)
        self.assertIn("release:", text)
        self.assertIn("types: [published]", text)
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
        self.assertIn("github.event_name == 'workflow_dispatch'", text)
        self.assertIn("github.event_name == 'workflow_call'", text)
        self.assertNotIn("github.event_name == 'push' ||", text)
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
        for selector in ('class="description"', 'class="family-id"', 'class="license-status"', 'class="preview"', 'class="tags"', 'class="license"', 'class="downloads"', 'class="source-link"', 'class="license-link"'):
            self.assertIn(selector, html)

        self.assertIn('--font-sans: "DM Sans", ui-sans-serif, sans-serif, system-ui;', css)
        self.assertIn("--radius: 1rem;", css)
        self.assertIn("--background: #ffffff;", css)
        self.assertIn("--primary: #171717;", css)
        self.assertIn("grid-template-columns: repeat(3, minmax(0, 1fr));", css)
        self.assertIn('.locale-switcher button[aria-pressed="true"]', css)
        self.assertNotIn("font-family: Georgia", css)
        self.assertNotIn("#f4f1e8", css)
        self.assertIn('<div id="preview-size" class="preview-size-switch" role="group"', html)
        self.assertNotIn('<select id="preview-size"', html)

    def test_preview_size_defaults_to_18_pt(self):
        script = PAGE_JS.read_text(encoding="utf-8")

        self.assertIn('const DEFAULT_PREVIEW_SIZE = "18";', script)
        self.assertIn('previewSize: DEFAULT_PREVIEW_SIZE', script)
        self.assertIn('state.catalog.previewSizes.map(String).includes(DEFAULT_PREVIEW_SIZE)', script)
        self.assertNotIn('previewSize: "14"', script)

    def test_font_cards_localize_display_names_and_keep_stable_ids_searchable(self):
        script = PAGE_JS.read_text(encoding="utf-8")

        self.assertIn("function familyDisplayName(family)", script)
        self.assertIn("family.displayNames[state.locale]", script)
        self.assertIn('fragment.querySelector(".family-id").textContent = family.name;', script)
        self.assertIn("Object.values(family.displayNames)", script)
        self.assertIn("const displayName = familyDisplayName(family);", script)
        self.assertIn("preview.alt = `${displayName}, ${state.previewSize} pt`;", script)

    def test_filter_options_localize_labels_without_changing_catalog_values(self):
        script = PAGE_JS.read_text(encoding="utf-8")

        self.assertIn('languages: { "zh-Hans": "Simplified Chinese", "zh-Hant": "Traditional Chinese", ja: "Japanese" }', script)
        self.assertIn('categories: { "sans-serif": "Sans serif", serif: "Serif", handwriting: "Handwriting", "rounded-sans": "Rounded sans", display: "Display", fangsong: "Fangsong" }', script)
        self.assertIn('languages: { "zh-Hans": "简体中文", "zh-Hant": "繁体中文", ja: "日语" }', script)
        self.assertIn('categories: { "sans-serif": "无衬线体", serif: "衬线体", handwriting: "手写体", "rounded-sans": "圆体", display: "展示体", fangsong: "仿宋体" }', script)
        self.assertIn('languages: { "zh-Hans": "簡体字中国語", "zh-Hant": "繁体字中国語", ja: "日本語" }', script)
        self.assertIn('categories: { "sans-serif": "ゴシック体", serif: "明朝体", handwriting: "手書き体", "rounded-sans": "丸ゴシック体", display: "ディスプレイ体", fangsong: "仿宋体" }', script)
        self.assertIn('function filterOptionLabel(kind, value)', script)
        self.assertIn('new Option(filterOptionLabel(kind, value), value)', script)
        self.assertIn('const selected = node.value;', script)
        self.assertIn('node.value = values.includes(selected) ? selected : "";', script)
        self.assertNotIn('values.map(value => new Option(value, value))', script)

    def test_maker_link_uses_requested_chinese_copy_and_deployed_instance(self):
        html = PAGE_HTML.read_text(encoding="utf-8")
        script = PAGE_JS.read_text(encoding="utf-8")

        self.assertIn('maker: "制作自制字体"', script)
        self.assertNotIn("制作私人字体", script)
        self.assertIn(
            '<a id="maker-link" class="maker-link" href="https://crosspoint-cjk-font-maker.onrender.com/"',
            html,
        )
        self.assertLess(html.index('id="maker-link"'), html.index('class="toolbar"'))
        self.assertEqual(html.count('id="maker-link"'), 1)
        self.assertNotIn("nodes.maker.href = state.catalog.fontMakerUrl;", script)

    def test_locale_and_theme_controls_share_one_row_at_every_width(self):
        css = PAGE_CSS.read_text(encoding="utf-8")
        base_controls = css[css.index(".masthead__controls {") : css.index(".locale-switcher,", css.index(".masthead__controls {"))]
        mobile_css = css[css.index("@media (max-width: 640px)") :]

        self.assertIn("display: flex;", base_controls)
        self.assertIn("align-items: center;", base_controls)
        self.assertIn("justify-content: flex-end;", base_controls)
        self.assertIn("overflow-x: auto;", base_controls)
        self.assertNotIn("display: grid;", base_controls)
        mobile_controls = mobile_css[mobile_css.index(".masthead__controls {") : mobile_css.index(".locale-switcher,")]
        self.assertNotIn("grid-template-columns:", mobile_controls)
        self.assertNotIn("justify-self: end;", mobile_controls)

    def test_theme_switcher_matches_maker_dark_mode_and_uses_transparent_device_previews(self):
        html = PAGE_HTML.read_text(encoding="utf-8")
        css = PAGE_CSS.read_text(encoding="utf-8")
        script = PAGE_JS.read_text(encoding="utf-8")

        self.assertIn('<div id="theme-switcher" class="theme-switcher" role="group"', html)
        self.assertIn('themeLight: "浅色"', script)
        self.assertIn('themeDark: "深色"', script)
        self.assertIn('themeSystem: "跟随系统"', script)
        self.assertIn('window.matchMedia("(prefers-color-scheme: dark)")', script)
        self.assertIn('document.documentElement.dataset.theme = theme;', script)
        self.assertIn('localStorage.setItem(THEME_STORAGE_KEY, mode);', script)
        self.assertIn('updatePreviewAppearance(preview, theme === "dark");', script)
        self.assertNotIn('preview.style.filter = dark ? "invert(93.3%)" : "";', script)
        self.assertIn(':root[data-theme="dark"]', css)
        self.assertIn('--preview-dark-paper: #111111;', css)
        self.assertIn('<div class="preview-frame"><img class="preview"', html)
        self.assertIn('preview.classList.toggle("preview--light", !dark);', script)
        self.assertIn('preview.closest(".preview-frame")?.classList.toggle("preview-frame--dark", dark);', script)
        self.assertIn('.preview-frame {', css)
        self.assertIn('background: var(--preview-paper);', css)
        self.assertIn('.preview-frame.preview-frame--dark', css)
        self.assertIn('background: var(--preview-dark-paper);', css)
        self.assertIn('.preview.preview--light', css)
        self.assertIn('filter: invert(1);', css)
        self.assertNotIn('.preview:not(.preview--dark)', css)
        self.assertNotIn('.preview.preview--dark', css)
        self.assertNotIn('preview.style.filter = dark ? "invert(93.3%)" : "";', script)

    def test_font_cards_show_direct_download_buttons_without_an_expander(self):
        html = PAGE_HTML.read_text(encoding="utf-8")
        css = PAGE_CSS.read_text(encoding="utf-8")
        script = PAGE_JS.read_text(encoding="utf-8")

        self.assertIn('<div class="downloads" role="group" aria-label="Download physical sizes"></div>', html)
        self.assertNotIn("<details>", html)
        self.assertNotIn("<summary", html)
        self.assertNotIn('fragment.querySelector("summary")', script)
        self.assertIn('downloads.setAttribute("aria-label", `${family.name}: ${copy.downloads}`);', script)
        self.assertIn('link.textContent = `${file.physicalSize} pt`;', script)
        self.assertIn('link.setAttribute("aria-label", `${file.physicalSize} pt, ${humanBytes(file.byteSize)}`);', script)
        self.assertNotIn("white-space: pre-line;", css)
        self.assertIn("grid-template-columns: repeat(4, minmax(0, 1fr));", css)
        self.assertIn("min-height: 30px;", css)
        mobile_css = css[css.index("@media (max-width: 640px)") :]
        self.assertNotIn(".downloads {", mobile_css)

    def test_every_family_declares_filter_metadata(self):
        document = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))

        for family in document["families"]:
            self.assertIsInstance(family.get("display_names"), dict, family["name"])
            self.assertEqual(set(family["display_names"]), {"en", "zh", "ja"}, family["name"])
            self.assertTrue(all(isinstance(value, str) and value.strip() for value in family["display_names"].values()), family["name"])
            self.assertIsInstance(family.get("languages"), list, family["name"])
            self.assertTrue(family["languages"], family["name"])
            self.assertIsInstance(family.get("category"), str, family["name"])
            self.assertTrue(family["category"], family["name"])


if __name__ == "__main__":
    unittest.main()
