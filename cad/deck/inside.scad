// cad/deck/inside.scad: the generated window from the room side; open = 1 swings the screen up and pushes the sash out
include <lib.scad>

open = 0;
sash_deg = 22;
screen_deg = 72;
ztop = SZ0 + SASH[1];
hinges = SCREEN[0] > 1000 ? [0, floor((N_HEAD - 1) / 2), N_HEAD - 1] : [0, N_HEAD - 1];
function hinge_x(i) = F + GAP + i * (SEG_HEAD + GAP) + SEG_HEAD / 2;

module hinge_set(swing) {
    for (i = hinges) multmatrix([[1, 0, 0, hinge_x(i)], [0, 0, 1, DEPTH], [0, -1, 0, H - FRAME_BODY + SCREEN_OVERLAP]]) {
        color(C_HI) screen_hinge("HG");
        translate([0, 0, AXIS_W_]) rotate([swing, 0, 0]) translate([0, 0, -AXIS_W_]) color(C_HI) screen_leaf("HS");
    }
}

AXIS_W_ = SCREEN_DEPTH + 5;
axis_y = DEPTH + AXIS_W_;
axis_z = H - FRAME_BODY + SCREEN_OVERLAP;

frame_unit(C_FRAME, vis = 2.5);
transom_unit(C_FRAME, cams = true, vis = 2.5);
color(C_GLASS) fixed_glass();
translate([0, SASH_Y0, ztop]) rotate([-(open ? sash_deg : 0), 0, 0]) translate([0, -SASH_Y0, -ztop]) sash_unit("#b4bec6", keepers = true, vis = 2.5);
translate([0, axis_y, axis_z]) rotate([open ? screen_deg : 0, 0, 0]) translate([0, -axis_y, -axis_z]) screen_unit(C_SCREEN, vis = 2.5);
hinge_set(open ? screen_deg : 0);
