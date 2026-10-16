import tempfile
import unittest
from pathlib import Path

from fontTools.fontBuilder import FontBuilder
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib import TTFont

from patch_ttf import patch_ttf


def make_font(path, cmap, units=1000):
    builder = FontBuilder(units, isTTF=True)
    builder.setupGlyphOrder([".notdef", "space", "base", "composite"])
    builder.setupCharacterMap(cmap)
    pen = TTGlyphPen(None)
    pen.moveTo((40, 0))
    pen.lineTo((300, 700))
    pen.lineTo((560, 0))
    pen.closePath()
    glyphs = {".notdef": TTGlyphPen(None).glyph(), "space": TTGlyphPen(None).glyph(), "base": pen.glyph()}
    pen = TTGlyphPen(glyphs)
    pen.addComponent("base", (1, 0, 0, 1, 0, 0))
    glyphs["composite"] = pen.glyph()
    builder.setupGlyf(glyphs)
    builder.setupHorizontalMetrics({name: (600, 0 if name in ("space", ".notdef") else 40) for name in glyphs})
    builder.setupHorizontalHeader(ascent=800, descent=-200)
    builder.setupNameTable({"familyName": "Test", "styleName": "Regular"})
    builder.setupOS2()
    builder.setupPost(isFixedPitch=1)
    builder.save(path)


class PatchTTFTest(unittest.TestCase):
    def test_preserves_source_and_imports_wide_composite_symbols(self):
        with tempfile.TemporaryDirectory() as directory:
            source, first, second, output = [Path(directory) / name for name in ("source.ttf", "first.ttf", "second.ttf", "output.ttf")]
            make_font(source, {32: "space", 65: "base", 66: "composite"})
            make_font(first, {65: "base", 0xF101: "composite", 0xF102: "space"}, units=500)
            make_font(second, {0xF101: "composite", 0xF0001: "base"}, units=2000)
            patch_ttf(source, output, [first, second])
            with TTFont(source) as original, TTFont(output) as patched:
                self.assertEqual(patched["post"].isFixedPitch, 1)
                self.assertEqual(patched["name"].getDebugName(1), "Test Symbols")
                self.assertEqual(set(patched.getBestCmap()), {32, 65, 66, 0xF101, 0xF102, 0xF0001})
                for name in original.getGlyphOrder():
                    self.assertEqual(original["glyf"][name].compile(original["glyf"]), patched["glyf"][name].compile(patched["glyf"]))
                    self.assertEqual(original["hmtx"][name], patched["hmtx"][name])
                glyphs = patched.getGlyphSet()
                for codepoint, expected in [(0xF101, (80, 0, 1120, 1400)), (0xF102, None), (0xF0001, (170, 0, 430, 350))]:
                    name = patched.getBestCmap()[codepoint]
                    self.assertEqual(glyphs[name].width, 600)
                    self.assertFalse(patched["glyf"][name].isComposite())
                    pen = BoundsPen(glyphs)
                    glyphs[name].draw(pen)
                    self.assertEqual(pen.bounds, expected)


if __name__ == "__main__":
    unittest.main()
