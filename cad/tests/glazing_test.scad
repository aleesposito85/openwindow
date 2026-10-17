// cad/tests/glazing_test.scad
include <../generated/dims.scad>
use <../profile.scad>
use <../parts/acrylic_spacer.scad>
use <../parts/setting_block.scad>

assert(bead_y0("acrylic") == bead_seat_y(), "default acrylic bead sits on the bead seat");
assert(bead_y0("igu") == bead_seat_y(), "IGU bead sits on the bead seat");
assert(bead_y0("twinwall") == bead_seat_y() - (GLASS_T - TWINWALL_T), "twin-wall bead packs the pocket");
assert(bead_y0("acrylic", 18) == bead_seat_y() - 6, "an 18 mm sandwich deepens the bead by 6 mm");
assert(bead_y0("acrylic", 12) == bead_seat_y() - 12, "the thinnest sandwich deepens the bead by 12 mm");
assert(bead_y0("acrylic", 12) - GASKET_T >= GLASS_Y0 + 12, "the deepest bead still leaves the gasket gap to the glass");
let (c = bead_chamber("acrylic", 18))
    assert(!is_undef(c) && c[1] - (bead_y0("acrylic", 18) + KERF_D) >= MIN_SKIN, "deep bead chamber clears the kerf");
assert(bead_label_y("acrylic", 18) > bead_y0("acrylic", 18) && bead_label_y("acrylic", 18) < KEY_Y, "label stays on the bead face");
assert(spacer_t() == GLASS_T - 2 * ACRYLIC_T, "default spacer height is the default gap");
assert(spacer_t(12) == 12, "spacer height follows the gap");
assert(spacer_t(8) - 6 >= 2, "the smallest gap keeps a 2 mm desiccant channel");
assert(spacer_t(8) - 6 - 0.3 > 0, "the smallest gap keeps a corner plug");
for (s = [12, 18, 24, TWINWALL_T]) {
    glazing = s == TWINWALL_T ? "twinwall" : "acrylic";
    assert(setting_top(s) <= bead_y0(glazing, s) - GASKET_T, str("setting block clears the bead for a ", s, " mm pane"));
}
assert(setting_top() == GLASS_Y0 + GLASS_T, "default setting block is full pocket height");
let (c = bead_chamber("acrylic", 12))
    assert(!is_undef(c) && c[1] - (bead_y0("acrylic", 12) + KERF_D) >= MIN_SKIN, "deepest bead chamber clears the kerf");
assert(bead_label_y("acrylic", 12) - BEAD_LABEL / 2 >= bead_y0("acrylic", 12) + 0.5, "deepest bead label stays on the face");
echo("glazing rules ok");
