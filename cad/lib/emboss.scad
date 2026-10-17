// cad/lib/emboss.scad
include <../generated/dims.scad>

module engrave(code, at, z, size = LABEL_SIZE, facing = -1, spin = 0) {
    if (facing < 0)
        translate([at[0] + LABEL_DEPTH, at[1], z]) rotate([90, 0, -90])
            linear_extrude(LABEL_DEPTH + 0.01) rotate(spin) text(code, size = size, halign = "center", valign = "center");
    else
        translate([at[0] - LABEL_DEPTH, at[1], z]) rotate([90, 0, 90])
            linear_extrude(LABEL_DEPTH + 0.01) rotate(-spin) text(code, size = size, halign = "center", valign = "center");
}
