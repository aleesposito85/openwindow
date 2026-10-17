# Build guide (bench assembly)

Everything is assembled flat on a bench, then carried to the opening as separate units:
- the frame,
- the transom,
- the sash,
- the screen,
- the mullions (bays only),

plus the loose glass (or acrylic sandwich units). Part IDs are engraved on a hidden face of each part. Left and right in part names (CSL/CSR, TSL/TSR) are as seen from outside.

**Windows with bays.** A params file with `max_pane` or `bays` can split the window into bays (the `pane_fit` line of `generate.py` says how many). Each bay then has its own sash and screen. The sill, head and transom are built as one run per bay, with a node between runs: SN in the sill, HN in the head and TX in the transom. The mullions are dry-fitted in section 7 and fitted at install step 6. Steps marked **Bays:** apply only then, and `bom/<name>.md` lists the mullion centre lines under "Bays".

All quantities and lengths for your window are in `bom/<name>.md` (BOM, tube cut list, glass) and `bom/<name>-parts.csv`. Run `python3 bom/build_bom.py <name>` first. Don't work from `cad/generated/*.csv`: `cad/box.sh test` and `png` regenerate those for the bench window.

## Joint rules (frame, transom and sash)

- **Temperature and gap.** Assemble at about 20 °C (15–25 °C). Every segment joint gets a 1 mm gap: the generator makes each segment shorter by one gap per joint, so the member keeps its length and the tube cuts are unchanged. A 240 mm segment grows about 1 mm between 20 °C and 70 °C, and the gap is where that growth goes. Hold each gap with two 1 mm shims (strips of 1 mm plastic sheet, or feeler-gauge leaves), slipped in from the outside and inside faces. Pull them out once that part's tube screw is in. Screen joints close tight, with no shims.
- **Cord.** Each joint gets one ring of 4 mm closed-cell foam cord, pressed into the groove of one of the two faces only. The mating face's groove takes the other half. Both grooves are 1.5 mm deep, so the joint is 4 mm high at the 1 mm gap. The 4 mm cord, squeezed across the 3 mm-wide groove, still fills both grooves, and it compresses further as the joint closes in the heat.
- **Sealant.** Use the movement-rated MS polymer from the BOM (±50 %), because each gap cycles between about 0 and 1.3 mm. Butter it onto the face before closing each joint, keeping it off the cord:
  - over the whole band outside the cord ring (the 1.5 mm margin all round the outline), continuous with the end faces of the stops, fins and inner stop. At a 1 mm gap this band would otherwise be an open slot. Along the opening-side edge it runs from the outside face to the inside face, past both glazing gaskets and both sash seals.
  - around the tube pocket;
  - on transom faces, across the 2.7 mm web between the bead keyway and the tube (the cord ring stops either side of it).

  Work joint by joint, before the sealant skins (about 10 minutes for most MS polymers; check the cartridge):
  1. Butter the face, close the joint onto its shims, clamp it, and drive that part's tube screw.
  2. Pull the shims, and fill and tool the voids they leave. Tool the sealant flush with the 0.8 mm bevel along the joint's edges, so each joint shows as a neat V line.
  3. Clear any squeeze-out from the seal and glazing kerfs, the magnet channel and the bead keyways.
- **Tube screws.** Drive one through the inside-face countersink of every segment, corner leg, node and shoe.
  - Aluminium tubes: 8g × 30 stainless countersunk self-tappers, with a 3.2 mm pilot drilled through the printed hole into the tube.
  - Steel transom tube: 8g × 25 tek (self-drilling) screws in 410 stainless. Or drill a 3.5–3.8 mm pilot through the 1.6 mm steel wall and use a stainless self-tapper.
  - V-slot cores (`"core": "vslot"`): M5 countersunk screws into slide-in T-nuts, with no pilots. The transom pair takes 8g × 20 self-tappers instead. See section 8.

  Stop when the head is flush, so the screw doesn't strip the plastic.

## 1. Prepare
1. Cut the tubes to the cut list with a hacksaw or drop saw, never longer than the list. With V-slot cores, cut to the V-slot cut plan in `bom/<name>.md` instead (section 8). Each length leaves 1.5 mm clear at every corner socket floor for print shrinkage. Dry-fit each member on its tube with the shims in, and trim the tube if any joint will not close onto its shims. Deburr and wipe with isopropyl.
2. Press M4 heat-set inserts (230 °C iron, flush) into every boss:
   - all H segments (2 each), including the ones that won't carry a hinge, so the hinges can be moved later. If your params file has `"screen": false`, the H segments have no bosses and get no inserts;
   - TE (cam bases);
   - SBE (keepers): both boss pairs, 4 inserts each. The keeper uses the outer pair, the one nearer the sash corner. The pairs sit either side of the segment middle, so that the keeper lands right over its cam pivot.
   - the CMB pivot boss;
   - TC.

## 2. Acrylic sandwich (only if `glazing = acrylic`)
Make one unit per pane: AF* bars for the fixed pane, AS* for the sash, and four AC corners each.
1. Assemble the spacer frame, fill its channels with silica gel, and bond both sheets to it with butyl glazing tape. Use the thickness the glass list names (4 mm unless `acrylic_t` is set).
2. Peel the film off the inner faces only.

The sash unit is glazed in section 5. The fixed unit goes in at install step 9.

## 3. Frame
1. **Sill.**
   1. Fit corner CSL on the left end of the sill tube, with the tube end 1.5 mm off the socket floor, and drive its sill-leg tube screw.
   2. Thread on the sill segments: an SW (weep) segment first, then the S segments, then the other SW. Fit CSR on the right end.
      - **Bays:** thread one such run per bay, with an SN node between runs. Its dovetail slot faces up into the opening and opens on the room side.
   3. Close the joints one by one from CSL (joint rules above), driving each segment's screw as you go. CSR's screw goes in last.
      - **Bays:** before you drive an SN's tube screw (inside face, centre of the node), set the shims so its centre is on its mullion centre line within 0.5 mm.
2. **Jambs.**
   1. On each jamb tube, thread the JL segments, one JN node, then the JU segments. With V-slot cores each jamb is two tubes: the JL segments and the JN go on the lower piece, the JU segments on the upper piece (section 8.3).
   2. Push the tube into its sill corner's socket, with the tube end 1.5 mm off the socket floor.
   3. Drive the sill corner's jamb-leg tube screw (CSL on the left, CSR on the right). Then close the joints from the bottom up, driving every JL and JU tube screw and the JN node's tube screw (inside face, centre of the node).
3. **Head.**
   1. Assemble CH, the H segments and CH on the head tube in the same way.
      - **Bays:** one run of H segments per bay, with an HN node between runs, its slot facing down into the opening. Centre each HN on its mullion centre line, like the SN below it.
   2. Butter the jamb-leg faces of both CH corners and drop the head onto the jamb tubes, closing the top jamb joints onto their shims.
   3. Check the diagonals are equal within 2 mm, then drive the CH jamb-leg screws.
4. Pull out any shims that are still in, and fill and tool their voids.

## 4. Transom
The transom is only dry-fitted here. Its length has to match the node spacing of the installed frame, so it is sealed and screwed at install step 6.
1. **Cam bases.** Screw a cam base (CMB) to the inserts of every TE segment (two per bay), with two M4 × 10 countersunk screws each.
2. **Handles.** Fit each handle (CMH) over its pivot boss with an M4 × 8 pan screw and a 20 mm penny washer. The washer sits on the boss and holds the handle on.
3. **Dry-fit.**
   1. Thread the T and TE segments onto the steel tube, with a TE segment at each end.
      - **Bays:** one run per bay, each with a TE at both ends, and a TX cross-node between runs with its two slots facing up and down. Set the shims so that each TX centre sits on its mullion centre line.
   2. Fit shoe TSL on the left end and TSR on the right end (as seen from outside). Each shoe takes a cord ring only in its joint with the TE segment. The groove across the shoe's outer end face is for the seam with the node, filled at install step 6.
   3. Check every joint closes onto its shims. Leave the joints unsealed and unscrewed.

## 5. Sash
Make one sash per bay. They are all the same.

1. **Assemble.** Fit SH (top), SB + SBE (bottom, with SBE at the ends) and SV (sides) on their 20 × 20 tubes with four CS corners. Use the joint rules and 8g × 30 tube screws.
2. **Glaze.**
   1. Fit the outer wedge gasket into the sash stop kerf all round.
   2. Place four GF blocks: two on the bottom rail at the quarter points of the glass width (setting blocks), and one at mid-height on each side (locators).
   3. Fit the glass or the acrylic unit.
   4. Snap in the BSH and BSV beads with the inner wedge gasket.
3. **Keepers.** Screw each keeper (KP) to the outer boss pair of its SBE (the pair nearer the sash corner), with two M4 × 10 countersunk screws.
4. **Friction stays (sash side only).** Screw each stay's sash arm to a sash side. The tracks go on the jambs (and the mullions, with bays) at install step 8.
   - **Stay size:** stack height no more than 13 mm (the sash gap), and track and arm no more than 14 mm wide (BOM line). If no stay rated for your sash is that narrow, the CAD has to change first (spec §11).
   - **Position along the sash:** follow the stay's datasheet.
   - **Position across the sash side:** centre each arm 33–33.5 mm in from the sash's outside face, which is 35–35.5 mm from the frame's outside face once hung. A 14 mm stay then sits between the jamb fin top (28 mm) and the sash lip (46 mm), and its screw centres stay at least 1.5 mm inside the sash tube's edge (the tube is 17–37 mm in).
   - **Screws:** 8g × 16 stainless countersunk, in 3.2 mm pilots (3.5 mm with V-slot cores, section 8.7) drilled through the shell into the tube, using the stay as the template.

## 6. Screen

Skip this section if your params file has `"screen": false`: the part list, cut list and BOM then carry no screen parts, tubes or hardware.

Make one screen per bay.

1. **Rails.** Thread the NH and NV segments onto their 10 × 10 tubes. The cut list gives a tube for every rail of two or more segments. A single-segment rail has none.
   - Close the joints tight: no shims and no cord, because the screen is inside and carries no weather seal.
   - Drive an 8g × 12 tube screw (3.2 mm pilot) into each segment that has a tube.
2. **Corners.**
   1. Glue each rail end into its CN corner with 5-minute epoxy on both butt faces.
   2. Drive the CN tube screw in every leg that takes a tube.
   3. Check the diagonals before the epoxy sets.
3. **Mesh and strip.** Roll in the mesh with spline. Stick magnetic strip A into the screen's back channel all round.
4. Leave the hinge leaves off. HG and HS are fitted and aligned in place (install guide, step 12).

## 7. Mullions (bays only)

Skip this section for a window with one bay. Each bay boundary has a lower mullion (sill to transom) and an upper mullion (transom to head), each on its own 40 × 20 steel tube from the cut list. Like the transom, they are only dry-fitted here. Their lengths have to match the node spacing in the fitted frame, so they are sealed and screwed at install step 6.

1. **Lower mullion.** Thread an MSL shoe, the ML segments and a second MSL shoe onto a `mullion_lower` tube. Both shoes are the same part, with the top one turned end for end, so both tongues point outwards. Each shoe takes a cord ring only in its joint with the ML segment.
2. **Upper mullion.** Thread MST, the MU segments and MSH onto a `mullion_upper` tube. MST goes at the bottom, where it meets the transom. MSH goes at the top: its magnet channel turns along the head.
3. Check every joint closes onto its shims. Leave the joints unsealed and unscrewed. With V-slot mullion pairs, hang a T-nut on each screw with the carrier (section 8.4) as you thread the parts, but leave the screws loose.

## 8. V-slot cores (only if `"core": "vslot"`)

The frame and sash cores are V-slot 2020 (4-slot). The transom and any mullions are two 2020s side by side. The `core` check line, and "Standard tubes in this V-slot window" in `bom/<name>.md`, list any member that kept a standard tube and why. Everything above still applies; this section only changes the tubes and their screws.

1. **Check the extrusion first** (test log row 10). The groove mouth should be about 9.2 mm wide at the surface, and the slot about 6 mm deep. The screw positions assume the OpenBuilds V-slot profile.
2. **Cut** each piece to the V-slot cut plan in `bom/<name>.md`, which allows 2 mm per saw cut. Label each piece with its cut-list name, then square and deburr the ends. A joined member (`head 1/2`, `head 2/2`) lists its pieces in order from the left end seen from outside, or from the bottom for a jamb.
3. **Each jamb is two tubes.**
   - **Lower piece (`jamb_lower`):** runs from the sill corner socket up into the JN node, whose T-nut holds its top end.
   - **Upper piece (`jamb_upper`):** starts at the JN's top face and runs into the head corner.
   - **Why the step:** the head and the upper jambs sit 3 mm further out than the other members, so the stay screws land on solid metal beside the groove.
4. **T-nut screws.** Every tube screw into V-slot, except the transom's, is an M5 countersunk machine screw into an M5 slide-in T-nut, with the length the BOM gives. There are no pilots and no drilling.
   1. **Hang the nuts, with a carrier.** Before a tube goes in, hang a T-nut on each part's screw. The carrier is a short V-slot offcut (about 150 mm).
      1. Put the nut in the carrier's slot, long side along the slot.
      2. Slide the carrier into the part's empty pocket from the part's end, slot towards the screw, until the nut is under the screw hole.
      3. Drive the screw until it catches the nut and the nut is just snug against the carrier's lips.
      4. Back the screw off a quarter turn, then slide the carrier out along the slot.

      The nut stays on the screw at the depth the real tube needs.
   2. **Check one.** Looking into the pocket end, the nut's neck should be level with the pocket wall and its long side along the member. If a nut has turned, turn the screw a little until it lines up. If it hangs deeper than the slot (the tube end hits it), screw it in until its neck reaches the wall.
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
