// cad/deck/hero.scad: the generated window from outside, awning sash pushed open
include <lib.scad>

open = 22;
ztop = SZ0 + SASH[1];

frame_unit(C_FRAME, vis = 2.5);
transom_unit(C_FRAME, cams = false, vis = 2.5);
color(C_GLASS) fixed_glass();
translate([0, SASH_Y0, ztop]) rotate([-open, 0, 0]) translate([0, -SASH_Y0, -ztop]) sash_unit("#b4bec6", vis = 2.5);
