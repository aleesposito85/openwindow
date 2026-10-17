#!/usr/bin/env python3
"""Build the OpenWindow guide deck: slides (Markdown-ish text, renders, live BOM numbers) -> HTML (stdlib) -> headless Chrome PDF."""
import argparse
import concurrent.futures
import csv
import datetime
import html
import json
import math
import os
import pathlib
import re
import struct
import subprocess
import sys
import tempfile
import time
import zlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
PDF_DIR = ROOT / "pdf"
OUT_HTML = PDF_DIR / "openwindow-deck.html"
OUT_PDF = ROOT / "OpenWindow-Guide.pdf"
IMG = ROOT / "docs" / "img"
DECK = IMG / "deck"
BOX_CACHE = pathlib.Path(tempfile.gettempdir()) / "openwindow-deck-imgbox.json"
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
SLIDE_W, SLIDE_H = 1280, 720
RENDER_W, RENDER_H = 1600, 1000
RENDER_BG = (248, 248, 248)

sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "bom"))
import build_bom  # noqa: E402
import generate  # noqa: E402
import stl  # noqa: E402
import window  # noqa: E402

D = window.D
HOME, BENCH, TWO_BAY = "home-1800x1500", "bench-600", "home-1800x1500-2bay"

SECTIONS = {
    "overview": ("Overview", "#1f6f78"),
    "how": ("How it works", "#2f5d9a"),
    "materials": ("Materials", "#8a6326"),
    "size": ("Size it", "#6a4c93"),
    "print": ("Printing", "#c0631a"),
    "shop": ("Shopping list", "#2e7d4f"),
    "build": ("Bench assembly", "#b23a48"),
    "install": ("Installation", "#3f5866"),
    "manual": ("User manual", "#00808a"),
    "test": ("Testing", "#7a6500"),
    "appendix": ("Appendices", "#5f6368"),
}

PART_NAMES = {
    "H": "Head segment, hinge inserts", "S": "Sill segment", "SW": "Sill segment with weep",
    "JL": "Lower jamb segment", "JU": "Upper jamb segment", "T": "Transom segment",
    "TE": "Transom end: weep, cam inserts", "SH": "Sash top segment", "SB": "Sash bottom segment",
    "SBE": "Sash bottom end: weep, keeper inserts", "SV": "Sash side segment", "NH": "Screen horizontal segment",
    "NV": "Screen vertical segment", "CH": "Head corner", "CSL": "Sill corner, left", "CSR": "Sill corner, right",
    "CS": "Sash corner", "CN": "Screen corner", "JN": "Jamb node (transom slot)", "TSL": "Transom shoe, left",
    "TSR": "Transom shoe, right", "GW": "Wedge setting block", "GF": "Flat setting block / locator",
    "WC": "Weep cap", "NS": "Sill nose", "CMB": "Cam base", "CMH": "Cam handle", "KP": "Cam keeper",
    "HG": "Hinge leaf, frame", "HS": "Hinge leaf, screen", "TC": "Test coupon",
    "BFH": "Fixed-pane bead, horizontal", "BFV": "Fixed-pane bead, vertical", "BSH": "Sash bead, horizontal",
    "BSV": "Sash bead, vertical", "SN": "Sill node (mullion slot)", "HN": "Head node (mullion slot)",
    "TX": "Transom cross-node", "MSL": "Lower mullion shoe", "MST": "Upper mullion shoe, transom end",
    "MSH": "Upper mullion shoe, head end", "ML": "Lower mullion segment", "MU": "Upper mullion segment",
    "AFH": "Acrylic spacer, fixed, horiz.", "AFV": "Acrylic spacer, fixed, vert.",
    "ASH": "Acrylic spacer, sash, horiz.", "ASV": "Acrylic spacer, sash, vert.", "AC": "Acrylic spacer corner",
}
GALLERY_ORDER = ["H", "S", "SW", "JL", "JU", "CH", "CSL", "CSR", "JN", "NS",
                 "T", "TE", "TSL", "TSR", "SH", "SB", "SBE", "SV", "CS", "TC",
                 "NH", "NV", "CN", "HG", "HS", "CMB", "CMH", "KP", "WC", "GW",
                 "GF", "BFH", "BFV", "BSH", "BSV", "AFH", "AFV", "ASH", "ASV", "AC"]
FAMILIES = [
    ("Frame segments", ["H", "S", "SW", "JL", "JU"]),
    ("Frame corners, nodes, nose", ["CH", "CSL", "CSR", "JN", "NS"]),
    ("Transom", ["T", "TE", "TSL", "TSR"]),
    ("Sash", ["SH", "SB", "SBE", "SV", "CS"]),
    ("Beads", ["BFH", "BFV", "BSH", "BSV"]),
    ("Screen and hinges", ["NH", "NV", "CN", "HG", "HS"]),
    ("Small parts", ["GW", "GF", "WC", "CMB", "CMH", "KP", "TC"]),
    ("Acrylic spacers", ["AFH", "AFV", "ASH", "ASV", "AC"]),
]


def fmt(x):
    if isinstance(x, str):
        x = float(x)
    if abs(x - round(x)) < 1e-9:
        return f"{int(round(x))}"
    return f"{x:.2f}".rstrip("0").rstrip(".")


def esc(s):
    return html.escape(str(s), quote=True)


def read_csv(path):
    with path.open(newline="") as fh:
        return list(csv.DictReader(fh))


class Window:
    def __init__(self, name):
        self.name = name
        self.params = json.loads((ROOT / "params" / f"{name}.json").read_text())
        self.lay = window.layout(self.params)
        self.parts = generate.parts(self.lay)
        self.bom = read_csv(ROOT / "bom" / f"{name}.csv")
        self.part_rows = read_csv(ROOT / "bom" / f"{name}-parts.csv")
        self.cut = read_csv(ROOT / "bom" / f"{name}-cutlist.csv")
        self.glass = read_csv(ROOT / "bom" / f"{name}-glass.csv")
        live = [(p["id"], p["qty"]) for p in self.parts]
        filed = [(r["id"], int(r["qty"])) for r in self.part_rows]
        if live != filed:
            sys.exit(f"bom/{name}-parts.csv is out of date: run python3 bom/build_bom.py {name}")
        self.qty = dict(filed)
        self.role = {r["id"]: r["role"] for r in self.part_rows}
        self.members = {m["name"]: m for m in self.lay["members"]}

    def item(self, needle):
        rows = [r for r in self.bom if needle in r["item"]]
        if len(rows) != 1:
            sys.exit(f"bom/{self.name}.csv: expected one line containing {needle!r}, found {len(rows)}")
        return rows[0]

    def q(self, needle):
        return fmt(self.item(needle)["qty"])

    @property
    def prints(self):
        return sum(self.qty.values())

    @property
    def types(self):
        return len(self.qty)

    def filament(self):
        rows = [r for r in self.bom if r["group"] == "Filament"]
        inner = [r for r in rows if "(interior)" in r["item"]][0]
        outer = [r for r in rows if "exterior" in r["item"]][0]
        return float(outer["qty"]), float(inner["qty"]), outer["item"]

    def glass_size(self, pane):
        r = [g for g in self.glass if g["pane"] == pane][0]
        return int(r["width_mm"]), int(r["height_mm"])

    def tube(self, member):
        return [t for t in self.cut if t["member"] == member][0]

    def check(self, name):
        return [c for c in self.lay["checks"] if c["name"] == name][0]

    def part_mass_g(self):
        out = {}
        tier = self.params["tier"]
        for pid, role in self.role.items():
            f = ROOT / "cad" / "stl" / self.name / f"{pid}.stl"
            if not f.exists():
                continue
            vol, area = stl.volume_area(stl.load(f))
            out[pid] = build_bom.mass_g(vol, area, build_bom.DENSITY["interior" if role == "interior" else tier])
        return out


def png_rows(path):
    d = path.read_bytes()
    i, idat = 8, b""
    while i < len(d):
        n, t = struct.unpack(">I4s", d[i:i + 8])
        c = d[i + 8:i + 8 + n]
        i += 12 + n
        if t == b"IHDR":
            w, h, _, ct = struct.unpack(">IIBB", c[:10])
        elif t == b"IDAT":
            idat += c
    bpp = 4 if ct == 6 else 3
    raw = zlib.decompress(idat)
    st = w * bpp
    prev = bytearray(st)
    p = 0
    for _ in range(h):
        f = raw[p]
        line = bytearray(raw[p + 1:p + 1 + st])
        p += 1 + st
        if f == 1:
            for x in range(bpp, st):
                line[x] = (line[x] + line[x - bpp]) & 255
        elif f == 2:
            line = bytearray((a + b) & 255 for a, b in zip(line, prev))
        elif f == 3:
            for x in range(st):
                line[x] = (line[x] + ((line[x - bpp] if x >= bpp else 0) + prev[x]) // 2) & 255
        elif f == 4:
            for x in range(st):
                a = line[x - bpp] if x >= bpp else 0
                b = prev[x]
                c = prev[x - bpp] if x >= bpp else 0
                pa, pb, pc = abs(b - c), abs(a - c), abs(a + b - 2 * c)
                line[x] = (line[x] + (a if pa <= pb and pa <= pc else b if pb <= pc else c)) & 255
        yield w, h, bpp, line
        prev = line


def content_box(path):
    xs0, ys0, xs1, ys1 = 10 ** 9, 10 ** 9, -1, -1
    bg = bytes(RENDER_BG)
    for y, (w, h, bpp, line) in enumerate(png_rows(path)):
        row = bytes(line)
        if bpp == 3 and row == bg * w:
            continue
        hit = [x for x in range(w) if abs(row[x * bpp] - 248) > 6 or abs(row[x * bpp + 1] - 248) > 6 or abs(row[x * bpp + 2] - 248) > 6]
        if hit:
            xs0, xs1 = min(xs0, hit[0]), max(xs1, hit[-1])
            ys0, ys1 = min(ys0, y), max(ys1, y)
    return [xs0, ys0, xs1, ys1] if xs1 >= 0 else [0, 0, RENDER_W, RENDER_H]


class Boxes:
    def __init__(self):
        self.data = json.loads(BOX_CACHE.read_text()) if BOX_CACHE.exists() else {}
        self.dirty = False

    def get(self, path):
        key = str(path.relative_to(ROOT))
        st = path.stat()
        stamp = f"{st.st_size}:{int(st.st_mtime)}"
        hit = self.data.get(key)
        if not hit or hit["stamp"] != stamp:
            hit = {"stamp": stamp, "box": content_box(path)}
            self.data[key] = hit
            self.dirty = True
        return hit["box"]

    def save(self):
        if self.dirty:
            BOX_CACHE.write_text(json.dumps(self.data, indent=1, sort_keys=True))


BOXES = Boxes()
USED_IMAGES = set()


def rel(path):
    USED_IMAGES.add(path)
    return os.path.relpath(path, PDF_DIR)


def fig(path, w, h, pad=0.05, cap=None, box=None, extra=""):
    path = pathlib.Path(path)
    if not path.exists():
        sys.exit(f"missing image {path}")
    x0, y0, x1, y1 = box or BOXES.get(path)
    cw, ch = x1 - x0 + 1, y1 - y0 + 1
    m = pad * max(cw, ch)
    bx, by, bw, bh = x0 - m, y0 - m, cw + 2 * m, ch + 2 * m
    if bw / bh < w / h:
        nw = bh * w / h
        bx -= (nw - bw) / 2
        bw = nw
    else:
        nh = bw * h / w
        by -= (nh - bh) / 2
        bh = nh
    svg = (f'<svg viewBox="{bx:.1f} {by:.1f} {bw:.1f} {bh:.1f}" preserveAspectRatio="xMidYMid meet">'
           f'<image href="{esc(rel(path))}" x="0" y="0" width="{RENDER_W}" height="{RENDER_H}"/>{extra}</svg>')
    out = f'<div class="fig" style="width:{w}px;height:{h}px">{svg}</div>'
    if cap:
        out = f'<figure style="width:{w}px">{out}<figcaption>{inline(cap)}</figcaption></figure>'
    return out


class Ortho:
    def __init__(self, dist, cu, cv):
        self.s = RENDER_H / (2 * math.tan(math.radians(11.25)) * dist)
        self.cu, self.cv = cu, cv

    def px(self, u, v):
        return RENDER_W / 2 + (u - self.cu) * self.s, RENDER_H / 2 - (v - self.cv) * self.s


def overlay_fig(path, cam, urange, vrange, disp_h, badges, dims=(), cap=None, legend_cls=""):
    x0, y0 = cam.px(urange[0], vrange[1])
    x1, y1 = cam.px(urange[1], vrange[0])
    vb = (x0, y0, x1 - x0, y1 - y0)
    disp_w = round(disp_h * vb[2] / vb[3])
    k = vb[3] / disp_h
    parts = []
    spans = []
    for n, b, t in badges:
        bx, by = cam.px(*b)
        if t is not None:
            tx, ty = cam.px(*t)
            parts.append(f'<line x1="{bx:.1f}" y1="{by:.1f}" x2="{tx:.1f}" y2="{ty:.1f}" stroke="#1f3b57" stroke-width="{1.6 * k:.2f}"/>'
                         f'<circle cx="{tx:.1f}" cy="{ty:.1f}" r="{3.2 * k:.2f}" fill="#1f3b57"/>')
        spans.append(f'<span class="badge" style="left:{(bx - vb[0]) / vb[2] * 100:.2f}%;top:{(by - vb[1]) / vb[3] * 100:.2f}%">{esc(n)}</span>')
    for (ua, va), (ub, vb_), label, (lu, lv) in dims:
        ax, ay = cam.px(ua, va)
        bx, by = cam.px(ub, vb_)
        lx, ly = cam.px(lu, lv)
        parts.append(f'<line x1="{ax:.1f}" y1="{ay:.1f}" x2="{bx:.1f}" y2="{by:.1f}" stroke="#b23a48" stroke-width="{1.4 * k:.2f}" stroke-dasharray="{5 * k:.1f} {3 * k:.1f}"/>')
        spans.append(f'<span class="dimlabel" style="left:{(lx - vb[0]) / vb[2] * 100:.2f}%;top:{(ly - vb[1]) / vb[3] * 100:.2f}%">{esc(label)}</span>')
    path = pathlib.Path(path)
    svg = (f'<svg viewBox="{vb[0]:.1f} {vb[1]:.1f} {vb[2]:.1f} {vb[3]:.1f}" preserveAspectRatio="xMidYMid meet">'
           f'<image href="{esc(rel(path))}" x="0" y="0" width="{RENDER_W}" height="{RENDER_H}"/>{"".join(parts)}</svg>')
    out = f'<div class="fig ofig" style="width:{disp_w}px;height:{disp_h}px">{svg}{"".join(spans)}</div>'
    if cap:
        out = f'<figure style="width:{disp_w}px">{out}<figcaption>{inline(cap)}</figcaption></figure>'
    return out, disp_w


def inline(text):
    holders = []

    def hold(s):
        holders.append(s)
        return f"\x00{len(holders) - 1}\x00"

    text = re.sub(r"`([^`]+)`", lambda m: hold(f"<code>{esc(m.group(1))}</code>"), text)
    text = re.sub(r"\[\[([A-Za-z0-9/ ]+?)\]\]", lambda m: hold("".join(f'<span class="id">{esc(x)}</span>' for x in m.group(1).split("/"))), text)
    text = html.escape(text, quote=False)
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"(?<![\*\w])\*(?!\s)(.+?)(?<!\s)\*(?![\*\w])", r"<em>\1</em>", text)
    while "\x00" in text:
        text = re.sub(r"\x00(\d+)\x00", lambda m: holders[int(m.group(1))], text)
    return text


def chipify(text):
    ids = sorted(set(PART_NAMES) | {"S", "T"}, key=len, reverse=True)
    pat = r"(?<![\w`\[])`(" + "|".join(ids) + r")`(?![\w`])"
    return re.sub(pat, r"[[\1]]", text)


def md_table(rows, cls=""):
    def cells(r):
        r = r.strip().strip("|")
        return [c.strip() for c in r.split("|")]
    head = cells(rows[0])
    body = [cells(r) for r in rows[2:]]
    out = [f'<table class="{cls}"><thead><tr>' + "".join(f"<th>{inline(c)}</th>" for c in head) + "</tr></thead><tbody>"]
    for r in body:
        out.append("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in r) + "</tr>")
    out.append("</tbody></table>")
    return "".join(out)


def md_list(lines, steps=False):
    items = []
    for ln in lines:
        m = re.match(r"^(\s*)([-*]|\d+\.)\s+(.*)", ln)
        if m:
            num = int(m.group(2)[:-1]) if m.group(2)[-1] == "." else 1
            items.append([len(m.group(1)), m.group(2)[-1] == ".", m.group(3), num])
        elif items and ln.strip():
            items[-1][2] += " " + ln.strip()
    out, stack = [], []
    for indent, ordered, text, num in items:
        while stack and indent < stack[-1][0]:
            out.append("</li></%s>" % ("ol" if stack.pop()[1] else "ul"))
        if not stack or indent > stack[-1][0]:
            tag = "ol" if ordered else "ul"
            cls = ' class="steps"' if ordered and steps and not stack else ""
            start = f' start="{num}" style="counter-reset: st {num - 1}"' if ordered and num != 1 else ""
            out.append(f"<{tag}{cls}{start}>")
            stack.append((indent, ordered))
        else:
            out.append("</li>")
        out.append(f"<li>{inline(text)}")
    while stack:
        out.append("</li></%s>" % ("ol" if stack.pop()[1] else "ul"))
    return "".join(out)


CALLOUTS = {"!!": "warn", "??": "note", "++": "tip"}


def md(text, steps=False, table_cls=""):
    lines = text.strip("\n").splitlines()
    out, i = [], 0
    while i < len(lines):
        ln = lines[i]
        s = ln.strip()
        if not s:
            i += 1
            continue
        if s.startswith("```"):
            j = i + 1
            while j < len(lines) and not lines[j].strip().startswith("```"):
                j += 1
            out.append("<pre>" + esc("\n".join(x for x in lines[i + 1:j])) + "</pre>")
            i = j + 1
            continue
        m = re.match(r"^(#{2,4})\s+(.*)", s)
        if m:
            lvl = len(m.group(1)) + (1 if len(m.group(1)) == 2 else 0)
            out.append(f"<h{min(lvl, 4)}>{inline(m.group(2))}</h{min(lvl, 4)}>")
            i += 1
            continue
        if s[:2] in CALLOUTS:
            kind = CALLOUTS[s[:2]]
            j = i
            buf = []
            while j < len(lines) and lines[j].strip().startswith(s[:2]):
                buf.append(lines[j].strip()[2:].strip())
                j += 1
            out.append(f'<div class="callout {kind}">{inline(" ".join(buf))}</div>')
            i = j
            continue
        if s.startswith("|"):
            j = i
            while j < len(lines) and lines[j].strip().startswith("|"):
                j += 1
            out.append(md_table([x.strip() for x in lines[i:j]], table_cls))
            i = j
            continue
        if re.match(r"^\s*([-*]|\d+\.)\s+", ln):
            j = i
            while j < len(lines):
                l2 = lines[j]
                if not l2.strip():
                    nxt = lines[j + 1] if j + 1 < len(lines) else ""
                    if re.match(r"^\s+\S", nxt) or re.match(r"^\s*([-*]|\d+\.)\s+", nxt):
                        j += 1
                        continue
                    break
                if not (re.match(r"^\s*([-*]|\d+\.)\s+", l2) or l2.startswith(" ")):
                    break
                j += 1
            out.append(md_list(lines[i:j], steps))
            i = j
            continue
        j = i
        para = []
        while j < len(lines) and lines[j].strip() and not re.match(r"^(#|\||```|!!|\?\?|\+\+|\s*([-*]|\d+\.)\s+)", lines[j].strip()):
            para.append(lines[j].strip())
            j += 1
        out.append(f"<p>{inline(' '.join(para))}</p>")
        i = j
    return "\n".join(out)


def table(header, rows, cls="", widths=None):
    cols = ""
    if widths:
        cols = "<colgroup>" + "".join(f'<col style="width:{w}">' for w in widths) + "</colgroup>"
    out = [f'<table class="{cls}">{cols}<thead><tr>' + "".join(f"<th>{inline(h)}</th>" for h in header) + "</tr></thead><tbody>"]
    for r in rows:
        out.append("<tr>" + "".join(f"<td>{inline(str(c))}</td>" for c in r) + "</tr>")
    out.append("</tbody></table>")
    return "".join(out)


def kpis(items, cols=None):
    cols = cols or len(items)
    cells = "".join(f'<div class="kpi"><b>{inline(v)}</b><span>{inline(l)}</span></div>' for v, l in items)
    return f'<div class="kpis" style="grid-template-columns:repeat({cols},1fr)">{cells}</div>'


def grid(*cells, cols=None, gap=28, align="start"):
    cols = cols or " ".join(["1fr"] * len(cells))
    return (f'<div class="grid" style="grid-template-columns:{cols};gap:{gap}px;align-items:{align}">'
            + "".join(f"<div>{c}</div>" for c in cells) + "</div>")


def legend(items, start_cls=""):
    lis = "".join(f'<li><span class="badge inl">{esc(n)}</span><span>{inline(t)}</span></li>' for n, t in items)
    return f'<ul class="legend {start_cls}">{lis}</ul>'


def swatches(items):
    lis = "".join(f'<li><span class="sw" style="background:{c}"></span><span>{inline(t)}</span></li>' for c, t in items)
    return f'<ul class="legend sws">{lis}</ul>'


CSS = """
@page { size: 1280px 720px; margin: 0; }
* { box-sizing: border-box; }
html { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
body { margin: 0; background: #e9edf0; font-family: -apple-system, "SF Pro Text", "Helvetica Neue", Helvetica, Arial, sans-serif;
  font-size: 19px; line-height: 1.36; color: #1b252b; }
.slide { width: 1280px; height: 720px; position: relative; overflow: hidden; background: #fff; break-after: page; page-break-after: always; margin: 0 auto; }
.slide:last-child { break-after: auto; page-break-after: auto; }
.tab { position: absolute; left: 0; top: 0; bottom: 0; width: 12px; background: var(--sec); }
.head { position: absolute; left: 48px; right: 150px; top: 20px; }
.kicker { font-size: 13.5px; font-weight: 700; letter-spacing: .09em; text-transform: uppercase; color: var(--sec); }
h1 { font-size: 30px; line-height: 1.12; margin: 3px 0 0; color: #10202b; font-weight: 700; letter-spacing: -.01em; }
.pno { position: absolute; right: 48px; top: 24px; font-size: 15px; color: #7b878e; font-variant-numeric: tabular-nums; }
.body { position: absolute; left: 48px; right: 48px; top: 100px; bottom: 50px; overflow: hidden; }
.foot { position: absolute; left: 48px; right: 48px; bottom: 14px; height: 24px; border-top: 1px solid #e2e7ea; padding-top: 6px;
  font-size: 13px; color: #7b878e; display: flex; justify-content: space-between; }
.foot b { color: var(--sec); font-weight: 600; }
p { margin: 0 0 10px; }
h3 { font-size: 21px; margin: 0 0 8px; color: var(--sec); }
h4 { font-size: 19px; margin: 6px 0 4px; }
ul, ol { margin: 0 0 10px; padding-left: 24px; }
li { margin: 0 0 6px; }
li::marker { color: var(--sec); }
ul ul, ol ul { margin: 4px 0 0; }
ol.steps { list-style: none; padding-left: 0; counter-reset: st; }
ol.steps > li { counter-increment: st; position: relative; padding-left: 42px; margin-bottom: 9px; }
ol.steps > li::before { content: counter(st); position: absolute; left: 0; top: -1px; width: 29px; height: 29px; border-radius: 50%;
  background: var(--sec); color: #fff; font-weight: 700; font-size: 16px; line-height: 29px; text-align: center; }
code, pre, .id { font-family: "SF Mono", Menlo, Consolas, monospace; }
code { font-size: .84em; background: #eef2f4; border-radius: 4px; padding: 1px 4px; }
pre { font-size: 15.5px; line-height: 1.4; background: #f3f6f8; border: 1px solid #dfe5e9; border-radius: 8px; padding: 10px 14px; margin: 0 0 12px; white-space: pre-wrap; }
.id { display: inline-block; font-size: .8em; font-weight: 600; line-height: 1.25; padding: 1px 6px; margin: 0 1px; border-radius: 5px;
  background: #e9eff3; color: #1f3b57; border: 1px solid #c9d5dd; vertical-align: 1px; }
strong { font-weight: 650; }
.grid { display: grid; }
.callout { border-radius: 8px; padding: 9px 14px 9px 46px; margin: 0 0 12px; position: relative; font-size: 18px; line-height: 1.33; }
.callout::before { position: absolute; left: 13px; top: 8px; width: 23px; height: 23px; border-radius: 50%; color: #fff; font-weight: 800;
  font-size: 15px; line-height: 23px; text-align: center; }
.callout.warn { background: #fdecea; border: 1.5px solid #e2a29a; }
.callout.warn::before { content: "!"; background: #c0392b; }
.callout.note { background: #eaf2fb; border: 1.5px solid #a9c4e4; }
.callout.note::before { content: "i"; background: #2f5d9a; font-family: Georgia, serif; }
.callout.tip { background: #eaf6ee; border: 1.5px solid #9fd0ad; }
.callout.tip::before { content: "\\2713"; background: #2e7d4f; }
table { border-collapse: collapse; width: 100%; font-size: 16px; line-height: 1.3; margin: 0 0 12px; }
th { text-align: left; font-weight: 650; color: #233541; background: #eef3f6; border-bottom: 2px solid #c9d5dd; padding: 6px 9px; }
td { padding: 5px 9px; border-bottom: 1px solid #e2e8ec; vertical-align: top; }
table.num td:nth-child(n+3), table.r td.r { text-align: right; white-space: nowrap; }
table.compact td, table.compact th { padding: 4px 8px; }
table.big { font-size: 17.5px; }
td .id { font-size: .82em; }
.fig { position: relative; background: #f8f8f8; border-radius: 10px; overflow: hidden; }
.fig svg { width: 100%; height: 100%; display: block; }
figure { margin: 0; }
figcaption { font-size: 15px; color: #56636b; margin-top: 6px; line-height: 1.3; }
.badge { position: absolute; width: 26px; height: 26px; margin: -13px 0 0 -13px; border-radius: 50%; background: #1f3b57; color: #fff;
  font-size: 14px; font-weight: 700; line-height: 26px; text-align: center; box-shadow: 0 0 0 2px #fff; }
.badge.inl { position: static; display: inline-block; margin: 0; flex: 0 0 26px; box-shadow: none; }
.dimlabel { position: absolute; transform: translate(-50%, -50%); font-size: 14px; font-weight: 700; color: #b23a48; background: rgba(248,248,248,.92);
  padding: 0 4px; border-radius: 4px; white-space: nowrap; }
ul.legend { list-style: none; padding: 0; margin: 0; }
ul.legend li { display: flex; gap: 10px; align-items: flex-start; font-size: 17.5px; line-height: 1.3; margin-bottom: 8px; }
ul.legend .sw { flex: 0 0 22px; height: 22px; border-radius: 5px; border: 1px solid rgba(0,0,0,.18); margin-top: 0; }
.kpis { display: grid; gap: 12px; margin-bottom: 14px; }
.kpi { background: #f2f6f8; border-radius: 10px; padding: 10px 14px 11px; border-left: 5px solid var(--sec); }
.kpi b { display: block; font-size: 25px; line-height: 1.12; color: #12232e; font-weight: 700; }
.kpi span { display: block; font-size: 15px; line-height: 1.28; color: #4f5d65; margin-top: 3px; }
.tiles { display: grid; gap: 12px 14px; }
.tile { background: #fff; border: 1px solid #dfe5e9; border-radius: 10px; overflow: hidden; }
.tile .fig { border-radius: 0; }
.tile .t { padding: 6px 9px 8px; font-size: 15px; line-height: 1.25; }
.tile .t .nm { display: block; color: #2a3740; min-height: 37px; }
.tile .t .meta { display: flex; justify-content: space-between; color: #5b6870; font-size: 14px; margin-top: 3px; }
.role { display: inline-block; width: 10px; height: 10px; border-radius: 50%; margin-right: 5px; vertical-align: 0; }
.role.exterior { background: #c0631a; }
.role.interior { background: #2f5d9a; }
.muted { color: #5b6870; }
.small { font-size: 16px; line-height: 1.32; }
.lede { font-size: 21px; line-height: 1.35; color: #24343e; margin-bottom: 14px; }
.cover { background: linear-gradient(120deg, #0f3f46 0%, #1f6f78 58%, #2b8a8f 100%); color: #fff; }
.cover .tab { display: none; }
.cover .ct { position: absolute; left: 64px; top: 70px; width: 600px; }
.cover .ck { font-size: 15px; letter-spacing: .16em; text-transform: uppercase; opacity: .85; font-weight: 600; }
.cover h1 { color: #fff; font-size: 45px; line-height: 1.07; margin: 14px 0 18px; letter-spacing: -.02em; }
table.xl { font-size: 19px; }
.cover .sub { font-size: 21px; line-height: 1.4; opacity: .93; }
.cover .facts { margin-top: 30px; display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.cover .facts div { background: rgba(255,255,255,.1); border-radius: 10px; padding: 10px 14px; font-size: 16px; line-height: 1.3; }
.cover .facts b { display: block; font-size: 23px; }
.cover .hero { position: absolute; right: 40px; top: 52px; width: 560px; height: 560px; border-radius: 18px; overflow: hidden; background: #f8f8f8; }
.cover .cf { position: absolute; left: 64px; right: 64px; bottom: 26px; display: flex; justify-content: space-between; font-size: 15px; opacity: .85; }
.toc { columns: 2; column-gap: 56px; }
.toc .row { display: flex; align-items: baseline; gap: 12px; padding: 9px 0; border-bottom: 1px solid #e2e8ec; break-inside: avoid; font-size: 20px; }
.toc .dot { flex: 0 0 14px; height: 14px; border-radius: 4px; }
.toc .nm { flex: 1; font-weight: 600; }
.toc .rg { color: #66737a; font-variant-numeric: tabular-nums; font-size: 17px; }
.toc .ds { display: block; font-weight: 400; font-size: 15px; color: #5b6870; }
.sch { background: #fbfcfd; border: 1px solid #e2e8ec; border-radius: 10px; }
.sch svg { display: block; width: 100%; height: 100%; }
.cols2 { columns: 2; column-gap: 36px; }
.cols2 li { break-inside: avoid; }
.cols3 { columns: 3; column-gap: 30px; }
.cols3 li { break-inside: avoid; }
.overflow-flag { outline: 6px solid red; }
table.nowrap-code code { white-space: nowrap; }
table.numall td:nth-child(n+2) { text-align: right; }
table.tight { font-size: 15.5px; }
table.tight td, table.tight th { padding: 3px 8px; }
.sidefig { margin-top: 14px; }
.lg li { font-size: 20px; line-height: 1.38; margin-bottom: 9px; }
"""


SLIDES = []


def slide(sec, title, body, kicker=None):
    SLIDES.append({"sec": sec, "title": title, "body": body, "kicker": kicker})


def render_slide(i, s, total, today):
    if s["sec"] == "cover":
        return s["body"]
    name, color = SECTIONS[s["sec"]]
    kick = s["kicker"] or name
    return (f'<section class="slide" id="s{i}" style="--sec:{color}" data-n="{i}"><div class="tab"></div>'
            f'<div class="head"><div class="kicker">{esc(kick)}</div><h1>{inline(s["title"])}</h1></div>'
            f'<div class="pno">{i} / {total}</div><div class="body">{s["body"]}</div>'
            f'<div class="foot"><span>OpenWindow v1 · {today} · open source</span><b>{esc(name)}</b></div></section>')


CHECK_JS = """
<script>
window.addEventListener('load', () => {
  const bad = [];
  document.querySelectorAll('.slide').forEach(s => {
    const els = [s.querySelector('.body'), s.querySelector('.head'), ...s.querySelectorAll('.body *')].filter(Boolean);
    for (const el of els) {
      if (el.closest('svg')) continue;
      const cs = getComputedStyle(el);
      const clip = /(hidden|clip|auto|scroll)/.test(cs.overflow + cs.overflowX + cs.overflowY);
      if ((el.scrollHeight > el.clientHeight + 2 || el.scrollWidth > el.clientWidth + 2) && (clip || el.classList.contains('body'))) {
        bad.push(s.dataset.n + ':' + (el.className || el.tagName)); s.classList.add('overflow-flag'); break;
      }
    }
    const sb = s.getBoundingClientRect();
    const hb = s.querySelector('.head');
    if (hb && hb.getBoundingClientRect().bottom > sb.top + 100) { bad.push(s.dataset.n + ':head'); }
  });
  document.body.setAttribute('data-overflow', bad.join(' ') || 'none');
});
</script>
"""


def page_html(slides_html, check=False):
    return (f'<!doctype html><html lang="en-AU"><head><meta charset="utf-8"><title>OpenWindow guide</title>'
            f'<style>{CSS}</style>{CHECK_JS if check else ""}</head><body>{"".join(slides_html)}</body></html>')


def run_chrome(args, done_marker="bytes written", timeout=240, read_stdout=False):
    with tempfile.TemporaryDirectory(prefix="ow-chrome-", dir=os.environ.get("TMPDIR")) as prof:
        cmd = [CHROME, "--headless", "--disable-gpu", "--no-first-run", "--no-default-browser-check", "--hide-scrollbars",
               f"--user-data-dir={prof}", "--allow-file-access-from-files"] + args
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE if read_stdout else subprocess.DEVNULL,
                                stderr=subprocess.PIPE, text=True)
        deadline = time.time() + timeout
        out = ""
        ok = False
        try:
            if read_stdout:
                buf = []
                for line in proc.stdout:
                    buf.append(line)
                    if "</html>" in line or time.time() > deadline:
                        ok = "</html>" in line
                        break
                out = "".join(buf)
            else:
                for line in proc.stderr:
                    if done_marker in line:
                        ok = True
                        break
                    if time.time() > deadline:
                        break
        finally:
            proc.terminate()
            try:
                proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                proc.kill()
        return ok, out


def write_pdf(html_path, pdf_path):
    if pdf_path.exists():
        pdf_path.unlink()
    ok, _ = run_chrome(["--no-pdf-header-footer", f"--print-to-pdf={pdf_path}", html_path.as_uri()])
    for _ in range(50):
        if pdf_path.exists() and pdf_path.stat().st_size > 0:
            break
        time.sleep(0.1)
    if not pdf_path.exists():
        sys.exit("Chrome did not produce the PDF")


def screenshot(slide_html, out_png):
    out_png = pathlib.Path(out_png).resolve()
    tmp = PDF_DIR / f".slide-{os.getpid()}-{out_png.stem}.html"
    tmp.write_text(page_html([slide_html]))
    try:
        if out_png.exists():
            out_png.unlink()
        run_chrome([f"--window-size={SLIDE_W},{SLIDE_H}", "--force-device-scale-factor=1", f"--screenshot={out_png}", tmp.as_uri()])
        for _ in range(50):
            if out_png.exists() and out_png.stat().st_size > 0:
                break
            time.sleep(0.1)
    finally:
        tmp.unlink(missing_ok=True)
    return out_png.exists()


def check_overflow(slides_html):
    tmp = PDF_DIR / f".check-{os.getpid()}.html"
    tmp.write_text(page_html(slides_html, check=True))
    try:
        ok, dom = run_chrome(["--window-size=1280,720", "--virtual-time-budget=5000", "--dump-dom", tmp.as_uri()], read_stdout=True)
    finally:
        tmp.unlink(missing_ok=True)
    m = re.search(r'data-overflow="([^"]*)"', dom)
    return m.group(1) if m else "unknown"


def pdf_pages(path):
    data = path.read_bytes()
    boxes = re.findall(rb"/MediaBox\s*\[\s*([\d.\s-]+)\]", data)
    count = len(re.findall(rb"/Type\s*/Page(?!s)", data))
    return count, sorted({tuple(float(x) for x in b.split()) for b in boxes})


def svg_wrap(w, h, body, cls="sch"):
    return (f'<div class="{cls}" style="width:{w}px;height:{h}px"><svg viewBox="0 0 {w} {h}" font-family="-apple-system, Helvetica, Arial, sans-serif">'
            f'<defs><marker id="ah" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
            f'<path d="M0,0 L10,5 L0,10 z" fill="#33424c"/></marker></defs>{body}</svg></div>')


def t(x, y, s, size=15, anchor="start", weight=400, fill="#24343e"):
    return f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" text-anchor="{anchor}" font-weight="{weight}" fill="{fill}">{esc(s)}</text>'


def ln(x1, y1, x2, y2, stroke="#33424c", w=1.4, arrow=False, dash=None):
    a = ' marker-end="url(#ah)"' if arrow else ""
    d = f' stroke-dasharray="{dash}"' if dash else ""
    return f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{stroke}" stroke-width="{w}"{a}{d}/>'


def rc(x, y, w, h, fill, stroke="none", sw=1, extra=""):
    return f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}" {extra}/>'


def svg_joint(w=560, h=370):
    k = 13.0
    gx, top = 175, 92
    seg_l = 120
    body = 17 * k
    b = []
    for side in (-1, 1):
        x = gx - 0.5 * k - seg_l if side < 0 else gx + 0.5 * k
        b.append(rc(x, top, seg_l, body, "#c3cbd1", "#8a949b", 1.2))
        gxg = gx - 0.5 * k - 1.5 * k if side < 0 else gx + 0.5 * k
        b.append(rc(gxg, top + 1.5 * k, 1.5 * k, 3 * k, "#ffffff"))
        b.append(t(x + seg_l / 2, top + body - 14, "Segment " + ("A" if side < 0 else "B"), 15, "middle", 600, "#3a4a54"))
    b.append(rc(gx - 0.5 * k, top, k, 1.5 * k, "#8a5a35"))
    b.append(f'<ellipse cx="{gx}" cy="{top + 3 * k}" rx="{2 * k}" ry="{1.5 * k}" fill="#262626"/>')
    b.append(rc(gx - 0.5 * k, top + 11 * k, k, 4 * k, "#ef8a22"))
    tube_y = top + 7 * k
    b.append(rc(gx - 0.5 * k - seg_l + 6, tube_y, 2 * seg_l + k - 12, 1.6 * k, "#878e94"))
    b.append(rc(gx - 0.5 * k, tube_y + 1.6 * k, k, 2.4 * k, "#ffffff"))
    b.append(ln(gx - 0.5 * k, top - 26, gx - 0.5 * k, top - 4, w=1))
    b.append(ln(gx + 0.5 * k, top - 26, gx + 0.5 * k, top - 4, w=1))
    b.append(ln(gx - 0.5 * k - 30, top - 16, gx - 0.5 * k, top - 16, arrow=True))
    b.append(ln(gx + 0.5 * k + 30, top - 16, gx + 0.5 * k, top - 16, arrow=True))
    b.append(t(gx + 0.5 * k + 36, top - 11, "1 mm gap, set at about 20 °C", 15, weight=600))
    b.append(t(gx - 0.5 * k - seg_l, top - 46, "Outer face of the profile", 14, fill="#56636b"))
    lab_x = gx + 0.5 * k + seg_l + 14
    items = [
        (top + 3 * k, gx + 2 * k, "4 mm foam cord fills", "both 1.5 mm grooves"),
        (top + 0.75 * k, gx + 0.5 * k, "MS polymer (±50 %) fills", "the band outside the cord"),
        (tube_y + 0.8 * k, gx + 0.5 * k + seg_l - 10, "continuous tube", "carries the load"),
        (top + 13 * k, gx + 0.5 * k, "1 mm shim: pull it once", "the tube screw is in"),
    ]
    ys = [top + 2 * k + 6, top + 6 * k + 4, top + 10.6 * k, top + 14.4 * k]
    for (ty, tx, l1, l2), yy in zip(items, ys):
        b.append(ln(lab_x - 4, yy - 5, tx, ty, w=1.2))
        b.append(f'<circle cx="{tx:.1f}" cy="{ty:.1f}" r="3" fill="#33424c"/>')
        b.append(t(lab_x, yy, l1, 14.5))
        b.append(t(lab_x, yy + 18, l2, 14.5))
    b.append(t(20, h - 16, "Schematic section through one joint at the cord ring (not to scale).", 13.5, fill="#66737a"))
    return svg_wrap(w, h, "".join(b))


def svg_measure(win, w=600, h=430):
    p = win.params
    b = []
    ox, oy, ow, oh = 64, 64, 236, 236
    b.append('<defs><pattern id="brick" width="46" height="38" patternUnits="userSpaceOnUse"><rect width="46" height="38" fill="#c98f6b"/>'
             '<path d="M0,0.5 H46 M0,19 H46 M23,0 V19 M0.5,19 V38" stroke="#b07554" stroke-width="1.2" fill="none"/></pattern></defs>')
    b.append(rc(ox - 34, oy - 34, ow + 68, oh + 68, "url(#brick)", "#a86f4f", 1.5, extra='rx="6"'))
    b.append(rc(ox, oy, ow, oh, "#f4f1ea", "#7d5a43", 1.5))
    for i, fy in enumerate((0.12, 0.5, 0.88)):
        y = oy + oh * fy
        b.append(ln(ox + 6, y, ox + ow - 6, y, arrow=True, w=1.6))
        b.append(ln(ox + ow - 6, y, ox + 6, y, arrow=True, w=1.6))
        b.append(t(ox + ow * 0.68, y - 6, f"W{i + 1}", 14, "middle", 700))
    for i, fx in enumerate((0.1, 0.5, 0.9)):
        x = ox + ow * fx
        b.append(ln(x, oy + 6, x, oy + oh - 6, arrow=True, w=1.6, stroke="#2f5d9a"))
        b.append(ln(x, oy + oh - 6, x, oy + 6, arrow=True, w=1.6, stroke="#2f5d9a"))
        b.append(t(x + (6 if i < 2 else -6), oy + oh * 0.32, f"H{i + 1}", 14, "start" if i < 2 else "end", 700, "#2f5d9a"))
    tx = ox + ow + 64
    for k, (s1, wt, col) in enumerate([("Width, reveal to reveal:", 400, "#24343e"), ("W1, W2, W3", 700, "#24343e"),
                                       ("Height, head to brick sill:", 400, "#2f5d9a"), ("H1, H2, H3", 700, "#2f5d9a"),
                                       ("Use the smallest of each", 600, "#24343e"), ("for opening_w and opening_h", 400, "#56636b")]):
        b.append(t(tx, oy + 4 + k * 22 + (10 if k >= 2 else 0) + (10 if k >= 4 else 0), s1, 14.5, weight=wt, fill=col))
    sx, sy = tx, oy + 190
    b.append(rc(sx, sy, 30, 90, "#c98f6b", "#a86f4f"))
    b.append(rc(sx + 30, sy, 32, 90, "#ffffff", "none"))
    b.append(rc(sx + 62, sy, 90, 90, "#d9b98f", "#9a7a55"))
    b.append(rc(sx + 62, sy - 26, 90, 26, "#c3cbd1", "#8a949b", extra='fill-opacity="0.6" stroke-dasharray="4 3"'))
    b.append(ln(sx + 62, sy + 104, sx + 152, sy + 104, arrow=True))
    b.append(ln(sx + 152, sy + 104, sx + 62, sy + 104, arrow=True))
    b.append(t(sx + 107, sy + 122, f"reveal ≥ {fmt(D['DEPTH'])} mm deep", 13.5, "middle", 600))
    b.append(t(sx + 15, sy - 6, "brick", 12.5, "middle", fill="#7d5a43"))
    b.append(t(sx + 107, sy - 32, "frame", 12.5, "middle", fill="#56636b"))
    b.append(t(sx + 107, sy + 50, "timber", 12.5, "middle", fill="#5e4426"))
    b.append(t(20, h - 32, "Frame = opening − 2 × fix_gap. The home window's", 13.5, fill="#56636b"))
    b.append(t(20, h - 14, f"{fmt(p['opening_w'])} × {fmt(p['opening_h'])} opening gives a {fmt(win.lay['w'])} × {fmt(win.lay['h'])} frame.", 13.5, fill="#56636b"))
    return svg_wrap(w, h, "".join(b))


def svg_sill_tray(w=620, h=400):
    b = []
    base = 250
    b.append(t(24, 30, "150 mm butyl flashing tape, ends turned up 100 mm.", 14.5, weight=600))
    b.append(t(24, 50, "With 100 mm tape: outer run first, inner run lapped 50 mm over it.", 14.5))
    b.append(t(24, 86, "OUTSIDE", 13, weight=700, fill="#7b878e"))
    b.append(t(w - 24, 86, "ROOM", 13, "end", 700, "#7b878e"))
    b.append(f'<polygon points="30,{base + 18} 230,{base + 8} 230,{base + 110} 30,{base + 110}" fill="#c98f6b" stroke="#a86f4f"/>')
    b.append(t(80, base + 70, "brick sill", 15, weight=600, fill="#5e3b26"))
    b.append(rc(250, base, 340, 110, "#d9b98f", "#9a7a55"))
    b.append(t(430, base + 70, "timber reveal floor", 15, "middle", 600, "#5e4426"))
    fx0, fx1 = 300, 300 + 63 * 2.6
    b.append(rc(fx0, base - 92, fx1 - fx0, 86, "#c3cbd1", "#8a949b", extra='fill-opacity="0.45" stroke-dasharray="5 4"'))
    b.append(t((fx0 + fx1) / 2, base - 44, "frame, on packers", 14, "middle", fill="#3a4a54"))
    b.append(ln(fx0, base - 108, fx1, base - 108, arrow=True))
    b.append(ln(fx1, base - 108, fx0, base - 108, arrow=True))
    b.append(t((fx0 + fx1) / 2, base - 116, "full 63 mm frame depth", 14, "middle"))
    tape = f"M120,{base + 12.5} L230,{base + 8} L250,{base - 2} L{fx1},{base - 2} L{fx1},{base - 2 - 30 * 2.2}"
    b.append(f'<path d="{tape}" fill="none" stroke="#1f3b57" stroke-width="5" stroke-linejoin="round"/>')
    b.append(ln(120, base - 18, 230, base - 18, arrow=True))
    b.append(ln(230, base - 18, 120, base - 18, arrow=True))
    b.append(t(175, base - 26, "≥ 50 mm onto the brick sill", 14, "middle"))
    b.append(ln(fx1 + 22, base - 2, fx1 + 22, base - 2 - 30 * 2.2, arrow=True))
    b.append(ln(fx1 + 22, base - 2 - 30 * 2.2, fx1 + 22, base - 2, arrow=True))
    b.append(t(fx1 + 30, base - 40, "30 mm up", 14))
    b.append(t(fx1 + 30, base - 22, "at the back", 14))
    b.append(t(24, h - 12, "Schematic section through the sill, not to scale.", 13.5, fill="#66737a"))
    return svg_wrap(w, h, "".join(b))


def fixings(win):
    lay, m = win.lay, win.members
    F, T, gap = D["FRAME_W"], D["TRANSOM_W"], D["JOINT_GAP"]
    W, H = lay["w"], lay["h"]
    tb = lay["transom_c"] - T / 2
    dz = D["FIX_DZ"] / 2
    mids = lambda mem, z0: [z0 + gap + i * (mem["seg"] + gap) + mem["seg"] / 2 for i in range(mem["n"])]
    out = []
    for x in mids(m["sill"], F):
        out.append(("S", x, 20, "bed", "below"))
    for x in mids(m["head"], F):
        out.append(("H", x + dz, H - 20, "dry", "above"))
    for side in (0, 1):
        mx = lambda x: W - x if side else x
        sx = -1 if side == 0 else 1
        for z in mids(m["jamb_lower"], F):
            out.append(("JL", mx(20), z, "bed", "side"))
        for z in mids(m["jamb_upper"], tb + T):
            out.append(("JU", mx(20), z + dz, "dry", "side"))
        for z in (tb + T / 2 - D["NODE_FIX_OFFSET"], tb + T / 2 + D["NODE_FIX_OFFSET"]):
            out.append(("JN", mx(20), z, "bed", "side"))
        cs = F - D["SOCKET_FRAME"] / 2
        out.append(("CS", mx(cs), 20, "bed", "below"))
        out.append(("CS", mx(20), cs, "bed", "side"))
        ch = F - D["SOCKET_FRAME"] / 2 + dz
        out.append(("CH", mx(ch), H - 20, "dry", "above"))
        out.append(("CH", mx(20), H - ch, "dry", "side"))
    return out


def svg_fixmap(win, w=640, h=560, focus="fixings"):
    lay = win.lay
    F, T = D["FRAME_W"], D["TRANSOM_W"]
    W, H = lay["w"], lay["h"]
    gap = win.params["fix_gap"]
    tb = lay["transom_c"] - T / 2
    s = min((w - 120) / W, (h - 110) / H)
    ox, oy = (w - W * s) / 2, 40
    X = lambda x: ox + (W - x) * s
    Y = lambda z: oy + (H - z) * s
    b = []
    b.append(rc(X(W + gap), Y(H + gap), (W + 2 * gap) * s, (H + 2 * gap) * s, "none", "#9a7a55", 2))
    band = "#d3d9de"
    for x0, z0, x1, z1 in [(0, 0, W, F), (0, H - F, W, H), (0, 0, F, H), (W - F, 0, W, H), (F, tb, W - F, tb + T)]:
        b.append(rc(X(x1), Y(z1), (x1 - x0) * s, (z1 - z0) * s, band, "#9aa5ad", 1))
    gl = win.glass_size("fixed")
    b.append(rc(X(W - F), Y(tb), (W - 2 * F) * s, (tb - F) * s, "#e3f0f6"))
    b.append(t(X(W / 2), Y(tb / 2) + 5, "fixed pane", 14, "middle", fill="#56636b"))
    b.append(t(X(W / 2), Y((tb + T + H - F) / 2) + 5, "sash opening", 14, "middle", fill="#56636b"))
    fx = fixings(win)
    pk = 7
    packers = []
    for kind, x, z, wet, where in fx:
        if where == "below":
            packers.append((X(x) - pk, Y(0) + 1, 2 * pk, 6))
        elif where == "above":
            packers.append((X(x) - pk, Y(H) - 7, 2 * pk, 6))
        else:
            edge = 0 if x < W / 2 else W
            packers.append(((X(edge) + 1) if edge == 0 else (X(edge) - 7), Y(z) - pk, 6, 2 * pk))
    qx = math.floor(D["GLASS_EDGE"] + gl[0] / 4)
    extra = [(X(qx) - pk, Y(0) + 1, 2 * pk, 6), (X(W - qx) - pk, Y(0) + 1, 2 * pk, 6),
             (X(F / 2) - pk, Y(0) + 1, 2 * pk, 6), (X(W - F / 2) - pk, Y(0) + 1, 2 * pk, 6),
             (X(0) + 1, Y(H - F / 2) - pk, 6, 2 * pk), (X(W) - 7, Y(H - F / 2) - pk, 6, 2 * pk)]
    pk_col = "#1b252b" if focus == "packers" else "#55616a"
    for x, y, pw, ph in packers + extra:
        b.append(rc(x, y, pw, ph, pk_col))
    for x, y, pw, ph in extra[:2]:
        b.append(rc(x - 3, y - 3, pw + 6, ph + 6, "none", "#c0631a", 2.4))
    for x, y, pw, ph in extra[2:]:
        b.append(rc(x - 3, y - 3, pw + 6, ph + 6, "none", "#6a4c93", 2.4))
    if focus == "fixings":
        for kind, x, z, wet, where in fx:
            col = "#1f6fb8" if wet == "bed" else "#c0392b"
            b.append(f'<circle cx="{X(x):.1f}" cy="{Y(z):.1f}" r="5.2" fill="{col}" stroke="#fff" stroke-width="1.2"/>')
    b.append(t(X(0), Y(0) + 30, "CSL", 14, "middle", 700))
    b.append(t(X(W), Y(0) + 30, "CSR", 14, "middle", 700))
    b.append(t(X(0) + 6, Y(H) - 14, "CH", 14, "end", 700))
    b.append(t(X(W) - 6, Y(H) - 14, "CH", 14, "start", 700))
    b.append(t(X(qx), Y(0) + 30, f"{qx} mm", 13.5, "middle", 600, "#c0631a"))
    b.append(t(X(W - qx), Y(0) + 30, f"{qx} mm", 13.5, "middle", 600, "#c0631a"))
    b.append(t(w / 2, h - 12, "Seen from the room. Packers and fixings to scale in position, not in size.", 13.5, "middle", fill="#66737a"))
    return svg_wrap(w, h, "".join(b)), len(fx), len(packers) + len(extra), qx


def svg_hinges(win, w=600, h=210):
    n = win.members["head"]["n"]
    hinges = win.qty["HG"]
    idx = [0, (n - 1) // 2, n - 1] if hinges == 3 else [0, n - 1]
    b = []
    x0, y0, sw = 30, 40, (w - 60) / n
    for i in range(n):
        b.append(rc(x0 + i * sw + 1.5, y0, sw - 3, 34, "#c3cbd1", "#8a949b"))
        b.append(t(x0 + i * sw + sw / 2, y0 + 22, f"H {i + 1}", 14, "middle", 600, "#33424c"))
        if i in idx:
            b.append(rc(x0 + i * sw + sw / 2 - 16, y0 + 34, 32, 20, "#ef8a22", "#b9611a"))
    b.append(rc(x0 + 10, y0 + 54, w - 80, 52, "none", "#5f6a73", 6, extra='rx="3"'))
    b.append(t(w / 2, y0 + 86, "screen, hanging from the HG / HS hinges", 14, "middle", fill="#3a4a54"))
    b.append(t(x0, y0 - 14, f"Head: {n} H segments, all with inserts. {hinges} hinges on segments " + ", ".join(str(i + 1) for i in idx) + ".", 14.5, weight=600))
    return svg_wrap(w, h, "".join(b))


def zone_cam(win, zone):
    h, tb = win.lay["h"], win.lay["transom_c"] - D["TRANSOM_W"] / 2
    cv = [h - 68, tb + 48, 50, 63][zone]
    return Ortho(410, 35, cv), cv


def section_fig(win, zone, disp_h, badges, dims=(), urange=(-34, 108)):
    cam, cv = zone_cam(win, zone)
    return overlay_fig(DECK / f"section-{zone}.png", cam, urange, (cv - 80, cv + 80), disp_h, badges, dims)


def overview_slides(hm, bn, today):
    ext, inn, ext_item = hm.filament()
    bext, binn, _ = bn.filament()
    fw, fh = hm.glass_size("fixed")
    sw, sh = hm.glass_size("sash")
    p = hm.params
    cover = f"""
<section class="slide cover" data-n="1">
  <div class="ct">
    <div class="ck">OpenWindow v1 · build and owner's guide</div>
    <h1>OpenWindow — a 3D&#8209;printable, double&#8209;glazed awning window</h1>
    <div class="sub">Size it for your opening, print it on a Bambu P1S, assemble it on the bench, fit it into a brick-veneer wall,
    and look after it: the whole job, step by step.</div>
    <div class="facts">
      <div><b>{fmt(p['opening_w'])} × {fmt(p['opening_h'])} mm</b>home window: top awning over a fixed IGU</div>
      <div><b>{hm.prints} prints</b>{hm.types} part types, {fmt(ext)} + {fmt(inn)} kg filament</div>
      <div><b>63 mm deep</b>printed shells on aluminium and steel tubes</div>
      <div><b>Bench window first</b>{fmt(bn.params['opening_w'])} × {fmt(bn.params['opening_h'])} mm test build: {bn.prints} prints</div>
    </div>
  </div>
  <div class="hero">{fig(DECK / 'hero.png', 560, 560, pad=0.04)}</div>
  <div class="cf"><span>Version 1 · {today}</span><span>Open source · licence: to be chosen</span></div>
</section>"""
    SLIDES.append({"sec": "cover", "title": "", "body": cover, "kicker": None})
    slide("overview", "Contents", "{{TOC}}")

    why = md("""
### The problem
- Basic single-glazed aluminium sliders lose heat fast: about **6 W/m²K** through the glass.
- Brush-pile seals leak air, so they're draughty in wind and let insects in.

### What OpenWindow aims for
- Double glazing: about **2.7–3.0 W/m²K** at the glass.
- **Airtight when closed:** EPDM compression seals, not brush pile.
- An insect screen on the room side.
- **Open source and parametric:** one small params file per opening; the generator does the rest.
""")
    scope = table(["v1 decision", ""], [
        ["Replacement", "Full: the old window comes out down to the wall opening"],
        ["Wall", "Brick veneer (timber frame + brick skin), typical of Melbourne"],
        ["Opening", "1500–1800 mm wide × 1200–1500 mm high"],
        ["Layout", "Top awning strip (about 450 mm high) over one fixed pane"],
        ["Operation", "Top-hung on stainless friction stays, two printed cam locks"],
        ["Glazing", "Universal 24 mm pocket: IGU, acrylic sandwich or twin-wall"],
        ["Screen", "Room side, hinged at the top, magnetic seal"],
    ], cls="compact")
    slide("overview", "Why OpenWindow, and what v1 is", grid(why, scope + md("""
?? Planned later: a horizontal slider sash for the same frame, kits for weatherboard and solid-brick walls, other layouts.
"""), cols="1fr 1.08fr", gap=40))

    tubes = f"{hm.q('Tube alu20')} m 20 × 20 alu, {hm.q('Tube alu10')} m 10 × 10 alu, {hm.q('Tube steel40x20')} m 40 × 20 steel"
    glance = kpis([
        (f"{fmt(hm.lay['w'])} × {fmt(hm.lay['h'])}", f"frame (mm) for a {fmt(p['opening_w'])} × {fmt(p['opening_h'])} opening, 63 deep"),
        (f"{hm.prints} prints", f"{hm.types} part types, every one ≤ 240 mm long"),
        (f"{fmt(ext)} + {fmt(inn)} kg", f"exterior filament (tier {p['tier']}) + interior PETG"),
        (f"{fw} × {fh}", f"fixed IGU (mm); sash IGU {sw} × {sh}"),
        (f"{fmt(hm.lay['sash_kg'])} kg sash", f"on a {hm.lay['stay']} mm friction-stay pair"),
        (f"{hm.q('Timber screw')} fixings", f"10g × 75 into the reveal, {hm.q('packers')} packers"),
        (f"{hm.q('EPDM bulb')} m", "EPDM bulb seal in two loops round the sash"),
        (f"{hm.q('MS-polymer')} cartridges", "±50 % MS-polymer sealant for joints and perimeter"),
    ], cols=2)
    defl = hm.check("transom_deflection")["msg"]
    slide("overview", f"The home window at a glance ({fmt(p['opening_w'])} × {fmt(p['opening_h'])})", grid(
        glance + md(f"Tubes: {tubes}. Transom: {defl.replace('transom deflects', 'deflects')}."),
        fig(DECK / "inside.png", 500, 500, pad=0.03, cap="Room side, screen closed. Every number on this slide comes from `bom/home-1800x1500.*`."),
        cols="1fr 500px", gap=34))

    slide("overview", "Honest limits (1): the size of the job", grid(
        kpis([(f"{hm.prints}", "prints for the home window"), (f"{fmt(ext + inn)} kg", "filament in total"),
              ("≈ 550 h", "printer time, spec estimate (§7)"), ("2 people", "to install; a dry day")], cols=2)
        + md(f"""
- Each printed segment is at most 240 mm long to fit the P1S bed, so a 1.8 m member has seven of them, and every joint is sealed by hand.
- The fixed IGU alone weighs about **{fmt(round(fw * fh / 1e6 * window.GLAZING_KG_M2['igu']))} kg**.
- Besides filament you buy metal tube, a steel transom tube, glass from a glazier, EPDM seals, sealant and stainless hardware.
"""),
        md(f"""
### Start small
The {fmt(bn.params['opening_w'])} × {fmt(bn.params['opening_h'])} mm **bench window** uses the same profiles, joints, seals and hardware:

- {bn.prints} prints, {fmt(bext)} + {fmt(binn)} kg filament;
- acrylic glazing, tier 1 PETG;
- mounted in a timber test box and put through the test protocol.

++ Print and pass the bench window before you commit to the full size.
""") + fig(DECK / "hero-bench.png", 540, 230, pad=0.04), cols="1fr 1fr", gap=40))

    gate_fig, gate_w = section_fig(hm, 3, 470, [(1, (98, 46.5), (40, 46.5))],
                                   dims=[((28, 40), (28, 112), "28", (28, 118)), ((46, 53), (46, 112), "46", (46, 118))])
    slide("overview", "Honest limits (2): not certified, not yet proven", grid(md("""
### Not certified
- No **AS 2047** window rating (wind, water, air): nothing has been tested by a lab.
- Glass must follow **AS 1288**: toughened where it requires; buy it from a glazier.
- Not designed for bushfire-prone (**BAL**-rated) sites.
- Fit opening restrictors where the **NCC** requires them.
- Check your local building rules before you start.
"""), md(f"""
### Not yet proven
- **Friction-stay gate:** a 400 mm stay pair must fit a stack of ≤ 13 mm and a width of ≤ 14 mm, rated ≥ {fmt(hm.lay['sash_kg'])} kg. Many are 16–19 mm wide. If none fits, the CAD has to change.
- Joint sealing at the 1 mm expansion gap relies on a ±50 % sealant.
- Creep of printed parts in full sun, stays and corners under load, cam wear: all in the test protocol.

!! Build and test the bench window first (Testing section). Order glass only after measuring the real opening.
"""), gate_fig + '<p class="small muted" style="margin-top:6px">The stay (1) must fold into the 13 mm gap between the jamb fin top (28) and the sash lip (46).</p>',
        cols=f"1fr 1fr {gate_w}px", gap=30))


def how_slides(hm, bn):
    p = hm.params
    lay = hm.lay
    slide("how", "Layout: a top awning over a fixed pane", grid(
        fig(DECK / "inside-open.png", 640, 560, pad=0.03),
        md("""
Seen from the room with the screen lifted and the sash pushed out.

- **Frame:** head, sill and two jambs, screwed to the timber reveal.
- **Transom:** a separate steel-cored bar. Its shoes slide down dovetails in the two jamb nodes after the frame is fixed.
- **Sash:** top-hung on a pair of stainless friction stays; two printed cam locks pull it onto its seals.
- **Fixed pane:** sits in the lower frame on printed setting blocks.
- **Screen:** hinged along the head, held shut by magnets; the cams sit inside it.
"""), cols="640px 1fr", gap=34))

    sw, sh = lay["sash"]
    nw, nh = lay["screen"]
    tiles = [
        ("unit-0.png", f"**Frame** {fmt(lay['w'])} × {fmt(lay['h'])} mm: sill, jambs with nodes, head, four corners"),
        ("unit-1.png", f"**Transom** with shoes and cam bases; dry-fitted at the bench, sealed at install"),
        ("unit-2.png", f"**Sash** {fmt(sw)} × {fmt(sh)} mm, glazed at the bench, with keepers and stay arms"),
        ("unit-3.png", f"**Screen** {fmt(nw)} × {fmt(nh)} mm with mesh and magnetic strip A"),
    ]
    cells = [fig(DECK / f, 560, 196, pad=0.03, cap=c) for f, c in tiles]
    fw, fh = hm.glass_size("fixed")
    loose = inline(f"Plus the loose glass: the fixed {fw} × {fh} mm IGU goes in after the frame is fixed (install step 9).")
    slide("how", "Four units, built flat on the bench", grid(*cells, cols="1fr 1fr", gap=18) + f'<p style="margin-top:14px">{loose}</p>')

    cores = table(["Member", "Core", "Why"], [
        ["Head, sill, jambs", "20 × 20 × 1.6 aluminium", "screwed to the reveal every 400 mm"],
        ["Transom", "40 × 20 × 1.6 galvanised steel", "the only member spanning the full width"],
        ["Sash", "20 × 20 × 1.6 aluminium", "carried at the jambs by the stays"],
        ["Screen", "10 × 10 aluminium", "in every rail of two or more segments"],
    ], cls="compact")
    slide("how", "Structure: printed shells on continuous metal tubes", grid(
        fig(DECK / "joint.png", 400, 560, pad=0.04),
        md("""
- Every member has **one continuous tube** running its full length.
- Printed segments, each **≤ 240 mm**, slide over it. One stainless screw through the inside face fixes each segment to the tube at its middle.
- **Corner blocks** take the tube ends in sockets; each tube stops 1.5 mm short of the socket floor.
- The tube carries the load. The joint between segments only aligns and seals.
""") + cores + md(f"Transom check for this opening: it {hm.check('transom_deflection')['msg'].replace('transom ', '', 1)}."),
        cols="400px 1fr", gap=34))

    slide("how", "Segment joints are built to move", grid(svg_joint(), md("""
- PETG and ASA expand by 65–95 µm/m·K. A 240 mm segment grows **0.8–1.1 mm** over a 50 °C swing; one long printed part would bow instead.
- Each joint is assembled at about 20 °C on two **1 mm shims**. The generator shortens every segment by one gap per joint, so member lengths and tube cuts don't change.
- One ring of **4 mm closed-cell foam cord** sits in the 1.5 mm grooves of the two end faces.
- **MS polymer rated for ±50 %** fills the band outside the cord and the end faces of the stops and fins: the gap cycles between about 0 and 1.3 mm.
"""), cols="560px 1fr", gap=34))

    names = [("Glazing", "lower jambs [[JL]], sill-corner legs"), ("Sash rebate", "head [[H]], upper jambs [[JU]], [[CH]]"),
             ("Sill + nose", "[[S]] [[SW]] and the clip-on [[NS]]"), ("Transom", "[[T]] [[TE]] and shoes [[TSL]] [[TSR]]"),
             ("Sash", "[[SH]] [[SB]] [[SBE]] [[SV]] [[CS]]"), ("Screen", "[[NH]] [[NV]] [[CN]]"),
             ("Bead, IGU / acrylic", "[[BFH]] [[BFV]] [[BSH]] [[BSV]]"), ("Bead, twin-wall", "packer variant")]
    cam = Ortho(210, 0, 0)
    box = [*map(int, cam.px(-40, 40)), *map(int, cam.px(40, -40))]
    tiles = "".join(f'<div class="tile">{fig(DECK / f"profile-{k}.png", 176, 150, pad=0, box=box)}'
                    f'<div class="t"><b>{esc(n)}</b><br><span class="muted">{inline(c)}</span></div></div>'
                    for k, (n, c) in enumerate(names))
    slide("how", "Profiles, thermal break and air chambers", grid(
        f'<div class="tiles" style="grid-template-columns:repeat(4,176px)">{tiles}</div>'
        + '<p class="small muted" style="margin-top:8px">All drawn at the same scale, outside on the left. Black: seals and gaskets; brown: magnetic strip.</p>',
        md("""
- Every cross-section comes from one file, `cad/profile.scad`.
- The tube sits in a pocket **fully enclosed by plastic**, at least **6 mm** from the inside and outside faces.
- **No metal bridges** from outside to inside: stay and lock screws go into the core from one side only.
- Bodies are hollow, multi-chamber profiles with **2.5 mm walls**, like uPVC.
- Frame: 63 mm deep, 58 mm face. Transom body 34 mm, sash body 33 mm.
"""), cols="752px 1fr", gap=30))

    h = lay["h"]
    tb = lay["transom_c"] - D["TRANSOM_W"] / 2
    sz0 = lay["transom_c"] + D["TRANSOM_HALF_BODY"] + D["SASH_GAP"]
    stop = sz0 + lay["sash"][1]
    nz0 = tb + D["TRANSOM_MAG_X"] - D["SCREEN_OVERLAP"] - 2
    ntop = nz0 + lay["screen"][1]
    L, R = -24, 98
    z0, w0 = section_fig(hm, 0, 560, [
        (1, (L, h - 20), (1.2, h - 20)), (2, (R, h - 6), (22.3, h - 16)), (3, (L, h - 44), (18.5, h - 44)),
        (4, (R, h - 54), (53, h - 49)), (5, (R, h - 34), (40, h - 46)), (6, (L, stop - 22), (3, stop - 22)),
        (7, (L, stop - 70), (12.5, stop - 70)), (8, (R, stop - 41), (44, stop - 41)), (9, (R, ntop - 76), (82.5, ntop - 76))])
    leg0 = legend([
        (1, "Head: sash-rebate profile ([[H]] segments, [[CH]] corners)"),
        (2, "20 × 20 aluminium tube, wrapped in plastic"),
        (3, "Outer weather seal: EPDM bulb in the fin kerf, closed on by the sash flange"),
        (4, "Inner air seal: EPDM bulb in the inner-stop kerf, closed on by the sash lip"),
        (5, "Pressure-equalised chamber between the seals: the 13 mm sash gap, where the stays live on the jambs"),
        (6, "Sash top rail [[SH]] on its own 20 × 20 tube"),
        (7, "24 mm IGU between two 3 mm wedge gaskets"),
        (8, "Snap-in bead [[BSH]] holds the inner gasket"),
        (9, "Screen top rail [[NH]]: magnetic strip A against strip B in the frame channel; mesh in the spline groove"),
    ])
    slide("how", "Section 1: head and top of the sash", grid(z0, '<p class="small muted">Vertical section at mid-width, outside on the left.</p>' + leg0,
                                                          cols=f"{w0}px 1fr", gap=30))

    z1, w1 = section_fig(hm, 1, 560, [
        (7, (L, tb - 14), (12.5, tb - 14)), (10, (R, tb + 2), (43, tb + 10)), (11, (L, tb + 36), (22.3, tb + 36)),
        (12, (L, tb + 54), (21, tb + 54)), (3, (L, tb + 66), (18.5, tb + 56)), (4, (R, tb + 66), (53, tb + 61)),
        (13, (L, sz0 + 24), (3, sz0 + 24)), (14, (R, nz0 + 30), (82.5, nz0 + 22)), (8, (R, sz0 + 46), (44, sz0 + 41))])
    leg1 = legend([
        (10, "Fixed-pane bead [[BFH]], snapped into the transom's keyway"),
        (11, "Transom [[T]] / [[TE]] on a 40 × 20 × 1.6 steel tube"),
        (12, "Weep slot through the fin root, in the two [[TE]] segments: drains the chamber between the seals"),
        (3, "Outer weather seal on the transom fin"),
        (4, "Inner air seal on the transom's inner stop"),
        (13, "Sash bottom rail [[SB]] / [[SBE]]: glass on [[GF]] setting blocks; the [[SBE]] weeps drain the sash pocket"),
        (14, "Screen bottom rail on the lower half of the transom's inside face; the cam locks sit above it, inside the closed screen"),
        (7, "Fixed IGU (below) and sash IGU (above)"),
        (8, "Sash bead [[BSH]]"),
    ])
    slide("how", "Section 2: transom, sash bottom and fixed-pane top", grid(z1, f'<p class="small muted">{inline("Blue: weep slots, cut only in [[TE]] and [[SBE]] segments.")}</p>' + leg1,
                                                                        cols=f"{w1}px 1fr", gap=30))

    z2, w2 = section_fig(hm, 2, 560, [
        (15, (L, 50), (5, 50)), (16, (R, 40), (30, 40)), (17, (L, 4), (-13.5, 6)), (18, (L, 30), (3, 37.2)),
        (7, (L, 100), (12.5, 100)), (8, (R, 62), (44, 46))], urange=(-40, 104))
    leg2 = legend([
        (15, "Sill [[S]] / [[SW]]: the glazing-pocket floor falls 8° outward to the weep"),
        (16, "[[GW]] wedge setting block at each quarter point, over a packer under the sill"),
        (17, "Clip-on sill nose [[NS]] with drip groove, 15 mm proud of the frame face"),
        (18, "Weep slot through the outer stop ([[SW]] segments), behind a flap cap [[WC]]"),
        (7, "Fixed IGU standing on its setting block"),
        (8, "Bead [[BFH]], snapped in from the room side"),
    ])
    slide("how", "Section 3: sill and bottom of the fixed pane", grid(z2, leg2 + md("""
!! Never seal over the weep slots or the nose drip. Water that gets past a seal must have a way out.
"""), cols=f"{w2}px 1fr", gap=30))

    rows = [["IGU (glazier)", "4/16/4 or 5/14/5, low-E/argon optional", "standard", "best thermal and clarity; heaviest"],
            ["Acrylic sandwich", "4 mm + 16 mm printed spacer + 4 mm", "standard", "spacer has a desiccant channel; unit can be opened to clean"],
            ["Twin-wall PC", "16 mm sheet + 8 mm printed packer", "packer", "translucent: bathrooms, laundries"]]
    cam = Ortho(210, 0, 0)
    box = [*map(int, cam.px(-16, 16)), *map(int, cam.px(16, -16))]
    beads = grid(fig(DECK / "profile-6.png", 190, 160, pad=0, box=box, cap="IGU / acrylic bead"),
                 fig(DECK / "profile-7.png", 190, 160, pad=0, box=box, cap="Twin-wall bead"),
                 fig(DECK / "part-GW.png", 190, 130, pad=0.06, cap="[[GW]] wedge block"),
                 fig(DECK / "part-AFH.png", 190, 130, pad=0.06, cap="[[AFH]] acrylic spacer"), cols="190px 190px", gap=16)
    slide("how", "Glazing: one 24 mm pocket, three fillings", table(["Glazing", "Make-up", "Bead", "Notes"], rows, cls="big")
          + grid(md("""
- 3 mm EPDM **wedge gaskets** on both faces: the outer one in the stop kerf, the inner one in the bead.
- Glass stands on printed **setting blocks**: [[GW]] wedges on the sloped sill, [[GF]] flat blocks in the sash and as side locators.
- **Beads snap** into an undercut keyway from the room side; no screws.
- Each glazing pocket is drained and ventilated through weep holes with flap caps.
"""), beads, cols="1fr 396px", gap=30))

    slide("how", "Hardware: cam locks, screen hinges, friction stays", grid(
        fig(IMG / "lock_view.png", 370, 380, pad=0.03, cap="Cam lock: base [[CMB]] and handle [[CMH]] on a [[TE]], keeper [[KP]] on the sash"),
        fig(DECK / "hinge.png", 370, 380, pad=0.03, cap="Screen hinge: [[HG]] on an [[H]] segment, [[HS]] on the screen rail, M4 × 50 pin"),
        md(f"""
- **Two cam locks**, one near each end: turning the lever 60° pulls the sash in about 3 mm onto both seals. Each keeper sits over its cam pivot.
- **Screen:** {hm.qty['HG']} pin hinges on the head; it closes under gravity onto magnetic strips A and B.
- **Friction stays:** a stainless pair holds the sash at any opening. Screws go into the tubes from one side only.
- Heat-set M4 inserts take every machine screw that gets re-tightened.
"""), cols="370px 370px 1fr", gap=24))

    stay_badges = [(1, (-24, 16), (22.3, 16)), (2, (-24, 70), (3, 70)), (3, (98, 46.5), (40, 46.5)),
                   (4, (98, 28), (35.25, 28)), (5, (98, 62), (35.25, 62))]
    dims = [((28, 40), (28, 120), "28", (28, 124)), ((46, 53), (46, 120), "46", (46, 124)),
            ((35.25, 53), (35.25, 106), "35–35.5", (35.25, 110))]
    zf, wf = section_fig(hm, 3, 560, stay_badges, dims=dims)
    slide("how", "The friction-stay gate: check this before printing", grid(zf, legend([
        (1, "Upper jamb [[JU]] and its tube (21.5–41.5 mm from the outside face; V-slot cores: see the V-slot slide)"),
        (2, "Sash side [[SV]] and its tube (17–37 mm from the sash's outside face)"),
        (3, f"Folded stay: **≤ {fmt(D['SASH_GAP'])} mm stack** in the sash gap, **≤ {fmt(D['STAY_W'])} mm wide**, centred 35–35.5 mm from the outside face"),
        (4, "Track screws 8g × 25 into the jamb tube"),
        (5, "Arm screws 8g × 16 into the sash tube"),
    ]) + md(f"""
Dimensions in mm from the frame's outside face: the stay must sit between the jamb fin top (28) and the sash lip (46).

!! Find a {lay['stay']} mm stay pair rated ≥ **{fmt(lay['sash_kg'])} kg** that fits this envelope before printing anything full size. Most 400 mm awning stays are 16–19 mm wide and will not fit.
"""), cols=f"{wf}px 1fr", gap=30), kicker="How it works · plan section through the upper jamb")


def materials_slides(hm, bn):
    ext_ids = [i for i in GALLERY_ORDER if hm.role.get(i) == "exterior"]
    int_ids = [i for i in GALLERY_ORDER if hm.role.get(i) == "interior"]
    tiers = table(["Tier", "Exposure", "Min HDT", "UV", "Examples"], [
        ["1", "South-facing or shaded, light colour", "≥ 70 °C", "stable or painted", "PETG + exterior acrylic paint, ASA"],
        ["2", "East or part sun, light colour", "≥ 90 °C", "inherently stable", "ASA"],
        ["3", "North or west full sun, or any dark colour", "≥ 105 °C", "inherently stable", "ASA-CF, PC-ABS (painted)"],
    ], cls="big")
    slide("materials", "Pick the material tier for your wall", tiers + grid(md("""
- **Rule:** heat-deflection temperature (HDT at 0.45 MPa) at least **15 °C above** the hottest surface, and exterior parts UV-stable or painted.
- Melbourne design surface temperatures: about 50–55 °C on light colours, 75–80 °C on dark colours in afternoon sun.
- **A dark colour moves any exposure up one tier.** Light colours are strongly recommended.
- Set `tier` in your params file; the BOM names the material and weighs it.
"""), md(f"""
### Exterior parts (tier material)
{" ".join(f"[[{i}]]" for i in ext_ids)}

### Interior parts (PETG in every tier)
{" ".join(f"[[{i}]]" for i in int_ids)}

?? P1S: ASA and PC need the enclosure closed; CF filaments need a hardened-steel nozzle.
"""), cols="1fr 1fr", gap=36))


def check_lines(win):
    lines = [f"{win.name}: {win.types} part types, {win.prints} prints -> {generate.GENERATED}".replace(str(ROOT) + "/", "")]
    for c in win.lay["checks"]:
        lines.append(("ok       " if c["ok"] else "WARNING  ") + c["msg"])
    return lines


def bays_slide(hm, tb):
    fw, fh = tb.glass_size("fixed")
    sw, sh = tb.glass_size("sash")
    hfw, hfh = hm.glass_size("fixed")
    ext, inn, _ = tb.filament()
    hext, hinn, _ = hm.filament()
    limit = " × ".join(fmt(v) for v in tb.params["max_pane"])
    rows = [
        ["Fixed panes", f"1 × {hfw} × {hfh}", f"{tb.lay['bays']} × {fw} × {fh}"],
        ["Sashes", f"1, {fmt(hm.lay['sash_kg'])} kg", f"{tb.lay['bays']}, {fmt(tb.lay['sash_kg'])} kg each"],
        ["Transom", hm.check("transom_deflection")["msg"].replace("transom deflects ", ""),
         tb.check("transom_deflection")["msg"].replace("transom deflects ", "")],
        ["Mullion", "none", tb.check("mullion_deflection")["msg"]],
        ["Prints", f"{hm.prints} in {hm.types} types", f"{tb.prints} in {tb.types} types"],
        ["Filament", f"{fmt(hext)} + {fmt(hinn)} kg", f"{fmt(ext)} + {fmt(inn)} kg"],
    ]
    slide("size", "Sheet smaller than the panes? Mullions and bays", grid(md(f"""
Add `"max_pane": [{', '.join(fmt(v) for v in tb.params['max_pane'])}]` to the params file: the largest glass or acrylic sheet you can get, either way round.

- The generator picks the **fewest equal bays** that make every pane fit, splits the window with **mullions**, and gives each bay its own fixed pane, awning sash, screen and two cams.
- `"bays": n` asks for more bays than needed, never fewer.
- A pane too tall for the sheet needs a second transom, which OpenWindow does not do: the generator stops and says so.
- New parts: sill node [[SN]], head node [[HN]], transom cross-node [[TX]], mullion shoes [[MSL]], [[MST]], [[MSH]] and segments [[ML]], [[MU]], each on a 40 × 20 steel tube.
""") + table(["", "One bay", f"{limit} mm sheet"], rows, cls="compact", widths=["18%", "36%", "46%"]),
        fig(IMG / "assembly-home-2bay.png", 420, 420, pad=0.03, cap=f"`params/{tb.name}.json`, seen from the room."),
        cols="1fr 420px", gap=30))


def size_slides(hm, bn, tb):
    slide("size", "Measure the opening", grid(svg_measure(hm), md(f"""
1. Take the old window out first (install step 1), or measure inside its frame and confirm later.
2. Measure **width** reveal to reveal and **height** head to brick sill, three times each. Use the smallest.
3. Check the timber reveal is at least **{fmt(D['DEPTH'])} mm deep**, so the frame sits fully on it.
4. Pick `fix_gap`, the gap to the brickwork each side: **6–10 mm**.

!! Print and order glass only from these measurements, after regenerating the BOM.
""", steps=True), cols="600px 1fr", gap=32))

    rows = []
    meaning = {"name": "must match the file name", "opening_w": "measured width (mm)", "opening_h": "measured height (mm)",
               "fix_gap": "gap to the brickwork each side, 6–10", "awning_h": "awning height, at least 150",
               "glazing": "`igu`, `acrylic` or `twinwall`", "tier": "material tier 1–3"}
    for k in ["name", "opening_w", "opening_h", "fix_gap", "awning_h", "glazing", "tier"]:
        rows.append([f"`{k}`", meaning[k], f"`{hm.params[k]}`", f"`{bn.params[k]}`"])
    js = json.dumps(dict(hm.params, name="my-window"), indent=2)
    slide("size", "Your params file: six numbers and a name", grid(
        table(["Field", "Meaning", "Home", "Bench"], rows, cls="big nowrap-code", widths=["22%", "36%", "25%", "17%"]),
        md(f"""
```
cp params/home-1800x1500.json params/my-window.json
```
Then edit it:

```
{js}
```
"""), cols="1.25fr 1fr", gap=32))
    bays_slide(hm, tb)

    out = "\n".join(check_lines(hm))
    slide("size", "Generate, read the checks, render, build the BOM", md(f"""
```
$ python3 tools/generate.py params/home-1800x1500.json
{out}
```
""").replace("<pre>", '<pre style="font-size:14px">') + grid(md(f"""
- **Transom deflection** against span/175 at 0.7 kPa wind.
- **Sash weight** against the friction-stay pair it picks; the BOM asks for a stay rated at least this weight.
- **Segment length** ≤ 240 mm, and **cam/keeper** alignment.

!! A `WARNING` line needs a change before you print.
"""), md("""
```
cad/box.sh render my-window
python3 bom/build_bom.py my-window
```
- `box.sh` renders every part on an OpenSCAD machine and checks each STL against the part list. No such machine? Export each `cad/generated/parts/<ID>.scad` in your own OpenSCAD.
- The BOM step writes `bom/my-window.md` and the `-parts`, `-cutlist` and `-glass` CSVs.

?? Build from the per-name files in `bom/`: `cad/generated/` only holds the last window generated.
"""), cols="1fr 1fr", gap=30))


def print_slides(hm, bn, masses):
    ins = hm.q("heat-set insert")
    slide("print", "Printer settings (Bambu P1S)", grid(md("""
- 0.4 mm nozzle (hardened steel for CF filaments), **0.2 mm layers**.
- **5 walls, 5 top and 5 bottom layers, 15 % gyroid infill.** Most profile walls are 2.5 mm, so they print solid anyway.
- ASA and PC-ABS: enclosure closed, door shut, no auxiliary fan, textured PEI plate with glue stick.
- Exterior parts in your tier's material, interior parts in PETG (the parts list marks each).

++ Print the test coupon [[TC]] and one segment of each profile first, and check the fit before committing a full spool.
""") + fig(DECK / "part-TC.png", 300, 170, pad=0.05, cap="Test coupon [[TC]]: a 60 mm sash-rebate segment with two inserts."), md(f"""
### Heat-set inserts: {ins} × M4 for this window
Pressed flush with a 230 °C iron, wherever a machine screw is re-tightened:

- [[H]]: 2 each, on every head segment, so the hinges can move later;
- [[TE]]: cam bases;
- [[SBE]]: both boss pairs, 4 each (the keeper uses the outer pair);
- [[CMB]]: the cam pivot boss;
- [[TC]]: 2, for the heat and torque test.
"""), cols="1fr 1fr", gap=40))

    slide("print", "Orientation on the bed", table(["Parts", "Orientation"], [
        ["Segments [[H]] [[S]] [[SW]] [[JL]] [[JU]] [[T]] [[TE]] [[SH]] [[SB]] [[SBE]] [[SV]] [[NH]] [[NV]], and [[TC]]",
         "Standing on an end face, exactly as exported. No supports. The 2 mm rounded long edges stand vertical, and each 0.8 mm joint bevel prints as four 0.2 mm layers."],
        ["Corners [[CH]] [[CSL]] [[CSR]] [[CS]] [[CN]]", "As exported. Supports on the build plate only, for the rebate overhangs."],
        ["[[JN]] [[TSL]] [[TSR]]", "On the outside face, so the dovetail slot and tongue print in plane and slide without binding. Supports on the plate only."],
        ["Beads (B…)", "On their glass face (the gasket-kerf side), so the rounded edge prints on top."],
        ["Sill nose [[NS]], acrylic spacers (A…)", "Laid flat on their longest face."],
        ["Setting blocks, weep caps, cam parts, hinge leaves, keepers", "Flat side down."],
    ], cls="big", widths=["46%", "54%"]) + grid(
        fig(DECK / "print-H.png", 260, 200, pad=0.05, cap="[[H]] as exported: standing on its end face."),
        fig(DECK / "part-CSL.png", 260, 200, pad=0.05, cap="[[CSL]] as exported."),
        md("?? The catalogue that follows shows every part lying down, so its profile is visible; print segments and corners as exported."),
        cols="260px 260px 1fr", gap=24))

    per = 10
    ids = GALLERY_ORDER
    pages = [ids[i:i + per] for i in range(0, len(ids), per)]
    for n, page in enumerate(pages, 1):
        cells = []
        for pid in page:
            win = hm if pid in hm.qty else bn
            qty = win.qty[pid]
            role = win.role[pid]
            g = masses[win.name].get(pid)
            where = "home" if win is hm else "bench, acrylic only"
            meta = f'<span><i class="role {role}"></i>{qty} × {where}</span><span>{fmt(round(g))} g</span>' if g else f"<span>{qty}</span>"
            cells.append(f'<div class="tile">{fig(DECK / f"part-{pid}.png", 225, 175, pad=0.05)}'
                         f'<div class="t"><span class="nm"><span class="id">{esc(pid)}</span> {esc(PART_NAMES[pid])}</span>'
                         f'<span class="meta">{meta}</span></div></div>')
        slide("print", f"Part catalogue ({n}/{len(pages)})", f'<div class="tiles" style="grid-template-columns:repeat(5,1fr)">{"".join(cells)}</div>'
              + '<p class="small muted" style="margin-top:10px"><i class="role exterior"></i>exterior, tier material &nbsp; '
                '<i class="role interior"></i>interior, PETG &nbsp;·&nbsp; quantity for the home window (acrylic spacers: bench window) '
                '&nbsp;·&nbsp; mass each, estimated from the STL. Not to scale.</p>')

    ext, inn, _ = hm.filament()
    rows = []
    tot_n = tot_g = 0
    for fam, fids in FAMILIES:
        here = [i for i in fids if i in hm.qty]
        if not here:
            continue
        n = sum(hm.qty[i] for i in here)
        g = sum(masses[hm.name][i] * hm.qty[i] for i in here)
        tot_n += n
        tot_g += g
        rows.append([fam, " ".join(f"[[{i}]]" for i in here), n, f"{g / 1000:.2f}"])
    if abs(tot_g / 1000 - (ext + inn)) > 0.02 or tot_n != hm.prints:
        sys.exit(f"filament families ({tot_g / 1000:.2f} kg, {tot_n}) disagree with the BOM ({ext + inn:.2f} kg, {hm.prints})")
    rows.append(["**Total**", "", f"**{tot_n}**", f"**{tot_g / 1000:.2f}**"])
    slide("print", "Filament and print time (home window)", grid(
        table(["Family", "Parts", "Prints", "kg"], rows, cls="num compact"),
        kpis([(f"{fmt(ext)} kg", "exterior, tier material"), (f"{fmt(inn)} kg", "interior PETG"),
              ("≈ 550 h", "printer time (spec §7 estimate, from the STLs)")], cols=1)
        + md("Masses are estimated from the rendered STLs with the slicer settings above (2.1 mm shell, 15 % infill), as in `bom/build_bom.py`."),
        cols="1.45fr 1fr", gap=32))


def bom_rows_html(win, groups):
    rows = []
    for g in groups:
        for r in win.bom:
            if r["group"] == g:
                rows.append(f'<tr><td>{esc(g)}</td><td>{inline(chipify(r["item"]))}</td><td class="r">{esc(fmt(r["qty"]))}</td><td>{esc(r["unit"])}</td></tr>')
    return ('<table class="big r"><colgroup><col style="width:11%"><col style="width:73%"><col style="width:8%"><col style="width:8%"></colgroup>'
            '<thead><tr><th>Group</th><th>Item</th><th>Qty</th><th>Unit</th></tr></thead><tbody>' + "".join(rows) + "</tbody></table>")


def shop_slides(hm, bn):
    pages = [(["Fixings"], "fixings"), (["Hardware", "Seals"], "hardware and seals"),
             (["Screen", "Tube", "Glazing", "Filament"], "screen, tube, glass, filament")]
    for n, (groups, label) in enumerate(pages, 1):
        slide("shop", f"Bill of materials, home window ({n}/3): {label}", bom_rows_html(hm, groups)
              + (md("?? Every line is generated from the geometry by `bom/build_bom.py`. Your window: `bom/<name>.md`.") if n == 1 else ""))

    cut = table(["Member", "Core", "Length (mm)", "Qty"], [[t["member"].replace("_", " "), t["core"], fmt(t["length_mm"]), t["qty"]] for t in hm.cut], cls="num big")
    slide("shop", "Tube cut list (home window)", grid(cut, md(f"""
- Cut with a hacksaw or a drop saw with a metal blade, **never longer than the list**. Each length leaves 1.5 mm clear at every corner-socket floor for print shrinkage.
- Dry-fit each member on its tube with the shims in. Trim the tube if a joint won't close onto its shims.
- Deburr and wipe with isopropyl alcohol.
- Buy aluminium in 1 m or 3 m stock: {hm.q('Tube alu20')} m of 20 × 20 × 1.6 and {hm.q('Tube alu10')} m of 10 × 10. Steel: {hm.q('Tube steel40x20')} m of 40 × 20 × 1.6 galvanised.
- The transom tube is checked again at install step 6 against the real node spacing.
"""), cols="1fr 1fr", gap=36))

    fw, fh = hm.glass_size("fixed")
    sw, sh = hm.glass_size("sash")
    spec = hm.glass[0]["spec"]
    slide("shop", "Glass order (home window)", grid(table(["Pane", "Width (mm)", "Height (mm)", "Qty"], [
        ["Fixed", fw, fh, 1], ["Sash", sw, sh, 1]], cls="numall big") + md(f"""
**Spec:** {spec}.

Weights: fixed about {fmt(round(fw * fh / 1e6 * window.GLAZING_KG_M2['igu']))} kg, sash glass about {fmt(round(sw * sh / 1e6 * window.GLAZING_KG_M2['igu']))} kg.
""") + fig(DECK / "unit-4.png", 540, 250, pad=0.03, cap="The fixed IGU sits below the transom; the sash IGU is glazed at the bench."), md("""
- Order from `bom/<name>-glass.csv` only **after** the opening is measured and the BOM rebuilt.
- Your glazier decides where AS 1288 requires toughened or laminated glass.
- Acrylic glazing: two 4 mm sheets per pane, cut to the same sizes, film on until assembly (bench window).
- Twin-wall: 16 mm polycarbonate, UV face out, flutes vertical.
"""), cols="1fr 1fr", gap=36))

    slide("shop", "Tools you will need", md("""
- **Cutting:** hacksaw or drop saw with a metal blade, file or deburring tool, utility knife
- **Drilling:** drill/driver; bits 2 mm (screen leaves), 3.2 mm (aluminium tube and stay pilots), 3.5–3.8 mm (steel transom, if not using tek screws); countersink to tidy holes
- **Driving:** Phillips/square driver bits for 4g, 8g and 10g screws, hex keys for M4, a small spanner for the nylocs
- **Inserts:** soldering iron with a heat-set insert tip, set to 230 °C
- **Joints:** caulking gun, sealant spatula, bar or F clamps, 1 mm shims (plastic strips or feeler leaves) and 0.5–1.5 mm shims for the transom
- **Measuring:** tape, steel rule, square, spirit level (plumb and diagonals within 2 mm)
- **Seals and screen:** spline roller, scissors, gel CA, 5-minute epoxy
- **Install:** pry bar and knife for the old window, foam gun or can, backer-rod tool or blunt putty knife, ladder or platform, glass suction lifters
- **Safety:** gloves, eye protection, and a second person for lifting
- **Testing (bench):** garden hose, smoke pencil and fan, heat lamp and thermocouple, torque screwdriver (1.5 N·m)
""", table_cls="compact").replace("<ul>", '<ul class="cols2">'))


def step_slide(sec, title, img, steps, side=None, img_w=560, img_h=380, cap=None, kicker=None):
    left = fig(img, img_w, img_h, pad=0.04, cap=cap) if img else ""
    if side:
        left += f'<div class="sidefig">{side}</div>'
    slide(sec, title, grid(left, steps, cols=f"{img_w}px 1fr", gap=32), kicker=kicker)


def build_slides(hm, bn):
    m = hm.members
    slide("build", "Joint rules (1): temperature, gap, cord", grid(fig(DECK / "joint.png", 330, 560, pad=0.04), md("""
Frame, transom and sash joints all follow these rules. Screen joints close tight with no shims and no cord.

- **Temperature:** assemble at about 20 °C (15–25 °C).
- **Gap:** every segment joint gets a 1 mm gap; the generator already shortened each segment by one gap per joint, so the member keeps its length.
- **Shims:** hold each gap with two 1 mm shims (strips of 1 mm plastic sheet, or feeler-gauge leaves), slipped in from the outside and inside faces. Pull them once that part's tube screw is in.
- **Cord:** one ring of 4 mm closed-cell foam cord per joint, pressed into the groove of **one** face only; the mating face's groove takes the other half.
"""), cols="330px 1fr", gap=34))

    slide("build", "Joint rules (2): sealant and tube screws", grid(md("""
### Sealant: MS polymer rated ±50 %
Butter it on the face before closing each joint, keeping it off the cord:

- over the whole **band outside the cord ring**, continuous with the end faces of the stops, fins and inner stop;
- around the **tube pocket**;
- on transom faces, across the 2.7 mm **web** between the bead keyway and the tube.

### Work joint by joint, before it skins (about 10 min)
1. Butter, close onto the shims, clamp, drive that part's tube screw.
2. Pull the shims; fill and tool their voids, flush with the 0.8 mm bevel.
3. Clear squeeze-out from the kerfs, magnet channel and bead keyways.
""", steps=True), md("""
### Tube screws
One through the inside-face countersink of every segment, corner leg, node and shoe.

- **Aluminium tubes:** 8g × 30 stainless countersunk self-tappers, in a 3.2 mm pilot drilled through the printed hole into the tube.
- **Steel transom tube:** 8g × 25 tek screws in 410 stainless, or a 3.5–3.8 mm pilot and a stainless self-tapper.
- **V-slot cores:** M5 countersunk screws into slide-in T-nuts, with no pilots (see the V-slot slide).

!! Stop when the head is flush, so the screw doesn't strip the plastic.
"""), cols="1.1fr 1fr", gap=36))

    acr = bn.lay["glass"]
    slide("build", "Step 1 · Prepare tubes and inserts · Step 2 · Acrylic sandwich", grid(md("""
### 1 · Prepare
1. Cut the tubes to the cut list, never longer (V-slot cores: see the V-slot slide). Dry-fit each member with the shims in; trim if a joint won't close. Deburr, wipe with isopropyl.
2. Press M4 heat-set inserts (230 °C, flush) into every boss: all [[H]] segments (2 each), [[TE]], [[SBE]] (both pairs, 4 each), the [[CMB]] pivot boss and [[TC]].
""", steps=True) + fig(DECK / "part-SBE.png", 520, 170, pad=0.05, cap="[[SBE]]: two insert pairs either side of the middle; the keeper uses the outer pair, nearer the sash corner."),
        md(f"""
### 2 · Acrylic sandwich (only if `glazing = acrylic`)
One unit per pane: [[AFH]] / [[AFV]] bars for the fixed pane, [[ASH]] / [[ASV]] for the sash, four [[AC]] corners each.

1. Assemble the spacer frame and fill its channels with silica gel.
2. Bond both 4 mm sheets to it with butyl glazing tape.
3. Peel the film off the inner faces only.

The sash unit is glazed in step 5, the fixed unit at install step 9. Bench window panes: fixed {acr['fixed'][0]} × {acr['fixed'][1]}, sash {acr['sash'][0]} × {acr['sash'][1]} mm.
""", steps=True) + grid(fig(DECK / "part-AFH.png", 255, 130, pad=0.05, cap="[[AFH]] spacer bar with its desiccant holes"),
                         fig(DECK / "part-AC.png", 255, 130, pad=0.05, cap="[[AC]] corner, four per pane"), cols="1fr 1fr", gap=16),
        cols="1fr 1fr", gap=36))

    step_slide("build", "Step 3a · Frame: the sill", DECK / "build-1.png", md(f"""
1. Fit corner [[CSL]] on the left end of the sill tube (as seen from outside), tube end 1.5 mm off the socket floor, and drive its sill-leg tube screw.
2. Thread on the sill segments: an [[SW]] (weep) first, then the {hm.qty.get('S', 0)} [[S]] segments, then the other [[SW]]. Fit [[CSR]] on the right end.
3. Close the joints one by one from [[CSL]], following the joint rules, driving each segment's screw as you go. [[CSR]]'s screw goes in last.
""", steps=True), side=fig(DECK / "corner.png", 560, 170, pad=0.04, cap="[[CSL]] with the sill and jamb tubes, [[SW]] and [[JL]] pulled back."),
               img_h=340, cap=None)

    step_slide("build", "Step 3b · Frame: jambs and nodes", DECK / "build-2.png", md(f"""
1. On each jamb tube thread the [[JL]] segments ({m['jamb_lower']['n']} per side), one [[JN]] node, then the [[JU]] segments ({m['jamb_upper']['n']} per side). With V-slot cores each jamb is two tubes (see the V-slot slide).
2. Push the tube into its sill corner's socket, tube end 1.5 mm off the socket floor.
3. Drive the sill corner's jamb-leg tube screw ([[CSL]] left, [[CSR]] right).
4. Close the joints from the bottom up, driving every [[JL]] and [[JU]] tube screw and the [[JN]] node's (inside face, centre of the node).
""", steps=True), side=fig(DECK / "node.png", 560, 170, pad=0.04, cap="[[JN]] between [[JL]] and [[JU]]; the transom shoe comes later (install step 6)."), img_h=340)

    step_slide("build", "Step 3c · Frame: head, square, shims out", DECK / "build-3.png", md(f"""
1. Assemble [[CH]], the {m['head']['n']} [[H]] segments and [[CH]] on the head tube in the same way.
2. Butter the jamb-leg faces of both [[CH]] corners and drop the head onto the jamb tubes, closing the top jamb joints onto their shims.
3. Check the **diagonals are equal within 2 mm**, then drive the [[CH]] jamb-leg screws.
4. Pull out any shims still in, and fill and tool their voids.
""", steps=True), img_h=560)

    step_slide("build", "Step 4 · Transom: cams and a dry fit", DECK / "build-4.png", md("""
The transom is only **dry-fitted** here: its length must match the node spacing of the installed frame, so it is sealed and screwed at install step 6.

1. **Cam bases:** screw the two [[CMB]] to the [[TE]] inserts, two M4 × 10 countersunk screws each.
2. **Handles:** fit each [[CMH]] over its pivot boss with an M4 × 8 pan screw and a 20 mm penny washer.
3. **Dry fit:** thread the [[T]] and [[TE]] segments on the steel tube, a [[TE]] at each end. Fit shoe [[TSL]] on the left end and [[TSR]] on the right (as seen from outside), each with a cord ring in its joint with the [[TE]]. Check every joint closes onto its shims; leave them unsealed and unscrewed.
""", steps=True), side=fig(IMG / "lock_view.png", 560, 150, pad=0.03, cap="Cam base and handle on a [[TE]]; the keeper is fitted to the sash in step 5b."), img_h=360)

    step_slide("build", "Step 5a · Sash: assemble and glaze", DECK / "build-5.png", md(f"""
1. **Assemble:** fit [[SH]] (top), [[SB]] + [[SBE]] (bottom, [[SBE]] at the ends) and [[SV]] (sides) on their 20 × 20 tubes with four [[CS]] corners. Joint rules, 8g × 30 tube screws.
2. **Outer gasket:** fit the outer wedge gasket into the sash stop kerf all round.
3. **Blocks:** place four [[GF]]: two on the bottom rail at the quarter points of the glass width, one at mid-height on each side.
4. **Glass:** fit the IGU (or the acrylic unit).
5. **Beads:** snap in the [[BSH]] and [[BSV]] beads with the inner wedge gasket.
""", steps=True), side=fig(DECK / "part-CS.png", 560, 180, pad=0.05, cap="[[CS]] sash corner: both sash tubes end in its 21 mm sockets."), img_h=330)

    zf, wf = section_fig(hm, 3, 470, [(1, (98, 46.5), (40, 46.5))], dims=[((35.25, 53), (35.25, 100), "35–35.5", (35.25, 106))])
    slide("build", "Step 5b · Keepers and friction stays (sash side)", grid(md(f"""
1. **Keepers:** screw each [[KP]] to the **outer** boss pair of its [[SBE]] (nearer the sash corner) with two M4 × 10 countersunk screws.
2. **Stay arms:** screw each stay's sash arm to a sash side. The tracks go on the jambs at install step 8.
   - Stay size: stack ≤ {fmt(D['SASH_GAP'])} mm, track and arm ≤ {fmt(D['STAY_W'])} mm wide, rated ≥ {fmt(hm.lay['sash_kg'])} kg.
   - Along the sash: follow the stay's datasheet.
   - Across the sash side: centre each arm **33–33.5 mm in from the sash's outside face** (35–35.5 mm from the frame's outside face once hung).
   - Screws: 8g × 16 stainless countersunk, in 3.2 mm pilots through the shell into the tube, using the stay as the template (V-slot cores: 3.5 mm pilots, see the V-slot slide).
""", steps=True), zf + '<p class="small muted" style="margin-top:6px">Plan section: the folded stay (1) between the jamb and the sash side.</p>',
        cols=f"1fr {wf}px", gap=32))

    slide("build", "V-slot cores (optional)", grid(md("""
Only if the params file has `"core": "vslot"` (build guide section 8). The frame and sash cores are V-slot 2020; the transom and mullions are 2020 pairs. Every other step still applies: only the tubes and their screws change.

1. **Check the extrusion** first (test-log row 10): groove mouth 9.0–9.4 mm, slot depth 5.9–6.3 mm.
2. **Cut** to the V-slot cut plan in `bom/<name>.md`.
3. **Jambs are two tubes:** the lower tube runs from the sill corner into [[JN]], the upper tube from [[JN]] to the head corner. The head and upper jambs sit **3 mm further out**.
4. **M5 countersunk screws** (lengths from the BOM) into slide-in T-nuts, with no drilling. Hang each nut with the **carrier**, a ~150 mm V-slot offcut:
   - put the nut in the offcut's slot and slide the offcut into the part's empty pocket until the nut is under the screw hole;
   - drive the screw until it catches the nut and the nut is snug against the offcut's lips;
   - back the screw off a quarter turn and slide the offcut out. The nut's neck now sits level with the pocket wall.
""", steps=True), md("""
5. **Joins** go inside the segment the BOM names, with the piece end a quarter of the way along it.
6. **Transom pair:** the outer bar is trapped by the shoe end walls; the room-side bar takes 8g × 20 self-tappers in **3.5 mm pilots**.
7. **Friction stays:** same positions, **3.5 mm pilots** instead of 3.2 mm.
8. **Standard tubes:** members the BOM lists as standard keep a standard tube.

!! Tighten each T-nut screw snug, about 2 N·m: the head pulls the printed wall against the aluminium.
""", steps=True), cols="1.15fr 1fr", gap=36))

    nz = [mm for mm in hm.lay["members"] if mm["name"].startswith("screen")]
    tubes = "; ".join(f"{mm['name'].split('_')[1]} rails: {mm['n']} segment{'s' if mm['n'] > 1 else ''}, " + ("on a tube" if mm["core"] else "no tube") for mm in nz)
    step_slide("build", "Step 6 · Screen", DECK / "build-6.png", md(f"""
1. **Rails:** thread the [[NH]] and [[NV]] segments on their 10 × 10 tubes ({tubes}). Close the joints tight: no shims, no cord. Drive an 8g × 12 screw (3.2 mm pilot) into each segment with a tube.
2. **Corners:** glue each rail end into its [[CN]] with 5-minute epoxy on both butt faces, drive the [[CN]] tube screw in every leg that takes a tube, and check the diagonals before the epoxy sets.
3. **Mesh and strip:** roll in the mesh with spline. Stick magnetic strip A into the screen's back channel all round.
4. Leave the hinge leaves off: [[HG]] and [[HS]] are fitted and aligned in place at install step 12.
""", steps=True), side=fig(DECK / "part-CN.png", 560, 180, pad=0.05, cap="[[CN]] screen corner, epoxied on both butt faces."), img_h=330)


def install_slides(hm, bn):
    lay = hm.lay
    fw, fh = hm.glass_size("fixed")
    node_gap = lay["w"] - 2 * D["FRAME_BODY"]
    slide("install", "Before you start, and steps 1–2", grid(md(f"""
### Plan the day
- **Two people.** A dry day, with no rain forecast for 24 h.
- All four units built and checked; glass on site ({fw} × {fh} fixed IGU, about {fmt(round(fw * fh / 1e6 * window.GLAZING_KG_M2['igu']))} kg).
- Fixings, packers, tape, backer rod, sealant and foam from the BOM.
- Work from a stable platform or ladder; gloves and eye protection when handling glass.

### The 13 steps
1 remove · 2 measure · 3 sill tray · 4 set the frame · 5 fix it · 6 transom · 7 seals and magnet strip · 8 hang the sash · 9 glaze the fixed pane · 10 seal outside · 11 inside · 12 screen · 13 cams
""") + grid(*[fig(DECK / f"unit-{k}.png", 128, 90, pad=0.04) for k in range(4)], cols="repeat(4,1fr)", gap=10)
        + '<p class="small muted" style="margin-top:6px">Frame, transom, sash and screen: the four units you carry to the opening.</p>', md(f"""
### 1 · Remove the old window
Unscrew the old frame from the timber reveal, cut the sealant to the brickwork and lift it out. **Keep the existing head flashing above the lintel intact.**

### 2 · Measure
- Width reveal to reveal and height head to brick sill, three points each; use the smallest.
- Timber reveal at least {fmt(D['DEPTH'])} mm deep.
- Put the numbers in your params file, regenerate and rebuild the BOM (Size it section). **Only print after this measurement.**
"""), cols="1fr 1fr", gap=36))

    slide("install", "Step 3 · Sill tray", grid(svg_sill_tray(), md(f"""
Lay {hm.q('Butyl flashing tape')} m of 150 mm butyl flashing tape across the opening floor:

- turned up **30 mm** at the back (room side);
- across the full **63 mm** frame depth;
- running out at least **50 mm** over the brick sill;
- turned up **100 mm** at each end.

With 100 mm tape, lay two runs: the outer run first, then the inner run lapped 50 mm over it, so the lap sheds water outward.
"""), cols="620px 1fr", gap=30))

    sv, nfix, npk, qx = svg_fixmap(hm, 560, 560, focus="packers")
    if str(nfix) != hm.q("Timber screw") or str(npk) != hm.q("packers"):
        sys.exit(f"fixing map ({nfix} fixings, {npk} packers) disagrees with the BOM")
    slide("install", "Step 4 · Set the frame on packers", grid(sv, md(f"""
1. Stand the frame on plastic packers under the two **sill corners** (purple) and under each **[[GW]] quarter point** (orange): {qx} mm in from each outer frame edge on this window. Mark them on the sill. These two carry the fixed pane's weight straight into the wall.
2. Centre the frame, then plumb and square it: **diagonals within 2 mm**.
3. Wedge it with packers between the jambs and the reveal at the two **head corners**.
4. Tuck the head under the existing head flashing.

?? The other black marks are the packers behind each fixing in step 5: {npk} packer stacks in all.
""", steps=True), cols="560px 1fr", gap=32))

    sv, nfix, npk, qx = svg_fixmap(hm, 560, 560, focus="fixings")
    slide("install", "Step 5 · Fix it", grid(sv, md(f"""
- Drive a **10g × 75** screw through every fixing hole into the reveal and studs ({nfix} here), with a packer behind each, so the frame doesn't bow. Holes sit at each segment middle, both legs of every corner and two in each node.
- The node fixings carry the transom: pack them tight. The screws should hold, not crush.
""") + swatches([
        ("#1f6fb8", "**Bed it:** sill [[S]] / [[SW]], both legs of [[CSL]] / [[CSR]], lower jambs [[JL]] and both node fixings [[JN]] open into the drained pocket or outside the sash seal. Bed each screw in MS polymer and fill its counterbore flush."),
        ("#c0392b", "**Dry:** head [[H]], upper jambs [[JU]] and [[CH]] sit between the two seals."),
    ]) + md("""
!! Drive every frame fixing before glazing, and before the stay tracks go on in step 8.
"""), cols="560px 1fr", gap=32))

    step_slide("install", "Step 6 · Assemble and fit the transom", DECK / "node.png", md(f"""
1. Measure between the two node faces (with the dovetail slots) at transom height, outside and inside edges; take the smaller. Design figure: **{fmt(node_gap)} mm**.
2. On the bench, seal, close and screw the dry-fitted transom with the joint rules. Spread its shims (0.5–1.5 mm each) so the shoes' outer faces end up **0.5 mm closer** than the measured distance. Over 2 mm to close up? Trim the tube first. Drive the tek screws.
3. Lay 3 mm foam cord in the groove across each shoe's outer end face; butter the rest of the face with MS polymer.
4. Lift the transom in from the room side and slide the shoe tongues down the node dovetails to the stop.
5. Drive the four **M4 × 16** countersunk lock screws down the dovetail flanks; their heads finish under the magnet strip.
6. Tool the squeezed-out sealant along each shoe/node seam.
""", steps=True), img_w=420, img_h=560)

    hh = lay["h"]
    seal_fig, seal_w = section_fig(hm, 0, 520, [(1, (-24, hh - 44), (18.5, hh - 44)), (2, (98, hh - 30), (53, hh - 49)),
                                                (3, (98, hh - 60), (62, hh - 48.5))], urange=(-34, 104))
    slide("install", "Step 7 · Frame seals and magnet strip", grid(md(f"""
### EPDM bulb seals: two continuous loops
Outer seal in the fin kerf, inner seal in the inner-stop kerf; {hm.q('EPDM bulb')} m in all.

1. Start each loop at the middle of the head.
2. Run it across the head, down an upper jamb, through the shoe turn, along the transom, through the other shoe turn, up the other jamb and back.
3. Push it in **without stretching** it.
4. Cut the end square and butt it to the start with a drop of gel CA.
""", steps=True), md(f"""
### Magnetic strip B
Press it into the frame's magnet channel: along the **lower half of the transom's inside face**, through each shoe turn, up both upper jambs and across the head ({hm.q('magnetic strip B')} m). It covers the lock-screw heads.

?? Strip B must be the matched partner of the screen's strip A, or a steel strip if A is a plain magnet.
"""), seal_fig + '<p class="small muted" style="margin-top:6px">Head section: outer seal (1), inner seal (2), strip B (3).</p>',
        cols=f"1fr 1fr {seal_w}px", gap=30))

    zf, wf = section_fig(hm, 3, 520, [(1, (98, 46.5), (40, 46.5))], dims=[((28, 40), (28, 112), "28", (28, 118)), ((46, 53), (46, 112), "46", (46, 118))])
    slide("install", "Step 8 · Hang the sash", grid(md(f"""
Two people. All frame fixings are in, and the stays are already on the sash.

1. Hold the sash in the opening and place each stay's track against its upper jamb, at the height the stay's datasheet shows.
2. Centre each track **35–35.5 mm** in from the frame's outside face, level with its sash arm. Its body sits between the jamb fin top (28) and the sash lip (46); its screws hit the jamb tube (21.5–41.5 mm in; V-slot cores: see the V-slot slide) below the [[JU]] fixing counterbores (43–53 mm in).
3. Drill 3.2 mm pilots (3.5 mm with V-slot cores) through the track holes and screw the track on with **8g × 25** stainless countersunk screws.
4. Close the sash and check both seals touch evenly; adjust with the stay screws if needed.
""", steps=True), zf, cols=f"1fr {wf}px", gap=32))

    z2, w2 = section_fig(hm, 2, 520, [(1, (98, 40), (30, 40)), (2, (98, 62), (44, 46)), (3, (-30, 47), (6, 47))], urange=(-40, 104))
    slide("install", "Step 9 · Glaze the fixed pane", grid(z2, md("""
1. Fit the outer wedge gasket into the stop kerfs (3).
2. Place two [[GW]] wedge blocks (1) on the sill floor at the quarter points, over the step-4 packers, and one [[GF]] locator at mid-height on each side.
3. Fit the glass, or the fixed acrylic unit.
4. Snap in the [[BFH]] / [[BFV]] beads (2) from the room side, with the inner wedge gasket.

!! Lift the IGU with two people and suction lifters. Set it on the blocks; never on the bare sill.
""", steps=True), cols=f"{w2}px 1fr", gap=32))

    step_slide("install", "Step 10 · Seal outside", DECK / "sill-detail.png", md(f"""
1. Push backer rod into the gap between the frame and the brickwork ({hm.q('Backer rod')} m), gun MS polymer over it and tool it smooth.
2. Clip on the sill-nose pieces [[NS]] with 1 mm gaps between them. The end pieces stop 17 mm from each frame edge. Tool a small fillet of MS polymer from each nose end to the perimeter seal.
3. Push in the four weep caps [[WC]], open end facing down: two on the [[SW]] sill weeps and two on the [[SBE]] sash weeps (open the sash to reach them). The [[TE]] fin weeps get no cap.

!! Never seal over weep holes or the nose drip.
""", steps=True), img_h=420, cap="[[SW]] segment from outside: weep cap and two nose pieces pulled off.")

    step_slide("install", "Steps 11–13 · Inside, screen, cams", DECK / "hinge.png", md(f"""
11. **Inside:** fill the gap to the reveal with low-expansion foam, trim it and refit the architraves.
12. **Screen:** screw the [[HG]] leaves to the head inserts (two M4 × 10 pan or button heads each). Pin an [[HS]] into each with an M4 × 50 bolt and nyloc, snug but free to turn. Hold the screen closed on its magnets with an even **10 mm overlap** all round, swing the [[HS]] leaves onto its top rail and screw them with 4g × 12 screws (2 mm pilots). Check the strip closes along all four sides.
13. **Cams:** with the sash closed, turn each lever 60° counter-clockwise. The sash pulls in about 3 mm and both seals compress evenly.
""", steps=True), side=svg_hinges(hm, 520, 170), img_w=520, img_h=360)


def manual_sections():
    text = (ROOT / "docs" / "user-manual.md").read_text()
    parts = re.split(r"^## ", text, flags=re.M)
    out = {}
    for p in parts[1:]:
        head, _, body = p.partition("\n")
        out[head.strip()] = chipify(body.strip())
    return out


def manual_slides(hm, bn):
    ms = manual_sections()
    expected = ["Operation", "Screen", "Ventilation and weather", "Cleaning", "Maintenance schedule", "Seasonal care",
                "Troubleshooting", "Safety", "Spare parts and repairs", "Specifications"]
    if list(ms) != expected:
        sys.exit(f"docs/user-manual.md sections changed: {list(ms)}")
    op = ms["Operation"]
    a, b = op.split("### Closing and latching")
    b, note = b.split("\n\nThe two cams")
    slide("manual", "Operating the window", grid(
        fig(DECK / "inside-open.png", 360, 420, pad=0.03, cap="Screen lifted, sash pushed out."),
        md(a.replace("### Opening the sash", "### Opening the sash"), steps=True),
        md("### Closing and latching" + b, steps=True) + md("?? The two cams" + note),
        cols="360px 1fr 1fr", gap=28))
    slide("manual", "Screen, ventilation and weather", grid(md("### Screen\n" + ms["Screen"]), md("### Ventilation and weather\n" + ms["Ventilation and weather"]),
                                                       cols="1fr 1fr", gap=36))
    clean = ms["Cleaning"]
    slide("manual", "Cleaning", grid(md(clean), fig(DECK / "sill-detail.png", 380, 300, pad=0.04,
                                                     cap="Weep cap [[WC]] on an [[SW]] sill segment: pull, clear the slot, push back open end down."),
                                     cols="1fr 380px", gap=32))
    sched, tail = ms["Maintenance schedule"].split("\n\nIn the first year")
    slide("manual", "Maintenance schedule", md(sched, table_cls="xl compact") + md("?? In the first year" + tail))
    slide("manual", "Seasonal care", grid(md(ms["Seasonal care"]), fig(DECK / "section-1.png", 360, 440, pad=0.02,
                                                                       cap="Weeps (blue) in the [[TE]] fin and [[SBE]] rail keep the pockets drained."),
                                          cols="1fr 360px", gap=34))
    rows = [r for r in ms["Troubleshooting"].splitlines() if r.startswith("|")]
    half = 2 + (len(rows) - 2 + 1) // 2
    slide("manual", "Troubleshooting (1/2)", md("\n".join(rows[:half]), table_cls="xl compact"))
    slide("manual", "Troubleshooting (2/2)", md("\n".join(rows[:2] + rows[half:]), table_cls="xl compact"))
    slide("manual", "Safety", md(ms["Safety"]).replace("<ul>", '<ul class="cols2 lg">'))
    spare_ids = ["BSH", "WC", "NS", "CMH", "KP", "HS"]
    spare_tiles = "".join(f'<div class="tile">{fig(DECK / f"part-{i}.png", 180, 110, pad=0.05)}<div class="t"><span class="id">{i}</span> {esc(PART_NAMES[i])}</div></div>'
                          for i in spare_ids)
    slide("manual", "Spare parts and repairs", md(ms["Spare parts and repairs"])
          + f'<div class="tiles" style="grid-template-columns:repeat(6,1fr);margin-top:6px">{spare_tiles}</div>')

    fw, fh = hm.glass_size("fixed")
    sw, sh = hm.glass_size("sash")
    ext, inn, ext_item = hm.filament()
    p = hm.params
    spec_rows = [
        ["Opening", f"{fmt(p['opening_w'])} × {fmt(p['opening_h'])} mm, brick veneer, {fmt(p['fix_gap'])} mm gap each side"],
        ["Frame", f"{fmt(hm.lay['w'])} × {fmt(hm.lay['h'])} mm, {fmt(D['DEPTH'])} mm deep, {fmt(D['FRAME_W'])} mm face"],
        ["Layout", f"{fmt(p['awning_h'])} mm top awning over a fixed pane"],
        ["Glazing", f"24 mm IGU 4/16/4: fixed {fw} × {fh} mm, sash {sw} × {sh} mm"],
        ["Sash", f"About {fmt(hm.lay['sash_kg'])} kg on a {hm.lay['stay']} mm stainless friction-stay pair"],
        ["Transom", "40 × 20 × 1.6 steel tube: " + hm.check("transom_deflection")["msg"].replace("transom deflects ", "")],
        ["Seals", "Two continuous EPDM bulb loops round the sash; wedge gaskets both sides of the glass"],
        ["Printed parts", f"{hm.prints} prints in {hm.types} types: {fmt(ext)} kg exterior (tier {p['tier']}) + {fmt(inn)} kg interior PETG"],
        ["Glass thermal", "About 2.7–3.0 W/m²K at the glass for double glazing (single glazing about 6): a design target, not a tested rating"],
    ]
    spec_md = ms["Specifications"]
    for needle in [f"{fw} × {fh}", f"{sw} × {sh}", f"{fmt(hm.lay['sash_kg'])} kg", f"{hm.prints} prints", f"{fmt(ext)} kg", f"{fmt(inn)} kg",
                   f"{fmt(hm.lay['w'])} × {fmt(hm.lay['h'])}"]:
        if needle not in spec_md:
            sys.exit(f"docs/user-manual.md Specifications is stale: {needle!r} not found")
    slide("manual", f"Specifications ({fmt(p['opening_w'])} × {fmt(p['opening_h'])} home window)", grid(
        table(["Item", "Value"], spec_rows, cls="big", widths=["22%", "78%"])
        + md("Your own window's figures are in `bom/<name>.md` and in the lines `generate.py` prints."),
        fig(DECK / "hero.png", 300, 420, pad=0.03), cols="1fr 300px", gap=30))


def test_slides(hm, bn):
    text = (ROOT / "docs" / "test-log.md").read_text()
    rows = [r for r in text.splitlines() if r.startswith("|")]
    head = "| # | Test | Method | Pass criterion |"
    body = []
    for r in rows[2:]:
        c = [x.strip() for x in r.strip().strip("|").split("|")]
        body.append(f"| {c[0]} | **{c[1]}** | {c[2]} | {c[3]} |")
    chunks = [body[i:i + 4] for i in range(0, len(body), 4)]
    for n, chunk in enumerate(chunks, 1):
        intro = md(f"""
Bench window `params/{bn.name}.json` ({bn.params['glazing']} glazing, tier {bn.params['tier']}), mounted in a timber test box ({fmt(bn.params['opening_w'])} × {fmt(bn.params['opening_h'])} opening, 63 mm deep) and fixed exactly as in the install guide. Record each result in `docs/test-log.md`.
""") if n == 1 else ""
        notes = md("""
?? The joint sealant is assumed to take the movement: each 1 mm gap cycles between about 0 mm (hot) and 1.3 mm (cold). Repeat rows 2–3 after a hot day and a cold night, and record any joint whose sealant has torn or come away.

?? Rows 8–9 need a window with bays: `docs/test-log.md` gives a 2-bay bench window (`bench-1000-2bay`, 1000 × 600). Rows 10–12 are for V-slot cores: save `bench-600` as `params/bench-600-vslot.json` with `"name": "bench-600-vslot"` and `"core": "vslot"` added.
""") if n == len(chunks) else ""
        slide("test", f"Bench test protocol ({n}/{len(chunks)})",
              intro + md("\n".join([head, "|---|---|---|---|"] + chunk), table_cls="xl compact") + notes)
    slide("test", "The gate before the full-size build", grid(md(f"""
1. **Friction stay found:** a {hm.lay['stay']} mm pair rated ≥ {fmt(hm.lay['sash_kg'])} kg, stack ≤ {fmt(D['SASH_GAP'])} mm, width ≤ {fmt(D['STAY_W'])} mm. If none exists, the sash cavity or tube must change, and the frame, sash and corner parts be re-rendered.
2. **Bench rows 1–6 passed:** fit, water, air, heat/creep, sash load, cam. A window with bays also needs rows 8–9 (mullion tees, shoe pull-out) passed on a 2-bay bench window. V-slot cores run rows 1–6 on the V-slot bench window (`bench-600-vslot`) as well, since row 5 loads the sash through its M5 corners and V-slot stays, and also need rows 10–12 (profile, stay screw pull-out, T-nut hold).
3. **Opening measured,** params updated, `generate.py` clean (no `WARNING`), BOM rebuilt.
4. **Glass ordered** from `bom/<name>-glass.csv`, toughened where AS 1288 requires.
5. **Material tier** chosen for the wall's sun exposure, in a light colour.

++ Then print the home window: {hm.prints} parts.
""", steps=True), fig(DECK / "hero-bench.png", 460, 420, pad=0.04, cap=f"The {fmt(bn.params['opening_w'])} × {fmt(bn.params['opening_h'])} bench window: {bn.prints} prints, the same profiles and hardware."),
        cols="1fr 460px", gap=34))


def appendix_slides(hm, bn):
    rows = [r for r in bn.bom]
    per = math.ceil(len(rows) / 3)
    chunks = [rows[i:i + per] for i in range(0, len(rows), per)]
    for n, chunk in enumerate(chunks, 1):
        groups = []
        for r in chunk:
            if r["group"] not in groups:
                groups.append(r["group"])
        html_rows = "".join(f'<tr><td>{esc(r["group"])}</td><td>{inline(r["item"])}</td><td class="r">{esc(fmt(r["qty"]))}</td><td>{esc(r["unit"])}</td></tr>' for r in chunk)
        slide("appendix", f"A1 · Bench window bill of materials ({n}/{len(chunks)})",
              '<table class="xl compact r"><colgroup><col style="width:11%"><col style="width:73%"><col style="width:8%"><col style="width:8%"></colgroup>'
              '<thead><tr><th>Group</th><th>Item</th><th>Qty</th><th>Unit</th></tr></thead><tbody>' + html_rows + "</tbody></table>",
              kicker="Appendices · bom/bench-600.csv")

    def cut(win):
        return table(["Member", "Core", "mm", "Qty"], [[t["member"].replace("_", " "), t["core"], fmt(t["length_mm"]), t["qty"]] for t in win.cut], cls="num compact")

    def gl(win):
        return table(["Pane", "Glazing", "W", "H", "Qty"], [[g["pane"], g["glazing"], g["width_mm"], g["height_mm"], g["qty"]] for g in win.glass], cls="num compact")
    slide("appendix", "A2 · Cut lists and glass: home and bench", grid(
        "<h3>home-1800x1500</h3>" + cut(hm) + gl(hm), "<h3>bench-600</h3>" + cut(bn) + gl(bn), cols="1fr 1fr", gap=36))

    keys = [("DEPTH", "frame depth"), ("FRAME_W", "frame face"), ("FRAME_BODY", "frame body"), ("TRANSOM_W", "transom width"),
            ("TRANSOM_HALF_BODY", "transom half body"), ("SASH_W", "sash width"), ("SASH_BODY", "sash body"), ("SASH_GAP", "sash gap (stay cavity)"),
            ("STAY_W", "max stay width"), ("SCREEN_W", "screen rail width"), ("SCREEN_DEPTH", "screen depth"), ("SCREEN_OVERLAP", "screen overlap"),
            ("GLASS_T", "glazing pocket"), ("GLASS_EDGE", "fixed-glass edge cover"), ("SASH_GLASS", "sash-glass edge cover"), ("BEAD_T", "bead thickness"),
            ("MAX_SEG", "max segment length"), ("JOINT_GAP", "joint gap"), ("CORD_D", "cord groove width"), ("MIN_SHELL", "min plastic round tube"),
            ("CHAMBER_WALL", "chamber wall"), ("SOCKET_FRAME", "frame tube socket"), ("SOCKET_SASH", "sash tube socket"), ("SOCKET_SCREEN", "screen tube socket"),
            ("SILL_SLOPE_DEG", "sill pocket slope (°)"), ("NOSE_PROJECTION", "sill-nose projection"), ("INSERT_M4_D", "insert hole Ø"), ("FIX_CB_D", "fixing counterbore Ø")]
    rows = [[f"`{k}`", lbl, fmt(D[k])] for k, lbl in keys]
    third = (len(rows) + 2) // 3
    slide("appendix", "A3 · Key dimensions (`cad/dims.json`, mm)", grid(
        *[table(["Key", "", "Value"], rows[i:i + third], cls="num compact") for i in range(0, len(rows), third)], cols="1fr 1fr 1fr", gap=24))

    slide("appendix", "A4 · Repository map", grid(md("""
- `params/`: one JSON file per window
- `tools/window.py`: layout, segment splits, glass, tube cuts, checks
- `tools/generate.py`: part wrappers and CSVs in `cad/generated/`
- `tools/check_stl.py`, `stl.py`: STL checks; `test_*.py`: Python tests
- `cad/dims.json`: every shared dimension
- `cad/profile.scad`: every cross-section
- `cad/lib/`, `cad/parts/`: segments, corners, nodes, shoes, small parts
- `cad/tests/`: OpenSCAD assert tests and the review views
"""), md("""
- `cad/box.sh`: render, test and png on the OpenSCAD machine
- `cad/stl/<name>/`: the printable STLs
- `cad/deck/`: views for this guide's illustrations
- `bom/build_bom.py` and `bom/<name>.*`: BOM, cut list, glass, part list
- `docs/`: design spec, plan, printing, build and install guides, test log, owner's manual, images
- `pdf/build_deck.py`: this guide, as `OpenWindow-Guide.pdf`
"""), cols="1fr 1fr", gap=36))

    slide("appendix", "A5 · Rebuild everything, credits and licence", grid(md("""
```
python3 tools/generate.py params/<name>.json
cad/box.sh render <name>
python3 bom/build_bom.py <name>
cd tools && python3 -m unittest discover -p 'test_*.py'
cad/box.sh test
python3 pdf/build_deck.py
```
- Deck illustrations: `python3 pdf/render_deck.py` (one line per image in `pdf/deck_renders.txt`)
- Check one slide: `python3 pdf/build_deck.py --slide N --png out.png`
"""), md(f"""
### Credits and licence
- OpenWindow v1: design, CAD, generator and guides by the OpenWindow project.
- Modelled in OpenSCAD (manifold backend); this guide is built with Python and headless Chrome.
- **Licence: to be chosen.** Until then, ask before redistributing.

?? Status: designed and checked in CAD and software only. No window has been printed or tested yet; the bench test is next.
"""), cols="1.15fr 1fr", gap=36))


def toc_body(slides):
    first, last = {}, {}
    for i, s in enumerate(slides, 1):
        if s["sec"] == "cover":
            continue
        first.setdefault(s["sec"], i)
        last[s["sec"]] = i
    desc = {
        "overview": "why, what v1 is, the home window, honest limits", "how": "layout, units, tubes and joints, sections, glazing, hardware, stay gate",
        "materials": "tiers, exterior and interior parts", "size": "measure, params, generate, render, BOM",
        "print": "settings, orientation, inserts, part catalogue, filament", "shop": "bill of materials, cut list, glass, tools",
        "build": "joint rules and the six bench steps", "install": "the 13 steps into a brick-veneer opening",
        "manual": "operation, cleaning, maintenance, troubleshooting, safety", "test": "bench protocol and the gate",
        "appendix": "bench BOM, cut lists, dimensions, repository, rebuild"}
    rows = []
    for key, (name, color) in SECTIONS.items():
        if key not in first:
            continue
        rows.append(f'<div class="row"><span class="dot" style="background:{color}"></span><span class="nm">{esc(name)}'
                    f'<span class="ds">{esc(desc[key])}</span></span><span class="rg">{first[key]}{"–" + str(last[key]) if last[key] != first[key] else ""}</span></div>')
    return f'<div class="toc">{"".join(rows)}</div>'


def build_all():
    hm, bn, tb = Window(HOME), Window(BENCH), Window(TWO_BAY)
    masses = {HOME: hm.part_mass_g(), BENCH: bn.part_mass_g()}
    today = datetime.date.today().strftime("%-d %B %Y")
    SLIDES.clear()
    overview_slides(hm, bn, today)
    how_slides(hm, bn)
    materials_slides(hm, bn)
    size_slides(hm, bn, tb)
    print_slides(hm, bn, masses)
    shop_slides(hm, bn)
    build_slides(hm, bn)
    install_slides(hm, bn)
    manual_slides(hm, bn)
    test_slides(hm, bn)
    appendix_slides(hm, bn)
    for s in SLIDES:
        if s["body"] == "{{TOC}}":
            s["body"] = toc_body(SLIDES)
    total = len(SLIDES)
    out = [render_slide(i, s, total, today) for i, s in enumerate(SLIDES, 1)]
    BOXES.save()
    unused = sorted(p.name for p in DECK.glob("*.png") if p not in USED_IMAGES)
    if unused:
        print("unused deck images: " + ", ".join(unused))
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--slide", type=int, help="screenshot one slide (1-based) instead of building the PDF")
    ap.add_argument("--png", help="output PNG for --slide")
    ap.add_argument("--png-all", help="screenshot every slide into this folder")
    ap.add_argument("--check", action="store_true", help="report slides whose content overflows")
    ap.add_argument("--no-pdf", action="store_true", help="write the HTML only")
    a = ap.parse_args()
    slides = build_all()
    if a.slide:
        if not a.png:
            sys.exit("--slide needs --png")
        if not 1 <= a.slide <= len(slides):
            sys.exit(f"slide {a.slide} out of range 1..{len(slides)}")
        ok = screenshot(slides[a.slide - 1], a.png)
        print(f"slide {a.slide}/{len(slides)} -> {a.png}" if ok else "screenshot failed")
        return 0 if ok else 1
    if a.png_all:
        d = pathlib.Path(a.png_all)
        d.mkdir(parents=True, exist_ok=True)
        with concurrent.futures.ThreadPoolExecutor(4) as ex:
            res = list(ex.map(lambda i: screenshot(slides[i], d / f"slide-{i + 1:02d}.png"), range(len(slides))))
        print(f"{sum(res)}/{len(slides)} slides -> {d}")
        return 0 if all(res) else 1
    if a.check:
        print("overflow:", check_overflow(slides))
        return 0
    OUT_HTML.write_text(page_html(slides))
    print(f"wrote {OUT_HTML.relative_to(ROOT)} ({len(slides)} slides, {OUT_HTML.stat().st_size // 1024} KB)")
    if a.no_pdf:
        return 0
    write_pdf(OUT_HTML, OUT_PDF)
    n, boxes = pdf_pages(OUT_PDF)
    print(f"wrote {OUT_PDF.relative_to(ROOT)} ({OUT_PDF.stat().st_size // 1024} KB, {n} pages, MediaBox {boxes})")
    if n and n != len(slides):
        sys.exit(f"PDF has {n} pages for {len(slides)} slides")
    return 0


if __name__ == "__main__":
    sys.exit(main())
