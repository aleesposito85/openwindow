// cad/tests/mullion_sheet.scad
use <../profile.scad>
include <../generated/dims.scad>

names = ["mullion_glazing", "transom", "mullion_sash"];
for (i = [0 : len(names) - 1]) translate([i * 100, 0]) {
    color("SteelBlue") profile(names[i]);
    color("Black") translate([0, -12]) text(names[i], size = 5);
}
