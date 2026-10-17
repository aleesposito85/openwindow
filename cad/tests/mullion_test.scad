// cad/tests/mullion_test.scad
include <../generated/dims.scad>
use <../profile.scad>
use <../lib/segment.scad>

TRACK_SCREW_L = 16;
ml = MULLION_W / 2 - MULLION_HALF_BODY;
mh = MULLION_W / 2 + MULLION_HALF_BODY;

assert(ml == FRAME_W - FRAME_BODY, "the mullion leg zone matches the frame's, so one shoe fits the sill and the transom");
assert(MULLION_W / 2 - TRANSOM_GLASS == FRAME_W - GLASS_EDGE, "end and inner bays get the same pane bite");
assert(TRANSOM_GLASS - MULLION_HALF_BODY == GLASS_CLEAR, "mullion glass clearance");
assert(BEAD_W <= ml, "bead fits the mullion rebate and ends inside the node keyway");
assert(MULLION_W - (mh + 2 + MAG_W) >= MIN_SKIN, "mullion magnet channel keeps a lip at the profile edge");

for (n = ["mullion_glazing", "mullion_sash"]) {
    o = pocket_origin(n);
    p = pocket(n);
    pr = pocket_rect(n);
    assert(o[0] - ml >= MIN_SHELL && mh - (o[0] + p[0]) >= MIN_SHELL && o[1] >= MIN_SHELL && DEPTH - (o[1] + p[1]) >= MIN_SHELL,
           str(n, ": shell round the steel tube"));
    assert(len(chamber_rects(n)) == 0, str(n, ": solid body, like the transom"));
    assert(core_box(n) == [ml, 0, mh, DEPTH] && has_cord(n), str(n, ": cord ring round the body"));
    for (r = concat(bead_key_rects(n), kerf_rects(n), mag_rects(n)))
        assert(rect_gap(r, pr) >= MIN_SKIN, str(n, ": feature ", r, " to tube pocket ", rect_gap(r, pr)));
    for (r = kerf_rects(n)) for (m = mag_rects(n))
        assert(rect_gap(r, m) >= MIN_SKIN, str(n, ": kerf ", r, " to magnet channel ", m));
    sx = screw_x(n);
    assert(sx - TUBE_SCREW_D / 2 >= pr[0] + 3 && sx + TUBE_SCREW_D / 2 <= pr[2] - 3, str(n, ": tube screw on the flat of the tube"));
    for (m = mag_rects(n)) assert(rect_gap([sx - CSK_D / 2, DEPTH - 1, sx + CSK_D / 2, DEPTH], m) >= MIN_SKIN,
                                  str(n, ": tube-screw countersink clears the magnet channel"));
    assert(label_at(n)[0] == core_box(n)[0], str(n, ": label on the body's low-x face, engraved facing -x"));
}
assert(len(kerf_rects("mullion_glazing")) == 2 && len(bead_key_rects("mullion_glazing")) == 4, "glazing kerf and bead keyway on both sides");
assert(len(kerf_rects("mullion_sash")) == 4 && len(mag_rects("mullion_sash")) == 2, "fin kerf, inner-stop kerf and magnet channel on both sides");
assert(glazing_kerf_rect("mullion_glazing")[1] >= MIN_SKIN, "mullion glazing kerf floor");
assert(kerf_rects("mullion_sash")[0] == seal_kerf_rects("transom")[0] && kerf_rects("mullion_sash")[1] == seal_kerf_rects("transom")[1],
       "mullion sash side matches the transom sash side");

mt = [pocket_rect("mullion_sash")[1] + TUBE_CLEAR, pocket_rect("mullion_sash")[3] - TUBE_CLEAR];
assert(stay_c_min() >= mt[0] + MIN_SKIN && stay_c_max() <= mt[1] - MIN_SKIN, "stay track screws land on the mullion tube");
assert((mh - ml) - 2 * TRACK_SCREW_L >= MIN_SKIN, "8g x 16 stay-track screws from the two sides miss each other inside the tube");
echo("mullion profile rules ok");

use <../lib/mullion.scad>
use <../parts/jamb_node.scad>
use <../parts/cross_node.scad>

c = MULLION_W / 2;
k = mullion_leg();
d = mdove();
lk = mlock_uv();
tx = cross_faces();
function line_dist(p, a, b) = abs((b - a)[0] * (p - a)[1] - (b - a)[1] * (p - a)[0]) / norm(b - a);
function head_rect(x, z) = [x - CSK_D / 2, z - CSK_D / 2, x + CSK_D / 2, z + CSK_D / 2];
function xz(b) = [b[0], b[4], b[2], b[5]];

hd = dove_head(DOVE_CLEAR, d[0], d[1]);
up = [[0, DOVE_W / 2], [-d[0], DOVE_W / 2 + d[1]]];
dn = [[0, -DOVE_W / 2], [-d[0], -DOVE_W / 2 - d[1]]];
for (i = [1, 2]) assert(abs(line_dist(hd[i], up[0], up[1]) - DOVE_CLEAR) < 1e-6, str("mullion dovetail flank gap at ", hd[i]));
for (i = [0, 3]) assert(abs(line_dist(hd[i], dn[0], dn[1]) - DOVE_CLEAR) < 1e-6, str("mullion dovetail flank gap at ", hd[i]));
assert(abs(hd[0][0] + DOVE_CLEAR) < 1e-9 && abs(hd[2][0] + d[0] - DOVE_CLEAR) < 1e-9, "mullion dovetail mouth and floor gaps");
assert(d[1] / d[0] == DOVE_FLARE / DOVE_D, "mullion dovetail flanks at the jamb node's angle");
assert(pocket_rect("transom")[0] - (tx[0] + d[0]) >= CHAMBER_WALL && (tx[1] - d[0]) - pocket_rect("transom")[2] >= CHAMBER_WALL,
       "cross-node slots stop a chamber wall short of the transom tube");
for (n = ["sill", "sash_rebate"]) assert(FRAME_BODY - d[0] - pocket_rect(n)[2] >= CHAMBER_WALL, str(n, " node slot clears the frame tube"));

assert(len(lk) == 2, "two lock screws per joint");
for (q = lk) {
    fl = DOVE_W / 2 + d[1] * (-q[0]) / d[0];
    assert(q[0] == -LOCK_U && abs(abs(q[1]) - fl) < 1e-9, str("mullion lock axis on the slot flank ", q));
    zs = c + q[1];
    assert(zs - CSK_D / 2 >= k + MIN_SKIN && zs + CSK_D / 2 <= MULLION_W - k - MIN_SKIN, "lock heads clear the node bead keyways");
    for (dz = [-NODE_FIX_OFFSET, NODE_FIX_OFFSET])
        assert(abs(zs - (c + dz)) - CSK_D / 2 - FIX_CB_D / 2 >= MIN_SKIN, "lock heads clear the SN and HN fixing counterbores");
}
for (q = lk) assert(FRAME_BODY - (FRAME_BODY + q[0]) - LOCK_D / 2 >= LOCK_U - LOCK_D / 2 - 1e-9, str("SN and HN lock pilot wall to the node face ", q));
for (q = cross_locks()) assert(min(abs(q[0] - tx[0]), abs(q[0] - tx[1])) - LOCK_D / 2 >= LOCK_U - LOCK_D / 2 - 1e-9, str("TX lock pilot wall to its node face ", q));
assert(LOCK_D / 2 - DOVE_CLEAR >= 1, "lock pilot bites into the tongue");
assert(DEPTH - LOCK_L >= STOP_T + DOVE_CLEAR + MIN_SKIN, "lock pilot stays inside the tongue length");
assert(lock_top() <= DEPTH - MAG_D, "lock heads at or below the magnet channel floor");
for (q = cross_locks()) {
    assert(q[0] - LOCK_D / 2 >= pocket_rect("transom")[2] + MIN_SKIN || q[0] + LOCK_D / 2 <= pocket_rect("transom")[0] - MIN_SKIN,
           str("cross-node lock pilot clears the transom tube ", q));
    hr = head_rect(q[0], c + q[1]);
    sx = screw_x("transom");
    assert(rect_gap(hr, [sx - CSK_D / 2, c - CSK_D / 2, sx + CSK_D / 2, c + CSK_D / 2]) >= MIN_SKIN, "cross-node lock heads clear its tube screw");
    for (m = cross_mag_cuts()) assert(rect_gap(hr, xz(m)) >= MIN_SKIN || hr[0] >= m[0], str("cross-node lock head clear of the screen channel ", q));
}
for (m = cross_mag_cuts()) {
    assert(m[0] <= mag_rect("transom")[0] && m[2] > tx[1] && m[1] == DEPTH - MAG_D, str("screen channel runs from the transom channel to the upper shoe ", m));
    assert(m[4] >= CORD_D / 2 + MIN_SKIN && m[5] <= MULLION_W - CORD_D / 2 - MIN_SKIN, "screen channel clears the cross-node end grooves");
}
assert([for (m = cross_mag_cuts()) [m[4], m[5]]] == [for (r = mag_rects("mullion_sash")) [r[0], r[2]]], "cross-node channels line up with the mullion channels");
echo("mullion node rules ok");

use <../parts/mullion_shoe.scad>

for (q = lk) assert(head_rect(c + q[1], q[0])[0] >= ml + MIN_SKIN && head_rect(c + q[1], q[0])[2] <= mh - MIN_SKIN, "lock head lands on the shoe body");
for (profile = ["mullion_glazing", "mullion_sash"]) for (head = profile == "mullion_sash" ? [false, true] : [false]) {
    z = shoe_node_z(profile, head);
    f = shoe_features(profile, head);
    assert(len(z) == len(f), "one node feature per mullion feature pair");
    for (i = [0 : len(z) - 1]) for (r = f[i]) {
        b = mshoe_turn(r, z[i]);
        assert(b[0] <= r[0] && b[2] >= r[2] && (b[0] < 0 || b[2] > MULLION_W), str(profile, ": turn runs from the mullion feature to the shoe edge ", b));
        assert(b[4] >= 0 && b[5] <= k, str(profile, ": turn inside the shoe length ", b));
        for (q = lk) assert(rect_gap(xz(b), head_rect(c + q[1], q[0])) >= MIN_SKIN, str(profile, ": turn ", b, " clear of the lock heads"));
    }
    sz = mshoe_screw_z();
    assert(sz - TUBE_SCREW_D / 2 >= SHOE_WALL + 2 && sz + TUBE_SCREW_D / 2 <= k - MIN_SKIN,
           str(profile, ": shoe tube screw hits the tube with the tube anywhere in its 2 mm end clearance"));
    for (t = mshoe_turns(profile, head))
        assert(rect_gap(xz(t), [screw_x(profile) - CSK_D / 2, sz - CSK_D / 2, screw_x(profile) + CSK_D / 2, sz + CSK_D / 2]) >= MIN_SKIN
               || t[1] < DEPTH - MAG_D - 1, str(profile, ": tube-screw head clear of the turns"));
    g = mshoe_seam_groove(profile);
    assert(g[3] - g[1] == CORD_D && g[1] >= MIN_SKIN && g[3] <= STOP_T - MIN_SKIN, str(profile, ": seam groove below the dovetail stop"));
    assert(g[0] <= c - DOVE_W / 2 - d[1] && g[2] >= c + DOVE_W / 2 + d[1], str(profile, ": seam groove spans the dovetail"));
    for (r = kerf_rects(profile)) assert(rect_gap([g[0], g[1], g[2], g[3]], r) >= MIN_SKIN, str(profile, ": seam groove clears the kerfs"));
}
assert(node_z(glazing_kerf_rect("sill"), FRAME_BODY) == [tx[0] - glazing_kerf_rect("transom")[2], tx[0] - glazing_kerf_rect("transom")[0]],
       "sill and transom glazing kerfs sit at the same depth, so MSL serves both ends");
for (i = [0, 1]) assert(node_z(seal_kerf_rects("sash_rebate")[i], FRAME_BODY) == node_z(seal_kerf_rects("transom")[i], tx[1]),
                        "head and transom seal kerfs sit at the same depth in the upper shoes");
for (s = mshoe_fin_stubs("mullion_sash")) {
    assert(s[1] == FIN_Y0 && s[3] == FIN_Y1 && s[4] == 0 && s[5] == FIN_L && (s[0] == 0 || s[2] == MULLION_W), str("fin stub bridges to the shoe edge ", s));
    assert(s[0] >= seal_kerf_rects("mullion_sash")[0][2] + MIN_SKIN || s[2] <= MULLION_W - seal_kerf_rects("mullion_sash")[0][2] - MIN_SKIN,
           str("fin stub starts past the mullion fin kerf ", s));
}
echo("mullion shoe rules ok");
