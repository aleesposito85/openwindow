// cad/tests/vslot_sheet.scad
use <../profile.scad>
use <../lib/segment.scad>
include <../generated/dims.scad>

V = "vslot";

module slot2d() {
    m = VSLOT_MOUTH / 2;
    n = VSLOT_NECK / 2;
    v = m - n;
    polygon([[-m, 0.01], [m, 0.01], [n, -v], [n, -VSLOT_LIP], [5.5, -VSLOT_LIP], [5.5, -VSLOT_FLOOR + 2],
             [3, -VSLOT_FLOOR], [-3, -VSLOT_FLOOR], [-5.5, -VSLOT_FLOOR + 2], [-5.5, -VSLOT_LIP], [-n, -VSLOT_LIP], [-n, -v]]);
}

module vslot2020(c) {
    translate(c) difference() {
        square(20, center = true);
        for (a = [0, 90, 180, 270]) rotate(a) translate([0, 10]) slot2d();
        circle(d = 4.2, $fn = 24);
    }
}

function centre(r) = [(r[0] + r[2]) / 2, (r[1] + r[3]) / 2];

sel = 0;

module edges(a, b, w) {
    for (y = [a - 2.1, a + 2.1]) if (w) translate([b[0], y - 0.12]) square([b[1] - b[0], 0.24]);
}

module band_h(y, x0, x1) { for (e = [y - TUBE_SCREW_D / 2, y + TUBE_SCREW_D / 2]) translate([x0, e - 0.12]) square([x1 - x0, 0.24]); }

module band_v(x, y0, y1, d) { for (e = [x - d / 2, x + d / 2]) translate([e - 0.12, y0]) square([0.24, y1 - y0]); }

module show(name, tubes) {
    difference() {
        union() {
            profile(name, core = V);
            for (c = tubes) vslot2020(c);
        }
        children();
    }
}

if (sel == 0) show("sash_rebate", [centre(pocket_rect("sash_rebate", V))]) {
    for (y = [stay_c_min(), stay_c_max()]) band_h(y, 0, FRAME_BODY + 2);
    band_v(screw_x("sash_rebate", V), pocket_rect("sash_rebate", V)[3] - 6, DEPTH + 1, VSLOT_SCREW_D);
}
if (sel == 1) show("sash", [centre(pocket_rect("sash"))]) {
    for (y = [stay_c_min(), stay_c_max()]) band_h(y, -FLANGE_L - 1, 30);
    band_v(screw_x("sash", V), pocket_rect("sash")[3] - 6, LIP_Y1 + 1, VSLOT_SCREW_D);
}
r = pocket_rect("transom");
if (sel == 2) show("transom", [for (y = [r[1] + TUBE_CLEAR + 10, r[3] - TUBE_CLEAR - 10]) [(r[0] + r[2]) / 2, y]])
    band_v(screw_x("transom", V), r[3] - 8, DEPTH + 1, TUBE_SCREW_D);
m = pocket_rect("mullion_sash");
if (sel == 3) show("mullion_sash", [for (y = [m[1] + TUBE_CLEAR + 10, m[3] - TUBE_CLEAR - 10]) [(m[0] + m[2]) / 2, y]]) {
    for (y = [stay_c_min(), stay_c_max()]) band_h(y, -1, MULLION_W + 1);
    band_v(screw_x("mullion_sash", V), m[3] - 6, DEPTH + 1, VSLOT_SCREW_D);
}
