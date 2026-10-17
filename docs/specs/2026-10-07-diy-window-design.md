# OpenWindow — 3D-printable modular window — Design Spec

Date: 2026-10-07
Status: Approved 2026-10-07; amended 2026-10-08, 2026-10-09 and 2026-10-10 (§12)

## 1. Goal

A full replacement for basic single-glazed, aluminium, horizontal-sliding windows, mostly printed on a
Bambu Lab P1S (256 × 256 × 256 mm build volume), using only common hardware-store extras. It must:

- cut heat loss (single glazing ≈ 6 W/m²K → double glazing ≈ 2.7–3.0 W/m²K at the glass)
- be airtight when closed (compression seals, not brush pile)
- keep insects out
- be open source and parametric, so others can build it for their own openings

### Scope of v1

| Item | v1 decision |
|---|---|
| Replacement type | Full replacement: old window removed down to the wall opening |
| Wall type | Brick veneer (timber stud frame + brick skin), typical Melbourne |
| Opening size | 1500–1800 mm wide × 1200–1500 mm high |
| Layout | Top awning strip (≈ 450 mm high, full width) over one large fixed pane |
| Operation | Top-hinged awning on stainless friction stays, two printed cam locks |
| Glazing | Universal 24 mm pocket: IGU, acrylic sandwich, or 16 mm twin-wall PC |
| Insect screen | Inside, hinged, magnetic-seal frame over the awning opening |

### Out of scope for v1 (planned later)

- Horizontal slider sash (option B), designed to fit the same outer frame
- Weatherboard / clad timber-frame fixing kit
- Solid / double brick fixing kit (masonry anchors)
- Other layouts (twin side awnings, centre awning, twin top awnings)

## 2. Structure

### 2.1 Members

Outer frame: head, sill, two jambs, one full-width transom. Sash: four-sided frame. Screen: four-sided frame.

Every structural member is built the same way:

- A **continuous metal tube core** runs the full length of the member.
- **Printed shell segments**, each ≤ 240 mm long, slide over the tube.
- Every segment is screwed through into the tube at its middle (self-tapping stainless screws; tek screws into the steel transom).
- **Printed corner blocks** take the tube ends and are screwed to them.

| Member | Core | Reason |
|---|---|---|
| Head, sill, jambs | 20 × 20 × 1.6 aluminium SHS | Screwed to the reveal every 400 mm, so no free span |
| Transom | 40 × 20 × 1.6 galvanised steel RHS, 40 mm through the window depth | Only member spanning 1.8 m unsupported |
| Sash | 20 × 20 × 1.6 aluminium SHS | Carried at the jambs by the friction stays |
| Screen | 10 × 10 aluminium SHS in every rail of two or more segments; a single-segment rail is printed only (§12) | Light load, but the tube is what joins the segments |

**Transom check** (simply supported over 1.8 m, ≈ 0.7 m tributary height, 0.7 kPa serviceability
wind): aluminium 50 × 25 × 1.6 deflects ≈ 11 mm, while steel 50 × 25 × 1.6 deflects ≈ 3.5 mm. The
IGU edge-deflection limit is about L/175 (≈ 10 mm), so the transom must be steel. The generator
re-checks this for each opening and warns if span/175 is exceeded.

### 2.2 Segment joints

- Butt joint with a cord groove on both end faces (§12), taking one 4 mm closed-cell foam cord per joint.
- The joint only aligns and seals; the tube carries the load.
- A sealant bead at each joint closes off the tube cavity, so water in the glazing pocket can't get into it.
  The sealant also fills the band outside the cord ring, and must be rated for ±50 % movement (§12).
- Thermal expansion: PETG/ASA ≈ 65–95 µm/m·K. A 240 mm segment moves about 0.8–1.1 mm over a 50 °C
  swing, and each joint takes its own share. One long printed part would bow instead. Each joint is
  therefore assembled at about 20 °C with a 1 mm gap, and the segments are printed short by one gap per
  joint (§12).

### 2.3 Thermal break

- The tube sits in a pocket fully enclosed by plastic.
- At least 6 mm of printed shell between the tube and either the inside or the outside face.
- No metal part (screw, tube, insert) may bridge from the outside face to the inside face.
  Friction-stay and lock screws go into the core from one side only.

### 2.4 Profile

- Frame depth 63 mm and frame face 58 mm (slimmed on 2026-10-08, §12), which suits a typical brick-veneer reveal.
- The sash pocket was sized for a future slider sash (option B) to fit the same outer frame. That check predates the slimming, so the option-B slider pocket must be re-checked against the 63 mm profile before option B is designed.
- `profile.scad` is the single source of truth for every cross-section. Segments, corners, beads and
  the sill nose are all extrusions or cuts of these cross-sections.

### 2.5 Weight (1.8 × 1.5 m opening, IGU 4/16/4 ≈ 20 kg/m²)

- Fixed pane ≈ 32 kg. It sits on printed setting blocks at the quarter points, which carry the load
  straight down into the sill, packers and wall. There is a packer under the sill at each quarter point.
- Sash glass ≈ 13 kg, plus the frame. It must stay within the rating of the chosen friction-stay
  pair. The generator picks the stay size and warns if the rating is exceeded.

## 3. Glazing

Universal pocket for a 24 mm unit, with 3 mm wedge gaskets on each face. Glazing beads are swappable,
one variant per glazing type:

| Glazing | Make-up | Bead variant | Notes |
|---|---|---|---|
| IGU (glazier) | 4/16/4 or 5/14/5, low-E/argon optional | Standard | Best thermal and clarity, heaviest |
| Acrylic sandwich | 4 mm + 16 mm printed spacer + 4 mm = 24 mm | Standard | Printed spacer has a desiccant channel; unit can be opened for cleaning |
| Twin-wall PC | 16 mm sheet + 8 mm printed packer | Packer | Translucent; suits bathrooms and laundries |

- The glass sits on printed setting blocks. The bottom of the glazing pocket slopes outward to two
  weep holes with printed flap caps (drained, ventilated pocket).

## 4. Seals and drainage

### 4.1 Sash

- **Outer weather seal:** an EPDM bulb gasket in a printed kerf groove on the frame rebate.
- **Inner air seal:** an EPDM bulb gasket in a kerf on the frame's inner stop, closed on by the sash's inner lip (§12).
- Use off-the-shelf EPDM. Printed TPU is allowed for prototypes only: it takes a permanent set under
  constant compression.
- The chamber between the two seals is pressure-equalised and drains through the weep slots in the
  transom fin at the two TE segments. The SBE weeps in the sash bottom rail drain the sash's own glazing
  pocket.
- **Two printed cam locks,** one near each end of the sash, give even compression along the full width.
  Each keeper sits directly over its cam pivot along the run (§12).

### 4.2 Sill

- Top surface slopes 8° outward.
- A printed sill nose clips on, with a drip groove underneath, projecting 15 mm past the frame's
  outside face. It runs over the sill corners to within 17 mm of each frame edge.

### 4.3 Wall interface (brick veneer)

1. **Sill tray:** 150 mm butyl flashing tape laid in the opening before installation, turned up 30 mm at
   the back, across the 63 mm frame depth and running at least 50 mm out onto the brick sill.
2. **Head:** the existing head flashing over the lintel stays and must lap over the new frame head.
3. **Fixing:** the frame sits on plastic packers, with one under each sill corner and under each
   fixed-pane setting block. It's screwed through the sill, jambs and head into the timber reveal and
   studs, every 400 mm and within 150 mm of each corner. Screws go through solid printed columns, never
   straight through a thin wall. The sill, lower-jamb and node fixings open into the drained glazing
   pocket or outside the sash seal, so each is bedded in MS polymer with its counterbore filled.
4. **Outside:** a 6–10 mm gap to the brickwork, filled with backer rod and MS-polymer sealant.
5. **Inside:** low-expansion window foam, then the architraves go back on.
6. Weep holes and drip edges must never be sealed over. The install guide calls this out.

## 5. Insect screen

- An inside frame covering the awning opening, with fibreglass or aluminium mesh held by a printed
  spline groove.
- Hinged at the top on printed pin hinges, so it swings up and inward to reach the sash.
- It seals against flexible magnetic strip in a channel on the inside face of the frame, and shuts
  itself under gravity plus the magnets. The screen and frame strips are a matched A/B pair, or a magnet
  strip against a steel strip.
- With the screen open, the sash is pushed out by hand. The friction stays hold it in any position.

## 6. Materials

Requirements are stated as numbers; filament names are examples only. Design surface temperatures
for Melbourne: about 50–55 °C on light colours, about 75–80 °C on dark colours in full afternoon sun.

**Rule: HDT (heat-deflection temperature @ 0.45 MPa) must be at least 15 °C above the expected
surface temperature, and exterior parts must be UV-stable or coated.**

| Tier | Exposure | Min HDT | UV | Examples |
|---|---|---|---|---|
| 1 | South-facing / shaded, light colour | ≥ 70 °C | Stable or painted | PETG + exterior acrylic paint, ASA |
| 2 | East / part sun, light colour | ≥ 90 °C | Inherently stable | ASA |
| 3 | North / west full sun, or any dark colour | ≥ 105 °C | Inherently stable | ASA-CF, PC-ABS (painted) |

- A dark colour moves any exposure up one tier. Light colours are strongly recommended.
- Parts that face only the room (inside beads, screen frame, cam lock handles, inner covers) are
  PETG in every tier.
- P1S: ASA and PC need the enclosure closed. CF filaments need a hardened-steel nozzle.

## 7. Printing

- Segments print standing up: the profile cross-section lies flat on the bed, and each segment is at
  most 240 mm tall.
- At least 5 walls, 15% gyroid infill, and at least 5 top and bottom layers. Frame and sash bodies are hollow multi-chamber profiles with 2.5 mm walls (§12).
- Heat-set brass inserts at every machine screw that is re-tightened: cam bases, keepers, cam pivots
  and screen hinges. Friction stays screw straight into the tube, beads snap in, and the frame fixings go
  through solid printed columns.
- Estimate for a 1.8 × 1.5 m window: 160 prints in 35 part types, about 16.46 kg of exterior filament plus 3.89 kg of interior PETG after slimming (21.9 kg before), roughly 550+ print hours (measured from the rendered STLs on 2026-10-09; see §12).

## 8. Parametric generator

OpenSCAD, run on the Windows build box. No installs on the Mac.

**Inputs** (`params/<name>.json`, one file per window; `name` matches the file name):
- `opening_w`, `opening_h`, `fix_gap`
- `awning_h`
- `glazing` = `igu` | `acrylic` | `twinwall`
- `tier` = 1 | 2 | 3
- optional: `screen`, `bed` (web configurator spec §3), and `max_pane`, `bays` (mullions and bays, §12.13)

**Outputs:**
- **STL set:** segments are split evenly, so there are no short filler pieces, and every segment is
  ≤ 240 mm. Each part has an engraved type ID, e.g. `H`, matching the guides. Identical parts share one
  ID and one STL.
- **Cut list CSV:** tube lengths per member.
- **Glass:** the IGU order size for the glazier, or acrylic and twin-wall cut sizes.
- **BOM CSV:** EPDM metres, foam cord, screws, inserts, friction-stay size, magnetic strip, mesh,
  sealant, flashing tape. `bom/build_bom.py` writes it per window as `bom/<name>.csv`/`.md`, with the
  cut list, glass and part list alongside (`bom/<name>-cutlist.csv`, `-glass.csv`, `-parts.csv`).
- **Checks:** transom deflection against span/175, sash weight against the friction-stay rating,
  and segment length ≤ 240 mm. A failed check produces a clear warning.

## 9. Repository layout

```
~/diy-window/
  README.md
  params/     one JSON file per window
  cad/        dims.json, profile.scad, parts/, lib/, tests/, box.sh, generated/, stl/<name>/
  tools/      window.py, generate.py, STL checker, Python tests
  bom/        build_bom.py, per-window BOM, cut list, glass and part list
  docs/       specs/, plans/, printing, build guide, install guide, test log, img/
```

A printable PDF build guide (`pdf/`) is planned for later.

## 10. Verification

1. **Bench prototype:** a 600 × 600 mm window with acrylic glazing, the full profile set, one cam lock.
2. **Water test:** hose spray on the outside face with the sash closed, about 15 minutes. Pass means
   no water on the inside.
3. **Air test:** smoke pencil around both seal lines and the segment joints. Pass means no visible draw.
4. **Heat/creep test:** a black-painted segment with a screwed boss, held at 80 °C under a lamp for
   24 h. Pass means no visible distortion and the screw still holds torque.
5. **Sash load test:** twice the sash weight hung from the open sash for 1 h. Pass means no permanent
   set at the stays or the corners.
6. **Full-size build** only after steps 1–5 pass. Glass is ordered from `bom/<name>-glass.csv`.

## 11. Open questions

- Friction-stay brand/model and its load rating for a 1.8 m × 450 mm sash (≈ 16 kg, 400 mm stays).
  The stay must fold into the 13 mm sash gap between the jamb fin top (28 mm from the outside face) and
  the sash lip (46 mm), and its screws must hit the sash tube (17–37 mm). That means a stack of
  13 mm or less, a track and arm no more than 14 mm wide, centred 35–35.5 mm from the outside face
  (`STAY_W` in `cad/dims.json`, checked in `profile_test.scad`). If no stay with the needed rating is
  that narrow, the stay cavity (fin, lip, `SASH_GAP`) or the sash tube has to move before printing.
- Exact brick-veneer reveal depth on the target house: the profile depth is now fixed at 63 mm, so the
  reveal must be at least 63 mm deep (install guide step 2).
- Screen frame span at 1.8 m: resolved. Every screen rail of two or more segments gets the 10 × 10
  aluminium core (§12).

## 12. Amendments (2026-10-08, from implementation planning)

Found while turning this spec into the plan (`docs/plans/2026-10-08-diy-window-v1.md`), each one checked by rendering on the build box:

1. **Segment joints** are butt joints with a foam-cord groove on both end faces, not stepped laps. Every segment of a member is then identical, and the cord ring also seals the tube cavity.
2. **Glazing beads snap** into an undercut keyway, not screwed into inserts. Bead pieces and segments split at different points, so inserts would not line up.
3. **The inner sash gasket** sits in a kerf on the frame's inner stop, not on the sash lip.
4. **Sash gap:** a uniform 13 mm on all four sides, for the friction-stay cavity, so one sash profile works on every side.
5. **Transom:** fits after the frame is fixed. Its dovetailed shoes slide into jamb nodes from the room side, held by two lock screws per end.
6. **Body sizes:** the transom body is 34 mm (38 mm before the slimming in item 9) and the sash body is 33 mm, so the 6 mm tube-to-face rule (§2.3) holds.
7. **Screen:** on the transom, its magnet line runs along the lower half of the inside face, so the cam locks sit inside the closed screen.
8. **Material and print time** are much higher than first estimated (§7). Even as hollow, uPVC-style profiles, a 70 mm-deep frame needs about 1.5 kg of plastic per metre.
9. **Slimmed profiles** to cut material:
   - perimeter tube 25 → 20 mm (screwed to the reveal every 400 mm, so stiffness doesn't matter);
   - frame body 45 → 40 mm and face 63 → 58 mm;
   - depth 70 → 63 mm (the inner stop only needs room for its seal kerf and the magnet strip);
   - transom steel 50 × 25 → 40 × 20, which deflects about 6.2 mm against a 9.5 mm limit for the 1.8 m home window (the 50 × 25 gave about 3 mm, so less margin);
   - glazing beads 14 → 10 mm thick.

   The §2.1 table and the transom check numbers above predate this change; `tools/window.py` re-checks the transom for every opening.
10. **Geometry fixes from the CAD review (2026-10-09):**
    - **Tube sockets.** Each tube runs into its corner to a solid stop, at a depth set per member: 28 mm for frame tubes, 21 mm for sash, 12 mm for screen. The single 30 mm socket made the two sash tubes collide inside each sash corner.
    - **Screw positions.**
      - Head and upper-jamb fixing screws run at y = 48, between the two seals, so they no longer open outside the outer weather seal.
      - Every fixing and tube screw has a solid column through the air chambers (§4.3.3).
    - **Segment ends.** Each end has a 4 mm solid cap with a continuous cord-groove ring around the body outline and the tube pocket.
      - The ring covers the main body only, not the stop legs, fins or inner stop.
      - On the transom the ring cannot cross the thin web between the bead keyway and the steel tube, so the joint sealant must bridge that web.
    - **Seals at the transom ends.** The transom shoes carry the outer-seal fin, both seal kerfs, the glazing kerf and the screen magnet channel around the junction with the jambs.
11. **Final review (2026-10-09).** Builder-level fixes. Each was checked against the CAD, and the stale text above is corrected in place.
    - **Thermal joint gap (§2.2).** At zero gap, nothing absorbed the 0.8–1.1 mm per joint that §2.2 relies on.
      - Each frame, transom and sash joint is now assembled at about 20 °C on 1 mm shims, which are removed once the tube screws are in.
      - `tools/window.py` shortens each segment by one gap per joint, so member lengths, tube cuts, glass and beads are unchanged.
      - The 3 mm cord could not seal that gap: two 1.5 mm half-grooves plus 1 mm make a 4 mm cavity. The joint cord is now 4 mm closed-cell foam, squeezed into the 3 mm-wide groove. The transom shoe seams keep 3 mm cord against the flat node face.
      - The joint sealant now also covers the stop, fin and inner-stop end faces, because the cord ring does not reach them and the inner stop is on the air-seal line.
    - **Screen frame.** Every rail of two or more segments gets the 10 × 10 core, because the tube is what joins the segments. Single-segment rails are printed only. The CN corners are epoxied, and screwed into the tube where there is one.
    - **Fasteners checked against the parts.**
      - M4 screws in the 8 mm blind insert holes are M4 × 10 through the 3–4 mm cam base, keeper and hinge leaves, and M4 × 8 through the cam-pivot washer.
      - The transom lock screws are M4 × 16 (an M4 × 20 reached the floor of the 22 mm pilot exactly).
      - The hinge pins are M4 × 50 through the 40 mm knuckle stack.
      - Frame tube screws are 8g × 30 (8g × 25 barely cleared the 20 × 20 tube wall), with tek screws into the steel transom.
      - Fixings are 10g × 75, which leaves about 30 mm in the timber.
      - `HINGE_BOSS_X` moved from 25 to 21 mm: no M4 screw head could seat beside the HG leaf's upright.
    - **Wall interface (§4.3.3 said jambs and head only).**
      - The sill is screwed too. Its fixings, the lower-jamb fixings and both node fixings open into the drained glazing pocket or outside the sash seal, so each is bedded in MS polymer with its counterbore filled.
      - A packer goes under each fixed-pane setting block (§2.5).
      - The sill tray tape is 150 mm wide.
    - **Install order.** Several steps could not be done in the order the guides gave.
      - The EPDM seal loops and the frame magnet strip go in after the transom.
      - Friction stays go on the sash at the bench, and their tracks go on the jambs only after the frame fixings, which the tracks would cover.
    - **Sill nose.** The nose now runs over the sill corners, re-split over its own length, stopping where the corner's key slot ends (16 mm in, plus one joint gap).
    - **Corrected in place:** §2.1 (screen core, screw per segment), §2.2, §2.4 (option-B pocket to re-check after slimming), §2.5, §4.1 (chamber drains via the TE fin weeps), §4.2 (nose is 15 mm past the frame face), §4.3, §5, §7 (inserts; 160 prints, 16.46 kg + 3.89 kg), §8 (params JSON, type IDs, per-window outputs), §9, §10 and §11 (depth is 63 mm, not 70 mm).
12. **Final review, round 2 (2026-10-09).**
    - **Cam and keeper alignment.** Each cam pivots at its TE segment's middle, but the keeper sat at its SBE segment's middle, 39.4 mm further along on the home window (23.0 mm on the bench). The keeper lip is ±10 mm and the flag ±13.7 mm, so the locks could not engage.
      - `tools/window.py` now works out that offset (`keeper_dz`) and checks it is in range (`cam_keeper`).
      - Each SBE carries two insert pairs, `keeper_dz` either side of its middle. One part serves both ends of the rail, in the same orientation, so each keeper uses the outer pair; IDs and quantities are unchanged.
      - `segment()` takes `boss_dz` and asserts it lies between the tube-screw clearance (20.6 mm on the sash) and the end-cap limit.
      - `cam_test.scad` checks the lip stays over the flag within `CAM_ALIGN_TOL` = 1 mm, and the Python tests check the boss centres agree for both windows.
    - **Joint sealant.** At a 1 mm gap, the 1.5 mm band outside the cord ring is an open slot. Along the opening-side edge it bypasses both glazing gaskets and both sash seals.
      - The whole band is now sealed, continuous with the stop, fin and inner-stop end faces, and the shim voids are tooled after the shims come out.
      - The sealant must be rated for ±50 % movement.
      - Test-log rows 2 and 3 now target the opening-side edge of the joints.
    - **Friction-stay envelope.** Recorded in §11, with `STAY_W` = 14 mm. The guides' stay screw zones did not fit that cavity and now follow it.
    - **Transom length.** The transom is dry-fitted at the bench. At install it is sealed and screwed with its shims set to the node spacing measured in the fixed frame.
13. **Mullions and bays (2026-10-10).** `docs/specs/2026-10-10-mullion-bays-design.md`, planned in `docs/plans/2026-10-10-mullion-bays.md`. With `max_pane`, the window splits into equal bays divided by mullions. Each bay has its own fixed pane, awning sash and screen, and the transom stays one member across the full width.
    - New parts: sill and head nodes (`SN`, `HN`), a transom cross-node (`TX`), mullion shoes (`MSL`, `MST`, `MSH`) and segments (`ML`, `MU`), each mullion on a 40 × 20 steel tube.
    - The dovetail tees use a 4 mm mullion dovetail (`MULLION_DOVE_D`), not the jamb node's 6 mm one, because the transom body leaves only 6.7 mm of shell over its tube. The mullion lock screws sit 3 mm into the node (`LOCK_U`), like the jamb node's.
    - The transom is checked over its full span, with each mullion's reaction as a point load: the dovetails carry no moment, so the mullions can't prop it. That gives 6.8 mm against 9.5 mm for the home opening in two bays.
14. **Configurable acrylic sandwich (2026-10-10).** With acrylic glazing, the optional params `acrylic_t` (2-6 mm, default 4) and `acrylic_gap` (8-16 mm, default 16) set the panel thickness and air gap. The sandwich must fit the unchanged 24 mm pocket: the beads deepen by 24 − (2·t + gap) and the spacer bars follow the gap. The frame depth stays 63 mm because it is set by the sash seal stack and the friction-stay cavity, not by the glazing, so a thinner sandwich saves acrylic weight and cost but not plastic. Without the keys every output is unchanged.
15. **V-slot 2020 cores (2026-10-10).** Designed in `docs/specs/2026-10-10-vslot-core-design.md` and planned in `docs/plans/2026-10-11-vslot-core.md`.
    - **Cores:** with `"core": "vslot"`, the cores are V-slot 2020, with the transom and mullions as a pair, held with M5 T-nuts.
    - **Joins:** the head, sill and lower jambs join pieces inside a segment.
    - **Stays:** the head and upper-jamb pocket moves 3 mm outward, so the friction-stay screws bite solid metal.
    - **Fallback:** a member that is too long for the stock, or fails its bending check, keeps its standard tube.
    - **Compatibility:** without the key every output is unchanged, apart from the new `VSLOT_*` lines in the `dims.scad` mirror.
16. **Soft edges (2026-10-11).** Designed in `docs/specs/2026-10-11-soft-edges-design.md` and planned in `docs/plans/2026-10-11-soft-edges.md`.
    - **Profiles:** every profile's convex outside corners are rounded 2 mm (`EDGE_R`) before the functional cuts. A few corners next to a seal kerf or magnet channel stay sharp, listed in `sharp_corners()`.
    - **Joints:** every joint face along a member gets a 0.8 mm bevel in 0.2 mm layers.
    - **Hand parts:** the cam handle, cam base, keeper and hinge leaves are softened.
    - **Outputs:** every STL changes; the generator outputs don't, apart from four new dims lines; BOM filament weights drop about 1%.
