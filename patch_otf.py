#!/usr/bin/env python3

import argparse
from pathlib import Path

from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.t2CharStringPen import T2CharStringPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont
from fontTools.ttLib.tables._c_m_a_p import CmapSubtable
from fontTools.varLib.builder import buildVarIdxMap

from rename_font import rename_font


def patch_otf(source: Path, output: Path, symbols: list[Path]) -> None:
    font = TTFont(source)
    cff2 = "CFF2" in font
    top = font["CFF2" if cff2 else "CFF "].cff.topDictIndex[0]
    charstrings = top.CharStrings
    glyph_order = font.getGlyphOrder()
    cmap = font.getBestCmap().copy()
    cid = hasattr(top, "ROS")
    private = top.FDArray[0].Private if hasattr(top, "FDArray") else top.Private
    next_cid = max(int(name[3:]) for name in glyph_order if name.startswith("cid")) + 1 if cid else 0
    cell = cmap.get(0x20, cmap.get(ord("M"))) if font["post"].isFixedPitch else None
    cell_width = font["hmtx"][cell][0] if cell else None
    if not cff2:
        top.isFixedPitch = font["post"].isFixedPitch
    if "HVAR" in font and font["HVAR"].table.AdvWidthMap is None:
        font["HVAR"].table.AdvWidthMap = buildVarIdxMap(range(len(glyph_order)), glyph_order)

    for path in symbols:
        with TTFont(path) as donor:
            glyphs = donor.getGlyphSet()
            scale = font["head"].unitsPerEm / donor["head"].unitsPerEm
            for codepoint, donor_name in donor.getBestCmap().items():
                if codepoint in cmap:
                    continue
                name = f"cid{next_cid:05d}" if cid else f"symbol{codepoint:06X}"
                next_cid += 1
                glyph_scale = scale
                offset = 0
                if cell_width:
                    bounds_pen = BoundsPen(glyphs)
                    glyphs[donor_name].draw(bounds_pen)
                    if bounds_pen.bounds:
                        left, _, right, _ = bounds_pen.bounds
                        glyph_width = max(right - left, glyphs[donor_name].width)
                        glyph_scale = min(scale, 2 * cell_width / glyph_width)
                        offset = (max(cell_width, glyph_width * glyph_scale) - (left + right) * glyph_scale) / 2
                width = cell_width or round(glyphs[donor_name].width * glyph_scale)
                pen = T2CharStringPen(None if cff2 else width - private.nominalWidthX, glyphs, CFF2=cff2)
                glyphs[donor_name].draw(TransformPen(pen, (glyph_scale, 0, 0, glyph_scale, offset, 0)))
                charstring = pen.getCharString(private=private, globalSubrs=top.GlobalSubrs)
                charstrings.charStrings[name] = len(charstrings.charStringsIndex)
                charstrings.charStringsIndex.append(charstring)
                if hasattr(top, "FDSelect"):
                    top.FDSelect.gidArray.append(0)
                glyph_order.append(name)
                cmap[codepoint] = name
                bounds = charstring.calcBounds(charstrings)
                font["hmtx"].metrics[name] = (width, round(bounds[0]) if bounds else 0)
                if "HVAR" in font:
                    hvar = font["HVAR"].table
                    hvar.AdvWidthMap.mapping[name] = hvar.AdvWidthMap.mapping[cell] if cell else 0xFFFFFFFF
                    for mapping in (hvar.LsbMap, hvar.RsbMap):
                        if mapping is not None:
                            mapping.mapping[name] = 0xFFFFFFFF

    top.charset = glyph_order
    if cid:
        top.CIDCount = next_cid
    font.setGlyphOrder(glyph_order)
    font["maxp"].numGlyphs = len(glyph_order)
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
    patch_otf(args.source, args.output, args.symbols)
