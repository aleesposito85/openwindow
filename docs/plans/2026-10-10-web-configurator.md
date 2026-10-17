# OpenWindow Web Configurator Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A local web page (`python3 web/server.py`, bound to 127.0.0.1) where the owner types a window opening and its options and gets:
- the dimensioned window and its checks as they type;
- every printable part, rendered on the Windows build box and shown in a built-in WebGL viewer;
- one zip with everything for that opening.

**Architecture:** The existing Python generator gains two optional params keys:
- `bed`: segment length follows the printer, and a new `bed_fit` check covers every part;
- `screen`: on or off.

Existing params files produce byte-identical output. A stdlib `http.server` in `web/` works as follows:
- it calls the generator in-process for previews (`web/api.py`, `web/drawing.py`);
- it runs `cad/box.sh render` in batches of six as a background job that can be cancelled;
- it builds the zip with `zipfile` (`web/zipper.py`).

The browser side is hand-written, with no libraries:
- `index.html` and `style.css`;
- `app.js`: the form, the SVG front view and the jobs;
- `viewer.js`: the WebGL STL viewer.

**Tech Stack:**
- Python 3 standard library only (`http.server`, `subprocess`, `threading`, `zipfile`, `unittest`), using the Mac's `python3` (3.14 when this plan was written).
- Plain HTML, CSS and ES-module JavaScript, with WebGL 1.
- OpenSCAD on the Windows box through the existing `cad/box.sh`.
- The Mac's Google Chrome, headless, for screenshots.

**Spec:** `docs/specs/2026-10-10-web-configurator-design.md`

---

## Execution status (2026-10-10)

- **Implemented, Tasks 0–15 done (including two review-fix rounds beyond this document's code, both approved).** Final checkpoint run 2026-10-10:
  - **Generator:** 213 Python tests pass in `tools/` (`cd tools && python3 -m unittest discover -p 'test_*.py'`). With no new params keys, `generate.py` and `build_bom.py` give byte-identical output for both reference windows (the compatibility check against `.web-baseline` is `BYTE-IDENTICAL`).
  - **Web:** 123 tests pass in `web/tests` (`python3 -m unittest discover -s web/tests -p 'test_*.py'`, about 48 s).
  - **OpenSCAD asserts:** `cad/box.sh test` reports `7 test files passed` and leaves `cad/generated/` on bench-600.
  - **Live renders on the real box (Task 13):** bench-600 end to end through `web/tests/live_render.py --cancel` came back `LIVE RENDER OK`: the mid-batch cancel ended the job `cancelled` with no `.generate.lock`, and the full render produced 37/37 parts whose STLs, plus the zip's other six files, matched the existing renders byte-identical.
  - **Screenshots (Task 14):** all seven UI-state screenshots (`web/tests/ui_shots.py`) were reviewed by eye against their checklists and pass, and the eight hand-driven interactions (debounced preview, invalid-name lockout, bed presets, screen toggle, render selected/all, cancel, download, viewer drag/zoom/assembled) were each verified in a live browser session against `--fake-render`.

## Decisions and spec gaps (found while planning)

| Spec says, or leaves open | Plan does | Why |
|---|---|---|
| `BED_MARGIN` is a new `dims.json` key, and the CLI output stays byte-identical | `generate.write()` leaves `BED_MARGIN` out of `cad/generated/dims.scad` | `dims.scad` mirrors every `dims.json` key, so the new key would add a line to a generated file. `BED_MARGIN` is only used in Python. If you'd rather keep the mirror complete, drop the `dims.pop("BED_MARGIN")` line (Task 2) and accept that one-line difference |
| `cad/box.sh render` is unchanged and "renders whatever the generator writes" | `generate.write()` writes `MAX_SEG = max_seg(bed)` into `dims.scad` | `cad/lib/segment.scad` asserts `len <= MAX_SEG`. With a bed bigger than the P1S, every longer segment would fail that assert. The default bed gives 240.0, which is unchanged. Verified with a live 500 mm-bed render |
| New check `bed_fit`, and byte-identical CLI output | `generate.py` prints the `bed_fit` line only when the params file has a `bed` key. The web preview, the zip README and the badges always include it | Without the key the output stays identical, and the old `segment_length` line already covers the P1S |
| Envelope table "from the reference STLs" | `tools/part_envelopes.py` reads `cad/stl/home-1800x1500` (igu) and `cad/stl/bench-600` (acrylic) | No reference render has twinwall beads. Their profile is 8 mm deeper (18 mm, not 10 mm), so the table under-states them. This can't matter: every cross-section is 70 mm or less, beds are at least 100 mm, and `check_stl` still checks the real STL against the bed |
| `bed_fit` as a check | Implemented as specified | Segments are split to `max_seg(bed)`, so they always fit. The largest fixed part is 100 mm long (setting blocks GF/GW). So `bed_fit` passes for every bed the web form accepts (100–500 mm). It is a safety net, and it does fail for smaller beds set in a params file by hand |
| Screen off: the BOM omits the 8g × 12 screws, the M4 × 10 pan screws and the M4 × 50 pins | Also omits the 4g × 12 screen-leaf (HS) screws | They are hinge hardware too, and their quantity would be 0 |
| `/api/box`: "a quick SSH echo" | New subcommand `cad/box.sh ping`, which runs `remote "echo ok"` | Rule: every ssh/scp goes through `box.sh`, which binds en0. `render` is untouched |
| `api.py` has `render_job(...)` | The job (thread, subprocess, cancel) is the `Job` class in `web/server.py`. `api.py` stays pure functions: validate, preview, save_params, part status, write_bom, build_zip | A job holds a process and a thread, not data. Keeping it out of `api.py` keeps that module unit-testable without HTTP |
| "After each batch it runs `check_stl.py` for those IDs" | The job calls `check_stl.check()` in-process for each ID, with the params bed | It is the same function the CLI runs. `box.sh render` still runs `check_stl.py` itself, and that output goes into the job log |
| "When everything has rendered, it runs `bom/build_bom.py <name>`" | Runs in-process through the same `build_bom` functions (`api.write_bom`) | Tests can then point it at a temporary folder. The output is identical: a unit test and the live run compare it with the CLI's files |
| (not covered) A part that fails to render keeps its old STL, because `box.sh render <ids>` doesn't clear them | The job deletes each batch's STLs just before rendering it | A failed part then shows as missing, instead of passing on an old file |
| The zip "needs a finished job for that name" | `/api/zip/<name>` gives 409 while a job for that name is running. It needs every part's STL on disk to pass the check (`?partial=1` otherwise) | Renders from an earlier session or from the CLI count too |
| (not covered) Rendering under an existing params file's name | `save_params` leaves an equivalent existing file untouched (same values once defaults are applied). It refuses to change `bench-600` or `home-1800x1500` | The unit tests read the reference params files |
| Job states idle/running/done/failed/cancelled | `done`: every part passed. `failed`: any part failed, or the box was unreachable. Parts the job never reached become `skipped` (failed job) or `cancelled` | The per-part states drive the row colours |
| Bound to 127.0.0.1 only | Also rejects a foreign `Host` header (403) and a POST that isn't JSON (415) | These stop DNS-rebinding and cross-site form posts from driving the box |
| Screenshots of the viewer and render states (§9.4) | The page reads form values and `view=<ID>` or `view=assembled` from the query string. `server.py --fake-render` renders box-shaped STLs into a temporary folder | Headless Chrome can't click. The query string also makes bookmarks possible |
| Assembled view: "frame, transom and sash instances" | Shows segments, corners, jamb nodes and transom shoes, placed with the transforms in `cad/assembly.scad` | The screen, beads and glass aren't shown |
| Suggested task order | `drawing.py` and `zipper.py` come before `api.py`, and `viewer.js` before `app.js`. `box.sh ping` gets its own task | `api.py` imports drawing and zipper, and `app.js` imports the viewer |

## Ground rules for whoever executes this

- **No git.** The user's rule: no git under `~` except one work repo. Every "commit" in the usual TDD loop is a **Checkpoint** step here: run the listed checks, and stop for review if any fails.
- **No installs on the Mac.** Use Python 3's standard library only. The browser side has no libraries, no CDN and no build step. Nothing is downloaded.
- **Network.** Every ssh/scp to the Windows box goes through `cad/box.sh`, which binds en0 because the work VPN takes over home-LAN routes. The server calls `box.sh` with argument lists, never a shell string.
- **No explanatory comments in code** beyond a one-line header (module docstring, or `//`/`/* */` first line). The reasons live in this plan.
- **Test method names** are camelCase `testXxx`, with no underscores.
- **Existing behaviour.** The 126 existing tests in `tools/` stay unchanged: new test classes are only appended. With no new params keys, `generate.py`/`build_bom.py` output stays byte-identical (checked against a baseline from Task 0).
- **Working folder.** Run every command from `~/diy-window`. Task 0 creates `.web-baseline/`, the checkpoints create `.web-after/`, and Task 15 deletes both.
- **Applying blocks.** **Create** means write the file with exactly the block's content. **Append to `X`** means insert the block before the `if __name__ == "__main__":` line of `X`, with two blank lines on each side. **Replace in `X`** means the first block occurs exactly once in `X`, and you replace it with the second block.

## File structure

```
~/diy-window/
  cad/dims.json                     + BED_MARGIN (16.0)
  cad/box.sh                        + `ping` subcommand
  tools/window.py                   max_seg(bed), DEFAULT_BED; split(limit); bed/max_seg/has_screen in the layout; screen members optional
  tools/generate.py                 split() callers use the bed limit; MAX_SEG in dims.scad; screen parts optional; bed_fit()
  tools/part_envelopes.py           NEW helper: writes part_envelopes.json from the reference STLs
  tools/part_envelopes.json         NEW per-part bounding boxes (segments: cross-section only)
  tools/check_stl.py                checks against the params bed
  bom/build_bom.py                  screen hardware optional
  tools/test_*.py                   new test classes appended; NEW test_part_envelopes.py
  docs/build-guide.md, docs/install-guide.md   screen-off notes
  README.md                         new params keys, web link, tests line, box.sh ping
  web/
    README.md                       how to run, requirements, troubleshooting
    server.py                       stdlib HTTP server, JSON API, render Job (batches, cancel), box status
    api.py                          pure functions: validate, preview, save_params, load, part status, write_bom, build_zip
    drawing.py                      SVG front-view geometry and assembled-view transforms
    zipper.py                       zip bytes and README.txt text
    fake_box.py                     stand-in for cad/box.sh (render | ping) for tests and --fake-render
    static/index.html, style.css    page layout
    static/app.js                   form, debounced preview, SVG, badges, table, jobs, downloads
    static/viewer.js                WebGL STL viewer (single part and assembled)
    tests/test_api.py, test_drawing.py, test_zipper.py, test_server.py   stdlib unittest
    tests/live_render.py            end-to-end render of bench-600 on the real box
    tests/ui_shots.py               headless-Chrome screenshots of the UI states
```

---

### Task 0: Baseline of today's generator output

The compatibility rule: with no new params keys, every file `generate.py` and `build_bom.py` write, and everything they print, stays byte-identical. This task records today's output once. Every generator task compares against it.

**Files:**
- Create: `.web-baseline/` (temporary, deleted in Task 15)

- [ ] **Step 1: Confirm the starting point**

Run: `cd ~/diy-window/tools && python3 -m unittest discover -p 'test_*.py' 2>&1 | grep -E '^(Ran|OK|FAILED)'`
Expected:
```
Ran 126 tests in 0.4s
OK
```

- [ ] **Step 2: Record the baseline**

Run:
```bash
cd ~/diy-window && rm -rf .web-baseline && mkdir .web-baseline
for n in bench-600 home-1800x1500; do
  python3 tools/generate.py params/$n.json > .web-baseline/$n.stdout
  python3 bom/build_bom.py $n >> .web-baseline/$n.stdout
  mkdir .web-baseline/$n && cp -R cad/generated .web-baseline/$n/ && cp bom/$n.* bom/$n-* .web-baseline/$n/
done
ls .web-baseline/bench-600
```
Expected: `bench-600-cutlist.csv  bench-600-glass.csv  bench-600-parts.csv  bench-600.csv  bench-600.md  generated`

The **compatibility check** used by later checkpoints re-runs the same commands into `.web-after/` and diffs:
```bash
cd ~/diy-window && rm -rf .web-after && mkdir .web-after
for n in bench-600 home-1800x1500; do
  python3 tools/generate.py params/$n.json > .web-after/$n.stdout
  python3 bom/build_bom.py $n >> .web-after/$n.stdout
  mkdir .web-after/$n && cp -R cad/generated .web-after/$n/ && cp bom/$n.* bom/$n-* .web-after/$n/
done
diff -r .web-baseline .web-after && echo BYTE-IDENTICAL
```
Expected: `BYTE-IDENTICAL` and no diff lines.

---

### Task 1: Bed size in the layout (`cad/dims.json`, `tools/window.py`)

`max_seg(bed) = min(bed_z, max(bed_x, bed_y)) − BED_MARGIN`. For the P1S (256³) that gives 240, today's `MAX_SEG`. `split()` takes the limit, and `layout()` reads `bed` from the params, defaulting to `[256, 256, 256]`. The defaults are never written into `lay["params"]`, because `generate.write()` saves that dict to `cad/generated/params.json`.

**Files:**
- Modify: `cad/dims.json` (after `MAX_SEG`)
- Modify: `tools/window.py` (`split`, `member`, `layout`)
- Test: `tools/test_window.py` (append `BedTest`)

- [ ] **Step 1: Write the failing tests**

**Append** to `tools/test_window.py`:
```python
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
```

- [ ] **Step 2: Run them to see them fail**

Run: `cd ~/diy-window/tools && python3 -m unittest test_window.BedTest 2>&1 | tail -3`
Expected: `FAILED (errors=7)`, with `AttributeError: module 'window' has no attribute 'max_seg'`, `KeyError: 'max_seg'` or `TypeError` from `split()`. `testExplicitP1sBedMatchesNoBedKey` already passes, because the `bed` key is ignored so far.

- [ ] **Step 3: Add `BED_MARGIN` to `cad/dims.json`**

**Replace** in `cad/dims.json`:
```json
  "MAX_SEG": 240.0,
```
**with:**
```json
  "MAX_SEG": 240.0,
  "BED_MARGIN": 16.0,
```

- [ ] **Step 4: Add `DEFAULT_BED` and `max_seg`, and give `split` a limit**

**Replace** in `tools/window.py`:
```python
MIN_FIXED = 150.0


def split(length, gap=0.0):
    if length <= 0:
        raise ValueError(f"member length must be positive, got {length}")
    n = max(1, math.ceil((length - gap) / (D["MAX_SEG"] + gap) - 1e-9))
```
**with:**
```python
MIN_FIXED = 150.0
DEFAULT_BED = [256, 256, 256]


def max_seg(bed):
    if len(bed) != 3 or min(bed) <= D["BED_MARGIN"]:
        raise ValueError(f"bed must be three sizes over {D['BED_MARGIN']:g} mm, got {bed}")
    return min(bed[2], max(bed[0], bed[1])) - D["BED_MARGIN"]


def split(length, gap=0.0, limit=None):
    limit = max_seg(DEFAULT_BED) if limit is None else limit
    if length <= 0:
        raise ValueError(f"member length must be positive, got {length}")
    n = max(1, math.ceil((length - gap) / (limit + gap) - 1e-9))
```

- [ ] **Step 5: Pass the limit through `member`**

**Replace** in `tools/window.py`:
```python
def member(name, length, profile, core, qty):
    gap = D["JOINT_GAP"] if profile in CORD_PROFILES else 0.0
    n, seg = split(length, gap)
```
**with:**
```python
def member(name, length, profile, core, qty, limit=None):
    gap = D["JOINT_GAP"] if profile in CORD_PROFILES else 0.0
    n, seg = split(length, gap, limit)
```

- [ ] **Step 6: Read the bed in `layout` and use it for every member**

The variable is `seg_max`, not `limit`: `layout()` already uses `limit` for the deflection limit further down.

**Replace** in `tools/window.py`:
```python
        raise ValueError(f"glazing must be one of {sorted(GLAZING_KG_M2)}, got {p['glazing']}")
    F, T, S, N = D["FRAME_W"], D["TRANSOM_W"], D["SASH_W"], D["SCREEN_W"]
```
**with:**
```python
        raise ValueError(f"glazing must be one of {sorted(GLAZING_KG_M2)}, got {p['glazing']}")
    bed = p.get("bed", DEFAULT_BED)
    seg_max = max_seg(bed)
    F, T, S, N = D["FRAME_W"], D["TRANSOM_W"], D["SASH_W"], D["SCREEN_W"]
```

**Replace** in `tools/window.py`:
```python
    screen_core = lambda length: "alu10" if split(length)[0] > 1 else None

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
```
**with:**
```python
    screen_core = lambda length: "alu10" if split(length, 0.0, seg_max)[0] > 1 else None

    members = [
        member("head", horiz, "sash_rebate", FRAME_CORE, 1, seg_max),
        member("sill", horiz, "sill", FRAME_CORE, 1, seg_max),
        member("jamb_lower", lower, "glazing", FRAME_CORE, 2, seg_max),
        member("jamb_upper", a, "sash_rebate", FRAME_CORE, 2, seg_max),
        member("transom", horiz, "transom", TRANSOM_CORE, 1, seg_max),
        member("sash_horizontal", sash_w - 2 * S, "sash", "alu20", 2, seg_max),
        member("sash_vertical", sash_h - 2 * S, "sash", "alu20", 2, seg_max),
        member("screen_horizontal", screen_w - 2 * N, "screen", screen_core(screen_w - 2 * N), 2, seg_max),
        member("screen_vertical", screen_h - 2 * N, "screen", screen_core(screen_h - 2 * N), 2, seg_max),
    ]
```

**Replace** in `tools/window.py`:
```python
    too_long = [m["name"] for m in members if m["seg"] > D["MAX_SEG"]]
```
**with:**
```python
    too_long = [m["name"] for m in members if m["seg"] > seg_max]
```

**Replace** in `tools/window.py`:
```python
            "sash_kg": round(sash_kg, 1), "stay": stay[0] if stay else None, "keeper_dz": keeper_dz,
            "checks": checks}
```
**with:**
```python
            "sash_kg": round(sash_kg, 1), "stay": stay[0] if stay else None, "keeper_dz": keeper_dz,
            "bed": bed, "max_seg": seg_max, "checks": checks}
```

- [ ] **Step 7: Run the tests to see them pass**

Run: `cd ~/diy-window/tools && python3 -m unittest test_window -v 2>&1 | tail -3`
Expected: `OK` (49 tests).

- [ ] **Step 8: Checkpoint**

Run: `cd ~/diy-window/tools && python3 -m unittest discover -p 'test_*.py' 2>&1 | grep -E '^(Ran|OK|FAILED)'`
Expected: `Ran 134 tests`, `OK`. Don't run the compatibility check yet: `dims.scad` carries the new `BED_MARGIN` line until Task 2.

---

### Task 2: Bed limit through the part list and `dims.scad` (`tools/generate.py`)

Beads, acrylic spacers and the sill nose call `split()` themselves, so they get the window's limit. `dims.scad` gets `MAX_SEG = max_seg(bed)` so that `cad/lib/segment.scad`'s `len <= MAX_SEG` assert follows the bed. `BED_MARGIN` stays out of `dims.scad`.

**Files:**
- Modify: `tools/generate.py` (`parts`, `write`)
- Test: `tools/test_generate.py` (append `load`, `BedPartsTest`, `WriteBedTest`)

- [ ] **Step 1: Write the failing tests**

**Append** to `tools/test_generate.py`:
```python
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
```

- [ ] **Step 2: Run them to see them fail**

Run: `cd ~/diy-window/tools && python3 -m unittest test_generate.BedPartsTest test_generate.WriteBedTest 2>&1 | tail -3`
Expected: `FAILED (failures=3)`. `testSmallBedAddsMiddleSegments` already passes, because the frame members come from `layout()`. The other three fail:
- `217.88 not less than or equal to 164.0 : NS`: the sill nose doesn't follow the bed yet;
- `'MAX_SEG = 484.0;\n' not found`;
- `'BED_MARGIN' unexpectedly found`.

- [ ] **Step 3: Use the bed limit in `parts()`**

**Replace** in `tools/generate.py`:
```python
    n_nose, s_nose = split(lay["w"] - 2 * NOSE_END, D["JOINT_GAP"])
```
**with:**
```python
    n_nose, s_nose = split(lay["w"] - 2 * NOSE_END, D["JOINT_GAP"], lay["max_seg"])
```

**Replace** in `tools/generate.py`:
```python
    for pid, run in runs:
        n, s = split(run)
```
**with:**
```python
    for pid, run in runs:
        n, s = split(run, limit=lay["max_seg"])
```

**Replace** in `tools/generate.py`:
```python
            for axis, run in (("H", gw - 2 * sw), ("V", gh - 2 * sw)):
                n, s = split(run)
```
**with:**
```python
            for axis, run in (("H", gw - 2 * sw), ("V", gh - 2 * sw)):
                n, s = split(run, limit=lay["max_seg"])
```

- [ ] **Step 4: Write the bed's `MAX_SEG` into `dims.scad`**

**Replace** in `tools/generate.py`:
```python
    (out / "dims.scad").write_text("".join(f"{k} = {json.dumps(v)};\n" for k, v in D.items()))
```
**with:**
```python
    dims = {**D, "MAX_SEG": lay["max_seg"]}
    dims.pop("BED_MARGIN")
    (out / "dims.scad").write_text("".join(f"{k} = {json.dumps(v)};\n" for k, v in dims.items()))
```

- [ ] **Step 5: Run the tests to see them pass**

Run: `cd ~/diy-window/tools && python3 -m unittest test_generate 2>&1 | tail -3`
Expected: `OK` (34 tests).

- [ ] **Step 6: Checkpoint**

Run: `cd ~/diy-window/tools && python3 -m unittest discover -p 'test_*.py' 2>&1 | grep -E '^(Ran|OK|FAILED)'`
Expected: `Ran 138 tests`, `OK`.

Then run the **compatibility check** (Task 0). Expected: `BYTE-IDENTICAL`.

---

### Task 3: Part envelopes and the `bed_fit` check

`bed_fit` asks whether every part's expected bounding box fits the bed in some rotation, comparing the sorted part sizes with the sorted bed sizes:
- segment-type parts (those with a `length`) use the profile cross-section × length;
- fixed-size parts use their full bounding box.

Both come from `tools/part_envelopes.json`, which a helper writes from the reference renders in `cad/stl/`. If the table is missing, `generate.py` loads an empty one, and `bed_fit` then fails every part with `(no envelope)`. That way the helper, which imports `generate`, can always rebuild the table.

**Files:**
- Create: `tools/part_envelopes.py`
- Create: `tools/part_envelopes.json` (written by the helper)
- Create: `tools/test_part_envelopes.py`
- Modify: `tools/generate.py` (`ENVELOPES`, `bed_fit`, `main`)
- Test: `tools/test_generate.py` (append `BedFitTest`)

- [ ] **Step 1: Write the failing helper tests**

**Create** `tools/test_part_envelopes.py`:
```python
"""Unit tests for tools/part_envelopes.py."""
import json
import unittest

import part_envelopes
import window


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
        self.assertEqual(part_envelopes.collect(window.ROOT, part_envelopes.REFERENCES), committed)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run them to see them fail**

Run: `cd ~/diy-window/tools && python3 -m unittest test_part_envelopes 2>&1 | tail -3`
Expected: `ModuleNotFoundError: No module named 'part_envelopes'`.

- [ ] **Step 3: Write the helper**

**Create** `tools/part_envelopes.py`:
```python
#!/usr/bin/env python3
"""Write tools/part_envelopes.json: each part's bounding box (segments: cross-section only) from the reference STLs."""
import json
import pathlib
import sys

import generate
import stl
import window

REFERENCES = ("home-1800x1500", "bench-600")
OUT = pathlib.Path(__file__).resolve().parent / "part_envelopes.json"
TOL = 0.6


def envelope(box, length):
    if length is None:
        return sorted(box)
    axis = min(range(3), key=lambda a: abs(box[a] - length))
    if abs(box[axis] - length) > TOL:
        raise ValueError(f"no axis of {box} matches length {length}")
    return sorted(box[a] for a in range(3) if a != axis)


def collect(root, names):
    env = {}
    for name in names:
        lay = window.layout(json.loads((root / "params" / f"{name}.json").read_text()))
        for pt in generate.parts(lay):
            e = envelope(stl.bbox(stl.load(root / "cad" / "stl" / name / f"{pt['id']}.stl")), pt["length"])
            env[pt["id"]] = [max(a, b) for a, b in zip(env.get(pt["id"], e), e)]
    return dict(sorted(env.items()))


def dumps(env):
    return "{\n" + ",\n".join(f"  {json.dumps(k)}: {json.dumps(v)}" for k, v in env.items()) + "\n}\n"


def main(argv):
    names = argv[1:] or list(REFERENCES)
    env = collect(window.ROOT, names)
    OUT.write_text(dumps(env))
    print(f"{OUT.name}: {len(env)} parts from {', '.join(names)}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
```

- [ ] **Step 4: Generate the table**

Run: `cd ~/diy-window/tools && python3 part_envelopes.py && cat part_envelopes.json`
Expected: `part_envelopes.json: 40 parts from home-1800x1500, bench-600`, then exactly:
```json
{
  "AC": [16.0, 27.0, 27.0],
  "AFH": [12.0, 16.0],
  "AFV": [12.0, 16.0],
  "ASH": [12.0, 16.0],
  "ASV": [12.0, 16.0],
  "BFH": [10.0, 19.8],
  "BFV": [10.0, 19.8],
  "BSH": [10.0, 19.8],
  "BSV": [10.0, 19.8],
  "CH": [58.0, 58.0, 63.0],
  "CMB": [9.0, 22.0, 40.0],
  "CMH": [10.0, 53.0, 86.151],
  "CN": [20.0, 30.0, 30.0],
  "CS": [50.0, 62.0, 62.0],
  "CSL": [58.0, 58.0, 63.0],
  "CSR": [58.0, 58.0, 63.0],
  "GF": [3.0, 24.0, 100.0],
  "GW": [6.795, 24.0, 100.0],
  "H": [58.0, 63.0],
  "HG": [25.0, 30.0, 40.0],
  "HS": [10.0, 24.0, 33.0],
  "JL": [58.0, 63.0],
  "JN": [40.0, 63.0, 70.0],
  "JU": [58.0, 63.0],
  "KP": [23.0, 34.5, 40.0],
  "NH": [20.0, 30.0],
  "NS": [18.8, 26.0],
  "NV": [20.0, 30.0],
  "S": [58.0, 63.0],
  "SB": [50.0, 62.0],
  "SBE": [50.0, 62.0],
  "SH": [50.0, 62.0],
  "SV": [50.0, 62.0],
  "SW": [58.0, 63.0],
  "T": [63.0, 70.0],
  "TC": [58.0, 60.0, 63.0],
  "TE": [63.0, 70.0],
  "TSL": [23.7, 63.0, 70.0],
  "TSR": [23.7, 63.0, 70.0],
  "WC": [7.0, 12.0, 30.0]
}
```

- [ ] **Step 5: Run the helper tests to see them pass**

Run: `cd ~/diy-window/tools && python3 -m unittest test_part_envelopes 2>&1 | tail -3`
Expected: `OK` (5 tests, about 1 s: the last one re-reads the 72 reference STLs).

- [ ] **Step 6: Write the failing `bed_fit` tests**

**Append** to `tools/test_generate.py`:
```python
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
        check = generate.bed_fit({"bed": [256, 60, 60]}, [{"id": "H", "length": 237.14}])
        self.assertEqual(check["msg"], "parts too big for the 256 x 60 x 60 mm bed: H 58 x 63 x 237.14")

    def testPartWithoutEnvelopeFails(self):
        check = generate.bed_fit({"bed": [256, 256, 256]}, [{"id": "ZZ", "length": None}])
        self.assertFalse(check["ok"])
        self.assertIn("ZZ (no envelope)", check["msg"])

    def testEnvelopeTableCoversEveryPartShape(self):
        variants = [load(n) for n in ("home-1800x1500.json", "bench-600.json")]
        variants += [dict(v, bed=[180, 180, 180]) for v in variants] + [dict(variants[0], glazing="twinwall")]
        for p in variants:
            for pt in generate.parts(window.layout(p)):
                self.assertEqual(len(generate.ENVELOPES[pt["id"]]), 2 if pt["length"] is not None else 3, pt["id"])
```

Run: `cd ~/diy-window/tools && python3 -m unittest test_generate.BedFitTest 2>&1 | tail -3`
Expected: `FAILED (errors=5)` with `AttributeError: module 'generate' has no attribute 'bed_fit'` or `'ENVELOPES'`.

- [ ] **Step 7: Load the table and add `bed_fit`**

**Replace** in `tools/generate.py`:
```python
NOSE_END = D["NOSE_KEY_X"] + D["NOSE_KEY_W"]
```
**with:**
```python
NOSE_END = D["NOSE_KEY_X"] + D["NOSE_KEY_W"]
ENVELOPE_FILE = pathlib.Path(__file__).resolve().parent / "part_envelopes.json"
ENVELOPES = json.loads(ENVELOPE_FILE.read_text()) if ENVELOPE_FILE.exists() else {}
```

**Replace** in `tools/generate.py`:
```python
    return out


def write_parts(plist, path):
```
**with:**
```python
    return out


def bed_fit(lay, plist):
    bed = lay["bed"]
    bad = []
    for pt in plist:
        env = ENVELOPES.get(pt["id"])
        if env is None:
            bad.append(f"{pt['id']} (no envelope)")
            continue
        size = env + ([pt["length"]] if pt["length"] is not None else [])
        if any(a > b for a, b in zip(sorted(size), sorted(bed))):
            bad.append(f"{pt['id']} {' x '.join(f'{v:g}' for v in size)}")
    text = " x ".join(f"{v:g}" for v in bed)
    msg = f"parts too big for the {text} mm bed: {', '.join(bad)}" if bad else f"every part fits the {text} mm bed"
    return {"name": "bed_fit", "ok": not bad, "msg": msg}


def write_parts(plist, path):
```

- [ ] **Step 8: Print `bed_fit` from the CLI only when the params name a bed**

**Replace** in `tools/generate.py`:
```python
    for c in lay["checks"]:
```
**with:**
```python
    checks = lay["checks"] + ([bed_fit(lay, plist)] if "bed" in params else [])
    for c in checks:
```

- [ ] **Step 9: Run the tests to see them pass**

Run: `cd ~/diy-window/tools && python3 -m unittest test_generate test_part_envelopes 2>&1 | tail -3`
Expected: `OK` (44 tests).

- [ ] **Step 10: Checkpoint**

Run: `cd ~/diy-window/tools && python3 -m unittest discover -p 'test_*.py' 2>&1 | grep -E '^(Ran|OK|FAILED)'`
Expected: `Ran 148 tests`, `OK`.

Then run the **compatibility check**. Expected: `BYTE-IDENTICAL`.

Then check the new CLI line with a bed key (written to `.web-after/`, not `params/`):
```bash
cd ~/diy-window && python3 -c "import json; p = json.load(open('params/bench-600.json')); p['bed'] = [180, 180, 180]; open('.web-after/bed180.json', 'w').write(json.dumps(p))" && python3 tools/generate.py .web-after/bed180.json | tail -2 && python3 tools/generate.py params/bench-600.json > /dev/null
```
Expected:
```
ok       keeper bosses 30.67 mm either side of the SBE middle, over the cams (allowed 20.6-41.7 mm, transom needs 2+ segments)
ok       every part fits the 180 x 180 x 180 mm bed
```
The last command puts `cad/generated/` back to the bench window.

---

### Task 4: `check_stl` uses the params bed (`tools/check_stl.py`)

`check()` gains a `bed` argument, defaulting to the P1S, and fits the STL's bounding box in any rotation. `main()` reads the bed from `cad/generated/params.json`. A cubic bed keeps the old message (`does not fit the 256 mm bed`).

**Files:**
- Modify: `tools/check_stl.py`
- Test: `tools/test_stl.py` (append `BedCheckTest`)

- [ ] **Step 1: Write the failing tests**

**Append** to `tools/test_stl.py`:
```python
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
```

- [ ] **Step 2: Run them to see them fail**

Run: `cd ~/diy-window/tools && python3 -m unittest test_stl.BedCheckTest 2>&1 | tail -3`
Expected: `FAILED (failures=1, errors=2)`. The errors are `TypeError: check() takes 2 positional arguments but 3 were given`, and `testMainUsesTheGeneratedParamsBed` fails with `0 != 1`.

- [ ] **Step 3: Implement**

**Replace** in `tools/check_stl.py`:
```python
import stl

ROOT = pathlib.Path(__file__).resolve().parent.parent
BED = 256.0
TOL = 0.6


def check(row, stl_dir):
```
**with:**
```python
import stl
from window import DEFAULT_BED

ROOT = pathlib.Path(__file__).resolve().parent.parent
TOL = 0.6


def bed_text(bed):
    return f"{bed[0]:.0f}" if len(set(bed)) == 1 else " x ".join(f"{v:g}" for v in bed)


def check(row, stl_dir, bed=DEFAULT_BED):
```

**Replace** in `tools/check_stl.py`:
```python
    if max(box) > BED:
        errors.append(f"{row['id']}: {box} does not fit the {BED:.0f} mm bed")
```
**with:**
```python
    if any(a > b for a, b in zip(sorted(box), sorted(bed))):
        errors.append(f"{row['id']}: {box} does not fit the {bed_text(bed)} mm bed")
```

**Replace** in `tools/check_stl.py`:
```python
    params_path = root / "cad" / "generated" / "params.json"
    if params_path.exists():
        generated_name = json.loads(params_path.read_text()).get("name")
        if generated_name != name:
            print(f"generated output is for {generated_name!r}, not {name!r}; rerun generate.py first",
                  file=sys.stderr)
            return 2
```
**with:**
```python
    params_path = root / "cad" / "generated" / "params.json"
    params = json.loads(params_path.read_text()) if params_path.exists() else {"name": name}
    if params.get("name") != name:
        print(f"generated output is for {params.get('name')!r}, not {name!r}; rerun generate.py first",
              file=sys.stderr)
        return 2
```

**Replace** in `tools/check_stl.py`:
```python
    errors = [e for r in rows for e in check(r, root / "cad" / "stl" / name)]
```
**with:**
```python
    errors = [e for r in rows for e in check(r, root / "cad" / "stl" / name, params.get("bed", DEFAULT_BED))]
```

- [ ] **Step 4: Run the tests to see them pass**

Run: `cd ~/diy-window/tools && python3 -m unittest test_stl 2>&1 | tail -3`
Expected: `OK` (29 tests). The `FAIL H: ... 20 mm bed` and `1/1 parts ok` lines are printed by `check_stl.main` inside the tests.

- [ ] **Step 5: Checkpoint**

Run: `cd ~/diy-window/tools && python3 -m unittest discover -p 'test_*.py' 2>&1 | grep -E '^(Ran|OK|FAILED)'`
Expected: `Ran 152 tests`, `OK`.

Then run: `cd ~/diy-window && python3 tools/generate.py params/bench-600.json > /dev/null && python3 tools/check_stl.py bench-600 | tail -1`
Expected: `37/37 parts ok`.

---

### Task 5: Screen on/off (`tools/window.py`, `tools/generate.py`, `bom/build_bom.py`, guides)

`screen` defaults to `true`. With `false`:
- `layout()` drops the two screen members, and with them their alu10 tubes;
- `parts()` drops `NH`, `NV`, `CN`, `HG` and `HS`, and the `H` segments get `bosses=false`;
- the BOM drops the Screen group (strips A and B, mesh, spline, epoxy), the 8g × 12 screen screws, the M4 × 10 pan screws, the M4 × 50 pins, the 4g × 12 leaf screws and the `H` insert pairs.

The frame magnet channel stays in the profiles.

**Files:**
- Modify: `tools/window.py`, `tools/generate.py`, `bom/build_bom.py`
- Modify: `docs/build-guide.md` (§6), `docs/install-guide.md` (steps 7.2 and 12)
- Test: `tools/test_window.py` (append `ScreenOffTest`), `tools/test_generate.py` (append `ScreenOffPartsTest`), `tools/test_bom.py` (append `ScreenOffBomTest`)

- [ ] **Step 1: Write the failing tests**

**Append** to `tools/test_window.py`:
```python
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
```

**Append** to `tools/test_generate.py`:
```python
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
```

**Append** to `tools/test_bom.py`:
```python
class ScreenOffBomTest(unittest.TestCase):
    def setUp(self):
        on = load("bench-600")
        off = window.layout(dict(on["params"], screen=False))
        self.on = {i["item"]: i for i in build_bom.hardware(on, generate.parts(on))}
        self.off = {i["item"]: i for i in build_bom.hardware(off, generate.parts(off))}

    def testScreenGroupIsOmitted(self):
        self.assertFalse([i for i in self.off.values() if i["group"] == "Screen"])

    def testScreenFixingsAreOmitted(self):
        self.assertFalse([k for k in self.off if k.startswith(build_bom.SCREEN_ONLY)])

    def testHeadInsertPairsAreOmitted(self):
        self.assertEqual(self.off["M4 heat-set insert for a 5.6 x 8 mm hole"]["qty"], 16)

    def testScreenTubeIsOmitted(self):
        self.assertFalse([k for k in self.off if k.startswith("Tube alu10")])

    def testEverythingElseIsUnchanged(self):
        dropped = {k for k in self.on if k not in self.off}
        self.assertEqual(len(dropped), 10)
        for k, item in self.off.items():
            if not k.startswith("M4 heat-set insert"):
                self.assertEqual(item, self.on[k], k)
```

- [ ] **Step 2: Run them to see them fail**

Run: `cd ~/diy-window/tools && python3 -m unittest test_window.ScreenOffTest test_generate.ScreenOffPartsTest test_bom.ScreenOffBomTest 2>&1 | tail -3`
Expected: `Ran 13 tests`, `FAILED (failures=10, errors=2)`. The errors are `KeyError: 'has_screen'` and `AttributeError: module 'build_bom' has no attribute 'SCREEN_ONLY'`. `testOtherPartsAreUnchanged` already passes.

- [ ] **Step 3: Make the screen members optional in `layout()`**

**Replace** in `tools/window.py`:
```python
    seg_max = max_seg(bed)
    F, T, S, N = D["FRAME_W"], D["TRANSOM_W"], D["SASH_W"], D["SCREEN_W"]
```
**with:**
```python
    seg_max = max_seg(bed)
    has_screen = p.get("screen", True)
    if not isinstance(has_screen, bool):
        raise ValueError(f"screen must be true or false, got {has_screen}")
    F, T, S, N = D["FRAME_W"], D["TRANSOM_W"], D["SASH_W"], D["SCREEN_W"]
```

**Replace** in `tools/window.py`:
```python
        member("sash_vertical", sash_h - 2 * S, "sash", "alu20", 2, seg_max),
        member("screen_horizontal", screen_w - 2 * N, "screen", screen_core(screen_w - 2 * N), 2, seg_max),
        member("screen_vertical", screen_h - 2 * N, "screen", screen_core(screen_h - 2 * N), 2, seg_max),
    ]
```
**with:**
```python
        member("sash_vertical", sash_h - 2 * S, "sash", "alu20", 2, seg_max),
    ]
    if has_screen:
        members += [
            member("screen_horizontal", screen_w - 2 * N, "screen", screen_core(screen_w - 2 * N), 2, seg_max),
            member("screen_vertical", screen_h - 2 * N, "screen", screen_core(screen_h - 2 * N), 2, seg_max),
        ]
```

**Replace** in `tools/window.py`:
```python
            "bed": bed, "max_seg": seg_max, "checks": checks}
```
**with:**
```python
            "bed": bed, "max_seg": seg_max, "has_screen": has_screen, "checks": checks}
```

The screen tubes need no change: the tube loop only adds tubes for screen members that exist. `lay["screen"]` (the screen's size) stays in the layout because `layout.scad` writes it.

- [ ] **Step 4: Make the screen parts optional in `parts()`**

**Replace** in `tools/generate.py`:
```python
NOSE_END = D["NOSE_KEY_X"] + D["NOSE_KEY_W"]
ENVELOPE_FILE = pathlib.Path(__file__).resolve().parent / "part_envelopes.json"
ENVELOPES = json.loads(ENVELOPE_FILE.read_text()) if ENVELOPE_FILE.exists() else {}
```
**with:**
```python
NOSE_END = D["NOSE_KEY_X"] + D["NOSE_KEY_W"]
SCREEN_PARTS = {"NH", "NV", "CN", "HG", "HS"}
ENVELOPE_FILE = pathlib.Path(__file__).resolve().parent / "part_envelopes.json"
ENVELOPES = json.loads(ENVELOPE_FILE.read_text()) if ENVELOPE_FILE.exists() else {}
```

**Replace** in `tools/generate.py`:
```python
    seg("H", "head", "sash_rebate", m["head"]["n"], bosses=True)
```
**with:**
```python
    seg("H", "head", "sash_rebate", m["head"]["n"], bosses=lay["has_screen"])
```

**Replace** in `tools/generate.py`:
```python
    seg("NH", "screen_horizontal", "screen", 2 * m["screen_horizontal"]["n"], "interior")
    seg("NV", "screen_vertical", "screen", 2 * m["screen_vertical"]["n"], "interior")
```
**with:**
```python
    if lay["has_screen"]:
        seg("NH", "screen_horizontal", "screen", 2 * m["screen_horizontal"]["n"], "interior")
        seg("NV", "screen_vertical", "screen", 2 * m["screen_vertical"]["n"], "interior")
```

**Replace** in `tools/generate.py`:
```python
        part("TC", "test_coupon", '"TC"', 1),
    ]
```
**with:**
```python
        part("TC", "test_coupon", '"TC"', 1),
    ]
    if not lay["has_screen"]:
        out = [pt for pt in out if pt["id"] not in SCREEN_PARTS]
```

With the screen on, `bosses=lay["has_screen"]` still writes `bosses=true`, so the `H` call is unchanged.

- [ ] **Step 5: Make the screen hardware optional in the BOM**

**Replace** in `bom/build_bom.py`:
```python
STAY_ARM_SCREWS = 3
```
**with:**
```python
STAY_ARM_SCREWS = 3
SCREEN_ONLY = ("Self-tapping screw 8g x 12", "M4 x 10 pan", "M4 x 50 bolt", "4g x 12")
```

**Replace** in `bom/build_bom.py`:
```python
    hinges = q["HG"]
```
**with:**
```python
    hinges = q.get("HG", 0)
    bossed = {"H", "TE"} if lay["has_screen"] else {"TE"}
```

**Replace** in `bom/build_bom.py`:
```python
         2 * total({"H", "TE"}) + (4 if lay["keeper_dz"] else 2) * q["SBE"] + q["CMB"] + 2 * q["TC"], "pcs"),
```
**with:**
```python
         2 * total(bossed) + (4 if lay["keeper_dz"] else 2) * q["SBE"] + q["CMB"] + 2 * q["TC"], "pcs"),
```

**Replace** in `bom/build_bom.py`:
```python
        ("Screen", "Two-part epoxy, 5-minute (screen corner joints)", 1, "pcs"),
    ]
```
**with:**
```python
        ("Screen", "Two-part epoxy, 5-minute (screen corner joints)", 1, "pcs"),
    ]
    if not lay["has_screen"]:
        items = [it for it in items if it[0] != "Screen" and not it[1].startswith(SCREEN_ONLY)]
```

The screen tube line disappears by itself, because the layout no longer lists alu10 tubes.

- [ ] **Step 6: Run the tests to see them pass**

Run: `cd ~/diy-window/tools && python3 -m unittest test_window test_generate test_bom 2>&1 | tail -3`
Expected: `OK` (131 tests).

- [ ] **Step 7: Note the skipped steps in the guides**

**Replace** in `docs/build-guide.md`:
```markdown
## 6. Screen
1. **Rails.**
```
**with:**
```markdown
## 6. Screen

Skip this section if your params file has `"screen": false`: the part list, cut list and BOM then carry no screen parts, tubes or hardware.

1. **Rails.**
```

**Replace** in `docs/install-guide.md`:
```markdown
   2. **Magnet strip B.** Press it into the frame magnet channel
```
**with:**
```markdown
   2. **Magnet strip B.** Skip it if your params file has `"screen": false`. Press it into the frame magnet channel
```

**Replace** in `docs/install-guide.md`:
```markdown
12. **Screen.**
```
**with:**
```markdown
12. **Screen.** Skip this step if your params file has `"screen": false`.
```

- [ ] **Step 8: Checkpoint**

Run: `cd ~/diy-window/tools && python3 -m unittest discover -p 'test_*.py' 2>&1 | grep -E '^(Ran|OK|FAILED)'`
Expected: `Ran 165 tests`, `OK`.

Then run the **compatibility check**. Expected: `BYTE-IDENTICAL`.

---

### Task 6: `cad/box.sh ping`

`/api/box` needs a quick reachability test that goes through `box.sh`, so that it binds en0 like every other SSH call. `render`, `test` and `png` stay unchanged.

**Files:**
- Modify: `cad/box.sh` (header line, usage line, `case`)

- [ ] **Step 1: Add the subcommand**

**Replace** in `cad/box.sh`:
```sh
# cad/box.sh: run OpenSCAD on the Windows build box (render | test | png)
```
**with:**
```sh
# cad/box.sh: run OpenSCAD on the Windows build box (render | test | png | ping)
```

**Replace** in `cad/box.sh`:
```sh
cmd=${1:?usage: box.sh render|test|png ...}
```
**with:**
```sh
cmd=${1:?usage: box.sh render|test|png|ping ...}
```

**Replace** in `cad/box.sh`:
```sh
  png) png "$@" ;;
```
**with:**
```sh
  png) png "$@" ;;
  ping) remote "echo ok" ;;
```

- [ ] **Step 2: Check it against the box and against an address that never answers**

Run: `cd ~/diy-window && cad/box.sh ping; echo "exit $?"`
Expected (box on): `ok`, then `exit 0`, in about 2 s.

Run: `cd ~/diy-window && BOX_HOST=alees@192.0.2.1 cad/box.sh ping; echo "exit $?"`
Expected, after the 10 s connect timeout: `ssh: connect to host 192.0.2.1 port 22: Operation timed out`, then `exit 255`. `192.0.2.1` is the TEST-NET-1 documentation address.

- [ ] **Step 3: Checkpoint**

Run: `cd ~/diy-window && cad/box.sh test`
Expected: `7 test files passed`. This runs the OpenSCAD asserts on the box, including `smoke_test.scad`'s `MAX_SEG == 240`, which checks that the default-bed `dims.scad` is unchanged.

---

### Task 7: Front-view and assembly geometry (`web/drawing.py`)

Pure geometry from `layout()`, in window coordinates: x to the right and y up, in mm, with the origin at the bottom-left of the frame. The opening starts at `-fix_gap`.
- `front(lay)` returns:
  - `rects`: each `kind` is `opening`, `frame`, `transom`, `glass`, `sash`, `sash-glass` or `screen`;
  - `dims`: dimension lines. Each has `axis`, the measured span `a`–`b`, `from` (the edge the extension lines start at), `at` (where the line is drawn) and `text`;
  - `labels`, plus `bounds` and `step` for the SVG viewBox and the font size.
- `assembly(lay, plist)` returns `[{id, m}]`. `m` is a row-major 4 × 4 matrix that places that part's STL in the window, following `cad/assembly.scad`:
  - world X runs across the window, Y through the wall (0 = outside face) and Z up;
  - segments are spaced by their joint gaps along each run;
  - `TSR` is placed by undoing the `mirrored=true` flip that turns it into `TSL`.

**Files:**
- Create: `web/drawing.py`
- Test: `web/tests/test_drawing.py`

- [ ] **Step 1: Write the failing tests**

**Create** `web/tests/test_drawing.py`:
```python
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


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run them to see them fail**

Run: `cd ~/diy-window && python3 -m unittest discover -s web/tests -p 'test_drawing.py' 2>&1 | tail -3`
Expected: `FAILED (errors=1)` after `ModuleNotFoundError: No module named 'drawing'`.

- [ ] **Step 3: Implement**

**Create** `web/drawing.py`:
```python
"""Window geometry for the browser: the dimensioned front view and the assembled-view part placements."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "tools"))

from window import D  # noqa: E402

I4 = [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]
MX = [[-1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]
MZ = [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, -1, 0], [0, 0, 0, 1]]


def fmt(v):
    return f"{v:g}"


def rect(kind, x, y, w, h):
    return {"kind": kind, "x": x, "y": y, "w": w, "h": h}


def front(lay):
    p = lay["params"]
    F, T = D["FRAME_W"], D["TRANSOM_W"]
    g, w, h, tc = p["fix_gap"], lay["w"], lay["h"], lay["transom_c"]
    tb = tc - T / 2
    sx, sy = D["FRAME_BODY"] + D["SASH_GAP"], tc + D["TRANSOM_HALF_BODY"] + D["SASH_GAP"]
    sw, sh = lay["sash"]
    fgw, fgh = lay["glass"]["fixed"]
    sgw, sgh = lay["glass"]["sash"]
    rects = [
        rect("opening", -g, -g, w + 2 * g, h + 2 * g),
        rect("frame", 0, h - F, w, F),
        rect("frame", 0, 0, w, F),
        rect("frame", 0, F, F, h - 2 * F),
        rect("frame", w - F, F, F, h - 2 * F),
        rect("transom", F, tb, w - 2 * F, T),
        rect("glass", D["GLASS_EDGE"], D["GLASS_EDGE"], fgw, fgh),
        rect("sash", sx, sy, sw, sh),
        rect("sash-glass", sx + D["SASH_GLASS"], sy + D["SASH_GLASS"], sgw, sgh),
    ]
    if lay["has_screen"]:
        scw, sch = lay["screen"]
        top = h - D["FRAME_BODY"] + D["SCREEN_OVERLAP"]
        rects.append(rect("screen", D["FRAME_BODY"] - D["SCREEN_OVERLAP"], top - sch, scw, sch))
    step = round(max(w, h) * 0.06)
    left, right = -g - step, w + g + step
    dims = [
        {"axis": "x", "a": -g, "b": w + g, "from": -g, "at": -g - 2 * step, "text": f"opening {fmt(p['opening_w'])}"},
        {"axis": "x", "a": 0, "b": w, "from": 0, "at": -g - step, "text": f"frame {fmt(w)}"},
        {"axis": "y", "a": -g, "b": h + g, "from": -g, "at": left - step, "text": f"opening {fmt(p['opening_h'])}"},
        {"axis": "y", "a": 0, "b": h, "from": 0, "at": left, "text": f"frame {fmt(h)}"},
        {"axis": "y", "a": 0, "b": tc, "from": w, "at": right, "text": f"transom centre {fmt(tc)}"},
        {"axis": "y", "a": tb + T, "b": h - F, "from": w, "at": right + step, "text": f"awning {fmt(p['awning_h'])}"},
        {"axis": "y", "a": F, "b": tb, "from": w, "at": right + step, "text": f"fixed {fmt(tb - F)}"},
    ]
    labels = [
        {"x": w / 2, "y": (F + tb) / 2, "text": f"fixed glass {fgw} x {fgh}"},
        {"x": w / 2, "y": sy + sh / 2, "text": f"sash {fmt(sw)} x {fmt(sh)}, glass {sgw} x {sgh}"},
    ]
    margin = step * 1.5
    bounds = [left - step - margin, -g - 2 * step - margin, right + step + margin, h + g + margin]
    return {"rects": rects, "dims": dims, "labels": labels, "bounds": bounds, "step": step}


def mul(a, b):
    return [[sum(a[i][k] * b[k][j] for k in range(4)) for j in range(4)] for i in range(4)]


def chain(*ms):
    out = I4
    for m in ms:
        out = mul(out, m)
    return out


def move(x, y, z):
    return [[1, 0, 0, x], [0, 1, 0, y], [0, 0, 1, z], [0, 0, 0, 1]]


def run(rows):
    return [list(r) for r in rows] + [[0, 0, 0, 1]]


def flat(m):
    return [round(v, 4) + 0.0 for row in m for v in row]


def assembly(lay, plist):
    F, TW, S = D["FRAME_W"], D["TRANSOM_W"], D["SASH_W"]
    W, H = lay["w"], lay["h"]
    tb = lay["transom_c"] - TW / 2
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
    shoe = run([[0, 0, 1, D["FRAME_BODY"]], [0, 1, 0, 0], [-1, 0, 0, TW]])
    shoe_flip = run([[-1, 0, 0, TW], [0, 1, 0, 0], [0, 0, 1, 0]])
    fixed = [
        ("CSL", I4), ("CSR", move(W, 0, 0)),
        ("CH", chain(move(0, 0, H), MZ)), ("CH", chain(move(W, 0, H), MX, MZ)),
        ("JN", move(0, 0, tb)), ("JN", chain(move(W, 0, tb), MX)),
        ("TSL", chain(move(0, 0, tb), shoe)), ("TSR", chain(move(W, 0, tb), MX, shoe, shoe_flip)),
        ("CS", move(sx, 0, sy)), ("CS", chain(move(sx + sw, 0, sy), MX)),
        ("CS", chain(move(sx, 0, sy + sh), MZ)), ("CS", chain(move(sx + sw, 0, sy + sh), MX, MZ)),
    ]
    ids = {pt["id"] for pt in plist}
    out += [{"id": pid, "m": flat(mat)} for pid, mat in fixed if pid in ids]
    return [x for x in out if x["id"] in ids]
```

- [ ] **Step 4: Run the tests to see them pass**

Run: `cd ~/diy-window && python3 -m unittest discover -s web/tests -p 'test_drawing.py' 2>&1 | tail -3`
Expected: `Ran 20 tests`, `OK`.

- [ ] **Step 5: Checkpoint**

Run: `cd ~/diy-window/tools && python3 -m unittest discover -p 'test_*.py' 2>&1 | grep -E '^(Ran|OK|FAILED)'`
Expected: `Ran 165 tests`, `OK`. `web/` only reads the generator.

---

### Task 8: Zip and README text (`web/zipper.py`)

`readme(name, params, checks, missing)` writes the zip's `README.txt`. It starts with a "CHECKS FAILED — do not print" block when any check failed, then a "PARTIAL ZIP — …" block when parts are missing. After those come the window summary, all check results, a print-settings summary (from `docs/printing.md`, with the tier's material from `build_bom.MATERIAL`), the file list and pointers to the guides. Older params files without `screen` or `bed` read as screen on and the P1S bed. `build(files)` deflates `{arcname: bytes or str}` into zip bytes, in the given order.

**Files:**
- Create: `web/zipper.py`
- Test: `web/tests/test_zipper.py`

- [ ] **Step 1: Write the failing tests**

**Create** `web/tests/test_zipper.py`:
```python
"""Unit tests for web/zipper.py."""
import io
import pathlib
import sys
import unittest
import zipfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

import zipper  # noqa: E402

PARAMS = {"name": "my-window", "opening_w": 1800, "opening_h": 1500, "fix_gap": 8, "awning_h": 450, "glazing": "igu",
          "tier": 3, "screen": True, "bed": [256, 256, 256]}
OK = [{"name": "transom_deflection", "ok": True, "msg": "transom deflects 6.2 mm"},
      {"name": "bed_fit", "ok": True, "msg": "every part fits the 256 x 256 x 256 mm bed"}]
BAD = [{"name": "transom_deflection", "ok": False, "msg": "transom deflects 12.6 mm"}, OK[1]]


class ReadmeTest(unittest.TestCase):
    def testAllOkStartsWithTheWindow(self):
        text = zipper.readme("my-window", PARAMS, OK, [])
        self.assertTrue(text.startswith("OpenWindow: my-window\n\nOpening 1800 x 1500 mm, fixing gap 8 mm, awning 450 mm, "
                                        "glazing igu, tier 3, screen yes, bed 256 x 256 x 256 mm.\n"))
        self.assertNotIn("CHECKS FAILED", text)
        self.assertNotIn("PARTIAL", text)

    def testCheckLines(self):
        text = zipper.readme("my-window", PARAMS, BAD, [])
        self.assertIn("  FAIL  transom_deflection: transom deflects 12.6 mm\n", text)
        self.assertIn("  ok    bed_fit: every part fits the 256 x 256 x 256 mm bed\n", text)

    def testFailedChecksBlockComesFirst(self):
        text = zipper.readme("my-window", PARAMS, BAD, [])
        self.assertTrue(text.startswith("CHECKS FAILED — do not print\n\n  - transom_deflection: transom deflects 12.6 mm\n\n"))

    def testPartialBlockListsTheMissingParts(self):
        text = zipper.readme("my-window", PARAMS, OK, ["H", "JL"])
        self.assertTrue(text.startswith("PARTIAL ZIP — these parts are missing or failed their STL check and are not in "
                                        "stl/:\n\n  H, JL\n\nOpenWindow: my-window\n"))

    def testFailedChecksThenPartial(self):
        text = zipper.readme("my-window", PARAMS, BAD, ["H"])
        self.assertLess(text.index("CHECKS FAILED"), text.index("PARTIAL ZIP"))
        self.assertLess(text.index("PARTIAL ZIP"), text.index("OpenWindow: my-window"))

    def testMaterialFollowsTheTier(self):
        self.assertIn("Exterior parts: ASA-CF or PC-ABS (light colour) (tier 3). Interior parts: PETG.",
                      zipper.readme("my-window", PARAMS, OK, []))
        self.assertIn("Exterior parts: ASA (tier 2).", zipper.readme("my-window", dict(PARAMS, tier=2), OK, []))

    def testOldParamsFileWithoutNewKeys(self):
        old = {k: v for k, v in PARAMS.items() if k not in ("screen", "bed")}
        self.assertIn("screen yes, bed 256 x 256 x 256 mm.", zipper.readme("my-window", old, OK, []))

    def testScreenOffNote(self):
        text = zipper.readme("my-window", dict(PARAMS, screen=False), OK, [])
        self.assertIn("screen no,", text)
        self.assertTrue(text.endswith("  No screen: skip the screen steps in the build and install guides.\n"))

    def testPointsToTheGuides(self):
        text = zipper.readme("my-window", PARAMS, OK, [])
        self.assertIn("OpenWindow-Guide.pdf", text)
        self.assertIn("docs/printing.md, docs/build-guide.md, docs/install-guide.md, docs/user-manual.md", text)


class BuildTest(unittest.TestCase):
    def testZipKeepsOrderAndContent(self):
        data = zipper.build({"README.txt": "CHECKS FAILED — do not print\n", "stl/H_x2.stl": b"\0\1\2"})
        z = zipfile.ZipFile(io.BytesIO(data))
        self.assertEqual(z.namelist(), ["README.txt", "stl/H_x2.stl"])
        self.assertEqual(z.read("stl/H_x2.stl"), b"\0\1\2")
        self.assertEqual(z.read("README.txt").decode("utf-8"), "CHECKS FAILED — do not print\n")
        self.assertEqual(z.getinfo("stl/H_x2.stl").compress_type, zipfile.ZIP_DEFLATED)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run them to see them fail**

Run: `cd ~/diy-window && python3 -m unittest discover -s web/tests -p 'test_zipper.py' 2>&1 | tail -3`
Expected: `FAILED (errors=1)` after `ModuleNotFoundError: No module named 'zipper'`.

- [ ] **Step 3: Implement**

**Create** `web/zipper.py`:
```python
"""The download zip for one window, and the README.txt that goes in it."""
import io
import pathlib
import sys
import zipfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "bom"))

import build_bom  # noqa: E402

FILES = [
    ("stl/", "one STL per part type, named <ID>_x<qty>.stl: print <qty> of each"),
    ("parts.csv", "the print list: id, qty, role (exterior/interior), length"),
    ("cutlist.csv", "tube cut list"),
    ("glass.csv", "glass or acrylic sizes"),
    ("BOM.md", "bill of materials, cut list, glass and filament estimate"),
    ("params.json", "the params file; copy it to params/<name>.json to regenerate or re-render"),
]


def readme(name, params, checks, missing):
    lines = []
    failed = [c for c in checks if not c["ok"]]
    if failed:
        lines += ["CHECKS FAILED — do not print", ""]
        lines += [f"  - {c['name']}: {c['msg']}" for c in failed] + [""]
    if missing:
        lines += ["PARTIAL ZIP — these parts are missing or failed their STL check and are not in stl/:", "",
                  f"  {', '.join(missing)}", ""]
    bed = params.get("bed", [256, 256, 256])
    screen = params.get("screen", True)
    tier = params["tier"]
    lines += [
        f"OpenWindow: {name}",
        "",
        f"Opening {params['opening_w']:g} x {params['opening_h']:g} mm, fixing gap {params['fix_gap']:g} mm, "
        f"awning {params['awning_h']:g} mm, glazing {params['glazing']}, tier {tier}, "
        f"screen {'yes' if screen else 'no'}, bed {' x '.join(f'{v:g}' for v in bed)} mm.",
        "",
        "Checks",
    ]
    lines += [f"  {'ok  ' if c['ok'] else 'FAIL'}  {c['name']}: {c['msg']}" for c in checks]
    lines += [
        "",
        "Print settings (full detail: docs/printing.md)",
        "  - 0.4 mm nozzle, 0.2 mm layers, 5 walls, 5 top and 5 bottom layers, 15% gyroid infill.",
        f"  - Exterior parts: {build_bom.MATERIAL[tier]} (tier {tier}). Interior parts: {build_bom.MATERIAL['interior']}.",
        "  - Segments stand on an end face exactly as exported, no supports. Corners as exported,",
        "    supports on the build plate only. Beads, sill nose and spacers lie flat on their longest face.",
        "  - Print the test coupon (TC) and one segment of each profile first, and check the fit.",
        "",
        "Files",
    ]
    lines += [f"  {f:<12} {text}" for f, text in FILES]
    lines += [
        "",
        "Guides (in the OpenWindow repo)",
        "  OpenWindow-Guide.pdf: the whole job as a slide deck",
        "  docs/printing.md, docs/build-guide.md, docs/install-guide.md, docs/user-manual.md",
    ]
    if not screen:
        lines.append("  No screen: skip the screen steps in the build and install guides.")
    return "\n".join(lines) + "\n"


def build(files):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for arc, data in files.items():
            zf.writestr(arc, data)
    return buf.getvalue()
```

- [ ] **Step 4: Run the tests to see them pass**

Run: `cd ~/diy-window && python3 -m unittest discover -s web/tests -p 'test_zipper.py' 2>&1 | tail -3`
Expected: `Ran 10 tests`, `OK`.

- [ ] **Step 5: Checkpoint**

Run: `cd ~/diy-window && python3 -m unittest discover -s web/tests -p 'test_*.py' 2>&1 | grep -E '^(Ran|OK|FAILED)'`
Expected: `Ran 30 tests`, `OK`.

---

### Task 9: Server-side logic (`web/api.py`)

These are pure functions, unit-tested without HTTP:

| Function | What it does |
|---|---|
| `validate(raw)` | Returns `(params, errors)`. Missing keys take the defaults (`DEFAULTS`), unknown keys go to `_form`, and each field error is keyed by its field name. The rules are spec §3: name `[a-z0-9-]{1,40}`, openings 300–3000, gap 0–20, awning at least `MIN_AWNING`, glazing, tier 1–3, screen boolean, bed three sizes of 100–500 |
| `preview(raw)` | Returns `{ok, errors, params, layout, checks, parts, bom, drawing, assembly}`. A generator `ValueError` becomes a field error (for example "fixed pane height …" goes to `awning_h`). A bad name alone still draws the window but sets `ok: false` |
| `save_params(params, root)` | Writes `params/<name>.json` in the same format as the reference files. An equivalent existing file is left untouched, and the reference windows are never changed |
| `load(name, root)` | Returns `(params, lay, plist)` for a saved window. Raises `LookupError` if there is none |
| `stl_dir`, `check_part`, `part_status` | Run the STL check of `check_stl.check` against the window's bed |
| `write_bom(name, lay, plist, out, ok_ids, root)` | Writes the same five files as `bom/build_bom.py <name>`, into any folder |
| `build_zip(name, partial, root)` | Returns `(filename, bytes)`. Raises `NotReady` unless every part passes, or `partial` is set |

`root` defaults to the repo, and the tests point it at a temporary folder. `name` is checked against the pattern before it touches any path (`params_path`).

**Files:**
- Create: `web/api.py`
- Test: `web/tests/test_api.py`

- [ ] **Step 1: Write the failing tests**

**Create** `web/tests/test_api.py`:
```python
"""Unit tests for web/api.py."""
import io
import json
import pathlib
import shutil
import sys
import tempfile
import unittest
import zipfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

import api  # noqa: E402


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
        path = api.save_params(self.params(), self.root)
        self.assertEqual(path, self.root / "params" / "my-window.json")
        self.assertEqual(json.loads(path.read_text()), api.DEFAULTS)
        self.assertIn('  "bed": [256, 256, 256]\n}\n', path.read_text())

    def testFormatMatchesTheReferenceFiles(self):
        for name in ("bench-600", "home-1800x1500"):
            self.assertEqual(api.dumps_params(ref(name)), (api.ROOT / "params" / f"{name}.json").read_text())

    def testEquivalentFileIsKeptAsItIs(self):
        text = (api.ROOT / "params" / "bench-600.json").read_text()
        (self.root / "params" / "bench-600.json").write_text(text)
        api.save_params(api.validate(ref("bench-600"))[0], self.root)
        self.assertEqual((self.root / "params" / "bench-600.json").read_text(), text)

    def testReferenceWindowIsNotOverwritten(self):
        (self.root / "params" / "bench-600.json").write_text((api.ROOT / "params" / "bench-600.json").read_text())
        with self.assertRaisesRegex(ValueError, "reference window"):
            api.save_params(api.validate(dict(ref("bench-600"), opening_w=700))[0], self.root)

    def testOwnWindowIsOverwritten(self):
        api.save_params(self.params(), self.root)
        api.save_params(self.params(opening_w=1200), self.root)
        self.assertEqual(json.loads((self.root / "params" / "my-window.json").read_text())["opening_w"], 1200)

    def testBadNameNeverReachesTheFilesystem(self):
        with self.assertRaises(ValueError):
            api.save_params(self.params(name="../evil"), self.root)
        self.assertEqual(list(self.root.rglob("*")), [self.root / "params"])


class StatusAndZipTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self.tmp.name)
        (self.root / "params").mkdir()
        shutil.copy(api.ROOT / "params" / "bench-600.json", self.root / "params")

    def tearDown(self):
        self.tmp.cleanup()

    def copyStls(self, skip=()):
        out = self.root / "cad" / "stl" / "bench-600"
        out.mkdir(parents=True)
        for f in (api.ROOT / "cad" / "stl" / "bench-600").glob("*.stl"):
            if f.stem not in skip:
                shutil.copy(f, out)

    def testLoadUnknownWindowRaises(self):
        with self.assertRaises(LookupError):
            api.load("nope", self.root)

    def testReferenceRendersPass(self):
        params, lay, plist = api.load("bench-600")
        self.assertEqual({pid: e for pid, e in api.part_status("bench-600", lay, plist).items() if e}, {})

    def testMissingStlsAreReported(self):
        params, lay, plist = api.load("bench-600", self.root)
        status = api.part_status("bench-600", lay, plist, self.root)
        self.assertEqual(status["H"], ["H: missing H.stl"])

    def testWriteBomMatchesTheCommandLine(self):
        self.copyStls()
        params, lay, plist = api.load("bench-600", self.root)
        api.write_bom("bench-600", lay, plist, self.root / "bom", root=self.root)
        for f in ("bench-600.md", "bench-600.csv", "bench-600-parts.csv", "bench-600-cutlist.csv", "bench-600-glass.csv"):
            self.assertEqual((self.root / "bom" / f).read_text(), (api.ROOT / "bom" / f).read_text(), f)

    def testZipHasEveryFile(self):
        self.copyStls()
        name, data = api.build_zip("bench-600", root=self.root)
        z = zipfile.ZipFile(io.BytesIO(data))
        names = z.namelist()
        self.assertEqual(name, "bench-600-openwindow.zip")
        self.assertEqual(names[:5], ["README.txt", "parts.csv", "cutlist.csv", "glass.csv", "BOM.md"])
        self.assertEqual(names[-1], "params.json")
        self.assertEqual(len([n for n in names if n.startswith("stl/")]), 37)
        self.assertEqual(z.read("stl/H_x2.stl"), (api.ROOT / "cad" / "stl" / "bench-600" / "H.stl").read_bytes())
        self.assertEqual(z.read("params.json"), (api.ROOT / "params" / "bench-600.json").read_bytes())
        self.assertTrue(z.read("README.txt").decode().startswith("OpenWindow: bench-600\n"))

    def testZipNeedsEveryPart(self):
        self.copyStls(skip={"H"})
        with self.assertRaisesRegex(api.NotReady, "H"):
            api.build_zip("bench-600", root=self.root)

    def testPartialZipLeavesOutMissingParts(self):
        self.copyStls(skip={"H", "JL"})
        z = zipfile.ZipFile(io.BytesIO(api.build_zip("bench-600", partial=True, root=self.root)[1]))
        self.assertNotIn("stl/H_x2.stl", z.namelist())
        readme = z.read("README.txt").decode()
        self.assertTrue(readme.startswith("PARTIAL ZIP"))
        self.assertIn("  H, JL\n", readme)
        self.assertIn("Filament excludes unrendered parts: H, JL.", z.read("BOM.md").decode())


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run them to see them fail**

Run: `cd ~/diy-window && python3 -m unittest discover -s web/tests -p 'test_api.py' 2>&1 | tail -3`
Expected: `FAILED (errors=1)` after `ModuleNotFoundError: No module named 'api'`.

- [ ] **Step 3: Implement**

**Create** `web/api.py`:
```python
"""Pure functions behind the web configurator: validation, preview, params files, part status, BOM and zip."""
import json
import math
import pathlib
import re
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "bom"))
sys.path.insert(0, str(ROOT / "tools"))

import build_bom  # noqa: E402
import check_stl  # noqa: E402
import drawing  # noqa: E402
import generate  # noqa: E402
import window  # noqa: E402
import zipper  # noqa: E402

NAME_RE = re.compile(r"[a-z0-9-]{1,40}")
REFERENCE_NAMES = {"bench-600", "home-1800x1500"}
DEFAULTS = {"name": "my-window", "opening_w": 1800, "opening_h": 1500, "fix_gap": 8, "awning_h": 450,
            "glazing": "igu", "tier": 3, "screen": True, "bed": [256, 256, 256]}
RANGES = {"opening_w": (300, 3000), "opening_h": (300, 3000), "fix_gap": (0, 20)}
BED_RANGE = (100, 500)
PRESETS = [
    {"key": "bambu", "label": "Bambu P1S / P1P / X1 / A1", "bed": [256, 256, 256]},
    {"key": "a1mini", "label": "Bambu A1 mini", "bed": [180, 180, 180]},
    {"key": "mk4", "label": "Prusa MK4", "bed": [250, 210, 220]},
    {"key": "prusamini", "label": "Prusa Mini", "bed": [180, 180, 180]},
    {"key": "ender3", "label": "Creality Ender-3", "bed": [220, 220, 250]},
]
PART_NAMES = {
    "H": "Head segment", "S": "Sill segment", "SW": "Sill end segment, weep", "JL": "Lower jamb segment",
    "JU": "Upper jamb segment", "T": "Transom segment", "TE": "Transom end segment, weep and cam bosses",
    "SH": "Sash top segment", "SB": "Sash bottom segment", "SBE": "Sash bottom end segment, weep and keeper bosses",
    "SV": "Sash side segment", "NH": "Screen top/bottom segment", "NV": "Screen side segment",
    "CH": "Head corner", "CSL": "Sill corner, left", "CSR": "Sill corner, right", "CS": "Sash corner",
    "CN": "Screen corner", "JN": "Jamb node", "TSL": "Transom shoe, left", "TSR": "Transom shoe, right",
    "GW": "Setting block, wedge", "GF": "Glass locator", "WC": "Weep cap", "NS": "Sill nose",
    "CMB": "Cam base", "CMH": "Cam handle", "KP": "Cam keeper", "HG": "Screen hinge, frame leaf",
    "HS": "Screen hinge, screen leaf", "TC": "Test coupon",
    "BFH": "Bead, fixed pane, horizontal", "BFV": "Bead, fixed pane, vertical",
    "BSH": "Bead, sash, horizontal", "BSV": "Bead, sash, vertical",
    "AFH": "Acrylic spacer, fixed pane, horizontal", "AFV": "Acrylic spacer, fixed pane, vertical",
    "ASH": "Acrylic spacer, sash, horizontal", "ASV": "Acrylic spacer, sash, vertical",
    "AC": "Acrylic spacer corner",
}
SUMMARY_KEYS = ("w", "h", "transom_c", "sash", "screen", "glass", "stay", "sash_kg", "keeper_dz", "bed", "max_seg",
                "has_screen", "members", "tubes")


class NotReady(Exception):
    pass


def is_number(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)


def validate(raw):
    if not isinstance(raw, dict):
        return dict(DEFAULTS), {"_form": "expected a JSON object"}
    params = {k: raw.get(k, v) for k, v in DEFAULTS.items()}
    errors = {}
    unknown = sorted(set(raw) - set(DEFAULTS))
    if unknown:
        errors["_form"] = f"unknown fields: {', '.join(unknown)}"
    if not isinstance(params["name"], str) or not NAME_RE.fullmatch(params["name"]):
        errors["name"] = "1-40 characters: lowercase letters, digits and dashes"
    for key, (lo, hi) in RANGES.items():
        if not is_number(params[key]) or not lo <= params[key] <= hi:
            errors[key] = f"{lo}-{hi} mm"
    if not is_number(params["awning_h"]) or params["awning_h"] < window.MIN_AWNING:
        errors["awning_h"] = f"at least {window.MIN_AWNING:g} mm"
    if params["glazing"] not in window.GLAZING_KG_M2:
        errors["glazing"] = "igu, acrylic or twinwall"
    if params["tier"] not in (1, 2, 3) or isinstance(params["tier"], bool):
        errors["tier"] = "1, 2 or 3"
    if not isinstance(params["screen"], bool):
        errors["screen"] = "true or false"
    bed = params["bed"]
    if not (isinstance(bed, list) and len(bed) == 3 and all(is_number(v) and BED_RANGE[0] <= v <= BED_RANGE[1] for v in bed)):
        errors["bed"] = f"three sizes, {BED_RANGE[0]}-{BED_RANGE[1]} mm each"
    return params, errors


def error_field(msg):
    if msg.startswith("fixed pane height"):
        return "awning_h"
    return next((k for k in DEFAULTS if msg.startswith(k)), "_form")


def checks(lay, plist):
    return lay["checks"] + [generate.bed_fit(lay, plist)]


def part_rows(plist):
    return [{"id": pt["id"], "name": PART_NAMES.get(pt["id"], pt["id"]), "qty": pt["qty"], "length": pt["length"],
             "role": pt["role"]} for pt in plist]


def preview(raw):
    params, errors = validate(raw)
    out = {"ok": False, "errors": errors, "params": params}
    if set(errors) - {"name"}:
        return out
    try:
        lay = window.layout(params)
        plist = generate.parts(lay)
    except ValueError as e:
        errors[error_field(str(e))] = str(e)
        return out
    out.update(ok=not errors, layout={k: lay[k] for k in SUMMARY_KEYS}, checks=checks(lay, plist),
               parts=part_rows(plist), bom=build_bom.hardware(lay, plist), drawing=drawing.front(lay),
               assembly=drawing.assembly(lay, plist))
    return out


def params_path(name, root=ROOT):
    if not isinstance(name, str) or not NAME_RE.fullmatch(name):
        raise ValueError(f"bad window name {name!r}")
    return pathlib.Path(root) / "params" / f"{name}.json"


def dumps_params(params):
    return "{\n" + ",\n".join(f"  {json.dumps(k)}: {json.dumps(v)}" for k, v in params.items()) + "\n}\n"


def save_params(params, root=ROOT):
    path = params_path(params["name"], root)
    if path.exists():
        if {**DEFAULTS, **json.loads(path.read_text())} == {**DEFAULTS, **params}:
            return path
        if params["name"] in REFERENCE_NAMES:
            raise ValueError(f"{params['name']} is a reference window; pick another name")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(dumps_params(params))
    return path


def load(name, root=ROOT):
    path = params_path(name, root)
    if not path.exists():
        raise LookupError(f"no params/{name}.json")
    params = json.loads(path.read_text())
    lay = window.layout(params)
    return params, lay, generate.parts(lay)


def stl_dir(name, root=ROOT):
    return pathlib.Path(root) / "cad" / "stl" / params_path(name, root).stem


def check_part(name, lay, pt, root=ROOT):
    row = {"id": pt["id"], "length": "" if pt["length"] is None else str(pt["length"])}
    return check_stl.check(row, stl_dir(name, root), lay["bed"])


def part_status(name, lay, plist, root=ROOT):
    return {pt["id"]: check_part(name, lay, pt, root) for pt in plist}


def write_bom(name, lay, plist, out, ok_ids=None, root=ROOT):
    ok = [pt for pt in plist if ok_ids is None or pt["id"] in ok_ids]
    fil, missing = build_bom.filament(lay, ok, stl_dir(name, root))
    missing += [pt["id"] for pt in plist if pt not in ok]
    pathlib.Path(out).mkdir(parents=True, exist_ok=True)
    build_bom.write(name, lay, plist, build_bom.hardware(lay, plist) + fil, missing, out)


def build_zip(name, partial=False, root=ROOT):
    params, lay, plist = load(name, root)
    status = part_status(name, lay, plist, root)
    missing = [pid for pid, errs in status.items() if errs]
    if missing and not partial:
        raise NotReady(f"not every part passed its STL check: {', '.join(missing)}")
    ok = [pt for pt in plist if pt["id"] not in missing]
    files = {"README.txt": zipper.readme(name, params, checks(lay, plist), missing)}
    with tempfile.TemporaryDirectory() as tmp:
        write_bom(name, lay, plist, tmp, {pt["id"] for pt in ok}, root)
        for arc, src in (("parts.csv", "-parts.csv"), ("cutlist.csv", "-cutlist.csv"), ("glass.csv", "-glass.csv"),
                         ("BOM.md", ".md")):
            files[arc] = (pathlib.Path(tmp) / f"{name}{src}").read_bytes()
    for pt in ok:
        files[f"stl/{pt['id']}_x{pt['qty']}.stl"] = (stl_dir(name, root) / f"{pt['id']}.stl").read_bytes()
    files["params.json"] = params_path(name, root).read_bytes()
    return f"{name}-openwindow.zip", zipper.build(files)
```

- [ ] **Step 4: Run the tests to see them pass**

Run: `cd ~/diy-window && python3 -m unittest discover -s web/tests -p 'test_api.py' 2>&1 | tail -3`
Expected: `Ran 35 tests`, `OK`, in about 3 s, most of it spent reading the reference STLs.

- [ ] **Step 5: Checkpoint**

Run: `cd ~/diy-window && python3 -m unittest discover -s web/tests -p 'test_*.py' 2>&1 | grep -E '^(Ran|OK|FAILED)'`
Expected: `Ran 65 tests`, `OK`.

Then check that the tests left no files behind: `cd ~/diy-window && ls params`
Expected: `bench-600.json  home-1800x1500.json`.

---

### Task 10: HTTP server and render job (`web/server.py`, `web/fake_box.py`)

**Server.** `ThreadingHTTPServer` on 127.0.0.1, with these routes:
- static files from `web/static/` (a flat folder; only `.html`, `.css` and `.js` are served);
- `GET /api/presets`, `/api/job`, `/api/box`, `/api/stl/<name>/<id>` and `/api/zip/<name>[?partial=1]`;
- `POST /api/preview`, `/api/render` and `/api/cancel`.

It returns 403 for a foreign `Host` header and 415 for a POST that isn't JSON.

**Renderer.** The renderer is a command prefix. The server appends `["render", name, *ids]` or `["ping"]` to it:
- normally `[cad/box.sh]`;
- in the tests and with `--fake-render`, `[python3, web/fake_box.py, --root, <folder>, …]`. With `--fake-render`, the data folder is a new temporary folder, removed when the server stops on Ctrl-C (SIGINT).

So the tests exercise the real subprocess, process-group and cancel code.

**Job.** One job runs at a time (409 otherwise). For each batch of up to six IDs, the `Job` thread:
1. deletes the batch's old STLs;
2. runs the renderer in its own session (`start_new_session=True`) and streams its output into a 40-line log;
3. checks each STL with the window's bed.

Exit 255 fails the job with "Windows build box unreachable (<host>)". At the end it writes `bom/<name>.*` in-process (`api.write_bom`). Cancel sends SIGTERM to the process group, then SIGKILL after 15 s if the group is still there. The SIGTERM lets `box.sh`'s EXIT trap release `.generate.lock` and remove the remote run folder. The live check while planning confirmed that no `.generate.lock` is left behind. It did not look on the box to see whether the run folder was gone, or whether OpenSCAD stopped there.

**Box status.** `GET /api/box` runs `<renderer> ping` and caches the answer for 30 s.

**Files:**
- Create: `web/fake_box.py`
- Create: `web/server.py`
- Test: `web/tests/test_server.py`

- [ ] **Step 1: Write the failing tests**

**Create** `web/tests/test_server.py`:
```python
"""Tests for web/server.py: the HTTP API on an ephemeral port, rendering with web/fake_box.py."""
import io
import json
import pathlib
import shutil
import sys
import tempfile
import threading
import time
import unittest
import urllib.error
import urllib.request
import zipfile

WEB = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(WEB))

import api  # noqa: E402
import server  # noqa: E402

BENCH = dict(json.loads((api.ROOT / "params" / "bench-600.json").read_text()), name="t-bench")


class ServerCase(unittest.TestCase):
    fake = []

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self.tmp.name)
        command = [sys.executable, str(WEB / "fake_box.py"), "--root", str(self.root), *self.fake]
        self.srv = server.make_server(0, self.root, command, "192.168.68.61")
        self.app = self.srv.RequestHandlerClass.app
        self.port = self.srv.server_address[1]
        threading.Thread(target=self.srv.serve_forever, daemon=True).start()

    def tearDown(self):
        if self.app.running():
            self.app.job.cancel()
            self.app.job.thread.join(10)
        self.srv.shutdown()
        self.srv.server_close()
        self.tmp.cleanup()

    def request(self, method, path, body=None, headers=None):
        data = None if body is None else json.dumps(body).encode()
        h = {"Content-Type": "application/json"} if body is not None else {}
        h.update(headers or {})
        req = urllib.request.Request(f"http://127.0.0.1:{self.port}{path}", data=data, method=method, headers=h)
        try:
            with urllib.request.urlopen(req, timeout=10) as r:
                return r.status, r.headers, r.read()
        except urllib.error.HTTPError as e:
            with e:
                return e.code, e.headers, e.read()

    def call(self, method, path, body=None):
        status, _, data = self.request(method, path, body)
        return status, json.loads(data)

    def waitJob(self, until=lambda job: job["state"] != "running", timeout=30):
        end = time.time() + timeout
        while time.time() < end:
            job = self.call("GET", "/api/job")[1]
            if until(job):
                return job
            time.sleep(0.05)
        self.fail(f"job did not reach the expected state: {job}")


class SafetyTest(ServerCase):
    def testOnlyStaticFilesAreServed(self):
        for path in ("/api.py", "/server.py", "/%2e%2e/README.md", "/..%2fapi.py", "/nope.js", "/api"):
            self.assertEqual(self.request("GET", path)[0], 404, path)

    def testForeignHostIsRejected(self):
        self.assertEqual(self.request("GET", "/api/presets", headers={"Host": "evil.example:80"})[0], 403)

    def testPostMustBeJson(self):
        status = self.request("POST", "/api/preview", body=BENCH, headers={"Content-Type": "text/plain"})[0]
        self.assertEqual(status, 415)

    def testOversizedBodyIsRejected(self):
        self.assertEqual(self.request("POST", "/api/preview", body={"name": "x" * 70000})[0], 400)

    def testTraversalInStlAndZipPaths(self):
        for path in ("/api/stl/..%2fparams/H", "/api/stl/t-bench/..%2f..%2fREADME", "/api/zip/..%2fbench-600",
                     "/api/stl/Bad/H", "/api/zip/nope"):
            self.assertEqual(self.request("GET", path)[0], 404, path)


class PreviewApiTest(ServerCase):
    def testPresets(self):
        status, body = self.call("GET", "/api/presets")
        self.assertEqual(status, 200)
        self.assertEqual([p["key"] for p in body["presets"]], ["bambu", "a1mini", "mk4", "prusamini", "ender3"])
        self.assertEqual(body["defaults"]["bed"], [256, 256, 256])

    def testPreview(self):
        status, body = self.call("POST", "/api/preview", BENCH)
        self.assertEqual((status, body["ok"], len(body["parts"])), (200, True, 37))

    def testInvalidPreview(self):
        body = self.call("POST", "/api/preview", dict(BENCH, opening_w=10))[1]
        self.assertEqual((body["ok"], body["errors"]), (False, {"opening_w": "300-3000 mm"}))

    def testIdleJob(self):
        self.assertEqual(self.call("GET", "/api/job"), (200, {"state": "idle"}))

    def testBoxStatus(self):
        status, body = self.call("GET", "/api/box")
        self.assertEqual((status, body["ok"], body["host"]), (200, True, "192.168.68.61"))

    def testBatchesOfSix(self):
        self.assertEqual([len(b) for b in server.batches(list(range(14)))], [6, 6, 2])


class RenderTest(ServerCase):
    def testRenderAllThenZip(self):
        status, body = self.call("POST", "/api/render", BENCH)
        self.assertEqual((status, body["job"]["state"], body["job"]["total"]), (200, "running", 37))
        job = self.waitJob()
        self.assertEqual((job["state"], job["done"], job["error"]), ("done", 37, ""))
        self.assertEqual(set(job["parts"].values()), {"ok"})
        self.assertTrue((self.root / "params" / "t-bench.json").exists())
        self.assertTrue((self.root / "bom" / "t-bench.md").exists())
        status, headers, data = self.request("GET", "/api/zip/t-bench")
        self.assertEqual((status, headers["Content-Type"]), (200, "application/zip"))
        self.assertEqual(headers["Content-Disposition"], 'attachment; filename="t-bench-openwindow.zip"')
        names = zipfile.ZipFile(io.BytesIO(data)).namelist()
        self.assertEqual(len([n for n in names if n.startswith("stl/")]), 37)

    def testSelectionRendersInBatchesOfSix(self):
        ids = ["H", "SW", "JL", "JU", "TE", "SH", "SBE", "SV"]
        self.call("POST", "/api/render", dict(BENCH, ids=list(reversed(ids))))
        job = self.waitJob()
        self.assertEqual((job["state"], job["total"], list(job["parts"])), ("done", 8, ids))
        self.assertEqual([x for x in job["log_tail"] if x.startswith("fake render")],
                         ["fake render: 6 parts", "fake render: 2 parts"])

    def testStlEndpoint(self):
        self.call("POST", "/api/render", dict(BENCH, ids=["H"]))
        self.waitJob()
        status, headers, data = self.request("GET", "/api/stl/t-bench/H")
        self.assertEqual((status, headers["Content-Type"], len(data)), (200, "model/stl", 84 + 12 * 50))
        self.assertEqual(self.request("GET", "/api/stl/t-bench/JL")[0], 404)
        self.assertEqual(self.request("GET", "/api/stl/t-bench/ZZ")[0], 404)

    def testUnknownIdIsRejected(self):
        status, body = self.call("POST", "/api/render", dict(BENCH, ids=["ZZ"]))
        self.assertEqual((status, list(body["errors"])), (400, ["ids"]))

    def testInvalidParamsAreRejected(self):
        status, body = self.call("POST", "/api/render", dict(BENCH, opening_w=10))
        self.assertEqual((status, body["errors"]), (400, {"opening_w": "300-3000 mm"}))
        self.assertEqual(self.call("GET", "/api/job")[1], {"state": "idle"})

    def testBadNameIsRejected(self):
        status, body = self.call("POST", "/api/render", dict(BENCH, name="../x"))
        self.assertEqual((status, list(body["errors"])), (400, ["name"]))
        self.assertFalse((self.root / "params").exists())

    def testReferenceWindowIsProtected(self):
        (self.root / "params").mkdir()
        shutil.copy(api.ROOT / "params" / "bench-600.json", self.root / "params")
        status, body = self.call("POST", "/api/render", dict(BENCH, name="bench-600", opening_w=700))
        self.assertEqual(status, 400)
        self.assertIn("reference window", body["errors"]["name"])

    def testCancelWithoutAJob(self):
        self.assertEqual(self.call("POST", "/api/cancel", {})[0], 409)


class SlowRenderTest(ServerCase):
    fake = ["--delay", "0.3"]

    def testBusyServerRefusesASecondJob(self):
        self.call("POST", "/api/render", BENCH)
        self.assertEqual(self.call("POST", "/api/render", BENCH)[0], 409)

    def testZipWhileRenderingIsRefused(self):
        self.call("POST", "/api/render", BENCH)
        self.assertEqual(self.request("GET", "/api/zip/t-bench")[0], 409)

    def testProgressNamesTheCurrentBatch(self):
        self.call("POST", "/api/render", BENCH)
        job = self.waitJob(lambda j: j["done"] >= 6)
        self.assertLessEqual(len(job["current"]), 6)
        self.assertEqual(job["total"], 37)

    def testCancelKillsTheRunningBatch(self):
        self.call("POST", "/api/render", BENCH)
        self.waitJob(lambda j: j["current"])
        started = time.time()
        status, body = self.call("POST", "/api/cancel", {})
        self.assertEqual(status, 200)
        job = self.waitJob()
        self.assertLess(time.time() - started, 3)
        self.assertEqual(job["state"], "cancelled")
        self.assertIn("cancelled", job["parts"].values())
        self.assertIsNotNone(self.app.job.proc.poll())


class FailingRenderTest(ServerCase):
    fake = ["--fail", "H,JL"]

    def testFailedPartsAndPartialZip(self):
        self.call("POST", "/api/render", BENCH)
        job = self.waitJob()
        self.assertEqual((job["state"], job["error"]), ("failed", "2 part(s) failed: H, JL"))
        self.assertEqual((job["parts"]["H"], job["parts"]["SW"]), ("failed", "ok"))
        self.assertEqual(job["errors"]["H"], ["H: missing H.stl"])
        self.assertTrue((self.root / "bom" / "t-bench.md").exists())
        self.assertEqual(self.request("GET", "/api/zip/t-bench")[0], 409)
        status, _, data = self.request("GET", "/api/zip/t-bench?partial=1")
        z = zipfile.ZipFile(io.BytesIO(data))
        self.assertEqual(status, 200)
        self.assertNotIn("stl/H_x2.stl", z.namelist())
        self.assertTrue(z.read("README.txt").decode().startswith("PARTIAL ZIP"))


class UnreachableBoxTest(ServerCase):
    fake = ["--exit", "255"]

    def testJobFailsWithTheBoxMessage(self):
        self.call("POST", "/api/render", BENCH)
        job = self.waitJob()
        self.assertEqual((job["state"], job["error"]), ("failed", "Windows build box unreachable (192.168.68.61)"))
        self.assertIn("ssh: connect to host 192.168.68.61 port 22: Operation timed out", job["log_tail"])
        self.assertEqual(job["parts"]["H"], "failed")
        self.assertEqual(job["parts"]["AC"], "skipped")
        self.assertFalse((self.root / "bom").exists())

    def testBoxStatusIsDown(self):
        self.assertEqual(self.call("GET", "/api/box")[1]["ok"], False)

    def testPreviewStillWorks(self):
        self.assertTrue(self.call("POST", "/api/preview", BENCH)[1]["ok"])


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run them to see them fail**

Run: `cd ~/diy-window && python3 -m unittest discover -s web/tests -p 'test_server.py' 2>&1 | tail -3`
Expected: `FAILED (errors=1)` after `ModuleNotFoundError: No module named 'server'`.

- [ ] **Step 3: Write the stand-in renderer**

**Create** `web/fake_box.py`:
```python
#!/usr/bin/env python3
"""Stand-in for cad/box.sh (render | ping) for tests and server.py --fake-render: writes box STLs that pass check_stl."""
import argparse
import json
import pathlib
import struct
import sys
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import api  # noqa: E402

FACES = [(0, 2, 1), (0, 3, 2), (4, 5, 6), (4, 6, 7), (0, 1, 5), (0, 5, 4),
         (1, 2, 6), (1, 6, 5), (2, 3, 7), (2, 7, 6), (3, 0, 4), (3, 4, 7)]


def box_stl(sx, sy, sz):
    v = [(x * sx, y * sy, z * sz) for x, y, z in
         [(0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0), (0, 0, 1), (1, 0, 1), (1, 1, 1), (0, 1, 1)]]
    out = b"\0" * 80 + struct.pack("<I", len(FACES))
    for f in FACES:
        out += struct.pack("<3f", 0, 0, 0) + b"".join(struct.pack("<3f", *v[i]) for i in f) + b"\0\0"
    return out


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=pathlib.Path, required=True)
    ap.add_argument("--delay", type=float, default=0.0)
    ap.add_argument("--fail", default="")
    ap.add_argument("--exit", type=int, default=0)
    ap.add_argument("cmd", choices=["render", "ping"])
    ap.add_argument("args", nargs="*")
    a = ap.parse_args(argv[1:])
    if a.exit:
        print("ssh: connect to host 192.168.68.61 port 22: Operation timed out", flush=True)
        return a.exit
    if a.cmd == "ping":
        print("ok")
        return 0
    name, ids = a.args[0], a.args[1:]
    params = json.loads(api.params_path(name, a.root).read_text())
    lengths = {pt["id"]: pt["length"] for pt in api.generate.parts(api.window.layout(params))}
    out = api.stl_dir(name, a.root)
    out.mkdir(parents=True, exist_ok=True)
    failed = set(a.fail.split(",")) & set(ids)
    print(f"fake render: {len(ids)} parts", flush=True)
    for pid in ids:
        print(f"== {pid}", flush=True)
        time.sleep(a.delay)
        if pid in failed:
            print(f"ERROR: fake render failure for {pid}", flush=True)
            continue
        (out / f"{pid}.stl").write_bytes(box_stl(10, 20, lengths[pid] or 20))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
```

It answers like `box.sh`:
- `render` prints `== <ID>` lines and writes an STL for each ID, as a 10 × 20 × length box (20 mm for fixed parts), so `check_stl` passes;
- `--fail H,JL` skips those IDs, which then show as missing;
- `--exit 255` fails like an unreachable box;
- `--delay` slows each part, so that a cancel can land mid-batch.

- [ ] **Step 4: Write the server**

**Create** `web/server.py`:
```python
#!/usr/bin/env python3
"""OpenWindow web configurator: serves web/static/ and the JSON API on 127.0.0.1 and runs one render job at a time."""
import argparse
import collections
import json
import os
import pathlib
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

WEB = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(WEB))

import api  # noqa: E402

STATIC = WEB / "static"
TYPES = {".html": "text/html; charset=utf-8", ".css": "text/css; charset=utf-8",
         ".js": "text/javascript; charset=utf-8"}
BATCH = 6
LOG_LINES = 40
BOX_TTL = 30.0
MAX_BODY = 65536
UNREACHABLE = 255
KILL_AFTER = 15.0


def box_host():
    m = re.search(r"HOST=\$\{BOX_HOST:-([^}]+)\}", (api.ROOT / "cad" / "box.sh").read_text())
    return os.environ.get("BOX_HOST", m.group(1)).split("@")[-1]


def batches(ids, size=BATCH):
    return [ids[i:i + size] for i in range(0, len(ids), size)]


class Job:
    def __init__(self, command, root, host, name, params, ids):
        self.command, self.root, self.host, self.name, self.ids = command, root, host, name, ids
        self.lay = api.window.layout(params)
        self.plist = api.generate.parts(self.lay)
        self.by_id = {pt["id"]: pt for pt in self.plist}
        self.state, self.error, self.current, self.done = "running", "", [], 0
        self.parts = {pid: "queued" for pid in ids}
        self.errors = {}
        self.log = collections.deque(maxlen=LOG_LINES)
        self.started, self.finished = time.time(), None
        self.proc, self.cancelled = None, False
        self.lock = threading.Lock()
        self.thread = threading.Thread(target=self.run, daemon=True)

    def snapshot(self):
        with self.lock:
            return {"state": self.state, "name": self.name, "total": len(self.ids), "done": self.done,
                    "current": list(self.current), "parts": dict(self.parts), "errors": dict(self.errors),
                    "error": self.error, "log_tail": list(self.log), "started": self.started,
                    "elapsed": round((self.finished or time.time()) - self.started, 1)}

    def run(self):
        try:
            for batch in batches(self.ids):
                if not self.render(batch):
                    break
            if self.state == "running" and not self.cancelled:
                api.write_bom(self.name, self.lay, self.plist, self.root / "bom", root=self.root)
                with self.lock:
                    self.log.append(f"bom/{self.name}.md and CSVs written")
                    bad = [pid for pid, s in self.parts.items() if s != "ok"]
                    self.state = "failed" if bad else "done"
                    self.error = f"{len(bad)} part(s) failed: {', '.join(bad)}" if bad else ""
        except Exception as e:
            with self.lock:
                self.state, self.error = "failed", f"{type(e).__name__}: {e}"
        finally:
            with self.lock:
                if self.cancelled:
                    self.state = "cancelled"
                leftover = "cancelled" if self.cancelled else "skipped"
                self.parts = {pid: leftover if s in ("queued", "rendering") else s for pid, s in self.parts.items()}
                self.current, self.finished = [], time.time()

    def render(self, batch):
        out = api.stl_dir(self.name, self.root)
        with self.lock:
            if self.cancelled:
                return False
            for pid in batch:
                (out / f"{pid}.stl").unlink(missing_ok=True)
                self.parts[pid] = "rendering"
            self.current = batch
            self.proc = subprocess.Popen(self.command + ["render", self.name, *batch], stdout=subprocess.PIPE,
                                         stderr=subprocess.STDOUT, text=True, start_new_session=True)
        with self.proc.stdout:
            for line in self.proc.stdout:
                with self.lock:
                    self.log.append(line.rstrip())
        rc = self.proc.wait()
        if self.cancelled:
            return False
        if rc == UNREACHABLE:
            with self.lock:
                self.state, self.error = "failed", f"Windows build box unreachable ({self.host})"
                for pid in batch:
                    self.parts[pid], self.errors[pid] = "failed", [self.error]
            return False
        for pid in batch:
            errs = api.check_part(self.name, self.lay, self.by_id[pid], self.root)
            with self.lock:
                self.parts[pid] = "failed" if errs else "ok"
                if errs:
                    self.errors[pid] = errs
                self.done += 1
        return True

    def cancel(self):
        with self.lock:
            self.cancelled = True
            proc = self.proc
        if proc is not None and proc.poll() is None:
            self.kill(proc, signal.SIGTERM)
            threading.Timer(KILL_AFTER, self.kill, (proc, signal.SIGKILL)).start()

    @staticmethod
    def kill(proc, sig):
        if proc.poll() is None:
            try:
                os.killpg(proc.pid, sig)
            except ProcessLookupError:
                pass


class App:
    def __init__(self, root, command, host):
        self.root, self.command, self.host = pathlib.Path(root), command, host
        self.job, self.box = None, {"ok": None, "host": host, "checked": 0.0}
        self.lock = threading.Lock()

    def running(self):
        return self.job is not None and self.job.thread.is_alive()

    def start(self, params, ids):
        with self.lock:
            if self.running():
                return None
            job = Job(self.command, self.root, self.host, params["name"], params, ids)
            self.job = job
            job.thread.start()
            return job

    def box_status(self):
        with self.lock:
            if time.time() - self.box["checked"] < BOX_TTL:
                return dict(self.box)
        try:
            ok = subprocess.run(self.command + ["ping"], capture_output=True, timeout=25).returncode == 0
        except subprocess.TimeoutExpired:
            ok = False
        with self.lock:
            self.box = {"ok": ok, "host": self.host, "checked": time.time()}
            return dict(self.box)


class Handler(BaseHTTPRequestHandler):
    app = None

    def log_request(self, code="-", size="-"):
        if isinstance(code, int) and code >= 500:
            super().log_request(code, size)

    def send(self, code, body, ctype, extra=None):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        for k, v in (extra or {}).items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(body)

    def reply(self, code, obj):
        self.send(code, json.dumps(obj).encode(), "application/json")

    def host_ok(self):
        port = self.server.server_address[1]
        return self.headers.get("Host") in (f"127.0.0.1:{port}", f"localhost:{port}")

    def body(self):
        n = int(self.headers.get("Content-Length") or 0)
        if n > MAX_BODY:
            raise ValueError("request body too large")
        return json.loads(self.rfile.read(n) or b"{}")

    def do_GET(self):
        if not self.host_ok():
            return self.reply(403, {"error": "forbidden host"})
        url = urlparse(self.path)
        seg = url.path.strip("/").split("/")
        if url.path == "/":
            return self.send_static("index.html")
        if len(seg) == 1 and seg[0] != "api":
            return self.send_static(seg[0])
        if seg == ["api", "presets"]:
            return self.reply(200, {"presets": api.PRESETS, "defaults": api.DEFAULTS})
        if seg == ["api", "job"]:
            job = self.app.job
            return self.reply(200, job.snapshot() if job else {"state": "idle"})
        if seg == ["api", "box"]:
            return self.reply(200, self.app.box_status())
        if len(seg) == 4 and seg[:2] == ["api", "stl"]:
            return self.send_stl(seg[2], seg[3])
        if len(seg) == 3 and seg[:2] == ["api", "zip"]:
            return self.send_zip(seg[2], parse_qs(url.query).get("partial") == ["1"])
        return self.reply(404, {"error": "not found"})

    def do_POST(self):
        if not self.host_ok():
            return self.reply(403, {"error": "forbidden host"})
        if not (self.headers.get("Content-Type") or "").startswith("application/json"):
            return self.reply(415, {"error": "send application/json"})
        try:
            body = self.body()
        except ValueError as e:
            return self.reply(400, {"error": str(e)})
        path = urlparse(self.path).path
        if path == "/api/preview":
            return self.reply(200, api.preview(body))
        if path == "/api/render":
            return self.start_render(body)
        if path == "/api/cancel":
            job = self.app.job
            if not self.app.running():
                return self.reply(409, {"error": "no job is running"})
            job.cancel()
            return self.reply(200, {"job": job.snapshot()})
        return self.reply(404, {"error": "not found"})

    def send_static(self, name):
        path = STATIC / name
        if path.suffix not in TYPES or path.parent != STATIC or not path.is_file():
            return self.reply(404, {"error": "not found"})
        self.send(200, path.read_bytes(), TYPES[path.suffix])

    def start_render(self, body):
        ids = body.pop("ids", None) if isinstance(body, dict) else None
        params, errors = api.validate(body)
        if not errors:
            try:
                plist = api.generate.parts(api.window.layout(params))
            except ValueError as e:
                errors[api.error_field(str(e))] = str(e)
        if errors:
            return self.reply(400, {"errors": errors})
        known = [pt["id"] for pt in plist]
        if ids is None:
            ids = known
        if not isinstance(ids, list) or not ids or not all(isinstance(i, str) and i in known for i in ids):
            return self.reply(400, {"errors": {"ids": "ids must be a non-empty list of this window's part IDs"}})
        if self.app.running():
            return self.reply(409, {"error": "a render job is already running"})
        try:
            api.save_params(params, self.app.root)
        except ValueError as e:
            return self.reply(400, {"errors": {"name": str(e)}})
        job = self.app.start(params, [i for i in known if i in ids])
        if job is None:
            return self.reply(409, {"error": "a render job is already running"})
        return self.reply(200, {"job": job.snapshot()})

    def send_stl(self, name, pid):
        try:
            params, lay, plist = api.load(name, self.app.root)
        except (ValueError, LookupError):
            return self.reply(404, {"error": "unknown window"})
        if pid not in {pt["id"] for pt in plist}:
            return self.reply(404, {"error": "unknown part"})
        path = api.stl_dir(name, self.app.root) / f"{pid}.stl"
        if not path.is_file():
            return self.reply(404, {"error": "not rendered"})
        self.send(200, path.read_bytes(), "model/stl")

    def send_zip(self, name, partial):
        job = self.app.job
        if job is not None and job.name == name and self.app.running():
            return self.reply(409, {"error": "a render job for this window is still running"})
        try:
            filename, data = api.build_zip(name, partial, self.app.root)
        except (ValueError, LookupError) as e:
            return self.reply(404, {"error": str(e)})
        except api.NotReady as e:
            return self.reply(409, {"error": str(e)})
        self.send(200, data, "application/zip", {"Content-Disposition": f'attachment; filename="{filename}"'})


def make_server(port, root, command, host=None):
    handler = type("BoundHandler", (Handler,), {"app": App(root, command, host or box_host())})
    srv = ThreadingHTTPServer(("127.0.0.1", port), handler)
    srv.daemon_threads = True
    return srv


def main(argv):
    ap = argparse.ArgumentParser(description="OpenWindow web configurator (local only)")
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--fake-render", action="store_true",
                    help="render with web/fake_box.py into a temporary folder instead of the Windows box")
    a = ap.parse_args(argv[1:])
    root, command = api.ROOT, [str(api.ROOT / "cad" / "box.sh")]
    if a.fake_render:
        root = pathlib.Path(tempfile.mkdtemp(prefix="openwindow-fake-"))
        command = [sys.executable, str(WEB / "fake_box.py"), "--root", str(root), "--delay", "0.4"]
    srv = make_server(a.port, root, command)
    print(f"OpenWindow configurator: http://127.0.0.1:{srv.server_address[1]}/ (data in {root}; Ctrl-C to stop)",
          flush=True)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        if a.fake_render:
            shutil.rmtree(root, ignore_errors=True)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
```

- [ ] **Step 5: Run the tests to see them pass**

Run: `cd ~/diy-window && python3 -m unittest discover -s web/tests -p 'test_server.py' 2>&1 | tail -3`
Expected: `Ran 27 tests`, `OK`, in about 25 s. Each test starts its own server on an ephemeral port, with a temporary data folder.

- [ ] **Step 6: Try the API by hand**

Run:
```bash
cd ~/diy-window && (python3 web/server.py --port 8790 > .web-after/server.log 2>&1 &) && sleep 1
python3 - <<'EOF'
import json, urllib.request
def post(path, body):
    req = urllib.request.Request("http://127.0.0.1:8790" + path, data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"}, method="POST")
    return json.loads(urllib.request.urlopen(req).read())
p = json.load(open("params/home-1800x1500.json"))
r = post("/api/preview", p)
print(r["ok"], [c["name"] for c in r["checks"] if not c["ok"]], len(r["parts"]), r["layout"]["max_seg"])
print(post("/api/preview", dict(p, opening_w=100))["errors"])
print(json.loads(urllib.request.urlopen("http://127.0.0.1:8790/api/box").read()))
EOF
pkill -f "web/server.py --port 8790"
```
Expected (the box line only says `True` when the box is up):
```
True [] 35 240.0
{'opening_w': '300-3000 mm'}
{'ok': True, 'host': '192.168.68.61', 'checked': <a timestamp>}
```

- [ ] **Step 7: Checkpoint**

Run: `cd ~/diy-window && python3 -m unittest discover -s web/tests -p 'test_*.py' 2>&1 | grep -E '^(Ran|OK|FAILED)'`
Expected: `Ran 92 tests`, `OK`.

Then run: `cd ~/diy-window && ls params cad/stl`
Expected: only the reference files and folders (`bench-600.json  home-1800x1500.json`, then `bench-600  home-1800x1500`). The tests write only to temporary folders.

---

### Task 11: WebGL STL viewer (`web/static/viewer.js`)

This is WebGL 1, with no library.
- `parseStl(buffer)` reads binary STL (when `84 + 50 n` equals the file size) or ASCII STL (the `vertex` lines). The reference renders are ASCII.
- Flat normals are computed per triangle. Lighting is two-sided (`abs(dot(n, light))`), because mirrored instances flip the triangle winding. There is one directional light.
- Orbit with mouse drag, and zoom with the wheel. Z is up.
- `showPart(url)` frames one STL. `showAssembly(urlFor, instances)` loads each distinct ID once, draws it once per instance with that instance's matrix, and returns the IDs it couldn't load.

**Files:**
- Create: `web/static/viewer.js`
- Test: `web/tests/test_server.py` (append `ViewerScriptTest`)

- [ ] **Step 1: Write the failing test**

**Append** to `web/tests/test_server.py`:
```python
class ViewerScriptTest(ServerCase):
    def testViewerScriptIsServed(self):
        status, headers, body = self.request("GET", "/viewer.js")
        self.assertEqual((status, headers["Content-Type"]), (200, "text/javascript; charset=utf-8"))
        self.assertIn(b"export class Viewer", body)
        self.assertIn(b"export function parseStl", body)
```

Run: `cd ~/diy-window && python3 -m unittest discover -s web/tests -p 'test_server.py' -k Viewer 2>&1 | tail -3`
Expected: `FAILED (failures=1)`, `404 != 200`.

- [ ] **Step 2: Write the viewer**

**Create** `web/static/viewer.js`:
```js
// Minimal WebGL STL viewer: binary/ASCII STL, orbit and zoom, one directional light, instanced assembly.
const VS = `
attribute vec3 position;
attribute vec3 normal;
uniform mat4 projView;
uniform mat4 model;
uniform mat3 normalMat;
varying vec3 vNormal;
void main() {
  vNormal = normalMat * normal;
  gl_Position = projView * model * vec4(position, 1.0);
}`;
const FS = `
precision mediump float;
uniform vec3 color;
uniform vec3 light;
varying vec3 vNormal;
void main() {
  float d = abs(dot(normalize(vNormal), light));
  gl_FragColor = vec4(color * (0.35 + 0.65 * d), 1.0);
}`;
const IDENTITY = [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1];
const PART_COLOUR = [0.78, 0.8, 0.83];
const GROUPS = [
  [["T", "TE", "TSL", "TSR"], [0.62, 0.66, 0.72]],
  [["SH", "SB", "SBE", "SV", "CS"], [0.72, 0.79, 0.86]],
];
const FOV = 0.7;

export function parseStl(buffer) {
  const view = new DataView(buffer);
  if (buffer.byteLength >= 84) {
    const n = view.getUint32(80, true);
    if (84 + 50 * n === buffer.byteLength) {
      const pos = new Float32Array(n * 9);
      for (let i = 0; i < n; i++) {
        for (let k = 0; k < 9; k++) pos[i * 9 + k] = view.getFloat32(84 + 50 * i + 12 + 4 * k, true);
      }
      return pos;
    }
  }
  const text = new TextDecoder().decode(buffer);
  const nums = [];
  const re = /vertex\s+(\S+)\s+(\S+)\s+(\S+)/g;
  let m;
  while ((m = re.exec(text))) nums.push(Number(m[1]), Number(m[2]), Number(m[3]));
  if (!nums.length || nums.length % 9) throw new Error("not an STL");
  return new Float32Array(nums);
}

function faceNormals(pos) {
  const out = new Float32Array(pos.length);
  for (let i = 0; i < pos.length; i += 9) {
    const ux = pos[i + 3] - pos[i], uy = pos[i + 4] - pos[i + 1], uz = pos[i + 5] - pos[i + 2];
    const vx = pos[i + 6] - pos[i], vy = pos[i + 7] - pos[i + 1], vz = pos[i + 8] - pos[i + 2];
    let nx = uy * vz - uz * vy, ny = uz * vx - ux * vz, nz = ux * vy - uy * vx;
    const len = Math.hypot(nx, ny, nz) || 1;
    nx /= len; ny /= len; nz /= len;
    for (let k = 0; k < 9; k += 3) { out[i + k] = nx; out[i + k + 1] = ny; out[i + k + 2] = nz; }
  }
  return out;
}

function bounds(pos) {
  const min = [Infinity, Infinity, Infinity], max = [-Infinity, -Infinity, -Infinity];
  for (let i = 0; i < pos.length; i += 3) {
    for (let a = 0; a < 3; a++) {
      min[a] = Math.min(min[a], pos[i + a]);
      max[a] = Math.max(max[a], pos[i + a]);
    }
  }
  return { min, max };
}

function multiply(a, b) {
  const out = new Array(16).fill(0);
  for (let c = 0; c < 4; c++) for (let r = 0; r < 4; r++) for (let k = 0; k < 4; k++) out[c * 4 + r] += a[k * 4 + r] * b[c * 4 + k];
  return out;
}

function perspective(fovy, aspect, near, far) {
  const f = 1 / Math.tan(fovy / 2), nf = 1 / (near - far);
  return [f / aspect, 0, 0, 0, 0, f, 0, 0, 0, 0, (far + near) * nf, -1, 0, 0, 2 * far * near * nf, 0];
}

function normalize(v) {
  const len = Math.hypot(...v) || 1;
  return v.map((x) => x / len);
}

function cross(a, b) {
  return [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]];
}

function lookAt(eye, center, up) {
  const z = normalize(eye.map((v, i) => v - center[i]));
  const x = normalize(cross(up, z));
  const y = cross(z, x);
  const dot = (a, b) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
  return [x[0], y[0], z[0], 0, x[1], y[1], z[1], 0, x[2], y[2], z[2], 0, -dot(x, eye), -dot(y, eye), -dot(z, eye), 1];
}

function fromRows(m) {
  return [0, 1, 2, 3].flatMap((c) => [m[c], m[4 + c], m[8 + c], m[12 + c]]);
}

function apply(m, p) {
  return [0, 1, 2].map((r) => m[r] * p[0] + m[4 + r] * p[1] + m[8 + r] * p[2] + m[12 + r]);
}

function colourFor(id) {
  const group = GROUPS.find(([ids]) => ids.includes(id));
  return group ? group[1] : [0.86, 0.85, 0.82];
}

export class Viewer {
  constructor(canvas) {
    this.canvas = canvas;
    this.gl = canvas.getContext("webgl", { antialias: true, preserveDrawingBuffer: true });
    this.meshes = new Map();
    this.items = [];
    this.yaw = -0.6;
    this.pitch = 0.45;
    this.dist = 1;
    this.center = [0, 0, 0];
    if (!this.gl) return;
    const gl = this.gl;
    const shader = (type, src) => {
      const s = gl.createShader(type);
      gl.shaderSource(s, src);
      gl.compileShader(s);
      if (!gl.getShaderParameter(s, gl.COMPILE_STATUS)) throw new Error(gl.getShaderInfoLog(s));
      return s;
    };
    this.prog = gl.createProgram();
    gl.attachShader(this.prog, shader(gl.VERTEX_SHADER, VS));
    gl.attachShader(this.prog, shader(gl.FRAGMENT_SHADER, FS));
    gl.linkProgram(this.prog);
    this.loc = {};
    for (const n of ["position", "normal"]) this.loc[n] = gl.getAttribLocation(this.prog, n);
    for (const n of ["projView", "model", "normalMat", "color", "light"]) this.loc[n] = gl.getUniformLocation(this.prog, n);
    let drag = null;
    canvas.addEventListener("mousedown", (e) => { drag = [e.clientX, e.clientY]; });
    window.addEventListener("mouseup", () => { drag = null; });
    window.addEventListener("mousemove", (e) => {
      if (!drag) return;
      this.yaw += (e.clientX - drag[0]) * 0.01;
      this.pitch = Math.max(-1.5, Math.min(1.5, this.pitch + (e.clientY - drag[1]) * 0.01));
      drag = [e.clientX, e.clientY];
      this.draw();
    });
    canvas.addEventListener("wheel", (e) => {
      e.preventDefault();
      this.dist *= Math.exp(e.deltaY * 0.001);
      this.draw();
    }, { passive: false });
    new ResizeObserver(() => this.draw()).observe(canvas);
  }

  async load(url) {
    if (this.meshes.has(url)) return this.meshes.get(url);
    const r = await fetch(url);
    if (!r.ok) throw new Error(`${url}: ${r.status}`);
    const pos = parseStl(await r.arrayBuffer());
    const gl = this.gl;
    const buf = (data) => {
      const b = gl.createBuffer();
      gl.bindBuffer(gl.ARRAY_BUFFER, b);
      gl.bufferData(gl.ARRAY_BUFFER, data, gl.STATIC_DRAW);
      return b;
    };
    const mesh = { pos: buf(pos), nrm: buf(faceNormals(pos)), count: pos.length / 3, box: bounds(pos) };
    this.meshes.set(url, mesh);
    return mesh;
  }

  async showPart(url) {
    const mesh = await this.load(url);
    this.items = [{ mesh, model: IDENTITY, color: PART_COLOUR }];
    this.yaw = -0.6;
    this.pitch = 0.45;
    this.frame();
  }

  async showAssembly(urlFor, instances) {
    const ids = [...new Set(instances.map((x) => x.id))];
    const loaded = await Promise.allSettled(ids.map((id) => this.load(urlFor(id))));
    const meshes = new Map(ids.map((id, i) => [id, loaded[i].status === "fulfilled" ? loaded[i].value : null]));
    this.items = instances.filter((x) => meshes.get(x.id))
      .map((x) => ({ mesh: meshes.get(x.id), model: fromRows(x.m), color: colourFor(x.id) }));
    this.yaw = 0.35;
    this.pitch = 0.3;
    this.frame();
    return ids.filter((id) => !meshes.get(id));
  }

  clear() {
    this.items = [];
    this.draw();
  }

  frame() {
    const min = [Infinity, Infinity, Infinity], max = [-Infinity, -Infinity, -Infinity];
    for (const { mesh, model } of this.items) {
      const { min: a, max: b } = mesh.box;
      for (let i = 0; i < 8; i++) {
        const p = apply(model, [i & 1 ? b[0] : a[0], i & 2 ? b[1] : a[1], i & 4 ? b[2] : a[2]]);
        for (let k = 0; k < 3; k++) { min[k] = Math.min(min[k], p[k]); max[k] = Math.max(max[k], p[k]); }
      }
    }
    if (!this.items.length) return this.draw();
    this.center = min.map((v, k) => (v + max[k]) / 2);
    const radius = Math.hypot(...max.map((v, k) => v - min[k])) / 2;
    this.dist = (radius / Math.sin(FOV / 2)) * 1.05;
    this.draw();
  }

  draw() {
    const gl = this.gl;
    if (!gl) return;
    const dpr = window.devicePixelRatio || 1;
    const w = Math.round(this.canvas.clientWidth * dpr), h = Math.round(this.canvas.clientHeight * dpr);
    if (!w || !h) return;
    if (this.canvas.width !== w || this.canvas.height !== h) { this.canvas.width = w; this.canvas.height = h; }
    gl.viewport(0, 0, w, h);
    gl.clearColor(0.914, 0.929, 0.941, 1);
    gl.enable(gl.DEPTH_TEST);
    gl.clear(gl.COLOR_BUFFER_BIT | gl.DEPTH_BUFFER_BIT);
    if (!this.items.length) return;
    const cp = Math.cos(this.pitch);
    const dir = [cp * Math.sin(this.yaw), -cp * Math.cos(this.yaw), Math.sin(this.pitch)];
    const eye = this.center.map((v, k) => v + this.dist * dir[k]);
    const projView = multiply(perspective(FOV, w / h, this.dist / 100, this.dist * 10), lookAt(eye, this.center, [0, 0, 1]));
    gl.useProgram(this.prog);
    gl.uniformMatrix4fv(this.loc.projView, false, projView);
    gl.uniform3fv(this.loc.light, normalize([dir[0] - 0.3 * dir[1], dir[1] + 0.3 * dir[0], dir[2] + 0.5]));
    gl.enableVertexAttribArray(this.loc.position);
    gl.enableVertexAttribArray(this.loc.normal);
    for (const { mesh, model, color } of this.items) {
      gl.uniformMatrix4fv(this.loc.model, false, model);
      gl.uniformMatrix3fv(this.loc.normalMat, false, [model[0], model[1], model[2], model[4], model[5], model[6], model[8], model[9], model[10]]);
      gl.uniform3fv(this.loc.color, color);
      gl.bindBuffer(gl.ARRAY_BUFFER, mesh.pos);
      gl.vertexAttribPointer(this.loc.position, 3, gl.FLOAT, false, 0, 0);
      gl.bindBuffer(gl.ARRAY_BUFFER, mesh.nrm);
      gl.vertexAttribPointer(this.loc.normal, 3, gl.FLOAT, false, 0, 0);
      gl.drawArrays(gl.TRIANGLES, 0, mesh.count);
    }
  }
}
```

- [ ] **Step 3: Run the test to see it pass**

Run: `cd ~/diy-window && python3 -m unittest discover -s web/tests -p 'test_server.py' -k Viewer 2>&1 | tail -3`
Expected: `Ran 1 test`, `OK`. The viewer is checked visually in Tasks 12 and 14.

---

### Task 12: The page (`web/static/index.html`, `style.css`, `app.js`)

The layout has three areas:
- the form on the left, with the render controls and downloads;
- the front view, check badges and failure explanations, beside the viewer;
- the parts table below, with tick boxes, states, and the job log.

`app.js` does the following:
- **Preview.** It debounces `/api/preview` by 250 ms and drops stale answers. It draws the SVG, flipping y into SVG coordinates, with the font size from `step`. It shows the errors next to their fields and greys out the stale drawing while the input is invalid.
- **Render.** It starts render jobs (all, or the ticked rows), polls `/api/job` every second, colours the rows, offers Cancel, and shows the download link (or a partial zip when some parts failed).
- **Box.** It polls `/api/box` every 30 s for the box indicator.
- **Query string.** It reads form values from the query string, and `view=<ID>` or `view=assembled` opens the viewer once the page has loaded.

**Files:**
- Create: `web/static/index.html`, `web/static/style.css`, `web/static/app.js`
- Create: `web/tests/ui_shots.py`
- Test: `web/tests/test_server.py` (append `PageTest`)

- [ ] **Step 1: Write the failing test**

**Append** to `web/tests/test_server.py`:
```python
class PageTest(ServerCase):
    def testPageStyleAndScriptAreServed(self):
        status, headers, body = self.request("GET", "/")
        self.assertEqual((status, headers["Content-Type"]), (200, "text/html; charset=utf-8"))
        self.assertIn(b'<script type="module" src="app.js"></script>', body)
        self.assertEqual(self.request("GET", "/style.css")[1]["Content-Type"], "text/css; charset=utf-8")
        status, headers, body = self.request("GET", "/app.js")
        self.assertEqual((status, headers["Content-Type"]), (200, "text/javascript; charset=utf-8"))
        self.assertIn(b'import { Viewer } from "./viewer.js";', body)
```

Run: `cd ~/diy-window && python3 -m unittest discover -s web/tests -p 'test_server.py' -k Page 2>&1 | tail -3`
Expected: `FAILED (failures=1)`, `404 != 200`.

- [ ] **Step 2: Write the page**

**Create** `web/static/index.html`:
```html
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>OpenWindow configurator</title>
<link rel="stylesheet" href="style.css">
<script type="module" src="app.js"></script>
</head>
<body>
<header>
  <h1>OpenWindow <span>configurator</span></h1>
  <div id="box" class="pill">Windows box: checking</div>
</header>
<main>
  <form id="form" autocomplete="off" novalidate>
    <fieldset>
      <legend>Window</legend>
      <label class="field">Name<input name="name" spellcheck="false"><small class="err" data-for="name"></small></label>
      <div class="pair">
        <label class="field">Opening width <em>mm</em><input name="opening_w" type="number" step="1"><small class="err" data-for="opening_w"></small></label>
        <label class="field">Opening height <em>mm</em><input name="opening_h" type="number" step="1"><small class="err" data-for="opening_h"></small></label>
      </div>
      <div class="pair">
        <label class="field">Fixing gap <em>mm, 6-10</em><input name="fix_gap" type="number" step="0.5"><small class="err" data-for="fix_gap"></small></label>
        <label class="field">Awning height <em>mm</em><input name="awning_h" type="number" step="1"><small class="err" data-for="awning_h"></small></label>
      </div>
      <label class="field">Glazing
        <select name="glazing">
          <option value="igu">IGU 4/16/4 double glazing</option>
          <option value="acrylic">Acrylic sandwich (2 x 4 mm)</option>
          <option value="twinwall">Twin-wall polycarbonate 16 mm</option>
        </select>
        <small class="err" data-for="glazing"></small>
      </label>
      <label class="field">Material tier
        <select name="tier">
          <option value="1">1: shaded, light colour</option>
          <option value="2">2: part sun, light colour</option>
          <option value="3">3: full sun, or any dark colour</option>
        </select>
        <small class="err" data-for="tier"></small>
      </label>
      <label class="check"><input name="screen" type="checkbox"> Insect screen</label>
    </fieldset>
    <fieldset>
      <legend>Printer</legend>
      <label class="field">Bed<select name="preset"></select></label>
      <div class="triple" id="custom-bed">
        <label class="field">X <em>mm</em><input name="bed_x" type="number" step="1"></label>
        <label class="field">Y <em>mm</em><input name="bed_y" type="number" step="1"></label>
        <label class="field">Z <em>mm</em><input name="bed_z" type="number" step="1"></label>
      </div>
      <small class="err" data-for="bed"></small>
      <p class="note" id="maxseg"></p>
    </fieldset>
    <small class="err" data-for="_form"></small>
    <fieldset>
      <legend>Render on the Windows box</legend>
      <div class="buttons">
        <button type="button" id="render-all">Render all</button>
        <button type="button" id="render-sel">Render selected</button>
        <button type="button" id="cancel" class="secondary">Cancel</button>
      </div>
      <div class="progress"><div id="bar"></div></div>
      <p class="note" id="job-text">No render in this session.</p>
      <p id="downloads"></p>
    </fieldset>
  </form>
  <section class="panel" id="drawing-panel">
    <h2>Front view <span>from outside, mm</span></h2>
    <div id="drawing"></div>
    <div id="badges"></div>
    <div id="explain"></div>
  </section>
  <section class="panel" id="viewer-panel">
    <h2><span id="viewer-title">Viewer</span><button type="button" id="assembled" class="small">Assembled</button></h2>
    <canvas id="viewer"></canvas>
    <p class="note" id="viewer-note">Click a part row to view its STL. Drag to orbit, scroll to zoom.</p>
  </section>
  <section class="panel" id="parts-panel">
    <h2>Parts <span id="parts-sum"></span></h2>
    <table id="parts">
      <thead><tr><th><input type="checkbox" id="select-all" title="Select all"></th><th>ID</th><th>Part</th><th class="n">Qty</th><th class="n">Length</th><th>Side</th><th>State</th></tr></thead>
      <tbody></tbody>
    </table>
    <pre id="log"></pre>
  </section>
</main>
</body>
</html>
```

**Create** `web/static/style.css`:
```css
/* OpenWindow configurator */
:root {
  --paper: #f4f3ef;
  --card: #fffffd;
  --ink: #1f262d;
  --muted: #69727b;
  --line: #d9d7cf;
  --accent: #245b8f;
  --ok: #2f7d4f;
  --fail: #b3261e;
  --warn: #9a6a00;
  --frame: #dcdad3;
  --sash: #c7d0d8;
  --glass: #dcebf5;
  --mono: ui-monospace, "SF Mono", Menlo, Consolas, monospace;
}
* { box-sizing: border-box; }
body { margin: 0; background: var(--paper); color: var(--ink); font: 14px/1.4 -apple-system, "Helvetica Neue", "Segoe UI", sans-serif; }
header { display: flex; align-items: center; justify-content: space-between; padding: 12px 20px; border-bottom: 1px solid var(--line); background: var(--card); }
h1 { margin: 0; font-size: 18px; letter-spacing: 0.02em; }
h1 span { font-weight: 400; color: var(--muted); }
h2 { display: flex; align-items: center; gap: 8px; margin: 0 0 10px; font-size: 13px; text-transform: uppercase; letter-spacing: 0.06em; }
h2 span { text-transform: none; letter-spacing: 0; font-weight: 400; color: var(--muted); }
h2 #viewer-title { color: var(--ink); font-weight: 600; }
main { display: grid; gap: 16px; padding: 16px 20px; grid-template-columns: 300px minmax(0, 1.25fr) minmax(0, 1fr);
       grid-template-areas: "form drawing viewer" "form parts parts"; align-items: start; }
#form { grid-area: form; }
#drawing-panel { grid-area: drawing; }
#viewer-panel { grid-area: viewer; }
#parts-panel { grid-area: parts; }
@media (max-width: 1100px) {
  main { grid-template-columns: 300px minmax(0, 1fr); grid-template-areas: "form drawing" "form viewer" "parts parts"; }
}
.panel, fieldset { background: var(--card); border: 1px solid var(--line); border-radius: 6px; padding: 14px; }
fieldset { margin: 0 0 12px; }
legend { padding: 0 4px; font-size: 12px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.06em; color: var(--muted); }
.field { display: block; margin-bottom: 10px; font-size: 12px; color: var(--muted); }
.field em { font-style: normal; opacity: 0.7; }
input, select { display: block; width: 100%; margin-top: 3px; padding: 6px 8px; border: 1px solid var(--line); border-radius: 4px;
                background: #fff; color: var(--ink); font: 14px var(--mono); }
select { font-family: inherit; }
input:focus, select:focus { outline: 2px solid var(--accent); outline-offset: -1px; }
input.invalid { border-color: var(--fail); background: #fff6f5; }
.check { display: flex; align-items: center; gap: 8px; font-size: 13px; }
.check input, th input, td input { width: auto; margin: 0; }
.pair { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
.triple { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 8px; }
.triple.hidden { display: none; }
.err { display: block; min-height: 0; color: var(--fail); font-size: 12px; }
.err:empty { display: none; }
.note { margin: 6px 0 0; font-size: 12px; color: var(--muted); }
.buttons { display: flex; gap: 8px; flex-wrap: wrap; }
button { padding: 7px 12px; border: 1px solid var(--accent); border-radius: 4px; background: var(--accent); color: #fff; font: 600 13px inherit; cursor: pointer; }
button.secondary, button.small { background: #fff; color: var(--accent); }
button.small { padding: 2px 8px; font-size: 11px; margin-left: auto; }
button:disabled { opacity: 0.4; cursor: default; }
.progress { height: 6px; margin-top: 12px; border-radius: 3px; background: var(--line); overflow: hidden; }
#bar { width: 0; height: 100%; background: var(--accent); }
#bar.done { background: var(--ok); }
#bar.failed, #bar.cancelled { background: var(--fail); }
#downloads a { display: block; margin-top: 8px; color: var(--accent); font-weight: 600; }
.pill { padding: 3px 10px; border-radius: 12px; border: 1px solid var(--line); font-size: 12px; color: var(--muted); }
.pill::before { content: ""; display: inline-block; width: 8px; height: 8px; margin-right: 6px; border-radius: 50%; background: var(--muted); }
.pill.ok::before { background: var(--ok); }
.pill.down { color: var(--fail); border-color: var(--fail); }
.pill.down::before { background: var(--fail); }
#drawing svg { display: block; width: 100%; height: auto; max-height: 62vh; }
.stale { opacity: 0.35; }
.r-opening { fill: none; stroke: var(--muted); stroke-dasharray: 6 4; }
.r-frame, .r-transom { fill: var(--frame); stroke: var(--ink); }
.r-glass, .r-sash-glass { fill: var(--glass); fill-opacity: 0.6; stroke: var(--accent); stroke-dasharray: 3 3; }
.r-sash { fill: var(--sash); stroke: var(--ink); }
.r-screen { fill: none; stroke: var(--warn); stroke-dasharray: 10 5; }
.dim line { stroke: var(--accent); }
.dim text, .label { fill: var(--ink); font-family: var(--mono); }
.dim text { fill: var(--accent); }
#badges { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 10px; }
.badge { padding: 3px 9px; border-radius: 12px; font-size: 12px; font-weight: 600; border: 1px solid; }
.badge.ok { color: var(--ok); border-color: var(--ok); background: #f1f8f3; }
.badge.fail { color: #fff; border-color: var(--fail); background: var(--fail); }
#explain p { margin: 6px 0 0; color: var(--fail); font-size: 12px; }
table { width: 100%; border-collapse: collapse; font-size: 13px; }
th { text-align: left; font-size: 11px; text-transform: uppercase; letter-spacing: 0.05em; color: var(--muted); border-bottom: 1px solid var(--line); padding: 4px 6px; }
td { padding: 4px 6px; border-bottom: 1px solid #eeece6; }
td.id { font: 600 13px var(--mono); }
.n { text-align: right; font-family: var(--mono); }
tbody tr { cursor: pointer; }
tbody tr:hover { background: #f7f6f1; }
tbody tr.viewing { background: #eaf1f8; }
.st { font-size: 12px; font-weight: 600; }
.st-ok { color: var(--ok); }
.st-failed { color: var(--fail); }
.st-rendering { color: var(--accent); }
.st-queued, .st-cancelled, .st-skipped { color: var(--muted); }
tr.failed td { background: #fff1ef; }
#log { max-height: 160px; overflow: auto; margin: 10px 0 0; padding: 8px; background: #22282e; color: #d7dde2; font: 11px/1.45 var(--mono); border-radius: 4px; }
#log:empty { display: none; }
#viewer { display: block; width: 100%; height: 360px; border-radius: 4px; background: #e9edf0; cursor: grab; }
```

**Create** `web/static/app.js`:
```js
// OpenWindow configurator page: form, live preview, render jobs, downloads.
import { Viewer } from "./viewer.js";

const $ = (sel) => document.querySelector(sel);
const form = $("#form");
const SVG = "http://www.w3.org/2000/svg";
const CHECKS = { transom_deflection: "Transom deflection", sash_weight: "Friction stay", segment_length: "Segment length",
                 cam_keeper: "Cam / keeper", bed_fit: "Bed fit" };
const FIELDS = ["name", "opening_w", "opening_h", "fix_gap", "awning_h", "glazing", "tier"];
const state = { presets: [], preview: null, job: null, selected: new Set(), seq: 0, timer: 0, poll: 0, viewing: null };
const viewer = new Viewer($("#viewer"));

async function getJson(path) {
  const r = await fetch(path);
  return r.json();
}

async function postJson(path, body) {
  const r = await fetch(path, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
  return { status: r.status, body: await r.json() };
}

function num(name) {
  const v = form.elements[name].value.trim();
  return v === "" ? null : Number(v);
}

function readForm() {
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
  const preset = state.presets.find((x) => x.bed.join() === p.bed.join());
  form.elements.preset.value = preset ? preset.key : "custom";
  ["bed_x", "bed_y", "bed_z"].forEach((k, i) => { form.elements[k].value = p.bed[i]; });
  $("#custom-bed").classList.toggle("hidden", Boolean(preset));
}

function fromQuery(defaults) {
  const q = new URLSearchParams(location.search);
  const p = { ...defaults };
  for (const k of FIELDS) if (q.has(k)) p[k] = q.get(k);
  if (q.has("screen")) p.screen = !["0", "false", "no"].includes(q.get("screen"));
  if (q.has("bed")) p.bed = q.get("bed").split(",").map(Number);
  return p;
}

function currentName() {
  return form.elements.name.value.trim();
}

function showErrors(errors) {
  for (const el of document.querySelectorAll(".err")) el.textContent = errors[el.dataset.for] || "";
  for (const el of form.querySelectorAll("input")) {
    const key = el.name.startsWith("bed_") ? "bed" : el.name;
    el.classList.toggle("invalid", Boolean(errors[key]));
  }
}

function schedulePreview() {
  clearTimeout(state.timer);
  state.timer = setTimeout(runPreview, 250);
}

async function runPreview() {
  const seq = ++state.seq;
  const { body } = await postJson("/api/preview", readForm());
  if (seq !== state.seq) return;
  state.preview = body;
  showErrors(body.errors);
  const drawn = Boolean(body.drawing);
  for (const id of ["#drawing", "#badges", "#explain", "#parts"]) $(id).classList.toggle("stale", !drawn);
  if (drawn) {
    drawFront(body.drawing);
    showChecks(body.checks);
    showParts(body.parts);
    $("#maxseg").textContent = `Bed ${body.layout.bed.join(" x ")} mm: segments up to ${body.layout.max_seg} mm.`;
  }
  updateButtons();
}

function el(tag, attrs, text) {
  const node = document.createElementNS(SVG, tag);
  for (const [k, v] of Object.entries(attrs)) node.setAttribute(k, v);
  if (text !== undefined) node.textContent = text;
  return node;
}

function drawFront(d) {
  const [x0, y0, x1, y1] = d.bounds;
  const Y = (y) => y0 + y1 - y;
  const fs = d.step * 0.42;
  const t = d.step * 0.12;
  const svg = el("svg", { viewBox: `${x0} ${y0} ${x1 - x0} ${y1 - y0}`, "font-size": fs });
  for (const r of d.rects) {
    svg.append(el("rect", { class: `r-${r.kind}`, x: r.x, y: Y(r.y + r.h), width: r.w, height: r.h, "vector-effect": "non-scaling-stroke" }));
  }
  for (const m of d.dims) {
    const g = el("g", { class: "dim" });
    const line = (ax, ay, bx, by) => g.append(el("line", { x1: ax, y1: Y(ay), x2: bx, y2: Y(by), "vector-effect": "non-scaling-stroke" }));
    const mid = (m.a + m.b) / 2;
    if (m.axis === "x") {
      line(m.a, m.at, m.b, m.at);
      for (const x of [m.a, m.b]) { line(x, m.from, x, m.at - t); line(x - t, m.at - t, x + t, m.at + t); }
      g.append(el("text", { x: mid, y: Y(m.at) - fs * 0.35, "text-anchor": "middle" }, m.text));
    } else {
      line(m.at, m.a, m.at, m.b);
      for (const y of [m.a, m.b]) { line(m.from, y, m.at + (m.at > m.from ? t : -t), y); line(m.at - t, y - t, m.at + t, y + t); }
      const tx = m.at - fs * 0.35;
      g.append(el("text", { x: tx, y: Y(mid), "text-anchor": "middle", transform: `rotate(-90 ${tx} ${Y(mid)})` }, m.text));
    }
    svg.append(g);
  }
  for (const l of d.labels) svg.append(el("text", { class: "label", x: l.x, y: Y(l.y), "text-anchor": "middle", "dominant-baseline": "middle" }, l.text));
  $("#drawing").replaceChildren(svg);
}

function showChecks(checks) {
  $("#badges").replaceChildren(...checks.map((c) => {
    const b = document.createElement("span");
    b.className = `badge ${c.ok ? "ok" : "fail"}`;
    b.textContent = CHECKS[c.name] || c.name;
    b.title = c.msg;
    return b;
  }));
  $("#explain").replaceChildren(...checks.filter((c) => !c.ok).map((c) => {
    const p = document.createElement("p");
    p.textContent = `${CHECKS[c.name] || c.name}: ${c.msg}`;
    return p;
  }));
}

function partState(id) {
  const job = state.job;
  return job && job.name === currentName() ? job.parts[id] || "" : "";
}

function showParts(parts) {
  const ids = new Set(parts.map((p) => p.id));
  state.selected = new Set([...state.selected].filter((id) => ids.has(id)));
  const rows = parts.map((p) => {
    const tr = document.createElement("tr");
    tr.dataset.id = p.id;
    const cells = [p.id, p.name, p.qty, p.length === null ? "" : p.length.toFixed(2), p.role, ""];
    const box = document.createElement("input");
    box.type = "checkbox";
    box.checked = state.selected.has(p.id);
    box.addEventListener("change", () => {
      if (box.checked) state.selected.add(p.id); else state.selected.delete(p.id);
      updateButtons();
    });
    const first = document.createElement("td");
    first.append(box);
    tr.append(first);
    cells.forEach((text, i) => {
      const td = document.createElement("td");
      td.textContent = text;
      td.className = ["id", "", "n", "n", "", "st"][i];
      tr.append(td);
    });
    tr.addEventListener("click", (e) => { if (e.target !== box) viewPart(p); });
    return tr;
  });
  $("#parts tbody").replaceChildren(...rows);
  const prints = parts.reduce((n, p) => n + p.qty, 0);
  $("#parts-sum").textContent = `${parts.length} types, ${prints} prints`;
  showStates();
}

function showStates() {
  const errors = state.job && state.job.name === currentName() ? state.job.errors : {};
  for (const tr of document.querySelectorAll("#parts tbody tr")) {
    const s = partState(tr.dataset.id);
    const cell = tr.lastChild;
    cell.textContent = s;
    cell.className = `st st-${s}`;
    tr.classList.toggle("failed", s === "failed");
    tr.classList.toggle("viewing", tr.dataset.id === state.viewing);
    tr.title = (errors[tr.dataset.id] || []).join("\n");
  }
}

function updateButtons() {
  const running = Boolean(state.job && state.job.state === "running");
  const renderable = Boolean(state.preview && state.preview.ok) && !running;
  $("#render-all").disabled = !renderable;
  $("#render-sel").disabled = !renderable || state.selected.size === 0;
  $("#render-sel").textContent = state.selected.size ? `Render selected (${state.selected.size})` : "Render selected";
  $("#cancel").disabled = !running;
  $("#select-all").checked = state.preview && state.preview.parts ? state.selected.size === state.preview.parts.length : false;
  const links = [];
  const job = state.job;
  if (job && !running && job.name === currentName()) {
    const okCount = Object.values(job.parts).filter((s) => s === "ok").length;
    const href = `/api/zip/${encodeURIComponent(job.name)}`;
    if (job.state === "done") links.push([href, `Download ${job.name}-openwindow.zip`]);
    else if (okCount) links.push([`${href}?partial=1`, `Download partial zip (${okCount} parts ok)`]);
  }
  $("#downloads").replaceChildren(...links.map(([href, text]) => {
    const a = document.createElement("a");
    a.href = href;
    a.textContent = text;
    a.setAttribute("download", "");
    return a;
  }));
}

function showJob(job) {
  state.job = job.state === "idle" ? null : job;
  const bar = $("#bar");
  if (!state.job) {
    $("#job-text").textContent = "No render in this session.";
  } else {
    bar.style.width = `${job.total ? (100 * job.done) / job.total : 0}%`;
    bar.className = job.state;
    const text = {
      running: `Rendering ${job.name}: ${job.done} of ${job.total} parts, now ${job.current.join(" ")} (${job.elapsed} s)`,
      done: `Rendered ${job.name}: ${job.total} parts ok in ${job.elapsed} s.`,
      failed: `${job.name}: ${job.error}`,
      cancelled: `Cancelled after ${job.done} of ${job.total} parts.`,
    };
    $("#job-text").textContent = text[job.state] || job.state;
    $("#log").textContent = job.state === "done" ? "" : job.log_tail.join("\n");
  }
  showStates();
  updateButtons();
}

async function pollJob() {
  const job = await getJson("/api/job");
  showJob(job);
  if (job.state !== "running") clearInterval(state.poll);
}

function startPolling() {
  clearInterval(state.poll);
  state.poll = setInterval(pollJob, 1000);
}

async function startRender(ids) {
  const body = readForm();
  if (ids) body.ids = ids;
  const r = await postJson("/api/render", body);
  if (r.status !== 200) {
    showErrors(r.body.errors || { _form: r.body.error });
    return;
  }
  showJob(r.body.job);
  startPolling();
}

async function pollBox() {
  const b = await getJson("/api/box");
  const pill = $("#box");
  pill.className = `pill ${b.ok ? "ok" : "down"}`;
  pill.textContent = `Windows box ${b.host}: ${b.ok ? "reachable" : "unreachable"}`;
}

async function viewPart(p) {
  state.viewing = p.id;
  showStates();
  $("#viewer-title").textContent = `${p.id}: ${p.name}`;
  try {
    await viewer.showPart(`/api/stl/${encodeURIComponent(currentName())}/${p.id}`);
    $("#viewer-note").textContent = `Print ${p.qty}. Drag to orbit, scroll to zoom.`;
  } catch (e) {
    viewer.clear();
    $("#viewer-note").textContent = `${p.id} is not rendered yet for ${currentName()}.`;
  }
}

async function viewAssembly() {
  if (!state.preview || !state.preview.assembly) return;
  state.viewing = null;
  showStates();
  $("#viewer-title").textContent = `${currentName()}: frame, transom and sash`;
  const name = encodeURIComponent(currentName());
  const missing = await viewer.showAssembly((id) => `/api/stl/${name}/${id}`, state.preview.assembly);
  $("#viewer-note").textContent = missing.length
    ? `Not rendered yet: ${missing.join(", ")}.`
    : "Seen from outside. Drag to orbit, scroll to zoom.";
}

async function init() {
  const { presets, defaults } = await getJson("/api/presets");
  state.presets = presets;
  const select = form.elements.preset;
  for (const p of presets) select.append(new Option(p.label, p.key));
  select.append(new Option("Custom", "custom"));
  fillForm(fromQuery(defaults));
  form.addEventListener("input", (e) => {
    if (e.target.name === "preset") {
      const preset = presets.find((p) => p.key === select.value);
      if (preset) fillForm({ ...readForm(), bed: preset.bed });
      $("#custom-bed").classList.toggle("hidden", Boolean(preset));
    }
    schedulePreview();
  });
  $("#render-all").addEventListener("click", () => startRender(null));
  $("#render-sel").addEventListener("click", () => startRender([...state.selected]));
  $("#cancel").addEventListener("click", () => postJson("/api/cancel", {}).then(pollJob));
  $("#assembled").addEventListener("click", viewAssembly);
  $("#select-all").addEventListener("change", (e) => {
    state.selected = new Set(e.target.checked && state.preview.parts ? state.preview.parts.map((p) => p.id) : []);
    for (const box of document.querySelectorAll("#parts tbody input")) box.checked = e.target.checked;
    updateButtons();
  });
  await runPreview();
  await pollJob();
  if (state.job && state.job.state === "running") startPolling();
  pollBox();
  setInterval(pollBox, 30000);
  const view = new URLSearchParams(location.search).get("view");
  if (view === "assembled") viewAssembly();
  else if (view && state.preview.parts) {
    const part = state.preview.parts.find((p) => p.id === view);
    if (part) viewPart(part);
  }
}

init();
```

- [ ] **Step 3: Run the test to see it pass**

Run: `cd ~/diy-window && python3 -m unittest discover -s web/tests -p 'test_server.py' -k Page 2>&1 | tail -3`
Expected: `Ran 1 test`, `OK`.

- [ ] **Step 4: Write the screenshot driver**

It starts two servers: the real one on `--port` (8781 by default), and a `--fake-render` one on the next port. It puts each into a state, then has headless Chrome screenshot the page. Chrome runs with a throwaway `--user-data-dir`, so your own Chrome profile isn't touched. Chrome 156 writes the PNG and then doesn't exit, so the script waits for the file and then stops Chrome's process group.

**Create** `web/tests/ui_shots.py`:
```python
#!/usr/bin/env python3
"""Headless-Chrome screenshots of the configurator's UI states, for review by eye (no installs; uses the Mac's Chrome)."""
import argparse
import json
import os
import pathlib
import signal
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request

WEB = pathlib.Path(__file__).resolve().parent.parent
ROOT = WEB.parent
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"


def params(name):
    return json.loads((ROOT / "params" / f"{name}.json").read_text())


def query(p, **extra):
    return "/?" + urllib.parse.urlencode({**{k: v for k, v in p.items() if k != "bed"}, **extra})


def call(base, method, path, body=None):
    data = None if body is None else json.dumps(body).encode()
    req = urllib.request.Request(base + path, data=data, method=method,
                                 headers={"Content-Type": "application/json"} if body is not None else {})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())


def start(port, *flags):
    proc = subprocess.Popen([sys.executable, str(WEB / "server.py"), "--port", str(port), *flags])
    for _ in range(50):
        try:
            call(f"http://127.0.0.1:{port}", "GET", "/api/presets")
            return proc
        except OSError:
            time.sleep(0.2)
    raise SystemExit(f"server on port {port} did not start")


def shot(url, out, profile, budget=6000):
    out.unlink(missing_ok=True)
    chrome = subprocess.Popen([CHROME, "--headless=new", "--use-angle=swiftshader", "--enable-unsafe-swiftshader",
                               "--hide-scrollbars", "--no-first-run", "--no-default-browser-check",
                               f"--user-data-dir={profile}", "--window-size=1440,1100",
                               f"--virtual-time-budget={budget}", f"--screenshot={out}", url],
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
    end, size = time.time() + 60, -1
    while time.time() < end and not (out.exists() and out.stat().st_size == size > 0):
        size = out.stat().st_size if out.exists() else -1
        time.sleep(1)
    os.killpg(chrome.pid, signal.SIGTERM)
    chrome.wait(10)
    print(f"{out.name}: {url}" if out.exists() else f"{out.name}: NO SCREENSHOT ({url})")


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("out", type=pathlib.Path, help="folder for the PNGs")
    ap.add_argument("--port", type=int, default=8781)
    a = ap.parse_args(argv[1:])
    a.out.mkdir(parents=True, exist_ok=True)
    real, fake = f"http://127.0.0.1:{a.port}", f"http://127.0.0.1:{a.port + 1}"
    servers = [start(a.port), start(a.port + 1, "--fake-render")]
    try:
        with tempfile.TemporaryDirectory() as profile:
            shot(real + "/", a.out / "1-valid.png", profile)
            shot(real + "/?name=Bad%20Name&opening_w=100", a.out / "2-invalid.png", profile)
            shot(real + "/?opening_w=3000&name=wide", a.out / "3-failed-check.png", profile)
            bench = dict(params("bench-600"), name="shot-bench")
            call(fake, "POST", "/api/render", bench)
            time.sleep(4)
            shot(fake + query(bench), a.out / "4-rendering.png", profile, budget=1500)
            while call(fake, "GET", "/api/job")["state"] == "running":
                time.sleep(0.5)
            shot(fake + query(bench), a.out / "5-download.png", profile)
            shot(real + query(params("bench-600"), view="SBE"), a.out / "6-viewer-part.png", profile)
            shot(real + query(params("home-1800x1500"), view="assembled"), a.out / "7-viewer-assembled.png", profile, 10000)
    finally:
        for s in servers:
            s.send_signal(signal.SIGINT)
            s.wait(10)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
```

- [ ] **Step 5: Smoke-test the page**

Run: `cd ~/diy-window && rm -rf .web-after/shots && python3 web/tests/ui_shots.py .web-after/shots | grep png`
Expected: seven lines, from `1-valid.png: http://127.0.0.1:8781/` to `7-viewer-assembled.png: …`, in about a minute. None should say `NO SCREENSHOT`.

Open `.web-after/shots/1-valid.png`. It must show:
- the form, with `my-window`, 1800 × 1500, gap 8, awning 450, IGU, tier 3, screen ticked and the Bambu bed;
- the front view, with the dimensions `opening 1800`, `frame 1784`, `opening 1500`, `frame 1484`, `transom centre 941`, `awning 450` and `fixed 848`, and the labels `fixed glass 1698 x 878` and `sash 1678 x 460, glass 1606 x 388`;
- five green badges;
- a parts table starting `H  Head segment  7  237.14  exterior`;
- the box indicator.

The full review is Task 14.

- [ ] **Step 6: Checkpoint**

Run: `cd ~/diy-window && python3 -m unittest discover -s web/tests -p 'test_*.py' 2>&1 | grep -E '^(Ran|OK|FAILED)'`
Expected: `Ran 94 tests`, `OK`.

---

### Task 13: Live render on the Windows box (`web/tests/live_render.py`)

> **Needs the Windows build box on the LAN.** `cad/box.sh ping` must print `ok`.

The script starts `web/server.py` on port 8799 against the real box and runs these steps:
1. **Cancel check** (`--cancel`): it starts a render, cancels it during the second batch, and checks that the job ends `cancelled` with no `.generate.lock` left behind.
2. **Render:** it renders all of `bench-600` through `POST /api/render`, polling every 2 s.
3. **Zip:** it downloads the zip and checks it holds 37 STLs and the six other files, and that `README.txt` starts with the window name.
4. **Compare:** it counts how many STLs are byte-identical to the renders that were there before.

The bench params are posted unchanged, so `save_params` keeps `params/bench-600.json` as it is. The run rewrites `cad/stl/bench-600/` and `bom/bench-600.*`; on 2026-10-10 both came out byte-identical.

**Files:**
- Create: `web/tests/live_render.py`

- [ ] **Step 1: Write the script**

**Create** `web/tests/live_render.py`:
```python
#!/usr/bin/env python3
"""Live end-to-end check (needs the Windows build box): render bench-600 through web/server.py, then check the zip."""
import argparse
import io
import json
import pathlib
import subprocess
import sys
import time
import urllib.error
import urllib.request
import zipfile

WEB = pathlib.Path(__file__).resolve().parent.parent
ROOT = WEB.parent
NAME = "bench-600"


def call(base, method, path, body=None):
    data = None if body is None else json.dumps(body).encode()
    req = urllib.request.Request(base + path, data=data, method=method,
                                 headers={"Content-Type": "application/json"} if body is not None else {})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        with e:
            return e.code, e.read()


def job(base):
    return json.loads(call(base, "GET", "/api/job")[1])


def wait(base, until, timeout):
    end, last = time.time() + timeout, None
    while time.time() < end:
        j = job(base)
        line = f"  {j['state']:<9} {j.get('done', 0):>2}/{j.get('total', 0)} current={' '.join(j.get('current', []))}"
        if line != last:
            print(f"{line}  ({j.get('elapsed', 0):.0f} s)", flush=True)
            last = line
        if until(j):
            return j
        time.sleep(2)
    raise SystemExit(f"timed out after {timeout} s: {j}")


def cancel_check(base, params):
    print("cancel check: start, wait for the second batch, cancel")
    assert call(base, "POST", "/api/render", params)[0] == 200
    wait(base, lambda j: j["done"] >= 6 or j["state"] != "running", 900)
    status, _ = call(base, "POST", "/api/cancel", {})
    j = wait(base, lambda j: j["state"] != "running", 120)
    lock = (ROOT / ".generate.lock").exists()
    print(f"cancel check: cancel -> {status}, state {j['state']}, generate lock left behind: {lock}")
    return status == 200 and j["state"] == "cancelled" and not lock


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--port", type=int, default=8799)
    ap.add_argument("--cancel", action="store_true", help="first start a render and cancel it during the second batch")
    a = ap.parse_args(argv[1:])
    base = f"http://127.0.0.1:{a.port}"
    params = json.loads((ROOT / "params" / f"{NAME}.json").read_text())
    before = {f.name: f.read_bytes() for f in (ROOT / "cad" / "stl" / NAME).glob("*.stl")}
    srv = subprocess.Popen([sys.executable, str(WEB / "server.py"), "--port", str(a.port)])
    try:
        for _ in range(50):
            try:
                call(base, "GET", "/api/presets")
                break
            except OSError:
                time.sleep(0.2)
        box = json.loads(call(base, "GET", "/api/box")[1])
        print(f"box {box['host']}: {'reachable' if box['ok'] else 'UNREACHABLE'}")
        if not box["ok"]:
            return 1
        if a.cancel and not cancel_check(base, params):
            return 1
        t0 = time.time()
        status, body = call(base, "POST", "/api/render", params)
        print(f"render -> {status}")
        if status != 200:
            print(body.decode())
            return 1
        j = wait(base, lambda j: j["state"] != "running", 1800)
        print(f"job {j['state']} in {time.time() - t0:.0f} s; error: {j['error'] or 'none'}")
        if j["state"] != "done":
            print("\n".join(j["log_tail"]))
            return 1
        status, data = call(base, "GET", f"/api/zip/{NAME}")
        z = zipfile.ZipFile(io.BytesIO(data))
        stls = [n for n in z.namelist() if n.startswith("stl/")]
        others = sorted(n for n in z.namelist() if not n.startswith("stl/"))
        same = sum(1 for n in stls if before.get(n[4:].split("_x")[0] + ".stl") == z.read(n))
        readme = z.read("README.txt").decode()
        print(f"zip -> {status}, {len(data)} bytes, {len(stls)} STLs, {same} byte-identical to the previous render")
        print(f"zip files: {', '.join(others)}")
        print(f"README first line: {readme.splitlines()[0]}")
        ok = (status == 200 and len(stls) == 37 and readme.startswith(f"OpenWindow: {NAME}")
              and others == ["BOM.md", "README.txt", "cutlist.csv", "glass.csv", "params.json", "parts.csv"])
        print("LIVE RENDER OK" if ok else "LIVE RENDER FAILED")
        return 0 if ok else 1
    finally:
        srv.terminate()
        srv.wait(10)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
```

- [ ] **Step 2: Run it**

Run: `cd ~/diy-window && python3 web/tests/live_render.py --cancel`
Expected, within a few minutes (the times will vary):
```
box 192.168.68.61: reachable
cancel check: start, wait for the second batch, cancel
  running    0/37 current=H SW JL JU TE SH  (0 s)
  running    6/37 current=SBE SV NH NV CH CSL  (10 s)
  cancelled  6/37 current=  (10 s)
cancel check: cancel -> 200, state cancelled, generate lock left behind: False
render -> 200
  running    0/37 current=H SW JL JU TE SH  (0 s)
  ...
  done      37/37 current=  (61 s)
job done in 62 s; error: none
zip -> 200, 754132 bytes, 37 STLs, 37 byte-identical to the previous render
zip files: BOM.md, README.txt, cutlist.csv, glass.csv, params.json, parts.csv
README first line: OpenWindow: bench-600
LIVE RENDER OK
```
If the box is unreachable, the script prints `box 192.168.68.61: UNREACHABLE` and exits with status 1. Fix the box, then re-run.

- [ ] **Step 3: Checkpoint**

Run the **compatibility check** (Task 0). Expected: `BYTE-IDENTICAL`, because the job's BOM step wrote the same `bom/bench-600.*`.

Then run: `cd ~/diy-window/tools && python3 -m unittest discover -p 'test_*.py' 2>&1 | grep -E '^(Ran|OK|FAILED)'`
Expected: `Ran 165 tests`, `OK`. The envelope test re-reads the re-rendered bench STLs.

---

### Task 14: Screenshot review of the UI states

**Files:** none. This produces review screenshots in `.web-after/shots/`.

- [ ] **Step 1: Take the screenshots**

Run: `cd ~/diy-window && rm -rf .web-after/shots && python3 web/tests/ui_shots.py .web-after/shots | grep png`
Expected: seven `<n>-<state>.png: <url>` lines and no `NO SCREENSHOT`.

- [ ] **Step 2: Review each one by eye**

Open each PNG and tick it off. Fix the CSS/JS and re-run until all seven pass.

| File | Must show |
|---|---|
| `1-valid.png` | Task 12 Step 5's list. `Render all` is enabled, and `Render selected` and `Cancel` are disabled |
| `2-invalid.png` | Red outlines and messages under Name ("1-40 characters: lowercase letters, digits and dashes") and Opening width ("300-3000 mm"). No drawing (nothing valid has been typed yet). The parts table is greyed out. Both render buttons are disabled |
| `3-failed-check.png` | A 3000 mm wide window. The red `Transom deflection` badge, with the red line "Transom deflection: transom deflects 54.2 mm at 0.7 kPa, limit span/175 = 16.4 mm". `Render all` is still enabled |
| `4-rendering.png` | `shot-bench` (600 × 600, acrylic, tier 1). A part-filled blue progress bar, and "Rendering shot-bench: N of 37 parts, now …". `Cancel` is enabled and the render buttons are disabled. The visible rows show `ok` (the later rows, below the fold, are `rendering` or `queued`) |
| `5-download.png` | A full green bar, "Rendered shot-bench: 37 parts ok in … s.", the link "Download shot-bench-openwindow.zip", and every row `ok` |
| `6-viewer-part.png` | Viewer title "SBE: Sash bottom end segment, weep and keeper bosses". A grey sash segment standing on its end face, with the weep slot visible, and the note "Print 2. …". The SBE row is highlighted |
| `7-viewer-assembled.png` | Viewer title "home-1800x1500: frame, transom and sash". The whole frame seen from outside: grey frame, darker transom, blue-grey sash at the top. No gaps at the corners or the jamb nodes, and no parts outside the frame |

- [ ] **Step 3: Try the interactions by hand**

Headless Chrome can't click, type or drag, so check these once in your own browser. Start the server with `python3 web/server.py --fake-render` (stop it with Ctrl-C) and open `http://127.0.0.1:8765/`:

1. Change Opening width to 2400. The drawing, badges and part counts update within about a third of a second. Then set it back to 1800.
2. Type `Bad` into Name. The field turns red and both render buttons go off. Put `my-window` back.
3. Pick Prusa MK4. The note says `Bed 250 x 210 x 220 mm: segments up to 204 mm`, and the head goes from 7 to 9 segments. Pick Custom: the X/Y/Z fields appear.
4. Untick Insect screen. `NH`, `NV`, `CN`, `HG` and `HS` leave the table, and the yellow screen outline leaves the drawing.
5. Tick two rows. The button reads `Render selected (2)`. Click it: the two rows go through `rendering` to `ok`.
6. Click `Render all`, then `Cancel` while it runs. The job text reads `Cancelled after …`, and the unfinished rows read `cancelled`.
7. Click `Render all` and let it finish. Click the download link: `my-window-openwindow.zip` downloads.
8. Click a rendered row. The viewer shows a box (the fake renderer draws boxes). Drag to orbit and scroll to zoom. Click `Assembled`: the boxes appear in the window's layout.

---

### Task 15: Documentation and clean-up

**Files:**
- Create: `web/README.md`
- Modify: `README.md`
- Modify: `docs/specs/2026-10-10-web-configurator-design.md` (status line)
- Delete: `.web-baseline/`, `.web-after/`

- [ ] **Step 1: Write the web README**

**Create** `web/README.md`:
```markdown
# OpenWindow web configurator

A local page for one window opening. Type the opening and the options, and it shows:
- the window as you type: a dimensioned front view, the checks and the parts table;
- every printable part, rendered by OpenSCAD on the Windows build box, with a 3D viewer;
- one zip with the STLs, cut list, glass sizes, BOM, params file and a README for that opening.

It runs on the Mac and is not public: the server only listens on 127.0.0.1.

## Run

    python3 web/server.py                  # then open http://127.0.0.1:8765/
    python3 web/server.py --port 9000      # another port
    python3 web/server.py --fake-render    # page work without the box: box-shaped STLs in a temporary folder, removed on Ctrl-C

Requirements:
- Python 3 on the Mac (standard library only) and a browser. Nothing gets installed or downloaded.
- For rendering: the Windows build box on the LAN, with the SSH key `cad/box.sh` already uses. Check it with `cad/box.sh ping` (prints `ok`).

## Using it

1. **Type.** The front view, check badges and parts table follow the form. A red field message means the input is invalid, and Render stays off until it is fixed. A red badge is a failed check: rendering and downloading still work, and the zip's `README.txt` then starts with "CHECKS FAILED — do not print".
2. **Printer.** Pick a bed preset or Custom. The generator splits every member into segments of at most min(Z, max(X, Y)) − 16 mm, and the Bed fit badge checks every part against the bed.
3. **Render all**, or tick rows and **Render selected**. The window's params are saved to `params/<name>.json`. A reference window (`bench-600`, `home-1800x1500`) is never overwritten: rendering it with its own values is fine, and changed values need another name. Parts render in batches of up to six through `cad/box.sh render`, each STL is checked like `tools/check_stl.py` does, and `bom/<name>.*` is rebuilt at the end. One job runs at a time, and **Cancel** stops the running batch.
4. **View.** Click a part row to see its STL, or **Assembled** for the frame, transom and sash in place, seen from outside. Drag to orbit and scroll to zoom.
5. **Download** `<name>-openwindow.zip` once every part has passed its STL check. If some parts failed, a partial zip leaves them out and lists them at the top of its `README.txt`.

Any form field can also be preset in the address, for example `/?name=bench-600&opening_w=600&opening_h=600&awning_h=200&glazing=acrylic&tier=1`. Add `view=<ID>` or `view=assembled` to open the viewer.

## Files it writes

The same files as the command-line flow: `params/<name>.json`, `cad/generated/` (rewritten by every `box.sh` batch, as on the command line), `cad/stl/<name>/` and `bom/<name>.*`. The zip is built on request and isn't stored.

## Tests

    python3 -m unittest discover -s web/tests -p 'test_*.py'   # no box needed; the renderer is web/fake_box.py
    python3 web/tests/live_render.py --cancel                  # needs the box: cancel check, then bench-600 end to end
    python3 web/tests/ui_shots.py <folder>                     # headless-Chrome screenshots of each UI state

## Troubleshooting

- **"Windows build box unreachable (192.168.68.61)"**: the box is off, asleep or off the LAN, or the VPN is in the way. `cad/box.sh ping` must print `ok`. The preview keeps working without the box.
- **A red part row**: hover it for its STL check errors. The log under the parts table shows the output of `box.sh`.
- **"timed out waiting for the generate.py lock"**: another `generate.py` or `box.sh` is running in a terminal. If nothing is running, an interrupted run left `.generate.lock` behind: remove it with `rmdir .generate.lock`.
- **Address already in use**: another server is on that port. Use `--port`.
- **Requests answered 403 or 415**: the server only accepts the `127.0.0.1` and `localhost` host names, and JSON POST bodies. This keeps other web pages from driving it. Don't put it behind a proxy or open it to the network.
```

- [ ] **Step 2: Update the repo README**

**Replace** in `README.md`:
```markdown
cad/box.sh png`
```
**with:**
```markdown
cad/box.sh png`
- [Web configurator](web/README.md): a local page that sizes and checks a window as you type, renders its parts on the Windows box and zips everything for that opening (`python3 web/server.py`)
```

**Replace** in `README.md`:
```markdown
   - `tier`: 1–3, picked from [printing](docs/printing.md).
```
**with:**
```markdown
   - `tier`: 1–3, picked from [printing](docs/printing.md);
   - `screen` (optional, default `true`): `false` leaves out the insect screen, its parts and its hardware;
   - `bed` (optional, default `[256, 256, 256]`, a Bambu P1S): your printer's build volume X, Y, Z in mm. Segments are split to at most min(Z, max(X, Y)) − 16 mm.
```

**Replace** in `README.md`:
```markdown
Run the tests with `cd tools && python3 -m unittest discover -p 'test_*.py'` (Python) and `cad/box.sh test` (OpenSCAD asserts).
```
**with:**
```markdown
Run the tests with `cd tools && python3 -m unittest discover -p 'test_*.py'` (Python), `python3 -m unittest discover -s web/tests -p 'test_*.py'` (web configurator) and `cad/box.sh test` (OpenSCAD asserts).
```

**Replace** in `README.md`:
```markdown
- `BOX_HOST=user@host cad/box.sh render my-window` picks the machine. The default is the author's build box.
```
**with:**
```markdown
- `BOX_HOST=user@host cad/box.sh render my-window` picks the machine. The default is the author's build box.
- `cad/box.sh ping` prints `ok` when the box answers over SSH, and exits 255 when it doesn't. The web configurator's box indicator uses it.
```

- [ ] **Step 3: Mark the spec implemented**

**Replace** in `docs/specs/2026-10-10-web-configurator-design.md`:
```markdown
Status: Approved (revised 2026-10-10: local server + Windows-box OpenSCAD, replacing the in-browser WebAssembly design)
```
**with:**
```markdown
Status: Implemented (plan: docs/plans/2026-10-10-web-configurator.md). Revised 2026-10-10: local server + Windows-box OpenSCAD, replacing the in-browser WebAssembly design
```

- [ ] **Step 4: Final checkpoint**

Run the **compatibility check** once more. Expected: `BYTE-IDENTICAL`.

Then run:
```bash
cd ~/diy-window/tools && python3 -m unittest discover -p 'test_*.py' 2>&1 | grep -E '^(Ran|OK|FAILED)'
cd ~/diy-window && python3 -m unittest discover -s web/tests -p 'test_*.py' 2>&1 | grep -E '^(Ran|OK|FAILED)'
cd ~/diy-window && cad/box.sh test
```
Expected: `Ran 165 tests` and `OK`, then `Ran 94 tests` and `OK`, then `7 test files passed`. The last command regenerates `cad/generated/` for the bench window, as it always does.

- [ ] **Step 5: Remove the temporary folders**

Run: `cd ~/diy-window && rm -rf .web-baseline .web-after && ls -a | grep web`
Expected: only `web`.

- [ ] **Step 6: Update this plan's "Execution status"** with the date, the test counts, the live render result and the screenshot review.

---

## Self-review (done while writing; re-check after executing)

**Spec coverage:**

| Spec | Task |
|---|---|
| §2 local stdlib server, in-process generator, `box.sh` rendering, WebGL viewer, no installs | Tasks 9–12 |
| §3 inputs and ranges, bed presets, new params keys | Task 9 `validate`, `PRESETS`, `DEFAULTS`; Tasks 1 and 5 |
| §4.1 `max_seg`, `BED_MARGIN`, every `split()` caller, `bed_fit` (segments: envelope × length; fixed parts: table from the reference STLs), `cam_keeper` unchanged, `check_stl` bed, `box.sh render` unchanged | Tasks 1–4 (`render` untouched; `ping` added in Task 6) |
| §4.2 screen off: parts, `bosses=false`, layout, BOM, guides | Task 5 |
| §4.3 byte-identical output, existing tests unchanged | Task 0 baseline; compatibility checks in Tasks 2, 3, 5, 13 and 15 |
| §5 files `server.py`, `api.py`, `drawing.py`, `zipper.py`, `static/*`, `README.md`, the four test files | Tasks 7–12 and 15 (`render_job` lives in `server.py`'s `Job`; see the decisions table) |
| §6 API: every route, 409 and 400, batches of 6, `check_stl` after each batch, BOM at the end, `?partial=1` | Task 10 |
| §7 debounced preview, SVG dimensions, badges, table, render all or selected, progress, cancel, viewer and assembled view, zip contents | Tasks 7–12 |
| §8 inline field errors, red badge plus explanation, `CHECKS FAILED` README block, unreachable-box message and box indicator, red rows plus log tail, partial zip, 127.0.0.1, name validation, ID checks, argument lists | Tasks 8–12 |
| §9 generator tests, web unit tests, live render, screenshots | Tasks 1–5, 7–12, 13 and 14 |

**Placeholder scan:** every code step shows the complete file or the exact block to replace, and every command shows its expected output. There are no TBDs.

**Names used across tasks:**
- Generator and layout: `window.max_seg`, `window.DEFAULT_BED`, `lay["bed"]`, `lay["max_seg"]` and `lay["has_screen"]` (Tasks 1 and 5), used by `generate.parts`/`bed_fit`/`write` (Tasks 2, 3, 5), `build_bom.hardware` (Task 5) and `web/drawing.py` (Task 7).
- `generate.ENVELOPES` and `generate.bed_fit(lay, plist)` (Task 3), used by `api.checks` (Task 9).
- `check_stl.check(row, stl_dir, bed)` (Task 4), used by `api.check_part` (Task 9).
- `api.validate`, `api.error_field`, `api.save_params`, `api.load`, `api.stl_dir`, `api.check_part`, `api.write_bom`, `api.build_zip`, `api.NotReady`, `api.PRESETS` and `api.DEFAULTS` (Task 9), used by `web/server.py` and `web/fake_box.py` (Task 10).
- JSON field names in `app.js` (`layout.max_seg`, `layout.bed`, `drawing.rects/dims/labels/bounds/step`, `assembly[].id/m`, `job.parts/errors/log_tail/current/elapsed/error`) match `api.preview` and `Job.snapshot`.
