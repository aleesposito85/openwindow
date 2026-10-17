#!/usr/bin/env python3
"""OpenWindow web configurator: serves web/static/ and the JSON API on 127.0.0.1 and runs one render job at a time."""
import argparse
import collections
import json
import os
import pathlib
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

WEB = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(WEB))

import api  # noqa: E402

STATIC = WEB / "static"
TYPES = {".html": "text/html; charset=utf-8", ".css": "text/css; charset=utf-8",
         ".js": "text/javascript; charset=utf-8"}
BATCH = 6
LOG_LINES = 40
BOX_TTL = 30.0
MAX_BODY = 65536
UNREACHABLE = 255
KILL_AFTER = 15.0
SHUTDOWN_WAIT = 5.0
CONN_LOST = re.compile(r"connect to host|connection (reset|closed|refused|timed out)|operation timed out|broken pipe|"
                       r"no route to host|network is unreachable|could not resolve hostname|lost connection|"
                       r"ssh connection failed|scp exit 255", re.I)


def box_host():
    m = re.search(r"HOST=\$\{BOX_HOST:-([^}]+)\}", (api.ROOT / "cad" / "box.sh").read_text())
    return os.environ.get("BOX_HOST", m.group(1)).split("@")[-1]


def batches(ids, size=BATCH):
    return [ids[i:i + size] for i in range(0, len(ids), size)]


def stamp(path):
    try:
        st = path.stat()
    except FileNotFoundError:
        return None
    return st.st_ino, st.st_size, st.st_mtime_ns, st.st_ctime_ns


def kill_group(pgid, sig):
    try:
        os.killpg(pgid, sig)
    except (ProcessLookupError, PermissionError):
        pass


def group_alive(pgid):
    try:
        os.killpg(pgid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        pass
    return True


class Job:
    def __init__(self, command, root, host, name, params, ids):
        self.command, self.root, self.host, self.name, self.ids, self.params = command, root, host, name, ids, params
        self.lay = api.window.layout(params)
        self.plist = api.generate.parts(self.lay)
        self.by_id = {pt["id"]: pt for pt in self.plist}
        self.state, self.error, self.current, self.done = "running", "", [], 0
        self.parts = {pid: "queued" for pid in ids}
        self.errors = {}
        self.log = collections.deque(maxlen=LOG_LINES)
        self.started, self.finished = time.time(), None
        self.proc, self.pgid, self.killer, self.cancelled = None, None, None, False
        self.lock = threading.Lock()
        self.thread = threading.Thread(target=self.run, daemon=True)

    def snapshot(self):
        with self.lock:
            return {"state": self.state, "name": self.name, "params": dict(self.params), "total": len(self.ids),
                    "done": self.done, "current": list(self.current), "parts": dict(self.parts),
                    "errors": dict(self.errors), "error": self.error, "log_tail": list(self.log),
                    "started": self.started, "finished": self.finished,
                    "elapsed": round((self.finished or time.time()) - self.started, 1)}

    def note(self, line):
        with self.lock:
            self.log.append(line)

    def run(self):
        try:
            for batch in batches(self.ids):
                if not self.render(batch):
                    break
            if self.state == "running" and not self.cancelled:
                api.write_bom(self.name, self.lay, self.plist, self.root / "bom", root=self.root)
                with self.lock:
                    self.log.append(f"bom/{self.name}.md and CSVs written")
                    bad = [pid for pid, s in self.parts.items() if s != "ok"]
                    self.state = "failed" if bad else "done"
                    self.error = f"{len(bad)} part(s) failed: {', '.join(bad)}" if bad else ""
        except Exception as e:
            with self.lock:
                self.state, self.error = "failed", f"{type(e).__name__}: {e}"
        finally:
            with self.lock:
                if self.cancelled:
                    self.state = "cancelled"
                leftover = "cancelled" if self.cancelled else "skipped"
                self.parts = {pid: leftover if s in ("queued", "rendering") else s for pid, s in self.parts.items()}
                self.current, self.finished = [], time.time()
                killer, pgid = self.killer, self.pgid
            if killer is not None and not group_alive(pgid):
                killer.cancel()

    def render(self, batch):
        out = api.stl_dir(self.name, self.root)
        with self.lock:
            if self.cancelled:
                return False
            before = {pid: stamp(out / f"{pid}.stl") for pid in batch}
            for pid in batch:
                self.parts[pid] = "rendering"
            self.current = batch
            self.proc = proc = subprocess.Popen(self.command + ["render", self.name, *batch], stdout=subprocess.PIPE,
                                                stderr=subprocess.STDOUT, text=True, errors="replace",
                                                start_new_session=True)
            self.pgid = proc.pid
        lines = []
        try:
            with proc.stdout:
                for line in proc.stdout:
                    lines.append(line.rstrip())
                    self.note(lines[-1])
            rc = proc.wait()
        finally:
            if proc.poll() is None:
                self.stop(proc)
        if self.cancelled:
            return False
        down = rc == UNREACHABLE or (rc != 0 and any(CONN_LOST.search(x) for x in lines))
        error = f"Windows build box unreachable ({self.host})" if down else ""
        for pid in batch:
            after = stamp(out / f"{pid}.stl")
            stale = after is not None and after == before[pid]
            if error and (after is None or stale):
                errs = [error]
            elif stale:
                errs = [f"{pid}: box.sh did not write a new {pid}.stl"]
            else:
                errs = api.check_part(self.name, self.lay, self.by_id[pid], self.root)
            with self.lock:
                self.parts[pid] = "failed" if errs else "ok"
                if errs:
                    self.errors[pid] = errs
                self.done += 1
        if error:
            with self.lock:
                self.state, self.error = "failed", error
            return False
        return True

    def stop(self, proc):
        kill_group(self.pgid, signal.SIGTERM)
        try:
            proc.wait(KILL_AFTER)
        except subprocess.TimeoutExpired:
            kill_group(self.pgid, signal.SIGKILL)
            proc.wait()

    def cancel(self):
        with self.lock:
            self.cancelled = True
            pgid = self.pgid
        if pgid is None:
            return
        kill_group(pgid, signal.SIGTERM)
        killer = threading.Timer(KILL_AFTER, kill_group, (pgid, signal.SIGKILL))
        killer.daemon = True
        with self.lock:
            if self.killer is not None:
                self.killer.cancel()
            self.killer = killer
        killer.start()


class App:
    def __init__(self, root, command, host):
        self.root, self.command, self.host = pathlib.Path(root), command, host
        self.job, self.box = None, {"ok": None, "host": host, "checked": 0.0}
        self.lock, self.box_lock = threading.Lock(), threading.Lock()

    def running(self):
        job = self.job
        return job is not None and job.thread.is_alive()

    def busy(self, name):
        job = self.job
        return job is not None and job.name == name and job.thread.is_alive()

    def start(self, params, ids):
        with self.lock:
            if self.running():
                return None
            if api.save_params(params, self.root)[1]:
                api.clear_stls(params["name"], self.root)
            job = Job(self.command, self.root, self.host, params["name"], params, ids)
            self.job = job
            job.thread.start()
            return job

    def ping(self):
        try:
            return subprocess.run(self.command + ["ping"], capture_output=True, timeout=25).returncode == 0
        except subprocess.TimeoutExpired:
            return False

    def box_status(self):
        with self.box_lock:
            if time.time() - self.box["checked"] >= BOX_TTL:
                self.box = {"ok": self.ping(), "host": self.host, "checked": time.time()}
            return dict(self.box)

    def shutdown(self):
        job = self.job
        if job is None or not job.thread.is_alive():
            return
        job.cancel()
        job.thread.join(SHUTDOWN_WAIT)
        if job.thread.is_alive() and job.pgid is not None:
            kill_group(job.pgid, signal.SIGKILL)
            job.thread.join(SHUTDOWN_WAIT)


class Handler(BaseHTTPRequestHandler):
    app = None

    def log_request(self, code="-", size="-"):
        if isinstance(code, int) and code >= 500:
            super().log_request(code, size)

    def send(self, code, body, ctype, extra=None):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        for k, v in (extra or {}).items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(body)

    def reply(self, code, obj):
        self.send(code, json.dumps(obj).encode(), "application/json")

    def host_ok(self):
        port = self.server.server_address[1]
        host = self.headers.get("Host", "")
        if host in (f"127.0.0.1:{port}", f"localhost:{port}"):
            return True
        allow = getattr(self.server, "allow_hosts", ())
        name = host.rsplit(":", 1)[0] if ":" in host.rsplit(".", 1)[-1] else host
        return name in allow or host in allow

    def body(self):
        try:
            n = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            raise ValueError("bad Content-Length") from None
        if n < 0:
            raise ValueError("bad Content-Length")
        if n > MAX_BODY:
            raise ValueError("request body too large")
        return json.loads(self.rfile.read(n) or b"{}")

    def do_GET(self):
        if not self.host_ok():
            return self.reply(403, {"error": "forbidden host"})
        url = urlparse(self.path)
        seg = url.path.strip("/").split("/")
        if url.path == "/":
            return self.send_static("index.html")
        if url.path == "/guide.pdf":
            return self.send_guide()
        if len(seg) == 1 and seg[0] != "api":
            return self.send_static(seg[0])
        if seg == ["api", "presets"]:
            return self.reply(200, {"presets": api.PRESETS, "defaults": api.DEFAULTS, "max_pane": api.PAGE_MAX_PANE})
        if seg == ["api", "job"]:
            job = self.app.job
            return self.reply(200, job.snapshot() if job else {"state": "idle"})
        if seg == ["api", "box"]:
            return self.reply(200, self.app.box_status())
        if len(seg) == 4 and seg[:2] == ["api", "stl"]:
            return self.send_stl(seg[2], seg[3])
        if len(seg) == 3 and seg[:2] == ["api", "zip"]:
            return self.send_zip(seg[2], parse_qs(url.query).get("partial") == ["1"])
        return self.reply(404, {"error": "not found"})

    def do_POST(self):
        if not self.host_ok():
            return self.reply(403, {"error": "forbidden host"})
        if not (self.headers.get("Content-Type") or "").startswith("application/json"):
            return self.reply(415, {"error": "send application/json"})
        try:
            body = self.body()
        except ValueError as e:
            return self.reply(400, {"error": str(e)})
        path = urlparse(self.path).path
        if path == "/api/preview":
            return self.reply(200, api.preview(body))
        if path == "/api/render":
            return self.start_render(body)
        if path == "/api/cancel":
            job = self.app.job
            if not self.app.running():
                return self.reply(409, {"error": "no job is running"})
            job.cancel()
            return self.reply(200, {"job": job.snapshot()})
        return self.reply(404, {"error": "not found"})

    def send_guide(self):
        path = pathlib.Path(self.app.root) / "OpenWindow-Guide.pdf"
        if not path.is_file():
            path = api.ROOT / "OpenWindow-Guide.pdf"
        if not path.is_file():
            return self.reply(404, {"error": "OpenWindow-Guide.pdf not found; rebuild it with python3 pdf/build_deck.py"})
        self.send(200, path.read_bytes(), "application/pdf",
                  {"Content-Disposition": 'inline; filename="OpenWindow-Guide.pdf"'})

    def send_static(self, name):
        path = STATIC / name
        if path.suffix not in TYPES or path.parent != STATIC or not path.is_file():
            return self.reply(404, {"error": "not found"})
        self.send(200, path.read_bytes(), TYPES[path.suffix])

    def start_render(self, body):
        ids = body.pop("ids", None) if isinstance(body, dict) else None
        params, errors = api.validate(body)
        if not errors:
            try:
                plist = api.generate.parts(api.window.layout(params))
            except ValueError as e:
                errors[api.error_field(str(e))] = str(e)
        if errors:
            return self.reply(400, {"errors": errors})
        known = [pt["id"] for pt in plist]
        if ids is None:
            ids = known
        if not isinstance(ids, list) or not ids or not all(isinstance(i, str) and i in known for i in ids):
            return self.reply(400, {"errors": {"ids": "ids must be a non-empty list of this window's part IDs"}})
        try:
            job = self.app.start(params, [i for i in known if i in ids])
        except ValueError as e:
            return self.reply(400, {"errors": {"name": str(e)}})
        if job is None:
            return self.reply(409, {"error": "a render job is already running"})
        return self.reply(200, {"job": job.snapshot()})

    def send_stl(self, name, pid):
        with self.app.lock:
            code, out = self.read_stl(name, pid)
        if code != 200:
            return self.reply(code, {"error": out})
        self.send(200, out, "model/stl")

    def read_stl(self, name, pid):
        if self.app.busy(name):
            return 409, "a render job for this window is still running"
        try:
            plist = api.load(name, self.app.root)[2]
        except (ValueError, LookupError):
            return 404, "unknown window"
        if pid not in {pt["id"] for pt in plist}:
            return 404, "unknown part"
        try:
            return 200, (api.stl_dir(name, self.app.root) / f"{pid}.stl").read_bytes()
        except (FileNotFoundError, IsADirectoryError):
            return 404, "not rendered"

    def send_zip(self, name, partial):
        with self.app.lock:
            code, out = self.read_zip(name, partial)
        if code != 200:
            return self.reply(code, {"error": out})
        filename, data = out
        self.send(200, data, "application/zip", {"Content-Disposition": f'attachment; filename="{filename}"'})

    def read_zip(self, name, partial):
        if self.app.busy(name):
            return 409, "a render job for this window is still running"
        try:
            return 200, api.build_zip(name, partial, self.app.root)
        except (ValueError, LookupError) as e:
            return 404, str(e)
        except api.NotReady as e:
            return 409, str(e)
        except FileNotFoundError as e:
            return 409, f"a file changed while the zip was built ({e.filename or e}); try again"


def make_server(port, root, command, host=None, bind="127.0.0.1", allow_hosts=()):
    handler = type("BoundHandler", (Handler,), {"app": App(root, command, host or box_host())})
    srv = ThreadingHTTPServer((bind, port), handler)
    srv.daemon_threads = True
    srv.allow_hosts = tuple(allow_hosts)
    return srv


def main(argv):
    ap = argparse.ArgumentParser(description="OpenWindow web configurator (local only)")
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--bind", default="127.0.0.1",
                    help="interface to listen on (default 127.0.0.1; use 0.0.0.0 behind a reverse proxy)")
    ap.add_argument("--allow-host", action="append", default=[], dest="allow_hosts",
                    help="extra Host name to accept (repeatable); keeps other web pages from driving the API")
    ap.add_argument("--fake-render", action="store_true",
                    help="render with web/fake_box.py into a temporary folder instead of the Windows box")
    a = ap.parse_args(argv[1:])
    root, command = api.ROOT, [str(api.ROOT / "cad" / "box.sh")]
    if a.fake_render:
        root = pathlib.Path(tempfile.mkdtemp(prefix="openwindow-fake-"))
        command = [sys.executable, str(WEB / "fake_box.py"), "--root", str(root), "--delay", "0.4"]
    srv = make_server(a.port, root, command, bind=a.bind, allow_hosts=a.allow_hosts)
    app = srv.RequestHandlerClass.app

    def stop(signum, frame):
        raise KeyboardInterrupt

    for sig in (signal.SIGTERM, signal.SIGHUP):
        signal.signal(sig, stop)
    try:
        print(f"OpenWindow configurator: http://127.0.0.1:{srv.server_address[1]}/ (data in {root}; Ctrl-C to stop)",
              flush=True)
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        for sig in (signal.SIGTERM, signal.SIGHUP):
            signal.signal(sig, signal.SIG_IGN)
        app.shutdown()
        srv.server_close()
        if a.fake_render:
            shutil.rmtree(root, ignore_errors=True)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
