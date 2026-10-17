"""Pure functions behind the web configurator: validation, preview, params files, part status, BOM and zip."""
import json
import math
import pathlib
import re
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "bom"))
sys.path.insert(0, str(ROOT / "tools"))

import build_bom  # noqa: E402
import check_stl  # noqa: E402
import drawing  # noqa: E402
import generate  # noqa: E402
import weight  # noqa: E402
import window  # noqa: E402
import zipper  # noqa: E402

NAME_RE = re.compile(r"[a-z0-9-]{1,40}")
REFERENCE_NAMES = {"bench-600", "home-1800x1500", "home-1800x1500-2bay"}
DEFAULTS = {"name": "my-window", "opening_w": 1800, "opening_h": 1500, "fix_gap": 8, "awning_h": 450,
            "glazing": "igu", "tier": 3, "screen": True, "bed": [256, 256, 256]}
OPTIONAL = ("max_pane", "bays", "acrylic_t", "acrylic_gap", "core", "vslot_stock")
PAGE_MAX_PANE = [1200, 900]
RANGES = {"opening_w": (300, 3000), "opening_h": (300, 3000), "fix_gap": (0, 20)}
BED_RANGE = (100, 500)
PRESETS = [
    {"key": "bambu", "label": "Bambu P1S / P1P / X1 / A1", "bed": [256, 256, 256]},
    {"key": "a1mini", "label": "Bambu A1 mini", "bed": [180, 180, 180]},
    {"key": "mk4", "label": "Prusa MK4", "bed": [250, 210, 220]},
    {"key": "prusamini", "label": "Prusa Mini", "bed": [180, 180, 180]},
    {"key": "ender3", "label": "Creality Ender-3", "bed": [220, 220, 250]},
]
PART_NAMES = {
    "H": "Head segment", "S": "Sill segment", "SW": "Sill end segment, weep", "JL": "Lower jamb segment",
    "JU": "Upper jamb segment", "T": "Transom segment", "TE": "Transom end segment, weep and cam bosses",
    "SH": "Sash top segment", "SB": "Sash bottom segment", "SBE": "Sash bottom end segment, weep and keeper bosses",
    "SV": "Sash side segment", "NH": "Screen top/bottom segment", "NV": "Screen side segment",
    "CH": "Head corner", "CSL": "Sill corner, left", "CSR": "Sill corner, right", "CS": "Sash corner",
    "CN": "Screen corner", "JN": "Jamb node", "TSL": "Transom shoe, left", "TSR": "Transom shoe, right",
    "GW": "Setting block, wedge", "GF": "Glass locator", "WC": "Weep cap", "NS": "Sill nose",
    "CMB": "Cam base", "CMH": "Cam handle", "KP": "Cam keeper", "HG": "Screen hinge, frame leaf",
    "HS": "Screen hinge, screen leaf", "TC": "Test coupon",
    "BFH": "Bead, fixed pane, horizontal", "BFV": "Bead, fixed pane, vertical",
    "BSH": "Bead, sash, horizontal", "BSV": "Bead, sash, vertical",
    "AFH": "Acrylic spacer, fixed pane, horizontal", "AFV": "Acrylic spacer, fixed pane, vertical",
    "ASH": "Acrylic spacer, sash, horizontal", "ASV": "Acrylic spacer, sash, vertical",
    "AC": "Acrylic spacer corner",
    "SN": "Sill node, mullion slot", "HN": "Head node, mullion slot", "TX": "Transom cross-node, mullion slots",
    "MSL": "Lower mullion shoe", "MST": "Upper mullion shoe, transom end", "MSH": "Upper mullion shoe, head end",
    "ML": "Lower mullion segment", "MU": "Upper mullion segment",
}
SUMMARY_KEYS = ("w", "h", "transom_c", "sash", "screen", "glass", "stay", "sash_kg", "keeper_dz", "bed", "max_seg",
                "has_screen", "members", "tubes", "bays", "auto_bays", "pitch", "mullions", "sandwich", "vslot")


class NotReady(Exception):
    pass


def is_number(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)


def validate(raw):
    if not isinstance(raw, dict):
        return dict(DEFAULTS), {"_form": "expected a JSON object"}
    params = {k: raw.get(k, v) for k, v in DEFAULTS.items()}
    params.update({k: raw[k] for k in OPTIONAL if k in raw})
    errors = {}
    unknown = sorted(set(raw) - set(DEFAULTS) - set(OPTIONAL))
    if unknown:
        errors["_form"] = f"unknown fields: {', '.join(unknown)}"
    if not isinstance(params["name"], str) or not NAME_RE.fullmatch(params["name"]):
        errors["name"] = "1-40 characters: lowercase letters, digits and dashes"
    for key, (lo, hi) in RANGES.items():
        if not is_number(params[key]) or not lo <= params[key] <= hi:
            errors[key] = f"{lo}-{hi} mm"
    if not is_number(params["awning_h"]) or params["awning_h"] < window.MIN_AWNING:
        errors["awning_h"] = f"at least {window.MIN_AWNING:g} mm"
    if params["glazing"] not in window.GLAZING_KG_M2:
        errors["glazing"] = "igu, acrylic or twinwall"
    if type(params["tier"]) is not int or params["tier"] not in (1, 2, 3):
        errors["tier"] = "1, 2 or 3"
    if not isinstance(params["screen"], bool):
        errors["screen"] = "true or false"
    bed = params["bed"]
    if not (isinstance(bed, list) and len(bed) == 3 and all(is_number(v) and BED_RANGE[0] <= v <= BED_RANGE[1] for v in bed)):
        errors["bed"] = f"three sizes, {BED_RANGE[0]}-{BED_RANGE[1]} mm each"
    lo, hi = window.PANE_RANGE
    if "max_pane" in params and not (isinstance(params["max_pane"], list) and len(params["max_pane"]) == 2
                                     and all(is_number(v) and lo <= v <= hi for v in params["max_pane"])):
        errors["max_pane"] = f"two sizes, {lo}-{hi} mm each"
    if "bays" in params and (type(params["bays"]) is not int or params["bays"] < 1):
        errors["bays"] = "a whole number, 1 or more"
    for key, (lo, hi) in (("acrylic_t", window.ACRYLIC_T_RANGE), ("acrylic_gap", window.ACRYLIC_GAP_RANGE)):
        if key in params and not (is_number(params[key]) and lo <= params[key] <= hi):
            errors[key] = f"{lo}-{hi} mm"
    if "core" in params and params["core"] != "vslot":
        errors["core"] = "vslot, or leave it out for standard tubes"
    if "vslot_stock" in params:
        lo, hi = window.VSLOT_STOCK_RANGE
        if "core" not in params:
            errors["vslot_stock"] = "only with core vslot"
        elif not (is_number(params["vslot_stock"]) and lo <= params["vslot_stock"] <= hi):
            errors["vslot_stock"] = f"{lo}-{hi} mm"
    return params, errors


def error_field(msg):
    if msg.startswith("fixed pane height"):
        return "awning_h"
    return next((k for k in (*DEFAULTS, *OPTIONAL) if msg.startswith(k)), "_form")


def checks(lay, plist):
    return lay["checks"] + [generate.bed_fit(lay, plist)]


def part_rows(plist):
    return [{"id": pt["id"], "name": PART_NAMES.get(pt["id"], pt["id"]), "qty": pt["qty"], "length": pt["length"],
             "role": pt["role"]} for pt in plist]


def preview(raw):
    params, errors = validate(raw)
    out = {"ok": False, "errors": errors, "params": params}
    if set(errors) - {"name"}:
        return out
    try:
        lay = window.layout(params)
        plist = generate.parts(lay)
    except ValueError as e:
        errors[error_field(str(e))] = str(e)
        return out
    out.update(ok=not errors, layout={k: lay[k] for k in SUMMARY_KEYS}, checks=checks(lay, plist),
               parts=part_rows(plist), bom=build_bom.hardware(lay, plist), drawing=drawing.front(lay),
               assembly=drawing.assembly(lay, plist), weight=weight.estimate(params, lay, plist))
    return out


def params_path(name, root=ROOT):
    if not isinstance(name, str) or not NAME_RE.fullmatch(name):
        raise ValueError(f"bad window name {name!r}")
    return pathlib.Path(root) / "params" / f"{name}.json"


def dumps_params(params):
    return "{\n" + ",\n".join(f"  {json.dumps(k)}: {json.dumps(v)}" for k, v in params.items()) + "\n}\n"


def save_params(params, root=ROOT):
    path = params_path(params["name"], root)
    if path.exists():
        saved, wanted = {**DEFAULTS, **json.loads(path.read_text())}, {**DEFAULTS, **params}
        if saved == wanted:
            return path, False
        if params["name"] in REFERENCE_NAMES:
            differ = sorted(k for k in saved.keys() | wanted.keys() if k not in saved or k not in wanted or saved[k] != wanted[k])
            raise ValueError(f"{params['name']} is a reference window (differs in: {', '.join(differ)}); pick another name")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(dumps_params(params))
    return path, True


def read_params(name, root=ROOT):
    path = params_path(name, root)
    try:
        return path.read_bytes()
    except FileNotFoundError:
        raise LookupError(f"no params/{name}.json") from None


def load(name, root=ROOT, raw=None):
    params = json.loads(read_params(name, root) if raw is None else raw)
    lay = window.layout(params)
    return params, lay, generate.parts(lay)


def stl_dir(name, root=ROOT):
    return pathlib.Path(root) / "cad" / "stl" / params_path(name, root).stem


def clear_stls(name, root=ROOT):
    for f in stl_dir(name, root).glob("*.stl"):
        f.unlink(missing_ok=True)


def check_part(name, lay, pt, root=ROOT):
    row = {"id": pt["id"], "length": "" if pt["length"] is None else str(pt["length"])}
    return check_stl.check(row, stl_dir(name, root), lay["bed"])


def part_status(name, lay, plist, root=ROOT):
    return {pt["id"]: check_part(name, lay, pt, root) for pt in plist}


def write_bom(name, lay, plist, out, ok_ids=None, root=ROOT):
    ok = [pt for pt in plist if ok_ids is None or pt["id"] in ok_ids]
    fil, missing = build_bom.filament(lay, ok, stl_dir(name, root))
    missing += [pt["id"] for pt in plist if pt not in ok]
    pathlib.Path(out).mkdir(parents=True, exist_ok=True)
    build_bom.write(name, lay, plist, build_bom.hardware(lay, plist) + fil, missing, out)


def build_zip(name, partial=False, root=ROOT):
    raw = read_params(name, root)
    params, lay, plist = load(name, root, raw)
    status = part_status(name, lay, plist, root)
    missing = [pid for pid, errs in status.items() if errs]
    if missing and not partial:
        raise NotReady(f"not every part passed its STL check: {', '.join(missing)}")
    ok = [pt for pt in plist if pt["id"] not in missing]
    files = {"README.txt": zipper.readme(name, params, checks(lay, plist), missing, weight.estimate(params, lay, plist))}
    with tempfile.TemporaryDirectory() as tmp:
        write_bom(name, lay, plist, tmp, {pt["id"] for pt in ok}, root)
        for arc, src in (("parts.csv", "-parts.csv"), ("cutlist.csv", "-cutlist.csv"), ("glass.csv", "-glass.csv"),
                         ("BOM.md", ".md")):
            files[arc] = (pathlib.Path(tmp) / f"{name}{src}").read_bytes()
    for pt in ok:
        files[f"stl/{pt['id']}_x{pt['qty']}.stl"] = (stl_dir(name, root) / f"{pt['id']}.stl").read_bytes()
    guide = pathlib.Path(root) / "OpenWindow-Guide.pdf"
    if not guide.is_file():
        guide = ROOT / "OpenWindow-Guide.pdf"
    if guide.is_file():
        files["OpenWindow-Guide.pdf"] = guide.read_bytes()
    files["params.json"] = raw
    return f"{name}-openwindow.zip", zipper.build(files)
