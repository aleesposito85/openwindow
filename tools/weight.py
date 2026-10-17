#!/usr/bin/env python3
"""Weight estimate for a window: glass + tube cores + printed plastic + hardware allowance.

Glass and cores are exact from the layout. Plastic comes from tools/plastic.py (rates
calibrated on the rendered reference windows). Hardware and seals are a flat allowance
per metre of member; the BOM has the exact shopping list.
"""
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import plastic  # noqa: E402
import window  # noqa: E402
from window import CORES, GLAZING_KG_M2  # noqa: E402

HARDWARE_KG_M = 0.45


def estimate(params, lay, parts):
    sandwich = lay.get("sandwich")
    kg_m2 = GLAZING_KG_M2[params["glazing"]]
    if params["glazing"] == "acrylic" and sandwich:
        kg_m2 *= sandwich["t"] / window.D["ACRYLIC_T"]
    glass_kg = sum(w * h for w, h in lay["glass"].values()) / 1e6 * kg_m2 * lay["bays"]
    core_kg = sum(t["length"] / 1000.0 * CORES[t["core"]][4] * t["qty"] for t in lay["tubes"])
    member_m = sum(m["length"] / 1000.0 * m["qty"] for m in lay["members"])
    hard_kg = member_m * HARDWARE_KG_M
    fil = plastic.estimate(lay, parts)
    total = glass_kg + core_kg + fil["total_kg"] + hard_kg
    return {"glass_kg": round(glass_kg, 1), "core_kg": round(core_kg, 1),
            "plastic_kg": fil["total_kg"], "plastic_interior_kg": fil["interior_kg"],
            "plastic_exterior_kg": fil["exterior_kg"], "hardware_kg": round(hard_kg, 1),
            "total_kg": round(total, 1), "sash_kg": lay["sash_kg"],
            "kg_per_m2": round(total / (lay["w"] * lay["h"] / 1e6), 1)}
