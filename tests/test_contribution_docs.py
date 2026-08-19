#!/usr/bin/env python3

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
README_ZH = ROOT / "README.zh-CN.md"
README_JA = ROOT / "README.ja.md"
CONTRIBUTING = ROOT / "CONTRIBUTING.md"
CONTRIBUTING_ZH = ROOT / "CONTRIBUTING.zh-CN.md"
CONTRIBUTING_JA = ROOT / "CONTRIBUTING.ja.md"
FONT_TEMPLATE = ROOT / ".github" / "PULL_REQUEST_TEMPLATE.md"
FONT_CHOOSER_TEMPLATE = ROOT / ".github" / "PULL_REQUEST_TEMPLATE" / "font-submission.md"
GENERAL_TEMPLATE = ROOT / ".github" / "PULL_REQUEST_TEMPLATE" / "general-change.md"


class ContributionDocsTest(unittest.TestCase):
    def test_readme_has_a_prominent_font_submission_entry_point(self):
        readmes = [
            (README.read_text(encoding="utf-8"), "## Catalog"),
            (README_ZH.read_text(encoding="utf-8"), "## 字体目录"),
            (README_JA.read_text(encoding="utf-8"), "## カタログ"),
        ]
        text = readmes[0][0]
        submission_position = text.index("## Submit a font")

        self.assertLess(submission_position, text.index("## Catalog"))
        self.assertIn("[read the font contribution guide](CONTRIBUTING.md)", text)
        self.assertIn("Font submission", text)
        self.assertIn("Put one TTF, OTF, or ZIP file", text)
        for localized, catalog_heading in readmes:
            self.assertNotIn("## Reproducibility", localized)
            self.assertNotIn("## 可复现性", localized)
            self.assertNotIn("## 再現性", localized)
            self.assertNotIn("The generated binaries are deliberately excluded from Git history", localized)
            self.assertNotIn("生成的二进制文件不会提交到 Git 历史", localized)
            self.assertNotIn("生成済みバイナリは Git 履歴へコミットしません", localized)
            self.assertIn(catalog_heading, localized)

    def test_readmes_link_the_three_language_versions(self):
        english = README.read_text(encoding="utf-8")
        chinese = README_ZH.read_text(encoding="utf-8")
        japanese = README_JA.read_text(encoding="utf-8")

        for text in (english, chinese, japanese):
            self.assertIn("README.md", text)
            self.assertIn("README.zh-CN.md", text)
            self.assertIn("README.ja.md", text)

        self.assertIn("## Submit a font", english)
        self.assertIn("## 提交字体", chinese)
        self.assertIn("## フォントを投稿する", japanese)
        self.assertIn("CONTRIBUTING.md", english)
        self.assertIn("CONTRIBUTING.zh-CN.md", chinese)
        self.assertIn("CONTRIBUTING.ja.md", japanese)

    def test_contribution_guides_cover_the_same_submission_contract(self):
        guides = {
            "en": CONTRIBUTING.read_text(encoding="utf-8"),
            "zh": CONTRIBUTING_ZH.read_text(encoding="utf-8"),
            "ja": CONTRIBUTING_JA.read_text(encoding="utf-8"),
        }
        expected_tables = {
            "en": "| Field | Required | Description |",
            "zh": "| 字段 | 是否必填 | 简要说明 |",
            "ja": "| Field | Required | Description |",
        }
        for locale, text in guides.items():
            self.assertIn(expected_tables[locale], text)
            for expected in (
                "source_url",
                "config/fonts.yaml",
                "archive_member",
                "variable: {wght: 400}",
                "path: community-fonts/ExampleSansJP/ExampleSans-Regular.ttf",
            ):
                self.assertIn(expected, text)
            for removed in (
                "license_type",
                "license_url",
                "LICENSES.md",
                "python scripts/validate_config.py",
                "python scripts/build_fonts.py --clean --only <FamilyId>",
            ):
                self.assertNotIn(removed, text)

        self.assertIn("一个 CJK 字体家族", guides["zh"])
        self.assertIn("1つの CJK フォントファミリー", guides["ja"])
        self.assertIn("来源官网或源仓库", guides["zh"])
        self.assertIn("配布元サイトまたはソースリポジトリ", guides["ja"])

    def test_optional_metadata_and_autohint_are_explained(self):
        guides = [
            CONTRIBUTING.read_text(encoding="utf-8"),
            CONTRIBUTING_ZH.read_text(encoding="utf-8"),
            CONTRIBUTING_JA.read_text(encoding="utf-8"),
        ]
        for text in guides:
            self.assertRegex(text, r"`display_names\.en`\s*\|\s*(Yes|是|必須)")
            self.assertRegex(text, r"`display_names\.zh`\s*\|\s*(No|否|任意)")
            self.assertRegex(text, r"`display_names\.ja`\s*\|\s*(No|否|任意)")
            self.assertRegex(text, r"`description`\s*\|\s*(No|否|任意)")
            self.assertIn("FreeType", text)
            self.assertIn("hint", text.lower())
            self.assertIn("false", text)

    def test_intervals_are_explained_as_glyph_coverage(self):
        guides = {
            "en": CONTRIBUTING.read_text(encoding="utf-8"),
            "zh": CONTRIBUTING_ZH.read_text(encoding="utf-8"),
            "ja": CONTRIBUTING_JA.read_text(encoding="utf-8"),
        }
        for text in guides.values():
            self.assertIn("Unicode", text)
            self.assertIn("latin-ext,cjk", text)
            self.assertIn(".cpfont", text)
            self.assertIn("U+FFFD", text)
            self.assertIn("(0x2100-0x214F)", text)
        self.assertIn("does not describe the font's language or style", guides["en"])
        self.assertIn("不是字体语言或风格标签", guides["zh"])
        self.assertIn("言語や書体の分類ラベルではありません", guides["ja"])

    def test_contribution_guide_documents_the_complete_one_family_flow(self):
        text = CONTRIBUTING.read_text(encoding="utf-8")
        for expected in (
            "one CJK font family",
            "| Field | Required | Description |",
            "source_url",
            "config/fonts.yaml",
            "archive_member",
            "variable: {wght: 400}",
            "path: community-fonts/ExampleSansJP/ExampleSans-Regular.ttf",
            "Pull requests from forks run read-only checks",
        ):
            self.assertIn(expected, text)
        for removed in ("license_type", "license_url", "LICENSES.md", "## 5. Local validation"):
            self.assertNotIn(removed, text)

    def test_font_pr_template_collects_source_and_catalog_metadata(self):
        text = FONT_TEMPLATE.read_text(encoding="utf-8")
        for expected in (
            "Stable family ID",
            "Font file path",
            "Source homepage or repository URL",
            "config/fonts.yaml",
            "one font family",
        ):
            self.assertIn(expected, text)
        for removed in ("License", "LICENSES.md", "## Validation", "python scripts/"):
            self.assertNotIn(removed, text)

        self.assertIn("English display name", text)
        self.assertIn("Optional localized names or description", text)
        self.assertIn("FreeType auto-hinting", text)

        self.assertIn("name: Font submission", FONT_CHOOSER_TEMPLATE.read_text(encoding="utf-8"))
        self.assertTrue(GENERAL_TEMPLATE.is_file())
        self.assertIn("name: General change", GENERAL_TEMPLATE.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
