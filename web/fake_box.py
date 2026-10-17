#!/usr/bin/env python3
"""Stand-in for cad/box.sh (render | ping) for tests and server.py --fake-render: writes box STLs that pass check_stl."""
import argparse
import json
import pathlib
import signal
import struct
import subprocess
import sys
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import api  # noqa: E402

FACES = [(0, 2, 1), (0, 3, 2), (4, 5, 6), (4, 6, 7), (0, 1, 5), (0, 5, 4),
         (1, 2, 6), (1, 6, 5), (2, 3, 7), (2, 7, 6), (3, 0, 4), (3, 4, 7)]


def box_stl(sx, sy, sz):
    v = [(x * sx, y * sy, z * sz) for x, y, z in
         [(0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0), (0, 0, 1), (1, 0, 1), (1, 1, 1), (0, 1, 1)]]
    out = b"\0" * 80 + struct.pack("<I", len(FACES))
    for f in FACES:
        out += struct.pack("<3f", 0, 0, 0) + b"".join(struct.pack("<3f", *v[i]) for i in f) + b"\0\0"
    return out


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=pathlib.Path, required=True)
    ap.add_argument("--delay", type=float, default=0.0)
    ap.add_argument("--fail", default="")
    ap.add_argument("--exit", type=int, default=0)
    ap.add_argument("--drop", default="", help="lose the connection (exit 1, no STLs) in the batch with this ID")
    ap.add_argument("--garbage", action="store_true", help="print a line that is not valid UTF-8")
    ap.add_argument("--child", action="store_true", help="wait on a long-running child process")
    ap.add_argument("--child-ignores-term", action="store_true")
    ap.add_argument("--ignore-term", action="store_true")
    ap.add_argument("cmd", choices=["render", "ping"])
    ap.add_argument("args", nargs="*")
    a = ap.parse_args(argv[1:])
    if a.exit:
        print("ssh: connect to host 192.168.68.61 port 22: Operation timed out", flush=True)
        return a.exit
    if a.cmd == "ping":
        print("ok")
        return 0
    if a.ignore_term:
        signal.signal(signal.SIGTERM, signal.SIG_IGN)
    name, ids = a.args[0], a.args[1:]
    if a.garbage:
        sys.stdout.buffer.write(b"garbage: \xff\xfe not utf-8 \xc3\x28\n")
        sys.stdout.flush()
    if a.drop in ids:
        print("client_loop: send disconnect: Broken pipe", flush=True)
        print("box.sh: ssh connection failed (exit 255)", flush=True)
        return 1
    if a.child:
        ignore = "signal.signal(signal.SIGTERM, signal.SIG_IGN); " if a.child_ignores_term else ""
        code = f"import os, signal, time; {ignore}print(f'child pid {{os.getpid()}}', flush=True); time.sleep(60)"
        subprocess.Popen([sys.executable, "-c", code]).wait()
    params = json.loads(api.params_path(name, a.root).read_text())
    lengths = {pt["id"]: pt["length"] for pt in api.generate.parts(api.window.layout(params))}
    out = api.stl_dir(name, a.root)
    out.mkdir(parents=True, exist_ok=True)
    failed = set(a.fail.split(",")) & set(ids)
    print(f"fake render: {len(ids)} parts", flush=True)
    for pid in ids:
        print(f"== {pid}", flush=True)
        time.sleep(a.delay)
        if pid in failed:
            print(f"ERROR: fake render failure for {pid}", flush=True)
            continue
        (out / f"{pid}.stl").write_bytes(box_stl(10, 20, lengths[pid] or 20))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
