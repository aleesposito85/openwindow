"""Check rendered STLs in cad/stl/<name>/ against cad/generated/parts.csv: bed fit, length, closed single-body mesh."""
import csv
import json
import pathlib
import sys

import stl
from window import DEFAULT_BED

ROOT = pathlib.Path(__file__).resolve().parent.parent
TOL = 0.6


def bed_text(bed):
    return f"{bed[0]:.0f}" if len(set(bed)) == 1 else " x ".join(f"{v:g}" for v in bed)


def check(row, stl_dir, bed=DEFAULT_BED):
    path = pathlib.Path(stl_dir) / f"{row['id']}.stl"
    if not path.exists():
        return [f"{row['id']}: missing {path.name}"]
    try:
        tris = stl.load(path)
        box = stl.bbox(tris)
    except ValueError as e:
        return [f"{row['id']}: unreadable STL: {e}"]
    errors = []
    if any(a > b for a, b in zip(sorted(box), sorted(bed))):
        errors.append(f"{row['id']}: {box} does not fit the {bed_text(bed)} mm bed")
    if row["length"] and not any(abs(d - float(row["length"])) <= TOL for d in box):
        errors.append(f"{row['id']}: no axis of {box} matches length {row['length']}")
    bad = stl.open_edges(tris)
    if bad:
        errors.append(f"{row['id']}: not closed, {bad} edges not shared by exactly two triangles")
    vols = stl.shell_volumes(tris)
    solid = [v for v in vols if v > 0]
    if len(solid) != 1:
        errors.append(f"{row['id']}: {len(solid)} solid shells, expected 1")
    if sum(vols) <= 0:
        errors.append(f"{row['id']}: non-positive volume {sum(vols):.3f} cm3")
    return errors


def main(argv, root=ROOT):
    if len(argv) < 2:
        print("usage: check_stl.py <params-name> [ID ...]", file=sys.stderr)
        return 2
    name = argv[1]
    params_path = root / "cad" / "generated" / "params.json"
    params = json.loads(params_path.read_text()) if params_path.exists() else {"name": name}
    if params.get("name") != name:
        print(f"generated output is for {params.get('name')!r}, not {name!r}; rerun generate.py first",
              file=sys.stderr)
        return 2
    rows = list(csv.DictReader((root / "cad" / "generated" / "parts.csv").read_text().splitlines()))
    if argv[2:]:
        wanted = argv[2:]
        known = {r["id"] for r in rows}
        unknown = sorted(set(wanted) - known)
        if unknown:
            print(f"unknown part ids: {', '.join(unknown)}", file=sys.stderr)
            return 2
        rows = [r for r in rows if r["id"] in wanted]
    if not rows:
        print("no parts to check", file=sys.stderr)
        return 2
    errors = [e for r in rows for e in check(r, root / "cad" / "stl" / name, params.get("bed", DEFAULT_BED))]
    for e in errors:
        print("FAIL", e)
    print(f"{len(rows) - len({e.split(':')[0] for e in errors})}/{len(rows)} parts ok")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
