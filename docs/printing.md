# Printing

## Pick the material tier

Rule: heat-deflection temperature (HDT @ 0.45 MPa) at least 15 °C above the hottest surface temperature, and exterior parts UV-stable or painted. Melbourne design surface temperatures: about 50–55 °C on light colours, 75–80 °C on dark colours in full afternoon sun.

| Tier | Exposure | Min HDT | UV | Examples |
|---|---|---|---|---|
| 1 | South-facing / shaded, light colour | ≥ 70 °C | Stable or painted | PETG + exterior acrylic paint, ASA |
| 2 | East / part sun, light colour | ≥ 90 °C | Inherently stable | ASA |
| 3 | North / west full sun, or any dark colour | ≥ 105 °C | Inherently stable | ASA-CF, PC-ABS (painted) |

A dark colour moves any exposure up one tier. Set `tier` in your params file. The parts list marks each part `exterior` (print in your tier's material) or `interior` (PETG in every tier).

## Settings (Bambu P1S)

- 0.4 mm nozzle (hardened steel for CF filaments), 0.2 mm layers.
- 5 walls, 5 top and 5 bottom layers, 15% gyroid infill. Most profile walls are 2.5 mm, so they print solid anyway.
- ASA and PC-ABS: enclosure closed, door shut, no auxiliary fan, textured PEI plate with glue stick.
- Heat-set inserts: 230 °C iron, pressed flush.

## Orientation

| Parts | Orientation |
|---|---|
| Segments (H, S, SW, JL, JU, T, TE, ML, MU, SH, SB, SBE, SV, NH, NV), TC | Standing on an end face, exactly as exported. No supports. The 2 mm rounded long edges stand vertical, and each 0.8 mm joint bevel prints as four 0.2 mm layers. |
| Corners (CH, CSL, CSR, CS, CN) | As exported. Supports on build plate only, for the rebate overhangs. |
| JN, TSL, TSR, and with bays SN, HN, TX, MSL, MST, MSH | On the outside face (the face that looks out of the window), so the dovetail slots and tongues print in plane and slide without binding. Supports on build plate only. |
| Beads (B*) | Lying on their glass face (the face with the gasket kerf), so the rounded room-side edge prints on top. |
| Sill nose (NS), acrylic spacers (A*) | Laid flat on their longest face. |
| Setting blocks, weep caps, cam parts, hinge leaves, keepers | Flat side down. |

## Quantities

`bom/<name>-parts.csv` lists every part and how many to print, and `bom/<name>.md` has the filament estimate (run `python3 bom/build_bom.py <name>` after rendering). `cad/generated/parts.csv` is the same list for whichever window was generated last, and `cad/box.sh test` and `png` regenerate it for the bench window, so don't print from it.

The 1800 × 1500 home window needs 160 prints in 35 types, about 16.36 kg of exterior filament plus 3.84 kg of interior PETG (measured from the STLs on 2026-10-11). The same opening split into two bays for a 1200 × 900 mm sheet (`params/home-1800x1500-2bay.json`) needs 226 prints in 43 types, about 19.06 kg of exterior filament plus 4.75 kg of interior PETG (measured from its STLs on 2026-10-11). Print a test coupon (TC) and one segment of each profile first, and check the fit before committing a full spool. On the coupon, also check the thin lip outside the cord groove at each end face: if it chips, set `JOINT_BEVEL` to 0.6 in `cad/dims.json` and re-render.

## Acrylic sandwich size

With acrylic glazing, `acrylic_t` and `acrylic_gap` set the panel thickness and air gap (default 4 + 16 + 4 = 24 mm). The frame keeps its 24 mm pocket, so a thinner sandwich prints deeper beads (hollow, so only slightly heavier) and lower spacer bars. On the 2-bay home window, 3 + 12 + 3 is about 0.5 kg more bead PETG and 0.3 kg less spacer filament, so roughly the same plastic; the gain is about 4.8 kg less acrylic.
