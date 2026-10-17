"""Joint bevels never split a part's end face into extra pieces."""
import pathlib
import unittest

import stl

ROOT = pathlib.Path(__file__).resolve().parents[1]
WINDOWS = ["bench-600", "home-1800x1500", "home-1800x1500-2bay", "my-window"]
BEVELLED = {"H", "S", "SW", "JL", "JU", "T", "TE", "ML", "MU", "SH", "SB", "SBE", "SV", "NH", "NV", "TC",
            "JN", "SN", "HN", "TX"}


def pieces(tris, z):
    parent = {}

    def find(k):
        while parent.setdefault(k, k) != k:
            parent[k] = parent[parent[k]]
            k = parent[k]
        return k

    for tri in tris:
        pts = []
        for a, b in ((tri[0], tri[1]), (tri[1], tri[2]), (tri[2], tri[0])):
            a, b = min(a, b), max(a, b)
            if (a[2] - z) * (b[2] - z) < 0:
                t = (z - a[2]) / (b[2] - a[2])
                pts.append((round(a[0] + t * (b[0] - a[0]), 4), round(a[1] + t * (b[1] - a[1]), 4)))
        if len(pts) == 2:
            parent[find(pts[0])] = find(pts[1])
    return len({find(k) for k in list(parent)})


def box(x0, y0, x1, y1, z0, z1):
    v = [(x, y, z) for z in (z0, z1) for y in (y0, y1) for x in (x0, x1)]
    quads = [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)]
    return [tri for a, b, c, d in quads for tri in ((v[a], v[b], v[c]), (v[a], v[c], v[d]))]


class BevelFaceTest(unittest.TestCase):
    def testPiecesCountsEachOutline(self):
        self.assertEqual(pieces(box(0, 0, 10, 10, 0, 5), 2.5), 1)
        self.assertEqual(pieces(box(0, 0, 10, 10, 0, 5) + box(20, 0, 30, 10, 0, 5), 2.5), 2)
        self.assertEqual(pieces(box(0, 0, 10, 10, 0, 5), 7.0), 0)

    def testEndFacesKeepTheirPieces(self):
        checked = 0
        for w in WINDOWS:
            for f in sorted((ROOT / "cad" / "stl" / w).glob("*.stl")):
                if f.stem not in BEVELLED:
                    continue
                tris = stl.load(f)
                zs = [v[2] for t in tris for v in t]
                lo, hi = min(zs), max(zs)
                with self.subTest(window=w, part=f.stem):
                    self.assertEqual(pieces(tris, lo + 0.1), pieces(tris, lo + 1.1))
                    self.assertEqual(pieces(tris, hi - 0.1), pieces(tris, hi - 1.1))
                checked += 1
        self.assertGreater(checked, 40)


if __name__ == "__main__":
    unittest.main()
