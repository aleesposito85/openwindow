// cad/parts/weep_cap.scad
include <../generated/dims.scad>
use <../lib/emboss.scad>

module weep_cap(code) {
    w = WEEP_W + 10;
    t = WEEP_CAP_T;
    sx = (WEEP_CAP_H - WEEP_H) / 2;
    difference() {
        cube([WEEP_CAP_H, 4, w]);
        translate([-1, -0.01, t]) cube([WEEP_CAP_H - t + 1, 4 - t + 0.01, w - 2 * t]);
    }
    for (z = [5 + 0.2, w - 5 - 0.2 - 1.2])
        translate([sx + 0.2, -3, z]) cube([WEEP_H - 0.4, 3 + 4 - t + 0.01, 1.2]);
}
