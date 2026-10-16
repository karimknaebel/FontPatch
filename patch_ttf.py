#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["fonttools==4.65.0"]
# ///

import argparse
from pathlib import Path

from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.recordingPen import DecomposingRecordingPen
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib import TTFont
from fontTools.ttLib.tables._c_m_a_p import CmapSubtable
from fontTools.varLib.instancer import instantiateVariableFont

from rename_font import rename_font


def patch_ttf(source: Path, output: Path, symbols: list[Path]) -> None:
    font = TTFont(source)
    if "fvar" in font:
        instantiateVariableFont(
            font, {axis.axisTag: axis.defaultValue for axis in font["fvar"].axes}, inplace=True,
        )

    glyph_order = font.getGlyphOrder()
    cmap = font.getBestCmap().copy()
    cell = cmap.get(0x20, cmap.get(ord("M"))) if font["post"].isFixedPitch else None
    cell_width = font["hmtx"][cell][0] if cell else None
    for path in symbols:
        with TTFont(path) as donor:
            glyphs = donor.getGlyphSet()
            scale = font["head"].unitsPerEm / donor["head"].unitsPerEm
            for codepoint, donor_name in donor.getBestCmap().items():
                if codepoint in cmap:
                    continue
                outline = DecomposingRecordingPen(glyphs)
                glyphs[donor_name].draw(outline)
                glyph_scale = scale
                offset = 0
                if cell_width:
                    bounds_pen = BoundsPen(None)
                    outline.replay(bounds_pen)
                    if bounds_pen.bounds:
                        left, _, right, _ = bounds_pen.bounds
                        glyph_width = max(right - left, glyphs[donor_name].width)
                        glyph_scale = min(scale, 2 * cell_width / glyph_width)
                        offset = (max(cell_width, glyph_width * glyph_scale) - (left + right) * glyph_scale) / 2
                pen = TTGlyphPen(None)
                outline.replay(TransformPen(pen, (glyph_scale, 0, 0, glyph_scale, offset, 0)))
                name = f"symbol{codepoint:06X}"
                font["glyf"].glyphs[name] = pen.glyph()
                font["glyf"][name].recalcBounds(font["glyf"])
                font["hmtx"].metrics[name] = (
                    cell_width or round(glyphs[donor_name].width * glyph_scale),
                    font["glyf"][name].xMin,
                )
                glyph_order.append(name)
                cmap[codepoint] = name

    font.setGlyphOrder(glyph_order)
    for table in font["cmap"].tables:
        if table.isUnicode() and table.format in (4, 12):
            table.cmap = {c: n for c, n in cmap.items() if table.format == 12 or c <= 0xFFFF}
    if not any(table.format == 12 for table in font["cmap"].tables):
        table = CmapSubtable.newSubtable(12)
        table.platformID, table.platEncID, table.language = 3, 10, 0
        table.cmap = cmap
        font["cmap"].tables.append(table)
    font.save(output)
    font.close()
    rename_font(source, output)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("symbols", type=Path, nargs="+")
    args = parser.parse_args()
    patch_ttf(args.source, args.output, args.symbols)
