// cad/parts/frame_node.scad
include <../generated/dims.scad>
use <../profile.scad>
use <../lib/segment.scad>
use <../lib/emboss.scad>
use <../lib/mullion.scad>
use <jamb_node.scad>

EPS = 0.01;

function frame_node_fix(name) = name == "sill" ? "glazing" : name;

module frame_node(name, code, core) {
    assert(name == "sill" || name == "sash_rebate", str(code, ": frame nodes sit in the sill or the head, not ", name));
    c = MULLION_W / 2;
    k = mullion_leg();
    d = mdove();
    b = [0, 0, FRAME_BODY, DEPTH];
    s = node_sharp(b, [name]);
    difference() {
        linear_extrude(MULLION_W) soft_rect(b, s);
        bevel_ends(MULLION_W) difference() { soft_rect(b, s); bead_key(name); if (name == "sill") for (r = nose_key_rects()) rect_r(r); }
        translate([0, 0, -EPS]) linear_extrude(MULLION_W + 2 * EPS) {
            pocket_cut(name, core);
            if (name == "sill") for (r = nose_key_rects()) rect_r(r);
        }
        for (z = [-EPS, MULLION_W - k]) translate([0, 0, z]) linear_extrude(k + EPS) bead_key(name);
        for (z = [-EPS, MULLION_W - CORD_D / 2]) translate([0, 0, z]) end_groove(name, core);
        translate([FRAME_BODY, DEPTH + EPS, c]) rotate([90, 0, 0]) linear_extrude(DEPTH - STOP_T + EPS) dove_slot2d(d[0], d[1]);
        for (q = mlock_uv()) translate([FRAME_BODY + q[0], 0, c + q[1]]) lock_hole();
        tube_screw(name, c, core = core);
        for (dz = [-NODE_FIX_OFFSET, NODE_FIX_OFFSET]) fixing_hole(frame_node_fix(name), c + dz);
        engrave(code, label_at(name), c);
    }
}
