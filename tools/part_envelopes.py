#!/usr/bin/env python3
"""Write tools/part_envelopes.json: each part's bounding box (segments: cross-section only, beads per glazing) from rendered STLs."""
import json
import pathlib
import sys

import generate
import stl
import window

REFERENCES = ("home-1800x1500", "bench-600", "home-1800x1500-2bay")
OUT = pathlib.Path(__file__).resolve().parent / "part_envelopes.json"
TOL = 0.6


def envelope(box, length):
    if length is None:
        return sorted(box)
    axis = min(range(3), key=lambda a: abs(box[a] - length))
    if abs(box[axis] - length) > TOL:
        raise ValueError(f"no axis of {box} matches length {length}")
    return sorted(box[a] for a in range(3) if a != axis)


def collect(root, names, ids=None):
    env = {}
    for name in names:
        lay = window.layout(json.loads((root / "params" / f"{name}.json").read_text()))
        plist = generate.parts(lay)
        unknown = sorted(set(ids or ()) - {pt["id"] for pt in plist})
        if unknown:
            raise ValueError(f"unknown part ids for {name}: {', '.join(unknown)}")
        for pt in plist:
            if ids and pt["id"] not in ids:
                continue
            e = envelope(stl.bbox(stl.load(root / "cad" / "stl" / name / f"{pt['id']}.stl")), pt["length"])
            key = generate.envelope_key(pt, lay["params"]["glazing"])
            env[key] = [max(a, b) for a, b in zip(env.get(key, e), e)]
    return dict(sorted(env.items()))


def dumps(env):
    return "{\n" + ",\n".join(f"  {json.dumps(k)}: {json.dumps(v)}" for k, v in env.items()) + "\n}\n"


def main(argv):
    names, ids = (argv[1:2], set(argv[2:])) if len(argv) > 1 else (list(REFERENCES), set())
    measured = collect(window.ROOT, names, ids)
    old = json.loads(OUT.read_text()) if OUT.exists() else {}
    env = dict(sorted({**old, **measured}.items()))
    OUT.write_text(dumps(env))
    print(f"{OUT.name}: {len(measured)} measured from {', '.join(names)}, {len(env)} in all")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
