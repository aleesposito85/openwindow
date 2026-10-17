// cad/deck/section.scad: section drawings of the generated window by zone (0 head, 1 transom, 2 sill, 3 upper jamb in plan), centred for a fixed ortho camera
include <lib.scad>

zone = 1;
g = GLAZING;
GT = g == "twinwall" ? TWINWALL_T : GLASS_T;
TL = TRANSOM_W / 2 - TRANSOM_HALF_BODY;
STAY_C = (stay_c_min() + stay_c_max()) / 2;
SASH_TOP = SZ0 + SASH[1];
CU = 35;
ZONE_CV = [H - 68, TB + 48, 50, 63];
C_WATER = "#3d9be0";

module up(b, du = 0) multmatrix([[0, 1, 0, du], [1, 0, 0, b], [0, 0, 1, 0]]) children();
module dn(b, du = 0) multmatrix([[0, 1, 0, du], [-1, 0, 0, b], [0, 0, 1, 0]]) children();
module at(dir, b, du = 0) { if (dir > 0) up(b, du) children(); else dn(b, du) children(); }
module lay(col, z = 0) color(col) translate([0, 0, z]) linear_extrude(1) children();

module member(name, dir, b, col) {
    lay(col) at(dir, b) profile(name);
    lay(name == "transom" ? C_STEEL : C_ALU) at(dir, b) tube2d(name);
}

module seals(name, dir, b) {
    k = seal_kerf_rects(name);
    lay(C_SEAL, 0.02) at(dir, b) {
        rect_r(k[0]);
        translate([(k[0][0] + k[0][2]) / 2, FIN_Y0 - 1.5]) circle(r = 1.6, $fn = 24);
        rect_r(k[1]);
        translate([(k[1][0] + k[1][2]) / 2, ISTOP_Y0 - 1.0]) circle(r = 1.2, $fn = 24);
    }
}

module magnet(name, dir, b) { lay(C_MAG, 0.02) at(dir, b) rect_r(mag_rect(name)); }

module glaze_out(name, dir, b) {
    k = glazing_kerf_rect(name);
    cx = (k[0] + k[2]) / 2;
    lay(C_SEAL, 0.02) at(dir, b) { rect_r(k); rect(cx - 2, STOP_T, cx + 2, GLASS_Y0); }
}

module bead_set(dir, b, e, flip) {
    kx = GLASS_CLEAR + GASKET_IN;
    lay(C_BEAD) at(dir, b) translate([e, 0]) mirror([flip ? 1 : 0, 0]) bead_profile(g);
    lay(C_SEAL, 0.02) at(dir, b) translate([e, 0]) mirror([flip ? 1 : 0, 0]) {
        rect(kx - 1.5, bead_y0(g), kx + 1.5, bead_y0(g) + KERF_D);
        rect(kx - 2, GLASS_Y0 + GT, kx + 2, bead_y0(g));
    }
}

module glass(v0, v1) {
    if (g == "igu") {
        lay(C_GLASS_SOLID) { rect(GLASS_Y0, v0, GLASS_Y0 + 4, v1); rect(GLASS_Y0 + 20, v0, GLASS_Y0 + 24, v1); }
        for (e = [[v0, 1], [v1, -1]]) {
            lay("#8b949b") rect(GLASS_Y0 + 4, min(e[0] + e[1] * 3, e[0] + e[1] * 10), GLASS_Y0 + 20, max(e[0] + e[1] * 3, e[0] + e[1] * 10));
            lay("#3c4247") rect(GLASS_Y0 + 4, min(e[0], e[0] + e[1] * 3), GLASS_Y0 + 20, max(e[0], e[0] + e[1] * 3));
        }
    } else lay(C_GLASS_SOLID) rect(GLASS_Y0, v0, GLASS_Y0 + GT, v1);
}

module screen_rail(dir, b) {
    lay(C_SCREEN) at(dir, b, DEPTH) profile("screen");
    lay(C_ALU) at(dir, b, DEPTH) tube2d("screen");
    lay(C_MAG, 0.02) at(dir, b, DEPTH) rect(SCREEN_OVERLAP + 2, 0, SCREEN_OVERLAP + 2 + MAG_W, MAG_D);
    lay(C_SEAL, 0.02) at(dir, b, DEPTH) {
        rect(SCREEN_W - 8, SCREEN_DEPTH - SPLINE_D, SCREEN_W - 8 + SPLINE_W, SCREEN_DEPTH);
        rect(SCREEN_W - 6.3, SCREEN_DEPTH - 0.7, SCREEN_W + 200, SCREEN_DEPTH - 0.1);
    }
}

module weep(name, dir, b) { lay(C_WATER, 0.03) at(dir, b) rect_r(weep_rect(name)); }

module gw_block() {
    s = tan(SILL_SLOPE_DEG);
    fx = function(y) FRAME_BODY - (bead_seat_y() - y) * s;
    y0 = GLASS_Y0;
    y1 = GLASS_Y0 + GT;
    lay(C_BLOCK) up(0) polygon([[fx(y0), y0], [fx(y1), y1], [GLASS_EDGE, y1], [GLASS_EDGE, y0]]);
}

module gf_block(dir, b) { lay(C_BLOCK) at(dir, b) rect(SASH_BODY, GLASS_Y0, SASH_BODY + GLASS_CLEAR, GLASS_Y0 + GT); }

module zone0() {
    member("sash_rebate", -1, H, C_FRAME);
    seals("sash_rebate", -1, H);
    magnet("sash_rebate", -1, H);
    member("sash", -1, SASH_TOP, C_SASH);
    glaze_out("sash", -1, SASH_TOP);
    bead_set(-1, SASH_TOP, SASH_BODY, false);
    glass(SZ0 + SASH_GLASS, SZ0 + SASH_GLASS + SASH_GLASS_DIMS[1]);
    screen_rail(-1, NZ0 + SCREEN[1]);
}

module zone1() {
    member("transom", 1, TB, C_TRANSOM);
    seals("transom", 1, TB);
    magnet("transom", 1, TB);
    glaze_out("transom", 1, TB);
    bead_set(1, TB, TL, true);
    weep("transom", 1, TB);
    glass(GLASS_EDGE, GLASS_EDGE + FIXED_GLASS[1]);
    member("sash", 1, SZ0, C_SASH);
    glaze_out("sash", 1, SZ0);
    bead_set(1, SZ0, SASH_BODY, false);
    gf_block(1, SZ0);
    weep("sash", 1, SZ0);
    glass(SZ0 + SASH_GLASS, SZ0 + SASH_GLASS + SASH_GLASS_DIMS[1]);
    screen_rail(1, NZ0);
}

module zone2() {
    member("sill", 1, 0, C_FRAME);
    glaze_out("sill", 1, 0);
    bead_set(1, 0, FRAME_BODY, false);
    lay(C_FRAME) up(0) nose_profile();
    gw_block();
    weep("sill", 1, 0);
    glass(GLASS_EDGE, GLASS_EDGE + FIXED_GLASS[1]);
}

module zone3() {
    member("sash_rebate", 1, 0, C_FRAME);
    seals("sash_rebate", 1, 0);
    magnet("sash_rebate", 1, 0);
    member("sash", 1, SX0, C_SASH);
    glaze_out("sash", 1, SX0);
    bead_set(1, SX0, SASH_BODY, false);
    glass(SX0 + SASH_GLASS, SX0 + SASH_GLASS + SASH_GLASS_DIMS[0]);
    screen_rail(1, NX0);
    lay(C_HI, 0.04) rect(STAY_C - STAY_W / 2, FRAME_BODY, STAY_C + STAY_W / 2, FRAME_BODY + SASH_GAP);
    lay("#3a3a3a", 0.05) {
        rect(STAY_C - 2.1, FRAME_BODY - 22, STAY_C + 2.1, FRAME_BODY + 3);
        rect(STAY_C - 2.1, SX0 - 3, STAY_C + 2.1, SX0 + 13);
    }
}

module drawing() {
    if (zone == 0) zone0();
    else if (zone == 1) zone1();
    else if (zone == 2) zone2();
    else zone3();
}

translate([-CU, -ZONE_CV[zone], 0]) intersection() {
    drawing();
    translate([-200, ZONE_CV[zone] - 80, -5]) cube([500, 160, 20]);
}
