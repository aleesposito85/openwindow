#!/usr/bin/env python3
"""OpenWindow layout: member lengths, segment splits, glass sizes, tube cuts, structural checks."""
import json
import math
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
D = json.loads((ROOT / "cad" / "dims.json").read_text())

WIND_KPA = 0.7
GLAZING_KG_M2 = {"igu": 20.0, "acrylic": 9.5, "twinwall": 2.7}
CORES = {
    "alu10": (69000, 10, 10, 1.0, 0.10),
    "alu20": (69000, 20, 20, 1.6, 0.32),
    "alu25": (69000, 25, 25, 1.6, 0.41),
    "steel40x20": (200000, 20, 40, 1.6, 1.43),
    "alu50x25": (69000, 25, 50, 1.6, 0.62),
    "steel50x25": (200000, 25, 50, 1.6, 1.80),
    "vslot2020": (69000, 20, 20, None, 0.456),
    "vslot2020x2": (69000, 20, 40, None, 0.912),
}
VSLOT = "vslot2020"
VSLOT_PAIR = "vslot2020x2"
SECTION_I = {VSLOT: 6890.0, VSLOT_PAIR: 13780.0}
VSLOT_STOCK = 1000
VSLOT_STOCK_RANGE = (300, 6000)
SAW_KERF = 2.0
JOIN_END = 15.0
JOIN_NUT = 15.0
FRAME_CORE = "alu20"
TRANSOM_CORE = "steel40x20"
STAYS = [(200, 12.0), (250, 17.0), (300, 20.0), (400, 30.0), (500, 35.0)]
STAY_RATIO = 0.75
SASH_FRAME_KG_M = 0.75
CORD_PROFILES = {"sash_rebate", "sill", "glazing", "transom", "sash", "mullion_glazing", "mullion_sash"}
MIN_AWNING = 150.0
MIN_FIXED = 150.0
DEFAULT_BED = [256, 256, 256]
WIDE_SCREEN = 1000.0
MIN_BAY = 150.0
ACRYLIC_T_RANGE = (2, 6)
ACRYLIC_GAP_RANGE = (8, 16)
PANE_RANGE = (200, 3000)


def is_size(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)


def max_seg(bed):
    if not (isinstance(bed, (list, tuple)) and len(bed) == 3 and all(is_size(v) for v in bed)):
        raise ValueError(f"bed must be a list of three finite numbers in mm, got {bed!r}")
    seg = math.floor((min(bed[2], max(bed[0], bed[1])) - D["BED_MARGIN"]) * 100 + 1e-6) / 100
    if min(bed) <= D["BED_MARGIN"] or seg <= 0:
        raise ValueError(f"bed must be three sizes over {D['BED_MARGIN']:g} mm, got {bed}")
    return seg


def hinge_count(screen_w):
    return 3 if screen_w > WIDE_SCREEN else 2


def split(length, gap=0.0, limit=None, min_n=1):
    limit = max_seg(DEFAULT_BED) if limit is None else limit
    if length <= 0:
        raise ValueError(f"member length must be positive, got {length}")
    n = max(min_n, math.ceil((length - gap) / (limit + gap) - 1e-9))
    seg = (length - (n + 1) * gap) / n
    if seg <= 0:
        raise ValueError(f"member length {length} leaves no room for {n + 1} joint gaps of {gap}")
    return n, round(seg, 2)


def keeper_dz_min(csk=None):
    return D["BOSS_PITCH"] / 2 + (D["CSK_D"] if csk is None else csk) / 2 + D["INSERT_M4_D"] / 2 + D["MIN_SKIN"]


def keeper_dz_max(seg):
    return seg / 2 - D["END_CAP"] - D["MIN_SKIN"] - D["INSERT_M4_D"] / 2 - D["BOSS_PITCH"] / 2


def inertia(core):
    if core in SECTION_I:
        return SECTION_I[core]
    _, b, d, t, _ = CORES[core]
    return (b * d ** 3 - (b - 2 * t) * (d - 2 * t) ** 3) / 12.0


def deflection(core, span, trib_h):
    w = WIND_KPA / 1000.0 * trib_h
    return 5 * w * span ** 4 / (384 * CORES[core][0] * inertia(core))


def bay_width(horiz, n):
    return (horiz - (n - 1) * D["MULLION_W"]) / n


def max_bays(horiz):
    n = 1
    while bay_width(horiz, n + 1) >= MIN_BAY:
        n += 1
    return n


MULLION_ALIGN = (("FRAME_BODY", "MULLION_HALF_BODY"), ("GLASS_EDGE", "TRANSOM_GLASS"))


def check_mullion_dims():
    for frame_key, mullion_key in MULLION_ALIGN:
        a = D["FRAME_W"] - D[frame_key]
        b = D["MULLION_W"] / 2 - D[mullion_key]
        if not math.isclose(a, b, abs_tol=1e-9):
            raise ValueError(f"mullion dims: FRAME_W - {frame_key} must equal MULLION_W / 2 - {mullion_key} "
                             f"in cad/dims.json, got {a:g} and {b:g}")


def fits(pane, sheet):
    return all(a <= b for a, b in zip(sorted(pane), sorted(sheet)))


def beam_deflection(core, span, loads):
    ei = CORES[core][0] * inertia(core)

    def at(x):
        d = 0.0
        for a, f in loads:
            b = span - a
            d += f * b * x * (span ** 2 - b ** 2 - x ** 2) if x <= a else f * a * (span - x) * (span ** 2 - a ** 2 - (span - x) ** 2)
        return d / (6 * span * ei)

    return max(at(span * k / 100) for k in range(101))


def strip_loads(x0, x1, w, parts=50):
    step = (x1 - x0) / parts
    return [(x0 + (k + 0.5) * step, w * step) for k in range(parts)]


def bay_layout(p, horiz, panes_at):
    limit = p.get("max_pane")
    top = max_bays(horiz)
    auto = 1
    if "max_pane" in p:
        lo, hi = PANE_RANGE
        if not (isinstance(limit, (list, tuple)) and len(limit) == 2 and all(is_size(v) and lo <= v <= hi for v in limit)):
            raise ValueError(f"max_pane must be two sizes, {lo}-{hi} mm each, got {limit!r}")
        auto = next((n for n in range(1, top + 1) if all(fits(pane, limit) for pane in panes_at(n).values())), None)
        if auto is None:
            sheet = " x ".join(f"{v:g}" for v in limit)
            bad = {k: v for k, v in panes_at(top).items() if not fits(v, limit)}
            tall = [k for k, (pw, ph) in bad.items() if ph > min(limit)]
            if tall:
                fix = "use a taller awning_h or a shorter opening" if tall[0] == "fixed" else "use a shorter awning_h"
                raise ValueError(f"max_pane: the {bad[tall[0]][1]} mm tall {tall[0]} pane does not fit a {sheet} mm sheet "
                                 f"at any bay count; that needs a second horizontal transom, which is out of scope: {fix}")
            k, (pw, ph) = next(iter(bad.items()))
            raise ValueError(f"max_pane: at {top} bay{'s' if top > 1 else ''}, the most this opening takes "
                             f"({MIN_BAY:g} mm each at least), the {k} pane is still {pw} x {ph} mm, too big for a {sheet} mm sheet")
    n = p.get("bays", auto)
    if type(n) is not int or n < 1:
        raise ValueError(f"bays must be a whole number of at least 1, got {n!r}")
    if n < auto:
        raise ValueError(f"bays must be at least {auto} for a {' x '.join(f'{v:g}' for v in limit)} mm max_pane, got {n}")
    if n > top:
        raise ValueError(f"bays must be at most {top} for this opening (bays at least {MIN_BAY:g} mm wide), got {n}")
    pitch = (horiz + D["MULLION_W"]) / n
    mullions = [D["FRAME_W"] - D["MULLION_W"] / 2 + i * pitch for i in range(1, n)]
    return n, auto, pitch, mullions


def member(name, length, profile, core, qty, limit=None, min_n=1):
    gap = D["JOINT_GAP"] if profile in CORD_PROFILES else 0.0
    n, seg = split(length, gap, limit, min_n)
    return {"name": name, "length": round(length, 2), "profile": profile, "core": core,
            "qty": qty, "n": n, "seg": seg, "gap": gap}


def vslot_stock(p):
    if "core" not in p:
        if "vslot_stock" in p:
            raise ValueError("vslot_stock only applies with core vslot")
        return None
    if p["core"] != "vslot":
        raise ValueError(f"core must be vslot, got {p['core']!r}")
    stock = p.get("vslot_stock", VSLOT_STOCK)
    lo, hi = VSLOT_STOCK_RANGE
    if not (is_size(stock) and lo <= stock <= hi):
        raise ValueError(f"vslot_stock must be a number from {lo} to {hi} mm, got {stock!r}")
    return stock


def pocket_top(profile, shifted=False):
    clear = D["TUBE_CLEAR"]
    if profile == "sash":
        return (D["SASH_Y0"] + D["LIP_Y1"]) / 2 + D["TUBE_SASH"][1] / 2 + clear
    if profile in ("transom", "mullion_glazing", "mullion_sash"):
        return D["DEPTH"] / 2 + D["TUBE_TRANSOM"][1] / 2 + clear
    shift = D["VSLOT_SHIFT"] if shifted and profile == "sash_rebate" else 0
    return (D["DEPTH"] + D["TUBE_FRAME"][1]) / 2 + clear - shift


def m5_length(profile):
    face = D["LIP_Y1"] if profile == "sash" else D["DEPTH"]
    reach = face - pocket_top(profile, shifted=True) + sum(D["VSLOT_TIP"]) / 2
    return max(n for n in D["VSLOT_M5_L"] if n <= reach + 1e-9)


def join_plan(total, segments, held, stock):
    cands = sorted(q for s0, s1, c, nut in segments for q in (c - (s1 - s0) / 4, c + (s1 - s0) / 4)
                   if min(q - s0, s1 - q) >= JOIN_END and abs(q - c) - nut / 2 >= JOIN_NUT)
    joins, start = [], 0.0
    while total - start > stock + 1e-9:
        ok = [q for q in cands if start < q <= start + stock + 1e-9 and any(start < h < q for h in held)]
        if not ok:
            return None
        start = max(ok)
        joins.append(start)
    return joins


def cut_plan(cuts, stock):
    bins = []
    for label, length in sorted(cuts, key=lambda c: -c[1]):
        for b in bins:
            if b["used"] + SAW_KERF + length <= stock + 1e-9:
                b["cuts"].append((label, length))
                b["used"] += SAW_KERF + length
                break
        else:
            bins.append({"cuts": [(label, length)], "used": length})
    return [{"cuts": b["cuts"], "offcut": round(stock - b["used"], 1)} for b in bins]


def acrylic_sandwich(p):
    keys = [k for k in ("acrylic_t", "acrylic_gap") if k in p]
    for k in keys:
        if p["glazing"] != "acrylic":
            raise ValueError(f"{k} only applies to acrylic glazing, got glazing {p['glazing']}")
    if p["glazing"] != "acrylic":
        return None
    default = (D["ACRYLIC_T"], D["GLASS_T"] - 2 * D["ACRYLIC_T"])
    t = p.get("acrylic_t", default[0])
    gap = p.get("acrylic_gap", default[1])
    for k, v, (lo, hi) in (("acrylic_t", t, ACRYLIC_T_RANGE), ("acrylic_gap", gap, ACRYLIC_GAP_RANGE)):
        if not (isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v) and lo <= v <= hi):
            raise ValueError(f"{k} must be a number from {lo} to {hi} mm, got {v}")
    total = 2 * t + gap
    if total > D["GLASS_T"]:
        raise ValueError(f"acrylic_t: 2 x {t:g} + {gap:g} = {total:g} mm does not fit the {D['GLASS_T']:g} mm glazing pocket")
    return {"t": t, "gap": gap, "custom": (t, gap) != default}


def vslot_cores(stock, members, tubes, transom_delta, limit, lower, a, pitch, run, bays, sock, clear):
    F, T, MW, gap = D["FRAME_W"], D["TRANSOM_W"], D["MULLION_W"], D["JOINT_GAP"]
    m = {x["name"]: x for x in members}
    t = {x["member"]: x for x in tubes}
    fallbacks, joins, out = [], {}, []

    def longer(core, label, length):
        return f"{core} {label}: {length:g} mm is longer than the {stock:g} mm V-slot pieces"

    def runs(name, n_runs, nut):
        mem = m[name]
        segs, held = [], [sock / 2]
        for b in range(n_runs):
            x0 = sock + b * (run + MW)
            for k in range(mem["n"]):
                s0 = x0 + gap + k * (mem["seg"] + gap)
                segs.append((s0, s0 + mem["seg"], s0 + mem["seg"] / 2, nut))
                held.append(s0 + mem["seg"] / 2)
            if b < n_runs - 1:
                held.append(x0 + run + MW / 2)
        return segs, held

    def joined(name, label, total, segs, held, qty):
        js = join_plan(total, segs, held, stock)
        if js is None:
            m[name]["core"] = "alu20"
            fallbacks.append(f"alu20 {label}: {stock:g} mm V-slot pieces can't be joined inside its {m[name]['seg']:g} mm segments")
            out.append({"member": label, "core": "alu20", "length": total, "qty": qty})
            return
        m[name]["core"] = VSLOT
        joins[label] = [{"at": round(j, 1), "segment": next(i + 1 for i, s in enumerate(segs) if s[0] < j < s[1])}
                        for j in js]
        ends = [0.0] + js + [total]
        k = len(ends) - 1
        for i in range(k):
            out.append({"member": label if k == 1 else f"{label} {i + 1}/{k}", "core": VSLOT,
                        "length": ends[i + 1] - ends[i], "qty": qty})

    def single(name, label, length, qty, fallback):
        if length <= stock:
            m[name]["core"] = VSLOT
            out.append({"member": label, "core": VSLOT, "length": length, "qty": qty})
        else:
            m[name]["core"] = fallback
            fallbacks.append(longer(fallback, label, length))
            out.append({"member": label, "core": fallback, "length": length, "qty": qty})

    horiz_total = t["head"]["length"]
    for name in ("head", "sill"):
        segs, held = runs(name, bays, D["FIX_DZ"] if name == "head" else 0.0)
        joined(name, name, horiz_total, segs, held + [horiz_total - sock / 2], 1)
    lower_total = lower + T + sock - clear
    segs, held = runs("jamb_lower", 1, 0.0)
    joined("jamb_lower", "jamb_lower", lower_total, segs, held + [lower + T / 2 + sock], 2)
    single("jamb_upper", "jamb_upper", a + sock - clear, 2, "alu20")

    tl = t["transom"]["length"]
    pair_delta = transom_delta(VSLOT_PAIR)
    if tl <= stock and pair_delta <= limit:
        m["transom"]["core"] = VSLOT_PAIR
        out.append({"member": "transom", "core": VSLOT, "length": tl, "qty": 2})
    else:
        why = [f"{tl:g} mm is longer than the {stock:g} mm V-slot pieces"] if tl > stock else []
        if pair_delta > limit:
            why.append(f"a V-slot pair would deflect {pair_delta:.1f} mm (limit {limit:.1f} mm)")
        m["transom"]["core"] = "steel40x20"
        fallbacks.append(f"steel transom: {', and '.join(why)}")
        out.append(dict(t["transom"]))

    if bays > 1:
        for stub, span in (("lower", lower), ("upper", a)):
            name = f"mullion_{stub}"
            length = t[name]["length"]
            d = deflection(VSLOT_PAIR, span, pitch)
            if length <= stock and d <= span / 175:
                m[name]["core"] = VSLOT_PAIR
                out.append({"member": name, "core": VSLOT, "length": length, "qty": 2 * (bays - 1)})
                continue
            why = [f"{length:g} mm is longer than the {stock:g} mm V-slot pieces"] if length > stock else []
            if d > span / 175:
                why.append(f"a V-slot pair would deflect {d:.1f} mm over {span:g} mm (limit {span / 175:.1f} mm)")
            m[name]["core"] = "steel40x20"
            fallbacks.append(f"steel {stub} mullion: {', and '.join(why)}")
            out.append(dict(t[name]))

    for name in ("sash_horizontal", "sash_vertical"):
        single(name, name, t[name]["length"], t[name]["qty"], "alu20")
    out += [x for x in tubes if x["member"].startswith("screen")]
    for x in out:
        x["length"] = round(x["length"], 1)
    tubes[:] = out
    cuts = [(x["member"], x["length"]) for x in out if x["core"] == VSLOT for _ in range(x["qty"])]
    return {"stock": stock, "joins": joins, "fallbacks": fallbacks, "plan": cut_plan(cuts, stock)}


def layout(p):
    if p["glazing"] not in GLAZING_KG_M2:
        raise ValueError(f"glazing must be one of {sorted(GLAZING_KG_M2)}, got {p['glazing']}")
    bed = p.get("bed", DEFAULT_BED)
    seg_max = max_seg(bed)
    has_screen = p.get("screen", True)
    if not isinstance(has_screen, bool):
        raise ValueError(f"screen must be true or false, got {has_screen}")
    sandwich = acrylic_sandwich(p)
    stock = vslot_stock(p)
    for key in ("opening_w", "opening_h", "fix_gap", "awning_h"):
        if isinstance(p[key], float) and not math.isfinite(p[key]):
            raise ValueError(f"{key} must be a finite number, got {p[key]}")
    F, T, S, N = D["FRAME_W"], D["TRANSOM_W"], D["SASH_W"], D["SCREEN_W"]
    w = p["opening_w"] - 2 * p["fix_gap"]
    h = p["opening_h"] - 2 * p["fix_gap"]
    a = p["awning_h"]
    if a < MIN_AWNING:
        raise ValueError(f"awning_h must be at least {MIN_AWNING}, got {a}")
    horiz = w - 2 * F
    transom_c = h - F - a - T / 2
    lower = transom_c - T / 2 - F
    if lower < MIN_FIXED:
        raise ValueError(f"fixed pane height {lower} is below {MIN_FIXED}; reduce awning_h")
    sash_h = (h - D["FRAME_BODY"]) - (transom_c + D["TRANSOM_HALF_BODY"]) - 2 * D["SASH_GAP"]
    fixed_gh = math.floor(transom_c - D["TRANSOM_GLASS"] - D["GLASS_EDGE"])
    sash_gh = math.floor(sash_h - 2 * D["SASH_GLASS"])

    def widths(n):
        if n == 1:
            return (w - 2 * D["FRAME_BODY"] - 2 * D["SASH_GAP"], w - 2 * D["FRAME_BODY"] + 2 * D["SCREEN_OVERLAP"],
                    w - 2 * D["GLASS_EDGE"], w - 2 * D["FRAME_BODY"])
        check_mullion_dims()
        m1 = F - D["MULLION_W"] / 2 + (horiz + D["MULLION_W"]) / n
        opening = m1 - D["MULLION_HALF_BODY"] - D["FRAME_BODY"]
        return (opening - 2 * D["SASH_GAP"], opening + 2 * D["SCREEN_OVERLAP"],
                m1 - D["TRANSOM_GLASS"] - D["GLASS_EDGE"], opening)

    def panes_at(n):
        sw, _, fw, _ = widths(n)
        return {"fixed": (math.floor(fw), fixed_gh), "sash": (math.floor(sw - 2 * D["SASH_GLASS"]), sash_gh)}

    bays, auto_bays, pitch, mullions = bay_layout(p, horiz, panes_at)
    sash_w, screen_w, _, opening = widths(bays)
    run = bay_width(horiz, bays)
    screen_h = (h - D["FRAME_BODY"] + D["SCREEN_OVERLAP"]) - (transom_c - T / 2 + D["TRANSOM_MAG_X"] - D["SCREEN_OVERLAP"] - 2)
    screen_core = lambda length: "alu10" if split(length, 0.0, seg_max)[0] > 1 else None
    hinges = hinge_count(screen_w) if has_screen else 0

    members = [
        member("head", run, "sash_rebate", FRAME_CORE, bays, seg_max, max(1, hinges)),
        member("sill", run, "sill", FRAME_CORE, bays, seg_max),
        member("jamb_lower", lower, "glazing", FRAME_CORE, 2, seg_max),
        member("jamb_upper", a, "sash_rebate", FRAME_CORE, 2, seg_max),
        member("transom", run, "transom", TRANSOM_CORE, bays, seg_max, 2),
    ]
    if bays > 1:
        members += [
            member("mullion_lower", lower, "mullion_glazing", TRANSOM_CORE, bays - 1, seg_max),
            member("mullion_upper", a, "mullion_sash", TRANSOM_CORE, bays - 1, seg_max),
        ]
    members += [
        member("sash_horizontal", sash_w - 2 * S, "sash", "alu20", 2 * bays, seg_max),
        member("sash_vertical", sash_h - 2 * S, "sash", "alu20", 2 * bays, seg_max),
    ]
    if has_screen:
        members += [
            member("screen_horizontal", screen_w - 2 * N, "screen", screen_core(screen_w - 2 * N), 2 * bays, seg_max),
            member("screen_vertical", screen_h - 2 * N, "screen", screen_core(screen_h - 2 * N), 2 * bays, seg_max),
        ]

    clear = D["TUBE_END_CLEAR"]
    sock, sash_sock, screen_sock = (D[k] - clear for k in ("SOCKET_FRAME", "SOCKET_SASH", "SOCKET_SCREEN"))
    shoe_sock = (F - D["FRAME_BODY"]) + (D["MULLION_W"] / 2 - D["MULLION_HALF_BODY"]) - 2 * (D["SHOE_WALL"] + 1)
    tubes = [
        {"member": "head", "core": FRAME_CORE, "length": horiz + 2 * sock, "qty": 1},
        {"member": "sill", "core": FRAME_CORE, "length": horiz + 2 * sock, "qty": 1},
        {"member": "jamb", "core": FRAME_CORE, "length": h - 2 * F + 2 * sock, "qty": 2},
        {"member": "transom", "core": TRANSOM_CORE,
         "length": horiz + 2 * (F - D["FRAME_BODY"]) - 2 * (D["SHOE_WALL"] + 1), "qty": 1},
    ]
    if bays > 1:
        tubes += [
            {"member": "mullion_lower", "core": TRANSOM_CORE, "length": lower + shoe_sock, "qty": bays - 1},
            {"member": "mullion_upper", "core": TRANSOM_CORE, "length": a + shoe_sock, "qty": bays - 1},
        ]
    tubes += [
        {"member": "sash_horizontal", "core": "alu20", "length": sash_w - 2 * S + 2 * sash_sock, "qty": 2 * bays},
        {"member": "sash_vertical", "core": "alu20", "length": sash_h - 2 * S + 2 * sash_sock, "qty": 2 * bays},
    ]
    for m in members:
        if m["name"].startswith("screen") and m["core"]:
            tubes.append({"member": m["name"], "core": m["core"], "length": m["length"] + 2 * screen_sock,
                          "qty": m["qty"]})
    for t in tubes:
        t["length"] = round(t["length"], 1)

    glass = panes_at(bays)
    each = f", each of {bays} sashes" if bays > 1 else ""

    checks = []
    trib = (lower + a) / 2
    limit = horiz / 175

    def transom_delta(core):
        if bays == 1:
            return deflection(core, horiz, trib)
        w_t = WIND_KPA / 1000.0 * trib
        half = run / 2
        loads = strip_loads(0.0, half, w_t) + strip_loads(horiz - half, horiz, w_t)
        loads += [(c - F, WIND_KPA / 1000.0 * pitch * trib) for c in mullions]
        return beam_deflection(core, horiz, loads)

    loads_msg = "" if bays == 1 else f" carrying {bays - 1} mullion{'s' if bays > 2 else ''}"
    vslot = None
    if stock is not None:
        vslot = vslot_cores(stock, members, tubes, transom_delta, limit, lower, a, pitch, run, bays, sock, clear)
    core_of = {m["name"]: m["core"] for m in members}
    delta = transom_delta(core_of["transom"])
    checks.append({"name": "transom_deflection", "ok": delta <= limit,
                   "msg": f"transom deflects {delta:.1f} mm at {WIND_KPA} kPa{loads_msg}, limit span/175 = {limit:.1f} mm"})

    gw, gh = glass["sash"]
    kg_m2 = GLAZING_KG_M2[p["glazing"]] * (sandwich["t"] / D["ACRYLIC_T"] if p["glazing"] == "acrylic" else 1)
    sash_kg = gw * gh / 1e6 * kg_m2 + 2 * (sash_w + sash_h) / 1000 * SASH_FRAME_KG_M
    extra = CORES[VSLOT][4] - CORES["alu20"][4]
    sash_kg += sum(2 * span / 1000 * extra for name, span in (("sash_horizontal", sash_w), ("sash_vertical", sash_h))
                   if core_of[name] == VSLOT)
    candidates = [s for s in STAYS if STAY_RATIO * sash_h <= s[0] <= sash_h]
    stay = next((s for s in candidates if s[1] >= sash_kg), None)
    stay_ok = stay is not None
    if stay_ok:
        msg = f"sash {sash_kg:.1f} kg, stay pair {stay[0]} mm rated {stay[1]} kg{each}"
    else:
        msg = (f"sash {sash_kg:.1f} kg, no stay pair in {STAY_RATIO * sash_h:.0f}-{sash_h:.0f} mm "
               f"range rated for it{each}")
    checks.append({"name": "sash_weight", "ok": stay_ok, "msg": msg})

    too_long = [m["name"] for m in members if m["seg"] > seg_max]
    checks.append({"name": "segment_length", "ok": not too_long, "msg": f"segments over bed: {too_long}"})

    by_name = {m["name"]: m for m in members}
    cam_at = F + D["JOINT_GAP"] + by_name["transom"]["seg"] / 2
    keeper_at = D["FRAME_BODY"] + D["SASH_GAP"] + S + D["JOINT_GAP"] + by_name["sash_horizontal"]["seg"] / 2
    keeper_dz = round(abs(keeper_at - cam_at), 2)
    lo = keeper_dz_min(D["VSLOT_CSK_D"] if core_of["sash_horizontal"] == VSLOT else None)
    hi = keeper_dz_max(by_name["sash_horizontal"]["seg"])
    checks.append({"name": "cam_keeper", "ok": by_name["transom"]["n"] >= 2 and lo <= keeper_dz <= hi,
                   "msg": f"keeper bosses {keeper_dz:.2f} mm either side of the SBE middle, over the cams "
                          f"(allowed {lo:.1f}-{hi:.1f} mm, transom needs 2+ segments{' per bay' if bays > 1 else ''}){each}"})

    if "max_pane" in p or "bays" in p:
        limit_pane = p.get("max_pane")
        if limit_pane is None:
            msg = f"{bays} bay{'s' if bays > 1 else ''}, no max_pane limit"
        else:
            sheet = " x ".join(f"{v:g}" for v in limit_pane)
            chosen = f"{bays} bays ({auto_bays} needed)" if bays > auto_bays else f"{bays} bay{'s' if bays > 1 else ''}"
            msg = (f"{chosen}: fixed panes {glass['fixed'][0]} x {glass['fixed'][1]}, sash panes "
                   f"{glass['sash'][0]} x {glass['sash'][1]} fit a {sheet} mm sheet")
        checks.append({"name": "pane_fit", "ok": True, "msg": msg})
        if bays == 1:
            checks.append({"name": "mullion_deflection", "ok": True, "msg": "1 bay, no mullions"})
        else:
            stubs = [(name, span, deflection(core_of[f"mullion_{name}"], span, pitch))
                     for name, span in (("lower", lower), ("upper", a))]
            name, span, d = max(stubs, key=lambda s: s[2] / s[1])
            checks.append({"name": "mullion_deflection", "ok": all(d_ <= s_ / 175 for _, s_, d_ in stubs),
                           "msg": f"{name} mullion deflects {d:.1f} mm at {WIND_KPA} kPa over {span:g} mm, "
                                  f"limit span/175 = {span / 175:.1f} mm"})

    if vslot is not None:
        joined = [f"{name} {len(js)}" for name, js in vslot["joins"].items() if js]
        notes = [f"V-slot 2020: {len(vslot['plan'])} pieces of {stock:g} mm"]
        notes += [f"joins: {', '.join(joined)}"] if joined else []
        notes += vslot["fallbacks"]
        checks.append({"name": "core", "ok": True, "msg": "; ".join(notes)})

    return {"params": p, "sandwich": sandwich, "vslot": vslot, "w": w, "h": h, "transom_c": transom_c, "members": members,
            "tubes": tubes, "glass": glass, "sash": (sash_w, sash_h), "screen": (screen_w, screen_h),
            "sash_kg": round(sash_kg, 1), "stay": stay[0] if stay else None, "keeper_dz": keeper_dz,
            "bed": list(bed), "max_seg": seg_max, "has_screen": has_screen, "hinges": hinges,
            "bays": bays, "auto_bays": auto_bays, "pitch": pitch, "mullions": mullions, "bay_w": run, "opening": opening,
            "checks": checks}
