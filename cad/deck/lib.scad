// cad/deck/lib.scad: palette and window-unit modules shared by the guide-deck views
include <../generated/dims.scad>
include <../generated/layout.scad>
use <../profile.scad>
use <../lib/segment.scad>
use <../parts/corner_block.scad>
use <../parts/jamb_node.scad>
use <../parts/transom_shoe.scad>
use <../parts/cam_lock.scad>
use <../parts/screen_hinge.scad>
use <../parts/sill_nose.scad>
use <../parts/weep_cap.scad>
use <../parts/setting_block.scad>

C_FRAME = "#c3cbd1";
C_TRANSOM = "#7fa7bf";
C_SASH = "#93b49c";
C_SCREEN = "#5f6a73";
C_BEAD = "#e2d6bd";
C_GLASS = "#b9dbe9";
C_GLASS_SOLID = "#b9dbe9";
C_ALU = "#878e94";
C_STEEL = "#4f565c";
C_SEAL = "#262626";
C_HI = "#ef8a22";
C_DONE = "#d9dee2";
C_MAG = "#8a5a35";
C_BLOCK = "#8e979e";

F = FRAME_W;
TB = TRANSOM_C - TRANSOM_W / 2;
SX0 = FRAME_BODY + SASH_GAP;
SZ0 = TRANSOM_C + TRANSOM_HALF_BODY + SASH_GAP;
NX0 = FRAME_BODY - SCREEN_OVERLAP;
NZ0 = TB + TRANSOM_MAG_X - SCREEN_OVERLAP - 2;
GAP = JOINT_GAP;
SOCK = SOCKET_FRAME - TUBE_END_CLEAR;
SASH_SOCK = SOCKET_SASH - TUBE_END_CLEAR;
SCREEN_SOCK = SOCKET_SCREEN - TUBE_END_CLEAR;
CAM_AT = F + GAP + SEG_TRANSOM / 2;

M_SILL = [[0, 0, 1, F], [0, 1, 0, 0], [1, 0, 0, 0]];
M_HEAD = [[0, 0, 1, F], [0, 1, 0, 0], [-1, 0, 0, H]];
M_TRANSOM = [[0, 0, 1, F], [0, 1, 0, 0], [1, 0, 0, TB]];

function m_jamb(right, z0) = right ? [[-1, 0, 0, W], [0, 1, 0, 0], [0, 0, 1, z0]] : [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, z0]];
function m_sash_h(top) = [[0, 0, 1, SX0 + SASH_W], [0, 1, 0, 0], top ? [-1, 0, 0, SZ0 + SASH[1]] : [1, 0, 0, SZ0]];
function m_sash_v(right) = right ? [[-1, 0, 0, SX0 + SASH[0]], [0, 1, 0, 0], [0, 0, 1, SZ0 + SASH_W]] : [[1, 0, 0, SX0], [0, 1, 0, 0], [0, 0, 1, SZ0 + SASH_W]];
function m_screen_h(top) = [[0, 0, 1, NX0 + SCREEN_W], [0, 1, 0, DEPTH], top ? [-1, 0, 0, NZ0 + SCREEN[1]] : [1, 0, 0, NZ0]];
function m_screen_v(right) = right ? [[-1, 0, 0, NX0 + SCREEN[0]], [0, 1, 0, DEPTH], [0, 0, 1, NZ0 + SCREEN_W]] : [[1, 0, 0, NX0], [0, 1, 0, DEPTH], [0, 0, 1, NZ0 + SCREEN_W]];
function m_cam(x) = [[-1, 0, 0, x], [0, 0, 1, DEPTH], [0, 1, 0, TB + CAM_BOSS_X]];

function tube_wall(name) = name == "screen" ? 1.0 : 1.6;

module tube2d(name) {
    r = pocket_rect(name);
    c = TUBE_CLEAR;
    difference() {
        rect(r[0] + c, r[1] + c, r[2] - c, r[3] - c);
        offset(delta = -tube_wall(name)) rect(r[0] + c, r[1] + c, r[2] - c, r[3] - c);
    }
}

module seg_run(name, n, seg, m, col, vis = 2) {
    gap = name == "screen" ? 0 : GAP;
    multmatrix(m) color(col) for (i = [0 : n - 1])
        translate([0, 0, gap + i * (seg + gap) + vis / 2]) linear_extrude(seg - vis) profile(name);
}

module tube_run(name, len, ext, m, col) {
    multmatrix(m) color(col) translate([0, 0, -ext]) linear_extrude(len + 2 * ext) tube2d(name);
}

module sill_member(col, tubes = false, vis = 2) {
    seg_run("sill", N_SILL, SEG_SILL, M_SILL, col, vis);
    if (tubes) tube_run("sill", W - 2 * F, SOCK, M_SILL, C_ALU);
    color(col) {
        corner_block("sill", "glazing", "CSL");
        translate([W, 0, 0]) corner_block("sill", "glazing", "CSR", mirrored = true);
    }
}

module jamb_members(col, tubes = false, vis = 2) {
    for (r = [false, true]) {
        seg_run("glazing", N_JAMB_LOWER, SEG_JAMB_LOWER, m_jamb(r, F), col, vis);
        seg_run("sash_rebate", N_JAMB_UPPER, SEG_JAMB_UPPER, m_jamb(r, TB + TRANSOM_W), col, vis);
        color(col) translate([r ? W : 0, 0, TB]) mirror([r ? 1 : 0, 0, 0]) jamb_node("JN");
        if (tubes) tube_run("glazing", H - 2 * F, SOCK, m_jamb(r, F), C_ALU);
    }
}

module head_member(col, tubes = false, vis = 2) {
    seg_run("sash_rebate", N_HEAD, SEG_HEAD, M_HEAD, col, vis);
    if (tubes) tube_run("sash_rebate", W - 2 * F, SOCK, M_HEAD, C_ALU);
    color(col) {
        translate([0, 0, H]) mirror([0, 0, 1]) corner_block("sash_rebate", "sash_rebate", "CH");
        translate([W, 0, H]) mirror([1, 0, 0]) mirror([0, 0, 1]) corner_block("sash_rebate", "sash_rebate", "CH");
    }
}

module frame_unit(col = C_FRAME, tubes = false, vis = 2) {
    sill_member(col, tubes, vis);
    jamb_members(col, tubes, vis);
    head_member(col, tubes, vis);
}

module cam_set(x, keeper = true) {
    multmatrix(m_cam(x)) {
        color("#d9692b") cam_base("CMB");
        color(C_HI) cam_handle("CMH");
        if (keeper) color("#b8432f") cam_keeper("KP");
    }
}

module transom_unit(col = C_TRANSOM, tubes = false, cams = true, vis = 2) {
    seg_run("transom", N_TRANSOM, SEG_TRANSOM, M_TRANSOM, col, vis);
    if (tubes) tube_run("transom", W - 2 * F, F - FRAME_BODY - SHOE_WALL - 1, M_TRANSOM, C_STEEL);
    color(col) for (s = [[1, 0], [-1, W]])
        translate([s[1], 0, TB]) mirror([s[0] < 0 ? 1 : 0, 0, 0])
            multmatrix([[0, 0, 1, FRAME_BODY], [0, 1, 0, 0], [-1, 0, 0, TRANSOM_W]]) transom_shoe("TSL", mirrored = true);
    if (cams) for (x = [CAM_AT, W - CAM_AT]) cam_set(x, false);
}

module sash_glass() {
    translate([SX0 + SASH_GLASS, GLASS_Y0, SZ0 + SASH_GLASS]) cube([SASH_GLASS_DIMS[0], GLASS_T, SASH_GLASS_DIMS[1]]);
}

module fixed_glass() {
    translate([GLASS_EDGE, GLASS_Y0, GLASS_EDGE]) cube([FIXED_GLASS[0], GLASS_T, FIXED_GLASS[1]]);
}

module sash_unit(col = C_SASH, tubes = false, glass = true, keepers = false, vis = 2) {
    S = SASH_W;
    for (t = [false, true]) seg_run("sash", N_SASH_HORIZONTAL, SEG_SASH_HORIZONTAL, m_sash_h(t), col, vis);
    for (r = [false, true]) seg_run("sash", N_SASH_VERTICAL, SEG_SASH_VERTICAL, m_sash_v(r), col, vis);
    if (tubes) {
        for (t = [false, true]) tube_run("sash", SASH[0] - 2 * S, SASH_SOCK, m_sash_h(t), C_ALU);
        for (r = [false, true]) tube_run("sash", SASH[1] - 2 * S, SASH_SOCK, m_sash_v(r), C_ALU);
    }
    color(col) {
        translate([SX0, 0, SZ0]) corner_block("sash", "sash", "CS");
        translate([SX0 + SASH[0], 0, SZ0]) mirror([1, 0, 0]) corner_block("sash", "sash", "CS");
        translate([SX0, 0, SZ0 + SASH[1]]) mirror([0, 0, 1]) corner_block("sash", "sash", "CS");
        translate([SX0 + SASH[0], 0, SZ0 + SASH[1]]) mirror([1, 0, 0]) mirror([0, 0, 1]) corner_block("sash", "sash", "CS");
    }
    if (glass) color(C_GLASS) sash_glass();
    if (keepers) for (x = [CAM_AT, W - CAM_AT]) multmatrix(m_cam(x)) color("#b8432f") cam_keeper("KP");
}

module screen_unit(col = C_SCREEN, tubes = false, mesh = true, vis = 2) {
    N = SCREEN_W;
    for (t = [false, true]) seg_run("screen", N_SCREEN_HORIZONTAL, SEG_SCREEN_HORIZONTAL, m_screen_h(t), col, vis);
    for (r = [false, true]) seg_run("screen", N_SCREEN_VERTICAL, SEG_SCREEN_VERTICAL, m_screen_v(r), col, vis);
    if (tubes) for (t = [false, true]) tube_run("screen", SCREEN[0] - 2 * N, SCREEN_SOCK, m_screen_h(t), C_ALU);
    color(col) translate([0, DEPTH, 0]) {
        translate([NX0, 0, NZ0]) corner_block("screen", "screen", "CN");
        translate([NX0 + SCREEN[0], 0, NZ0]) mirror([1, 0, 0]) corner_block("screen", "screen", "CN");
        translate([NX0, 0, NZ0 + SCREEN[1]]) mirror([0, 0, 1]) corner_block("screen", "screen", "CN");
        translate([NX0 + SCREEN[0], 0, NZ0 + SCREEN[1]]) mirror([1, 0, 0]) mirror([0, 0, 1]) corner_block("screen", "screen", "CN");
    }
    if (mesh) color("#8d959b")
        translate([NX0 + N - 6, DEPTH + SCREEN_DEPTH - 1, NZ0 + N - 6]) cube([SCREEN[0] - 2 * N + 12, 0.6, SCREEN[1] - 2 * N + 12]);
}
