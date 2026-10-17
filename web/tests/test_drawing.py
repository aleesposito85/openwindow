"""Unit tests for web/drawing.py."""
import json
import pathlib
import sys
import unittest

WEB = pathlib.Path(__file__).resolve().parent.parent
ROOT = WEB.parent
sys.path.insert(0, str(WEB))
sys.path.insert(0, str(ROOT / "tools"))

import drawing  # noqa: E402
import generate  # noqa: E402
import stl  # noqa: E402
import window  # noqa: E402

D = window.D


def lay(name, **changes):
    return window.layout(dict(json.loads((ROOT / "params" / f"{name}.json").read_text()), **changes))


def rects(d, kind):
    return [(r["x"], r["y"], r["w"], r["h"]) for r in d["rects"] if r["kind"] == kind]


class HomeFrontTest(unittest.TestCase):
    def setUp(self):
        self.d = drawing.front(lay("home-1800x1500"))

    def testOpeningOutline(self):
        self.assertEqual(rects(self.d, "opening"), [(-8, -8, 1800, 1500)])

    def testFrameMembers(self):
        self.assertEqual(rects(self.d, "frame"), [(0, 1426, 1784, 58), (0, 0, 1784, 58), (0, 58, 58, 1368), (1726, 58, 58, 1368)])

    def testTransomBand(self):
        self.assertEqual(rects(self.d, "transom"), [(58, 906.0, 1668, 70)])

    def testSashAndGlass(self):
        self.assertEqual(rects(self.d, "sash"), [(53, 971.0, 1678.0, 460.0)])
        self.assertEqual(rects(self.d, "glass"), [(43, 43, 1698, 878)])
        self.assertEqual(rects(self.d, "sash-glass"), [(89, 1007.0, 1606, 388)])

    def testScreenOutline(self):
        self.assertEqual(rects(self.d, "screen"), [(30.0, 914.0, 1724.0, 540.0)])

    def testDimensionTexts(self):
        self.assertEqual([x["text"] for x in self.d["dims"]],
                         ["opening 1800", "frame 1784", "opening 1500", "frame 1484", "transom centre 941", "awning 450",
                          "fixed 848"])

    def testAwningAndFixedSpansMatchTheJambs(self):
        spans = {x["text"]: x["b"] - x["a"] for x in self.d["dims"]}
        self.assertEqual((spans["awning 450"], spans["fixed 848"]), (450, 848))

    def testGlassLabels(self):
        self.assertEqual([x["text"] for x in self.d["labels"]],
                         ["fixed glass 1698 x 878", "sash 1678 x 460, glass 1606 x 388"])

    def testBoundsHoldEveryDimensionLine(self):
        x0, y0, x1, y1 = self.d["bounds"]
        for dim in self.d["dims"]:
            lo, hi = (y0, y1) if dim["axis"] == "x" else (x0, x1)
            self.assertTrue(lo < dim["at"] < hi, dim["text"])


class BenchFrontTest(unittest.TestCase):
    def testBenchDimensions(self):
        d = drawing.front(lay("bench-600"))
        self.assertEqual([x["text"] for x in d["dims"]],
                         ["opening 600", "frame 584", "opening 600", "frame 584", "transom centre 291", "awning 200",
                          "fixed 198"])
        self.assertEqual(d["labels"][0]["text"], "fixed glass 498 x 228")
        self.assertEqual(d["step"], 35)

    def testNoScreenOutlineWithoutAScreen(self):
        self.assertEqual(rects(drawing.front(lay("bench-600", screen=False)), "screen"), [])


class AssemblyTest(unittest.TestCase):
    def setUp(self):
        self.lay = lay("home-1800x1500")
        self.plist = generate.parts(self.lay)
        self.inst = drawing.assembly(self.lay, self.plist)

    def matrices(self, pid):
        return [x["m"] for x in self.inst if x["id"] == pid]

    def testOneInstancePerPrintedFrameTransomAndSashPart(self):
        qty = {pt["id"]: pt["qty"] for pt in self.plist}
        counts = {}
        for x in self.inst:
            counts[x["id"]] = counts.get(x["id"], 0) + 1
        self.assertEqual(set(counts), {"H", "S", "SW", "JL", "JU", "T", "TE", "SH", "SB", "SBE", "SV",
                                       "CH", "CSL", "CSR", "CS", "JN", "TSL", "TSR"})
        for pid, n in counts.items():
            self.assertEqual(n, qty[pid], pid)

    def testSillRunsAlongXFromTheLeftCorner(self):
        first = self.matrices("SW")[0]
        self.assertEqual(first[0:4], [0.0, 0.0, 1.0, 59.0])
        self.assertEqual(first[8:12], [1.0, 0.0, 0.0, 0.0])

    def testLastSillSegmentEndsAtTheRightCorner(self):
        last = self.matrices("SW")[-1]
        seg = next(m["seg"] for m in self.lay["members"] if m["name"] == "sill")
        self.assertAlmostEqual(last[3] + seg + 1.0, self.lay["w"] - D["FRAME_W"], delta=0.05)

    def testHeadIsFlippedUnderTheTop(self):
        self.assertEqual(self.matrices("H")[0][8:12], [-1.0, 0.0, 0.0, 1484.0])

    def testCornersSitAtTheFrameCorners(self):
        self.assertEqual(self.matrices("CSL"), [[1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0]])
        self.assertEqual(self.matrices("CSR")[0][3], 1784.0)
        self.assertEqual([m[11] for m in self.matrices("CH")], [1484.0, 1484.0])

    def testRightShoeIsTheMirrorOfTheLeft(self):
        left, right = self.matrices("TSL")[0], self.matrices("TSR")[0]
        self.assertEqual(left[3], D["FRAME_BODY"])
        self.assertEqual(right[3], 1784 - D["FRAME_BODY"])
        self.assertEqual((left[11], right[11]), (976.0, 906.0))

    def testScreenOffDropsNothingFromTheAssembly(self):
        off = lay("home-1800x1500", screen=False)
        self.assertEqual(len(drawing.assembly(off, generate.parts(off))), len(self.inst))


class AssemblyPlacementTest(unittest.TestCase):
    def setUp(self):
        self.lay = lay("home-1800x1500")
        cache = {}
        self.boxes = []
        for x in drawing.assembly(self.lay, generate.parts(self.lay)):
            if x["id"] not in cache:
                pts = [v for t in stl.load(ROOT / "cad" / "stl" / "home-1800x1500" / f"{x['id']}.stl") for v in t]
                cache[x["id"]] = [[min(p[a] for p in pts) for a in range(3)], [max(p[a] for p in pts) for a in range(3)]]
            lo, hi = cache[x["id"]]
            m = x["m"]
            corners = [[(hi if i >> a & 1 else lo)[a] for a in range(3)] for i in range(8)]
            world = [[sum(m[r * 4 + k] * c[k] for k in range(3)) + m[r * 4 + 3] for r in range(3)] for c in corners]
            self.boxes.append((x["id"], [round(min(w[a] for w in world), 1) for a in range(3)],
                               [round(max(w[a] for w in world), 1) for a in range(3)]))

    def testEveryInstanceStaysInsideTheFrameOutline(self):
        for pid, lo, hi in self.boxes:
            self.assertGreaterEqual(min(lo), 0.0, pid)
            self.assertLessEqual(hi[0], self.lay["w"], pid)
            self.assertLessEqual(hi[1], D["DEPTH"], pid)
            self.assertLessEqual(hi[2], self.lay["h"], pid)

    def testCornersNodesAndShoesSitWhereAssemblyScadPutsThem(self):
        got = {}
        for pid, lo, hi in self.boxes:
            got.setdefault(pid, []).append((lo, hi))
        self.assertEqual(got["CSR"], [([1726.0, 0.0, 0.0], [1784.0, 63.0, 58.0])])
        self.assertEqual(got["CH"][1], ([1726.0, 0.0, 1426.0], [1784.0, 63.0, 1484.0]))
        self.assertEqual(got["JN"][1], ([1744.0, 0.0, 906.0], [1784.0, 63.0, 976.0]))
        self.assertEqual(got["TSL"], [([34.3, 0.0, 906.0], [58.0, 63.0, 976.0])])
        self.assertEqual(got["TSR"], [([1726.0, 0.0, 906.0], [1749.7, 63.0, 976.0])])
        self.assertEqual(got["CS"][3], ([1680.0, 2.0, 1380.0], [1742.0, 52.0, 1442.0]))



class TwoBayFrontTest(unittest.TestCase):
    def setUp(self):
        self.d = drawing.front(lay("home-1800x1500-2bay"))

    def testMullionsBelowAndAboveTheTransom(self):
        self.assertEqual(rects(self.d, "mullion"), [(857.0, 58.0, 70.0, 848.0), (857.0, 976.0, 70.0, 450.0)])

    def testEveryBayHasItsPanesSashAndScreen(self):
        self.assertEqual(rects(self.d, "glass"), [(43.0, 43.0, 829, 878), (912.0, 43.0, 829, 878)])
        self.assertEqual(rects(self.d, "sash"), [(53.0, 971.0, 809.0, 460.0), (922.0, 971.0, 809.0, 460.0)])
        self.assertEqual(rects(self.d, "sash-glass"), [(89.0, 1007.0, 737, 388), (958.0, 1007.0, 737, 388)])
        self.assertEqual(rects(self.d, "screen"), [(30.0, 914.0, 855.0, 540.0), (899.0, 914.0, 855.0, 540.0)])

    def testBayDimensionAndPaneLabels(self):
        self.assertEqual(self.d["dims"][-1]["text"], "bay 799")
        self.assertEqual([x["text"] for x in self.d["labels"]],
                         ["fixed glass", "829 x 878", "sash glass", "737 x 388"] * 2)

    def testBoundsHoldTheBayDimension(self):
        self.assertLess(self.d["dims"][-1]["at"], self.d["bounds"][3])


class TwoBayAssemblyTest(unittest.TestCase):
    def setUp(self):
        self.lay = lay("home-1800x1500-2bay")
        self.plist = generate.parts(self.lay)
        self.inst = drawing.assembly(self.lay, self.plist)

    def testOneInstancePerPrintedFrameTransomMullionAndSashPart(self):
        qty = {pt["id"]: pt["qty"] for pt in self.plist}
        counts = {}
        for x in self.inst:
            counts[x["id"]] = counts.get(x["id"], 0) + 1
        self.assertEqual(set(counts), {"H", "S", "SW", "JL", "JU", "T", "TE", "SH", "SB", "SBE", "SV", "CH", "CSL", "CSR",
                                       "CS", "JN", "TSL", "TSR", "SN", "HN", "TX", "MSL", "MST", "MSH", "ML", "MU"})
        for pid, n in counts.items():
            self.assertEqual(n, qty[pid], pid)

    def testSecondRunStartsPastTheNode(self):
        sw = [x["m"] for x in self.inst if x["id"] == "SW"]
        self.assertEqual([m[3] for m in sw], [59.0, 657.5, 928.0, 1526.5])


class TwoBayPlacementTest(unittest.TestCase):
    def setUp(self):
        self.lay = lay("home-1800x1500-2bay")
        cache = {}
        self.got = {}
        for x in drawing.assembly(self.lay, generate.parts(self.lay)):
            if x["id"] not in cache:
                pts = [v for t in stl.load(ROOT / "cad" / "stl" / "home-1800x1500-2bay" / f"{x['id']}.stl") for v in t]
                cache[x["id"]] = [[min(p[a] for p in pts) for a in range(3)], [max(p[a] for p in pts) for a in range(3)]]
            lo, hi = cache[x["id"]]
            m = x["m"]
            corners = [[(hi if i >> a & 1 else lo)[a] for a in range(3)] for i in range(8)]
            world = [[sum(m[r * 4 + k] * c[k] for k in range(3)) + m[r * 4 + 3] for r in range(3)] for c in corners]
            self.got.setdefault(x["id"], []).append(([round(min(w[a] for w in world), 1) for a in range(3)],
                                                     [round(max(w[a] for w in world), 1) for a in range(3)]))

    def testEveryInstanceStaysInsideTheFrameOutline(self):
        for pid, boxes in self.got.items():
            for lo, hi in boxes:
                self.assertGreaterEqual(min(lo), 0.0, pid)
                self.assertLessEqual(hi[0], self.lay["w"], pid)
                self.assertLessEqual(hi[1], D["DEPTH"], pid)
                self.assertLessEqual(hi[2], self.lay["h"], pid)

    def testNodesAndShoesSitWhereAssemblyScadPutsThem(self):
        self.assertEqual(self.got["SN"], [([857.0, 0.0, 0.0], [927.0, 63.0, 40.0])])
        self.assertEqual(self.got["HN"], [([857.0, 0.0, 1444.0], [927.0, 63.0, 1484.0])])
        self.assertEqual(self.got["TX"], [([857.0, 0.0, 924.0], [927.0, 63.0, 958.0])])
        self.assertEqual(self.got["MSL"], [([857.0, 0.0, 36.3], [927.0, 63.0, 58.0]), ([857.0, 0.0, 906.0], [927.0, 63.0, 927.7])])
        self.assertEqual(self.got["MST"], [([857.0, 0.0, 954.3], [927.0, 63.0, 976.0])])
        self.assertEqual(self.got["MSH"], [([857.0, 0.0, 1426.0], [927.0, 63.0, 1447.7])])

    def testShoeTonguesReachIntoTheirNodeSlots(self):
        depth = D["MULLION_DOVE_D"] - D["DOVE_CLEAR"]
        self.assertAlmostEqual(self.got["MSL"][0][0][2], D["FRAME_BODY"] - depth, delta=0.05)
        self.assertAlmostEqual(self.got["MSH"][0][1][2], self.lay["h"] - D["FRAME_BODY"] + depth, delta=0.05)


class SandwichLabelTest(unittest.TestCase):
    def label(self, **extra):
        p = {**json.loads((ROOT / "params" / "bench-600.json").read_text()), **extra}
        return drawing.front(window.layout(p))["labels"][0]["text"]

    def testDefaultLabelIsUnchanged(self):
        self.assertEqual(self.label(), "fixed glass 498 x 228")

    def testCustomSandwichIsLabelled(self):
        self.assertEqual(self.label(acrylic_t=3, acrylic_gap=12), "fixed glass 498 x 228, 3 + 12 + 3")


if __name__ == "__main__":
    unittest.main()
