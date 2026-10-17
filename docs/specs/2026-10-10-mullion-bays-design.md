# OpenWindow — mullions and bays for a maximum pane size — Design Spec

Date: 2026-10-10
Status: Implemented (plan: `docs/plans/2026-10-10-mullion-bays.md`); amended while planning (§10)

## 1. Goal

Let a window be built when the largest glazing sheet available is smaller than the window's panes. Example: 1200 × 900 mm acrylic or glass, while the 1800 × 1500 home window needs a 1698 × 878 fixed pane and a 1606 × 388 sash pane.

The window splits side by side into equal **bays**, separated by true **mullions**. Each bay has its own fixed pane, awning sash and insect screen.

## 2. Decisions

| Topic | Decision |
|---|---|
| Split method | True mullions (not coupled units, not glazing bars) |
| Bay count | Automatic: the fewest equal bays that make every pane fit; optional override upward |
| Awnings | Every bay has an awning sash |
| Transom | Stays one continuous member across the full width (steel 40×20, existing shoes and jamb nodes) |
| Mullions | Two per bay boundary: lower (sill → transom) and upper (transom → head), each with its own 40×20 steel tube |
| Joints | Dovetail tees, following the jamb node / transom shoe pattern |
| Default behaviour | No limit → 1 bay → byte-identical outputs and unchanged tests |

## 3. Inputs (params keys, all optional)

| Key | Type | Default | Meaning |
|---|---|---|---|
| `max_pane` | `[a, b]` mm, each 200–3000 | none (no limit) | largest glazing sheet. A pane fits if `sorted(pane) <= sorted(max_pane)` element-wise, so rotation is allowed |
| `bays` | int ≥ 1 | automatic | override. It must be at least the automatic count, otherwise a validation error is raised |

**Web configurator.**
- A "Max pane size" field pair, defaulting to 1200 × 900 on the page, with a "No limit" checkbox.
- A "Bays" field showing the automatic value, editable upward.

## 4. Geometry

### 4.1 Layout
Only the frame and transom are unchanged: same depth, frame profiles, transom height and awning height.

Bays and mullions:
- `bays = n`, with equal bay widths. Mullion centrelines sit at `FRAME_W + i · pitch` (i = 1…n−1), where `pitch = (w − 2·FRAME_W + MULLION_W) / n` (superseded: see §10 item 1). The same formula is used throughout, so the end bays and the inner bays have identical daylight widths.
- `MULLION_W = TRANSOM_W` (70) and `MULLION_HALF_BODY = TRANSOM_HALF_BODY` (17), held as new `dims.json` keys so they can diverge later.
- The glazing rebate and pane bite on each mullion side are the same as on the transom's glazing side (`TRANSOM_GLASS`).

Per bay:
- **Fixed pane:** width = bay daylight + 2 × bite. The height is as today.
- **Sash:** width = bay daylight between the mullion bodies (or the frame body at the end bays) − 2 × `SASH_GAP`. The height is as today.
- **Screen:** one per bay, overlapping the frame and mullion faces by `SCREEN_OVERLAP`.

Too tall for any sheet orientation:
- If a pane's height alone exceeds `max(max_pane)`, or its height exceeds `min(max_pane)` while its width also exceeds `min(max_pane)` at every bay count, the generator raises a validation error.
- The message says that a second horizontal transom would be needed, which is out of scope, and suggests a taller awning or a shorter opening.

### 4.2 New profiles (`cad/profile.scad`)
- **`mullion_glazing`:** the transom body (steel 40×20 pocket), with a glazing rebate, stop leg and bead keyway on *both* sides, plus outer/inner glazing kerfs on both sides.
- **`mullion_sash`:** the transom body, with the sash-side features on *both* sides: fin + kerf, inner stop + kerf, and screen magnet channel. These are mirrored about the centreline.
- Both get chambers only where the transom rules allow; the transom currently has none. Both get the end-cap and cord-ring treatment.

### 4.3 New joint parts (`cad/parts/`)
| ID | Part | Notes |
|---|---|---|
| `SN` | sill node | a sill-profile segment of length `MULLION_W`, with a dovetail slot in the rebate face. The sill tube passes through it |
| `HN` | head node | a head-profile (`sash_rebate`) segment, with a dovetail slot. The head tube passes through it |
| `TX` | transom cross-node | a transom-profile segment with dovetail slots on both faces (down to the lower mullion, up to the upper mullion). The transom tube passes through it. It carries cam-boss positions only if a sash end requires them (see §4.4) |
| `MSL` / `MSU` | mullion shoes (lower / upper) | each mullion end has a dovetail tongue into its node, a 3 mm end wall and the steel socket. There are separate IDs where the two ends differ (sill vs transom, transom vs head) (superseded: the part IDs are `MSL`, `MST` and `MSH`; see §10 item 5) |
| `ML`, `MU` | lower / upper mullion segments | split to fit the bed like every member; min 1 |

**Seal and channel continuity at every tee:**
- outer fin + kerf;
- inner stop + kerf;
- glazing kerfs;
- frame magnet channel (screen);
- bead keyways.

Each must turn the corner the way the transom shoe already does. The shoe end faces get the cord groove + sealant treatment from the transom seam.

**Assembly:** mullions slide in from the room side into the node slots after the transom is fitted, then are locked with screws along the seam, using the same lock-hole rules (countersunk, below the magnet channel floor, clear of keyways).

### 4.4 Hardware per bay
- **Friction stays:** a stay pair per sash, sized by the existing stay rule for that sash.
- **Cam locks:** two per sash, one near each sash end.
  - The transom gets cam-boss segments (TE-type) at each bay's ends, not only at the window ends.
  - The segment split of the transom is per bay run (between nodes), so each run's end segments carry the bosses.
  - The keeper offset check (`cam_keeper`) is evaluated per sash.
- **Weeps:** sill weep segments at the ends of each bay run, and SBE per sash as today.
- **Setting blocks:** per pane (`GW`, `GF` counts × bays).

### 4.5 Member runs and tubes
- The sill, head and transom are split into runs between nodes (jamb node or corner → node → … → node → jamb node or corner), and each run is split to fit the bed.
- Their tubes stay single pieces running through the node segments. Tube lengths are unchanged.
- Mullion tubes: one steel 40×20 per mullion stub, length = stub span between node faces + sockets − end clearance.

## 5. Checks

- **New `pane_fit`:** every pane against `max_pane`, in any rotation. Reports ok with "no limit" when `max_pane` is absent.
- **New `mullion_deflection`:**
  - simply supported over the stub span;
  - tributary width = one bay (half a bay each side);
  - 0.7 kPa;
  - limit span/175;
  - steel 40×20.
- **`transom_deflection`:** span = the largest bay daylight width, since the transom is propped at each mullion (superseded: see §10 item 3). Unchanged for 1 bay.
- **`sash_weight` / stay** and **`cam_keeper`:** evaluated per sash. All sashes are identical, so these are reported once, with a "× n" note.
- **`bed_fit`** covers the new parts (envelopes added to `tools/part_envelopes.json` from reference renders).

## 6. BOM and documents

**BOM:**
- new parts;
- the steel tube for the mullions;
- everything that scales per bay:
  - friction-stay pairs and their screws;
  - cam hardware;
  - screens, mesh, spline and magnet strips;
  - glazing gaskets;
  - EPDM loops (one loop per sash opening);
  - setting blocks and weep caps;
  - inserts and lock screws for the mullion seams.
- `printing.md` gets the orientation of the new parts (nodes and shoes print on their outside face, like JN/TS).

**Documents:**
- **Build guide:** thread the SN/HN nodes onto the sill and head, and TX onto the transom, at the marked positions.
- **Install guide:** slide the lower mullions in after the transom, then the upper mullions; seam sealing; per-bay glazing, seals, stays, magnet strips and screens.
- **User manual and spec:** updated. The guide PDF is regenerated (`pdf/build_deck.py`).
- **Configurator:** the drawing shows the mullions and each pane's size, there is a `pane_fit` badge, and the assembled viewer includes the mullions.

## 7. Compatibility

With neither `max_pane` nor `bays` in the params:
- `n = 1`;
- generator, BOM and CSV outputs are byte-identical for both reference windows;
- all existing Python, web and OpenSCAD tests pass unchanged.

## 8. Testing

1. **Generator unit tests:**
   - bay count: home with 1200 × 900 gives 2 (fixed panes ≈ 829 × 878); with 900 × 600 it gives 3 (fixed panes ≈ 539 × 878, because the 878 mm height only fits along the 900 side); one rotated-fit case; one too-tall-for-any-sheet error; the override (valid, and below automatic gives an error);
   - bay widths and mullion positions;
   - run splitting around nodes, with the P1S and 180 mm beds;
   - per-bay part counts;
   - `pane_fit`, `mullion_deflection`, and the transom bay span;
   - BOM line quantities.
2. **CAD asserts first** (`cad/tests/`):
   - walls ≥ `MIN_SKIN` around every new pocket, keyway, kerf, lock hole, fixing and socket;
   - uniform dovetail clearance;
   - fin, kerfs, glazing kerf and magnet channel continuous through every tee;
   - tube screws hitting their tubes with the tube at either socket end;
   - lock heads below the channel floor.
3. **Renders:** every new part renders, and passes the closed single-body mesh check.
4. **Section views reviewed by eye:** lower mullion, upper mullion, TX cross-node, SN and HN tees.
5. **New reference window** `params/home-1800x1500-2bay.json` (the home opening + `max_pane: [1200, 900]`):
   - full render on the Windows box;
   - `check_stl` all ok;
   - BOM built;
   - assembly preview and a mullion section checked by eye.
6. **Configurator:** web tests updated for bays/max_pane; screenshots of the 2-bay preview and the assembled viewer reviewed.
7. **Reviews:** generator changes; CAD geometry (the tees); final docs/BOM/code consistency.

## 9. Out of scope

- A second horizontal transom (panes too tall for the sheet)
- Unequal bays, or bays without an awning
- Separate pane limits per glazing type
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
10. **Mullion lock holes** sit at `LOCK_U` (3 mm into the node), like the jamb node's, not at half the 4 mm dovetail depth: at 2 mm they left 0.35 mm to the node's mating face. They grip about half as much tongue as the jamb's, so the test log gets a mullion shoe pull-out row (200 N).
11. **Assembly order.** The `SN` and `HN` fixings go in first, because the `HN` counterbore sits about 1 mm from the mullion's inner stop and the `SN` counterbores end up under the pane edge. Then the mullions slide in along y from the room side, then the panes go in. An `SN` top is flat, with no outward fall over its fixing counterbores, so its fixings are bedded in MS polymer.
