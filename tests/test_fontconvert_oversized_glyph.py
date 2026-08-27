#!/usr/bin/env python3

import importlib.util
import unittest
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
SPEC = importlib.util.spec_from_file_location("fontconvert_sdcard", ROOT / "scripts" / "fontconvert_sdcard.py")
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class OversizedGlyphTest(unittest.TestCase):
    def test_oversized_primary_glyph_uses_fallback_before_packing(self):
        source = ROOT / ".cache" / "sources" / "ChillDuanHeiSongSC" / "寒蝉端黑宋.otf"
        fallback = ROOT / "vendor" / "NotoSans-Regular.ttf"
        if not source.exists() or not fallback.exists():
            self.skipTest("cached regression fonts are unavailable")

        data = MODULE.rasterize_font_style(
            str(source),
            8,
            [(0x4E44, 0x4E44)],
            "regular",
            force_autohint=True,
            fallback_fontfile=str(fallback),
        )
        glyph, _ = data.all_glyphs[0]
        self.assertLessEqual(glyph.width, 0xFF)
        self.assertLessEqual(glyph.height, 0xFF)
        MODULE.pack_style_sections(data)


if __name__ == "__main__":
    unittest.main()
