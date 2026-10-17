// cad/deck/corner.scad: sill corner CSL with its two tubes and the first SW and JL segments pulled back
include <lib.scad>

e = 46;
L = 130;

color(C_HI) corner_block("sill", "glazing", "CSL");
multmatrix(M_SILL) {
    color(C_ALU) translate([0, 0, -SOCK + e * 0.5]) linear_extrude(L + SOCK + 30) tube2d("sill");
    color(C_FRAME) translate([0, 0, GAP + e]) segment("sill", L, "SW", weep = true);
}
multmatrix(m_jamb(false, F)) {
    color(C_ALU) translate([0, 0, -SOCK + e * 0.5]) linear_extrude(L + SOCK + 30) tube2d("glazing");
    color(C_FRAME) translate([0, 0, GAP + e]) segment("glazing", L, "JL");
}
