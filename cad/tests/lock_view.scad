// cad/tests/lock_view.scad
include <../generated/dims.scad>
use <../parts/cam_lock.scad>
use <../profile.scad>

sash_v = TRANSOM_W / 2 + TRANSOM_HALF_BODY + SASH_GAP - CAM_BOSS_X;
color("SteelBlue") multmatrix([[0, 0, 1, -60], [1, 0, 0, -CAM_BOSS_X], [0, 1, 0, -DEPTH]]) linear_extrude(120) profile("transom");
color("LightSteelBlue") multmatrix([[0, 0, 1, -60], [1, 0, 0, sash_v], [0, 1, 0, -DEPTH]]) linear_extrude(120) profile("sash");
cam_base("CMB");
color("Orange") cam_handle("CMH");
color("Red") cam_keeper("KP");
