// cad/tests/fit_view.scad
include <../generated/dims.scad>
use <../parts/jamb_node.scad>
use <../parts/transom_shoe.scad>
use <../parts/corner_block.scad>

jamb_node("JN");
color("Orange") multmatrix([[0, 0, 1, FRAME_BODY], [0, 1, 0, 0], [-1, 0, 0, TRANSOM_W]]) transom_shoe("TSL", mirrored = true);
translate([150, 0, 0]) corner_block("sill", "glazing", "CSL");
translate([300, 0, 0]) corner_block("sash", "sash", "CS");
