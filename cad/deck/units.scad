// cad/deck/units.scad: one bench-built unit per render (u = 0 frame, 1 transom, 2 sash with glass, 3 screen, 4 frame with transom and fixed glass)
include <lib.scad>

u = 0;

if (u == 0) frame_unit(C_FRAME, vis = 3);
if (u == 1) transom_unit(C_TRANSOM, cams = true, vis = 3);
if (u == 2) sash_unit(C_SASH, keepers = true, vis = 3);
if (u == 3) screen_unit(C_SCREEN, vis = 3);
if (u == 4) {
    frame_unit(C_FRAME, vis = 3);
    transom_unit(C_TRANSOM, cams = true, vis = 3);
    color(C_GLASS) fixed_glass();
}
