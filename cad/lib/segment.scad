// cad/lib/segment.scad
include <../generated/dims.scad>
use <../profile.scad>
use <emboss.scad>

EPS = 0.01;

function is_perimeter(name) = name == "glazing" || name == "sash_rebate" || name == "sill";

function top_face(name) = name == "sash" ? LIP_Y1 : name == "screen" ? SCREEN_DEPTH : DEPTH;

function boss_x(name) =
    name == "sash_rebate" ? HINGE_BOSS_X : name == "transom" ? CAM_BOSS_X : name == "sash" ? SASH_BODY / 2 : undef;

function boss_offsets(dz) = dz == 0 ? [0] : [-dz, dz];

function boss_dz_min(name, core) =
    BOSS_PITCH / 2 + max((INSERT_M4_D + MIN_SKIN) / 2,
        fix_dz(name) / 2 + sqrt(max(0, pow(csk_d(name, core) / 2 + INSERT_M4_D / 2 + MIN_SKIN, 2) - pow(boss_x(name) - screw_x(name, core), 2))));

function boss_dz_max(len) = len / 2 - END_CAP - MIN_SKIN - INSERT_M4_D / 2 - BOSS_PITCH / 2;

function screw_x(name, core) =
    name == "transom" ? (core == "vslot" ? VSLOT_TRANSOM_X : TRANSOM_SCREW_X) : pocket_origin(name, core)[0] + pocket(name)[0] / 2;

function tnut(name, core) = core == "vslot" && name != "transom";

function csk_d(name, core) = tnut(name, core) ? VSLOT_CSK_D : CSK_D;

function column_d(name, core) = tnut(name, core) ? VSLOT_CSK_D + 4 : 10;

function vslot_shell(name) = top_face(name) - pocket_rect(name, "vslot")[3];

function vslot_tip_target() = (VSLOT_TIP[0] + VSLOT_TIP[1]) / 2;

function vslot_screw_l(name) = max([for (l = VSLOT_M5_L) if (l <= vslot_shell(name) + vslot_tip_target() + 1e-9) l]);

function vslot_seat(name) = vslot_shell(name) + vslot_tip_target() - vslot_screw_l(name);

function label_at(name) =
    name == "transom" ? [TRANSOM_W / 2 - TRANSOM_HALF_BODY, GLASS_Y0 + 11]
  : name == "mullion_glazing" ? [MULLION_W / 2 - MULLION_HALF_BODY, GLASS_Y0 + 11]
  : name == "mullion_sash" ? [MULLION_W / 2 - MULLION_HALF_BODY, (FIN_Y1 + LIP_Y0) / 2]
  : name == "sash" ? [0, (FLANGE_Y1 + LIP_Y0) / 2]
  : name == "screen" ? [0, SCREEN_DEPTH / 2]
  : [0, DEPTH / 2];

function weep_rect(name) =
    name == "sill" ? let(f = FRAME_BODY - (bead_seat_y() - STOP_T) * tan(SILL_SLOPE_DEG)) [f - 1, -1, f - 1 + WEEP_H, STOP_T + 1]
  : name == "transom" ? let(th = TRANSOM_W / 2 + TRANSOM_HALF_BODY) [th - 0.5, FIN_Y0 - 1, th + WEEP_H, FIN_Y1 + 1]
  : name == "sash" ? [SASH_BODY - 1, SASH_Y0 - 1, SASH_BODY - 1 + WEEP_H, STOP_T + 1]
  : undef;

module end_groove(name, core) { linear_extrude(CORD_D / 2 + EPS) cord_ring(name, core); }

module end_cap(name, pocket = true, core) { linear_extrude(END_CAP) profile_solid(name, pocket, core); }

module tube_screw(name, z, top = undef, core) {
    t = tnut(name, core);
    assert(!t || is_undef(top), str(name, ": a T-nut screw takes no seat override"));
    p = pocket_rect(name, core);
    d = t ? VSLOT_SCREW_D : TUBE_SCREW_D;
    k = csk_d(name, core);
    cone = t ? (k - d) / 2 : 2.2;
    h = (t ? top_face(name) - vslot_seat(name) : is_undef(top) ? top_face(name) : top) - p[3];
    translate([screw_x(name, core), p[3] - EPS, z]) rotate([-90, 0, 0]) {
        cylinder(d = d, h = top_face(name) - p[3] + 1, $fn = 24);
        translate([0, 0, h - cone]) cylinder(d1 = d, d2 = k, h = cone + 2 * EPS, $fn = 32);
        translate([0, 0, h]) cylinder(d = k, h = top_face(name) - p[3] - h + 1, $fn = 32);
    }
}

module screw_column(name, z, core) {
    p = pocket_rect(name, core);
    translate([screw_x(name, core), p[3], z]) rotate([-90, 0, 0]) cylinder(d = column_d(name, core), h = top_face(name) - p[3], $fn = 32);
}

module fixing_hole(name, z) {
    translate([-1, fix_y(name), z]) rotate([0, 90, 0]) cylinder(d = FIX_D, h = FRAME_W + 2, $fn = 24);
    translate([rebate_face(name) - FIX_CB_L, fix_y(name), z]) rotate([0, 90, 0])
        cylinder(d = FIX_CB_D, h = FIX_CB_L + 1, $fn = 32);
}

module fixing_column(name, z) {
    translate([-1, fix_y(name), z]) rotate([0, 90, 0]) cylinder(d = FIX_BOSS_D, h = FRAME_BODY + 1, $fn = 40);
}

module boss_columns(name, z, core) {
    p = pocket_rect(name, core);
    for (dz = [-BOSS_PITCH / 2, BOSS_PITCH / 2])
        translate([boss_x(name), p[3], z + dz]) rotate([-90, 0, 0])
            cylinder(d = INSERT_M4_D + 4, h = top_face(name) - p[3], $fn = 32);
}

module insert_holes(name, z) {
    for (dz = [-BOSS_PITCH / 2, BOSS_PITCH / 2])
        translate([boss_x(name), top_face(name) + EPS, z + dz]) rotate([90, 0, 0])
            cylinder(d = INSERT_M4_D, h = INSERT_M4_L, $fn = 24);
}

module local_solids(name, z, bosses = false, boss_dz = 0, core) {
    screw_column(name, z - fix_dz(name) / 2, core);
    if (is_perimeter(name)) fixing_column(name, z + fix_dz(name) / 2);
    if (bosses) for (c = boss_offsets(boss_dz)) boss_columns(name, z + c, core);
}

module local_cuts(name, z, bosses = false, boss_dz = 0, core) {
    tube_screw(name, z - fix_dz(name) / 2, core = core);
    if (is_perimeter(name)) fixing_hole(name, z + fix_dz(name) / 2);
    if (bosses) for (c = boss_offsets(boss_dz)) insert_holes(name, z + c);
}

module segment(name, len, code, weep = false, bosses = false, boss_dz = 0, core) {
    assert(len > 0 && len <= MAX_SEG, str(code, ": length ", len, " outside 0..", MAX_SEG));
    assert(!weep || name == "sill" || name == "transom" || name == "sash", str(code, ": no weep on ", name));
    assert(!bosses || boss_x(name) != undef, str(code, ": no bosses on ", name));
    if (boss_dz != 0)
        assert(bosses && abs(boss_dz) >= boss_dz_min(name, core) && abs(boss_dz) <= boss_dz_max(len),
               str(code, ": boss offset ", boss_dz, " outside ", boss_dz_min(name, core), "..", boss_dz_max(len)));
    difference() {
        union() {
            linear_extrude(len) profile(name, core = core);
            for (z = [0, len - END_CAP]) translate([0, 0, z]) end_cap(name, core = core);
            intersection() {
                linear_extrude(len) profile_solid(name, core = core);
                local_solids(name, len / 2, bosses, abs(boss_dz), core);
            }
        }
        for (z = [-EPS, len - CORD_D / 2]) translate([0, 0, z]) end_groove(name, core);
        bevel_ends(len) bevel_outline(name, core);
        local_cuts(name, len / 2, bosses, abs(boss_dz), core);
        if (weep) translate([0, 0, len / 2 - WEEP_W / 2]) linear_extrude(WEEP_W) rect_r(weep_rect(name));
        engrave(code, label_at(name), len / 2);
    }
}
