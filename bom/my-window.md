# BOM: my-window

Prints: 294 parts in 48 types (list: `bom/my-window-parts.csv`).

| Group | Item | Qty | Unit |
|---|---|---|---|
| Fixings | Timber screw 10g x 75, stainless or galvanised (frame fixings) | 44 | pcs |
| Fixings | Tek screw 8g x 25, 410 stainless, countersunk (steel tubes: transom) | 11 | pcs |
| Fixings | M5 x 16 countersunk machine screw, stainless (V-slot tube screws, one T-nut each) | 10 | pcs |
| Fixings | M5 x 20 countersunk machine screw, stainless (V-slot tube screws, one T-nut each) | 36 | pcs |
| Fixings | M5 x 25 countersunk machine screw, stainless (V-slot tube screws, one T-nut each) | 40 | pcs |
| Fixings | M5 slide-in T-nut for 20-series V-slot, 6 mm slot (V-slot tube screws) | 86 | pcs |
| Fixings | Self-tapping screw 8g x 12 stainless, countersunk (screen tube screws) | 40 | pcs |
| Fixings | M4 heat-set insert for a 5.6 x 8 mm hole | 46 | pcs |
| Fixings | M4 x 10 countersunk machine screw (cam bases CMB, keepers KP) | 16 | pcs |
| Fixings | M4 x 10 pan or button head machine screw (hinge frame leaves HG) | 8 | pcs |
| Fixings | M4 x 8 pan screw + 20 mm penny washer (cam pivots) | 4 | pcs |
| Fixings | M4 x 16 countersunk machine screw (transom and mullion lock screws) | 12 | pcs |
| Fixings | M4 x 50 bolt + nyloc nut (hinge pins) | 4 | pcs |
| Fixings | 4g x 12 self-tapping screw (screen leaves HS) | 8 | pcs |
| Fixings | Plastic window packers, assorted 1-10 mm (one stack per position) | 53 | pcs |
| Hardware | Stainless friction stay pair, 400 mm, stack <= 13 mm, track/arm width <= 14 mm (check rating >= 4.3 kg) | 2 | pair |
| Hardware | Friction-stay screw 8g x 25 stainless, countersunk (tracks to upper jambs; match the stay's holes) | 8 | pcs |
| Hardware | Self-tapping screw 8g x 16 stainless, countersunk (friction-stay tracks to upper mullions, 3.5 mm pilot; match the stay's holes) | 8 | pcs |
| Hardware | Friction-stay screw 8g x 16 stainless, countersunk (arms to sash sides; match the stay's holes) | 12 | pcs |
| Seals | EPDM bulb kerf seal, 3 mm kerf (outer + inner loop round each sash opening) | 10.67 | m |
| Seals | EPDM glazing wedge gasket, 3 mm | 22.66 | m |
| Seals | Closed-cell foam cord, 4 mm (one ring per segment joint) | 14.9 | m |
| Seals | Closed-cell foam cord, 3 mm (transom and mullion shoe seams) | 0.42 | m |
| Seals | MS-polymer sealant rated for +/-50% joint movement (ASTM C920 Class 50 or equal), 290 ml cartridge (joints, fixing bedding, outside perimeter) | 4 | pcs |
| Seals | Butyl flashing tape, 150 mm wide (sill tray; or two 100 mm runs lapped 50 mm) | 2.08 | m |
| Seals | Backer rod, 10 mm | 6.54 | m |
| Seals | Low-expansion window foam, can | 1 | pcs |
| Seals | Gel CA glue (EPDM loop joints) | 1 | pcs |
| Screen | Flexible magnetic strip A, 12.7 mm, adhesive-backed (screen back channel) | 5.58 | m |
| Screen | Flexible magnetic strip B, 12.7 mm, adhesive-backed, matched to A, or adhesive steel strip (frame magnet channel) | 5.58 | m |
| Screen | Fibreglass insect mesh | 1.02 | m2 |
| Screen | Screen spline, 4 mm | 5.58 | m |
| Screen | Two-part epoxy, 5-minute (screen corner joints) | 1 | pcs |
| Tube | V-slot 2020, 4-slot, 1000 mm pieces (cut plan in the BOM) | 16 | pcs |
| Tube | Tube alu10 (total length; buy in 1 m/3 m stock) | 5.27 | m |
| Tube | Tube steel40x20 (total length; buy in 1 m/3 m stock) | 1.7 | m |
| Glazing | Acrylic 3 mm, 829 x 878 (fixed pane) | 4 | pcs |
| Glazing | Acrylic 3 mm, 737 x 388 (sash pane) | 4 | pcs |
| Glazing | Silica gel desiccant beads | 200 | g |
| Glazing | Butyl glazing tape, 3 mm (acrylic sandwich edge) | 22.66 | m |
| Filament | PETG (interior) | 4.93 | kg |
| Filament | PETG + exterior paint, or ASA (exterior, tier 1) | 22.11 | kg |

## Tube cut list (`bom/my-window-cutlist.csv`)

| Member | Core | Length (mm) | Qty |
|---|---|---|---|
| head 1/2 | vslot2020 | 946.1 | 1 |
| head 2/2 | vslot2020 | 774.9 | 1 |
| sill 1/2 | vslot2020 | 946.1 | 1 |
| sill 2/2 | vslot2020 | 774.9 | 1 |
| jamb_lower | vslot2020 | 943.0 | 2 |
| jamb_upper | vslot2020 | 475.0 | 2 |
| transom | steel40x20 | 1696.0 | 1 |
| mullion_lower | vslot2020 | 876.0 | 2 |
| mullion_upper | vslot2020 | 478.0 | 2 |
| sash_horizontal | vslot2020 | 746.0 | 4 |
| sash_vertical | vslot2020 | 397.0 | 4 |
| screen_horizontal | alu10 | 816.0 | 4 |
| screen_vertical | alu10 | 501.0 | 4 |

## Glass (`bom/my-window-glass.csv`)

| Pane | Glazing | Width (mm) | Height (mm) | Qty |
|---|---|---|---|---|
| fixed | acrylic | 829 | 878 | 2 |
| sash | acrylic | 737 | 388 | 2 |

## V-slot cut plan

16 pieces of 1000 mm V-slot 2020, with 2 mm per saw cut.

| Piece | Cuts (mm) | Offcut (mm) |
|---|---|---|
| 1 | head 1/2 946.1 | 53.9 |
| 2 | sill 1/2 946.1 | 53.9 |
| 3 | jamb_lower 943 | 57 |
| 4 | jamb_lower 943 | 57 |
| 5 | mullion_lower 876 | 124 |
| 6 | mullion_lower 876 | 124 |
| 7 | head 2/2 774.9 | 225.1 |
| 8 | sill 2/2 774.9 | 225.1 |
| 9 | sash_horizontal 746 | 254 |
| 10 | sash_horizontal 746 | 254 |
| 11 | sash_horizontal 746 | 254 |
| 12 | sash_horizontal 746 | 254 |
| 13 | mullion_upper 478, mullion_upper 478 | 42 |
| 14 | jamb_upper 475, jamb_upper 475 | 48 |
| 15 | sash_vertical 397, sash_vertical 397 | 204 |
| 16 | sash_vertical 397, sash_vertical 397 | 204 |

## V-slot joins

Pieces butt together inside a printed segment, a quarter of the way along it, clear of its T-nut. Measure from the left end seen from outside (jambs: from the bottom); the segments are symmetric, so either end works.

- head: 946.1 mm, inside segment 5
- sill: 946.1 mm, inside segment 5

## Standard tubes in this V-slot window

- steel transom: 1696 mm is longer than the 1000 mm V-slot pieces, and a V-slot pair would deflect 52.9 mm (limit 9.5 mm)

## Bays

2 bays, 869 mm apart. Mullion centre lines, from the frame's left outer edge as seen from outside: 892 mm.
