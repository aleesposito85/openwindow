# OpenWindow owner's manual

This manual is for a finished, installed OpenWindow v1: a top-hung awning sash over a fixed pane, with a hinged insect screen on the room side. Part IDs (`H`, `TE`, `CMH` and so on) are engraved on a hidden face of every printed part and match the build and install guides. Keep your params file (`params/<name>.json`), the `bom/<name>.*` files and the `cad/stl/<name>/` folder with the house papers: they are how you re-print a part or re-order glass.

## Operation

### Opening the sash

1. Lift the insect screen by its bottom rail. It is hinged along the top and swings up towards the room.
2. Turn both cam levers (`CMH`) back, clockwise as seen from the room, about 60°, until each cam flag is clear of its keeper (`KP`) on the sash.
3. Push the sash out by its bottom rail. The friction stays hold it wherever you stop. Don't force it past the stays' end stop.
4. Lower the screen. It closes itself on its magnets, so the sash can stay open with the screen shut.

### Closing and latching

1. Lift the screen.
2. Pull the sash in by its bottom rail until it sits evenly on both seals all round.
3. Turn each cam lever about 60° counter-clockwise. The flag rides up the keeper and pulls the sash in about 3 mm, so both seals compress evenly. Latch both cams, not just one.
4. Lower the screen.

The two cams are latches that hold the sash on its seals. They are not a keyed security lock.

A window split into bays by mullions has a sash, two cams and a screen in every bay. Open, close and latch each one on its own, as above.

## Screen

- The screen hangs on printed pin hinges (`HG` on the head, `HS` on the screen, an M4 × 50 bolt and nyloc as the pin): three on a wide window, two on a narrow one. Gravity and a matched pair of magnetic strips (A on the screen, B on the frame) close it.
- Open it by the bottom rail only, and let it close gently. Don't hang anything on it or lean on it.
- If light shows at the bottom corners, where the screen's magnet line leaves the transom, stick a thin foam pad there (test-log row 7).
- If it won't close by itself, the hinge pins are too tight: back off the nyloc nuts until the knuckles turn freely.
- To take the screen off, remove the three hinge bolts. To re-mesh it, pull the old 4 mm spline, roll in new mesh and spline, and trim.

## Ventilation and weather

- A top-hung awning sheds light rain when it is open a little: water runs down the outside of the glass and off the sash. Keep the opening small in rain.
- Close and latch the sash in strong wind, storms or driving rain, and when nobody is home. The friction stays are sized for the sash's weight, not for gusts.
- Water that gets past the outer weather seal drains out of the chamber between the two seals through the weep slots in the transom fin (`TE` segments). Water in the glazing pockets drains through the sill weeps (`SW`) and sash weeps (`SBE`), each behind a flap cap (`WC`). These openings are part of the design: never seal, paint or block them.

## Cleaning

- **Glass and frame faces:** warm water with a little dish detergent, a soft cloth or sponge, and a squeegee. No solvents (acetone, thinners, methylated spirits on painted parts), no abrasive pads or powders: they attack printed plastics and paint.
- **Acrylic glazing:** use a plastic-safe cleaner and a microfibre cloth. Acrylic scratches easily, and ammonia or solvent cleaners craze it.
- **Replacement acrylic:** cut new panels to the sizes in `bom/<name>-glass.csv`, in the same thickness as the window was built for (the glass list names it, e.g. "2 x 3 mm clear acrylic, 12 mm gap"). A different thickness needs re-printed beads and spacers.
- **Outside faces:** clean the fixed pane and the outside of the sash from outside, from the ground or a safe ladder or platform. Don't lean out through the open sash.
- **Seal kerfs and seals:** vacuum or brush out grit, and wipe the EPDM with water. Keep oils and petroleum products off EPDM.
- **Weeps:** pull each weep cap (`WC`), clear the slot with a pipe cleaner, and push the cap back with its open end facing down. Brush out the transom fin slots with the sash open.
- **Screen mesh:** take the screen off and wash it with soapy water and a soft brush, or vacuum it with a brush head.

## Maintenance schedule

| When | Check and do |
|---|---|
| Monthly, and after storms | Weeps (`SW`, `SBE` caps, `TE` fin slots) and the sill-nose drip are clear; no water inside; screen closes on its magnets |
| Every season | Both EPDM seal loops are seated in their kerfs and their glued joints are closed; glazing wedge gaskets in place; mesh intact |
| Every 6 months | Friction stays: wipe clean, lubricate the pivots and slides as the stay maker specifies, and check their screws (8g × 25 in the tracks, 8g × 16 in the arms) are snug without over-tightening into the plastic. Cam locks: even pull-in, no cracks at the keeper post or flag, pivot screw snug |
| Yearly | Sealant at the segment joints (inside and outside faces), the perimeter seal to the brickwork and the sill-nose end fillets: cut out and re-fill any torn or loose bead with ±50 % MS polymer. Printed parts: look for chalking, cracks or creep, mostly on sunny faces. Hinge pins snug but turning |
| Every few years | Replace EPDM seals that have taken a permanent set or cracked, magnetic strips that no longer pull, and paint on painted (tier 1) parts once it chalks |

In the first year, check the joint sealant after the first hot spell and again after the first cold snap. Each 1 mm joint gap cycles between about 0 mm (hot) and 1.3 mm (cold), and that is when a weak bead tears.

## Seasonal care

- **Winter:** condensation on the inside of the glass and frame is room moisture. Wipe it off and ventilate (crack the sash with the screen shut). Keep the weeps clear so the pockets can drain.
- **Fogging between panes:** in an IGU this means its edge seal has failed, and the unit must be replaced. In an acrylic sandwich the desiccant is saturated: open the unit, dry it and refill the silica gel (Troubleshooting).
- **Summer:** printed parts soften if the surface gets hotter than the material tier allows. Watch sunny and dark faces for distortion in the first summer. Keep light colours, and don't stick dark films or stickers on the frame.
- **Before storm season:** check the seals and sealant, and clear the weeps.

## Troubleshooting

| Symptom | Likely cause | What to do |
|---|---|---|
| Draft at a segment joint | Sealant torn, often at the opening-side edge or in the band outside the cord ring | Cut out the loose sealant, clean, re-fill with ±50 % MS polymer and tool it, ideally at 15–25 °C |
| Draft round the sash | A seal loop out of its kerf, an open loop joint, or the cams not pulling in evenly | Re-seat the loop without stretching it, re-glue the joint with gel CA, latch both cams |
| Water inside | Blocked weeps, a torn joint or perimeter seal, or the head flashing not lapping the head | Clear the weeps first. Then hose-test from outside (test-log row 2) to find the leak, and re-seal |
| Condensation between acrylic panes | Desiccant saturated, or the butyl tape leaking | Unclip the beads, lift the unit out, open it, dry it, refill the silica gel and re-tape |
| Fog between IGU panes | Failed IGU edge seal | Replace the IGU. The size is in `bom/<name>-glass.csv` |
| Cam won't pull the sash in | Keeper loose or on the wrong boss pair, a seal out of its kerf, or the sash has dropped | Keeper screws (M4 × 10) on the outer boss pair of its `SBE`; re-seat the seals; check the stays and their screws |
| Cam lever loose or wobbly | Pivot screw loose, or a worn handle | Snug the M4 × 8 pivot screw and its penny washer; re-print `CMH` |
| Gaps along the screen | Magnetic strip unstuck or not a matched pair, or the screen hanging crooked | Re-stick the strip, add foam pads at the bottom corners, re-align the hinge leaves |
| Sash sags, rubs or won't close evenly | Stay screws loose, a stay under-rated for the sash, or a sash corner creeping | Tighten the stay screws; check the stay rating is at least the sash weight; inspect the `CS` corners |
| Printed part cracked, warped or creeping | Material tier too low for the exposure, a dark colour, or a solvent | Re-print the part by its ID in the right tier and a light colour; paint tier-1 PETG |
| Glass rattles | Bead out of its keyway, or a wedge gasket missing | Snap the bead back in and refit the gasket |

## Safety

- **Glass:** order glass toughened wherever AS 1288 requires it; your glazier will know which panes. If a pane breaks, keep people away, wear gloves and eye protection, and tape or board the opening.
- **Weight:** the home window's fixed IGU weighs about 30 kg and the sash about 16 kg. Lift glass with two people and suction lifters.
- **Children and falls:** fit a window opening restrictor where the NCC requires one, for example on bedroom windows where the floor is 2 m or more above the ground below. Check your local requirements. The insect screen is not a barrier: never rely on it to stop a fall.
- **Not an emergency exit:** don't rely on the awning opening as an escape route.
- **Never lean on, hang from or put weight on an open sash,** and don't let children swing it.
- **Pinch points:** keep fingers clear of the sash edge and the cam levers when closing.
- **Working at height:** clean and maintain from the ground or a stable ladder or platform, never by leaning out of the window.
- **Not certified:** OpenWindow has no AS 2047 window rating and is not designed for bushfire-prone (BAL-rated) sites.

## Spare parts and repairs

- **Re-print any part by its ID** from `cad/stl/<name>/<ID>.stl`: exterior parts in your tier's material, interior parts in PETG (`bom/<name>-parts.csv` says which). If the STLs are lost, regenerate them from the params file: `python3 tools/generate.py params/<name>.json`, then `cad/box.sh render <name>` (or export each `cad/generated/parts/<ID>.scad` in your own OpenSCAD).
- **Swap in place:** beads (`BFH`, `BFV`, `BSH`, `BSV`) unclip; weep caps (`WC`), sill-nose pieces (`NS`, re-tool the end fillets), cam handles and bases (`CMH`, `CMB`), keepers (`KP`), hinge leaves (`HG`, `HS`) and the whole screen unscrew.
- **Workshop jobs:** segments, corners, nodes and shoes are threaded on or screwed to the metal tubes. With V-slot cores, the tube screws are M5 into T-nuts, so they undo and go back in. A mullion (`MSL`, `ML`, `MST`, `MU`, `MSH`) slides out towards the room once its four lock screws are out and the seams are cut, but only after the parts around it come out. Take off the sashes and screens on both sides of it, peel off magnet strip B (it covers the lock screw heads) and the EPDM bulb loops that run through its channel and kerfs, then unclip the beads and lift out both fixed panes beside it: a lower mullion's stop legs sit outside the panes. A frame part means taking the window out, so a small crack in a frame segment is better bonded and sealed in place.
- **Off-the-shelf spares:** EPDM bulb kerf seal (3 mm kerf), EPDM glazing wedge gasket (3 mm), 4 mm closed-cell foam cord, 12.7 mm magnetic strip A and B, 4 mm screen spline, fibreglass mesh, ±50 % MS-polymer sealant, and the screws listed in `bom/<name>.md`.
- **Glass:** re-order from `bom/<name>-glass.csv` (or the glass table in `bom/<name>.md`).

## Specifications

For the 1800 × 1500 home window (`params/home-1800x1500.json`). Your own window's figures are in `bom/<name>.md` and in the lines `generate.py` prints.

| Item | Value |
|---|---|
| Opening | 1800 × 1500 mm, brick veneer, 8 mm gap each side |
| Frame | 1784 × 1484 mm, 63 mm deep, 58 mm face |
| Layout | 450 mm top awning over a fixed pane |
| Glazing | 24 mm IGU 4/16/4: fixed 1698 × 878 mm, sash 1606 × 388 mm |
| Sash | About 15.7 kg on a 400 mm stainless friction-stay pair |
| Transom | 40 × 20 × 1.6 steel tube: 6.2 mm deflection at 0.7 kPa, limit 9.5 mm |
| Seals | Two continuous EPDM bulb loops round the sash; wedge gaskets both sides of the glass |
| Screen | Hinged, magnetic, fibreglass mesh, room side |
| Printed parts | 160 prints in 35 types: 16.36 kg exterior (tier 3, ASA-CF or PC-ABS, light colour) + 3.84 kg interior PETG |
| Glass thermal | About 2.7–3.0 W/m²K at the glass for double glazing (single glazing about 6). A design target, not a tested whole-window rating |
