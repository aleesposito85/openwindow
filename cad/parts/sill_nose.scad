// cad/parts/sill_nose.scad
include <../generated/dims.scad>
use <../profile.scad>
use <../lib/emboss.scad>

module nose_profile() {
    s = tan(SILL_SLOPE_DEG);
    p = NOSE_PROJECTION;
    top = NOSE_KEY_X + NOSE_KEY_W + 6;
    xt = function(y) top + y * s;
    difference() {
        union() {
            polygon([[top, 0], [NOSE_KEY_X - 2, 0], [NOSE_KEY_X - 2, -3], [xt(-3) - 3, -3],
                     [xt(-p + 3) - 3, -p + 3], [-4, -p + 3], [-4, -p], [xt(-p), -p]]);
            translate([NOSE_KEY_X, 0]) key_tongue(NOSE_KEY_D, NOSE_KEY_W);
        }
        rect(-2, -p + 2.4, 0, -p + 3 + 0.01);
    }
}

module sill_nose(len, code) {
    difference() {
        linear_extrude(len) nose_profile();
        engrave(code, [NOSE_KEY_X - 2, -1.5], len / 2, 2);
    }
}
