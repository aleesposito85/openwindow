"""Unit tests for tools/plastic.py and tools/weight.py."""
import json
import pathlib
import unittest

import generate
import plastic
import weight
import window

ROOT = pathlib.Path(__file__).resolve().parent.parent
REFERENCES = ("bench-600", "home-1800x1500", "home-1800x1500-2bay", "my-window")


def load(name):
    params = json.loads((ROOT / "params" / f"{name}.json").read_text())
    return params, window.layout(params), generate.parts(window.layout(params))


def bom_filament_kg(name):
    text = (ROOT / "bom" / f"{name}.md").read_text()
    return sum(float(line.split("|")[3]) for line in text.splitlines() if "| Filament |" in line)


class Rates(unittest.TestCase):
    def testEveryReferencePartHasARate(self):
        r = plastic.rates()
        for name in REFERENCES:
            _, lay, plist = load(name)
            for pt in plist:
                key = f"{pt['id']}/{generate.pane_thickness(lay):g}" if pt["module"] == "bead" else pt["id"]
                self.assertIn(key, r, f"{name}: no rate for {key}")

    def testNoPartFallsBack(self):
        for name in REFERENCES:
            _, lay, plist = load(name)
            self.assertEqual(plastic.estimate(lay, plist)["unknown_ids"], [])


class PlasticMass(unittest.TestCase):
    def testMatchesBomFilamentWithinHalfPercent(self):
        for name in REFERENCES:
            _, lay, plist = load(name)
            est = plastic.estimate(lay, plist)["total_kg"]
            meas = bom_filament_kg(name)
            self.assertLess(abs(est - meas) / meas, 0.005, f"{name}: est {est} vs BOM {meas}")

    def testInteriorExteriorSplitMatchesBom(self):
        for name in REFERENCES:
            _, lay, plist = load(name)
            est = plastic.estimate(lay, plist)
            text = (ROOT / "bom" / f"{name}.md").read_text()
            rows = {("interior" if "(interior" in line else "exterior"): float(line.split("|")[3])
                    for line in text.splitlines() if "| Filament |" in line}
            # rates are averaged across the reference windows, so the split can
            # drift a few tens of grams from the exact per-STL BOM measurement
            self.assertAlmostEqual(est["interior_kg"], rows["interior"], delta=0.05, msg=name)
            self.assertAlmostEqual(est["exterior_kg"], rows["exterior"], delta=0.05, msg=name)

    def testUncalibratedPaneDepthScalesBeads(self):
        base = json.loads((ROOT / "params" / "home-1800x1500.json").read_text())
        base.pop("name", None)
        for extra in ({"glazing": "twinwall"}, {"glazing": "acrylic", "acrylic_t": 2, "acrylic_gap": 8}):
            params = dict(base, **extra)
            lay = window.layout(params)
            est = plastic.estimate(lay, generate.parts(lay))
            self.assertEqual(est["unknown_ids"], [], str(extra))
            self.assertGreater(est["total_kg"], 0)

    def testDeeperBeadsWeighMore(self):
        base = json.loads((ROOT / "params" / "home-1800x1500.json").read_text())
        base.pop("name", None)
        deep = plastic.estimate(window.layout(dict(base, glazing="acrylic", acrylic_t=2, acrylic_gap=8)),
                                generate.parts(window.layout(dict(base, glazing="acrylic", acrylic_t=2, acrylic_gap=8))))
        std = plastic.estimate(window.layout(base), generate.parts(window.layout(base)))
        self.assertGreater(deep["total_kg"], std["total_kg"])


class Weight(unittest.TestCase):
    def testComponentsSumToTotal(self):
        for name in REFERENCES:
            params, lay, plist = load(name)
            w = weight.estimate(params, lay, plist)
            parts = w["glass_kg"] + w["core_kg"] + w["plastic_kg"] + w["hardware_kg"]
            self.assertAlmostEqual(w["total_kg"], parts, delta=0.15, msg=name)

    def testGlassMatchesLayoutArea(self):
        params, lay, _ = load("home-1800x1500-2bay")
        w = weight.estimate(params, lay, [])
        area_m2 = sum(gw * gh for gw, gh in lay["glass"].values()) * lay["bays"] / 1e6
        self.assertAlmostEqual(w["glass_kg"], area_m2 * window.GLAZING_KG_M2["igu"], delta=0.05)

    def testSashWeightPassesStayCheck(self):
        _, lay, plist = load("home-1800x1500-2bay")
        w = weight.estimate(lay["params"], lay, plist)
        self.assertLess(w["sash_kg"], 30)

    def testKgPerSquareMetreIsPlausible(self):
        for name in REFERENCES:
            params, lay, plist = load(name)
            w = weight.estimate(params, lay, plist)
            self.assertGreater(w["kg_per_m2"], 10)
            self.assertLess(w["kg_per_m2"], 60)


if __name__ == "__main__":
    unittest.main()
