// cad/parts/cam_lock.scad
include <../generated/dims.scad>

R0 = 18;
R1 = 40;
LEAD = 2;
RISE = 3;
ARC = 40;
BASE_T = 4;
BOSS_D = 14;
BOSS_H = 5;
LIP_T = 3;
HUB_D = 26;
LIP_HALF = 10;
KEEPER_HALF = 20;

function sash_face_w() = LIP_Y1 - DEPTH;
function keeper_v() = TRANSOM_W / 2 + TRANSOM_HALF_BODY + SASH_GAP + SASH_BODY / 2 - CAM_BOSS_X;
function lip_w() = BASE_T + LEAD + RISE;
function flag_half_run() = R1 * sin(ARC / 2);
function keeper_lip_half_run() = LIP_HALF;
function keeper_half_run() = KEEPER_HALF;

TOP_R = 1.5;

module soften_plan(r) { offset(r = r, $fn = 32) offset(delta = -r) children(); }

module soft_top(h, r = TOP_R, n = 6) {
    linear_extrude(h - r) children();
    for (i = [0 : n - 1]) translate([0, 0, h - r + i * r / n - 0.01]) linear_extrude(r / n + 0.01)
        offset(delta = -(r - sqrt(r * r - pow((i + 1) * r / n, 2)))) children();
}

module countersunk(d, t) {
    translate([0, 0, -0.01]) cylinder(d = d, h = t + 0.02, $fn = 20);
    translate([0, 0, t - 2.2]) cylinder(d1 = d, d2 = CSK_D, h = 2.21, $fn = 24);
}

module cam_base(code) {
    assert(EDGE_R <= 22 / 2, "cam base plate rounding fits the plate");
    difference() {
        union() {
            linear_extrude(BASE_T) soften_plan(EDGE_R) translate([-20, -10]) square([40, 22]);
            cylinder(d = BOSS_D, h = BASE_T + BOSS_H, $fn = 48);
        }
        for (u = [-BOSS_PITCH / 2, BOSS_PITCH / 2]) translate([u, 0, 0]) countersunk(4.4, BASE_T);
        translate([0, 0, BASE_T + BOSS_H - INSERT_M4_L + 0.01]) cylinder(d = INSERT_M4_D, h = INSERT_M4_L, $fn = 24);
    }
}

module flag_slice(k) {
    rotate([0, 0, 90 - ARC / 2 + k * ARC / 8])
        translate([R0, -0.5, BASE_T]) cube([R1 - R0, 1, LEAD + RISE * (1 - k / 8)]);
}

module flag_web(k) {
    rotate([0, 0, 90 - ARC / 2 + k * ARC / 8])
        translate([HUB_D / 2 - 1, -0.5, BASE_T]) cube([R0 - HUB_D / 2 + 2, 1, LEAD]);
}

module cam_handle(code) {
    assert(HANDLE_R <= 12 / 2 && TOP_R <= BOSS_H - 0.3, "cam handle rounding fits the lever and hub");
    difference() {
        union() {
            translate([0, 0, BASE_T]) soft_top(BOSS_H - 0.3) circle(d = HUB_D, $fn = 48);
            for (k = [0 : 7]) hull() { flag_slice(k); flag_slice(k + 1); }
            for (k = [0 : 7]) hull() { flag_web(k); flag_web(k + 1); }
            translate([0, 0, BASE_T]) soft_top(10) soften_plan(HANDLE_R) union() {
                translate([-64, -6]) square([58, 12]);
                translate([-64, 0]) circle(d = 16, $fn = 32);
            }
        }
        translate([0, 0, BASE_T - 0.01]) cylinder(d = BOSS_D + 0.4, h = BOSS_H + 0.02, $fn = 48);
    }
}

module cam_keeper(code) {
    kv = keeper_v();
    sw = sash_face_w();
    assert(EDGE_R <= 10 / 2, "keeper rounding fits the post");
    difference() {
        union() {
            translate([0, 0, sw]) linear_extrude(3) soften_plan(EDGE_R) translate([-KEEPER_HALF, kv - 6]) square([2 * KEEPER_HALF, 22]);
            translate([0, 0, sw]) linear_extrude(lip_w() + LIP_T - sw) soften_plan(EDGE_R) translate([-8, kv + 5]) square([16, 10]);
            translate([-LIP_HALF, R0 - 2, lip_w()]) cube([2 * LIP_HALF, kv + 15 - (R0 - 2), LIP_T]);
        }
        for (u = [-BOSS_PITCH / 2, BOSS_PITCH / 2]) translate([u, kv, sw]) countersunk(4.4, 3);
    }
}
