# OpenWindow Soft Edges Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Round every printed profile's outside edges to 2 mm, bevel every joint by 0.8 mm, and soften the hand-touched parts. Seals, glazing, tubes, joints and fixings keep their exact shape.

**Architecture:**
- **Profile rounding.**
  - `cad/profile.scad` builds each profile from a list of base rectangles (or the sill polygon). It rounds them with `soften()` (shrink by `EDGE_R`, grow back with radius `EDGE_R`) before subtracting any functional cut.
  - A short per-profile table, `sharp_corners()`, adds back the corners where a cut ends too close to keep a 1.5 mm wall.
  - A new CAD test finds every convex corner automatically, samples its 2 mm arc and checks the distance to every cut, so the table can't go stale.
- **Joint bevel.** `bevel_ends()` subtracts four 0.2 mm stepped rings from the end faces of segments, corner-block legs, nodes and shoes.
- **Nodes and stubs.** The in-line nodes round their plain block outline with `soft_rect()`. The shoes' fin stubs use `fin_stub()`.
- **Hand parts.** The cam and hinge parts round their plates in plan, and the cam handle's tops get a stepped 1.5 mm quarter-round.
- **Re-renders.** All four windows are re-rendered. The guide's 73 illustrations get a committed job list (`pdf/deck_renders.txt`) and a runner (`pdf/render_deck.py`), then the PDF is rebuilt.

**Tech Stack:**
- Python 3 standard library only, using the Mac's `python3`.
- OpenSCAD on the Windows box through `cad/box.sh` (nightly 2026.10.02, manifold backend).
- The Mac's Google Chrome, headless, for the guide PDF.

**Spec:** `docs/specs/2026-10-11-soft-edges-design.md`. Background: `docs/specs/2026-10-07-diy-window-design.md` (§12 amendments win).

## Global Constraints

- `EDGE_R` = 2.0, `JOINT_BEVEL` = 0.8, `BEVEL_STEP` = 0.2, `HANDLE_R` = 3.0 (new `cad/dims.json` keys).
- Rounded: convex outside corners only. Concave corners stay sharp. Every functional cut stays sharp and unchanged: tube pockets, kerfs, bead keyways, magnet channels, nose keys, spline groove, dovetails, fixing and screw holes.
- Any rounded corner keeps at least `MIN_SKIN` (1.5 mm) to every cut and chamber; a corner that can't is listed in `sharp_corners()`.
- Joint bevel on the outer outline of every end face that butts another part along a member (segments both ends, corner-block leg ends, node ends, shoes' segment-side end); never round the tube pocket; `CORD_INSET − JOINT_BEVEL ≥ 0.6`.
- Hand parts: cam handle `HANDLE_R` in plan plus a 1.5 mm top round; cam base, keeper and hinge plates 2 mm in plan. The cam ramp, hub bore, keeper lip, knuckles, pin and screw holes are unchanged.
- Generator outputs (part calls, cut lists, glass, layout) byte-identical apart from the four new `dims.scad` lines. BOM and CSV files change only in their `Filament` lines.
- Bed-fit envelopes change only for S, SW and CMH (spec §10 item 5).
- Not changed: outer frame and sash corners in the window plane, sill nose, weep caps, setting blocks, acrylic spacers.

## Review Focus

These are the failure modes the spec implies, each pinned by a test or a check:

1. **Steps at joints.** A node or stub whose outline doesn't match the member it continues leaves a visible step. The corner test asserts that the TX keeps exactly the transom's sharp corners on its body, and that no frame profile's sharp corner lies on a frame node (Task 1). The joint close-up (Task 2) shows the seam.
2. **Thin lips from rounding.** A rounded corner next to a kerf, keyway or channel leaves a thin lip at the slot mouth. The corner test samples every arc against every cut, for both cores (Task 1).
3. **V-slot windows.** The rounding must hold with the V-slot pocket shift (`core = "vslot"`). The corner test runs both cores, and Task 2 renders a V-slot upper jamb, head corner and segment.
4. **The cam must still lock.** The flag, hub bore and keeper lip are unchanged. `cam_test.scad` keeps passing, and the CMH envelope keeps its 10.0 mm height (Task 4).
5. **Owner's window.** The owner's window must re-render cleanly with its params untouched: `my-window` is rendered in full in Task 4.

## Execution status

**Done (2026-10-11), via subagents.** Reviews took the code and docs beyond this plan's blocks, so `cad/`, `tools/`, `docs/` and `pdf/` are authoritative over them. The changes:
- **Arc resolution:** every rounding uses `$fn = 32` (spec §10 item 8).
- **Nodes:** node bevels follow the keyway, nose-key and magnet-channel mouths. `node_sharp()` keeps SN, HN and TX sharp where their profile runs flat, and JN pulls its cord grooves in at its two reveal corners (§10 item 9).
- **Sash joints:** `bevel_outline()` and `bevel_fill()` keep the bevel out of the sash glazing kerf, whose floor is only 1.5 mm (§10 item 6).
- **Hinge leaves:** HG's wall stays square within the plate's thickness, and HS rounds plate and wall as one footprint (§10 item 3).
- **Tests:** `soft_test.scad` instantiates the five hand parts, so their asserts run in `cad/box.sh test`. The new `tools/test_bevel_faces.py` checks that no bevel splits a segment's or node's end face.
- **Images:** `pdf/deck_renders.txt` also lists the four README and deck renders in `docs/img` (77 lines). The README's transom section is now `docs/img/deck/section-1.png`.
- **Docs:** T-junction notch filling (install guide 6.6), the `JOINT_BEVEL` fallback (printing guide), and the deck's orientation and joint-rules slides.

Final checks:
- tools `Ran 348 tests`, OK; web `Ran 165 tests`, OK; `cad/box.sh test` 11 files passed;
- renders 37/37, 35/35, 43/43, 48/48; envelopes S/SW 57.699 and CMH 86.122, no others changed;
- filament: home 16.36 + 3.84 kg, 2-bay 19.06 + 4.75 kg;
- guide 77/77 images, 77 pages, `overflow: none`.

Before execution, every task below was run once, in order, on a scratch copy of the repo while the plan was written:
- stdlib Python;
- the real Windows box through the copy's `cad/box.sh`;
- the Mac's Chrome.

The run applied every Create and Replace block literally, with a small script.

**Results:**
- **Tests:** `cad/box.sh test` reports `11 test files passed` (10 before). Tools ran 346 tests OK and web ran 165 OK, unchanged.
- **Renders:** bench-600 37/37, home-1800x1500 35/35, home-1800x1500-2bay 43/43 and my-window 48/48 parts ok.
- **Envelopes:** exactly S, SW and CMH changed.
- **BOMs:** only the `Filament` lines changed.
- **Compatibility check:** `BYTE-IDENTICAL`.
- **Guide:** 73/73 guide images re-rendered; the PDF is 77 pages with `overflow: none`.
- **By eye:** the joint, corner and cam-handle close-ups were checked.

The numbers quoted in the expected outputs come from that run.

## Decisions and spec gaps (found while planning)

The spec's §10 records these, and Task 5 writes them into it.

| Spec says, or leaves open | Plan does | Why |
|---|---|---|
| §3.1: exception corners "listed per profile" | The corner test found these, and the table holds exactly these:<br>• the fin tip beside the outer seal kerf on `sash_rebate`, `transom` and both sides of `mullion_sash`;<br>• the room-face corner next to a magnet channel on the `sash_rebate` inner stop, the `transom` body and both sides of `mullion_sash`.<br>The cross-node TX keeps the transom's body corner sharp too (`cross_sharp()`). | Rounding there leaves a 0–1 mm lip at the kerf or channel mouth. Every other corner keeps at least 1.5 mm |
| §3.1: rounding method | `base_rects()` replaces the hand-written unions in `profile_solid()`, with the same rectangles, so the unrounded base is unchanged. Convex corners are found by sampling the four quadrants round each rectangle corner, and the sill by the polygon's turn direction | The test and the geometry share one description of each profile |
| §2: beads "on their room-side edges" | Only the bead's room-side edge facing the glass is rounded. The edge against the frame stays sharp | The key tongue starts within 1 mm of that edge, and rounding it would undercut the tongue's root |
| §3.3: bevel faces | No bevel on beads | Bead segments butt without sealant; the spec lists member joints only |
| §3.4: hinge plates and walls 2 mm | HG: the plate rounds only its free corners. Its 3 mm wall gets `WALL_R` = 1 mm. HS: the plate and its 5 mm wall get 2 mm | Rounding HG's plate corners against the wall would notch the joint, and a 2 mm radius would delete a 3 mm wall |
| §3.4: cam handle "3 mm in plan, softened top edge" | `HANDLE_R` rounds the lever and knob in plan. `soft_top()` adds a 1.5 mm quarter-round (`TOP_R`) to the lever, knob and hub tops, in six 0.25 mm layers | The lever's plan corners sit inside the hub and knob, so the top round is what you feel |
| §6: bed-fit envelopes unchanged | S and SW go from 58 to 57.68 mm, and CMH from 86.151 to 86.122 mm. The table is re-measured | The sill's acute outside corner (82°) is rounded, and so is the knob's 32-gon |
| §6: re-render the guide images | `pdf/deck_renders.txt` holds 73 lines recovered from the original renders. Re-rendering three of them from the unchanged repo gave byte-identical PNGs | Future geometry changes can refresh the guide in one command |
| §9: if the cord-groove lip chips on the test coupon, drop the bevel to 0.6 mm | No new test-log row. The test coupon (TC) is a 60 mm `sash_rebate` segment with the joint bevel on both ends, and the printing guide already says to print it first and check the fit | It's a look-at-it check on the first print. Changing `JOINT_BEVEL` is one `dims.json` value, and the bevel asserts still hold at 0.6 |
| §6: "filament weights shift" | The owner's manual and `docs/printing.md` quote the home window's weights, and the deck builder checks the manual's value against the BOM. Both are updated | The PDF build stops on a stale manual value |

## Ground rules for whoever executes this

- **No git.** The user's rule: no git under `~` except one work repo. Every "commit" is a **Checkpoint** step: run its checks, and stop for review if any fails.
- **No installs on the Mac,** and nothing gets downloaded.
- **Windows box access.** Every ssh/scp goes through `cad/box.sh`, which binds en0.
- **One box job at a time.** Run `box.sh render` one at a time, and never with `generate.py` or `box.sh png` running: `render` ends with `check_stl.py` reading `cad/generated/`. `pdf/render_deck.py` runs `png` jobs four at a time, which is safe on its own.
- **No explanatory comments in code** beyond a one-line header. The reasons live in this plan and the spec.
- **Existing tests stay unchanged.**
- **The owner's window.** Leave `params/my-window.json` as it is. Task 4 re-renders `cad/stl/my-window` from it.
- **Working folder.** Run every command from `~/diy-window`.
  - Task 0 creates `.soft-baseline/`.
  - The checkpoints create `.soft-after/`.
  - Tasks 2–3 create `params/zz-soft*.json` and `cad/stl/zz-soft*`.
  - Task 4 creates `.soft-review/`.
  - Task 5 deletes all of them.

## File structure

| File | Change |
|---|---|
| `cad/dims.json` | + `EDGE_R`, `JOINT_BEVEL`, `BEVEL_STEP`, `HANDLE_R` |
| `cad/profile.scad` | The profile and rounding helpers:<br>• `base_rects`, `sash_side_rects`, `sill_points`;<br>• `convex_corners` (with `rect_convex` and `poly_convex`), `sharp_corners`, `soft_arc`, `cut_rects`, `screen_cut_rects`;<br>• `soften`, `profile_base`, `soft_base`, `soft_rect`, `bevel_ends`, `fin_stub`.<br>`profile_solid` is built on `soft_base`, and `bead_profile` rounds its room-side edge |
| `cad/lib/segment.scad` | Segments get `bevel_ends` |
| `cad/parts/corner_block.scad` | Leg ends get `bevel_ends` |
| `cad/parts/jamb_node.scad`, `cad/parts/frame_node.scad`, `cad/parts/cross_node.scad` | `soft_rect` body plus `bevel_ends`; the TX also gets `cross_sharp()` |
| `cad/parts/transom_shoe.scad`, `cad/parts/mullion_shoe.scad` | `fin_stub` plus `bevel_ends` at the segment end |
| `cad/parts/cam_lock.scad`, `cad/parts/screen_hinge.scad` | Plan rounding, `soft_top`, fit asserts |
| `cad/tests/soft_test.scad` | New: the rounding rules |
| `tools/part_envelopes.json` | Re-measured (S, SW, CMH) |
| `cad/stl/*/`, `bom/*` | Re-rendered and rebuilt |
| `pdf/deck_renders.txt`, `pdf/render_deck.py` | New: the guide image job list and its runner |
| `docs/img/deck/*.png`, `OpenWindow-Guide.pdf` | Re-rendered and rebuilt |
| `docs/build-guide.md`, `docs/printing.md`, `docs/user-manual.md`, `README.md`, `pdf/build_deck.py`, both specs | Doc updates |

---

### Task 0: Baseline of today's outputs

The compatibility rule: generator outputs stay byte-identical apart from the four new `dims.scad` lines. The BOM and CSV files stay identical outside their `Filament` lines. This task records today's outputs once.

**Files:**
- Create: `.soft-baseline/` (temporary, deleted in Task 5)

- [ ] **Step 1: Confirm the starting point**

Run:
```bash
cd ~/diy-window/tools && python3 -m unittest discover -p 'test_*.py' 2>&1 | grep -E '^(Ran|OK|FAILED)'
cd ~/diy-window && python3 -m unittest discover -s web/tests -p 'test_*.py' 2>&1 | grep -E '^(Ran|OK|FAILED)'
cd ~/diy-window && cad/box.sh test
```
Expected: `Ran 346 tests`, `OK`; then `Ran 165 tests`, `OK`; then `10 test files passed`.

- [ ] **Step 2: Record the baseline**

Run:
```bash
cd ~/diy-window && rm -rf .soft-baseline && mkdir .soft-baseline
for n in bench-600 home-1800x1500 home-1800x1500-2bay my-window; do
  python3 tools/generate.py params/$n.json > .soft-baseline/$n.stdout
  python3 bom/build_bom.py $n >> .soft-baseline/$n.stdout
  mkdir .soft-baseline/$n && cp -R cad/generated .soft-baseline/$n/
  for f in $n.csv $n.md $n-cutlist.csv $n-glass.csv $n-parts.csv; do grep -v Filament bom/$f > .soft-baseline/$n/$f; done
done
python3 tools/generate.py params/bench-600.json > /dev/null
ls .soft-baseline
```
Expected: `bench-600  bench-600.stdout  home-1800x1500  home-1800x1500-2bay  home-1800x1500-2bay.stdout  home-1800x1500.stdout  my-window  my-window.stdout`

The **compatibility check** used by later checkpoints re-runs the same commands into `.soft-after/` and compares:
```bash
cd ~/diy-window && rm -rf .soft-after && mkdir .soft-after
for n in bench-600 home-1800x1500 home-1800x1500-2bay my-window; do
  python3 tools/generate.py params/$n.json > .soft-after/$n.stdout
  python3 bom/build_bom.py $n >> .soft-after/$n.stdout
  mkdir .soft-after/$n && cp -R cad/generated .soft-after/$n/
  for f in $n.csv $n.md $n-cutlist.csv $n-glass.csv $n-parts.csv; do grep -v Filament bom/$f > .soft-after/$n/$f; done
done
python3 tools/generate.py params/bench-600.json > /dev/null
ok=1
diff -r -x dims.scad .soft-baseline .soft-after || ok=0
for n in bench-600 home-1800x1500 home-1800x1500-2bay my-window; do
  extra=$(diff .soft-baseline/$n/generated/dims.scad .soft-after/$n/generated/dims.scad | grep '^[<>]' | grep -v -E '^> (EDGE_R|JOINT_BEVEL|BEVEL_STEP|HANDLE_R) = ')
  [ -n "$extra" ] && { echo "$extra"; ok=0; }
done
[ $ok = 1 ] && echo BYTE-IDENTICAL || echo DIFFERENT
```
Expected, now and after every later task: `BYTE-IDENTICAL`, with no other output.

---

### Task 1: Rounded profiles and the corner rules (`cad/dims.json`, `cad/profile.scad`)

**Files:**
- Create: `cad/tests/soft_test.scad`
- Modify: `cad/dims.json`, `cad/profile.scad`, `cad/parts/cross_node.scad` (the `cross_sharp()` function only)

**Interfaces:**
- Produces:
  - **Profile functions (`cad/profile.scad`):** `base_rects(name)`, `sash_side_rects(e, w)`, `sill_points()`, `convex_corners(name)` (returns `[point, edge_dir_a, edge_dir_b]` per convex corner), `sharp_corners(name)`, `soft_arc(corner, steps = 8)`, `screen_cut_rects()`, `cut_rects(name, core)`.
  - **Profile modules:** `soften(r = EDGE_R)`, `profile_base(name)`, `soft_base(name)`, `soft_rect(r, sharp = [], rad = EDGE_R)`, `bevel_ends(len, bottom = true, top = true)` (children: the 2D outline), `fin_stub(b)` (b = `[x0, y0, x1, y1, z0, z1]`).
  - **Unchanged signatures:** `profile_solid(name, pocket = true, core)` and `profile(name, pocket = true, core)` keep their signatures and build on `soft_base`. `bead_profile` rounds its room-side glass edge.
  - **Later tasks:** Tasks 2–3 use `soft_rect`, `bevel_ends` and `fin_stub`.

- [ ] **Step 1: Write the failing CAD test**

**Create** `cad/tests/soft_test.scad`:
```openscad
// cad/tests/soft_test.scad
use <../profile.scad>
use <../parts/cross_node.scad>
include <../generated/dims.scad>

NAMES = ["glazing", "sash_rebate", "sill", "transom", "sash", "screen", "mullion_glazing", "mullion_sash"];

function pt_gap(r, p) = rect_gap(r, [p[0], p[1], p[0], p[1]]);
function corner_gap(name, c, core) = min([for (k = cut_rects(name, core), a = soft_arc(c)) pt_gap(k, a)]);
function is_sharp(name, p) = len([for (s = sharp_corners(name)) if (norm(s - p) < 1e-6) 1]) > 0;

bad = [for (n = NAMES, core = [undef, "vslot"], c = convex_corners(n)) if (!is_sharp(n, c[0]) && corner_gap(n, c, core) < MIN_SKIN)
           [n, core, c[0], corner_gap(n, c, core)]];
assert(len(bad) == 0, str("rounded corners too close to a cut: ", bad));
for (n = NAMES) for (s = sharp_corners(n))
    assert(len([for (c = convex_corners(n)) if (norm(c[0] - s) < 1e-6) 1]) > 0, str(n, ": sharp corner ", s, " is not a convex corner"));
for (n = NAMES) for (r = base_rects(n))
    assert(min(r[2] - r[0], r[3] - r[1]) >= 2 * EDGE_R, str(n, ": feature ", r, " is thinner than 2 x EDGE_R"));
assert(STOP_T >= 2 * EDGE_R, "sill stop survives the rounding");
assert([for (s = sharp_corners("transom")) if (s[0] >= cross_faces()[0] - 1e-6 && s[0] <= cross_faces()[1] + 1e-6) s] == cross_sharp(),
       "TX keeps the transom's sharp corners that lie on its body");
for (n = ["glazing", "sill", "sash_rebate"]) for (s = sharp_corners(n))
    assert(s[0] > FRAME_BODY + 1e-6, str(n, ": sharp corner ", s, " lies on a frame node's body"));
for (g = ["igu", "acrylic", "twinwall"], pane = [undef, 12, 18]) {
    y0 = bead_y0(g, pane);
    top = bead_seat_y() + BEAD_T;
    corner = [[BEAD_W, top], [-1, 0], [0, -1]];
    cuts = concat([kerf_rect(GLASS_CLEAR + GASKET_IN, y0, 1)], is_undef(bead_chamber(g, pane)) ? [] : [bead_chamber(g, pane)]);
    gap = min([for (k = cuts, a = soft_arc(corner)) pt_gap(k, a)]);
    assert(gap >= MIN_SKIN, str(g, " bead ", pane, ": rounded edge ", gap, " from a cut"));
    assert(BEAD_W >= 2 * EDGE_R && top - y0 >= 2 * EDGE_R, str(g, " bead ", pane, ": too thin to round"));
}
assert(EDGE_R <= CHAMBER_WALL, "rounding keeps the chamber walls");
assert(abs(JOINT_BEVEL / BEVEL_STEP - round(JOINT_BEVEL / BEVEL_STEP)) < 1e-9, "joint bevel is whole layers");
assert(CORD_INSET - JOINT_BEVEL >= 0.6, "joint bevel leaves a lip outside the cord groove");
echo("soft rules ok");
```

- [ ] **Step 2: Run it to see it fail**

Run: `cd ~/diy-window && cad/box.sh test; echo "exit $?"`
Expected: `exit 1`. The `soft_test.scad` section of the log shows `WARNING: Ignoring unknown function 'convex_corners'`, then the same for `'sharp_corners'` and `'base_rects'`, then `ERROR: Assertion '(STOP_T >= (2 * EDGE_R))' failed: "sill stop survives the rounding"`. The other ten files run clean.

- [ ] **Step 3: Add the dimensions**

**Replace** in `cad/dims.json`:
```json
  "VSLOT_CSK_D": 10.0,
  "VSLOT_M5_L": [10, 12, 16, 20, 25, 30, 35, 40],
  "VSLOT_TRANSOM_X": 41.25
}
```
**with:**
```json
  "VSLOT_CSK_D": 10.0,
  "VSLOT_M5_L": [10, 12, 16, 20, 25, 30, 35, 40],
  "VSLOT_TRANSOM_X": 41.25,
  "EDGE_R": 2.0,
  "JOINT_BEVEL": 0.8,
  "BEVEL_STEP": 0.2,
  "HANDLE_R": 3.0
}
```

- [ ] **Step 4: Round the profiles**

Apply these blocks in order:

**Replace** in `cad/profile.scad`:
```openscad
module bead_key(name) { for (r = bead_key_rects(name)) rect_r(r); }

module sash_side_add(e, w) {
    rect(e, FIN_Y0, e + FIN_L, FIN_Y1);
    rect(e, ISTOP_Y0, e + w, DEPTH);
}

module sill_body() {
    s = tan(SILL_SLOPE_DEG);
    polygon([[0, 0], [FRAME_W, 0], [FRAME_W - STOP_T * s, STOP_T],
             [FRAME_BODY - (BEAD_SEAT_Y - STOP_T) * s, STOP_T], [FRAME_BODY, BEAD_SEAT_Y],
             [FRAME_BODY, DEPTH], [0, DEPTH]]);
}

module chambers(name, core) { for (r = chamber_rects(name, core)) rect_r(r); }

module profile_solid(name, pocket = true, core) {
    fb = FRAME_BODY;
    tl = TRANSOM_W / 2 - TRANSOM_HALF_BODY;
    th = TRANSOM_W / 2 + TRANSOM_HALF_BODY;
    ml = MULLION_W / 2 - MULLION_HALF_BODY;
    mh = MULLION_W / 2 + MULLION_HALF_BODY;
    difference() {
        if (name == "glazing") union() { rect(0, 0, fb, DEPTH); rect(fb, 0, FRAME_W, STOP_T); }
        else if (name == "sash_rebate") union() { rect(0, 0, fb, DEPTH); sash_side_add(fb, FRAME_W - fb); }
        else if (name == "sill") sill_body();
        else if (name == "transom") union() { rect(tl, 0, th, DEPTH); rect(0, 0, tl, STOP_T); sash_side_add(th, TRANSOM_W - th); }
        else if (name == "sash") union() {
            rect(0, SASH_Y0, SASH_BODY, LIP_Y1);
            rect(-FLANGE_L, SASH_Y0, 0, FLANGE_Y1);
            rect(-LIP_L, LIP_Y0, 0, LIP_Y1);
            rect(SASH_BODY, SASH_Y0, SASH_W, STOP_T);
        }
        else if (name == "screen") rect(0, 0, SCREEN_W, SCREEN_DEPTH);
        else if (name == "mullion_glazing") union() { rect(ml, 0, mh, DEPTH); rect(0, 0, ml, STOP_T); rect(mh, 0, MULLION_W, STOP_T); }
        else if (name == "mullion_sash") union() {
            rect(ml, 0, mh, DEPTH);
            sash_side_add(mh, MULLION_W - mh);
            translate([MULLION_W, 0]) mirror([1, 0]) sash_side_add(mh, MULLION_W - mh);
        }
        else assert(false, str("unknown profile ", name));
        if (pocket) pocket_cut(name, core);
        bead_key(name);
```
**with:**
```openscad
module bead_key(name) { for (r = bead_key_rects(name)) rect_r(r); }

module sash_side_add(e, w) { for (r = sash_side_rects(e, w)) rect_r(r); }

function sash_side_rects(e, w) = [[e, FIN_Y0, e + FIN_L, FIN_Y1], [e, ISTOP_Y0, e + w, DEPTH]];

function base_rects(name) =
    let(fb = FRAME_BODY, tl = TRANSOM_W / 2 - TRANSOM_HALF_BODY, th = TRANSOM_W / 2 + TRANSOM_HALF_BODY,
        ml = MULLION_W / 2 - MULLION_HALF_BODY, mh = MULLION_W / 2 + MULLION_HALF_BODY)
    name == "glazing" ? [[0, 0, fb, DEPTH], [fb, 0, FRAME_W, STOP_T]]
  : name == "sash_rebate" ? concat([[0, 0, fb, DEPTH]], sash_side_rects(fb, FRAME_W - fb))
  : name == "transom" ? concat([[tl, 0, th, DEPTH], [0, 0, tl, STOP_T]], sash_side_rects(th, TRANSOM_W - th))
  : name == "sash" ? [[0, SASH_Y0, SASH_BODY, LIP_Y1], [-FLANGE_L, SASH_Y0, 0, FLANGE_Y1], [-LIP_L, LIP_Y0, 0, LIP_Y1],
                      [SASH_BODY, SASH_Y0, SASH_W, STOP_T]]
  : name == "screen" ? [[0, 0, SCREEN_W, SCREEN_DEPTH]]
  : name == "mullion_glazing" ? [[ml, 0, mh, DEPTH], [0, 0, ml, STOP_T], [mh, 0, MULLION_W, STOP_T]]
  : name == "mullion_sash" ? let(s = sash_side_rects(mh, MULLION_W - mh)) concat([[ml, 0, mh, DEPTH]], s, [for (r = s) mirror_rect(r)])
  : [];

function sill_points() =
    let(s = tan(SILL_SLOPE_DEG))
    [[0, 0], [FRAME_W, 0], [FRAME_W - STOP_T * s, STOP_T], [FRAME_BODY - (BEAD_SEAT_Y - STOP_T) * s, STOP_T],
     [FRAME_BODY, BEAD_SEAT_Y], [FRAME_BODY, DEPTH], [0, DEPTH]];

module sill_body() { polygon(sill_points()); }

function in_rects(q, rs) = len([for (r = rs) if (q[0] > r[0] && q[0] < r[2] && q[1] > r[1] && q[1] < r[3]) 1]) > 0;

function rect_convex(rs) =
    [for (r = rs, p = [[r[0], r[1]], [r[2], r[1]], [r[0], r[3]], [r[2], r[3]]])
        let(q = [for (sx = [-1, 1], sy = [-1, 1]) if (in_rects(p + 0.01 * [sx, sy], rs)) [sx, sy]])
        if (len(q) == 1) [p, [q[0][0], 0], [0, q[0][1]]]];

function unit(v) = v / norm(v);

function poly_convex(pts) =
    let(n = len(pts))
    [for (i = [0 : n - 1]) let(a = pts[(i + n - 1) % n], p = pts[i], b = pts[(i + 1) % n],
                                u = p - a, v = b - p)
        if (u[0] * v[1] - u[1] * v[0] > 1e-9) [p, unit(a - p), unit(b - p)]];

function convex_corners(name) = name == "sill" ? poly_convex(sill_points()) : rect_convex(base_rects(name));

function sharp_corners(name) =
    let(tl = TRANSOM_W / 2 - TRANSOM_HALF_BODY, th = TRANSOM_W / 2 + TRANSOM_HALF_BODY,
        ml = MULLION_W / 2 - MULLION_HALF_BODY, mh = MULLION_W / 2 + MULLION_HALF_BODY)
    name == "sash_rebate" ? [[FRAME_BODY + FIN_L, FIN_Y0], [FRAME_W, DEPTH]]
  : name == "transom" ? [[th + FIN_L, FIN_Y0], [tl, DEPTH]]
  : name == "mullion_sash" ? [[mh + FIN_L, FIN_Y0], [ml - FIN_L, FIN_Y0], [MULLION_W, DEPTH], [0, DEPTH]]
  : [];

function soft_arc(c, steps = 8) =
    let(p = c[0], u = c[1], v = c[2], phi = acos(u * v), m = unit(u + v),
        ctr = p + m * EDGE_R / sin(phi / 2), ta = p + u * EDGE_R / tan(phi / 2), tb = p + v * EDGE_R / tan(phi / 2),
        a0 = atan2((ta - ctr)[1], (ta - ctr)[0]), a1 = atan2((tb - ctr)[1], (tb - ctr)[0]),
        d0 = a1 - a0, da = d0 > 180 ? d0 - 360 : d0 < -180 ? d0 + 360 : d0)
    [for (k = [0 : steps]) ctr + EDGE_R * [cos(a0 + da * k / steps), sin(a0 + da * k / steps)]];

module soften(r = EDGE_R) { offset(r = r, $fn = 32) offset(delta = -r) children(); }

module profile_base(name) {
    if (name == "sill") sill_body();
    else {
        assert(len(base_rects(name)) > 0, str("unknown profile ", name));
        for (r = base_rects(name)) rect_r(r);
    }
}

module soft_rect(r, sharp = [], rad = EDGE_R) {
    soften(rad) rect_r(r);
    for (c = sharp) intersection() {
        rect_r(r);
        translate(c - [rad, rad] * 1.5) square(3 * rad);
    }
}

module bevel_ends(len, bottom = true, top = true) {
    n = round(JOINT_BEVEL / BEVEL_STEP);
    for (i = [0 : n - 1]) {
        k = JOINT_BEVEL - i * BEVEL_STEP;
        for (z = concat(bottom ? [i * BEVEL_STEP - EPS] : [], top ? [len - (i + 1) * BEVEL_STEP] : []))
            translate([0, 0, z]) linear_extrude(BEVEL_STEP + EPS) difference() {
                offset(delta = 1) children();
                offset(delta = -k) children();
            }
    }
}

module fin_stub(b) {
    translate([b[0], 0, 0]) rotate([90, 0, 90]) linear_extrude(b[2] - b[0]) union() {
        soften() rect(b[1], b[4], b[3], b[5]);
        rect(b[1], b[4], b[3] - EDGE_R, b[5]);
        rect(b[1], b[4], b[3], b[5] - EDGE_R);
    }
}

module soft_base(name) {
    soften() profile_base(name);
    for (c = sharp_corners(name)) intersection() {
        profile_base(name);
        translate(c - [EDGE_R, EDGE_R] * 1.5) square(3 * EDGE_R);
    }
}

function screen_cut_rects() =
    [[SCREEN_OVERLAP + 2, -EPS, SCREEN_OVERLAP + 2 + MAG_W, MAG_D],
     [SCREEN_W - 8, SCREEN_DEPTH - SPLINE_D, SCREEN_W - 8 + SPLINE_W, SCREEN_DEPTH + EPS]];

function cut_rects(name, core) =
    concat([pocket_rect(name, core)], bead_key_rects(name), kerf_rects(name), mag_rects(name),
           name == "sill" ? nose_key_rects() : [], name == "screen" ? screen_cut_rects() : [], chamber_rects(name, core));

module chambers(name, core) { for (r = chamber_rects(name, core)) rect_r(r); }

module profile_solid(name, pocket = true, core) {
    difference() {
        soft_base(name);
        if (pocket) pocket_cut(name, core);
        bead_key(name);
```

**Replace** in `cad/profile.scad`:
```openscad
        for (r = mag_rects(name)) rect_r(r);
        if (name == "sill") for (r = nose_key_rects()) rect_r(r);
        if (name == "screen") {
            rect(SCREEN_OVERLAP + 2, -EPS, SCREEN_OVERLAP + 2 + MAG_W, MAG_D);
            rect(SCREEN_W - 8, SCREEN_DEPTH - SPLINE_D, SCREEN_W - 8 + SPLINE_W, SCREEN_DEPTH + EPS);
        }
    }
}
```
**with:**
```openscad
        for (r = mag_rects(name)) rect_r(r);
        if (name == "sill") for (r = nose_key_rects()) rect_r(r);
        if (name == "screen") for (r = screen_cut_rects()) rect_r(r);
    }
}
```

**Replace** in `cad/profile.scad`:
```openscad
    difference() {
        union() {
            rect(0, y0, BEAD_W, top);
            translate([0, KEY_Y]) rotate(90) key_tongue(KEY_D, KEY_H);
        }
```
**with:**
```openscad
    difference() {
        union() {
            soften() rect(0, y0, BEAD_W, top);
            rect(0, y0, BEAD_W - EDGE_R, top);
            rect(0, y0, BEAD_W, top - EDGE_R);
            translate([0, KEY_Y]) rotate(90) key_tongue(KEY_D, KEY_H);
        }
```

The test also checks the transom cross-node's sharp corner, so name it now (Task 2 uses it):

**Replace** in `cad/parts/cross_node.scad`:
```openscad
function cross_faces() = [TRANSOM_W / 2 - TRANSOM_HALF_BODY, TRANSOM_W / 2 + TRANSOM_HALF_BODY];

function cross_mag_cuts() =
    [for (r = mag_rects("mullion_sash")) [TRANSOM_MAG_X, DEPTH - MAG_D, cross_faces()[1] + EPS, DEPTH + EPS, r[0], r[2]]];
```
**with:**
```openscad
function cross_faces() = [TRANSOM_W / 2 - TRANSOM_HALF_BODY, TRANSOM_W / 2 + TRANSOM_HALF_BODY];

function cross_sharp() = [[cross_faces()[0], DEPTH]];

function cross_mag_cuts() =
    [for (r = mag_rects("mullion_sash")) [TRANSOM_MAG_X, DEPTH - MAG_D, cross_faces()[1] + EPS, DEPTH + EPS, r[0], r[2]]];
```

- [ ] **Step 5: Run the CAD tests to see them pass**

Run: `cd ~/diy-window && cad/box.sh test`
Expected: `11 test files passed`.

- [ ] **Step 6: Checkpoint**

Run the compatibility check (Task 0). Expected: `BYTE-IDENTICAL`. The STLs haven't been re-rendered yet, so the BOMs are unchanged too.

---

### Task 2: Joint bevels, nodes and fin stubs

**Files:**
- Modify: `cad/lib/segment.scad`, `cad/parts/corner_block.scad`, `cad/parts/jamb_node.scad`, `cad/parts/frame_node.scad`, `cad/parts/cross_node.scad`, `cad/parts/transom_shoe.scad`, `cad/parts/mullion_shoe.scad`
- Temporary: `params/zz-soft.json`, `params/zz-soft-2bay.json`, `params/zz-soft-vslot.json`, `cad/stl/zz-soft*` (deleted in Task 5). They keep the reference STLs untouched until Task 4.

**Interfaces:**
- Consumes: `soft_rect`, `bevel_ends`, `fin_stub`, `profile_solid` (Task 1).
- Consumes also: `cross_sharp()` in `cad/parts/cross_node.scad` (Task 1).

- [ ] **Step 1: Apply the bevels and outlines**

**Replace** in `cad/lib/segment.scad`:
```openscad
        }
        for (z = [-EPS, len - CORD_D / 2]) translate([0, 0, z]) end_groove(name, core);
        local_cuts(name, len / 2, bosses, abs(boss_dz), core);
        if (weep) translate([0, 0, len / 2 - WEEP_W / 2]) linear_extrude(WEEP_W) rect_r(weep_rect(name));
```
**with:**
```openscad
        }
        for (z = [-EPS, len - CORD_D / 2]) translate([0, 0, z]) end_groove(name, core);
        bevel_ends(len) profile_solid(name, false, core);
        local_cuts(name, len / 2, bosses, abs(boss_dz), core);
        if (weep) translate([0, 0, len / 2 - WEEP_W / 2]) linear_extrude(WEEP_W) rect_r(weep_rect(name));
```

**Replace** in `cad/parts/corner_block.scad`:
```openscad
    translate([0, 0, z1 - socket_depth(a)]) linear_extrude(socket_depth(a) + EPS) pocket_cut(a, core);
    translate([0, 0, z1 - CORD_D / 2]) end_groove(a, core);
    tube_screw(a, corner_screw_at(a, b), core = core);
    if (is_perimeter(a)) fixing_hole(a, corner_fix_at(a, b));
```
**with:**
```openscad
    translate([0, 0, z1 - socket_depth(a)]) linear_extrude(socket_depth(a) + EPS) pocket_cut(a, core);
    translate([0, 0, z1 - CORD_D / 2]) end_groove(a, core);
    bevel_ends(z1, bottom = false) profile_solid(a, false, core);
    tube_screw(a, corner_screw_at(a, b), core = core);
    if (is_perimeter(a)) fixing_hole(a, corner_fix_at(a, b));
```

**Replace** in `cad/parts/jamb_node.scad`:
```openscad
    k = node_key_len();
    difference() {
        linear_extrude(TRANSOM_W) rect(0, 0, FRAME_BODY, DEPTH);
        translate([0, 0, -EPS]) linear_extrude(TRANSOM_W + 2 * EPS) pocket_cut("glazing", core);
        for (z = [-EPS, TRANSOM_W - k]) translate([0, 0, z]) linear_extrude(k + EPS) bead_key("glazing");
```
**with:**
```openscad
    k = node_key_len();
    difference() {
        linear_extrude(TRANSOM_W) soft_rect([0, 0, FRAME_BODY, DEPTH]);
        bevel_ends(TRANSOM_W) soft_rect([0, 0, FRAME_BODY, DEPTH]);
        translate([0, 0, -EPS]) linear_extrude(TRANSOM_W + 2 * EPS) pocket_cut("glazing", core);
        for (z = [-EPS, TRANSOM_W - k]) translate([0, 0, z]) linear_extrude(k + EPS) bead_key("glazing");
```

**Replace** in `cad/parts/frame_node.scad`:
```openscad
    d = mdove();
    difference() {
        linear_extrude(MULLION_W) rect(0, 0, FRAME_BODY, DEPTH);
        translate([0, 0, -EPS]) linear_extrude(MULLION_W + 2 * EPS) {
            pocket_cut(name, core);
```
**with:**
```openscad
    d = mdove();
    difference() {
        linear_extrude(MULLION_W) soft_rect([0, 0, FRAME_BODY, DEPTH]);
        bevel_ends(MULLION_W) soft_rect([0, 0, FRAME_BODY, DEPTH]);
        translate([0, 0, -EPS]) linear_extrude(MULLION_W + 2 * EPS) {
            pocket_cut(name, core);
```

**Replace** in `cad/parts/cross_node.scad`:
```openscad
    f = cross_faces();
    difference() {
        linear_extrude(MULLION_W) rect(f[0], 0, f[1], DEPTH);
        translate([0, 0, -EPS]) linear_extrude(MULLION_W + 2 * EPS) { pocket_cut("transom", core); rect_r(mag_rect("transom")); }
        for (z = [-EPS, MULLION_W - k]) translate([0, 0, z]) linear_extrude(k + EPS) bead_key("transom");
```
**with:**
```openscad
    f = cross_faces();
    difference() {
        linear_extrude(MULLION_W) soft_rect([f[0], 0, f[1], DEPTH], cross_sharp());
        bevel_ends(MULLION_W) soft_rect([f[0], 0, f[1], DEPTH], cross_sharp());
        translate([0, 0, -EPS]) linear_extrude(MULLION_W + 2 * EPS) { pocket_cut("transom", core); rect_r(mag_rect("transom")); }
        for (z = [-EPS, MULLION_W - k]) translate([0, 0, z]) linear_extrude(k + EPS) bead_key("transom");
```

**Replace** in `cad/parts/transom_shoe.scad`:
```openscad
                linear_extrude(L) profile("transom", core = core);
                linear_extrude(SHOE_WALL) profile_solid("transom", false, core);
                box(shoe_fin_stub());
                multmatrix([[0, 1, 0, c], [0, 0, 1, STOP_T + DOVE_CLEAR], [1, 0, 0, 0]])
                    linear_extrude(DEPTH - STOP_T - DOVE_CLEAR) dove_tongue2d();
```
**with:**
```openscad
                linear_extrude(L) profile("transom", core = core);
                linear_extrude(SHOE_WALL) profile_solid("transom", false, core);
                fin_stub(shoe_fin_stub());
                multmatrix([[0, 1, 0, c], [0, 0, 1, STOP_T + DOVE_CLEAR], [1, 0, 0, 0]])
                    linear_extrude(DEPTH - STOP_T - DOVE_CLEAR) dove_tongue2d();
```

**Replace** in `cad/parts/transom_shoe.scad`:
```openscad
            for (t = shoe_turns()) box(t[0]);
            translate([0, 0, L - CORD_D / 2]) end_groove("transom", core);
            for (q = lock_uv()) translate([c + q[1], 0, q[0]]) lock_hole();
            box(shoe_seam_groove());
```
**with:**
```openscad
            for (t = shoe_turns()) box(t[0]);
            translate([0, 0, L - CORD_D / 2]) end_groove("transom", core);
            bevel_ends(L, bottom = false) profile_solid("transom", false, core);
            for (q = lock_uv()) translate([c + q[1], 0, q[0]]) lock_hole();
            box(shoe_seam_groove());
```

**Replace** in `cad/parts/mullion_shoe.scad`:
```openscad
            linear_extrude(L) profile(profile, core = core);
            linear_extrude(SHOE_WALL) profile_solid(profile, false, core);
            for (b = mshoe_fin_stubs(profile)) box(b);
            multmatrix([[0, 1, 0, c], [0, 0, 1, STOP_T + DOVE_CLEAR], [1, 0, 0, 0]])
                linear_extrude(DEPTH - STOP_T - DOVE_CLEAR) dove_tongue2d(d[0], d[1]);
```
**with:**
```openscad
            linear_extrude(L) profile(profile, core = core);
            linear_extrude(SHOE_WALL) profile_solid(profile, false, core);
            for (b = mshoe_fin_stubs(profile)) fin_stub(b);
            multmatrix([[0, 1, 0, c], [0, 0, 1, STOP_T + DOVE_CLEAR], [1, 0, 0, 0]])
                linear_extrude(DEPTH - STOP_T - DOVE_CLEAR) dove_tongue2d(d[0], d[1]);
```

**Replace** in `cad/parts/mullion_shoe.scad`:
```openscad
        for (t = mshoe_turns(profile, head)) box(t);
        translate([0, 0, L - CORD_D / 2]) end_groove(profile, core);
        for (q = mlock_uv()) translate([c + q[1], 0, q[0]]) lock_hole();
        box(mshoe_seam_groove(profile));
```
**with:**
```openscad
        for (t = mshoe_turns(profile, head)) box(t);
        translate([0, 0, L - CORD_D / 2]) end_groove(profile, core);
        bevel_ends(L, bottom = false) profile_solid(profile, false, core);
        for (q = mlock_uv()) translate([c + q[1], 0, q[0]]) lock_hole();
        box(mshoe_seam_groove(profile));
```

- [ ] **Step 2: Run the CAD tests**

Run: `cd ~/diy-window && cad/box.sh test`
Expected: `11 test files passed`.

- [ ] **Step 3: Render the changed parts under temporary names, one at a time**

Run:
```bash
cd ~/diy-window && python3 - <<'EOF'
import json
for src, dst, extra in (("bench-600", "zz-soft", {}), ("home-1800x1500-2bay", "zz-soft-2bay", {}), ("bench-600", "zz-soft-vslot", {"core": "vslot"})):
    p = json.load(open(f"params/{src}.json")) | {"name": dst} | extra
    json.dump(p, open(f"params/{dst}.json", "w"), indent=2)
EOF
cad/box.sh render zz-soft H SW JL JU TE SH SBE SV NH NV CH CSL CSR CS CN JN TSL TSR TC BFH BFV BSH BSV | tail -1
cad/box.sh render zz-soft-2bay SN HN TX MSL MST MSH ML MU | tail -1
cad/box.sh render zz-soft-vslot H JU CH | tail -1
```
Expected: `23/23 parts ok`, `8/8 parts ok`, `3/3 parts ok`. The bench window has only end segments on its sill, transom and sash bottom (SW, TE, SBE), so S, T and SB don't exist there. The beads (Task 1) render here too.

- [ ] **Step 4: Check a joint by eye**

Run:
```bash
cd ~/diy-window && mkdir -p .soft-review && cat > cad/tests/zz_joint.scad <<'EOF'
use <../lib/segment.scad>
segment("sash_rebate", 50, "A");
translate([0, 0, 51]) segment("sash_rebate", 50, "B");
EOF
cad/box.sh png tests/zz_joint.scad ~/diy-window/.soft-review/joint.png --camera=20,30,51,60,0,140,190 && rm cad/tests/zz_joint.scad
```
Look at `.soft-review/joint.png`. You should see two upper-jamb segments with a 1 mm gap between them. The room face carries the tube-screw countersink:
- **Long edges:** the vertical long edges are rounded.
- **Bevel:** each face round the gap shows the stepped bevel, four thin layers, along its outer outline and into the mouths of the kerfs and channels.
- **Inside the faces:** the tube pocket edges and the cord groove inside each face are not bevelled.

Stop for review if the bevel reaches the pocket or the cord groove.

---

### Task 3: Softer hand-touched parts (`cad/parts/cam_lock.scad`, `cad/parts/screen_hinge.scad`)

**Files:**
- Modify: `cad/parts/cam_lock.scad`, `cad/parts/screen_hinge.scad`

**Interfaces:**
- Consumes: `EDGE_R`, `HANDLE_R` (Task 1).
- Produces: in `cam_lock.scad`, `TOP_R`, `soften_plan(r)` and `soft_top(h, r = TOP_R, n = 6)`; in `screen_hinge.scad`, `WALL_R` and `soften_plan(r)`. Neither file uses `profile.scad`, so each defines its own `soften_plan`.

- [ ] **Step 1: Soften the parts**

**Replace** in `cad/parts/cam_lock.scad`:
```openscad
function keeper_half_run() = KEEPER_HALF;

module countersunk(d, t) {
    translate([0, 0, -0.01]) cylinder(d = d, h = t + 0.02, $fn = 20);
```
**with:**
```openscad
function keeper_half_run() = KEEPER_HALF;

TOP_R = 1.5;

module soften_plan(r) { offset(r = r, $fn = 32) offset(delta = -r) children(); }

module soft_top(h, r = TOP_R, n = 6) {
    linear_extrude(h - r) children();
    for (i = [0 : n - 1]) translate([0, 0, h - r + i * r / n - 0.01]) linear_extrude(r / n + 0.01)
        offset(delta = -(r - sqrt(r * r - pow((i + 1) * r / n, 2)))) children();
}

module countersunk(d, t) {
    translate([0, 0, -0.01]) cylinder(d = d, h = t + 0.02, $fn = 20);
```

**Replace** in `cad/parts/cam_lock.scad`:
```openscad

module cam_base(code) {
    difference() {
        union() {
            translate([-20, -10, 0]) cube([40, 22, BASE_T]);
            cylinder(d = BOSS_D, h = BASE_T + BOSS_H, $fn = 48);
        }
```
**with:**
```openscad

module cam_base(code) {
    assert(EDGE_R <= 22 / 2, "cam base plate rounding fits the plate");
    difference() {
        union() {
            linear_extrude(BASE_T) soften_plan(EDGE_R) translate([-20, -10]) square([40, 22]);
            cylinder(d = BOSS_D, h = BASE_T + BOSS_H, $fn = 48);
        }
```

**Replace** in `cad/parts/cam_lock.scad`:
```openscad

module cam_handle(code) {
    difference() {
        union() {
            translate([0, 0, BASE_T]) cylinder(d = HUB_D, h = BOSS_H - 0.3, $fn = 48);
            for (k = [0 : 7]) hull() { flag_slice(k); flag_slice(k + 1); }
            for (k = [0 : 7]) hull() { flag_web(k); flag_web(k + 1); }
            translate([-64, -6, BASE_T]) cube([58, 12, 10]);
            translate([-64, 0, BASE_T]) cylinder(d = 16, h = 10, $fn = 32);
        }
        translate([0, 0, BASE_T - 0.01]) cylinder(d = BOSS_D + 0.4, h = BOSS_H + 0.02, $fn = 48);
```
**with:**
```openscad

module cam_handle(code) {
    assert(HANDLE_R <= 12 / 2 && TOP_R <= BOSS_H - 0.3, "cam handle rounding fits the lever and hub");
    difference() {
        union() {
            translate([0, 0, BASE_T]) soft_top(BOSS_H - 0.3) circle(d = HUB_D, $fn = 48);
            for (k = [0 : 7]) hull() { flag_slice(k); flag_slice(k + 1); }
            for (k = [0 : 7]) hull() { flag_web(k); flag_web(k + 1); }
            translate([0, 0, BASE_T]) soft_top(10) soften_plan(HANDLE_R) union() {
                translate([-64, -6]) square([58, 12]);
                translate([-64, 0]) circle(d = 16, $fn = 32);
            }
        }
        translate([0, 0, BASE_T - 0.01]) cylinder(d = BOSS_D + 0.4, h = BOSS_H + 0.02, $fn = 48);
```

**Replace** in `cad/parts/cam_lock.scad`:
```openscad
    kv = keeper_v();
    sw = sash_face_w();
    difference() {
        union() {
            translate([-KEEPER_HALF, kv - 6, sw]) cube([2 * KEEPER_HALF, 22, 3]);
            translate([-8, kv + 5, sw]) cube([16, 10, lip_w() + LIP_T - sw]);
            translate([-LIP_HALF, R0 - 2, lip_w()]) cube([2 * LIP_HALF, kv + 15 - (R0 - 2), LIP_T]);
        }
```
**with:**
```openscad
    kv = keeper_v();
    sw = sash_face_w();
    assert(EDGE_R <= 10 / 2, "keeper rounding fits the post");
    difference() {
        union() {
            translate([0, 0, sw]) linear_extrude(3) soften_plan(EDGE_R) translate([-KEEPER_HALF, kv - 6]) square([2 * KEEPER_HALF, 22]);
            translate([0, 0, sw]) linear_extrude(lip_w() + LIP_T - sw) soften_plan(EDGE_R) translate([-8, kv + 5]) square([16, 10]);
            translate([-LIP_HALF, R0 - 2, lip_w()]) cube([2 * LIP_HALF, kv + 15 - (R0 - 2), LIP_T]);
        }
```

**Replace** in `cad/parts/screen_hinge.scad`:
```openscad
function hinge_leaf_t() = LEAF_T;

module knuckles(spans) {
    for (s = spans) translate([s[0], 0, AXIS_W]) rotate([0, 90, 0]) cylinder(d = KN_D, h = s[1] - s[0], $fn = 32);
```
**with:**
```openscad
function hinge_leaf_t() = LEAF_T;

WALL_R = 1;

module soften_plan(r) { offset(r = r, $fn = 32) offset(delta = -r) children(); }

module knuckles(spans) {
    for (s = spans) translate([s[0], 0, AXIS_W]) rotate([0, 90, 0]) cylinder(d = KN_D, h = s[1] - s[0], $fn = 32);
```

**Replace** in `cad/parts/screen_hinge.scad`:
```openscad
module screen_hinge(code) {
    v_hole = hinge_hole_v();
    difference() {
        union() {
            translate([-20, hinge_plate_v(), 0]) cube([40, PLATE_W, LEAF_T]);
            translate([-20, hinge_wall_v(), 0]) cube([40, WALL_T, AXIS_W]);
            knuckles(FRAME_KN);
        }
```
**with:**
```openscad
module screen_hinge(code) {
    v_hole = hinge_hole_v();
    assert(EDGE_R <= PLATE_W / 2 && WALL_R <= WALL_T / 2, "hinge leaf rounding fits the plate and wall");
    difference() {
        union() {
            linear_extrude(LEAF_T) union() {
                soften_plan(EDGE_R) translate([-20, hinge_plate_v()]) square([40, PLATE_W]);
                translate([-20, hinge_plate_v() + EDGE_R]) square([40, PLATE_W - EDGE_R]);
            }
            linear_extrude(AXIS_W) soften_plan(WALL_R) translate([-20, hinge_wall_v()]) square([40, WALL_T]);
            knuckles(FRAME_KN);
        }
```

**Replace** in `cad/parts/screen_hinge.scad`:
```openscad

module screen_leaf(code) {
    difference() {
        union() {
            translate([-12, 3, SCREEN_DEPTH]) cube([24, 25, LEAF_T]);
            translate([-12, 0, SCREEN_DEPTH]) cube([24, 5, AXIS_W - SCREEN_DEPTH]);
            knuckles(SCREEN_KN);
        }
```
**with:**
```openscad

module screen_leaf(code) {
    assert(EDGE_R <= 5 / 2, "screen leaf rounding fits its wall");
    difference() {
        union() {
            translate([0, 0, SCREEN_DEPTH]) linear_extrude(LEAF_T) soften_plan(EDGE_R) translate([-12, 3]) square([24, 25]);
            translate([0, 0, SCREEN_DEPTH]) linear_extrude(AXIS_W - SCREEN_DEPTH) soften_plan(EDGE_R) translate([-12, 0]) square([24, 5]);
            knuckles(SCREEN_KN);
        }
```

- [ ] **Step 2: Run the CAD tests and render the parts**

Run:
```bash
cd ~/diy-window && cad/box.sh test
cd ~/diy-window && cad/box.sh render zz-soft CMB CMH KP HG HS | tail -1
```
Expected: `11 test files passed`; then `5/5 parts ok`.

- [ ] **Step 3: Check the cam handle by eye**

Run: `cd ~/diy-window && PARAMS=zz-soft cad/box.sh png generated/parts/CMH.scad ~/diy-window/.soft-review/cmh.png --camera=0,0,0,24,-53,180,500 --viewall --autocenter`

Look at `.soft-review/cmh.png`:
- **Lever, knob and hub:** their tops have a smooth rounded edge.
- **Flag (the fan-shaped ramp):** unchanged.

Run `python3 tools/generate.py params/bench-600.json > /dev/null` afterwards, to leave `cad/generated/` on the bench window.

---

### Task 4: Re-render the four windows, envelopes and BOMs

**Files:**
- Modify (outputs): `cad/stl/bench-600/`, `cad/stl/home-1800x1500/`, `cad/stl/home-1800x1500-2bay/`, `cad/stl/my-window/`, `tools/part_envelopes.json`, `bom/*`

- [ ] **Step 1: Render all four windows in full, one at a time**

Run:
```bash
cd ~/diy-window && for n in bench-600 home-1800x1500 home-1800x1500-2bay my-window; do cad/box.sh render $n | tail -1; done
```
Expected: `37/37 parts ok`, `35/35 parts ok`, `43/43 parts ok`, `48/48 parts ok` (several minutes each).

- [ ] **Step 2: Re-measure the bed-fit envelopes**

Run:
```bash
cd ~/diy-window && cp tools/part_envelopes.json .soft-review/envelopes-before.json && python3 tools/part_envelopes.py | tail -1
cd ~/diy-window && python3 -c "
import json; a=json.load(open('tools/part_envelopes.json')); b=json.load(open('.soft-review/envelopes-before.json'))
print({k: (b.get(k), a[k]) for k in a if a[k] != b.get(k)})"
```
Expected: `part_envelopes.json: 52 measured from home-1800x1500, bench-600, home-1800x1500-2bay, 56 in all`; then `{'CMH': ([10.0, 53.0, 86.151], [10.0, 53.0, 86.122]), 'S': ([58.0, 63.0], [57.68, 63.0]), 'SW': ([58.0, 63.0], [57.68, 63.0])}`.

- [ ] **Step 3: Suites and BOMs**

Run:
```bash
cd ~/diy-window/tools && python3 -m unittest discover -p 'test_*.py' 2>&1 | grep -E '^(Ran|OK|FAILED)'
cd ~/diy-window && python3 -m unittest discover -s web/tests -p 'test_*.py' 2>&1 | grep -E '^(Ran|OK|FAILED)'
cd ~/diy-window && for n in bench-600 home-1800x1500 home-1800x1500-2bay my-window; do python3 bom/build_bom.py $n > /dev/null; grep Filament bom/$n.csv; done
```
Expected: `Ran 346 tests`, `OK`; `Ran 165 tests`, `OK`; then the eight filament lines:
```
Filament,PETG (interior),1.24,kg
Filament,"PETG + exterior paint, or ASA (exterior, tier 1)",6.18,kg
Filament,PETG (interior),3.83,kg
Filament,"ASA-CF or PC-ABS (light colour) (exterior, tier 3)",16.33,kg
Filament,PETG (interior),4.74,kg
Filament,"ASA-CF or PC-ABS (light colour) (exterior, tier 3)",19.03,kg
Filament,PETG (interior),4.92,kg
Filament,"PETG + exterior paint, or ASA (exterior, tier 1)",22.08,kg
```

- [ ] **Step 4: Checkpoint**

Run the compatibility check (Task 0). Expected: `BYTE-IDENTICAL`.

---

### Task 5: Guide images, docs and the guide PDF

**Files:**
- Create: `pdf/deck_renders.txt`, `pdf/render_deck.py`
- Modify: `docs/build-guide.md`, `docs/printing.md`, `docs/user-manual.md`, `README.md`, `pdf/build_deck.py`, `docs/specs/2026-10-07-diy-window-design.md`, `docs/specs/2026-10-11-soft-edges-design.md`
- Modify (outputs): `docs/img/deck/*.png`, `pdf/openwindow-deck.html`, `OpenWindow-Guide.pdf`

- [ ] **Step 1: The job list and its runner**

**Create** `pdf/deck_renders.txt`:
```text
# Guide-deck illustrations: PARAMS|view (relative to cad/)|output|openscad args. Render with python3 pdf/render_deck.py.
home-1800x1500|deck/hero.scad|docs/img/deck/hero.png|--camera=0,0,0,80,0,32,6000 --viewall --autocenter
home-1800x1500|deck/inside.scad|docs/img/deck/inside.png|--camera=0,0,0,78,0,205,6000 --viewall --autocenter
home-1800x1500|deck/inside.scad|docs/img/deck/inside-open.png|-D open=1 --camera=0,0,0,74,0,218,6000 --viewall --autocenter
home-1800x1500|deck/section.scad|docs/img/deck/section-0.png|-D zone=0 --camera=0,0,0,0,0,0,410 --projection=ortho
home-1800x1500|deck/section.scad|docs/img/deck/section-1.png|-D zone=1 --camera=0,0,0,0,0,0,410 --projection=ortho
home-1800x1500|deck/section.scad|docs/img/deck/section-2.png|-D zone=2 --camera=0,0,0,0,0,0,410 --projection=ortho
home-1800x1500|deck/section.scad|docs/img/deck/section-3.png|-D zone=3 --camera=0,0,0,0,0,0,410 --projection=ortho
home-1800x1500|deck/profiles.scad|docs/img/deck/profile-0.png|-D k=0 --camera=0,0,0,0,0,0,210 --projection=ortho
home-1800x1500|deck/profiles.scad|docs/img/deck/profile-1.png|-D k=1 --camera=0,0,0,0,0,0,210 --projection=ortho
home-1800x1500|deck/profiles.scad|docs/img/deck/profile-2.png|-D k=2 --camera=0,0,0,0,0,0,210 --projection=ortho
home-1800x1500|deck/profiles.scad|docs/img/deck/profile-3.png|-D k=3 --camera=0,0,0,0,0,0,210 --projection=ortho
home-1800x1500|deck/profiles.scad|docs/img/deck/profile-4.png|-D k=4 --camera=0,0,0,0,0,0,210 --projection=ortho
home-1800x1500|deck/profiles.scad|docs/img/deck/profile-5.png|-D k=5 --camera=0,0,0,0,0,0,210 --projection=ortho
home-1800x1500|deck/profiles.scad|docs/img/deck/profile-6.png|-D k=6 --camera=0,0,0,0,0,0,210 --projection=ortho
home-1800x1500|deck/profiles.scad|docs/img/deck/profile-7.png|-D k=7 --camera=0,0,0,0,0,0,210 --projection=ortho
home-1800x1500|deck/buildup.scad|docs/img/deck/build-1.png|-D step=1 --camera=0,0,0,48,0,200,8000 --viewall --autocenter
home-1800x1500|deck/buildup.scad|docs/img/deck/build-2.png|-D step=2 --camera=0,0,0,48,0,200,8000 --viewall --autocenter
home-1800x1500|deck/buildup.scad|docs/img/deck/build-3.png|-D step=3 --camera=0,0,0,48,0,200,8000 --viewall --autocenter
home-1800x1500|deck/buildup.scad|docs/img/deck/build-4.png|-D step=4 --camera=0,0,0,48,0,200,8000 --viewall --autocenter
home-1800x1500|deck/buildup.scad|docs/img/deck/build-5.png|-D step=5 --camera=0,0,0,48,0,200,8000 --viewall --autocenter
home-1800x1500|deck/buildup.scad|docs/img/deck/build-6.png|-D step=6 --camera=0,0,0,48,0,200,8000 --viewall --autocenter
home-1800x1500|deck/joint.scad|docs/img/deck/joint.png|--camera=0,0,0,68,0,212,800 --viewall --autocenter
home-1800x1500|deck/corner.scad|docs/img/deck/corner.png|--camera=0,0,0,62,0,205,800 --viewall --autocenter
home-1800x1500|deck/node.scad|docs/img/deck/node.png|--camera=0,0,0,62,0,222,800 --viewall --autocenter
home-1800x1500|deck/sill_detail.scad|docs/img/deck/sill-detail.png|--camera=0,0,0,72,0,28,800 --viewall --autocenter
home-1800x1500|deck/hinge.scad|docs/img/deck/hinge.png|--camera=0,0,0,62,0,205,800 --viewall --autocenter
home-1800x1500|generated/parts/H.scad|docs/img/deck/part-H.png|--camera=0,0,0,24,-53,180,500 --viewall --autocenter
home-1800x1500|generated/parts/S.scad|docs/img/deck/part-S.png|--camera=0,0,0,24,-53,180,500 --viewall --autocenter
home-1800x1500|generated/parts/SW.scad|docs/img/deck/part-SW.png|--camera=0,0,0,24,-53,180,500 --viewall --autocenter
home-1800x1500|generated/parts/JL.scad|docs/img/deck/part-JL.png|--camera=0,0,0,24,-53,180,500 --viewall --autocenter
home-1800x1500|generated/parts/JU.scad|docs/img/deck/part-JU.png|--camera=0,0,0,24,-53,180,500 --viewall --autocenter
home-1800x1500|generated/parts/T.scad|docs/img/deck/part-T.png|--camera=0,0,0,24,-53,180,500 --viewall --autocenter
home-1800x1500|generated/parts/TE.scad|docs/img/deck/part-TE.png|--camera=0,0,0,24,-53,180,500 --viewall --autocenter
home-1800x1500|generated/parts/SH.scad|docs/img/deck/part-SH.png|--camera=0,0,0,24,-53,180,500 --viewall --autocenter
home-1800x1500|generated/parts/SB.scad|docs/img/deck/part-SB.png|--camera=0,0,0,24,-53,180,500 --viewall --autocenter
home-1800x1500|generated/parts/SBE.scad|docs/img/deck/part-SBE.png|--camera=0,0,0,24,-53,180,500 --viewall --autocenter
home-1800x1500|generated/parts/SV.scad|docs/img/deck/part-SV.png|--camera=0,0,0,24,-53,180,500 --viewall --autocenter
home-1800x1500|generated/parts/NH.scad|docs/img/deck/part-NH.png|--camera=0,0,0,24,-53,180,500 --viewall --autocenter
home-1800x1500|generated/parts/NV.scad|docs/img/deck/part-NV.png|--camera=0,0,0,24,-53,180,500 --viewall --autocenter
home-1800x1500|generated/parts/NS.scad|docs/img/deck/part-NS.png|--camera=0,0,0,24,-53,180,500 --viewall --autocenter
home-1800x1500|generated/parts/BFH.scad|docs/img/deck/part-BFH.png|--camera=0,0,0,24,-53,180,500 --viewall --autocenter
home-1800x1500|generated/parts/BFV.scad|docs/img/deck/part-BFV.png|--camera=0,0,0,24,-53,180,500 --viewall --autocenter
home-1800x1500|generated/parts/BSH.scad|docs/img/deck/part-BSH.png|--camera=0,0,0,24,-53,180,500 --viewall --autocenter
home-1800x1500|generated/parts/BSV.scad|docs/img/deck/part-BSV.png|--camera=0,0,0,24,-53,180,500 --viewall --autocenter
home-1800x1500|generated/parts/GW.scad|docs/img/deck/part-GW.png|--camera=0,0,0,24,-53,180,500 --viewall --autocenter
home-1800x1500|generated/parts/GF.scad|docs/img/deck/part-GF.png|--camera=0,0,0,24,-53,180,500 --viewall --autocenter
home-1800x1500|generated/parts/WC.scad|docs/img/deck/part-WC.png|--camera=0,0,0,24,-53,180,500 --viewall --autocenter
home-1800x1500|generated/parts/TC.scad|docs/img/deck/part-TC.png|--camera=0,0,0,24,-53,180,500 --viewall --autocenter
home-1800x1500|generated/parts/CH.scad|docs/img/deck/part-CH.png|--camera=0,0,0,55,0,25,500 --viewall --autocenter
home-1800x1500|generated/parts/CSL.scad|docs/img/deck/part-CSL.png|--camera=0,0,0,55,0,25,500 --viewall --autocenter
home-1800x1500|generated/parts/CSR.scad|docs/img/deck/part-CSR.png|--camera=0,0,0,55,0,25,500 --viewall --autocenter
home-1800x1500|generated/parts/CS.scad|docs/img/deck/part-CS.png|--camera=0,0,0,55,0,25,500 --viewall --autocenter
home-1800x1500|generated/parts/CN.scad|docs/img/deck/part-CN.png|--camera=0,0,0,55,0,25,500 --viewall --autocenter
home-1800x1500|generated/parts/JN.scad|docs/img/deck/part-JN.png|--camera=0,0,0,55,0,25,500 --viewall --autocenter
home-1800x1500|generated/parts/TSL.scad|docs/img/deck/part-TSL.png|--camera=0,0,0,55,0,25,500 --viewall --autocenter
home-1800x1500|generated/parts/TSR.scad|docs/img/deck/part-TSR.png|--camera=0,0,0,55,0,25,500 --viewall --autocenter
home-1800x1500|generated/parts/CMB.scad|docs/img/deck/part-CMB.png|--camera=0,0,0,55,0,25,500 --viewall --autocenter
home-1800x1500|generated/parts/CMH.scad|docs/img/deck/part-CMH.png|--camera=0,0,0,55,0,25,500 --viewall --autocenter
home-1800x1500|generated/parts/KP.scad|docs/img/deck/part-KP.png|--camera=0,0,0,55,0,25,500 --viewall --autocenter
home-1800x1500|generated/parts/HG.scad|docs/img/deck/part-HG.png|--camera=0,0,0,55,0,25,500 --viewall --autocenter
home-1800x1500|generated/parts/HS.scad|docs/img/deck/part-HS.png|--camera=0,0,0,55,0,25,500 --viewall --autocenter
bench-600|generated/parts/AFH.scad|docs/img/deck/part-AFH.png|--camera=0,0,0,24,-53,180,500 --viewall --autocenter
bench-600|generated/parts/AFV.scad|docs/img/deck/part-AFV.png|--camera=0,0,0,24,-53,180,500 --viewall --autocenter
bench-600|generated/parts/ASH.scad|docs/img/deck/part-ASH.png|--camera=0,0,0,24,-53,180,500 --viewall --autocenter
bench-600|generated/parts/ASV.scad|docs/img/deck/part-ASV.png|--camera=0,0,0,24,-53,180,500 --viewall --autocenter
bench-600|generated/parts/AC.scad|docs/img/deck/part-AC.png|--camera=0,0,0,55,0,25,500 --viewall --autocenter
home-1800x1500|deck/units.scad|docs/img/deck/unit-0.png|-D u=0 --camera=0,0,0,72,0,205,8000 --viewall --autocenter
home-1800x1500|deck/units.scad|docs/img/deck/unit-1.png|-D u=1 --camera=0,0,0,62,0,190,8000 --viewall --autocenter
home-1800x1500|deck/units.scad|docs/img/deck/unit-2.png|-D u=2 --camera=0,0,0,66,0,198,8000 --viewall --autocenter
home-1800x1500|deck/units.scad|docs/img/deck/unit-3.png|-D u=3 --camera=0,0,0,66,0,198,8000 --viewall --autocenter
home-1800x1500|deck/units.scad|docs/img/deck/unit-4.png|-D u=4 --camera=0,0,0,72,0,205,8000 --viewall --autocenter
home-1800x1500|generated/parts/H.scad|docs/img/deck/print-H.png|--camera=0,0,0,62,0,32,500 --viewall --autocenter
bench-600|deck/hero.scad|docs/img/deck/hero-bench.png|--camera=0,0,0,78,0,32,3000 --viewall --autocenter
```

**Create** `pdf/render_deck.py`:
```python
#!/usr/bin/env python3
"""Re-render the guide deck's illustrations listed in pdf/deck_renders.txt through cad/box.sh png."""
import argparse
import concurrent.futures
import os
import pathlib
import shlex
import subprocess
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parent.parent
LIST = ROOT / "pdf" / "deck_renders.txt"


def jobs(path, only):
    out = []
    for line in path.read_text().splitlines():
        if not line.strip() or line.startswith("#"):
            continue
        params, src, png, args = line.split("|")
        if not only or any(o in png for o in only):
            out.append((params, src, png, args))
    return out


def run(job):
    params, src, png, args = job
    start = time.time()
    p = subprocess.run(["cad/box.sh", "png", src, png, *shlex.split(args)], cwd=ROOT,
                       env={**os.environ, "PARAMS": params}, capture_output=True, text=True)
    return p.returncode, png, time.time() - start, (p.stdout + p.stderr)[-1500:]


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("only", nargs="*", help="only render outputs whose path contains one of these")
    ap.add_argument("--jobs", type=int, default=4, help="renders at once (default 4)")
    a = ap.parse_args(argv[1:])
    todo = jobs(LIST, a.only)
    failed = 0
    with concurrent.futures.ThreadPoolExecutor(a.jobs) as ex:
        for rc, png, dt, log in ex.map(run, todo):
            print(("ok   " if rc == 0 else "FAIL ") + f"{dt:5.1f}s {png}" + ("" if rc == 0 else "\n" + log), flush=True)
            failed += rc != 0
    print(f"{len(todo) - failed}/{len(todo)} images rendered")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
```

- [ ] **Step 2: Re-render the guide images**

Run: `cd ~/diy-window && python3 pdf/render_deck.py | tail -1 && python3 tools/generate.py params/bench-600.json > /dev/null`
Expected: `73/73 images rendered` (about 15 minutes, four at a time).

Look at `docs/img/deck/corner.png`, `joint.png` and `part-CMH.png`: the long edges are visibly rounded.

- [ ] **Step 3: Docs**

**Replace** in `docs/build-guide.md`:
```markdown
  Work joint by joint, before the sealant skins (about 10 minutes for most MS polymers; check the cartridge):
  1. Butter the face, close the joint onto its shims, clamp it, and drive that part's tube screw.
  2. Pull the shims, and fill and tool the voids they leave.
  3. Clear any squeeze-out from the seal and glazing kerfs, the magnet channel and the bead keyways.
- **Tube screws.** Drive one through the inside-face countersink of every segment, corner leg, node and shoe.
```
**with:**
```markdown
  Work joint by joint, before the sealant skins (about 10 minutes for most MS polymers; check the cartridge):
  1. Butter the face, close the joint onto its shims, clamp it, and drive that part's tube screw.
  2. Pull the shims, and fill and tool the voids they leave. Tool the sealant flush with the 0.8 mm bevel along the joint's edges, so each joint shows as a neat V line.
  3. Clear any squeeze-out from the seal and glazing kerfs, the magnet channel and the bead keyways.
- **Tube screws.** Drive one through the inside-face countersink of every segment, corner leg, node and shoe.
```

**Replace** in `docs/printing.md`:
```markdown
| Parts | Orientation |
|---|---|
| Segments (H, S, SW, JL, JU, T, TE, ML, MU, SH, SB, SBE, SV, NH, NV), TC | Standing on an end face, exactly as exported. No supports. |
| Corners (CH, CSL, CSR, CS, CN) | As exported. Supports on build plate only, for the rebate overhangs. |
| JN, TSL, TSR, and with bays SN, HN, TX, MSL, MST, MSH | On the outside face (the face that looks out of the window), so the dovetail slots and tongues print in plane and slide without binding. Supports on build plate only. |
| Beads (B*), sill nose (NS), acrylic spacers (A*) | Laid flat on their longest face. |
| Setting blocks, weep caps, cam parts, hinge leaves, keepers | Flat side down. |

```
**with:**
```markdown
| Parts | Orientation |
|---|---|
| Segments (H, S, SW, JL, JU, T, TE, ML, MU, SH, SB, SBE, SV, NH, NV), TC | Standing on an end face, exactly as exported. No supports. The 2 mm rounded long edges stand vertical, and each 0.8 mm joint bevel prints as four 0.2 mm layers. |
| Corners (CH, CSL, CSR, CS, CN) | As exported. Supports on build plate only, for the rebate overhangs. |
| JN, TSL, TSR, and with bays SN, HN, TX, MSL, MST, MSH | On the outside face (the face that looks out of the window), so the dovetail slots and tongues print in plane and slide without binding. Supports on build plate only. |
| Beads (B*) | Lying on their glass face (the face with the gasket kerf), so the rounded room-side edge prints on top. |
| Sill nose (NS), acrylic spacers (A*) | Laid flat on their longest face. |
| Setting blocks, weep caps, cam parts, hinge leaves, keepers | Flat side down. |

```

**Replace** in `docs/printing.md`:
```markdown
`bom/<name>-parts.csv` lists every part and how many to print, and `bom/<name>.md` has the filament estimate (run `python3 bom/build_bom.py <name>` after rendering). `cad/generated/parts.csv` is the same list for whichever window was generated last, and `cad/box.sh test` and `png` regenerate it for the bench window, so don't print from it.

The 1800 × 1500 home window needs 160 prints in 35 types, about 16.46 kg of exterior filament plus 3.89 kg of interior PETG (measured from the STLs on 2026-10-09). The same opening split into two bays for a 1200 × 900 mm sheet (`params/home-1800x1500-2bay.json`) needs 226 prints in 43 types, about 19.19 kg of exterior filament plus 4.81 kg of interior PETG (measured from its STLs on 2026-10-10). Print a test coupon (TC) and one segment of each profile first, and check the fit before committing a full spool.

## Acrylic sandwich size
```
**with:**
```markdown
`bom/<name>-parts.csv` lists every part and how many to print, and `bom/<name>.md` has the filament estimate (run `python3 bom/build_bom.py <name>` after rendering). `cad/generated/parts.csv` is the same list for whichever window was generated last, and `cad/box.sh test` and `png` regenerate it for the bench window, so don't print from it.

The 1800 × 1500 home window needs 160 prints in 35 types, about 16.33 kg of exterior filament plus 3.83 kg of interior PETG (measured from the STLs on 2026-10-11). The same opening split into two bays for a 1200 × 900 mm sheet (`params/home-1800x1500-2bay.json`) needs 226 prints in 43 types, about 19.03 kg of exterior filament plus 4.74 kg of interior PETG (measured from its STLs on 2026-10-11). Print a test coupon (TC) and one segment of each profile first, and check the fit before committing a full spool.

## Acrylic sandwich size
```

**Replace** in `docs/user-manual.md`:
```markdown
| Seals | Two continuous EPDM bulb loops round the sash; wedge gaskets both sides of the glass |
| Screen | Hinged, magnetic, fibreglass mesh, room side |
| Printed parts | 160 prints in 35 types: 16.46 kg exterior (tier 3, ASA-CF or PC-ABS, light colour) + 3.89 kg interior PETG |
| Glass thermal | About 2.7–3.0 W/m²K at the glass for double glazing (single glazing about 6). A design target, not a tested whole-window rating |
```
**with:**
```markdown
| Seals | Two continuous EPDM bulb loops round the sash; wedge gaskets both sides of the glass |
| Screen | Hinged, magnetic, fibreglass mesh, room side |
| Printed parts | 160 prints in 35 types: 16.33 kg exterior (tier 3, ASA-CF or PC-ABS, light colour) + 3.83 kg interior PETG |
| Glass thermal | About 2.7–3.0 W/m²K at the glass for double glazing (single glazing about 6). A design target, not a tested whole-window rating |
```

**Replace** in `README.md`:
```markdown
- [Test log](docs/test-log.md): bench-window tests to pass before the full-size build (with bays, on a two-bay bench window too; with V-slot cores, rows 10–12 as well)
- [Owner's manual](docs/user-manual.md): operation, cleaning, maintenance, troubleshooting and safety for a finished window
- [OpenWindow-Guide.pdf](OpenWindow-Guide.pdf): the whole job as a slide deck (sizing, printing, assembly, installation, owner's manual, BOM, tests). Rebuild it with `python3 pdf/build_deck.py`; its illustrations come from `cad/deck/*.scad` via `cad/box.sh png`
- [Web configurator](web/README.md): a local page that sizes and checks a window as you type, renders its parts on the Windows box and zips everything for that opening (`python3 web/server.py`)

```
**with:**
```markdown
- [Test log](docs/test-log.md): bench-window tests to pass before the full-size build (with bays, on a two-bay bench window too; with V-slot cores, rows 10–12 as well)
- [Owner's manual](docs/user-manual.md): operation, cleaning, maintenance, troubleshooting and safety for a finished window
- [OpenWindow-Guide.pdf](OpenWindow-Guide.pdf): the whole job as a slide deck (sizing, printing, assembly, installation, owner's manual, BOM, tests). Rebuild it with `python3 pdf/build_deck.py`; its illustrations come from `cad/deck/*.scad` via `cad/box.sh png`, and `python3 pdf/render_deck.py` re-renders all of them from `pdf/deck_renders.txt` after a geometry change
- [Web configurator](web/README.md): a local page that sizes and checks a window as you type, renders its parts on the Windows box and zips everything for that opening (`python3 web/server.py`)

```

**Replace** in `pdf/build_deck.py`:
````python
python3 pdf/build_deck.py
```
- Deck illustrations: `PARAMS=home-1800x1500 cad/box.sh png deck/<view>.scad docs/img/deck/<out>.png ...`
- Check one slide: `python3 pdf/build_deck.py --slide N --png out.png`
"""), md(f"""
````
**with:**
````python
python3 pdf/build_deck.py
```
- Deck illustrations: `python3 pdf/render_deck.py` (one line per image in `pdf/deck_renders.txt`)
- Check one slide: `python3 pdf/build_deck.py --slide N --png out.png`
"""), md(f"""
````

- [ ] **Step 4: Specs**

**Replace** in `docs/specs/2026-10-07-diy-window-design.md`:
```markdown
    - **Fallback:** a member that is too long for the stock, or fails its bending check, keeps its standard tube.
    - **Compatibility:** without the key every output is unchanged, apart from the new `VSLOT_*` lines in the `dims.scad` mirror.
```
**with:**
```markdown
    - **Fallback:** a member that is too long for the stock, or fails its bending check, keeps its standard tube.
    - **Compatibility:** without the key every output is unchanged, apart from the new `VSLOT_*` lines in the `dims.scad` mirror.
16. **Soft edges (2026-10-11).** Designed in `docs/specs/2026-10-11-soft-edges-design.md` and planned in `docs/plans/2026-10-11-soft-edges.md`.
    - **Profiles:** every profile's convex outside corners are rounded 2 mm (`EDGE_R`) before the functional cuts. A few corners next to a seal kerf or magnet channel stay sharp, listed in `sharp_corners()`.
    - **Joints:** every joint face along a member gets a 0.8 mm bevel in 0.2 mm layers.
    - **Hand parts:** the cam handle, cam base, keeper and hinge leaves are softened.
    - **Outputs:** every STL changes; the generator outputs don't, apart from four new dims lines; BOM filament weights drop about 1%.
```

**Replace** in `docs/specs/2026-10-11-soft-edges-design.md`:
```markdown

Date: 2026-10-11
Status: Draft for review

## 1. Goal
```
**with:**
```markdown

Date: 2026-10-11
Status: Implemented (plan: `docs/plans/2026-10-11-soft-edges.md`); amended while planning (§10)

## 1. Goal
```

**Replace** in `docs/specs/2026-10-11-soft-edges-design.md`:
```markdown
- **Cord-groove lip:** at the joint face, the lip outside the foam-cord groove is 0.7 mm instead of 1.5 mm, over the bevel's 0.8 mm depth. The lip is backed by the full section below it, and the sealant fills the V. If it chips on the test coupon, the bevel drops to 0.6 mm (one `dims.json` value).
- **First-layer bevel:** the bottom end of a standing segment is bevelled on the bed. A 0.8 mm bevel is smaller than most elephant's-foot, so it should print cleanly and hide that foot.
```
**with:**
```markdown
- **Cord-groove lip:** at the joint face, the lip outside the foam-cord groove is 0.7 mm instead of 1.5 mm, over the bevel's 0.8 mm depth. The lip is backed by the full section below it, and the sealant fills the V. If it chips on the test coupon, the bevel drops to 0.6 mm (one `dims.json` value).
- **First-layer bevel:** the bottom end of a standing segment is bevelled on the bed. A 0.8 mm bevel is smaller than most elephant's-foot, so it should print cleanly and hide that foot.

## 10. Amendments (2026-10-11, from implementation planning)

Each was checked in a scratch build: CAD tests, box renders of all four windows, section and close-up views, the bed-fit envelope test and the BOM diff.

1. **Sharp corners.** The corner check found these and nothing else. Each one keeps its sharp edge:
   - **Fin tips beside the outer seal kerf.** Rounding them would leave a 0.5 mm lip at the kerf mouth. That's the upper jamb and head (`sash_rebate`), the transom, and both sides of the upper mullion.
   - **Room-face corners next to a magnet channel.** The channel ends 0–3 mm from them: the `sash_rebate` inner stop, the transom body, and both sides of the upper mullion.

   The transom cross-node (TX) keeps the same room-face corner sharp. The check samples each 2 mm arc and measures its distance to every cut, chambers included. The sill's sloped corners are handled as a polygon.
2. **Beads.** Only the room-side edge facing the glass is rounded. The edge against the frame stays sharp, because the bead's key tongue starts within 1 mm of it. Beads get no joint bevel: their segments butt without sealant.
3. **Hinge leaves.**
   - **HG:** the plate rounds only its free corners, so it still meets its wall without a notch. Its 3 mm wall is rounded 1 mm (`WALL_R`), because 2 mm would delete it.
   - **HS:** its 5 mm wall takes the full 2 mm.
4. **Cam handle.**
   - **Top edge:** the softening is a 1.5 mm quarter-round (`TOP_R`) on the lever, knob and hub tops, built in 0.25 mm steps.
   - **Plan rounding:** in plan, the lever's corners sit inside the hub and knob, so `HANDLE_R` changes almost nothing that shows.
5. **Bed-fit envelopes.** Three entries change, and the table is re-measured:
   - **S and SW:** 58 → 57.68 mm. The sill's acute outside corner is rounded.
   - **CMH:** 86.151 → 86.122 mm, from the rounded knob.
6. **Keyway lip at joint faces.** In the last 0.6 mm of each segment end, the bevel also trims the 0.8 mm bead-keyway lip. Bead retention comes from the length of the keyway, so this is harmless.
7. **Guide images.** The deck job list was recovered from the original renders. Re-rendering three images with it from the unchanged repo gave byte-identical PNGs.
```

- [ ] **Step 5: Rebuild the guide PDF**

Run:
```bash
cd ~/diy-window && python3 pdf/build_deck.py --check | tail -1
cd ~/diy-window && python3 pdf/build_deck.py | tail -2
```
Expected: `overflow: none`; then `wrote pdf/openwindow-deck.html (77 slides, …)` and `wrote OpenWindow-Guide.pdf (… KB, 77 pages, …)`.

- [ ] **Step 6: Final checks and clean-up**

Run:
```bash
cd ~/diy-window && cad/box.sh test
cd ~/diy-window/tools && python3 -m unittest discover -p 'test_*.py' 2>&1 | grep -E '^(Ran|OK|FAILED)'
```
Then run the compatibility check (Task 0), then:
```bash
cd ~/diy-window && rm -rf .soft-baseline .soft-after .soft-review params/zz-soft*.json cad/stl/zz-soft* && ls params cad/stl && python3 tools/generate.py params/bench-600.json | head -1
```
Expected:
- `11 test files passed`; `Ran 346 tests`, `OK`; `BYTE-IDENTICAL`;
- `params` lists `bench-600.json  home-1800x1500-2bay.json  home-1800x1500.json  my-window.json`;
- `cad/stl` lists `bench-600  home-1800x1500  home-1800x1500-2bay  my-window`;
- `bench-600: 37 part types, 98 prints -> …/cad/generated`.
