// cad/parts/acrylic_spacer.scad
include <../generated/dims.scad>
use <../profile.scad>
use <../lib/emboss.scad>

function spacer_t(gap) = is_undef(gap) ? GLASS_T - 2 * ACRYLIC_T : gap;

module spacer_channel(gap) { rect(3, 3, SPACER_W - 3, spacer_t(gap) - 3); }

module acrylic_spacer(len, code, gap) {
    difference() {
        linear_extrude(len) rect(0, 0, SPACER_W, spacer_t(gap));
        translate([0, 0, -0.01]) linear_extrude(len + 0.02) spacer_channel(gap);
        for (z = [10 : 10 : len - 5])
            translate([SPACER_W - 3.5, spacer_t(gap) / 2, z]) rotate([0, 90, 0]) cylinder(d = 2, h = 4, $fn = 12);
        engrave(code, [0, spacer_t(gap) / 2], len / 2, 3);
    }
}

module acrylic_spacer_corner(code, gap) {
    leg = 15;
    plug = [SPACER_W - 6 - 0.3, spacer_t(gap) - 6 - 0.3];
    linear_extrude(spacer_t(gap)) square([SPACER_W, SPACER_W]);
    translate([SPACER_W, 3.15, 3.15]) cube([leg, plug[0], plug[1]]);
    translate([3.15, SPACER_W, 3.15]) cube([plug[0], leg, plug[1]]);
}
