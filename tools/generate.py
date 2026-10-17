#!/usr/bin/env python3
"""Turn a window layout into part wrappers plus parts/cutlist/glass CSVs under cad/generated/."""
import csv
import json
import pathlib
import sys

import window
from window import D, split

GENERATED = window.ROOT / "cad" / "generated"
MODULE_FILE = {"cam_base": "cam_lock", "cam_handle": "cam_lock", "cam_keeper": "cam_lock",
               "acrylic_spacer_corner": "acrylic_spacer", "screen_leaf": "screen_hinge"}
GLASS_SPEC = {
    "igu": "IGU 4/16/4 = 24 mm, toughened if required by AS 1288, low-E/argon optional",
    "acrylic": "2 x 4 mm clear acrylic, cut to size, protective film on until assembly",
    "twinwall": "16 mm twin-wall polycarbonate, UV face out, flutes vertical",
}
NOSE_END = D["NOSE_KEY_X"] + D["NOSE_KEY_W"]
SCREEN_PARTS = {"NH", "NV", "CN", "HG", "HS"}
ENVELOPE_FILE = pathlib.Path(__file__).resolve().parent / "part_envelopes.json"
ENVELOPES = json.loads(ENVELOPE_FILE.read_text()) if ENVELOPE_FILE.exists() else {}


def part(pid, module, args, qty, role="exterior", length=None):
    return {"id": pid, "module": module, "call": f"{module}({args});", "qty": qty, "role": role, "length": length}


def core_arg(lay, name, key="core"):
    if lay.get("vslot") is None:
        return ""
    mem = next(x for x in lay["members"] if x["name"] == name)
    if mem["core"] in (window.VSLOT, window.VSLOT_PAIR):
        return f', {key}="vslot"'
    return f', {key}="alu20"' if mem["profile"] == "sash_rebate" else ""


def parts(lay):
    m = {x["name"]: x for x in lay["members"]}
    ends = lambda name: min(2, m[name]["n"])
    bays = lay["bays"]
    ca = lambda name, key="core": core_arg(lay, name, key)
    out = []

    def seg(pid, name, profile, qty, role="exterior", **flags):
        if qty <= 0:
            return
        f = "".join(f", {k}={str(v).lower()}" for k, v in flags.items())
        s = m[name]["seg"]
        out.append(part(pid, "frame_segment", f'"{profile}", {s}, "{pid}"{f}{ca(name)}', qty, role, s))

    seg("H", "head", "sash_rebate", bays * m["head"]["n"], bosses=lay["has_screen"])
    seg("S", "sill", "sill", bays * (m["sill"]["n"] - ends("sill")))
    seg("SW", "sill", "sill", bays * ends("sill"), weep=True)
    seg("JL", "jamb_lower", "glazing", 2 * m["jamb_lower"]["n"])
    seg("JU", "jamb_upper", "sash_rebate", 2 * m["jamb_upper"]["n"])
    seg("T", "transom", "transom", bays * (m["transom"]["n"] - ends("transom")))
    seg("TE", "transom", "transom", bays * ends("transom"), weep=True, bosses=True)
    if bays > 1:
        seg("ML", "mullion_lower", "mullion_glazing", (bays - 1) * m["mullion_lower"]["n"])
        seg("MU", "mullion_upper", "mullion_sash", (bays - 1) * m["mullion_upper"]["n"])
    seg("SH", "sash_horizontal", "sash", bays * m["sash_horizontal"]["n"])
    seg("SB", "sash_horizontal", "sash", bays * (m["sash_horizontal"]["n"] - ends("sash_horizontal")))
    seg("SBE", "sash_horizontal", "sash", bays * ends("sash_horizontal"), weep=True, bosses=True,
        boss_dz=lay["keeper_dz"])
    seg("SV", "sash_vertical", "sash", 2 * bays * m["sash_vertical"]["n"])
    if lay["has_screen"]:
        seg("NH", "screen_horizontal", "screen", 2 * bays * m["screen_horizontal"]["n"], "interior")
        seg("NV", "screen_vertical", "screen", 2 * bays * m["screen_vertical"]["n"], "interior")

    pane = pane_thickness(lay)
    block_arg = f", pane_t={pane:g}" if pane != D["GLASS_T"] else ""
    hinges = lay["hinges"] * bays
    n_nose, s_nose = split(lay["w"] - 2 * NOSE_END, D["JOINT_GAP"], lay["max_seg"])
    out += [
        part("CH", "corner_block", f'"sash_rebate", "sash_rebate", "CH"{ca("head", "core_a")}{ca("jamb_upper", "core_b")}', 2),
        part("CSL", "corner_block", f'"sill", "glazing", "CSL"{ca("sill", "core_a")}{ca("jamb_lower", "core_b")}', 1),
        part("CSR", "corner_block",
             f'"sill", "glazing", "CSR", mirrored=true{ca("sill", "core_a")}{ca("jamb_lower", "core_b")}', 1),
        part("CS", "corner_block",
             f'"sash", "sash", "CS"{ca("sash_horizontal", "core_a")}{ca("sash_vertical", "core_b")}', 4 * bays),
        part("CN", "corner_block", '"screen", "screen", "CN"', 4 * bays, "interior"),
        part("JN", "jamb_node", f'"JN"{ca("jamb_lower")}', 2),
        part("TSL", "transom_shoe", f'"TSL", mirrored=true{ca("transom")}', 1),
        part("TSR", "transom_shoe", f'"TSR"{ca("transom")}', 1),
    ]
    if bays > 1:
        out += [
            part("SN", "frame_node", f'"sill", "SN"{ca("sill")}', bays - 1),
            part("HN", "frame_node", f'"sash_rebate", "HN"{ca("head")}', bays - 1),
            part("TX", "cross_node", f'"TX"{ca("transom")}', bays - 1),
            part("MSL", "mullion_shoe", f'"mullion_glazing", "MSL"{ca("mullion_lower")}', 2 * (bays - 1)),
            part("MST", "mullion_shoe", f'"mullion_sash", "MST"{ca("mullion_upper")}', bays - 1),
            part("MSH", "mullion_shoe", f'"mullion_sash", "MSH", head=true{ca("mullion_upper")}', bays - 1),
        ]
    out += [
        part("GW", "setting_block", f'"GW", wedge=true{block_arg}', 2 * bays),
        part("GF", "setting_block", f'"GF"{block_arg}', 6 * bays),
        part("WC", "weep_cap", '"WC"', bays * (ends("sill") + ends("sash_horizontal"))),
        part("NS", "sill_nose", f'{s_nose}, "NS"', n_nose, "exterior", s_nose),
        part("CMB", "cam_base", '"CMB"', 2 * bays, "interior"),
        part("CMH", "cam_handle", '"CMH"', 2 * bays, "interior"),
        part("KP", "cam_keeper", '"KP"', 2 * bays, "interior"),
        part("HG", "screen_hinge", '"HG"', hinges, "interior"),
        part("HS", "screen_leaf", '"HS"', hinges, "interior"),
        part("TC", "test_coupon", '"TC"', 1),
    ]
    if not lay["has_screen"]:
        out = [pt for pt in out if pt["id"] not in SCREEN_PARTS]

    g = lay["params"]["glazing"]
    bw = D["BEAD_W"]
    sash_w, sash_h = lay["sash"]
    runs = [
        ("BFH", lay["opening"]),
        ("BFV", lay["transom_c"] - D["TRANSOM_HALF_BODY"] - D["FRAME_BODY"] - 2 * bw),
        ("BSH", sash_w - 2 * D["SASH_BODY"]),
        ("BSV", sash_h - 2 * D["SASH_BODY"] - 2 * bw),
    ]
    sandwich = lay["sandwich"]
    pane_arg = f', {2 * sandwich["t"] + sandwich["gap"]:g}' if g == "acrylic" and sandwich["custom"] else ""
    gap_arg = f', {sandwich["gap"]:g}' if g == "acrylic" and sandwich["custom"] else ""
    for pid, run in runs:
        n, s = split(run, limit=lay["max_seg"])
        out.append(part(pid, "bead", f'"{g}", {s}, "{pid}"{pane_arg}', 2 * n * bays, "interior", s))

    if g == "acrylic":
        sw = D["SPACER_W"]
        for pane, key in (("F", "fixed"), ("S", "sash")):
            gw, gh = lay["glass"][key]
            for axis, run in (("H", gw - 2 * sw), ("V", gh - 2 * sw)):
                n, s = split(run, limit=lay["max_seg"])
                pid = f"A{pane}{axis}"
                out.append(part(pid, "acrylic_spacer", f'{s}, "{pid}"{gap_arg}', 2 * n * bays, "exterior", s))
        out.append(part("AC", "acrylic_spacer_corner", f'"AC"{gap_arg}', 8 * bays))
    return out


def envelope_key(pt, glazing):
    return f"{pt['id']}/{glazing}" if pt["module"] == "bead" else pt["id"]


def pane_thickness(lay):
    g = lay["params"]["glazing"]
    if g == "twinwall":
        return D["TWINWALL_T"]
    sandwich = lay.get("sandwich")
    if g == "acrylic" and sandwich and sandwich["custom"]:
        return 2 * sandwich["t"] + sandwich["gap"]
    return D["GLASS_T"]


def part_envelope(pt, lay):
    env = ENVELOPES.get(envelope_key(pt, lay["params"]["glazing"]))
    pane = pane_thickness(lay)
    if env is None or pane == D["GLASS_T"]:
        return env
    if pt["module"] == "setting_block":
        low, _, high = sorted(env)
        return [low, pane, high]
    if lay["params"]["glazing"] != "acrylic":
        return env
    gap = lay["sandwich"]["gap"]
    if pt["module"] == "bead":
        return [D["BEAD_T"] + D["GLASS_T"] - pane, max(env)]
    if pt["module"] == "acrylic_spacer":
        return [D["SPACER_W"], gap]
    if pt["module"] == "acrylic_spacer_corner":
        return [gap] + sorted(env)[1:]
    return env


def glass_spec(lay):
    g, sandwich = lay["params"]["glazing"], lay["sandwich"]
    if g != "acrylic" or not sandwich["custom"]:
        return GLASS_SPEC[g]
    return (f"2 x {sandwich['t']:g} mm clear acrylic, {sandwich['gap']:g} mm gap, cut to size, "
            "protective film on until assembly")


def bed_fit(lay, plist):
    bed = lay["bed"]
    bad = []
    for pt in plist:
        env = part_envelope(pt, lay)
        if env is None:
            bad.append(f"{pt['id']} (no envelope)")
            continue
        size = env + ([pt["length"]] if pt["length"] is not None else [])
        if any(a > b for a, b in zip(sorted(size), sorted(bed))):
            bad.append(f"{pt['id']} {' x '.join(f'{v:g}' for v in size)}")
    text = " x ".join(f"{v:g}" for v in bed)
    msg = f"parts too big for the {text} mm bed: {', '.join(bad)}" if bad else f"every part fits the {text} mm bed"
    return {"name": "bed_fit", "ok": not bad, "msg": msg}


def write_parts(plist, path):
    with pathlib.Path(path).open("w", newline="") as fh:
        wr = csv.DictWriter(fh, ["id", "qty", "role", "length", "module", "call"])
        wr.writeheader()
        for pt in plist:
            wr.writerow({**pt, "length": "" if pt["length"] is None else pt["length"]})


def write_cutlist(lay, path):
    with pathlib.Path(path).open("w", newline="") as fh:
        wr = csv.writer(fh)
        wr.writerow(["member", "core", "length_mm", "qty"])
        for t in lay["tubes"]:
            wr.writerow([t["member"], t["core"], t["length"], t["qty"]])


def write_glass(lay, path):
    g = lay["params"]["glazing"]
    with pathlib.Path(path).open("w", newline="") as fh:
        wr = csv.writer(fh)
        wr.writerow(["pane", "glazing", "width_mm", "height_mm", "qty", "spec"])
        for pane, (gw, gh) in lay["glass"].items():
            wr.writerow([pane, g, gw, gh, lay["bays"], glass_spec(lay)])


def write(lay, out=GENERATED):
    out = pathlib.Path(out)
    if out.name != "generated":
        raise ValueError(f"refusing to clear {out}: expected a directory named 'generated'")
    parts_dir = out / "parts"
    parts_dir.mkdir(parents=True, exist_ok=True)
    for stale in parts_dir.glob("*.scad"):
        stale.unlink()

    dims = {**D, "MAX_SEG": lay["max_seg"]}
    dims.pop("BED_MARGIN")
    (out / "dims.scad").write_text("".join(f"{k} = {json.dumps(v)};\n" for k, v in dims.items()))

    p = lay["params"]
    (out / "params.json").write_text(json.dumps(p, indent=2))

    lines = {
        "W": float(lay["w"]), "H": float(lay["h"]), "TRANSOM_C": float(lay["transom_c"]),
        "AWNING_H": float(p["awning_h"]), "SASH": list(lay["sash"]), "SCREEN": list(lay["screen"]),
        "FIXED_GLASS": list(lay["glass"]["fixed"]), "SASH_GLASS_DIMS": list(lay["glass"]["sash"]),
    }
    text = f'NAME = "{p["name"]}";\n'
    text += "".join(f"{k} = {json.dumps(v)};\n" for k, v in lines.items())
    text += f'GLAZING = "{p["glazing"]}";\n'
    for mem in lay["members"]:
        key = mem["name"].upper()
        text += f"SEG_{key} = {mem['seg']};\nN_{key} = {mem['n']};\n"
    if lay["bays"] > 1:
        text += f"BAYS = {lay['bays']};\nPITCH = {round(lay['pitch'], 4)};\n"
        text += f"MULLIONS = {json.dumps([round(c, 4) for c in lay['mullions']])};\n"
    (out / "layout.scad").write_text(text)

    plist = parts(lay)
    for pt in plist:
        f = MODULE_FILE.get(pt["module"], pt["module"])
        (out / "parts" / f"{pt['id']}.scad").write_text(f"use <../../parts/{f}.scad>\n{pt['call']}\n")

    write_parts(plist, out / "parts.csv")
    write_cutlist(lay, out / "cutlist.csv")
    write_glass(lay, out / "glass.csv")
    return plist


def main(argv):
    if len(argv) != 2:
        print("usage: generate.py params/<name>.json", file=sys.stderr)
        return 2
    params = json.loads(pathlib.Path(argv[1]).read_text())
    lay = window.layout(params)
    plist = write(lay)
    print(f"{params['name']}: {len(plist)} part types, {sum(x['qty'] for x in plist)} prints -> {GENERATED}")
    checks = lay["checks"] + ([bed_fit(lay, plist)] if "bed" in params else [])
    for c in checks:
        print(("ok       " if c["ok"] else "WARNING  ") + c["msg"])
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
