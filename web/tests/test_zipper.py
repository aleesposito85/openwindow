"""Unit tests for web/zipper.py."""
import io
import pathlib
import sys
import unittest
import zipfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

import zipper  # noqa: E402

PARAMS = {"name": "my-window", "opening_w": 1800, "opening_h": 1500, "fix_gap": 8, "awning_h": 450, "glazing": "igu",
          "tier": 3, "screen": True, "bed": [256, 256, 256]}
OK = [{"name": "transom_deflection", "ok": True, "msg": "transom deflects 6.2 mm"},
      {"name": "bed_fit", "ok": True, "msg": "every part fits the 256 x 256 x 256 mm bed"}]
BAD = [{"name": "transom_deflection", "ok": False, "msg": "transom deflects 12.6 mm"}, OK[1]]


class ReadmeTest(unittest.TestCase):
    def testAllOkStartsWithTheWindow(self):
        text = zipper.readme("my-window", PARAMS, OK, [])
        self.assertTrue(text.startswith("OpenWindow: my-window\n\nOpening 1800 x 1500 mm, fixing gap 8 mm, awning 450 mm, "
                                        "glazing igu, tier 3, screen yes, bed 256 x 256 x 256 mm.\n"))
        self.assertNotIn("CHECKS FAILED", text)
        self.assertNotIn("PARTIAL", text)

    def testCheckLines(self):
        text = zipper.readme("my-window", PARAMS, BAD, [])
        self.assertIn("  FAIL  transom_deflection: transom deflects 12.6 mm\n", text)
        self.assertIn("  ok    bed_fit: every part fits the 256 x 256 x 256 mm bed\n", text)

    def testFailedChecksBlockComesFirst(self):
        text = zipper.readme("my-window", PARAMS, BAD, [])
        self.assertTrue(text.startswith("CHECKS FAILED — do not print\n\n  - transom_deflection: transom deflects 12.6 mm\n\n"))

    def testPartialBlockListsTheMissingParts(self):
        text = zipper.readme("my-window", PARAMS, OK, ["H", "JL"])
        self.assertTrue(text.startswith("PARTIAL ZIP — these parts are missing or failed their STL check and are not in "
                                        "stl/:\n\n  H, JL\n\nOpenWindow: my-window\n"))

    def testFailedChecksThenPartial(self):
        text = zipper.readme("my-window", PARAMS, BAD, ["H"])
        self.assertLess(text.index("CHECKS FAILED"), text.index("PARTIAL ZIP"))
        self.assertLess(text.index("PARTIAL ZIP"), text.index("OpenWindow: my-window"))

    def testMaterialFollowsTheTier(self):
        self.assertIn("Exterior parts: ASA-CF or PC-ABS (light colour) (tier 3). Interior parts: PETG.",
                      zipper.readme("my-window", PARAMS, OK, []))
        self.assertIn("Exterior parts: ASA (tier 2).", zipper.readme("my-window", dict(PARAMS, tier=2), OK, []))

    def testOldParamsFileWithoutNewKeys(self):
        old = {k: v for k, v in PARAMS.items() if k not in ("screen", "bed")}
        self.assertIn("screen yes, bed 256 x 256 x 256 mm.", zipper.readme("my-window", old, OK, []))

    def testScreenOffNote(self):
        text = zipper.readme("my-window", dict(PARAMS, screen=False), OK, [])
        self.assertIn("screen no,", text)
        self.assertTrue(text.endswith("  No screen: skip the screen steps in the build and install guides.\n"))

    def testPointsToTheGuides(self):
        text = zipper.readme("my-window", PARAMS, OK, [])
        self.assertIn("OpenWindow-Guide.pdf", text)
        self.assertIn("docs/printing.md, docs/build-guide.md, docs/install-guide.md, docs/user-manual.md", text)

    def testWeightLineWhenGiven(self):
        w = {"total_kg": 75.8, "kg_per_m2": 28.6, "glass_kg": 42.3, "core_kg": 6.2,
             "plastic_kg": 20.25, "hardware_kg": 7.1, "sash_kg": 15.7}
        text = zipper.readme("my-window", PARAMS, OK, [], w)
        self.assertIn("Weight estimate: about 75.8 kg all up (28.6 kg/m2)", text)
        self.assertIn("The sash alone is 15.7 kg", text)

    def testNoWeightLineWithoutTheArgument(self):
        self.assertNotIn("Weight estimate", zipper.readme("my-window", PARAMS, OK, []))


class BuildTest(unittest.TestCase):
    def testZipKeepsOrderAndContent(self):
        data = zipper.build({"README.txt": "CHECKS FAILED — do not print\n", "stl/H_x2.stl": b"\0\1\2"})
        z = zipfile.ZipFile(io.BytesIO(data))
        self.assertEqual(z.namelist(), ["README.txt", "stl/H_x2.stl"])
        self.assertEqual(z.read("stl/H_x2.stl"), b"\0\1\2")
        self.assertEqual(z.read("README.txt").decode("utf-8"), "CHECKS FAILED — do not print\n")
        self.assertEqual(z.getinfo("stl/H_x2.stl").compress_type, zipfile.ZIP_DEFLATED)


if __name__ == "__main__":
    unittest.main()
