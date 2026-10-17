// cad/assembly.scad
include <generated/dims.scad>
include <generated/layout.scad>
use <profile.scad>
use <parts/corner_block.scad>
use <parts/jamb_node.scad>
use <parts/transom_shoe.scad>
use <parts/frame_node.scad>
use <parts/cross_node.scad>
use <parts/mullion_shoe.scad>

section = false;
cut_x = W / 2;
plan_z = -1;
cut_t = 2;
NB = is_undef(BAYS) ? 1 : BAYS;
MX = is_undef(MULLIONS) ? [] : MULLIONS;

module run(name, len, m) { multmatrix(m) linear_extrude(len) profile(name); }

function run_x0(i) = i == 0 ? FRAME_W : MX[i - 1] + MULLION_W / 2;
function run_x1(i) = i == NB - 1 ? W - FRAME_W : MX[i] - MULLION_W / 2;
function sash_x(i) = i == 0 ? FRAME_BODY + SASH_GAP : MX[i - 1] + MULLION_HALF_BODY + SASH_GAP;
function glass_x(i) = i == 0 ? GLASS_EDGE : MX[i - 1] + TRANSOM_GLASS;

CUT = section || plan_z >= 0;
COLOURS = CUT ? ["SlateGray", "DarkOrange", "SkyBlue", "SteelBlue"] : ["WhiteSmoke", "WhiteSmoke", "Gainsboro", "LightBlue"];

module clip() {
    if (plan_z >= 0) intersection() { children(); translate([-50, -50, plan_z - cut_t / 2]) cube([W + 100, DEPTH + 100, cut_t]); }
    else if (section) intersection() { children(); translate([cut_x - cut_t / 2, -50, -50]) cube([cut_t, DEPTH + 100, H + 100]); }
    else children();
}

module mullion_runs(xm, tb) {
    x0 = xm - MULLION_W / 2;
    run("mullion_glazing", tb - FRAME_W, [[1, 0, 0, x0], [0, 1, 0, 0], [0, 0, 1, FRAME_W]]);
    run("mullion_sash", H - FRAME_W - (tb + TRANSOM_W), [[1, 0, 0, x0], [0, 1, 0, 0], [0, 0, 1, tb + TRANSOM_W]]);
}

module mullion_joints(xm, tb) {
    x0 = xm - MULLION_W / 2;
    x1 = xm + MULLION_W / 2;
    multmatrix([[0, 0, 1, x0], [0, 1, 0, 0], [1, 0, 0, 0]]) frame_node("sill", "SN");
    multmatrix([[0, 0, 1, x0], [0, 1, 0, 0], [-1, 0, 0, H]]) frame_node("sash_rebate", "HN");
    multmatrix([[0, 0, 1, x0], [0, 1, 0, 0], [1, 0, 0, tb]]) cross_node("TX");
    multmatrix([[1, 0, 0, x0], [0, 1, 0, 0], [0, 0, 1, FRAME_BODY]]) mullion_shoe("mullion_glazing", "MSL");
    multmatrix([[-1, 0, 0, x1], [0, 1, 0, 0], [0, 0, -1, tb + TRANSOM_W / 2 - TRANSOM_HALF_BODY]]) mullion_shoe("mullion_glazing", "MSL");
    multmatrix([[1, 0, 0, x0], [0, 1, 0, 0], [0, 0, 1, tb + TRANSOM_W / 2 + TRANSOM_HALF_BODY]]) mullion_shoe("mullion_sash", "MST");
    multmatrix([[-1, 0, 0, x1], [0, 1, 0, 0], [0, 0, -1, H - FRAME_BODY]]) mullion_shoe("mullion_sash", "MSH", head = true);
}

module frame() {
    F = FRAME_W;
    tb = TRANSOM_C - TRANSOM_W / 2;
    for (i = [0 : NB - 1]) {
        x0 = run_x0(i);
        len = run_x1(i) - x0;
        run("sill", len, [[0, 0, 1, x0], [0, 1, 0, 0], [1, 0, 0, 0]]);
        run("sash_rebate", len, [[0, 0, 1, x0], [0, 1, 0, 0], [-1, 0, 0, H]]);
        run("transom", len, [[0, 0, 1, x0], [0, 1, 0, 0], [1, 0, 0, tb]]);
    }
    for (xm = MX) mullion_runs(xm, tb);
    for (s = [[1, 0], [-1, W]]) {
        run("glazing", tb - F, [[s[0], 0, 0, s[1]], [0, 1, 0, 0], [0, 0, 1, F]]);
        run("sash_rebate", H - F - (tb + TRANSOM_W), [[s[0], 0, 0, s[1]], [0, 1, 0, 0], [0, 0, 1, tb + TRANSOM_W]]);
        translate([s[1], 0, tb]) mirror([s[0] < 0 ? 1 : 0, 0, 0]) {
            jamb_node("JN");
            multmatrix([[0, 0, 1, FRAME_BODY], [0, 1, 0, 0], [-1, 0, 0, TRANSOM_W]]) transom_shoe("TSL", mirrored = true);
        }
    }
    corner_block("sill", "glazing", "CSL");
    translate([W, 0, 0]) corner_block("sill", "glazing", "CSR", mirrored = true);
    translate([0, 0, H]) mirror([0, 0, 1]) corner_block("sash_rebate", "sash_rebate", "CH");
    translate([W, 0, H]) mirror([1, 0, 0]) mirror([0, 0, 1]) corner_block("sash_rebate", "sash_rebate", "CH");
}

module sash(x0) {
    z0 = TRANSOM_C + TRANSOM_HALF_BODY + SASH_GAP;
    S = SASH_W;
    run("sash", SASH[0] - 2 * S, [[0, 0, 1, x0 + S], [0, 1, 0, 0], [1, 0, 0, z0]]);
    run("sash", SASH[0] - 2 * S, [[0, 0, 1, x0 + S], [0, 1, 0, 0], [-1, 0, 0, z0 + SASH[1]]]);
    run("sash", SASH[1] - 2 * S, [[1, 0, 0, x0], [0, 1, 0, 0], [0, 0, 1, z0 + S]]);
    run("sash", SASH[1] - 2 * S, [[-1, 0, 0, x0 + SASH[0]], [0, 1, 0, 0], [0, 0, 1, z0 + S]]);
    translate([x0, 0, z0]) corner_block("sash", "sash", "CS");
    translate([x0 + SASH[0], 0, z0]) mirror([1, 0, 0]) corner_block("sash", "sash", "CS");
    translate([x0, 0, z0 + SASH[1]]) mirror([0, 0, 1]) corner_block("sash", "sash", "CS");
    translate([x0 + SASH[0], 0, z0 + SASH[1]]) mirror([1, 0, 0]) mirror([0, 0, 1]) corner_block("sash", "sash", "CS");
}

module pane(x, z, dims) { color(COLOURS[3], CUT ? 1 : 0.35) clip() translate([x, GLASS_Y0, z]) cube([dims[0], GLASS_T, dims[1]]); }

module window() {
    tb = TRANSOM_C - TRANSOM_W / 2;
    z0 = TRANSOM_C + TRANSOM_HALF_BODY + SASH_GAP;
    color(COLOURS[0]) clip() frame();
    color(COLOURS[1]) clip() for (xm = MX) mullion_joints(xm, tb);
    for (i = [0 : NB - 1]) {
        color(COLOURS[2]) clip() sash(sash_x(i));
        pane(sash_x(i) + SASH_GLASS, z0 + SASH_GLASS, SASH_GLASS_DIMS);
        pane(glass_x(i), GLASS_EDGE, FIXED_GLASS);
    }
}

window();
