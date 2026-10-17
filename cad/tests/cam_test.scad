// cad/tests/cam_test.scad
include <../generated/dims.scad>
use <../parts/cam_lock.scad>

assert(flag_half_run() - keeper_lip_half_run() >= CAM_ALIGN_TOL,
       str("keeper lip (+/-", keeper_lip_half_run(), ") stays over the cam flag (+/-", flag_half_run(), ") within the alignment tolerance"));
assert(keeper_half_run() <= BOSS_PITCH / 2 + INSERT_M4_D / 2 + MIN_SKIN + END_CAP, "keeper plate stays on the SBE at the largest boss offset");
echo("cam rules ok");
