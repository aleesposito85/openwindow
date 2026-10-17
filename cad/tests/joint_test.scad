// cad/tests/joint_test.scad
include <../generated/dims.scad>
use <../profile.scad>
use <../parts/jamb_node.scad>
use <../parts/transom_shoe.scad>

c = TRANSOM_W / 2;
tl = TRANSOM_W / 2 - TRANSOM_HALF_BODY;
th = TRANSOM_W / 2 + TRANSOM_HALF_BODY;
function line_dist(p, a, b) = abs((b - a)[0] * (p - a)[1] - (b - a)[1] * (p - a)[0]) / norm(b - a);

hd = dove_head(DOVE_CLEAR);
up = [[0, DOVE_W / 2], [-DOVE_D, DOVE_W / 2 + DOVE_FLARE]];
dn = [[0, -DOVE_W / 2], [-DOVE_D, -DOVE_W / 2 - DOVE_FLARE]];
assert(DOVE_CLEAR >= 0.3, "dovetail clearance");
for (i = [1, 2]) assert(abs(line_dist(hd[i], up[0], up[1]) - DOVE_CLEAR) < 1e-6, str("dovetail flank gap at ", hd[i]));
for (i = [0, 3]) assert(abs(line_dist(hd[i], dn[0], dn[1]) - DOVE_CLEAR) < 1e-6, str("dovetail flank gap at ", hd[i]));
assert(abs(hd[0][0] + DOVE_CLEAR) < 1e-9 && abs(hd[2][0] + DOVE_D - DOVE_CLEAR) < 1e-9, "dovetail mouth and floor gaps");
assert(dove_root_w() / 2 + DOVE_CLEAR <= DOVE_W / 2 + 1e-9, "tongue root clears the slot mouth");
assert(dove_root_d() == SHOE_WALL, "tongue root is the full shoe end wall");

lk = lock_uv();
fl = DOVE_W / 2 + DOVE_FLARE * LOCK_U / DOVE_D;
assert(LOCK_U > 0 && LOCK_U < DOVE_D && len(lk) == 2, "lock screws sit on the dovetail flanks");
for (q = lk) assert(q[0] == -LOCK_U && abs(abs(q[1]) - fl) < 1e-9, str("lock axis on the slot flank ", q));
assert(LOCK_D / 2 - DOVE_CLEAR >= 1, "lock pilot bites into the tongue past the slide clearance");
assert(DEPTH - LOCK_L >= STOP_T + DOVE_CLEAR + MIN_SKIN, "lock pilot stays inside the tongue length");
assert(DEPTH - LOCK_L >= FIX_Y + FIX_CB_D / 2 + MIN_SKIN, "lock pilot clears the node fixing counterbores");
mz = shoe_turns()[2][0];
channels = [[FRAME_BODY, TRANSOM_MAG_X, FRAME_W, TRANSOM_MAG_X + MAG_W], [FRAME_BODY + mz[4], mz[0], FRAME_BODY + mz[5], TRANSOM_W]];
for (q = lk) {
    hx = FRAME_BODY + q[0];
    hz = c + q[1];
    head = [hx - CSK_D / 2, hz - CSK_D / 2, hx + CSK_D / 2, hz + CSK_D / 2];
    for (ch = channels)
        assert(rect_gap(head, ch) > 0 || lock_top() <= DEPTH - MAG_D, str("lock head above the magnet channel floor at ", q));
    assert(lock_top() <= DEPTH && lock_top() - (CSK_D - LOCK_D) / 2 >= DEPTH - LOCK_L, "lock countersink inside the pilot depth");
    assert(head[1] >= node_key_len() + MIN_SKIN && head[3] <= TRANSOM_W - node_key_len() - MIN_SKIN, "lock head clears the node keyways");
    assert(head[2] <= FRAME_BODY || (head[1] >= tl + MIN_SKIN && head[3] <= th - MIN_SKIN), "lock head lands on the shoe body");
    assert(head[2] <= FRAME_BODY || mz[4] <= 0, "no rib between the lock head and the jamb magnet channel");
}
assert(tl - BEAD_W >= 0 && tl - BEAD_W <= node_key_len(), "fixed-pane side bead ends inside the node keyway");

L = FRAME_W - FRAME_BODY;
for (t = shoe_turns()) {
    b = t[0];
    j = t[1];
    r = t[2];
    assert(j[1] == r[1] && j[3] == r[3], str("jamb and transom feature depths match ", j, r));
    assert(b[5] == j[2] - FRAME_BODY && (t[3] ? b[4] <= 0 : b[4] == j[0] - FRAME_BODY) && b[4] >= -1 && b[5] <= L,
           str("turn lines up with the jamb feature ", b));
    assert(b[0] <= r[0] && b[2] >= r[2] && (b[0] < 0 || b[2] > TRANSOM_W), str("turn runs from the transom feature to the shoe edge ", b));
}
fs = shoe_fin_stub();
assert(fs[0] <= th + FIN_L && fs[0] >= seal_kerf_rects("transom")[0][2] + MIN_SKIN && fs[2] == TRANSOM_W && fs[1] == FIN_Y0 && fs[3] == FIN_Y1 && fs[4] == 0 && fs[5] == FIN_L,
       str("shoe fin stub bridges the transom fin to the jamb fin ", fs));
sg = shoe_seam_groove();
assert(sg[2] - sg[0] > 0 && sg[3] - sg[1] == CORD_D && sg[5] == CORD_D / 2, str("shoe seam cord groove ", sg));
assert(sg[1] >= MIN_SKIN && sg[3] <= STOP_T - MIN_SKIN, "seam groove sits on the node face below the dovetail stop");
assert(sg[0] >= glazing_kerf_rect("transom")[2] + MIN_SKIN && sg[2] <= th - MIN_SKIN, "seam groove walls to the glazing kerf and the sash face");
assert(sg[0] <= c - DOVE_W / 2 - DOVE_FLARE && sg[2] >= c + DOVE_W / 2 + DOVE_FLARE, "seam groove spans the whole dovetail");
echo("joint rules ok");
