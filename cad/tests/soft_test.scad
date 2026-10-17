// cad/tests/soft_test.scad
use <../profile.scad>
use <../parts/cross_node.scad>
use <../parts/cam_lock.scad>
use <../parts/screen_hinge.scad>
include <../generated/dims.scad>

NAMES = ["glazing", "sash_rebate", "sill", "transom", "sash", "screen", "mullion_glazing", "mullion_sash"];

function pt_gap(r, p) = rect_gap(r, [p[0], p[1], p[0], p[1]]);
function corner_gap(name, c, core) = min([for (k = cut_rects(name, core), a = soft_arc(c)) pt_gap(k, a)]);
function is_sharp(name, p) = len([for (s = sharp_corners(name)) if (norm(s - p) < 1e-6) 1]) > 0;

bad = [for (n = NAMES, core = [undef, "vslot"], c = convex_corners(n)) if (!is_sharp(n, c[0]) && corner_gap(n, c, core) < MIN_SKIN)
           [n, core, c[0], corner_gap(n, c, core)]];
assert(len(bad) == 0, str("rounded corners too close to a cut: ", bad));
for (n = NAMES) for (s = sharp_corners(n))
    assert(len([for (c = convex_corners(n)) if (norm(c[0] - s) < 1e-6) 1]) > 0, str(n, ": sharp corner ", s, " is not a convex corner"));
for (n = NAMES) for (r = base_rects(n))
    assert(min(r[2] - r[0], r[3] - r[1]) >= 2 * EDGE_R, str(n, ": feature ", r, " is thinner than 2 x EDGE_R"));
assert(STOP_T >= 2 * EDGE_R, "sill stop survives the rounding");
assert(cross_sharp() == [[cross_faces()[0], 0], [cross_faces()[1], DEPTH], [cross_faces()[0], DEPTH]],
       "TX stays sharp where the transom runs flat or keeps its corner sharp");
assert(node_sharp([0, 0, FRAME_BODY, DEPTH], ["sill"]) == [[FRAME_BODY, 0]], "SN stays sharp where the sill runs flat");
assert(node_sharp([0, 0, FRAME_BODY, DEPTH], ["sash_rebate"]) == [[FRAME_BODY, DEPTH]], "HN stays sharp where the head runs flat");
assert(node_sharp([0, 0, FRAME_BODY, DEPTH], ["glazing", "sash_rebate"]) == [], "JN rounds every corner either jamb rounds");
assert(len(bevel_fill("sash")) == 1 && bevel_fill("glazing") == [] && bevel_fill("transom") == [], "only the sash glazing kerf is too shallow to bevel");
for (n = ["glazing", "sill", "sash_rebate"]) for (s = sharp_corners(n))
    assert(s[0] > FRAME_BODY + 1e-6, str(n, ": sharp corner ", s, " lies on a frame node's body"));
for (g = ["igu", "acrylic", "twinwall"], pane = [undef, 12, 18]) {
    y0 = bead_y0(g, pane);
    top = bead_seat_y() + BEAD_T;
    corner = [[BEAD_W, top], [-1, 0], [0, -1]];
    cuts = concat([kerf_rect(GLASS_CLEAR + GASKET_IN, y0, 1)], is_undef(bead_chamber(g, pane)) ? [] : [bead_chamber(g, pane)]);
    gap = min([for (k = cuts, a = soft_arc(corner)) pt_gap(k, a)]);
    assert(gap >= MIN_SKIN, str(g, " bead ", pane, ": rounded edge ", gap, " from a cut"));
    assert(BEAD_W >= 2 * EDGE_R && top - y0 >= 2 * EDGE_R, str(g, " bead ", pane, ": too thin to round"));
}
assert(EDGE_R <= CHAMBER_WALL, "rounding keeps the chamber walls");
assert(abs(JOINT_BEVEL / BEVEL_STEP - round(JOINT_BEVEL / BEVEL_STEP)) < 1e-9, "joint bevel is whole layers");
assert(CORD_INSET - JOINT_BEVEL >= 0.6, "joint bevel leaves a lip outside the cord groove");
cam_base("T");
cam_handle("T");
cam_keeper("T");
screen_hinge("T");
screen_leaf("T");
echo("soft rules ok");
