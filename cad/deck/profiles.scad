// cad/deck/profiles.scad: one cross-section per render (k = 0..7), outside to the left, centred for a fixed ortho camera
include <lib.scad>

k = 0;
NAMES = ["glazing", "sash_rebate", "sill", "transom", "sash", "screen", "igu", "twinwall"];
COLS = [C_FRAME, C_FRAME, C_FRAME, C_TRANSOM, C_SASH, C_SCREEN, C_BEAD, C_BEAD];
name = NAMES[k];

function x_range(n) = n == "igu" || n == "twinwall" ? [-KEY_D, BEAD_W] : n == "sill" ? [-NOSE_PROJECTION, FRAME_W] : [profile_min(n), profile_width(n)];
function y_range(n) = n == "igu" || n == "twinwall" ? [bead_y0(n), bead_seat_y() + BEAD_T] : n == "sash" ? [SASH_Y0, LIP_Y1] : n == "screen" ? [0, SCREEN_DEPTH] : [0, DEPTH];

module up() multmatrix([[0, 1, 0, 0], [1, 0, 0, 0], [0, 0, 1, 0]]) children();
module lay(col, z = 0) color(col) translate([0, 0, z]) linear_extrude(1) children();

module dressing(n) {
    if (n == "sash_rebate" || n == "transom") {
        kr = seal_kerf_rects(n);
        lay(C_SEAL, 0.02) up() {
            rect_r(kr[0]);
            translate([(kr[0][0] + kr[0][2]) / 2, FIN_Y0 - 1.5]) circle(r = 1.6, $fn = 24);
            rect_r(kr[1]);
            translate([(kr[1][0] + kr[1][2]) / 2, ISTOP_Y0 - 1.0]) circle(r = 1.2, $fn = 24);
        }
        lay(C_MAG, 0.02) up() rect_r(mag_rect(n));
    }
    gk = glazing_kerf_rect(n);
    if (!is_undef(gk)) lay(C_SEAL, 0.02) up() rect_r(gk);
    if (n == "screen") {
        lay(C_MAG, 0.02) up() rect(SCREEN_OVERLAP + 2, 0, SCREEN_OVERLAP + 2 + MAG_W, MAG_D);
        lay(C_SEAL, 0.02) up() rect(SCREEN_W - 8, SCREEN_DEPTH - SPLINE_D, SCREEN_W - 8 + SPLINE_W, SCREEN_DEPTH);
    }
}

xr = x_range(name);
yr = y_range(name);
translate([-(yr[0] + yr[1]) / 2, -(xr[0] + xr[1]) / 2, 0]) {
    if (k >= 6) {
        lay(C_BEAD) up() bead_profile(name);
        lay(C_SEAL, 0.02) up() rect(GLASS_CLEAR + GASKET_IN - 1.5, bead_y0(name), GLASS_CLEAR + GASKET_IN + 1.5, bead_y0(name) + KERF_D);
    } else {
        lay(COLS[k]) up() profile(name);
        lay(name == "transom" ? C_STEEL : C_ALU) up() tube2d(name);
        dressing(name);
        if (name == "sill") lay(C_FRAME) up() nose_profile();
    }
}
