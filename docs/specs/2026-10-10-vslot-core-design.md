# OpenWindow: V-slot 2020 tube cores (Design Spec)

Date: 2026-10-10
Status: Implemented (plan: `docs/plans/2026-10-11-vslot-core.md`); amended while planning (§13)

## 1. Goal

Build the window's metal cores from V-slot 2020 extrusion the owner already has. The stock is mostly 2020 in 1 m pieces.

- **Where V-slot is used:** every member that can take it: frame, sash, transom and mullions.
- **Longer members:** pieces are joined where the frame is screwed to the brick.
- **Fallback:** a member gets the standard tube only when V-slot can't work, because it is too long for the stock with no join allowed, or it fails its bending check.

## 2. Decisions

| Topic | Decision |
|---|---|
| Profile | V-slot 2020, 4 slots (OpenBuilds-style). Drawing: OpenBuilds "V-Slot 20X20 Linear Rail" |
| Scope | Every member except the screen (its 10 mm tubes are unchanged) |
| Transom and mullions | Two 2020s side by side in the existing 20 × 40 pocket |
| Tube-lock screws | M5 countersunk into slide-in T-nuts on the slot centreline, hung on the screw before the tube goes in. The transom is the exception (§5.2) |
| Friction stays | V-slot too. Stay screws are 8g self-tappers into the solid shoulder beside a slot. The upper-jamb tube moves 2.5 mm (§5.3) |
| Joins | Only in head, sill and lower jambs. They are fixed to the brick every segment |
| No joins | Transom, mullions, sash members and upper jambs. They span the opening or carry the stays |
| Fallback | Per member, standard core (`alu20` / `steel40x20`). The summary and BOM say why |
| Default behaviour | No `core` key gives byte-identical outputs and unchanged tests |

## 3. Inputs (params keys, both optional)

| Key | Type | Default | Meaning |
|---|---|---|---|
| `core` | `"vslot"` | absent (standard tubes) | build the cores from V-slot 2020 |
| `vslot_stock` | number, 300–6000 mm | 1000 | length of the owner's V-slot pieces. Only allowed with `core` |

**Web configurator:**
- A "Tube core" select: "Standard tubes" or "V-slot 2020 (T-nuts)".
- A "V-slot piece length" field, shown only for V-slot.

## 4. Profile data

From the OpenBuilds drawing:
- Groove mouth 9.16 mm at the surface, with a 90° V narrowing to 6.25 mm at 1.80 mm deep (the lip).
- Cavity under the lip 11 mm wide.
- Slot floor 6.1 mm below the face (1.80 + 4.30).
- Webs 1.50 mm, centre bore 4.20 mm.

Derived:
- **Solid shoulder:** the metal is solid about 4.5 mm deep from 5.5 to 8.2 mm off a face centre.
- **Stay screw window:** an 8g screw (4.2 mm) whose centre is **5.6–7.4 mm** off a face centre bites solid metal on its whole circumference. Only a sliver of the V lies under its inner edge.

From the supplier datasheet (Systéal 4-slot V-slot 20x20):
- I = 6890 mm⁴ on both axes.
- 0.456 kg/m.

Section values per core:

| Core | I (mm⁴) | E (MPa) | kg/m | Model |
|---|---|---|---|---|
| `vslot2020` | 6890 | 69000 | 0.456 | datasheet |
| `vslot2020x2` | 13780 | 69000 | 0.912 | two separate bars, no composite action (conservative) |

## 5. Geometry

### 5.1 T-nut tube screws

**Where they are used:** every tube screw that lands on a V-slot face centre:
- segments;
- corner blocks;
- frame nodes (SN/HN), jamb nodes (JN);
- mullion shoes (MSL/MST/MSH).

**What changes:**
- Through-hole 5.5 mm, M5 countersink (head Ø10).
- The head seat is sunk below the face by the amount that puts the screw tip **5.6–5.9 mm into the slot** for the chosen standard length. That is past the lip and inside the nut body, short of the 6.1 mm floor.
  - The generator picks the longest standard M5 length (10, 12, 16, 20, 25, 30, 35, 40) that needs a seat depth of 0 or more.
  - The CAD sinks the seat with the existing `top` argument of `tube_screw`.
- The screw position is unchanged: the face centre is the slot centreline.

**Assembly:**
- Thread a slide-in T-nut one or two turns onto each screw so it hangs inside the empty pocket.
- Push the tube in. The slot catches each nut and the lip passes beside the nut's neck.
- Tighten.

### 5.2 Transom screws

The transom's magnet channel (x 20–33) sits over the slot centre (x 35). That is why its screws already sit at `TRANSOM_SCREW_X` = 39.

- **V-slot mode:** these screws become 8g self-tappers into the room-side 2020's shoulder at **x = 41.25** (6.25 mm off its centre), clear of the channel.
  - This applies to transom segments, transom shoes (TS) and cross nodes (TX).
- **The outer 2020 of the pair:** no screws. The end walls of the TS shoes trap it along its length, and the pocket traps it across. The outer 2020s of the mullion pairs are trapped the same way, by the end walls of their shoes (MSL/MST/MSH).

### 5.3 Stays and the upper-jamb tube

Stay lines today, measured from the frame's outside face:
- jamb tracks at 35–35.5 mm;
- sash arms at 33–33.5 mm in the sash's own coordinates, which is 35–35.5 mm once hung.

Positions against the tubes:

| Tube | Centre (frame coords) | Stay offset now | V-slot mode |
|---|---|---|---|
| Sash (sides) | 29 | 6–6.5 | unchanged, in window |
| Upper jamb | 31.5 | 3.5–4 (in the groove) | **centre moves to 29**: offset 6–6.5, in window |
| Upper mullion, room-side 2020 of the pair | 41.5 | 6–6.5 | in window |

**What moves:** in V-slot mode the `sash_rebate` pocket moves 2.5 mm towards the outside, from y 21.2–41.8 to 18.7–39.3. That profile is used by the upper jambs and the head.

**Clearances:**
- The fixing hole at y 48 gains clearance (6.2 mm, was 3.7).
- The shell below the pocket stays 18.7 mm.

**What doesn't change:**
- Stay positions, stack limits and width limits are the same.
- The stays need no change in the docs except the screw note.

**Stay screws:** 8g self-tappers, as now, in 3.5 mm pilots drilled through the shell into the V-slot shoulder.

### 5.4 Jambs in two pieces

In V-slot mode the jamb is two tubes:
- **Lower piece:** in the `glazing` pocket, from the sill corner socket into the jamb node (JN). The JN's T-nut holds its end.
- **Upper piece:** in the shifted `sash_rebate` pocket, from the JN's top face to the head corner socket. Its first JU segment and the head corner hold it.

The JN keeps its `glazing` pocket. Each piece is still subject to the stock length (§6).

### 5.5 Joins (head, sill, lower jambs)

A join is a butt joint inside a plain printed segment. It sits between the segment's tube screw (its middle) and one of its ends, at the quarter point.

**Constraints:**
- At least 15 mm from the segment end, so the print bridges it.
- At least 15 mm from the T-nut, so a nut never straddles a joint.
- Never inside a node or corner.

**Each piece:**
- holds at least one T-nut;
- is at most `vslot_stock` long.

The segment either side is fixed to the brick, so the joint needs no bending strength.

**Placement:** greedy from the member's start. Each piece ends at the farthest allowed joint that keeps it within stock.

If a member can't be split this way, it falls back to the standard core with a summary note. That should only happen with stock shorter than about two segments.

### 5.6 Part calls

V-slot geometry reaches the CAD through an optional `core` argument on the part calls. This follows the `pane_t` pattern. Without it, the calls and the geometry are exactly today's.

## 6. Core per member

| Member | V-slot when | Otherwise |
|---|---|---|
| Head, sill, lower jamb | always, joined as needed (§5.5) | `alu20` if no valid split |
| Upper jamb | one piece ≤ stock | `alu20` in the shifted pocket (stays still land on its wall) |
| Sash horizontal, sash vertical | one piece ≤ stock | `alu20` |
| Transom | both 2020s ≤ stock **and** `transom_deflection` passes with `vslot2020x2` | `steel40x20` |
| Mullion lower / upper (each stub) | both 2020s ≤ stock **and** `mullion_deflection` passes for that stub | `steel40x20` |
| Screen | never | `alu10` (unchanged) |

**Deflection checks:** the transom and mullion checks report the core actually chosen. A fallback is noted in the summary, e.g.:
- "steel transom: V-slot pair deflects 48.2 mm, limit 9.5 mm";
- "alu20 sash horizontal: 1615 mm is longer than the 1000 mm V-slot pieces".

**Sash weight:** each sash member's metal mass is its own core's kg/m. The stay check uses the result.

Expected outcomes with 1 m stock:

| Window | V-slot | Standard |
|---|---|---|
| bench-600 | everything | — |
| home 1.8 × 1.5 | head, sill (1 join each), jambs (lower ≈ 0.9 m, upper ≈ 0.5 m, no joins), sash sides | sash top/bottom `alu20`, transom `steel40x20` |
| home 2-bay | as home, plus sash top/bottom (746 mm), lower and upper mullions (lower passes: 4.3 mm against a 4.8 mm limit) | transom `steel40x20` |

## 7. Checks

A new `core` check appears only with `core` set. It is informational, so always ok, and reports:
- the stock pieces needed;
- the joins per member;
- every fallback and its reason.

**`bed_fit` and envelopes:**
- Unchanged. Only holes and the pocket position change, inside the same outline.
- The `sash_rebate` pocket shift is inside the profile.

## 8. BOM and documents

**BOM:**
- **Tube lines:**
  - "V-slot 2020 (4-slot), N pieces of `vslot_stock` mm".
  - A **cut plan** in BOM.md and the cut-list CSV, listing each stock piece and the cuts it gives. It is packed first-fit decreasing, with a 2 mm saw allowance per cut.
  - Fallback tubes as today, per core.
- **Fixings:**
  - "M5 × L countersunk + M5 slide-in T-nut (20-series, 6 mm slot)", per length.
  - The 8g × 30 self-tapper count drops by the T-nut count.
  - 8g self-tappers for the transom shoulder screws.
  - Tek screws only where steel remains.
  - With V-slot upper mullions, the stay screws on mullions become 8g × 16 self-tappers in 3.5 mm pilots.
- **Mass:** core masses per member.

**Documents:**
- **Build guide:**
  - "V-slot cores": the hanging-nut method, which nut type, checking one nut first;
  - joins and the cut plan;
  - pilots for stay screws into the shoulder.
- **Install guide:** stay tracks into V-slot (3.5 mm pilot), and the mullion case.
- **Test log:**
  - **Profile check:** measure the extrusion: mouth ≈ 9.2 mm, slot depth ≈ 6 mm.
  - **Stay screw pull-out** from the V-slot shoulder.
  - **T-nut joint slip** under a hand load.
- **Other docs:** README params, web README, a §12 item in the main spec, and the user manual (replacement tubes). Regenerate the guide PDF.

## 9. Compatibility

With no `core` key:
- generator, BOM and CSV outputs are byte-identical for every reference window;
- part calls are unchanged;
- all existing Python, web and OpenSCAD tests pass unchanged.

## 10. Testing

1. **Generator unit tests:**
   - core choice per member, with each fallback reason;
   - the transom and mullion checks with the pair;
   - jamb split into two tubes;
   - join placement (rules in §5.5, pieces ≤ stock, every piece holds a T-nut);
   - cut-plan packing and the stock count;
   - M5 length and seat depth per profile;
   - sash weight;
   - `core`/`vslot_stock` validation;
   - default calls unchanged.
2. **CAD asserts first** (`cad/tests/`), in V-slot mode:
   - walls ≥ `MIN_SKIN` round the shifted `sash_rebate` pocket and every M5 hole and countersink;
   - T-nut screws on the slot centreline;
   - transom shoulder screws within 5.6–7.4 mm of the room-side 2020's centre and `MIN_SKIN` clear of the magnet channel;
   - stay lines within 5.6–7.4 mm of the upper jamb, sash and room-side mullion tube centres;
   - screw tip 5.6–5.9 mm into the slot.
3. **Renders:**
   - a temporary V-slot bench window (every part) and V-slot home and 2-bay windows (changed parts), all passing `check_stl`;
   - section views of the shifted upper jamb and the transom checked by eye.
4. **BOMs:** for the V-slot bench and home windows.
5. **Configurator:** web tests for the new fields, and a screenshot of a V-slot window's summary.
6. **Reviews:** generator, CAD, and a final consistency review.

## 11. Risks

- **Brand variation:** the owner's extrusion may differ from the OpenBuilds drawing. The build guide and test log start with the measurement. The shoulder window (§4) has about 0.9 mm of margin either side.
- **Cam bosses:** the transom screw moves from x 39 to 41.25, which changes the clearance to the transom's cam-keeper bosses. CAD asserts and `cam_keeper` must confirm it. If they clash, the screw takes the mirrored shoulder (x 28.75), under the magnet channel. Its head is seated at the channel floor and covered by the strip, as the TS shoe's screw already is. That is tried before any other change.
- **Hanging nuts:** the method is fiddly over long members. The build guide gives the order, and the test log has a dry run on one segment.

## 12. Out of scope

- 2040, 4040 and other profiles; T-slot (non-V) extrusion; other slot sizes.
- Joins in the transom, mullions, sash or upper jambs.
- Composite action of the transom pair.
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
11. **Stay screw bite.** §4's "bites solid metal on its whole circumference" holds only for a screw centred 7.6 mm or more off the slot centre (the sash). Closer in, part of the screw passes over the 11 mm T-slot cavity below the lip: the jamb (6.5–7 mm off), the transom (6.25) and the upper mullion (6–6.5). Each such screw still bites the full 1.8 mm lip (more than the plain tube's 1.6 mm wall), plus the solid shoulder beyond 5.5 mm further down. Bench row 11 is the check. If it fails, `VSLOT_SHIFT` (up to 4.5 mm) and `VSLOT_TRANSOM_X` (up to about 43 mm) move the jamb and transom screws outward with only dims changes.
12. **Cut plan location.** The cut plan (which stock piece gives which cuts) is in `bom/<name>.md`. The cut-list CSV keeps its four columns and lists every V-slot piece, without the stock grouping.
13. **Hanging the nut.** §5.1's "one or two turns" hangs the nut too deep: the M5 tip ends 5.4 mm past the pocket wall, so a nut on its last turns sits below the slot floor. The nut must hang with its neck level with the pocket wall and its body just under the lip line, which is where it sits in a V-slot slot. The build guide hangs each nut with a carrier: a short V-slot offcut that holds the nut under its screw hole while the screw catches it, then slides out.
