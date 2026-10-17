// cad/parts/mullion_shoe.scad
include <../generated/dims.scad>
use <../profile.scad>
use <../lib/segment.scad>
use <../lib/emboss.scad>
use <../lib/mullion.scad>
use <jamb_node.scad>
use <transom_shoe.scad>

EPS = 0.01;

function node_z(r, e) = [r[0] - e, r[2] - e];

function shoe_node_z(profile, head) =
    profile == "mullion_glazing" ? [node_z(glazing_kerf_rect("sill"), FRAME_BODY)]
  : let(n = head ? "sash_rebate" : "transom", e = sash_side_e(n))
    concat([for (r = seal_kerf_rects(n)) node_z(r, e)], head ? [node_z(mag_rect(n), e)] : []);

function shoe_features(profile, head) =
    let(k = kerf_rects(profile))
    profile == "mullion_glazing" ? [k]
  : concat([[k[0], k[2]], [k[1], k[3]]], head ? [mag_rects(profile)] : []);

function mshoe_turn(r, z) =
    r[0] > MULLION_W / 2 ? [r[0], r[1], MULLION_W + EPS, r[3], z[0], z[1]] : [-EPS, r[1], r[2], r[3], z[0], z[1]];

function mshoe_turns(profile, head = false) =
    let(z = shoe_node_z(profile, head), f = shoe_features(profile, head))
    [for (i = [0 : len(z) - 1]) for (r = f[i]) mshoe_turn(r, z[i])];

function mshoe_fin_stubs(profile) =
    profile != "mullion_sash" ? []
  : let(mh = MULLION_W / 2 + MULLION_HALF_BODY)
    [[mh + FIN_L - EPS, FIN_Y0, MULLION_W, FIN_Y1, 0, FIN_L], [0, FIN_Y0, MULLION_W - mh - FIN_L + EPS, FIN_Y1, 0, FIN_L]];

function mshoe_seam_groove(profile) =
    let(x0 = profile == "mullion_glazing" ? kerf_rects(profile)[0][2] + MIN_SKIN : mullion_leg() + MIN_SKIN)
    [x0, STOP_T / 2 - CORD_D / 2, MULLION_W - x0, STOP_T / 2 + CORD_D / 2, -EPS, CORD_D / 2];

function mshoe_screw_z() = SHOE_WALL + (mullion_leg() - SHOE_WALL) / 2;

module mullion_shoe(profile, code, head = false, core) {
    assert(is_mullion(profile), str(code, ": ", profile, " is not a mullion profile"));
    assert(!head || profile == "mullion_sash", str(code, ": only the upper mullion meets the head"));
    L = mullion_leg();
    c = MULLION_W / 2;
    d = mdove();
    difference() {
        union() {
            linear_extrude(L) profile(profile, core = core);
            linear_extrude(SHOE_WALL) profile_solid(profile, false, core);
            for (b = mshoe_fin_stubs(profile)) fin_stub(b);
            multmatrix([[0, 1, 0, c], [0, 0, 1, STOP_T + DOVE_CLEAR], [1, 0, 0, 0]])
                linear_extrude(DEPTH - STOP_T - DOVE_CLEAR) dove_tongue2d(d[0], d[1]);
        }
        for (t = mshoe_turns(profile, head)) box(t);
        translate([0, 0, L - CORD_D / 2]) end_groove(profile, core);
        bevel_ends(L, bottom = false) bevel_outline(profile, core);
        for (q = mlock_uv()) translate([c + q[1], 0, q[0]]) lock_hole();
        box(mshoe_seam_groove(profile));
        tube_screw(profile, mshoe_screw_z(), core = core);
        engrave(code, label_at(profile), L / 2);
    }
}
