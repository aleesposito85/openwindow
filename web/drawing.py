"""Window geometry for the browser: the dimensioned front view and the assembled-view part placements."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "tools"))

from window import D  # noqa: E402

I4 = [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]
MX = [[-1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]
MZ = [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, -1, 0], [0, 0, 0, 1]]


def fmt(v):
    return f"{v:g}"


def rect(kind, x, y, w, h):
    return {"kind": kind, "x": x, "y": y, "w": w, "h": h}


def bay_x(lay, i):
    return D["FRAME_W"] if i == 0 else lay["mullions"][i - 1] + D["MULLION_W"] / 2


def body_x(lay, i):
    return D["FRAME_BODY"] if i == 0 else lay["mullions"][i - 1] + D["MULLION_HALF_BODY"]


def glass_x(lay, i):
    return D["GLASS_EDGE"] if i == 0 else lay["mullions"][i - 1] + D["TRANSOM_GLASS"]


def front(lay):
    p = lay["params"]
    F, T = D["FRAME_W"], D["TRANSOM_W"]
    g, w, h, tc = p["fix_gap"], lay["w"], lay["h"], lay["transom_c"]
    tb = tc - T / 2
    sy = tc + D["TRANSOM_HALF_BODY"] + D["SASH_GAP"]
    sw, sh = lay["sash"]
    fgw, fgh = lay["glass"]["fixed"]
    sgw, sgh = lay["glass"]["sash"]
    bays = lay["bays"]
    rects = [
        rect("opening", -g, -g, w + 2 * g, h + 2 * g),
        rect("frame", 0, h - F, w, F),
        rect("frame", 0, 0, w, F),
        rect("frame", 0, F, F, h - 2 * F),
        rect("frame", w - F, F, F, h - 2 * F),
        rect("transom", F, tb, w - 2 * F, T),
    ]
    for c in lay["mullions"]:
        rects += [rect("mullion", c - D["MULLION_W"] / 2, F, D["MULLION_W"], tb - F),
                  rect("mullion", c - D["MULLION_W"] / 2, tb + T, D["MULLION_W"], h - F - tb - T)]
    for i in range(bays):
        x = body_x(lay, i) + D["SASH_GAP"]
        rects += [rect("glass", glass_x(lay, i), D["GLASS_EDGE"], fgw, fgh), rect("sash", x, sy, sw, sh),
                  rect("sash-glass", x + D["SASH_GLASS"], sy + D["SASH_GLASS"], sgw, sgh)]
    if lay["has_screen"]:
        scw, sch = lay["screen"]
        top = h - D["FRAME_BODY"] + D["SCREEN_OVERLAP"]
        rects += [rect("screen", body_x(lay, i) - D["SCREEN_OVERLAP"], top - sch, scw, sch) for i in range(bays)]
    step = round(max(w, h) * 0.06)
    left, right = -g - step, w + g + step
    dims = [
        {"axis": "x", "a": -g, "b": w + g, "from": -g, "at": -g - 2 * step, "text": f"opening {fmt(p['opening_w'])}"},
        {"axis": "x", "a": 0, "b": w, "from": 0, "at": -g - step, "text": f"frame {fmt(w)}"},
        {"axis": "y", "a": -g, "b": h + g, "from": -g, "at": left - step, "text": f"opening {fmt(p['opening_h'])}"},
        {"axis": "y", "a": 0, "b": h, "from": 0, "at": left, "text": f"frame {fmt(h)}"},
        {"axis": "y", "a": 0, "b": tc, "from": w, "at": right, "text": f"transom centre {fmt(tc)}"},
        {"axis": "y", "a": tb + T, "b": h - F, "from": w, "at": right + step, "text": f"awning {fmt(p['awning_h'])}"},
        {"axis": "y", "a": F, "b": tb, "from": w, "at": right + step, "text": f"fixed {fmt(tb - F)}"},
    ]
    sand = lay["sandwich"]
    pane = f", {sand['t']:g} + {sand['gap']:g} + {sand['t']:g}" if p["glazing"] == "acrylic" and sand["custom"] else ""
    labels = [
        {"x": w / 2, "y": (F + tb) / 2, "text": f"fixed glass {fgw} x {fgh}{pane}"},
        {"x": w / 2, "y": sy + sh / 2, "text": f"sash {fmt(sw)} x {fmt(sh)}, glass {sgw} x {sgh}"},
    ]
    margin = step * 1.5
    top_dim = 0
    if bays > 1:
        run = lay["bay_w"]
        dims.append({"axis": "x", "a": F, "b": F + run, "from": h, "at": h + g + step, "text": f"bay {fmt(round(run, 1))}"})
        labels = []
        for i in range(bays):
            cx = bay_x(lay, i) + run / 2
            labels += [{"x": cx, "y": (F + tb) / 2 + step * 0.3, "text": "fixed glass"},
                       {"x": cx, "y": (F + tb) / 2 - step * 0.3, "text": f"{fgw} x {fgh}{pane}"},
                       {"x": cx, "y": sy + sh / 2 + step * 0.3, "text": "sash glass"},
                       {"x": cx, "y": sy + sh / 2 - step * 0.3, "text": f"{sgw} x {sgh}"}]
        top_dim = step
    bounds = [left - step - margin, -g - 2 * step - margin, right + step + margin, h + g + top_dim + margin]
    return {"rects": rects, "dims": dims, "labels": labels, "bounds": bounds, "step": step}


def mul(a, b):
    return [[sum(a[i][k] * b[k][j] for k in range(4)) for j in range(4)] for i in range(4)]


def chain(*ms):
    out = I4
    for m in ms:
        out = mul(out, m)
    return out


def move(x, y, z):
    return [[1, 0, 0, x], [0, 1, 0, y], [0, 0, 1, z], [0, 0, 0, 1]]


def run(rows):
    return [list(r) for r in rows] + [[0, 0, 0, 1]]


def flat(m):
    return [round(v, 4) + 0.0 for row in m for v in row]


def assembly(lay, plist):
    F, TW, S = D["FRAME_W"], D["TRANSOM_W"], D["SASH_W"]
    W, H = lay["w"], lay["h"]
    tb = lay["transom_c"] - TW / 2
    sy = lay["transom_c"] + D["TRANSOM_HALF_BODY"] + D["SASH_GAP"]
    sw, sh = lay["sash"]
    m = {x["name"]: x for x in lay["members"]}
    bays = range(lay["bays"])
    offsets = [bay_x(lay, i) - F for i in bays]
    runs = [
        ("sill", [[0, 0, 1, F], [0, 1, 0, 0], [1, 0, 0, 0]], "SW", "S", offsets),
        ("head", [[0, 0, 1, F], [0, 1, 0, 0], [-1, 0, 0, H]], "H", "H", offsets),
        ("transom", [[0, 0, 1, F], [0, 1, 0, 0], [1, 0, 0, tb]], "TE", "T", offsets),
        ("jamb_lower", [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, F]], "JL", "JL", [0]),
        ("jamb_lower", [[-1, 0, 0, W], [0, 1, 0, 0], [0, 0, 1, F]], "JL", "JL", [0]),
        ("jamb_upper", [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, tb + TW]], "JU", "JU", [0]),
        ("jamb_upper", [[-1, 0, 0, W], [0, 1, 0, 0], [0, 0, 1, tb + TW]], "JU", "JU", [0]),
    ]
    for c in lay["mullions"]:
        runs += [("mullion_lower", [[1, 0, 0, c - D["MULLION_W"] / 2], [0, 1, 0, 0], [0, 0, 1, F]], "ML", "ML", [0]),
                 ("mullion_upper", [[1, 0, 0, c - D["MULLION_W"] / 2], [0, 1, 0, 0], [0, 0, 1, tb + TW]], "MU", "MU", [0])]
    for i in bays:
        sx = body_x(lay, i) + D["SASH_GAP"]
        runs += [
            ("sash_horizontal", [[0, 0, 1, sx + S], [0, 1, 0, 0], [1, 0, 0, sy]], "SBE", "SB", [0]),
            ("sash_horizontal", [[0, 0, 1, sx + S], [0, 1, 0, 0], [-1, 0, 0, sy + sh]], "SH", "SH", [0]),
            ("sash_vertical", [[1, 0, 0, sx], [0, 1, 0, 0], [0, 0, 1, sy + S]], "SV", "SV", [0]),
            ("sash_vertical", [[-1, 0, 0, sx + sw], [0, 1, 0, 0], [0, 0, 1, sy + S]], "SV", "SV", [0]),
        ]
    out = []
    for name, rows, end_id, mid_id, offs in runs:
        mem = m[name]
        for off in offs:
            for i in range(mem["n"]):
                pid = end_id if i in (0, mem["n"] - 1) else mid_id
                out.append({"id": pid, "m": flat(chain(run(rows), move(0, 0, off + mem["gap"] + i * (mem["seg"] + mem["gap"]))))})
    shoe = run([[0, 0, 1, D["FRAME_BODY"]], [0, 1, 0, 0], [-1, 0, 0, TW]])
    shoe_flip = run([[-1, 0, 0, TW], [0, 1, 0, 0], [0, 0, 1, 0]])
    fixed = [
        ("CSL", I4), ("CSR", move(W, 0, 0)),
        ("CH", chain(move(0, 0, H), MZ)), ("CH", chain(move(W, 0, H), MX, MZ)),
        ("JN", move(0, 0, tb)), ("JN", chain(move(W, 0, tb), MX)),
        ("TSL", chain(move(0, 0, tb), shoe)), ("TSR", chain(move(W, 0, tb), MX, shoe, shoe_flip)),
    ]
    for i in bays:
        sx = body_x(lay, i) + D["SASH_GAP"]
        fixed += [("CS", move(sx, 0, sy)), ("CS", chain(move(sx + sw, 0, sy), MX)),
                  ("CS", chain(move(sx, 0, sy + sh), MZ)), ("CS", chain(move(sx + sw, 0, sy + sh), MX, MZ))]
    tl, th = TW / 2 - D["TRANSOM_HALF_BODY"], TW / 2 + D["TRANSOM_HALF_BODY"]
    for c in lay["mullions"]:
        x0, x1 = c - D["MULLION_W"] / 2, c + D["MULLION_W"] / 2
        fixed += [
            ("SN", run([[0, 0, 1, x0], [0, 1, 0, 0], [1, 0, 0, 0]])),
            ("HN", run([[0, 0, 1, x0], [0, 1, 0, 0], [-1, 0, 0, H]])),
            ("TX", run([[0, 0, 1, x0], [0, 1, 0, 0], [1, 0, 0, tb]])),
            ("MSL", move(x0, 0, D["FRAME_BODY"])),
            ("MSL", run([[-1, 0, 0, x1], [0, 1, 0, 0], [0, 0, -1, tb + tl]])),
            ("MST", move(x0, 0, tb + th)),
            ("MSH", run([[-1, 0, 0, x1], [0, 1, 0, 0], [0, 0, -1, H - D["FRAME_BODY"]]])),
        ]
    ids = {pt["id"] for pt in plist}
    out += [{"id": pid, "m": flat(mat)} for pid, mat in fixed if pid in ids]
    return [x for x in out if x["id"] in ids]
