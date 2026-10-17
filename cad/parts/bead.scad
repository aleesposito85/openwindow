// cad/parts/bead.scad
include <../generated/dims.scad>
use <../profile.scad>
use <../lib/emboss.scad>

module bead(glazing, len, code, pane_t) {
    difference() {
        linear_extrude(len) bead_profile(glazing, pane_t);
        engrave(code, [0, bead_label_y(glazing, pane_t)], len / 2, BEAD_LABEL, spin = 90);
    }
}
