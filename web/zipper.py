"""The download zip for one window, and the README.txt that goes in it."""
import io
import pathlib
import sys
import zipfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "bom"))

import build_bom  # noqa: E402

FILES = [
    ("stl/", "one STL per part type, named <ID>_x<qty>.stl: print <qty> of each"),
    ("parts.csv", "the print list: id, qty, role (exterior/interior), length"),
    ("cutlist.csv", "tube cut list"),
    ("glass.csv", "glass or acrylic sizes"),
    ("BOM.md", "bill of materials, cut list, glass and filament estimate"),
    ("OpenWindow-Guide.pdf", "the whole job as a slide deck: sizing, printing, assembly, installation, tests"),
    ("params.json", "the params file; copy it to params/<name>.json to regenerate or re-render"),
]


def readme(name, params, checks, missing, weight=None):
    lines = []
    failed = [c for c in checks if not c["ok"]]
    if failed:
        lines += ["CHECKS FAILED — do not print", ""]
        lines += [f"  - {c['name']}: {c['msg']}" for c in failed] + [""]
    if missing:
        lines += ["PARTIAL ZIP — these parts are missing or failed their STL check and are not in stl/:", "",
                  f"  {', '.join(missing)}", ""]
    bed = params.get("bed", [256, 256, 256])
    screen = params.get("screen", True)
    tier = params["tier"]
    lines += [
        f"OpenWindow: {name}",
        "",
        f"Opening {params['opening_w']:g} x {params['opening_h']:g} mm, fixing gap {params['fix_gap']:g} mm, "
        f"awning {params['awning_h']:g} mm, glazing {params['glazing']}, tier {tier}, "
        f"screen {'yes' if screen else 'no'}, bed {' x '.join(f'{v:g}' for v in bed)} mm.",
        "",
        "Checks",
    ]
    lines += [f"  {'ok  ' if c['ok'] else 'FAIL'}  {c['name']}: {c['msg']}" for c in checks]
    if weight:
        lines += [
            "",
            f"Weight estimate: about {weight['total_kg']} kg all up ({weight['kg_per_m2']} kg/m2):",
            f"  glass {weight['glass_kg']} kg, tube cores {weight['core_kg']} kg, "
            f"printed plastic {weight['plastic_kg']} kg, hardware and seals {weight['hardware_kg']} kg.",
            f"  The sash alone is {weight['sash_kg']} kg; check the friction-stay pair rating against it.",
        ]
    lines += [
        "",
        "Print settings (full detail: docs/printing.md)",
        "  - 0.4 mm nozzle, 0.2 mm layers, 5 walls, 5 top and 5 bottom layers, 15% gyroid infill.",
        f"  - Exterior parts: {build_bom.MATERIAL[tier]} (tier {tier}). Interior parts: {build_bom.MATERIAL['interior']}.",
        "  - Segments stand on an end face exactly as exported, no supports. Corners as exported,",
        "    supports on the build plate only. Beads, sill nose and spacers lie flat on their longest face.",
        "  - Print the test coupon (TC) and one segment of each profile first, and check the fit.",
        "",
        "Files",
    ]
    lines += [f"  {f:<12} {text}" for f, text in FILES]
    lines += [
        "",
        "Guides (in the OpenWindow repo)",
        "  OpenWindow-Guide.pdf: the whole job as a slide deck",
        "  docs/printing.md, docs/build-guide.md, docs/install-guide.md, docs/user-manual.md",
    ]
    if not screen:
        lines.append("  No screen: skip the screen steps in the build and install guides.")
    return "\n".join(lines) + "\n"


def build(files):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for arc, data in files.items():
            zf.writestr(arc, data)
    return buf.getvalue()
