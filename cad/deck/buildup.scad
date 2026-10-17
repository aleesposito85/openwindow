// cad/deck/buildup.scad: bench assembly sequence (step 1 sill, 2 jambs, 3 head, 4 transom dry fit, 5 sash, 6 screen), lying inside face up
include <lib.scad>

step = 1;
lift = 160;

rotate([90, 0, 0]) {
    if (step <= 4) {
        sill_member(step == 1 ? C_HI : C_DONE, step == 1);
        if (step >= 2) jamb_members(step == 2 ? C_HI : C_DONE, step == 2);
        if (step >= 3) head_member(step == 3 ? C_HI : C_DONE, step == 3);
        if (step == 4) translate([0, lift, 0]) transom_unit(C_HI, tubes = true, cams = true);
    }
    if (step == 5) sash_unit(C_HI, tubes = true, glass = true, keepers = true);
    if (step == 6) screen_unit(C_HI, tubes = true, mesh = false);
}
