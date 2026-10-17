"""Unit tests for tools/generate.py."""
import contextlib
import csv
import io
import json
import pathlib
import re
import tempfile
import unittest
from unittest import mock

import generate
import window

ROOT = pathlib.Path(__file__).resolve().parent.parent


def lay(name):
    return window.layout(json.loads((ROOT / "params" / name).read_text()))


def byId(parts):
    return {p["id"]: p for p in parts}


def bossCentres(parts):
    D = window.D
    te = D["FRAME_W"] + D["JOINT_GAP"] + parts["TE"]["length"] / 2
    dz = float(re.search(r"boss_dz=([0-9.]+)", parts["SBE"]["call"]).group(1))
    sbe = D["FRAME_BODY"] + D["SASH_GAP"] + D["SASH_W"] + D["JOINT_GAP"] + parts["SBE"]["length"] / 2 - dz
    return te, sbe


class HomePartsTest(unittest.TestCase):
    def setUp(self):
        self.parts = byId(generate.parts(lay("home-1800x1500.json")))

    def testHeadSegmentCall(self):
        h = self.parts["H"]
        self.assertEqual(h["call"], 'frame_segment("sash_rebate", 237.14, "H", bosses=true);')
        self.assertEqual(h["qty"], 7)

    def testSillWeepsOnTheTwoEndSegments(self):
        self.assertEqual((self.parts["S"]["qty"], self.parts["SW"]["qty"]), (5, 2))

    def testJambSegmentsCoverBothJambs(self):
        self.assertEqual(self.parts["JL"]["qty"], 8)
        self.assertEqual(self.parts["JU"]["qty"], 4)

    def testSillCornersAreMirrored(self):
        self.assertIn("mirrored=true", self.parts["CSR"]["call"])
        self.assertNotIn("mirrored", self.parts["CSL"]["call"])

    def testBeadRuns(self):
        got = {k: (self.parts[k]["length"], self.parts[k]["qty"]) for k in ("BFH", "BFV", "BSH", "BSV")}
        self.assertEqual(got, {"BFH": (213.0, 16), "BFV": (213.0, 8), "BSH": (230.29, 14), "BSV": (181.0, 4)})

    def testBeadsUseTheGlazingVariant(self):
        self.assertTrue(self.parts["BFH"]["call"].startswith('bead("igu", '))

    def testNoAcrylicSpacersForIgu(self):
        self.assertFalse([k for k in self.parts if k.startswith("A")])

    def testSillNoseRunsOverTheCornersToTheKeySlotEnds(self):
        ns = self.parts["NS"]
        self.assertEqual((ns["qty"], ns["length"]), (8, 217.88))
        self.assertEqual(ns["call"], 'sill_nose(217.88, "NS");')
        self.assertAlmostEqual(ns["qty"] * ns["length"] + (ns["qty"] + 1) * 1.0, 1784 - 2 * 16, delta=0.05)

    def testKeeperBossesCarryTheCamOffset(self):
        self.assertEqual(self.parts["SBE"]["call"], 'frame_segment("sash", 224.0, "SBE", weep=true, bosses=true, boss_dz=39.43);')
        self.assertEqual((self.parts["SBE"]["qty"], self.parts["TE"]["qty"]), (2, 2))
        self.assertNotIn("boss_dz", self.parts["TE"]["call"])

    def testThreeScreenHingesOnAWideScreen(self):
        self.assertEqual(self.parts["HG"]["qty"], 3)

    def testInteriorRoles(self):
        for k in ("NH", "NV", "CN", "CMB", "CMH", "KP", "HG", "HS", "BFH"):
            self.assertEqual(self.parts[k]["role"], "interior", k)
        self.assertEqual(self.parts["H"]["role"], "exterior")


class BenchPartsTest(unittest.TestCase):
    def setUp(self):
        self.parts = byId(generate.parts(lay("bench-600.json")))

    def testTwoSegmentSillHasOnlyWeepSegments(self):
        self.assertNotIn("S", self.parts)
        self.assertEqual(self.parts["SW"]["qty"], 2)

    def testSillNoseSplitsIndependentlyOfTheSill(self):
        self.assertEqual((self.parts["NS"]["qty"], self.parts["NS"]["length"]), (3, 182.67))

    def testAcrylicSpacers(self):
        self.assertEqual((self.parts["AFH"]["length"], self.parts["AFH"]["qty"]), (237.0, 4))
        self.assertEqual((self.parts["AFV"]["length"], self.parts["AFV"]["qty"]), (204.0, 2))
        self.assertEqual(self.parts["AC"]["qty"], 8)


class AllPartsTest(unittest.TestCase):
    def testCamAndKeeperBossCentresAgree(self):
        for name in ("home-1800x1500.json", "bench-600.json"):
            te, sbe = bossCentres(byId(generate.parts(lay(name))))
            self.assertLessEqual(abs(te - sbe), window.D["CAM_ALIGN_TOL"], name)

    def testIdsAreUnique(self):
        for name in ("home-1800x1500.json", "bench-600.json"):
            ids = [p["id"] for p in generate.parts(lay(name))]
            self.assertEqual(len(ids), len(set(ids)), name)

    def testEveryLengthFitsTheBed(self):
        for p in generate.parts(lay("home-1800x1500.json")):
            if p["length"] is not None:
                self.assertLessEqual(p["length"], 240.0, p["id"])

    def testQuantitiesArePositive(self):
        for p in generate.parts(lay("home-1800x1500.json")):
            self.assertGreater(p["qty"], 0, p["id"])


class WriteTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.out = pathlib.Path(self.tmp.name) / "generated"
        self.lay = lay("home-1800x1500.json")
        generate.write(self.lay, self.out)

    def tearDown(self):
        self.tmp.cleanup()

    def testWrapperUsesThePartFileAndCallsTheModule(self):
        text = (self.out / "parts" / "H.scad").read_text()
        self.assertEqual(text, 'use <../../parts/frame_segment.scad>\nframe_segment("sash_rebate", 237.14, "H", bosses=true);\n')

    def testCamPartsShareOneFile(self):
        self.assertIn("use <../../parts/cam_lock.scad>", (self.out / "parts" / "KP.scad").read_text())

    def testDimsMirror(self):
        self.assertIn("FRAME_W = 58.0;\n", (self.out / "dims.scad").read_text())

    def testLayoutScad(self):
        text = (self.out / "layout.scad").read_text()
        self.assertIn("TRANSOM_C = 941.0;\n", text)
        self.assertIn('GLAZING = "igu";\n', text)
        self.assertIn("FIXED_GLASS = [1698, 878];\n", text)
        self.assertIn('NAME = "home-1800x1500";\n', text)

    def testParamsJsonMatchesInput(self):
        saved = json.loads((self.out / "params.json").read_text())
        self.assertEqual(saved, self.lay["params"])

    def testPartsCsvMatchesParts(self):
        rows = list(csv.DictReader((self.out / "parts.csv").read_text().splitlines()))
        self.assertEqual(len(rows), len(generate.parts(self.lay)))
        self.assertEqual(rows[0].keys(), {"id", "qty", "role", "length", "module", "call"})

    def testCutlist(self):
        rows = {r["member"]: r for r in csv.DictReader((self.out / "cutlist.csv").read_text().splitlines())}
        self.assertEqual(rows["transom"]["core"], "steel40x20")
        self.assertEqual(float(rows["transom"]["length_mm"]), 1696.0)

    def testGlassCsv(self):
        rows = {r["pane"]: r for r in csv.DictReader((self.out / "glass.csv").read_text().splitlines())}
        self.assertEqual((rows["fixed"]["width_mm"], rows["fixed"]["height_mm"]), ("1698", "878"))

    def testCsvWritersTakeAnyPath(self):
        generate.write_cutlist(self.lay, self.out / "x-cutlist.csv")
        generate.write_glass(self.lay, self.out / "x-glass.csv")
        generate.write_parts(generate.parts(self.lay), self.out / "x-parts.csv")
        for f in ("cutlist", "glass", "parts"):
            self.assertEqual((self.out / f"x-{f}.csv").read_text(), (self.out / f"{f}.csv").read_text(), f)

    def testStaleWrappersAreRemoved(self):
        (self.out / "parts" / "OLD.scad").write_text("x")
        generate.write(self.lay, self.out)
        self.assertFalse((self.out / "parts" / "OLD.scad").exists())


class WriteGuardTest(unittest.TestCase):
    def testRefusesDirNotNamedGenerated(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                generate.write(lay("home-1800x1500.json"), pathlib.Path(tmp) / "output")

    def testNonScadFileInPartsSurvives(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = pathlib.Path(tmp) / "generated"
            (out / "parts").mkdir(parents=True)
            (out / "parts" / "README.txt").write_text("keep me")
            generate.write(lay("home-1800x1500.json"), out)
            self.assertTrue((out / "parts" / "README.txt").exists())


def load(name):
    return json.loads((ROOT / "params" / name).read_text())


class BedPartsTest(unittest.TestCase):
    def testSmallBedAddsMiddleSegments(self):
        parts = byId(generate.parts(window.layout(dict(load("bench-600.json"), bed=[180, 180, 180]))))
        self.assertEqual((parts["S"]["qty"], parts["T"]["qty"], parts["SB"]["qty"]), (1, 1, 1))

    def testEveryLengthFitsTheSmallBed(self):
        for p in generate.parts(window.layout(dict(load("home-1800x1500.json"), bed=[180, 180, 180]))):
            if p["length"] is not None:
                self.assertLessEqual(p["length"], 164.0, p["id"])


class WriteBedTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.out = pathlib.Path(self.tmp.name) / "generated"

    def tearDown(self):
        self.tmp.cleanup()

    def testDimsScadCarriesTheBedLimit(self):
        generate.write(window.layout(dict(load("bench-600.json"), bed=[500, 500, 500])), self.out)
        self.assertIn("MAX_SEG = 484.0;\n", (self.out / "dims.scad").read_text())

    def testDimsScadIsUnchangedForTheDefaultBed(self):
        generate.write(lay("bench-600.json"), self.out)
        text = (self.out / "dims.scad").read_text()
        self.assertIn("MAX_SEG = 240.0;\n", text)
        self.assertNotIn("BED_MARGIN", text)


class BedFitTest(unittest.TestCase):
    def testBedFitPassesForBothReferenceWindows(self):
        for name in ("home-1800x1500.json", "bench-600.json"):
            x = lay(name)
            check = generate.bed_fit(x, generate.parts(x))
            self.assertEqual(check, {"name": "bed_fit", "ok": True, "msg": "every part fits the 256 x 256 x 256 mm bed"})

    def testBedFitFailsWhenFixedPartsAreTooBig(self):
        x = window.layout(dict(load("bench-600.json"), bed=[90, 90, 90]))
        check = generate.bed_fit(x, generate.parts(x))
        self.assertFalse(check["ok"])
        self.assertEqual(check["msg"], "parts too big for the 90 x 90 x 90 mm bed: GW 6.795 x 24 x 100, GF 3 x 24 x 100")

    def testBedFitUsesProfileEnvelopeTimesLength(self):
        check = generate.bed_fit({"bed": [256, 60, 60], "params": {"glazing": "igu"}},
                                 [{"id": "H", "module": "frame_segment", "length": 237.14}])
        self.assertEqual(check["msg"], "parts too big for the 256 x 60 x 60 mm bed: H 58 x 63 x 237.14")

    def testPartWithoutEnvelopeFails(self):
        check = generate.bed_fit({"bed": [256, 256, 256], "params": {"glazing": "igu"}},
                                 [{"id": "ZZ", "module": "zz", "length": None}])
        self.assertFalse(check["ok"])
        self.assertIn("ZZ (no envelope)", check["msg"])

    def testEnvelopeTableCoversEveryPartShape(self):
        variants = [load(n) for n in ("home-1800x1500.json", "bench-600.json")]
        variants += [dict(v, bed=[180, 180, 180]) for v in variants]
        variants += [dict(variants[0], glazing=g) for g in ("twinwall", "acrylic")] + [dict(variants[1], glazing="igu")]
        for p in variants:
            for pt in generate.parts(window.layout(p)):
                key = generate.envelope_key(pt, p["glazing"])
                self.assertEqual(len(generate.ENVELOPES[key]), 2 if pt["length"] is not None else 3, key)


class ScreenOffPartsTest(unittest.TestCase):
    def setUp(self):
        self.on = byId(generate.parts(lay("home-1800x1500.json")))
        self.off = byId(generate.parts(window.layout(dict(load("home-1800x1500.json"), screen=False))))

    def testScreenPartsAreOmitted(self):
        self.assertEqual(set(self.on) - set(self.off), {"NH", "NV", "CN", "HG", "HS"})

    def testHeadSegmentsLoseTheHingeBosses(self):
        self.assertEqual(self.off["H"]["call"], 'frame_segment("sash_rebate", 237.14, "H", bosses=false);')

    def testOtherPartsAreUnchanged(self):
        for pid, pt in self.off.items():
            if pid != "H":
                self.assertEqual(pt, self.on[pid], pid)


class MinSegmentPartsTest(unittest.TestCase):
    def testBigBedBenchGetsTwoTransomEndsAndAHeadSegmentPerHinge(self):
        x = window.layout(dict(load("bench-600.json"), bed=[500, 500, 500]))
        parts = byId(generate.parts(x))
        self.assertNotIn("T", parts)
        self.assertEqual((parts["TE"]["qty"], parts["H"]["qty"], parts["HG"]["qty"]), (2, 2, 2))
        te, sbe = bossCentres(parts)
        self.assertLessEqual(abs(te - sbe), window.D["CAM_ALIGN_TOL"])
        self.assertTrue(generate.bed_fit(x, generate.parts(x))["ok"])

    def testWideWindowOnABigBedHasAHeadSegmentPerHinge(self):
        for w in (1080, 1090, 1100):
            parts = byId(generate.parts(window.layout(dict(load("home-1800x1500.json"), opening_w=w,
                                                           bed=[500, 500, 500]))))
            self.assertEqual(parts["HG"]["qty"], 3, w)
            self.assertGreaterEqual(parts["H"]["qty"], parts["HG"]["qty"], w)

    def testHingeQuantityComesFromTheLayout(self):
        x = lay("home-1800x1500.json")
        self.assertEqual(byId(generate.parts(dict(x, hinges=4)))["HS"]["qty"], 4)


class GlazedEnvelopeTest(unittest.TestCase):
    def testEnvelopeKeyQualifiesOnlyBeadsByGlazing(self):
        self.assertEqual(generate.envelope_key({"id": "BFH", "module": "bead"}, "twinwall"), "BFH/twinwall")
        self.assertEqual(generate.envelope_key({"id": "H", "module": "frame_segment"}, "twinwall"), "H")

    def testTwinwallWindowUsesTheTwinwallBeadEnvelope(self):
        bed = [256, 256, 15]
        for glazing, msg in (("igu", "every part fits the 256 x 256 x 15 mm bed"),
                             ("twinwall", "parts too big for the 256 x 256 x 15 mm bed: BFH 18 x 19.8 x 213, "
                                          "BFV 18 x 19.8 x 213, BSH 18 x 19.8 x 230.29, BSV 18 x 19.8 x 181")):
            x = window.layout(dict(load("home-1800x1500.json"), glazing=glazing))
            beads = [pt for pt in generate.parts(x) if pt["module"] == "bead"]
            self.assertEqual(generate.bed_fit(dict(x, bed=bed), beads)["msg"], msg, glazing)


class WriteScreenOffTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.out = pathlib.Path(self.tmp.name) / "generated"
        self.lay = window.layout(dict(load("home-1800x1500.json"), screen=False))

    def tearDown(self):
        self.tmp.cleanup()

    def wrappers(self):
        return {f.stem for f in (self.out / "parts").glob("*.scad")}

    def testScreenWrappersAreNotWritten(self):
        generate.write(self.lay, self.out)
        self.assertFalse(self.wrappers() & {"NH", "NV", "CN", "HG", "HS"})
        self.assertEqual(self.wrappers(), {p["id"] for p in generate.parts(self.lay)})

    def testStaleScreenWrappersAreRemoved(self):
        generate.write(lay("home-1800x1500.json"), self.out)
        generate.write(self.lay, self.out)
        self.assertFalse(self.wrappers() & {"NH", "NV", "CN", "HG", "HS"})

    def testHeadWrapperHasNoBosses(self):
        generate.write(self.lay, self.out)
        self.assertEqual((self.out / "parts" / "H.scad").read_text(),
                         'use <../../parts/frame_segment.scad>\nframe_segment("sash_rebate", 237.14, "H", bosses=false);\n')

    def testLayoutScadHasNoScreenMembers(self):
        generate.write(self.lay, self.out)
        text = (self.out / "layout.scad").read_text()
        self.assertNotIn("SEG_SCREEN_", text)
        self.assertNotIn("N_SCREEN_", text)
        self.assertIn("SEG_HEAD = 237.14;\nN_HEAD = 7;\n", text)

    def testCsvsCarryNoScreenPartsOrTubes(self):
        generate.write(self.lay, self.out)
        ids = {r["id"] for r in csv.DictReader((self.out / "parts.csv").read_text().splitlines())}
        self.assertFalse(ids & {"NH", "NV", "CN", "HG", "HS"})
        cores = {r["core"] for r in csv.DictReader((self.out / "cutlist.csv").read_text().splitlines())}
        self.assertNotIn("alu10", cores)

    def testParamsJsonKeepsTheScreenKey(self):
        generate.write(self.lay, self.out)
        self.assertIs(json.loads((self.out / "params.json").read_text())["screen"], False)


class MainTest(unittest.TestCase):
    def runMain(self, params):
        with tempfile.TemporaryDirectory() as tmp:
            path = pathlib.Path(tmp) / "params.json"
            path.write_text(json.dumps(params))
            out = io.StringIO()
            with mock.patch.object(generate, "write", generate.parts), contextlib.redirect_stdout(out):
                rc = generate.main(["generate.py", str(path)])
        self.assertEqual(rc, 0)
        return out.getvalue().splitlines()

    def testNoBedKeyPrintsNoBedFitLine(self):
        lines = self.runMain(load("bench-600.json"))
        self.assertEqual(len(lines), 5)
        self.assertFalse([x for x in lines if "fits the" in x or "too big for the" in x])

    def testBedKeyPrintsTheBedFitLine(self):
        lines = self.runMain(dict(load("bench-600.json"), bed=[256, 256, 256]))
        self.assertEqual(len(lines), 6)
        self.assertEqual(lines[-1], "ok       every part fits the 256 x 256 x 256 mm bed")

    def testBedFitFailureIsAWarning(self):
        lines = self.runMain(dict(load("bench-600.json"), bed=[90, 90, 90]))
        self.assertEqual(lines[-1], "WARNING  parts too big for the 90 x 90 x 90 mm bed: GW 6.795 x 24 x 100, GF 3 x 24 x 100")


def bayCams(lay, parts):
    D = window.D
    run, sash_seg = parts["TE"]["length"], parts["SBE"]["length"]
    dz = float(re.search(r"boss_dz=([0-9.]+)", parts["SBE"]["call"]).group(1))
    out = []
    for i in range(lay["bays"]):
        x0 = D["FRAME_W"] if i == 0 else lay["mullions"][i - 1] + D["MULLION_W"] / 2
        s0 = D["FRAME_BODY"] if i == 0 else lay["mullions"][i - 1] + D["MULLION_HALF_BODY"]
        s0 += D["SASH_GAP"]
        cams = [x0 + D["JOINT_GAP"] + run / 2, x0 + lay["bay_w"] - D["JOINT_GAP"] - run / 2]
        keepers = [s0 + D["SASH_W"] + D["JOINT_GAP"] + sash_seg / 2 - dz,
                   s0 + lay["sash"][0] - D["SASH_W"] - D["JOINT_GAP"] - sash_seg / 2 + dz]
        out.append((cams, keepers))
    return out


class BayPartsTest(unittest.TestCase):
    def setUp(self):
        self.lay = lay("home-1800x1500-2bay.json")
        self.parts = byId(generate.parts(self.lay))

    def qty(self, *ids):
        return tuple(self.parts[i]["qty"] for i in ids)

    def testNodeAndShoeParts(self):
        self.assertEqual(self.qty("SN", "HN", "TX", "MSL", "MST", "MSH"), (1, 1, 1, 2, 1, 1))
        self.assertEqual(self.parts["SN"]["call"], 'frame_node("sill", "SN");')
        self.assertEqual(self.parts["HN"]["call"], 'frame_node("sash_rebate", "HN");')
        self.assertEqual(self.parts["TX"]["call"], 'cross_node("TX");')
        self.assertEqual(self.parts["MSL"]["call"], 'mullion_shoe("mullion_glazing", "MSL");')
        self.assertEqual(self.parts["MSH"]["call"], 'mullion_shoe("mullion_sash", "MSH", head=true);')

    def testMullionSegments(self):
        self.assertEqual(self.parts["ML"]["call"], 'frame_segment("mullion_glazing", 210.75, "ML");')
        self.assertEqual(self.parts["MU"]["call"], 'frame_segment("mullion_sash", 223.5, "MU");')
        self.assertEqual(self.qty("ML", "MU"), (4, 2))

    def testRunsGetTheirOwnEndSegments(self):
        self.assertEqual(self.qty("H", "S", "SW", "T", "TE"), (8, 4, 4, 4, 4))
        self.assertEqual(self.parts["TE"]["call"], 'frame_segment("transom", 198.5, "TE", weep=true, bosses=true);')

    def testEveryBayGetsItsOwnSashScreenAndHardware(self):
        self.assertEqual(self.qty("SH", "SB", "SBE", "SV", "CS"), (6, 2, 4, 8, 8))
        self.assertEqual(self.qty("NH", "NV", "CN", "HG", "HS"), (16, 8, 8, 4, 4))
        self.assertEqual(self.qty("CMB", "CMH", "KP", "GW", "GF", "WC"), (4, 4, 4, 4, 12, 8))

    def testFrameCornersAndJambsAreUnchanged(self):
        self.assertEqual(self.qty("CH", "CSL", "CSR", "JN", "TSL", "TSR", "JL", "JU", "NS"), (2, 1, 1, 2, 1, 1, 8, 4, 8))

    def testBeadsPerPane(self):
        got = {k: (self.parts[k]["length"], self.parts[k]["qty"]) for k in ("BFH", "BFV", "BSH", "BSV")}
        self.assertEqual(got, {"BFH": (208.75, 16), "BFV": (213.0, 16), "BSH": (185.75, 16), "BSV": (181.0, 8)})

    def testEveryBayHasItsCamsOverItsKeepers(self):
        for cams, keepers in bayCams(self.lay, self.parts):
            for cam, keeper in zip(cams, keepers):
                self.assertLessEqual(abs(cam - keeper), window.D["CAM_ALIGN_TOL"])

    def testThreeBays(self):
        x = window.layout(dict(load("home-1800x1500.json"), max_pane=[900, 600]))
        parts = byId(generate.parts(x))
        self.assertEqual(tuple(parts[i]["qty"] for i in ("SN", "HN", "TX", "MSL", "MST", "MSH", "ML", "MU", "TE", "CMB")),
                         (2, 2, 2, 4, 2, 2, 8, 4, 6, 6))
        for cams, keepers in bayCams(x, parts):
            for cam, keeper in zip(cams, keepers):
                self.assertLessEqual(abs(cam - keeper), window.D["CAM_ALIGN_TOL"])

    def testOneBayHasNoMullionParts(self):
        self.assertEqual(generate.parts(window.layout(dict(load("home-1800x1500.json"), bays=1))),
                         generate.parts(lay("home-1800x1500.json")))

    def testAcrylicSpacersPerPane(self):
        parts = byId(generate.parts(window.layout(dict(load("home-1800x1500-2bay.json"), glazing="acrylic"))))
        self.assertEqual((parts["AC"]["qty"], parts["AFH"]["qty"], parts["AFV"]["qty"]), (16, 16, 16))


class WriteBaysTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.out = pathlib.Path(self.tmp.name) / "generated"

    def tearDown(self):
        self.tmp.cleanup()

    def testLayoutScadCarriesTheBays(self):
        generate.write(lay("home-1800x1500-2bay.json"), self.out)
        text = (self.out / "layout.scad").read_text()
        self.assertIn("SEG_MULLION_LOWER = 210.75;\nN_MULLION_LOWER = 4;\n", text)
        self.assertTrue(text.endswith("BAYS = 2;\nPITCH = 869.0;\nMULLIONS = [892.0];\n"))

    def testOneBayLayoutScadHasNoBayLines(self):
        generate.write(lay("home-1800x1500.json"), self.out)
        self.assertNotIn("BAYS", (self.out / "layout.scad").read_text())

    def testNodeAndShoeWrappers(self):
        generate.write(lay("home-1800x1500-2bay.json"), self.out)
        self.assertEqual((self.out / "parts" / "SN.scad").read_text(), 'use <../../parts/frame_node.scad>\nframe_node("sill", "SN");\n')
        self.assertEqual((self.out / "parts" / "TX.scad").read_text(), 'use <../../parts/cross_node.scad>\ncross_node("TX");\n')
        self.assertEqual((self.out / "parts" / "MST.scad").read_text(),
                         'use <../../parts/mullion_shoe.scad>\nmullion_shoe("mullion_sash", "MST");\n')

    def testGlassAndCutlistPerBay(self):
        generate.write(lay("home-1800x1500-2bay.json"), self.out)
        glass = {r["pane"]: r for r in csv.DictReader((self.out / "glass.csv").read_text().splitlines())}
        self.assertEqual((glass["fixed"]["width_mm"], glass["fixed"]["qty"], glass["sash"]["qty"]), ("829", "2", "2"))
        cut = {r["member"]: r for r in csv.DictReader((self.out / "cutlist.csv").read_text().splitlines())}
        self.assertEqual((cut["mullion_lower"]["length_mm"], cut["mullion_upper"]["length_mm"]), ("876.0", "478.0"))


class MainBaysTest(unittest.TestCase):
    def testBayKeysPrintTheTwoNewChecks(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = pathlib.Path(tmp) / "params.json"
            path.write_text(json.dumps(load("home-1800x1500-2bay.json")))
            out = io.StringIO()
            with mock.patch.object(generate, "write", generate.parts), contextlib.redirect_stdout(out):
                self.assertEqual(generate.main(["generate.py", str(path)]), 0)
        lines = out.getvalue().splitlines()
        self.assertEqual(lines[0].split(" -> ")[0], "home-1800x1500-2bay: 43 part types, 226 prints")
        self.assertEqual(lines[-2:], ["ok       2 bays: fixed panes 829 x 878, sash panes 737 x 388 fit a 1200 x 900 mm sheet",
                                      "ok       lower mullion deflects 0.6 mm at 0.7 kPa over 848 mm, limit span/175 = 4.8 mm"])


class BayEnvelopeTest(unittest.TestCase):
    def testBedFitCoversTheNewParts(self):
        x = lay("home-1800x1500-2bay.json")
        self.assertEqual(generate.bed_fit(x, generate.parts(x))["msg"], "every part fits the 256 x 256 x 256 mm bed")
        small = window.layout(dict(load("home-1800x1500-2bay.json"), bed=[180, 180, 180]))
        self.assertTrue(generate.bed_fit(small, generate.parts(small))["ok"])

    def testEnvelopeTableHasEveryMullionPart(self):
        for pid, dims in (("SN", 3), ("HN", 3), ("TX", 3), ("MSL", 3), ("MST", 3), ("MSH", 3), ("ML", 2), ("MU", 2)):
            self.assertEqual(len(generate.ENVELOPES[pid]), dims, pid)


def thinBench():
    return window.layout({**json.loads((ROOT / "params" / "bench-600.json").read_text()), "acrylic_t": 3, "acrylic_gap": 12})


class SandwichPartsTest(unittest.TestCase):
    def testDefaultAcrylicCallsAreUnchanged(self):
        parts = byId(generate.parts(lay("bench-600.json")))
        self.assertTrue(parts["BFH"]["call"].endswith(', "BFH");'))
        self.assertTrue(parts["AFH"]["call"].endswith(', "AFH");'))
        self.assertEqual(parts["AC"]["call"], 'acrylic_spacer_corner("AC");')

    def testBeadsCarryTheSandwichThickness(self):
        parts = byId(generate.parts(thinBench()))
        for pid in ("BFH", "BFV", "BSH", "BSV"):
            self.assertTrue(parts[pid]["call"].startswith('bead("acrylic", '), pid)
            self.assertTrue(parts[pid]["call"].endswith(f', "{pid}", 18);'), parts[pid]["call"])

    def testSpacersCarryTheGap(self):
        parts = byId(generate.parts(thinBench()))
        for pid in ("AFH", "AFV", "ASH", "ASV"):
            self.assertTrue(parts[pid]["call"].endswith(f', "{pid}", 12);'), parts[pid]["call"])
        self.assertEqual(parts["AC"]["call"], 'acrylic_spacer_corner("AC", 12);')

    def testPartCountsDoNotChange(self):
        default = {p["id"]: p["qty"] for p in generate.parts(lay("bench-600.json"))}
        thin = {p["id"]: p["qty"] for p in generate.parts(thinBench())}
        self.assertEqual(default, thin)

    def testDeeperBeadsAreCheckedAgainstTheBed(self):
        l = thinBench()
        parts = byId(generate.parts(l))
        default = generate.ENVELOPES["BFH/acrylic"]
        self.assertEqual(generate.part_envelope(parts["BFH"], l), [default[0] + 6, default[1]])
        self.assertEqual(generate.part_envelope(parts["BFH"], lay("bench-600.json")), default)

    def testSpacerEnvelopesFollowTheGap(self):
        l = thinBench()
        parts = byId(generate.parts(l))
        self.assertEqual(generate.part_envelope(parts["AFH"], l), [12.0, 12])
        self.assertEqual(generate.part_envelope(parts["AC"], l), [12, 27.0, 27.0])

    def testSettingBlocksFollowThePane(self):
        parts = byId(generate.parts(thinBench()))
        self.assertEqual(parts["GW"]["call"], 'setting_block("GW", wedge=true, pane_t=18);')
        self.assertEqual(parts["GF"]["call"], 'setting_block("GF", pane_t=18);')
        default = byId(generate.parts(lay("bench-600.json")))
        self.assertEqual(default["GW"]["call"], 'setting_block("GW", wedge=true);')
        twin = byId(generate.parts(window.layout({**json.loads((ROOT / "params" / "bench-600.json").read_text()),
                                                   "glazing": "twinwall"})))
        self.assertEqual(twin["GF"]["call"], 'setting_block("GF", pane_t=16);')

    def testEnvelopesAreComputedForTheSandwich(self):
        l = thinBench()
        parts = byId(generate.parts(l))
        D = window.D
        self.assertEqual(generate.part_envelope(parts["BFH"], l)[0], D["BEAD_T"] + 6)
        self.assertEqual(generate.part_envelope(parts["AFH"], l), [D["SPACER_W"], 12])
        self.assertEqual(generate.part_envelope(parts["GF"], l), [3.0, 18, 100.0])
        self.assertEqual(generate.part_envelope(parts["GW"], lay("bench-600.json")), generate.ENVELOPES["GW"])

    def testExplicitDefaultSandwichKeepsTheDefaultCalls(self):
        l = window.layout({**json.loads((ROOT / "params" / "bench-600.json").read_text()), "acrylic_t": 4, "acrylic_gap": 16})
        self.assertEqual([p["call"] for p in generate.parts(l)], [p["call"] for p in generate.parts(lay("bench-600.json"))])

    def testGlassSpecNamesThePanels(self):
        self.assertEqual(generate.glass_spec(lay("bench-600.json")), generate.GLASS_SPEC["acrylic"])
        self.assertEqual(generate.glass_spec(thinBench()),
                         "2 x 3 mm clear acrylic, 12 mm gap, cut to size, protective film on until assembly")
        self.assertEqual(generate.glass_spec(lay("home-1800x1500.json")), generate.GLASS_SPEC["igu"])


def vslotLay(name, **changes):
    return window.layout({**json.loads((ROOT / "params" / name).read_text()), "core": "vslot", **changes})


class VslotPartsTest(unittest.TestCase):
    def testDefaultCallsHaveNoCore(self):
        for name in ("bench-600.json", "home-1800x1500.json", "home-1800x1500-2bay.json"):
            self.assertFalse([p["id"] for p in generate.parts(lay(name)) if "core" in p["call"]], name)

    def testBenchCallsAreAllVslot(self):
        parts = byId(generate.parts(vslotLay("bench-600.json")))
        self.assertEqual(parts["H"]["call"], 'frame_segment("sash_rebate", 232.5, "H", bosses=true, core="vslot");')
        self.assertEqual(parts["TE"]["call"].split(", ")[-1], 'core="vslot");')
        self.assertEqual(parts["CH"]["call"], 'corner_block("sash_rebate", "sash_rebate", "CH", core_a="vslot", core_b="vslot");')
        self.assertEqual(parts["JN"]["call"], 'jamb_node("JN", core="vslot");')
        self.assertEqual(parts["TSL"]["call"], 'transom_shoe("TSL", mirrored=true, core="vslot");')

    def testHomeFallbacksKeepTheirCalls(self):
        parts = byId(generate.parts(vslotLay("home-1800x1500.json")))
        for pid in ("SH", "SB", "SBE", "T", "TE", "TSL", "TSR"):
            self.assertNotIn("core", parts[pid]["call"], pid)
        self.assertEqual(parts["CS"]["call"], 'corner_block("sash", "sash", "CS", core_b="vslot");')
        self.assertIn('core="vslot"', parts["SV"]["call"])

    def testStandardUpperJambStaysInTheMovedPocket(self):
        parts = byId(generate.parts(vslotLay("home-1800x1500.json", vslot_stock=400)))
        self.assertTrue(parts["JU"]["call"].endswith(', core="alu20");'))
        self.assertTrue(parts["CH"]["call"].endswith('core_a="vslot", core_b="alu20");'))

    def testTwoBayNodesAndShoes(self):
        parts = byId(generate.parts(window.layout({**json.loads((ROOT / "params" / "home-1800x1500-2bay.json").read_text()), "core": "vslot"})))
        self.assertEqual(parts["HN"]["call"], 'frame_node("sash_rebate", "HN", core="vslot");')
        self.assertEqual(parts["MSH"]["call"], 'mullion_shoe("mullion_sash", "MSH", head=true, core="vslot");')
        self.assertEqual(parts["TX"]["call"], 'cross_node("TX");')

    def testCutlistListsThePieces(self):
        with tempfile.TemporaryDirectory() as d:
            path = pathlib.Path(d) / "cut.csv"
            generate.write_cutlist(vslotLay("home-1800x1500.json"), path)
            with path.open() as f:
                rows = list(csv.reader(f))
        self.assertEqual(rows[1:3], [["head 1/2", "vslot2020", "919.8", "1"], ["head 2/2", "vslot2020", "801.2", "1"]])


if __name__ == "__main__":
    unittest.main()
