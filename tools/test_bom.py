"""Unit tests for bom/build_bom.py."""
import csv
import importlib.util
import json
import pathlib
import tempfile
import unittest

import generate
import window

ROOT = pathlib.Path(__file__).resolve().parent.parent
SCREEN_FIXINGS = {
    "Self-tapping screw 8g x 12 stainless, countersunk (screen tube screws)",
    "M4 x 10 pan or button head machine screw (hinge frame leaves HG)",
    "M4 x 50 bolt + nyloc nut (hinge pins)",
    "4g x 12 self-tapping screw (screen leaves HS)",
}
SCREEN_ITEMS = SCREEN_FIXINGS | {
    "Flexible magnetic strip A, 12.7 mm, adhesive-backed (screen back channel)",
    "Flexible magnetic strip B, 12.7 mm, adhesive-backed, matched to A, or adhesive steel strip (frame magnet channel)",
    "Fibreglass insect mesh",
    "Screen spline, 4 mm",
    "Two-part epoxy, 5-minute (screen corner joints)",
    "Tube alu10 (total length; buy in 1 m/3 m stock)",
}
spec = importlib.util.spec_from_file_location("build_bom", ROOT / "bom" / "build_bom.py")
build_bom = importlib.util.module_from_spec(spec)
spec.loader.exec_module(build_bom)


def load(name):
    return window.layout(json.loads((ROOT / "params" / f"{name}.json").read_text()))


class BomCase(unittest.TestCase):
    name = None

    def setUp(self):
        self.lay = load(self.name)
        self.items = {i["item"]: i for i in build_bom.hardware(self.lay, generate.parts(self.lay))}

    def qty(self, key):
        found = [i["qty"] for k, i in self.items.items() if k.startswith(key)]
        self.assertEqual(len(found), 1, f"{key}: {len(found)} matching lines")
        return found[0]


class HomeBomTest(BomCase):
    name = "home-1800x1500"

    def testFixingScrews(self):
        self.assertEqual(self.qty("Timber screw 10g x 75"), 38)

    def testAluminiumTubeScrews(self):
        self.assertEqual(self.qty("Self-tapping screw 8g x 30"), 62)

    def testSteelTransomTubeScrewsAreTek(self):
        self.assertEqual(self.qty("Tek screw 8g x 25"), 9)

    def testScreenTubeScrews(self):
        self.assertEqual(self.qty("Self-tapping screw 8g x 12"), 26)

    def testInserts(self):
        self.assertEqual(self.qty("M4 heat-set insert for a 5.6 x 8 mm hole"), 30)

    def testM4ScrewLengthsSuitTheBlindInsertHoles(self):
        self.assertEqual(self.qty("M4 x 10 countersunk"), 8)
        self.assertEqual(self.qty("M4 x 10 pan"), 6)
        self.assertEqual(self.qty("M4 x 8 pan"), 2)
        self.assertEqual(self.qty("M4 x 16 countersunk"), 4)

    def testHingePinsSpanTheKnuckleStack(self):
        self.assertEqual(self.qty("M4 x 50 bolt"), 3)

    def testPackers(self):
        self.assertEqual(self.qty("Plastic window packers"), 44)

    def testFrictionStayScrews(self):
        self.assertEqual(self.qty("Friction-stay screw 8g x 25"), 8)
        self.assertEqual(self.qty("Friction-stay screw 8g x 16"), 6)

    def testSashSealLoops(self):
        self.assertEqual(self.qty("EPDM bulb kerf seal"), 8.92)

    def testJointCord(self):
        self.assertEqual(self.qty("Closed-cell foam cord, 4 mm"), 11.3)
        self.assertEqual(self.qty("Closed-cell foam cord, 3 mm"), 0.14)

    def testSealantCartridges(self):
        self.assertEqual(self.qty("MS-polymer sealant"), 3)

    def testSillTrayTapeIsWideEnough(self):
        self.assertEqual(self.qty("Butyl flashing tape, 150 mm"), 2.08)

    def testAdhesives(self):
        self.assertEqual(self.qty("Two-part epoxy"), 1)
        self.assertEqual(self.qty("Gel CA glue"), 1)

    def testMagneticStripPair(self):
        self.assertEqual(self.qty("Flexible magnetic strip A"), 4.53)
        self.assertEqual(self.qty("Flexible magnetic strip B"), 4.53)

    def testStayPair(self):
        stay = next(k for k in self.items if k.startswith("Stainless friction stay"))
        self.assertIn("400 mm", stay)
        self.assertIn("stack <= 13 mm", stay)
        self.assertIn("track/arm width <= 14 mm", stay)

    def testSealantIsMovementRated(self):
        self.assertIn("50%", next(k for k in self.items if k.startswith("MS-polymer sealant")))

    def testTubeMetresByCore(self):
        self.assertEqual(self.qty("Tube steel40x20"), 1.7)
        self.assertEqual(self.qty("Tube alu10"), 4.37)

    def testNoAcrylicItemsForIgu(self):
        self.assertFalse([k for k in self.items if "esiccant" in k])


class BenchBomTest(BomCase):
    name = "bench-600"

    def testScrewCounts(self):
        self.assertEqual(self.qty("Timber screw 10g x 75"), 20)
        self.assertEqual(self.qty("Self-tapping screw 8g x 30"), 32)
        self.assertEqual(self.qty("Tek screw 8g x 25"), 4)
        self.assertEqual(self.qty("Self-tapping screw 8g x 12"), 8)

    def testPackers(self):
        self.assertEqual(self.qty("Plastic window packers"), 26)

    def testInserts(self):
        self.assertEqual(self.qty("M4 heat-set insert"), 20)

    def testSealsAndSealant(self):
        self.assertEqual(self.qty("EPDM bulb kerf seal"), 2.94)
        self.assertEqual(self.qty("Closed-cell foam cord, 4 mm"), 4.9)
        self.assertEqual(self.qty("MS-polymer sealant"), 2)

    def testOnlyTheTwoSegmentScreenRailsGetTubes(self):
        self.assertEqual(self.qty("Tube alu10"), 0.97)


class WriteTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.out = pathlib.Path(self.tmp.name)
        lay = load("home-1800x1500")
        parts = generate.parts(lay)
        build_bom.write("home-1800x1500", lay, parts, build_bom.hardware(lay, parts), [], self.out)

    def tearDown(self):
        self.tmp.cleanup()

    def rows(self, f):
        return list(csv.DictReader((self.out / f).read_text().splitlines()))

    def testCutlistIsWrittenPerName(self):
        rows = {r["member"]: r for r in self.rows("home-1800x1500-cutlist.csv")}
        self.assertEqual(float(rows["transom"]["length_mm"]), 1696.0)

    def testGlassIsWrittenPerName(self):
        rows = {r["pane"]: r for r in self.rows("home-1800x1500-glass.csv")}
        self.assertEqual((rows["fixed"]["width_mm"], rows["fixed"]["height_mm"]), ("1698", "878"))

    def testPartsAreWrittenPerName(self):
        rows = {r["id"]: r for r in self.rows("home-1800x1500-parts.csv")}
        self.assertEqual(rows["H"]["qty"], "7")

    def testMarkdownCarriesCutlistAndGlass(self):
        text = (self.out / "home-1800x1500.md").read_text()
        self.assertIn("| transom | steel40x20 | 1696.0 | 1 |", text)
        self.assertIn("| fixed | igu | 1698 | 878 | 1 |", text)


class MassTest(unittest.TestCase):
    def testSolidSmallPartIsAllShell(self):
        self.assertAlmostEqual(build_bom.mass_g(1.0, 6.0, 1.27), 1.27, places=3)

    def testLargePartUsesInfill(self):
        self.assertAlmostEqual(build_bom.mass_g(100.0, 100.0, 1.0), 21.0 + 79.0 * 0.15, places=3)


class ScreenOffBomTest(unittest.TestCase):
    def setUp(self):
        on = load("bench-600")
        off = window.layout(dict(on["params"], screen=False))
        self.on = {i["item"]: i for i in build_bom.hardware(on, generate.parts(on))}
        self.off = {i["item"]: i for i in build_bom.hardware(off, generate.parts(off))}

    def testScreenGroupIsOmitted(self):
        self.assertFalse([i for i in self.off.values() if i["group"] == "Screen"])

    def testScreenFixingsAreOmitted(self):
        self.assertEqual(SCREEN_FIXINGS & set(self.on), SCREEN_FIXINGS)
        self.assertFalse(SCREEN_FIXINGS & set(self.off))

    def testHeadInsertPairsAreOmitted(self):
        self.assertEqual(self.off["M4 heat-set insert for a 5.6 x 8 mm hole"]["qty"], 16)

    def testScreenTubeIsOmitted(self):
        self.assertFalse([k for k in self.off if k.startswith("Tube alu10")])

    def testEverythingElseIsUnchanged(self):
        dropped = {k for k in self.on if k not in self.off}
        self.assertEqual(len(dropped), 10)
        for k, item in self.off.items():
            if not k.startswith("M4 heat-set insert"):
                self.assertEqual(item, self.on[k], k)


def items(lay):
    return {i["item"]: i for i in build_bom.hardware(lay, generate.parts(lay))}


class HomeScreenOffBomTest(unittest.TestCase):
    def setUp(self):
        on = load("home-1800x1500")
        self.on = items(on)
        self.off = items(window.layout(dict(on["params"], screen=False)))

    def testExactlyTheScreenItemsAreDropped(self):
        self.assertEqual(set(self.on) - set(self.off), SCREEN_ITEMS)
        self.assertEqual(set(self.off) - set(self.on), set())

    def testAllSevenHeadInsertPairsAreOmitted(self):
        self.assertEqual(self.on["M4 heat-set insert for a 5.6 x 8 mm hole"]["qty"], 30)
        self.assertEqual(self.off["M4 heat-set insert for a 5.6 x 8 mm hole"]["qty"], 16)

    def testEverythingElseIsUnchanged(self):
        for k, item in self.off.items():
            if not k.startswith("M4 heat-set insert"):
                self.assertEqual(item, self.on[k], k)

    def testItemOrderIsKept(self):
        self.assertEqual(list(self.off), [k for k in self.on if k in self.off])


class BenchScreenItemsTest(unittest.TestCase):
    def testExactlyTheScreenItemsAreDropped(self):
        on = load("bench-600")
        self.assertEqual(set(items(on)) - set(items(window.layout(dict(on["params"], screen=False)))), SCREEN_ITEMS)


class BigBedHingeBomTest(unittest.TestCase):
    def testEveryHingeScrewHasAHeadInsert(self):
        for w in (1080, 1090, 1100):
            lay = window.layout(dict(load("home-1800x1500")["params"], opening_w=w, bed=[500, 500, 500]))
            q = {p["id"]: p["qty"] for p in generate.parts(lay)}
            got = items(lay)
            self.assertEqual(got["M4 x 10 pan or button head machine screw (hinge frame leaves HG)"]["qty"], 6, w)
            self.assertGreaterEqual(2 * q["H"], 6, w)
            self.assertEqual(got["M4 heat-set insert for a 5.6 x 8 mm hole"]["qty"],
                             2 * (q["H"] + q["TE"]) + 4 * q["SBE"] + q["CMB"] + 2 * q["TC"], w)


class ScreenOffWriteTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.out = pathlib.Path(self.tmp.name)
        lay = window.layout(dict(load("home-1800x1500")["params"], screen=False))
        parts = generate.parts(lay)
        build_bom.write("home-off", lay, parts, build_bom.hardware(lay, parts), [], self.out)

    def tearDown(self):
        self.tmp.cleanup()

    def rows(self, f):
        return list(csv.DictReader((self.out / f).read_text().splitlines()))

    def testCsvHasNoScreenItems(self):
        got = {r["item"] for r in self.rows("home-off.csv")}
        self.assertFalse(got & SCREEN_ITEMS)
        self.assertNotIn("Screen", {r["group"] for r in self.rows("home-off.csv")})

    def testMarkdownHasNoScreenRowsOrTubes(self):
        text = (self.out / "home-off.md").read_text()
        self.assertNotIn("| Screen |", text)
        self.assertNotIn("alu10", text)
        self.assertNotIn("screen_horizontal", text)

    def testPartsAndCutlistHaveNoScreenEntries(self):
        self.assertFalse({r["id"] for r in self.rows("home-off-parts.csv")} & {"NH", "NV", "CN", "HG", "HS"})
        self.assertNotIn("alu10", {r["core"] for r in self.rows("home-off-cutlist.csv")})
        self.assertEqual(next(r for r in self.rows("home-off-parts.csv") if r["id"] == "H")["call"],
                         'frame_segment("sash_rebate", 237.14, "H", bosses=false);')


class TwoBayBomTest(BomCase):
    name = "home-1800x1500-2bay"

    def testFixingsAndTubeScrews(self):
        self.assertEqual(self.qty("Timber screw 10g x 75"), 44)
        self.assertEqual(self.qty("Self-tapping screw 8g x 30"), 76)
        self.assertEqual(self.qty("Tek screw 8g x 25, 410 stainless, countersunk (steel transom and mullion tubes"), 21)

    def testLockScrewsForTheTransomAndEveryMullionShoe(self):
        self.assertEqual(self.qty("M4 x 16 countersunk machine screw (transom and mullion lock screws)"), 12)

    def testInsertsAndCamScrewsScaleWithTheBays(self):
        self.assertEqual(self.qty("M4 heat-set insert"), 46)
        self.assertEqual(self.qty("M4 x 10 countersunk"), 16)
        self.assertEqual(self.qty("M4 x 8 pan"), 4)

    def testPackersIncludeOneUnderEachSillNode(self):
        self.assertEqual(self.qty("Plastic window packers"), 53)

    def testOneStayPairPerSash(self):
        stay = next(i for k, i in self.items.items() if k.startswith("Stainless friction stay"))
        self.assertEqual((stay["qty"], stay["unit"]), (2, "pair"))
        self.assertIn("check rating >= 7.6 kg", stay["item"])

    def testStayScrewsOnTheJambsAndTheMullion(self):
        self.assertEqual(self.qty("Friction-stay screw 8g x 25"), 8)
        self.assertEqual(self.qty("Tek screw 8g x 16, 410 stainless, countersunk (friction-stay tracks to upper mullions"), 8)
        self.assertEqual(self.qty("Friction-stay screw 8g x 16"), 12)

    def testSealsScaleWithTheBays(self):
        self.assertEqual(self.qty("EPDM bulb kerf seal, 3 mm kerf (outer + inner loop round each sash opening)"), 10.67)
        self.assertEqual(self.qty("EPDM glazing wedge gasket"), 22.66)
        self.assertEqual(self.qty("Closed-cell foam cord, 4 mm"), 14.9)
        self.assertEqual(self.qty("Closed-cell foam cord, 3 mm (transom and mullion shoe seams)"), 0.42)
        self.assertEqual(self.qty("MS-polymer sealant"), 4)

    def testScreenPerBay(self):
        self.assertEqual(self.qty("Flexible magnetic strip A"), 5.58)
        self.assertEqual(self.qty("Fibreglass insect mesh"), 1.02)

    def testSteelForTheMullions(self):
        self.assertEqual(self.qty("Tube steel40x20"), 3.05)
        self.assertEqual(self.qty("Tube alu20"), 10.86)

    def testGlassPerBay(self):
        self.assertEqual(self.qty("IGU 4/16/4 = 24 mm, toughened if required by AS 1288, low-E/argon optional, 829 x 878"), 2)
        self.assertEqual(self.qty("IGU 4/16/4 = 24 mm, toughened if required by AS 1288, low-E/argon optional, 737 x 388"), 2)


class OneBayBomTest(unittest.TestCase):
    def testExplicitOneBayIsTheSameBom(self):
        home = load("home-1800x1500")
        self.assertEqual(items(window.layout(dict(home["params"], bays=1))), items(home))

    def testMullionLinesOnlyWithBays(self):
        self.assertFalse([k for k in items(load("home-1800x1500")) if "mullion" in k])


class TwoBayWriteTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.out = pathlib.Path(self.tmp.name)
        lay = load("home-1800x1500-2bay")
        parts = generate.parts(lay)
        build_bom.write("two", lay, parts, build_bom.hardware(lay, parts), [], self.out)

    def tearDown(self):
        self.tmp.cleanup()

    def testMarkdownGlassTableCountsThePanes(self):
        text = (self.out / "two.md").read_text()
        self.assertIn("| fixed | igu | 829 | 878 | 2 |", text)
        self.assertIn("| mullion_lower | steel40x20 | 876.0 | 1 |", text)

    def testMarkdownListsTheMullionCentres(self):
        self.assertIn("## Bays\n\n2 bays, 869 mm apart. Mullion centre lines, from the frame's left outer edge as seen "
                      "from outside: 892 mm.\n", (self.out / "two.md").read_text())


class SandwichBomTest(unittest.TestCase):
    def sheets(self, lay):
        parts = generate.parts(lay)
        return [i for i in build_bom.hardware(lay, parts) if i["item"].startswith("Acrylic ")]

    def testDefaultSheetsAreFourMillimetre(self):
        rows = self.sheets(load("bench-600"))
        self.assertTrue(rows and all(r["item"].startswith("Acrylic 4 mm, ") for r in rows))

    def testThinSheetsNameTheirThickness(self):
        lay = window.layout({**json.loads((ROOT / "params" / "bench-600.json").read_text()), "acrylic_t": 3, "acrylic_gap": 12})
        rows = self.sheets(lay)
        self.assertEqual([r["item"].split(",")[0] for r in rows], ["Acrylic 3 mm", "Acrylic 3 mm"])
        self.assertEqual([r["qty"] for r in rows], [2, 2])


def vslotLoad(name, **changes):
    return window.layout({**json.loads((ROOT / "params" / f"{name}.json").read_text()), "core": "vslot", **changes})


class VslotBomTest(unittest.TestCase):
    def qty(self, lay):
        return {i["item"]: i["qty"] for i in build_bom.hardware(lay, generate.parts(lay))}

    def screws(self, lay):
        return sum(n for n in build_bom.tube_screws(lay, {p["id"]: p["qty"] for p in generate.parts(lay)}).values())

    def testTubeScrewTotalIsUnchanged(self):
        for name in ("bench-600", "home-1800x1500", "home-1800x1500-2bay"):
            self.assertEqual(self.screws(vslotLoad(name)), self.screws(load(name)), name)

    def testDefaultCountsMatchTheOldRule(self):
        q = self.qty(load("home-1800x1500"))
        self.assertEqual(q["Self-tapping screw 8g x 30 stainless, countersunk (aluminium tube screws: frame, sash, corners, nodes)"], 62)
        self.assertEqual(q["Tek screw 8g x 25, 410 stainless, countersunk (steel transom tube: T, TE, shoes)"], 9)

    def testHomeScrewLines(self):
        q = self.qty(vslotLoad("home-1800x1500"))
        self.assertEqual(q["M5 x 25 countersunk machine screw, stainless (V-slot tube screws, one T-nut each)"], 36)
        self.assertEqual(q["M5 x 20 countersunk machine screw, stainless (V-slot tube screws, one T-nut each)"], 8)
        self.assertEqual(q["M5 slide-in T-nut for 20-series V-slot, 6 mm slot (V-slot tube screws)"], 44)
        self.assertEqual(q["Self-tapping screw 8g x 30 stainless, countersunk (aluminium tube screws: frame, sash, corners, nodes)"], 18)
        self.assertEqual(q["Tek screw 8g x 25, 410 stainless, countersunk (steel tubes: transom)"], 9)
        self.assertEqual(q["V-slot 2020, 4-slot, 1000 mm pieces (cut plan in the BOM)"], 8)
        self.assertEqual(q["Tube alu20 (total length; buy in 1 m/3 m stock)"], 3.23)

    def testBenchHasShoulderScrewsAndNoEmptyLines(self):
        q = self.qty(vslotLoad("bench-600"))
        self.assertEqual(q["Self-tapping screw 8g x 20 stainless, countersunk (V-slot transom pair: T, TE, TX, shoes; 3.5 mm pilot)"], 4)
        self.assertFalse([k for k, v in q.items() if v == 0])
        self.assertFalse([k for k in q if k.startswith("Tube alu20") or k.startswith("Tek screw 8g x 25")])

    def testVslotMullionStaysTakeSelfTappers(self):
        q = self.qty(vslotLoad("home-1800x1500-2bay"))
        self.assertEqual(q["Self-tapping screw 8g x 16 stainless, countersunk (friction-stay tracks to upper mullions, 3.5 mm pilot; "
                           "match the stay's holes)"], 8)

    def testMarkdownHasThePlanJoinsAndFallbacks(self):
        lay = vslotLoad("home-1800x1500")
        parts = generate.parts(lay)
        with tempfile.TemporaryDirectory() as d:
            build_bom.write("vhome", lay, parts, build_bom.hardware(lay, parts), [], d)
            text = (pathlib.Path(d) / "vhome.md").read_text()
        for needle in ("## V-slot cut plan", "8 pieces of 1000 mm V-slot 2020, with 2 mm per saw cut.", "| 1 | jamb_lower 943 | 57 |",
                       "| 7 | jamb_upper 475, jamb_upper 475 | 48 |", "- head: 919.8 mm, inside segment 4",
                       "## Standard tubes in this V-slot window", "- alu20 sash_horizontal: 1615 mm is longer than the 1000 mm V-slot pieces"):
            self.assertIn(needle, text)


if __name__ == "__main__":
    unittest.main()
