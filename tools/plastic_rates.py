#!/usr/bin/env python3
"""Write tools/plastic_rates.json: printed-plastic volume per part, calibrated from rendered STLs.

Length-varying parts (segments, beads, spacers, sill nose) store cm3 per mm of part length;
fixed parts store cm3 per piece. Beads are keyed <ID>/<glazing> like part_envelopes.
tools/plastic.py uses the table to estimate plastic mass before any STL is rendered.
"""
import json
import pathlib
import sys

import generate
import stl
import window

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = pathlib.Path(__file__).resolve().parent / "plastic_rates.json"
REFERENCES = ("bench-600", "home-1800x1500", "home-1800x1500-2bay", "my-window")
LENGTH_MODULES = {"frame_segment", "sash_segment", "screen_segment", "bead", "acrylic_spacer", "sill_nose"}


def collect(names):
    per_id = {}
    for name in names:
        params = json.loads((ROOT / "params" / f"{name}.json").read_text())
        lay = window.layout(params)
        for pt in generate.parts(lay):
            f = ROOT / "cad" / "stl" / name / f"{pt['id']}.stl"
            if not f.exists():
                raise ValueError(f"{name}: {pt['id']}.stl not rendered; render the references first")
            vol, area = stl.volume_area(stl.load(f))
            if pt["module"] == "bead":
                # bead depth follows the pane thickness, so key by it
                key = f"{pt['id']}/{generate.pane_thickness(lay):g}"
            elif pt["module"] in LENGTH_MODULES:
                key = pt["id"]
            else:
                key = pt["id"]
            if pt["module"] in LENGTH_MODULES or pt["module"] == "bead":
                if not pt["length"]:
                    raise ValueError(f"{key}: length-varying module without a length")
                per_id.setdefault(key, []).append((vol / pt["length"], area / pt["length"]))
            else:
                per_id.setdefault(key, []).append((vol, area))
    rates = {}
    for key, samples in sorted(per_id.items()):
        values = [s[0] for s in samples]
        spread = (max(values) - min(values)) / max(values)
        if spread > 0.12:
            print(f"note: {key} varies {spread:.0%} across windows", file=sys.stderr)
        rates[key] = {"vol": round(sum(s[0] for s in samples) / len(samples), 6),
                      "area": round(sum(s[1] for s in samples) / len(samples), 6)}
    return rates


def main(argv):
    rates = collect(argv[1:] or list(REFERENCES))
    OUT.write_text("{\n" + ",\n".join(f"  {json.dumps(k)}: {json.dumps(v)}" for k, v in sorted(rates.items())) + "\n}\n")
    print(f"{OUT.name}: {len(rates)} part rates from {', '.join(argv[1:] or REFERENCES)}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
