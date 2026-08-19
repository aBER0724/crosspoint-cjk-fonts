#!/usr/bin/env python3

import struct
import unittest
from dataclasses import dataclass

from scripts.cpfont_v4 import CpfontError, CpfontFile


GLOBAL_HEADER = struct.Struct("<8sHHB19s")
STYLE_TOC = struct.Struct("<B3xIIBhhHHBBBI4x")
INTERVAL = struct.Struct("<III")
GLYPH = struct.Struct("<BBHhhH2xI")
KERN_CLASS = struct.Struct("<HB")
LIGATURE = struct.Struct("<II")


@dataclass(frozen=True)
class StyleFixture:
    style_id: int = 0
    interval_offset: int = 0
    first_bitmap_length: int = 1
    first_bitmap_offset: int = 0
    second_bitmap_length: int = 1
    second_bitmap_offset: int = 1


def build_style(fixture: StyleFixture) -> tuple[bytes, dict[str, int]]:
    intervals = INTERVAL.pack(0x41, 0x42, fixture.interval_offset)
    glyphs = b"".join(
        (
            GLYPH.pack(
                4,
                1,
                32,
                0,
                1,
                fixture.first_bitmap_length,
                fixture.first_bitmap_offset,
            ),
            GLYPH.pack(
                1,
                2,
                24,
                -1,
                2,
                fixture.second_bitmap_length,
                fixture.second_bitmap_offset,
            ),
        )
    )
    kern_left = KERN_CLASS.pack(0x41, 1)
    kern_right = KERN_CLASS.pack(0x42, 1)
    kern_matrix = struct.pack("<b", -8)
    ligatures = LIGATURE.pack((0x41 << 16) | 0x42, 0xFB01)
    bitmaps = bytes((0x1B, 0xD0))
    blob = intervals + glyphs + kern_left + kern_right + kern_matrix + ligatures + bitmaps
    return blob, {
        "interval_count": 1,
        "glyph_count": 2,
        "kern_left_count": 1,
        "kern_right_count": 1,
        "kern_left_classes": 1,
        "kern_right_classes": 1,
        "ligature_count": 1,
    }


def build_cpfont(*fixtures: StyleFixture, flags: int = 1, version: int = 4) -> bytes:
    if not fixtures:
        fixtures = (StyleFixture(),)

    blobs = []
    metadata = []
    data_offset = GLOBAL_HEADER.size + STYLE_TOC.size * len(fixtures)
    for fixture in fixtures:
        blob, counts = build_style(fixture)
        blobs.append(blob)
        metadata.append((fixture, counts, data_offset))
        data_offset += len(blob)

    header = GLOBAL_HEADER.pack(b"CPFONT\x00\x00", version, flags, len(fixtures), bytes(19))
    toc = bytearray()
    for fixture, counts, offset in metadata:
        toc += STYLE_TOC.pack(
            fixture.style_id,
            counts["interval_count"],
            counts["glyph_count"],
            20,
            15,
            -5,
            counts["kern_left_count"],
            counts["kern_right_count"],
            counts["kern_left_classes"],
            counts["kern_right_classes"],
            counts["ligature_count"],
            offset,
        )
    return header + bytes(toc) + b"".join(blobs)


class CpfontV4ParserTest(unittest.TestCase):
    def test_parses_complete_regular_style_and_looks_up_codepoints(self):
        font = CpfontFile.from_bytes(build_cpfont())

        self.assertEqual(font.header.version, 4)
        self.assertTrue(font.header.is_2bit)
        self.assertEqual(font.style_ids, (0,))

        regular = font.regular
        self.assertEqual(regular.advance_y, 20)
        self.assertEqual(regular.ascender, 15)
        self.assertEqual(regular.descender, -5)
        self.assertEqual(regular.glyph_index(0x41), 0)
        self.assertEqual(regular.glyph_index(0x42), 1)
        self.assertIsNone(regular.glyph_index(0x43))

        glyph_a = regular.glyph_for(0x41)
        self.assertIsNotNone(glyph_a)
        self.assertEqual(glyph_a.advance_x, 32)
        self.assertEqual(regular.bitmap_for(glyph_a), b"\x1b")
        self.assertEqual(regular.kerning_fp4(0x41, 0x42), -8)
        self.assertEqual(regular.ligature_for(0x41, 0x42), 0xFB01)

    def test_decodes_four_pixels_most_significant_pair_first(self):
        font = CpfontFile.from_bytes(build_cpfont())
        regular = font.regular
        glyph = regular.glyph_for(0x41)

        self.assertEqual(regular.decode_bitmap(glyph), ((0, 1, 2, 3),))

    def test_rejects_bad_magic_and_wrong_version(self):
        bad_magic = bytearray(build_cpfont())
        bad_magic[:8] = b"NOTFONT!"
        with self.assertRaisesRegex(CpfontError, "magic"):
            CpfontFile.from_bytes(bytes(bad_magic))

        with self.assertRaisesRegex(CpfontError, "version"):
            CpfontFile.from_bytes(build_cpfont(version=3))

    def test_rejects_non_2bit_files(self):
        with self.assertRaisesRegex(CpfontError, "2-bit"):
            CpfontFile.from_bytes(build_cpfont(flags=0))

    def test_rejects_truncated_toc_and_invalid_style_ids(self):
        declared_two_styles = bytearray(build_cpfont())
        declared_two_styles[12] = 2
        with self.assertRaisesRegex(CpfontError, "TOC"):
            CpfontFile.from_bytes(bytes(declared_two_styles[:63]))

        with self.assertRaisesRegex(CpfontError, "style ID"):
            CpfontFile.from_bytes(build_cpfont(StyleFixture(style_id=4)))

        with self.assertRaisesRegex(CpfontError, "duplicate style"):
            CpfontFile.from_bytes(build_cpfont(StyleFixture(), StyleFixture()))

    def test_rejects_invalid_interval_offsets_and_counts(self):
        with self.assertRaisesRegex(CpfontError, "interval offset"):
            CpfontFile.from_bytes(build_cpfont(StyleFixture(interval_offset=1)))

        broken = bytearray(build_cpfont())
        style_data = GLOBAL_HEADER.size + STYLE_TOC.size
        struct.pack_into("<I", broken, style_data + 4, 0x40)
        with self.assertRaisesRegex(CpfontError, "interval"):
            CpfontFile.from_bytes(bytes(broken))

    def test_rejects_invalid_bitmap_lengths_and_ranges(self):
        with self.assertRaisesRegex(CpfontError, "bitmap length"):
            CpfontFile.from_bytes(build_cpfont(StyleFixture(first_bitmap_length=2)))

        with self.assertRaisesRegex(CpfontError, "bitmap range"):
            CpfontFile.from_bytes(build_cpfont(StyleFixture(first_bitmap_offset=99)))

    def test_rejects_trailing_or_overlapping_style_data(self):
        with self.assertRaisesRegex(CpfontError, "trailing"):
            CpfontFile.from_bytes(build_cpfont() + b"\x00")

        two_styles = bytearray(build_cpfont(StyleFixture(style_id=0), StyleFixture(style_id=1)))
        first_offset = struct.unpack_from("<I", two_styles, GLOBAL_HEADER.size + 24)[0]
        struct.pack_into("<I", two_styles, GLOBAL_HEADER.size + STYLE_TOC.size + 24, first_offset)
        with self.assertRaisesRegex(CpfontError, "data offset"):
            CpfontFile.from_bytes(bytes(two_styles))


if __name__ == "__main__":
    unittest.main()
