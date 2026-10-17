// cad/parts/corner_block.scad
include <../generated/dims.scad>
use <../profile.scad>
use <../lib/segment.scad>
use <../lib/emboss.scad>

EPS = 0.01;
ALONG_X = [[0, 0, 1, 0], [0, 1, 0, 0], [1, 0, 0, 0]];

function socket_limit(a, b, core) = profile_width(b) - pocket_rect(b, core)[2] - CHAMBER_WALL;
function corner_anchor(a, b) = profile_width(b) - socket_depth(a) / 2;
function corner_screw_at(a, b) = corner_anchor(a, b) - fix_dz(a) / 2;
function corner_fix_at(a, b) = corner_anchor(a, b) + fix_dz(a) / 2;

module half_space(lo, hi, below) {
    pts = below ? [[lo, lo], [hi, lo], [hi, hi]] : [[lo, lo], [hi, hi], [lo, hi]];
    translate([0, DEPTH + 1, 0]) rotate([90, 0, 0]) linear_extrude(DEPTH + 2) polygon(pts);
}

module leg(a, b, core) {
    z0 = profile_min(b);
    z1 = profile_width(b);
    translate([0, 0, z0]) linear_extrude(z1 - z0) profile(a, false, core);
    translate([0, 0, z1 - END_CAP]) end_cap(a, false, core);
    intersection() {
        translate([0, 0, z0]) linear_extrude(z1 - z0) profile_solid(a, false, core);
        union() {
            screw_column(a, corner_screw_at(a, b), core);
            if (is_perimeter(a)) fixing_column(a, corner_fix_at(a, b));
        }
    }
}

module leg_cuts(a, b, core) {
    z1 = profile_width(b);
    translate([0, 0, z1 - socket_depth(a)]) linear_extrude(socket_depth(a) + EPS) pocket_cut(a, core);
    translate([0, 0, z1 - CORD_D / 2]) end_groove(a, core);
    bevel_ends(z1, bottom = false) bevel_outline(a, core);
    tube_screw(a, corner_screw_at(a, b), core = core);
    if (is_perimeter(a)) fixing_hole(a, corner_fix_at(a, b));
}

module corner_block(a, b, code, mirrored = false, core_a, core_b) {
    assert(socket_depth(a) <= socket_limit(a, b, core_b) && socket_depth(b) <= socket_limit(b, a, core_a), str(code, ": tube sockets collide"));
    lo = min(profile_min(a), profile_min(b));
    hi = max(profile_width(a), profile_width(b));
    difference() {
        mirror([mirrored ? 1 : 0, 0, 0]) difference() {
            union() {
                intersection() {
                    multmatrix(ALONG_X) leg(a, b, core_a);
                    half_space(lo - 1, hi + 1, true);
                }
                intersection() {
                    leg(b, a, core_b);
                    half_space(lo - 1, hi + 1, false);
                }
            }
            multmatrix(ALONG_X) leg_cuts(a, b, core_a);
            leg_cuts(b, a, core_b);
        }
        engrave(code, label_at(b), (profile_min(a) + profile_width(a)) / 2, facing = mirrored ? 1 : -1);
    }
}
