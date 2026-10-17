# OpenWindow: soft edges (Design Spec)

Date: 2026-10-11
Status: Implemented (plan: `docs/plans/2026-10-11-soft-edges.md`); amended while planning and implementing (§10)

## 1. Goal

Make the printed window look and feel finished rather than sharp:
- **Rounded profile edges:** 2 mm rounded long edges on every profile.
- **Joint bevel:** a small bevel at every segment joint.
- **Hand-touched parts:** softened edges on the parts you touch.

Everything that does a job keeps its exact shape: seals, glazing, tubes, joints and fixings.

## 2. Decisions

| Topic | Decision |
|---|---|
| Edge style | Rounded, radius `EDGE_R` = 2 mm |
| Where | Every convex outside corner of each profile cross-section: frame (glazing, sash rebate, sill), transom, mullions, sash, screen. Beads on their room-side edges |
| Concave corners | Stay sharp |
| Functional cuts | Stay sharp and unchanged: tube pockets, seal and glazing kerfs, bead keyways, magnet channels, sill-nose keys, spline groove, dovetail slots, fixing holes, screw holes |
| Joints | A 0.8 mm bevel (`JOINT_BEVEL`) round the outside outline of every end face that butts another part along a member, built in 0.2 mm steps (`BEVEL_STEP`, one print layer) |
| Hand-touched parts | Cam handle (lever and knob) rounded 3 mm (`HANDLE_R`) in plan, with a softened top edge; cam base, keeper and both hinge leaves rounded 2 mm on their plate corners |
| Not changed | The window's outer frame and sash corners in the window plane, the sill nose, weep caps, setting blocks, acrylic spacers |
| Outputs | Every STL changes on purpose. Generator, BOM and CSV outputs are unchanged except the filament weights |

## 3. Geometry rules

### 3.1 Profile rounding

- **Method:** each profile's base shape (the union of its body, fin, stop, lip and flange rectangles, or the sill polygon) is rounded before any functional cut is subtracted. Rounding means shrink by `EDGE_R`, then grow back with radius `EDGE_R`. This rounds convex corners only; concave corners and every cut stay exactly as they are.
- **Thin features:** every base feature must be at least `2 × EDGE_R` thick, or the shrink step would delete it. The thinnest base features today are 6 mm (fins, stops, lips, flanges), so 2 mm is safe.
- **Chambers:** with `EDGE_R` ≤ `CHAMBER_WALL` (2.5 mm), the wall between a rounded corner and a chamber stays at least `CHAMBER_WALL`.
- **Cuts near a corner:** where a functional cut ends within `EDGE_R` + `MIN_SKIN` of a rounded corner, the wall between them would taper below `MIN_SKIN`. That corner keeps its sharp edge instead: the original corner square is added back after rounding. One table per profile lists these exception corners, and the CAD tests check it.
- **Inheritance:** every part built from a profile picks the rounding up automatically: segments, corner-block legs, shoes and the test coupon. The V-slot geometry (`core`) is unaffected: it moves the tube pocket only.

### 3.2 Parts that continue a profile's outline

- **Node outlines:** in-line nodes are plain blocks today (JN; with bays, SN, HN and TX). Their cross-section outline gets the same `EDGE_R` rounding before their cuts, so at each joint their outline matches the segments either side.
- **Fin stubs:** small box stubs that continue a fin or stop across a joint (the transom and mullion shoes' fin stubs) get the same rounding on the edges that continue a rounded profile edge.
- **The rule:** at every joint along a member, the two outlines that meet match within 0.1 mm, apart from the bevel.

### 3.3 Joint bevel

- **Where:** at every end face that butts another part along a member, the outer outline gets a 0.8 mm × 45° bevel, built as 4 layers of 0.2 mm, each one stepped in by 0.2 mm. The end faces are:
  - both ends of every segment, the screen's included;
  - the leg ends of corner blocks that meet a segment;
  - both ends of nodes;
  - the segment-side end of transom and mullion shoes.
- **Outline only:** the bevel follows the outer outline only, which includes the mouths of kerfs, keyways and channels. It does not touch the tube pocket or any closed hole.
- **Clearance:** it stays inside the 1.5 mm `CORD_INSET`, so it never cuts into the foam-cord groove. It does thin the groove's outer lip at the very face: 0.7 mm at the face (`CORD_INSET` − `JOINT_BEVEL`), widening to the full 1.5 mm at 0.8 mm deep.
- **Result:** each sealed joint reads as a neat V line, with the sealant sitting inside it.

### 3.4 Hand-touched parts

- **Cam handle (CMH):**
  - **Lever and knob:** the corners in plan are rounded `HANDLE_R` (3 mm), and the top edge is softened by 1.5 mm.
  - **Unchanged:** the flag ramp, the hub and its bore.
- **Cam base (CMB):** the plate corners in plan are rounded 2 mm. The boss, insert hole and countersinks are unchanged.
- **Keeper (KP):** the plate and post corners in plan are rounded 2 mm. The lip that the flag rides on is unchanged.
- **Hinge leaves (HG, HS):** the plate and wall corners in plan are rounded 2 mm. Knuckles, pin hole and screw holes are unchanged.
- **Printing:** these parts print flat side down, so their rounded edges are vertical or on top, with no overhang.

### 3.5 Dimensions

New `cad/dims.json` keys, mirrored in `cad/generated/dims.scad`:

| Key | Value |
|---|---|
| `EDGE_R` | 2.0 |
| `JOINT_BEVEL` | 0.8 |
| `BEVEL_STEP` | 0.2 |
| `HANDLE_R` | 3.0 |

## 4. Printing

Orientation is unchanged: segments stand on an end face, so the rounded edges are vertical. One clarification for beads goes into `docs/printing.md`: they lie on their glass face (the face with the gasket kerf), so the rounded room-side edges print on top. The bevel steps are one layer each, so they print as a clean bevel at 0.2 mm layers.

## 5. Checks

New asserts in `cad/tests/`:
- **Thickness:** every base feature is at least `2 × EDGE_R` thick (per profile, from the dims).
- **Chamber walls:** `EDGE_R` ≤ `CHAMBER_WALL`.
- **Cuts near corners:** each functional cut is either at least `EDGE_R + MIN_SKIN` from every rounded convex corner of its profile, or that corner is in the profile's exception table.
- **Bevel clearance:** `CORD_INSET` − `JOINT_BEVEL` ≥ 0.6 mm, so the bevel never reaches the cord groove and leaves a lip outside it.
- **Bevel steps:** `JOINT_BEVEL` is a whole number of `BEVEL_STEP`s.
- **Hand parts:** each hand-part radius fits its plate (radius ≤ half the plate's smaller side).

Existing tests keep passing unchanged.

## 6. Outputs and compatibility

- **STLs:** every STL changes. All four windows are re-rendered: bench-600, home-1800x1500, home-1800x1500-2bay, and the owner's my-window, whose params are not touched. Every part must pass `check_stl`.
- **Generator, BOM and CSV:** outputs are byte-identical except:
  - the new dims lines in `dims.scad`;
  - the filament weights in each `bom/<name>.md` and `.csv`.

  `docs/printing.md`'s quoted weights are updated.
- **Bed-fit envelopes:** unchanged. Rounding and bevels stay inside each part's bounding box. `tools/test_part_envelopes.py` re-measures the new renders and must still match the committed table.
- **Guide illustrations:** re-rendered.
  - **Job list:** the render job list (77 images: the 73 deck illustrations and the four README and deck renders in `docs/img`) goes into the repo as `pdf/deck_renders.txt`, one `params|view|output|openscad args` line per image.
  - **Runner:** a small stdlib runner, `pdf/render_deck.py`, renders them through `cad/box.sh png`. Then the guide PDF is rebuilt with `overflow: none`.

## 7. Testing

1. CAD asserts first (§5), then the geometry.
2. Box renders of every part of the bench window and the changed parts of the others, with `check_stl` all ok.
3. Section views by eye:
   - each profile's rounded outline over the old one;
   - one joint seam, showing the V bevel;
   - one corner block;
   - the cam handle.
4. The bed-fit envelope test against the new renders.
5. Python and web suites unchanged and passing. Reference BOMs rebuilt, with only the filament lines changed.

## 8. Out of scope

- Rounding the window's outer frame and sash corners in the window plane.
- Fillets on concave corners.
- Changing any functional geometry, print orientation or part split.
- The sill nose, weep caps, setting blocks and acrylic spacers.

## 9. Risks

- **Joint mismatch:** a part whose outline isn't derived from the profile could leave a visible step at a joint. The 0.1 mm outline-match rule (§3.2) and the joint section view check this.
- **Thin lips near corners:** cuts that end close to a rounded corner (for example, a magnet channel ending 3 mm from the corner) are handled by the exception table, which is checked by assert.
- **Cord-groove lip:** at the joint face, the lip outside the foam-cord groove is 0.7 mm instead of 1.5 mm, over the bevel's 0.8 mm depth. The lip is backed by the full section below it, and the sealant fills the V. If it chips on the test coupon, the bevel drops to 0.6 mm (one `dims.json` value).
- **First-layer bevel:** the bottom end of a standing segment is bevelled on the bed. A 0.8 mm bevel is smaller than most elephant's-foot, so it should print cleanly and hide that foot.

## 10. Amendments (2026-10-11, from implementation planning and execution)

Each was checked in a scratch build or in the implementation's reviews: CAD tests, box renders of all four windows, section and close-up views, STL slices, the bed-fit envelope test and the BOM diff.

1. **Sharp corners.** The corner check found these and nothing else. Each one keeps its sharp edge:
   - **Fin tips beside the outer seal kerf.** Rounding them would leave a 0.5 mm lip at the kerf mouth. That's the upper jamb and head (`sash_rebate`), the transom, and both sides of the upper mullion.
   - **Room-face corners next to a magnet channel.** The channel ends 0–3 mm from them: the `sash_rebate` inner stop, the transom body, and both sides of the upper mullion.

   The transom cross-node (TX) keeps the same room-face corner sharp. The check samples each 2 mm arc and measures its distance to every cut, chambers included. The sill's sloped corners are handled as a polygon.
2. **Beads.** Only the room-side edge facing the glass is rounded. The edge against the frame stays sharp, because the bead's key tongue starts within 1 mm of it. Beads get no joint bevel: their segments butt without sealant.
3. **Hinge leaves.**
   - **HG:** the plate rounds only its free corners, and within the plate's thickness the wall's plate-side corners stay square, so plate and wall meet without a notch. Its 3 mm wall is rounded 1 mm (`WALL_R`), because 2 mm would delete it.
   - **HS:** within the plate's thickness, the plate and wall are rounded as one footprint, so there is no cusp where they overlap. Above the plate, the 5 mm wall takes the full 2 mm.
4. **Cam handle.**
   - **Top edge:** the softening is a 1.5 mm quarter-round (`TOP_R`) on the lever, knob and hub tops, built in 0.25 mm steps.
   - **Plan rounding:** in plan, the lever's corners sit inside the hub and knob, so `HANDLE_R` changes almost nothing that shows.
5. **Bed-fit envelopes.** Three entries change, and the table is re-measured:
   - **S and SW:** 58 → 57.70 mm. The sill's acute outside corner is rounded.
   - **CMH:** 86.151 → 86.122 mm, from the rounded knob.
6. **Keyway lip at joint faces.** In the last 0.6 mm of each segment end, the bevel also trims the 0.8 mm bead-keyway lip. Bead retention comes from the length of the keyway, so this is harmless. At transom joints, the bevel also thins the 2 mm wall between the sharp room-face corner and the magnet channel: it is 0.4 mm in the first 0.2 mm layer and back to 2 mm at 0.8 mm deep. The same trim removes the 0.8 mm lip of the sill's nose keys at the ends of S, SW and SN. The sash's glazing kerf has only a 1.5 mm floor, so at sash joint faces the bevel steps over that kerf's mouth (`bevel_fill()`) instead of cutting through its floor.
7. **Guide images.** The deck job list was recovered from the original renders. Re-rendering three images with it from the unchanged repo gave byte-identical PNGs.
8. **Arc resolution.** Every rounding uses 32 segments per circle (`$fn = 32`, 8 per quarter turn), so each 2 mm arc is within 0.01 mm of a true circle, and outlines that meet at a joint are built from the same arcs.
9. **Node outlines.** A node keeps a corner sharp unless a neighbouring profile rounds it (`node_sharp()`), so SN, HN and TX match the segments either side exactly. The jamb node (JN) meets two profiles whose corners differ: on its shoe face, the lower jamb runs flat past the outside corner and the upper jamb past the room corner. JN rounds both, so at each of those corners it sits up to 0.8 mm inside one segment, a small reveal along its seam with the transom shoe. It is never proud. Its cord grooves are pulled in at those corners, so the lip outside them stays 1.5 mm (0.7 mm at the face). The node bevels follow the keyway, nose-key and magnet-channel mouths, just as the segments' do.
10. **T-junctions.** Where a shoe meets the end of a segment at right angles, the shoe's rounded edges run across the segment's end face: the transom shoes over the jamb stops, and the mullion shoes beside the sill, transom and head segments. The end face shows a small notch under each round. Only one faces up on the weather side, where a transom shoe's outside bottom edge sits on the end of the lower jamb. The install guide fills it with the seam sealant and tools it flush.
