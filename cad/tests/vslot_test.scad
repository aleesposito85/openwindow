// cad/tests/vslot_test.scad
use <../profile.scad>
use <../lib/segment.scad>
include <../generated/dims.scad>

V = "vslot";
TNUT = ["glazing", "sill", "sash_rebate", "sash", "mullion_glazing", "mullion_sash"];
function mid(r) = (r[1] + r[3]) / 2;
function in_shoulder(c, y) = abs(y - c) >= VSLOT_SHOULDER[0] && abs(y - c) <= VSLOT_SHOULDER[1];

o = pocket_origin("sash_rebate", V);
p = pocket("sash_rebate");
assert(o[1] == pocket_origin("sash_rebate")[1] - VSLOT_SHIFT, "V-slot moves the head and upper-jamb pocket outward");
assert(pocket_origin("sash_rebate", "alu20") == o, "a standard tube in a V-slot window sits in the moved pocket");
assert(pocket_rect("glazing", V) == pocket_rect("glazing") && pocket_rect("sash", V) == pocket_rect("sash"), "only sash_rebate moves");
assert(o[1] >= MIN_SHELL && DEPTH - (o[1] + p[1]) >= MIN_SHELL, str("moved pocket shell ", o[1]));
assert(fix_y("sash_rebate") - FIX_D / 2 >= o[1] + p[1] + 2, "fixing screw clears the moved tube");
for (r = chamber_rects("sash_rebate", V)) {
    assert(r[2] - r[0] >= CHAMBER_WALL && r[3] - r[1] >= CHAMBER_WALL, str("collapsed chamber ", r));
    assert(rect_gap(r, pocket_rect("sash_rebate", V)) >= CHAMBER_WALL - 1e-6, str("chamber ", r, " to moved pocket"));
    for (k = kerf_rects("sash_rebate")) assert(rect_gap(r, k) >= MIN_SKIN, str("chamber ", r, " to kerf"));
}
for (c = [undef, V]) let(rs = chamber_rects("sash_rebate", c)) for (i = [0 : len(rs) - 2]) for (j = [i + 1 : len(rs) - 1])
    assert(rect_gap(rs[i], rs[j]) >= CHAMBER_WALL - 1e-6, str("sash_rebate ", c, ": chambers ", rs[i], " and ", rs[j], " ", rect_gap(rs[i], rs[j]), " apart"));

jt = pocket_rect("sash_rebate", V);
assert(stay_c_min() >= jt[1] + TUBE_CLEAR + MIN_SKIN && stay_c_max() <= jt[3] - TUBE_CLEAR - MIN_SKIN, "stay screws land on the moved jamb tube");
mc = pocket_rect("mullion_sash", V)[3] - TUBE_CLEAR - TUBE_FRAME[1] / 2;
for (c = [mid(jt), mid(pocket_rect("sash")), mc]) for (y = [stay_c_min(), stay_c_max()])
    assert(in_shoulder(c, y), str("stay screw at ", y, " is ", abs(y - c), " mm off the tube centre ", c, ", outside the shoulder"));

for (n = TNUT) {
    r = pocket_rect(n, V);
    assert(screw_x(n, V) == (r[0] + r[2]) / 2, str(n, ": T-nut screw on the slot centreline"));
    tip = vslot_seat(n) + vslot_screw_l(n) - vslot_shell(n);
    assert(tip >= VSLOT_TIP[0] && tip <= VSLOT_TIP[1], str(n, ": screw tip ", tip, " mm into the slot"));
    assert(vslot_seat(n) >= 0, str(n, ": seat above the face"));
    assert(vslot_seat(n) + (VSLOT_CSK_D - VSLOT_SCREW_D) / 2 <= vslot_shell(n) - MIN_SKIN, str(n, ": countersink inside the shell"));
    assert((column_d(n, V) - VSLOT_CSK_D) / 2 >= MIN_SKIN, str(n, ": column wall round the M5 head"));
}
assert([for (n = TNUT) vslot_screw_l(n)] == [25, 25, 25, 20, 16, 16], str("M5 lengths ", [for (n = TNUT) vslot_screw_l(n)]));
assert(VSLOT_TIP[0] >= VSLOT_LIP + 3 && VSLOT_TIP[1] <= VSLOT_FLOOR - 0.3, "tip window: 3 mm of nut past the lip, short of the floor");

tc = TRANSOM_W / 2;
assert(screw_x("transom", V) == VSLOT_TRANSOM_X && abs(VSLOT_TRANSOM_X - tc) >= VSLOT_SHOULDER[0] && abs(VSLOT_TRANSOM_X - tc) <= VSLOT_SHOULDER[1],
       "transom screw on the room-side 2020's shoulder");
assert(VSLOT_TRANSOM_X - CSK_D / 2 >= TRANSOM_MAG_X + MAG_W + MIN_SKIN, "transom screw head clear of the magnet channel");
assert(VSLOT_TRANSOM_X + CSK_D / 2 <= TRANSOM_W / 2 + TRANSOM_HALF_BODY - MIN_SKIN, "transom screw head inside the body");
assert(norm([CAM_BOSS_X - VSLOT_TRANSOM_X, BOSS_PITCH / 2]) - INSERT_M4_D / 2 - CSK_D / 2 >= MIN_SKIN, "transom screw clear of the cam inserts");
assert(norm([HINGE_BOSS_X - screw_x("sash_rebate", V), BOSS_PITCH / 2 - FIX_DZ / 2]) - INSERT_M4_D / 2 - VSLOT_CSK_D / 2 >= MIN_SKIN,
       "head M5 clear of the hinge inserts");
assert(boss_dz_min("sash", V) == BOSS_PITCH / 2 + VSLOT_CSK_D / 2 + INSERT_M4_D / 2 + MIN_SKIN, "keeper bosses clear the sash M5 head");
echo("vslot rules ok");
