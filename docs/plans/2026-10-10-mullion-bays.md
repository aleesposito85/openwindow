# OpenWindow Mullions and Bays Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ] `) syntax for tracking.

**Goal:** Two optional params keys, `max_pane` (the largest glass sheet) and `bays` (an upward override), split a window into the fewest equal bays that make every pane fit. The bays are divided by true mullions with dovetail tees, and each bay has its own fixed pane, awning sash and screen.

**Architecture:**
- **Generator.** `tools/window.py` finds the bay count and lays out:
  - one run per bay in the sill, head and transom, with a node between runs;
  - a lower and an upper mullion per bay boundary, each on its own 40 × 20 steel tube;
  - per-bay sashes and screens.

  It also adds two checks, `pane_fit` and `mullion_deflection`, and checks the transom with the mullion loads on it. `tools/generate.py` and `bom/build_bom.py` scale the parts and the hardware per bay and per run.
- **CAD.**
  - Two profiles, `mullion_glazing` and `mullion_sash`, in `cad/profile.scad`.
  - Three nodes: `SN` (sill), `HN` (head) and `TX` (transom).
  - Three shoes: `MSL`, `MST` and `MSH`.
  - The nodes and shoes follow the jamb-node / transom-shoe pattern: the nodes are plain bodies with dovetail slots, and the shoes carry every seal, kerf, magnet-channel and fin turn.
  - Every rule is an OpenSCAD assert, written before the geometry.
- **Web.** The configurator gets a "Glass sheet and bays" fieldset, a mullion-aware front view and assembled view, and two new badges.
- **Compatibility.** With neither key in the params, every output is byte-identical, apart from three new lines in the `dims.scad` mirror (see Decisions).

**Tech Stack:**
- Python 3 standard library only (`unittest`, `json`, `math`), using the Mac's `python3` (3.14 when this plan was written).
- OpenSCAD on the Windows box through `cad/box.sh` (nightly 2026.10.02, manifold backend).
- Plain HTML/CSS/ES-module JavaScript.
- Node, already on the Mac, for `web/tests/viewer_test.mjs`.
- The Mac's Google Chrome, headless, for screenshots and the guide PDF.

**Spec:** `docs/specs/2026-10-10-mullion-bays-design.md`. Background: `docs/specs/2026-10-07-diy-window-design.md` (§12 amendments win) and `docs/specs/2026-10-10-web-configurator-design.md`.

---

## Execution status (2026-10-10)

- **Done in `~/diy-window`.** All 15 tasks done via subagents; review fixes went beyond the plan's code (lock holes at `LOCK_U`; docs corrections), so `cad/`, `tools/`, `bom/`, `web/` and `docs/` are authoritative over the plan's code blocks.
- **Final checks (Task 14, 2026-10-10):** 279 tests pass in `tools/`, 147 in `web/tests`, `cad/box.sh test` reports `8 test files passed`, and the references render `37/37` (bench-600), `35/35` (home-1800x1500) and `43/43` (home-1800x1500-2bay) parts ok. The compatibility check prints `BYTE-IDENTICAL`. The BOMs have 38, 36 and 37 lines, and the deck check reports `overflow: none`.
- **Before execution,** every task below was run once, in order, on a scratch copy of the repo while the plan was written (stdlib Python, the real Windows box through the copy's `cad/box.sh`, the Mac's Chrome):
  - **Python:** 279 tests pass in `tools/` (213 before), and 147 pass in `web/tests` (123 before).
  - **OpenSCAD:** `cad/box.sh test` reports `8 test files passed`.
  - **Compatibility:** the check prints `BYTE-IDENTICAL`.
  - **Renders:**
    - The full render of `params/home-1800x1500-2bay.json` gives `43/43 parts ok`.
    - Re-rendering the home window's JN, TSL, TSR, H, T, TE, JU, CH and SBE gives byte-identical STLs.
  - **By eye:**
    - the PNGs of every new part, the section views (Task 9) and the UI screenshots (Task 12);
    - the new guide slide, with a 75-page PDF.
- The numbers quoted in the expected outputs come from that run. The run applied every Create, Replace and Append block of this plan literally, with a small script.
- **Not run while planning:** the hand checks in Task 12 Step 6, which need a person at a live page. The physical bench tests are also out of this plan's scope.

## Decisions and spec gaps (found while planning)

| Spec says, or leaves open | Plan does | Why |
|---|---|---|
| §4.1: mullion centres at `FRAME_W + i·pitch` | Centres at `FRAME_W − MULLION_W/2 + i·pitch` (892 mm for the 2-bay home window) | The spec formula puts the 2-bay mullion at 927 mm, 35 mm off centre, which breaks its own rule that end and inner bays have the same daylight. With the corrected formula, every bay is `pitch − MULLION_W` = 799 mm (unit test with 3 bays) |
| §4.1: `MULLION_W` and `MULLION_HALF_BODY` are new `dims.json` keys; §7: generator outputs byte-identical | Adds them, plus `MULLION_DOVE_D`. `cad/generated/dims.scad` mirrors every `dims.json` key, so it gains exactly these three lines. Everything else (stdout, `layout.scad`, part wrappers, CSVs, BOM) is byte-identical | The OpenSCAD parts need the values, so they can't be left out of `dims.scad` the way `BED_MARGIN` was. The compatibility check allows exactly those three added lines and nothing else |
| §5: `transom_deflection` span = the largest bay, "since the transom is propped at each mullion" | Checks the transom over its full span. The UDL acts on the two end half-bays, and each mullion's reaction is a point load: one bay's width × the same tributary height. One bay is unchanged (6.2 mm). The 2-bay home window gives 6.8 mm against 9.5 mm | The lower and upper mullions meet the TX through dovetails, which carry no moment. So the two stubs are pinned at the TX and can't prop it: the TX moves with the transom. The spec's model would report 0.3 mm. That understates the glass-edge movement at the TX by about 20 times. If you want the spec's model instead, use `deflection(TRANSOM_CORE, run, trib)` with the limit `run / 175` in the transom check (Task 2, Step 4) |
| §5: `pane_fit` "reports ok with 'no limit' when `max_pane` is absent"; §7 and the web tests: unchanged checks | `pane_fit` and `mullion_deflection` are only in the checks when the params have `max_pane` or `bays`. With `bays` alone, `pane_fit` says "no max_pane limit" | With no keys, the CLI output and the web check list stay identical (`testChecksEndWithBedFit`, `MainTest`). The page sends `max_pane` unless No limit is ticked, so the badge is there whenever a limit is set |
| §4.3: dovetail tees "following the jamb node" | One mullion dovetail in SN, HN and TX: 4 mm deep (`MULLION_DOVE_D`), flanks at the jamb node's angle (flare 2 mm), lock screws at `u = LOCK_U` (3 mm into the node, like the jamb node) | The transom body is 34 mm wide around a 20.6 mm tube pocket. The jamb node's 6 mm dovetail would leave 0.7 mm to the steel. 4 mm leaves 2.7 mm (asserted ≥ `CHAMBER_WALL`). Using one depth everywhere lets one `MSL` part serve the sill end and the transom end |
| §4.3: each feature "must turn the corner the way the transom shoe already does" | The shoes carry the turns, and the nodes stay plain bodies like `JN`. `MSL` turns the glazing kerf on both sides. `MST` adds the fin stubs and the fin and inner-stop kerf turns. `MSH` does the same as `MST`, plus the head magnet-channel turns. `TX` carries the vertical magnet channels from the transom channel up to `MST` | This is the existing pattern, and the asserts are their shoe-turn equivalents. The sill and transom glazing kerfs sit at the same depth from their node faces, and the head and transom seal kerfs too (both asserted). So one lower shoe and two upper shoes are enough |
| §4.2: `mullion_sash` screen magnet channel "mirrored about the centreline" | Each side's channel sits like the jamb's: 2–15 mm in from its body face, so at 3–16 and 54–67 mm across the 70 mm profile | The transom's channel position (`TRANSOM_MAG_X`, 20–33), mirrored, would put the two screens on top of each other. With the jamb position each screen overlaps the mullion by `SCREEN_OVERLAP`, and the two screens are 14 mm apart |
| §4.4: a stay pair per sash | Stay tracks on a mullion get "Tek screw 8g × 16 (friction-stay tracks to upper mullions)" | The mullion tube is steel. The two stays either side of a mullion screw into the same tube. 8g × 25 screws would meet inside it, and 16 mm ones are 2 mm apart (asserted) |
| §3, §4.1: `bays` ≥ automatic; "at every bay count" | Also caps `bays` at the most that keeps every bay at least 150 mm wide (`MIN_BAY`, like `MIN_FIXED`/`MIN_AWNING`). "At every bay count" means up to that cap. A sash pane that is too tall suggests a shorter `awning_h` | Without a cap, "every bay count" has no end. A taller awning only helps when the fixed pane is too tall |
| §4.3: `TX` carries cam bosses only if a sash end needs them | `TX` never carries them | Each bay's transom run has its own `TE` ends, and those take the cams (`testEveryBayHasItsCamsOverItsKeepers`) |
| §6: BOM scales per bay | Also: a packer under each `SN`; 3 mm cord for the four shoe seams per mullion; M4 × 16 lock screws = 2 per transom or mullion shoe; a "Bays" note in `bom/<name>.md` with the mullion centre lines | The build guide needs those positions to set the nodes |
| §8.4: section views by eye | `cad/assembly.scad` gains `cut_x`, `plan_z` and `cut_t` options, and colours each part group separately in a cut | The old section view lost every colour in the `intersection()`, so the new parts couldn't be told apart |
| §6: "The guide PDF is regenerated" | Adds one sizing slide built from the 2-bay window's BOM (Task 13). The other slides still describe the one-bay home window | The deck builder reads `docs/user-manual.md` and `docs/test-log.md` and checks their structure, so those edits stay within its sections |
| Not covered | Test-log row 8 (mullion tees: water and smoke) | The tees are new weather joints, and the bench window has one bay |

## Ground rules for whoever executes this

- **No git.** The user's rule: no git under `~` except one work repo. Every "commit" in the usual TDD loop is a **Checkpoint** step here. Run the listed checks, and stop for review if any of them fails.
- **No installs on the Mac.** Python 3 standard library only, and plain JavaScript. Nothing gets downloaded.
- **Network.** Every ssh/scp to the Windows box goes through `cad/box.sh`, which binds en0. It is safe to run several `box.sh` commands at once: each uses its own remote folder, and they share a generate lock.
- **No explanatory comments in code** beyond a one-line header (module docstring, or a `//` first line). The reasons live in this plan.
- **Test method names** are camelCase `testXxx`, with no underscores.
- **Existing tests stay unchanged.** New test classes are only appended. With no new params keys, the outputs stay byte-identical (the compatibility check, Task 0).
- **Working folder.** Run every command from `~/diy-window`, unless a step says otherwise.
  - Task 0 creates `.bays-baseline/`.
  - The checkpoints create `.bays-after/`.
  - The review PNGs go to `.bays-review/`.
  - Task 14 deletes all three.
- **Applying blocks.**
  - **Create** means write the file with exactly the block's content.
  - **Append to `X`**: if `X` has an `if __name__ == "__main__":` line, insert the block before it, with two blank lines on each side. Otherwise add the block at the end of `X`, after one blank line.
  - **Replace in `X`** means the first block occurs exactly once in `X`. Replace it with the second block.
  - **Replace from `L` to the end of `X`** means: replace everything from the line `L` to the end of `X` with the block.
- **Reviews (spec §8.7).** Stop for a review after Task 3 (generator), Task 9 (the CAD tees, with the section PNGs), and Task 14 (docs, BOM and code consistency).

## File structure

```
~/diy-window/
  cad/dims.json                      + MULLION_W 70, MULLION_HALF_BODY 17, MULLION_DOVE_D 4
  params/home-1800x1500-2bay.json    NEW reference window: the home opening + "max_pane": [1200, 900]
  tools/window.py                    bay count, per-bay layout, runs, mullion members and tubes, pane_fit, mullion_deflection, transom with mullion loads
  tools/generate.py                  parts per run and per bay, SN/HN/TX/MSL/MST/MSH/ML/MU, BAYS/PITCH/MULLIONS in layout.scad, glass qty
  tools/part_envelopes.py, .json     the 2-bay window joins the references; envelopes for the new parts
  bom/build_bom.py                   hardware per bay, mullion lines, "Bays" note in the .md
  cad/profile.scad                   mullion_glazing and mullion_sash profiles (is_mullion, both_sides, mag_rects)
  cad/lib/segment.scad               label positions for the mullion profiles
  cad/lib/mullion.scad               NEW mullion dovetail and lock helpers
  cad/parts/jamb_node.scad           dovetail and lock functions take depth/flare/offset (defaults unchanged)
  cad/parts/frame_node.scad          NEW SN and HN
  cad/parts/cross_node.scad          NEW TX
  cad/parts/mullion_shoe.scad        NEW MSL, MST, MSH
  cad/tests/mullion_test.scad        NEW asserts: profiles, nodes, shoes
  cad/tests/mullion_sheet.scad       NEW view: the two mullion profiles beside the transom
  cad/assembly.scad                  bays, mullions, per-bay sashes and panes; cut_x / plan_z / cut_t sections with colours
  tools/test_window.py, test_generate.py, test_bom.py, test_part_envelopes.py   new test classes appended
  web/drawing.py, api.py, server.py  mullions and per-bay rects/labels/instances; max_pane/bays validation; presets carry the page sheet size
  web/static/index.html, app.js, style.css, viewer.js   "Glass sheet and bays" fieldset, badges, viewer colours
  web/tests/test_drawing.py, test_api.py, test_server.py   new test classes appended; ui_shots.py gains three shots
  docs/build-guide.md, install-guide.md, printing.md, user-manual.md, test-log.md, README.md, web/README.md, specs   bay notes
  pdf/build_deck.py                  one sizing slide for bays; the PDF is rebuilt
  docs/img/assembly-home-2bay.png    NEW render for the README and the deck
```

---

### Task 0: Baseline of today's outputs

The compatibility rule: with no `max_pane` or `bays` key, every file `generate.py` and `build_bom.py` write, and everything they print, stays byte-identical. The one exception is the three new `dims.scad` lines. This task records today's output once.

**Files:**
- Create: `.bays-baseline/` (temporary, deleted in Task 14)

- [ ] **Step 1: Confirm the starting point**

Run:
```bash
cd ~/diy-window/tools && python3 -m unittest discover -p 'test_*.py' 2>&1 | grep -E '^(Ran|OK|FAILED)'
cd ~/diy-window && python3 -m unittest discover -s web/tests -p 'test_*.py' 2>&1 | grep -E '^(Ran|OK|FAILED)'
cd ~/diy-window && cad/box.sh test
```
Expected: `Ran 213 tests`, `OK`; then `Ran 123 tests` (about 47 s), `OK`; then `7 test files passed`.

- [ ] **Step 2: Record the baseline**

Run:
```bash
cd ~/diy-window && rm -rf .bays-baseline && mkdir .bays-baseline
for n in bench-600 home-1800x1500; do
  python3 tools/generate.py params/$n.json > .bays-baseline/$n.stdout
  python3 bom/build_bom.py $n >> .bays-baseline/$n.stdout
  mkdir .bays-baseline/$n && cp -R cad/generated .bays-baseline/$n/
  for f in $n.csv $n.md $n-cutlist.csv $n-glass.csv $n-parts.csv; do cp bom/$f .bays-baseline/$n/; done
done
ls .bays-baseline/bench-600
```
Expected: `bench-600-cutlist.csv  bench-600-glass.csv  bench-600-parts.csv  bench-600.csv  bench-600.md  generated`

The **compatibility check** used by later checkpoints re-runs the same commands into `.bays-after/` and compares:
```bash
cd ~/diy-window && rm -rf .bays-after && mkdir .bays-after
for n in bench-600 home-1800x1500; do
  python3 tools/generate.py params/$n.json > .bays-after/$n.stdout
  python3 bom/build_bom.py $n >> .bays-after/$n.stdout
  mkdir .bays-after/$n && cp -R cad/generated .bays-after/$n/
  for f in $n.csv $n.md $n-cutlist.csv $n-glass.csv $n-parts.csv; do cp bom/$f .bays-after/$n/; done
done
ok=1
diff -r -x dims.scad .bays-baseline .bays-after || ok=0
for n in bench-600 home-1800x1500; do
  extra=$(diff .bays-baseline/$n/generated/dims.scad .bays-after/$n/generated/dims.scad | grep '^[<>]' | grep -v -E '^> (MULLION_W|MULLION_HALF_BODY|MULLION_DOVE_D) = ')
  [ -n "$extra" ] && { echo "$extra"; ok=0; }
done
[ $ok = 1 ] && echo BYTE-IDENTICAL || echo DIFFERENT
```
Expected, from Task 1 on: `BYTE-IDENTICAL`, with no other output. (`diff .bays-baseline/home-1800x1500/generated/dims.scad .bays-after/home-1800x1500/generated/dims.scad` shows only `> MULLION_W = 70.0;`, `> MULLION_HALF_BODY = 17.0;` and `> MULLION_DOVE_D = 4.0;`.)

---
### Task 1: Bay count and per-bay layout (`cad/dims.json`, `params/`, `tools/window.py`)

`layout()` finds the bay count and the bay geometry:
- **Bay count.** With `max_pane`, it is the fewest bays (up to the most that keep every bay at least `MIN_BAY` = 150 mm wide) at which both panes fit the sheet in some rotation. `bays` can raise it.
- **Runs.** The sill, head and transom become one run per bay, so these members carry `length` = the bay daylight and `qty` = the number of bays. The mullions get their own members and tubes.
- **Unchanged.** With one bay, every number is the old one: the end-bay formulas are only used from two bays up. The checks are not touched here (Task 2).

Numbers for the 2-bay home window (1800 × 1500, `max_pane` 1200 × 900):

| Quantity | Value |
|---|---|
| Pitch | (1668 + 70) / 2 = 869 |
| Mullion centre | 58 − 35 + 869 = 892, the middle of the 1784 mm frame |
| Bay daylight | 799 |
| Fixed pane | 892 − 20 − 43 = 829 × 878 |
| Sash | 875 − 40 − 26 = 809 × 460, glass 737 × 388 |
| Screen | 855 × 540 |

With 900 × 600 the 878 mm pane height only fits along the 900 side. That makes the width at most 600, so 3 bays (539 × 878).

**Files:**
- Modify: `cad/dims.json` (end)
- Create: `params/home-1800x1500-2bay.json`
- Modify: `tools/window.py` (constants, new helpers before `member()`, `layout()`)
- Test: `tools/test_window.py` (append `two_bay`, `BayCountTest`, `BayLayoutTest`)

- [ ] **Step 1: Write the failing tests**

**Append** to `tools/test_window.py`:
```python
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
```

- [ ] **Step 2: Run them to see them fail**

Run: `cd ~/diy-window/tools && python3 -m unittest test_window.BayCountTest test_window.BayLayoutTest 2>&1 | tail -3`
Expected: `FAILED (failures=6, errors=17)`:
- every `BayLayoutTest` test errors with `FileNotFoundError: ... params/home-1800x1500-2bay.json`;
- the `BayCountTest` tests fail with `KeyError: 'bays'`, `AttributeError: module 'window' has no attribute 'max_bays'` or `'fits'`, or `ValueError not raised`.

- [ ] **Step 3: Add the reference window and the mullion dims**

**Create** `params/home-1800x1500-2bay.json`:
```json
{
  "name": "home-1800x1500-2bay",
  "opening_w": 1800,
  "opening_h": 1500,
  "fix_gap": 8,
  "awning_h": 450,
  "glazing": "igu",
  "tier": 3,
  "max_pane": [1200, 900]
}
```

**Replace** in `cad/dims.json`:
```json
  "NOSE_PROJECTION": 15.0
}
```
**with:**
```json
  "NOSE_PROJECTION": 15.0,
  "MULLION_W": 70.0,
  "MULLION_HALF_BODY": 17.0,
  "MULLION_DOVE_D": 4.0
}
```

- [ ] **Step 4: Add the bay helpers to `tools/window.py`**

**Replace** in `tools/window.py`:
```python
DEFAULT_BED = [256, 256, 256]
WIDE_SCREEN = 1000.0
```
**with:**
```python
DEFAULT_BED = [256, 256, 256]
WIDE_SCREEN = 1000.0
MIN_BAY = 150.0
PANE_RANGE = (200, 3000)
```

**Replace** in `tools/window.py`:
```python
CORD_PROFILES = {"sash_rebate", "sill", "glazing", "transom", "sash"}
```
**with:**
```python
CORD_PROFILES = {"sash_rebate", "sill", "glazing", "transom", "sash", "mullion_glazing", "mullion_sash"}
```

**Replace** in `tools/window.py`:
```python
def member(name, length, profile, core, qty, limit=None, min_n=1):
```
**with:**
```python
def bay_width(horiz, n):
    return (horiz - (n - 1) * D["MULLION_W"]) / n


def max_bays(horiz):
    n = 1
    while bay_width(horiz, n + 1) >= MIN_BAY:
        n += 1
    return n


def fits(pane, sheet):
    return all(a <= b for a, b in zip(sorted(pane), sorted(sheet)))


def bay_layout(p, horiz, panes_at):
    limit = p.get("max_pane")
    top = max_bays(horiz)
    auto = 1
    if "max_pane" in p:
        lo, hi = PANE_RANGE
        if not (isinstance(limit, (list, tuple)) and len(limit) == 2 and all(is_size(v) and lo <= v <= hi for v in limit)):
            raise ValueError(f"max_pane must be two sizes, {lo}-{hi} mm each, got {limit!r}")
        auto = next((n for n in range(1, top + 1) if all(fits(pane, limit) for pane in panes_at(n).values())), None)
        if auto is None:
            sheet = " x ".join(f"{v:g}" for v in limit)
            bad = {k: v for k, v in panes_at(top).items() if not fits(v, limit)}
            tall = [k for k, (pw, ph) in bad.items() if ph > min(limit)]
            if tall:
                fix = "use a taller awning_h or a shorter opening" if tall[0] == "fixed" else "use a shorter awning_h"
                raise ValueError(f"max_pane: the {bad[tall[0]][1]} mm tall {tall[0]} pane does not fit a {sheet} mm sheet "
                                 f"at any bay count; that needs a second horizontal transom, which is out of scope: {fix}")
            k, (pw, ph) = next(iter(bad.items()))
            raise ValueError(f"max_pane: at {top} bay{'s' if top > 1 else ''}, the most this opening takes "
                             f"({MIN_BAY:g} mm each at least), the {k} pane is still {pw} x {ph} mm, too big for a {sheet} mm sheet")
    n = p.get("bays", auto)
    if type(n) is not int or n < 1:
        raise ValueError(f"bays must be a whole number of at least 1, got {n!r}")
    if n < auto:
        raise ValueError(f"bays must be at least {auto} for a {' x '.join(f'{v:g}' for v in limit)} mm max_pane, got {n}")
    if n > top:
        raise ValueError(f"bays must be at most {top} for this opening (bays at least {MIN_BAY:g} mm wide), got {n}")
    pitch = (horiz + D["MULLION_W"]) / n
    mullions = [D["FRAME_W"] - D["MULLION_W"] / 2 + i * pitch for i in range(1, n)]
    return n, auto, pitch, mullions


def member(name, length, profile, core, qty, limit=None, min_n=1):
```

- [ ] **Step 5: Lay out the bays**

**Replace from** `def layout(p):` **to the end of** `tools/window.py` **with:**
```python
def layout(p):
    if p["glazing"] not in GLAZING_KG_M2:
        raise ValueError(f"glazing must be one of {sorted(GLAZING_KG_M2)}, got {p['glazing']}")
    bed = p.get("bed", DEFAULT_BED)
    seg_max = max_seg(bed)
    has_screen = p.get("screen", True)
    if not isinstance(has_screen, bool):
        raise ValueError(f"screen must be true or false, got {has_screen}")
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
    sash_h = (h - D["FRAME_BODY"]) - (transom_c + D["TRANSOM_HALF_BODY"]) - 2 * D["SASH_GAP"]
    fixed_gh = math.floor(transom_c - D["TRANSOM_GLASS"] - D["GLASS_EDGE"])
    sash_gh = math.floor(sash_h - 2 * D["SASH_GLASS"])

    def widths(n):
        if n == 1:
            return (w - 2 * D["FRAME_BODY"] - 2 * D["SASH_GAP"], w - 2 * D["FRAME_BODY"] + 2 * D["SCREEN_OVERLAP"],
                    w - 2 * D["GLASS_EDGE"], w - 2 * D["FRAME_BODY"])
        m1 = F - D["MULLION_W"] / 2 + (horiz + D["MULLION_W"]) / n
        opening = m1 - D["MULLION_HALF_BODY"] - D["FRAME_BODY"]
        return (opening - 2 * D["SASH_GAP"], opening + 2 * D["SCREEN_OVERLAP"],
                m1 - D["TRANSOM_GLASS"] - D["GLASS_EDGE"], opening)

    def panes_at(n):
        sw, _, fw, _ = widths(n)
        return {"fixed": (math.floor(fw), fixed_gh), "sash": (math.floor(sw - 2 * D["SASH_GLASS"]), sash_gh)}

    bays, auto_bays, pitch, mullions = bay_layout(p, horiz, panes_at)
    sash_w, screen_w, _, opening = widths(bays)
    run = bay_width(horiz, bays)
    screen_h = (h - D["FRAME_BODY"] + D["SCREEN_OVERLAP"]) - (transom_c - T / 2 + D["TRANSOM_MAG_X"] - D["SCREEN_OVERLAP"] - 2)
    screen_core = lambda length: "alu10" if split(length, 0.0, seg_max)[0] > 1 else None
    hinges = hinge_count(screen_w) if has_screen else 0

    members = [
        member("head", run, "sash_rebate", FRAME_CORE, bays, seg_max, max(1, hinges)),
        member("sill", run, "sill", FRAME_CORE, bays, seg_max),
        member("jamb_lower", lower, "glazing", FRAME_CORE, 2, seg_max),
        member("jamb_upper", a, "sash_rebate", FRAME_CORE, 2, seg_max),
        member("transom", run, "transom", TRANSOM_CORE, bays, seg_max, 2),
    ]
    if bays > 1:
        members += [
            member("mullion_lower", lower, "mullion_glazing", TRANSOM_CORE, bays - 1, seg_max),
            member("mullion_upper", a, "mullion_sash", TRANSOM_CORE, bays - 1, seg_max),
        ]
    members += [
        member("sash_horizontal", sash_w - 2 * S, "sash", "alu20", 2 * bays, seg_max),
        member("sash_vertical", sash_h - 2 * S, "sash", "alu20", 2 * bays, seg_max),
    ]
    if has_screen:
        members += [
            member("screen_horizontal", screen_w - 2 * N, "screen", screen_core(screen_w - 2 * N), 2 * bays, seg_max),
            member("screen_vertical", screen_h - 2 * N, "screen", screen_core(screen_h - 2 * N), 2 * bays, seg_max),
        ]

    clear = D["TUBE_END_CLEAR"]
    sock, sash_sock, screen_sock = (D[k] - clear for k in ("SOCKET_FRAME", "SOCKET_SASH", "SOCKET_SCREEN"))
    shoe_sock = (F - D["FRAME_BODY"]) + (D["MULLION_W"] / 2 - D["MULLION_HALF_BODY"]) - 2 * (D["SHOE_WALL"] + 1)
    tubes = [
        {"member": "head", "core": FRAME_CORE, "length": horiz + 2 * sock, "qty": 1},
        {"member": "sill", "core": FRAME_CORE, "length": horiz + 2 * sock, "qty": 1},
        {"member": "jamb", "core": FRAME_CORE, "length": h - 2 * F + 2 * sock, "qty": 2},
        {"member": "transom", "core": TRANSOM_CORE,
         "length": horiz + 2 * (F - D["FRAME_BODY"]) - 2 * (D["SHOE_WALL"] + 1), "qty": 1},
    ]
    if bays > 1:
        tubes += [
            {"member": "mullion_lower", "core": TRANSOM_CORE, "length": lower + shoe_sock, "qty": bays - 1},
            {"member": "mullion_upper", "core": TRANSOM_CORE, "length": a + shoe_sock, "qty": bays - 1},
        ]
    tubes += [
        {"member": "sash_horizontal", "core": "alu20", "length": sash_w - 2 * S + 2 * sash_sock, "qty": 2 * bays},
        {"member": "sash_vertical", "core": "alu20", "length": sash_h - 2 * S + 2 * sash_sock, "qty": 2 * bays},
    ]
    for m in members:
        if m["name"].startswith("screen") and m["core"]:
            tubes.append({"member": m["name"], "core": m["core"], "length": m["length"] + 2 * screen_sock,
                          "qty": m["qty"]})
    for t in tubes:
        t["length"] = round(t["length"], 1)

    glass = panes_at(bays)

    checks = []
    trib = (lower + a) / 2
    delta = deflection(TRANSOM_CORE, horiz, trib)
    limit = horiz / 175
    checks.append({"name": "transom_deflection", "ok": delta <= limit,
                   "msg": f"transom deflects {delta:.1f} mm at {WIND_KPA} kPa, limit span/175 = {limit:.1f} mm"})

    gw, gh = glass["sash"]
    sash_kg = gw * gh / 1e6 * GLAZING_KG_M2[p["glazing"]] + 2 * (sash_w + sash_h) / 1000 * SASH_FRAME_KG_M
    candidates = [s for s in STAYS if STAY_RATIO * sash_h <= s[0] <= sash_h]
    stay = next((s for s in candidates if s[1] >= sash_kg), None)
    stay_ok = stay is not None
    if stay_ok:
        msg = f"sash {sash_kg:.1f} kg, stay pair {stay[0]} mm rated {stay[1]} kg"
    else:
        msg = (f"sash {sash_kg:.1f} kg, no stay pair in {STAY_RATIO * sash_h:.0f}-{sash_h:.0f} mm "
               f"range rated for it")
    checks.append({"name": "sash_weight", "ok": stay_ok, "msg": msg})

    too_long = [m["name"] for m in members if m["seg"] > seg_max]
    checks.append({"name": "segment_length", "ok": not too_long, "msg": f"segments over bed: {too_long}"})

    by_name = {m["name"]: m for m in members}
    cam_at = F + D["JOINT_GAP"] + by_name["transom"]["seg"] / 2
    keeper_at = D["FRAME_BODY"] + D["SASH_GAP"] + S + D["JOINT_GAP"] + by_name["sash_horizontal"]["seg"] / 2
    keeper_dz = round(abs(keeper_at - cam_at), 2)
    lo, hi = keeper_dz_min(), keeper_dz_max(by_name["sash_horizontal"]["seg"])
    checks.append({"name": "cam_keeper", "ok": by_name["transom"]["n"] >= 2 and lo <= keeper_dz <= hi,
                   "msg": f"keeper bosses {keeper_dz:.2f} mm either side of the SBE middle, over the cams "
                          f"(allowed {lo:.1f}-{hi:.1f} mm, transom needs 2+ segments)"})

    return {"params": p, "w": w, "h": h, "transom_c": transom_c, "members": members,
            "tubes": tubes, "glass": glass, "sash": (sash_w, sash_h), "screen": (screen_w, screen_h),
            "sash_kg": round(sash_kg, 1), "stay": stay[0] if stay else None, "keeper_dz": keeper_dz,
            "bed": list(bed), "max_seg": seg_max, "has_screen": has_screen, "hinges": hinges,
            "bays": bays, "auto_bays": auto_bays, "pitch": pitch, "mullions": mullions, "bay_w": run, "opening": opening,
            "checks": checks}
```

The one-bay branch of `widths()` keeps today's expressions exactly, so floats round the same for any `fix_gap`. The cam/keeper offset only needs the first run and the first sash: every run and every sash is the same, and the gap between a run's end and its sash's edge is 5 mm at a jamb and at a mullion (58 − 53 = 35 − 30).

- [ ] **Step 6: Run the tests to see them pass**

Run: `cd ~/diy-window/tools && python3 -m unittest test_window 2>&1 | tail -3`
Expected: `OK` (97 tests).

- [ ] **Step 7: Checkpoint**

Run: `cd ~/diy-window/tools && python3 -m unittest discover -p 'test_*.py' 2>&1 | grep -E '^(Ran|OK|FAILED)'`
Expected: `Ran 237 tests`, `OK`.

Then run the **compatibility check** (Task 0). Expected: `BYTE-IDENTICAL`.

---

### Task 2: Checks per bay (`tools/window.py`)

The two new checks are only reported when the params have `max_pane` or `bays`, so the four existing check lines stay as they are:
- `pane_fit`: always ok, because a window whose panes can't fit raises instead;
- `mullion_deflection`: the worse of the two stubs, simply supported, with one bay pitch of tributary width at 0.7 kPa, limit span/175.

`transom_deflection`, from two bays up:
- the transom stays a full-span steel beam;
- the uniform load only acts on its two end half-bays, and each mullion strip's load arrives as a point load at the TX (see Decisions);
- the load is summed by superposing point loads (the end strips as 50 slices each), and the result is the largest deflection over 101 stations.

The `sash_weight` and `cam_keeper` lines get an ", each of n sashes" note.

**Files:**
- Modify: `tools/window.py` (new `beam_deflection`, `strip_loads`; the checks in `layout()`)
- Test: `tools/test_window.py` (append `checks_by_name`, `BayChecksTest`)

- [ ] **Step 1: Write the failing tests**

**Append** to `tools/test_window.py`:
```python
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
```

- [ ] **Step 2: Run them to see them fail**

Run: `cd ~/diy-window/tools && python3 -m unittest test_window.BayChecksTest 2>&1 | tail -3`
Expected: `FAILED (failures=3, errors=4)`:
- the errors are `KeyError: 'pane_fit'`, `KeyError: 'mullion_deflection'` and `AttributeError: module 'window' has no attribute 'beam_deflection'`;
- the failures are the check-name list, the transom message (`transom deflects 6.2 mm`) and the sash message (no `each of 2 sashes`);
- `testNoBayKeysKeepTheFourChecks` and `testAllChecksPassForTheTwoBayHome` already pass.

- [ ] **Step 3: Add the beam helpers**

**Replace** in `tools/window.py`:
```python
def bay_layout(p, horiz, panes_at):
```
**with:**
```python
def beam_deflection(core, span, loads):
    ei = CORES[core][0] * inertia(core)

    def at(x):
        d = 0.0
        for a, f in loads:
            b = span - a
            d += f * b * x * (span ** 2 - b ** 2 - x ** 2) if x <= a else f * a * (span - x) * (span ** 2 - a ** 2 - (span - x) ** 2)
        return d / (6 * span * ei)

    return max(at(span * k / 100) for k in range(101))


def strip_loads(x0, x1, w, parts=50):
    step = (x1 - x0) / parts
    return [(x0 + (k + 0.5) * step, w * step) for k in range(parts)]


def bay_layout(p, horiz, panes_at):
```

- [ ] **Step 4: Check the transom with the mullion loads**

**Replace** in `tools/window.py`:
```python
    glass = panes_at(bays)

    checks = []
    trib = (lower + a) / 2
    delta = deflection(TRANSOM_CORE, horiz, trib)
    limit = horiz / 175
    checks.append({"name": "transom_deflection", "ok": delta <= limit,
                   "msg": f"transom deflects {delta:.1f} mm at {WIND_KPA} kPa, limit span/175 = {limit:.1f} mm"})
```
**with:**
```python
    glass = panes_at(bays)
    each = f", each of {bays} sashes" if bays > 1 else ""

    checks = []
    trib = (lower + a) / 2
    limit = horiz / 175
    if bays == 1:
        delta = deflection(TRANSOM_CORE, horiz, trib)
        loads_msg = ""
    else:
        w_t = WIND_KPA / 1000.0 * trib
        half = run / 2
        loads = strip_loads(0.0, half, w_t) + strip_loads(horiz - half, horiz, w_t)
        loads += [(c - F, WIND_KPA / 1000.0 * pitch * trib) for c in mullions]
        delta = beam_deflection(TRANSOM_CORE, horiz, loads)
        loads_msg = f" carrying {bays - 1} mullion{'s' if bays > 2 else ''}"
    checks.append({"name": "transom_deflection", "ok": delta <= limit,
                   "msg": f"transom deflects {delta:.1f} mm at {WIND_KPA} kPa{loads_msg}, limit span/175 = {limit:.1f} mm"})
```

- [ ] **Step 5: Note the sash count, and add `pane_fit` and `mullion_deflection`**

**Replace** in `tools/window.py`:
```python
    if stay_ok:
        msg = f"sash {sash_kg:.1f} kg, stay pair {stay[0]} mm rated {stay[1]} kg"
    else:
        msg = (f"sash {sash_kg:.1f} kg, no stay pair in {STAY_RATIO * sash_h:.0f}-{sash_h:.0f} mm "
               f"range rated for it")
```
**with:**
```python
    if stay_ok:
        msg = f"sash {sash_kg:.1f} kg, stay pair {stay[0]} mm rated {stay[1]} kg{each}"
    else:
        msg = (f"sash {sash_kg:.1f} kg, no stay pair in {STAY_RATIO * sash_h:.0f}-{sash_h:.0f} mm "
               f"range rated for it{each}")
```

**Replace** in `tools/window.py`:
```python
                          f"(allowed {lo:.1f}-{hi:.1f} mm, transom needs 2+ segments)"})
```
**with:**
```python
                          f"(allowed {lo:.1f}-{hi:.1f} mm, transom needs 2+ segments{' per bay' if bays > 1 else ''}){each}"})

    if "max_pane" in p or "bays" in p:
        limit_pane = p.get("max_pane")
        if limit_pane is None:
            msg = f"{bays} bay{'s' if bays > 1 else ''}, no max_pane limit"
        else:
            sheet = " x ".join(f"{v:g}" for v in limit_pane)
            chosen = f"{bays} bays ({auto_bays} needed)" if bays > auto_bays else f"{bays} bay{'s' if bays > 1 else ''}"
            msg = (f"{chosen}: fixed panes {glass['fixed'][0]} x {glass['fixed'][1]}, sash panes "
                   f"{glass['sash'][0]} x {glass['sash'][1]} fit a {sheet} mm sheet")
        checks.append({"name": "pane_fit", "ok": True, "msg": msg})
        if bays == 1:
            checks.append({"name": "mullion_deflection", "ok": True, "msg": "1 bay, no mullions"})
        else:
            stubs = [(name, span, deflection(TRANSOM_CORE, span, pitch)) for name, span in (("lower", lower), ("upper", a))]
            name, span, d = max(stubs, key=lambda s: s[2] / s[1])
            checks.append({"name": "mullion_deflection", "ok": all(d_ <= s_ / 175 for _, s_, d_ in stubs),
                           "msg": f"{name} mullion deflects {d:.1f} mm at {WIND_KPA} kPa over {span:g} mm, "
                                  f"limit span/175 = {span / 175:.1f} mm"})
```

- [ ] **Step 6: Run the tests to see them pass**

Run: `cd ~/diy-window/tools && python3 -m unittest test_window 2>&1 | tail -3`
Expected: `OK` (106 tests).

- [ ] **Step 7: Checkpoint**

Run: `cd ~/diy-window/tools && python3 -m unittest discover -p 'test_*.py' 2>&1 | grep -E '^(Ran|OK|FAILED)'`
Expected: `Ran 246 tests`, `OK`.

Then print the checks for the 2-bay window. Don't use `generate.py` yet: its part list only learns about bays in Task 3.
```bash
cd ~/diy-window/tools && python3 -c "
import json, window
for c in window.layout(json.load(open('../params/home-1800x1500-2bay.json')))['checks']: print(c['ok'], c['msg'])"
```
Expected:
```
True transom deflects 6.8 mm at 0.7 kPa carrying 1 mullion, limit span/175 = 9.5 mm
True sash 7.6 kg, stay pair 400 mm rated 30.0 kg, each of 2 sashes
True segments over bed: []
True keeper bosses 63.92 mm either side of the SBE middle, over the cams (allowed 20.6-96.9 mm, transom needs 2+ segments per bay), each of 2 sashes
True 2 bays: fixed panes 829 x 878, sash panes 737 x 388 fit a 1200 x 900 mm sheet
True lower mullion deflects 0.6 mm at 0.7 kPa over 848 mm, limit span/175 = 4.8 mm
```

Then run the **compatibility check** (Task 0). Expected: `BYTE-IDENTICAL`.

---
### Task 3: Parts per run and per bay (`tools/generate.py`)

**Part counts.**
- Every run gets its own end segments: `SW` (weeps) and `TE` (weeps and cam bosses) at both ends of every run.
- Every bay gets its own sash, screen, corners, cams, keepers, hinges, setting blocks, weep caps, beads and acrylic spacers.
- Every mullion adds `SN`, `HN`, `TX`, two `MSL`, `MST`, `MSH`, the `ML` segments and the `MU` segments. The `ML` and `MU` segments come from the new members, through `frame_segment` with the new profiles (Task 4).
- The sill nose still runs the full width.

**Generated files.**
- `layout.scad` gains `BAYS`, `PITCH` and `MULLIONS` lines, only from two bays up.
- `glass.csv` gives a quantity of one per bay.

**Files:**
- Modify: `tools/generate.py` (`parts`, `write_glass`, `write`)
- Test: `tools/test_generate.py` (append `bayCams`, `BayPartsTest`, `WriteBaysTest`, `MainBaysTest`)

- [ ] **Step 1: Write the failing tests**

**Append** to `tools/test_generate.py`:
```python
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
```

- [ ] **Step 2: Run them to see them fail**

Run: `cd ~/diy-window/tools && python3 -m unittest test_generate.BayPartsTest test_generate.WriteBaysTest test_generate.MainBaysTest 2>&1 | tail -3`
Expected: `FAILED (failures=7, errors=4)`:
- the errors are `KeyError: 'SN'` and `'ML'`, and a missing `SN.scad`;
- the failures are counts that don't scale yet: `H` 4 instead of 8, glass qty `1`, no `BAYS` lines, and `35 part types, 129 prints`;
- `testFrameCornersAndJambsAreUnchanged`, `testEveryBayHasItsCamsOverItsKeepers`, `testOneBayHasNoMullionParts` and `testOneBayLayoutScadHasNoBayLines` already pass.

- [ ] **Step 3: Scale the frame, transom and sash segments**

**Replace** in `tools/generate.py`:
```python
    ends = lambda name: min(2, m[name]["n"])
    out = []
```
**with:**
```python
    ends = lambda name: min(2, m[name]["n"])
    bays = lay["bays"]
    out = []
```

**Replace** in `tools/generate.py`:
```python
    seg("H", "head", "sash_rebate", m["head"]["n"], bosses=lay["has_screen"])
    seg("S", "sill", "sill", m["sill"]["n"] - ends("sill"))
    seg("SW", "sill", "sill", ends("sill"), weep=True)
    seg("JL", "jamb_lower", "glazing", 2 * m["jamb_lower"]["n"])
    seg("JU", "jamb_upper", "sash_rebate", 2 * m["jamb_upper"]["n"])
    seg("T", "transom", "transom", m["transom"]["n"] - ends("transom"))
    seg("TE", "transom", "transom", ends("transom"), weep=True, bosses=True)
    seg("SH", "sash_horizontal", "sash", m["sash_horizontal"]["n"])
    seg("SB", "sash_horizontal", "sash", m["sash_horizontal"]["n"] - ends("sash_horizontal"))
    seg("SBE", "sash_horizontal", "sash", ends("sash_horizontal"), weep=True, bosses=True, boss_dz=lay["keeper_dz"])
    seg("SV", "sash_vertical", "sash", 2 * m["sash_vertical"]["n"])
    if lay["has_screen"]:
        seg("NH", "screen_horizontal", "screen", 2 * m["screen_horizontal"]["n"], "interior")
        seg("NV", "screen_vertical", "screen", 2 * m["screen_vertical"]["n"], "interior")
```
**with:**
```python
    seg("H", "head", "sash_rebate", bays * m["head"]["n"], bosses=lay["has_screen"])
    seg("S", "sill", "sill", bays * (m["sill"]["n"] - ends("sill")))
    seg("SW", "sill", "sill", bays * ends("sill"), weep=True)
    seg("JL", "jamb_lower", "glazing", 2 * m["jamb_lower"]["n"])
    seg("JU", "jamb_upper", "sash_rebate", 2 * m["jamb_upper"]["n"])
    seg("T", "transom", "transom", bays * (m["transom"]["n"] - ends("transom")))
    seg("TE", "transom", "transom", bays * ends("transom"), weep=True, bosses=True)
    if bays > 1:
        seg("ML", "mullion_lower", "mullion_glazing", (bays - 1) * m["mullion_lower"]["n"])
        seg("MU", "mullion_upper", "mullion_sash", (bays - 1) * m["mullion_upper"]["n"])
    seg("SH", "sash_horizontal", "sash", bays * m["sash_horizontal"]["n"])
    seg("SB", "sash_horizontal", "sash", bays * (m["sash_horizontal"]["n"] - ends("sash_horizontal")))
    seg("SBE", "sash_horizontal", "sash", bays * ends("sash_horizontal"), weep=True, bosses=True,
        boss_dz=lay["keeper_dz"])
    seg("SV", "sash_vertical", "sash", 2 * bays * m["sash_vertical"]["n"])
    if lay["has_screen"]:
        seg("NH", "screen_horizontal", "screen", 2 * bays * m["screen_horizontal"]["n"], "interior")
        seg("NV", "screen_vertical", "screen", 2 * bays * m["screen_vertical"]["n"], "interior")
```

- [ ] **Step 4: Add the nodes and shoes, and scale the per-bay parts**

**Replace** in `tools/generate.py`:
```python
    hinges = lay["hinges"]
    n_nose, s_nose = split(lay["w"] - 2 * NOSE_END, D["JOINT_GAP"], lay["max_seg"])
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
        part("NS", "sill_nose", f'{s_nose}, "NS"', n_nose, "exterior", s_nose),
        part("CMB", "cam_base", '"CMB"', 2, "interior"),
        part("CMH", "cam_handle", '"CMH"', 2, "interior"),
        part("KP", "cam_keeper", '"KP"', 2, "interior"),
```
**with:**
```python
    hinges = lay["hinges"] * bays
    n_nose, s_nose = split(lay["w"] - 2 * NOSE_END, D["JOINT_GAP"], lay["max_seg"])
    out += [
        part("CH", "corner_block", '"sash_rebate", "sash_rebate", "CH"', 2),
        part("CSL", "corner_block", '"sill", "glazing", "CSL"', 1),
        part("CSR", "corner_block", '"sill", "glazing", "CSR", mirrored=true', 1),
        part("CS", "corner_block", '"sash", "sash", "CS"', 4 * bays),
        part("CN", "corner_block", '"screen", "screen", "CN"', 4 * bays, "interior"),
        part("JN", "jamb_node", '"JN"', 2),
        part("TSL", "transom_shoe", '"TSL", mirrored=true', 1),
        part("TSR", "transom_shoe", '"TSR"', 1),
    ]
    if bays > 1:
        out += [
            part("SN", "frame_node", '"sill", "SN"', bays - 1),
            part("HN", "frame_node", '"sash_rebate", "HN"', bays - 1),
            part("TX", "cross_node", '"TX"', bays - 1),
            part("MSL", "mullion_shoe", '"mullion_glazing", "MSL"', 2 * (bays - 1)),
            part("MST", "mullion_shoe", '"mullion_sash", "MST"', bays - 1),
            part("MSH", "mullion_shoe", '"mullion_sash", "MSH", head=true', bays - 1),
        ]
    out += [
        part("GW", "setting_block", '"GW", wedge=true', 2 * bays),
        part("GF", "setting_block", '"GF"', 6 * bays),
        part("WC", "weep_cap", '"WC"', bays * (ends("sill") + ends("sash_horizontal"))),
        part("NS", "sill_nose", f'{s_nose}, "NS"', n_nose, "exterior", s_nose),
        part("CMB", "cam_base", '"CMB"', 2 * bays, "interior"),
        part("CMH", "cam_handle", '"CMH"', 2 * bays, "interior"),
        part("KP", "cam_keeper", '"KP"', 2 * bays, "interior"),
```

- [ ] **Step 5: Beads and spacers per pane**

**Replace** in `tools/generate.py`:
```python
        ("BFH", lay["w"] - 2 * D["FRAME_BODY"]),
```
**with:**
```python
        ("BFH", lay["opening"]),
```

**Replace** in `tools/generate.py`:
```python
        out.append(part(pid, "bead", f'"{g}", {s}, "{pid}"', 2 * n, "interior", s))
```
**with:**
```python
        out.append(part(pid, "bead", f'"{g}", {s}, "{pid}"', 2 * n * bays, "interior", s))
```

**Replace** in `tools/generate.py`:
```python
                out.append(part(pid, "acrylic_spacer", f'{s}, "{pid}"', 2 * n, "exterior", s))
        out.append(part("AC", "acrylic_spacer_corner", '"AC"', 8))
```
**with:**
```python
                out.append(part(pid, "acrylic_spacer", f'{s}, "{pid}"', 2 * n * bays, "exterior", s))
        out.append(part("AC", "acrylic_spacer_corner", '"AC"', 8 * bays))
```

`lay["opening"]` is `w − 2·FRAME_BODY` for one bay (exactly today's `BFH` run) and the body-to-body bay width from two bays up.

- [ ] **Step 6: Glass quantity and the bay lines in `layout.scad`**

**Replace** in `tools/generate.py`:
```python
            wr.writerow([pane, g, gw, gh, 1, GLASS_SPEC[g]])
```
**with:**
```python
            wr.writerow([pane, g, gw, gh, lay["bays"], GLASS_SPEC[g]])
```

**Replace** in `tools/generate.py`:
```python
        text += f"SEG_{key} = {mem['seg']};\nN_{key} = {mem['n']};\n"
```
**with:**
```python
        text += f"SEG_{key} = {mem['seg']};\nN_{key} = {mem['n']};\n"
    if lay["bays"] > 1:
        text += f"BAYS = {lay['bays']};\nPITCH = {round(lay['pitch'], 4)};\n"
        text += f"MULLIONS = {json.dumps([round(c, 4) for c in lay['mullions']])};\n"
```

- [ ] **Step 7: Run the tests to see them pass**

Run: `cd ~/diy-window/tools && python3 -m unittest test_generate 2>&1 | tail -3`
Expected: `OK` (71 tests).

- [ ] **Step 8: Checkpoint**

Run: `cd ~/diy-window/tools && python3 -m unittest discover -p 'test_*.py' 2>&1 | grep -E '^(Ran|OK|FAILED)'`
Expected: `Ran 261 tests`, `OK`.

Then run the **compatibility check** (Task 0). Expected: `BYTE-IDENTICAL`.

Then: `cd ~/diy-window && python3 tools/generate.py params/home-1800x1500-2bay.json | head -1`. Expected: `home-1800x1500-2bay: 43 part types, 226 prints -> .../cad/generated`. Finish with `python3 tools/generate.py params/bench-600.json > /dev/null`, so that `cad/generated/` is back on the bench window.

**Review gate (generator):** stop here for a review of Tasks 1–3 against spec §§3–5 and the Decisions table.

---
### Task 4: The two mullion profiles (`cad/profile.scad`)

The two profiles keep the transom's body and pocket, and have features on both sides:
- **`mullion_glazing`**: the transom's glazing side on both sides (stop leg, glazing kerf, bead keyway).
- **`mullion_sash`**: the transom's sash side on both sides (fin and kerf, inner stop and kerf), plus a screen magnet channel 2–15 mm in from each body face, where the jamb has it.

How they are built:
- The right side is defined once. `both_sides()` mirrors it about the 35 mm centreline, so the two sides are mirror images by construction.
- Neither profile has chambers. The transom has none either: its body is too narrow.
- Every existing profile's geometry is unchanged (Task 5 re-renders the home window's segments and compares the bytes).

**Files:**
- Create: `cad/tests/mullion_test.scad`, `cad/tests/mullion_sheet.scad`
- Modify: `cad/profile.scad`, `cad/lib/segment.scad` (`label_at`)

- [ ] **Step 1: Write the profile asserts**

**Create** `cad/tests/mullion_test.scad`:
```openscad
// cad/tests/mullion_test.scad
include <../generated/dims.scad>
use <../profile.scad>
use <../lib/segment.scad>

TRACK_SCREW_L = 16;
ml = MULLION_W / 2 - MULLION_HALF_BODY;
mh = MULLION_W / 2 + MULLION_HALF_BODY;

assert(ml == FRAME_W - FRAME_BODY, "the mullion leg zone matches the frame's, so one shoe fits the sill and the transom");
assert(MULLION_W / 2 - TRANSOM_GLASS == FRAME_W - GLASS_EDGE, "end and inner bays get the same pane bite");
assert(TRANSOM_GLASS - MULLION_HALF_BODY == GLASS_CLEAR, "mullion glass clearance");
assert(BEAD_W <= ml, "bead fits the mullion rebate and ends inside the node keyway");
assert(MULLION_W - (mh + 2 + MAG_W) >= MIN_SKIN, "mullion magnet channel keeps a lip at the profile edge");

for (n = ["mullion_glazing", "mullion_sash"]) {
    o = pocket_origin(n);
    p = pocket(n);
    pr = pocket_rect(n);
    assert(o[0] - ml >= MIN_SHELL && mh - (o[0] + p[0]) >= MIN_SHELL && o[1] >= MIN_SHELL && DEPTH - (o[1] + p[1]) >= MIN_SHELL,
           str(n, ": shell round the steel tube"));
    assert(len(chamber_rects(n)) == 0, str(n, ": solid body, like the transom"));
    assert(core_box(n) == [ml, 0, mh, DEPTH] && has_cord(n), str(n, ": cord ring round the body"));
    for (r = concat(bead_key_rects(n), kerf_rects(n), mag_rects(n)))
        assert(rect_gap(r, pr) >= MIN_SKIN, str(n, ": feature ", r, " to tube pocket ", rect_gap(r, pr)));
    for (r = kerf_rects(n)) for (m = mag_rects(n))
        assert(rect_gap(r, m) >= MIN_SKIN, str(n, ": kerf ", r, " to magnet channel ", m));
    sx = screw_x(n);
    assert(sx - TUBE_SCREW_D / 2 >= pr[0] + 3 && sx + TUBE_SCREW_D / 2 <= pr[2] - 3, str(n, ": tube screw on the flat of the tube"));
    for (m = mag_rects(n)) assert(rect_gap([sx - CSK_D / 2, DEPTH - 1, sx + CSK_D / 2, DEPTH], m) >= MIN_SKIN,
                                  str(n, ": tube-screw countersink clears the magnet channel"));
    assert(label_at(n)[0] == core_box(n)[0], str(n, ": label on the body's low-x face, engraved facing -x"));
}
assert(len(kerf_rects("mullion_glazing")) == 2 && len(bead_key_rects("mullion_glazing")) == 4, "glazing kerf and bead keyway on both sides");
assert(len(kerf_rects("mullion_sash")) == 4 && len(mag_rects("mullion_sash")) == 2, "fin kerf, inner-stop kerf and magnet channel on both sides");
assert(glazing_kerf_rect("mullion_glazing")[1] >= MIN_SKIN, "mullion glazing kerf floor");
assert(kerf_rects("mullion_sash")[0] == seal_kerf_rects("transom")[0] && kerf_rects("mullion_sash")[1] == seal_kerf_rects("transom")[1],
       "mullion sash side matches the transom sash side");

mt = [pocket_rect("mullion_sash")[1] + TUBE_CLEAR, pocket_rect("mullion_sash")[3] - TUBE_CLEAR];
assert(stay_c_min() >= mt[0] + MIN_SKIN && stay_c_max() <= mt[1] - MIN_SKIN, "stay track screws land on the mullion tube");
assert((mh - ml) - 2 * TRACK_SCREW_L >= MIN_SKIN, "8g x 16 stay-track screws from the two sides miss each other inside the tube");
echo("mullion profile rules ok");
```

- [ ] **Step 2: Run them to see them fail**

Run: `cd ~/diy-window && cad/box.sh test`
Expected: exit 1, with `ERROR: Assertion '...' failed: "mullion_glazing: shell round the steel tube" in file mullion_test.scad, line 20`. An unknown profile name falls through to the frame's pocket.

- [ ] **Step 3: Add the profiles**

**Replace** in `cad/profile.scad`:
```openscad
function tube(name) =
    name == "transom" ? TUBE_TRANSOM : name == "sash" ? TUBE_SASH : name == "screen" ? TUBE_SCREEN : TUBE_FRAME;
```
**with:**
```openscad
function is_mullion(name) = name == "mullion_glazing" || name == "mullion_sash";

function mirror_rect(r) = [MULLION_W - r[2], r[1], MULLION_W - r[0], r[3]];

function both_sides(rs) = concat(rs, [for (r = rs) mirror_rect(r)]);

function tube(name) =
    name == "transom" || is_mullion(name) ? TUBE_TRANSOM : name == "sash" ? TUBE_SASH : name == "screen" ? TUBE_SCREEN : TUBE_FRAME;
```

**Replace** in `cad/profile.scad`:
```openscad
    name == "transom" ? [TRANSOM_W / 2, DEPTH / 2] - pocket(name) / 2
```
**with:**
```openscad
    name == "transom" ? [TRANSOM_W / 2, DEPTH / 2] - pocket(name) / 2
  : is_mullion(name) ? [MULLION_W / 2, DEPTH / 2] - pocket(name) / 2
```

**Replace** in `cad/profile.scad`:
```openscad
    name == "transom" ? TRANSOM_W : name == "sash" ? SASH_W : name == "screen" ? SCREEN_W : FRAME_W;
```
**with:**
```openscad
    name == "transom" ? TRANSOM_W : is_mullion(name) ? MULLION_W : name == "sash" ? SASH_W : name == "screen" ? SCREEN_W : FRAME_W;
```

**Replace** in `cad/profile.scad`:
```openscad
  : name == "transom" ? key_rects(TRANSOM_W / 2 - TRANSOM_HALF_BODY, 1)
  : [];
```
**with:**
```openscad
  : name == "transom" ? key_rects(TRANSOM_W / 2 - TRANSOM_HALF_BODY, 1)
  : name == "mullion_glazing" ? both_sides(key_rects(MULLION_W / 2 - MULLION_HALF_BODY, 1))
  : [];
```

**Replace** in `cad/profile.scad`:
```openscad
  : name == "transom" ? kerf_rect(TRANSOM_W / 2 - TRANSOM_GLASS - GASKET_IN, STOP_T, -1)
```
**with:**
```openscad
  : name == "transom" ? kerf_rect(TRANSOM_W / 2 - TRANSOM_GLASS - GASKET_IN, STOP_T, -1)
  : name == "mullion_glazing" ? kerf_rect(MULLION_W / 2 - TRANSOM_GLASS - GASKET_IN, STOP_T, -1)
```

**Replace** in `cad/profile.scad`:
```openscad
function sash_side_e(name) = name == "sash_rebate" ? FRAME_BODY : name == "transom" ? TRANSOM_W / 2 + TRANSOM_HALF_BODY : undef;
```
**with:**
```openscad
function sash_side_e(name) =
    name == "sash_rebate" ? FRAME_BODY : name == "transom" ? TRANSOM_W / 2 + TRANSOM_HALF_BODY
  : name == "mullion_sash" ? MULLION_W / 2 + MULLION_HALF_BODY : undef;
```

**Replace** in `cad/profile.scad`:
```openscad
function kerf_rects(name) =
    concat(is_undef(glazing_kerf_rect(name)) ? [] : [glazing_kerf_rect(name)], seal_kerf_rects(name));
```
**with:**
```openscad
function kerf_rects(name) =
    let(k = concat(is_undef(glazing_kerf_rect(name)) ? [] : [glazing_kerf_rect(name)], seal_kerf_rects(name)))
    is_mullion(name) ? both_sides(k) : k;
```

**Replace** in `cad/profile.scad`:
```openscad
  : name == "transom" ? [TRANSOM_MAG_X, DEPTH - MAG_D, TRANSOM_MAG_X + MAG_W, DEPTH + EPS]
  : undef;
```
**with:**
```openscad
  : name == "transom" ? [TRANSOM_MAG_X, DEPTH - MAG_D, TRANSOM_MAG_X + MAG_W, DEPTH + EPS]
  : name == "mullion_sash" ? let(e = sash_side_e(name)) [e + 2, DEPTH - MAG_D, e + 2 + MAG_W, DEPTH + EPS]
  : undef;

function mag_rects(name) = is_undef(mag_rect(name)) ? [] : is_mullion(name) ? both_sides([mag_rect(name)]) : [mag_rect(name)];
```

**Replace** in `cad/profile.scad`:
```openscad
    th = TRANSOM_W / 2 + TRANSOM_HALF_BODY;
    difference() {
```
**with:**
```openscad
    th = TRANSOM_W / 2 + TRANSOM_HALF_BODY;
    ml = MULLION_W / 2 - MULLION_HALF_BODY;
    mh = MULLION_W / 2 + MULLION_HALF_BODY;
    difference() {
```

**Replace** in `cad/profile.scad`:
```openscad
        else if (name == "screen") rect(0, 0, SCREEN_W, SCREEN_DEPTH);
        else assert(false, str("unknown profile ", name));
```
**with:**
```openscad
        else if (name == "screen") rect(0, 0, SCREEN_W, SCREEN_DEPTH);
        else if (name == "mullion_glazing") union() { rect(ml, 0, mh, DEPTH); rect(0, 0, ml, STOP_T); rect(mh, 0, MULLION_W, STOP_T); }
        else if (name == "mullion_sash") union() {
            rect(ml, 0, mh, DEPTH);
            sash_side_add(mh, MULLION_W - mh);
            translate([MULLION_W, 0]) mirror([1, 0]) sash_side_add(mh, MULLION_W - mh);
        }
        else assert(false, str("unknown profile ", name));
```

**Replace** in `cad/profile.scad`:
```openscad
        if (name == "sash_rebate" || name == "transom") rect_r(mag_rect(name));
```
**with:**
```openscad
        for (r = mag_rects(name)) rect_r(r);
```

**Replace** in `cad/profile.scad`:
```openscad
  : name == "transom" ? [TRANSOM_W / 2 - TRANSOM_HALF_BODY, 0, TRANSOM_W / 2 + TRANSOM_HALF_BODY, DEPTH]
  : name == "sash" ? [0, SASH_Y0, SASH_BODY, LIP_Y1]
```
**with:**
```openscad
  : name == "transom" ? [TRANSOM_W / 2 - TRANSOM_HALF_BODY, 0, TRANSOM_W / 2 + TRANSOM_HALF_BODY, DEPTH]
  : is_mullion(name) ? [MULLION_W / 2 - MULLION_HALF_BODY, 0, MULLION_W / 2 + MULLION_HALF_BODY, DEPTH]
  : name == "sash" ? [0, SASH_Y0, SASH_BODY, LIP_Y1]
```

- [ ] **Step 4: Put the segment labels on a hidden body face**

**Replace** in `cad/lib/segment.scad`:
```openscad
    name == "transom" ? [TRANSOM_W / 2 - TRANSOM_HALF_BODY, GLASS_Y0 + 11]
```
**with:**
```openscad
    name == "transom" ? [TRANSOM_W / 2 - TRANSOM_HALF_BODY, GLASS_Y0 + 11]
  : name == "mullion_glazing" ? [MULLION_W / 2 - MULLION_HALF_BODY, GLASS_Y0 + 11]
  : name == "mullion_sash" ? [MULLION_W / 2 - MULLION_HALF_BODY, (FIN_Y1 + LIP_Y0) / 2]
```

Where the labels end up:
- **`ML`**: the label sits in the left glazing pocket, behind the pane edge, like the transom's.
- **`MU`**: its body face at y = 22 lies under the fin, so the label goes in the stay cavity between the fin top and the sash lip (y = 37). That face is hidden while the sash is closed.

Both use the existing `engrave()` with `facing = -1`, which reads correctly on a face that looks towards −x (asserted: the label x is the body's low-x face).

- [ ] **Step 5: Run the asserts to see them pass**

Run: `cd ~/diy-window && cad/box.sh test`
Expected: `8 test files passed`.

- [ ] **Step 6: Look at the profiles**

**Create** `cad/tests/mullion_sheet.scad`:
```openscad
// cad/tests/mullion_sheet.scad
use <../profile.scad>
include <../generated/dims.scad>

names = ["mullion_glazing", "transom", "mullion_sash"];
for (i = [0 : len(names) - 1]) translate([i * 100, 0]) {
    color("SteelBlue") profile(names[i]);
    color("Black") translate([0, -12]) text(names[i], size = 5);
}
```

Run: `cd ~/diy-window && mkdir -p .bays-review && cad/box.sh png tests/mullion_sheet.scad ~/diy-window/.bays-review/mullion-sheet.png --camera=0,0,0,0,0,0,500 --viewall --autocenter --projection=ortho`

Read the PNG. The outside face is at the bottom of each profile, and the transom sits in the middle for comparison. Check:
- **`mullion_glazing`:** a 34 mm body with the 20.6 × 40.6 pocket, and an 18 mm stop leg on each side at the bottom, each with its glazing kerf notch. Bead keyway notches high up on both body faces.
- **`mullion_sash`:** a fin with its kerf at mid-height on both sides, the inner stop at the top on both sides with its kerf, and the magnet-channel steps at both top corners.
- **Symmetry:** both profiles are mirror-symmetric about their centre.

- [ ] **Step 7: Checkpoint**

Run: `cd ~/diy-window/tools && python3 -m unittest discover -p 'test_*.py' 2>&1 | grep -E '^(Ran|OK|FAILED)'`
Expected: `Ran 261 tests`, `OK` (no Python change).

---

### Task 5: Nodes SN, HN and TX (`cad/parts/frame_node.scad`, `cad/parts/cross_node.scad`)

**The nodes.** They are plain bodies, like `JN`: the shoes carry the turns.
- **`SN`** (sill) and **`HN`** (head) are 70 mm lengths of frame body, threaded on the sill and head tubes. Each has:
  - the dovetail slot in its body face, open on the room side and stopped 8 mm from the outside face;
  - two lock screws on the slot flanks;
  - a tube screw and two wall fixings;
  - end cord grooves;
  - bead keyways in its first and last 18 mm, where the horizontal beads of the two bays end. `SN` also has the sill-nose keyway, so the nose runs through it.
- **`TX`** is a 70 mm length of transom body on the transom tube, with a slot in both faces. It also carries the transom magnet channel and, on its inside face, the two vertical channels that take each screen's magnet line from the transom channel up to the upper mullion.

**The dovetail.** All three nodes use the 4 mm mullion dovetail (see Decisions). `jamb_node.scad`'s dovetail and lock functions take the depth, flare and lock offset as parameters, with today's values as defaults, so `JN`, `TSL` and `TSR` don't change (this task re-renders them and compares the bytes).

**Files:**
- Modify: `cad/parts/jamb_node.scad`
- Create: `cad/lib/mullion.scad`, `cad/parts/frame_node.scad`, `cad/parts/cross_node.scad`
- Test: `cad/tests/mullion_test.scad` (append the node asserts)

- [ ] **Step 1: Write the node asserts**

**Append** to `cad/tests/mullion_test.scad`:
```openscad
use <../lib/mullion.scad>
use <../parts/jamb_node.scad>
use <../parts/cross_node.scad>

c = MULLION_W / 2;
k = mullion_leg();
d = mdove();
lk = mlock_uv();
tx = cross_faces();
function line_dist(p, a, b) = abs((b - a)[0] * (p - a)[1] - (b - a)[1] * (p - a)[0]) / norm(b - a);
function head_rect(x, z) = [x - CSK_D / 2, z - CSK_D / 2, x + CSK_D / 2, z + CSK_D / 2];
function xz(b) = [b[0], b[4], b[2], b[5]];

hd = dove_head(DOVE_CLEAR, d[0], d[1]);
up = [[0, DOVE_W / 2], [-d[0], DOVE_W / 2 + d[1]]];
dn = [[0, -DOVE_W / 2], [-d[0], -DOVE_W / 2 - d[1]]];
for (i = [1, 2]) assert(abs(line_dist(hd[i], up[0], up[1]) - DOVE_CLEAR) < 1e-6, str("mullion dovetail flank gap at ", hd[i]));
for (i = [0, 3]) assert(abs(line_dist(hd[i], dn[0], dn[1]) - DOVE_CLEAR) < 1e-6, str("mullion dovetail flank gap at ", hd[i]));
assert(abs(hd[0][0] + DOVE_CLEAR) < 1e-9 && abs(hd[2][0] + d[0] - DOVE_CLEAR) < 1e-9, "mullion dovetail mouth and floor gaps");
assert(d[1] / d[0] == DOVE_FLARE / DOVE_D, "mullion dovetail flanks at the jamb node's angle");
assert(pocket_rect("transom")[0] - (tx[0] + d[0]) >= CHAMBER_WALL && (tx[1] - d[0]) - pocket_rect("transom")[2] >= CHAMBER_WALL,
       "cross-node slots stop a chamber wall short of the transom tube");
for (n = ["sill", "sash_rebate"]) assert(FRAME_BODY - d[0] - pocket_rect(n)[2] >= CHAMBER_WALL, str(n, " node slot clears the frame tube"));

assert(len(lk) == 2, "two lock screws per joint");
for (q = lk) {
    fl = DOVE_W / 2 + d[1] * (-q[0]) / d[0];
    assert(q[0] == -d[0] / 2 && abs(abs(q[1]) - fl) < 1e-9, str("mullion lock axis on the slot flank ", q));
    zs = c + q[1];
    assert(zs - CSK_D / 2 >= k + MIN_SKIN && zs + CSK_D / 2 <= MULLION_W - k - MIN_SKIN, "lock heads clear the node bead keyways");
    for (dz = [-NODE_FIX_OFFSET, NODE_FIX_OFFSET])
        assert(abs(zs - (c + dz)) - CSK_D / 2 - FIX_CB_D / 2 >= MIN_SKIN, "lock heads clear the SN and HN fixing counterbores");
}
assert(LOCK_D / 2 - DOVE_CLEAR >= 1, "lock pilot bites into the tongue");
assert(DEPTH - LOCK_L >= STOP_T + DOVE_CLEAR + MIN_SKIN, "lock pilot stays inside the tongue length");
assert(lock_top() <= DEPTH - MAG_D, "lock heads at or below the magnet channel floor");
for (q = cross_locks()) {
    assert(q[0] - LOCK_D / 2 >= pocket_rect("transom")[2] + MIN_SKIN || q[0] + LOCK_D / 2 <= pocket_rect("transom")[0] - MIN_SKIN,
           str("cross-node lock pilot clears the transom tube ", q));
    hr = head_rect(q[0], c + q[1]);
    sx = screw_x("transom");
    assert(rect_gap(hr, [sx - CSK_D / 2, c - CSK_D / 2, sx + CSK_D / 2, c + CSK_D / 2]) >= MIN_SKIN, "cross-node lock heads clear its tube screw");
    for (m = cross_mag_cuts()) assert(rect_gap(hr, xz(m)) >= MIN_SKIN || hr[0] >= m[0], str("cross-node lock head clear of the screen channel ", q));
}
for (m = cross_mag_cuts()) {
    assert(m[0] <= mag_rect("transom")[0] && m[2] > tx[1] && m[1] == DEPTH - MAG_D, str("screen channel runs from the transom channel to the upper shoe ", m));
    assert(m[4] >= CORD_D / 2 + MIN_SKIN && m[5] <= MULLION_W - CORD_D / 2 - MIN_SKIN, "screen channel clears the cross-node end grooves");
}
assert([for (m = cross_mag_cuts()) [m[4], m[5]]] == [for (r = mag_rects("mullion_sash")) [r[0], r[2]]], "cross-node channels line up with the mullion channels");
echo("mullion node rules ok");
```

- [ ] **Step 2: Run them to see them fail**

Run: `cd ~/diy-window && cad/box.sh test`
Expected: exit 1, with `WARNING: Can't open library '../lib/mullion.scad'` (and `'../parts/cross_node.scad'`) from `mullion_test.scad`.

- [ ] **Step 3: Give the jamb node's dovetail functions parameters**

**Replace** in `cad/parts/jamb_node.scad`:
```openscad
function lock_uv() = [for (s = [-1, 1]) [-LOCK_U, s * (DOVE_W / 2 + DOVE_FLARE * LOCK_U / DOVE_D)]];
```
**with:**
```openscad
function lock_uv(d = DOVE_D, f = DOVE_FLARE, u = LOCK_U) = [for (s = [-1, 1]) [-u, s * (DOVE_W / 2 + f * u / d)]];
```

**Replace** in `cad/parts/jamb_node.scad`:
```openscad
function dove_slot() =
    let(m = DOVE_W / 2, b = m + DOVE_FLARE)
    [[EPS, -m], [EPS, m], [0, m], [-DOVE_D, b], [-DOVE_D, -b], [0, -m]];

function dove_head(c) =
    let(m = DOVE_W / 2, b = m + DOVE_FLARE, l = norm([DOVE_D, DOVE_FLARE]),
        mh = m - c * (l - DOVE_FLARE) / DOVE_D, bh = b - c * (l + DOVE_FLARE) / DOVE_D)
    [[-c, -mh], [-c, mh], [-DOVE_D + c, bh], [-DOVE_D + c, -bh]];
```
**with:**
```openscad
function dove_slot(d = DOVE_D, f = DOVE_FLARE) =
    let(m = DOVE_W / 2, b = m + f)
    [[EPS, -m], [EPS, m], [0, m], [-d, b], [-d, -b], [0, -m]];

function dove_head(c, d = DOVE_D, f = DOVE_FLARE) =
    let(m = DOVE_W / 2, b = m + f, l = norm([d, f]), mh = m - c * (l - f) / d, bh = b - c * (l + f) / d)
    [[-c, -mh], [-c, mh], [-d + c, bh], [-d + c, -bh]];
```

**Replace** in `cad/parts/jamb_node.scad`:
```openscad
module dove_slot2d() { polygon(dove_slot()); }

module dove_tongue2d() {
    polygon(dove_head(DOVE_CLEAR));
```
**with:**
```openscad
module dove_slot2d(d = DOVE_D, f = DOVE_FLARE) { polygon(dove_slot(d, f)); }

module dove_tongue2d(d = DOVE_D, f = DOVE_FLARE) {
    polygon(dove_head(DOVE_CLEAR, d, f));
```

- [ ] **Step 4: Add the mullion helpers and the two node parts**

**Create** `cad/lib/mullion.scad`:
```openscad
// cad/lib/mullion.scad
include <../generated/dims.scad>
use <../parts/jamb_node.scad>

function mullion_leg() = MULLION_W / 2 - MULLION_HALF_BODY;

function mdove() = [MULLION_DOVE_D, MULLION_DOVE_D * DOVE_FLARE / DOVE_D];

function mlock_uv() = lock_uv(mdove()[0], mdove()[1], LOCK_U);
```

**Create** `cad/parts/frame_node.scad`:
```openscad
// cad/parts/frame_node.scad
include <../generated/dims.scad>
use <../profile.scad>
use <../lib/segment.scad>
use <../lib/emboss.scad>
use <../lib/mullion.scad>
use <jamb_node.scad>

EPS = 0.01;

function frame_node_fix(name) = name == "sill" ? "glazing" : name;

module frame_node(name, code) {
    assert(name == "sill" || name == "sash_rebate", str(code, ": frame nodes sit in the sill or the head, not ", name));
    c = MULLION_W / 2;
    k = mullion_leg();
    d = mdove();
    difference() {
        linear_extrude(MULLION_W) rect(0, 0, FRAME_BODY, DEPTH);
        translate([0, 0, -EPS]) linear_extrude(MULLION_W + 2 * EPS) {
            pocket_cut(name);
            if (name == "sill") for (r = nose_key_rects()) rect_r(r);
        }
        for (z = [-EPS, MULLION_W - k]) translate([0, 0, z]) linear_extrude(k + EPS) bead_key(name);
        for (z = [-EPS, MULLION_W - CORD_D / 2]) translate([0, 0, z]) end_groove(name);
        translate([FRAME_BODY, DEPTH + EPS, c]) rotate([90, 0, 0]) linear_extrude(DEPTH - STOP_T + EPS) dove_slot2d(d[0], d[1]);
        for (q = mlock_uv()) translate([FRAME_BODY + q[0], 0, c + q[1]]) lock_hole();
        tube_screw(name, c);
        for (dz = [-NODE_FIX_OFFSET, NODE_FIX_OFFSET]) fixing_hole(frame_node_fix(name), c + dz);
        engrave(code, label_at(name), c);
    }
}
```

**Create** `cad/parts/cross_node.scad`:
```openscad
// cad/parts/cross_node.scad
include <../generated/dims.scad>
use <../profile.scad>
use <../lib/segment.scad>
use <../lib/emboss.scad>
use <../lib/mullion.scad>
use <jamb_node.scad>
use <transom_shoe.scad>

EPS = 0.01;

function cross_faces() = [TRANSOM_W / 2 - TRANSOM_HALF_BODY, TRANSOM_W / 2 + TRANSOM_HALF_BODY];

function cross_mag_cuts() =
    [for (r = mag_rects("mullion_sash")) [TRANSOM_MAG_X, DEPTH - MAG_D, cross_faces()[1] + EPS, DEPTH + EPS, r[0], r[2]]];

function cross_locks() =
    [for (q = mlock_uv()) each [[cross_faces()[0] - q[0], q[1]], [cross_faces()[1] + q[0], q[1]]]];

module cross_node(code) {
    c = MULLION_W / 2;
    k = mullion_leg();
    d = mdove();
    f = cross_faces();
    difference() {
        linear_extrude(MULLION_W) rect(f[0], 0, f[1], DEPTH);
        translate([0, 0, -EPS]) linear_extrude(MULLION_W + 2 * EPS) { pocket_cut("transom"); rect_r(mag_rect("transom")); }
        for (z = [-EPS, MULLION_W - k]) translate([0, 0, z]) linear_extrude(k + EPS) bead_key("transom");
        for (z = [-EPS, MULLION_W - CORD_D / 2]) translate([0, 0, z]) end_groove("transom");
        for (s = [[f[0], -1], [f[1], 1]]) translate([s[0], DEPTH + EPS, c]) rotate([90, 0, 0]) scale([s[1], 1, 1])
            linear_extrude(DEPTH - STOP_T + EPS) dove_slot2d(d[0], d[1]);
        for (q = cross_locks()) translate([q[0], 0, c + q[1]]) lock_hole();
        for (r = cross_mag_cuts()) box(r);
        tube_screw("transom", c);
        engrave(code, label_at("transom"), k / 2);
    }
}
```

Notes on the geometry:
- **Fixings.** `SN` fixes through its 40 mm flat top like a lower-jamb segment (`"glazing"` fixing, y = 16). Its counterbore opens into the drained glazing pocket and gets bedded. `HN` uses the head's fixing at y = 48, which opens between the two sash seals.
- **Slots.** `TX`'s lower slot is the same polygon, mirrored with `scale([-1, 1, 1])`, so it cuts upwards from the transom's glazing face.
- **Lock screws.** They sit at `u = LOCK_U` (3 mm into the node, like the jamb node), on the flank lines (asserted). Their heads finish 2 mm under the inside face, at the magnet-channel floor (asserted).

- [ ] **Step 5: Run the asserts to see them pass**

Run: `cd ~/diy-window && cad/box.sh test`
Expected: `8 test files passed`. `joint_test.scad` still passes, so the jamb node's defaults are unchanged.

- [ ] **Step 6: Render the nodes, and re-render the home window's existing parts**

Run:
```bash
cd ~/diy-window && mkdir -p .bays-review/stl-before && cp cad/stl/home-1800x1500/{JN,TSL,TSR,H,T,TE,JU,CH,SBE}.stl .bays-review/stl-before/
cad/box.sh render home-1800x1500 JN TSL TSR H T TE JU CH SBE | tail -1
for f in JN TSL TSR H T TE JU CH SBE; do cmp -s cad/stl/home-1800x1500/$f.stl .bays-review/stl-before/$f.stl && echo "$f same" || echo "$f DIFFERS"; done
cad/box.sh render home-1800x1500-2bay SN HN TX | tail -1
```
Expected: `9/9 parts ok`, all nine lines `... same`, then `3/3 parts ok`. If any reference STL differs, restore it from `.bays-review/stl-before/` and stop: the profile or dovetail change has altered an existing part.

- [ ] **Step 7: Look at the nodes**

Run (a throwaway view file: it isn't a `*_test.scad`, so `box.sh test` never runs it, and the last line deletes it):
```bash
cd ~/diy-window && cat > cad/tests/zz_view.scad <<'SCAD'
include <../generated/dims.scad>
use <../parts/frame_node.scad>
use <../parts/cross_node.scad>
sel = 0;
color("Peru") {
    if (sel == 0) frame_node("sill", "SN");
    if (sel == 1) frame_node("sash_rebate", "HN");
    if (sel == 2) cross_node("TX");
}
SCAD
view() { PARAMS=home-1800x1500-2bay cad/box.sh png tests/zz_view.scad ~/diy-window/.bays-review/$1.png -Dsel=$2 --projection=o $3; }
view sn 0 "--camera=0,0,0,60,0,130,300 --viewall --autocenter" &
view hn 1 "--camera=0,0,0,60,0,130,300 --viewall --autocenter" &
view tx 2 "--camera=0,0,0,60,0,130,300 --viewall --autocenter" &
view tx-label 2 "--camera=-120,-10,40,18,22,9" &
wait; rm cad/tests/zz_view.scad
```

Read the PNGs and check:
- **`sn.png`:**
  - The rebate face (x = 40) has the dovetail slot. It is open at the room-side edge, with the two countersunk lock holes cut into that edge on the slot flanks, and it stops short of the outside face.
  - There are two bead-keyway grooves, in the first and last 18 mm.
  - There are two large fixing counterbores near the outside face.
  - The end faces show the sill cord ring and the tube pocket.
- **`hn.png`:** the same slot. The counterbores sit near the room side (y = 48), and there are no bead keyways.
- **`tx.png`:**
  - The slot on the sash face, with its lock holes.
  - The transom magnet channel along the inside face, and the two vertical screen channels near the ends.
- **`tx-label.png`:** "TX" reads left to right, not mirrored, on the glazing face, in the first 18 mm, clear of the keyway.

- [ ] **Step 8: Checkpoint**

Run: `cd ~/diy-window && python3 tools/check_stl.py home-1800x1500` (after `python3 tools/generate.py params/home-1800x1500.json > /dev/null`).
Expected: `35/35 parts ok`.

Then: `python3 tools/generate.py params/bench-600.json > /dev/null`.

---

### Task 6: Mullion shoes MSL, MST and MSH (`cad/parts/mullion_shoe.scad`)

Each shoe is 18 mm of mullion profile: the node's leg zone, the same depth as the transom shoe. It has:
- a 3 mm solid end wall, which is the tube stop;
- the 4 mm dovetail tongue;
- two lock holes on the tongue flanks;
- a tube screw;
- a 3 mm cord seam groove across its end face, below the dovetail stop;
- a cord ring at its far end;
- the turns that carry the node member's features across the shoe, into the mullion's matching features:
  - **`MSL`** (`mullion_glazing`): the glazing kerf on both sides. The sill kerf and the transom's glazing kerf sit at the same depth from their node faces (asserted), so one part serves both ends of a lower mullion. The top one is turned end for end.
  - **`MST`** (`mullion_sash` at the transom): fin stubs that join the transom fin to the mullion fins, and the fin-kerf and inner-stop-kerf turns. The mullion's own magnet channels run straight through it, onto `TX`.
  - **`MSH`** (`mullion_sash` at the head): the same, plus the head's magnet channel turning into the mullion channels.

**Files:**
- Create: `cad/parts/mullion_shoe.scad`
- Test: `cad/tests/mullion_test.scad` (append the shoe asserts)

- [ ] **Step 1: Write the shoe asserts**

**Append** to `cad/tests/mullion_test.scad`:
```openscad
use <../parts/mullion_shoe.scad>

for (q = lk) assert(head_rect(c + q[1], q[0])[0] >= ml + MIN_SKIN && head_rect(c + q[1], q[0])[2] <= mh - MIN_SKIN, "lock head lands on the shoe body");
for (profile = ["mullion_glazing", "mullion_sash"]) for (head = profile == "mullion_sash" ? [false, true] : [false]) {
    z = shoe_node_z(profile, head);
    f = shoe_features(profile, head);
    assert(len(z) == len(f), "one node feature per mullion feature pair");
    for (i = [0 : len(z) - 1]) for (r = f[i]) {
        b = mshoe_turn(r, z[i]);
        assert(b[0] <= r[0] && b[2] >= r[2] && (b[0] < 0 || b[2] > MULLION_W), str(profile, ": turn runs from the mullion feature to the shoe edge ", b));
        assert(b[4] >= 0 && b[5] <= k, str(profile, ": turn inside the shoe length ", b));
        for (q = lk) assert(rect_gap(xz(b), head_rect(c + q[1], q[0])) >= MIN_SKIN, str(profile, ": turn ", b, " clear of the lock heads"));
    }
    sz = mshoe_screw_z();
    assert(sz - TUBE_SCREW_D / 2 >= SHOE_WALL + 2 && sz + TUBE_SCREW_D / 2 <= k - MIN_SKIN,
           str(profile, ": shoe tube screw hits the tube with the tube anywhere in its 2 mm end clearance"));
    for (t = mshoe_turns(profile, head))
        assert(rect_gap(xz(t), [screw_x(profile) - CSK_D / 2, sz - CSK_D / 2, screw_x(profile) + CSK_D / 2, sz + CSK_D / 2]) >= MIN_SKIN
               || t[1] < DEPTH - MAG_D - 1, str(profile, ": tube-screw head clear of the turns"));
    g = mshoe_seam_groove(profile);
    assert(g[3] - g[1] == CORD_D && g[1] >= MIN_SKIN && g[3] <= STOP_T - MIN_SKIN, str(profile, ": seam groove below the dovetail stop"));
    assert(g[0] <= c - DOVE_W / 2 - d[1] && g[2] >= c + DOVE_W / 2 + d[1], str(profile, ": seam groove spans the dovetail"));
    for (r = kerf_rects(profile)) assert(rect_gap([g[0], g[1], g[2], g[3]], r) >= MIN_SKIN, str(profile, ": seam groove clears the kerfs"));
}
assert(node_z(glazing_kerf_rect("sill"), FRAME_BODY) == [tx[0] - glazing_kerf_rect("transom")[2], tx[0] - glazing_kerf_rect("transom")[0]],
       "sill and transom glazing kerfs sit at the same depth, so MSL serves both ends");
for (i = [0, 1]) assert(node_z(seal_kerf_rects("sash_rebate")[i], FRAME_BODY) == node_z(seal_kerf_rects("transom")[i], tx[1]),
                        "head and transom seal kerfs sit at the same depth in the upper shoes");
for (s = mshoe_fin_stubs("mullion_sash")) {
    assert(s[1] == FIN_Y0 && s[3] == FIN_Y1 && s[4] == 0 && s[5] == FIN_L && (s[0] == 0 || s[2] == MULLION_W), str("fin stub bridges to the shoe edge ", s));
    assert(s[0] >= seal_kerf_rects("mullion_sash")[0][2] + MIN_SKIN || s[2] <= MULLION_W - seal_kerf_rects("mullion_sash")[0][2] - MIN_SKIN,
           str("fin stub starts past the mullion fin kerf ", s));
}
echo("mullion shoe rules ok");
```

- [ ] **Step 2: Run them to see them fail**

Run: `cd ~/diy-window && cad/box.sh test`
Expected: exit 1, with `WARNING: Can't open library '../parts/mullion_shoe.scad'` from `mullion_test.scad`.

- [ ] **Step 3: Write the shoe**

**Create** `cad/parts/mullion_shoe.scad`:
```openscad
// cad/parts/mullion_shoe.scad
include <../generated/dims.scad>
use <../profile.scad>
use <../lib/segment.scad>
use <../lib/emboss.scad>
use <../lib/mullion.scad>
use <jamb_node.scad>
use <transom_shoe.scad>

EPS = 0.01;

function node_z(r, e) = [r[0] - e, r[2] - e];

function shoe_node_z(profile, head) =
    profile == "mullion_glazing" ? [node_z(glazing_kerf_rect("sill"), FRAME_BODY)]
  : let(n = head ? "sash_rebate" : "transom", e = sash_side_e(n))
    concat([for (r = seal_kerf_rects(n)) node_z(r, e)], head ? [node_z(mag_rect(n), e)] : []);

function shoe_features(profile, head) =
    let(k = kerf_rects(profile))
    profile == "mullion_glazing" ? [k]
  : concat([[k[0], k[2]], [k[1], k[3]]], head ? [mag_rects(profile)] : []);

function mshoe_turn(r, z) =
    r[0] > MULLION_W / 2 ? [r[0], r[1], MULLION_W + EPS, r[3], z[0], z[1]] : [-EPS, r[1], r[2], r[3], z[0], z[1]];

function mshoe_turns(profile, head = false) =
    let(z = shoe_node_z(profile, head), f = shoe_features(profile, head))
    [for (i = [0 : len(z) - 1]) for (r = f[i]) mshoe_turn(r, z[i])];

function mshoe_fin_stubs(profile) =
    profile != "mullion_sash" ? []
  : let(mh = MULLION_W / 2 + MULLION_HALF_BODY)
    [[mh + FIN_L - EPS, FIN_Y0, MULLION_W, FIN_Y1, 0, FIN_L], [0, FIN_Y0, MULLION_W - mh - FIN_L + EPS, FIN_Y1, 0, FIN_L]];

function mshoe_seam_groove(profile) =
    let(x0 = profile == "mullion_glazing" ? kerf_rects(profile)[0][2] + MIN_SKIN : mullion_leg() + MIN_SKIN)
    [x0, STOP_T / 2 - CORD_D / 2, MULLION_W - x0, STOP_T / 2 + CORD_D / 2, -EPS, CORD_D / 2];

function mshoe_screw_z() = SHOE_WALL + (mullion_leg() - SHOE_WALL) / 2;

module mullion_shoe(profile, code, head = false) {
    assert(is_mullion(profile), str(code, ": ", profile, " is not a mullion profile"));
    assert(!head || profile == "mullion_sash", str(code, ": only the upper mullion meets the head"));
    L = mullion_leg();
    c = MULLION_W / 2;
    d = mdove();
    difference() {
        union() {
            linear_extrude(L) profile(profile);
            linear_extrude(SHOE_WALL) profile_solid(profile, false);
            for (b = mshoe_fin_stubs(profile)) box(b);
            multmatrix([[0, 1, 0, c], [0, 0, 1, STOP_T + DOVE_CLEAR], [1, 0, 0, 0]])
                linear_extrude(DEPTH - STOP_T - DOVE_CLEAR) dove_tongue2d(d[0], d[1]);
        }
        for (t = mshoe_turns(profile, head)) box(t);
        translate([0, 0, L - CORD_D / 2]) end_groove(profile);
        for (q = mlock_uv()) translate([c + q[1], 0, q[0]]) lock_hole();
        box(mshoe_seam_groove(profile));
        tube_screw(profile, mshoe_screw_z());
        engrave(code, label_at(profile), L / 2);
    }
}
```

How the turns work:
- `shoe_node_z` reads each node feature's distance from the node's body face. `shoe_features` pairs it with the mullion's feature on both sides.
- `mshoe_turn` cuts from the mullion feature out to the shoe's side edge, where the run's segment ends. These are the transom shoe's `shoe_turn` boxes, mirrored for the second side.
- The fin stubs fill the 10 mm between the mullion fin and the shoe edge for the node fin's 8 mm, as the transom shoe's `shoe_fin_stub` does.

- [ ] **Step 4: Run the asserts to see them pass**

Run: `cd ~/diy-window && cad/box.sh test`
Expected: `8 test files passed`.

- [ ] **Step 5: Render the shoes and look at them**

Run: `cd ~/diy-window && cad/box.sh render home-1800x1500-2bay MSL MST MSH | tail -1`
Expected: `3/3 parts ok`.

Run:
```bash
cd ~/diy-window && cat > cad/tests/zz_view.scad <<'SCAD'
include <../generated/dims.scad>
use <../parts/mullion_shoe.scad>
sel = 0;
color("Peru") {
    if (sel == 0) mullion_shoe("mullion_glazing", "MSL");
    if (sel == 1) mullion_shoe("mullion_sash", "MST");
    if (sel == 2) mullion_shoe("mullion_sash", "MSH", head = true);
}
SCAD
view() { PARAMS=home-1800x1500-2bay cad/box.sh png tests/zz_view.scad ~/diy-window/.bays-review/$1.png -Dsel=$2 --projection=o $3; }
view msl 0 "--camera=0,0,0,130,0,-30,300 --viewall --autocenter" &
view mst 1 "--camera=0,0,0,130,0,-30,300 --viewall --autocenter" &
view msh 2 "--camera=0,0,0,130,0,-30,300 --viewall --autocenter" &
view msl-label 0 "--camera=-120,-10,40,18,25,9" &
view mst-room 1 "--camera=-40,160,-60,35,40,9" &
view msh-room 2 "--camera=-40,160,-60,35,40,9" &
wait; rm cad/tests/zz_view.scad
```

Read the PNGs and check:
- **The tongue.** A trapezoid tongue runs from 8.3 mm off the outside face to the inside face, with half-moon lock holes at its room-side end.
- **`MSL`.** The stop leg is across the full width at the outside face, with the seam groove line along its end face. The glazing-kerf notches are on both sides.
- **`MST` and `MSH`.**
  - Fin stubs at both outer edges, at fin height, with the kerf slot through them.
  - Inner-stop kerf notches, and the magnet-channel steps at both top corners.
- **`mst-room.png` and `msh-room.png`** (the room face, with the tube screw and the two half-moon lock holes):
  - On `MST`, each magnet channel runs the full 18 mm, with a 3 mm lip outside it.
  - On `MSH`, that lip is cut away from 2 mm to 15 mm off the end face, leaving two small corner blocks on each side. This is the head channel turning into the mullion channel.
- **`msl-label.png`.** "MSL" reads left to right on the left body face.

- [ ] **Step 6: Checkpoint**

Run: `cd ~/diy-window/tools && python3 -m unittest discover -p 'test_*.py' 2>&1 | grep -E '^(Ran|OK|FAILED)'`
Expected: `Ran 261 tests`, `OK`.

---
### Task 7: Render the two-bay reference window and measure the new envelopes

`bed_fit` needs an envelope for every part, and `tools/part_envelopes.json` is measured from the reference renders. The 2-bay window becomes the third reference. `testCommittedTableMatchesTheReferenceRenders` (unchanged) then requires all 43 of its STLs to be on disk, so render the whole window.

**Files:**
- Modify: `tools/part_envelopes.py` (`REFERENCES`)
- Modify: `tools/part_envelopes.json` (regenerated)
- Create: `cad/stl/home-1800x1500-2bay/*.stl` (43 files)
- Test: `tools/test_generate.py` (append `BayEnvelopeTest`), `tools/test_part_envelopes.py` (append `TwoBayEnvelopeTest`)

- [ ] **Step 1: Write the failing tests**

**Append** to `tools/test_generate.py`:
```python
class BayEnvelopeTest(unittest.TestCase):
    def testBedFitCoversTheNewParts(self):
        x = lay("home-1800x1500-2bay.json")
        self.assertEqual(generate.bed_fit(x, generate.parts(x))["msg"], "every part fits the 256 x 256 x 256 mm bed")
        small = window.layout(dict(load("home-1800x1500-2bay.json"), bed=[180, 180, 180]))
        self.assertTrue(generate.bed_fit(small, generate.parts(small))["ok"])

    def testEnvelopeTableHasEveryMullionPart(self):
        for pid, dims in (("SN", 3), ("HN", 3), ("TX", 3), ("MSL", 3), ("MST", 3), ("MSH", 3), ("ML", 2), ("MU", 2)):
            self.assertEqual(len(generate.ENVELOPES[pid]), dims, pid)
```

**Append** to `tools/test_part_envelopes.py`:
```python
class TwoBayEnvelopeTest(unittest.TestCase):
    def testTheTwoBayWindowIsAReference(self):
        self.assertIn("home-1800x1500-2bay", part_envelopes.REFERENCES)

    def testMullionPartsComeFromItsRenders(self):
        got = part_envelopes.collect(window.ROOT, ["home-1800x1500-2bay"], {"SN", "TX", "MSL", "ML"})
        self.assertEqual(got, {"ML": [63.0, 70.0], "MSL": [21.7, 63.0, 70.0], "SN": [40.0, 63.0, 70.0], "TX": [34.0, 63.0, 70.0]})
```

- [ ] **Step 2: Run them to see them fail**

Run: `cd ~/diy-window/tools && python3 -m unittest test_generate.BayEnvelopeTest test_part_envelopes.TwoBayEnvelopeTest 2>&1 | tail -3`
Expected: `FAILED (failures=2, errors=2)`. The errors are `KeyError: 'SN'` and a missing `ML.stl`. The failures are the `bed_fit` message (`SN (no envelope)`) and `REFERENCES`.

- [ ] **Step 3: Render every part of the two-bay window**

Run: `cd ~/diy-window && cad/box.sh render home-1800x1500-2bay | tail -1`
Expected: `43/43 parts ok`, in about 20 s. `check_stl` has passed every STL: it is closed, a single body, inside the bed, and the right length.

- [ ] **Step 4: Make it a reference and re-measure**

**Replace** in `tools/part_envelopes.py`:
```python
REFERENCES = ("home-1800x1500", "bench-600")
```
**with:**
```python
REFERENCES = ("home-1800x1500", "bench-600", "home-1800x1500-2bay")
```

Run: `cd ~/diy-window && python3 tools/part_envelopes.py`
Expected: `part_envelopes.json: 52 measured from home-1800x1500, bench-600, home-1800x1500-2bay, 56 in all`. The table gains exactly these eight lines, and nothing else changes:
```
  "HN": [40.0, 63.0, 70.0],
  "ML": [63.0, 70.0],
  "MSH": [21.7, 63.0, 70.0],
  "MSL": [21.7, 63.0, 70.0],
  "MST": [21.7, 63.0, 70.0],
  "MU": [63.0, 70.0],
  "SN": [40.0, 63.0, 70.0],
  "TX": [34.0, 63.0, 70.0],
```
(The shoes are 18 mm plus the 3.7 mm tongue. `TX` is the 34 mm transom body.)

- [ ] **Step 5: Run the tests to see them pass**

Run: `cd ~/diy-window/tools && python3 -m unittest test_generate test_part_envelopes 2>&1 | tail -3`
Expected: `OK` (86 tests).

- [ ] **Step 6: Checkpoint**

Run: `cd ~/diy-window/tools && python3 -m unittest discover -p 'test_*.py' 2>&1 | grep -E '^(Ran|OK|FAILED)'`
Expected: `Ran 265 tests`, `OK`.

Then run `cd ~/diy-window && python3 tools/generate.py params/bench-600.json > /dev/null` and the **compatibility check** (Task 0). Expected: `BYTE-IDENTICAL`.

---

### Task 8: Hardware per bay (`bom/build_bom.py`) and the reference BOM

**What scales with the bays:**
- the stay pairs and their arm screws;
- the cams, keepers and inserts (through the part counts);
- the seal loops, glazing gaskets, screen strips, mesh and spline;
- the glass and the acrylic sandwich extras.

**What the mullions add:**
- steel tube and tek screws for `TX`, the shoes and the `ML`/`MU` segments;
- two lock screws per mullion shoe;
- 3 mm cord for each shoe seam;
- two fixings in each `SN` and `HN`, and the `SN` fixings are bedded;
- a packer under each `SN`;
- 8g × 16 tek screws for the stay tracks on the mullions.

**What stays the same for one bay.** The new lines and wordings only appear from two bays up, so a one-bay BOM is unchanged. The `.md` gets a "Bays" note with the mullion centre lines.

**Files:**
- Modify: `bom/build_bom.py`
- Create: `bom/home-1800x1500-2bay.csv`, `.md`, `-cutlist.csv`, `-glass.csv`, `-parts.csv`
- Test: `tools/test_bom.py` (append `TwoBayBomTest`, `OneBayBomTest`, `TwoBayWriteTest`)

- [ ] **Step 1: Write the failing tests**

**Append** to `tools/test_bom.py`:
```python
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
```

- [ ] **Step 2: Run them to see them fail**

Run: `cd ~/diy-window/tools && python3 -m unittest test_bom.TwoBayBomTest test_bom.OneBayBomTest test_bom.TwoBayWriteTest 2>&1 | tail -3`
Expected: `FAILED (failures=10)`. The 2-bay quantities are still one bay's, and the new lines and the Bays note are missing. Four tests already pass, because the part counts and the layout already scale: `testExplicitOneBayIsTheSameBom`, `testMullionLinesOnlyWithBays`, `testInsertsAndCamScrewsScaleWithTheBays` and `testSteelForTheMullions`.

- [ ] **Step 3: Constants**

**Replace** in `bom/build_bom.py`:
```python
TRANSOM_PARTS = {"T", "TE", "TSL", "TSR"}
```
**with:**
```python
TRANSOM_PARTS = {"T", "TE", "TSL", "TSR"}
MULLION_STEEL = {"TX", "MSL", "MST", "MSH", "ML", "MU"}
MULLION_SHOES = {"MSL", "MST", "MSH"}
```

**Replace** in `bom/build_bom.py`:
```python
SCREEN_ONLY = "screen-only"
```
**with:**
```python
SCREEN_ONLY = "screen-only"
MULLION_ONLY = "mullion-only"
```

**Replace** in `bom/build_bom.py`:
```python
    w, d = {"transom": (2 * D["TRANSOM_HALF_BODY"], D["DEPTH"]),
```
**with:**
```python
    w, d = {"transom": (2 * D["TRANSOM_HALF_BODY"], D["DEPTH"]),
            "mullion_glazing": (2 * D["MULLION_HALF_BODY"], D["DEPTH"]),
            "mullion_sash": (2 * D["MULLION_HALF_BODY"], D["DEPTH"]),
```

- [ ] **Step 4: Fixings, sealant and the tube screws**

**Replace** in `bom/build_bom.py`:
```python
    total = lambda ids: sum(q.get(i, 0) for i in ids)
    scr_w, scr_h = lay["screen"]
```
**with:**
```python
    total = lambda ids: sum(q.get(i, 0) for i in ids)
    bays = lay["bays"]
    scr_w, scr_h = lay["screen"]
```

**Replace** in `bom/build_bom.py`:
```python
    fixings = total(PERIMETER_SEGMENTS) + 2 * total(PERIMETER_CORNERS) + 2 * q["JN"]
    bedded = total({"S", "SW", "JL"}) + 2 * total({"CSL", "CSR"}) + 2 * q["JN"]
```
**with:**
```python
    fixings = total(PERIMETER_SEGMENTS) + 2 * total(PERIMETER_CORNERS) + 2 * total({"JN", "SN", "HN"})
    bedded = total({"S", "SW", "JL"}) + 2 * total({"CSL", "CSR"}) + 2 * total({"JN", "SN"})
```

**Replace** in `bom/build_bom.py`:
```python
                  + BED_ML * bedded + SHOE_FACE_ML * (q["TSL"] + q["TSR"]))
    loop_extra = 8 * (D["SASH_GAP"] - D["FIN_L"] / 2 + D["LIP_L"] / 2)
```
**with:**
```python
                  + BED_ML * bedded + SHOE_FACE_ML * total({"TSL", "TSR"} | MULLION_SHOES))
    loop_extra = 8 * (D["SASH_GAP"] - D["FIN_L"] / 2 + D["LIP_L"] / 2)
    steel = "steel transom tube: T, TE, shoes" if bays == 1 else "steel transom and mullion tubes: T, TE, TX, ML, MU, shoes"
```

**Replace** in `bom/build_bom.py`:
```python
         total(FRAME_SEGMENTS - TRANSOM_PARTS) + 2 * total(FRAME_CORNERS) + q["JN"], "pcs"),
        ("Fixings", "Tek screw 8g x 25, 410 stainless, countersunk (steel transom tube: T, TE, shoes)",
         total(TRANSOM_PARTS), "pcs"),
```
**with:**
```python
         total(FRAME_SEGMENTS - TRANSOM_PARTS) + 2 * total(FRAME_CORNERS) + total({"JN", "SN", "HN"}), "pcs"),
        ("Fixings", f"Tek screw 8g x 25, 410 stainless, countersunk ({steel})",
         total(TRANSOM_PARTS | MULLION_STEEL), "pcs"),
```

**Replace** in `bom/build_bom.py`:
```python
        ("Fixings", "M4 x 16 countersunk machine screw (transom lock screws)", 4, "pcs"),
```
**with:**
```python
        ("Fixings", f"M4 x 16 countersunk machine screw ({'transom' if bays == 1 else 'transom and mullion'} lock screws)",
         2 * total({"TSL", "TSR"} | MULLION_SHOES), "pcs"),
```

**Replace** in `bom/build_bom.py`:
```python
        ("Fixings", "Plastic window packers, assorted 1-10 mm (one stack per position)", fixings + q["GW"] + 4, "pcs"),
```
**with:**
```python
        ("Fixings", "Plastic window packers, assorted 1-10 mm (one stack per position)",
         fixings + q["GW"] + 4 + q.get("SN", 0), "pcs"),
```

- [ ] **Step 5: Stays, seals, screen and glass per bay**

**Replace** in `bom/build_bom.py`:
```python
                     f"track/arm width <= {D['STAY_W']:g} mm (check rating >= {lay['sash_kg']} kg)", 1, "pair"),
        ("Hardware", "Friction-stay screw 8g x 25 stainless, countersunk (tracks to upper jambs; match the stay's holes)",
         2 * STAY_TRACK_SCREWS, "pcs"),
        ("Hardware", "Friction-stay screw 8g x 16 stainless, countersunk (arms to sash sides; match the stay's holes)",
         2 * STAY_ARM_SCREWS, "pcs"),
        ("Seals", "EPDM bulb kerf seal, 3 mm kerf (outer + inner loop round the sash opening)",
         m((2 * perim(lay["sash"]) + loop_extra) * SEAL_ALLOWANCE), "m"),
        ("Seals", "EPDM glazing wedge gasket, 3 mm", m(2 * (perim(lay["glass"]["fixed"]) + perim(lay["glass"]["sash"]))), "m"),
```
**with:**
```python
                     f"track/arm width <= {D['STAY_W']:g} mm (check rating >= {lay['sash_kg']} kg)", bays, "pair"),
        ("Hardware", "Friction-stay screw 8g x 25 stainless, countersunk (tracks to upper jambs; match the stay's holes)",
         2 * STAY_TRACK_SCREWS, "pcs"),
        ("Hardware", "Tek screw 8g x 16, 410 stainless, countersunk (friction-stay tracks to upper mullions; match the stay's holes)",
         2 * (bays - 1) * STAY_TRACK_SCREWS, "pcs", MULLION_ONLY),
        ("Hardware", "Friction-stay screw 8g x 16 stainless, countersunk (arms to sash sides; match the stay's holes)",
         2 * STAY_ARM_SCREWS * bays, "pcs"),
        ("Seals", f"EPDM bulb kerf seal, 3 mm kerf (outer + inner loop round {'the sash opening' if bays == 1 else 'each sash opening'})",
         m((2 * perim(lay["sash"]) + loop_extra) * SEAL_ALLOWANCE * bays), "m"),
        ("Seals", "EPDM glazing wedge gasket, 3 mm",
         m(2 * (perim(lay["glass"]["fixed"]) + perim(lay["glass"]["sash"])) * bays), "m"),
```

**Replace** in `bom/build_bom.py`:
```python
        ("Seals", "Closed-cell foam cord, 3 mm (transom shoe seams)", m(2 * D["TRANSOM_W"]), "m"),
```
**with:**
```python
        ("Seals", f"Closed-cell foam cord, 3 mm ({'transom shoe' if bays == 1 else 'transom and mullion shoe'} seams)",
         m(2 * D["TRANSOM_W"] + 4 * (bays - 1) * D["MULLION_W"]), "m"),
```

**Replace** in `bom/build_bom.py`:
```python
        ("Screen", "Flexible magnetic strip A, 12.7 mm, adhesive-backed (screen back channel)", m(perim(lay["screen"])), "m",
         SCREEN_ONLY),
        ("Screen", "Flexible magnetic strip B, 12.7 mm, adhesive-backed, matched to A, or adhesive steel strip "
                   "(frame magnet channel)", m(perim(lay["screen"])), "m", SCREEN_ONLY),
        ("Screen", "Fibreglass insect mesh", round(scr_w * scr_h / 1e6 * 1.1, 2), "m2", SCREEN_ONLY),
        ("Screen", "Screen spline, 4 mm", m(perim(lay["screen"])), "m", SCREEN_ONLY),
```
**with:**
```python
        ("Screen", "Flexible magnetic strip A, 12.7 mm, adhesive-backed (screen back channel)",
         m(perim(lay["screen"]) * bays), "m", SCREEN_ONLY),
        ("Screen", "Flexible magnetic strip B, 12.7 mm, adhesive-backed, matched to A, or adhesive steel strip "
                   "(frame magnet channel)", m(perim(lay["screen"]) * bays), "m", SCREEN_ONLY),
        ("Screen", "Fibreglass insect mesh", round(scr_w * scr_h / 1e6 * 1.1 * bays, 2), "m2", SCREEN_ONLY),
        ("Screen", "Screen spline, 4 mm", m(perim(lay["screen"]) * bays), "m", SCREEN_ONLY),
```

**Replace** in `bom/build_bom.py`:
```python
    if not lay["has_screen"]:
        items = [it for it in items if SCREEN_ONLY not in it[4:]]
```
**with:**
```python
    if not lay["has_screen"]:
        items = [it for it in items if SCREEN_ONLY not in it[4:]]
    if bays == 1:
        items = [it for it in items if MULLION_ONLY not in it[4:]]
```

**Replace** in `bom/build_bom.py`:
```python
            items.append(("Glazing", f"Acrylic 4 mm, {gw} x {gh} ({pane} pane)", 2, "pcs"))
        else:
            items.append(("Glazing", f"{generate.GLASS_SPEC[g]}, {gw} x {gh} ({pane} pane)", 1, "pcs"))
    if lay["params"]["glazing"] == "acrylic":
        items.append(("Glazing", "Silica gel desiccant beads", 100, "g"))
        items.append(("Glazing", "Butyl glazing tape, 3 mm (acrylic sandwich edge)", m(2 * sum(perim(v) for v in lay["glass"].values())), "m"))
```
**with:**
```python
            items.append(("Glazing", f"Acrylic 4 mm, {gw} x {gh} ({pane} pane)", 2 * bays, "pcs"))
        else:
            items.append(("Glazing", f"{generate.GLASS_SPEC[g]}, {gw} x {gh} ({pane} pane)", bays, "pcs"))
    if lay["params"]["glazing"] == "acrylic":
        items.append(("Glazing", "Silica gel desiccant beads", 100 * bays, "g"))
        items.append(("Glazing", "Butyl glazing tape, 3 mm (acrylic sandwich edge)",
                      m(2 * sum(perim(v) for v in lay["glass"].values()) * bays), "m"))
```

- [ ] **Step 6: The `.md` glass table and the "Bays" note**

**Replace** in `bom/build_bom.py`:
```python
    lines += [f"| {pane} | {lay['params']['glazing']} | {gw} | {gh} | 1 |" for pane, (gw, gh) in lay["glass"].items()]
```
**with:**
```python
    lines += [f"| {pane} | {lay['params']['glazing']} | {gw} | {gh} | {lay['bays']} |" for pane, (gw, gh) in lay["glass"].items()]
    if lay["bays"] > 1:
        centres = ", ".join(f"{c:g}" for c in (round(c, 1) for c in lay["mullions"]))
        lines += ["", "## Bays", "", f"{lay['bays']} bays, {round(lay['pitch'], 1):g} mm apart. Mullion centre lines, "
                  f"from the frame's left outer edge as seen from outside: {centres} mm."]
```

- [ ] **Step 7: Run the tests to see them pass**

Run: `cd ~/diy-window/tools && python3 -m unittest test_bom 2>&1 | tail -3`
Expected: `OK` (58 tests).

- [ ] **Step 8: Build the reference BOM and read its numbers**

Run: `cd ~/diy-window && python3 bom/build_bom.py home-1800x1500-2bay && grep -E 'Prints:|pair|Tube steel|Filament|mullion_|\| (fixed|sash) \||mm apart' bom/home-1800x1500-2bay.md`
Expected:
- `bom/home-1800x1500-2bay.csv, .md, -cutlist.csv, -glass.csv, -parts.csv: 37 lines`, with no STLs missing;
- `Prints: 226 parts in 43 types`;
- 2 stay pairs `(check rating >= 7.6 kg)`;
- `Tube steel40x20 ... | 3.05 | m`;
- `PETG (interior) | 4.81 | kg` and `(exterior, tier 3) | 19.19 | kg`;
- the cut list rows `| mullion_lower | steel40x20 | 876.0 | 1 |` and `| mullion_upper | steel40x20 | 478.0 | 1 |`;
- glass `| fixed | igu | 829 | 878 | 2 |` and `| sash | igu | 737 | 388 | 2 |`;
- the "Bays" note: `892 mm`.

- [ ] **Step 9: Checkpoint**

Run: `cd ~/diy-window/tools && python3 -m unittest discover -p 'test_*.py' 2>&1 | grep -E '^(Ran|OK|FAILED)'`
Expected: `Ran 279 tests`, `OK`.

Then run the **compatibility check** (Task 0). Expected: `BYTE-IDENTICAL`.

---
### Task 9: Assembly with bays, and the tee sections by eye (`cad/assembly.scad`)

**The assembly.** `cad/assembly.scad` places everything from `layout.scad`:
- the sill, head and transom runs between nodes;
- every node, shoe and mullion run;
- a sash and both panes per bay.

`BAYS` and `MULLIONS` only exist in `layout.scad` from two bays up, so the file reads them through `is_undef()`, which OpenSCAD allows without a warning.

**The cut options.**
- `cut_x` moves the vertical section, `plan_z` makes a horizontal one, and `cut_t` sets the slab thickness.
- In a cut, each group gets its own strong colour: frame grey, mullion joints orange, sashes light blue, glass blue.
- The full view keeps today's colours.

**Files:**
- Modify: `cad/assembly.scad` (whole file)
- Create: `docs/img/assembly-home-2bay.png`

- [ ] **Step 1: Rewrite the assembly**

**Create** `cad/assembly.scad`:
```openscad
// cad/assembly.scad
include <generated/dims.scad>
include <generated/layout.scad>
use <profile.scad>
use <parts/corner_block.scad>
use <parts/jamb_node.scad>
use <parts/transom_shoe.scad>
use <parts/frame_node.scad>
use <parts/cross_node.scad>
use <parts/mullion_shoe.scad>

section = false;
cut_x = W / 2;
plan_z = -1;
cut_t = 2;
NB = is_undef(BAYS) ? 1 : BAYS;
MX = is_undef(MULLIONS) ? [] : MULLIONS;

module run(name, len, m) { multmatrix(m) linear_extrude(len) profile(name); }

function run_x0(i) = i == 0 ? FRAME_W : MX[i - 1] + MULLION_W / 2;
function run_x1(i) = i == NB - 1 ? W - FRAME_W : MX[i] - MULLION_W / 2;
function sash_x(i) = i == 0 ? FRAME_BODY + SASH_GAP : MX[i - 1] + MULLION_HALF_BODY + SASH_GAP;
function glass_x(i) = i == 0 ? GLASS_EDGE : MX[i - 1] + TRANSOM_GLASS;

CUT = section || plan_z >= 0;
COLOURS = CUT ? ["SlateGray", "DarkOrange", "SkyBlue", "SteelBlue"] : ["WhiteSmoke", "WhiteSmoke", "Gainsboro", "LightBlue"];

module clip() {
    if (plan_z >= 0) intersection() { children(); translate([-50, -50, plan_z - cut_t / 2]) cube([W + 100, DEPTH + 100, cut_t]); }
    else if (section) intersection() { children(); translate([cut_x - cut_t / 2, -50, -50]) cube([cut_t, DEPTH + 100, H + 100]); }
    else children();
}

module mullion_runs(xm, tb) {
    x0 = xm - MULLION_W / 2;
    run("mullion_glazing", tb - FRAME_W, [[1, 0, 0, x0], [0, 1, 0, 0], [0, 0, 1, FRAME_W]]);
    run("mullion_sash", H - FRAME_W - (tb + TRANSOM_W), [[1, 0, 0, x0], [0, 1, 0, 0], [0, 0, 1, tb + TRANSOM_W]]);
}

module mullion_joints(xm, tb) {
    x0 = xm - MULLION_W / 2;
    x1 = xm + MULLION_W / 2;
    multmatrix([[0, 0, 1, x0], [0, 1, 0, 0], [1, 0, 0, 0]]) frame_node("sill", "SN");
    multmatrix([[0, 0, 1, x0], [0, 1, 0, 0], [-1, 0, 0, H]]) frame_node("sash_rebate", "HN");
    multmatrix([[0, 0, 1, x0], [0, 1, 0, 0], [1, 0, 0, tb]]) cross_node("TX");
    multmatrix([[1, 0, 0, x0], [0, 1, 0, 0], [0, 0, 1, FRAME_BODY]]) mullion_shoe("mullion_glazing", "MSL");
    multmatrix([[-1, 0, 0, x1], [0, 1, 0, 0], [0, 0, -1, tb + TRANSOM_W / 2 - TRANSOM_HALF_BODY]]) mullion_shoe("mullion_glazing", "MSL");
    multmatrix([[1, 0, 0, x0], [0, 1, 0, 0], [0, 0, 1, tb + TRANSOM_W / 2 + TRANSOM_HALF_BODY]]) mullion_shoe("mullion_sash", "MST");
    multmatrix([[-1, 0, 0, x1], [0, 1, 0, 0], [0, 0, -1, H - FRAME_BODY]]) mullion_shoe("mullion_sash", "MSH", head = true);
}

module frame() {
    F = FRAME_W;
    tb = TRANSOM_C - TRANSOM_W / 2;
    for (i = [0 : NB - 1]) {
        x0 = run_x0(i);
        len = run_x1(i) - x0;
        run("sill", len, [[0, 0, 1, x0], [0, 1, 0, 0], [1, 0, 0, 0]]);
        run("sash_rebate", len, [[0, 0, 1, x0], [0, 1, 0, 0], [-1, 0, 0, H]]);
        run("transom", len, [[0, 0, 1, x0], [0, 1, 0, 0], [1, 0, 0, tb]]);
    }
    for (xm = MX) mullion_runs(xm, tb);
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

module sash(x0) {
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
}

module pane(x, z, dims) { color(COLOURS[3], CUT ? 1 : 0.35) clip() translate([x, GLASS_Y0, z]) cube([dims[0], GLASS_T, dims[1]]); }

module window() {
    tb = TRANSOM_C - TRANSOM_W / 2;
    z0 = TRANSOM_C + TRANSOM_HALF_BODY + SASH_GAP;
    color(COLOURS[0]) clip() frame();
    color(COLOURS[1]) clip() for (xm = MX) mullion_joints(xm, tb);
    for (i = [0 : NB - 1]) {
        color(COLOURS[2]) clip() sash(sash_x(i));
        pane(sash_x(i) + SASH_GLASS, z0 + SASH_GLASS, SASH_GLASS_DIMS);
        pane(glass_x(i), GLASS_EDGE, FIXED_GLASS);
    }
}

window();
```

- [ ] **Step 2: The one-bay views still render**

Run:
```bash
cd ~/diy-window && mkdir -p .bays-review
PARAMS=home-1800x1500 cad/box.sh png assembly.scad ~/diy-window/.bays-review/one-bay.png --camera=0,0,0,70,0,200,0 --viewall --autocenter
PARAMS=bench-600 cad/box.sh png assembly.scad ~/diy-window/.bays-review/bench.png --camera=0,0,0,70,0,200,0 --viewall --autocenter
```
Expected: both commands exit 0 with no `WARNING` (a missing `BAYS` would be a warning, and `box.sh` would fail). Read `one-bay.png` beside `docs/img/assembly-home.png`: the frame, transom and fixed pane match. The sash glass now shows as glass, not grey, because each pane has its own colour.

- [ ] **Step 3: The two-bay window, from outside and from the room**

Run:
```bash
cd ~/diy-window
PARAMS=home-1800x1500-2bay cad/box.sh png assembly.scad ~/diy-window/.bays-review/two-bay-front.png --camera=892,-2500,742,892,30,742 --projection=o --viewall &
PARAMS=home-1800x1500-2bay cad/box.sh png assembly.scad ~/diy-window/docs/img/assembly-home-2bay.png --camera=0,0,0,70,0,200,0 --viewall --autocenter &
wait
```
Read both. You should see two equal bays, each with an awning sash over a fixed pane, a mullion on the centre line from the sill to the head, and the transom running through.

- [ ] **Step 4: Horizontal sections through the mullions and every turn**

Run (each one is a 0.4 mm slab, looked at from above, with the outside face at the bottom of the image):
```bash
cd ~/diy-window
for z in 480 1200 47 917 961.5 967 1436; do
  PARAMS=home-1800x1500-2bay cad/box.sh png assembly.scad ~/diy-window/.bays-review/plan-$z.png -Dplan_z=$z -Dcut_t=0.4 \
    --camera=892,30,$(python3 -c "print($z + 400)"),892,31,$z --projection=o &
done; wait
```

Read each PNG and check:

| PNG | Height | Must show |
|---|---|---|
| `plan-480` | lower mullion | The `mullion_glazing` profile: the body with its tube pocket, a stop leg on each side with a glazing-kerf notch under the pane edge, and the bead keyways high up on both body faces. Both fixed panes run 15 mm onto the stop legs and stop 3 mm short of the body |
| `plan-1200` | upper mullion | The `mullion_sash` profile between two sashes: the fins with their kerfs at mid-depth, the inner stops at the top with kerfs and magnet steps, and a 13 mm gap from each body face to its sash. The sash flanges reach under the fin seals and the sash lips under the inner stops |
| `plan-47` | sill glazing kerf | The sill segments (grey) only show y 0–3: the kerf is cut above that. The MSL (orange) shows the same 0–3 mm strip from each side edge to its mullion kerf. One continuous glazing-gasket groove from the sill into each mullion kerf |
| `plan-917` | transom glazing kerf | The same as `plan-47`, under the transom, with the upper MSL turned end for end. Its label is now on the right-hand body face |
| `plan-961.5` | MST fin kerf | The transom segments show only the fin above its kerf (y 25–28). The MST shows the same strip from each edge to the mullion fin kerf (the fin stubs). Full fin material between the turn and the body |
| `plan-967` | MST inner-stop kerf | The transom inner stops and the MST edges show only y 59–63 (the kerf is cut below). The tube-screw notch is at the top centre |
| `plan-1436` | MSH, head | The head (grey) shows a thin strip at y 59–61 (inner-stop kerf below, magnet channel above), and the MSH edges show the same strip out to the mullion channels. The fin stubs line up with the head fin at y 20–28 |

- [ ] **Step 5: Vertical sections through the left leg zone of each tee**

Run (2 mm slabs at X = 867, i.e. 10 mm into the mullion, looked at from +x, with the outside face on the left):
```bash
cd ~/diy-window
for z in 45 941 1440; do
  PARAMS=home-1800x1500-2bay cad/box.sh png assembly.scad ~/diy-window/.bays-review/sec-$z.png -Dsection=true -Dcut_x=867 \
    --camera=1300,31,$z,867,31,$z --projection=o &
done; wait
```
Check:
- **`sec-45` (SN tee).**
  - The SN (orange, Z 0–40) has the sill tube pocket, the nose keyway on the outside face, a bead-keyway notch at its top face, and the SN fixing hole running up to its counterbore in the top face.
  - Above it, the MSL stop leg has the glazing-kerf turn notch at Z 45.5–48.5, and the ML stop leg (grey) carries on from Z 58.
  - The fixed pane starts 3 mm above the SN top.
- **`sec-941` (TX tee).**
  - The TX body (orange) has the transom pocket.
  - Below it is the MSL's stop leg with its glazing-kerf turn.
  - Above it, the MST fin has its kerf-turn notch, joining the MU fin and inner stop (grey).
  - The sash flange and lip (light blue) reach down to the transom.
  - The narrow step at the TX's inside face is the screen magnet channel.
- **`sec-1440` (HN tee).**
  - The HN has the head tube pocket and the HN fixing hole opening between the seals.
  - The MSH fin has its kerf-turn notch, above the MU fin and inner stop.

- [ ] **Step 6: Checkpoint**

Run: `cd ~/diy-window && cad/box.sh test && python3 tools/generate.py params/bench-600.json > /dev/null`
Expected: `8 test files passed`.

**Review gate (CAD tees):** stop here for a review of Tasks 4–9: the asserts in `cad/tests/mullion_test.scad`, the part PNGs from Tasks 5–6, and the section PNGs above, against the CAD rules in spec §8.2 and the Decisions table.

---
### Task 10: Front view and assembled view with mullions (`web/drawing.py`)

**`front()`** adds two `mullion` rects per mullion (below and above the transom), and draws the panes, sash and screen of every bay at that bay's own x. From two bays up it also adds:
- a `bay 799` dimension above the frame, with the bounds raised to hold it;
- two-line labels per pane (`fixed glass` / `829 x 878`), short enough for a 500 mm bay.

**`assembly()`** places:
- the segments of every run (offset by its start);
- every `ML`/`MU` segment;
- each bay's sash members and corners;
- every node and shoe, with the transforms `cad/assembly.scad` uses.

One bay gives the same lists, in the same order.

**Files:**
- Modify: `web/drawing.py`
- Test: `web/tests/test_drawing.py` (append `TwoBayFrontTest`, `TwoBayAssemblyTest`, `TwoBayPlacementTest`)

- [ ] **Step 1: Write the failing tests**

**Append** to `web/tests/test_drawing.py`:
```python
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
```

- [ ] **Step 2: Run them to see them fail**

Run: `cd ~/diy-window && python3 -m unittest discover -s web/tests -p 'test_drawing.py' 2>&1 | tail -3`
Expected: `FAILED (failures=6, errors=2)`:
- two `TwoBayPlacementTest` tests error with `KeyError: 'SN'` and `'MSL'`;
- the four front-view tests fail (no mullion rects, one glass rect, no `bay` dimension, short bounds);
- both assembly tests fail (no mullion instances, and only the first run's two `SW`);
- `testEveryInstanceStaysInsideTheFrameOutline` already passes.

- [ ] **Step 3: Bay helpers and the front view**

**Replace** in `web/drawing.py`:
```python
def rect(kind, x, y, w, h):
    return {"kind": kind, "x": x, "y": y, "w": w, "h": h}
```
**with:**
```python
def rect(kind, x, y, w, h):
    return {"kind": kind, "x": x, "y": y, "w": w, "h": h}


def bay_x(lay, i):
    return D["FRAME_W"] if i == 0 else lay["mullions"][i - 1] + D["MULLION_W"] / 2


def body_x(lay, i):
    return D["FRAME_BODY"] if i == 0 else lay["mullions"][i - 1] + D["MULLION_HALF_BODY"]


def glass_x(lay, i):
    return D["GLASS_EDGE"] if i == 0 else lay["mullions"][i - 1] + D["TRANSOM_GLASS"]
```

**Replace** in `web/drawing.py`:
```python
    sx, sy = D["FRAME_BODY"] + D["SASH_GAP"], tc + D["TRANSOM_HALF_BODY"] + D["SASH_GAP"]
```
**with:**
```python
    sy = tc + D["TRANSOM_HALF_BODY"] + D["SASH_GAP"]
```

**Replace** in `web/drawing.py`:
```python
    sgw, sgh = lay["glass"]["sash"]
    rects = [
```
**with:**
```python
    sgw, sgh = lay["glass"]["sash"]
    bays = lay["bays"]
    rects = [
```

**Replace** in `web/drawing.py`:
```python
        rect("transom", F, tb, w - 2 * F, T),
        rect("glass", D["GLASS_EDGE"], D["GLASS_EDGE"], fgw, fgh),
        rect("sash", sx, sy, sw, sh),
        rect("sash-glass", sx + D["SASH_GLASS"], sy + D["SASH_GLASS"], sgw, sgh),
    ]
    if lay["has_screen"]:
        scw, sch = lay["screen"]
        top = h - D["FRAME_BODY"] + D["SCREEN_OVERLAP"]
        rects.append(rect("screen", D["FRAME_BODY"] - D["SCREEN_OVERLAP"], top - sch, scw, sch))
```
**with:**
```python
        rect("transom", F, tb, w - 2 * F, T),
    ]
    for c in lay["mullions"]:
        rects += [rect("mullion", c - D["MULLION_W"] / 2, F, D["MULLION_W"], tb - F),
                  rect("mullion", c - D["MULLION_W"] / 2, tb + T, D["MULLION_W"], h - F - tb - T)]
    for i in range(bays):
        x = body_x(lay, i) + D["SASH_GAP"]
        rects += [rect("glass", glass_x(lay, i), D["GLASS_EDGE"], fgw, fgh), rect("sash", x, sy, sw, sh),
                  rect("sash-glass", x + D["SASH_GLASS"], sy + D["SASH_GLASS"], sgw, sgh)]
    if lay["has_screen"]:
        scw, sch = lay["screen"]
        top = h - D["FRAME_BODY"] + D["SCREEN_OVERLAP"]
        rects += [rect("screen", body_x(lay, i) - D["SCREEN_OVERLAP"], top - sch, scw, sch) for i in range(bays)]
```

**Replace** in `web/drawing.py`:
```python
    margin = step * 1.5
    bounds = [left - step - margin, -g - 2 * step - margin, right + step + margin, h + g + margin]
```
**with:**
```python
    margin = step * 1.5
    top_dim = 0
    if bays > 1:
        run = lay["bay_w"]
        dims.append({"axis": "x", "a": F, "b": F + run, "from": h, "at": h + g + step, "text": f"bay {fmt(round(run, 1))}"})
        labels = []
        for i in range(bays):
            cx = bay_x(lay, i) + run / 2
            labels += [{"x": cx, "y": (F + tb) / 2 + step * 0.3, "text": "fixed glass"},
                       {"x": cx, "y": (F + tb) / 2 - step * 0.3, "text": f"{fgw} x {fgh}"},
                       {"x": cx, "y": sy + sh / 2 + step * 0.3, "text": "sash glass"},
                       {"x": cx, "y": sy + sh / 2 - step * 0.3, "text": f"{sgw} x {sgh}"}]
        top_dim = step
    bounds = [left - step - margin, -g - 2 * step - margin, right + step + margin, h + g + top_dim + margin]
```

- [ ] **Step 4: The assembled view**

**Replace** in `web/drawing.py`:
```python
    sx, sy = D["FRAME_BODY"] + D["SASH_GAP"], lay["transom_c"] + D["TRANSOM_HALF_BODY"] + D["SASH_GAP"]
    sw, sh = lay["sash"]
    m = {x["name"]: x for x in lay["members"]}
    runs = [
        ("sill", [[0, 0, 1, F], [0, 1, 0, 0], [1, 0, 0, 0]], "SW", "S"),
        ("head", [[0, 0, 1, F], [0, 1, 0, 0], [-1, 0, 0, H]], "H", "H"),
        ("transom", [[0, 0, 1, F], [0, 1, 0, 0], [1, 0, 0, tb]], "TE", "T"),
        ("jamb_lower", [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, F]], "JL", "JL"),
        ("jamb_lower", [[-1, 0, 0, W], [0, 1, 0, 0], [0, 0, 1, F]], "JL", "JL"),
        ("jamb_upper", [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, tb + TW]], "JU", "JU"),
        ("jamb_upper", [[-1, 0, 0, W], [0, 1, 0, 0], [0, 0, 1, tb + TW]], "JU", "JU"),
        ("sash_horizontal", [[0, 0, 1, sx + S], [0, 1, 0, 0], [1, 0, 0, sy]], "SBE", "SB"),
        ("sash_horizontal", [[0, 0, 1, sx + S], [0, 1, 0, 0], [-1, 0, 0, sy + sh]], "SH", "SH"),
        ("sash_vertical", [[1, 0, 0, sx], [0, 1, 0, 0], [0, 0, 1, sy + S]], "SV", "SV"),
        ("sash_vertical", [[-1, 0, 0, sx + sw], [0, 1, 0, 0], [0, 0, 1, sy + S]], "SV", "SV"),
    ]
    out = []
    for name, rows, end_id, mid_id in runs:
        mem = m[name]
        for i in range(mem["n"]):
            pid = end_id if i in (0, mem["n"] - 1) else mid_id
            out.append({"id": pid, "m": flat(chain(run(rows), move(0, 0, mem["gap"] + i * (mem["seg"] + mem["gap"]))))})
```
**with:**
```python
    sy = lay["transom_c"] + D["TRANSOM_HALF_BODY"] + D["SASH_GAP"]
    sw, sh = lay["sash"]
    m = {x["name"]: x for x in lay["members"]}
    bays = range(lay["bays"])
    offsets = [bay_x(lay, i) - F for i in bays]
    runs = [
        ("sill", [[0, 0, 1, F], [0, 1, 0, 0], [1, 0, 0, 0]], "SW", "S", offsets),
        ("head", [[0, 0, 1, F], [0, 1, 0, 0], [-1, 0, 0, H]], "H", "H", offsets),
        ("transom", [[0, 0, 1, F], [0, 1, 0, 0], [1, 0, 0, tb]], "TE", "T", offsets),
        ("jamb_lower", [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, F]], "JL", "JL", [0]),
        ("jamb_lower", [[-1, 0, 0, W], [0, 1, 0, 0], [0, 0, 1, F]], "JL", "JL", [0]),
        ("jamb_upper", [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, tb + TW]], "JU", "JU", [0]),
        ("jamb_upper", [[-1, 0, 0, W], [0, 1, 0, 0], [0, 0, 1, tb + TW]], "JU", "JU", [0]),
    ]
    for c in lay["mullions"]:
        runs += [("mullion_lower", [[1, 0, 0, c - D["MULLION_W"] / 2], [0, 1, 0, 0], [0, 0, 1, F]], "ML", "ML", [0]),
                 ("mullion_upper", [[1, 0, 0, c - D["MULLION_W"] / 2], [0, 1, 0, 0], [0, 0, 1, tb + TW]], "MU", "MU", [0])]
    for i in bays:
        sx = body_x(lay, i) + D["SASH_GAP"]
        runs += [
            ("sash_horizontal", [[0, 0, 1, sx + S], [0, 1, 0, 0], [1, 0, 0, sy]], "SBE", "SB", [0]),
            ("sash_horizontal", [[0, 0, 1, sx + S], [0, 1, 0, 0], [-1, 0, 0, sy + sh]], "SH", "SH", [0]),
            ("sash_vertical", [[1, 0, 0, sx], [0, 1, 0, 0], [0, 0, 1, sy + S]], "SV", "SV", [0]),
            ("sash_vertical", [[-1, 0, 0, sx + sw], [0, 1, 0, 0], [0, 0, 1, sy + S]], "SV", "SV", [0]),
        ]
    out = []
    for name, rows, end_id, mid_id, offs in runs:
        mem = m[name]
        for off in offs:
            for i in range(mem["n"]):
                pid = end_id if i in (0, mem["n"] - 1) else mid_id
                out.append({"id": pid, "m": flat(chain(run(rows), move(0, 0, off + mem["gap"] + i * (mem["seg"] + mem["gap"]))))})
```

**Replace** in `web/drawing.py`:
```python
        ("TSL", chain(move(0, 0, tb), shoe)), ("TSR", chain(move(W, 0, tb), MX, shoe, shoe_flip)),
        ("CS", move(sx, 0, sy)), ("CS", chain(move(sx + sw, 0, sy), MX)),
        ("CS", chain(move(sx, 0, sy + sh), MZ)), ("CS", chain(move(sx + sw, 0, sy + sh), MX, MZ)),
    ]
```
**with:**
```python
        ("TSL", chain(move(0, 0, tb), shoe)), ("TSR", chain(move(W, 0, tb), MX, shoe, shoe_flip)),
    ]
    for i in bays:
        sx = body_x(lay, i) + D["SASH_GAP"]
        fixed += [("CS", move(sx, 0, sy)), ("CS", chain(move(sx + sw, 0, sy), MX)),
                  ("CS", chain(move(sx, 0, sy + sh), MZ)), ("CS", chain(move(sx + sw, 0, sy + sh), MX, MZ))]
    tl, th = TW / 2 - D["TRANSOM_HALF_BODY"], TW / 2 + D["TRANSOM_HALF_BODY"]
    for c in lay["mullions"]:
        x0, x1 = c - D["MULLION_W"] / 2, c + D["MULLION_W"] / 2
        fixed += [
            ("SN", run([[0, 0, 1, x0], [0, 1, 0, 0], [1, 0, 0, 0]])),
            ("HN", run([[0, 0, 1, x0], [0, 1, 0, 0], [-1, 0, 0, H]])),
            ("TX", run([[0, 0, 1, x0], [0, 1, 0, 0], [1, 0, 0, tb]])),
            ("MSL", move(x0, 0, D["FRAME_BODY"])),
            ("MSL", run([[-1, 0, 0, x1], [0, 1, 0, 0], [0, 0, -1, tb + tl]])),
            ("MST", move(x0, 0, tb + th)),
            ("MSH", run([[-1, 0, 0, x1], [0, 1, 0, 0], [0, 0, -1, H - D["FRAME_BODY"]]])),
        ]
```

- [ ] **Step 5: Run the tests to see them pass**

Run: `cd ~/diy-window && python3 -m unittest discover -s web/tests -p 'test_drawing.py' 2>&1 | tail -3`
Expected: `OK` (29 tests).

- [ ] **Step 6: Checkpoint**

Run: `cd ~/diy-window && python3 -m unittest discover -s web/tests -p 'test_*.py' 2>&1 | grep -E '^(Ran|OK|FAILED)'`
Expected: `Ran 132 tests`, `OK`.

---

### Task 11: `max_pane` and `bays` through the API (`web/api.py`, `web/server.py`)

**What changes.**
- `validate()` passes the two optional keys through when they are present, and checks them. `DEFAULTS` itself is unchanged, so a form with no limit, the saved params files and every existing test stay as they are.
- `error_field()` sends the generator's `max_pane:`/`bays` messages to those fields.
- The preview summary carries the bay figures, and the new parts get names.
- The 2-bay window becomes a protected reference.
- `/api/presets` returns the page's default sheet, 1200 × 900.

**Files:**
- Modify: `web/api.py`, `web/server.py`
- Test: `web/tests/test_api.py` (append `BaysValidateTest`, `BaysPreviewTest`), `web/tests/test_server.py` (append `BaysApiTest`)

- [ ] **Step 1: Write the failing tests**

**Append** to `web/tests/test_api.py`:
```python
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
```

**Append** to `web/tests/test_server.py`:
```python
class BaysApiTest(ServerCase):
    def testPresetsCarryThePageMaxPane(self):
        self.assertEqual(self.call("GET", "/api/presets")[1]["max_pane"], [1200, 900])

    def testPreviewWithAMaxPane(self):
        status, body = self.call("POST", "/api/preview", dict(BENCH, opening_w=1800, opening_h=1500, awning_h=450,
                                                              max_pane=[1200, 900]))
        self.assertEqual((status, body["ok"], body["layout"]["bays"]), (200, True, 2))

    def testRenderRefusesTooFewBays(self):
        status, body = self.call("POST", "/api/render", dict(BENCH, opening_w=1800, opening_h=1500, awning_h=450,
                                                             max_pane=[1200, 900], bays=1))
        self.assertEqual((status, list(body["errors"])), (400, ["bays"]))
```

- [ ] **Step 2: Run them to see them fail**

Run: `cd ~/diy-window && python3 -m unittest discover -s web/tests -p 'test_api.py' 2>&1 | tail -3`
Expected: `FAILED (failures=7, errors=4)`:
- the keys are reported as `unknown fields: max_pane`;
- the summary has no `bays` (`KeyError`);
- `TX` has no name;
- the 2-bay window isn't a reference yet;
- `testDefaultsHaveNoLimit` already passes.

Then run `python3 -m unittest discover -s web/tests -p 'test_server.py' 2>&1 | tail -3`. Expected: `FAILED (failures=1, errors=2)`.

- [ ] **Step 3: Validate and pass the keys through**

**Replace** in `web/api.py`:
```python
REFERENCE_NAMES = {"bench-600", "home-1800x1500"}
DEFAULTS = {"name": "my-window", "opening_w": 1800, "opening_h": 1500, "fix_gap": 8, "awning_h": 450,
            "glazing": "igu", "tier": 3, "screen": True, "bed": [256, 256, 256]}
```
**with:**
```python
REFERENCE_NAMES = {"bench-600", "home-1800x1500", "home-1800x1500-2bay"}
DEFAULTS = {"name": "my-window", "opening_w": 1800, "opening_h": 1500, "fix_gap": 8, "awning_h": 450,
            "glazing": "igu", "tier": 3, "screen": True, "bed": [256, 256, 256]}
OPTIONAL = ("max_pane", "bays")
PAGE_MAX_PANE = [1200, 900]
```

**Replace** in `web/api.py`:
```python
    "AC": "Acrylic spacer corner",
}
SUMMARY_KEYS = ("w", "h", "transom_c", "sash", "screen", "glass", "stay", "sash_kg", "keeper_dz", "bed", "max_seg",
                "has_screen", "members", "tubes")
```
**with:**
```python
    "AC": "Acrylic spacer corner",
    "SN": "Sill node, mullion slot", "HN": "Head node, mullion slot", "TX": "Transom cross-node, mullion slots",
    "MSL": "Lower mullion shoe", "MST": "Upper mullion shoe, transom end", "MSH": "Upper mullion shoe, head end",
    "ML": "Lower mullion segment", "MU": "Upper mullion segment",
}
SUMMARY_KEYS = ("w", "h", "transom_c", "sash", "screen", "glass", "stay", "sash_kg", "keeper_dz", "bed", "max_seg",
                "has_screen", "members", "tubes", "bays", "auto_bays", "pitch", "mullions")
```

**Replace** in `web/api.py`:
```python
    params = {k: raw.get(k, v) for k, v in DEFAULTS.items()}
    errors = {}
    unknown = sorted(set(raw) - set(DEFAULTS))
```
**with:**
```python
    params = {k: raw.get(k, v) for k, v in DEFAULTS.items()}
    params.update({k: raw[k] for k in OPTIONAL if k in raw})
    errors = {}
    unknown = sorted(set(raw) - set(DEFAULTS) - set(OPTIONAL))
```

**Replace** in `web/api.py`:
```python
        errors["bed"] = f"three sizes, {BED_RANGE[0]}-{BED_RANGE[1]} mm each"
    return params, errors
```
**with:**
```python
        errors["bed"] = f"three sizes, {BED_RANGE[0]}-{BED_RANGE[1]} mm each"
    lo, hi = window.PANE_RANGE
    if "max_pane" in params and not (isinstance(params["max_pane"], list) and len(params["max_pane"]) == 2
                                     and all(is_number(v) and lo <= v <= hi for v in params["max_pane"])):
        errors["max_pane"] = f"two sizes, {lo}-{hi} mm each"
    if "bays" in params and (type(params["bays"]) is not int or params["bays"] < 1):
        errors["bays"] = "a whole number, 1 or more"
    return params, errors
```

**Replace** in `web/api.py`:
```python
    return next((k for k in DEFAULTS if msg.startswith(k)), "_form")
```
**with:**
```python
    return next((k for k in (*DEFAULTS, *OPTIONAL) if msg.startswith(k)), "_form")
```

**Replace** in `web/server.py`:
```python
            return self.reply(200, {"presets": api.PRESETS, "defaults": api.DEFAULTS})
```
**with:**
```python
            return self.reply(200, {"presets": api.PRESETS, "defaults": api.DEFAULTS, "max_pane": api.PAGE_MAX_PANE})
```

- [ ] **Step 4: Run the tests to see them pass**

Run: `cd ~/diy-window && python3 -m unittest discover -s web/tests -p 'test_api.py' 2>&1 | tail -3`
Expected: `OK` (50 tests).

- [ ] **Step 5: Checkpoint**

Run: `cd ~/diy-window && python3 -m unittest discover -s web/tests -p 'test_*.py' 2>&1 | grep -E '^(Ran|OK|FAILED)'`
Expected: `Ran 147 tests`, `OK`.

---

### Task 12: The page (`web/static/`) and the screenshots

**The new fieldset.** "Glass sheet and bays" has:
- two Max pane inputs, filled from `/api/presets` (1200 × 900);
- a No limit box, which disables the inputs and leaves `max_pane` out of the request;
- a Bays input, empty for automatic, whose placeholder shows `automatic: N`;
- a note with the bay count, the mullions and the pitch.

**Other page changes.**
- The query string takes `max_pane=1200,900`, `max_pane=none` and `bays=N`.
- `sameParams` compares both key sets, so ticking No limit after a render marks the rows stale.
- The badges get labels for the two new checks.
- The viewer colours the steel-cored mullion parts like the transom.

**Files:**
- Modify: `web/static/index.html`, `web/static/app.js`, `web/static/style.css`, `web/static/viewer.js`
- Modify: `web/tests/ui_shots.py` (the `query` helper, and three shots)

- [ ] **Step 1: The fieldset**

**Replace** in `web/static/index.html`:
```html
      <label class="check"><input name="screen" type="checkbox"> Insect screen</label>
    </fieldset>
```
**with:**
```html
      <label class="check"><input name="screen" type="checkbox"> Insect screen</label>
    </fieldset>
    <fieldset>
      <legend>Glass sheet and bays</legend>
      <div class="pair">
        <label class="field">Max pane <em>mm</em><input name="max_a" type="number" step="1"></label>
        <label class="field">by <em>mm</em><input name="max_b" type="number" step="1"></label>
      </div>
      <label class="check"><input name="max_none" type="checkbox"> No limit</label>
      <small class="err" data-for="max_pane"></small>
      <label class="field">Bays <em>empty for automatic</em><input name="bays" type="number" step="1" min="1"><small class="err" data-for="bays"></small></label>
      <p class="note" id="bays-note"></p>
    </fieldset>
```

**Replace** in `web/static/style.css`:
```css
input.invalid { border-color: var(--fail); background: #fff6f5; }
```
**with:**
```css
input.invalid { border-color: var(--fail); background: #fff6f5; }
input:disabled { opacity: 0.5; }
```

**Replace** in `web/static/style.css`:
```css
.r-frame, .r-transom { fill: var(--frame); stroke: var(--ink); }
```
**with:**
```css
.r-frame, .r-transom, .r-mullion { fill: var(--frame); stroke: var(--ink); }
```

**Replace** in `web/static/viewer.js`:
```javascript
  [["T", "TE", "TSL", "TSR"], [0.62, 0.66, 0.72]],
```
**with:**
```javascript
  [["T", "TE", "TSL", "TSR", "TX", "MSL", "MST", "MSH", "ML", "MU"], [0.62, 0.66, 0.72]],
```

- [ ] **Step 2: Form state in `app.js`**

**Replace** in `web/static/app.js`:
```javascript
                 cam_keeper: "Cam / keeper", bed_fit: "Bed fit" };
```
**with:**
```javascript
                 cam_keeper: "Cam / keeper", pane_fit: "Pane fit", mullion_deflection: "Mullion deflection", bed_fit: "Bed fit" };
```

**Replace** in `web/static/app.js`:
```javascript
const state = { presets: [], preview: null, job: null, jobRev: null, selected: new Set(), seq: 0, timer: 0, poll: 0,
                pollFailures: 0, online: true, viewing: null, view: null, viewSeq: 0 };
```
**with:**
```javascript
const state = { presets: [], maxPane: [1200, 900], preview: null, job: null, jobRev: null, selected: new Set(), seq: 0,
                timer: 0, poll: 0, pollFailures: 0, online: true, viewing: null, view: null, viewSeq: 0 };
```

**Replace** in `web/static/app.js`:
```javascript
  const preset = state.presets.find((p) => p.key === form.elements.preset.value);
  return {
    name: form.elements.name.value.trim(),
    opening_w: num("opening_w"), opening_h: num("opening_h"), fix_gap: num("fix_gap"), awning_h: num("awning_h"),
    glazing: form.elements.glazing.value, tier: Number(form.elements.tier.value), screen: form.elements.screen.checked,
    bed: preset ? preset.bed : [num("bed_x"), num("bed_y"), num("bed_z")],
  };
}

function fillForm(p) {
  for (const k of FIELDS) form.elements[k].value = p[k];
  form.elements.screen.checked = p.screen;
```
**with:**
```javascript
  const preset = state.presets.find((p) => p.key === form.elements.preset.value);
  const out = {
    name: form.elements.name.value.trim(),
    opening_w: num("opening_w"), opening_h: num("opening_h"), fix_gap: num("fix_gap"), awning_h: num("awning_h"),
    glazing: form.elements.glazing.value, tier: Number(form.elements.tier.value), screen: form.elements.screen.checked,
    bed: preset ? preset.bed : [num("bed_x"), num("bed_y"), num("bed_z")],
  };
  if (!form.elements.max_none.checked) out.max_pane = [num("max_a"), num("max_b")];
  if (num("bays") !== null) out.bays = num("bays");
  return out;
}

function fillForm(p) {
  for (const k of FIELDS) form.elements[k].value = p[k];
  form.elements.screen.checked = p.screen;
  const limit = p.max_pane || state.maxPane;
  form.elements.max_none.checked = !p.max_pane;
  ["max_a", "max_b"].forEach((k, i) => { form.elements[k].value = limit[i]; form.elements[k].disabled = !p.max_pane; });
  form.elements.bays.value = p.bays === undefined ? "" : p.bays;
```

**Replace** in `web/static/app.js`:
```javascript
  const p = { ...defaults };
```
**with:**
```javascript
  const p = { ...defaults, max_pane: state.maxPane };
```

**Replace** in `web/static/app.js`:
```javascript
  if (q.has("bed")) p.bed = q.get("bed").split(",").map(Number);
  return p;
```
**with:**
```javascript
  if (q.has("bed")) p.bed = q.get("bed").split(",").map(Number);
  if (q.has("max_pane")) p.max_pane = q.get("max_pane") === "none" ? null : q.get("max_pane").split(",").map(Number);
  if (q.has("bays")) p.bays = Number(q.get("bays"));
  return p;
```

**Replace** in `web/static/app.js`:
```javascript
  return Object.keys(params).every((k) => JSON.stringify(values[k]) === JSON.stringify(params[k]));
```
**with:**
```javascript
  const keys = new Set([...Object.keys(values), ...Object.keys(params)]);
  return [...keys].every((k) => JSON.stringify(values[k]) === JSON.stringify(params[k]));
```

**Replace** in `web/static/app.js`:
```javascript
    const key = el.name.startsWith("bed_") ? "bed" : el.name;
```
**with:**
```javascript
    const key = el.name.startsWith("bed_") ? "bed" : el.name.startsWith("max_") ? "max_pane" : el.name;
```

- [ ] **Step 3: The bays note, the viewer title and the presets in `app.js`**

**Replace** in `web/static/app.js`:
```javascript
    $("#maxseg").textContent = `Bed ${body.layout.bed.join(" x ")} mm: segments up to ${body.layout.max_seg} mm.`;
```
**with:**
```javascript
    $("#maxseg").textContent = `Bed ${body.layout.bed.join(" x ")} mm: segments up to ${body.layout.max_seg} mm.`;
    const lay = body.layout;
    form.elements.bays.placeholder = `automatic: ${lay.auto_bays}`;
    $("#bays-note").textContent = lay.bays > 1
      ? `${lay.bays} bays, ${lay.bays - 1} mullion${lay.bays > 2 ? "s" : ""}, ${Math.round(lay.pitch * 10) / 10} mm apart.`
      : "One bay: no mullions.";
```

**Replace** in `web/static/app.js`:
```javascript
  $("#viewer-title").textContent = `${name}: frame, transom and sash`;
```
**with:**
```javascript
  const many = state.preview.layout && state.preview.layout.bays > 1;
  $("#viewer-title").textContent = `${name}: ${many ? "frame, transom, mullions and sashes" : "frame, transom and sash"}`;
```

**Replace** in `web/static/app.js`:
```javascript
  let presets, defaults;
  for (let failures = 0; ; failures++) {
    try {
      ({ presets, defaults } = await getJson("/api/presets"));
```
**with:**
```javascript
  let presets, defaults, maxPane;
  for (let failures = 0; ; failures++) {
    try {
      ({ presets, defaults, max_pane: maxPane } = await getJson("/api/presets"));
```

**Replace** in `web/static/app.js`:
```javascript
  state.presets = presets;
  const select = form.elements.preset;
```
**with:**
```javascript
  state.presets = presets;
  if (maxPane) state.maxPane = maxPane;
  const select = form.elements.preset;
```

**Replace** in `web/static/app.js`:
```javascript
      $("#custom-bed").classList.toggle("hidden", Boolean(preset));
    }
    schedulePreview();
```
**with:**
```javascript
      $("#custom-bed").classList.toggle("hidden", Boolean(preset));
    }
    if (e.target.name === "max_none") ["max_a", "max_b"].forEach((k) => { form.elements[k].disabled = e.target.checked; });
    schedulePreview();
```

Run: `cd ~/diy-window && node --check web/static/app.js && node --check web/static/viewer.js && echo syntax ok`
Expected: `syntax ok`.

- [ ] **Step 4: Three more screenshots**

**Replace** in `web/tests/ui_shots.py`:
```python
def query(p, **extra):
    return "/?" + urllib.parse.urlencode({**{k: v for k, v in p.items() if k != "bed"}, **extra})
```
**with:**
```python
def query(p, **extra):
    limit = ",".join(f"{v:g}" for v in p["max_pane"]) if "max_pane" in p else "none"
    return "/?" + urllib.parse.urlencode({**{k: v for k, v in p.items() if k not in ("bed", "max_pane")},
                                          "max_pane": limit, **extra})
```

**Replace** in `web/tests/ui_shots.py`:
```python
            shot(real + query(params("home-1800x1500"), view="assembled"), a.out / "7-viewer-assembled.png", profile, 10000)
```
**with:**
```python
            shot(real + query(params("home-1800x1500"), view="assembled"), a.out / "7-viewer-assembled.png", profile, 10000)
            shot(real + query(params("home-1800x1500-2bay")), a.out / "8-two-bays.png", profile)
            shot(real + query(params("home-1800x1500-2bay"), view="assembled"), a.out / "9-viewer-two-bays.png", profile, 12000)
            shot(real + query(params("home-1800x1500-2bay"), max_pane="800,800"), a.out / "10-too-tall.png", profile)
```

The reference windows' queries now carry `max_pane=none`, so shots 4–7 stay one-bay. Shots 1–3 use the page default (1200 × 900), so they now show bays.

- [ ] **Step 5: Run the suites, take the screenshots and review them**

Run: `cd ~/diy-window && python3 -m unittest discover -s web/tests -p 'test_*.py' 2>&1 | grep -E '^(Ran|OK|FAILED)'`
Expected: `Ran 147 tests`, `OK`. `test_viewer` runs `viewer_test.mjs` under Node.

Run: `cd ~/diy-window && python3 web/tests/ui_shots.py ~/diy-window/.bays-review/shots`
Expected: ten lines, `1-valid.png: ...` to `10-too-tall.png: ...`, with no `NO SCREENSHOT`.

Read each PNG and check:
- **`1-valid.png`** (the page default: 1800 × 1500 with a 1200 × 900 sheet):
  - The front view shows two bays, a mullion and a `bay 799` dimension, and each pane is labelled `829 x 878` and `737 x 388`.
  - All seven badges are green, including Pane fit and Mullion deflection.
  - The Bays field shows `automatic: 2`, and the note reads `2 bays, 1 mullion, 869 mm apart.`
- **`2-invalid.png`:** as before (a name error and a width error).
- **`3-failed-check.png`** (3000 mm wide, three bays):
  - The Transom deflection badge is red, and the explanation under the badges reads "Transom deflection: transom deflects 56.5 mm at 0.7 kPa carrying 2 mullions, limit span/175 = 16.4 mm". Mullions don't rescue a 2.9 m transom: see Decisions.
  - The three bays' labels fit inside their panes.
- **`4-rendering.png`, `5-download.png`, `6-viewer-part.png`:** as before. No limit is ticked, and the Max pane inputs are greyed out.
- **`7-viewer-assembled.png`:** the one-bay home window, the same as before.
- **`8-two-bays.png`:** the same as shot 1, under the name `home-1800x1500-2bay`. The parts table lists 43 types and 226 prints, with `ML`, `MU`, `SN`, `HN`, `TX`, `MSL`, `MST` and `MSH`.
- **`9-viewer-two-bays.png`:** the viewer title reads "frame, transom, mullions and sashes", and the assembled view has two sashes and the mullion on the centre line.
- **`10-too-tall.png`:**
  - The two Max pane inputs are red.
  - The message under them reads "max_pane: the 878 mm tall fixed pane does not fit a 800 x 800 mm sheet at any bay count; that needs a second horizontal transom, which is out of scope: use a taller awning_h or a shorter opening".
  - Render is disabled.

- [ ] **Step 6: Checkpoint**

Hand-check in a live page (`python3 web/server.py`, then open http://127.0.0.1:8765/):
1. Ticking No limit greys the inputs and redraws one bay. Unticking redraws two bays.
2. Typing 3 in Bays redraws three bays, and Pane fit's tooltip says `3 bays (2 needed)`.
3. Typing 1 shows "bays must be at least 2 …" under Bays.
4. With `python3 web/server.py --fake-render` (box-shaped STLs in a temporary folder, nothing written to `params/` or `cad/stl/`), **Render selected** on `TX` for a new name, then tick No limit: the row turns `ok, old settings`.

---
### Task 13: Guides, manual, specs, README and the guide PDF

**What changes.**
- Every guide step that a window with bays does differently gets a **Bays:** note, or a per-bay wording ("each sash"). A one-bay window reads exactly as before.
- New text: the mullion dry-fit (build guide §7), the mullion fitting (install step 6.7–6.11), the stay tracks on a mullion, the packers under each `SN`, and the per-bay seals and magnet strips.
- The specs record the planning amendments.

**Where the new text goes, and why.**
- The new build-guide section goes at the end and the install sub-steps go inside step 6, because the guides cross-reference their step numbers.
- `docs/user-manual.md` keeps its ten `## ` sections and its home-window Specifications table, because `pdf/build_deck.py` checks both.
- The deck gets one sizing slide, built from the 2-bay window's BOM and `docs/img/assembly-home-2bay.png` (Task 9).

**Files:**
- Modify: `docs/build-guide.md`, `docs/install-guide.md`, `docs/printing.md`, `docs/user-manual.md`, `docs/test-log.md`, `README.md`, `web/README.md`
- Modify: `docs/specs/2026-10-07-diy-window-design.md`, `docs/specs/2026-10-10-mullion-bays-design.md`
- Modify: `pdf/build_deck.py`
- Regenerate: `pdf/openwindow-deck.html`, `OpenWindow-Guide.pdf`

- [ ] **Step 1: The guides, manual, test log and READMEs**

**Replace** in `docs/build-guide.md`:
```markdown
All quantities and lengths for your window are in `bom/<name>.md` (BOM, tube cut list, glass) and `bom/<name>-parts.csv`. Run `python3 bom/build_bom.py <name>` first. Don't work from `cad/generated/*.csv`: `cad/box.sh test` and `png` regenerate those for the bench window.
```
**with:**
```markdown
**Windows with bays.** A params file with `max_pane` or `bays` can split the window into bays (the `pane_fit` line of `generate.py` says how many). Each bay then has its own sash and screen. The sill, head and transom are built as one run per bay, with a node between runs: SN in the sill, HN in the head and TX in the transom. The mullions are dry-fitted in section 7 and fitted at install step 6. Steps marked **Bays:** apply only then, and `bom/<name>.md` lists the mullion centre lines under "Bays".

All quantities and lengths for your window are in `bom/<name>.md` (BOM, tube cut list, glass) and `bom/<name>-parts.csv`. Run `python3 bom/build_bom.py <name>` first. Don't work from `cad/generated/*.csv`: `cad/box.sh test` and `png` regenerate those for the bench window.
```

**Replace** in `docs/build-guide.md`:
```markdown
   2. Thread on the sill segments: an SW (weep) segment first, then the S segments, then the other SW. Fit CSR on the right end.
   3. Close the joints one by one from CSL (joint rules above), driving each segment's screw as you go. CSR's screw goes in last.
```
**with:**
```markdown
   2. Thread on the sill segments: an SW (weep) segment first, then the S segments, then the other SW. Fit CSR on the right end.
      - **Bays:** thread one such run per bay, with an SN node between runs. Its dovetail slot faces up into the opening and opens on the room side.
   3. Close the joints one by one from CSL (joint rules above), driving each segment's screw as you go. CSR's screw goes in last.
      - **Bays:** before you drive an SN's tube screw (inside face, centre of the node), set the shims so its centre is on its mullion centre line within 0.5 mm.
```

**Replace** in `docs/build-guide.md`:
```markdown
   1. Assemble CH, the H segments and CH on the head tube in the same way.
```
**with:**
```markdown
   1. Assemble CH, the H segments and CH on the head tube in the same way.
      - **Bays:** one run of H segments per bay, with an HN node between runs, its slot facing down into the opening. Centre each HN on its mullion centre line, like the SN below it.
```

**Replace** in `docs/build-guide.md`:
```markdown
1. **Cam bases.** Screw the two cam bases (CMB) to the TE inserts, with two M4 × 10 countersunk screws each.
```
**with:**
```markdown
1. **Cam bases.** Screw a cam base (CMB) to the inserts of every TE segment (two per bay), with two M4 × 10 countersunk screws each.
```

**Replace** in `docs/build-guide.md`:
```markdown
   1. Thread the T and TE segments onto the steel tube, with a TE segment at each end.
```
**with:**
```markdown
   1. Thread the T and TE segments onto the steel tube, with a TE segment at each end.
      - **Bays:** one run per bay, each with a TE at both ends, and a TX cross-node between runs with its two slots facing up and down. Set the shims so that each TX centre sits on its mullion centre line.
```

**Replace** in `docs/build-guide.md`:
```markdown
## 5. Sash
1. **Assemble.** Fit SH (top), SB + SBE (bottom, with SBE at the ends) and SV (sides) on their 20 × 20 tubes with four CS corners. Use the joint rules and 8g × 30 tube screws.
```
**with:**
```markdown
## 5. Sash
Make one sash per bay. They are all the same.

1. **Assemble.** Fit SH (top), SB + SBE (bottom, with SBE at the ends) and SV (sides) on their 20 × 20 tubes with four CS corners. Use the joint rules and 8g × 30 tube screws.
```

**Replace** in `docs/build-guide.md`:
```markdown
4. **Friction stays (sash side only).** Screw each stay's sash arm to a sash side. The tracks go on the jambs at install step 8.
```
**with:**
```markdown
4. **Friction stays (sash side only).** Screw each stay's sash arm to a sash side. The tracks go on the jambs (and the mullions, with bays) at install step 8.
```

**Replace** in `docs/build-guide.md`:
```markdown
1. **Rails.** Thread the NH and NV segments onto their 10 × 10 tubes. The cut list gives a tube for every rail of two or more segments. A single-segment rail has none.
```
**with:**
```markdown
Make one screen per bay.

1. **Rails.** Thread the NH and NV segments onto their 10 × 10 tubes. The cut list gives a tube for every rail of two or more segments. A single-segment rail has none.
```

**Replace** in `docs/build-guide.md`:
```markdown
4. Leave the hinge leaves off. HG and HS are fitted and aligned in place (install guide, step 12).
```
**with:**
```markdown
4. Leave the hinge leaves off. HG and HS are fitted and aligned in place (install guide, step 12).

## 7. Mullions (bays only)

Skip this section for a window with one bay. Each bay boundary has a lower mullion (sill to transom) and an upper mullion (transom to head), each on its own 40 × 20 steel tube from the cut list. Like the transom, they are only dry-fitted here. Their lengths have to match the node spacing in the fitted frame, so they are sealed and screwed at install step 6.

1. **Lower mullion.** Thread an MSL shoe, the ML segments and a second MSL shoe onto a `mullion_lower` tube. Both shoes are the same part, with the top one turned end for end, so both tongues point outwards. Each shoe takes a cord ring only in its joint with the ML segment.
2. **Upper mullion.** Thread MST, the MU segments and MSH onto a `mullion_upper` tube. MST goes at the bottom, where it meets the transom. MSH goes at the top: its magnet channel turns along the head.
3. Check every joint closes onto its shims. Leave the joints unsealed and unscrewed.
```

**Replace** in `docs/install-guide.md`:
```markdown
   1. Stand the frame on plastic packers under the two sill corners, and under each GW quarter point. Those points are a quarter of the fixed glass width in from each glass edge: 43 mm plus a quarter of the glass width from each outer frame edge, so about 467 mm for the home window and 167 mm for the bench window. Mark them on the sill. These two packers carry the fixed pane's weight straight down into the wall (spec §2.5).
```
**with:**
```markdown
   1. Stand the frame on plastic packers under the two sill corners, and under each GW quarter point. Those points are a quarter of the fixed glass width in from each glass edge: 43 mm plus a quarter of the glass width from each outer frame edge, so about 467 mm for the home window and 167 mm for the bench window. Mark them on the sill. These two packers carry the fixed pane's weight straight down into the wall (spec §2.5).
      - **Bays:** every fixed pane has its own two quarter points, a quarter of its width in from each of its edges: about 250 and 665 mm from each outer frame edge for the two-bay home window. Put a packer under each SN node too: the mullions bring the transom's share of the sash weight down there.
```

**Replace** in `docs/install-guide.md`:
```markdown
     - both fixings in each node (JN).
```
**with:**
```markdown
     - both fixings in each node (JN, and SN with bays).
```

**Replace** in `docs/install-guide.md`:
```markdown
   6. Tool the squeezed-out sealant along each shoe/node seam on the inside face.
```
**with:**
```markdown
   6. Tool the squeezed-out sealant along each shoe/node seam on the inside face.
   7. **Bays: check the nodes line up.** Hold a straightedge or a plumb line through the slot centres of each SN, TX and HN. If a TX is more than 0.5 mm off the line, reset the transom shims (step 6.2) before going on.
   8. **Bays: lower mullions.** For each one, measure from the SN slot face to the TX's lower slot face, at the outside and inside edges, and take the smaller figure. The design figure is the fixed-pane height plus 36 mm (884 mm for the two-bay home window). Seal, close and screw its dry-fitted assembly (build guide 7.1) to 0.5 mm under that figure, with the joint rules, and drive the tek screws.
   9. Lay 3 mm foam cord in the groove across each MSL end face, and butter the rest of the face with MS polymer. Lift the mullion in from the room side and slide both tongues down the SN and TX slots together, to the stop. Drive its four M4 × 16 countersunk lock screws down the slot flanks, two at each end.
   10. **Bays: upper mullions.** Do the same from the TX's upper slot face to the HN slot face (the awning height plus 36 mm, so 486 mm), with MST at the bottom and MSH at the top (build guide 7.2).
   11. Tool the sealant along every mullion shoe/node seam on the inside face.
```

**Replace** in `docs/install-guide.md`:
```markdown
   1. **EPDM bulb seals.** Fit two continuous loops round the sash opening, each with a single joint: the outer seal in the fin kerf, and the inner seal in the inner-stop kerf.
      - Start each loop at the middle of the head. Run it across the head, down an upper jamb, through the shoe turn, along the transom, through the other shoe turn, up the other jamb and back to the start.
```
**with:**
```markdown
   1. **EPDM bulb seals.** Fit two continuous loops round each sash opening, each with a single joint: the outer seal in the fin kerf, and the inner seal in the inner-stop kerf.
      - Start each loop at the middle of the head. Run it across the head, down an upper jamb, through the shoe turn, along the transom, through the other shoe turn, up the other jamb and back to the start.
      - **Bays:** on a mullion side the loop runs down the upper mullion's kerf, turns along the transom in the MST shoe and turns up into the head's kerf in the MSH shoe.
```

**Replace** in `docs/install-guide.md`:
```markdown
   2. **Magnet strip B.** Skip it if your params file has `"screen": false`. Press it into the frame magnet channel: along the lower half of the transom's inside face, through each shoe turn, up both upper jambs, and across the head. It covers the lock screw heads. Strip B must be the matched partner of the screen's strip A (or a steel strip, if strip A is a plain magnet).
```
**with:**
```markdown
   2. **Magnet strip B.** Skip it if your params file has `"screen": false`. Press it into the frame magnet channel: along the lower half of the transom's inside face, through each shoe turn, up both upper jambs, and across the head. It covers the lock screw heads.
      - **Bays:** one loop per bay. On a mullion side it runs up the mullion's channel, which drops across the TX face to the transom channel, and turns along the head in the MSH shoe. Strip B must be the matched partner of the screen's strip A (or a steel strip, if strip A is a plain magnet).
```

**Replace** in `docs/install-guide.md`:
```markdown
8. **Hang the sash.** Two people. The frame fixings are all in (step 5), and the stays are already on the sash (build guide 5.4).
```
**with:**
```markdown
8. **Hang the sash** (each sash, with bays). Two people. The frame fixings are all in (step 5), and the stays are already on the sash (build guide 5.4).
```

**Replace** in `docs/install-guide.md`:
```markdown
   3. Drill 3.2 mm pilots through the track holes, and screw the track on with 8g × 25 stainless countersunk screws.
```
**with:**
```markdown
   3. Drill 3.2 mm pilots through the track holes, and screw the track on with 8g × 25 stainless countersunk screws.
      - **Bays:** a track on a mullion goes into its steel tube. Use the 8g × 16 tek screws from the BOM, with no pilot. The two stays either side of a mullion screw into the same tube, and 16 mm screws miss each other inside it.
```

**Replace** in `docs/install-guide.md`:
```markdown
9. **Glaze the fixed pane.**
```
**with:**
```markdown
9. **Glaze the fixed pane** (each pane, with bays).
```

**Replace** in `docs/install-guide.md`:
```markdown
    3. Push in the four weep caps (WC), open end facing down: two on the SW sill weeps, and two on the SBE sash weeps (open the sash to reach them). The TE weeps in the transom fin drain the chamber between the sash seals and get no cap.
```
**with:**
```markdown
    3. Push in the weep caps (WC), open end facing down: one on each SW sill weep and one on each SBE sash weep (open the sash to reach them), so four per bay. The TE weeps in the transom fin drain the chamber between the sash seals and get no cap.
```

**Replace** in `docs/install-guide.md`:
```markdown
12. **Screen.** Skip this step if your params file has `"screen": false`.
```
**with:**
```markdown
12. **Screen** (each screen, with bays). Skip this step if your params file has `"screen": false`.
```

**Replace** in `docs/install-guide.md`:
```markdown
    1. Screw the HG hinge leaves to the head inserts, with two M4 × 10 pan- or button-head screws each. Hinges go on the two end H segments and, with three hinges, on the segment nearest the centre. With an even number of H segments, use either of the two middle ones. On the 7-segment home head that means the 1st, 4th and 7th.
```
**with:**
```markdown
    1. Screw the HG hinge leaves to the head inserts, with two M4 × 10 pan- or button-head screws each. Hinges go on the two end H segments (of that bay's run, with bays) and, with three hinges, on the segment nearest the centre. With an even number of H segments, use either of the two middle ones. On the 7-segment home head that means the 1st, 4th and 7th.
```

**Replace** in `docs/printing.md`:
```markdown
| Segments (H, S, SW, JL, JU, T, TE, SH, SB, SBE, SV, NH, NV), TC | Standing on an end face, exactly as exported. No supports. |
```
**with:**
```markdown
| Segments (H, S, SW, JL, JU, T, TE, ML, MU, SH, SB, SBE, SV, NH, NV), TC | Standing on an end face, exactly as exported. No supports. |
```

**Replace** in `docs/printing.md`:
```markdown
| JN, TSL, TSR | On the outside face (the face that looks out of the window), so the dovetail slot and tongue print in plane and slide without binding. Supports on build plate only. |
```
**with:**
```markdown
| JN, TSL, TSR, and with bays SN, HN, TX, MSL, MST, MSH | On the outside face (the face that looks out of the window), so the dovetail slots and tongues print in plane and slide without binding. Supports on build plate only. |
```

**Replace** in `docs/printing.md`:
```markdown
The 1800 × 1500 home window needs 160 prints in 35 types, about 16.46 kg of exterior filament plus 3.89 kg of interior PETG (measured from the STLs on 2026-10-09). Print a test coupon (TC) and one segment of each profile first, and check the fit before committing a full spool.
```
**with:**
```markdown
The 1800 × 1500 home window needs 160 prints in 35 types, about 16.46 kg of exterior filament plus 3.89 kg of interior PETG (measured from the STLs on 2026-10-09). The same opening split into two bays for a 1200 × 900 mm sheet (`params/home-1800x1500-2bay.json`) needs 226 prints in 43 types, about 19.19 kg of exterior filament plus 4.81 kg of interior PETG (measured from its STLs on 2026-10-10). Print a test coupon (TC) and one segment of each profile first, and check the fit before committing a full spool.
```

**Replace** in `docs/user-manual.md`:
```markdown
The two cams are latches that hold the sash on its seals. They are not a keyed security lock.
```
**with:**
```markdown
The two cams are latches that hold the sash on its seals. They are not a keyed security lock.

A window split into bays by mullions has a sash, two cams and a screen in every bay. Open, close and latch each one on its own, as above.
```

**Replace** in `docs/user-manual.md`:
```markdown
- **Workshop jobs:** segments, corners, nodes and shoes are threaded on or screwed to the metal tubes. The sash and screen come off for this. A frame part means taking the window out, so a small crack in a frame segment is better bonded and sealed in place.
```
**with:**
```markdown
- **Workshop jobs:** segments, corners, nodes and shoes are threaded on or screwed to the metal tubes. A mullion (`MSL`, `ML`, `MST`, `MU`, `MSH`) slides out towards the room once its four lock screws are out and the seams are cut. The sash and screen come off for this. A frame part means taking the window out, so a small crack in a frame segment is better bonded and sealed in place.
```

**Replace** in `README.md`:
```markdown
   - `bed` (optional, default `[256, 256, 256]`, a Bambu P1S): your printer's build volume X, Y, Z in mm. Segments are split to at most min(Z, max(X, Y)) − 16 mm.
```
**with:**
```markdown
   - `bed` (optional, default `[256, 256, 256]`, a Bambu P1S): your printer's build volume X, Y, Z in mm. Segments are split to at most min(Z, max(X, Y)) − 16 mm.
   - `max_pane` (optional, no limit by default): the largest glass or acrylic sheet you can get, `[a, b]` in mm, either way round. The window is split into the fewest equal bays, divided by mullions, that make every pane fit. Each bay has its own fixed pane, awning sash and screen.
   - `bays` (optional): more bays than `max_pane` needs. Fewer is an error.
```

**Replace** in `README.md`:
```markdown
3. **Generate:** `python3 tools/generate.py params/my-window.json`. Read the check lines it prints (transom deflection, friction-stay rating, segment length). A `WARNING` line needs a change before you print.
```
**with:**
```markdown
3. **Generate:** `python3 tools/generate.py params/my-window.json`. Read the check lines it prints (transom deflection, friction-stay rating, segment length, and with `max_pane` or `bays` the pane fit and mullion deflection). A `WARNING` line needs a change before you print.
```

**Replace** in `README.md`:
```markdown
![Profiles](docs/img/profiles.png)
```
**with:**
```markdown
![Profiles](docs/img/profiles.png)

Too big for your glass sheet? `params/home-1800x1500-2bay.json` is the same opening with `"max_pane": [1200, 900]`: two bays, split by a mullion.

![Home window in two bays](docs/img/assembly-home-2bay.png)
```

**Replace** in `web/README.md`:
```markdown
2. **Printer.** Pick a bed preset or Custom. The generator splits every member into segments of at most min(Z, max(X, Y)) − 16 mm, and the Bed fit badge checks every part against the bed.
```
**with:**
```markdown
2. **Glass sheet and bays.** Max pane is the largest sheet you can get, 1200 × 900 mm until you change it. Tick No limit for one bay. The window splits into the fewest equal bays that make every pane fit, and the Bays field shows that number. Type a larger number to ask for more bays.
3. **Printer.** Pick a bed preset or Custom. The generator splits every member into segments of at most min(Z, max(X, Y)) − 16 mm, and the Bed fit badge checks every part against the bed.
```

**Replace** in `web/README.md`:
```markdown
3. **Render all**, or tick rows and **Render selected**. The window's params are saved to `params/<name>.json`. A reference window (`bench-600`, `home-1800x1500`) is never overwritten: rendering it with its own values is fine, and changed values need another name. Parts render in batches of up to six through `cad/box.sh render`, each STL is checked like `tools/check_stl.py` does, and `bom/<name>.*` is rebuilt at the end. One job runs at a time, and **Cancel** stops the running batch.
```
**with:**
```markdown
4. **Render all**, or tick rows and **Render selected**. The window's params are saved to `params/<name>.json`. A reference window (`bench-600`, `home-1800x1500`, `home-1800x1500-2bay`) is never overwritten: rendering it with its own values is fine, and changed values need another name. Parts render in batches of up to six through `cad/box.sh render`, each STL is checked like `tools/check_stl.py` does, and `bom/<name>.*` is rebuilt at the end. One job runs at a time, and **Cancel** stops the running batch.
```

**Replace** in `web/README.md`:
```markdown
4. **View.** Click a part row to see its STL, or **Assembled** for the frame, transom and sash in place, seen from outside. Drag to orbit and scroll to zoom.
```
**with:**
```markdown
5. **View.** Click a part row to see its STL, or **Assembled** for the frame, transom and sash in place, seen from outside. Drag to orbit and scroll to zoom.
```

**Replace** in `web/README.md`:
```markdown
5. **Download** `<name>-openwindow.zip` once every part has passed its STL check. If some parts failed, a partial zip leaves them out and lists them at the top of its `README.txt`.
```
**with:**
```markdown
6. **Download** `<name>-openwindow.zip` once every part has passed its STL check. If some parts failed, a partial zip leaves them out and lists them at the top of its `README.txt`.
```

**Replace** in `web/README.md`:
```markdown
Any form field can also be preset in the address, for example `/?name=bench-600&opening_w=600&opening_h=600&awning_h=200&glazing=acrylic&tier=1`. Add `view=<ID>` or `view=assembled` to open the viewer.
```
**with:**
```markdown
Any form field can also be preset in the address, for example `/?name=bench-600&opening_w=600&opening_h=600&awning_h=200&glazing=acrylic&tier=1`. Add `view=<ID>` or `view=assembled` to open the viewer, and `max_pane=1200,900` or `max_pane=none` for the sheet limit.
```

**Replace** in `docs/test-log.md`:
```markdown
| 7 | Screen corners | Look for light at the screen's bottom corners (where its magnet strip leaves the transom) | No gap above 1 mm; if there is one, add foam pads and record where | | | |
```
**with:**
```markdown
| 7 | Screen corners | Look for light at the screen's bottom corners (where its magnet strip leaves the transom) | No gap above 1 mm; if there is one, add foam pads and record where | | | |
| 8 | Mullion tees (windows with bays) | Rows 2 and 3 again, aimed at the SN, TX and HN seams and at the shoe turns either side of each mullion | No water inside and no smoke draw at any mullion seam | | | |
```

**Replace** in `docs/specs/2026-10-07-diy-window-design.md`:
```markdown
Status: Approved 2026-10-07; amended 2026-10-08 and 2026-10-09 (§12)
```
**with:**
```markdown
Status: Approved 2026-10-07; amended 2026-10-08, 2026-10-09 and 2026-10-10 (§12)
```

**Replace** in `docs/specs/2026-10-07-diy-window-design.md`:
```markdown
- `tier` = 1 | 2 | 3
```
**with:**
```markdown
- `tier` = 1 | 2 | 3
- optional: `screen`, `bed` (web configurator spec §3), and `max_pane`, `bays` (mullions and bays, §12.13)
```

**Replace** in `docs/specs/2026-10-07-diy-window-design.md`:
```markdown
    - **Transom length.** The transom is dry-fitted at the bench. At install it is sealed and screwed with its shims set to the node spacing measured in the fixed frame.
```
**with:**
```markdown
    - **Transom length.** The transom is dry-fitted at the bench. At install it is sealed and screwed with its shims set to the node spacing measured in the fixed frame.
13. **Mullions and bays (2026-10-10).** `docs/specs/2026-10-10-mullion-bays-design.md`, planned in `docs/plans/2026-10-10-mullion-bays.md`. With `max_pane`, the window splits into equal bays divided by mullions. Each bay has its own fixed pane, awning sash and screen, and the transom stays one member across the full width.
    - New parts: sill and head nodes (`SN`, `HN`), a transom cross-node (`TX`), mullion shoes (`MSL`, `MST`, `MSH`) and segments (`ML`, `MU`), each mullion on a 40 × 20 steel tube.
    - The dovetail tees use a 4 mm mullion dovetail (`MULLION_DOVE_D`), not the jamb node's 6 mm one, because the transom body leaves only 6.7 mm of shell over its tube.
    - The transom is checked over its full span, with each mullion's reaction as a point load: the dovetails carry no moment, so the mullions can't prop it. That gives 6.8 mm against 9.5 mm for the home opening in two bays.
```

**Replace** in `docs/specs/2026-10-10-mullion-bays-design.md`:
```markdown
Status: Draft for review
```
**with:**
```markdown
Status: Implemented (plan: `docs/plans/2026-10-10-mullion-bays.md`); amended while planning (§10)
```

**Replace** in `docs/specs/2026-10-10-mullion-bays-design.md`:
```markdown
- Coupled multi-frame units
```
**with:**
```markdown
- Coupled multi-frame units

## 10. Amendments (2026-10-10, from implementation planning)

Each one was checked in a scratch build: tests, box renders and section views. The plan's "Decisions and spec gaps" table has the reasons.

1. **Mullion centres** sit at `FRAME_W − MULLION_W/2 + i · pitch`, not `FRAME_W + i · pitch`. The §4.1 formula put the 2-bay mullion 35 mm off centre and broke the equal-daylight rule.
2. **`dims.json`** gains `MULLION_W`, `MULLION_HALF_BODY` and `MULLION_DOVE_D`. `cad/generated/dims.scad` mirrors them, so it gains three lines. That is the one exception to §7. Everything else is byte-identical.
3. **`transom_deflection`** keeps the full transom span. The end half-bays carry the uniform load, and each mullion's reaction is a point load, because the dovetail tees are pinned. One bay is unchanged.
4. **`pane_fit` and `mullion_deflection`** only appear when the params have `max_pane` or `bays`, so the outputs for existing windows don't change.
5. **The dovetail** is 4 mm deep in every mullion node, so one `MSL` serves the sill and the transom ends. The upper mullion has two shoes: `MST` at the transom and `MSH` at the head, where the head's magnet channel turns.
6. **The screen magnet channels** on `mullion_sash` sit 2–15 mm from each body face, as on the jamb. Mirroring the transom's position would overlap the two screens.
7. **Bays are capped** so that every bay is at least 150 mm wide. A sash pane that is too tall suggests a shorter awning.
8. **Stay tracks on a mullion** use 8g × 16 tek screws into the steel tube.
9. **Also:** a packer goes under each `SN`. `bom/<name>.md` lists the mullion centre lines, and the test log gets a mullion-tee row.
```

- [ ] **Step 2: One sizing slide in the deck**

**Replace** in `pdf/build_deck.py`:
```python
HOME, BENCH = "home-1800x1500", "bench-600"
```
**with:**
```python
HOME, BENCH, TWO_BAY = "home-1800x1500", "bench-600", "home-1800x1500-2bay"
```

**Replace** in `pdf/build_deck.py`:
```python
    "BSV": "Sash bead, vertical", "AFH": "Acrylic spacer, fixed, horiz.", "AFV": "Acrylic spacer, fixed, vert.",
```
**with:**
```python
    "BSV": "Sash bead, vertical", "SN": "Sill node (mullion slot)", "HN": "Head node (mullion slot)",
    "TX": "Transom cross-node", "MSL": "Lower mullion shoe", "MST": "Upper mullion shoe, transom end",
    "MSH": "Upper mullion shoe, head end", "ML": "Lower mullion segment", "MU": "Upper mullion segment",
    "AFH": "Acrylic spacer, fixed, horiz.", "AFV": "Acrylic spacer, fixed, vert.",
```

**Replace** in `pdf/build_deck.py`:
```python
def size_slides(hm, bn):
```
**with:**
```python
def bays_slide(hm, tb):
    fw, fh = tb.glass_size("fixed")
    sw, sh = tb.glass_size("sash")
    hfw, hfh = hm.glass_size("fixed")
    ext, inn, _ = tb.filament()
    hext, hinn, _ = hm.filament()
    limit = " × ".join(fmt(v) for v in tb.params["max_pane"])
    rows = [
        ["Fixed panes", f"1 × {hfw} × {hfh}", f"{tb.lay['bays']} × {fw} × {fh}"],
        ["Sashes", f"1, {fmt(hm.lay['sash_kg'])} kg", f"{tb.lay['bays']}, {fmt(tb.lay['sash_kg'])} kg each"],
        ["Transom", hm.check("transom_deflection")["msg"].replace("transom deflects ", ""),
         tb.check("transom_deflection")["msg"].replace("transom deflects ", "")],
        ["Mullion", "none", tb.check("mullion_deflection")["msg"]],
        ["Prints", f"{hm.prints} in {hm.types} types", f"{tb.prints} in {tb.types} types"],
        ["Filament", f"{fmt(hext)} + {fmt(hinn)} kg", f"{fmt(ext)} + {fmt(inn)} kg"],
    ]
    slide("size", "Sheet smaller than the panes? Mullions and bays", grid(md(f"""
Add `"max_pane": [{', '.join(fmt(v) for v in tb.params['max_pane'])}]` to the params file: the largest glass or acrylic sheet you can get, either way round.

- The generator picks the **fewest equal bays** that make every pane fit, splits the window with **mullions**, and gives each bay its own fixed pane, awning sash, screen and two cams.
- `"bays": n` asks for more bays than needed, never fewer.
- A pane too tall for the sheet needs a second transom, which OpenWindow does not do: the generator stops and says so.
- New parts: sill node [[SN]], head node [[HN]], transom cross-node [[TX]], mullion shoes [[MSL]], [[MST]], [[MSH]] and segments [[ML]], [[MU]], each on a 40 × 20 steel tube.
""") + table(["", "One bay", f"{limit} mm sheet"], rows, cls="compact", widths=["18%", "36%", "46%"]),
        fig(IMG / "assembly-home-2bay.png", 420, 420, pad=0.03, cap=f"`params/{tb.name}.json`, seen from the room."),
        cols="1fr 420px", gap=30))


def size_slides(hm, bn, tb):
```

**Replace** in `pdf/build_deck.py`:
```python
"""), cols="1.25fr 1fr", gap=32))

    out = "\n".join(check_lines(hm))
```
**with:**
```python
"""), cols="1.25fr 1fr", gap=32))
    bays_slide(hm, tb)

    out = "\n".join(check_lines(hm))
```

**Replace** in `pdf/build_deck.py`:
```python
    hm, bn = Window(HOME), Window(BENCH)
```
**with:**
```python
    hm, bn, tb = Window(HOME), Window(BENCH), Window(TWO_BAY)
```

**Replace** in `pdf/build_deck.py`:
```python
    size_slides(hm, bn)
```
**with:**
```python
    size_slides(hm, bn, tb)
```

The new slide's `[[ID]]` chips need the new names in the deck's `PART_NAMES`. `Window(TWO_BAY)` reads `bom/home-1800x1500-2bay*` (Task 8) and refuses to run if that parts list is stale.

- [ ] **Step 3: Check the slides, look at the new one, and rebuild the PDF**

Run: `cd ~/diy-window && python3 pdf/build_deck.py --check`
Expected: `overflow: none`. The builder also exits early if `docs/user-manual.md`'s sections or Specifications needles have changed: they haven't.

Run: `cd ~/diy-window && python3 pdf/build_deck.py --slide 21 --png ~/diy-window/.bays-review/slide-bays.png`
Expected: `slide 21/75 -> ...`. Read the PNG:
- the title is "Sheet smaller than the panes? Mullions and bays";
- the six-row table reads 1 × 1698 × 878 against 2 × 829 × 878, 15.7 kg against 7.6 kg each, 6.2 against 6.8 mm, the mullion line, 160 against 226 prints, and 16.46 + 3.89 against 19.19 + 4.81 kg;
- the 2-bay render is on the right, and the part chips are styled.

Run: `cd ~/diy-window && python3 pdf/build_deck.py`
Expected: `wrote pdf/openwindow-deck.html (75 slides, ...)`, then `wrote OpenWindow-Guide.pdf (... KB, 75 pages, MediaBox [(0.0, 0.0, 960.0, 540.0)])`.

- [ ] **Step 4: Checkpoint**

Run: `cd ~/diy-window && grep -c 'Bays:' docs/build-guide.md docs/install-guide.md`
Expected: `docs/build-guide.md:5` and `docs/install-guide.md:7`.

Read the changed parts of `docs/build-guide.md` §3–§7 and `docs/install-guide.md` steps 4–12 once, in order, as a builder of the 2-bay window. Every new part (`SN`, `HN`, `TX`, `MSL`, `MST`, `MSH`, `ML`, `MU`) and every new BOM line (mullion tek screws, M4 × 16 lock screws, 3 mm cord, packers) should come up at the step that uses it.

---

### Task 14: Final checks and clean-up

**Files:**
- Delete: `.bays-baseline/`, `.bays-after/`, `.bays-review/`
- Modify: this plan's "Execution status"

- [ ] **Step 1: Every suite, every reference window**

Run:
```bash
cd ~/diy-window/tools && python3 -m unittest discover -p 'test_*.py' 2>&1 | grep -E '^(Ran|OK|FAILED)'
cd ~/diy-window && python3 -m unittest discover -s web/tests -p 'test_*.py' 2>&1 | grep -E '^(Ran|OK|FAILED)'
cd ~/diy-window && cad/box.sh test
for n in bench-600 home-1800x1500 home-1800x1500-2bay; do python3 tools/generate.py params/$n.json > /dev/null && python3 tools/check_stl.py $n | tail -1; done
python3 tools/generate.py params/bench-600.json > /dev/null
```
Expected:
- `Ran 279 tests`, `OK`;
- `Ran 147 tests`, `OK`;
- `8 test files passed`;
- `37/37 parts ok`, `35/35 parts ok` and `43/43 parts ok`.

Then run the **compatibility check** (Task 0). Expected: `BYTE-IDENTICAL`.

- [ ] **Step 2: The reference outputs are current**

Run: `cd ~/diy-window && for n in bench-600 home-1800x1500 home-1800x1500-2bay; do python3 bom/build_bom.py $n; done`
Expected: `38 lines`, `36 lines` and `37 lines` (bench, home, 2-bay), with no "STLs missing".

Then:
- `cmp bom/home-1800x1500.md .bays-baseline/home-1800x1500/home-1800x1500.md` gives no output;
- `python3 pdf/build_deck.py --check` gives `overflow: none`.

- [ ] **Step 3: Final review**

**Review gate (docs, BOM and code consistency, spec §8.7):** stop here for a review. Check that:
- the numbers in `docs/printing.md`, the deck slide and `bom/home-1800x1500-2bay.md` agree (226 prints, 19.19 + 4.81 kg);
- every BOM line is used by a guide step, and every part ID appears in `web/api.py`'s `PART_NAMES`, the deck's `PART_NAMES` and `docs/printing.md`;
- the Decisions table matches the code.

- [ ] **Step 4: Clean up and record**

Run: `cd ~/diy-window && rm -rf .bays-baseline .bays-after .bays-review && ls -a | grep '^\.bays' ; ls cad/tests | grep zz_`
Expected: no output.

Replace this plan's "Execution status" section with the date, the four counts from Step 1 (279, 147, 8 files, 43/43) and the review results.
