// cad/parts/transom_shoe.scad
include <../generated/dims.scad>
use <../profile.scad>
use <../lib/segment.scad>
use <../lib/emboss.scad>
use <jamb_node.scad>

EPS = 0.01;

function shoe_fin_stub() = [TRANSOM_W / 2 + TRANSOM_HALF_BODY + FIN_L - EPS, FIN_Y0, TRANSOM_W, FIN_Y1, 0, FIN_L];

function shoe_turn(j, r, up, seam = false) =
    [[up ? r[0] : -EPS, r[1], up ? TRANSOM_W + EPS : r[2], r[3], seam ? -EPS : j[0] - FRAME_BODY, j[2] - FRAME_BODY], j, r, seam];

function shoe_turns() = [
    shoe_turn(seal_kerf_rects("sash_rebate")[0], seal_kerf_rects("transom")[0], true),
    shoe_turn(seal_kerf_rects("sash_rebate")[1], seal_kerf_rects("transom")[1], true),
    shoe_turn(mag_rect("sash_rebate"), mag_rect("transom"), true, true),
    shoe_turn(glazing_kerf_rect("glazing"), glazing_kerf_rect("transom"), false),
];

function shoe_seam_groove() =
    [glazing_kerf_rect("transom")[2] + MIN_SKIN, STOP_T / 2 - CORD_D / 2,
     TRANSOM_W / 2 + TRANSOM_HALF_BODY - MIN_SKIN, STOP_T / 2 + CORD_D / 2, -EPS, CORD_D / 2];

module box(b) { translate([b[0], b[1], b[4]]) cube([b[2] - b[0], b[3] - b[1], b[5] - b[4]]); }

module transom_shoe(code, mirrored = false, core) {
    L = FRAME_W - FRAME_BODY;
    c = TRANSOM_W / 2;
    at = label_at("transom");
    difference() {
        translate([mirrored ? TRANSOM_W : 0, 0, 0]) mirror([mirrored ? 1 : 0, 0, 0]) difference() {
            union() {
                linear_extrude(L) profile("transom", core = core);
                linear_extrude(SHOE_WALL) profile_solid("transom", false, core);
                fin_stub(shoe_fin_stub());
                multmatrix([[0, 1, 0, c], [0, 0, 1, STOP_T + DOVE_CLEAR], [1, 0, 0, 0]])
                    linear_extrude(DEPTH - STOP_T - DOVE_CLEAR) dove_tongue2d();
            }
            for (t = shoe_turns()) box(t[0]);
            translate([0, 0, L - CORD_D / 2]) end_groove("transom", core);
            bevel_ends(L, bottom = false) bevel_outline("transom", core);
            for (q = lock_uv()) translate([c + q[1], 0, q[0]]) lock_hole();
            box(shoe_seam_groove());
            tube_screw("transom", SHOE_WALL + (L - SHOE_WALL) / 2, DEPTH - MAG_D, core);
        }
        engrave(code, [mirrored ? TRANSOM_W - at[0] : at[0], at[1]], L / 2, facing = mirrored ? 1 : -1);
    }
}
