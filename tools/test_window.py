"""Unit tests for tools/window.py."""
import json
import pathlib
import unittest
from unittest import mock

import window

ROOT = pathlib.Path(__file__).resolve().parent.parent


def load(name):
    return json.loads((ROOT / "params" / name).read_text())


class SplitTest(unittest.TestCase):
    def testSplitEvenlyBelowMax(self):
        self.assertEqual(window.split(1658), (7, 236.86))

    def testSplitExactlyMaxIsOneSegment(self):
        self.assertEqual(window.split(240), (1, 240.0))

    def testSplitJustOverMaxIsTwoSegments(self):
        self.assertEqual(window.split(241), (2, 120.5))

    def testSplitRejectsNonPositive(self):
        with self.assertRaises(ValueError):
            window.split(0)

    def testSplitWithJointGapLeavesOneGapPerJoint(self):
        self.assertEqual(window.split(1668, 1.0), (7, 237.14))

    def testSplitRejectsLengthWithinTheJointGaps(self):
        for length in (0.5, 1.0, 2.0):
            with self.assertRaises(ValueError):
                window.split(length, 1.0)

    def testSplitWithJointGapUsesFewestSegments(self):
        self.assertEqual(window.split(481), (3, 160.33))
        self.assertEqual(window.split(481, 1.0), (2, 239.0))


class StructureTest(unittest.TestCase):
    def testSteelTransomInertia(self):
        self.assertAlmostEqual(window.inertia("steel50x25"), 74202.5, delta=1.0)

    def testSlimSteelTransomInertia(self):
        self.assertAlmostEqual(window.inertia("steel40x20"), 36896.2, delta=1.0)

    def testSteelTransomDeflection(self):
        self.assertAlmostEqual(window.deflection("steel50x25", 1658, 644), 2.99, delta=0.05)

    def testAluminiumDeflectsMoreBySteelModulusRatio(self):
        alu = window.deflection("alu50x25", 1658, 644)
        steel = window.deflection("steel50x25", 1658, 644)
        self.assertAlmostEqual(alu / steel, 200000 / 69000, delta=0.01)


class LayoutTest(unittest.TestCase):
    def setUp(self):
        self.lay = window.layout(load("home-1800x1500.json"))

    def member(self, name):
        return next(m for m in self.lay["members"] if m["name"] == name)

    def testHeadIsSplitIntoSevenSegments(self):
        head = self.member("head")
        self.assertEqual((head["length"], head["n"], head["seg"]), (1668, 7, 237.14))
        self.assertEqual(head["profile"], "sash_rebate")

    def testLowerJambUsesGlazingProfile(self):
        jamb = self.member("jamb_lower")
        self.assertEqual((jamb["length"], jamb["n"], jamb["seg"], jamb["qty"]), (848, 4, 210.75, 2))
        self.assertEqual(jamb["profile"], "glazing")

    def testUpperJambMatchesAwningHeight(self):
        jamb = self.member("jamb_upper")
        self.assertEqual((jamb["length"], jamb["n"], jamb["seg"]), (450, 2, 223.5))

    def testTransomIsSteel(self):
        self.assertEqual(self.member("transom")["core"], "steel40x20")

    def testFixedGlassSize(self):
        self.assertEqual(self.lay["glass"]["fixed"], (1698, 878))

    def testSashOuterAndGlassSize(self):
        self.assertEqual(self.lay["sash"], (1678, 460))
        self.assertEqual(self.lay["glass"]["sash"], (1606, 388))

    def testSashMembers(self):
        self.assertEqual(self.member("sash_horizontal")["n"], 7)
        self.assertEqual(self.member("sash_vertical")["seg"], 177.5)

    def testScreenSpansFromHeadToTransomMagnetStrip(self):
        self.assertEqual(self.lay["screen"], (1724, 540))

    def testEveryMultiSegmentScreenRailGetsACore(self):
        self.assertEqual(self.member("screen_horizontal")["core"], "alu10")
        self.assertEqual(self.member("screen_vertical")["core"], "alu10")

    def testCordJointedMembersLeaveAGapAtEveryJoint(self):
        for name in ("head", "sill", "jamb_lower", "jamb_upper", "transom", "sash_horizontal", "sash_vertical"):
            m = self.member(name)
            self.assertAlmostEqual(m["n"] * m["seg"] + (m["n"] + 1) * 1.0, m["length"], delta=0.05, msg=name)

    def testScreenRailsCloseTight(self):
        for name in ("screen_horizontal", "screen_vertical"):
            m = self.member(name)
            self.assertAlmostEqual(m["n"] * m["seg"], m["length"], delta=0.05, msg=name)

    def testEverySegmentFitsTheBed(self):
        for m in self.lay["members"]:
            self.assertLessEqual(m["seg"], 240.0, m["name"])

    def testTubeCutsIncludeSockets(self):
        tubes = {t["member"]: t for t in self.lay["tubes"]}
        self.assertEqual(tubes["head"]["length"], 1668 + 2 * (28 - 1.5))
        self.assertEqual(tubes["jamb"]["length"], 1484 - 2 * 58 + 2 * (28 - 1.5))
        self.assertEqual(tubes["transom"]["length"], 1668 + 2 * 18 - 2 * 4)

    def testSashAndScreenTubesUseTheirOwnSocketDepth(self):
        tubes = {t["member"]: t for t in self.lay["tubes"]}
        self.assertEqual(tubes["sash_horizontal"]["length"], 1678 - 2 * 51 + 2 * (21 - 1.5))
        self.assertEqual(tubes["screen_horizontal"]["length"], 1724 - 2 * 30 + 2 * (12 - 1.5))
        self.assertEqual(tubes["screen_vertical"]["length"], 540 - 2 * 30 + 2 * (12 - 1.5))

    def testEveryTubeStopsShortOfItsSocketFloors(self):
        sock = {"head": 28, "sill": 28, "jamb": 28, "sash_horizontal": 21, "sash_vertical": 21,
                "screen_horizontal": 12, "screen_vertical": 12}
        spans = {"head": 1668, "sill": 1668, "jamb": 1484 - 2 * 58, "sash_horizontal": 1678 - 2 * 51,
                 "sash_vertical": 460 - 2 * 51, "screen_horizontal": 1724 - 2 * 30, "screen_vertical": 540 - 2 * 30}
        for t in self.lay["tubes"]:
            if t["member"] in sock:
                self.assertLessEqual(t["length"], spans[t["member"]] + 2 * sock[t["member"]] - 3, t["member"])

    def testAllChecksPassForHome(self):
        failed = [c for c in self.lay["checks"] if not c["ok"]]
        self.assertEqual(failed, [])

    def testKeeperBossOffsetPutsKeeperOverCam(self):
        self.assertEqual(self.lay["keeper_dz"], 39.43)
        checks = {c["name"]: c for c in self.lay["checks"]}
        self.assertTrue(checks["cam_keeper"]["ok"])

    def testStayIsChosenFromSashHeight(self):
        self.assertEqual(self.lay["stay"], 400)


class ValidationTest(unittest.TestCase):
    def testRejectsAwningTooSmall(self):
        p = load("home-1800x1500.json")
        p["awning_h"] = 100
        with self.assertRaises(ValueError):
            window.layout(p)

    def testRejectsUnknownGlazing(self):
        p = load("home-1800x1500.json")
        p["glazing"] = "glass"
        with self.assertRaises(ValueError):
            window.layout(p)

    def testFailedCheckIsReportedNotRaised(self):
        p = load("home-1800x1500.json")
        p["opening_w"] = 3200
        checks = {c["name"]: c for c in window.layout(p)["checks"]}
        self.assertFalse(checks["transom_deflection"]["ok"])


class BenchTest(unittest.TestCase):
    def testBenchLayout(self):
        lay = window.layout(load("bench-600.json"))
        head = next(m for m in lay["members"] if m["name"] == "head")
        self.assertEqual((head["length"], head["n"]), (468, 2))

    def testBenchKeeperBossOffset(self):
        self.assertEqual(window.layout(load("bench-600.json"))["keeper_dz"], 23.0)

    def testSingleSegmentScreenRailHasNoCore(self):
        lay = window.layout(load("bench-600.json"))
        cores = {m["name"]: (m["n"], m["core"]) for m in lay["members"] if m["name"].startswith("screen")}
        self.assertEqual(cores, {"screen_horizontal": (2, "alu10"), "screen_vertical": (1, None)})

    def testBenchGetsGenericStayAndPasses(self):
        lay = window.layout(load("bench-600.json"))
        self.assertEqual(lay["stay"], 200)
        checks = {c["name"]: c for c in lay["checks"]}
        self.assertTrue(checks["sash_weight"]["ok"])


class CamKeeperLimitTest(unittest.TestCase):
    def testKeeperOffsetLimitsFollowTheSashSegment(self):
        self.assertAlmostEqual(window.keeper_dz_min(), 12 + 4.3 + 2.8 + 1.5)
        self.assertAlmostEqual(window.keeper_dz_max(186.5), 186.5 / 2 - 4 - 1.5 - 2.8 - 12)

    def testOffsetBeyondTheSashSegmentFailsCheck(self):
        p = load("bench-600.json")
        p["opening_w"] = 400
        lay = window.layout(p)
        seg = next(m["seg"] for m in lay["members"] if m["name"] == "sash_horizontal")
        self.assertGreater(lay["keeper_dz"], window.keeper_dz_max(seg))
        checks = {c["name"]: c for c in lay["checks"]}
        self.assertFalse(checks["cam_keeper"]["ok"])


class StaySelectionTest(unittest.TestCase):
    def setUp(self):
        self.originalStays = window.STAYS[:]

    def tearDown(self):
        window.STAYS[:] = self.originalStays

    def testHeavySashSkipsTooLightStay(self):
        window.STAYS[:] = [(160, 1.0), (205, 100.0)]
        lay = window.layout(load("bench-600.json"))
        self.assertEqual(lay["stay"], 205)
        checks = {c["name"]: c for c in lay["checks"]}
        self.assertTrue(checks["sash_weight"]["ok"])

    def testNoStayFitsFailsCheck(self):
        window.STAYS[:] = [(160, 0.1), (205, 0.2)]
        lay = window.layout(load("bench-600.json"))
        self.assertIsNone(lay["stay"])
        checks = {c["name"]: c for c in lay["checks"]}
        self.assertFalse(checks["sash_weight"]["ok"])


class GlassSizeTest(unittest.TestCase):
    def testGlassSizesFloorRatherThanRound(self):
        p = load("home-1800x1500.json")
        p["fix_gap"] = 8.25
        lay = window.layout(p)
        self.assertEqual(lay["glass"]["fixed"][0], 1697)
        self.assertEqual(lay["glass"]["sash"][0], 1605)


class BedTest(unittest.TestCase):
    def member(self, lay, name):
        return next(m for m in lay["members"] if m["name"] == name)

    def testP1sBedKeepsTheOldMaximum(self):
        self.assertEqual(window.max_seg([256, 256, 256]), 240.0)

    def testMaxSegIsTheShorterOfHeightAndLongestSide(self):
        self.assertEqual(window.max_seg([250, 210, 220]), 204.0)
        self.assertEqual(window.max_seg([220, 220, 250]), 204.0)
        self.assertEqual(window.max_seg([180, 180, 180]), 164.0)

    def testMaxSegRejectsABadBed(self):
        for bed in ([256, 256], [256, 256, 16]):
            with self.assertRaises(ValueError):
                window.max_seg(bed)

    def testSplitTakesTheLimit(self):
        self.assertEqual(window.split(1668, 1.0, 164.0), (11, 150.55))

    def testExplicitP1sBedMatchesNoBedKey(self):
        p = load("home-1800x1500.json")
        self.assertEqual(window.layout(p)["members"], window.layout(dict(p, bed=[256, 256, 256]))["members"])

    def testSmallBedSplitsEveryMemberFiner(self):
        lay = window.layout(dict(load("home-1800x1500.json"), bed=[180, 180, 180]))
        self.assertEqual(lay["max_seg"], 164.0)
        for m in lay["members"]:
            self.assertLessEqual(m["seg"], 164.0, m["name"])
        head = self.member(lay, "head")
        self.assertEqual((head["n"], head["seg"]), (11, 150.55))
        self.assertEqual([c["name"] for c in lay["checks"] if not c["ok"]], [])

    def testMk4BedOnTheBench(self):
        lay = window.layout(dict(load("bench-600.json"), bed=[250, 210, 220]))
        self.assertEqual(lay["max_seg"], 204.0)
        self.assertEqual((self.member(lay, "head")["n"], self.member(lay, "head")["seg"]), (3, 154.67))
        self.assertEqual((self.member(lay, "jamb_upper")["n"], self.member(lay, "jamb_upper")["seg"]), (1, 198.0))

    def testDefaultBedStaysOutOfParams(self):
        lay = window.layout(load("bench-600.json"))
        self.assertNotIn("bed", lay["params"])
        self.assertEqual((lay["bed"], lay["max_seg"]), ([256, 256, 256], 240.0))


class ScreenOffTest(unittest.TestCase):
    def setUp(self):
        self.on = window.layout(load("home-1800x1500.json"))
        self.off = window.layout(dict(load("home-1800x1500.json"), screen=False))

    def testScreenDefaultsToOnAndStaysOutOfParams(self):
        self.assertTrue(self.on["has_screen"])
        self.assertNotIn("screen", self.on["params"])

    def testScreenMembersAreOmitted(self):
        self.assertFalse([m for m in self.off["members"] if m["name"].startswith("screen")])
        self.assertFalse(self.off["has_screen"])

    def testScreenTubesAreOmitted(self):
        self.assertNotIn("alu10", {t["core"] for t in self.off["tubes"]})

    def testFrameAndSashAreUnchanged(self):
        keep = lambda lay: [m for m in lay["members"] if not m["name"].startswith("screen")]
        self.assertEqual(keep(self.on), self.off["members"])
        self.assertEqual(self.on["glass"], self.off["glass"])

    def testScreenMustBeABoolean(self):
        with self.assertRaises(ValueError):
            window.layout(dict(load("home-1800x1500.json"), screen="no"))


class MinSegmentTest(unittest.TestCase):
    def member(self, lay, name):
        return next(m for m in lay["members"] if m["name"] == name)

    def testSplitTakesAMinimumSegmentCount(self):
        self.assertEqual(window.split(468, 1.0, 484.0), (1, 466.0))
        self.assertEqual(window.split(468, 1.0, 484.0, 2), (2, 232.5))

    def testMinimumBelowTheNaturalCountChangesNothing(self):
        self.assertEqual(window.split(1668, 1.0, None, 2), (7, 237.14))

    def testHingeCountFollowsTheScreenWidth(self):
        self.assertEqual((window.hinge_count(1000.0), window.hinge_count(1000.5)), (2, 3))

    def testBigBedBenchKeepsATwoSegmentTransomAndPassesCamKeeper(self):
        lay = window.layout(dict(load("bench-600.json"), bed=[500, 500, 500]))
        self.assertEqual(self.member(lay, "transom")["n"], 2)
        checks = {c["name"]: c for c in lay["checks"]}
        self.assertTrue(checks["cam_keeper"]["ok"], checks["cam_keeper"]["msg"])
        self.assertEqual([c["name"] for c in lay["checks"] if not c["ok"]], [])

    def testBigBedBenchHeadKeepsASegmentPerHinge(self):
        lay = window.layout(dict(load("bench-600.json"), bed=[500, 500, 500]))
        self.assertEqual(self.member(lay, "head")["n"], 2)

    def testWideWindowOnABigBedGetsAHeadSegmentPerHinge(self):
        for w in (1080, 1090, 1100):
            lay = window.layout(dict(load("home-1800x1500.json"), opening_w=w, bed=[500, 500, 500]))
            self.assertEqual(window.hinge_count(lay["screen"][0]), 3, w)
            self.assertGreaterEqual(self.member(lay, "head")["n"], 3, w)

    def testScreenOffHeadNeedsNoExtraSegments(self):
        lay = window.layout(dict(load("home-1800x1500.json"), opening_w=1090, bed=[500, 500, 500], screen=False))
        self.assertEqual(self.member(lay, "head")["n"], 2)

    def testLayoutCarriesTheHingeCount(self):
        self.assertEqual(window.layout(load("home-1800x1500.json"))["hinges"], 3)
        self.assertEqual(window.layout(load("bench-600.json"))["hinges"], 2)
        self.assertEqual(window.layout(dict(load("bench-600.json"), screen=False))["hinges"], 0)

    def testDefaultBedSegmentCountsAreUnchanged(self):
        counts = lambda lay: {m["name"]: (m["n"], m["seg"]) for m in lay["members"]}
        self.assertEqual(counts(window.layout(load("bench-600.json")))["transom"], (2, 232.5))
        self.assertEqual(counts(window.layout(load("home-1800x1500.json")))["head"], (7, 237.14))


class BedValidationTest(unittest.TestCase):
    def setUp(self):
        self.defaultBed = list(window.DEFAULT_BED)

    def tearDown(self):
        window.DEFAULT_BED[:] = self.defaultBed

    def testMaxSegAcceptsAListOrATuple(self):
        self.assertEqual(window.max_seg((250, 210, 220)), 204.0)
        self.assertEqual(window.max_seg([250.0, 210, 220]), 204.0)

    def testMaxSegRejectsAnythingButThreeFiniteNumbers(self):
        bad = (None, 256, "256", "abc", {"x": 256, "y": 256, "z": 256}, [256, 256, "256"], [256, 256, None],
               [256, 256, True], [256, 256, float("nan")], [256, 256, float("inf")], [256, 256, -float("inf")],
               [256, 256, 256, 256], [], [[256], [256], [256]])
        for bed in bad:
            with self.assertRaisesRegex(ValueError, "^bed must be", msg=repr(bed)):
                window.max_seg(bed)

    def testLayoutRejectsABadBed(self):
        for bed in ("big", [256, 256, float("nan")], {"x": 256}):
            with self.assertRaisesRegex(ValueError, "^bed must be", msg=repr(bed)):
                window.layout(dict(load("bench-600.json"), bed=bed))

    def testMaxSegIsFlooredToTwoDecimals(self):
        self.assertEqual(window.max_seg([250.129, 250.129, 250.129]), 234.12)
        self.assertEqual(window.max_seg([220.07, 220.07, 220.07]), 204.07)
        self.assertEqual(window.max_seg([256.5, 256.5, 256.5]), 240.5)

    def testTwoDecimalBedsKeepTheirExactLimit(self):
        for i in range(10000, 50001):
            self.assertEqual(window.max_seg([i / 100] * 3), round(i / 100 - 16, 2), i)

    def testBedThatFloorsToNothingIsRejected(self):
        with self.assertRaisesRegex(ValueError, "^bed must be"):
            window.max_seg([16.005, 16.005, 16.005])

    def testRoundedSegmentsNeverExceedAThreeDecimalBed(self):
        bed = [250.129, 250.129, 250.129]
        n, seg = window.split(234.128, 0.0, window.max_seg(bed))
        self.assertEqual((n, seg), (2, 117.06))
        lay = window.layout(dict(load("home-1800x1500.json"), bed=bed))
        for m in lay["members"]:
            self.assertLessEqual(m["seg"], lay["max_seg"], m["name"])
        self.assertTrue(next(c for c in lay["checks"] if c["name"] == "segment_length")["ok"])

    def testDimsMaxSegMatchesTheDefaultBed(self):
        self.assertEqual(window.D["MAX_SEG"], window.max_seg(window.DEFAULT_BED))

    def testLayoutBedDoesNotAliasTheDefault(self):
        lay = window.layout(load("bench-600.json"))
        lay["bed"][0] = 1
        lay["bed"].append(2)
        self.assertEqual(window.DEFAULT_BED, [256, 256, 256])

    def testLayoutBedDoesNotAliasTheParams(self):
        p = dict(load("bench-600.json"), bed=(250, 210, 220))
        lay = window.layout(p)
        self.assertEqual(lay["bed"], [250, 210, 220])
        lay["bed"][0] = 1
        self.assertEqual(p["bed"], (250, 210, 220))


def two_bay(**changes):
    return window.layout(dict(load("home-1800x1500-2bay.json"), **changes))


class BayCountTest(unittest.TestCase):
    def home(self, **changes):
        return window.layout(dict(load("home-1800x1500.json"), **changes))

    def testNoLimitIsOneBay(self):
        lay = self.home()
        self.assertEqual((lay["bays"], lay["auto_bays"], lay["mullions"]), (1, 1, []))

    def testTwelveByNineSheetGivesTwoBays(self):
        lay = self.home(max_pane=[1200, 900])
        self.assertEqual((lay["bays"], lay["auto_bays"]), (2, 2))
        self.assertEqual(lay["glass"], {"fixed": (829, 878), "sash": (737, 388)})

    def testNineBySixSheetGivesThreeBays(self):
        lay = self.home(max_pane=[900, 600])
        self.assertEqual(lay["bays"], 3)
        self.assertEqual(lay["glass"], {"fixed": (539, 878), "sash": (447, 388)})

    def testSheetOrderDoesNotMatter(self):
        self.assertEqual(self.home(max_pane=[900, 1200])["glass"], self.home(max_pane=[1200, 900])["glass"])

    def testPaneMayTurnToFitTheSheet(self):
        lay = self.home(max_pane=[1000, 850])
        self.assertEqual((lay["bays"], lay["glass"]["fixed"]), (2, (829, 878)))

    def testFixedPaneTooTallForAnySheetRaises(self):
        with self.assertRaisesRegex(ValueError, "^max_pane: the 878 mm tall fixed pane .* second horizontal transom"
                                                ".* taller awning_h or a shorter opening$"):
            self.home(max_pane=[800, 800])

    def testSashPaneTooTallSuggestsAShorterAwning(self):
        with self.assertRaisesRegex(ValueError, "^max_pane: the 1038 mm tall sash pane .* shorter awning_h$"):
            self.home(awning_h=1100, max_pane=[1000, 1000])

    def testNarrowWindowThatCannotSplitRaises(self):
        with self.assertRaisesRegex(ValueError, "^max_pane: at 1 bay, the most this opening takes .* "
                                                "fixed pane is still 348 x 228 mm, too big for a 300 x 300 mm sheet$"):
            window.layout(dict(load("bench-600.json"), opening_w=450, max_pane=[300, 300]))

    def testMoreBaysThanNeeded(self):
        lay = self.home(max_pane=[1200, 900], bays=3)
        self.assertEqual((lay["bays"], lay["auto_bays"], lay["glass"]["fixed"]), (3, 2, (539, 878)))

    def testFewerBaysThanNeededRaises(self):
        with self.assertRaisesRegex(ValueError, "^bays must be at least 2 for a 1200 x 900 mm max_pane, got 1$"):
            self.home(max_pane=[1200, 900], bays=1)

    def testBaysWithoutALimit(self):
        self.assertEqual(self.home(bays=2)["bays"], 2)

    def testBaysMustBeAWholeNumber(self):
        for bays in (0, -1, 2.0, True, "2", None):
            with self.assertRaisesRegex(ValueError, "^bays must be a whole number", msg=repr(bays)):
                self.home(bays=bays)

    def testBaysAboveTheMostRaises(self):
        self.assertEqual(window.max_bays(1668), 7)
        with self.assertRaisesRegex(ValueError, "^bays must be at most 7 for this opening"):
            self.home(bays=8)

    def testMaxPaneMustBeTwoSizes(self):
        for limit in ([1200], [1200, 900, 600], [150, 900], [1200, 3001], [1200, "900"], [1200, float("nan")],
                      [True, 900], "1200x900", None):
            with self.assertRaisesRegex(ValueError, "^max_pane must be two sizes", msg=repr(limit)):
                self.home(max_pane=limit)

    def testFitsTurnsThePane(self):
        self.assertTrue(window.fits((878, 829), (900, 1200)))
        self.assertFalse(window.fits((910, 829), (900, 900)))


class NonFiniteInputTest(unittest.TestCase):
    def testNonFiniteSizesAreRejected(self):
        for key in ("opening_w", "opening_h", "fix_gap", "awning_h"):
            for value in (float("inf"), float("-inf"), float("nan")):
                params = dict(load("home-1800x1500.json"), **{key: value})
                with self.assertRaisesRegex(ValueError, f"^{key} must be a finite number", msg=f"{key}={value}"):
                    window.layout(params)


class MullionDimsTest(unittest.TestCase):
    def testShippedDimsAgree(self):
        self.assertEqual(two_bay()["bays"], 2)

    def testMullionHalfBodyOutOfStepIsRejected(self):
        with mock.patch.dict(window.D, {"MULLION_HALF_BODY": window.D["MULLION_HALF_BODY"] + 1}):
            with self.assertRaisesRegex(ValueError, r"^mullion dims: FRAME_W - FRAME_BODY must equal MULLION_W / 2 - MULLION_HALF_BODY"):
                two_bay()

    def testTransomGlassOutOfStepIsRejected(self):
        with mock.patch.dict(window.D, {"TRANSOM_GLASS": window.D["TRANSOM_GLASS"] + 1}):
            with self.assertRaisesRegex(ValueError, r"^mullion dims: FRAME_W - GLASS_EDGE must equal MULLION_W / 2 - TRANSOM_GLASS"):
                two_bay()

    def testMullionWidthOutOfStepIsRejectedWhenBaysComeFromTheSearch(self):
        with mock.patch.dict(window.D, {"MULLION_W": window.D["MULLION_W"] + 2}):
            with self.assertRaisesRegex(ValueError, "^mullion dims: "):
                two_bay()

    def testOneBayIgnoresTheMullionDims(self):
        with mock.patch.dict(window.D, {"MULLION_HALF_BODY": window.D["MULLION_HALF_BODY"] + 1}):
            self.assertEqual(window.layout(load("home-1800x1500.json"))["bays"], 1)

    def testDimsAreRestoredAfterThePatch(self):
        with mock.patch.dict(window.D, {"TRANSOM_GLASS": 0}):
            pass
        self.assertEqual(two_bay()["bays"], 2)


class BayLayoutTest(unittest.TestCase):
    def setUp(self):
        self.lay = two_bay()

    def member(self, name, lay=None):
        return next(m for m in (lay or self.lay)["members"] if m["name"] == name)

    def testMullionSitsOnTheCentreLine(self):
        self.assertEqual((self.lay["pitch"], self.lay["mullions"], self.lay["bay_w"]), (869.0, [892.0], 799.0))

    def testEveryBayHasTheSameDaylight(self):
        lay = window.layout(dict(load("home-1800x1500.json"), max_pane=[900, 600]))
        F, MW = window.D["FRAME_W"], window.D["MULLION_W"]
        edges = [F] + [x for c in lay["mullions"] for x in (c - MW / 2, c + MW / 2)] + [lay["w"] - F]
        widths = [edges[i + 1] - edges[i] for i in range(0, len(edges), 2)]
        for got in widths:
            self.assertAlmostEqual(got, lay["bay_w"], places=6)

    def testRunsSplitBetweenTheNodes(self):
        for name in ("head", "sill", "transom"):
            m = self.member(name)
            self.assertEqual((m["length"], m["qty"], m["n"], m["seg"]), (799.0, 2, 4, 198.5), name)

    def testRunsAndNodesFillTheWidth(self):
        m = self.member("sill")
        self.assertAlmostEqual(self.lay["bays"] * m["length"] + (self.lay["bays"] - 1) * window.D["MULLION_W"],
                               self.lay["w"] - 2 * window.D["FRAME_W"], places=6)

    def testSmallBedSplitsTheRunsFiner(self):
        lay = two_bay(bed=[180, 180, 180])
        self.assertEqual((self.member("sill", lay)["n"], self.member("sill", lay)["seg"]), (5, 158.6))
        self.assertEqual((self.member("mullion_lower", lay)["n"], self.member("mullion_lower", lay)["seg"]), (6, 140.17))

    def testMullionMembers(self):
        low, up = self.member("mullion_lower"), self.member("mullion_upper")
        self.assertEqual((low["length"], low["profile"], low["core"], low["qty"], low["n"], low["seg"]),
                         (848.0, "mullion_glazing", "steel40x20", 1, 4, 210.75))
        self.assertEqual((up["length"], up["profile"], up["qty"], up["n"], up["seg"]), (450, "mullion_sash", 1, 2, 223.5))

    def testSashAndScreenPerBay(self):
        self.assertEqual((self.lay["sash"], self.lay["screen"], self.lay["opening"]), ((809.0, 460.0), (855.0, 540.0), 835.0))
        self.assertEqual((self.member("sash_horizontal")["qty"], self.member("screen_vertical")["qty"]), (4, 4))

    def testTubes(self):
        tubes = {t["member"]: (t["length"], t["qty"]) for t in self.lay["tubes"]}
        self.assertEqual((tubes["head"], tubes["sill"], tubes["transom"]), ((1721.0, 1), (1721.0, 1), (1696.0, 1)))
        self.assertEqual((tubes["mullion_lower"], tubes["mullion_upper"]), ((876.0, 1), (478.0, 1)))
        self.assertEqual((tubes["sash_horizontal"], tubes["sash_vertical"]), ((746.0, 4), (397.0, 4)))

    def testOneBayIsTheOldLayout(self):
        old, new = window.layout(load("home-1800x1500.json")), window.layout(dict(load("home-1800x1500.json"), bays=1))
        for key in ("members", "tubes", "glass", "sash", "screen", "keeper_dz"):
            self.assertEqual(old[key], new[key], key)


def checks_by_name(lay):
    return {c["name"]: c for c in lay["checks"]}


class BayChecksTest(unittest.TestCase):
    def testNoBayKeysKeepTheFourChecks(self):
        self.assertEqual([c["name"] for c in window.layout(load("home-1800x1500.json"))["checks"]],
                         ["transom_deflection", "sash_weight", "segment_length", "cam_keeper"])

    def testBayKeysAddPaneFitAndMullionDeflection(self):
        self.assertEqual([c["name"] for c in two_bay()["checks"]],
                         ["transom_deflection", "sash_weight", "segment_length", "cam_keeper", "pane_fit", "mullion_deflection"])

    def testAllChecksPassForTheTwoBayHome(self):
        self.assertEqual([c["name"] for c in two_bay()["checks"] if not c["ok"]], [])

    def testPaneFitMessages(self):
        self.assertEqual(checks_by_name(two_bay())["pane_fit"]["msg"],
                         "2 bays: fixed panes 829 x 878, sash panes 737 x 388 fit a 1200 x 900 mm sheet")
        self.assertEqual(checks_by_name(two_bay(bays=3))["pane_fit"]["msg"],
                         "3 bays (2 needed): fixed panes 539 x 878, sash panes 447 x 388 fit a 1200 x 900 mm sheet")
        no_limit = window.layout(dict(load("home-1800x1500.json"), bays=2))
        self.assertEqual(checks_by_name(no_limit)["pane_fit"]["msg"], "2 bays, no max_pane limit")

    def testMullionDeflectsLikeASimpleBeamOverTheLowerStub(self):
        c = checks_by_name(two_bay())["mullion_deflection"]
        self.assertTrue(c["ok"])
        self.assertEqual(c["msg"], "lower mullion deflects 0.6 mm at 0.7 kPa over 848 mm, limit span/175 = 4.8 mm")
        self.assertAlmostEqual(window.deflection("steel40x20", 848, 869), 0.555, delta=0.005)

    def testOneBayHasNoMullions(self):
        c = checks_by_name(window.layout(dict(load("home-1800x1500.json"), bays=1)))["mullion_deflection"]
        self.assertEqual((c["ok"], c["msg"]), (True, "1 bay, no mullions"))

    def testTransomCarriesTheMullionLoadOverItsFullSpan(self):
        lay = two_bay()
        self.assertEqual(checks_by_name(lay)["transom_deflection"]["msg"],
                         "transom deflects 6.8 mm at 0.7 kPa carrying 1 mullion, limit span/175 = 9.5 mm")
        w = 0.7 / 1000 * 649
        loads = (window.strip_loads(0, 399.5, w) + window.strip_loads(1268.5, 1668, w)
                 + [(834.0, 0.7 / 1000 * 869 * 649)])
        self.assertAlmostEqual(window.beam_deflection("steel40x20", 1668, loads), 6.82, delta=0.01)

    def testBeamDeflectionMatchesTheClosedForms(self):
        udl = window.beam_deflection("steel40x20", 1668, window.strip_loads(0, 1668, 0.7 / 1000 * 649))
        self.assertAlmostEqual(udl, window.deflection("steel40x20", 1668, 649), delta=0.01)
        point = window.beam_deflection("steel40x20", 1668, [(834, 400.0)])
        self.assertAlmostEqual(point, 400.0 * 1668 ** 3 / (48 * 200000 * window.inertia("steel40x20")), places=6)

    def testSashChecksAreReportedOnceForEverySash(self):
        c = checks_by_name(two_bay())
        self.assertEqual(c["sash_weight"]["msg"], "sash 7.6 kg, stay pair 400 mm rated 30.0 kg, each of 2 sashes")
        self.assertTrue(c["cam_keeper"]["msg"].endswith("transom needs 2+ segments per bay), each of 2 sashes"))
        self.assertEqual(two_bay()["keeper_dz"], 63.92)


class SandwichTest(unittest.TestCase):
    def acrylic(self, **extra):
        return window.layout({**load("bench-600.json"), **extra})

    def testDefaultSandwichIsFourSixteenFour(self):
        self.assertEqual(self.acrylic()["sandwich"], {"t": 4.0, "gap": 16.0, "custom": False})

    def testCustomSandwichIsReported(self):
        self.assertEqual(self.acrylic(acrylic_t=3, acrylic_gap=12)["sandwich"], {"t": 3, "gap": 12, "custom": True})

    def testOneKeyAloneKeepsTheOtherDefault(self):
        self.assertEqual(self.acrylic(acrylic_t=3)["sandwich"], {"t": 3, "gap": 16.0, "custom": True})

    def testThinnerPanelsLightenTheSash(self):
        lay = window.layout({**load("home-1800x1500.json"), "glazing": "acrylic", "acrylic_t": 3, "acrylic_gap": 12})
        gw, gh = lay["glass"]["sash"]
        sw, sh = lay["sash"]
        frame = 2 * (sw + sh) / 1000 * window.SASH_FRAME_KG_M
        self.assertEqual(lay["sash_kg"], round(gw * gh / 1e6 * 9.5 * 3 / 4 + frame, 1))

    def testDefaultSashWeightIsUnchanged(self):
        self.assertEqual(self.acrylic()["sash_kg"], window.layout(load("bench-600.json"))["sash_kg"])

    def testSandwichKeysNeedAcrylic(self):
        with self.assertRaisesRegex(ValueError, "^acrylic_t only applies to acrylic glazing"):
            window.layout({**load("home-1800x1500.json"), "acrylic_t": 3})
        with self.assertRaisesRegex(ValueError, "^acrylic_gap only applies to acrylic glazing"):
            window.layout({**load("home-1800x1500.json"), "acrylic_gap": 12})

    def testThicknessRange(self):
        for bad in (1.5, 6.5, True, "3", float("nan")):
            with self.assertRaisesRegex(ValueError, "^acrylic_t must be a number from 2 to 6 mm", msg=bad):
                self.acrylic(acrylic_t=bad)

    def testGapRange(self):
        for bad in (7, 16.5, None, float("inf")):
            with self.assertRaisesRegex(ValueError, "^acrylic_gap must be a number from 8 to 16 mm", msg=bad):
                self.acrylic(acrylic_gap=bad)

    def testSandwichMustFitThePocket(self):
        with self.assertRaisesRegex(ValueError, r"^acrylic_t: 2 x 5 \+ 16 = 26 mm does not fit the 24 mm glazing pocket"):
            self.acrylic(acrylic_t=5)
        self.assertEqual(self.acrylic(acrylic_t=4, acrylic_gap=16)["sandwich"]["custom"], False)

    def testLimitsAreAccepted(self):
        for t_, gap in ((2, 8), (2, 16), (6, 12), (4, 16), (3, 12)):
            self.assertEqual(self.acrylic(acrylic_t=t_, acrylic_gap=gap)["sandwich"]["t"], t_)

    def testOtherGlazingsHaveNoSandwich(self):
        self.assertIsNone(window.layout(load("home-1800x1500.json"))["sandwich"])


def vslot(name, **changes):
    return window.layout({**load(f"{name}.json"), "core": "vslot", **changes})


class VslotInputTest(unittest.TestCase):
    def testDefaultHasNoVslot(self):
        lay = window.layout(load("home-1800x1500.json"))
        self.assertIsNone(lay["vslot"])
        self.assertNotIn("core", [c["name"] for c in lay["checks"]])

    def testCoreMustBeVslot(self):
        for value in ("tube", "", None, 2020):
            with self.assertRaisesRegex(ValueError, "^core must be vslot"):
                window.layout({**load("bench-600.json"), "core": value})

    def testStockNeedsTheCore(self):
        with self.assertRaisesRegex(ValueError, "^vslot_stock only applies with core vslot"):
            window.layout({**load("bench-600.json"), "vslot_stock": 1000})

    def testStockRange(self):
        for value in (299, 6001, True, "1000", None, float("inf")):
            with self.assertRaisesRegex(ValueError, "^vslot_stock must be a number from 300 to 6000 mm"):
                vslot("bench-600", vslot_stock=value)

    def testStockLimitsAreAccepted(self):
        for value in (300, 6000):
            self.assertEqual(vslot("bench-600", vslot_stock=value)["vslot"]["stock"], value)


class VslotCoresTest(unittest.TestCase):
    def cores(self, lay):
        return {m["name"]: m["core"] for m in lay["members"]}

    def testBenchIsAllVslot(self):
        lay = vslot("bench-600")
        self.assertEqual({k: v for k, v in self.cores(lay).items() if not k.startswith("screen")},
                         {"head": "vslot2020", "sill": "vslot2020", "jamb_lower": "vslot2020", "jamb_upper": "vslot2020",
                          "transom": "vslot2020x2", "sash_horizontal": "vslot2020", "sash_vertical": "vslot2020"})
        self.assertEqual(lay["vslot"]["fallbacks"], [])
        self.assertEqual(checks_by_name(lay)["core"]["msg"], "V-slot 2020: 5 pieces of 1000 mm")

    def testHomeFallsBackWithReasons(self):
        lay = vslot("home-1800x1500")
        cores = self.cores(lay)
        self.assertEqual((cores["transom"], cores["sash_horizontal"], cores["sash_vertical"]), ("steel40x20", "alu20", "vslot2020"))
        self.assertEqual(checks_by_name(lay)["core"]["msg"],
                         "V-slot 2020: 8 pieces of 1000 mm; joins: head 1, sill 1; steel transom: 1696 mm is longer than "
                         "the 1000 mm V-slot pieces, and a V-slot pair would deflect 48.2 mm (limit 9.5 mm); alu20 "
                         "sash_horizontal: 1615 mm is longer than the 1000 mm V-slot pieces")
        self.assertTrue(checks_by_name(lay)["core"]["ok"])

    def testLongerStockOnlyLeavesTheTransom(self):
        lay = vslot("home-1800x1500", vslot_stock=2000)
        self.assertEqual(lay["vslot"]["fallbacks"], ["steel transom: a V-slot pair would deflect 48.2 mm (limit 9.5 mm)"])
        self.assertEqual(lay["vslot"]["joins"], {"head": [], "sill": [], "jamb_lower": []})

    def testHomeTubes(self):
        tubes = [(t["member"], t["core"], t["length"], t["qty"]) for t in vslot("home-1800x1500")["tubes"]]
        self.assertEqual(tubes[:6], [("head 1/2", "vslot2020", 919.8, 1), ("head 2/2", "vslot2020", 801.2, 1),
                                     ("sill 1/2", "vslot2020", 919.8, 1), ("sill 2/2", "vslot2020", 801.2, 1),
                                     ("jamb_lower", "vslot2020", 943.0, 2), ("jamb_upper", "vslot2020", 475.0, 2)])
        self.assertEqual(vslot("home-1800x1500")["vslot"]["joins"]["head"], [{"at": 919.8, "segment": 4}])

    def testJambPiecesAddUpToTheStandardJamb(self):
        plain = next(t for t in window.layout(load("home-1800x1500.json"))["tubes"] if t["member"] == "jamb")
        pieces = {t["member"]: t for t in vslot("home-1800x1500")["tubes"]}
        clear = window.D["TUBE_END_CLEAR"]
        self.assertAlmostEqual(pieces["jamb_lower"]["length"] + pieces["jamb_upper"]["length"] + 2 * clear, plain["length"], places=6)

    def testStockEqualToATubeIsEnough(self):
        self.assertEqual(self.cores(vslot("bench-600", vslot_stock=496))["transom"], "vslot2020x2")
        self.assertEqual(self.cores(vslot("bench-600", vslot_stock=495))["transom"], "steel40x20")

    def testTransomPairIsTwoBars(self):
        t = next(x for x in vslot("bench-600")["tubes"] if x["member"] == "transom")
        self.assertEqual((t["core"], t["length"], t["qty"]), ("vslot2020", 496.0, 2))
        self.assertEqual(window.inertia("vslot2020x2"), 2 * window.inertia("vslot2020"))

    def testTwoBayMullionsArePairs(self):
        lay = two_bay(core="vslot")
        cores = self.cores(lay)
        self.assertEqual((cores["mullion_lower"], cores["mullion_upper"], cores["transom"]), ("vslot2020x2", "vslot2020x2", "steel40x20"))
        self.assertEqual(checks_by_name(lay)["mullion_deflection"]["msg"],
                         "lower mullion deflects 4.3 mm at 0.7 kPa over 848 mm, limit span/175 = 4.8 mm")

    def testTallLowerMullionFallsBackToSteel(self):
        lay = two_bay(core="vslot", opening_h=1800, vslot_stock=3000)
        cores = self.cores(lay)
        self.assertEqual((cores["mullion_lower"], cores["mullion_upper"]), ("steel40x20", "vslot2020x2"))
        self.assertEqual(lay["vslot"]["fallbacks"], ["steel transom: a V-slot pair would deflect 65.1 mm (limit 9.5 mm)",
                                                     "steel lower mullion: a V-slot pair would deflect 14.5 mm over 1148 mm (limit 6.6 mm)"])
        self.assertEqual(checks_by_name(lay)["mullion_deflection"]["msg"],
                         "lower mullion deflects 1.9 mm at 0.7 kPa over 1148 mm, limit span/175 = 6.6 mm")

    def testSashWeightCountsTheVslotMass(self):
        lay = vslot("bench-600")
        sw, sh = lay["sash"]
        gw, gh = lay["glass"]["sash"]
        extra = window.CORES["vslot2020"][4] - window.CORES["alu20"][4]
        expected = gw * gh / 1e6 * window.GLAZING_KG_M2["acrylic"] + 2 * (sw + sh) / 1000 * window.SASH_FRAME_KG_M
        self.assertEqual(lay["sash_kg"], round(expected + 2 * (sw + sh) / 1000 * extra, 1))

    def testKeeperMinimumUsesTheM5Head(self):
        self.assertIn("allowed 21.3-73.0 mm", checks_by_name(vslot("bench-600"))["cam_keeper"]["msg"])
        self.assertIn("allowed 20.6-73.0 mm", checks_by_name(window.layout(load("bench-600.json")))["cam_keeper"]["msg"])

    def testM5Lengths(self):
        names = ["glazing", "sill", "sash_rebate", "sash", "mullion_glazing", "mullion_sash"]
        self.assertEqual([window.m5_length(n) for n in names], [25, 25, 25, 20, 16, 16])


class VslotJoinTest(unittest.TestCase):
    def testJoinsSitInsideSegmentsClearOfTheirNuts(self):
        sock = window.D["SOCKET_FRAME"] - window.D["TUBE_END_CLEAR"]
        gap = window.D["JOINT_GAP"]
        for lay in (vslot("home-1800x1500", vslot_stock=500), vslot("bench-600", vslot_stock=300)):
            members = {m["name"]: m for m in lay["members"]}
            for name, joins in lay["vslot"]["joins"].items():
                m = members[name]
                nut = window.D["FIX_DZ"] if name == "head" else 0.0
                for j in joins:
                    s0 = sock + gap + (j["segment"] - 1) * (m["seg"] + gap)
                    s1 = s0 + m["seg"]
                    c = (s0 + s1) / 2
                    self.assertGreaterEqual(min(j["at"] - s0, s1 - j["at"]), window.JOIN_END - 0.05, (name, j))
                    self.assertGreaterEqual(abs(j["at"] - c) - nut / 2, window.JOIN_NUT - 0.05, (name, j))
        for lay in (vslot("home-1800x1500"), vslot("bench-600", vslot_stock=300), two_bay(core="vslot")):
            for t in lay["tubes"]:
                if t["core"] == "vslot2020":
                    self.assertLessEqual(t["length"], lay["vslot"]["stock"], t)

    def testShortStockJoinsMoreThanOnce(self):
        lay = vslot("bench-600", vslot_stock=300)
        self.assertEqual([j["at"] for j in lay["vslot"]["joins"]["head"]], [201.9, 435.4])
        self.assertEqual([t["length"] for t in lay["tubes"] if t["member"].startswith("head")], [201.9, 233.5, 85.6])

    def testShortSegmentsKeepTheStandardTube(self):
        lay = vslot("bench-600", vslot_stock=300, bed=[80, 80, 80])
        self.assertEqual({m["name"]: m["core"] for m in lay["members"]}["head"], "alu20")
        self.assertEqual(lay["vslot"]["fallbacks"][:2], ["alu20 head: 300 mm V-slot pieces can't be joined inside its 57.38 mm segments",
                                                         "alu20 sill: 300 mm V-slot pieces can't be joined inside its 57.38 mm segments"])
        self.assertEqual([t["core"] for t in lay["tubes"] if t["member"] == "head"], ["alu20"])

    def testLowerJambJoinsHoldTheirOwnNuts(self):
        lay = vslot("home-1800x1500", vslot_stock=500)
        self.assertEqual({m["name"]: m["core"] for m in lay["members"]}["jamb_lower"], "vslot2020")
        self.assertEqual(lay["vslot"]["joins"]["jamb_lower"], [{"at": 397.3, "segment": 2}, {"at": 820.8, "segment": 4}])
        self.assertEqual([(t["member"], t["length"], t["qty"]) for t in lay["tubes"] if t["member"].startswith("jamb_lower")],
                         [("jamb_lower 1/3", 397.3, 2), ("jamb_lower 2/3", 423.5, 2), ("jamb_lower 3/3", 122.2, 2)])
        self.assertFalse([f for f in lay["vslot"]["fallbacks"] if "jamb_lower" in f])

    def testJoinPlanNeedsACandidate(self):
        self.assertIsNone(window.join_plan(500.0, [(10.0, 60.0, 35.0, 0.0)], [5.0, 495.0], 300))

    def testJoinPlanKeepsANutInEveryPiece(self):
        segs = [(10.0 + 100 * k, 105.0 + 100 * k, 57.5 + 100 * k, 0.0) for k in range(5)]
        joins = window.join_plan(510.0, segs, [5.0, 505.0], 300)
        self.assertEqual(joins, [281.25])
        self.assertIsNone(window.join_plan(510.0, segs, [5.0, 505.0], 120))

    def testJoinPlanKeepsJoinsClearOfTheNut(self):
        held = [5.0, 43.0, 113.0, 183.0, 253.0, 295.0]
        segs = [(10.0 + 70 * k, 76.0 + 70 * k, 43.0 + 70 * k, 0.0) for k in range(4)]
        self.assertEqual(window.join_plan(300.0, segs, held, 150), [129.5, 269.5])
        segs = [(10.0 + 70 * k, 76.0 + 70 * k, 43.0 + 70 * k, 7.0) for k in range(4)]
        self.assertIsNone(window.join_plan(300.0, segs, held, 150))

    def testCutPlanPacksFirstFitDecreasing(self):
        plan = window.cut_plan([("a", 600.0), ("b", 500.0), ("c", 398.0)], 1000)
        self.assertEqual(plan, [{"cuts": [("a", 600.0), ("c", 398.0)], "offcut": 0.0}, {"cuts": [("b", 500.0)], "offcut": 500.0}])


if __name__ == "__main__":
    unittest.main()
