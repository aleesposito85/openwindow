#!/usr/bin/env python3
"""Headless-Chrome screenshots of the configurator's UI states, for review by eye (no installs; uses the Mac's Chrome)."""
import argparse
import json
import os
import pathlib
import signal
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request

WEB = pathlib.Path(__file__).resolve().parent.parent
ROOT = WEB.parent
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"


def params(name):
    return json.loads((ROOT / "params" / f"{name}.json").read_text())


def query(p, **extra):
    limit = ",".join(f"{v:g}" for v in p["max_pane"]) if "max_pane" in p else "none"
    return "/?" + urllib.parse.urlencode({**{k: v for k, v in p.items() if k not in ("bed", "max_pane")},
                                          "max_pane": limit, **extra})


def call(base, method, path, body=None):
    data = None if body is None else json.dumps(body).encode()
    req = urllib.request.Request(base + path, data=data, method=method,
                                 headers={"Content-Type": "application/json"} if body is not None else {})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())


def start(port, *flags):
    proc = subprocess.Popen([sys.executable, str(WEB / "server.py"), "--port", str(port), *flags])
    for _ in range(50):
        try:
            call(f"http://127.0.0.1:{port}", "GET", "/api/presets")
            return proc
        except OSError:
            time.sleep(0.2)
    raise SystemExit(f"server on port {port} did not start")


def shot(url, out, profile, budget=6000):
    out.unlink(missing_ok=True)
    chrome = subprocess.Popen([CHROME, "--headless=new", "--use-angle=swiftshader", "--enable-unsafe-swiftshader",
                               "--hide-scrollbars", "--no-first-run", "--no-default-browser-check",
                               f"--user-data-dir={profile}", "--window-size=1440,1100",
                               f"--virtual-time-budget={budget}", f"--screenshot={out}", url],
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
    end, size = time.time() + 60, -1
    while time.time() < end and not (out.exists() and out.stat().st_size == size > 0):
        size = out.stat().st_size if out.exists() else -1
        time.sleep(1)
    os.killpg(chrome.pid, signal.SIGTERM)
    chrome.wait(10)
    print(f"{out.name}: {url}" if out.exists() else f"{out.name}: NO SCREENSHOT ({url})")


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("out", type=pathlib.Path, help="folder for the PNGs")
    ap.add_argument("--port", type=int, default=8781)
    a = ap.parse_args(argv[1:])
    a.out.mkdir(parents=True, exist_ok=True)
    real, fake = f"http://127.0.0.1:{a.port}", f"http://127.0.0.1:{a.port + 1}"
    servers = [start(a.port), start(a.port + 1, "--fake-render")]
    try:
        with tempfile.TemporaryDirectory() as profile:
            shot(real + "/", a.out / "1-valid.png", profile)
            shot(real + "/?name=Bad%20Name&opening_w=100", a.out / "2-invalid.png", profile)
            shot(real + "/?opening_w=3000&name=wide", a.out / "3-failed-check.png", profile)
            bench = dict(params("bench-600"), name="shot-bench")
            call(fake, "POST", "/api/render", bench)
            time.sleep(4)
            shot(fake + query(bench), a.out / "4-rendering.png", profile, budget=1500)
            while call(fake, "GET", "/api/job")["state"] == "running":
                time.sleep(0.5)
            shot(fake + query(bench), a.out / "5-download.png", profile)
            shot(real + query(params("bench-600"), view="SBE"), a.out / "6-viewer-part.png", profile)
            shot(real + query(params("home-1800x1500"), view="assembled"), a.out / "7-viewer-assembled.png", profile, 10000)
            shot(real + query(params("home-1800x1500-2bay")), a.out / "8-two-bays.png", profile)
            shot(real + query(params("home-1800x1500-2bay"), view="assembled"), a.out / "9-viewer-two-bays.png", profile, 12000)
            shot(real + query(params("home-1800x1500-2bay"), max_pane="800,800"), a.out / "10-too-tall.png", profile)
            shot(real + query(params("home-1800x1500"), core="vslot"), a.out / "11-vslot.png", profile)
    finally:
        for s in servers:
            s.send_signal(signal.SIGINT)
            s.wait(10)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
