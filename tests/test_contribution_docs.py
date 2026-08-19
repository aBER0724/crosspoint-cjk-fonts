#!/usr/bin/env python3

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
CONTRIBUTING = ROOT / "CONTRIBUTING.md"
FONT_TEMPLATE = ROOT / ".github" / "PULL_REQUEST_TEMPLATE.md"
FONT_CHOOSER_TEMPLATE = ROOT / ".github" / "PULL_REQUEST_TEMPLATE" / "font-submission.md"
GENERAL_TEMPLATE = ROOT / ".github" / "PULL_REQUEST_TEMPLATE" / "general-change.md"


class ContributionDocsTest(unittest.TestCase):
    def test_readme_has_a_prominent_font_submission_entry_point(self):
        text = README.read_text(encoding="utf-8")
        catalog_position = text.index("## Catalog")
        submission_position = text.index("## Submit a font")

        self.assertLess(submission_position, catalog_position)
        self.assertIn("[read the font contribution guide](CONTRIBUTING.md)", text)
        self.assertIn("Font submission", text)
        self.assertIn("Do **not** commit TTF/OTF/ZIP sources", text)

    def test_contribution_guide_documents_the_complete_one_family_flow(self):
        text = CONTRIBUTING.read_text(encoding="utf-8")
        for expected in (
            "one font family",
            "SIL Open Font License 1.1",
            "full commit SHA",
            "config/fonts.yaml",
            "LICENSES.md",
            "archive_member",
            "variable: {wght: 400}",
            "python scripts/validate_config.py",
            "python scripts/build_fonts.py --clean --only <FamilyId>",
            "Do **not** add `dist/`",
            "Pull requests from forks run read-only validation",
        ):
            self.assertIn(expected, text)

    def test_font_pr_template_collects_source_license_and_validation_evidence(self):
        text = FONT_TEMPLATE.read_text(encoding="utf-8")
        for expected in (
            "Stable family ID",
            "Stable family ID",
            "Pinned release or full commit SHA",
            "Source SHA-256",
            "Reserved Font Name declared?",
            "config/fonts.yaml",
            "LICENSES.md",
            "python scripts/build_fonts.py --clean --only <FamilyId>",
            "one font family",
        ):
            self.assertIn(expected, text)

        self.assertIn("name: Font submission", FONT_CHOOSER_TEMPLATE.read_text(encoding="utf-8"))
        self.assertTrue(GENERAL_TEMPLATE.is_file())
        self.assertIn("name: General change", GENERAL_TEMPLATE.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
