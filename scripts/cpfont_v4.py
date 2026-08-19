#!/usr/bin/env python3
"""Strict reader for the uncompressed 2-bit CrossPoint `.cpfont` v4 format."""

from __future__ import annotations

import struct
from bisect import bisect_right
from dataclasses import dataclass
from pathlib import Path


CPFONT_MAGIC = b"CPFONT\x00\x00"
CPFONT_VERSION = 4
CPFONT_FLAG_2BIT = 0x0001

GLOBAL_HEADER = struct.Struct("<8sHHB19s")
STYLE_TOC = struct.Struct("<B3xIIBhhHHBBBI4x")
INTERVAL = struct.Struct("<III")
GLYPH = struct.Struct("<BBHhhH2xI")
KERN_CLASS = struct.Struct("<HB")
LIGATURE = struct.Struct("<II")

MAX_STYLES = 4
MAX_GLYPHS = 65536
MAX_KERN_ENTRIES = 4096


class CpfontError(ValueError):
    """Raised when a `.cpfont` file violates the v4 binary contract."""


@dataclass(frozen=True)
class CpfontHeader:
    version: int
    flags: int
    style_count: int

    @property
    def is_2bit(self) -> bool:
        return bool(self.flags & CPFONT_FLAG_2BIT)


@dataclass(frozen=True)
class UnicodeInterval:
    first: int
    last: int
    offset: int


@dataclass(frozen=True)
class Glyph:
    width: int
    height: int
    advance_x: int
    left: int
    top: int
    data_length: int
    data_offset: int


@dataclass(frozen=True)
class KernClassEntry:
    codepoint: int
    class_id: int


@dataclass(frozen=True)
class LigaturePair:
    pair: int
    replacement: int


@dataclass(frozen=True)
class _StyleToc:
    style_id: int
    interval_count: int
    glyph_count: int
    advance_y: int
    ascender: int
    descender: int
    kern_left_entry_count: int
    kern_right_entry_count: int
    kern_left_class_count: int
    kern_right_class_count: int
    ligature_pair_count: int
    data_offset: int


class CpfontStyle:
    """One parsed font style and its immutable binary data."""

    def __init__(
        self,
        *,
        toc: _StyleToc,
        intervals: tuple[UnicodeInterval, ...],
        glyphs: tuple[Glyph, ...],
        kern_left: tuple[KernClassEntry, ...],
        kern_right: tuple[KernClassEntry, ...],
        kern_matrix: bytes,
        ligatures: tuple[LigaturePair, ...],
        bitmaps: bytes,
    ) -> None:
        self.style_id = toc.style_id
        self.advance_y = toc.advance_y
        self.ascender = toc.ascender
        self.descender = toc.descender
        self.intervals = intervals
        self.glyphs = glyphs
        self.kern_left = kern_left
        self.kern_right = kern_right
        self.kern_matrix = kern_matrix
        self.ligatures = ligatures
        self.bitmaps = bitmaps
        self.kern_left_class_count = toc.kern_left_class_count
        self.kern_right_class_count = toc.kern_right_class_count
        self._interval_starts = tuple(interval.first for interval in intervals)
        self._kern_left_map = {entry.codepoint: entry.class_id for entry in kern_left}
        self._kern_right_map = {entry.codepoint: entry.class_id for entry in kern_right}
        self._ligature_map = {entry.pair: entry.replacement for entry in ligatures}

    def glyph_index(self, codepoint: int) -> int | None:
        position = bisect_right(self._interval_starts, codepoint) - 1
        if position < 0:
            return None
        interval = self.intervals[position]
        if codepoint > interval.last:
            return None
        return interval.offset + codepoint - interval.first

    def glyph_for(self, codepoint: int) -> Glyph | None:
        index = self.glyph_index(codepoint)
        return self.glyphs[index] if index is not None else None

    def bitmap_for(self, glyph: Glyph) -> bytes:
        start = glyph.data_offset
        return self.bitmaps[start : start + glyph.data_length]

    def decode_bitmap(self, glyph: Glyph) -> tuple[tuple[int, ...], ...]:
        bitmap = self.bitmap_for(glyph)
        rows = []
        for y in range(glyph.height):
            row = []
            for x in range(glyph.width):
                position = y * glyph.width + x
                value = bitmap[position >> 2]
                shift = (3 - (position & 3)) * 2
                row.append((value >> shift) & 0x03)
            rows.append(tuple(row))
        return tuple(rows)

    def kerning_fp4(self, left: int, right: int) -> int:
        left_class = self._kern_left_map.get(left, 0)
        right_class = self._kern_right_map.get(right, 0)
        if left_class == 0 or right_class == 0:
            return 0
        index = (left_class - 1) * self.kern_right_class_count + right_class - 1
        raw = self.kern_matrix[index]
        return raw - 256 if raw >= 128 else raw

    def ligature_for(self, left: int, right: int) -> int | None:
        if left > 0xFFFF or right > 0xFFFF:
            return None
        return self._ligature_map.get((left << 16) | right)


class CpfontFile:
    """Validated `.cpfont` v4 file."""

    def __init__(self, header: CpfontHeader, styles: tuple[CpfontStyle, ...]) -> None:
        self.header = header
        self.styles = styles
        self._styles_by_id = {style.style_id: style for style in styles}

    @classmethod
    def from_path(cls, path: str | Path) -> "CpfontFile":
        return cls.from_bytes(Path(path).read_bytes())

    @classmethod
    def from_bytes(cls, data: bytes) -> "CpfontFile":
        if len(data) < GLOBAL_HEADER.size:
            raise CpfontError("truncated global header")
        magic, version, flags, style_count, _reserved = GLOBAL_HEADER.unpack_from(data)
        if magic != CPFONT_MAGIC:
            raise CpfontError("invalid cpfont magic")
        if version != CPFONT_VERSION:
            raise CpfontError(f"unsupported cpfont version {version}")
        if not flags & CPFONT_FLAG_2BIT:
            raise CpfontError("cpfont v4 preview requires 2-bit bitmap data")
        if flags & ~CPFONT_FLAG_2BIT:
            raise CpfontError(f"unsupported cpfont flags 0x{flags:04x}")
        if not 1 <= style_count <= MAX_STYLES:
            raise CpfontError(f"invalid style count {style_count}")

        toc_end = GLOBAL_HEADER.size + style_count * STYLE_TOC.size
        if len(data) < toc_end:
            raise CpfontError("truncated style TOC")

        toc_entries = []
        style_ids = set()
        for index in range(style_count):
            values = STYLE_TOC.unpack_from(data, GLOBAL_HEADER.size + index * STYLE_TOC.size)
            toc = _StyleToc(*values)
            if toc.style_id not in range(MAX_STYLES):
                raise CpfontError(f"invalid style ID {toc.style_id}")
            if toc.style_id in style_ids:
                raise CpfontError(f"duplicate style ID {toc.style_id}")
            style_ids.add(toc.style_id)
            if toc.glyph_count > MAX_GLYPHS:
                raise CpfontError(f"style {toc.style_id}: unreasonable glyph count")
            if toc.interval_count > toc.glyph_count:
                raise CpfontError(f"style {toc.style_id}: interval count exceeds glyph count")
            if (
                toc.kern_left_entry_count > MAX_KERN_ENTRIES
                or toc.kern_right_entry_count > MAX_KERN_ENTRIES
            ):
                raise CpfontError(f"style {toc.style_id}: unreasonable kerning entry count")
            toc_entries.append(toc)

        toc_entries.sort(key=lambda entry: entry.data_offset)
        for previous, current in zip(toc_entries, toc_entries[1:]):
            if current.data_offset <= previous.data_offset:
                raise CpfontError("style data offsets must be strictly increasing")
        expected_data_offset = toc_end
        parsed_styles = []
        for index, toc in enumerate(toc_entries):
            if toc.data_offset != expected_data_offset:
                raise CpfontError(
                    f"style {toc.style_id}: invalid data offset {toc.data_offset}, expected {expected_data_offset}"
                )
            style_limit = (
                toc_entries[index + 1].data_offset if index + 1 < len(toc_entries) else len(data)
            )
            style, expected_data_offset = _parse_style(data, toc, style_limit)
            parsed_styles.append(style)

        if expected_data_offset != len(data):
            raise CpfontError("unexpected trailing bytes after style data")

        parsed_styles.sort(key=lambda style: style.style_id)
        return cls(
            CpfontHeader(version=version, flags=flags, style_count=style_count),
            tuple(parsed_styles),
        )

    @property
    def style_ids(self) -> tuple[int, ...]:
        return tuple(style.style_id for style in self.styles)

    def style(self, style_id: int) -> CpfontStyle | None:
        return self._styles_by_id.get(style_id)

    @property
    def regular(self) -> CpfontStyle:
        regular = self.style(0)
        if regular is None:
            raise CpfontError("cpfont has no regular style")
        return regular


def _read_records(data: bytes, offset: int, count: int, record: struct.Struct, label: str, limit: int):
    end = offset + count * record.size
    if end > limit:
        raise CpfontError(f"style data has truncated {label} section")
    return tuple(record.unpack_from(data, offset + index * record.size) for index in range(count)), end


def _validate_class_entries(
    entries: tuple[KernClassEntry, ...], class_count: int, label: str
) -> None:
    previous = -1
    for entry in entries:
        if entry.codepoint <= previous:
            raise CpfontError(f"{label} kerning entries are not strictly sorted")
        if not 1 <= entry.class_id <= class_count:
            raise CpfontError(f"{label} kerning entry has invalid class ID")
        previous = entry.codepoint
    if class_count and not entries:
        raise CpfontError(f"{label} kerning class count has no entries")


def _parse_style(data: bytes, toc: _StyleToc, style_limit: int) -> tuple[CpfontStyle, int]:
    offset = toc.data_offset

    raw_intervals, offset = _read_records(
        data, offset, toc.interval_count, INTERVAL, "interval", style_limit
    )
    intervals = tuple(UnicodeInterval(*values) for values in raw_intervals)
    expected_glyph_offset = 0
    previous_last = -1
    for interval in intervals:
        if interval.first > interval.last:
            raise CpfontError(f"style {toc.style_id}: invalid interval range")
        if interval.first <= previous_last:
            raise CpfontError(f"style {toc.style_id}: overlapping interval range")
        if interval.offset != expected_glyph_offset:
            raise CpfontError(
                f"style {toc.style_id}: invalid interval offset {interval.offset}, expected {expected_glyph_offset}"
            )
        expected_glyph_offset += interval.last - interval.first + 1
        if expected_glyph_offset > toc.glyph_count:
            raise CpfontError(f"style {toc.style_id}: interval exceeds glyph count")
        previous_last = interval.last
    if expected_glyph_offset != toc.glyph_count:
        raise CpfontError(f"style {toc.style_id}: intervals do not cover glyph count")

    raw_glyphs, offset = _read_records(data, offset, toc.glyph_count, GLYPH, "glyph", style_limit)
    glyphs = tuple(Glyph(*values) for values in raw_glyphs)
    for glyph in glyphs:
        expected_length = (glyph.width * glyph.height + 3) // 4
        if glyph.data_length != expected_length:
            raise CpfontError(
                f"style {toc.style_id}: invalid glyph bitmap length {glyph.data_length}, expected {expected_length}"
            )

    raw_left, offset = _read_records(
        data, offset, toc.kern_left_entry_count, KERN_CLASS, "left kerning", style_limit
    )
    raw_right, offset = _read_records(
        data, offset, toc.kern_right_entry_count, KERN_CLASS, "right kerning", style_limit
    )
    kern_left = tuple(KernClassEntry(*values) for values in raw_left)
    kern_right = tuple(KernClassEntry(*values) for values in raw_right)
    _validate_class_entries(kern_left, toc.kern_left_class_count, "left")
    _validate_class_entries(kern_right, toc.kern_right_class_count, "right")

    matrix_size = toc.kern_left_class_count * toc.kern_right_class_count
    matrix_end = offset + matrix_size
    if matrix_end > style_limit:
        raise CpfontError("style data has truncated kerning matrix")
    kern_matrix = data[offset:matrix_end]
    offset = matrix_end

    raw_ligatures, offset = _read_records(
        data, offset, toc.ligature_pair_count, LIGATURE, "ligature", style_limit
    )
    ligatures = tuple(LigaturePair(*values) for values in raw_ligatures)
    previous_pair = -1
    for ligature in ligatures:
        if ligature.pair <= previous_pair:
            raise CpfontError("ligature pairs are not strictly sorted")
        previous_pair = ligature.pair

    bitmap_start = offset
    bitmap_size = style_limit - bitmap_start
    expected_bitmap_offset = 0
    for glyph in glyphs:
        end = glyph.data_offset + glyph.data_length
        if end > bitmap_size:
            raise CpfontError(f"style {toc.style_id}: glyph bitmap range exceeds style data")
        if glyph.data_offset != expected_bitmap_offset:
            raise CpfontError(
                f"style {toc.style_id}: non-contiguous glyph bitmap range at {glyph.data_offset}"
            )
        expected_bitmap_offset = end
    if expected_bitmap_offset != bitmap_size:
        raise CpfontError("unexpected trailing bytes after style bitmap data")

    style = CpfontStyle(
        toc=toc,
        intervals=intervals,
        glyphs=glyphs,
        kern_left=kern_left,
        kern_right=kern_right,
        kern_matrix=kern_matrix,
        ligatures=ligatures,
        bitmaps=data[bitmap_start:style_limit],
    )
    return style, style_limit
