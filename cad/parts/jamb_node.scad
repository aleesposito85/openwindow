// cad/parts/jamb_node.scad
include <../generated/dims.scad>
use <../profile.scad>
use <../lib/segment.scad>
use <../lib/emboss.scad>

EPS = 0.01;

function lock_uv(d = DOVE_D, f = DOVE_FLARE, u = LOCK_U) = [for (s = [-1, 1]) [-u, s * (DOVE_W / 2 + f * u / d)]];

function lock_top() = DEPTH - MAG_D;

module lock_hole() {
    s = DEPTH - lock_top();
    translate([0, DEPTH + EPS, 0]) rotate([90, 0, 0]) {
        cylinder(d = LOCK_D, h = LOCK_L + EPS, $fn = 16);
        translate([0, 0, s]) cylinder(d1 = CSK_D, d2 = LOCK_D, h = (CSK_D - LOCK_D) / 2, $fn = 32);
        translate([0, 0, -1]) cylinder(d = CSK_D, h = s + 1 + EPS, $fn = 32);
    }
}

function node_key_len() = TRANSOM_W / 2 - TRANSOM_HALF_BODY;

function dove_slot(d = DOVE_D, f = DOVE_FLARE) =
    let(m = DOVE_W / 2, b = m + f)
    [[EPS, -m], [EPS, m], [0, m], [-d, b], [-d, -b], [0, -m]];

function dove_head(c, d = DOVE_D, f = DOVE_FLARE) =
    let(m = DOVE_W / 2, b = m + f, l = norm([d, f]), mh = m - c * (l - f) / d, bh = b - c * (l + f) / d)
    [[-c, -mh], [-c, mh], [-d + c, bh], [-d + c, -bh]];

function dove_root_w() = DOVE_W - 2 * DOVE_CLEAR;

function dove_root_d() = SHOE_WALL;

module dove_slot2d(d = DOVE_D, f = DOVE_FLARE) { polygon(dove_slot(d, f)); }

module dove_tongue2d(d = DOVE_D, f = DOVE_FLARE) {
    polygon(dove_head(DOVE_CLEAR, d, f));
    translate([-DOVE_CLEAR - EPS, -dove_root_w() / 2]) square([dove_root_d() + DOVE_CLEAR + EPS, dove_root_w()]);
}

module jamb_node(code, core) {
    c = TRANSOM_W / 2;
    k = node_key_len();
    b = [0, 0, FRAME_BODY, DEPTH];
    s = node_sharp(b, ["glazing", "sash_rebate"]);
    difference() {
        linear_extrude(TRANSOM_W) soft_rect(b, s);
        bevel_ends(TRANSOM_W) difference() { soft_rect(b, s); bead_key("glazing"); }
        translate([0, 0, -EPS]) linear_extrude(TRANSOM_W + 2 * EPS) pocket_cut("glazing", core);
        for (z = [-EPS, TRANSOM_W - k]) translate([0, 0, z]) linear_extrude(k + EPS) bead_key("glazing");
        for (z = [-EPS, TRANSOM_W - CORD_D / 2]) translate([0, 0, z]) intersection() { end_groove("glazing", core); linear_extrude(CORD_D) offset(delta = -CORD_INSET) soft_rect(b, s); }
        translate([FRAME_BODY, DEPTH + EPS, c]) rotate([90, 0, 0]) linear_extrude(DEPTH - STOP_T + EPS) dove_slot2d();
        for (q = lock_uv()) translate([FRAME_BODY + q[0], 0, c + q[1]]) lock_hole();
        tube_screw("glazing", c, core = core);
        for (dz = [-NODE_FIX_OFFSET, NODE_FIX_OFFSET]) fixing_hole("glazing", c + dz);
        engrave(code, label_at("glazing"), c);
    }
}
