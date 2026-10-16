import tempfile
import unittest
from pathlib import Path

from fontTools.cffLib.CFFToCFF2 import convertCFFToCFF2
from fontTools.fontBuilder import FontBuilder
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.t2CharStringPen import T2CharStringPen
from fontTools.ttLib import TTFont

from patch_otf import patch_otf


def make_font(path, cmap, units=1000):
    builder = FontBuilder(units, isTTF=False)
    builder.setupGlyphOrder([".notdef", *cmap.values()])
    builder.setupCharacterMap(cmap)
    charstrings = {".notdef": T2CharStringPen(600, None).getCharString()}
    for name in cmap.values():
        pen = T2CharStringPen(600, None)
        pen.moveTo((40, 0))
        pen.lineTo((300, 700))
        pen.lineTo((560, 0))
        pen.closePath()
        charstrings[name] = pen.getCharString()
    builder.setupCFF("Test-Regular", {}, charstrings, {})
    builder.setupHorizontalMetrics({name: (600, 40) for name in charstrings})
    builder.setupHorizontalHeader(ascent=800, descent=-200)
    builder.setupNameTable({"familyName": "Test", "styleName": "Regular"})
    builder.setupOS2()
    builder.setupPost()
    builder.save(path)


class PatchOTFTest(unittest.TestCase):
    def test_preserves_variable_axes_and_monospaced_symbols(self):
        with tempfile.TemporaryDirectory() as directory:
            source, donor, output = [Path(directory) / name for name in ("source.otf", "donor.otf", "output.otf")]
            make_font(source, {32: "space", 65: "A"})
            make_font(donor, {0xF101: "icon"}, units=500)
            with TTFont(source) as font:
                font["post"].isFixedPitch = 1
                convertCFFToCFF2(font)
                FontBuilder(font=font).setupFvar(
                    [("wght", 100, 400, 900, "Weight")],
                    [{"location": {"wght": 400}, "stylename": "Regular"}],
                )
                font.save(source)
            patch_otf(source, output, [donor])
            with TTFont(source) as original, TTFont(output) as patched:
                self.assertIn("CFF2", patched)
                self.assertEqual(original.getTableData("fvar"), patched.getTableData("fvar"))
                self.assertEqual(patched["post"].isFixedPitch, 1)
                self.assertEqual(patched["hmtx"][patched.getBestCmap()[0xF101]][0], 600)
                bounds = BoundsPen(patched.getGlyphSet())
                patched.getGlyphSet()[patched.getBestCmap()[0xF101]].draw(bounds)
                self.assertEqual(bounds.bounds, (80, 0, 1120, 1400))
                self.assertEqual(patched["name"].getDebugName(25), "TestSymbols")

    def test_static_monospaced_cff_flag(self):
        with tempfile.TemporaryDirectory() as directory:
            source, output = Path(directory) / "source.otf", Path(directory) / "output.otf"
            make_font(source, {32: "space", 65: "A"})
            with TTFont(source) as font:
                font["post"].isFixedPitch = 1
                font.save(source)
            patch_otf(source, output, [])
            with TTFont(output) as font:
                self.assertEqual(font["CFF "].cff.topDictIndex[0].isFixedPitch, 1)

    def test_preserves_source_and_merges_symbols_in_order(self):
        with tempfile.TemporaryDirectory() as directory:
            source, first, second, output = [
                Path(directory) / name for name in ("source.otf", "first.otf", "second.otf", "output.otf")
            ]
            make_font(source, {65: "A"})
            make_font(first, {65: "A", 0xF101: "icon"}, units=2000)
            make_font(second, {0xF101: "other", 0xF0001: "supplementary"})
            patch_otf(source, output, [first, second])
            with TTFont(source) as original, TTFont(output) as patched:
                self.assertEqual(set(patched.getBestCmap()), {65, 0xF101, 0xF0001})
                before, after = RecordingPen(), RecordingPen()
                original.getGlyphSet()["A"].draw(before)
                patched.getGlyphSet()["A"].draw(after)
                self.assertEqual(before.value, after.value)
                self.assertEqual(original["hmtx"]["A"], patched["hmtx"]["A"])
                self.assertEqual(patched["hmtx"][patched.getBestCmap()[0xF101]][0], 300)
                self.assertEqual(patched["hmtx"][patched.getBestCmap()[0xF0001]][0], 600)
                self.assertEqual(patched["name"].getDebugName(1), "Test Symbols")


if __name__ == "__main__":
    unittest.main()
