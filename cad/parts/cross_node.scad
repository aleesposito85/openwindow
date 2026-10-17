// cad/parts/cross_node.scad
include <../generated/dims.scad>
use <../profile.scad>
use <../lib/segment.scad>
use <../lib/emboss.scad>
use <../lib/mullion.scad>
use <jamb_node.scad>
use <transom_shoe.scad>

EPS = 0.01;

function cross_faces() = [TRANSOM_W / 2 - TRANSOM_HALF_BODY, TRANSOM_W / 2 + TRANSOM_HALF_BODY];

function cross_sharp() = node_sharp([cross_faces()[0], 0, cross_faces()[1], DEPTH], ["transom"]);

function cross_mag_cuts() =
    [for (r = mag_rects("mullion_sash")) [TRANSOM_MAG_X, DEPTH - MAG_D, cross_faces()[1] + EPS, DEPTH + EPS, r[0], r[2]]];

function cross_locks() =
    [for (q = mlock_uv()) each [[cross_faces()[0] - q[0], q[1]], [cross_faces()[1] + q[0], q[1]]]];

module cross_node(code, core) {
    c = MULLION_W / 2;
    k = mullion_leg();
    d = mdove();
    f = cross_faces();
    difference() {
        linear_extrude(MULLION_W) soft_rect([f[0], 0, f[1], DEPTH], cross_sharp());
        bevel_ends(MULLION_W) difference() { soft_rect([f[0], 0, f[1], DEPTH], cross_sharp()); bead_key("transom"); rect_r(mag_rect("transom")); }
        translate([0, 0, -EPS]) linear_extrude(MULLION_W + 2 * EPS) { pocket_cut("transom", core); rect_r(mag_rect("transom")); }
        for (z = [-EPS, MULLION_W - k]) translate([0, 0, z]) linear_extrude(k + EPS) bead_key("transom");
        for (z = [-EPS, MULLION_W - CORD_D / 2]) translate([0, 0, z]) end_groove("transom", core);
        for (s = [[f[0], -1], [f[1], 1]]) translate([s[0], DEPTH + EPS, c]) rotate([90, 0, 0]) scale([s[1], 1, 1])
            linear_extrude(DEPTH - STOP_T + EPS) dove_slot2d(d[0], d[1]);
        for (q = cross_locks()) translate([q[0], 0, c + q[1]]) lock_hole();
        for (r = cross_mag_cuts()) box(r);
        tube_screw("transom", c, core = core);
        engrave(code, label_at("transom"), k / 2);
    }
}
