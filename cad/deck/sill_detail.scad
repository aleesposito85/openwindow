// cad/deck/sill_detail.scad: an SW sill segment from outside with its weep cap and sill-nose pieces pulled off
include <lib.scad>

L = 180;
e = 40;
s = tan(SILL_SLOPE_DEG);
f = FRAME_BODY - (bead_seat_y() - STOP_T) * s;
sx = (WEEP_CAP_H - WEEP_H) / 2;
M0 = [[0, 0, 1, 0], [0, 1, 0, 0], [1, 0, 0, 0]];

multmatrix(M0) {
    color(C_FRAME) segment("sill", L, "SW", weep = true);
    color(C_ALU) translate([0, 0, -20]) linear_extrude(L + 40) tube2d("sill");
    color(C_HI) translate([f - 1 - sx, -e, L / 2 - (WEEP_W + 10) / 2]) mirror([0, 1, 0]) weep_cap("WC");
    color("#d9692b") translate([-e * 0.6, -e * 1.4, 0]) {
        translate([0, 0, -60]) sill_nose(L / 2 + 59, "NS");
        translate([0, 0, L / 2 + GAP]) sill_nose(L / 2 + 59, "NS");
    }
}
