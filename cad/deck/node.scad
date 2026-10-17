// cad/deck/node.scad: left jamb node JN between JL and JU, with the transom shoe TSL, a TE segment and the steel tube pulled into the room
include <lib.scad>

e = 110;
L = 110;

multmatrix(m_jamb(false, -L - GAP - 25)) color(C_ALU) linear_extrude(2 * L + TRANSOM_W + 2 * GAP + 50) tube2d("glazing");
multmatrix(m_jamb(false, -L - GAP)) color(C_FRAME) segment("glazing", L, "JL");
color(C_HI) jamb_node("JN");
multmatrix(m_jamb(false, TRANSOM_W + GAP)) color(C_FRAME) segment("sash_rebate", L, "JU");
translate([0, e, 0]) {
    color(C_TRANSOM) multmatrix([[0, 0, 1, FRAME_BODY], [0, 1, 0, 0], [-1, 0, 0, TRANSOM_W]]) transom_shoe("TSL", mirrored = true);
    multmatrix([[0, 0, 1, F], [0, 1, 0, 0], [1, 0, 0, 0]]) {
        color(C_TRANSOM) translate([0, 0, GAP]) segment("transom", 150, "TE", weep = true, bosses = true);
        color(C_STEEL) translate([0, 0, -(F - FRAME_BODY - SHOE_WALL - 1)]) linear_extrude(190) tube2d("transom");
    }
}
color("#3b3f43") for (q = lock_uv()) translate([FRAME_BODY + q[0], DEPTH + e + 70, TRANSOM_W / 2 + q[1]]) rotate([-90, 0, 0]) {
    cylinder(d = 4, h = 16, $fn = 20);
    translate([0, 0, -2.2]) cylinder(d1 = 8.6, d2 = 4, h = 2.2, $fn = 28);
}
