// cad/deck/hinge.scad: screen hinge HG on an H segment and HS on the screen top rail, pinned with an M4 x 50 bolt
include <lib.scad>

L = 120;
ax = SCREEN_DEPTH + 5;
Ht = 0;

multmatrix([[0, 0, 1, -L / 2], [0, 1, 0, 0], [-1, 0, 0, Ht]]) color(C_FRAME) segment("sash_rebate", L, "H", bosses = true);
multmatrix([[0, 0, 1, -L / 2], [0, 1, 0, DEPTH], [-1, 0, 0, Ht - FRAME_BODY + SCREEN_OVERLAP]]) {
    color(C_SCREEN) linear_extrude(L) profile("screen");
}
multmatrix([[1, 0, 0, 0], [0, 0, 1, DEPTH], [0, -1, 0, Ht - FRAME_BODY + SCREEN_OVERLAP]]) {
    color(C_HI) screen_hinge("HG");
    color("#d9692b") screen_leaf("HS");
    color("#3b3f43") translate([-25, 0, ax]) rotate([0, 90, 0]) cylinder(d = 4, h = 50, $fn = 20);
}
