#!/usr/bin/env python3
"""Estimate printed-plastic mass from tools/plastic_rates.json, before any STL is rendered.

Same mass model as bom/build_bom.py (2.1 mm shell, 15% infill, per-tier density), so the
estimate is directly comparable to the measured filament rows in the BOM. Rates come from
the rendered reference windows; a part id with no rate falls back to the frame segment rate.
"""
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "bom"))
sys.path.insert(0, str(ROOT / "tools"))

import build_bom  # noqa: E402
import generate  # noqa: E402
import window  # noqa: E402
from build_bom import DENSITY, INFILL, SHELL_MM, mass_g  # noqa: E402

RATES_PATH = pathlib.Path(__file__).resolve().parent / "plastic_rates.json"
FALLBACK = "H"


def rates():
    return json.loads(RATES_PATH.read_text())


def mass_g_for(pt, rate, density):
    length = pt["length"] or 0.0
    vol = rate["vol"] * (length if length else 1.0)
    area = rate["area"] * (length if length else 1.0)
    return mass_g(vol, area, density)


def estimate(lay, parts):
    r = rates()
    tier = lay["params"]["tier"]
    pane = generate.pane_thickness(lay)
    grams = {"interior": 0.0, tier: 0.0}
    unknown = []
    for pt in parts:
        rate = None
        if pt["module"] == "bead":
            # bead depth follows the pane thickness, so rates are keyed by it
            key = f"{pt['id']}/{pane:g}"
            if key in r:
                rate = r[key]
            else:
                # uncalibrated pane depth: the bead profile deepens 1:1 with the
                # pocket it fills, so scale the closest rate by the depth ratio
                other = next((k for k in r if k.startswith(pt["id"] + "/")), None)
                if other:
                    cal = float(other.rsplit("/", 1)[1])
                    d = window.D["BEAD_T"] + window.D["GLASS_T"]
                    scale = (d - pane) / (d - cal)
                    rate = {k: r[other][k] * scale for k in ("vol", "area")}
        else:
            rate = r.get(pt["id"])
        if rate is None:
            rate = r[FALLBACK]
            unknown.append(pt["id"])
        key_mass = "interior" if pt["role"] == "interior" else tier
        grams[key_mass] += mass_g_for(pt, rate, DENSITY[key_mass]) * pt["qty"]
    kg = {k: round(g / 1000.0, 2) for k, g in grams.items()}
    return {"interior_kg": kg["interior"], "exterior_kg": kg[tier],
            "total_kg": round(sum(grams.values()) / 1000.0, 2), "unknown_ids": sorted(set(unknown))}
