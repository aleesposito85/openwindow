// cad/deck/joint.scad: one segment joint pulled apart along its tube: segment, foam cord ring, two 1 mm shims, segment, tube screw
include <lib.scad>

name = "glazing";
L = 90;
e = 34;
z2 = L + 2 * e;

color(C_ALU) translate([0, 0, -30]) linear_extrude(z2 + L + 60) tube2d(name);
color(C_FRAME) segment(name, L, "JL");
color(C_SEAL) translate([0, 0, L + e * 0.55]) linear_extrude(4) cord_ring(name);
color(C_HI) translate([0, 0, L + e * 1.25]) {
    translate([12, -14, 0]) cube([12, 22, 1]);
    translate([12, DEPTH - 8, 0]) cube([12, 22, 1]);
}
color(C_FRAME) translate([0, 0, z2]) segment(name, L, "JL");
color("#3b3f43") translate([screw_x(name), DEPTH + 18, z2 + L / 2]) rotate([-90, 0, 0]) {
    cylinder(d = 4.2, h = 30, $fn = 24);
    translate([0, 0, 30]) cylinder(d1 = 8.6, d2 = 8.6, h = 1, $fn = 32);
    translate([0, 0, 27.8]) cylinder(d1 = 4.2, d2 = 8.6, h = 2.2, $fn = 32);
}
