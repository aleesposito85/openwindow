# OpenWindow v1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A parametric OpenSCAD + Python generator that turns a measured brick-veneer window opening into a printable STL set, tube cut list, glass order and BOM for the v1 OpenWindow (top awning over a fixed pane), plus the build and install guides and a bench-test protocol.

**Architecture:** `cad/dims.json` holds every shared dimension. `tools/window.py` (pure Python, unit-tested on the Mac) reads it plus a params file and computes the layout: member lengths, segment splits, glass sizes, tube cuts and structural checks. It writes `cad/generated/` (a `dims.scad` mirror, one wrapper `.scad` per printable part, CSVs). `cad/profile.scad` draws every 2D cross-section from those dims, `cad/lib/*.scad` turns profiles into segments and corners, and `cad/box.sh` renders every generated wrapper to STL on the Windows build box and runs the OpenSCAD assert tests there.

**Tech Stack:** OpenSCAD nightly 2026.10.02 (manifold backend) on the Windows box `alees@192.168.68.61`, Python 3 stdlib only (Mac system `python3`, `unittest`), POSIX sh.

**Spec:** `docs/specs/2026-10-07-diy-window-design.md`

---

## Execution status (2026-10-09)

- **All 14 tasks: software steps done.** `~/diy-window/cad/`, `tools/`, `bom/` and `docs/` are authoritative. The code blocks in this plan are the pre-review versions.
  - Python: 126 tests pass.
  - `cad/box.sh test`: 7 OpenSCAD assert files pass.
  - Renders: bench-600 37/37 parts ok (98 prints); home-1800x1500 35/35 ok (160 prints, 16.46 kg exterior + 3.89 kg interior).
  - BOMs: both rebuilt from the STLs, with no parts missing.
- **Left for the builder:** Task 14 steps 3–4, the physical bench tests (print and assemble the bench window, fill in `docs/test-log.md`, and pass rows 1–6 before the home window is printed).
- **Gate before printing the home window:** find a 400 mm friction-stay pair rated for at least the sash weight (15.7 kg) with a stack height of 13 mm or less and a track/arm width of 14 mm or less (`STAY_W`, spec §11). If none exists, the sash cavity (fin, lip, `SASH_GAP`) or the sash tube must change first, and the frame, sash and corner parts must be re-rendered.
- **Review rounds:**
  1. **Code-quality review of Tasks 1–4** (2026-10-08).
     - The stay must fit within the sash height, and a 200 mm stay row was added.
     - `generated/params.json` and the `NAME` line tie generated output to its params, and `check_stl` refuses a mismatch.
     - `write()` only deletes `generated/parts/*.scad`.
     - Unknown IDs and unreadable STLs are reported.
     - Glass sizes are floored.
  2. **Review of Tasks 5–10, 12 and 13** (2026-10-08): `cad/box.sh` hardening (per-run remote folders, a `== DONE` sentinel, a test-count check, a connect timeout, a lock around `generate.py`).
  3. **CAD geometry review** (2026-10-09, spec §12 item 10): keyway backing, fixing and screw columns, per-member socket depths, the shoe end wall, seal continuity at the transom junction, solid end caps.
  4. **Final review** (2026-10-09, spec §12 item 11).
     - 1 mm thermal joint gaps built into the segment lengths, with 4 mm joint cord.
     - Every multi-segment screen rail gets the 10 × 10 core.
     - Fastener lengths checked against the parts, and the hinge bosses moved to `HINGE_BOSS_X` = 21.
     - Sill nose over the corners.
     - Per-window cut list, glass and part list in `bom/`.
     - Guides re-ordered (seals, magnet strip and stay tracks after the transom and fixings).
     - BOM estimates derived from the geometry.
  5. **Final review, round 2** (2026-10-09, spec §12 item 12).
     - Keeper bosses offset to sit over the cams (two pairs per SBE).
     - The whole band outside the cord ring sealed, with a ±50 % sealant.
     - Friction-stay envelope (`STAY_W`) asserted.
     - Transom length set to the installed frame.

## Deviations from the spec (found while planning; spec §12 records them)

| Spec said | Plan does | Why |
|---|---|---|
| Stepped-lap segment joints | Butt joints with a foam-cord groove on both end faces; the tube aligns them | Lets every segment be identical and symmetric (one STL per segment type); the cord ring also seals the tube cavity |
| Beads screwed into inserts | Beads snap into an undercut keyway | Bead pieces and segments split at different points, so inserts would never line up; snap beads need no hardware |
| Inner sash gasket on the sash lip | Inner gasket in a kerf on the frame's inner stop | Keeps the lip 6 mm and the stay cavity 18 mm deep |
| Sash gap not specified | Uniform 13 mm `SASH_GAP` on all four sides | Friction stays need the cavity, and one sash profile (flange + lip) must work on every side |
| Transom joined to jambs (unspecified) | Dovetail shoe slides in from the room side into a jamb node, plus two lock screws | Transom fits after the frame is fixed; load goes node → jamb tube |
| Screen magnet line on the frame around the opening | On the transom it runs along the lower half of the inside face | Keeps the cam locks inside the closed screen |
| ~60 parts, 4–5 kg, 50–70 print hours (1.8 × 1.5 m) | Measured after slimming: 160 prints in 35 types, ≈ 16.46 kg exterior + 3.89 kg interior filament (≈ 21.9 kg before slimming), roughly 550+ print hours (2026-10-09) | The spec figure was an under-estimate; even hollow 2.5 mm-walled profiles of this depth weigh about as much per metre as uPVC |
| 40% infill | 15% infill; frame and sash bodies are hollow multi-chamber profiles | The tube carries the load; chambers cut weight and add insulation |

## Ground rules for whoever executes this

- **No git.** The user's rule is no git under `~` except one work repo. Every "commit" checkpoint in this plan is replaced by a **Checkpoint** step: run the listed checks and stop for review if anything fails.
- **No installs on the Mac.** OpenSCAD runs only on the Windows box. Python is stdlib only.
- **Network:** every SSH/SCP to the Windows box must bind en0 (`ssh -B en0`, `scp -o BindInterface=en0`), because the work VPN hijacks home-LAN routes.
- **No explanatory comments in code** beyond a one-line module docstring/header. Rationale lives in this plan and the spec.
- **Test method names** are camelCase `testXxx`, no underscores.
- **Units:** millimetres, kilograms, N/mm². Coordinates in profiles: `x` = across the visible face (0 = wall side of the member, increasing toward the opening), `y` = through the wall depth (0 = outside face, `DEPTH` = inside face).

## File structure

```
~/diy-window/
  README.md                         project overview, quick start
  params/
    bench-600.json                  600 x 600 bench prototype (acrylic)
    home-1800x1500.json             first full-size target
  cad/
    dims.json                       SINGLE SOURCE for shared dimensions
    profile.scad                    2D cross-sections, one module per profile name
    lib/
      segment.scad                  profile -> straight segment (tube pocket, lap ends, bosses, ID)
      corner.scad                   two profiles -> mitred-node corner block with tube sockets
      emboss.scad                   embossed part ID text
    parts/
      frame_segment.scad            head/sill/jamb/transom/sash/screen segments (wraps lib/segment)
      corner_block.scad             frame, sash and screen corners (wraps lib/corner)
      jamb_node.scad                jamb piece where the transom meets the jamb, with transom shoe socket
      transom_shoe.scad             printed shoe on each steel transom end
      bead.scad                     glazing bead, variants igu/acrylic/twinwall
      setting_block.scad            glass setting block
      weep_cap.scad                 flap weep cap
      sill_nose.scad                clip-on sill nose with drip groove
      acrylic_spacer.scad           16 mm spacer bar + corner for the acrylic sandwich
      cam_lock.scad                 cam handle + sash keeper
      screen_hinge.scad             printed pin hinge for the screen
      test_coupon.scad              heat/creep test coupon
    box.sh                          Windows-box runner: render parts, run cad/tests, export PNGs
    tests/*_test.scad               OpenSCAD assert tests, evaluated by box.sh test
    assembly.scad                   full window assembly for previews and fit checks
    generated/                      written by tools/window.py, never hand-edited
      dims.scad
      layout.scad
      parts/<ID>.scad
    stl/<params-name>/              rendered STLs
  tools/
    window.py                       layout calculator + generator CLI
    test_window.py                  unit tests for window.py
    stl.py                          STL reader + bounding box
    test_stl.py                     unit tests for stl.py
    check_stl.py                    verifies rendered STLs against parts.csv bounding boxes
  bom/
    build_bom.py                    BOM CSV + markdown from generated/parts.csv and cutlist
  docs/
    specs/2026-10-07-diy-window-design.md
    plans/2026-10-08-diy-window-v1.md
    printing.md                     materials tiers, print settings
    build-guide.md                  assembly steps
    install-guide.md                brick-veneer installation
    test-log.md                     bench test protocol + results table
```

Each `parts/*.scad` file only *defines* modules. `window.py` writes thin wrappers into `generated/parts/` that call them with concrete arguments, so no string `-D` quoting has to cross SSH into Windows `cmd`.

---

### Task 1: Project scaffold and parameter files

**Files:**
- Create: `~/diy-window/README.md`
- Create: `~/diy-window/params/bench-600.json`
- Create: `~/diy-window/params/home-1800x1500.json`
- Create: `~/diy-window/cad/dims.json`

- [ ] **Step 1: Create the folders**

```bash
mkdir -p ~/diy-window/{params,cad/lib,cad/parts,cad/generated/parts,cad/stl,tools,bom,docs/specs,docs/plans}
```

- [ ] **Step 2: Write `params/home-1800x1500.json`**

```json
{
  "name": "home-1800x1500",
  "opening_w": 1800,
  "opening_h": 1500,
  "fix_gap": 8,
  "awning_h": 450,
  "glazing": "igu",
  "tier": 3
}
```

- [ ] **Step 3: Write `params/bench-600.json`**

```json
{
  "name": "bench-600",
  "opening_w": 600,
  "opening_h": 600,
  "fix_gap": 8,
  "awning_h": 200,
  "glazing": "acrylic",
  "tier": 1
}
```

- [ ] **Step 4: Write `cad/dims.json`**

These values are the v1 profile geometry. Every other file reads them; never copy a number out of here.

```json
{
  "MAX_SEG": 240.0,
  "DEPTH": 63.0,
  "FRAME_W": 58.0,
  "FRAME_BODY": 40.0,
  "TRANSOM_W": 70.0,
  "TRANSOM_HALF_BODY": 17.0,
  "SASH_W": 51.0,
  "SASH_BODY": 33.0,
  "SASH_Y0": 2.0,
  "SASH_GAP": 13.0,
  "SCREEN_W": 30.0,
  "SCREEN_DEPTH": 20.0,
  "SCREEN_OVERLAP": 10.0,
  "SCREEN_SHELL": 4.0,
  "GLASS_T": 24.0,
  "TWINWALL_T": 16.0,
  "GLASS_CLEAR": 3.0,
  "GASKET_T": 3.0,
  "GASKET_IN": 4.0,
  "GLASS_EDGE": 43.0,
  "TRANSOM_GLASS": 20.0,
  "SASH_GLASS": 36.0,
  "STOP_T": 8.0,
  "GLASS_Y0": 11.0,
  "BEAD_W": 16.0,
  "BEAD_T": 10.0,
  "KEY_Y": 43.0,
  "KEY_D": 4.0,
  "KEY_H": 4.0,
  "KEY_LIP": 0.8,
  "KEY_THROAT": 1.2,
  "FIN_Y0": 20.0,
  "FIN_Y1": 28.0,
  "FIN_L": 8.0,
  "ISTOP_Y0": 54.0,
  "FLANGE_Y1": 17.0,
  "FLANGE_L": 11.0,
  "LIP_Y0": 46.0,
  "LIP_Y1": 52.0,
  "LIP_L": 8.0,
  "KERF_W": 3.0,
  "KERF_D": 5.0,
  "MAG_W": 13.0,
  "MAG_D": 2.0,
  "SPLINE_W": 4.0,
  "SPLINE_D": 5.0,
  "SPACER_W": 12.0,
  "ACRYLIC_T": 4.0,
  "SETTING_L": 100.0,
  "WEEP_CAP_H": 12.0,
  "WEEP_CAP_T": 1.5,
  "TUBE_FRAME": [20.0, 20.0],
  "TUBE_TRANSOM": [20.0, 40.0],
  "TUBE_SASH": [20.0, 20.0],
  "TUBE_SCREEN": [10.0, 10.0],
  "SOCKET": 30.0,
  "TUBE_CLEAR": 0.3,
  "MIN_SHELL": 6.0,
  "CHAMBER_WALL": 2.5,
  "CORD_D": 3.0,
  "FIX_Y": 16.0,
  "FIX_D": 5.0,
  "FIX_CB_D": 10.0,
  "FIX_CB_L": 6.0,
  "TUBE_SCREW_D": 4.2,
  "INSERT_M4_D": 5.6,
  "INSERT_M4_L": 8.0,
  "BOSS_PITCH": 24.0,
  "DOVE_W": 16.0,
  "DOVE_FLARE": 3.0,
  "DOVE_D": 6.0,
  "LOCK_OFFSET": 15.0,
  "LOCK_D": 3.3,
  "LOCK_L": 30.0,
  "NODE_FIX_OFFSET": 25.0,
  "SHOE_WALL": 3.0,
  "HINGE_BOSS_X": 25.0,
  "CAM_BOSS_X": 47.0,
  "TRANSOM_MAG_X": 19.0,
  "LABEL_DEPTH": 0.6,
  "LABEL_SIZE": 5.0,
  "WEEP_W": 20.0,
  "WEEP_H": 5.0,
  "SILL_SLOPE_DEG": 8.0,
  "NOSE_KEY_X": 10.0,
  "NOSE_KEY_W": 6.0,
  "NOSE_KEY_D": 4.0,
  "NOSE_PROJECTION": 15.0
}
```

- [ ] **Step 5: Write `README.md`**

```markdown
# OpenWindow

A mostly 3D-printable replacement window for basic single-glazed aluminium sliders.
v1: top awning over a fixed double-glazed pane, brick-veneer walls, Bambu P1S-sized parts.

Design: docs/specs/2026-10-07-diy-window-design.md

## Quick start

    python3 tools/window.py params/bench-600.json     # writes cad/generated/ and bom/
    cad/box.sh render bench-600                       # renders + checks STLs on the Windows box
    
Measure the opening (brick reveal to brick reveal, and head to brick sill) at three
points each way and use the smallest values.
```

- [ ] **Step 6: Checkpoint**

Run: `python3 -c "import json;[json.load(open(f)) for f in ['$HOME/diy-window/cad/dims.json','$HOME/diy-window/params/bench-600.json','$HOME/diy-window/params/home-1800x1500.json']];print('ok')"`
Expected: `ok`

---

### Task 2: Layout calculator (`tools/window.py`, pure math)

The numbers in the tests below are worked by hand from `dims.json` and `home-1800x1500.json`:
`w = 1800 − 2·8 = 1784`, `h = 1484`, horizontal members `1784 − 2·58 = 1668`, transom centreline
`1484 − 58 − 450 − 35 = 941`, lower jamb `941 − 35 − 58 = 848`.
The sash clears the frame by `SASH_GAP` = 13 mm on all four sides. That cavity is where the friction stays live, and keeping it uniform lets one sash profile (with its outer weather flange and inner seal lip) work on every side: `sash_w = 1784 − 2·40 − 2·13 = 1678`, `sash_h = (1484 − 40) − (941 + 17) − 2·13 = 460`.
The transom check uses the 40 × 20 steel tube (`I ≈ 36 896 mm⁴`): about 6.2 mm under 0.7 kPa, against a span/175 limit of 9.5 mm.

**Files:**
- Create: `~/diy-window/tools/window.py`
- Test: `~/diy-window/tools/test_window.py`

- [ ] **Step 1: Write the failing tests**

```python
"""Unit tests for tools/window.py."""
import json
import pathlib
import unittest

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
        self.assertEqual((head["length"], head["n"], head["seg"]), (1668, 7, 238.29))
        self.assertEqual(head["profile"], "sash_rebate")

    def testLowerJambUsesGlazingProfile(self):
        jamb = self.member("jamb_lower")
        self.assertEqual((jamb["length"], jamb["n"], jamb["seg"], jamb["qty"]), (848, 4, 212.0, 2))
        self.assertEqual(jamb["profile"], "glazing")

    def testUpperJambMatchesAwningHeight(self):
        jamb = self.member("jamb_upper")
        self.assertEqual((jamb["length"], jamb["n"], jamb["seg"]), (450, 2, 225.0))

    def testTransomIsSteel(self):
        self.assertEqual(self.member("transom")["core"], "steel40x20")

    def testFixedGlassSize(self):
        self.assertEqual(self.lay["glass"]["fixed"], (1698, 878))

    def testSashOuterAndGlassSize(self):
        self.assertEqual(self.lay["sash"], (1678, 460))
        self.assertEqual(self.lay["glass"]["sash"], (1606, 388))

    def testSashMembers(self):
        self.assertEqual(self.member("sash_horizontal")["n"], 7)
        self.assertEqual(self.member("sash_vertical")["seg"], 179.0)

    def testScreenSpansFromHeadToTransomMagnetStrip(self):
        self.assertEqual(self.lay["screen"], (1724, 541))

    def testScreenHorizontalsGetACore(self):
        self.assertEqual(self.member("screen_horizontal")["core"], "alu10")
        self.assertIsNone(self.member("screen_vertical")["core"])

    def testEverySegmentFitsTheBed(self):
        for m in self.lay["members"]:
            self.assertLessEqual(m["seg"], 240.0, m["name"])

    def testTubeCutsIncludeSockets(self):
        tubes = {t["member"]: t for t in self.lay["tubes"]}
        self.assertEqual(tubes["head"]["length"], 1668 + 2 * 30)
        self.assertEqual(tubes["jamb"]["length"], 1484 - 2 * 58 + 2 * 30)
        self.assertEqual(tubes["transom"]["length"], 1668 + 2 * 18 - 2 * 4)

    def testAllChecksPassForHome(self):
        failed = [c for c in self.lay["checks"] if not c["ok"]]
        self.assertEqual(failed, [])

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


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `cd ~/diy-window/tools && python3 -m unittest test_window -v`
Expected: `ModuleNotFoundError: No module named 'window'`

- [ ] **Step 3: Write `tools/window.py` (calculation part)**

The friction-stay table is the generic stainless-stay rating band. Spec §11 says to confirm it against the stay actually bought; when a product is chosen, replace the table with its datasheet values.

```python
#!/usr/bin/env python3
"""OpenWindow layout: member lengths, segment splits, glass sizes, tube cuts, structural checks."""
import json
import math
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
D = json.loads((ROOT / "cad" / "dims.json").read_text())

WIND_KPA = 0.7
GLAZING_KG_M2 = {"igu": 20.0, "acrylic": 9.5, "twinwall": 2.7}
CORES = {
    "alu10": (69000, 10, 10, 1.0, 0.10),
    "alu20": (69000, 20, 20, 1.6, 0.32),
    "alu25": (69000, 25, 25, 1.6, 0.41),
    "steel40x20": (200000, 20, 40, 1.6, 1.43),
    "alu50x25": (69000, 25, 50, 1.6, 0.62),
    "steel50x25": (200000, 25, 50, 1.6, 1.80),
}
FRAME_CORE = "alu20"
TRANSOM_CORE = "steel40x20"
STAYS = [(250, 17.0), (300, 20.0), (400, 30.0), (500, 35.0)]
STAY_RATIO = 0.75
SASH_FRAME_KG_M = 0.75
SCREEN_CORE_OVER = 1200.0
MIN_AWNING = 150.0
MIN_FIXED = 150.0


def split(length):
    if length <= 0:
        raise ValueError(f"member length must be positive, got {length}")
    n = math.ceil(length / D["MAX_SEG"] - 1e-9)
    return n, round(length / n, 2)


def inertia(core):
    _, b, d, t, _ = CORES[core]
    return (b * d ** 3 - (b - 2 * t) * (d - 2 * t) ** 3) / 12.0


def deflection(core, span, trib_h):
    w = WIND_KPA / 1000.0 * trib_h
    return 5 * w * span ** 4 / (384 * CORES[core][0] * inertia(core))


def member(name, length, profile, core, qty):
    n, seg = split(length)
    return {"name": name, "length": round(length, 2), "profile": profile, "core": core,
            "qty": qty, "n": n, "seg": seg}


def layout(p):
    if p["glazing"] not in GLAZING_KG_M2:
        raise ValueError(f"glazing must be one of {sorted(GLAZING_KG_M2)}, got {p['glazing']}")
    F, T, S, N = D["FRAME_W"], D["TRANSOM_W"], D["SASH_W"], D["SCREEN_W"]
    w = p["opening_w"] - 2 * p["fix_gap"]
    h = p["opening_h"] - 2 * p["fix_gap"]
    a = p["awning_h"]
    if a < MIN_AWNING:
        raise ValueError(f"awning_h must be at least {MIN_AWNING}, got {a}")
    horiz = w - 2 * F
    transom_c = h - F - a - T / 2
    lower = transom_c - T / 2 - F
    if lower < MIN_FIXED:
        raise ValueError(f"fixed pane height {lower} is below {MIN_FIXED}; reduce awning_h")

    sash_w = w - 2 * D["FRAME_BODY"] - 2 * D["SASH_GAP"]
    sash_h = (h - D["FRAME_BODY"]) - (transom_c + D["TRANSOM_HALF_BODY"]) - 2 * D["SASH_GAP"]
    screen_w = w - 2 * D["FRAME_BODY"] + 2 * D["SCREEN_OVERLAP"]
    screen_h = (h - D["FRAME_BODY"] + D["SCREEN_OVERLAP"]) - (transom_c - T / 2 + D["TRANSOM_MAG_X"] - D["SCREEN_OVERLAP"] - 2)
    screen_core = lambda length: "alu10" if length > SCREEN_CORE_OVER else None

    members = [
        member("head", horiz, "sash_rebate", FRAME_CORE, 1),
        member("sill", horiz, "sill", FRAME_CORE, 1),
        member("jamb_lower", lower, "glazing", FRAME_CORE, 2),
        member("jamb_upper", a, "sash_rebate", FRAME_CORE, 2),
        member("transom", horiz, "transom", TRANSOM_CORE, 1),
        member("sash_horizontal", sash_w - 2 * S, "sash", "alu20", 2),
        member("sash_vertical", sash_h - 2 * S, "sash", "alu20", 2),
        member("screen_horizontal", screen_w - 2 * N, "screen", screen_core(screen_w - 2 * N), 2),
        member("screen_vertical", screen_h - 2 * N, "screen", screen_core(screen_h - 2 * N), 2),
    ]

    sock = D["SOCKET"]
    tubes = [
        {"member": "head", "core": FRAME_CORE, "length": horiz + 2 * sock, "qty": 1},
        {"member": "sill", "core": FRAME_CORE, "length": horiz + 2 * sock, "qty": 1},
        {"member": "jamb", "core": FRAME_CORE, "length": h - 2 * F + 2 * sock, "qty": 2},
        {"member": "transom", "core": TRANSOM_CORE,
         "length": horiz + 2 * (F - D["FRAME_BODY"]) - 2 * (D["SHOE_WALL"] + 1), "qty": 1},
        {"member": "sash_horizontal", "core": "alu20", "length": sash_w - 2 * S + 2 * sock, "qty": 2},
        {"member": "sash_vertical", "core": "alu20", "length": sash_h - 2 * S + 2 * sock, "qty": 2},
    ]
    for m in members:
        if m["name"].startswith("screen") and m["core"]:
            tubes.append({"member": m["name"], "core": m["core"], "length": m["length"] + 2 * sock, "qty": m["qty"]})
    for t in tubes:
        t["length"] = round(t["length"], 1)

    glass = {
        "fixed": (round(w - 2 * D["GLASS_EDGE"]), round(transom_c - D["TRANSOM_GLASS"] - D["GLASS_EDGE"])),
        "sash": (round(sash_w - 2 * D["SASH_GLASS"]), round(sash_h - 2 * D["SASH_GLASS"])),
    }

    checks = []
    trib = (lower + a) / 2
    delta = deflection(TRANSOM_CORE, horiz, trib)
    limit = horiz / 175
    checks.append({"name": "transom_deflection", "ok": delta <= limit,
                   "msg": f"transom deflects {delta:.1f} mm at {WIND_KPA} kPa, limit span/175 = {limit:.1f} mm"})

    gw, gh = glass["sash"]
    sash_kg = gw * gh / 1e6 * GLAZING_KG_M2[p["glazing"]] + 2 * (sash_w + sash_h) / 1000 * SASH_FRAME_KG_M
    stay = next((s for s in STAYS if s[0] >= STAY_RATIO * sash_h), None)
    stay_ok = stay is not None and stay[1] >= sash_kg
    checks.append({"name": "sash_weight", "ok": stay_ok,
                   "msg": f"sash {sash_kg:.1f} kg, stay pair {stay[0] if stay else '-'} mm rated "
                          f"{stay[1] if stay else '-'} kg"})

    too_long = [m["name"] for m in members if m["seg"] > D["MAX_SEG"]]
    checks.append({"name": "segment_length", "ok": not too_long, "msg": f"segments over bed: {too_long}"})

    return {"params": p, "w": w, "h": h, "transom_c": transom_c, "members": members,
            "tubes": tubes, "glass": glass, "sash": (sash_w, sash_h), "screen": (screen_w, screen_h),
            "sash_kg": round(sash_kg, 1), "stay": stay[0] if stay else None, "checks": checks}
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `cd ~/diy-window/tools && python3 -m unittest test_window -v`
Expected: all tests `ok`. With 3200 mm the transom check fails: span 3058, trib 644, about 34.6 mm deflection against a 17.5 mm limit.

- [ ] **Step 5: Checkpoint**

Run: `cd ~/diy-window/tools && python3 -c "import window,json;l=window.layout(json.load(open('../params/home-1800x1500.json')));[print(c['msg']) for c in l['checks']]"`
Expected: transom ≈ 6.2 mm (limit 9.5), sash ≈ 15.7 kg on a 400 mm stay pair rated 30 kg, no segments over the bed.

---

### Task 3: Generator (`tools/generate.py`): part list, wrappers and CSVs

`window.py` only calculates. `generate.py` decides which printable parts exist and how many, then writes `cad/generated/`.

Decisions this task locks in:
- **Segments are interchangeable.** Every segment has identical, symmetric ends, so the left and right jambs (and the head and sill) are the same part rotated about the depth axis. That gives one STL per segment type, printed `qty` times.
- **End segments carry the special features.** The two end segments of the sill get weep slots. The two end segments of the transom and of the sash bottom rail get both weep slots and insert bosses. That puts the weeps and cam locks near each end, as the spec requires.
- **Some parts come as left/right mirror pairs.** The sill/jamb corners (`CSL`/`CSR`) are mirrored because their two legs have different profiles. The transom shoes (`TSL`/`TSR`) are mirrored because the dovetail tongue is on one end only. Every other corner type has identical legs and is a single part, and the jamb node is symmetric, so it is one part.
- **Beads run between the frame bodies**, not between corner blocks. Horizontal beads run the full daylight width, and vertical beads fit between them. Bead runs are split again to fit the bed.
- **`length` in `parts.csv`** is the longest dimension a part must have. `check_stl.py` (Task 9) checks every STL against it.

Worked numbers for the home window: fixed horizontal bead run `1784 − 2·40 = 1704`, split 8 × 213; fixed vertical `941 − 17 − 40 − 2·16 = 852`, split 4 × 213; sash horizontal `1678 − 2·33 = 1612`, split 7 × 230.29; sash vertical `460 − 66 − 32 = 362`, split 2 × 181.

**Files:**
- Create: `~/diy-window/tools/generate.py`
- Test: `~/diy-window/tools/test_generate.py`
- Modify: `~/diy-window/README.md` (quick start command)

- [ ] **Step 1: Write the failing tests**

```python
"""Unit tests for tools/generate.py."""
import csv
import json
import pathlib
import tempfile
import unittest

import generate
import window

ROOT = pathlib.Path(__file__).resolve().parent.parent


def lay(name):
    return window.layout(json.loads((ROOT / "params" / name).read_text()))


def byId(parts):
    return {p["id"]: p for p in parts}


class HomePartsTest(unittest.TestCase):
    def setUp(self):
        self.parts = byId(generate.parts(lay("home-1800x1500.json")))

    def testHeadSegmentCall(self):
        h = self.parts["H"]
        self.assertEqual(h["call"], 'frame_segment("sash_rebate", 238.29, "H", bosses=true);')
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

    def testAcrylicSpacers(self):
        self.assertEqual((self.parts["AFH"]["length"], self.parts["AFH"]["qty"]), (237.0, 4))
        self.assertEqual((self.parts["AFV"]["length"], self.parts["AFV"]["qty"]), (204.0, 2))
        self.assertEqual(self.parts["AC"]["qty"], 8)


class AllPartsTest(unittest.TestCase):
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
        self.out = pathlib.Path(self.tmp.name)
        self.lay = lay("home-1800x1500.json")
        generate.write(self.lay, self.out)

    def tearDown(self):
        self.tmp.cleanup()

    def testWrapperUsesThePartFileAndCallsTheModule(self):
        text = (self.out / "parts" / "H.scad").read_text()
        self.assertEqual(text, 'use <../../parts/frame_segment.scad>\nframe_segment("sash_rebate", 238.29, "H", bosses=true);\n')

    def testCamPartsShareOneFile(self):
        self.assertIn("use <../../parts/cam_lock.scad>", (self.out / "parts" / "KP.scad").read_text())

    def testDimsMirror(self):
        self.assertIn("FRAME_W = 58.0;\n", (self.out / "dims.scad").read_text())

    def testLayoutScad(self):
        text = (self.out / "layout.scad").read_text()
        self.assertIn("TRANSOM_C = 941.0;\n", text)
        self.assertIn('GLAZING = "igu";\n', text)
        self.assertIn("FIXED_GLASS = [1698, 878];\n", text)

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

    def testStaleWrappersAreRemoved(self):
        (self.out / "parts" / "OLD.scad").write_text("x")
        generate.write(self.lay, self.out)
        self.assertFalse((self.out / "parts" / "OLD.scad").exists())


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `cd ~/diy-window/tools && python3 -m unittest test_generate -v`
Expected: `ModuleNotFoundError: No module named 'generate'`

- [ ] **Step 3: Write `tools/generate.py`**

```python
#!/usr/bin/env python3
"""Turn a window layout into part wrappers plus parts/cutlist/glass CSVs under cad/generated/."""
import csv
import json
import pathlib
import shutil
import sys

import window
from window import D, split

GENERATED = window.ROOT / "cad" / "generated"
MODULE_FILE = {"cam_base": "cam_lock", "cam_handle": "cam_lock", "cam_keeper": "cam_lock",
               "acrylic_spacer_corner": "acrylic_spacer", "screen_leaf": "screen_hinge"}
GLASS_SPEC = {
    "igu": "IGU 4/16/4 = 24 mm, toughened if required by AS 1288, low-E/argon optional",
    "acrylic": "2 x 4 mm clear acrylic, cut to size, protective film on until assembly",
    "twinwall": "16 mm twin-wall polycarbonate, UV face out, flutes vertical",
}
WIDE_SCREEN = 1000.0


def part(pid, module, args, qty, role="exterior", length=None):
    return {"id": pid, "module": module, "call": f"{module}({args});", "qty": qty, "role": role, "length": length}


def parts(lay):
    m = {x["name"]: x for x in lay["members"]}
    ends = lambda name: min(2, m[name]["n"])
    out = []

    def seg(pid, name, profile, qty, role="exterior", **flags):
        if qty <= 0:
            return
        f = "".join(f", {k}={str(v).lower()}" for k, v in flags.items())
        s = m[name]["seg"]
        out.append(part(pid, "frame_segment", f'"{profile}", {s}, "{pid}"{f}', qty, role, s))

    seg("H", "head", "sash_rebate", m["head"]["n"], bosses=True)
    seg("S", "sill", "sill", m["sill"]["n"] - ends("sill"))
    seg("SW", "sill", "sill", ends("sill"), weep=True)
    seg("JL", "jamb_lower", "glazing", 2 * m["jamb_lower"]["n"])
    seg("JU", "jamb_upper", "sash_rebate", 2 * m["jamb_upper"]["n"])
    seg("T", "transom", "transom", m["transom"]["n"] - ends("transom"))
    seg("TE", "transom", "transom", ends("transom"), weep=True, bosses=True)
    seg("SH", "sash_horizontal", "sash", m["sash_horizontal"]["n"])
    seg("SB", "sash_horizontal", "sash", m["sash_horizontal"]["n"] - ends("sash_horizontal"))
    seg("SBE", "sash_horizontal", "sash", ends("sash_horizontal"), weep=True, bosses=True)
    seg("SV", "sash_vertical", "sash", 2 * m["sash_vertical"]["n"])
    seg("NH", "screen_horizontal", "screen", 2 * m["screen_horizontal"]["n"], "interior")
    seg("NV", "screen_vertical", "screen", 2 * m["screen_vertical"]["n"], "interior")

    hinges = 3 if lay["screen"][0] > WIDE_SCREEN else 2
    out += [
        part("CH", "corner_block", '"sash_rebate", "sash_rebate", "CH"', 2),
        part("CSL", "corner_block", '"sill", "glazing", "CSL"', 1),
        part("CSR", "corner_block", '"sill", "glazing", "CSR", mirrored=true', 1),
        part("CS", "corner_block", '"sash", "sash", "CS"', 4),
        part("CN", "corner_block", '"screen", "screen", "CN"', 4, "interior"),
        part("JN", "jamb_node", '"JN"', 2),
        part("TSL", "transom_shoe", '"TSL", mirrored=true', 1),
        part("TSR", "transom_shoe", '"TSR"', 1),
        part("GW", "setting_block", '"GW", wedge=true', 2),
        part("GF", "setting_block", '"GF"', 6),
        part("WC", "weep_cap", '"WC"', ends("sill") + ends("sash_horizontal")),
        part("NS", "sill_nose", f'{m["sill"]["seg"]}, "NS"', m["sill"]["n"], "exterior", m["sill"]["seg"]),
        part("CMB", "cam_base", '"CMB"', 2, "interior"),
        part("CMH", "cam_handle", '"CMH"', 2, "interior"),
        part("KP", "cam_keeper", '"KP"', 2, "interior"),
        part("HG", "screen_hinge", '"HG"', hinges, "interior"),
        part("HS", "screen_leaf", '"HS"', hinges, "interior"),
        part("TC", "test_coupon", '"TC"', 1),
    ]

    g = lay["params"]["glazing"]
    bw = D["BEAD_W"]
    sash_w, sash_h = lay["sash"]
    runs = [
        ("BFH", lay["w"] - 2 * D["FRAME_BODY"]),
        ("BFV", lay["transom_c"] - D["TRANSOM_HALF_BODY"] - D["FRAME_BODY"] - 2 * bw),
        ("BSH", sash_w - 2 * D["SASH_BODY"]),
        ("BSV", sash_h - 2 * D["SASH_BODY"] - 2 * bw),
    ]
    for pid, run in runs:
        n, s = split(run)
        out.append(part(pid, "bead", f'"{g}", {s}, "{pid}"', 2 * n, "interior", s))

    if g == "acrylic":
        sw = D["SPACER_W"]
        for pane, key in (("F", "fixed"), ("S", "sash")):
            gw, gh = lay["glass"][key]
            for axis, run in (("H", gw - 2 * sw), ("V", gh - 2 * sw)):
                n, s = split(run)
                pid = f"A{pane}{axis}"
                out.append(part(pid, "acrylic_spacer", f'{s}, "{pid}"', 2 * n, "exterior", s))
        out.append(part("AC", "acrylic_spacer_corner", '"AC"', 8))
    return out


def write(lay, out=GENERATED):
    out = pathlib.Path(out)
    shutil.rmtree(out / "parts", ignore_errors=True)
    (out / "parts").mkdir(parents=True)

    (out / "dims.scad").write_text("".join(f"{k} = {v};\n" for k, v in D.items()))

    p = lay["params"]
    lines = {
        "W": float(lay["w"]), "H": float(lay["h"]), "TRANSOM_C": float(lay["transom_c"]),
        "AWNING_H": float(p["awning_h"]), "SASH": list(lay["sash"]), "SCREEN": list(lay["screen"]),
        "FIXED_GLASS": list(lay["glass"]["fixed"]), "SASH_GLASS_DIMS": list(lay["glass"]["sash"]),
    }
    text = "".join(f"{k} = {json.dumps(v)};\n" for k, v in lines.items())
    text += f'GLAZING = "{p["glazing"]}";\n'
    for mem in lay["members"]:
        key = mem["name"].upper()
        text += f"SEG_{key} = {mem['seg']};\nN_{key} = {mem['n']};\n"
    (out / "layout.scad").write_text(text)

    plist = parts(lay)
    for pt in plist:
        f = MODULE_FILE.get(pt["module"], pt["module"])
        (out / "parts" / f"{pt['id']}.scad").write_text(f"use <../../parts/{f}.scad>\n{pt['call']}\n")

    with (out / "parts.csv").open("w", newline="") as fh:
        wr = csv.DictWriter(fh, ["id", "qty", "role", "length", "module", "call"])
        wr.writeheader()
        for pt in plist:
            wr.writerow({**pt, "length": "" if pt["length"] is None else pt["length"]})

    with (out / "cutlist.csv").open("w", newline="") as fh:
        wr = csv.writer(fh)
        wr.writerow(["member", "core", "length_mm", "qty"])
        for t in lay["tubes"]:
            wr.writerow([t["member"], t["core"], t["length"], t["qty"]])

    with (out / "glass.csv").open("w", newline="") as fh:
        wr = csv.writer(fh)
        wr.writerow(["pane", "glazing", "width_mm", "height_mm", "qty", "spec"])
        for pane, (gw, gh) in lay["glass"].items():
            wr.writerow([pane, p["glazing"], gw, gh, 1, GLASS_SPEC[p["glazing"]]])
    return plist


def main(argv):
    if len(argv) != 2:
        print("usage: generate.py params/<name>.json", file=sys.stderr)
        return 2
    params = json.loads(pathlib.Path(argv[1]).read_text())
    lay = window.layout(params)
    plist = write(lay)
    print(f"{params['name']}: {len(plist)} part types, {sum(x['qty'] for x in plist)} prints -> {GENERATED}")
    for c in lay["checks"]:
        print(("ok       " if c["ok"] else "WARNING  ") + c["msg"])
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `cd ~/diy-window/tools && python3 -m unittest test_window test_generate -v`
Expected: all tests `ok`.

- [ ] **Step 5: Update the README quick start**

In `README.md`, replace the line `python3 tools/window.py params/bench-600.json     # writes cad/generated/ and bom/` with:

```
    python3 tools/generate.py params/bench-600.json   # writes cad/generated/
```

- [ ] **Step 6: Checkpoint**

Run: `cd ~/diy-window && python3 tools/generate.py params/home-1800x1500.json && ls cad/generated/parts | wc -l`
Expected: the summary line, three `ok` lines, and a wrapper count equal to the number of part types.

---

### Task 4: STL reader and STL checker (`tools/stl.py`, `tools/check_stl.py`)

This gives every later CAD task an automatic pass/fail. After rendering, each STL must exist, fit the P1S bed (≤ 256 mm on every axis), and have one bounding-box dimension within 0.6 mm of the `length` the generator expects.

**Files:**
- Create: `~/diy-window/tools/stl.py`
- Create: `~/diy-window/tools/check_stl.py`
- Test: `~/diy-window/tools/test_stl.py`

- [ ] **Step 1: Write the failing tests**

```python
# tools/test_stl.py
"""Unit tests for tools/stl.py and tools/check_stl.py."""
import pathlib
import struct
import tempfile
import unittest

import check_stl
import stl

CUBE = [((0, 0, 0), (10, 0, 0), (10, 20, 0)), ((0, 0, 0), (10, 20, 0), (0, 20, 30))]


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


class CheckTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = pathlib.Path(self.tmp.name)
        writeBinary(self.dir / "H.stl", CUBE)

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


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `cd ~/diy-window/tools && python3 -m unittest test_stl -v`
Expected: `ModuleNotFoundError: No module named 'check_stl'`

- [ ] **Step 3: Write `tools/stl.py`**

```python
# tools/stl.py
"""Minimal STL reader (binary and ASCII), bounding box, volume and area."""
import pathlib
import struct


def load(path):
    data = pathlib.Path(path).read_bytes()
    if len(data) < 84:
        if data.lstrip().startswith(b"solid") and b"vertex" in data:
            return _ascii(data)
        raise ValueError(f"{path}: not an STL")
    n = struct.unpack_from("<I", data, 80)[0]
    if 84 + 50 * n == len(data):
        return [tuple(struct.unpack_from("<3f", data, 84 + 50 * i + 12 + 12 * k) for k in range(3))
                for i in range(n)]
    return _ascii(data)


def _ascii(data):
    vs = [tuple(float(x) for x in line.split()[1:4])
          for line in data.decode("ascii", "replace").splitlines() if line.strip().startswith("vertex")]
    if not vs or len(vs) % 3:
        raise ValueError("no facets")
    return [tuple(vs[i:i + 3]) for i in range(0, len(vs), 3)]


def bbox(tris):
    pts = [v for t in tris for v in t]
    return tuple(round(max(p[a] for p in pts) - min(p[a] for p in pts), 3) for a in range(3))
```

- [ ] **Step 4: Write `tools/check_stl.py`**

```python
# tools/check_stl.py
"""Check rendered STLs in cad/stl/<name>/ against cad/generated/parts.csv."""
import csv
import pathlib
import sys

import stl

ROOT = pathlib.Path(__file__).resolve().parent.parent
BED = 256.0
TOL = 0.6


def check(row, stl_dir):
    path = pathlib.Path(stl_dir) / f"{row['id']}.stl"
    if not path.exists():
        return [f"{row['id']}: missing {path.name}"]
    box = stl.bbox(stl.load(path))
    errors = []
    if max(box) > BED:
        errors.append(f"{row['id']}: {box} does not fit the {BED:.0f} mm bed")
    if row["length"] and not any(abs(d - float(row["length"])) <= TOL for d in box):
        errors.append(f"{row['id']}: no axis of {box} matches length {row['length']}")
    return errors


def main(argv):
    if len(argv) < 2:
        print("usage: check_stl.py <params-name> [ID ...]", file=sys.stderr)
        return 2
    rows = list(csv.DictReader((ROOT / "cad" / "generated" / "parts.csv").read_text().splitlines()))
    if argv[2:]:
        rows = [r for r in rows if r["id"] in argv[2:]]
    errors = [e for r in rows for e in check(r, ROOT / "cad" / "stl" / argv[1])]
    for e in errors:
        print("FAIL", e)
    print(f"{len(rows) - len({e.split(':')[0] for e in errors})}/{len(rows)} parts ok")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
```

- [ ] **Step 5: Run the tests to verify they pass**

Run: `cd ~/diy-window/tools && python3 -m unittest test_stl -v`
Expected: 7 tests `ok`.

- [ ] **Step 6: Checkpoint**

Run: `cd ~/diy-window/tools && python3 -m unittest discover -p 'test_*.py'`
Expected: `OK`, 54 tests.

---

### Task 5: Windows-box runner (`cad/box.sh`) and the OpenSCAD test harness

One script owns everything that touches the Windows box:
- **Upload:** packs `cad/` (without `stl/`) as a tar, replaces `C:\Users\alees\diywindow` on the box, and unpacks it there.
- **Batch:** writes one `.cmd` batch file and runs it over a single SSH session, instead of one SSH call per part.
- **Strict logs:** any `ERROR`, `WARNING`, failed `assert` or `FAILED` line in the OpenSCAD output fails the run.

Its three modes:
- `render <params> [ID…]` regenerates the parts first, then renders the STLs and runs `check_stl.py`.
- `test [params]` evaluates every `cad/tests/*_test.scad` to an `.echo` file, so the `assert()` calls run without producing geometry. OpenSCAD writes assertion errors into the `.echo` file, not to the console, and still exits 0, so the batch `type`s each `.echo` file back into the log.
- `png <file.scad> <out.png> [openscad args]` regenerates for `$PARAMS` (default `bench-600`), then exports a preview image.

**Files:**
- Create: `~/diy-window/cad/box.sh`
- Create: `~/diy-window/cad/tests/smoke_test.scad`

- [ ] **Step 1: Write the smoke test**

```openscad
// cad/tests/smoke_test.scad
include <../generated/dims.scad>
assert(MAX_SEG == 240, "dims.scad not generated from cad/dims.json");
echo("smoke ok");
```

- [ ] **Step 2: Write `cad/box.sh`**

```sh
#!/bin/sh
# cad/box.sh: run OpenSCAD on the Windows build box (render | test | png)
set -e
HOST=alees@192.168.68.61
REMOTE=C:/Users/alees/diywindow
WREMOTE='C:\Users\alees\diywindow'
SCAD=C:/Users/alees/tools/OpenSCAD-2026.10.02-x86-64/openscad.com
CAD=$(cd "$(dirname "$0")" && pwd)
ROOT=$(dirname "$CAD")
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT

remote() { ssh -B en0 -o BatchMode=yes "$HOST" "$@"; }
put() { scp -q -o BindInterface=en0 -o BatchMode=yes "$1" "$HOST:$2"; }
get() { scp -q -o BindInterface=en0 -o BatchMode=yes "$HOST:$1" "$2"; }

upload() {
  COPYFILE_DISABLE=1 tar -cf "$TMP/cad.tar" -C "$ROOT" --exclude 'cad/stl' cad
  remote "if exist $WREMOTE rmdir /s /q $WREMOTE" >/dev/null
  remote "mkdir $WREMOTE\\out"
  put "$TMP/cad.tar" "$REMOTE/cad.tar"
  remote "tar -xf $REMOTE/cad.tar -C $REMOTE"
}

run_batch() {
  put "$TMP/run.cmd" "$REMOTE/run.cmd"
  remote "$WREMOTE\\run.cmd" > "$TMP/log.txt" 2>&1 || true
  if grep -qE "ERROR|WARNING|[Aa]ssert|FAILED" "$TMP/log.txt"; then
    grep -E "^== |ERROR|WARNING|[Aa]ssert|FAILED" "$TMP/log.txt"
    return 1
  fi
}

render() {
  name=${1:?usage: box.sh render <params-name> [ID ...]}
  shift
  python3 "$ROOT/tools/generate.py" "$ROOT/params/$name.json"
  ids=${*:-$(cd "$CAD/generated/parts" && ls *.scad | sed 's/\.scad$//')}
  upload
  printf '@echo off\r\n' > "$TMP/run.cmd"
  for id in $ids; do
    printf 'echo == %s\r\n"%s" --backend=manifold -o %s/out/%s.stl %s/cad/generated/parts/%s.scad 2>&1 || echo FAILED %s\r\n' \
      "$id" "$SCAD" "$REMOTE" "$id" "$REMOTE" "$id" "$id" >> "$TMP/run.cmd"
  done
  status=0
  run_batch || status=1
  remote "tar -cf $REMOTE/stl.tar -C $REMOTE/out ."
  get "$REMOTE/stl.tar" "$TMP/stl.tar"
  mkdir -p "$CAD/stl/$name"
  tar -xf "$TMP/stl.tar" -C "$CAD/stl/$name"
  python3 "$ROOT/tools/check_stl.py" "$name" $* || status=1
  return $status
}

tests() {
  python3 "$ROOT/tools/generate.py" "$ROOT/params/${1:-bench-600}.json" >/dev/null
  upload
  printf '@echo off\r\n' > "$TMP/run.cmd"
  for f in $(cd "$CAD/tests" && ls *_test.scad); do
    printf 'echo == %s\r\n"%s" -o %s/out/%s.echo %s/cad/tests/%s 2>&1 || echo FAILED %s\r\ntype %s\\out\\%s.echo\r\n' \
      "$f" "$SCAD" "$REMOTE" "$f" "$REMOTE" "$f" "$f" "$WREMOTE" "$f" >> "$TMP/run.cmd"
  done
  if run_batch; then
    grep -c "^== " "$TMP/log.txt" | sed 's/$/ test files passed/'
  else
    return 1
  fi
}

png() {
  src=${1:?usage: box.sh png <file.scad relative to cad/> <out.png> [openscad args]}
  out=${2:?missing out.png}
  shift 2
  python3 "$ROOT/tools/generate.py" "$ROOT/params/${PARAMS:-bench-600}.json" >/dev/null
  upload
  printf '@echo off\r\n"%s" --backend=manifold --render --imgsize=1600,1000 --colorscheme=Tomorrow %s -o %s/out/preview.png %s/cad/%s 2>&1 || echo FAILED png\r\n' \
    "$SCAD" "$*" "$REMOTE" "$REMOTE" "$src" > "$TMP/run.cmd"
  run_batch
  get "$REMOTE/out/preview.png" "$out"
}

cmd=${1:?usage: box.sh render|test|png ...}
shift
case $cmd in
  render) render "$@" ;;
  test) tests "$@" ;;
  png) png "$@" ;;
  *) echo "unknown command $cmd" >&2; exit 2 ;;
esac
```

- [ ] **Step 3: Make it executable and run the smoke test**

Run: `chmod +x ~/diy-window/cad/box.sh && ~/diy-window/cad/box.sh test`
Expected: `1 test files passed`

- [ ] **Step 4: Prove a failing assert fails the run**

Run: `printf 'assert(false, "deliberate");\n' > ~/diy-window/cad/tests/fail_test.scad && ~/diy-window/cad/box.sh test; echo "exit $?"; rm ~/diy-window/cad/tests/fail_test.scad`
Expected: a line containing `Assertion` and `deliberate`, then `exit 1`.

- [ ] **Step 5: Checkpoint**

Run: `~/diy-window/cad/box.sh test`
Expected: `1 test files passed`

---

### Task 6: Cross-section profiles (`cad/profile.scad`)

Every member's 2D cross-section lives here, built only from `dims.scad`. Coordinates follow the convention in the ground rules: `x` runs across the visible face and `y` runs through the wall from the outside face. The profiles are:
- `glazing` (lower jambs)
- `sash_rebate` (head, upper jambs)
- `sill`
- `transom` (glazing rebate underneath, sash rebate on top)
- `sash` (with its outer weather flange and inner seal lip reaching back toward the frame, so `x < 0`)
- `screen`
- the bead profile for each glazing type

Seal and drainage features (spec §4):
- **Outer weather seal:** a kerf in the frame fin's outward face holds the EPDM bulb, and the sash flange presses on it.
- **Inner air seal:** a kerf in the frame inner stop's outward face holds the second gasket, and the sash inner lip presses on it. The spec put this gasket on the sash lip. Moving it to the frame stop keeps the 6 mm lip solid and the stay cavity at 18 mm.
- **Glazing gaskets:** kerfs 4 mm in from the glass edge, on the outer stop and on the bead.
- **Beads** snap into an undercut keyway in the host body face. This replaces the spec's screwed beads: no inserts, and a bead pries out with a putty knife.
- **Sill:** the pocket floor slopes 8° outward, and a keyway on the outside face takes the clip-on nose.

**Air chambers.** The frame and sash bodies are hollow, with `CHAMBER_WALL` (2.5 mm) walls, like a uPVC multi-chamber profile. The tube carries the load, so solid plastic only adds weight and print time, and the air layers insulate.
- The tube sits in a 2.5 mm-walled pocket, with chambers between it and both faces. The thermal-break distance (`MIN_SHELL`, tube to face) is unchanged; most of it is now air.
- The fixing screw crosses the outside chamber. Its head bears on the remaining wall behind the counterbore.
- The bead keyway keeps a 6 mm wall, and the sill keeps solid material above its nose keyway.
- The insert bosses and tube screws get local solid columns, added per segment in Task 7, not solid bands along the whole profile.
- The beads and the screen rails are hollow too.
- The transom has no chambers, because its steel tube already fills the body.

The outcome is recorded in Task 12: the filament total dropped from about 23 kg to the figure printed by the BOM.

**Files:**
- Create: `~/diy-window/cad/profile.scad`
- Test: `~/diy-window/cad/tests/profile_test.scad`
- Create: `~/diy-window/cad/tests/profiles_sheet.scad` (visual check, not a test)

- [ ] **Step 1: Write the failing test**

These asserts are the design rules from the spec, written as numbers: shell thickness around every tube, glass bite and clearance, seal overlaps and compression gaps, stay cavity size, and screen/frame magnet alignment. A dims change that breaks one fails here first.

```openscad
// cad/tests/profile_test.scad
use <../profile.scad>
include <../generated/dims.scad>

module shell_ok(name, x0, x1, y0, y1) {
    o = pocket_origin(name);
    p = pocket(name);
    assert(o[0] - x0 >= MIN_SHELL, str(name, ": shell on low x ", o[0] - x0));
    assert(x1 - (o[0] + p[0]) >= MIN_SHELL, str(name, ": shell on high x ", x1 - (o[0] + p[0])));
    assert(o[1] - y0 >= MIN_SHELL, str(name, ": shell outside ", o[1] - y0));
    assert(y1 - (o[1] + p[1]) >= MIN_SHELL, str(name, ": shell inside ", y1 - (o[1] + p[1])));
}

shell_ok("glazing", 0, FRAME_BODY, 0, DEPTH);
shell_ok("sash_rebate", 0, FRAME_BODY, 0, DEPTH);
shell_ok("sill", 0, FRAME_BODY - (bead_seat_y() - STOP_T) * tan(SILL_SLOPE_DEG), 0, DEPTH);
shell_ok("transom", TRANSOM_W / 2 - TRANSOM_HALF_BODY, TRANSOM_W / 2 + TRANSOM_HALF_BODY, 0, DEPTH);
shell_ok("sash", 0, SASH_BODY, SASH_Y0, LIP_Y1);

assert(FRAME_W - GLASS_EDGE >= 12, "frame glass bite");
assert(TRANSOM_W / 2 - TRANSOM_GLASS >= 12, "transom glass bite");
assert(SASH_W - SASH_GLASS >= 12, "sash glass bite");
assert(GLASS_EDGE - FRAME_BODY == GLASS_CLEAR, "frame glass clearance");
assert(TRANSOM_GLASS - TRANSOM_HALF_BODY == GLASS_CLEAR, "transom glass clearance");
assert(SASH_GLASS - SASH_BODY == GLASS_CLEAR, "sash glass clearance");
assert(GLASS_Y0 - STOP_T == GASKET_T, "outer glazing gasket gap");
assert(KEY_Y >= bead_seat_y() + 2, "bead keyway clears the bead seat");
assert(bead_seat_y() + BEAD_T <= DEPTH, "bead inside the frame depth");
assert(BEAD_W <= TRANSOM_W / 2 - TRANSOM_HALF_BODY, "bead fits the transom rebate");

sash_edge = FRAME_BODY + SASH_GAP;
assert(sash_edge - FLANGE_L <= FRAME_BODY + FIN_L / 2 - KERF_W / 2, "sash flange covers the fin seal");
assert(FIN_Y0 - FLANGE_Y1 >= 2 && FIN_Y0 - FLANGE_Y1 <= 4, "outer seal compression gap 2-4 mm");
assert(ISTOP_Y0 - LIP_Y1 >= 2 && ISTOP_Y0 - LIP_Y1 <= 4, "inner seal compression gap 2-4 mm");
assert(sash_edge - LIP_L >= FRAME_BODY, "sash lip stays over the inner stop");
assert(TRANSOM_W - (TRANSOM_W / 2 + TRANSOM_HALF_BODY) >= SASH_GAP, "transom stop reaches under the sash lip");
assert(SASH_GAP >= 13, "friction stay cavity width");
assert(LIP_Y0 - FIN_Y1 >= 16, "friction stay cavity depth");
assert(FIX_Y + FIX_D / 2 <= pocket_origin("glazing")[1] - 2, "fixing screw clears the tube");
assert(SCREEN_OVERLAP + 2 + MAG_W <= SCREEN_W, "screen magnet channel inside the screen face");
assert(SCREEN_DEPTH - SPLINE_D - MAG_D >= 4, "screen wall between magnet channel and spline groove");
assert(TRANSOM_MAG_X >= TRANSOM_W / 2 - TRANSOM_HALF_BODY && TRANSOM_MAG_X + MAG_W <= TRANSOM_W / 2 + TRANSOM_HALF_BODY,
       "transom magnet channel on the transom body face");
assert(DEPTH - INSERT_M4_L >= pocket_origin("transom")[1] + pocket("transom")[1] + 1.5, "cam inserts clear the steel tube");
echo("profile rules ok");
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `~/diy-window/cad/box.sh test`
Expected: FAIL, with `ERROR`/`WARNING` lines saying `profile.scad` can't be found or `pocket_origin` is unknown. (`use <>` imports only modules and functions, never variables, which is why the test calls `bead_seat_y()` and not a constant.)

- [ ] **Step 3: Write `cad/profile.scad`**

```openscad
// cad/profile.scad
include <generated/dims.scad>

EPS = 0.01;
function bead_seat_y() = GLASS_Y0 + GLASS_T + GASKET_T;
BEAD_SEAT_Y = bead_seat_y();

function tube(name) =
    name == "transom" ? TUBE_TRANSOM : name == "sash" ? TUBE_SASH : name == "screen" ? TUBE_SCREEN : TUBE_FRAME;

function pocket(name) = tube(name) + [2, 2] * TUBE_CLEAR;

function pocket_origin(name) =
    name == "transom" ? [TRANSOM_W / 2, DEPTH / 2] - pocket(name) / 2
  : name == "sash" ? [SASH_BODY / 2, (SASH_Y0 + LIP_Y1) / 2] - pocket(name) / 2
  : name == "screen" ? [SCREEN_SHELL, (SCREEN_DEPTH - pocket(name)[1]) / 2]
  : [MIN_SHELL, (DEPTH - pocket(name)[1]) / 2];

function profile_min(name) = name == "sash" ? -FLANGE_L : 0;

function profile_width(name) =
    name == "transom" ? TRANSOM_W : name == "sash" ? SASH_W : name == "screen" ? SCREEN_W : FRAME_W;

module rect(x0, y0, x1, y1) { translate([x0, y0]) square([x1 - x0, y1 - y0]); }

module key_slot(d, h) {
    rect(0, KEY_THROAT, h, d);
    rect(0, -EPS, h - KEY_LIP, KEY_THROAT + EPS);
}

module key_tongue(d, h) {
    rect(0.2, KEY_THROAT + 0.2, h - 0.2, d - 0.2);
    rect(0.2, -2, h - KEY_LIP - 0.2, KEY_THROAT + 0.4);
}

module kerf(cx, y, dir = 1) {
    if (dir > 0) rect(cx - KERF_W / 2, y - EPS, cx + KERF_W / 2, y + KERF_D);
    else rect(cx - KERF_W / 2, y - KERF_D, cx + KERF_W / 2, y + EPS);
}

module pocket_cut(name) { translate(pocket_origin(name)) square(pocket(name)); }

module bead_key(e) { translate([e, KEY_Y]) rotate(90) key_slot(KEY_D, KEY_H); }

module bead_key_rev(e) { translate([e, KEY_Y]) mirror([1, 0]) rotate(90) key_slot(KEY_D, KEY_H); }

module sash_side_add(e, w) {
    rect(e, FIN_Y0, e + FIN_L, FIN_Y1);
    rect(e, ISTOP_Y0, e + w, DEPTH);
}

module sash_side_cut(e, mag = true) {
    kerf(e + FIN_L / 2, FIN_Y0);
    kerf(e + SASH_GAP - LIP_L / 2, ISTOP_Y0);
    if (mag) rect(e + 2, DEPTH - MAG_D, e + 2 + MAG_W, DEPTH + EPS);
}

module sill_body() {
    s = tan(SILL_SLOPE_DEG);
    polygon([[0, 0], [FRAME_W, 0], [FRAME_W - STOP_T * s, STOP_T],
             [FRAME_BODY - (BEAD_SEAT_Y - STOP_T) * s, STOP_T], [FRAME_BODY, BEAD_SEAT_Y],
             [FRAME_BODY, DEPTH], [0, DEPTH]]);
}

function is_frame_body(name) = name == "glazing" || name == "sash_rebate" || name == "sill";

module chambers(name) {
    w = CHAMBER_WALL;
    o = pocket_origin(name);
    p = pocket(name);
    if (is_frame_body(name)) {
        y0 = name == "sill" ? NOSE_KEY_D + w : w;
        rect(w, y0, FRAME_BODY - FIX_CB_L - w, o[1] - w);
        rect(o[0] + p[0] + w, o[1], FRAME_BODY - 2 * w, KEY_Y - w);
        rect(w, o[1] + p[1] + w, FRAME_BODY - w, DEPTH - w);
    }
    else if (name == "sash") {
        rect(w, SASH_Y0 + w, SASH_BODY - w, o[1] - w);
        rect(w, o[1] + p[1] + w, SASH_BODY - 2 * w, LIP_Y1 - w);
    }
    else if (name == "screen") rect(o[0] + p[0] + w, MAG_D + w, SCREEN_W - w, SCREEN_DEPTH - SPLINE_D - w);
}

module profile_solid(name) {
    fb = FRAME_BODY;
    tl = TRANSOM_W / 2 - TRANSOM_HALF_BODY;
    th = TRANSOM_W / 2 + TRANSOM_HALF_BODY;
    if (name == "glazing") difference() {
        union() { rect(0, 0, fb, DEPTH); rect(fb, 0, FRAME_W, STOP_T); }
        pocket_cut(name);
        bead_key(fb);
        kerf(GLASS_EDGE + GASKET_IN, STOP_T, -1);
    }
    else if (name == "sash_rebate") difference() {
        union() { rect(0, 0, fb, DEPTH); sash_side_add(fb, FRAME_W - fb); }
        pocket_cut(name);
        sash_side_cut(fb);
    }
    else if (name == "sill") difference() {
        sill_body();
        pocket_cut(name);
        bead_key(fb);
        kerf(GLASS_EDGE + GASKET_IN, STOP_T, -1);
        translate([NOSE_KEY_X, 0]) key_slot(NOSE_KEY_D, NOSE_KEY_W);
    }
    else if (name == "transom") difference() {
        union() { rect(tl, 0, th, DEPTH); rect(0, 0, tl, STOP_T); sash_side_add(th, TRANSOM_W - th); }
        pocket_cut(name);
        bead_key_rev(tl);
        kerf(TRANSOM_W / 2 - TRANSOM_GLASS - GASKET_IN, STOP_T, -1);
        sash_side_cut(th, false);
        rect(TRANSOM_MAG_X, DEPTH - MAG_D, TRANSOM_MAG_X + MAG_W, DEPTH + EPS);
    }
    else if (name == "sash") difference() {
        union() {
            rect(0, SASH_Y0, SASH_BODY, LIP_Y1);
            rect(-FLANGE_L, SASH_Y0, 0, FLANGE_Y1);
            rect(-LIP_L, LIP_Y0, 0, LIP_Y1);
            rect(SASH_BODY, SASH_Y0, SASH_W, STOP_T);
        }
        pocket_cut(name);
        bead_key(SASH_BODY);
        kerf(SASH_GLASS + GASKET_IN, STOP_T, -1);
    }
    else if (name == "screen") difference() {
        rect(0, 0, SCREEN_W, SCREEN_DEPTH);
        pocket_cut(name);
        rect(SCREEN_OVERLAP + 2, -EPS, SCREEN_OVERLAP + 2 + MAG_W, MAG_D);
        rect(SCREEN_W - 8, SCREEN_DEPTH - SPLINE_D, SCREEN_W - 8 + SPLINE_W, SCREEN_DEPTH + EPS);
    }
    else assert(false, str("unknown profile ", name));
}

module profile(name) {
    difference() {
        profile_solid(name);
        chambers(name);
    }
}

module bead_profile(glazing) {
    assert(glazing == "igu" || glazing == "acrylic" || glazing == "twinwall", str("unknown glazing ", glazing));
    y0 = BEAD_SEAT_Y - (glazing == "twinwall" ? GLASS_T - TWINWALL_T : 0);
    top = BEAD_SEAT_Y + BEAD_T;
    difference() {
        union() {
            rect(0, y0, BEAD_W, top);
            translate([0, KEY_Y]) rotate(90) key_tongue(KEY_D, KEY_H);
        }
        kerf(GLASS_CLEAR + GASKET_IN, y0, 1);
        rect(KEY_D, y0 + KERF_D + 2, BEAD_W - 2.5, top - 2.5);
    }
}
```

- [ ] **Step 4: Write the visual sheet**

```openscad
// cad/tests/profiles_sheet.scad
use <../profile.scad>
include <../generated/dims.scad>

names = ["glazing", "sash_rebate", "sill", "transom", "sash", "screen"];
for (i = [0 : len(names) - 1]) translate([i * 100 + 20, 0]) {
    color("SteelBlue") profile(names[i]);
    color("Black") translate([0, -12]) text(names[i], size = 5);
}
for (g = [["igu", 0], ["twinwall", 1]]) translate([620 + g[1] * 40, 0]) {
    color("Peru") bead_profile(g[0]);
    color("Black") translate([0, -12]) text(g[0], size = 5);
}
```

- [ ] **Step 5: Run the test to verify it passes**

Run: `~/diy-window/cad/box.sh test`
Expected: `2 test files passed`

- [ ] **Step 6: Render the sheet and look at it**

Run: `~/diy-window/cad/box.sh png tests/profiles_sheet.scad ~/diy-window/docs/img/profiles.png --camera=0,0,0,0,0,0,500 --viewall --autocenter --projection=ortho`
Expected: a PNG with six profiles and two beads. Check by eye:
- every tube pocket is fully enclosed;
- the sill floor slopes down toward `y = 0`;
- the sash flange and lip reach left past `x = 0`;
- the transom shows a stop leg on its low side and fin + stop on its high side.

- [ ] **Step 7: Checkpoint**

Run: `~/diy-window/cad/box.sh test`
Expected: `2 test files passed`

---

### Task 7: Straight segments (`cad/lib/segment.scad`, `cad/parts/frame_segment.scad`)

A segment is its profile extruded to the segment length. It prints standing up, so the extrusion axis is `z` and the profile lies flat on the bed. Every segment gets:
- **End-face cord grooves:** a 1.5 mm deep ring, `CORD_D` wide, inset 2 mm from the outline, on both ends. It also rings the tube pocket, so the joint seals the tube cavity (spec §2.2).
- **Tube screw:** one countersunk clearance hole from the inside face down into the tube, at mid-length. It goes in from the room side only, so it can't bridge the thermal break (spec §2.3).
- **Fixing hole (perimeter profiles only):** a hole through the body along `x` at `y = FIX_Y`, counterbored from the rebate face so the screw head sits below it. The screw is driven before glazing and before the sash is hung, then hidden behind the glass edge or the sash flange.
- **Engraved ID** on a hidden face (wall side, sash edge, or inside the transom glazing pocket).

Optional features, set by the generator:
- `weep = true` (sill, transom and sash only) cuts a `WEEP_W` × `WEEP_H` drainage slot at mid-length.
- `bosses = true` (sash_rebate, transom and sash only) adds two M4 heat-set insert holes in the inside face, `BOSS_PITCH` apart. They take the screen hinges on the head, the cam handles on the transom, and the keepers on the sash bottom rail.

**Files:**
- Create: `~/diy-window/cad/lib/emboss.scad`
- Create: `~/diy-window/cad/lib/segment.scad`
- Create: `~/diy-window/cad/parts/frame_segment.scad`
- Test: `~/diy-window/cad/tests/segment_test.scad`; rendered STLs checked by `check_stl.py`

- [ ] **Step 1: Write the failing assert test**

```openscad
// cad/tests/segment_test.scad
use <../lib/segment.scad>
include <../generated/dims.scad>

assert(boss_x("sash_rebate") == HINGE_BOSS_X);
assert(boss_x("glazing") == undef, "glazing segments take no bosses");
assert(rebate_face("sill") < FRAME_BODY, "sill rebate face follows the sloped floor");
assert(top_face("sash") == LIP_Y1);
assert(len([for (n = ["glazing", "sash_rebate", "sill"]) if (is_perimeter(n)) n]) == 3);
assert(!is_perimeter("transom"));
echo("segment rules ok");
```

- [ ] **Step 2: Run it to verify it fails**

Run: `~/diy-window/cad/box.sh test`
Expected: FAIL. `segment_test.scad` reports `WARNING: Can't open library '../lib/segment.scad'` or unknown function `boss_x`.

- [ ] **Step 3: Write `cad/lib/emboss.scad`**

```openscad
// cad/lib/emboss.scad
include <../generated/dims.scad>

module engrave(code, at, z, size = LABEL_SIZE) {
    translate([at[0] - 0.01, at[1], z]) rotate([90, 0, 90])
        linear_extrude(LABEL_DEPTH + 0.01) text(code, size = size, halign = "center", valign = "center");
}
```

- [ ] **Step 4: Write `cad/lib/segment.scad`**

```openscad
// cad/lib/segment.scad
include <../generated/dims.scad>
use <../profile.scad>
use <emboss.scad>

EPS = 0.01;

function is_perimeter(name) = name == "glazing" || name == "sash_rebate" || name == "sill";

function top_face(name) = name == "sash" ? LIP_Y1 : name == "screen" ? SCREEN_DEPTH : DEPTH;

function rebate_face(name) =
    name == "sill" ? FRAME_BODY - (bead_seat_y() - FIX_Y) * tan(SILL_SLOPE_DEG) : FRAME_BODY;

function boss_x(name) =
    name == "sash_rebate" ? HINGE_BOSS_X : name == "transom" ? CAM_BOSS_X : name == "sash" ? SASH_BODY / 2 : undef;

function label_at(name) =
    name == "transom" ? [TRANSOM_W / 2 - TRANSOM_HALF_BODY, GLASS_Y0 + 11]
  : name == "sash" ? [0, (FLANGE_Y1 + LIP_Y0) / 2]
  : name == "screen" ? [0, SCREEN_DEPTH / 2]
  : [0, DEPTH / 2];

module end_groove(name) {
    difference() {
        offset(delta = -2) profile(name);
        offset(delta = -2 - CORD_D) profile(name);
    }
}

module weep_cut(name) {
    if (name == "sill") {
        f = FRAME_BODY - (bead_seat_y() - STOP_T) * tan(SILL_SLOPE_DEG);
        rect(f - 1, -1, f + WEEP_H, STOP_T + 1);
    }
    else if (name == "transom") {
        th = TRANSOM_W / 2 + TRANSOM_HALF_BODY;
        rect(th - 0.5, FIN_Y0 - 1, th + WEEP_H, FIN_Y1 + 1);
    }
    else if (name == "sash") rect(SASH_BODY - 1, SASH_Y0 - 1, SASH_BODY + WEEP_H, STOP_T + 1);
}

module tube_screw(name, z) {
    o = pocket_origin(name);
    p = pocket(name);
    h = top_face(name) - (o[1] + p[1]);
    translate([o[0] + p[0] / 2, o[1] + p[1] - EPS, z]) rotate([-90, 0, 0]) {
        cylinder(d = TUBE_SCREW_D, h = h + 1, $fn = 24);
        translate([0, 0, h - 2.2]) cylinder(d1 = TUBE_SCREW_D, d2 = 8.6, h = 2.2 + 2 * EPS, $fn = 32);
    }
}

module fixing_hole(name, z) {
    translate([-1, FIX_Y, z]) rotate([0, 90, 0]) cylinder(d = FIX_D, h = FRAME_W + 2, $fn = 24);
    translate([rebate_face(name) - FIX_CB_L, FIX_Y, z]) rotate([0, 90, 0])
        cylinder(d = FIX_CB_D, h = FIX_CB_L + 1, $fn = 32);
}

module boss_columns(name, z) {
    o = pocket_origin(name);
    p = pocket(name);
    for (dz = [-BOSS_PITCH / 2, BOSS_PITCH / 2])
        translate([boss_x(name), o[1] + p[1], z + dz]) rotate([-90, 0, 0])
            cylinder(d = INSERT_M4_D + 4, h = top_face(name) - (o[1] + p[1]), $fn = 32);
}

module screw_column(name, z) {
    o = pocket_origin(name);
    p = pocket(name);
    translate([o[0] + p[0] / 2, o[1] + p[1], z]) rotate([-90, 0, 0])
        cylinder(d = 10, h = top_face(name) - (o[1] + p[1]), $fn = 32);
}

module insert_holes(name, z) {
    for (dz = [-BOSS_PITCH / 2, BOSS_PITCH / 2])
        translate([boss_x(name), top_face(name) + EPS, z + dz]) rotate([90, 0, 0])
            cylinder(d = INSERT_M4_D, h = INSERT_M4_L, $fn = 24);
}

module segment(name, len, code, weep = false, bosses = false) {
    assert(len > 0 && len <= MAX_SEG, str(code, ": length ", len, " outside 0..", MAX_SEG));
    assert(!weep || name == "sill" || name == "transom" || name == "sash", str(code, ": no weep on ", name));
    assert(!bosses || boss_x(name) != undef, str(code, ": no bosses on ", name));
    difference() {
        union() {
            linear_extrude(len) profile(name);
            if (name != "screen") screw_column(name, len / 2);
            if (bosses) boss_columns(name, len / 2);
        }
        for (z = [-EPS, len - CORD_D / 2]) translate([0, 0, z]) linear_extrude(CORD_D / 2 + EPS) end_groove(name);
        tube_screw(name, len / 2);
        if (is_perimeter(name)) fixing_hole(name, len / 2);
        if (weep) translate([0, 0, len / 2 - WEEP_W / 2]) linear_extrude(WEEP_W) weep_cut(name);
        if (bosses) insert_holes(name, len / 2);
        engrave(code, label_at(name), len / 2);
    }
}
```

- [ ] **Step 5: Write `cad/parts/frame_segment.scad`**

```openscad
// cad/parts/frame_segment.scad
use <../lib/segment.scad>

module frame_segment(profile, len, code, weep = false, bosses = false) {
    segment(profile, len, code, weep, bosses);
}
```

- [ ] **Step 6: Run the assert test**

Run: `~/diy-window/cad/box.sh test`
Expected: `3 test files passed`

- [ ] **Step 7: Render one segment of every profile and feature combination and check the STLs**

Run: `~/diy-window/cad/box.sh render bench-600 H SW JL JU TE SBE SV NH`
Expected: no `ERROR`/`WARNING` lines, then `8/8 parts ok`. Each segment's `z` extent equals its `length` in `parts.csv`.

- [ ] **Step 8: Look at one**

Run: `~/diy-window/cad/box.sh png generated/parts/TE.scad ~/diy-window/docs/img/segment_TE.png --viewall --autocenter`
Expected: a transom segment showing the fin weep window, two insert holes either side of the tube-screw countersink on the inside face, and both end grooves.

- [ ] **Step 9: Checkpoint**

Run: `~/diy-window/cad/box.sh test && cd ~/diy-window/tools && python3 -m unittest discover -p 'test_*.py'`
Expected: `3 test files passed`, then `OK`.

---

### Task 8: Corner blocks, jamb node, transom shoe

**Corner blocks are true mitres.** Simply intersecting the two leg prisms would hollow out the region where one leg is solid body and the other is rebate, leaving the tube sockets open. Instead, each leg keeps its own profile on its side of the diagonal: leg A (which runs along `+X`) where `Z < X`, and leg B (which runs along `+Z`) where `X < Z`.
- Each leg has a `SOCKET`-deep tube pocket, a tube screw, an end cord groove and, on perimeter profiles, a fixing hole. The leg's fixing hole sits 48 mm from the outer corner, within the spec's 150 mm.
- The two sockets don't collide, because each tube runs inside its own leg's body zone.
- `mirrored = true` produces the right-hand sill/jamb corner.

**The transom connects with a dovetail.**
- Each **jamb node** is a plain body block, the full jamb tube passing through. On its rebate face it has a dovetail slot that is open at the inside face and stops at the outer stop.
- Each **transom shoe** is an 18 mm (`FRAME_W − FRAME_BODY`) slice of the transom profile. The left shoe is the mirror of the right, so the transom's glazing side stays at the bottom at both ends. It has a matching dovetail tongue, a 3 mm end wall, and the steel-tube socket.
- The assembled transom (tube, segments and both shoes) slides in from the room side until it hits the stop. Two M4 × 30 lock screws, driven from the inside face along the shoe/node seam, stop it sliding back out.
- That fixes the steel cut length at `1668 + 2·18 − 2·(3 + 1) = 1696` mm, which Task 2's tube test already expects.

**Files:**
- Create: `~/diy-window/cad/parts/corner_block.scad`
- Create: `~/diy-window/cad/parts/jamb_node.scad`
- Create: `~/diy-window/cad/parts/transom_shoe.scad`

- [ ] **Step 1: Render the parts that don't exist yet, to see them fail**

Run: `~/diy-window/cad/box.sh render bench-600 CH CSL CSR CS CN JN TSL TSR`
Expected: FAIL. `WARNING: Can't open library '../../parts/corner_block.scad'` and similar, then `0/8 parts ok`.

- [ ] **Step 2: Write `cad/parts/corner_block.scad`**

```openscad
// cad/parts/corner_block.scad
include <../generated/dims.scad>
use <../profile.scad>
use <../lib/segment.scad>
use <../lib/emboss.scad>

EPS = 0.01;
ALONG_X = [[0, 0, 1, 0], [0, 1, 0, 0], [1, 0, 0, 0]];

module half_space(lo, hi, below) {
    pts = below ? [[lo, lo], [hi, lo], [hi, hi]] : [[lo, lo], [hi, hi], [lo, hi]];
    translate([0, DEPTH + 1, 0]) rotate([90, 0, 0]) linear_extrude(DEPTH + 2) polygon(pts);
}

module corner_block(a, b, code, mirrored = false) {
    lo = min(profile_min(a), profile_min(b));
    hi = max(profile_width(a), profile_width(b));
    xa = [profile_min(b), profile_width(b)];
    za = [profile_min(a), profile_width(a)];
    mirror([mirrored ? 1 : 0, 0, 0]) difference() {
        union() {
            intersection() {
                multmatrix(ALONG_X) translate([0, 0, xa[0]]) linear_extrude(xa[1] - xa[0]) profile(a);
                half_space(lo - 1, hi + 1, true);
            }
            intersection() {
                translate([0, 0, za[0]]) linear_extrude(za[1] - za[0]) profile(b);
                half_space(lo - 1, hi + 1, false);
            }
        }
        multmatrix(ALONG_X) {
            translate([0, 0, xa[1] - SOCKET]) linear_extrude(SOCKET + EPS) pocket_cut(a);
            translate([0, 0, xa[1] - CORD_D / 2]) linear_extrude(CORD_D / 2 + EPS) end_groove(a);
            tube_screw(a, xa[1] - SOCKET / 2);
            if (is_perimeter(a)) fixing_hole(a, xa[1] - SOCKET / 2);
        }
        translate([0, 0, za[1] - SOCKET]) linear_extrude(SOCKET + EPS) pocket_cut(b);
        translate([0, 0, za[1] - CORD_D / 2]) linear_extrude(CORD_D / 2 + EPS) end_groove(b);
        tube_screw(b, za[1] - SOCKET / 2);
        if (is_perimeter(b)) fixing_hole(b, za[1] - SOCKET / 2);
        engrave(code, label_at(b), (za[0] + za[1]) / 2);
    }
}
```

- [ ] **Step 3: Write `cad/parts/jamb_node.scad`**

`dovetail2d(clear, root)` is shared with the shoe. `u` is the depth into the node (negative), `v` is the window-height offset from the transom centreline, and `root` is how far the shape extends on the shoe side of the seam.

```openscad
// cad/parts/jamb_node.scad
include <../generated/dims.scad>
use <../profile.scad>
use <../lib/segment.scad>
use <../lib/emboss.scad>

EPS = 0.01;

module dovetail2d(clear, root) {
    m = DOVE_W / 2 - clear;
    b = DOVE_W / 2 + DOVE_FLARE - clear;
    polygon([[root, -m], [root, m], [0, m], [-DOVE_D + clear, b], [-DOVE_D + clear, -b], [0, -m]]);
}

module node_groove() {
    difference() {
        offset(delta = -2) rect(0, 0, FRAME_BODY, DEPTH);
        offset(delta = -2 - CORD_D) rect(0, 0, FRAME_BODY, DEPTH);
    }
}

module jamb_node(code) {
    c = TRANSOM_W / 2;
    difference() {
        linear_extrude(TRANSOM_W) rect(0, 0, FRAME_BODY, DEPTH);
        translate([0, 0, -EPS]) linear_extrude(TRANSOM_W + 2 * EPS) pocket_cut("glazing");
        for (z = [-EPS, TRANSOM_W - CORD_D / 2]) translate([0, 0, z]) linear_extrude(CORD_D / 2 + EPS) node_groove();
        translate([FRAME_BODY, DEPTH + EPS, c]) rotate([90, 0, 0]) linear_extrude(DEPTH - STOP_T + EPS) dovetail2d(0, EPS);
        for (dz = [-LOCK_OFFSET, LOCK_OFFSET])
            translate([FRAME_BODY, DEPTH + EPS, c + dz]) rotate([90, 0, 0]) cylinder(d = LOCK_D, h = LOCK_L, $fn = 16);
        tube_screw("glazing", c);
        for (dz = [-NODE_FIX_OFFSET, NODE_FIX_OFFSET]) fixing_hole("glazing", c + dz);
        engrave(code, label_at("glazing"), c);
    }
}
```

- [ ] **Step 4: Write `cad/parts/transom_shoe.scad`**

```openscad
// cad/parts/transom_shoe.scad
include <../generated/dims.scad>
use <../profile.scad>
use <../lib/segment.scad>
use <../lib/emboss.scad>
use <jamb_node.scad>

EPS = 0.01;

module transom_shoe(code, mirrored = false) {
    L = FRAME_W - FRAME_BODY;
    c = TRANSOM_W / 2;
    translate([mirrored ? TRANSOM_W : 0, 0, 0]) mirror([mirrored ? 1 : 0, 0, 0]) difference() {
        union() {
            linear_extrude(L) profile("transom");
            multmatrix([[0, 1, 0, c], [0, 0, 1, STOP_T + 0.2], [1, 0, 0, 0]])
                linear_extrude(DEPTH - STOP_T - 0.2) dovetail2d(0.2, 1);
        }
        translate([0, 0, SHOE_WALL]) linear_extrude(L) pocket_cut("transom");
        translate([0, 0, L - CORD_D / 2]) linear_extrude(CORD_D / 2 + EPS) end_groove("transom");
        for (dx = [-LOCK_OFFSET, LOCK_OFFSET])
            translate([c + dx, DEPTH + EPS, 0]) rotate([90, 0, 0]) cylinder(d = LOCK_D, h = LOCK_L, $fn = 16);
        tube_screw("transom", SHOE_WALL + (L - SHOE_WALL) / 2);
        engrave(code, label_at("transom"), L / 2);
    }
}
```

- [ ] **Step 5: Render and check**

Run: `~/diy-window/cad/box.sh render bench-600 CH CSL CSR CS CN JN TSL TSR`
Expected: no `ERROR`/`WARNING` lines, `8/8 parts ok`.

- [ ] **Step 6: Fit check, node + shoe and a sill corner**

Write `cad/tests/fit_view.scad`:

```openscad
// cad/tests/fit_view.scad
include <../generated/dims.scad>
use <../parts/jamb_node.scad>
use <../parts/transom_shoe.scad>
use <../parts/corner_block.scad>

jamb_node("JN");
color("Orange") multmatrix([[0, 0, 1, FRAME_BODY], [0, 1, 0, 0], [-1, 0, 0, TRANSOM_W]]) transom_shoe("TSL", mirrored = true);
translate([150, 0, 0]) corner_block("sill", "glazing", "CSL");
translate([300, 0, 0]) corner_block("sash", "sash", "CS");
```

Run: `~/diy-window/cad/box.sh png tests/fit_view.scad ~/diy-window/docs/img/fit_view.png --camera=0,0,0,60,0,30,600 --viewall --autocenter`
Expected, by eye:
- the orange shoe's tongue sits inside the node's slot, against the face where the glazing rebate begins;
- the sill corner shows a continuous mitred stop leg and sloped floor;
- the sash corner shows the flange and lip wrapping around the outside of the corner.

- [ ] **Step 7: Checkpoint**

Run: `~/diy-window/cad/box.sh test && ~/diy-window/cad/box.sh render bench-600 H JL CH CSL CSR CS CN JN TSL TSR`
Expected: `3 test files passed`, `10/10 parts ok`.

---

### Task 9: Glazing and drainage small parts

These are all short, single-purpose parts:
- **`bead`:** the bead profile extruded to length, with its ID engraved small on the hidden face against the host.
- **`setting_block`:**
  - `wedge = true` (`GW`, 2 per window) sits on the sloped sill floor and gives the fixed pane a level bed at the glass edge.
  - Flat (`GF`, 6 per window) is a 3 mm block: 2 under the sash glass, 4 as side locators.
- **`weep_cap`:** a hood that press-fits into a weep slot's outer opening with two prongs. It is open only at the bottom, so water drains out and wind can't blow straight in. One cap fits both the sill and the sash weeps, which share the `WEEP_W` × `WEEP_H` slot.
- **`sill_nose`:** a 3 mm-walled sloped apron. It clips into the sill's outside keyway, laps 4 mm below the frame to cover the sill-tray edge and sealant joint, and has a drip notch on the inner face of its lip.
- **`acrylic_spacer`:** a `SPACER_W` × (`GLASS_T` − 2·`ACRYLIC_T` = 16) bar. Its 6 × 10 desiccant channel breathes into the air gap through 2 mm holes every 10 mm.
- **`acrylic_spacer_corner`:** an L that plugs both bars' channels and seals their ends.

**Files:**
- Create: `~/diy-window/cad/parts/bead.scad`
- Create: `~/diy-window/cad/parts/setting_block.scad`
- Create: `~/diy-window/cad/parts/weep_cap.scad`
- Create: `~/diy-window/cad/parts/sill_nose.scad`
- Create: `~/diy-window/cad/parts/acrylic_spacer.scad`

- [ ] **Step 1: Render to see them fail**

Run: `~/diy-window/cad/box.sh render bench-600 BFH BSV GW GF WC NS AFH AFV AC`
Expected: FAIL with `Can't open library` warnings, `0/9 parts ok`.

- [ ] **Step 2: Write `cad/parts/bead.scad`**

```openscad
// cad/parts/bead.scad
include <../generated/dims.scad>
use <../profile.scad>
use <../lib/emboss.scad>

module bead(glazing, len, code) {
    difference() {
        linear_extrude(len) bead_profile(glazing);
        engrave(code, [0, bead_seat_y() + BEAD_T - 2.5], len / 2, 3);
    }
}
```

- [ ] **Step 3: Write `cad/parts/setting_block.scad`**

```openscad
// cad/parts/setting_block.scad
include <../generated/dims.scad>
use <../profile.scad>
use <../lib/emboss.scad>

module setting_block(code, wedge = false) {
    s = tan(SILL_SLOPE_DEG);
    floor_x = function(y) FRAME_BODY - (bead_seat_y() - y) * s;
    y0 = GLASS_Y0;
    y1 = GLASS_Y0 + GLASS_T;
    pts = wedge ? [[floor_x(y0), y0], [floor_x(y1), y1], [GLASS_EDGE, y1], [GLASS_EDGE, y0]]
                : [[0, y0], [0, y1], [GLASS_CLEAR, y1], [GLASS_CLEAR, y0]];
    difference() {
        linear_extrude(SETTING_L) polygon(pts);
        engrave(code, [wedge ? floor_x(y0) + 0.2 : 0, (y0 + y1) / 2], SETTING_L / 2, 3);
    }
}
```

- [ ] **Step 4: Write `cad/parts/weep_cap.scad`**

The cap's own frame: `x` is up (0 = open bottom), `y` points away from the wall (0 = back, against the frame face), `z` runs along the slot.

```openscad
// cad/parts/weep_cap.scad
include <../generated/dims.scad>
use <../lib/emboss.scad>

module weep_cap(code) {
    w = WEEP_W + 10;
    t = WEEP_CAP_T;
    sx = (WEEP_CAP_H - WEEP_H) / 2;
    difference() {
        union() {
            cube([WEEP_CAP_H, 4, w]);
            for (z = [5 + 0.2, w - 5 - 0.2 - 1.2])
                translate([sx + 0.2, -3, z]) cube([WEEP_H - 0.4, 3.01, 1.2]);
        }
        translate([-1, -0.01, t]) cube([WEEP_CAP_H - t + 1, 4 - t + 0.01, w - 2 * t]);
    }
}
```

- [ ] **Step 5: Write `cad/parts/sill_nose.scad`**

Drawn in sill-profile coordinates (`x` up, `y` outward is negative), so it reads directly against the `sill` profile.

```openscad
// cad/parts/sill_nose.scad
include <../generated/dims.scad>
use <../profile.scad>
use <../lib/emboss.scad>

module nose_profile() {
    s = tan(SILL_SLOPE_DEG);
    p = NOSE_PROJECTION;
    top = NOSE_KEY_X + NOSE_KEY_W + 6;
    xt = function(y) top + y * s;
    difference() {
        union() {
            polygon([[top, 0], [NOSE_KEY_X - 2, 0], [NOSE_KEY_X - 2, -3], [xt(-3) - 3, -3],
                     [xt(-p + 3) - 3, -p + 3], [-4, -p + 3], [-4, -p], [xt(-p), -p]]);
            translate([NOSE_KEY_X, 0]) key_tongue(NOSE_KEY_D, NOSE_KEY_W);
        }
        rect(-2, -p + 2.4, 0, -p + 3 + 0.01);
    }
}

module sill_nose(len, code) {
    difference() {
        linear_extrude(len) nose_profile();
        engrave(code, [NOSE_KEY_X - 2, -1.5], len / 2, 2);
    }
}
```

- [ ] **Step 6: Write `cad/parts/acrylic_spacer.scad`**

```openscad
// cad/parts/acrylic_spacer.scad
include <../generated/dims.scad>
use <../profile.scad>
use <../lib/emboss.scad>

function spacer_t() = GLASS_T - 2 * ACRYLIC_T;

module spacer_channel() { rect(3, 3, SPACER_W - 3, spacer_t() - 3); }

module acrylic_spacer(len, code) {
    difference() {
        linear_extrude(len) rect(0, 0, SPACER_W, spacer_t());
        translate([0, 0, -0.01]) linear_extrude(len + 0.02) spacer_channel();
        for (z = [10 : 10 : len - 5])
            translate([SPACER_W - 3.5, spacer_t() / 2, z]) rotate([0, 90, 0]) cylinder(d = 2, h = 4, $fn = 12);
        engrave(code, [0, spacer_t() / 2], len / 2, 3);
    }
}

module acrylic_spacer_corner(code) {
    leg = 15;
    plug = [SPACER_W - 6 - 0.3, spacer_t() - 6 - 0.3];
    linear_extrude(spacer_t()) square([SPACER_W, SPACER_W]);
    translate([SPACER_W, 3.15, 3.15]) cube([leg, plug[0], plug[1]]);
    translate([3.15, SPACER_W, 3.15]) cube([plug[0], leg, plug[1]]);
}
```

- [ ] **Step 7: Render and check**

Run: `~/diy-window/cad/box.sh render bench-600 BFH BSV GW GF WC NS AFH AFV AC`
Expected: no `ERROR`/`WARNING` lines, `9/9 parts ok`.

- [ ] **Step 8: Check the twin-wall bead too**

Run: `cd ~/diy-window && python3 -c "import json;p=json.load(open('params/bench-600.json'));p.update(name='bench-600-tw',glazing='twinwall');json.dump(p,open('params/bench-600-tw.json','w'))" && cad/box.sh render bench-600-tw BFH; rm -f params/bench-600-tw.json`
Expected: `1/1 parts ok`.

- [ ] **Step 9: Checkpoint**

Run: `~/diy-window/cad/box.sh test`
Expected: `3 test files passed`

---

### Task 10: Cam lock, screen hinge, test coupon

**Cam lock (2 per window).** It is a ramped wedge that pulls the sash onto both seals. All three parts are drawn in *transom-face coordinates*:
- `u` runs along the transom;
- `v` runs up the window from the cam insert line (transom profile `x = CAM_BOSS_X`);
- `w` runs into the room from the transom inside face.

The three parts:
- **`cam_base` (CMB)** screws to the two inserts in a `TE` transom segment. Its central boss carries an M4 insert, which is the pivot.
- **`cam_handle` (CMH)** turns on the boss and is held by an M4 screw plus a 20 mm penny washer. Its flag is a helical ramp, 18–40 mm out from the pivot over a 40° arc, rising from 2 mm thick at the leading edge to 5 mm at the trailing edge. Closed, the flag points up (`+v`) and the lever points sideways (`−u`).
- **`cam_keeper` (KP)** screws to the two inserts in an `SBE` sash segment. Its post comes into the room past the transom face, and a lip hooks back down over the flag.

How it works:
- With the seals just touching, the lip's underside sits at `w = 6`, the flag's leading-edge height. Turning the lever 60° counter-clockwise drives the ramp under the lip and pulls the sash 3 mm inward, which is the seal compression designed in Task 6.
- Everything stays within `w < 20`, so the closed screen covers it.
- The keeper post is 10 mm thick in `v`, sized for about 150 N of seal pull per lock (≈15 MPa bending in PETG).

**Screen hinge (2–3 per window).** It has two leaves and an M4 × 40 bolt with a nyloc nut as the pin. The axis sits 5 mm in front of the screen's room face, at its top edge, so the screen swings up and into the room.
- **`screen_hinge` (HG):** the frame leaf, screwed to a pair of `H` head-segment inserts.
- **`screen_leaf` (HS):** screwed into the screen top rail between its tube pocket and its spline groove.

**Test coupon (TC).** A 60 mm `sash_rebate` segment with an insert pair, for the heat/creep test in Task 14.

**Files:**
- Create: `~/diy-window/cad/parts/cam_lock.scad`
- Create: `~/diy-window/cad/parts/screen_hinge.scad`
- Create: `~/diy-window/cad/parts/test_coupon.scad`

- [ ] **Step 1: Render to see them fail**

Run: `~/diy-window/cad/box.sh render bench-600 CMB CMH KP HG HS TC`
Expected: FAIL with `Can't open library` warnings, `0/6 parts ok`.

- [ ] **Step 2: Write `cad/parts/cam_lock.scad`**

```openscad
// cad/parts/cam_lock.scad
include <../generated/dims.scad>

R0 = 18;
R1 = 40;
LEAD = 2;
RISE = 3;
ARC = 40;
BASE_T = 4;
BOSS_D = 14;
BOSS_H = 5;
LIP_T = 3;

function sash_face_w() = LIP_Y1 - DEPTH;
function keeper_v() = TRANSOM_W / 2 + TRANSOM_HALF_BODY + SASH_GAP + SASH_BODY / 2 - CAM_BOSS_X;
function lip_w() = BASE_T + LEAD + RISE;

module countersunk(d, t) {
    translate([0, 0, -0.01]) cylinder(d = d, h = t + 0.02, $fn = 20);
    translate([0, 0, t - 2.2]) cylinder(d1 = d, d2 = 8.6, h = 2.21, $fn = 24);
}

module cam_base(code) {
    difference() {
        union() {
            translate([-20, -10, 0]) cube([40, 22, BASE_T]);
            cylinder(d = BOSS_D, h = BASE_T + BOSS_H, $fn = 48);
        }
        for (u = [-BOSS_PITCH / 2, BOSS_PITCH / 2]) translate([u, 0, 0]) countersunk(4.4, BASE_T);
        translate([0, 0, BASE_T + BOSS_H - INSERT_M4_L + 0.01]) cylinder(d = INSERT_M4_D, h = INSERT_M4_L, $fn = 24);
    }
}

module flag_slice(k) {
    rotate([0, 0, 90 - ARC / 2 + k * ARC / 8])
        translate([R0, -0.5, BASE_T]) cube([R1 - R0, 1, LEAD + RISE * (1 - k / 8)]);
}

module cam_handle(code) {
    difference() {
        union() {
            translate([0, 0, BASE_T]) cylinder(d = 26, h = BOSS_H - 0.3, $fn = 48);
            for (k = [0 : 7]) hull() { flag_slice(k); flag_slice(k + 1); }
            translate([-64, -6, BASE_T]) cube([58, 12, 10]);
            translate([-64, 0, BASE_T]) cylinder(d = 16, h = 10, $fn = 32);
        }
        translate([0, 0, BASE_T - 0.01]) cylinder(d = BOSS_D + 0.4, h = BOSS_H + 0.02, $fn = 48);
    }
}

module cam_keeper(code) {
    kv = keeper_v();
    sw = sash_face_w();
    difference() {
        union() {
            translate([-20, kv - 6, sw]) cube([40, 22, 3]);
            translate([-8, kv + 5, sw]) cube([16, 10, lip_w() + LIP_T - sw]);
            translate([-10, R0 - 2, lip_w()]) cube([20, kv + 15 - (R0 - 2), LIP_T]);
        }
        for (u = [-BOSS_PITCH / 2, BOSS_PITCH / 2]) translate([u, kv, sw]) countersunk(4.4, 3);
    }
}
```

- [ ] **Step 3: Write `cad/parts/screen_hinge.scad`**

The hinge's own frame: `u` runs along the window, `v` runs down from the screen top edge, and `w` runs into the room from the head's inside face.

```openscad
// cad/parts/screen_hinge.scad
include <../generated/dims.scad>

KN_D = 10;
PIN_D = 4.3;
LEAF_T = 3;
AXIS_W = SCREEN_DEPTH + 5;
FRAME_KN = [[-20, -12], [-4, 4], [12, 20]];
SCREEN_KN = [[-11.6, -4.4], [4.4, 11.6]];

module knuckles(spans) {
    for (s = spans) translate([s[0], 0, AXIS_W]) rotate([0, 90, 0]) cylinder(d = KN_D, h = s[1] - s[0], $fn = 32);
}

module pin_hole() {
    translate([-21, 0, AXIS_W]) rotate([0, 90, 0]) cylinder(d = PIN_D, h = 42, $fn = 20);
}

module screen_hinge(code) {
    v_hole = HINGE_BOSS_X - (FRAME_BODY - SCREEN_OVERLAP);
    difference() {
        union() {
            translate([-20, -20, 0]) cube([40, 17, LEAF_T]);
            translate([-20, -3, 0]) cube([40, 3, AXIS_W]);
            knuckles(FRAME_KN);
        }
        pin_hole();
        for (u = [-BOSS_PITCH / 2, BOSS_PITCH / 2])
            translate([u, v_hole, -0.01]) cylinder(d = 4.4, h = LEAF_T + 0.02, $fn = 20);
    }
}

module screen_leaf(code) {
    difference() {
        union() {
            translate([-12, 3, SCREEN_DEPTH]) cube([24, 25, LEAF_T]);
            translate([-12, 0, SCREEN_DEPTH]) cube([24, 5, AXIS_W - SCREEN_DEPTH]);
            knuckles(SCREEN_KN);
        }
        pin_hole();
        for (u = [-8, 8]) translate([u, 18, SCREEN_DEPTH - 0.01]) cylinder(d = 3.4, h = LEAF_T + 0.02, $fn = 16);
    }
}
```

- [ ] **Step 4: Write `cad/parts/test_coupon.scad`**

```openscad
// cad/parts/test_coupon.scad
use <../lib/segment.scad>

module test_coupon(code) {
    segment("sash_rebate", 60, code, false, true);
}
```

- [ ] **Step 5: Render and check**

Run: `~/diy-window/cad/box.sh render bench-600 CMB CMH KP HG HS TC`
Expected: no `ERROR`/`WARNING` lines, `6/6 parts ok`.

- [ ] **Step 6: Look at the lock closed**

Write `cad/tests/lock_view.scad`:

```openscad
// cad/tests/lock_view.scad
include <../generated/dims.scad>
use <../parts/cam_lock.scad>
use <../profile.scad>

sash_v = TRANSOM_W / 2 + TRANSOM_HALF_BODY + SASH_GAP - CAM_BOSS_X;
color("SteelBlue") multmatrix([[0, 0, 1, -60], [1, 0, 0, -CAM_BOSS_X], [0, 1, 0, -DEPTH]]) linear_extrude(120) profile("transom");
color("LightSteelBlue") multmatrix([[0, 0, 1, -60], [1, 0, 0, sash_v], [0, 1, 0, -DEPTH]]) linear_extrude(120) profile("sash");
cam_base("CMB");
color("Orange") cam_handle("CMH");
color("Red") cam_keeper("KP");
```

Run: `~/diy-window/cad/box.sh png tests/lock_view.scad ~/diy-window/docs/img/lock_view.png --camera=0,0,0,65,0,210,350 --viewall --autocenter`
Expected, by eye:
- the red keeper lip sits just above the orange flag's thick end;
- the keeper post clears the blue transom's top edge and stands on the pale sash bottom rail;
- the base sits on the transom's inside face above the magnet channel.

- [ ] **Step 7: Checkpoint**

Run: `~/diy-window/cad/box.sh test && cd ~/diy-window/tools && python3 -m unittest discover -p 'test_*.py'`
Expected: `3 test files passed`, `OK`.

---

### Task 11: Full render of both windows and an assembly preview

`assembly.scad` shows the members as continuous profile runs, with the real corner blocks, nodes and glass, so the whole window can be checked by eye. It is for visual checks only: the STLs come from the per-part wrappers. It reads `generated/layout.scad`, so it always matches the last `generate.py` run.

Window coordinates: `X` across the width from the left frame edge, `Z` up from the frame bottom, `Y` through the depth from the outside face.

**Files:**
- Create: `~/diy-window/cad/assembly.scad`

- [ ] **Step 1: Write `cad/assembly.scad`**

```openscad
// cad/assembly.scad
include <generated/dims.scad>
include <generated/layout.scad>
use <profile.scad>
use <parts/corner_block.scad>
use <parts/jamb_node.scad>
use <parts/transom_shoe.scad>

section = false;

module run(name, len, m) { multmatrix(m) linear_extrude(len) profile(name); }

module frame() {
    F = FRAME_W;
    tb = TRANSOM_C - TRANSOM_W / 2;
    run("sill", W - 2 * F, [[0, 0, 1, F], [0, 1, 0, 0], [1, 0, 0, 0]]);
    run("sash_rebate", W - 2 * F, [[0, 0, 1, F], [0, 1, 0, 0], [-1, 0, 0, H]]);
    run("transom", W - 2 * F, [[0, 0, 1, F], [0, 1, 0, 0], [1, 0, 0, tb]]);
    for (s = [[1, 0], [-1, W]]) {
        run("glazing", tb - F, [[s[0], 0, 0, s[1]], [0, 1, 0, 0], [0, 0, 1, F]]);
        run("sash_rebate", H - F - (tb + TRANSOM_W), [[s[0], 0, 0, s[1]], [0, 1, 0, 0], [0, 0, 1, tb + TRANSOM_W]]);
        translate([s[1], 0, tb]) mirror([s[0] < 0 ? 1 : 0, 0, 0]) {
            jamb_node("JN");
            multmatrix([[0, 0, 1, FRAME_BODY], [0, 1, 0, 0], [-1, 0, 0, TRANSOM_W]]) transom_shoe("TSL", mirrored = true);
        }
    }
    corner_block("sill", "glazing", "CSL");
    translate([W, 0, 0]) corner_block("sill", "glazing", "CSR", mirrored = true);
    translate([0, 0, H]) mirror([0, 0, 1]) corner_block("sash_rebate", "sash_rebate", "CH");
    translate([W, 0, H]) mirror([1, 0, 0]) mirror([0, 0, 1]) corner_block("sash_rebate", "sash_rebate", "CH");
}

module sash() {
    x0 = FRAME_BODY + SASH_GAP;
    z0 = TRANSOM_C + TRANSOM_HALF_BODY + SASH_GAP;
    S = SASH_W;
    run("sash", SASH[0] - 2 * S, [[0, 0, 1, x0 + S], [0, 1, 0, 0], [1, 0, 0, z0]]);
    run("sash", SASH[0] - 2 * S, [[0, 0, 1, x0 + S], [0, 1, 0, 0], [-1, 0, 0, z0 + SASH[1]]]);
    run("sash", SASH[1] - 2 * S, [[1, 0, 0, x0], [0, 1, 0, 0], [0, 0, 1, z0 + S]]);
    run("sash", SASH[1] - 2 * S, [[-1, 0, 0, x0 + SASH[0]], [0, 1, 0, 0], [0, 0, 1, z0 + S]]);
    translate([x0, 0, z0]) corner_block("sash", "sash", "CS");
    translate([x0 + SASH[0], 0, z0]) mirror([1, 0, 0]) corner_block("sash", "sash", "CS");
    translate([x0, 0, z0 + SASH[1]]) mirror([0, 0, 1]) corner_block("sash", "sash", "CS");
    translate([x0 + SASH[0], 0, z0 + SASH[1]]) mirror([1, 0, 0]) mirror([0, 0, 1]) corner_block("sash", "sash", "CS");
    color("LightBlue", 0.35) translate([x0 + SASH_GLASS, GLASS_Y0, z0 + SASH_GLASS]) cube([SASH_GLASS_DIMS[0], GLASS_T, SASH_GLASS_DIMS[1]]);
}

module window() {
    color("WhiteSmoke") frame();
    color("Gainsboro") sash();
    color("LightBlue", 0.35) translate([GLASS_EDGE, GLASS_Y0, GLASS_EDGE]) cube([FIXED_GLASS[0], GLASS_T, FIXED_GLASS[1]]);
}

if (section) intersection() {
    window();
    translate([W / 2 - 1, -50, -50]) cube([2, DEPTH + 100, H + 100]);
}
else window();
```

`layout.scad` names the sash pane size `SASH_GLASS_DIMS`, because `SASH_GLASS` is already the `dims` name for the sash edge-to-glass distance.

- [ ] **Step 2: Render every part of the bench window**

Run: `~/diy-window/cad/box.sh render bench-600`
Expected: no `ERROR`/`WARNING` lines, `37/37 parts ok`.

- [ ] **Step 3: Render every part of the home window**

Run: `~/diy-window/cad/box.sh render home-1800x1500`
Expected: no `ERROR`/`WARNING` lines, `35/35 parts ok` (no acrylic spacers, three hinges).

- [ ] **Step 4: Preview both assemblies**

Run:
```
PARAMS=bench-600 ~/diy-window/cad/box.sh png assembly.scad ~/diy-window/docs/img/assembly-bench-600.png --camera=0,0,0,70,0,200,0 --viewall --autocenter
PARAMS=home-1800x1500 ~/diy-window/cad/box.sh png assembly.scad ~/diy-window/docs/img/assembly-home.png --camera=0,0,0,70,0,200,0 --viewall --autocenter
```
Then the mid-width section of the home window, seen from the side:

```
PARAMS=home-1800x1500 ~/diy-window/cad/box.sh png assembly.scad ~/diy-window/docs/img/section-home.png -D section=true --camera=0,0,0,90,0,90,0 --viewall --autocenter --projection=ortho
```

Expected, by eye, for the two assembly views (seen from the room side):
- a closed rectangular frame with the transom near the top and the sash in the awning opening;
- the fixed glass seated in its rebate;
- no member poking through another;
- the sash flange visible around the sash edge, outside the frame fin.

Expected for the section:
- the head, transom and sill all span the same 70 mm depth;
- the fixed glass and the sash glass sit in the same plane (`y` 11–35);
- the sash bottom-rail flange laps over the transom fin, and its inner lip sits over the transom inner stop.

- [ ] **Step 5: Checkpoint**

Run: `cd ~/diy-window/tools && python3 -m unittest discover -p 'test_*.py' && ~/diy-window/cad/box.sh test`
Expected: `OK`, `3 test files passed`.

---

### Task 12: Bill of materials (`bom/build_bom.py`)

The BOM is built from the generator's outputs plus the rendered STLs, so it always matches the actual parts. It lists quantities only. Prices are left for the builder, because they change and vary by supplier.

Counting rules, all derived from `parts.csv` quantities:
- **Tube screws** (8g × 25 stainless self-tappers): one per frame or sash segment, two per frame or sash corner, one per jamb node, one per shoe. Screen tubes are held by the corners, not screwed.
- **Fixing screws** (10g × 65 timber screws into the reveal): one per perimeter segment, two per perimeter corner, two per jamb node.
- **M4 heat-set inserts:** two per `bosses` segment, one per cam base, two in the test coupon.
- **EPDM bulb seal:** two runs (outer and inner) around the sash perimeter.
- **Glazing wedge gasket:** both faces around each pane.
- **Magnetic strip:** the screen perimeter, twice (once on the screen, once on the frame).
- **Foam cord:** about 0.3 m per joint, where joints = segments + members.
- **Filament:** mass is estimated from each STL as a 2.1 mm shell (5 walls) plus 15% infill. Density is 1.27 g/cm³ (PETG) for interior parts, and 1.07 g/cm³ (ASA) or 1.20 g/cm³ (PC-ABS / ASA-CF class) for exterior parts, by tier.

**Files:**
- Modify: `~/diy-window/tools/stl.py` (add `volume_area`)
- Modify: `~/diy-window/tools/test_stl.py` (add a volume test)
- Create: `~/diy-window/bom/build_bom.py`
- Test: `~/diy-window/tools/test_bom.py`

- [ ] **Step 1: Add a failing volume test**

Append to the `StlTest` class in `tools/test_stl.py`:

```python
    def testUnitCubeVolumeAndArea(self):
        v = [(0, 0, 0), (10, 0, 0), (10, 10, 0), (0, 10, 0), (0, 0, 10), (10, 0, 10), (10, 10, 10), (0, 10, 10)]
        faces = [(0, 2, 1), (0, 3, 2), (4, 5, 6), (4, 6, 7), (0, 1, 5), (0, 5, 4),
                 (1, 2, 6), (1, 6, 5), (2, 3, 7), (2, 7, 6), (3, 0, 4), (3, 4, 7)]
        writeBinary(self.dir / "c.stl", [tuple(v[i] for i in f) for f in faces])
        vol, area = stl.volume_area(stl.load(self.dir / "c.stl"))
        self.assertAlmostEqual(vol, 1.0, places=6)
        self.assertAlmostEqual(area, 6.0, places=6)
```

Run: `cd ~/diy-window/tools && python3 -m unittest test_stl -v`
Expected: FAIL with `AttributeError: module 'stl' has no attribute 'volume_area'`.

- [ ] **Step 2: Add `volume_area` to `tools/stl.py`**

```python
def volume_area(tris):
    v = a = 0.0
    for p, q, r in tris:
        v += (p[0] * (q[1] * r[2] - q[2] * r[1]) - p[1] * (q[0] * r[2] - q[2] * r[0])
              + p[2] * (q[0] * r[1] - q[1] * r[0])) / 6.0
        ux, uy, uz = q[0] - p[0], q[1] - p[1], q[2] - p[2]
        wx, wy, wz = r[0] - p[0], r[1] - p[1], r[2] - p[2]
        a += 0.5 * ((uy * wz - uz * wy) ** 2 + (uz * wx - ux * wz) ** 2 + (ux * wy - uy * wx) ** 2) ** 0.5
    return abs(v) / 1000.0, a / 100.0
```

Run: `cd ~/diy-window/tools && python3 -m unittest test_stl -v`
Expected: 8 tests `ok`.

- [ ] **Step 3: Write the failing BOM tests**

```python
# tools/test_bom.py
"""Unit tests for bom/build_bom.py."""
import importlib.util
import json
import pathlib
import unittest

import generate
import window

ROOT = pathlib.Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("build_bom", ROOT / "bom" / "build_bom.py")
build_bom = importlib.util.module_from_spec(spec)
spec.loader.exec_module(build_bom)


class HomeBomTest(unittest.TestCase):
    def setUp(self):
        self.lay = window.layout(json.loads((ROOT / "params" / "home-1800x1500.json").read_text()))
        self.items = {i["item"]: i for i in build_bom.hardware(self.lay, generate.parts(self.lay))}

    def qty(self, key):
        return next(i["qty"] for k, i in self.items.items() if k.startswith(key))

    def testFixingScrews(self):
        self.assertEqual(self.qty("Timber screw 10g x 65"), 38)

    def testTubeScrews(self):
        self.assertEqual(self.qty("Self-tapping screw 8g x 25"), 71)

    def testInserts(self):
        self.assertEqual(self.qty("M4 heat-set insert"), 26)

    def testSashSealMetres(self):
        self.assertEqual(self.qty("EPDM bulb kerf seal"), 8.55)

    def testMagneticStripMetres(self):
        self.assertEqual(self.qty("Flexible magnetic strip"), 9.06)

    def testStayPair(self):
        self.assertIn("400 mm", next(k for k in self.items if k.startswith("Stainless friction stay")))

    def testTubeMetresByCore(self):
        steel = next(i for k, i in self.items.items() if "steel40x20" in k)
        self.assertEqual(steel["qty"], 1.7)

    def testNoAcrylicItemsForIgu(self):
        self.assertFalse([k for k in self.items if "esiccant" in k])


class MassTest(unittest.TestCase):
    def testSolidSmallPartIsAllShell(self):
        self.assertAlmostEqual(build_bom.mass_g(1.0, 6.0, 1.27), 1.27, places=3)

    def testLargePartUsesInfill(self):
        self.assertAlmostEqual(build_bom.mass_g(100.0, 100.0, 1.0), 21.0 + 79.0 * 0.15, places=3)


if __name__ == "__main__":
    unittest.main()
```

Run: `cd ~/diy-window/tools && python3 -m unittest test_bom -v`
Expected: FAIL with `FileNotFoundError` for `bom/build_bom.py`.

- [ ] **Step 4: Write `bom/build_bom.py`**

```python
#!/usr/bin/env python3
"""Build bom/<name>.csv and bom/<name>.md from the layout, the part list and the rendered STLs."""
import csv
import json
import math
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import generate  # noqa: E402
import stl  # noqa: E402
import window  # noqa: E402

SHELL_MM = 2.1
INFILL = 0.15
DENSITY = {"interior": 1.27, 1: 1.27, 2: 1.07, 3: 1.20}
MATERIAL = {"interior": "PETG", 1: "PETG + exterior paint, or ASA", 2: "ASA", 3: "ASA-CF or PC-ABS (light colour)"}
CORD_PER_JOINT_M = 0.3
FRAME_SEGMENTS = {"H", "S", "SW", "JL", "JU", "T", "TE", "SH", "SB", "SBE", "SV"}
PERIMETER_SEGMENTS = {"H", "S", "SW", "JL", "JU"}
FRAME_CORNERS = {"CH", "CSL", "CSR", "CS"}
PERIMETER_CORNERS = {"CH", "CSL", "CSR"}
BOSS_SEGMENTS = {"H", "TE", "SBE"}


def mass_g(vol_cm3, area_cm2, density):
    shell = min(vol_cm3, area_cm2 * SHELL_MM / 10.0)
    return (shell + (vol_cm3 - shell) * INFILL) * density


def hardware(lay, parts):
    q = {p["id"]: p["qty"] for p in parts}
    total = lambda ids: sum(q.get(i, 0) for i in ids)
    sash_w, sash_h = lay["sash"]
    scr_w, scr_h = lay["screen"]
    m = lambda mm: round(mm / 1000.0, 2)
    perim = lambda wh: 2 * (wh[0] + wh[1])
    hinges = q["HG"]
    joints = total(FRAME_SEGMENTS) + len(lay["members"])
    items = [
        ("Fixings", "Timber screw 10g x 65, stainless or galvanised", total(PERIMETER_SEGMENTS)
         + 2 * total(PERIMETER_CORNERS) + 2 * q["JN"], "pcs"),
        ("Fixings", "Self-tapping screw 8g x 25 stainless, countersunk (tube screws)", total(FRAME_SEGMENTS)
         + 2 * total(FRAME_CORNERS) + q["JN"] + q["TSL"] + q["TSR"], "pcs"),
        ("Fixings", "M4 heat-set insert, 5.6 x 8 mm", 2 * total(BOSS_SEGMENTS) + q["CMB"] + 2 * q["TC"], "pcs"),
        ("Fixings", "M4 x 12 countersunk machine screw (cam bases, keepers, hinge frame leaves)",
         2 * q["CMB"] + 2 * q["KP"] + 2 * hinges, "pcs"),
        ("Fixings", "M4 x 30 countersunk machine screw (transom lock screws)", 4, "pcs"),
        ("Fixings", "M4 x 10 pan screw + 20 mm penny washer (cam pivots)", q["CMH"], "pcs"),
        ("Fixings", "M4 x 40 bolt + nyloc nut (hinge pins)", hinges, "pcs"),
        ("Fixings", "4g x 12 self-tapping screw (screen leaves)", 2 * hinges, "pcs"),
        ("Fixings", "Plastic window packers, assorted 1-10 mm", 12, "pcs"),
        ("Seals", "EPDM bulb kerf seal, 3 mm kerf (sash outer + inner)", m(2 * perim(lay["sash"])), "m"),
        ("Seals", "EPDM glazing wedge gasket, 3 mm", m(2 * (perim(lay["glass"]["fixed"]) + perim(lay["glass"]["sash"]))), "m"),
        ("Seals", "Closed-cell foam cord, 3 mm (segment joints, approx.)", round(joints * CORD_PER_JOINT_M, 1), "m"),
        ("Seals", "MS-polymer sealant, 290 ml cartridge", math.ceil(perim((lay["w"], lay["h"])) / 1000 * 1.5 / 6), "pcs"),
        ("Seals", "Butyl flashing tape, 100 mm wide (sill tray)", m(lay["w"] + 300), "m"),
        ("Seals", "Backer rod, 10 mm", m(perim((lay["w"], lay["h"]))), "m"),
        ("Seals", "Low-expansion window foam, can", 1, "pcs"),
        ("Hardware", f"Stainless friction stay pair, {lay['stay']} mm (check rating >= {lay['sash_kg']} kg)", 1, "pair"),
        ("Screen", "Flexible magnetic strip, 12.7 mm, adhesive-backed", m(2 * perim(lay["screen"])), "m"),
        ("Screen", "Fibreglass insect mesh", round(scr_w * scr_h / 1e6 * 1.1, 2), "m2"),
        ("Screen", "Screen spline, 4 mm", m(perim(lay["screen"])), "m"),
    ]
    by_core = {}
    for t in lay["tubes"]:
        by_core[t["core"]] = by_core.get(t["core"], 0) + t["length"] * t["qty"]
    for core, mm in sorted(by_core.items()):
        items.append(("Tube", f"Tube {core} (total length; buy in 1 m/3 m stock)", m(mm), "m"))
    for pane, (gw, gh) in lay["glass"].items():
        g = lay["params"]["glazing"]
        if g == "acrylic":
            items.append(("Glazing", f"Acrylic 4 mm, {gw} x {gh} ({pane} pane)", 2, "pcs"))
        else:
            items.append(("Glazing", f"{generate.GLASS_SPEC[g]}, {gw} x {gh} ({pane} pane)", 1, "pcs"))
    if lay["params"]["glazing"] == "acrylic":
        items.append(("Glazing", "Silica gel desiccant beads", 100, "g"))
        items.append(("Glazing", "Butyl glazing tape, 3 mm (acrylic sandwich edge)", m(2 * sum(perim(v) for v in lay["glass"].values())), "m"))
    return [{"group": g, "item": i, "qty": n, "unit": u} for g, i, n, u in items]


def filament(lay, parts, stl_dir):
    tier = lay["params"]["tier"]
    grams = {"interior": 0.0, tier: 0.0}
    missing = []
    for p in parts:
        f = pathlib.Path(stl_dir) / f"{p['id']}.stl"
        if not f.exists():
            missing.append(p["id"])
            continue
        key = "interior" if p["role"] == "interior" else tier
        vol, area = stl.volume_area(stl.load(f))
        grams[key] += mass_g(vol, area, DENSITY[key]) * p["qty"]
    rows = [{"group": "Filament", "item": f"{MATERIAL[k]} ({'interior' if k == 'interior' else f'exterior, tier {k}'})",
             "qty": round(g / 1000.0, 2), "unit": "kg"} for k, g in grams.items()]
    return rows, missing


def main(argv):
    if len(argv) != 2:
        print("usage: build_bom.py <params-name>", file=sys.stderr)
        return 2
    name = argv[1]
    lay = window.layout(json.loads((ROOT / "params" / f"{name}.json").read_text()))
    parts = generate.parts(lay)
    fil, missing = filament(lay, parts, ROOT / "cad" / "stl" / name)
    items = hardware(lay, parts) + fil
    with (ROOT / "bom" / f"{name}.csv").open("w", newline="") as fh:
        wr = csv.DictWriter(fh, ["group", "item", "qty", "unit"])
        wr.writeheader()
        wr.writerows(items)
    lines = [f"# BOM: {name}", "", f"Prints: {sum(p['qty'] for p in parts)} parts in {len(parts)} types.", "",
             "| Group | Item | Qty | Unit |", "|---|---|---|---|"]
    lines += [f"| {i['group']} | {i['item']} | {i['qty']} | {i['unit']} |" for i in items]
    if missing:
        lines += ["", f"Filament excludes unrendered parts: {', '.join(missing)}. Run `cad/box.sh render {name}` first."]
    (ROOT / "bom" / f"{name}.md").write_text("\n".join(lines) + "\n")
    print(f"bom/{name}.csv, bom/{name}.md: {len(items)} lines" + (f", {len(missing)} STLs missing" if missing else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
```

- [ ] **Step 5: Run the tests to verify they pass**

Run: `cd ~/diy-window/tools && python3 -m unittest discover -p 'test_*.py'`
Expected: `OK`.

- [ ] **Step 6: Build the real BOMs (after Task 11's renders)**

Run: `cd ~/diy-window && python3 bom/build_bom.py home-1800x1500 && python3 bom/build_bom.py bench-600 && cat bom/home-1800x1500.md`
Expected: two BOMs with no "STLs missing" note. At plan time the measured totals were:
- home window: about 16.0 kg of exterior filament (tier 3) plus 3.9 kg of interior PETG;
- bench window: about 6.0 kg plus 1.2 kg.

Record the real totals in `docs/printing.md` (Task 13).

- [ ] **Step 7: Checkpoint**

Run: `cd ~/diy-window/tools && python3 -m unittest discover -p 'test_*.py'`
Expected: `OK`.

---

### Task 13: Printing, build and install guides

These are written docs, checked by reading them against the spec and the generated BOM. The three guides follow the order things actually happen: print, assemble on the bench, install into the wall.

**Files:**
- Create: `~/diy-window/docs/printing.md`
- Create: `~/diy-window/docs/build-guide.md`
- Create: `~/diy-window/docs/install-guide.md`

- [ ] **Step 1: Write `docs/printing.md`**

```markdown
# Printing

## Pick the material tier

Rule: heat-deflection temperature (HDT @ 0.45 MPa) at least 15 °C above the hottest surface temperature, and exterior parts UV-stable or painted. Melbourne design surface temperatures: about 50–55 °C on light colours, 75–80 °C on dark colours in full afternoon sun.

| Tier | Exposure | Min HDT | UV | Examples |
|---|---|---|---|---|
| 1 | South-facing / shaded, light colour | ≥ 70 °C | Stable or painted | PETG + exterior acrylic paint, ASA |
| 2 | East / part sun, light colour | ≥ 90 °C | Inherently stable | ASA |
| 3 | North / west full sun, or any dark colour | ≥ 105 °C | Inherently stable | ASA-CF, PC-ABS (painted) |

A dark colour moves any exposure up one tier. Set `tier` in your params file. `parts.csv` marks each part `exterior` (print in your tier's material) or `interior` (PETG in every tier).

## Settings (Bambu P1S)

- 0.4 mm nozzle (hardened steel for CF filaments), 0.2 mm layers.
- 5 walls, 5 top and 5 bottom layers, 15% gyroid infill. Most profile walls are 2.5 mm, so they print solid anyway.
- ASA and PC-ABS: enclosure closed, door shut, no auxiliary fan, textured PEI plate with glue stick.
- Heat-set inserts: 230 °C iron, pressed flush.

## Orientation

| Parts | Orientation |
|---|---|
| Segments (H, S, SW, JL, JU, T, TE, SH, SB, SBE, SV, NH, NV), TC | Standing on an end face, exactly as exported. No supports. |
| Corners (CH, CSL, CSR, CS, CN), JN, TSL, TSR | As exported. Supports on build plate only, for the rebate overhangs. |
| Beads (B*), sill nose (NS), acrylic spacers (A*) | Laid flat on their longest face. |
| Setting blocks, weep caps, cam parts, hinge leaves, keepers | Flat side down. |

## Quantities

`cad/generated/parts.csv` lists every part and how many to print. For the 1800 × 1500 home window at plan time: 161 prints in 35 types, about 16.0 kg exterior filament plus 3.9 kg interior PETG (`bom/home-1800x1500.md` has the current figure). Print a test coupon (TC) and one segment of each profile first, and check fit before committing a full spool.
```

- [ ] **Step 2: Write `docs/build-guide.md`**

```markdown
# Build guide (bench assembly)

Everything is assembled flat on a bench, then carried to the opening as three units:
- the frame,
- the transom,
- the sash,

plus the loose glass. Part IDs are engraved on a hidden face of each part.

## 1. Prepare
1. Cut tubes to `cad/generated/cutlist.csv` with a hacksaw or drop saw. Deburr and wipe with isopropyl.
2. Press M4 heat-set inserts into every boss: H (screen hinges), TE (cam bases), SBE (keepers), CMB pivots, TC.
3. Lay 3 mm foam cord into both end grooves of every segment, corner, node and shoe.

## 2. Frame
1. Sill: thread the S and SW segments onto the sill tube, with the two SW (weep) segments at the ends. Fit corner CSL on the left end and CSR on the right end.
2. Jambs: on each jamb tube, thread the JL segments, then one JN node, then the JU segments. Push each jamb tube into its sill corner socket.
3. Head: thread the H segments onto the head tube, fit the two CH corners, and drop the head onto the jamb tubes.
4. Square the frame (equal diagonals within 2 mm). Clamp every joint closed so the cord compresses.
5. Drive one 8g × 25 tube screw through every segment's inside-face countersink, and one in each corner leg. Run a bead of MS polymer around the tube pocket at each joint, from inside, before closing it.

## 3. Transom
1. Thread T and TE segments onto the steel tube, with the two TE segments at the ends. Fit shoe TSL on the left end and TSR on the right end, and screw each shoe to the tube.
2. Fit the two cam bases (CMB) to the TE inserts, then the handles (CMH) with an M4 screw and penny washer on each pivot.
3. Do not fit the transom into the frame yet. It goes in after the frame is installed (install guide, step 6).

## 4. Sash
1. Assemble SH (top), SB + SBE (bottom, SBE at the ends) and SV (sides) on 20 × 20 tubes with four CS corners. Screw and seal the joints as for the frame.
2. Push EPDM bulb seal into the frame kerfs: the fin kerf (outer seal) and the inner-stop kerf (inner seal), on head, upper jambs and transom.
3. Glaze the sash: fit the outer wedge gasket into the sash stop kerf, then GF blocks on the bottom rail, then the glass, then the BSH and BSV beads with the inner wedge gasket.
4. Fit the keepers (KP) to the SBE inserts.
5. Screw the friction stays to the sash sides and to the upper jambs. Drill 3.2 mm pilots through the shell into the tube, using the stay as the template.

## 5. Screen
Assemble NH/NV rails with CN corners (alu10 tube in the long rails). Roll in the mesh with spline, stick magnetic strip into the screen's back channel, and fit the HS leaves. HG leaves go onto the head inserts; join them with M4 × 40 bolts and nylocs.

## 6. Acrylic sandwich (only if `glazing = acrylic`)
Assemble the spacer frame (A* bars + AC corners), fill the channels with silica gel, and bond both 4 mm sheets with butyl glazing tape. Peel the film off the inner faces only.
```

- [ ] **Step 3: Write `docs/install-guide.md`**

```markdown
# Install guide: brick veneer

Two people. Allow a dry day, with no rain forecast for 24 h.

1. **Remove the old window.** Unscrew the old frame from the timber reveal, cut the sealant to the brickwork, and lift it out. Keep the existing head flashing above the lintel intact.
2. **Measure.** Measure the opening width (reveal to reveal) and height (head to brick sill) at three points each and use the smallest. Put those numbers in your params file and regenerate. Only print after this measurement.
3. **Sill tray.** Lay butyl flashing tape across the opening floor: turned up 30 mm at the back (room side), running out over the brick sill, and turned up 100 mm at each end.
4. **Set the frame.** Stand the frame on plastic packers at each corner and under each jamb node. Centre it, and plumb and square it (diagonals within 2 mm). Tuck the head under the existing head flashing.
5. **Fix it.** Drive a 10g × 65 screw through every fixing hole into the reveal and studs, packing behind each one so the frame doesn't bow. Holes sit at each segment middle, both legs of every corner, and each node, which meets the spec rule of at most 400 mm apart and within 150 mm of each corner. Don't overtighten: the screws should hold, not crush.
6. **Fit the transom.** Lift the transom unit in from the room side, slide its shoe tongues down the node dovetails to the stop, and drive the four M4 × 30 lock screws along the seams.
7. **Glaze the fixed pane.** Fit outer wedge gasket into the stop kerfs, two GW wedge blocks at the quarter points on the sill floor and GF locators at the sides, then the glass, then the BFH/BFV beads (snap in from the room side) with inner wedge gasket.
8. **Hang the sash** on the friction stays, close it, and check both seals touch evenly. Adjust with the stay screws if needed.
9. **Seal outside.** Push backer rod into the gap between frame and brickwork, gun MS polymer over it, and tool it smooth. Clip on the sill nose (NS) and push in the weep caps (WC). Never seal over weep holes or the nose drip.
10. **Inside.** Fill the gap to the reveal with low-expansion foam, trim, and refit the architraves.
11. **Screen.** Screw the HG hinge leaves to the head inserts, hang the screen, and check the magnetic strip closes along all four sides.
12. **Cam locks.** With the sash closed, turn each lever 60° counter-clockwise. The sash should pull in about 3 mm, and the seals should compress evenly.
```

- [ ] **Step 4: Checkpoint**

Read the three guides against spec sections 4.3 (wall interface), 5 (screen) and 6 (materials). Every spec step must appear: sill tray, head flashing lap, packers, fixing spacing, backer rod + MS polymer, foam, never-seal-weeps, the material tier rule.

---

### Task 14: Bench prototype and verification (physical)

The physical tests from spec §10, run on the 600 × 600 bench window before any wall is opened. You run these; the plan only fixes the protocol and the pass criteria. Results go in `docs/test-log.md`.

**Files:**
- Create: `~/diy-window/docs/test-log.md`

- [ ] **Step 1: Write `docs/test-log.md`**

```markdown
# Test log

Bench window: params/bench-600.json (acrylic glazing, tier 1 PETG).
Mount it in a timber test box (opening 600 × 600, 70 mm deep), fixed exactly as in the install guide.

| # | Test | Method | Pass criterion | Date | Result | Notes |
|---|---|---|---|---|---|---|
| 1 | Fit | Assemble from the printed parts with no filing | Every joint closes, diagonals within 2 mm, sash closes on both seals | | | |
| 2 | Water | Garden hose, fan spray, 300 mm from the outside face, 15 min, sash closed and cammed | No water on the room side; water leaves through the weeps | | | |
| 3 | Air | Smoke pencil along both sash seal lines, every segment joint and the screen magnet line, with a fan blowing at the outside face | No visible smoke draw | | | |
| 4 | Heat/creep | TC coupon painted matt black, 80 °C under a heat lamp (thermocouple on the face) for 24 h, with an M4 screw torqued to 1.5 N·m in one insert | No visible distortion; screw still holds 1.5 N·m | | | |
| 5 | Sash load | Hang 2 × sash weight from the open sash's bottom rail for 1 h | No permanent set at the stays or the corners after unloading | | | |
| 6 | Cam | Close and cam 50 times | Same compression on cycle 50 as on cycle 1, no cracking at keeper post or flag | | | |
| 7 | Screen corners | Look for light at the screen's bottom corners (where its magnet strip leaves the transom) | No gap above 1 mm; if there is one, add foam pads and record where | | | |

Full-size build only after rows 1–6 pass. Order glass from cad/generated/glass.csv after the opening is measured (install guide step 2).
```

- [ ] **Step 2: Print and assemble the bench window**

Run: `cd ~/diy-window && python3 tools/generate.py params/bench-600.json && cad/box.sh render bench-600 && python3 bom/build_bom.py bench-600`
Expected: `37/37 parts ok`, then the BOM. Print the parts, buy the BOM items, then assemble with `docs/build-guide.md`.

- [ ] **Step 3: Run tests 1–7 and fill in the table**

Expected: a dated result in every row. Any failure goes back into the CAD as a dims change (most fixes are in `cad/dims.json`: gaps, kerf width, cam ramp), then regenerate, re-render, reprint the affected parts and retest that row.

- [ ] **Step 4: Checkpoint**

Rows 1–6 all pass before the home window is generated for printing.
