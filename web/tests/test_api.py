"""Unit tests for web/api.py."""
import contextlib
import io
import json
import pathlib
import shutil
import sys
import tempfile
import unittest
import zipfile
from unittest import mock

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

import api  # noqa: E402
import fake_box  # noqa: E402


def ref(name):
    return json.loads((api.ROOT / "params" / f"{name}.json").read_text())


class ValidateTest(unittest.TestCase):
    def errors(self, **changes):
        return api.validate(dict(api.DEFAULTS, **changes))[1]

    def testDefaultsAreValid(self):
        self.assertEqual(api.validate({}), (api.DEFAULTS, {}))

    def testReferenceParamsGainTheNewKeys(self):
        params, errors = api.validate(ref("bench-600"))
        self.assertEqual(errors, {})
        self.assertEqual(list(params), list(api.DEFAULTS))
        self.assertEqual((params["screen"], params["bed"]), (True, [256, 256, 256]))

    def testBadNames(self):
        for name in ("My-Window", "", "a" * 41, "../x", "a b", 7):
            self.assertIn("name", self.errors(name=name), name)

    def testRanges(self):
        self.assertEqual(self.errors(opening_w=299), {"opening_w": "300-3000 mm"})
        self.assertEqual(self.errors(opening_h=3001), {"opening_h": "300-3000 mm"})
        self.assertEqual(self.errors(fix_gap=21), {"fix_gap": "0-20 mm"})
        self.assertEqual(self.errors(awning_h=149), {"awning_h": "at least 150 mm"})

    def testNumbersMustBeNumbers(self):
        for value in ("1800", True, None, float("nan")):
            self.assertIn("opening_w", self.errors(opening_w=value), value)

    def testChoices(self):
        self.assertIn("glazing", self.errors(glazing="glass"))
        self.assertIn("tier", self.errors(tier=4))
        self.assertIn("tier", self.errors(tier=True))
        self.assertEqual(self.errors(tier=2.0), {"tier": "1, 2 or 3"})
        self.assertIn("screen", self.errors(screen="yes"))

    def testBed(self):
        for bed in ([256, 256], [99, 256, 256], [256, 256, 501], "256", [256, "256", 256]):
            self.assertEqual(self.errors(bed=bed), {"bed": "three sizes, 100-500 mm each"}, bed)

    def testUnknownFieldsAreRejected(self):
        self.assertEqual(api.validate({"colour": "red"})[1], {"_form": "unknown fields: colour"})

    def testNonObjectIsRejected(self):
        self.assertIn("_form", api.validate([1, 2])[1])


class PreviewTest(unittest.TestCase):
    def setUp(self):
        self.home = api.preview(ref("home-1800x1500"))

    def testHomePreviewIsOk(self):
        self.assertEqual((self.home["ok"], self.home["errors"]), (True, {}))

    def testChecksEndWithBedFit(self):
        self.assertEqual([c["name"] for c in self.home["checks"]],
                         ["transom_deflection", "sash_weight", "segment_length", "cam_keeper", "bed_fit"])
        self.assertTrue(all(c["ok"] for c in self.home["checks"]))

    def testPartsTable(self):
        rows = {r["id"]: r for r in self.home["parts"]}
        self.assertEqual(len(rows), 35)
        self.assertEqual(rows["H"], {"id": "H", "name": "Head segment", "qty": 7, "length": 237.14, "role": "exterior"})

    def testEveryPartHasAName(self):
        for p in (ref("home-1800x1500"), ref("bench-600"), dict(ref("home-1800x1500"), bed=[180, 180, 180])):
            for row in api.preview(p)["parts"]:
                self.assertIn(row["id"], api.PART_NAMES)

    def testLayoutSummary(self):
        lay = self.home["layout"]
        self.assertEqual((lay["w"], lay["h"], lay["transom_c"], lay["max_seg"]), (1784, 1484, 941.0, 240.0))
        self.assertEqual(lay["glass"]["fixed"], (1698, 878))

    def testBomLines(self):
        timber = [i for i in self.home["bom"] if i["item"].startswith("Timber screw 10g x 75")]
        self.assertEqual(timber[0]["qty"], 38)

    def testDrawingAndAssemblyArePresent(self):
        self.assertIn("rects", self.home["drawing"])
        self.assertEqual(len(self.home["assembly"]), 63)

    def testPreviewIsJson(self):
        self.assertEqual(json.loads(json.dumps(self.home))["parts"][0]["id"], "H")

    def testPreviewCarriesAWeightEstimate(self):
        w = self.home["weight"]
        self.assertEqual(w["glass_kg"], 42.3)
        self.assertAlmostEqual(w["plastic_kg"], 20.25, delta=0.05)
        self.assertAlmostEqual(w["total_kg"], w["glass_kg"] + w["core_kg"] + w["plastic_kg"] + w["hardware_kg"], delta=0.15)
        self.assertGreater(w["kg_per_m2"], 10)

    def testFieldErrorStopsThePreview(self):
        r = api.preview(dict(api.DEFAULTS, opening_w=100))
        self.assertFalse(r["ok"])
        self.assertNotIn("layout", r)
        self.assertEqual(r["errors"], {"opening_w": "300-3000 mm"})

    def testGeneratorErrorBecomesAFieldError(self):
        r = api.preview(dict(api.DEFAULTS, opening_h=600))
        self.assertEqual(list(r["errors"]), ["awning_h"])
        self.assertTrue(r["errors"]["awning_h"].startswith("fixed pane height"))

    def testBadNameStillDraws(self):
        r = api.preview(dict(api.DEFAULTS, name="Bad Name"))
        self.assertFalse(r["ok"])
        self.assertEqual(list(r["errors"]), ["name"])
        self.assertIn("drawing", r)

    def testFailedCheckIsNotAnError(self):
        r = api.preview(dict(api.DEFAULTS, opening_w=3000))
        self.assertTrue(r["ok"])
        self.assertEqual([c["name"] for c in r["checks"] if not c["ok"]], ["transom_deflection"])

    def testScreenOff(self):
        r = api.preview(dict(api.DEFAULTS, screen=False))
        self.assertFalse({"NH", "NV", "CN", "HG", "HS"} & {row["id"] for row in r["parts"]})
        self.assertFalse([i for i in r["bom"] if i["group"] == "Screen"])


class SaveParamsTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self.tmp.name)
        (self.root / "params").mkdir()

    def tearDown(self):
        self.tmp.cleanup()

    def params(self, **changes):
        return api.validate(dict(api.DEFAULTS, **changes))[0]

    def testWritesTheParamsFile(self):
        path, changed = api.save_params(self.params(), self.root)
        self.assertEqual((path, changed), (self.root / "params" / "my-window.json", True))
        self.assertEqual(json.loads(path.read_text()), api.DEFAULTS)
        self.assertIn('  "bed": [256, 256, 256]\n}\n', path.read_text())

    def testFormatMatchesTheReferenceFiles(self):
        for name in ("bench-600", "home-1800x1500"):
            self.assertEqual(api.dumps_params(ref(name)), (api.ROOT / "params" / f"{name}.json").read_text())

    def testEquivalentFileIsKeptAsItIs(self):
        text = (api.ROOT / "params" / "bench-600.json").read_text()
        (self.root / "params" / "bench-600.json").write_text(text)
        self.assertFalse(api.save_params(api.validate(ref("bench-600"))[0], self.root)[1])
        self.assertEqual((self.root / "params" / "bench-600.json").read_text(), text)

    def testReferenceWindowIsNotOverwritten(self):
        (self.root / "params" / "bench-600.json").write_text((api.ROOT / "params" / "bench-600.json").read_text())
        with self.assertRaisesRegex(ValueError, "reference window"):
            api.save_params(api.validate(dict(ref("bench-600"), opening_w=700))[0], self.root)

    def testReferenceRefusalNamesTheKeysThatDiffer(self):
        (self.root / "params" / "bench-600.json").write_text((api.ROOT / "params" / "bench-600.json").read_text())
        for changes, keys in ((dict(opening_w=700), "opening_w"), (dict(max_pane=[1200, 900]), "max_pane"),
                              (dict(opening_w=700, awning_h=250, max_pane=[1200, 900]), "awning_h, max_pane, opening_w")):
            with self.assertRaisesRegex(ValueError, rf"^bench-600 is a reference window \(differs in: {keys}\); pick another name$"):
                api.save_params(api.validate(dict(ref("bench-600"), **changes))[0], self.root)

    def testOwnWindowIsOverwritten(self):
        api.save_params(self.params(), self.root)
        self.assertTrue(api.save_params(self.params(opening_w=1200), self.root)[1])
        self.assertEqual(json.loads((self.root / "params" / "my-window.json").read_text())["opening_w"], 1200)

    def testBadNameNeverReachesTheFilesystem(self):
        with self.assertRaises(ValueError):
            api.save_params(self.params(name="../evil"), self.root)
        self.assertEqual(list(self.root.rglob("*")), [self.root / "params"])

    def testClearStlsEmptiesOnlyThatWindow(self):
        for name in ("my-window", "other"):
            out = self.root / "cad" / "stl" / name
            out.mkdir(parents=True)
            (out / "H.stl").write_bytes(b"x")
            (out / "notes.txt").write_text("keep")
        api.clear_stls("my-window", self.root)
        self.assertEqual(sorted(f.name for f in (self.root / "cad" / "stl" / "my-window").iterdir()), ["notes.txt"])
        self.assertTrue((self.root / "cad" / "stl" / "other" / "H.stl").exists())

    def testClearStlsWithoutAFolder(self):
        api.clear_stls("my-window", self.root)
        self.assertFalse((self.root / "cad").exists())


class StatusAndZipTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self.tmp.name)
        (self.root / "params").mkdir()
        shutil.copy(api.ROOT / "params" / "bench-600.json", self.root / "params")
        self.out = self.root / "cad" / "stl" / "bench-600"

    def tearDown(self):
        self.tmp.cleanup()

    def fakeRender(self, skip=()):
        self.out.mkdir(parents=True)
        for pt in api.load("bench-600", self.root)[2]:
            if pt["id"] not in skip:
                (self.out / f"{pt['id']}.stl").write_bytes(fake_box.box_stl(10, 20, pt["length"] or 20))

    def testLoadUnknownWindowRaises(self):
        with self.assertRaises(LookupError):
            api.load("nope", self.root)

    def testRenderedPartsPass(self):
        self.fakeRender()
        params, lay, plist = api.load("bench-600", self.root)
        self.assertEqual({pid: e for pid, e in api.part_status("bench-600", lay, plist, self.root).items() if e}, {})

    def testMissingStlsAreReported(self):
        params, lay, plist = api.load("bench-600", self.root)
        status = api.part_status("bench-600", lay, plist, self.root)
        self.assertEqual(status["H"], ["H: missing H.stl"])

    def testWriteBomMatchesTheCommandLine(self):
        self.fakeRender()
        params, lay, plist = api.load("bench-600", self.root)
        api.write_bom("bench-600", lay, plist, self.root / "web-bom", root=self.root)
        (self.root / "bom").mkdir()
        with mock.patch.object(api.build_bom, "ROOT", self.root), contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(api.build_bom.main(["build_bom.py", "bench-600"]), 0)
        for f in ("bench-600.md", "bench-600.csv", "bench-600-parts.csv", "bench-600-cutlist.csv", "bench-600-glass.csv"):
            self.assertEqual((self.root / "web-bom" / f).read_text(), (self.root / "bom" / f).read_text(), f)

    def testZipHasEveryFile(self):
        self.fakeRender()
        name, data = api.build_zip("bench-600", root=self.root)
        z = zipfile.ZipFile(io.BytesIO(data))
        names = z.namelist()
        self.assertEqual(name, "bench-600-openwindow.zip")
        self.assertEqual(names[:5], ["README.txt", "parts.csv", "cutlist.csv", "glass.csv", "BOM.md"])
        self.assertEqual(names[-1], "params.json")
        self.assertEqual(len([n for n in names if n.startswith("stl/")]), 37)
        self.assertIn("OpenWindow-Guide.pdf", names)
        self.assertTrue(zipfile.ZipFile(io.BytesIO(data)).read("OpenWindow-Guide.pdf").startswith(b"%PDF-"))
        self.assertEqual(z.read("stl/H_x2.stl"), (self.out / "H.stl").read_bytes())
        self.assertEqual(z.read("params.json"), (api.ROOT / "params" / "bench-600.json").read_bytes())
        self.assertTrue(z.read("README.txt").decode().startswith("OpenWindow: bench-600\n"))

    def testZipParamsAreReadOnce(self):
        self.fakeRender()
        path = self.root / "params" / "bench-600.json"
        original = path.read_bytes()
        real = api.part_status

        def status(*args):
            path.write_text(api.dumps_params(dict(json.loads(original), glazing="twinwall")))
            return real(*args)

        with mock.patch.object(api, "part_status", side_effect=status):
            z = zipfile.ZipFile(io.BytesIO(api.build_zip("bench-600", root=self.root)[1]))
        self.assertEqual(z.read("params.json"), original)

    def testZipNeedsEveryPart(self):
        self.fakeRender(skip={"H"})
        with self.assertRaisesRegex(api.NotReady, "H"):
            api.build_zip("bench-600", root=self.root)

    def testPartialZipLeavesOutMissingParts(self):
        self.fakeRender(skip={"H", "JL"})
        z = zipfile.ZipFile(io.BytesIO(api.build_zip("bench-600", partial=True, root=self.root)[1]))
        self.assertNotIn("stl/H_x2.stl", z.namelist())
        readme = z.read("README.txt").decode()
        self.assertTrue(readme.startswith("PARTIAL ZIP"))
        self.assertIn("  H, JL\n", readme)
        self.assertIn("Filament excludes unrendered parts: H, JL.", z.read("BOM.md").decode())


class BaysValidateTest(unittest.TestCase):
    def errors(self, **changes):
        return api.validate(dict(api.DEFAULTS, **changes))[1]

    def testOptionalKeysPassThrough(self):
        params, errors = api.validate(dict(api.DEFAULTS, max_pane=[1200, 900], bays=3))
        self.assertEqual(errors, {})
        self.assertEqual((params["max_pane"], params["bays"]), ([1200, 900], 3))
        self.assertEqual(list(params)[-2:], ["max_pane", "bays"])

    def testDefaultsHaveNoLimit(self):
        self.assertNotIn("max_pane", api.validate({})[0])
        self.assertNotIn("bays", api.validate({})[0])

    def testBadMaxPane(self):
        for value in ([1200], [1200, 900, 1], [199, 900], [1200, 3001], [1200, "900"], "1200,900", None, [True, 900]):
            self.assertEqual(self.errors(max_pane=value), {"max_pane": "two sizes, 200-3000 mm each"}, value)

    def testBadBays(self):
        for value in (0, 2.0, True, "2", None):
            self.assertEqual(self.errors(bays=value), {"bays": "a whole number, 1 or more"}, value)


class BaysPreviewTest(unittest.TestCase):
    def setUp(self):
        self.two = api.preview(ref("home-1800x1500-2bay"))

    def testTwoBayPreviewIsOk(self):
        self.assertEqual((self.two["ok"], self.two["errors"]), (True, {}))

    def testChecksIncludePaneFitAndMullionDeflection(self):
        self.assertEqual([c["name"] for c in self.two["checks"]],
                         ["transom_deflection", "sash_weight", "segment_length", "cam_keeper", "pane_fit",
                          "mullion_deflection", "bed_fit"])
        self.assertTrue(all(c["ok"] for c in self.two["checks"]))

    def testLayoutSummaryCarriesTheBays(self):
        lay = self.two["layout"]
        self.assertEqual((lay["bays"], lay["auto_bays"], lay["pitch"], lay["mullions"]), (2, 2, 869.0, [892.0]))

    def testPartsTableHasTheNewParts(self):
        rows = {r["id"]: r for r in self.two["parts"]}
        self.assertEqual(len(rows), 43)
        self.assertEqual(rows["TX"], {"id": "TX", "name": "Transom cross-node, mullion slots", "qty": 1, "length": None,
                                      "role": "exterior"})
        for row in rows.values():
            self.assertIn(row["id"], api.PART_NAMES)

    def testAssemblyHasEveryFramePart(self):
        self.assertEqual(len(self.two["assembly"]), 85)

    def testTooTallPaneIsAMaxPaneError(self):
        r = api.preview(dict(ref("home-1800x1500-2bay"), max_pane=[800, 800]))
        self.assertEqual(list(r["errors"]), ["max_pane"])
        self.assertIn("second horizontal transom", r["errors"]["max_pane"])

    def testTooFewBaysIsABaysError(self):
        r = api.preview(dict(ref("home-1800x1500-2bay"), bays=1))
        self.assertEqual(r["errors"], {"bays": "bays must be at least 2 for a 1200 x 900 mm max_pane, got 1"})

    def testTheTwoBayWindowIsAReference(self):
        self.assertIn("home-1800x1500-2bay", api.REFERENCE_NAMES)
        self.assertEqual(api.dumps_params(ref("home-1800x1500-2bay")),
                         (api.ROOT / "params" / "home-1800x1500-2bay.json").read_text())


class SandwichApiTest(unittest.TestCase):
    def thin(self, **changes):
        return dict(ref("bench-600"), name="thin-bench", acrylic_t=3, acrylic_gap=12, **changes)

    def testSandwichKeysPassThrough(self):
        params, errors = api.validate(self.thin())
        self.assertEqual(errors, {})
        self.assertEqual((params["acrylic_t"], params["acrylic_gap"]), (3, 12))

    def testLimitsAreAccepted(self):
        for t_, gap in ((2, 8), (6, 12), (2, 16)):
            self.assertEqual(api.validate(self.thin() | {"acrylic_t": t_, "acrylic_gap": gap})[1], {}, (t_, gap))

    def testDefaultsHaveNoSandwichKeys(self):
        params = api.validate({})[0]
        self.assertNotIn("acrylic_t", params)
        self.assertNotIn("acrylic_gap", params)

    def testBadThickness(self):
        for value in (1, 7, True, "3", None):
            self.assertEqual(api.validate(self.thin() | {"acrylic_t": value})[1], {"acrylic_t": "2-6 mm"}, value)

    def testBadGap(self):
        for value in (7, 17, False, "12", None):
            self.assertEqual(api.validate(self.thin() | {"acrylic_gap": value})[1], {"acrylic_gap": "8-16 mm"}, value)

    def testGeneratorErrorsGoToTheirField(self):
        wrong = api.preview(dict(ref("home-1800x1500"), name="x", acrylic_t=3))
        self.assertEqual(wrong["errors"], {"acrylic_t": "acrylic_t only applies to acrylic glazing, got glazing igu"})
        thick = api.preview(dict(ref("bench-600"), name="x", acrylic_t=5))
        self.assertEqual(thick["errors"],
                         {"acrylic_t": "acrylic_t: 2 x 5 + 16 = 26 mm does not fit the 24 mm glazing pocket"})

    def testPreviewCarriesTheSandwich(self):
        out = api.preview(self.thin())
        self.assertEqual((out["ok"], out["errors"]), (True, {}))
        self.assertEqual(out["layout"]["sandwich"], {"t": 3, "gap": 12, "custom": True})
        calls = {r["id"]: r for r in out["parts"]}
        self.assertIn("AC", calls)


class VslotApiTest(unittest.TestCase):
    def vslot(self, **changes):
        return dict(ref("bench-600"), name="vslot-bench", core="vslot", **changes)

    def testVslotKeysPassThrough(self):
        params, errors = api.validate(self.vslot(vslot_stock=1200))
        self.assertEqual(errors, {})
        self.assertEqual((params["core"], params["vslot_stock"]), ("vslot", 1200))

    def testDefaultsHaveNoCoreKeys(self):
        params = api.validate({})[0]
        self.assertNotIn("core", params)
        self.assertNotIn("vslot_stock", params)

    def testStockLimitsAreAccepted(self):
        for stock in (300, 1000, 6000):
            self.assertEqual(api.validate(self.vslot(vslot_stock=stock))[1], {}, stock)

    def testBadCore(self):
        for value in ("tube", "", None, True, 2020):
            self.assertEqual(api.validate(self.vslot() | {"core": value})[1],
                             {"core": "vslot, or leave it out for standard tubes"}, value)

    def testBadStock(self):
        for value in (299, 6001, True, "1000", None):
            self.assertEqual(api.validate(self.vslot(vslot_stock=value))[1], {"vslot_stock": "300-6000 mm"}, value)

    def testStockNeedsTheCore(self):
        raw = dict(ref("bench-600"), name="x", vslot_stock=1000)
        self.assertEqual(api.validate(raw)[1], {"vslot_stock": "only with core vslot"})

    def testPreviewReportsTheCores(self):
        out = api.preview(self.vslot())
        self.assertTrue(out["ok"], out["errors"])
        core = next(c for c in out["checks"] if c["name"] == "core")
        self.assertEqual(core["msg"], "V-slot 2020: 5 pieces of 1000 mm")
        self.assertEqual(out["layout"]["vslot"]["stock"], 1000)
        self.assertEqual(len(out["layout"]["vslot"]["plan"]), 5)

    def testStandardPreviewHasNoCoreCheck(self):
        out = api.preview(dict(ref("bench-600"), name="x"))
        self.assertNotIn("core", [c["name"] for c in out["checks"]])
        self.assertIsNone(out["layout"]["vslot"])


if __name__ == "__main__":
    unittest.main()
