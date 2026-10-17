// cad/tests/profile_test.scad
use <../profile.scad>
include <../generated/dims.scad>

module shell_ok(name, x0, x1, y0, y1) {
    o = pocket_origin(name);
    p = pocket(name);
    assert(o[0] - x0 >= MIN_SHELL, str(name, ": shell on low x ", o[0] - x0));
    assert(x1 - (o[0] + p[0]) >= MIN_SHELL, str(name, ": shell on high x ", x1 - (o[0] + p[0])));
    assert(o[1] - y0 >= MIN_SHELL, str(name, ": shell outside ", o[1] - y0));
    assert(y1 - (o[1] + p[1]) >= MIN_SHELL, str(name, ": shell inside ", y1 - (o[1] + p[1])));
}

shell_ok("glazing", 0, FRAME_BODY, 0, DEPTH);
shell_ok("sash_rebate", 0, FRAME_BODY, 0, DEPTH);
shell_ok("sill", 0, FRAME_BODY - (bead_seat_y() - STOP_T) * tan(SILL_SLOPE_DEG), 0, DEPTH);
shell_ok("transom", TRANSOM_W / 2 - TRANSOM_HALF_BODY, TRANSOM_W / 2 + TRANSOM_HALF_BODY, 0, DEPTH);
shell_ok("sash", 0, SASH_BODY, SASH_Y0, LIP_Y1);

assert(FRAME_W - GLASS_EDGE >= 12, "frame glass bite");
assert(TRANSOM_W / 2 - TRANSOM_GLASS >= 12, "transom glass bite");
assert(SASH_W - SASH_GLASS >= 12, "sash glass bite");
assert(GLASS_EDGE - FRAME_BODY == GLASS_CLEAR, "frame glass clearance");
assert(TRANSOM_GLASS - TRANSOM_HALF_BODY == GLASS_CLEAR, "transom glass clearance");
assert(SASH_GLASS - SASH_BODY == GLASS_CLEAR, "sash glass clearance");
assert(GLASS_Y0 - STOP_T == GASKET_T, "outer glazing gasket gap");
assert(KEY_Y >= bead_seat_y() + 2, "bead keyway clears the bead seat");
assert(bead_seat_y() + BEAD_T <= DEPTH, "bead inside the frame depth");
assert(BEAD_W <= TRANSOM_W / 2 - TRANSOM_HALF_BODY, "bead fits the transom rebate");

sash_edge = FRAME_BODY + SASH_GAP;
assert(sash_edge - FLANGE_L <= FRAME_BODY + FIN_L / 2 - KERF_W / 2, "sash flange covers the fin seal");
assert(FIN_Y0 - FLANGE_Y1 >= 2 && FIN_Y0 - FLANGE_Y1 <= 4, "outer seal compression gap 2-4 mm");
assert(ISTOP_Y0 - LIP_Y1 >= 2 && ISTOP_Y0 - LIP_Y1 <= 4, "inner seal compression gap 2-4 mm");
assert(sash_edge - LIP_L >= FRAME_BODY, "sash lip stays over the inner stop");
assert(TRANSOM_W - (TRANSOM_W / 2 + TRANSOM_HALF_BODY) >= SASH_GAP, "transom stop reaches under the sash lip");
assert(SASH_GAP >= 13, "friction stay cavity width");
assert(LIP_Y0 - FIN_Y1 >= 16, "friction stay cavity depth");
assert(FIX_Y + FIX_D / 2 <= pocket_origin("glazing")[1] - 2, "fixing screw clears the tube");
assert(SCREEN_OVERLAP + 2 + MAG_W <= SCREEN_W, "screen magnet channel inside the screen face");
assert(SCREEN_DEPTH - SPLINE_D - MAG_D >= 4, "screen wall between magnet channel and spline groove");
assert(TRANSOM_MAG_X >= TRANSOM_W / 2 - TRANSOM_HALF_BODY && TRANSOM_MAG_X + MAG_W <= TRANSOM_W / 2 + TRANSOM_HALF_BODY,
       "transom magnet channel on the transom body face");
assert(DEPTH - INSERT_M4_L >= pocket_origin("transom")[1] + pocket("transom")[1] + 1.5, "cam inserts clear the steel tube");

tl = TRANSOM_W / 2 - TRANSOM_HALF_BODY;
th = TRANSOM_W / 2 + TRANSOM_HALF_BODY;
function nearest(rs, t) = min([for (r = rs) rect_gap(r, t)]);

assert(rect_gap([0, 0, 1, 1], [4, 5, 5, 6]) == 5 && rect_gap([0, 0, 2, 2], [1, 1, 3, 3]) == 0, "rect_gap");
for (n = ["glazing", "sash_rebate", "sill", "sash", "screen"]) {
    assert(len(chamber_rects(n)) > 0, str(n, ": chambers"));
    for (r = chamber_rects(n)) {
        assert(r[2] - r[0] >= CHAMBER_WALL && r[3] - r[1] >= CHAMBER_WALL, str(n, ": collapsed chamber ", r));
        assert(rect_gap(r, pocket_rect(n)) >= CHAMBER_WALL - 1e-6, str(n, ": chamber ", r, " to tube pocket"));
        for (k = bead_key_rects(n))
            assert(rect_gap(r, k) >= MIN_SKIN, str(n, ": chamber ", r, " to bead keyway ", rect_gap(r, k)));
        for (k = kerf_rects(n))
            assert(rect_gap(r, k) >= MIN_SKIN, str(n, ": chamber ", r, " to kerf ", rect_gap(r, k)));
    }
}
for (r = chamber_rects("sill")) for (k = nose_key_rects())
    assert(rect_gap(r, k) >= MIN_SKIN, str("sill: chamber ", r, " to nose keyway ", rect_gap(r, k)));
for (n = ["glazing", "sill"]) for (r = chamber_rects(n))
    assert(rect_gap(r, counterbore_rect(n)) >= MIN_SKIN, str(n, ": chamber ", r, " to fixing counterbore ", rect_gap(r, counterbore_rect(n))));
assert(len(chamber_rects("transom")) == 0, "transom body is solid");

for (n = ["glazing", "sash_rebate", "sill"]) {
    o = pocket_origin(n);
    p = pocket(n);
    cb = counterbore_rect(n);
    assert(fix_y(n) + FIX_D / 2 <= o[1] - 2 || fix_y(n) - FIX_D / 2 >= o[1] + p[1] + 2, str(n, ": fixing screw clears the tube"));
    assert(cb[0] - (o[0] + p[0]) >= MIN_SKIN, str(n, ": counterbore floor clears the tube pocket"));
    assert((FIX_BOSS_D - FIX_CB_D) / 2 >= MIN_SKIN, "fixing column wall around the counterbore");
    for (k = bead_key_rects(n)) assert(fix_y(n) + FIX_BOSS_D / 2 + MIN_SKIN <= k[1], str(n, ": fixing column clears the bead keyway"));
}
assert(fix_y("sash_rebate") - FIX_CB_D / 2 >= FIN_Y1 && fix_y("sash_rebate") + FIX_CB_D / 2 <= ISTOP_Y0,
       "sash_rebate fixing opens between the outer and inner seals");
for (n = ["glazing", "sill"]) assert(fix_y(n) - FIX_CB_D / 2 >= STOP_T && fix_y(n) + FIX_CB_D / 2 <= GLASS_Y0 + GLASS_T,
       str(n, ": fixing opens inside the glazing pocket"));
assert(fix_y("sill") - FIX_BOSS_D / 2 >= NOSE_KEY_D + MIN_SKIN, "sill fixing column clears the nose keyway");

for (n = ["glazing", "sill", "transom", "sash"])
    assert(glazing_kerf_rect(n)[1] - stop_floor(n) >= MIN_SKIN, str(n, ": glazing kerf floor ", glazing_kerf_rect(n)[1] - stop_floor(n)));
assert(FIN_Y1 - (FIN_Y0 + KERF_D) >= MIN_SKIN, "fin kerf floor");
assert(DEPTH - (ISTOP_Y0 + KERF_D) >= MIN_SKIN, "inner stop kerf floor");

assert(TRANSOM_MAG_X - tl >= MIN_SKIN, str("transom magnet channel lip to the glazing face ", TRANSOM_MAG_X - tl));
assert(nearest(bead_key_rects("transom"), pocket_rect("transom")) >= MIN_SKIN, "transom keyway to steel tube");

for (g = ["igu", "acrylic", "twinwall"]) {
    c = bead_chamber(g);
    assert(is_undef(c) || (c[3] - c[1] >= CHAMBER_WALL && c[2] - c[0] >= CHAMBER_WALL), str(g, ": bead chamber slit ", c));
}
for (n = ["glazing", "sash_rebate", "sill", "transom", "sash", "screen"])
    assert(socket_depth(n) > TUBE_END_CLEAR, str(n, ": socket depth"));
for (g = ["igu", "acrylic", "twinwall"])
    assert(bead_label_y(g) - BEAD_LABEL / 2 >= bead_y0(g) + 0.5 && bead_label_y(g) + BEAD_LABEL / 2 <= KEY_Y + 0.2 - 0.5,
           str(g, ": bead ID on the host face below the key tongue"));
echo("profile rules ok");

jt = [pocket_rect("sash_rebate")[1] + TUBE_CLEAR, pocket_rect("sash_rebate")[3] - TUBE_CLEAR];
assert(stay_c_min() <= stay_c_max(), str("a ", STAY_W, " mm stay fits between the jamb fin and the sash tube edge: ", stay_c_min(), " > ", stay_c_max()));
assert(sash_tube_y()[1] - stay_c_max() >= MIN_SKIN && stay_c_min() - sash_tube_y()[0] >= MIN_SKIN, "stay screws land on the sash tube");
assert(stay_c_max() + STAY_W / 2 <= LIP_Y0, "stay body clears the sash lip");
assert(stay_c_min() - STAY_W / 2 >= FIN_Y1, "stay body clears the jamb fin");
assert(stay_c_min() >= jt[0] + MIN_SKIN && stay_c_max() <= jt[1] - MIN_SKIN, "stay screws land on the jamb tube");
assert(stay_c_max() + TUBE_SCREW_D / 2 + MIN_SKIN <= FIX_Y_IN - FIX_CB_D / 2, "stay screws pass below the JU fixing counterbores");
echo("stay envelope ok");
