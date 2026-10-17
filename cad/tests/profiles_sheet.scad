// cad/tests/profiles_sheet.scad
use <../profile.scad>
include <../generated/dims.scad>

names = ["glazing", "sash_rebate", "sill", "transom", "sash", "screen"];
for (i = [0 : len(names) - 1]) translate([i * 100 + 20, 0]) {
    color("SteelBlue") profile(names[i]);
    color("Black") translate([0, -12]) text(names[i], size = 5);
}
for (g = [["igu", 0], ["twinwall", 1]]) translate([620 + g[1] * 40, 0]) {
    color("Peru") bead_profile(g[0]);
    color("Black") translate([0, -12]) text(g[0], size = 5);
}
