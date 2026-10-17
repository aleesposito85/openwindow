# OpenWindow V-slot 2020 Cores Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Two optional params keys build the window's metal cores from V-slot 2020 extrusion the owner already has:
- `core: "vslot"` selects V-slot;
- `vslot_stock` gives the length of the owner's pieces.

Members are joined from pieces where the frame is fixed to the brick. A member keeps its standard tube only when V-slot can't work.

**Architecture:**
- **Generator.** `tools/window.py`:
  - chooses a core per member, with a reason for every fallback;
  - places joins in the head, sill and lower jambs (inside a segment, a quarter along it, clear of its T-nut);
  - splits each jamb into two tubes;
  - makes the transom and mullions a 2020 pair;
  - packs the pieces into a cut plan;
  - reports all of it in a `core` check.

  `tools/generate.py` passes an optional `core` argument to every part that holds a tube. `bom/build_bom.py` counts each tube screw by the core it goes into.
- **CAD.**
  - **`core` argument:** `cad/profile.scad`, `cad/lib/segment.scad` and the seven tube-holding parts take an optional `core`.
  - **Pocket:** with `core` set, the `sash_rebate` pocket (head and upper jambs) moves 3 mm outward, so the stay screws bite the solid shoulder beside a groove.
  - **Screws:** a V-slot tube screw becomes an M5 countersunk screw into a T-nut, with its head seated so the tip ends 5.4 mm into the slot. The transom's screws move onto the shoulder instead, because its magnet channel sits over the slot.
  - **Asserts:** every rule is an OpenSCAD assert in a new `cad/tests/vslot_test.scad`.
- **Web.** A "Tube cores" fieldset, a `core` badge, and the core summary under the field.
- **Compatibility.** With no `core` key, every output is byte-identical, apart from the new `VSLOT_*` lines in the `dims.scad` mirror. That includes the STLs: Task 2 re-renders them to prove it.

**Tech Stack:**
- Python 3 standard library only (`unittest`, `json`, `math`), using the Mac's `python3`.
- OpenSCAD on the Windows box through `cad/box.sh` (nightly 2026.10.02, manifold backend).
- Plain HTML/CSS/ES-module JavaScript.
- The Mac's Google Chrome, headless, for screenshots and the guide PDF.

**Spec:** `docs/specs/2026-10-10-vslot-core-design.md`. Background:
- `docs/specs/2026-10-07-diy-window-design.md` (§12 amendments win);
- `docs/specs/2026-10-10-mullion-bays-design.md`;
- `docs/specs/2026-10-10-web-configurator-design.md`.

The V-slot geometry comes from the OpenBuilds drawing "V-Slot 20X20 Linear Rail":
- mouth 9.16 mm, 90° V down to 6.25 mm at 1.80 mm (the lip);
- cavity 11 mm;
- floor 6.1 mm;
- webs 1.50 mm, bore 4.20 mm.

## Global Constraints

- Profile: V-slot 2020, 4-slot (OpenBuilds-style). `vslot2020`: I = 6890 mm⁴, E = 69000 MPa, 0.456 kg/m. `vslot2020x2`: I = 13780 mm⁴ (two separate bars, no composite action), 0.912 kg/m.
- `core` is optional and must be `"vslot"`. `vslot_stock` is optional, only with `core`, 300–6000 mm, default 1000.
- Joins only in head, sill and lower jambs; never in transom, mullions, sash or upper jambs.
- Fallback per member: `alu20` (frame, sash) or `steel40x20` (transom, mullions), with the reason in the `core` check and the BOM.
- No `core` key: generator, BOM and CSV outputs byte-identical for every reference window; part calls unchanged; STLs byte-identical; existing tests pass unchanged. The one exception is the `VSLOT_*` lines added to `cad/generated/dims.scad`.
- Stay screws (8g) land 5.6–8.5 mm off a V-slot face centre (`VSLOT_SHOULDER`). M5 tips land 5.0–5.8 mm into the slot (`VSLOT_TIP`), target 5.4.

## Review Focus

These are failure modes the spec implies, each pinned by a test or a check:

1. **Page sends a stray stock.** Switching "Tube core" back to Standard after typing a piece length must send neither key. `readForm` only sends `vslot_stock` with `core`. If it ever leaked, the server would show "only with core vslot" under the field (`testStockNeedsTheCore`, Task 6). The by-eye step in Task 6 checks the round trip.
2. **Segments too short to join.** A V-slot window whose segments are too short to join (a small bed) must keep the standard tube with a reason, not fail or place a join under a nut (`testShortSegmentsKeepTheStandardTube`, Task 1).
3. **Tall bays.** A tall window with bays must give a steel lower mullion when the pair is too flexible, and the mullion check must report the steel figure (`testTallLowerMullionFallsBackToSteel`, Task 1).
4. **Stock equal to a tube.** A piece exactly as long as a tube must be enough, and 1 mm shorter must not (`testStockEqualToATubeIsEnough`, Task 1).
5. **Mixed sash corner.** A sash corner whose two legs have different cores (V-slot sides, plain top and bottom) must render closed (`CS` in the `zz-vhome` render, Task 4) and pass its call test (`testHomeFallbacksKeepTheirCalls`, Task 3).

## Execution status

**Done (2026-10-11), via subagents.** Reviews made the code and docs go beyond this plan's blocks, so `tools/`, `bom/`, `cad/`, `web/`, `docs/` and `pdf/` are authoritative over them. The changes:
- **Lower jamb:** a lower jamb's own segment T-nuts now count as holding points, so a lower jamb needing three or more pieces no longer falls back to the standard tube.
- **Join tests:** strengthened, with a nut-zone `join_plan` test and position checks.
- **Page:** `#vslot.hidden` gets a CSS rule.
- **Web tests:** the `test_api.py` main block moved below the new class.
- **Install guide:** V-slot screws at install steps 6.2 and 6.8.
- **Test gate:** rows 1–6 and 10–12 on a separate `bench-600-vslot` window, and row 11 adds the mullion stay case.
- **T-nuts:** hung with an offcut carrier (spec §13 item 13).
- **Guide PDF:** a V-slot slide and pointers in the deck.

Final checks:
- tools `Ran 346 tests`, OK;
- web `Ran 165 tests`, OK;
- `cad/box.sh test` reports `10 test files passed`;
- the compatibility check prints `BYTE-IDENTICAL`;
- default STLs are byte-identical;
- V-slot renders are 37/37, 12/12 and 11/11 parts ok;
- the guide PDF is 77 pages with `overflow: none`.

The expected numbers below are the plan as written.

Before execution, every task below was run once, in order, on a scratch copy of the repo while the plan was written:
- stdlib Python;
- the real Windows box through the copy's `cad/box.sh`;
- the Mac's Chrome.

The run applied every Create and Replace block of this plan literally, with a small script.

**Results:**
- **Python:** 344 tests pass in `tools/` (309 before), and 165 pass in `web/tests` (157 before).
- **OpenSCAD:** `cad/box.sh test` reports `10 test files passed` (9 before).
- **Compatibility:** the check prints `BYTE-IDENTICAL`. The re-rendered default bench STLs (37) and the 2-bay mullion parts (8) match today's byte for byte.
- **V-slot renders:** `zz-vbench` 37/37, `zz-vhome` 12/12 and `zz-v2bay` 11/11 parts ok.
- **Section views:** the four section views and the UI screenshot `11-vslot.png` were checked by eye.
- **Guide PDF:** 76 pages, `overflow: none`.

The numbers quoted in the expected outputs come from that run. Not run while planning: the physical bench rows 10–12.

## Decisions and spec gaps (found while planning)

| Spec says, or leaves open | Plan does | Why |
|---|---|---|
| §5.3: sash tube centre 29, stay offset 6–6.5 | Sash tube centre 27, offset 8–8.5, at the existing "screw centre 1.5 mm inside the tube edge" rule | The sash profile is drawn in frame coordinates (`SASH_Y0` = 2), so its tube is at y 17–37. The spec read the 17–37 as sash-face distances |
| §4: shoulder window 5.6–7.4 | **5.6–8.5** (`VSLOT_SHOULDER`) | The outer bound is the existing tube-edge rule. From 8.2 mm out, the V-slot corner is solid to about 5.6 mm deep, so the screw bites as well as on the plain tube today |
| §5.3: upper-jamb pocket moves 2.5 mm, to centre 29 | Moves **3.0 mm** (`VSLOT_SHIFT`): pocket y 18.2–38.8, tube centre 28.5 | Stay screws then sit 6.5–7 mm off centre, in the middle of the window. At 2.5 mm they sat 0.4 mm from its inner bound. The fixing hole clearance grows to 6.7 mm |
| §5.1: tip "5.6–5.9 mm into the slot" | Tip 5.0–5.8 (target 5.4) below the tube face, with the tube pulled tight against the pocket wall | Tightening pulls the tube up by the 0.3 mm clearance. The nut body (about 2.5 mm under a 1.8 mm neck) must hang below the lip while the tube slides in, and must still be fully threaded after tightening. 5.4 leaves 0.7 mm to the 6.1 mm floor |
| §5.1: pick the longest standard M5 needing seat ≥ 0 | Longest standard length ≤ shell + 5.4. The seat is sunk by the remainder: glazing/sill 25 mm (seat 1.6), sash_rebate 25 (4.6), sash 20 (0.1), mullion 16 (0.6) | The same rule in Python (`window.m5_length`) and in OpenSCAD (`vslot_screw_l`). A test on each side pins the four lengths |
| Not covered | The solid boss round an M5 screw is 14 mm (10 mm for 8g) | At 13 mm the boss was tangent to the sash corner block's end cap, which gave a non-manifold edge in `CS` |
| Not covered | The chamber beside the `sash_rebate` pocket is capped at the pocket top (`min(KEY_Y - w, o[1] + p[1])`) | With the pocket moved, the uncapped chamber left 0.8 mm to the chamber above it, and a non-manifold edge in `CH`. Default geometry is unchanged: 40.5 is below 41.8 |
| §2: transom screws "self-tappers into the shoulder" | 8g × 20 stainless self-tappers in 3.5 mm pilots at x = 41.25 (`VSLOT_TRANSOM_X`), counted in a new BOM line | The shell above the pocket is 11.2 mm. 20 mm reaches through the 4.5 mm solid shoulder |
| §8: V-slot mullion stays | Stay tracks on a V-slot upper mullion take 8g × 16 self-tappers in 3.5 mm pilots (BOM line text changes) | The room-side 2020's centre is 41.5, so the stay screws land 6–6.5 mm off it, on the shoulder |
| §9: byte-identical outputs | `dims.json` gains 11 `VSLOT_*` keys, which `cad/generated/dims.scad` mirrors. The compatibility check allows exactly those added lines | OpenSCAD and Python both need the values. A missing variable is a `WARNING`, which `box.sh` treats as a failure |
| §6: upper jamb fallback "alu20 in the shifted pocket" | The CAD `core` value `"alu20"` means "standard tube in a V-slot window". Only `sash_rebate` reacts to it (it moves the pocket). The generator emits it only for `sash_rebate` members | One argument carries both facts, the window layout and the tube in this member |
| §5.4: jamb in two pieces | In V-slot mode the jamb is always two tubes, even if the lower one falls back to `alu20` | The two pockets differ by 3 mm, so no single tube can run through both |
| §5.5: greedy placement | The longest first piece, then the rest. Each piece must hold a T-nut or a corner/node screw. Pieces are packed first-fit decreasing with 2 mm per saw cut | This gives the fewest joins. The packing is simple and good enough for the stock count |
| §6: fallback note examples | A transom or mullion fallback gives both reasons when both apply ("…is longer than the 1000 mm V-slot pieces, and a V-slot pair would deflect 48.2 mm") | The owner can see that longer stock won't help |
| §7: `core` check | Only in V-slot mode | So the default check list stays unchanged (`testChecksEndWithBedFit` and the CLI output) |
| §6: sash weight | Adds (0.456 − 0.32) kg/m × 2 × length for each V-slot sash member | The stay check uses the result |
| Not covered | `keeper_dz_min` uses the M5 head (Ø10) when the sash horizontals are V-slot: 21.3 mm, not 20.6 | The SBE keeper bosses sit beside the sash screw. The bench window's 23.0 mm still passes |
| §8: "Mass: core masses per member" | No BOM mass line. The V-slot mass goes into the sash weight, so the stay check uses it | The BOM lists tube lengths, not metal mass, today. The only place the mass matters is the friction-stay rating |
| §8: the test log gets three rows | The deck's bench-test slides become three slides of 4 rows | With 12 rows, slide 2 of 2 overflowed |

## Ground rules for whoever executes this

- **No git.** The user's rule: no git under `~` except one work repo. Every "commit" in the usual TDD loop is a **Checkpoint** step here. Run the listed checks, and stop for review if any of them fails.
- **No installs on the Mac,** and nothing gets downloaded.
- **Network.** Every ssh/scp to the Windows box goes through `cad/box.sh`, which binds en0.
- **One render at a time.** `cad/box.sh render` ends with `check_stl.py`, which reads `cad/generated/`. A second render or `generate.py` run in the meantime leaves it reading the wrong window, and it prints "generated output is for …".
- **No explanatory comments in code** beyond a one-line header. The reasons live in this plan.
- **Test method names** are camelCase `testXxx`, with no underscores.
- **Existing tests stay unchanged.** New test classes are only appended.
- **Working folder.** Run every command from `~/diy-window`, unless a step says otherwise.
  - Task 0 creates `.vslot-baseline/`.
  - The checkpoints create `.vslot-after/`.
  - Task 4 creates `.vslot-review/`.
  - Task 8 deletes all three.

## File structure

| File | Change |
|---|---|
| `cad/dims.json` | + 11 `VSLOT_*` keys |
| `tools/window.py` | Cores, `vslot_stock`, `pocket_top`, `m5_length`, `join_plan`, `cut_plan`, `vslot_cores`. The checks take the chosen cores, plus the `core` check |
| `tools/generate.py` | `core_arg` and the `core` / `core_a` / `core_b` arguments in the part calls |
| `bom/build_bom.py` | `SCREW_HOSTS`, `screw_kind`, `tube_screws`; M5, T-nut and shoulder screw lines; V-slot pieces line; cut plan, joins and fallbacks in the `.md` |
| `cad/profile.scad` | `pocket_shift`; `core` on the pocket, chamber, profile and cord functions; chamber cap |
| `cad/lib/segment.scad` | `core` on `screw_x`, `boss_dz_min`, `tube_screw`, `screw_column` and `segment`; `tnut`, `csk_d`, `column_d`, `vslot_shell`, `vslot_screw_l`, `vslot_seat` |
| `cad/parts/{frame_segment,corner_block,jamb_node,transom_shoe,frame_node,cross_node,mullion_shoe}.scad` | Optional `core` (`core_a`/`core_b` on corner blocks), passed through |
| `cad/tests/vslot_test.scad` | New: the V-slot asserts |
| `cad/tests/vslot_sheet.scad` | New: section views for review by eye (not a `_test`) |
| `web/api.py`, `web/static/index.html`, `web/static/app.js` | `core`, `vslot_stock`, the Tube cores fieldset, the badge and the note |
| `web/tests/ui_shots.py` | + one V-slot screenshot |
| `tools/test_window.py`, `tools/test_generate.py`, `tools/test_bom.py`, `web/tests/test_api.py` | New test classes, appended |
| `docs/…`, `README.md`, `web/README.md`, `pdf/build_deck.py` | Section 8 of the build guide; install, test-log and manual notes; params docs; both specs; three bench-test slides |

---

### Task 0: Baseline of today's outputs

The compatibility rule: with no `core` key, every file that `generate.py` and `build_bom.py` write, and everything they print, stays byte-identical. The only exception is the `VSLOT_*` lines in `dims.scad`. The STLs stay byte-identical too (Task 2). This task records today's outputs once.

**Files:**
- Create: `.vslot-baseline/` (temporary, deleted in Task 8)

- [ ] **Step 1: Confirm the starting point**

Run:
```bash
cd ~/diy-window/tools && python3 -m unittest discover -p 'test_*.py' 2>&1 | grep -E '^(Ran|OK|FAILED)'
cd ~/diy-window && python3 -m unittest discover -s web/tests -p 'test_*.py' 2>&1 | grep -E '^(Ran|OK|FAILED)'
cd ~/diy-window && cad/box.sh test
```
Expected: `Ran 309 tests`, `OK`; then `Ran 157 tests` (about 50 s), `OK`; then `9 test files passed`.

- [ ] **Step 2: Record the baseline**

Run:
```bash
cd ~/diy-window && rm -rf .vslot-baseline && mkdir .vslot-baseline
for n in bench-600 home-1800x1500 home-1800x1500-2bay; do
  python3 tools/generate.py params/$n.json > .vslot-baseline/$n.stdout
  python3 bom/build_bom.py $n >> .vslot-baseline/$n.stdout
  mkdir .vslot-baseline/$n && cp -R cad/generated .vslot-baseline/$n/
  for f in $n.csv $n.md $n-cutlist.csv $n-glass.csv $n-parts.csv; do cp bom/$f .vslot-baseline/$n/; done
done
cp -R cad/stl/bench-600 .vslot-baseline/stl-bench-600
cp -R cad/stl/home-1800x1500-2bay .vslot-baseline/stl-2bay
ls .vslot-baseline
```
Expected: `bench-600  bench-600.stdout  home-1800x1500  home-1800x1500-2bay  home-1800x1500-2bay.stdout  home-1800x1500.stdout  stl-2bay  stl-bench-600`

The **compatibility check** used by later checkpoints re-runs the same commands into `.vslot-after/` and compares:
```bash
cd ~/diy-window && rm -rf .vslot-after && mkdir .vslot-after
for n in bench-600 home-1800x1500 home-1800x1500-2bay; do
  python3 tools/generate.py params/$n.json > .vslot-after/$n.stdout
  python3 bom/build_bom.py $n >> .vslot-after/$n.stdout
  mkdir .vslot-after/$n && cp -R cad/generated .vslot-after/$n/
  for f in $n.csv $n.md $n-cutlist.csv $n-glass.csv $n-parts.csv; do cp bom/$f .vslot-after/$n/; done
done
ok=1
diff -r -x dims.scad -x 'stl-*' .vslot-baseline .vslot-after || ok=0
for n in bench-600 home-1800x1500 home-1800x1500-2bay; do
  extra=$(diff .vslot-baseline/$n/generated/dims.scad .vslot-after/$n/generated/dims.scad | grep '^[<>]' | grep -v -E '^> VSLOT_[A-Z0-9_]+ = ')
  [ -n "$extra" ] && { echo "$extra"; ok=0; }
done
[ $ok = 1 ] && echo BYTE-IDENTICAL || echo DIFFERENT
```
Expected, now and after every later task: `BYTE-IDENTICAL`, with no other output.

---

### Task 1: Cores, joins and the cut plan (`cad/dims.json`, `tools/window.py`)

**Files:**
- Modify: `cad/dims.json`, `tools/window.py`
- Test: `tools/test_window.py` (append)

**Interfaces:**
- Produces:
  - **Constants:** `window.VSLOT = "vslot2020"`, `window.VSLOT_PAIR = "vslot2020x2"`, `window.CORES[...]` entries for both, and `window.SECTION_I`.
  - **Join and cut constants:** `window.SAW_KERF = 2.0`, `window.JOIN_END = JOIN_NUT = 15.0`, `window.VSLOT_STOCK_RANGE = (300, 6000)`.
  - **Functions:**
    - `window.vslot_stock(p) -> float | None`;
    - `window.pocket_top(profile, shifted=False) -> float`;
    - `window.m5_length(profile) -> int`;
    - `window.join_plan(total, segments, held, stock) -> list[float] | None`, where segments are `(s0, s1, centre, nut_zone)`;
    - `window.cut_plan(cuts, stock) -> [{"cuts": [(label, mm)], "offcut": mm}]`;
    - `window.keeper_dz_min(csk=None)`.
  - **Layout result:** `layout()` returns `"vslot": None | {"stock", "joins": {member: [{"at", "segment"}]}, "fallbacks": [str], "plan": [...]}`.
  - **Members and tubes:** each member's `"core"` is the chosen core. In V-slot mode the tubes are per piece: `"head 1/2"`, `"jamb_lower"`, `"jamb_upper"`, and a transom pair with `"qty": 2`.
  - **Checks:** a `"core"` check (ok always) is appended in V-slot mode only.

- [ ] **Step 1: Write the failing tests**

**Replace** blocks, applied in order (they append the new classes before `if __name__ == "__main__":`):

**Replace** in `tools/test_window.py`:
```python


if __name__ == "__main__":
    unittest.main()
```
**with:**
```python


def vslot(name, **changes):
    return window.layout({**load(f"{name}.json"), "core": "vslot", **changes})


class VslotInputTest(unittest.TestCase):
    def testDefaultHasNoVslot(self):
        lay = window.layout(load("home-1800x1500.json"))
        self.assertIsNone(lay["vslot"])
        self.assertNotIn("core", [c["name"] for c in lay["checks"]])

    def testCoreMustBeVslot(self):
        for value in ("tube", "", None, 2020):
            with self.assertRaisesRegex(ValueError, "^core must be vslot"):
                window.layout({**load("bench-600.json"), "core": value})

    def testStockNeedsTheCore(self):
        with self.assertRaisesRegex(ValueError, "^vslot_stock only applies with core vslot"):
            window.layout({**load("bench-600.json"), "vslot_stock": 1000})

    def testStockRange(self):
        for value in (299, 6001, True, "1000", None, float("inf")):
            with self.assertRaisesRegex(ValueError, "^vslot_stock must be a number from 300 to 6000 mm"):
                vslot("bench-600", vslot_stock=value)

    def testStockLimitsAreAccepted(self):
        for value in (300, 6000):
            self.assertEqual(vslot("bench-600", vslot_stock=value)["vslot"]["stock"], value)


class VslotCoresTest(unittest.TestCase):
    def cores(self, lay):
        return {m["name"]: m["core"] for m in lay["members"]}

    def testBenchIsAllVslot(self):
        lay = vslot("bench-600")
        self.assertEqual({k: v for k, v in self.cores(lay).items() if not k.startswith("screen")},
                         {"head": "vslot2020", "sill": "vslot2020", "jamb_lower": "vslot2020", "jamb_upper": "vslot2020",
                          "transom": "vslot2020x2", "sash_horizontal": "vslot2020", "sash_vertical": "vslot2020"})
        self.assertEqual(lay["vslot"]["fallbacks"], [])
        self.assertEqual(checks_by_name(lay)["core"]["msg"], "V-slot 2020: 5 pieces of 1000 mm")

    def testHomeFallsBackWithReasons(self):
        lay = vslot("home-1800x1500")
        cores = self.cores(lay)
        self.assertEqual((cores["transom"], cores["sash_horizontal"], cores["sash_vertical"]), ("steel40x20", "alu20", "vslot2020"))
        self.assertEqual(checks_by_name(lay)["core"]["msg"],
                         "V-slot 2020: 8 pieces of 1000 mm; joins: head 1, sill 1; steel transom: 1696 mm is longer than "
                         "the 1000 mm V-slot pieces, and a V-slot pair would deflect 48.2 mm (limit 9.5 mm); alu20 "
                         "sash_horizontal: 1615 mm is longer than the 1000 mm V-slot pieces")
        self.assertTrue(checks_by_name(lay)["core"]["ok"])

    def testLongerStockOnlyLeavesTheTransom(self):
        lay = vslot("home-1800x1500", vslot_stock=2000)
        self.assertEqual(lay["vslot"]["fallbacks"], ["steel transom: a V-slot pair would deflect 48.2 mm (limit 9.5 mm)"])
        self.assertEqual(lay["vslot"]["joins"], {"head": [], "sill": [], "jamb_lower": []})

    def testHomeTubes(self):
        tubes = [(t["member"], t["core"], t["length"], t["qty"]) for t in vslot("home-1800x1500")["tubes"]]
        self.assertEqual(tubes[:6], [("head 1/2", "vslot2020", 919.8, 1), ("head 2/2", "vslot2020", 801.2, 1),
                                     ("sill 1/2", "vslot2020", 919.8, 1), ("sill 2/2", "vslot2020", 801.2, 1),
                                     ("jamb_lower", "vslot2020", 943.0, 2), ("jamb_upper", "vslot2020", 475.0, 2)])
        self.assertEqual(vslot("home-1800x1500")["vslot"]["joins"]["head"], [{"at": 919.8, "segment": 4}])

    def testJambPiecesAddUpToTheStandardJamb(self):
        plain = next(t for t in window.layout(load("home-1800x1500.json"))["tubes"] if t["member"] == "jamb")
        pieces = {t["member"]: t for t in vslot("home-1800x1500")["tubes"]}
        clear = window.D["TUBE_END_CLEAR"]
        self.assertAlmostEqual(pieces["jamb_lower"]["length"] + pieces["jamb_upper"]["length"] + 2 * clear, plain["length"], places=6)

    def testStockEqualToATubeIsEnough(self):
        self.assertEqual(self.cores(vslot("bench-600", vslot_stock=496))["transom"], "vslot2020x2")
        self.assertEqual(self.cores(vslot("bench-600", vslot_stock=495))["transom"], "steel40x20")

    def testTransomPairIsTwoBars(self):
        t = next(x for x in vslot("bench-600")["tubes"] if x["member"] == "transom")
        self.assertEqual((t["core"], t["length"], t["qty"]), ("vslot2020", 496.0, 2))
        self.assertEqual(window.inertia("vslot2020x2"), 2 * window.inertia("vslot2020"))

    def testTwoBayMullionsArePairs(self):
        lay = two_bay(core="vslot")
        cores = self.cores(lay)
        self.assertEqual((cores["mullion_lower"], cores["mullion_upper"], cores["transom"]), ("vslot2020x2", "vslot2020x2", "steel40x20"))
        self.assertEqual(checks_by_name(lay)["mullion_deflection"]["msg"],
                         "lower mullion deflects 4.3 mm at 0.7 kPa over 848 mm, limit span/175 = 4.8 mm")

    def testTallLowerMullionFallsBackToSteel(self):
        lay = two_bay(core="vslot", opening_h=1800, vslot_stock=3000)
        cores = self.cores(lay)
        self.assertEqual((cores["mullion_lower"], cores["mullion_upper"]), ("steel40x20", "vslot2020x2"))
        self.assertEqual(lay["vslot"]["fallbacks"], ["steel transom: a V-slot pair would deflect 65.1 mm (limit 9.5 mm)",
                                                     "steel lower mullion: a V-slot pair would deflect 14.5 mm over 1148 mm (limit 6.6 mm)"])
        self.assertEqual(checks_by_name(lay)["mullion_deflection"]["msg"],
                         "lower mullion deflects 1.9 mm at 0.7 kPa over 1148 mm, limit span/175 = 6.6 mm")

    def testSashWeightCountsTheVslotMass(self):
        lay = vslot("bench-600")
        sw, sh = lay["sash"]
        gw, gh = lay["glass"]["sash"]
        extra = window.CORES["vslot2020"][4] - window.CORES["alu20"][4]
        expected = gw * gh / 1e6 * window.GLAZING_KG_M2["acrylic"] + 2 * (sw + sh) / 1000 * window.SASH_FRAME_KG_M
        self.assertEqual(lay["sash_kg"], round(expected + 2 * (sw + sh) / 1000 * extra, 1))

    def testKeeperMinimumUsesTheM5Head(self):
        self.assertIn("allowed 21.3-73.0 mm", checks_by_name(vslot("bench-600"))["cam_keeper"]["msg"])
        self.assertIn("allowed 20.6-73.0 mm", checks_by_name(window.layout(load("bench-600.json")))["cam_keeper"]["msg"])

    def testM5Lengths(self):
        names = ["glazing", "sill", "sash_rebate", "sash", "mullion_glazing", "mullion_sash"]
        self.assertEqual([window.m5_length(n) for n in names], [25, 25, 25, 20, 16, 16])


class VslotJoinTest(unittest.TestCase):
    def testJoinsSitInsideSegmentsClearOfTheirNuts(self):
        for lay in (vslot("home-1800x1500"), vslot("bench-600", vslot_stock=300), two_bay(core="vslot")):
            members = {m["name"]: m for m in lay["members"]}
            for name, joins in lay["vslot"]["joins"].items():
                seg = members[name]["seg"]
                for j in joins:
                    self.assertGreaterEqual(seg / 4, window.JOIN_END, (name, j))
                    self.assertGreaterEqual(seg / 4 - (window.D["FIX_DZ"] if name == "head" else 0) / 2, window.JOIN_NUT, (name, j))
            for t in lay["tubes"]:
                if t["core"] == "vslot2020":
                    self.assertLessEqual(t["length"], lay["vslot"]["stock"], t)

    def testShortStockJoinsMoreThanOnce(self):
        lay = vslot("bench-600", vslot_stock=300)
        self.assertEqual([j["at"] for j in lay["vslot"]["joins"]["head"]], [201.9, 435.4])
        self.assertEqual([t["length"] for t in lay["tubes"] if t["member"].startswith("head")], [201.9, 233.5, 85.6])

    def testShortSegmentsKeepTheStandardTube(self):
        lay = vslot("bench-600", vslot_stock=300, bed=[80, 80, 80])
        self.assertEqual({m["name"]: m["core"] for m in lay["members"]}["head"], "alu20")
        self.assertEqual(lay["vslot"]["fallbacks"][:2], ["alu20 head: 300 mm V-slot pieces can't be joined inside its 57.38 mm segments",
                                                         "alu20 sill: 300 mm V-slot pieces can't be joined inside its 57.38 mm segments"])
        self.assertEqual([t["core"] for t in lay["tubes"] if t["member"] == "head"], ["alu20"])

    def testJoinPlanNeedsACandidate(self):
        self.assertIsNone(window.join_plan(500.0, [(10.0, 60.0, 35.0, 0.0)], [5.0, 495.0], 300))

    def testJoinPlanKeepsANutInEveryPiece(self):
        segs = [(10.0 + 100 * k, 105.0 + 100 * k, 57.5 + 100 * k, 0.0) for k in range(5)]
        joins = window.join_plan(510.0, segs, [5.0, 505.0], 300)
        self.assertEqual(joins, [281.25])
        self.assertIsNone(window.join_plan(510.0, segs, [5.0, 505.0], 120))

    def testCutPlanPacksFirstFitDecreasing(self):
        plan = window.cut_plan([("a", 600.0), ("b", 500.0), ("c", 398.0)], 1000)
        self.assertEqual(plan, [{"cuts": [("a", 600.0), ("c", 398.0)], "offcut": 0.0}, {"cuts": [("b", 500.0)], "offcut": 500.0}])


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the tests to see them fail**

Run: `cd ~/diy-window/tools && python3 -m unittest test_window 2>&1 | grep -E '^(Ran|OK|FAILED)'`
Expected: `Ran 147 tests`, `FAILED (failures=11, errors=12)`. The errors are `AttributeError: module 'window' has no attribute 'cut_plan'` and its kin, plus `ValueError not raised`.

- [ ] **Step 3: Add the V-slot dimensions**

**Replace** in `cad/dims.json`:
```json
  "MULLION_W": 70.0,
  "MULLION_HALF_BODY": 17.0,
  "MULLION_DOVE_D": 4.0
}
```
**with:**
```json
  "MULLION_W": 70.0,
  "MULLION_HALF_BODY": 17.0,
  "MULLION_DOVE_D": 4.0,
  "VSLOT_SHIFT": 3.0,
  "VSLOT_MOUTH": 9.16,
  "VSLOT_NECK": 6.25,
  "VSLOT_LIP": 1.8,
  "VSLOT_FLOOR": 6.1,
  "VSLOT_SHOULDER": [5.6, 8.5],
  "VSLOT_TIP": [5.0, 5.8],
  "VSLOT_SCREW_D": 5.5,
  "VSLOT_CSK_D": 10.0,
  "VSLOT_M5_L": [10, 12, 16, 20, 25, 30, 35, 40],
  "VSLOT_TRANSOM_X": 41.25
}
```

- [ ] **Step 4: Add cores, joins, the cut plan and the checks to `tools/window.py`**

Apply these blocks in order:

**Replace** in `tools/window.py`:
```python
    "alu50x25": (69000, 25, 50, 1.6, 0.62),
    "steel50x25": (200000, 25, 50, 1.6, 1.80),
}
FRAME_CORE = "alu20"
TRANSOM_CORE = "steel40x20"
```
**with:**
```python
    "alu50x25": (69000, 25, 50, 1.6, 0.62),
    "steel50x25": (200000, 25, 50, 1.6, 1.80),
    "vslot2020": (69000, 20, 20, None, 0.456),
    "vslot2020x2": (69000, 20, 40, None, 0.912),
}
VSLOT = "vslot2020"
VSLOT_PAIR = "vslot2020x2"
SECTION_I = {VSLOT: 6890.0, VSLOT_PAIR: 13780.0}
VSLOT_STOCK = 1000
VSLOT_STOCK_RANGE = (300, 6000)
SAW_KERF = 2.0
JOIN_END = 15.0
JOIN_NUT = 15.0
FRAME_CORE = "alu20"
TRANSOM_CORE = "steel40x20"
```

**Replace** in `tools/window.py`:
```python


def keeper_dz_min():
    return D["BOSS_PITCH"] / 2 + D["CSK_D"] / 2 + D["INSERT_M4_D"] / 2 + D["MIN_SKIN"]


```
**with:**
```python


def keeper_dz_min(csk=None):
    return D["BOSS_PITCH"] / 2 + (D["CSK_D"] if csk is None else csk) / 2 + D["INSERT_M4_D"] / 2 + D["MIN_SKIN"]


```

**Replace** in `tools/window.py`:
```python

def inertia(core):
    _, b, d, t, _ = CORES[core]
    return (b * d ** 3 - (b - 2 * t) * (d - 2 * t) ** 3) / 12.0
```
**with:**
```python

def inertia(core):
    if core in SECTION_I:
        return SECTION_I[core]
    _, b, d, t, _ = CORES[core]
    return (b * d ** 3 - (b - 2 * t) * (d - 2 * t) ** 3) / 12.0
```

**Replace** in `tools/window.py`:
```python


def acrylic_sandwich(p):
    keys = [k for k in ("acrylic_t", "acrylic_gap") if k in p]
```
**with:**
```python


def vslot_stock(p):
    if "core" not in p:
        if "vslot_stock" in p:
            raise ValueError("vslot_stock only applies with core vslot")
        return None
    if p["core"] != "vslot":
        raise ValueError(f"core must be vslot, got {p['core']!r}")
    stock = p.get("vslot_stock", VSLOT_STOCK)
    lo, hi = VSLOT_STOCK_RANGE
    if not (is_size(stock) and lo <= stock <= hi):
        raise ValueError(f"vslot_stock must be a number from {lo} to {hi} mm, got {stock!r}")
    return stock


def pocket_top(profile, shifted=False):
    clear = D["TUBE_CLEAR"]
    if profile == "sash":
        return (D["SASH_Y0"] + D["LIP_Y1"]) / 2 + D["TUBE_SASH"][1] / 2 + clear
    if profile in ("transom", "mullion_glazing", "mullion_sash"):
        return D["DEPTH"] / 2 + D["TUBE_TRANSOM"][1] / 2 + clear
    shift = D["VSLOT_SHIFT"] if shifted and profile == "sash_rebate" else 0
    return (D["DEPTH"] + D["TUBE_FRAME"][1]) / 2 + clear - shift


def m5_length(profile):
    face = D["LIP_Y1"] if profile == "sash" else D["DEPTH"]
    reach = face - pocket_top(profile, shifted=True) + sum(D["VSLOT_TIP"]) / 2
    return max(n for n in D["VSLOT_M5_L"] if n <= reach + 1e-9)


def join_plan(total, segments, held, stock):
    cands = sorted(q for s0, s1, c, nut in segments for q in (c - (s1 - s0) / 4, c + (s1 - s0) / 4)
                   if min(q - s0, s1 - q) >= JOIN_END and abs(q - c) - nut / 2 >= JOIN_NUT)
    joins, start = [], 0.0
    while total - start > stock + 1e-9:
        ok = [q for q in cands if start < q <= start + stock + 1e-9 and any(start < h < q for h in held)]
        if not ok:
            return None
        start = max(ok)
        joins.append(start)
    return joins


def cut_plan(cuts, stock):
    bins = []
    for label, length in sorted(cuts, key=lambda c: -c[1]):
        for b in bins:
            if b["used"] + SAW_KERF + length <= stock + 1e-9:
                b["cuts"].append((label, length))
                b["used"] += SAW_KERF + length
                break
        else:
            bins.append({"cuts": [(label, length)], "used": length})
    return [{"cuts": b["cuts"], "offcut": round(stock - b["used"], 1)} for b in bins]


def acrylic_sandwich(p):
    keys = [k for k in ("acrylic_t", "acrylic_gap") if k in p]
```

**Replace** in `tools/window.py`:
```python


def layout(p):
    if p["glazing"] not in GLAZING_KG_M2:
```
**with:**
```python


def vslot_cores(stock, members, tubes, transom_delta, limit, lower, a, pitch, run, bays, sock, clear):
    F, T, MW, gap = D["FRAME_W"], D["TRANSOM_W"], D["MULLION_W"], D["JOINT_GAP"]
    m = {x["name"]: x for x in members}
    t = {x["member"]: x for x in tubes}
    fallbacks, joins, out = [], {}, []

    def longer(core, label, length):
        return f"{core} {label}: {length:g} mm is longer than the {stock:g} mm V-slot pieces"

    def runs(name, n_runs, nut):
        mem = m[name]
        segs, held = [], [sock / 2]
        for b in range(n_runs):
            x0 = sock + b * (run + MW)
            for k in range(mem["n"]):
                s0 = x0 + gap + k * (mem["seg"] + gap)
                segs.append((s0, s0 + mem["seg"], s0 + mem["seg"] / 2, nut))
                held.append(s0 + mem["seg"] / 2)
            if b < n_runs - 1:
                held.append(x0 + run + MW / 2)
        return segs, held

    def joined(name, label, total, segs, held, qty):
        js = join_plan(total, segs, held, stock)
        if js is None:
            m[name]["core"] = "alu20"
            fallbacks.append(f"alu20 {label}: {stock:g} mm V-slot pieces can't be joined inside its {m[name]['seg']:g} mm segments")
            out.append({"member": label, "core": "alu20", "length": total, "qty": qty})
            return
        m[name]["core"] = VSLOT
        joins[label] = [{"at": round(j, 1), "segment": next(i + 1 for i, s in enumerate(segs) if s[0] < j < s[1])}
                        for j in js]
        ends = [0.0] + js + [total]
        k = len(ends) - 1
        for i in range(k):
            out.append({"member": label if k == 1 else f"{label} {i + 1}/{k}", "core": VSLOT,
                        "length": ends[i + 1] - ends[i], "qty": qty})

    def single(name, label, length, qty, fallback):
        if length <= stock:
            m[name]["core"] = VSLOT
            out.append({"member": label, "core": VSLOT, "length": length, "qty": qty})
        else:
            m[name]["core"] = fallback
            fallbacks.append(longer(fallback, label, length))
            out.append({"member": label, "core": fallback, "length": length, "qty": qty})

    horiz_total = t["head"]["length"]
    for name in ("head", "sill"):
        segs, held = runs(name, bays, D["FIX_DZ"] if name == "head" else 0.0)
        joined(name, name, horiz_total, segs, held + [horiz_total - sock / 2], 1)
    lower_total = lower + T + sock - clear
    segs, _ = runs("jamb_lower", 1, 0.0)
    joined("jamb_lower", "jamb_lower", lower_total, segs, [sock / 2, lower + T / 2 + sock], 2)
    single("jamb_upper", "jamb_upper", a + sock - clear, 2, "alu20")

    tl = t["transom"]["length"]
    pair_delta = transom_delta(VSLOT_PAIR)
    if tl <= stock and pair_delta <= limit:
        m["transom"]["core"] = VSLOT_PAIR
        out.append({"member": "transom", "core": VSLOT, "length": tl, "qty": 2})
    else:
        why = [f"{tl:g} mm is longer than the {stock:g} mm V-slot pieces"] if tl > stock else []
        if pair_delta > limit:
            why.append(f"a V-slot pair would deflect {pair_delta:.1f} mm (limit {limit:.1f} mm)")
        m["transom"]["core"] = "steel40x20"
        fallbacks.append(f"steel transom: {', and '.join(why)}")
        out.append(dict(t["transom"]))

    if bays > 1:
        for stub, span in (("lower", lower), ("upper", a)):
            name = f"mullion_{stub}"
            length = t[name]["length"]
            d = deflection(VSLOT_PAIR, span, pitch)
            if length <= stock and d <= span / 175:
                m[name]["core"] = VSLOT_PAIR
                out.append({"member": name, "core": VSLOT, "length": length, "qty": 2 * (bays - 1)})
                continue
            why = [f"{length:g} mm is longer than the {stock:g} mm V-slot pieces"] if length > stock else []
            if d > span / 175:
                why.append(f"a V-slot pair would deflect {d:.1f} mm over {span:g} mm (limit {span / 175:.1f} mm)")
            m[name]["core"] = "steel40x20"
            fallbacks.append(f"steel {stub} mullion: {', and '.join(why)}")
            out.append(dict(t[name]))

    for name in ("sash_horizontal", "sash_vertical"):
        single(name, name, t[name]["length"], t[name]["qty"], "alu20")
    out += [x for x in tubes if x["member"].startswith("screen")]
    for x in out:
        x["length"] = round(x["length"], 1)
    tubes[:] = out
    cuts = [(x["member"], x["length"]) for x in out if x["core"] == VSLOT for _ in range(x["qty"])]
    return {"stock": stock, "joins": joins, "fallbacks": fallbacks, "plan": cut_plan(cuts, stock)}


def layout(p):
    if p["glazing"] not in GLAZING_KG_M2:
```

**Replace** in `tools/window.py`:
```python
        raise ValueError(f"screen must be true or false, got {has_screen}")
    sandwich = acrylic_sandwich(p)
    for key in ("opening_w", "opening_h", "fix_gap", "awning_h"):
        if isinstance(p[key], float) and not math.isfinite(p[key]):
```
**with:**
```python
        raise ValueError(f"screen must be true or false, got {has_screen}")
    sandwich = acrylic_sandwich(p)
    stock = vslot_stock(p)
    for key in ("opening_w", "opening_h", "fix_gap", "awning_h"):
        if isinstance(p[key], float) and not math.isfinite(p[key]):
```

**Replace** in `tools/window.py`:
```python
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
**with:**
```python
    trib = (lower + a) / 2
    limit = horiz / 175

    def transom_delta(core):
        if bays == 1:
            return deflection(core, horiz, trib)
        w_t = WIND_KPA / 1000.0 * trib
        half = run / 2
        loads = strip_loads(0.0, half, w_t) + strip_loads(horiz - half, horiz, w_t)
        loads += [(c - F, WIND_KPA / 1000.0 * pitch * trib) for c in mullions]
        return beam_deflection(core, horiz, loads)

    loads_msg = "" if bays == 1 else f" carrying {bays - 1} mullion{'s' if bays > 2 else ''}"
    vslot = None
    if stock is not None:
        vslot = vslot_cores(stock, members, tubes, transom_delta, limit, lower, a, pitch, run, bays, sock, clear)
    core_of = {m["name"]: m["core"] for m in members}
    delta = transom_delta(core_of["transom"])
    checks.append({"name": "transom_deflection", "ok": delta <= limit,
                   "msg": f"transom deflects {delta:.1f} mm at {WIND_KPA} kPa{loads_msg}, limit span/175 = {limit:.1f} mm"})
```

**Replace** in `tools/window.py`:
```python
    kg_m2 = GLAZING_KG_M2[p["glazing"]] * (sandwich["t"] / D["ACRYLIC_T"] if p["glazing"] == "acrylic" else 1)
    sash_kg = gw * gh / 1e6 * kg_m2 + 2 * (sash_w + sash_h) / 1000 * SASH_FRAME_KG_M
    candidates = [s for s in STAYS if STAY_RATIO * sash_h <= s[0] <= sash_h]
    stay = next((s for s in candidates if s[1] >= sash_kg), None)
```
**with:**
```python
    kg_m2 = GLAZING_KG_M2[p["glazing"]] * (sandwich["t"] / D["ACRYLIC_T"] if p["glazing"] == "acrylic" else 1)
    sash_kg = gw * gh / 1e6 * kg_m2 + 2 * (sash_w + sash_h) / 1000 * SASH_FRAME_KG_M
    extra = CORES[VSLOT][4] - CORES["alu20"][4]
    sash_kg += sum(2 * span / 1000 * extra for name, span in (("sash_horizontal", sash_w), ("sash_vertical", sash_h))
                   if core_of[name] == VSLOT)
    candidates = [s for s in STAYS if STAY_RATIO * sash_h <= s[0] <= sash_h]
    stay = next((s for s in candidates if s[1] >= sash_kg), None)
```

**Replace** in `tools/window.py`:
```python
    keeper_at = D["FRAME_BODY"] + D["SASH_GAP"] + S + D["JOINT_GAP"] + by_name["sash_horizontal"]["seg"] / 2
    keeper_dz = round(abs(keeper_at - cam_at), 2)
    lo, hi = keeper_dz_min(), keeper_dz_max(by_name["sash_horizontal"]["seg"])
    checks.append({"name": "cam_keeper", "ok": by_name["transom"]["n"] >= 2 and lo <= keeper_dz <= hi,
                   "msg": f"keeper bosses {keeper_dz:.2f} mm either side of the SBE middle, over the cams "
```
**with:**
```python
    keeper_at = D["FRAME_BODY"] + D["SASH_GAP"] + S + D["JOINT_GAP"] + by_name["sash_horizontal"]["seg"] / 2
    keeper_dz = round(abs(keeper_at - cam_at), 2)
    lo = keeper_dz_min(D["VSLOT_CSK_D"] if core_of["sash_horizontal"] == VSLOT else None)
    hi = keeper_dz_max(by_name["sash_horizontal"]["seg"])
    checks.append({"name": "cam_keeper", "ok": by_name["transom"]["n"] >= 2 and lo <= keeper_dz <= hi,
                   "msg": f"keeper bosses {keeper_dz:.2f} mm either side of the SBE middle, over the cams "
```

**Replace** in `tools/window.py`:
```python
            checks.append({"name": "mullion_deflection", "ok": True, "msg": "1 bay, no mullions"})
        else:
            stubs = [(name, span, deflection(TRANSOM_CORE, span, pitch)) for name, span in (("lower", lower), ("upper", a))]
            name, span, d = max(stubs, key=lambda s: s[2] / s[1])
            checks.append({"name": "mullion_deflection", "ok": all(d_ <= s_ / 175 for _, s_, d_ in stubs),
```
**with:**
```python
            checks.append({"name": "mullion_deflection", "ok": True, "msg": "1 bay, no mullions"})
        else:
            stubs = [(name, span, deflection(core_of[f"mullion_{name}"], span, pitch))
                     for name, span in (("lower", lower), ("upper", a))]
            name, span, d = max(stubs, key=lambda s: s[2] / s[1])
            checks.append({"name": "mullion_deflection", "ok": all(d_ <= s_ / 175 for _, s_, d_ in stubs),
```

**Replace** in `tools/window.py`:
```python
                                  f"limit span/175 = {span / 175:.1f} mm"})

    return {"params": p, "sandwich": sandwich, "w": w, "h": h, "transom_c": transom_c, "members": members,
            "tubes": tubes, "glass": glass, "sash": (sash_w, sash_h), "screen": (screen_w, screen_h),
            "sash_kg": round(sash_kg, 1), "stay": stay[0] if stay else None, "keeper_dz": keeper_dz,
```
**with:**
```python
                                  f"limit span/175 = {span / 175:.1f} mm"})

    if vslot is not None:
        joined = [f"{name} {len(js)}" for name, js in vslot["joins"].items() if js]
        notes = [f"V-slot 2020: {len(vslot['plan'])} pieces of {stock:g} mm"]
        notes += [f"joins: {', '.join(joined)}"] if joined else []
        notes += vslot["fallbacks"]
        checks.append({"name": "core", "ok": True, "msg": "; ".join(notes)})

    return {"params": p, "sandwich": sandwich, "vslot": vslot, "w": w, "h": h, "transom_c": transom_c, "members": members,
            "tubes": tubes, "glass": glass, "sash": (sash_w, sash_h), "screen": (screen_w, screen_h),
            "sash_kg": round(sash_kg, 1), "stay": stay[0] if stay else None, "keeper_dz": keeper_dz,
```

- [ ] **Step 5: Run the tests to see them pass**

Run:
```bash
cd ~/diy-window/tools && python3 -m unittest test_window 2>&1 | grep -E '^(Ran|OK|FAILED)'
cd ~/diy-window/tools && python3 -m unittest discover -p 'test_*.py' 2>&1 | grep -E '^(Ran|OK|FAILED)'
```
Expected: `Ran 147 tests`, `OK`; then `Ran 332 tests`, `OK`.

- [ ] **Step 6: Checkpoint**

Run the compatibility check (Task 0) and the web suite:
```bash
cd ~/diy-window && python3 -m unittest discover -s web/tests -p 'test_*.py' 2>&1 | grep -E '^(Ran|OK|FAILED)'
```
Expected: `BYTE-IDENTICAL`; then `Ran 157 tests`, `OK`. Stop for review if either differs.

---

### Task 2: V-slot geometry in the CAD (`cad/profile.scad`, `cad/lib/segment.scad`, seven parts)

**Files:**
- Create: `cad/tests/vslot_test.scad`
- Modify: `cad/profile.scad`, `cad/lib/segment.scad`, `cad/parts/frame_segment.scad`, `cad/parts/corner_block.scad`, `cad/parts/jamb_node.scad`, `cad/parts/transom_shoe.scad`, `cad/parts/frame_node.scad`, `cad/parts/cross_node.scad`, `cad/parts/mullion_shoe.scad`

**Interfaces:**
- Consumes: the `VSLOT_*` keys (Task 1) through `cad/generated/dims.scad`.
- Produces (every new argument is optional, and leaving it out gives today's geometry exactly):
  - **Profile functions:** `pocket_shift(name, core)`, `pocket_origin(name, core)`, `pocket_rect(name, core)`, `pocket_cut(name, core)`, `chamber_rects(name, core)`, `chambers(name, core)`, `profile_solid(name, pocket = true, core)`, `profile(name, pocket = true, core)`, `cord_ring(name, core)`.
  - **Segment functions:** `screw_x(name, core)`, `tnut(name, core)`, `csk_d(name, core)`, `column_d(name, core)`, `vslot_shell(name)`, `vslot_tip_target()`, `vslot_screw_l(name)`, `vslot_seat(name)`, `boss_dz_min(name, core)`, `end_groove(name, core)`, `end_cap(name, pocket = true, core)`, `tube_screw(name, z, top = undef, core)`, `screw_column(name, z, core)`, `boss_columns(name, z, core)`, `local_solids(..., core)`, `local_cuts(..., core)`, `segment(name, len, code, weep, bosses, boss_dz, core)`.
  - **Part modules:** `frame_segment(..., core)`, `corner_block(a, b, code, mirrored = false, core_a, core_b)`, `jamb_node(code, core)`, `transom_shoe(code, mirrored = false, core)`, `frame_node(name, code, core)`, `cross_node(code, core)`, `mullion_shoe(profile, code, head = false, core)`.
  - **Core values:** `core = "vslot"` means a V-slot tube in this part. `core = "alu20"` means a standard tube in a V-slot window, and only moves the `sash_rebate` pocket.

- [ ] **Step 1: Write the failing CAD test**

**Create** `cad/tests/vslot_test.scad`:
```openscad
// cad/tests/vslot_test.scad
use <../profile.scad>
use <../lib/segment.scad>
include <../generated/dims.scad>

V = "vslot";
TNUT = ["glazing", "sill", "sash_rebate", "sash", "mullion_glazing", "mullion_sash"];
function mid(r) = (r[1] + r[3]) / 2;
function in_shoulder(c, y) = abs(y - c) >= VSLOT_SHOULDER[0] && abs(y - c) <= VSLOT_SHOULDER[1];

o = pocket_origin("sash_rebate", V);
p = pocket("sash_rebate");
assert(o[1] == pocket_origin("sash_rebate")[1] - VSLOT_SHIFT, "V-slot moves the head and upper-jamb pocket outward");
assert(pocket_origin("sash_rebate", "alu20") == o, "a standard tube in a V-slot window sits in the moved pocket");
assert(pocket_rect("glazing", V) == pocket_rect("glazing") && pocket_rect("sash", V) == pocket_rect("sash"), "only sash_rebate moves");
assert(o[1] >= MIN_SHELL && DEPTH - (o[1] + p[1]) >= MIN_SHELL, str("moved pocket shell ", o[1]));
assert(fix_y("sash_rebate") - FIX_D / 2 >= o[1] + p[1] + 2, "fixing screw clears the moved tube");
for (r = chamber_rects("sash_rebate", V)) {
    assert(r[2] - r[0] >= CHAMBER_WALL && r[3] - r[1] >= CHAMBER_WALL, str("collapsed chamber ", r));
    assert(rect_gap(r, pocket_rect("sash_rebate", V)) >= CHAMBER_WALL - 1e-6, str("chamber ", r, " to moved pocket"));
    for (k = kerf_rects("sash_rebate")) assert(rect_gap(r, k) >= MIN_SKIN, str("chamber ", r, " to kerf"));
}
for (c = [undef, V]) let(rs = chamber_rects("sash_rebate", c)) for (i = [0 : len(rs) - 2]) for (j = [i + 1 : len(rs) - 1])
    assert(rect_gap(rs[i], rs[j]) >= CHAMBER_WALL - 1e-6, str("sash_rebate ", c, ": chambers ", rs[i], " and ", rs[j], " ", rect_gap(rs[i], rs[j]), " apart"));

jt = pocket_rect("sash_rebate", V);
assert(stay_c_min() >= jt[1] + TUBE_CLEAR + MIN_SKIN && stay_c_max() <= jt[3] - TUBE_CLEAR - MIN_SKIN, "stay screws land on the moved jamb tube");
mc = pocket_rect("mullion_sash", V)[3] - TUBE_CLEAR - TUBE_FRAME[1] / 2;
for (c = [mid(jt), mid(pocket_rect("sash")), mc]) for (y = [stay_c_min(), stay_c_max()])
    assert(in_shoulder(c, y), str("stay screw at ", y, " is ", abs(y - c), " mm off the tube centre ", c, ", outside the shoulder"));

for (n = TNUT) {
    r = pocket_rect(n, V);
    assert(screw_x(n, V) == (r[0] + r[2]) / 2, str(n, ": T-nut screw on the slot centreline"));
    tip = vslot_seat(n) + vslot_screw_l(n) - vslot_shell(n);
    assert(tip >= VSLOT_TIP[0] && tip <= VSLOT_TIP[1], str(n, ": screw tip ", tip, " mm into the slot"));
    assert(vslot_seat(n) >= 0, str(n, ": seat above the face"));
    assert(vslot_seat(n) + (VSLOT_CSK_D - VSLOT_SCREW_D) / 2 <= vslot_shell(n) - MIN_SKIN, str(n, ": countersink inside the shell"));
    assert((column_d(n, V) - VSLOT_CSK_D) / 2 >= MIN_SKIN, str(n, ": column wall round the M5 head"));
}
assert([for (n = TNUT) vslot_screw_l(n)] == [25, 25, 25, 20, 16, 16], str("M5 lengths ", [for (n = TNUT) vslot_screw_l(n)]));
assert(VSLOT_TIP[0] >= VSLOT_LIP + 3 && VSLOT_TIP[1] <= VSLOT_FLOOR - 0.3, "tip window: 3 mm of nut past the lip, short of the floor");

tc = TRANSOM_W / 2;
assert(screw_x("transom", V) == VSLOT_TRANSOM_X && abs(VSLOT_TRANSOM_X - tc) >= VSLOT_SHOULDER[0] && abs(VSLOT_TRANSOM_X - tc) <= VSLOT_SHOULDER[1],
       "transom screw on the room-side 2020's shoulder");
assert(VSLOT_TRANSOM_X - CSK_D / 2 >= TRANSOM_MAG_X + MAG_W + MIN_SKIN, "transom screw head clear of the magnet channel");
assert(VSLOT_TRANSOM_X + CSK_D / 2 <= TRANSOM_W / 2 + TRANSOM_HALF_BODY - MIN_SKIN, "transom screw head inside the body");
assert(norm([CAM_BOSS_X - VSLOT_TRANSOM_X, BOSS_PITCH / 2]) - INSERT_M4_D / 2 - CSK_D / 2 >= MIN_SKIN, "transom screw clear of the cam inserts");
assert(norm([HINGE_BOSS_X - screw_x("sash_rebate", V), BOSS_PITCH / 2 - FIX_DZ / 2]) - INSERT_M4_D / 2 - VSLOT_CSK_D / 2 >= MIN_SKIN,
       "head M5 clear of the hinge inserts");
assert(boss_dz_min("sash", V) == BOSS_PITCH / 2 + VSLOT_CSK_D / 2 + INSERT_M4_D / 2 + MIN_SKIN, "keeper bosses clear the sash M5 head");
echo("vslot rules ok");
```

- [ ] **Step 2: Run it to see it fail**

Run: `cd ~/diy-window && cad/box.sh test; echo "exit $?"`
Expected: `exit 1`. The log ends with:
```
== vslot_test.scad
WARNING: Too many unnamed arguments supplied in file vslot_test.scad, line 11
WARNING: Too many unnamed arguments supplied in file vslot_test.scad, line 26
WARNING: Too many unnamed arguments supplied in file vslot_test.scad, line 28
ERROR: Assertion '(o[1] == (pocket_origin("sash_rebate")[1] - VSLOT_SHIFT))' failed: "V-slot moves the head and upper-jamb pocket outward" in file vslot_test.scad, line 13
== DONE
```

- [ ] **Step 3: Thread `core` through the profile**

**Replace** in `cad/profile.scad`:
```openscad
function pocket(name) = tube(name) + [2, 2] * TUBE_CLEAR;

function pocket_origin(name) =
    name == "transom" ? [TRANSOM_W / 2, DEPTH / 2] - pocket(name) / 2
  : is_mullion(name) ? [MULLION_W / 2, DEPTH / 2] - pocket(name) / 2
  : name == "sash" ? [SASH_BODY / 2, (SASH_Y0 + LIP_Y1) / 2] - pocket(name) / 2
  : name == "screen" ? [SCREEN_SHELL, (SCREEN_DEPTH - pocket(name)[1]) / 2]
  : [MIN_SHELL, (DEPTH - pocket(name)[1]) / 2];

function pocket_rect(name) = concat(pocket_origin(name), pocket_origin(name) + pocket(name));

function sash_tube_y() = [pocket_rect("sash")[1] + TUBE_CLEAR, pocket_rect("sash")[3] - TUBE_CLEAR];
```
**with:**
```openscad
function pocket(name) = tube(name) + [2, 2] * TUBE_CLEAR;

function pocket_shift(name, core) = name == "sash_rebate" && !is_undef(core) ? VSLOT_SHIFT : 0;

function pocket_origin(name, core) =
    name == "transom" ? [TRANSOM_W / 2, DEPTH / 2] - pocket(name) / 2
  : is_mullion(name) ? [MULLION_W / 2, DEPTH / 2] - pocket(name) / 2
  : name == "sash" ? [SASH_BODY / 2, (SASH_Y0 + LIP_Y1) / 2] - pocket(name) / 2
  : name == "screen" ? [SCREEN_SHELL, (SCREEN_DEPTH - pocket(name)[1]) / 2]
  : [MIN_SHELL, (DEPTH - pocket(name)[1]) / 2 - pocket_shift(name, core)];

function pocket_rect(name, core) = concat(pocket_origin(name, core), pocket_origin(name, core) + pocket(name));

function sash_tube_y() = [pocket_rect("sash")[1] + TUBE_CLEAR, pocket_rect("sash")[3] - TUBE_CLEAR];
```

**Replace** in `cad/profile.scad`:
```openscad
function mag_rects(name) = is_undef(mag_rect(name)) ? [] : is_mullion(name) ? both_sides([mag_rect(name)]) : [mag_rect(name)];

function chamber_rects(name) =
    let(w = CHAMBER_WALL, o = pocket_origin(name), p = pocket(name), keyed = len(bead_key_rects(name)) > 0)
    is_frame_body(name) ? concat(
        [[w, name == "sill" ? NOSE_KEY_D + w : w,
          name == "sash_rebate" ? FRAME_BODY - w : rebate_face(name) - FIX_CB_L - w, o[1] - w],
         [o[0] + p[0] + w, name == "sash_rebate" ? o[1] : max(o[1], fix_y(name) + FIX_CB_D / 2 + MIN_SKIN), FRAME_BODY - 2 * w, KEY_Y - w],
         [w, o[1] + p[1] + w, keyed ? FRAME_BODY - KEY_D - w : FRAME_BODY - w, DEPTH - w]],
        keyed ? [[w, KEY_Y + KEY_H + w, FRAME_BODY - w, DEPTH - w]] : [])
```
**with:**
```openscad
function mag_rects(name) = is_undef(mag_rect(name)) ? [] : is_mullion(name) ? both_sides([mag_rect(name)]) : [mag_rect(name)];

function chamber_rects(name, core) =
    let(w = CHAMBER_WALL, o = pocket_origin(name, core), p = pocket(name), keyed = len(bead_key_rects(name)) > 0)
    is_frame_body(name) ? concat(
        [[w, name == "sill" ? NOSE_KEY_D + w : w,
          name == "sash_rebate" ? FRAME_BODY - w : rebate_face(name) - FIX_CB_L - w, o[1] - w],
         [o[0] + p[0] + w, name == "sash_rebate" ? o[1] : max(o[1], fix_y(name) + FIX_CB_D / 2 + MIN_SKIN), FRAME_BODY - 2 * w, min(KEY_Y - w, o[1] + p[1])],
         [w, o[1] + p[1] + w, keyed ? FRAME_BODY - KEY_D - w : FRAME_BODY - w, DEPTH - w]],
        keyed ? [[w, KEY_Y + KEY_H + w, FRAME_BODY - w, DEPTH - w]] : [])
```

**Replace** in `cad/profile.scad`:
```openscad
module kerf(cx, y, dir = 1) { rect_r(kerf_rect(cx, y, dir)); }

module pocket_cut(name) { rect_r(pocket_rect(name)); }

module bead_key(name) { for (r = bead_key_rects(name)) rect_r(r); }
```
**with:**
```openscad
module kerf(cx, y, dir = 1) { rect_r(kerf_rect(cx, y, dir)); }

module pocket_cut(name, core) { rect_r(pocket_rect(name, core)); }

module bead_key(name) { for (r = bead_key_rects(name)) rect_r(r); }
```

**Replace** in `cad/profile.scad`:
```openscad
}

module chambers(name) { for (r = chamber_rects(name)) rect_r(r); }

module profile_solid(name, pocket = true) {
    fb = FRAME_BODY;
    tl = TRANSOM_W / 2 - TRANSOM_HALF_BODY;
```
**with:**
```openscad
}

module chambers(name, core) { for (r = chamber_rects(name, core)) rect_r(r); }

module profile_solid(name, pocket = true, core) {
    fb = FRAME_BODY;
    tl = TRANSOM_W / 2 - TRANSOM_HALF_BODY;
```

**Replace** in `cad/profile.scad`:
```openscad
        }
        else assert(false, str("unknown profile ", name));
        if (pocket) pocket_cut(name);
        bead_key(name);
        for (r = kerf_rects(name)) rect_r(r);
```
**with:**
```openscad
        }
        else assert(false, str("unknown profile ", name));
        if (pocket) pocket_cut(name, core);
        bead_key(name);
        for (r = kerf_rects(name)) rect_r(r);
```

**Replace** in `cad/profile.scad`:
```openscad
}

module profile(name, pocket = true) {
    difference() {
        profile_solid(name, pocket);
        chambers(name);
    }
}
```
**with:**
```openscad
}

module profile(name, pocket = true, core) {
    difference() {
        profile_solid(name, pocket, core);
        chambers(name, core);
    }
}
```

**Replace** in `cad/profile.scad`:
```openscad
function has_cord(name) = !is_undef(core_box(name));

module cord_ring(name) {
    if (has_cord(name)) difference() {
        offset(delta = -CORD_INSET) intersection() { profile_solid(name, false); rect_r(core_box(name)); }
        offset(delta = -CORD_INSET - CORD_D) intersection() { profile_solid(name, false); rect_r(core_box(name)); }
        offset(delta = MIN_SKIN) pocket_cut(name);
    }
}
```
**with:**
```openscad
function has_cord(name) = !is_undef(core_box(name));

module cord_ring(name, core) {
    if (has_cord(name)) difference() {
        offset(delta = -CORD_INSET) intersection() { profile_solid(name, false); rect_r(core_box(name)); }
        offset(delta = -CORD_INSET - CORD_D) intersection() { profile_solid(name, false); rect_r(core_box(name)); }
        offset(delta = MIN_SKIN) pocket_cut(name, core);
    }
}
```

- [ ] **Step 4: T-nut and shoulder screws in the segment library**

**Replace** in `cad/lib/segment.scad`:
```openscad
function boss_offsets(dz) = dz == 0 ? [0] : [-dz, dz];

function boss_dz_min(name) =
    BOSS_PITCH / 2 + max((INSERT_M4_D + MIN_SKIN) / 2,
        fix_dz(name) / 2 + sqrt(max(0, pow(CSK_D / 2 + INSERT_M4_D / 2 + MIN_SKIN, 2) - pow(boss_x(name) - screw_x(name), 2))));

function boss_dz_max(len) = len / 2 - END_CAP - MIN_SKIN - INSERT_M4_D / 2 - BOSS_PITCH / 2;

function screw_x(name) = name == "transom" ? TRANSOM_SCREW_X : pocket_origin(name)[0] + pocket(name)[0] / 2;

function label_at(name) =
```
**with:**
```openscad
function boss_offsets(dz) = dz == 0 ? [0] : [-dz, dz];

function boss_dz_min(name, core) =
    BOSS_PITCH / 2 + max((INSERT_M4_D + MIN_SKIN) / 2,
        fix_dz(name) / 2 + sqrt(max(0, pow(csk_d(name, core) / 2 + INSERT_M4_D / 2 + MIN_SKIN, 2) - pow(boss_x(name) - screw_x(name, core), 2))));

function boss_dz_max(len) = len / 2 - END_CAP - MIN_SKIN - INSERT_M4_D / 2 - BOSS_PITCH / 2;

function screw_x(name, core) =
    name == "transom" ? (core == "vslot" ? VSLOT_TRANSOM_X : TRANSOM_SCREW_X) : pocket_origin(name, core)[0] + pocket(name)[0] / 2;

function tnut(name, core) = core == "vslot" && name != "transom";

function csk_d(name, core) = tnut(name, core) ? VSLOT_CSK_D : CSK_D;

function column_d(name, core) = tnut(name, core) ? VSLOT_CSK_D + 4 : 10;

function vslot_shell(name) = top_face(name) - pocket_rect(name, "vslot")[3];

function vslot_tip_target() = (VSLOT_TIP[0] + VSLOT_TIP[1]) / 2;

function vslot_screw_l(name) = max([for (l = VSLOT_M5_L) if (l <= vslot_shell(name) + vslot_tip_target() + 1e-9) l]);

function vslot_seat(name) = vslot_shell(name) + vslot_tip_target() - vslot_screw_l(name);

function label_at(name) =
```

**Replace** in `cad/lib/segment.scad`:
```openscad
  : undef;

module end_groove(name) { linear_extrude(CORD_D / 2 + EPS) cord_ring(name); }

module end_cap(name, pocket = true) { linear_extrude(END_CAP) profile_solid(name, pocket); }

module tube_screw(name, z, top = undef) {
    p = pocket_rect(name);
    h = (is_undef(top) ? top_face(name) : top) - p[3];
    translate([screw_x(name), p[3] - EPS, z]) rotate([-90, 0, 0]) {
        cylinder(d = TUBE_SCREW_D, h = top_face(name) - p[3] + 1, $fn = 24);
        translate([0, 0, h - 2.2]) cylinder(d1 = TUBE_SCREW_D, d2 = CSK_D, h = 2.2 + 2 * EPS, $fn = 32);
        translate([0, 0, h]) cylinder(d = CSK_D, h = top_face(name) - p[3] - h + 1, $fn = 32);
    }
}

module screw_column(name, z) {
    p = pocket_rect(name);
    translate([screw_x(name), p[3], z]) rotate([-90, 0, 0]) cylinder(d = 10, h = top_face(name) - p[3], $fn = 32);
}

```
**with:**
```openscad
  : undef;

module end_groove(name, core) { linear_extrude(CORD_D / 2 + EPS) cord_ring(name, core); }

module end_cap(name, pocket = true, core) { linear_extrude(END_CAP) profile_solid(name, pocket, core); }

module tube_screw(name, z, top = undef, core) {
    t = tnut(name, core);
    assert(!t || is_undef(top), str(name, ": a T-nut screw takes no seat override"));
    p = pocket_rect(name, core);
    d = t ? VSLOT_SCREW_D : TUBE_SCREW_D;
    k = csk_d(name, core);
    cone = t ? (k - d) / 2 : 2.2;
    h = (t ? top_face(name) - vslot_seat(name) : is_undef(top) ? top_face(name) : top) - p[3];
    translate([screw_x(name, core), p[3] - EPS, z]) rotate([-90, 0, 0]) {
        cylinder(d = d, h = top_face(name) - p[3] + 1, $fn = 24);
        translate([0, 0, h - cone]) cylinder(d1 = d, d2 = k, h = cone + 2 * EPS, $fn = 32);
        translate([0, 0, h]) cylinder(d = k, h = top_face(name) - p[3] - h + 1, $fn = 32);
    }
}

module screw_column(name, z, core) {
    p = pocket_rect(name, core);
    translate([screw_x(name, core), p[3], z]) rotate([-90, 0, 0]) cylinder(d = column_d(name, core), h = top_face(name) - p[3], $fn = 32);
}

```

**Replace** in `cad/lib/segment.scad`:
```openscad
}

module boss_columns(name, z) {
    p = pocket_rect(name);
    for (dz = [-BOSS_PITCH / 2, BOSS_PITCH / 2])
        translate([boss_x(name), p[3], z + dz]) rotate([-90, 0, 0])
```
**with:**
```openscad
}

module boss_columns(name, z, core) {
    p = pocket_rect(name, core);
    for (dz = [-BOSS_PITCH / 2, BOSS_PITCH / 2])
        translate([boss_x(name), p[3], z + dz]) rotate([-90, 0, 0])
```

**Replace** in `cad/lib/segment.scad`:
```openscad
}

module local_solids(name, z, bosses = false, boss_dz = 0) {
    screw_column(name, z - fix_dz(name) / 2);
    if (is_perimeter(name)) fixing_column(name, z + fix_dz(name) / 2);
    if (bosses) for (c = boss_offsets(boss_dz)) boss_columns(name, z + c);
}

module local_cuts(name, z, bosses = false, boss_dz = 0) {
    tube_screw(name, z - fix_dz(name) / 2);
    if (is_perimeter(name)) fixing_hole(name, z + fix_dz(name) / 2);
    if (bosses) for (c = boss_offsets(boss_dz)) insert_holes(name, z + c);
}

module segment(name, len, code, weep = false, bosses = false, boss_dz = 0) {
    assert(len > 0 && len <= MAX_SEG, str(code, ": length ", len, " outside 0..", MAX_SEG));
    assert(!weep || name == "sill" || name == "transom" || name == "sash", str(code, ": no weep on ", name));
    assert(!bosses || boss_x(name) != undef, str(code, ": no bosses on ", name));
    if (boss_dz != 0)
        assert(bosses && abs(boss_dz) >= boss_dz_min(name) && abs(boss_dz) <= boss_dz_max(len),
               str(code, ": boss offset ", boss_dz, " outside ", boss_dz_min(name), "..", boss_dz_max(len)));
    difference() {
        union() {
            linear_extrude(len) profile(name);
            for (z = [0, len - END_CAP]) translate([0, 0, z]) end_cap(name);
            intersection() {
                linear_extrude(len) profile_solid(name);
                local_solids(name, len / 2, bosses, abs(boss_dz));
            }
        }
        for (z = [-EPS, len - CORD_D / 2]) translate([0, 0, z]) end_groove(name);
        local_cuts(name, len / 2, bosses, abs(boss_dz));
        if (weep) translate([0, 0, len / 2 - WEEP_W / 2]) linear_extrude(WEEP_W) rect_r(weep_rect(name));
        engrave(code, label_at(name), len / 2);
```
**with:**
```openscad
}

module local_solids(name, z, bosses = false, boss_dz = 0, core) {
    screw_column(name, z - fix_dz(name) / 2, core);
    if (is_perimeter(name)) fixing_column(name, z + fix_dz(name) / 2);
    if (bosses) for (c = boss_offsets(boss_dz)) boss_columns(name, z + c, core);
}

module local_cuts(name, z, bosses = false, boss_dz = 0, core) {
    tube_screw(name, z - fix_dz(name) / 2, core = core);
    if (is_perimeter(name)) fixing_hole(name, z + fix_dz(name) / 2);
    if (bosses) for (c = boss_offsets(boss_dz)) insert_holes(name, z + c);
}

module segment(name, len, code, weep = false, bosses = false, boss_dz = 0, core) {
    assert(len > 0 && len <= MAX_SEG, str(code, ": length ", len, " outside 0..", MAX_SEG));
    assert(!weep || name == "sill" || name == "transom" || name == "sash", str(code, ": no weep on ", name));
    assert(!bosses || boss_x(name) != undef, str(code, ": no bosses on ", name));
    if (boss_dz != 0)
        assert(bosses && abs(boss_dz) >= boss_dz_min(name, core) && abs(boss_dz) <= boss_dz_max(len),
               str(code, ": boss offset ", boss_dz, " outside ", boss_dz_min(name, core), "..", boss_dz_max(len)));
    difference() {
        union() {
            linear_extrude(len) profile(name, core = core);
            for (z = [0, len - END_CAP]) translate([0, 0, z]) end_cap(name, core = core);
            intersection() {
                linear_extrude(len) profile_solid(name, core = core);
                local_solids(name, len / 2, bosses, abs(boss_dz), core);
            }
        }
        for (z = [-EPS, len - CORD_D / 2]) translate([0, 0, z]) end_groove(name, core);
        local_cuts(name, len / 2, bosses, abs(boss_dz), core);
        if (weep) translate([0, 0, len / 2 - WEEP_W / 2]) linear_extrude(WEEP_W) rect_r(weep_rect(name));
        engrave(code, label_at(name), len / 2);
```

- [ ] **Step 5: Pass `core` through the parts**

**Replace** in `cad/parts/frame_segment.scad`:
```openscad
use <../lib/segment.scad>

module frame_segment(profile, len, code, weep = false, bosses = false, boss_dz = 0) {
    segment(profile, len, code, weep, bosses, boss_dz);
}
```
**with:**
```openscad
use <../lib/segment.scad>

module frame_segment(profile, len, code, weep = false, bosses = false, boss_dz = 0, core) {
    segment(profile, len, code, weep, bosses, boss_dz, core);
}
```

**Replace** in `cad/parts/corner_block.scad`:
```openscad
ALONG_X = [[0, 0, 1, 0], [0, 1, 0, 0], [1, 0, 0, 0]];

function socket_limit(a, b) = profile_width(b) - pocket_rect(b)[2] - CHAMBER_WALL;
function corner_anchor(a, b) = profile_width(b) - socket_depth(a) / 2;
function corner_screw_at(a, b) = corner_anchor(a, b) - fix_dz(a) / 2;
```
**with:**
```openscad
ALONG_X = [[0, 0, 1, 0], [0, 1, 0, 0], [1, 0, 0, 0]];

function socket_limit(a, b, core) = profile_width(b) - pocket_rect(b, core)[2] - CHAMBER_WALL;
function corner_anchor(a, b) = profile_width(b) - socket_depth(a) / 2;
function corner_screw_at(a, b) = corner_anchor(a, b) - fix_dz(a) / 2;
```

**Replace** in `cad/parts/corner_block.scad`:
```openscad
}

module leg(a, b) {
    z0 = profile_min(b);
    z1 = profile_width(b);
    translate([0, 0, z0]) linear_extrude(z1 - z0) profile(a, false);
    translate([0, 0, z1 - END_CAP]) end_cap(a, false);
    intersection() {
        translate([0, 0, z0]) linear_extrude(z1 - z0) profile_solid(a, false);
        union() {
            screw_column(a, corner_screw_at(a, b));
            if (is_perimeter(a)) fixing_column(a, corner_fix_at(a, b));
        }
```
**with:**
```openscad
}

module leg(a, b, core) {
    z0 = profile_min(b);
    z1 = profile_width(b);
    translate([0, 0, z0]) linear_extrude(z1 - z0) profile(a, false, core);
    translate([0, 0, z1 - END_CAP]) end_cap(a, false, core);
    intersection() {
        translate([0, 0, z0]) linear_extrude(z1 - z0) profile_solid(a, false, core);
        union() {
            screw_column(a, corner_screw_at(a, b), core);
            if (is_perimeter(a)) fixing_column(a, corner_fix_at(a, b));
        }
```

**Replace** in `cad/parts/corner_block.scad`:
```openscad
}

module leg_cuts(a, b) {
    z1 = profile_width(b);
    translate([0, 0, z1 - socket_depth(a)]) linear_extrude(socket_depth(a) + EPS) pocket_cut(a);
    translate([0, 0, z1 - CORD_D / 2]) end_groove(a);
    tube_screw(a, corner_screw_at(a, b));
    if (is_perimeter(a)) fixing_hole(a, corner_fix_at(a, b));
}

module corner_block(a, b, code, mirrored = false) {
    assert(socket_depth(a) <= socket_limit(a, b) && socket_depth(b) <= socket_limit(b, a), str(code, ": tube sockets collide"));
    lo = min(profile_min(a), profile_min(b));
    hi = max(profile_width(a), profile_width(b));
```
**with:**
```openscad
}

module leg_cuts(a, b, core) {
    z1 = profile_width(b);
    translate([0, 0, z1 - socket_depth(a)]) linear_extrude(socket_depth(a) + EPS) pocket_cut(a, core);
    translate([0, 0, z1 - CORD_D / 2]) end_groove(a, core);
    tube_screw(a, corner_screw_at(a, b), core = core);
    if (is_perimeter(a)) fixing_hole(a, corner_fix_at(a, b));
}

module corner_block(a, b, code, mirrored = false, core_a, core_b) {
    assert(socket_depth(a) <= socket_limit(a, b, core_b) && socket_depth(b) <= socket_limit(b, a, core_a), str(code, ": tube sockets collide"));
    lo = min(profile_min(a), profile_min(b));
    hi = max(profile_width(a), profile_width(b));
```

**Replace** in `cad/parts/corner_block.scad`:
```openscad
            union() {
                intersection() {
                    multmatrix(ALONG_X) leg(a, b);
                    half_space(lo - 1, hi + 1, true);
                }
                intersection() {
                    leg(b, a);
                    half_space(lo - 1, hi + 1, false);
                }
            }
            multmatrix(ALONG_X) leg_cuts(a, b);
            leg_cuts(b, a);
        }
        engrave(code, label_at(b), (profile_min(a) + profile_width(a)) / 2, facing = mirrored ? 1 : -1);
```
**with:**
```openscad
            union() {
                intersection() {
                    multmatrix(ALONG_X) leg(a, b, core_a);
                    half_space(lo - 1, hi + 1, true);
                }
                intersection() {
                    leg(b, a, core_b);
                    half_space(lo - 1, hi + 1, false);
                }
            }
            multmatrix(ALONG_X) leg_cuts(a, b, core_a);
            leg_cuts(b, a, core_b);
        }
        engrave(code, label_at(b), (profile_min(a) + profile_width(a)) / 2, facing = mirrored ? 1 : -1);
```

**Replace** in `cad/parts/jamb_node.scad`:
```openscad
}

module jamb_node(code) {
    c = TRANSOM_W / 2;
    k = node_key_len();
    difference() {
        linear_extrude(TRANSOM_W) rect(0, 0, FRAME_BODY, DEPTH);
        translate([0, 0, -EPS]) linear_extrude(TRANSOM_W + 2 * EPS) pocket_cut("glazing");
        for (z = [-EPS, TRANSOM_W - k]) translate([0, 0, z]) linear_extrude(k + EPS) bead_key("glazing");
        for (z = [-EPS, TRANSOM_W - CORD_D / 2]) translate([0, 0, z]) end_groove("glazing");
        translate([FRAME_BODY, DEPTH + EPS, c]) rotate([90, 0, 0]) linear_extrude(DEPTH - STOP_T + EPS) dove_slot2d();
        for (q = lock_uv()) translate([FRAME_BODY + q[0], 0, c + q[1]]) lock_hole();
        tube_screw("glazing", c);
        for (dz = [-NODE_FIX_OFFSET, NODE_FIX_OFFSET]) fixing_hole("glazing", c + dz);
        engrave(code, label_at("glazing"), c);
```
**with:**
```openscad
}

module jamb_node(code, core) {
    c = TRANSOM_W / 2;
    k = node_key_len();
    difference() {
        linear_extrude(TRANSOM_W) rect(0, 0, FRAME_BODY, DEPTH);
        translate([0, 0, -EPS]) linear_extrude(TRANSOM_W + 2 * EPS) pocket_cut("glazing", core);
        for (z = [-EPS, TRANSOM_W - k]) translate([0, 0, z]) linear_extrude(k + EPS) bead_key("glazing");
        for (z = [-EPS, TRANSOM_W - CORD_D / 2]) translate([0, 0, z]) end_groove("glazing", core);
        translate([FRAME_BODY, DEPTH + EPS, c]) rotate([90, 0, 0]) linear_extrude(DEPTH - STOP_T + EPS) dove_slot2d();
        for (q = lock_uv()) translate([FRAME_BODY + q[0], 0, c + q[1]]) lock_hole();
        tube_screw("glazing", c, core = core);
        for (dz = [-NODE_FIX_OFFSET, NODE_FIX_OFFSET]) fixing_hole("glazing", c + dz);
        engrave(code, label_at("glazing"), c);
```

**Replace** in `cad/parts/transom_shoe.scad`:
```openscad
module box(b) { translate([b[0], b[1], b[4]]) cube([b[2] - b[0], b[3] - b[1], b[5] - b[4]]); }

module transom_shoe(code, mirrored = false) {
    L = FRAME_W - FRAME_BODY;
    c = TRANSOM_W / 2;
```
**with:**
```openscad
module box(b) { translate([b[0], b[1], b[4]]) cube([b[2] - b[0], b[3] - b[1], b[5] - b[4]]); }

module transom_shoe(code, mirrored = false, core) {
    L = FRAME_W - FRAME_BODY;
    c = TRANSOM_W / 2;
```

**Replace** in `cad/parts/transom_shoe.scad`:
```openscad
        translate([mirrored ? TRANSOM_W : 0, 0, 0]) mirror([mirrored ? 1 : 0, 0, 0]) difference() {
            union() {
                linear_extrude(L) profile("transom");
                linear_extrude(SHOE_WALL) profile_solid("transom", false);
                box(shoe_fin_stub());
                multmatrix([[0, 1, 0, c], [0, 0, 1, STOP_T + DOVE_CLEAR], [1, 0, 0, 0]])
```
**with:**
```openscad
        translate([mirrored ? TRANSOM_W : 0, 0, 0]) mirror([mirrored ? 1 : 0, 0, 0]) difference() {
            union() {
                linear_extrude(L) profile("transom", core = core);
                linear_extrude(SHOE_WALL) profile_solid("transom", false, core);
                box(shoe_fin_stub());
                multmatrix([[0, 1, 0, c], [0, 0, 1, STOP_T + DOVE_CLEAR], [1, 0, 0, 0]])
```

**Replace** in `cad/parts/transom_shoe.scad`:
```openscad
            }
            for (t = shoe_turns()) box(t[0]);
            translate([0, 0, L - CORD_D / 2]) end_groove("transom");
            for (q = lock_uv()) translate([c + q[1], 0, q[0]]) lock_hole();
            box(shoe_seam_groove());
            tube_screw("transom", SHOE_WALL + (L - SHOE_WALL) / 2, DEPTH - MAG_D);
        }
        engrave(code, [mirrored ? TRANSOM_W - at[0] : at[0], at[1]], L / 2, facing = mirrored ? 1 : -1);
```
**with:**
```openscad
            }
            for (t = shoe_turns()) box(t[0]);
            translate([0, 0, L - CORD_D / 2]) end_groove("transom", core);
            for (q = lock_uv()) translate([c + q[1], 0, q[0]]) lock_hole();
            box(shoe_seam_groove());
            tube_screw("transom", SHOE_WALL + (L - SHOE_WALL) / 2, DEPTH - MAG_D, core);
        }
        engrave(code, [mirrored ? TRANSOM_W - at[0] : at[0], at[1]], L / 2, facing = mirrored ? 1 : -1);
```

**Replace** in `cad/parts/frame_node.scad`:
```openscad
function frame_node_fix(name) = name == "sill" ? "glazing" : name;

module frame_node(name, code) {
    assert(name == "sill" || name == "sash_rebate", str(code, ": frame nodes sit in the sill or the head, not ", name));
    c = MULLION_W / 2;
```
**with:**
```openscad
function frame_node_fix(name) = name == "sill" ? "glazing" : name;

module frame_node(name, code, core) {
    assert(name == "sill" || name == "sash_rebate", str(code, ": frame nodes sit in the sill or the head, not ", name));
    c = MULLION_W / 2;
```

**Replace** in `cad/parts/frame_node.scad`:
```openscad
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
```
**with:**
```openscad
        linear_extrude(MULLION_W) rect(0, 0, FRAME_BODY, DEPTH);
        translate([0, 0, -EPS]) linear_extrude(MULLION_W + 2 * EPS) {
            pocket_cut(name, core);
            if (name == "sill") for (r = nose_key_rects()) rect_r(r);
        }
        for (z = [-EPS, MULLION_W - k]) translate([0, 0, z]) linear_extrude(k + EPS) bead_key(name);
        for (z = [-EPS, MULLION_W - CORD_D / 2]) translate([0, 0, z]) end_groove(name, core);
        translate([FRAME_BODY, DEPTH + EPS, c]) rotate([90, 0, 0]) linear_extrude(DEPTH - STOP_T + EPS) dove_slot2d(d[0], d[1]);
        for (q = mlock_uv()) translate([FRAME_BODY + q[0], 0, c + q[1]]) lock_hole();
        tube_screw(name, c, core = core);
        for (dz = [-NODE_FIX_OFFSET, NODE_FIX_OFFSET]) fixing_hole(frame_node_fix(name), c + dz);
        engrave(code, label_at(name), c);
```

**Replace** in `cad/parts/cross_node.scad`:
```openscad
    [for (q = mlock_uv()) each [[cross_faces()[0] - q[0], q[1]], [cross_faces()[1] + q[0], q[1]]]];

module cross_node(code) {
    c = MULLION_W / 2;
    k = mullion_leg();
```
**with:**
```openscad
    [for (q = mlock_uv()) each [[cross_faces()[0] - q[0], q[1]], [cross_faces()[1] + q[0], q[1]]]];

module cross_node(code, core) {
    c = MULLION_W / 2;
    k = mullion_leg();
```

**Replace** in `cad/parts/cross_node.scad`:
```openscad
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
```
**with:**
```openscad
    difference() {
        linear_extrude(MULLION_W) rect(f[0], 0, f[1], DEPTH);
        translate([0, 0, -EPS]) linear_extrude(MULLION_W + 2 * EPS) { pocket_cut("transom", core); rect_r(mag_rect("transom")); }
        for (z = [-EPS, MULLION_W - k]) translate([0, 0, z]) linear_extrude(k + EPS) bead_key("transom");
        for (z = [-EPS, MULLION_W - CORD_D / 2]) translate([0, 0, z]) end_groove("transom", core);
        for (s = [[f[0], -1], [f[1], 1]]) translate([s[0], DEPTH + EPS, c]) rotate([90, 0, 0]) scale([s[1], 1, 1])
            linear_extrude(DEPTH - STOP_T + EPS) dove_slot2d(d[0], d[1]);
        for (q = cross_locks()) translate([q[0], 0, c + q[1]]) lock_hole();
        for (r = cross_mag_cuts()) box(r);
        tube_screw("transom", c, core = core);
        engrave(code, label_at("transom"), k / 2);
    }
```

**Replace** in `cad/parts/mullion_shoe.scad`:
```openscad
function mshoe_screw_z() = SHOE_WALL + (mullion_leg() - SHOE_WALL) / 2;

module mullion_shoe(profile, code, head = false) {
    assert(is_mullion(profile), str(code, ": ", profile, " is not a mullion profile"));
    assert(!head || profile == "mullion_sash", str(code, ": only the upper mullion meets the head"));
```
**with:**
```openscad
function mshoe_screw_z() = SHOE_WALL + (mullion_leg() - SHOE_WALL) / 2;

module mullion_shoe(profile, code, head = false, core) {
    assert(is_mullion(profile), str(code, ": ", profile, " is not a mullion profile"));
    assert(!head || profile == "mullion_sash", str(code, ": only the upper mullion meets the head"));
```

**Replace** in `cad/parts/mullion_shoe.scad`:
```openscad
    difference() {
        union() {
            linear_extrude(L) profile(profile);
            linear_extrude(SHOE_WALL) profile_solid(profile, false);
            for (b = mshoe_fin_stubs(profile)) box(b);
            multmatrix([[0, 1, 0, c], [0, 0, 1, STOP_T + DOVE_CLEAR], [1, 0, 0, 0]])
```
**with:**
```openscad
    difference() {
        union() {
            linear_extrude(L) profile(profile, core = core);
            linear_extrude(SHOE_WALL) profile_solid(profile, false, core);
            for (b = mshoe_fin_stubs(profile)) box(b);
            multmatrix([[0, 1, 0, c], [0, 0, 1, STOP_T + DOVE_CLEAR], [1, 0, 0, 0]])
```

**Replace** in `cad/parts/mullion_shoe.scad`:
```openscad
        }
        for (t = mshoe_turns(profile, head)) box(t);
        translate([0, 0, L - CORD_D / 2]) end_groove(profile);
        for (q = mlock_uv()) translate([c + q[1], 0, q[0]]) lock_hole();
        box(mshoe_seam_groove(profile));
        tube_screw(profile, mshoe_screw_z());
        engrave(code, label_at(profile), L / 2);
    }
```
**with:**
```openscad
        }
        for (t = mshoe_turns(profile, head)) box(t);
        translate([0, 0, L - CORD_D / 2]) end_groove(profile, core);
        for (q = mlock_uv()) translate([c + q[1], 0, q[0]]) lock_hole();
        box(mshoe_seam_groove(profile));
        tube_screw(profile, mshoe_screw_z(), core = core);
        engrave(code, label_at(profile), L / 2);
    }
```

- [ ] **Step 6: Run the CAD tests to see them pass**

Run: `cd ~/diy-window && cad/box.sh test`
Expected: `10 test files passed`.

- [ ] **Step 7: Checkpoint: default STLs are byte-identical**

This re-renders the whole bench window and the 2-bay window's mullion parts, which between them use every changed module, and compares them with the Task 0 copies. Run one render at a time:
```bash
cd ~/diy-window && cad/box.sh render bench-600 | tail -1
cd ~/diy-window && cad/box.sh render home-1800x1500-2bay SN HN TX MSL MST MSH ML MU | tail -1
cd ~/diy-window && n=0; bad=""; for f in .vslot-baseline/stl-bench-600/*.stl; do b=$(basename $f); cmp -s "$f" cad/stl/bench-600/$b && n=$((n+1)) || bad="$bad $b"; done; echo "bench: $n identical;$bad"
cd ~/diy-window && n=0; bad=""; for b in SN HN TX MSL MST MSH ML MU; do cmp -s .vslot-baseline/stl-2bay/$b.stl cad/stl/home-1800x1500-2bay/$b.stl && n=$((n+1)) || bad="$bad $b"; done; echo "2bay: $n identical;$bad"
```
Expected: `37/37 parts ok`, `8/8 parts ok`, `bench: 37 identical;`, `2bay: 8 identical;`. If a part differs, copy the baseline STLs back (`cp .vslot-baseline/stl-bench-600/*.stl cad/stl/bench-600/`, and the same for `stl-2bay`), then stop for review. Then run the compatibility check: `BYTE-IDENTICAL`.

---

### Task 3: Part calls carry the core (`tools/generate.py`)

**Files:**
- Modify: `tools/generate.py`
- Test: `tools/test_generate.py` (append)

**Interfaces:**
- Consumes: member cores and `lay["vslot"]` (Task 1), and the CAD arguments (Task 2).
- Produces: `generate.core_arg(lay, name, key="core") -> str`, which gives `', core="vslot"'`, `', core="alu20"'` (sash_rebate fallback only) or `""`.

- [ ] **Step 1: Write the failing tests**

**Replace** in `tools/test_generate.py`:
```python


if __name__ == "__main__":
    unittest.main()
```
**with:**
```python


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
            rows = list(csv.reader(path.open()))
        self.assertEqual(rows[1:3], [["head 1/2", "vslot2020", "919.8", "1"], ["head 2/2", "vslot2020", "801.2", "1"]])


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the tests to see them fail**

Run: `cd ~/diy-window/tools && python3 -m unittest test_generate 2>&1 | grep -E '^(Ran|OK|FAILED)'`
Expected: `Ran 89 tests`, `FAILED (failures=4)`. The call tests fail because the calls carry no `core` yet. `testDefaultCallsHaveNoCore` and `testCutlistListsThePieces` already pass: the cut list comes from Task 1.

- [ ] **Step 3: Add the core arguments**

**Replace** in `tools/generate.py`:
```python


def parts(lay):
    m = {x["name"]: x for x in lay["members"]}
    ends = lambda name: min(2, m[name]["n"])
    bays = lay["bays"]
    out = []

```
**with:**
```python


def core_arg(lay, name, key="core"):
    if lay.get("vslot") is None:
        return ""
    mem = next(x for x in lay["members"] if x["name"] == name)
    if mem["core"] in (window.VSLOT, window.VSLOT_PAIR):
        return f', {key}="vslot"'
    return f', {key}="alu20"' if mem["profile"] == "sash_rebate" else ""


def parts(lay):
    m = {x["name"]: x for x in lay["members"]}
    ends = lambda name: min(2, m[name]["n"])
    bays = lay["bays"]
    ca = lambda name, key="core": core_arg(lay, name, key)
    out = []

```

**Replace** in `tools/generate.py`:
```python
        f = "".join(f", {k}={str(v).lower()}" for k, v in flags.items())
        s = m[name]["seg"]
        out.append(part(pid, "frame_segment", f'"{profile}", {s}, "{pid}"{f}', qty, role, s))

    seg("H", "head", "sash_rebate", bays * m["head"]["n"], bosses=lay["has_screen"])
```
**with:**
```python
        f = "".join(f", {k}={str(v).lower()}" for k, v in flags.items())
        s = m[name]["seg"]
        out.append(part(pid, "frame_segment", f'"{profile}", {s}, "{pid}"{f}{ca(name)}', qty, role, s))

    seg("H", "head", "sash_rebate", bays * m["head"]["n"], bosses=lay["has_screen"])
```

**Replace** in `tools/generate.py`:
```python
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
```
**with:**
```python
    n_nose, s_nose = split(lay["w"] - 2 * NOSE_END, D["JOINT_GAP"], lay["max_seg"])
    out += [
        part("CH", "corner_block", f'"sash_rebate", "sash_rebate", "CH"{ca("head", "core_a")}{ca("jamb_upper", "core_b")}', 2),
        part("CSL", "corner_block", f'"sill", "glazing", "CSL"{ca("sill", "core_a")}{ca("jamb_lower", "core_b")}', 1),
        part("CSR", "corner_block",
             f'"sill", "glazing", "CSR", mirrored=true{ca("sill", "core_a")}{ca("jamb_lower", "core_b")}', 1),
        part("CS", "corner_block",
             f'"sash", "sash", "CS"{ca("sash_horizontal", "core_a")}{ca("sash_vertical", "core_b")}', 4 * bays),
        part("CN", "corner_block", '"screen", "screen", "CN"', 4 * bays, "interior"),
        part("JN", "jamb_node", f'"JN"{ca("jamb_lower")}', 2),
        part("TSL", "transom_shoe", f'"TSL", mirrored=true{ca("transom")}', 1),
        part("TSR", "transom_shoe", f'"TSR"{ca("transom")}', 1),
    ]
    if bays > 1:
        out += [
            part("SN", "frame_node", f'"sill", "SN"{ca("sill")}', bays - 1),
            part("HN", "frame_node", f'"sash_rebate", "HN"{ca("head")}', bays - 1),
            part("TX", "cross_node", f'"TX"{ca("transom")}', bays - 1),
            part("MSL", "mullion_shoe", f'"mullion_glazing", "MSL"{ca("mullion_lower")}', 2 * (bays - 1)),
            part("MST", "mullion_shoe", f'"mullion_sash", "MST"{ca("mullion_upper")}', bays - 1),
            part("MSH", "mullion_shoe", f'"mullion_sash", "MSH", head=true{ca("mullion_upper")}', bays - 1),
        ]
    out += [
```

- [ ] **Step 4: Run the tests to see them pass**

Run: `cd ~/diy-window/tools && python3 -m unittest discover -p 'test_*.py' 2>&1 | grep -E '^(Ran|OK|FAILED)'`
Expected: `Ran 338 tests`, `OK`.

- [ ] **Step 5: Checkpoint**

Run the compatibility check. Expected: `BYTE-IDENTICAL`.

---

### Task 4: Render the V-slot windows and check the sections by eye

**Files:**
- Create: `cad/tests/vslot_sheet.scad` (kept: it isn't a `_test`, so `box.sh test` skips it)
- Temporary: `params/zz-vbench.json`, `params/zz-vhome.json`, `params/zz-v2bay.json`, `cad/stl/zz-*`, `.vslot-review/` (deleted in Step 5 and Task 8)

- [ ] **Step 1: Make the temporary V-slot windows**

Run:
```bash
cd ~/diy-window && python3 - <<'EOF'
import json
for src, dst in (("bench-600", "zz-vbench"), ("home-1800x1500", "zz-vhome"), ("home-1800x1500-2bay", "zz-v2bay")):
    p = json.load(open(f"params/{src}.json")) | {"name": dst, "core": "vslot"}
    json.dump(p, open(f"params/{dst}.json", "w"), indent=2)
EOF
python3 tools/generate.py params/zz-vhome.json | tail -1
```
Expected: `ok       V-slot 2020: 8 pieces of 1000 mm; joins: head 1, sill 1; steel transom: 1696 mm is longer than the 1000 mm V-slot pieces, and a V-slot pair would deflect 48.2 mm (limit 9.5 mm); alu20 sash_horizontal: 1615 mm is longer than the 1000 mm V-slot pieces`

- [ ] **Step 2: Render them, one at a time**

The bench window is all V-slot. The home window renders the parts whose geometry changes, and the 2-bay window adds the nodes and shoes.
```bash
cd ~/diy-window && cad/box.sh render zz-vbench | tail -1
cd ~/diy-window && cad/box.sh render zz-vhome H JU CH S SW JL CSL CSR JN SV CS SH | tail -1
cd ~/diy-window && cad/box.sh render zz-v2bay SN HN MSL MST MSH ML MU CS SBE SV TX | tail -1
```
Expected: `37/37 parts ok`, `12/12 parts ok`, `11/11 parts ok`.

- [ ] **Step 3: Draw the section views**

**Create** `cad/tests/vslot_sheet.scad`:
```openscad
// cad/tests/vslot_sheet.scad
use <../profile.scad>
use <../lib/segment.scad>
include <../generated/dims.scad>

V = "vslot";

module slot2d() {
    m = VSLOT_MOUTH / 2;
    n = VSLOT_NECK / 2;
    v = m - n;
    polygon([[-m, 0.01], [m, 0.01], [n, -v], [n, -VSLOT_LIP], [5.5, -VSLOT_LIP], [5.5, -VSLOT_FLOOR + 2],
             [3, -VSLOT_FLOOR], [-3, -VSLOT_FLOOR], [-5.5, -VSLOT_FLOOR + 2], [-5.5, -VSLOT_LIP], [-n, -VSLOT_LIP], [-n, -v]]);
}

module vslot2020(c) {
    translate(c) difference() {
        square(20, center = true);
        for (a = [0, 90, 180, 270]) rotate(a) translate([0, 10]) slot2d();
        circle(d = 4.2, $fn = 24);
    }
}

function centre(r) = [(r[0] + r[2]) / 2, (r[1] + r[3]) / 2];

sel = 0;

module edges(a, b, w) {
    for (y = [a - 2.1, a + 2.1]) if (w) translate([b[0], y - 0.12]) square([b[1] - b[0], 0.24]);
}

module band_h(y, x0, x1) { for (e = [y - TUBE_SCREW_D / 2, y + TUBE_SCREW_D / 2]) translate([x0, e - 0.12]) square([x1 - x0, 0.24]); }

module band_v(x, y0, y1, d) { for (e = [x - d / 2, x + d / 2]) translate([e - 0.12, y0]) square([0.24, y1 - y0]); }

module show(name, tubes) {
    difference() {
        union() {
            profile(name, core = V);
            for (c = tubes) vslot2020(c);
        }
        children();
    }
}

if (sel == 0) show("sash_rebate", [centre(pocket_rect("sash_rebate", V))]) {
    for (y = [stay_c_min(), stay_c_max()]) band_h(y, 0, FRAME_BODY + 2);
    band_v(screw_x("sash_rebate", V), pocket_rect("sash_rebate", V)[3] - 6, DEPTH + 1, VSLOT_SCREW_D);
}
if (sel == 1) show("sash", [centre(pocket_rect("sash"))]) {
    for (y = [stay_c_min(), stay_c_max()]) band_h(y, -FLANGE_L - 1, 30);
    band_v(screw_x("sash", V), pocket_rect("sash")[3] - 6, LIP_Y1 + 1, VSLOT_SCREW_D);
}
r = pocket_rect("transom");
if (sel == 2) show("transom", [for (y = [r[1] + TUBE_CLEAR + 10, r[3] - TUBE_CLEAR - 10]) [(r[0] + r[2]) / 2, y]])
    band_v(screw_x("transom", V), r[3] - 8, DEPTH + 1, TUBE_SCREW_D);
m = pocket_rect("mullion_sash");
if (sel == 3) show("mullion_sash", [for (y = [m[1] + TUBE_CLEAR + 10, m[3] - TUBE_CLEAR - 10]) [(m[0] + m[2]) / 2, y]]) {
    for (y = [stay_c_min(), stay_c_max()]) band_h(y, -1, MULLION_W + 1);
    band_v(screw_x("mullion_sash", V), m[3] - 6, DEPTH + 1, VSLOT_SCREW_D);
}
```

Run:
```bash
cd ~/diy-window && mkdir -p .vslot-review && for i in 0 1 2 3; do cad/box.sh png tests/vslot_sheet.scad ~/diy-window/.vslot-review/vslot-$i.png -Dsel=$i --camera=0,0,0,0,0,0,200 --viewall --autocenter --projection=ortho; done; ls .vslot-review
```
Expected: `vslot-0.png  vslot-1.png  vslot-2.png  vslot-3.png`.

- [ ] **Step 4: Check the views by eye**

Each view shows a profile with the V-slot outline in its pocket; y points to the room. The pairs of thin lines are the screw edges.
- **`vslot-0` (upper jamb, `sash_rebate`):**
  - **Pocket:** it sits 3 mm lower (further out) than in `profiles_sheet`. The chamber beside it ends level with the pocket top, with a wall to the chamber above.
  - **Stay screws:** the two horizontal pairs (35 and 35.5 mm) cross the V-slot's right face in its upper corner block, above the groove mouth.
  - **M5:** the vertical pair falls into the top slot.
- **`vslot-1` (sash):** the stay pairs cross the left face in the top-left corner block. The upper edge line runs just above the V-slot, as the plain tube's does today. The M5 falls into the top slot.
- **`vslot-2` (transom pair):** the vertical pair at x = 41.25 enters the room-side 2020's top-right corner block, clear of the magnet channel at the top left.
- **`vslot-3` (upper mullion pair):** the stay pairs cross both side faces of the room-side (upper) 2020, above the joint between the two bars. The M5 falls into its top slot.

Stop for review if any line lands in a groove mouth or a slot (other than the M5 lines).

- [ ] **Step 5: Clean up**

Run: `cd ~/diy-window && rm -f params/zz-v*.json && rm -rf cad/stl/zz-v* && ls params cad/stl`
Expected: `params`: `bench-600.json  home-1800x1500-2bay.json  home-1800x1500.json  my-window.json`, and `cad/stl`: `bench-600  home-1800x1500  home-1800x1500-2bay  my-window`. (`my-window` is the owner's; leave it.)

---

### Task 5: BOM by core (`bom/build_bom.py`)

**Files:**
- Modify: `bom/build_bom.py`
- Test: `tools/test_bom.py` (append)

**Interfaces:**
- Consumes: member cores, `lay["vslot"]`, `window.m5_length`, `window.SAW_KERF` (Task 1), and the part list (Task 3).
- Produces:
  - `build_bom.SCREW_HOSTS` (part ID → the members its tube screws go into);
  - `build_bom.screw_kind(member) -> ("alu",) | ("tek",) | ("m5", L) | ("shoulder",)`;
  - `build_bom.tube_screws(lay, qty_by_id) -> {kind: count}`.

  With no `core` key, the counts equal the old rule.

- [ ] **Step 1: Write the failing tests**

**Replace** in `tools/test_bom.py`:
```python


if __name__ == "__main__":
    unittest.main()
```
**with:**
```python


def vslotLoad(name, **changes):
    return window.layout({**json.loads((ROOT / "params" / f"{name}.json").read_text()), "core": "vslot", **changes})


class VslotBomTest(unittest.TestCase):
    def qty(self, lay):
        return {i["item"]: i["qty"] for i in build_bom.hardware(lay, generate.parts(lay))}

    def screws(self, lay):
        return sum(n for n in build_bom.tube_screws(lay, {p["id"]: p["qty"] for p in generate.parts(lay)}).values())

    def testTubeScrewTotalIsUnchanged(self):
        for name in ("bench-600", "home-1800x1500", "home-1800x1500-2bay"):
            self.assertEqual(self.screws(vslotLoad(name)), self.screws(load(name)), name)

    def testDefaultCountsMatchTheOldRule(self):
        q = self.qty(load("home-1800x1500"))
        self.assertEqual(q["Self-tapping screw 8g x 30 stainless, countersunk (aluminium tube screws: frame, sash, corners, nodes)"], 62)
        self.assertEqual(q["Tek screw 8g x 25, 410 stainless, countersunk (steel transom tube: T, TE, shoes)"], 9)

    def testHomeScrewLines(self):
        q = self.qty(vslotLoad("home-1800x1500"))
        self.assertEqual(q["M5 x 25 countersunk machine screw, stainless (V-slot tube screws, one T-nut each)"], 36)
        self.assertEqual(q["M5 x 20 countersunk machine screw, stainless (V-slot tube screws, one T-nut each)"], 8)
        self.assertEqual(q["M5 slide-in T-nut for 20-series V-slot, 6 mm slot (V-slot tube screws)"], 44)
        self.assertEqual(q["Self-tapping screw 8g x 30 stainless, countersunk (aluminium tube screws: frame, sash, corners, nodes)"], 18)
        self.assertEqual(q["Tek screw 8g x 25, 410 stainless, countersunk (steel tubes: transom)"], 9)
        self.assertEqual(q["V-slot 2020, 4-slot, 1000 mm pieces (cut plan in the BOM)"], 8)
        self.assertEqual(q["Tube alu20 (total length; buy in 1 m/3 m stock)"], 3.23)

    def testBenchHasShoulderScrewsAndNoEmptyLines(self):
        q = self.qty(vslotLoad("bench-600"))
        self.assertEqual(q["Self-tapping screw 8g x 20 stainless, countersunk (V-slot transom pair: T, TE, TX, shoes; 3.5 mm pilot)"], 4)
        self.assertFalse([k for k, v in q.items() if v == 0])
        self.assertFalse([k for k in q if k.startswith("Tube alu20") or k.startswith("Tek screw 8g x 25")])

    def testVslotMullionStaysTakeSelfTappers(self):
        q = self.qty(vslotLoad("home-1800x1500-2bay"))
        self.assertEqual(q["Self-tapping screw 8g x 16 stainless, countersunk (friction-stay tracks to upper mullions, 3.5 mm pilot; "
                           "match the stay's holes)"], 8)

    def testMarkdownHasThePlanJoinsAndFallbacks(self):
        lay = vslotLoad("home-1800x1500")
        parts = generate.parts(lay)
        with tempfile.TemporaryDirectory() as d:
            build_bom.write("vhome", lay, parts, build_bom.hardware(lay, parts), [], d)
            text = (pathlib.Path(d) / "vhome.md").read_text()
        for needle in ("## V-slot cut plan", "8 pieces of 1000 mm V-slot 2020, with 2 mm per saw cut.", "| 1 | jamb_lower 943 | 57 |",
                       "| 7 | jamb_upper 475, jamb_upper 475 | 48 |", "- head: 919.8 mm, inside segment 4",
                       "## Standard tubes in this V-slot window", "- alu20 sash_horizontal: 1615 mm is longer than the 1000 mm V-slot pieces"):
            self.assertIn(needle, text)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the tests to see them fail**

Run: `cd ~/diy-window/tools && python3 -m unittest test_bom 2>&1 | grep -E '^(Ran|OK|FAILED)'`
Expected: `Ran 66 tests`, `FAILED (failures=1, errors=4)`. The errors are `AttributeError: module 'build_bom' has no attribute 'tube_screws'` and missing BOM lines.

- [ ] **Step 3: Count the screws by core, and add the V-slot lines**

**Replace** in `bom/build_bom.py`:
```python
SCREEN_ONLY = "screen-only"
MULLION_ONLY = "mullion-only"


```
**with:**
```python
SCREEN_ONLY = "screen-only"
MULLION_ONLY = "mullion-only"
SCREW_HOSTS = {
    "H": ("head",), "S": ("sill",), "SW": ("sill",), "JL": ("jamb_lower",), "JU": ("jamb_upper",),
    "T": ("transom",), "TE": ("transom",), "ML": ("mullion_lower",), "MU": ("mullion_upper",),
    "SH": ("sash_horizontal",), "SB": ("sash_horizontal",), "SBE": ("sash_horizontal",), "SV": ("sash_vertical",),
    "CH": ("head", "jamb_upper"), "CSL": ("sill", "jamb_lower"), "CSR": ("sill", "jamb_lower"),
    "CS": ("sash_horizontal", "sash_vertical"), "JN": ("jamb_lower",), "SN": ("sill",), "HN": ("head",),
    "TX": ("transom",), "TSL": ("transom",), "TSR": ("transom",),
    "MSL": ("mullion_lower",), "MST": ("mullion_upper",), "MSH": ("mullion_upper",),
}


```

**Replace** in `bom/build_bom.py`:
```python
            "sash": (D["SASH_BODY"], D["LIP_Y1"] - D["SASH_Y0"])}.get(profile, (D["FRAME_BODY"], D["DEPTH"]))
    return 2 * (w + d - 4 * inset)


```
**with:**
```python
            "sash": (D["SASH_BODY"], D["LIP_Y1"] - D["SASH_Y0"])}.get(profile, (D["FRAME_BODY"], D["DEPTH"]))
    return 2 * (w + d - 4 * inset)


def screw_kind(mem):
    if mem["core"] == window.VSLOT_PAIR and mem["profile"] == "transom":
        return ("shoulder",)
    if mem["core"] in (window.VSLOT, window.VSLOT_PAIR):
        return ("m5", window.m5_length(mem["profile"]))
    return ("tek",) if mem["core"].startswith("steel") else ("alu",)


def tube_screws(lay, q):
    mem = {m["name"]: m for m in lay["members"]}
    count = {}
    for pid, hosts in SCREW_HOSTS.items():
        for name in hosts:
            if q.get(pid) and name in mem:
                key = screw_kind(mem[name])
                count[key] = count.get(key, 0) + q[pid]
    return count


```

**Replace** in `bom/build_bom.py`:
```python
    loop_extra = 8 * (D["SASH_GAP"] - D["FIN_L"] / 2 + D["LIP_L"] / 2)
    steel = "steel transom tube: T, TE, shoes" if bays == 1 else "steel transom and mullion tubes: T, TE, TX, ML, MU, shoes"
    stay_desc = f"{lay['stay']} mm" if lay["stay"] is not None else "no stay fits (see check)"
    items = [
        ("Fixings", "Timber screw 10g x 75, stainless or galvanised (frame fixings)", fixings, "pcs"),
        ("Fixings", "Self-tapping screw 8g x 30 stainless, countersunk (aluminium tube screws: frame, sash, corners, nodes)",
         total(FRAME_SEGMENTS - TRANSOM_PARTS) + 2 * total(FRAME_CORNERS) + total({"JN", "SN", "HN"}), "pcs"),
        ("Fixings", f"Tek screw 8g x 25, 410 stainless, countersunk ({steel})",
         total(TRANSOM_PARTS | MULLION_STEEL), "pcs"),
        ("Fixings", "Self-tapping screw 8g x 12 stainless, countersunk (screen tube screws)", screen_screws, "pcs",
         SCREEN_ONLY),
```
**with:**
```python
    loop_extra = 8 * (D["SASH_GAP"] - D["FIN_L"] / 2 + D["LIP_L"] / 2)
    steel = "steel transom tube: T, TE, shoes" if bays == 1 else "steel transom and mullion tubes: T, TE, TX, ML, MU, shoes"
    vslot = lay.get("vslot")
    screws = tube_screws(lay, q)
    if vslot is not None:
        steel = "steel tubes: " + ", ".join(m["name"] for m in lay["members"] if (m["core"] or "").startswith("steel"))
    upper_vslot = any(m["name"] == "mullion_upper" and m["core"] == window.VSLOT_PAIR for m in lay["members"])
    stay_desc = f"{lay['stay']} mm" if lay["stay"] is not None else "no stay fits (see check)"
    items = [
        ("Fixings", "Timber screw 10g x 75, stainless or galvanised (frame fixings)", fixings, "pcs"),
        ("Fixings", "Self-tapping screw 8g x 30 stainless, countersunk (aluminium tube screws: frame, sash, corners, nodes)",
         screws.get(("alu",), 0), "pcs"),
        ("Fixings", f"Tek screw 8g x 25, 410 stainless, countersunk ({steel})", screws.get(("tek",), 0), "pcs"),
        *[("Fixings", f"M5 x {k[1]} countersunk machine screw, stainless (V-slot tube screws, one T-nut each)", n, "pcs")
          for k, n in sorted(screws.items()) if k[0] == "m5"],
        *([("Fixings", "M5 slide-in T-nut for 20-series V-slot, 6 mm slot (V-slot tube screws)",
            sum(n for k, n in screws.items() if k[0] == "m5"), "pcs")] if vslot is not None else []),
        *([("Fixings", "Self-tapping screw 8g x 20 stainless, countersunk (V-slot transom pair: T, TE, TX, shoes; 3.5 mm pilot)",
            screws[("shoulder",)], "pcs")] if ("shoulder",) in screws else []),
        ("Fixings", "Self-tapping screw 8g x 12 stainless, countersunk (screen tube screws)", screen_screws, "pcs",
         SCREEN_ONLY),
```

**Replace** in `bom/build_bom.py`:
```python
        ("Hardware", "Friction-stay screw 8g x 25 stainless, countersunk (tracks to upper jambs; match the stay's holes)",
         2 * STAY_TRACK_SCREWS, "pcs"),
        ("Hardware", "Tek screw 8g x 16, 410 stainless, countersunk (friction-stay tracks to upper mullions; match the stay's holes)",
         2 * (bays - 1) * STAY_TRACK_SCREWS, "pcs", MULLION_ONLY),
        ("Hardware", "Friction-stay screw 8g x 16 stainless, countersunk (arms to sash sides; match the stay's holes)",
```
**with:**
```python
        ("Hardware", "Friction-stay screw 8g x 25 stainless, countersunk (tracks to upper jambs; match the stay's holes)",
         2 * STAY_TRACK_SCREWS, "pcs"),
        ("Hardware", "Self-tapping screw 8g x 16 stainless, countersunk (friction-stay tracks to upper mullions, 3.5 mm pilot; "
                     "match the stay's holes)" if upper_vslot else
                     "Tek screw 8g x 16, 410 stainless, countersunk (friction-stay tracks to upper mullions; match the stay's holes)",
         2 * (bays - 1) * STAY_TRACK_SCREWS, "pcs", MULLION_ONLY),
        ("Hardware", "Friction-stay screw 8g x 16 stainless, countersunk (arms to sash sides; match the stay's holes)",
```

**Replace** in `bom/build_bom.py`:
```python
    if bays == 1:
        items = [it for it in items if MULLION_ONLY not in it[4:]]
    by_core = {}
    for t in lay["tubes"]:
        by_core[t["core"]] = by_core.get(t["core"], 0) + t["length"] * t["qty"]
    for core, mm in sorted(by_core.items()):
        items.append(("Tube", f"Tube {core} (total length; buy in 1 m/3 m stock)", m(mm), "m"))
```
**with:**
```python
    if bays == 1:
        items = [it for it in items if MULLION_ONLY not in it[4:]]
    if vslot is not None:
        items = [it for it in items if it[2] != 0]
        items.append(("Tube", f"V-slot 2020, 4-slot, {vslot['stock']:g} mm pieces (cut plan in the BOM)", len(vslot["plan"]), "pcs"))
    by_core = {}
    for t in lay["tubes"]:
        if t["core"] != window.VSLOT:
            by_core[t["core"]] = by_core.get(t["core"], 0) + t["length"] * t["qty"]
    for core, mm in sorted(by_core.items()):
        items.append(("Tube", f"Tube {core} (total length; buy in 1 m/3 m stock)", m(mm), "m"))
```

**Replace** in `bom/build_bom.py`:
```python
              "| Pane | Glazing | Width (mm) | Height (mm) | Qty |", "|---|---|---|---|---|"]
    lines += [f"| {pane} | {lay['params']['glazing']} | {gw} | {gh} | {lay['bays']} |" for pane, (gw, gh) in lay["glass"].items()]
    if lay["bays"] > 1:
        centres = ", ".join(f"{c:g}" for c in (round(c, 1) for c in lay["mullions"]))
```
**with:**
```python
              "| Pane | Glazing | Width (mm) | Height (mm) | Qty |", "|---|---|---|---|---|"]
    lines += [f"| {pane} | {lay['params']['glazing']} | {gw} | {gh} | {lay['bays']} |" for pane, (gw, gh) in lay["glass"].items()]
    vslot = lay.get("vslot")
    if vslot is not None:
        lines += ["", "## V-slot cut plan", "",
                  f"{len(vslot['plan'])} pieces of {vslot['stock']:g} mm V-slot 2020, with {window.SAW_KERF:g} mm per saw cut.", "",
                  "| Piece | Cuts (mm) | Offcut (mm) |", "|---|---|---|"]
        lines += [f"| {i} | {', '.join(f'{label} {length:g}' for label, length in b['cuts'])} | {b['offcut']:g} |"
                  for i, b in enumerate(vslot["plan"], 1)]
        joined = {k: v for k, v in vslot["joins"].items() if v}
        if joined:
            lines += ["", "## V-slot joins", "",
                      "Pieces butt together inside a printed segment, a quarter of the way along it, clear of its T-nut. "
                      "Measure from the left end seen from outside (jambs: from the bottom); the segments are symmetric, "
                      "so either end works.", ""]
            lines += [f"- {k}: " + "; ".join(f"{j['at']:g} mm, inside segment {j['segment']}" for j in v) for k, v in joined.items()]
        if vslot["fallbacks"]:
            lines += ["", "## Standard tubes in this V-slot window", ""] + [f"- {f}" for f in vslot["fallbacks"]]
    if lay["bays"] > 1:
        centres = ", ".join(f"{c:g}" for c in (round(c, 1) for c in lay["mullions"]))
```

- [ ] **Step 4: Run the tests to see them pass**

Run: `cd ~/diy-window/tools && python3 -m unittest discover -p 'test_*.py' 2>&1 | grep -E '^(Ran|OK|FAILED)'`
Expected: `Ran 344 tests`, `OK`.

- [ ] **Step 5: Checkpoint**

Run the compatibility check. Expected: `BYTE-IDENTICAL`.

---

### Task 6: The configurator (`web/api.py`, `web/static/`)

**Files:**
- Modify: `web/api.py`, `web/static/index.html`, `web/static/app.js`, `web/tests/ui_shots.py`
- Test: `web/tests/test_api.py` (append)

**Interfaces:**
- Consumes: `window.VSLOT_STOCK_RANGE`, `lay["vslot"]` and the `core` check (Task 1).
- Produces:
  - `api.OPTIONAL` gains `"core"` and `"vslot_stock"`, and `api.SUMMARY_KEYS` gains `"vslot"`.
  - Validation messages: `{"core": "vslot, or leave it out for standard tubes"}`, `{"vslot_stock": "300-6000 mm"}`, `{"vslot_stock": "only with core vslot"}`.
  - Page fields `core` (select) and `vslot_stock`, a `#vslot` block, a `#core-note`, and the `core: "Tube cores"` badge.

- [ ] **Step 1: Write the failing tests**

**Replace** in `web/tests/test_api.py`:
```python
if __name__ == "__main__":
    unittest.main()
```
**with:**
```python
if __name__ == "__main__":
    unittest.main()


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
```

- [ ] **Step 2: Run the tests to see them fail**

Run: `cd ~/diy-window && python3 -m unittest web.tests.test_api 2>&1 | grep -E '^(Ran|OK|FAILED)'`
Expected: `Ran 66 tests`, `FAILED (failures=6, errors=1)`. `core` and `vslot_stock` are still unknown fields.

- [ ] **Step 3: Validate and summarise the keys**

**Replace** in `web/api.py`:
```python
DEFAULTS = {"name": "my-window", "opening_w": 1800, "opening_h": 1500, "fix_gap": 8, "awning_h": 450,
            "glazing": "igu", "tier": 3, "screen": True, "bed": [256, 256, 256]}
OPTIONAL = ("max_pane", "bays", "acrylic_t", "acrylic_gap")
PAGE_MAX_PANE = [1200, 900]
RANGES = {"opening_w": (300, 3000), "opening_h": (300, 3000), "fix_gap": (0, 20)}
```
**with:**
```python
DEFAULTS = {"name": "my-window", "opening_w": 1800, "opening_h": 1500, "fix_gap": 8, "awning_h": 450,
            "glazing": "igu", "tier": 3, "screen": True, "bed": [256, 256, 256]}
OPTIONAL = ("max_pane", "bays", "acrylic_t", "acrylic_gap", "core", "vslot_stock")
PAGE_MAX_PANE = [1200, 900]
RANGES = {"opening_w": (300, 3000), "opening_h": (300, 3000), "fix_gap": (0, 20)}
```

**Replace** in `web/api.py`:
```python
}
SUMMARY_KEYS = ("w", "h", "transom_c", "sash", "screen", "glass", "stay", "sash_kg", "keeper_dz", "bed", "max_seg",
                "has_screen", "members", "tubes", "bays", "auto_bays", "pitch", "mullions", "sandwich")


```
**with:**
```python
}
SUMMARY_KEYS = ("w", "h", "transom_c", "sash", "screen", "glass", "stay", "sash_kg", "keeper_dz", "bed", "max_seg",
                "has_screen", "members", "tubes", "bays", "auto_bays", "pitch", "mullions", "sandwich", "vslot")


```

**Replace** in `web/api.py`:
```python
        if key in params and not (is_number(params[key]) and lo <= params[key] <= hi):
            errors[key] = f"{lo}-{hi} mm"
    return params, errors

```
**with:**
```python
        if key in params and not (is_number(params[key]) and lo <= params[key] <= hi):
            errors[key] = f"{lo}-{hi} mm"
    if "core" in params and params["core"] != "vslot":
        errors["core"] = "vslot, or leave it out for standard tubes"
    if "vslot_stock" in params:
        lo, hi = window.VSLOT_STOCK_RANGE
        if "core" not in params:
            errors["vslot_stock"] = "only with core vslot"
        elif not (is_number(params["vslot_stock"]) and lo <= params["vslot_stock"] <= hi):
            errors["vslot_stock"] = f"{lo}-{hi} mm"
    return params, errors

```

- [ ] **Step 4: The Tube cores fieldset**

**Replace** in `web/static/index.html`:
```html
      </label>
      <label class="check"><input name="screen" type="checkbox"> Insect screen</label>
    </fieldset>
    <fieldset>
```
**with:**
```html
      </label>
      <label class="check"><input name="screen" type="checkbox"> Insect screen</label>
    </fieldset>
    <fieldset>
      <legend>Tube cores</legend>
      <label class="field">Core
        <select name="core">
          <option value="">Standard tubes (20x20 aluminium, 40x20 steel transom)</option>
          <option value="vslot">V-slot 2020 (T-nuts)</option>
        </select>
        <small class="err" data-for="core"></small>
      </label>
      <div class="hidden" id="vslot">
        <label class="field">V-slot piece length <em>mm, 300-6000</em><input name="vslot_stock" type="number" step="1" min="300" max="6000"><small class="err" data-for="vslot_stock"></small></label>
        <p class="note" id="core-note"></p>
      </div>
    </fieldset>
    <fieldset>
```

- [ ] **Step 5: Read, fill and explain the fields**

**Replace** in `web/static/app.js`:
```javascript
const SVG = "http://www.w3.org/2000/svg";
const CHECKS = { transom_deflection: "Transom deflection", sash_weight: "Friction stay", segment_length: "Segment length",
                 cam_keeper: "Cam / keeper", pane_fit: "Pane fit", mullion_deflection: "Mullion deflection", bed_fit: "Bed fit" };
const FIELDS = ["name", "opening_w", "opening_h", "fix_gap", "awning_h", "glazing", "tier"];
const SANDWICH = { t: 4, gap: 16 };
const state = { presets: [], maxPane: [1200, 900], preview: null, job: null, jobRev: null, selected: new Set(), seq: 0,
                timer: 0, poll: 0, pollFailures: 0, online: true, viewing: null, view: null, viewSeq: 0 };
```
**with:**
```javascript
const SVG = "http://www.w3.org/2000/svg";
const CHECKS = { transom_deflection: "Transom deflection", sash_weight: "Friction stay", segment_length: "Segment length",
                 cam_keeper: "Cam / keeper", pane_fit: "Pane fit", mullion_deflection: "Mullion deflection", core: "Tube cores",
                 bed_fit: "Bed fit" };
const FIELDS = ["name", "opening_w", "opening_h", "fix_gap", "awning_h", "glazing", "tier"];
const SANDWICH = { t: 4, gap: 16 };
const VSLOT_STOCK = 1000;
const state = { presets: [], maxPane: [1200, 900], preview: null, job: null, jobRev: null, selected: new Set(), seq: 0,
                timer: 0, poll: 0, pollFailures: 0, online: true, viewing: null, view: null, viewSeq: 0 };
```

**Replace** in `web/static/app.js`:
```javascript
    if (gap !== null && gap !== SANDWICH.gap) out.acrylic_gap = gap;
  }
  return out;
}

```
**with:**
```javascript
    if (gap !== null && gap !== SANDWICH.gap) out.acrylic_gap = gap;
  }
  if (form.elements.core.value === "vslot") {
    out.core = "vslot";
    const stock = num("vslot_stock");
    if (stock !== null && stock !== VSLOT_STOCK) out.vslot_stock = stock;
  }
  return out;
}

function syncCore() {
  $("#vslot").classList.toggle("hidden", form.elements.core.value !== "vslot");
}

```

**Replace** in `web/static/app.js`:
```javascript
  form.elements.acrylic_gap.value = p.acrylic_gap === undefined ? SANDWICH.gap : p.acrylic_gap;
  syncSandwich();
  const preset = state.presets.find((x) => x.bed.join() === p.bed.join());
  form.elements.preset.value = preset ? preset.key : "custom";
```
**with:**
```javascript
  form.elements.acrylic_gap.value = p.acrylic_gap === undefined ? SANDWICH.gap : p.acrylic_gap;
  syncSandwich();
  form.elements.core.value = p.core || "";
  form.elements.vslot_stock.value = p.vslot_stock === undefined ? VSLOT_STOCK : p.vslot_stock;
  syncCore();
  const preset = state.presets.find((x) => x.bed.join() === p.bed.join());
  form.elements.preset.value = preset ? preset.key : "custom";
```

**Replace** in `web/static/app.js`:
```javascript
  if (q.has("acrylic_t")) p.acrylic_t = Number(q.get("acrylic_t"));
  if (q.has("acrylic_gap")) p.acrylic_gap = Number(q.get("acrylic_gap"));
  return p;
}
```
**with:**
```javascript
  if (q.has("acrylic_t")) p.acrylic_t = Number(q.get("acrylic_t"));
  if (q.has("acrylic_gap")) p.acrylic_gap = Number(q.get("acrylic_gap"));
  if (q.has("core")) p.core = q.get("core");
  if (q.has("vslot_stock")) p.vslot_stock = Number(q.get("vslot_stock"));
  return p;
}
```

**Replace** in `web/static/app.js`:
```javascript

function showChecks(checks) {
  $("#badges").replaceChildren(...checks.map((c) => {
    const b = document.createElement("span");
```
**with:**
```javascript

function showChecks(checks) {
  const core = checks.find((c) => c.name === "core");
  $("#core-note").textContent = core ? core.msg : "";
  $("#badges").replaceChildren(...checks.map((c) => {
    const b = document.createElement("span");
```

**Replace** in `web/static/app.js`:
```javascript
    if (e.target.name === "max_none") ["max_a", "max_b"].forEach((k) => { form.elements[k].disabled = e.target.checked; });
    if (e.target.name === "glazing") syncSandwich();
    schedulePreview();
  });
```
**with:**
```javascript
    if (e.target.name === "max_none") ["max_a", "max_b"].forEach((k) => { form.elements[k].disabled = e.target.checked; });
    if (e.target.name === "glazing") syncSandwich();
    if (e.target.name === "core") syncCore();
    schedulePreview();
  });
```

- [ ] **Step 6: Run the web tests**

Run: `cd ~/diy-window && python3 -m unittest discover -s web/tests -p 'test_*.py' 2>&1 | grep -E '^(Ran|OK|FAILED)'`
Expected: `Ran 165 tests`, `OK`.

- [ ] **Step 7: Screenshot, and check it by eye**

**Replace** in `web/tests/ui_shots.py`:
```python
            shot(real + query(params("home-1800x1500-2bay"), view="assembled"), a.out / "9-viewer-two-bays.png", profile, 12000)
            shot(real + query(params("home-1800x1500-2bay"), max_pane="800,800"), a.out / "10-too-tall.png", profile)
    finally:
        for s in servers:
```
**with:**
```python
            shot(real + query(params("home-1800x1500-2bay"), view="assembled"), a.out / "9-viewer-two-bays.png", profile, 12000)
            shot(real + query(params("home-1800x1500-2bay"), max_pane="800,800"), a.out / "10-too-tall.png", profile)
            shot(real + query(params("home-1800x1500"), core="vslot"), a.out / "11-vslot.png", profile)
    finally:
        for s in servers:
```

Run: `cd ~/diy-window && python3 web/tests/ui_shots.py .vslot-review/ui | tail -1`
Expected: `11-vslot.png: http://127.0.0.1:8781/?name=home-1800x1500&…&core=vslot`.

Look at `.vslot-review/ui/11-vslot.png`:
- **Fieldset:** the Tube cores fieldset shows "V-slot 2020 (T-nuts)", a piece length of 1000, and the note "V-slot 2020: 8 pieces of 1000 mm; joins: head 1, sill 1; steel transom: …".
- **Badge:** the badges include a green "Tube cores".

`1-valid.png` still shows "Standard tubes…" with no piece-length field.

---

### Task 7: Guides, manual, specs, README and the guide PDF

**Files:**
- Modify: `docs/build-guide.md`, `docs/install-guide.md`, `docs/test-log.md`, `docs/user-manual.md`, `README.md`, `web/README.md`, `docs/specs/2026-10-07-diy-window-design.md`, `docs/specs/2026-10-10-vslot-core-design.md`, `pdf/build_deck.py`

- [ ] **Step 1: Build guide: tube screws, cutting, and a new section 8**

**Replace** in `docs/build-guide.md`:
```markdown
  - Aluminium tubes: 8g × 30 stainless countersunk self-tappers, with a 3.2 mm pilot drilled through the printed hole into the tube.
  - Steel transom tube: 8g × 25 tek (self-drilling) screws in 410 stainless. Or drill a 3.5–3.8 mm pilot through the 1.6 mm steel wall and use a stainless self-tapper.

  Stop when the head is flush, so the screw doesn't strip the plastic.

## 1. Prepare
1. Cut the tubes to the cut list with a hacksaw or drop saw, never longer than the list. Each length leaves 1.5 mm clear at every corner socket floor for print shrinkage. Dry-fit each member on its tube with the shims in, and trim the tube if any joint will not close onto its shims. Deburr and wipe with isopropyl.
2. Press M4 heat-set inserts (230 °C iron, flush) into every boss:
   - all H segments (2 each), including the ones that won't carry a hinge, so the hinges can be moved later. If your params file has `"screen": false`, the H segments have no bosses and get no inserts;
```
**with:**
```markdown
  - Aluminium tubes: 8g × 30 stainless countersunk self-tappers, with a 3.2 mm pilot drilled through the printed hole into the tube.
  - Steel transom tube: 8g × 25 tek (self-drilling) screws in 410 stainless. Or drill a 3.5–3.8 mm pilot through the 1.6 mm steel wall and use a stainless self-tapper.
  - V-slot cores (`"core": "vslot"`): M5 countersunk screws into slide-in T-nuts, with no pilots. The transom pair takes 8g × 20 self-tappers instead. See section 8.

  Stop when the head is flush, so the screw doesn't strip the plastic.

## 1. Prepare
1. Cut the tubes to the cut list with a hacksaw or drop saw, never longer than the list. With V-slot cores, cut to the V-slot cut plan in `bom/<name>.md` instead (section 8). Each length leaves 1.5 mm clear at every corner socket floor for print shrinkage. Dry-fit each member on its tube with the shims in, and trim the tube if any joint will not close onto its shims. Deburr and wipe with isopropyl.
2. Press M4 heat-set inserts (230 °C iron, flush) into every boss:
   - all H segments (2 each), including the ones that won't carry a hinge, so the hinges can be moved later. If your params file has `"screen": false`, the H segments have no bosses and get no inserts;
```

**Replace** in `docs/build-guide.md`:
```markdown
2. **Upper mullion.** Thread MST, the MU segments and MSH onto a `mullion_upper` tube. MST goes at the bottom, where it meets the transom. MSH goes at the top: its magnet channel turns along the head.
3. Check every joint closes onto its shims. Leave the joints unsealed and unscrewed.
```
**with:**
```markdown
2. **Upper mullion.** Thread MST, the MU segments and MSH onto a `mullion_upper` tube. MST goes at the bottom, where it meets the transom. MSH goes at the top: its magnet channel turns along the head.
3. Check every joint closes onto its shims. Leave the joints unsealed and unscrewed.

## 8. V-slot cores (only if `"core": "vslot"`)

The frame and sash cores are V-slot 2020 (4-slot). The transom and any mullions are two 2020s side by side. The `core` check line, and "Standard tubes in this V-slot window" in `bom/<name>.md`, list any member that kept a standard tube and why. Everything above still applies; this section only changes the tubes and their screws.

1. **Check the extrusion first** (test log row 10). The groove mouth should be about 9.2 mm wide at the surface, and the slot about 6 mm deep. The screw positions assume the OpenBuilds V-slot profile.
2. **Cut** each piece to the V-slot cut plan in `bom/<name>.md`, which allows 2 mm per saw cut. Label each piece with its cut-list name, then square and deburr the ends. A joined member (`head 1/2`, `head 2/2`) lists its pieces in order from the left end seen from outside, or from the bottom for a jamb.
3. **Each jamb is two tubes.**
   - **Lower piece (`jamb_lower`):** runs from the sill corner socket up into the JN node, whose T-nut holds its top end.
   - **Upper piece (`jamb_upper`):** starts at the JN's top face and runs into the head corner.
   - **Why the step:** the head and the upper jambs sit 3 mm further out than the other members, so the stay screws land on solid metal beside the groove.
4. **T-nut screws.** Every tube screw into V-slot, except the transom's, is an M5 countersunk machine screw into an M5 slide-in T-nut, with the length the BOM gives. There are no pilots and no drilling.
   1. **Hang the nuts.** Before a tube goes in, push each part's screw through its countersink and spin a T-nut onto the tip by one or two turns. Put its wide side towards the tube and its long side along the member, so it hangs in the empty pocket.
   2. **Check one.** The nut's wide body must sit below the slot lips, so the tube slides past it. If it doesn't, back the screw out half a turn.
   3. **Slide and tighten.** Slide the tube in: the slot picks up each nut in turn. Tighten each screw until snug (about 2 N·m). Don't overtighten: the head pulls the printed wall against the aluminium.
5. **Joins** (head, sill and lower jambs, where the BOM lists them).
   1. **Thread to the join.** Thread the parts onto the first piece up to the segment the BOM names for the join.
   2. **Place the join segment.** Slide that segment on so the piece end sits a quarter of the way along it.
   3. **Butt the next piece.** Push the next piece in from the other side until the ends butt.

   Each piece is held by its own T-nuts, and the segments either side are fixed to the brick.
6. **Transom pair.**
   - **Fitting:** lay the two 2020s together and slide them into the pocket as one.
   - **Holding:** the room-side bar takes the screws. The outer bar is trapped by the end walls of the TS shoes. With bays, the mullion pairs are trapped the same way, by their shoes' end walls.
   - **Screws:** 8g × 20 stainless self-tappers in 3.5 mm pilots, drilled through the printed hole into the extrusion's solid shoulder beside the groove.
7. **Friction stays.** The positions are unchanged (5.4 and install step 8). The screws bite the solid shoulder beside a groove, so drill 3.5 mm pilots instead of 3.2 mm.
```

- [ ] **Step 2: Install guide: stay pilots in V-slot**

**Replace** in `docs/install-guide.md`:
```markdown
   3. Drill 3.2 mm pilots through the track holes, and screw the track on with 8g × 25 stainless countersunk screws.
      - **Bays:** a track on a mullion goes into its steel tube. Use the 8g × 16 tek screws from the BOM, with no pilot. The two stays either side of a mullion screw into the same tube, and 16 mm screws miss each other inside it.
   4. Close the sash, and check both seals touch evenly. Adjust with the stay screws if needed.
9. **Glaze the fixed pane** (each pane, with bays).
```
**with:**
```markdown
   3. Drill 3.2 mm pilots through the track holes, and screw the track on with 8g × 25 stainless countersunk screws.
      - **Bays:** a track on a mullion goes into its steel tube. Use the 8g × 16 tek screws from the BOM, with no pilot. The two stays either side of a mullion screw into the same tube, and 16 mm screws miss each other inside it.
      - **V-slot cores:** the upper-jamb tube is 18.5–38.5 mm in, and the track screws bite the solid metal beside its groove. Drill 3.5 mm pilots. A V-slot mullion takes the 8g × 16 self-tappers from the BOM, also in 3.5 mm pilots.
   4. Close the sash, and check both seals touch evenly. Adjust with the stay screws if needed.
9. **Glaze the fixed pane** (each pane, with bays).
```

- [ ] **Step 3: Test log rows 10–12**

**Replace** in `docs/test-log.md`:
```markdown

Bench window: params/bench-600.json (acrylic glazing, tier 1 PETG).
Mount it in a timber test box (opening 600 × 600, 63 mm deep), fixed exactly as in the install guide. Rows 8 and 9 need a window with bays, so they use the two-bay bench window described below the table.

| # | Test | Method | Pass criterion | Date | Result | Notes |
```
**with:**
```markdown

Bench window: params/bench-600.json (acrylic glazing, tier 1 PETG).
Mount it in a timber test box (opening 600 × 600, 63 mm deep), fixed exactly as in the install guide. Rows 8 and 9 need a window with bays, so they use the two-bay bench window described below the table. Rows 10–12 are for V-slot cores (`"core": "vslot"`): add that key to the bench window's params, and it becomes all V-slot (5 pieces of 1 m).

| # | Test | Method | Pass criterion | Date | Result | Notes |
```

**Replace** in `docs/test-log.md`:
```markdown
| 8 | Mullion tees (windows with bays) | Rows 2 and 3 again, aimed at the SN, TX and HN seams and at the shoe turns either side of each mullion | No water inside and no smoke draw at any mullion seam | | | |
| 9 | Mullion shoe pull-out (windows with bays) | With the lock screws in, hook a luggage scale round the mullion next to one shoe and pull room-ward along the slot, by hand, to 200 N for 10 s. Do the shoe at the SN and the shoe at the TX. The mullion lock screws grip about half as much tongue as the jamb node's | No slip under 200 N, and no cracking at the shoe or the node | | | |

The joint sealant is assumed to take the joint movement: each 1 mm gap cycles between about 0 mm (hot) and 1.3 mm (cold), which needs a sealant rated for ±50 % movement. Repeat rows 2–3 after the bench window has seen a hot day and a cold night, and record any joint whose sealant has torn or come away.
```
**with:**
```markdown
| 8 | Mullion tees (windows with bays) | Rows 2 and 3 again, aimed at the SN, TX and HN seams and at the shoe turns either side of each mullion | No water inside and no smoke draw at any mullion seam | | | |
| 9 | Mullion shoe pull-out (windows with bays) | With the lock screws in, hook a luggage scale round the mullion next to one shoe and pull room-ward along the slot, by hand, to 200 N for 10 s. Do the shoe at the SN and the shoe at the TX. The mullion lock screws grip about half as much tongue as the jamb node's | No slip under 200 N, and no cracking at the shoe or the node | | | |
| 10 | V-slot profile (V-slot cores) | Calipers on one piece: groove mouth width at the surface, and slot depth to the floor | Mouth 9.0–9.4 mm, depth 5.9–6.3 mm: the OpenBuilds profile that the screw positions assume | | | |
| 11 | V-slot stay screw pull-out (V-slot cores) | On a JU segment threaded on an offcut, drive an 8g × 25 screw through a 3.5 mm pilot at the stay line (35 mm in), then pull it straight out with a luggage scale to 300 N for 10 s | No pull-out, and no cracking at the extrusion or the print | | | |
| 12 | T-nut hold (V-slot cores) | A segment on an offcut with its M5 screw and T-nut snug: push the segment along the tube with a luggage scale to 150 N for 10 s | No slip, and no cracking round the countersink | | | |

The joint sealant is assumed to take the joint movement: each 1 mm gap cycles between about 0 mm (hot) and 1.3 mm (cold), which needs a sealant rated for ±50 % movement. Repeat rows 2–3 after the bench window has seen a hot day and a cold night, and record any joint whose sealant has torn or come away.
```

- [ ] **Step 4: User manual, README and web README**

**Replace** in `docs/user-manual.md`:
```markdown
- **Re-print any part by its ID** from `cad/stl/<name>/<ID>.stl`: exterior parts in your tier's material, interior parts in PETG (`bom/<name>-parts.csv` says which). If the STLs are lost, regenerate them from the params file: `python3 tools/generate.py params/<name>.json`, then `cad/box.sh render <name>` (or export each `cad/generated/parts/<ID>.scad` in your own OpenSCAD).
- **Swap in place:** beads (`BFH`, `BFV`, `BSH`, `BSV`) unclip; weep caps (`WC`), sill-nose pieces (`NS`, re-tool the end fillets), cam handles and bases (`CMH`, `CMB`), keepers (`KP`), hinge leaves (`HG`, `HS`) and the whole screen unscrew.
- **Workshop jobs:** segments, corners, nodes and shoes are threaded on or screwed to the metal tubes. A mullion (`MSL`, `ML`, `MST`, `MU`, `MSH`) slides out towards the room once its four lock screws are out and the seams are cut, but only after the parts around it come out. Take off the sashes and screens on both sides of it, peel off magnet strip B (it covers the lock screw heads) and the EPDM bulb loops that run through its channel and kerfs, then unclip the beads and lift out both fixed panes beside it: a lower mullion's stop legs sit outside the panes. A frame part means taking the window out, so a small crack in a frame segment is better bonded and sealed in place.
- **Off-the-shelf spares:** EPDM bulb kerf seal (3 mm kerf), EPDM glazing wedge gasket (3 mm), 4 mm closed-cell foam cord, 12.7 mm magnetic strip A and B, 4 mm screen spline, fibreglass mesh, ±50 % MS-polymer sealant, and the screws listed in `bom/<name>.md`.
- **Glass:** re-order from `bom/<name>-glass.csv` (or the glass table in `bom/<name>.md`).
```
**with:**
```markdown
- **Re-print any part by its ID** from `cad/stl/<name>/<ID>.stl`: exterior parts in your tier's material, interior parts in PETG (`bom/<name>-parts.csv` says which). If the STLs are lost, regenerate them from the params file: `python3 tools/generate.py params/<name>.json`, then `cad/box.sh render <name>` (or export each `cad/generated/parts/<ID>.scad` in your own OpenSCAD).
- **Swap in place:** beads (`BFH`, `BFV`, `BSH`, `BSV`) unclip; weep caps (`WC`), sill-nose pieces (`NS`, re-tool the end fillets), cam handles and bases (`CMH`, `CMB`), keepers (`KP`), hinge leaves (`HG`, `HS`) and the whole screen unscrew.
- **Workshop jobs:** segments, corners, nodes and shoes are threaded on or screwed to the metal tubes. With V-slot cores, the tube screws are M5 into T-nuts, so they undo and go back in. A mullion (`MSL`, `ML`, `MST`, `MU`, `MSH`) slides out towards the room once its four lock screws are out and the seams are cut, but only after the parts around it come out. Take off the sashes and screens on both sides of it, peel off magnet strip B (it covers the lock screw heads) and the EPDM bulb loops that run through its channel and kerfs, then unclip the beads and lift out both fixed panes beside it: a lower mullion's stop legs sit outside the panes. A frame part means taking the window out, so a small crack in a frame segment is better bonded and sealed in place.
- **Off-the-shelf spares:** EPDM bulb kerf seal (3 mm kerf), EPDM glazing wedge gasket (3 mm), 4 mm closed-cell foam cord, 12.7 mm magnetic strip A and B, 4 mm screen spline, fibreglass mesh, ±50 % MS-polymer sealant, and the screws listed in `bom/<name>.md`.
- **Glass:** re-order from `bom/<name>-glass.csv` (or the glass table in `bom/<name>.md`).
```

**Replace** in `README.md`:
```markdown
   - `max_pane` (optional, no limit by default): the largest glass or acrylic sheet you can get, `[a, b]` in mm, either way round. The window is split into the fewest equal bays, divided by mullions, that make every pane fit. Each bay has its own fixed pane, awning sash and screen.
   - `bays` (optional): more bays than `max_pane` needs, or a number of bays on its own, with no `max_pane`. Fewer than `max_pane` needs is an error.
3. **Generate:** `python3 tools/generate.py params/my-window.json`. Read the check lines it prints (transom deflection, friction-stay rating, segment length, and with `max_pane` or `bays` the pane fit and mullion deflection). A `WARNING` line needs a change before you print.
4. **Render:** `cad/box.sh render my-window` writes the STLs to `cad/stl/my-window/` and checks each one against the part list.
5. **BOM:** `python3 bom/build_bom.py my-window` writes the following to `bom/`:
```
**with:**
```markdown
   - `max_pane` (optional, no limit by default): the largest glass or acrylic sheet you can get, `[a, b]` in mm, either way round. The window is split into the fewest equal bays, divided by mullions, that make every pane fit. Each bay has its own fixed pane, awning sash and screen.
   - `bays` (optional): more bays than `max_pane` needs, or a number of bays on its own, with no `max_pane`. Fewer than `max_pane` needs is an error.
   - `core` (optional): `"vslot"` builds the cores from V-slot 2020 extrusion, with M5 T-nuts, joins in the head, sill and lower jambs, and a cut plan in the BOM. The transom and mullions become two 2020s side by side. A member that can't be V-slot keeps its standard tube, and the `core` check line says why. That happens when it is longer than your pieces and no join is allowed, or too flexible, like the 1.8 m transom.
   - `vslot_stock` (optional, with `core`, default 1000): the length of your V-slot pieces, 300-6000 mm.
3. **Generate:** `python3 tools/generate.py params/my-window.json`. Read the check lines it prints (transom deflection, friction-stay rating, segment length, with `max_pane` or `bays` the pane fit and mullion deflection, and with `core` the tube cores). A `WARNING` line needs a change before you print.
4. **Render:** `cad/box.sh render my-window` writes the STLs to `cad/stl/my-window/` and checks each one against the part list.
5. **BOM:** `python3 bom/build_bom.py my-window` writes the following to `bom/`:
```

**Replace** in `web/README.md`:
```markdown
6. **Download** `<name>-openwindow.zip` once every part has passed its STL check. If some parts failed, a partial zip leaves them out and lists them at the top of its `README.txt`.

Any form field can also be preset in the address, for example `/?name=bench-600&opening_w=600&opening_h=600&awning_h=200&glazing=acrylic&tier=1&max_pane=none`. Add `view=<ID>` or `view=assembled` to open the viewer, and `max_pane=1200,900` or `max_pane=none` for the sheet limit. For acrylic glazing, `acrylic_t=3&acrylic_gap=12` sets the panel thickness and air gap; the page only sends them when they differ from 4 and 16, so the reference windows still match.

## Files it writes
```
**with:**
```markdown
6. **Download** `<name>-openwindow.zip` once every part has passed its STL check. If some parts failed, a partial zip leaves them out and lists them at the top of its `README.txt`.

Any form field can also be preset in the address, for example `/?name=bench-600&opening_w=600&opening_h=600&awning_h=200&glazing=acrylic&tier=1&max_pane=none`. Add `view=<ID>` or `view=assembled` to open the viewer, and `max_pane=1200,900` or `max_pane=none` for the sheet limit. For acrylic glazing, `acrylic_t=3&acrylic_gap=12` sets the panel thickness and air gap; the page only sends them when they differ from 4 and 16, so the reference windows still match. `core=vslot` picks V-slot cores, and `vslot_stock=1200` sets a piece length other than 1000 mm.

## Files it writes
```

- [ ] **Step 5: Specs: the main spec's §12 item 15, and the V-slot spec's status and amendments**

**Replace** in `docs/specs/2026-10-07-diy-window-design.md`:
```markdown
    - The transom is checked over its full span, with each mullion's reaction as a point load: the dovetails carry no moment, so the mullions can't prop it. That gives 6.8 mm against 9.5 mm for the home opening in two bays.
14. **Configurable acrylic sandwich (2026-10-10).** With acrylic glazing, the optional params `acrylic_t` (2-6 mm, default 4) and `acrylic_gap` (8-16 mm, default 16) set the panel thickness and air gap. The sandwich must fit the unchanged 24 mm pocket: the beads deepen by 24 − (2·t + gap) and the spacer bars follow the gap. The frame depth stays 63 mm because it is set by the sash seal stack and the friction-stay cavity, not by the glazing, so a thinner sandwich saves acrylic weight and cost but not plastic. Without the keys every output is unchanged.
```
**with:**
```markdown
    - The transom is checked over its full span, with each mullion's reaction as a point load: the dovetails carry no moment, so the mullions can't prop it. That gives 6.8 mm against 9.5 mm for the home opening in two bays.
14. **Configurable acrylic sandwich (2026-10-10).** With acrylic glazing, the optional params `acrylic_t` (2-6 mm, default 4) and `acrylic_gap` (8-16 mm, default 16) set the panel thickness and air gap. The sandwich must fit the unchanged 24 mm pocket: the beads deepen by 24 − (2·t + gap) and the spacer bars follow the gap. The frame depth stays 63 mm because it is set by the sash seal stack and the friction-stay cavity, not by the glazing, so a thinner sandwich saves acrylic weight and cost but not plastic. Without the keys every output is unchanged.
15. **V-slot 2020 cores (2026-10-10).** Designed in `docs/specs/2026-10-10-vslot-core-design.md` and planned in `docs/plans/2026-10-11-vslot-core.md`.
    - **Cores:** with `"core": "vslot"`, the cores are V-slot 2020, with the transom and mullions as a pair, held with M5 T-nuts.
    - **Joins:** the head, sill and lower jambs join pieces inside a segment.
    - **Stays:** the head and upper-jamb pocket moves 3 mm outward, so the friction-stay screws bite solid metal.
    - **Fallback:** a member that is too long for the stock, or fails its bending check, keeps its standard tube.
    - **Compatibility:** without the key every output is unchanged, apart from the new `VSLOT_*` lines in the `dims.scad` mirror.
```

**Replace** in `docs/specs/2026-10-10-vslot-core-design.md`:
```markdown

Date: 2026-10-10
Status: Draft for review

## 1. Goal
```
**with:**
```markdown

Date: 2026-10-10
Status: Implemented (plan: `docs/plans/2026-10-11-vslot-core.md`); amended while planning (§13)

## 1. Goal
```

**Replace** in `docs/specs/2026-10-10-vslot-core-design.md`:
```markdown
- A sash bending check. 2020 V-slot is as stiff as the current tube, so nothing changes.
- Tracking offcuts across windows.
```
**with:**
```markdown
- A sash bending check. 2020 V-slot is as stiff as the current tube, so nothing changes.
- Tracking offcuts across windows.

## 13. Amendments (2026-10-11, from implementation planning)

Each was checked in a scratch build: tests, box renders, section views. The plan's "Decisions and spec gaps" table has the reasons.

1. **Sash stay offset.** The sash tube centre is at 27 mm, not 29 mm (the sash profile is drawn in frame coordinates). Its stay screws sit 8–8.5 mm off the centre, at the existing "1.5 mm inside the tube edge" rule.
2. **Shoulder window.** It is **5.6–8.5 mm** off a face centre. The outer bound is the existing tube-edge rule. Beyond 8.2 mm, the V-slot corner is solid to about 5.6 mm deep.
3. **Upper-jamb shift.** The head and upper-jamb pocket moves **3.0 mm** (y 18.2–38.8, tube centre 28.5), not 2.5. That puts its stay screws 6.5–7 mm off centre, in the middle of the window. The fixing hole clearance becomes 6.7 mm.
4. **Chamber cap.** The chamber beside the moved pocket is capped at the pocket top. Uncapped, it left 0.8 mm to the chamber above, and a non-manifold edge in CH.
5. **M5 tip and lengths.** The M5 tip target is **5.4 mm** (window 5.0–5.8) below the tube face, with the tube pulled tight against the pocket wall. The longest standard length that reaches it is chosen, and the head seat is sunk by the remainder:

   | Member | M5 length | Seat |
   |---|---|---|
   | glazing/sill | 25 | 1.6 mm |
   | sash_rebate | 25 | 4.6 mm |
   | sash | 20 | 0.1 mm |
   | mullion | 16 | 0.6 mm |
6. **Screw boss.** The solid boss round an M5 screw is 14 mm, not 13. At 13 mm it was tangent to the sash corner block's end cap, which gave a non-manifold edge.
7. **Transom screws.** The transom shoulder screws are 8g × 20 stainless self-tappers in 3.5 mm pilots, at x = 41.25 (`VSLOT_TRANSOM_X`).
8. **Mullion stays.** Stay tracks on a V-slot mullion use 8g × 16 self-tappers in 3.5 mm pilots instead of tek screws.
9. **New dims keys.** `dims.json` gains the `VSLOT_*` keys, and `cad/generated/dims.scad` mirrors them. That is the one exception to §9.
10. **Fallback reasons.** A transom or mullion fallback gives both reasons when both apply ("longer than the pieces, and a V-slot pair would deflect …"), so the owner can see that longer stock won't help.
```

- [ ] **Step 6: Bench-test slides in thirds**

**Replace** in `pdf/build_deck.py`:
```python
        c = [x.strip() for x in r.strip().strip("|").split("|")]
        body.append(f"| {c[0]} | **{c[1]}** | {c[2]} | {c[3]} |")
    half = (len(body) + 1) // 2
    slide("test", "Bench test protocol (1/2)", md(f"""
Bench window `params/{bn.name}.json` ({bn.params['glazing']} glazing, tier {bn.params['tier']}), mounted in a timber test box ({fmt(bn.params['opening_w'])} × {fmt(bn.params['opening_h'])} opening, 63 mm deep) and fixed exactly as in the install guide. Record each result in `docs/test-log.md`.
""") + md("\n".join([head, "|---|---|---|---|"] + body[:half]), table_cls="xl compact"))
    slide("test", "Bench test protocol (2/2)", md("\n".join([head, "|---|---|---|---|"] + body[half:]), table_cls="xl compact") + md("""
?? The joint sealant is assumed to take the movement: each 1 mm gap cycles between about 0 mm (hot) and 1.3 mm (cold). Repeat rows 2–3 after a hot day and a cold night, and record any joint whose sealant has torn or come away.

?? Rows 8–9 need a window with bays, and `bench-600` has one. `docs/test-log.md` gives the params for a 2-bay bench window (`bench-1000-2bay`, a 1000 × 600 opening).
"""))
    slide("test", "The gate before the full-size build", grid(md(f"""
1. **Friction stay found:** a {hm.lay['stay']} mm pair rated ≥ {fmt(hm.lay['sash_kg'])} kg, stack ≤ {fmt(D['SASH_GAP'])} mm, width ≤ {fmt(D['STAY_W'])} mm. If none exists, the sash cavity or tube must change, and the frame, sash and corner parts be re-rendered.
```
**with:**
```python
        c = [x.strip() for x in r.strip().strip("|").split("|")]
        body.append(f"| {c[0]} | **{c[1]}** | {c[2]} | {c[3]} |")
    chunks = [body[i:i + 4] for i in range(0, len(body), 4)]
    for n, chunk in enumerate(chunks, 1):
        intro = md(f"""
Bench window `params/{bn.name}.json` ({bn.params['glazing']} glazing, tier {bn.params['tier']}), mounted in a timber test box ({fmt(bn.params['opening_w'])} × {fmt(bn.params['opening_h'])} opening, 63 mm deep) and fixed exactly as in the install guide. Record each result in `docs/test-log.md`.
""") if n == 1 else ""
        notes = md("""
?? The joint sealant is assumed to take the movement: each 1 mm gap cycles between about 0 mm (hot) and 1.3 mm (cold). Repeat rows 2–3 after a hot day and a cold night, and record any joint whose sealant has torn or come away.

?? Rows 8–9 need a window with bays, and `bench-600` has one. `docs/test-log.md` gives the params for a 2-bay bench window (`bench-1000-2bay`, a 1000 × 600 opening). Rows 10–12 are for V-slot cores: add `"core": "vslot"` to the bench window's params.
""") if n == len(chunks) else ""
        slide("test", f"Bench test protocol ({n}/{len(chunks)})",
              intro + md("\n".join([head, "|---|---|---|---|"] + chunk), table_cls="xl compact") + notes)
    slide("test", "The gate before the full-size build", grid(md(f"""
1. **Friction stay found:** a {hm.lay['stay']} mm pair rated ≥ {fmt(hm.lay['sash_kg'])} kg, stack ≤ {fmt(D['SASH_GAP'])} mm, width ≤ {fmt(D['STAY_W'])} mm. If none exists, the sash cavity or tube must change, and the frame, sash and corner parts be re-rendered.
```

- [ ] **Step 7: Rebuild the guide PDF**

Run:
```bash
cd ~/diy-window && python3 pdf/build_deck.py --check | tail -1
cd ~/diy-window && python3 pdf/build_deck.py | tail -2
```
Expected: `overflow: none`; then `wrote pdf/openwindow-deck.html (76 slides, …)` and `wrote OpenWindow-Guide.pdf (… KB, 76 pages, …)`.

---

### Task 8: Final checks and clean-up

- [ ] **Step 1: Everything passes**

Run:
```bash
cd ~/diy-window/tools && python3 -m unittest discover -p 'test_*.py' 2>&1 | grep -E '^(Ran|OK|FAILED)'
cd ~/diy-window && python3 -m unittest discover -s web/tests -p 'test_*.py' 2>&1 | grep -E '^(Ran|OK|FAILED)'
cd ~/diy-window && cad/box.sh test
```
Expected: `Ran 344 tests`, `OK`; `Ran 165 tests`, `OK`; `10 test files passed`.

- [ ] **Step 2: Compatibility, one last time**

Run the compatibility check. Expected: `BYTE-IDENTICAL`.

- [ ] **Step 3: Clean up**

Run: `cd ~/diy-window && rm -rf .vslot-baseline .vslot-after .vslot-review && python3 tools/generate.py params/bench-600.json | head -1`
Expected: `bench-600: 37 part types, 98 prints -> …/cad/generated`. This leaves `cad/generated/` on the bench window, as `box.sh test` expects.
