# Install guide: brick veneer

Two people. Allow a dry day, with no rain forecast for 24 h. Quantities and lengths are in `bom/<name>.md`.

1. **Remove the old window.** Unscrew the old frame from the timber reveal, cut the sealant to the brickwork, and lift it out. Keep the existing head flashing above the lintel intact.
2. **Measure.**
   - Measure the opening width (reveal to reveal) and height (head to brick sill) at three points each, and use the smallest.
   - Check the timber reveal is at least 63 mm deep (the frame's depth), so the frame sits fully on it.
   - Put the numbers in your params file, regenerate, and rebuild the BOM (README, "Your own opening"). Only print after this measurement.
3. **Sill tray.** Lay 150 mm butyl flashing tape across the opening floor:
   - turned up 30 mm at the back (room side);
   - across the full 63 mm frame depth;
   - running out at least 50 mm over the brick sill;
   - turned up 100 mm at each end.

   With 100 mm tape, lay two runs: the outer run first, then the inner run lapped 50 mm over it, so the lap sheds water outward.
4. **Set the frame.**
   1. Stand the frame on plastic packers under the two sill corners, and under each GW quarter point. Those points are a quarter of the fixed glass width in from each glass edge: 43 mm plus a quarter of the glass width from each outer frame edge, so about 467 mm for the home window and 167 mm for the bench window. Mark them on the sill. These two packers carry the fixed pane's weight straight down into the wall (spec §2.5).
      - **Bays:** every fixed pane has its own two quarter points, a quarter of its width in from each of its edges: about 250 and 665 mm from each outer frame edge for the two-bay home window. Put a packer under each SN node too: the mullions bring the transom's share of the sash weight down there.
   2. Centre the frame, then plumb and square it (diagonals within 2 mm).
   3. Wedge it with packers between the jambs and the reveal at the two head corners.
   4. Tuck the head under the existing head flashing.
5. **Fix it.**
   - Drive a 10g × 75 screw through every fixing hole into the reveal and studs, with a packer behind each one (under it, on the sill) so the frame doesn't bow. Holes sit at each segment middle, both legs of every corner, and two in each node. That meets the spec rule of at most 400 mm apart and within 150 mm of each corner. The node fixings carry the transom, so pack them tight. Don't overtighten: the screws should hold, not crush.
   - **Bays:** drive every SN and HN fixing in this step, before any mullion goes in (step 6) and before any pane (step 9). With a mullion in place, the HN counterbore sits only about 1 mm from its inner stop, and each SN counterbore ends up under the edge of a pane.
   - **Bed the wet-side fixings.** Some fixings open into the drained glazing pocket, or outside the sash weather seal:
     - every fixing in the sill (S, SW);
     - both legs of the sill corners (CSL, CSR);
     - the lower jambs (JL);
     - both fixings in each node (JN, and SN with bays).

     Bed each of these screws in a dab of MS polymer, and fill its counterbore flush over the head (a sealing washer will not fit the 10 mm counterbore). The head, upper-jamb and CH fixings sit between the two sash seals and need no bedding.

     **Bays:** the sill's pocket floor slopes outward to drain, but the top of an SN is flat, with no outward fall over its two fixing counterbores. Bed both SN screws in MS polymer like the other wet-side fixings, and fill their counterbores flush over the heads.
6. **Assemble and fit the transom.**
   1. Measure between the two node faces (the faces with the dovetail slots) at the transom height, at the outside and inside edges, and take the smaller figure. The design figure is the frame width minus 80 mm (1704 mm for the home window).
   2. On the bench, seal, close and screw the dry-fitted transom (build guide 4.3) with the joint rules. Set its joints with the shims (0.5–1.5 mm each, spread evenly) so the shoes' outer end faces end up 0.5 mm closer together than the measured distance, so the shoes slide into the nodes. The steel tube leaves only 1 mm clear at each shoe's end wall: if the transom has to close up by more than 2 mm in total, trim the tube by the excess first. Drive the tek screws. With V-slot cores, a V-slot transom pair takes the 8g × 20 self-tappers from the BOM in 3.5 mm pilots instead (build guide 8.6). A steel transom (see "Standard tubes in this V-slot window" in the BOM) keeps the tek screws.
   3. Lay 3 mm foam cord in the groove across each shoe's outer end face, and butter the rest of that face with MS polymer.
   4. Lift the transom unit in from the room side, and slide its shoe tongues down the node dovetails to the stop.
   5. Drive the four M4 × 16 countersunk lock screws down the dovetail flanks. Their heads finish at the floor of the magnet channel, under the strip fitted in step 7.
   6. Tool the squeezed-out sealant along each shoe/node seam on the inside and outside faces. On the outside face, fill the small notch where each shoe's rounded bottom edge sits on the end of the lower jamb, and tool it flush so water runs off.
   7. **Bays: check the nodes line up.** Hold a straightedge or a plumb line through the slot centres of each SN, TX and HN. If a TX is more than 0.5 mm off the line, take the transom out (undo its lock screws and cut the seam sealant), reset its shims (step 6.2) and refit it before going on.
   8. **Bays: lower mullions.** For each one, measure from the SN slot face to the TX's lower slot face, at the outside and inside edges, and take the smaller figure. The design figure is the `mullion_lower` tube length in the cut list plus 8 mm (876 + 8 = 884 mm for the two-bay home window). Seal, close and screw its dry-fitted assembly (build guide 7.1) with the joint rules. Set its joints with the shims (0.5–1.5 mm each, spread evenly) so the shoes' outer end faces end up 0.5 mm closer together than the measured distance, so the shoes slide into the nodes. The steel tube leaves only 1 mm clear at each shoe's end wall: if the mullion has to close up by more than 2 mm in total, trim the tube by the excess first. Drive the tek screws. With V-slot cores, a V-slot mullion pair is held by M5 screws into T-nuts instead: hang the nuts when you thread the assembly (build guide 7.3 and 8.4), and tighten them here. A steel mullion keeps the tek screws.
   9. Lay 3 mm foam cord in the groove across each MSL end face, and butter the rest of the face with MS polymer. Lift the mullion in from the room side and slide both tongues down the SN and TX slots together, to the stop. Drive its four M4 × 16 countersunk lock screws down the slot flanks, two at each end.
   10. **Bays: upper mullions.** Do the same from the TX's upper slot face to the HN slot face (the `mullion_upper` tube length in the cut list plus 8 mm, so 478 + 8 = 486 mm), with MST at the bottom and MSH at the top (build guide 7.2), and the same shim range and tube trim as in step 6.8.
   11. Tool the sealant along every mullion shoe/node seam on the inside face.
7. **Frame seals and magnet strip.**
   1. **EPDM bulb seals.** Fit two continuous loops round each sash opening, each with a single joint: the outer seal in the fin kerf, and the inner seal in the inner-stop kerf.
      - Start each loop at the middle of the head. Run it across the head, down an upper jamb, through the shoe turn, along the transom, through the other shoe turn, up the other jamb and back to the start.
      - **Bays:** on a mullion side the loop runs down the upper mullion's kerf, turns along the transom in the MST shoe and turns up into the head's kerf in the MSH shoe.
      - Push the seal in without stretching it.
      - Cut the end square and butt it to the start with a drop of gel CA.
   2. **Magnet strip B.** Skip it if your params file has `"screen": false`. Press it into the frame magnet channel: along the lower half of the transom's inside face, through each shoe turn, up both upper jambs, and across the head. It covers the lock screw heads.
      - **Bays:** one loop per bay. On a mullion side it runs up the mullion's channel, which drops across the TX face to the transom channel, and turns along the head in the MSH shoe. Strip B must be the matched partner of the screen's strip A (or a steel strip, if strip A is a plain magnet).
8. **Hang the sash** (each sash, with bays). Two people. The frame fixings are all in (step 5), and the stays are already on the sash (build guide 5.4).
   1. Hold the sash in the opening, and place each stay's track against its upper jamb (or, with bays, against the upper mullion on a mullion side), at the height the stay's datasheet shows.
   2. Centre each track 35–35.5 mm in from the frame's outside face, level with its sash arm. Its body then sits between the jamb fin top (28 mm) and the sash lip (46 mm). Its screws hit the jamb tube (21.5–41.5 mm in) below the JU fixing counterbores (43–53 mm in). The stay must be no more than 14 mm wide with a stack of no more than 13 mm (BOM line). The screw positions above are for a jamb; for a track on a mullion see step 8.3.
   3. Drill 3.2 mm pilots through the track holes, and screw the track on with 8g × 25 stainless countersunk screws.
      - **Bays:** a track on a mullion goes into its steel tube. Use the 8g × 16 tek screws from the BOM, with no pilot. The two stays either side of a mullion screw into the same tube, and 16 mm screws miss each other inside it.
      - **V-slot cores:** the upper-jamb tube is 18.5–38.5 mm in, and the track screws bite the solid metal beside its groove. Drill 3.5 mm pilots. A V-slot mullion takes the 8g × 16 self-tappers from the BOM, also in 3.5 mm pilots.
   4. Close the sash, and check both seals touch evenly. Adjust with the stay screws if needed.
9. **Glaze the fixed pane** (each pane, with bays).
   1. Fit the outer wedge gasket into the stop kerfs.
   2. Place two GW wedge blocks on the sill floor at the quarter points (over the step-4 packers), and one GF locator at mid-height on each side.
   3. Fit the glass, or the fixed acrylic unit.
   4. Snap in the BFH/BFV beads from the room side, with the inner wedge gasket.
10. **Seal outside.**
    1. Push backer rod into the gap between the frame and the brickwork, gun MS polymer over it, and tool it smooth.
    2. Clip on the sill nose (NS) pieces with 1 mm gaps between them. The end pieces stop 17 mm from each frame edge, where the corner's key slot ends. Tool a small fillet of MS polymer from each nose end to the perimeter seal.
    3. Push in the weep caps (WC), open end facing down: one on each SW sill weep and one on each SBE sash weep (open the sash to reach them), so four per bay. The TE weeps in the transom fin drain the chamber between the sash seals and get no cap.
    4. Never seal over weep holes or the nose drip.
11. **Inside.** Fill the gap to the reveal with low-expansion foam, trim it, and refit the architraves.
12. **Screen** (each screen, with bays). Skip this step if your params file has `"screen": false`.
    1. Screw the HG hinge leaves to the head inserts, with two M4 × 10 pan- or button-head screws each. Hinges go on the two end H segments (of that bay's run, with bays) and, with three hinges, on the segment nearest the centre. With an even number of H segments, use either of the two middle ones. On the 7-segment home head that means the 1st, 4th and 7th.
    2. Pin an HS leaf into each HG with an M4 × 50 bolt and nyloc. Tighten it snug, but the knuckles must still turn.
    3. Hold the screen up against the frame, closed on the magnets, with an even 10 mm overlap all round.
    4. Swing the HS leaves down onto its top rail, and screw them on with 4g × 12 screws (2 mm pilots).
    5. Check the magnetic strip closes along all four sides.
13. **Cam locks.** With the sash closed, turn each lever 60° counter-clockwise. The sash should pull in about 3 mm, and the seals should compress evenly.
