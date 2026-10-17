// cad/profile.scad
include <generated/dims.scad>

EPS = 0.01;
function bead_seat_y() = GLASS_Y0 + GLASS_T + GASKET_T;
BEAD_SEAT_Y = bead_seat_y();

function is_mullion(name) = name == "mullion_glazing" || name == "mullion_sash";

function mirror_rect(r) = [MULLION_W - r[2], r[1], MULLION_W - r[0], r[3]];

function both_sides(rs) = concat(rs, [for (r = rs) mirror_rect(r)]);

function tube(name) =
    name == "transom" || is_mullion(name) ? TUBE_TRANSOM : name == "sash" ? TUBE_SASH : name == "screen" ? TUBE_SCREEN : TUBE_FRAME;

function pocket(name) = tube(name) + [2, 2] * TUBE_CLEAR;

function pocket_shift(name, core) = name == "sash_rebate" && !is_undef(core) ? VSLOT_SHIFT : 0;

function pocket_origin(name, core) =
    name == "transom" ? [TRANSOM_W / 2, DEPTH / 2] - pocket(name) / 2
  : is_mullion(name) ? [MULLION_W / 2, DEPTH / 2] - pocket(name) / 2
  : name == "sash" ? [SASH_BODY / 2, (SASH_Y0 + LIP_Y1) / 2] - pocket(name) / 2
  : name == "screen" ? [SCREEN_SHELL, (SCREEN_DEPTH - pocket(name)[1]) / 2]
  : [MIN_SHELL, (DEPTH - pocket(name)[1]) / 2 - pocket_shift(name, core)];

function pocket_rect(name, core) = concat(pocket_origin(name, core), pocket_origin(name, core) + pocket(name));

function sash_tube_y() = [pocket_rect("sash")[1] + TUBE_CLEAR, pocket_rect("sash")[3] - TUBE_CLEAR];

function stay_c_min() = FIN_Y1 + STAY_W / 2;

function stay_c_max() = sash_tube_y()[1] - MIN_SKIN;

function socket_depth(name) = name == "sash" ? SOCKET_SASH : name == "screen" ? SOCKET_SCREEN : SOCKET_FRAME;

function profile_min(name) = name == "sash" ? -FLANGE_L : 0;

function profile_width(name) =
    name == "transom" ? TRANSOM_W : is_mullion(name) ? MULLION_W : name == "sash" ? SASH_W : name == "screen" ? SCREEN_W : FRAME_W;

function is_frame_body(name) = name == "glazing" || name == "sash_rebate" || name == "sill";

function rebate_face(name) =
    name == "sill" ? FRAME_BODY - (bead_seat_y() - fix_y(name)) * tan(SILL_SLOPE_DEG) : FRAME_BODY;

function fix_y(name) = name == "sash_rebate" ? FIX_Y_IN : FIX_Y;

function fix_dz(name) = name == "sash_rebate" ? FIX_DZ : 0;

function counterbore_rect(name) =
    [rebate_face(name) - FIX_CB_L, fix_y(name) - FIX_CB_D / 2, rebate_face(name), fix_y(name) + FIX_CB_D / 2];

function rect_gap(a, b) = norm([max(0, a[0] - b[2], b[0] - a[2]), max(0, a[1] - b[3], b[1] - a[3])]);

module rect(x0, y0, x1, y1) { translate([x0, y0]) square([x1 - x0, y1 - y0]); }

module rect_r(r) { rect(r[0], r[1], r[2], r[3]); }

module key_tongue(d, h) {
    rect(0.2, KEY_THROAT + 0.2, h - 0.2, d - 0.2);
    rect(0.2, -2, h - KEY_LIP - 0.2, KEY_THROAT + 0.4);
}

function key_rects(e, dir) =
    dir < 0 ? [[e - KEY_D, KEY_Y, e - KEY_THROAT, KEY_Y + KEY_H], [e - KEY_THROAT - EPS, KEY_Y, e + EPS, KEY_Y + KEY_H - KEY_LIP]]
            : [[e + KEY_THROAT, KEY_Y, e + KEY_D, KEY_Y + KEY_H], [e - EPS, KEY_Y, e + KEY_THROAT + EPS, KEY_Y + KEY_H - KEY_LIP]];

function bead_key_rects(name) =
    name == "glazing" || name == "sill" ? key_rects(FRAME_BODY, -1)
  : name == "sash" ? key_rects(SASH_BODY, -1)
  : name == "transom" ? key_rects(TRANSOM_W / 2 - TRANSOM_HALF_BODY, 1)
  : name == "mullion_glazing" ? both_sides(key_rects(MULLION_W / 2 - MULLION_HALF_BODY, 1))
  : [];

function nose_key_rects() =
    [[NOSE_KEY_X, KEY_THROAT, NOSE_KEY_X + NOSE_KEY_W, NOSE_KEY_D], [NOSE_KEY_X, -EPS, NOSE_KEY_X + NOSE_KEY_W - KEY_LIP, KEY_THROAT + EPS]];

function kerf_rect(cx, y, dir, d = KERF_D) =
    dir > 0 ? [cx - KERF_W / 2, y - EPS, cx + KERF_W / 2, y + d] : [cx - KERF_W / 2, y - d, cx + KERF_W / 2, y + EPS];

function stop_floor(name) = name == "sash" ? SASH_Y0 : 0;

function glazing_kerf_rect(name) =
    name == "glazing" || name == "sill" ? kerf_rect(GLASS_EDGE + GASKET_IN, STOP_T, -1)
  : name == "transom" ? kerf_rect(TRANSOM_W / 2 - TRANSOM_GLASS - GASKET_IN, STOP_T, -1)
  : name == "mullion_glazing" ? kerf_rect(MULLION_W / 2 - TRANSOM_GLASS - GASKET_IN, STOP_T, -1)
  : name == "sash" ? kerf_rect(SASH_GLASS + GASKET_IN, STOP_T, -1, min(KERF_D, STOP_T - SASH_Y0 - MIN_SKIN))
  : undef;

function sash_side_e(name) =
    name == "sash_rebate" ? FRAME_BODY : name == "transom" ? TRANSOM_W / 2 + TRANSOM_HALF_BODY
  : name == "mullion_sash" ? MULLION_W / 2 + MULLION_HALF_BODY : undef;

function seal_kerf_rects(name) =
    let(e = sash_side_e(name))
    is_undef(e) ? [] : [kerf_rect(e + FIN_L / 2, FIN_Y0, 1), kerf_rect(e + SASH_GAP - LIP_L / 2, ISTOP_Y0, 1)];

function kerf_rects(name) =
    let(k = concat(is_undef(glazing_kerf_rect(name)) ? [] : [glazing_kerf_rect(name)], seal_kerf_rects(name)))
    is_mullion(name) ? both_sides(k) : k;

function mag_rect(name) =
    name == "sash_rebate" ? [FRAME_BODY + 2, DEPTH - MAG_D, FRAME_BODY + 2 + MAG_W, DEPTH + EPS]
  : name == "transom" ? [TRANSOM_MAG_X, DEPTH - MAG_D, TRANSOM_MAG_X + MAG_W, DEPTH + EPS]
  : name == "mullion_sash" ? let(e = sash_side_e(name)) [e + 2, DEPTH - MAG_D, e + 2 + MAG_W, DEPTH + EPS]
  : undef;

function mag_rects(name) = is_undef(mag_rect(name)) ? [] : is_mullion(name) ? both_sides([mag_rect(name)]) : [mag_rect(name)];

function chamber_rects(name, core) =
    let(w = CHAMBER_WALL, o = pocket_origin(name, core), p = pocket(name), keyed = len(bead_key_rects(name)) > 0)
    is_frame_body(name) ? concat(
        [[w, name == "sill" ? NOSE_KEY_D + w : w,
          name == "sash_rebate" ? FRAME_BODY - w : rebate_face(name) - FIX_CB_L - w, o[1] - w],
         [o[0] + p[0] + w, name == "sash_rebate" ? o[1] : max(o[1], fix_y(name) + FIX_CB_D / 2 + MIN_SKIN), FRAME_BODY - 2 * w, min(KEY_Y - w, o[1] + p[1])],
         [w, o[1] + p[1] + w, keyed ? FRAME_BODY - KEY_D - w : FRAME_BODY - w, DEPTH - w]],
        keyed ? [[w, KEY_Y + KEY_H + w, FRAME_BODY - w, DEPTH - w]] : [])
  : name == "sash" ? [[w, SASH_Y0 + w, SASH_BODY - w, o[1] - w], [w, o[1] + p[1] + w, SASH_BODY - KEY_D - w, LIP_Y1 - w]]
  : name == "screen" ? [[o[0] + p[0] + w, MAG_D + w, SCREEN_W - w, SCREEN_DEPTH - SPLINE_D - w]]
  : [];

module kerf(cx, y, dir = 1) { rect_r(kerf_rect(cx, y, dir)); }

module pocket_cut(name, core) { rect_r(pocket_rect(name, core)); }

module bead_key(name) { for (r = bead_key_rects(name)) rect_r(r); }

module sash_side_add(e, w) { for (r = sash_side_rects(e, w)) rect_r(r); }

function sash_side_rects(e, w) = [[e, FIN_Y0, e + FIN_L, FIN_Y1], [e, ISTOP_Y0, e + w, DEPTH]];

function base_rects(name) =
    let(fb = FRAME_BODY, tl = TRANSOM_W / 2 - TRANSOM_HALF_BODY, th = TRANSOM_W / 2 + TRANSOM_HALF_BODY,
        ml = MULLION_W / 2 - MULLION_HALF_BODY, mh = MULLION_W / 2 + MULLION_HALF_BODY)
    name == "glazing" ? [[0, 0, fb, DEPTH], [fb, 0, FRAME_W, STOP_T]]
  : name == "sash_rebate" ? concat([[0, 0, fb, DEPTH]], sash_side_rects(fb, FRAME_W - fb))
  : name == "transom" ? concat([[tl, 0, th, DEPTH], [0, 0, tl, STOP_T]], sash_side_rects(th, TRANSOM_W - th))
  : name == "sash" ? [[0, SASH_Y0, SASH_BODY, LIP_Y1], [-FLANGE_L, SASH_Y0, 0, FLANGE_Y1], [-LIP_L, LIP_Y0, 0, LIP_Y1],
                      [SASH_BODY, SASH_Y0, SASH_W, STOP_T]]
  : name == "screen" ? [[0, 0, SCREEN_W, SCREEN_DEPTH]]
  : name == "mullion_glazing" ? [[ml, 0, mh, DEPTH], [0, 0, ml, STOP_T], [mh, 0, MULLION_W, STOP_T]]
  : name == "mullion_sash" ? let(s = sash_side_rects(mh, MULLION_W - mh)) concat([[ml, 0, mh, DEPTH]], s, [for (r = s) mirror_rect(r)])
  : [];

function sill_points() =
    let(s = tan(SILL_SLOPE_DEG))
    [[0, 0], [FRAME_W, 0], [FRAME_W - STOP_T * s, STOP_T], [FRAME_BODY - (BEAD_SEAT_Y - STOP_T) * s, STOP_T],
     [FRAME_BODY, BEAD_SEAT_Y], [FRAME_BODY, DEPTH], [0, DEPTH]];

module sill_body() { polygon(sill_points()); }

function in_rects(q, rs) = len([for (r = rs) if (q[0] > r[0] && q[0] < r[2] && q[1] > r[1] && q[1] < r[3]) 1]) > 0;

function rect_convex(rs) =
    [for (r = rs, p = [[r[0], r[1]], [r[2], r[1]], [r[0], r[3]], [r[2], r[3]]])
        let(q = [for (sx = [-1, 1], sy = [-1, 1]) if (in_rects(p + 0.01 * [sx, sy], rs)) [sx, sy]])
        if (len(q) == 1) [p, [q[0][0], 0], [0, q[0][1]]]];

function unit(v) = v / norm(v);

function poly_convex(pts) =
    let(n = len(pts))
    [for (i = [0 : n - 1]) let(a = pts[(i + n - 1) % n], p = pts[i], b = pts[(i + 1) % n],
                                u = p - a, v = b - p)
        if (u[0] * v[1] - u[1] * v[0] > 1e-9) [p, unit(a - p), unit(b - p)]];

function convex_corners(name) = name == "sill" ? poly_convex(sill_points()) : rect_convex(base_rects(name));

function sharp_corners(name) =
    let(tl = TRANSOM_W / 2 - TRANSOM_HALF_BODY, th = TRANSOM_W / 2 + TRANSOM_HALF_BODY,
        ml = MULLION_W / 2 - MULLION_HALF_BODY, mh = MULLION_W / 2 + MULLION_HALF_BODY)
    name == "sash_rebate" ? [[FRAME_BODY + FIN_L, FIN_Y0], [FRAME_W, DEPTH]]
  : name == "transom" ? [[th + FIN_L, FIN_Y0], [tl, DEPTH]]
  : name == "mullion_sash" ? [[mh + FIN_L, FIN_Y0], [ml - FIN_L, FIN_Y0], [MULLION_W, DEPTH], [0, DEPTH]]
  : [];

function node_sharp(r, names) =
    [for (p = [[r[0], r[1]], [r[2], r[1]], [r[2], r[3]], [r[0], r[3]]])
        if (len([for (n = names, c = convex_corners(n))
                 if (norm(c[0] - p) < 1e-6 && len([for (s = sharp_corners(n)) if (norm(s - p) < 1e-6) 1]) == 0) 1]) == 0) p];

function soft_arc(c, steps = 8) =
    let(p = c[0], u = c[1], v = c[2], phi = acos(u * v), m = unit(u + v),
        ctr = p + m * EDGE_R / sin(phi / 2), ta = p + u * EDGE_R / tan(phi / 2), tb = p + v * EDGE_R / tan(phi / 2),
        a0 = atan2((ta - ctr)[1], (ta - ctr)[0]), a1 = atan2((tb - ctr)[1], (tb - ctr)[0]),
        d0 = a1 - a0, da = d0 > 180 ? d0 - 360 : d0 < -180 ? d0 + 360 : d0)
    [for (k = [0 : steps]) ctr + EDGE_R * [cos(a0 + da * k / steps), sin(a0 + da * k / steps)]];

module soften(r = EDGE_R) { offset(r = r, $fn = 32) offset(delta = -r) children(); }

module profile_base(name) {
    if (name == "sill") sill_body();
    else {
        assert(len(base_rects(name)) > 0, str("unknown profile ", name));
        for (r = base_rects(name)) rect_r(r);
    }
}

module soft_rect(r, sharp = [], rad = EDGE_R) {
    soften(rad) rect_r(r);
    for (c = sharp) intersection() {
        rect_r(r);
        translate(c - [rad, rad] * 1.5) square(3 * rad);
    }
}

module bevel_ends(len, bottom = true, top = true) {
    n = round(JOINT_BEVEL / BEVEL_STEP);
    for (i = [0 : 1 : n - 1]) {
        k = JOINT_BEVEL - i * BEVEL_STEP;
        for (z = concat(bottom ? [i * BEVEL_STEP - EPS] : [], top ? [len - (i + 1) * BEVEL_STEP] : []))
            translate([0, 0, z]) linear_extrude(BEVEL_STEP + EPS) difference() {
                offset(delta = 1) children();
                offset(delta = -k) children();
            }
    }
}

module fin_stub(b) {
    translate([b[0], 0, 0]) rotate([90, 0, 90]) linear_extrude(b[2] - b[0]) union() {
        soften() rect(b[1], b[4], b[3], b[5]);
        rect(b[1], b[4], b[3] - EDGE_R, b[5]);
        rect(b[1], b[4], b[3], b[5] - EDGE_R);
    }
}

module soft_base(name) {
    soften() profile_base(name);
    for (c = sharp_corners(name)) intersection() {
        profile_base(name);
        translate(c - [EDGE_R, EDGE_R] * 1.5) square(3 * EDGE_R);
    }
}

function screen_cut_rects() =
    [[SCREEN_OVERLAP + 2, -EPS, SCREEN_OVERLAP + 2 + MAG_W, MAG_D],
     [SCREEN_W - 8, SCREEN_DEPTH - SPLINE_D, SCREEN_W - 8 + SPLINE_W, SCREEN_DEPTH + EPS]];

function cut_rects(name, core) =
    concat([pocket_rect(name, core)], bead_key_rects(name), kerf_rects(name), mag_rects(name),
           name == "sill" ? nose_key_rects() : [], name == "screen" ? screen_cut_rects() : [], chamber_rects(name, core));

module chambers(name, core) { for (r = chamber_rects(name, core)) rect_r(r); }

module profile_solid(name, pocket = true, core) {
    difference() {
        soft_base(name);
        if (pocket) pocket_cut(name, core);
        bead_key(name);
        for (r = kerf_rects(name)) rect_r(r);
        for (r = mag_rects(name)) rect_r(r);
        if (name == "sill") for (r = nose_key_rects()) rect_r(r);
        if (name == "screen") for (r = screen_cut_rects()) rect_r(r);
    }
}

function bevel_fill(name) =
    let(g = glazing_kerf_rect(name))
    is_undef(g) || g[1] - stop_floor(name) - 2 * JOINT_BEVEL >= 0.6 ? [] : [for (r = kerf_rects(name)) if (r[1] == g[1] && r[3] == g[3]) r];

module bevel_outline(name, core) {
    union() {
        profile_solid(name, false, core);
        for (r = bevel_fill(name)) rect_r(r);
    }
}

module profile(name, pocket = true, core) {
    difference() {
        profile_solid(name, pocket, core);
        chambers(name, core);
    }
}

function core_box(name) =
    is_frame_body(name) ? [0, 0, FRAME_BODY, DEPTH]
  : name == "transom" ? [TRANSOM_W / 2 - TRANSOM_HALF_BODY, 0, TRANSOM_W / 2 + TRANSOM_HALF_BODY, DEPTH]
  : is_mullion(name) ? [MULLION_W / 2 - MULLION_HALF_BODY, 0, MULLION_W / 2 + MULLION_HALF_BODY, DEPTH]
  : name == "sash" ? [0, SASH_Y0, SASH_BODY, LIP_Y1]
  : undef;

function has_cord(name) = !is_undef(core_box(name));

module cord_ring(name, core) {
    if (has_cord(name)) difference() {
        offset(delta = -CORD_INSET) intersection() { profile_solid(name, false); rect_r(core_box(name)); }
        offset(delta = -CORD_INSET - CORD_D) intersection() { profile_solid(name, false); rect_r(core_box(name)); }
        offset(delta = MIN_SKIN) pocket_cut(name, core);
    }
}

function pane_thickness(glazing, pane_t) = glazing == "twinwall" ? TWINWALL_T : is_undef(pane_t) ? GLASS_T : pane_t;

function bead_y0(glazing, pane_t) = BEAD_SEAT_Y - (GLASS_T - pane_thickness(glazing, pane_t));

function bead_label_y(glazing, pane_t) = (bead_y0(glazing, pane_t) + KEY_Y) / 2;

function bead_chamber(glazing, pane_t) =
    let(y0 = bead_y0(glazing, pane_t), top = BEAD_SEAT_Y + BEAD_T, r = [KEY_D, y0 + KERF_D + 2, BEAD_W - CHAMBER_WALL, top - CHAMBER_WALL])
    r[3] - r[1] >= CHAMBER_WALL ? r : undef;

module bead_profile(glazing, pane_t) {
    assert(glazing == "igu" || glazing == "acrylic" || glazing == "twinwall", str("unknown glazing ", glazing));
    y0 = bead_y0(glazing, pane_t);
    top = BEAD_SEAT_Y + BEAD_T;
    difference() {
        union() {
            soften() rect(0, y0, BEAD_W, top);
            rect(0, y0, BEAD_W - EDGE_R, top);
            rect(0, y0, BEAD_W, top - EDGE_R);
            translate([0, KEY_Y]) rotate(90) key_tongue(KEY_D, KEY_H);
        }
        kerf(GLASS_CLEAR + GASKET_IN, y0, 1);
        if (!is_undef(bead_chamber(glazing, pane_t))) rect_r(bead_chamber(glazing, pane_t));
    }
}
