// cad/tests/segment_test.scad
use <../lib/segment.scad>
use <../profile.scad>
include <../generated/dims.scad>

assert(boss_x("sash_rebate") == HINGE_BOSS_X);
assert(boss_x("glazing") == undef, "glazing segments take no bosses");
assert(rebate_face("sill") < FRAME_BODY, "sill rebate face follows the sloped floor");
assert(top_face("sash") == LIP_Y1);
assert(len([for (n = ["glazing", "sash_rebate", "sill"]) if (is_perimeter(n)) n]) == 3);
assert(!is_perimeter("transom"));

assert(END_CAP >= CORD_D / 2 + MIN_SKIN, "end cap backs the cord groove");
assert(CORD_INSET >= MIN_SKIN && CORD_INSET + CORD_D + MIN_SKIN <= MIN_SHELL, "cord ring fits the tube shell");
assert(!has_cord("screen") && has_cord("transom") && has_cord("sash"), "cord rings on weather members only");

for (n = ["sill", "sash"]) {
    w = weep_rect(n);
    assert(w[2] - w[0] == WEEP_H, str(n, ": weep slot matches the weep cap"));
    assert(rect_gap(w, glazing_kerf_rect(n)) >= MIN_SKIN, str(n, ": weep slot to glazing kerf ", rect_gap(w, glazing_kerf_rect(n))));
    for (r = chamber_rects(n)) assert(rect_gap(w, r) >= MIN_SKIN, str(n, ": weep slot to chamber ", rect_gap(w, r)));
}

sx = screw_x("transom");
assert(sx - CSK_D / 2 - (TRANSOM_MAG_X + MAG_W) >= MIN_SKIN, "transom tube-screw countersink clears the magnet channel");
assert(sx - TUBE_SCREW_D / 2 >= pocket_rect("transom")[0] + 3 && sx + TUBE_SCREW_D / 2 <= pocket_rect("transom")[2] - 3,
       "transom tube screw lands on the flat of the steel tube");
assert(norm([CAM_BOSS_X - sx, BOSS_PITCH / 2]) - CSK_D / 2 - INSERT_M4_D / 2 >= MIN_SKIN, "transom tube screw clears the cam inserts");

assert(fix_dz("glazing") == 0 && fix_dz("sill") == 0, "glazing and sill fix below the tube, screw above it");
assert(fix_dz("sash_rebate") - FIX_D / 2 - TUBE_SCREW_D / 2 >= MIN_SKIN, "sash_rebate fixing hole clears the tube screw");
assert(DEPTH - INSERT_M4_L - (fix_y("sash_rebate") + FIX_D / 2) >= MIN_SKIN, "sash_rebate fixing hole clears the hinge inserts");
assert(norm([boss_x("sash_rebate") - screw_x("sash_rebate"), BOSS_PITCH / 2 - fix_dz("sash_rebate") / 2])
       - CSK_D / 2 - INSERT_M4_D / 2 >= MIN_SKIN, "head tube screw clears the hinge inserts");
for (n = ["sash", "transom", "sash_rebate"]) {
    d = boss_dz_min(n);
    assert(norm([boss_x(n) - screw_x(n), d - BOSS_PITCH / 2 - fix_dz(n) / 2]) - CSK_D / 2 - INSERT_M4_D / 2 >= MIN_SKIN - 1e-9,
           str(n, ": offset boss pairs keep their inner inserts clear of the tube screw"));
    assert(2 * (d - BOSS_PITCH / 2) >= INSERT_M4_D + MIN_SKIN - 1e-9, str(n, ": the two offset pairs' inner inserts clear each other"));
    assert(MAX_SEG / 2 - (boss_dz_max(MAX_SEG) + BOSS_PITCH / 2 + INSERT_M4_D / 2) >= END_CAP + MIN_SKIN - 1e-9,
           str(n, ": outer insert stops short of the end cap at the largest offset"));
}
assert(abs(boss_dz_min("sash") - (BOSS_PITCH / 2 + CSK_D / 2 + INSERT_M4_D / 2 + MIN_SKIN)) < 1e-9, "sash bosses share the tube screw's x");
assert(top_face("sash") - INSERT_M4_L >= weep_rect("sash")[3] + MIN_SKIN, "SBE inserts clear the weep slot at any offset");
assert(pocket_rect("sash")[3] >= weep_rect("sash")[3] + MIN_SKIN, "SBE boss columns stay above the weep slot at any offset");
assert(!is_perimeter("sash"), "sash segments have no fixing holes for offset bosses to meet");
echo("segment rules ok");
