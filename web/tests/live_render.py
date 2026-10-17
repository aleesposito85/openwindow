#!/usr/bin/env python3
"""Live end-to-end check (needs the Windows build box): render bench-600 through web/server.py, then check the zip."""
import argparse
import io
import json
import pathlib
import subprocess
import sys
import time
import urllib.error
import urllib.request
import zipfile

WEB = pathlib.Path(__file__).resolve().parent.parent
ROOT = WEB.parent
NAME = "bench-600"


def call(base, method, path, body=None):
    data = None if body is None else json.dumps(body).encode()
    req = urllib.request.Request(base + path, data=data, method=method,
                                 headers={"Content-Type": "application/json"} if body is not None else {})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        with e:
            return e.code, e.read()


def job(base):
    return json.loads(call(base, "GET", "/api/job")[1])


def wait(base, until, timeout):
    end, last = time.time() + timeout, None
    while time.time() < end:
        j = job(base)
        line = f"  {j['state']:<9} {j.get('done', 0):>2}/{j.get('total', 0)} current={' '.join(j.get('current', []))}"
        if line != last:
            print(f"{line}  ({j.get('elapsed', 0):.0f} s)", flush=True)
            last = line
        if until(j):
            return j
        time.sleep(2)
    raise SystemExit(f"timed out after {timeout} s: {j}")


def cancel_check(base, params, before):
    print("cancel check: start, wait for the second batch, cancel")
    assert call(base, "POST", "/api/render", params)[0] == 200
    wait(base, lambda j: j["done"] >= 6 or j["state"] != "running", 900)
    status, _ = call(base, "POST", "/api/cancel", {})
    j = wait(base, lambda j: j["state"] != "running", 120)
    lock = (ROOT / ".generate.lock").exists()
    kept = sorted(f.name for f in (ROOT / "cad" / "stl" / NAME).glob("*.stl"))
    print(f"cancel check: cancel -> {status}, state {j['state']}, generate lock left behind: {lock}, "
          f"reference STLs still there: {len(kept)}/{len(before)}")
    return status == 200 and j["state"] == "cancelled" and not lock and kept == sorted(before)


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--port", type=int, default=8799)
    ap.add_argument("--cancel", action="store_true", help="first start a render and cancel it during the second batch")
    a = ap.parse_args(argv[1:])
    base = f"http://127.0.0.1:{a.port}"
    params = json.loads((ROOT / "params" / f"{NAME}.json").read_text())
    before = {f.name: f.read_bytes() for f in (ROOT / "cad" / "stl" / NAME).glob("*.stl")}
    srv = subprocess.Popen([sys.executable, str(WEB / "server.py"), "--port", str(a.port)])
    try:
        for _ in range(50):
            try:
                call(base, "GET", "/api/presets")
                break
            except OSError:
                time.sleep(0.2)
        box = json.loads(call(base, "GET", "/api/box")[1])
        print(f"box {box['host']}: {'reachable' if box['ok'] else 'UNREACHABLE'}")
        if not box["ok"]:
            return 1
        if a.cancel and not cancel_check(base, params, before):
            return 1
        t0 = time.time()
        status, body = call(base, "POST", "/api/render", params)
        print(f"render -> {status}")
        if status != 200:
            print(body.decode())
            return 1
        j = wait(base, lambda j: j["state"] != "running", 1800)
        print(f"job {j['state']} in {time.time() - t0:.0f} s; error: {j['error'] or 'none'}")
        if j["state"] != "done":
            print("\n".join(j["log_tail"]))
            return 1
        status, data = call(base, "GET", f"/api/zip/{NAME}")
        z = zipfile.ZipFile(io.BytesIO(data))
        stls = [n for n in z.namelist() if n.startswith("stl/")]
        others = sorted(n for n in z.namelist() if not n.startswith("stl/"))
        same = sum(1 for n in stls if before.get(n[4:].split("_x")[0] + ".stl") == z.read(n))
        readme = z.read("README.txt").decode()
        print(f"zip -> {status}, {len(data)} bytes, {len(stls)} STLs, {same} byte-identical to the previous render")
        print(f"zip files: {', '.join(others)}")
        print(f"README first line: {readme.splitlines()[0]}")
        ok = (status == 200 and len(stls) == 37 and readme.startswith(f"OpenWindow: {NAME}")
              and others == ["BOM.md", "README.txt", "cutlist.csv", "glass.csv", "params.json", "parts.csv"])
        print("LIVE RENDER OK" if ok else "LIVE RENDER FAILED")
        return 0 if ok else 1
    finally:
        srv.terminate()
        srv.wait(10)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
