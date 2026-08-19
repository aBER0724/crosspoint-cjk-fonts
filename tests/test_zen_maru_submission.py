#!/usr/bin/env python3

import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "fonts.yaml"
SOURCES = ROOT / "SOURCES.md"


class ZenMaruSubmissionTest(unittest.TestCase):
    def test_zen_maru_gothic_submission_is_locked_and_has_a_source(self):
        document = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
        family = next((entry for entry in document["families"] if entry["name"] == "ZenMaruGothicJP"), None)

        self.assertIsNotNone(family)
        self.assertEqual(
            family,
            {
                "name": "ZenMaruGothicJP",
                "display_names": {
                    "en": "Zen Maru Gothic",
                    "zh": "Zen Maru Gothic",
                    "ja": "Zen 丸ゴシック",
                },
                "description": "Soft Japanese rounded sans-serif with kanji and kana",
                "category": "rounded-sans",
                "languages": ["ja"],
                "source_url": "https://github.com/google/fonts/tree/92503f07b74eab956c1abf4956fbf46170716caa/ofl/zenmarugothic",
                "intervals": "latin-ext,cjk",
                "source": {
                    "url": "https://raw.githubusercontent.com/google/fonts/92503f07b74eab956c1abf4956fbf46170716caa/ofl/zenmarugothic/ZenMaruGothic-Regular.ttf",
                    "filename": "ZenMaruGothic-Regular.ttf",
                    "sha256": "a0c0b53543e0993ae2225e629c833f3d51495ad31720694ff112ce4ce11111ef",
                },
            },
        )

        sources = SOURCES.read_text(encoding="utf-8")
        self.assertIn("| ZenMaruGothicJP |", sources)
        self.assertIn("92503f07b74eab956c1abf4956fbf46170716caa", sources)


if __name__ == "__main__":
    unittest.main()
