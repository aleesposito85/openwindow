# Test log

Bench window: params/bench-600.json (acrylic glazing, tier 1 PETG).
Mount it in a timber test box (opening 600 × 600, 63 mm deep), fixed exactly as in the install guide. Rows 8 and 9 need a window with bays, so they use the two-bay bench window described below the table. Rows 10–12 are for V-slot cores (`"core": "vslot"`), and a V-slot build also runs rows 1–6 on a V-slot bench window. Leave `bench-600.json` alone: it is a fixed reference. Save a copy of it as `params/bench-600-vslot.json` with `"name": "bench-600-vslot"` and `"core": "vslot"` added, then generate, render and build its BOM as in the README. It is all V-slot (5 pieces of 1 m).

| # | Test | Method | Pass criterion | Date | Result | Notes |
|---|---|---|---|---|---|---|
| 1 | Fit | Assemble from the printed parts with no filing | Every joint closes, diagonals within 2 mm, sash closes on both seals | | | |
| 2 | Water | Garden hose, fan spray, 300 mm from the outside face, 15 min, sash closed and cammed. Aim at the opening-side edge of every segment joint, where the joint crosses the stops, fin and inner stop. | No water on the room side, including at the inside face of every joint; water leaves through the weeps | | | |
| 3 | Air | Smoke pencil along both sash seal lines, the screen magnet line, and every segment joint, concentrating on its opening-side edge (stop, fin and inner-stop roots), with a fan blowing at the outside face | No visible smoke draw | | | |
| 4 | Heat/creep | TC coupon painted matt black, 80 °C under a heat lamp (thermocouple on the face) for 24 h, with an M4 screw torqued to 1.5 N·m in one insert | No visible distortion; screw still holds 1.5 N·m | | | |
| 5 | Sash load | Hang 2 × sash weight from the open sash's bottom rail for 1 h | No permanent set at the stays or the corners after unloading | | | |
| 6 | Cam | Close and cam 50 times | Same compression on cycle 50 as on cycle 1, no cracking at keeper post or flag | | | |
| 7 | Screen corners | Look for light at the screen's bottom corners (where its magnet strip leaves the transom) | No gap above 1 mm; if there is one, add foam pads and record where | | | |
| 8 | Mullion tees (windows with bays) | Rows 2 and 3 again, aimed at the SN, TX and HN seams and at the shoe turns either side of each mullion | No water inside and no smoke draw at any mullion seam | | | |
| 9 | Mullion shoe pull-out (windows with bays) | With the lock screws in, hook a luggage scale round the mullion next to one shoe and pull room-ward along the slot, by hand, to 200 N for 10 s. Do the shoe at the SN and the shoe at the TX. The mullion lock screws grip about half as much tongue as the jamb node's | No slip under 200 N, and no cracking at the shoe or the node | | | |
| 10 | V-slot profile (V-slot cores) | Calipers on one piece: groove mouth width at the surface, and slot depth to the floor | Mouth 9.0–9.4 mm, depth 5.9–6.3 mm: the OpenBuilds profile that the screw positions assume | | | |
| 11 | V-slot stay screw pull-out (V-slot cores) | On a JU segment on an offcut, drive an 8g × 25 screw through a 3.5 mm pilot at the stay line (35 mm in), then pull it straight out with a luggage scale to 300 N for 10 s. Repeat on the weakest case: an MU segment on two side-by-side offcuts, 8g × 16 in a 3.5 mm pilot at 35 mm in, to 300 N | No pull-out, and no cracking at the extrusion or the print | | | |
| 12 | T-nut hold (V-slot cores) | A segment on an offcut with its M5 screw and T-nut snug: push the segment along the tube with a luggage scale to 150 N for 10 s | No slip, and no cracking round the countersink | | | |

The joint sealant is assumed to take the joint movement: each 1 mm gap cycles between about 0 mm (hot) and 1.3 mm (cold), which needs a sealant rated for ±50 % movement. Repeat rows 2–3 after the bench window has seen a hot day and a cold night, and record any joint whose sealant has torn or come away.

**Two-bay bench window (rows 8 and 9).** `bench-600` has one bay, and giving it a small `max_pane` does not work: at two bays the cam keepers fall outside the transom segments, and `generate.py` prints a `WARNING`. Use this params file instead. Save it as `params/bench-1000-2bay.json`, then generate, render and build its BOM as in the README, and mount it in a timber test box (opening 1000 × 600, 63 mm deep):

```json
{
  "name": "bench-1000-2bay",
  "opening_w": 1000,
  "opening_h": 600,
  "fix_gap": 8,
  "awning_h": 200,
  "glazing": "acrylic",
  "tier": 1,
  "max_pane": [600, 500]
}
```

`generate.py` gives `bench-1000-2bay: 45 part types, 186 prints` and no `WARNING`. It has 2 bays with one mullion, centred 492 mm from the left outer frame edge. Each fixed pane is 429 × 228 mm and each sash pane 337 × 138 mm, both inside the 600 × 500 mm sheet.

Full-size build only after rows 1–6 pass. A window with bays also needs rows 8–9 passed on a 2-bay bench window. A window with V-slot cores runs rows 1–6 on the V-slot bench window (`bench-600-vslot`) as well, since row 5 loads the sash through its M5 corners and V-slot stays, and also needs rows 10–12 passed. Order glass from `bom/<name>-glass.csv` (or the glass table in `bom/<name>.md`) after the opening is measured and the BOM rebuilt (install guide step 2).
