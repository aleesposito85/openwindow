"""Unit tests for tools/stl.py and tools/check_stl.py."""
import csv
import json
import pathlib
import struct
import tempfile
import unittest

import check_stl
import stl

CUBE = [((0, 0, 0), (10, 0, 0), (10, 20, 0)), ((0, 0, 0), (10, 20, 0), (0, 20, 30))]
FACES = [(0, 2, 1), (0, 3, 2), (4, 5, 6), (4, 6, 7), (0, 1, 5), (0, 5, 4),
         (1, 2, 6), (1, 6, 5), (2, 3, 7), (2, 7, 6), (3, 0, 4), (3, 4, 7)]


def box(size, at=(0, 0, 0), inward=False):
    (sx, sy, sz), (ox, oy, oz) = size, at
    v = [(ox + x * sx, oy + y * sy, oz + z * sz)
         for x, y, z in [(0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0), (0, 0, 1), (1, 0, 1), (1, 1, 1), (0, 1, 1)]]
    return [tuple(v[i] for i in (f[::-1] if inward else f)) for f in FACES]


BOX = box((10, 20, 30))


def writeBinary(path, tris):
    with open(path, "wb") as fh:
        fh.write(b"\0" * 80 + struct.pack("<I", len(tris)))
        for tri in tris:
            fh.write(struct.pack("<3f", 0, 0, 0))
            for v in tri:
                fh.write(struct.pack("<3f", *v))
            fh.write(b"\0\0")


def writeAscii(path, tris):
    lines = ["solid t"]
    for tri in tris:
        lines += ["facet normal 0 0 0", "outer loop"] + [f"vertex {x} {y} {z}" for x, y, z in tri]
        lines += ["endloop", "endfacet"]
    pathlib.Path(path).write_text("\n".join(lines + ["endsolid t"]))


def writeRoot(root, rows, name="w", params_name=None):
    gen = root / "cad" / "generated"
    gen.mkdir(parents=True, exist_ok=True)
    with (gen / "parts.csv").open("w", newline="") as fh:
        wr = csv.DictWriter(fh, ["id", "qty", "role", "length", "module", "call"])
        wr.writeheader()
        for r in rows:
            wr.writerow(r)
    if params_name is not None:
        (gen / "params.json").write_text(json.dumps({"name": params_name}))
    stl_dir = root / "cad" / "stl" / name
    stl_dir.mkdir(parents=True, exist_ok=True)
    return stl_dir


class StlTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = pathlib.Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def testBinaryBbox(self):
        writeBinary(self.dir / "b.stl", CUBE)
        self.assertEqual(stl.bbox(stl.load(self.dir / "b.stl")), (10.0, 20.0, 30.0))

    def testAsciiBbox(self):
        writeAscii(self.dir / "a.stl", CUBE)
        self.assertEqual(stl.bbox(stl.load(self.dir / "a.stl")), (10.0, 20.0, 30.0))

    def testEmptyFileRaises(self):
        (self.dir / "e.stl").write_bytes(b"")
        with self.assertRaises(ValueError):
            stl.load(self.dir / "e.stl")

    def testZeroFacetBinaryBboxRaisesEmptyMesh(self):
        writeBinary(self.dir / "z.stl", [])
        with self.assertRaisesRegex(ValueError, "empty mesh"):
            stl.bbox(stl.load(self.dir / "z.stl"))

    def testMalformedAsciiVertexLineRaises(self):
        path = self.dir / "bad.stl"
        path.write_text(
            "solid t\nfacet normal 0 0 0\nouter loop\n"
            "vertex 1 2\nvertex 3 4 5\nvertex 6 7 8\n"
            "endloop\nendfacet\nendsolid t\n"
        )
        with self.assertRaises(ValueError):
            stl.load(path)

    def testUnitCubeVolumeAndArea(self):
        writeBinary(self.dir / "c.stl", box((10, 10, 10)))
        vol, area = stl.volume_area(stl.load(self.dir / "c.stl"))
        self.assertAlmostEqual(vol, 1.0, places=6)
        self.assertAlmostEqual(area, 6.0, places=6)

    def testClosedBoxHasNoOpenEdges(self):
        self.assertEqual(stl.open_edges(BOX), 0)

    def testMissingFaceLeavesOpenEdges(self):
        self.assertEqual(stl.open_edges(BOX[2:]), 4)

    def testEdgeSharedByFourTrianglesIsNotManifold(self):
        self.assertGreater(stl.open_edges(box((10, 10, 10)) + box((10, 10, 10), at=(10, 10, 0))), 0)

    def testClosedBoxIsOneSolidShell(self):
        vols = stl.shell_volumes(BOX)
        self.assertEqual(len(vols), 1)
        self.assertAlmostEqual(vols[0], 6.0, places=6)

    def testTwoSeparateBoxesAreTwoSolidShells(self):
        vols = stl.shell_volumes(box((10, 10, 10)) + box((10, 10, 10), at=(20, 0, 0)))
        self.assertEqual(sorted(round(v, 6) for v in vols), [1.0, 1.0])

    def testInnerVoidIsANegativeShell(self):
        vols = stl.shell_volumes(box((30, 30, 30)) + box((10, 10, 10), at=(10, 10, 10), inward=True))
        self.assertEqual(sorted(round(v, 6) for v in vols), [-1.0, 27.0])


class CheckTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = pathlib.Path(self.tmp.name)
        writeBinary(self.dir / "H.stl", BOX)

    def tearDown(self):
        self.tmp.cleanup()

    def testPassesWhenLengthMatchesAnAxis(self):
        self.assertEqual(check_stl.check({"id": "H", "length": "20.3"}, self.dir), [])

    def testFailsWhenNoAxisMatchesLength(self):
        self.assertIn("length", check_stl.check({"id": "H", "length": "25"}, self.dir)[0])

    def testFailsWhenMissing(self):
        self.assertIn("missing", check_stl.check({"id": "X", "length": ""}, self.dir)[0])

    def testFailsWhenOverBed(self):
        writeBinary(self.dir / "B.stl", [((0, 0, 0), (300, 0, 0), (0, 1, 1))])
        self.assertIn("bed", check_stl.check({"id": "B", "length": ""}, self.dir)[0])

    def testUnreadableStlIsReportedNotRaised(self):
        writeBinary(self.dir / "Z.stl", [])
        self.assertIn("unreadable STL", check_stl.check({"id": "Z", "length": ""}, self.dir)[0])

    def testFailsWhenNotClosed(self):
        writeBinary(self.dir / "O.stl", BOX[2:])
        self.assertTrue(any("not closed" in e for e in check_stl.check({"id": "O", "length": ""}, self.dir)))

    def testFailsWhenTwoSeparateBodies(self):
        writeBinary(self.dir / "T.stl", box((10, 10, 10)) + box((10, 10, 10), at=(20, 0, 0)))
        self.assertTrue(any("2 solid shells" in e for e in check_stl.check({"id": "T", "length": ""}, self.dir)))

    def testInnerVoidPasses(self):
        writeBinary(self.dir / "V.stl", box((30, 30, 30)) + box((10, 10, 10), at=(10, 10, 10), inward=True))
        self.assertEqual(check_stl.check({"id": "V", "length": ""}, self.dir), [])

    def testFailsWhenInsideOut(self):
        writeBinary(self.dir / "I.stl", box((10, 10, 10), inward=True))
        self.assertTrue(any("volume" in e for e in check_stl.check({"id": "I", "length": ""}, self.dir)))


class MainTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def testUnknownIdReturnsTwo(self):
        stl_dir = writeRoot(self.root, [
            {"id": "H", "qty": 1, "role": "exterior", "length": "", "module": "m", "call": "c();"},
        ])
        writeBinary(stl_dir / "H.stl", CUBE)
        self.assertEqual(check_stl.main(["check_stl.py", "w", "ZZ"], root=self.root), 2)

    def testEmptyRowSetReturnsTwo(self):
        writeRoot(self.root, [])
        self.assertEqual(check_stl.main(["check_stl.py", "w"], root=self.root), 2)

    def testNameMismatchWithParamsReturnsTwo(self):
        stl_dir = writeRoot(self.root, [
            {"id": "H", "qty": 1, "role": "exterior", "length": "", "module": "m", "call": "c();"},
        ], params_name="other")
        writeBinary(stl_dir / "H.stl", CUBE)
        self.assertEqual(check_stl.main(["check_stl.py", "w"], root=self.root), 2)

    def testMatchingNamePasses(self):
        stl_dir = writeRoot(self.root, [
            {"id": "H", "qty": 1, "role": "exterior", "length": "", "module": "m", "call": "c();"},
        ], params_name="w")
        writeBinary(stl_dir / "H.stl", BOX)
        self.assertEqual(check_stl.main(["check_stl.py", "w"], root=self.root), 0)


class BedCheckTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = pathlib.Path(self.tmp.name)
        writeBinary(self.dir / "H.stl", BOX)

    def tearDown(self):
        self.tmp.cleanup()

    def testFitsInAnyRotation(self):
        self.assertEqual(check_stl.check({"id": "H", "length": ""}, self.dir, (35, 15, 25)), [])

    def testFailsOnASmallBedAndNamesIt(self):
        errors = check_stl.check({"id": "H", "length": ""}, self.dir, (100, 15, 15))
        self.assertEqual(errors, ["H: (10.0, 20.0, 30.0) does not fit the 100 x 15 x 15 mm bed"])

    def testCubicBedMessageIsUnchanged(self):
        writeBinary(self.dir / "B.stl", [((0, 0, 0), (300, 0, 0), (0, 1, 1))])
        self.assertIn("does not fit the 256 mm bed", check_stl.check({"id": "B", "length": ""}, self.dir)[0])

    def testMainUsesTheGeneratedParamsBed(self):
        root = self.dir / "root"
        stl_dir = writeRoot(root, [
            {"id": "H", "qty": 1, "role": "exterior", "length": "", "module": "m", "call": "c();"},
        ])
        (root / "cad" / "generated" / "params.json").write_text(json.dumps({"name": "w", "bed": [20, 20, 20]}))
        writeBinary(stl_dir / "H.stl", BOX)
        self.assertEqual(check_stl.main(["check_stl.py", "w"], root=root), 1)


if __name__ == "__main__":
    unittest.main()
