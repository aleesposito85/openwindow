// cad/tests/hinge_test.scad
include <../generated/dims.scad>
use <../parts/screen_hinge.scad>

PAN_HEAD_D = 8;
v = hinge_hole_v();
assert(hinge_wall_v() - (v + PAN_HEAD_D / 2) >= MIN_SKIN, str("HG screw head ", v + PAN_HEAD_D / 2, " runs into the leaf wall at ", hinge_wall_v()));
assert(v - PAN_HEAD_D / 2 >= hinge_plate_v(), "HG screw head sits on the leaf plate");
assert(INSERT_M4_L - (10 - hinge_leaf_t()) >= 1, "M4 x 10 through the HG leaf stops short of the insert hole floor");
echo("hinge rules ok");
