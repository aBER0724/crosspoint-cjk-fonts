#!/usr/bin/env python3
"""Render deterministic PNG previews directly from `.cpfont v4` bitmap data."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

from PIL import Image

try:
    from .cpfont_v4 import CpfontFile, CpfontStyle, Glyph
except ImportError:
    from cpfont_v4 import CpfontFile, CpfontStyle, Glyph


GRAYSCALE_TONES = (255, 170, 85, 0)
REPLACEMENT_CODEPOINT = 0xFFFD


@dataclass(frozen=True)
class PositionedGlyph:
    codepoint: int
    glyph: Glyph
    x: int
    y: int


@dataclass(frozen=True)
class TextLayout:
    glyphs: tuple[PositionedGlyph, ...]
    baselines: tuple[int, ...]
    missing_codepoints: tuple[int, ...]
    width: int
    height: int


@dataclass(frozen=True)
class RenderResult:
    image: Image.Image
    missing_codepoints: tuple[int, ...]


def substitute_ligatures(style: CpfontStyle, codepoints: list[int]) -> list[int]:
    if len(codepoints) < 2:
        return codepoints
    result: list[int] = []
    for codepoint in codepoints:
        if result:
            replacement = style.ligature_for(result[-1], codepoint)
            if replacement is not None:
                result[-1] = replacement
                continue
        result.append(codepoint)
    return result


def _resolved_glyph(style: CpfontStyle, codepoint: int) -> tuple[int, Glyph | None, bool]:
    glyph = style.glyph_for(codepoint)
    if glyph is not None:
        return codepoint, glyph, False
    replacement = style.glyph_for(REPLACEMENT_CODEPOINT)
    if replacement is not None:
        return REPLACEMENT_CODEPOINT, replacement, True
    return codepoint, None, True


def layout_text(
    style: CpfontStyle,
    text: str,
    *,
    canvas_width: int,
    padding: int = 16,
    apply_ligatures: bool = True,
) -> TextLayout:
    if canvas_width <= padding * 2:
        raise ValueError("canvas width must exceed horizontal padding")
    if padding < 0:
        raise ValueError("padding cannot be negative")

    codepoints = [ord(character) for character in text]
    if apply_ligatures:
        codepoints = substitute_ligatures(style, codepoints)

    positioned: list[PositionedGlyph] = []
    missing: list[int] = []
    baselines: list[int] = []
    baseline = padding + style.ascender
    pen_x = padding
    previous_codepoint: int | None = None
    previous_advance_fp4 = 0

    def start_line() -> None:
        nonlocal pen_x, previous_codepoint, previous_advance_fp4
        if not baselines or baselines[-1] != baseline:
            baselines.append(baseline)
        pen_x = padding
        previous_codepoint = None
        previous_advance_fp4 = 0

    start_line()
    for original_codepoint in codepoints:
        if original_codepoint in (0x0A, 0x0D):
            if original_codepoint == 0x0D:
                continue
            baseline += style.advance_y
            start_line()
            continue

        resolved_codepoint, glyph, was_missing = _resolved_glyph(style, original_codepoint)
        if was_missing:
            missing.append(original_codepoint)
        if glyph is None:
            continue

        step = 0
        if previous_codepoint is not None:
            kern_fp4 = style.kerning_fp4(previous_codepoint, resolved_codepoint)
            step = (previous_advance_fp4 + kern_fp4 + 8) >> 4
        candidate_x = pen_x + step
        glyph_right = candidate_x + glyph.left + glyph.width
        if previous_codepoint is not None and glyph_right > canvas_width - padding:
            baseline += style.advance_y
            start_line()
            candidate_x = pen_x

        positioned.append(
            PositionedGlyph(
                codepoint=resolved_codepoint,
                glyph=glyph,
                x=candidate_x + glyph.left,
                y=baseline - glyph.top,
            )
        )
        pen_x = candidate_x
        previous_codepoint = resolved_codepoint
        previous_advance_fp4 = glyph.advance_x

    if not positioned:
        raise ValueError("preview text has no renderable glyphs")

    height = baselines[-1] - style.descender + padding
    return TextLayout(
        glyphs=tuple(positioned),
        baselines=tuple(baselines),
        missing_codepoints=tuple(dict.fromkeys(missing)),
        width=canvas_width,
        height=height,
    )


def render_text(
    font: CpfontFile,
    text: str,
    *,
    canvas_width: int = 880,
    padding: int = 24,
    apply_ligatures: bool = True,
) -> RenderResult:
    style = font.regular
    layout = layout_text(
        style,
        text,
        canvas_width=canvas_width,
        padding=padding,
        apply_ligatures=apply_ligatures,
    )
    image = Image.new("L", (layout.width, layout.height), color=255)
    pixels = image.load()
    for positioned in layout.glyphs:
        decoded = style.decode_bitmap(positioned.glyph)
        for y, row in enumerate(decoded):
            destination_y = positioned.y + y
            if destination_y < 0 or destination_y >= layout.height:
                continue
            for x, raw in enumerate(row):
                destination_x = positioned.x + x
                if 0 <= destination_x < layout.width:
                    pixels[destination_x, destination_y] = GRAYSCALE_TONES[raw]
    return RenderResult(image=image, missing_codepoints=layout.missing_codepoints)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("font", type=Path, help="Input `.cpfont v4` file")
    parser.add_argument("--text", required=True, help="Preview text")
    parser.add_argument("--output", required=True, type=Path, help="Output PNG")
    parser.add_argument("--width", type=int, default=880, help="Canvas width")
    parser.add_argument("--padding", type=int, default=24, help="Canvas padding")
    args = parser.parse_args()

    font = CpfontFile.from_path(args.font)
    result = render_text(font, args.text, canvas_width=args.width, padding=args.padding)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    result.image.save(args.output, format="PNG", optimize=True)
    if result.missing_codepoints:
        missing = ", ".join(f"U+{value:04X}" for value in result.missing_codepoints)
        print(f"WARNING: replacement glyph used for {missing}")
    print(f"Wrote {args.output} ({result.image.width}x{result.image.height})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
