// cad/lib/mullion.scad
include <../generated/dims.scad>
use <../parts/jamb_node.scad>

function mullion_leg() = MULLION_W / 2 - MULLION_HALF_BODY;

function mdove() = [MULLION_DOVE_D, MULLION_DOVE_D * DOVE_FLARE / DOVE_D];

function mlock_uv() = lock_uv(mdove()[0], mdove()[1], LOCK_U);
