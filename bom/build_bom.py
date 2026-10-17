#!/usr/bin/env python3
"""Build bom/<name>.csv/.md plus per-name cutlist, glass and parts CSVs from the layout, the part list and the STLs."""
import csv
import json
import math
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import generate  # noqa: E402
import stl  # noqa: E402
import window  # noqa: E402
from window import D  # noqa: E402

SHELL_MM = 2.1
INFILL = 0.15
DENSITY = {"interior": 1.27, 1: 1.27, 2: 1.07, 3: 1.20}
MATERIAL = {"interior": "PETG", 1: "PETG + exterior paint, or ASA", 2: "ASA", 3: "ASA-CF or PC-ABS (light colour)"}
FRAME_SEGMENTS = {"H", "S", "SW", "JL", "JU", "T", "TE", "SH", "SB", "SBE", "SV"}
TRANSOM_PARTS = {"T", "TE", "TSL", "TSR"}
MULLION_STEEL = {"TX", "MSL", "MST", "MSH", "ML", "MU"}
MULLION_SHOES = {"MSL", "MST", "MSH"}
PERIMETER_SEGMENTS = {"H", "S", "SW", "JL", "JU"}
FRAME_CORNERS = {"CH", "CSL", "CSR", "CS"}
PERIMETER_CORNERS = {"CH", "CSL", "CSR"}
CORD_WASTE = 1.1
SEAL_ALLOWANCE = 1.03
CARTRIDGE_ML = 290.0
BEAD_DEPTH_MM = 8.0
JOINT_ML = 3.0
BED_ML = 1.5
SHOE_FACE_ML = 5.0
SEALANT_WASTE = 1.25
STAY_TRACK_SCREWS = 4
STAY_ARM_SCREWS = 3
SCREEN_ONLY = "screen-only"
MULLION_ONLY = "mullion-only"
SCREW_HOSTS = {
    "H": ("head",), "S": ("sill",), "SW": ("sill",), "JL": ("jamb_lower",), "JU": ("jamb_upper",),
    "T": ("transom",), "TE": ("transom",), "ML": ("mullion_lower",), "MU": ("mullion_upper",),
    "SH": ("sash_horizontal",), "SB": ("sash_horizontal",), "SBE": ("sash_horizontal",), "SV": ("sash_vertical",),
    "CH": ("head", "jamb_upper"), "CSL": ("sill", "jamb_lower"), "CSR": ("sill", "jamb_lower"),
    "CS": ("sash_horizontal", "sash_vertical"), "JN": ("jamb_lower",), "SN": ("sill",), "HN": ("head",),
    "TX": ("transom",), "TSL": ("transom",), "TSR": ("transom",),
    "MSL": ("mullion_lower",), "MST": ("mullion_upper",), "MSH": ("mullion_upper",),
}


def mass_g(vol_cm3, area_cm2, density):
    shell = min(vol_cm3, area_cm2 * SHELL_MM / 10.0)
    return (shell + (vol_cm3 - shell) * INFILL) * density


def ring_mm(profile):
    inset = D["CORD_INSET"] + D["CORD_D"] / 2
    w, d = {"transom": (2 * D["TRANSOM_HALF_BODY"], D["DEPTH"]),
            "mullion_glazing": (2 * D["MULLION_HALF_BODY"], D["DEPTH"]),
            "mullion_sash": (2 * D["MULLION_HALF_BODY"], D["DEPTH"]),
            "sash": (D["SASH_BODY"], D["LIP_Y1"] - D["SASH_Y0"])}.get(profile, (D["FRAME_BODY"], D["DEPTH"]))
    return 2 * (w + d - 4 * inset)


def screw_kind(mem):
    if mem["core"] == window.VSLOT_PAIR and mem["profile"] == "transom":
        return ("shoulder",)
    if mem["core"] in (window.VSLOT, window.VSLOT_PAIR):
        return ("m5", window.m5_length(mem["profile"]))
    return ("tek",) if mem["core"].startswith("steel") else ("alu",)


def tube_screws(lay, q):
    mem = {m["name"]: m for m in lay["members"]}
    count = {}
    for pid, hosts in SCREW_HOSTS.items():
        for name in hosts:
            if q.get(pid) and name in mem:
                key = screw_kind(mem[name])
                count[key] = count.get(key, 0) + q[pid]
    return count


def hardware(lay, parts):
    q = {p["id"]: p["qty"] for p in parts}
    total = lambda ids: sum(q.get(i, 0) for i in ids)
    bays = lay["bays"]
    scr_w, scr_h = lay["screen"]
    m = lambda mm: round(mm / 1000.0, 2)
    perim = lambda wh: 2 * (wh[0] + wh[1])
    hinges = q.get("HG", 0)
    bossed = {"H", "TE"} if lay["has_screen"] else {"TE"}
    cord_joints = [((mem["n"] + 1) * mem["qty"], mem["profile"]) for mem in lay["members"]
                   if mem["profile"] in window.CORD_PROFILES]
    joints = sum(j for j, _ in cord_joints)
    fixings = total(PERIMETER_SEGMENTS) + 2 * total(PERIMETER_CORNERS) + 2 * total({"JN", "SN", "HN"})
    bedded = total({"S", "SW", "JL"}) + 2 * total({"CSL", "CSR"}) + 2 * total({"JN", "SN"})
    screen_screws = sum((mem["n"] + 2) * mem["qty"] for mem in lay["members"]
                        if mem["name"].startswith("screen") and mem["core"])
    outline = perim((lay["w"], lay["h"]))
    sealant_ml = (outline / 1000 * lay["params"]["fix_gap"] * BEAD_DEPTH_MM + JOINT_ML * joints
                  + BED_ML * bedded + SHOE_FACE_ML * total({"TSL", "TSR"} | MULLION_SHOES))
    loop_extra = 8 * (D["SASH_GAP"] - D["FIN_L"] / 2 + D["LIP_L"] / 2)
    steel = "steel transom tube: T, TE, shoes" if bays == 1 else "steel transom and mullion tubes: T, TE, TX, ML, MU, shoes"
    vslot = lay.get("vslot")
    screws = tube_screws(lay, q)
    if vslot is not None:
        steel = "steel tubes: " + ", ".join(m["name"] for m in lay["members"] if (m["core"] or "").startswith("steel"))
    upper_vslot = any(m["name"] == "mullion_upper" and m["core"] == window.VSLOT_PAIR for m in lay["members"])
    stay_desc = f"{lay['stay']} mm" if lay["stay"] is not None else "no stay fits (see check)"
    items = [
        ("Fixings", "Timber screw 10g x 75, stainless or galvanised (frame fixings)", fixings, "pcs"),
        ("Fixings", "Self-tapping screw 8g x 30 stainless, countersunk (aluminium tube screws: frame, sash, corners, nodes)",
         screws.get(("alu",), 0), "pcs"),
        ("Fixings", f"Tek screw 8g x 25, 410 stainless, countersunk ({steel})", screws.get(("tek",), 0), "pcs"),
        *[("Fixings", f"M5 x {k[1]} countersunk machine screw, stainless (V-slot tube screws, one T-nut each)", n, "pcs")
          for k, n in sorted(screws.items()) if k[0] == "m5"],
        *([("Fixings", "M5 slide-in T-nut for 20-series V-slot, 6 mm slot (V-slot tube screws)",
            sum(n for k, n in screws.items() if k[0] == "m5"), "pcs")] if vslot is not None else []),
        *([("Fixings", "Self-tapping screw 8g x 20 stainless, countersunk (V-slot transom pair: T, TE, TX, shoes; 3.5 mm pilot)",
            screws[("shoulder",)], "pcs")] if ("shoulder",) in screws else []),
        ("Fixings", "Self-tapping screw 8g x 12 stainless, countersunk (screen tube screws)", screen_screws, "pcs",
         SCREEN_ONLY),
        ("Fixings", "M4 heat-set insert for a 5.6 x 8 mm hole",
         2 * total(bossed) + (4 if lay["keeper_dz"] else 2) * q["SBE"] + q["CMB"] + 2 * q["TC"], "pcs"),
        ("Fixings", "M4 x 10 countersunk machine screw (cam bases CMB, keepers KP)", 2 * q["CMB"] + 2 * q["KP"], "pcs"),
        ("Fixings", "M4 x 10 pan or button head machine screw (hinge frame leaves HG)", 2 * hinges, "pcs", SCREEN_ONLY),
        ("Fixings", "M4 x 8 pan screw + 20 mm penny washer (cam pivots)", q["CMH"], "pcs"),
        ("Fixings", f"M4 x 16 countersunk machine screw ({'transom' if bays == 1 else 'transom and mullion'} lock screws)",
         2 * total({"TSL", "TSR"} | MULLION_SHOES), "pcs"),
        ("Fixings", "M4 x 50 bolt + nyloc nut (hinge pins)", hinges, "pcs", SCREEN_ONLY),
        ("Fixings", "4g x 12 self-tapping screw (screen leaves HS)", 2 * hinges, "pcs", SCREEN_ONLY),
        ("Fixings", "Plastic window packers, assorted 1-10 mm (one stack per position)",
         fixings + q["GW"] + 4 + q.get("SN", 0), "pcs"),
        ("Hardware", f"Stainless friction stay pair, {stay_desc}, stack <= {D['SASH_GAP']:g} mm, "
                     f"track/arm width <= {D['STAY_W']:g} mm (check rating >= {lay['sash_kg']} kg)", bays, "pair"),
        ("Hardware", "Friction-stay screw 8g x 25 stainless, countersunk (tracks to upper jambs; match the stay's holes)",
         2 * STAY_TRACK_SCREWS, "pcs"),
        ("Hardware", "Self-tapping screw 8g x 16 stainless, countersunk (friction-stay tracks to upper mullions, 3.5 mm pilot; "
                     "match the stay's holes)" if upper_vslot else
                     "Tek screw 8g x 16, 410 stainless, countersunk (friction-stay tracks to upper mullions; match the stay's holes)",
         2 * (bays - 1) * STAY_TRACK_SCREWS, "pcs", MULLION_ONLY),
        ("Hardware", "Friction-stay screw 8g x 16 stainless, countersunk (arms to sash sides; match the stay's holes)",
         2 * STAY_ARM_SCREWS * bays, "pcs"),
        ("Seals", f"EPDM bulb kerf seal, 3 mm kerf (outer + inner loop round {'the sash opening' if bays == 1 else 'each sash opening'})",
         m((2 * perim(lay["sash"]) + loop_extra) * SEAL_ALLOWANCE * bays), "m"),
        ("Seals", "EPDM glazing wedge gasket, 3 mm",
         m(2 * (perim(lay["glass"]["fixed"]) + perim(lay["glass"]["sash"])) * bays), "m"),
        ("Seals", "Closed-cell foam cord, 4 mm (one ring per segment joint)",
         round(sum(j * ring_mm(p) for j, p in cord_joints) * CORD_WASTE / 1000.0, 1), "m"),
        ("Seals", f"Closed-cell foam cord, 3 mm ({'transom shoe' if bays == 1 else 'transom and mullion shoe'} seams)",
         m(2 * D["TRANSOM_W"] + 4 * (bays - 1) * D["MULLION_W"]), "m"),
        ("Seals", "MS-polymer sealant rated for +/-50% joint movement (ASTM C920 Class 50 or equal), "
                  "290 ml cartridge (joints, fixing bedding, outside perimeter)",
         math.ceil(sealant_ml * SEALANT_WASTE / CARTRIDGE_ML), "pcs"),
        ("Seals", "Butyl flashing tape, 150 mm wide (sill tray; or two 100 mm runs lapped 50 mm)", m(lay["w"] + 300), "m"),
        ("Seals", "Backer rod, 10 mm", m(outline), "m"),
        ("Seals", "Low-expansion window foam, can", 1, "pcs"),
        ("Seals", "Gel CA glue (EPDM loop joints)", 1, "pcs"),
        ("Screen", "Flexible magnetic strip A, 12.7 mm, adhesive-backed (screen back channel)",
         m(perim(lay["screen"]) * bays), "m", SCREEN_ONLY),
        ("Screen", "Flexible magnetic strip B, 12.7 mm, adhesive-backed, matched to A, or adhesive steel strip "
                   "(frame magnet channel)", m(perim(lay["screen"]) * bays), "m", SCREEN_ONLY),
        ("Screen", "Fibreglass insect mesh", round(scr_w * scr_h / 1e6 * 1.1 * bays, 2), "m2", SCREEN_ONLY),
        ("Screen", "Screen spline, 4 mm", m(perim(lay["screen"]) * bays), "m", SCREEN_ONLY),
        ("Screen", "Two-part epoxy, 5-minute (screen corner joints)", 1, "pcs", SCREEN_ONLY),
    ]
    if not lay["has_screen"]:
        items = [it for it in items if SCREEN_ONLY not in it[4:]]
    if bays == 1:
        items = [it for it in items if MULLION_ONLY not in it[4:]]
    if vslot is not None:
        items = [it for it in items if it[2] != 0]
        items.append(("Tube", f"V-slot 2020, 4-slot, {vslot['stock']:g} mm pieces (cut plan in the BOM)", len(vslot["plan"]), "pcs"))
    by_core = {}
    for t in lay["tubes"]:
        if t["core"] != window.VSLOT:
            by_core[t["core"]] = by_core.get(t["core"], 0) + t["length"] * t["qty"]
    for core, mm in sorted(by_core.items()):
        items.append(("Tube", f"Tube {core} (total length; buy in 1 m/3 m stock)", m(mm), "m"))
    for pane, (gw, gh) in lay["glass"].items():
        g = lay["params"]["glazing"]
        if g == "acrylic":
            items.append(("Glazing", f"Acrylic {lay['sandwich']['t']:g} mm, {gw} x {gh} ({pane} pane)", 2 * bays, "pcs"))
        else:
            items.append(("Glazing", f"{generate.GLASS_SPEC[g]}, {gw} x {gh} ({pane} pane)", bays, "pcs"))
    if lay["params"]["glazing"] == "acrylic":
        items.append(("Glazing", "Silica gel desiccant beads", 100 * bays, "g"))
        items.append(("Glazing", "Butyl glazing tape, 3 mm (acrylic sandwich edge)",
                      m(2 * sum(perim(v) for v in lay["glass"].values()) * bays), "m"))
    return [{"group": g, "item": i, "qty": n, "unit": u} for g, i, n, u, *_ in items]


def filament(lay, parts, stl_dir):
    tier = lay["params"]["tier"]
    grams = {"interior": 0.0, tier: 0.0}
    missing = []
    for p in parts:
        f = pathlib.Path(stl_dir) / f"{p['id']}.stl"
        if not f.exists():
            missing.append(p["id"])
            continue
        key = "interior" if p["role"] == "interior" else tier
        vol, area = stl.volume_area(stl.load(f))
        grams[key] += mass_g(vol, area, DENSITY[key]) * p["qty"]
    rows = [{"group": "Filament", "item": f"{MATERIAL[k]} ({'interior' if k == 'interior' else f'exterior, tier {k}'})",
             "qty": round(g / 1000.0, 2), "unit": "kg"} for k, g in grams.items()]
    return rows, missing


def write(name, lay, parts, items, missing, out):
    out = pathlib.Path(out)
    with (out / f"{name}.csv").open("w", newline="") as fh:
        wr = csv.DictWriter(fh, ["group", "item", "qty", "unit"])
        wr.writeheader()
        wr.writerows(items)
    generate.write_cutlist(lay, out / f"{name}-cutlist.csv")
    generate.write_glass(lay, out / f"{name}-glass.csv")
    generate.write_parts(parts, out / f"{name}-parts.csv")
    lines = [f"# BOM: {name}", "", f"Prints: {sum(p['qty'] for p in parts)} parts in {len(parts)} types "
             f"(list: `bom/{name}-parts.csv`).", "",
             "| Group | Item | Qty | Unit |", "|---|---|---|---|"]
    lines += [f"| {i['group']} | {i['item']} | {i['qty']} | {i['unit']} |" for i in items]
    lines += ["", f"## Tube cut list (`bom/{name}-cutlist.csv`)", "",
              "| Member | Core | Length (mm) | Qty |", "|---|---|---|---|"]
    lines += [f"| {t['member']} | {t['core']} | {t['length']} | {t['qty']} |" for t in lay["tubes"]]
    lines += ["", f"## Glass (`bom/{name}-glass.csv`)", "",
              "| Pane | Glazing | Width (mm) | Height (mm) | Qty |", "|---|---|---|---|---|"]
    lines += [f"| {pane} | {lay['params']['glazing']} | {gw} | {gh} | {lay['bays']} |" for pane, (gw, gh) in lay["glass"].items()]
    vslot = lay.get("vslot")
    if vslot is not None:
        lines += ["", "## V-slot cut plan", "",
                  f"{len(vslot['plan'])} pieces of {vslot['stock']:g} mm V-slot 2020, with {window.SAW_KERF:g} mm per saw cut.", "",
                  "| Piece | Cuts (mm) | Offcut (mm) |", "|---|---|---|"]
        lines += [f"| {i} | {', '.join(f'{label} {length:g}' for label, length in b['cuts'])} | {b['offcut']:g} |"
                  for i, b in enumerate(vslot["plan"], 1)]
        joined = {k: v for k, v in vslot["joins"].items() if v}
        if joined:
            lines += ["", "## V-slot joins", "",
                      "Pieces butt together inside a printed segment, a quarter of the way along it, clear of its T-nut. "
                      "Measure from the left end seen from outside (jambs: from the bottom); the segments are symmetric, "
                      "so either end works.", ""]
            lines += [f"- {k}: " + "; ".join(f"{j['at']:g} mm, inside segment {j['segment']}" for j in v) for k, v in joined.items()]
        if vslot["fallbacks"]:
            lines += ["", "## Standard tubes in this V-slot window", ""] + [f"- {f}" for f in vslot["fallbacks"]]
    if lay["bays"] > 1:
        centres = ", ".join(f"{c:g}" for c in (round(c, 1) for c in lay["mullions"]))
        lines += ["", "## Bays", "", f"{lay['bays']} bays, {round(lay['pitch'], 1):g} mm apart. Mullion centre lines, "
                  f"from the frame's left outer edge as seen from outside: {centres} mm."]
    if missing:
        lines += ["", f"Filament excludes unrendered parts: {', '.join(missing)}. Run `cad/box.sh render {name}` first."]
    (out / f"{name}.md").write_text("\n".join(lines) + "\n")


def main(argv):
    if len(argv) != 2:
        print("usage: build_bom.py <params-name>", file=sys.stderr)
        return 2
    name = argv[1]
    lay = window.layout(json.loads((ROOT / "params" / f"{name}.json").read_text()))
    parts = generate.parts(lay)
    fil, missing = filament(lay, parts, ROOT / "cad" / "stl" / name)
    items = hardware(lay, parts) + fil
    write(name, lay, parts, items, missing, ROOT / "bom")
    print(f"bom/{name}.csv, .md, -cutlist.csv, -glass.csv, -parts.csv: {len(items)} lines"
          + (f", {len(missing)} STLs missing" if missing else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
