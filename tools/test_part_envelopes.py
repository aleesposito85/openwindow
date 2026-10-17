"""Unit tests for tools/part_envelopes.py."""
import contextlib
import io
import json
import pathlib
import tempfile
import unittest
from unittest import mock

import part_envelopes
import window

TWINWALL_BEADS = ["BFH/twinwall", "BFV/twinwall", "BSH/twinwall", "BSV/twinwall"]


class EnvelopeTest(unittest.TestCase):
    def testFixedPartKeepsAllThreeSidesSorted(self):
        self.assertEqual(part_envelopes.envelope((58.0, 63.0, 20.0), None), [20.0, 58.0, 63.0])

    def testSegmentDropsTheLengthAxis(self):
        self.assertEqual(part_envelopes.envelope((63.0, 58.0, 237.14), 237.14), [58.0, 63.0])

    def testSegmentWithoutAMatchingAxisRaises(self):
        with self.assertRaises(ValueError):
            part_envelopes.envelope((58.0, 63.0, 200.0), 237.14)

    def testDumpsWritesOnePartPerLine(self):
        text = part_envelopes.dumps({"A": [1.0, 2.0], "B": [3.0, 4.0, 5.0]})
        self.assertEqual(text, '{\n  "A": [1.0, 2.0],\n  "B": [3.0, 4.0, 5.0]\n}\n')

    def testCommittedTableMatchesTheReferenceRenders(self):
        committed = json.loads(part_envelopes.OUT.read_text())
        measured = part_envelopes.collect(window.ROOT, part_envelopes.REFERENCES)
        self.assertEqual({k: v for k, v in committed.items() if k in measured}, measured)
        self.assertEqual(sorted(set(committed) - set(measured)), TWINWALL_BEADS)


class GlazedEnvelopeTest(unittest.TestCase):
    def setUp(self):
        self.committed = json.loads(part_envelopes.OUT.read_text())

    def testCollectKeysBeadsByGlazingAndTakesSelectedParts(self):
        got = part_envelopes.collect(window.ROOT, ["home-1800x1500"], {"BFH", "H"})
        self.assertEqual(got, {"BFH/igu": [10.0, 19.8], "H": [58.0, 63.0]})

    def testCollectRejectsUnknownPartIds(self):
        with self.assertRaises(ValueError):
            part_envelopes.collect(window.ROOT, ["home-1800x1500"], {"BFH", "bench-600"})

    def testReferencesGiveIguAndAcrylicBeads(self):
        for pid in ("BFH", "BFV", "BSH", "BSV"):
            self.assertEqual(self.committed[f"{pid}/igu"], self.committed[f"{pid}/acrylic"], pid)
            self.assertNotIn(pid, self.committed)

    def testTwinwallBeadsAreTheIguBeadsDeepenedByTheThinnerPane(self):
        deeper = window.D["GLASS_T"] - window.D["TWINWALL_T"]
        for pid in ("BFH", "BFV", "BSH", "BSV"):
            depth, width = self.committed[f"{pid}/igu"]
            self.assertEqual(depth, window.D["BEAD_T"], pid)
            self.assertEqual(self.committed[f"{pid}/twinwall"], [depth + deeper, width], pid)


class MainTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.out = pathlib.Path(self.tmp.name) / "part_envelopes.json"
        self.out.write_text(part_envelopes.dumps({"BFH/twinwall": [18.0, 19.8], "ZZ": [1.0, 2.0]}))

    def tearDown(self):
        self.tmp.cleanup()

    def runMain(self, argv):
        with mock.patch.object(part_envelopes, "OUT", self.out), contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(part_envelopes.main(argv), 0)
        return json.loads(self.out.read_text())

    def testOneWindowsPartsMergeIntoTheTable(self):
        got = self.runMain(["part_envelopes.py", "bench-600", "BFH", "AC"])
        self.assertEqual(got, {"AC": [16.0, 27.0, 27.0], "BFH/acrylic": [10.0, 19.8], "BFH/twinwall": [18.0, 19.8],
                               "ZZ": [1.0, 2.0]})

    def testNoArgumentsRemeasureTheReferencesAndKeepOtherEntries(self):
        got = self.runMain(["part_envelopes.py"])
        want = dict(part_envelopes.collect(window.ROOT, part_envelopes.REFERENCES),
                    **{"BFH/twinwall": [18.0, 19.8], "ZZ": [1.0, 2.0]})
        self.assertEqual(got, dict(sorted(want.items())))
        self.assertEqual(list(got), sorted(got))


class TwoBayEnvelopeTest(unittest.TestCase):
    def testTheTwoBayWindowIsAReference(self):
        self.assertIn("home-1800x1500-2bay", part_envelopes.REFERENCES)

    def testMullionPartsComeFromItsRenders(self):
        got = part_envelopes.collect(window.ROOT, ["home-1800x1500-2bay"], {"SN", "TX", "MSL", "ML"})
        self.assertEqual(got, {"ML": [63.0, 70.0], "MSL": [21.7, 63.0, 70.0], "SN": [40.0, 63.0, 70.0], "TX": [34.0, 63.0, 70.0]})


if __name__ == "__main__":
    unittest.main()
