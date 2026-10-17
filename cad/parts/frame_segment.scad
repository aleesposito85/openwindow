// cad/parts/frame_segment.scad
use <../lib/segment.scad>

module frame_segment(profile, len, code, weep = false, bosses = false, boss_dz = 0, core) {
    segment(profile, len, code, weep, bosses, boss_dz, core);
}
