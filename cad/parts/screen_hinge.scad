// cad/parts/screen_hinge.scad
include <../generated/dims.scad>

KN_D = 10;
PIN_D = 4.3;
LEAF_T = 3;
AXIS_W = SCREEN_DEPTH + 5;
FRAME_KN = [[-20, -12], [-4, 4], [12, 20]];
SCREEN_KN = [[-11.6, -4.4], [4.4, 11.6]];
WALL_T = 3;
PLATE_W = 17;

function hinge_hole_v() = HINGE_BOSS_X - (FRAME_BODY - SCREEN_OVERLAP);
function hinge_wall_v() = -WALL_T;
function hinge_plate_v() = -WALL_T - PLATE_W;
function hinge_leaf_t() = LEAF_T;

WALL_R = 1;

module soften_plan(r) { offset(r = r, $fn = 32) offset(delta = -r) children(); }

module knuckles(spans) {
    for (s = spans) translate([s[0], 0, AXIS_W]) rotate([0, 90, 0]) cylinder(d = KN_D, h = s[1] - s[0], $fn = 32);
}

module pin_hole() {
    translate([-21, 0, AXIS_W]) rotate([0, 90, 0]) cylinder(d = PIN_D, h = 42, $fn = 20);
}

module screen_hinge(code) {
    v_hole = hinge_hole_v();
    assert(EDGE_R <= PLATE_W / 2 && WALL_R <= WALL_T / 2, "hinge leaf rounding fits the plate and wall");
    difference() {
        union() {
            linear_extrude(LEAF_T) union() {
                soften_plan(EDGE_R) translate([-20, hinge_plate_v()]) square([40, PLATE_W]);
                translate([-20, hinge_plate_v() + EDGE_R]) square([40, PLATE_W - EDGE_R]);
                translate([-20, hinge_wall_v()]) square([40, WALL_T - WALL_R]);
            }
            linear_extrude(AXIS_W) soften_plan(WALL_R) translate([-20, hinge_wall_v()]) square([40, WALL_T]);
            knuckles(FRAME_KN);
        }
        pin_hole();
        for (u = [-BOSS_PITCH / 2, BOSS_PITCH / 2])
            translate([u, v_hole, -0.01]) cylinder(d = 4.4, h = LEAF_T + 0.02, $fn = 20);
    }
}

module screen_leaf(code) {
    assert(EDGE_R <= 5 / 2, "screen leaf rounding fits its wall");
    difference() {
        union() {
            translate([0, 0, SCREEN_DEPTH]) linear_extrude(LEAF_T) soften_plan(EDGE_R) translate([-12, 0]) square([24, 28]);
            translate([0, 0, SCREEN_DEPTH]) linear_extrude(AXIS_W - SCREEN_DEPTH) soften_plan(EDGE_R) translate([-12, 0]) square([24, 5]);
            knuckles(SCREEN_KN);
        }
        pin_hole();
        for (u = [-8, 8]) translate([u, 18, SCREEN_DEPTH - 0.01]) cylinder(d = 3.4, h = LEAF_T + 0.02, $fn = 16);
    }
}
