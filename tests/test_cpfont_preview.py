#!/usr/bin/env python3

import struct
import unittest

from scripts.cpfont_v4 import CpfontFile
from scripts.render_cpfont_preview import GRAYSCALE_TONES, layout_text, render_text


GLOBAL_HEADER = struct.Struct("<8sHHB19s")
STYLE_TOC = struct.Struct("<B3xIIBhhHHBBBI4x")
INTERVAL = struct.Struct("<III")
GLYPH = struct.Struct("<BBHhhH2xI")
KERN_CLASS = struct.Struct("<HB")
LIGATURE = struct.Struct("<II")


def build_preview_font() -> CpfontFile:
    codepoints = (0x41, 0x42, 0xFB01, 0xFFFD)
    intervals = b"".join(
        (
            INTERVAL.pack(0x41, 0x42, 0),
            INTERVAL.pack(0xFB01, 0xFB01, 2),
            INTERVAL.pack(0xFFFD, 0xFFFD, 3),
        )
    )
    bitmaps = (b"\x1b", b"\xc0", b"\xf0", b"\x40")
    glyph_specs = (
        (4, 1, 32, 0, 1),
        (1, 2, 24, -1, 2),
        (2, 1, 40, 0, 1),
        (1, 1, 24, 0, 1),
    )
    glyphs = bytearray()
    offset = 0
    for (width, height, advance, left, top), bitmap in zip(glyph_specs, bitmaps):
        glyphs += GLYPH.pack(width, height, advance, left, top, len(bitmap), offset)
        offset += len(bitmap)

    kern_left = KERN_CLASS.pack(0x41, 1)
    kern_right = KERN_CLASS.pack(0x42, 1)
    kern_matrix = struct.pack("<b", -8)
    ligatures = LIGATURE.pack((0x41 << 16) | 0x42, 0xFB01)
    style_data = intervals + bytes(glyphs) + kern_left + kern_right + kern_matrix + ligatures + b"".join(bitmaps)
    data_offset = GLOBAL_HEADER.size + STYLE_TOC.size
    header = GLOBAL_HEADER.pack(b"CPFONT\x00\x00", 4, 1, 1, bytes(19))
    toc = STYLE_TOC.pack(0, 3, len(codepoints), 6, 4, -2, 1, 1, 1, 1, 1, data_offset)
    return CpfontFile.from_bytes(header + toc + style_data)


class CpfontPreviewTest(unittest.TestCase):
    def setUp(self):
        self.font = build_preview_font()

    def test_layout_uses_baseline_bearings_and_fp4_advance(self):
        layout = layout_text(self.font.regular, "AA", canvas_width=20, padding=2, apply_ligatures=False)

        self.assertEqual(layout.baselines, (6,))
        self.assertEqual([(item.codepoint, item.x, item.y) for item in layout.glyphs], [(0x41, 2, 5), (0x41, 4, 5)])

    def test_layout_keeps_kerning_in_fp4_until_pairwise_rounding(self):
        layout = layout_text(self.font.regular, "AB", canvas_width=20, padding=2, apply_ligatures=False)

        self.assertEqual([(item.codepoint, item.x) for item in layout.glyphs], [(0x41, 2), (0x42, 3)])

    def test_layout_applies_ligatures_before_glyph_lookup(self):
        layout = layout_text(self.font.regular, "AB", canvas_width=20, padding=2)

        self.assertEqual([item.codepoint for item in layout.glyphs], [0xFB01])

    def test_layout_wraps_without_scaling_physical_advances(self):
        layout = layout_text(self.font.regular, "AAA", canvas_width=8, padding=2, apply_ligatures=False)

        self.assertEqual(layout.baselines, (6, 12, 18))
        self.assertEqual([(item.x, item.y) for item in layout.glyphs], [(2, 5), (2, 11), (2, 17)])

    def test_missing_glyph_uses_replacement_and_records_original_codepoint(self):
        layout = layout_text(self.font.regular, "Z", canvas_width=20, padding=2)

        self.assertEqual([item.codepoint for item in layout.glyphs], [0xFFFD])
        self.assertEqual(layout.missing_codepoints, (0x5A,))

    def test_render_maps_raw_two_bit_values_to_fixed_grayscale(self):
        result = render_text(self.font, "A", canvas_width=12, padding=2, apply_ligatures=False)

        self.assertEqual(result.image.mode, "L")
        self.assertEqual(result.image.size, (12, 10))
        self.assertEqual(tuple(result.image.getpixel((x, 5)) for x in range(2, 6)), GRAYSCALE_TONES)
        self.assertEqual(result.image.getpixel((0, 0)), 255)

    def test_transparent_preview_keeps_glyph_coverage_without_white_canvas(self):
        result = render_text(
            self.font,
            "A",
            canvas_width=12,
            padding=2,
            apply_ligatures=False,
            transparent_background=True,
        )

        self.assertEqual(result.image.mode, "RGBA")
        self.assertEqual(result.image.getpixel((0, 0)), (255, 255, 255, 0))
        self.assertEqual(
            tuple(result.image.getpixel((x, 5))[3] for x in range(2, 6)),
            tuple(255 - tone for tone in GRAYSCALE_TONES),
        )


if __name__ == "__main__":
    unittest.main()
