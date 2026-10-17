#!/usr/bin/env python3
"""Re-render the guide deck's illustrations listed in pdf/deck_renders.txt through cad/box.sh png."""
import argparse
import concurrent.futures
import os
import pathlib
import shlex
import subprocess
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parent.parent
LIST = ROOT / "pdf" / "deck_renders.txt"


def jobs(path, only):
    out = []
    for line in path.read_text().splitlines():
        if not line.strip() or line.startswith("#"):
            continue
        params, src, png, args = line.split("|")
        if not only or any(o in png for o in only):
            out.append((params, src, png, args))
    return out


def run(job):
    params, src, png, args = job
    start = time.time()
    p = subprocess.run(["cad/box.sh", "png", src, png, *shlex.split(args)], cwd=ROOT,
                       env={**os.environ, "PARAMS": params}, capture_output=True, text=True)
    return p.returncode, png, time.time() - start, (p.stdout + p.stderr)[-1500:]


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("only", nargs="*", help="only render outputs whose path contains one of these")
    ap.add_argument("--jobs", type=int, default=4, help="renders at once (default 4)")
    a = ap.parse_args(argv[1:])
    todo = jobs(LIST, a.only)
    failed = 0
    with concurrent.futures.ThreadPoolExecutor(a.jobs) as ex:
        for rc, png, dt, log in ex.map(run, todo):
            print(("ok   " if rc == 0 else "FAIL ") + f"{dt:5.1f}s {png}" + ("" if rc == 0 else "\n" + log), flush=True)
            failed += rc != 0
    print(f"{len(todo) - failed}/{len(todo)} images rendered")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
