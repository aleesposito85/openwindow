"""Tests for web/server.py: the HTTP API on an ephemeral port, rendering with web/fake_box.py."""
import http.client
import io
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
import unittest
import urllib.error
import urllib.request
import zipfile
from unittest import mock

WEB = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(WEB))

import api  # noqa: E402
import fake_box  # noqa: E402
import server  # noqa: E402

REF = json.loads((api.ROOT / "params" / "bench-600.json").read_text())
BENCH = dict(REF, name="t-bench")
IDS = [pt["id"] for pt in api.generate.parts(api.window.layout(BENCH))]
HOST = "192.168.68.61"
UNREACHABLE = f"Windows build box unreachable ({HOST})"


def gone(pid, timeout=3):
    end = time.time() + timeout
    while time.time() < end:
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            return True
        time.sleep(0.05)
    return False


def seedReference(root):
    (root / "params").mkdir(exist_ok=True)
    shutil.copy(api.ROOT / "params" / "bench-600.json", root / "params")
    out = root / "cad" / "stl" / "bench-600"
    out.mkdir(parents=True)
    for pt in api.load("bench-600", root)[2]:
        (out / f"{pt['id']}.stl").write_bytes(fake_box.box_stl(12, 20, pt["length"] or 20))
    return {f.name: f.read_bytes() for f in out.glob("*.stl")}


class ServerCase(unittest.TestCase):
    fake = []
    kill_after = None

    def setUp(self):
        self.pids = []
        if self.kill_after is not None:
            patcher = mock.patch.object(server, "KILL_AFTER", self.kill_after)
            patcher.start()
            self.addCleanup(patcher.stop)
        self.tmp = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self.tmp.name)
        command = [sys.executable, str(WEB / "fake_box.py"), "--root", str(self.root), *self.fake]
        self.srv = server.make_server(0, self.root, command, HOST)
        self.app = self.srv.RequestHandlerClass.app
        self.port = self.srv.server_address[1]
        threading.Thread(target=self.srv.serve_forever, daemon=True).start()

    def tearDown(self):
        for pid in self.pids:
            try:
                os.kill(pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        if self.app.running():
            self.app.job.cancel()
            self.app.job.thread.join(10)
        self.srv.shutdown()
        self.srv.server_close()
        self.tmp.cleanup()

    def request(self, method, path, body=None, headers=None):
        data = None if body is None else json.dumps(body).encode()
        h = {"Content-Type": "application/json"} if body is not None else {}
        h.update(headers or {})
        req = urllib.request.Request(f"http://127.0.0.1:{self.port}{path}", data=data, method=method, headers=h)
        try:
            with urllib.request.urlopen(req, timeout=10) as r:
                return r.status, r.headers, r.read()
        except urllib.error.HTTPError as e:
            with e:
                return e.code, e.headers, e.read()

    def call(self, method, path, body=None):
        status, _, data = self.request(method, path, body)
        return status, json.loads(data)

    def raw(self, method, path, headers, body=None, host=True):
        conn = http.client.HTTPConnection("127.0.0.1", self.port, timeout=5)
        try:
            conn.putrequest(method, path, skip_host=not host, skip_accept_encoding=True)
            for k, v in headers.items():
                conn.putheader(k, v)
            conn.endheaders(body)
            r = conn.getresponse()
            r.read()
            return r.status
        finally:
            conn.close()

    def stlNames(self, name="t-bench"):
        return sorted(f.name for f in api.stl_dir(name, self.root).glob("*.stl"))

    def childPid(self):
        job = self.waitJob(lambda j: any(x.startswith("child pid ") for x in j["log_tail"]), timeout=10)
        pid = int(next(x for x in job["log_tail"] if x.startswith("child pid ")).split()[-1])
        self.pids.append(pid)
        return pid

    def waitJob(self, until=lambda job: job["state"] != "running", timeout=30):
        end = time.time() + timeout
        while time.time() < end:
            job = self.call("GET", "/api/job")[1]
            if until(job):
                return job
            time.sleep(0.05)
        self.fail(f"job did not reach the expected state: {job}")


class SafetyTest(ServerCase):
    def testOnlyStaticFilesAreServed(self):
        for path in ("/api.py", "/server.py", "/%2e%2e/README.md", "/..%2fapi.py", "/nope.js", "/api"):
            self.assertEqual(self.request("GET", path)[0], 404, path)

    def testForeignHostIsRejected(self):
        self.assertEqual(self.request("GET", "/api/presets", headers={"Host": "evil.example:80"})[0], 403)

    def testMissingHostIsRejected(self):
        self.assertEqual(self.raw("GET", "/api/presets", {}, host=False), 403)

    def testLocalhostHostIsAccepted(self):
        self.assertEqual(self.raw("GET", "/api/presets", {"Host": f"localhost:{self.port}"}, host=False), 200)

    def testForeignHostPostIsRejected(self):
        headers = {"Host": "evil.example", "Content-Type": "application/json", "Content-Length": "2"}
        self.assertEqual(self.raw("POST", "/api/render", headers, b"{}", host=False), 403)
        self.assertFalse((self.root / "params").exists())

    def testNegativeContentLengthIsRejected(self):
        headers = {"Content-Type": "application/json", "Content-Length": "-1"}
        self.assertEqual(self.raw("POST", "/api/preview", headers, b"{}"), 400)

    def testNonNumericContentLengthIsRejected(self):
        headers = {"Content-Type": "application/json", "Content-Length": "two"}
        self.assertEqual(self.raw("POST", "/api/preview", headers, b"{}"), 400)

    def testPostMustBeJson(self):
        status = self.request("POST", "/api/preview", body=BENCH, headers={"Content-Type": "text/plain"})[0]
        self.assertEqual(status, 415)

    def testOversizedBodyIsRejected(self):
        self.assertEqual(self.request("POST", "/api/preview", body={"name": "x" * 70000})[0], 400)

    def testTraversalInStlAndZipPaths(self):
        for path in ("/api/stl/..%2fparams/H", "/api/stl/t-bench/..%2f..%2fREADME", "/api/zip/..%2fbench-600",
                     "/api/stl/Bad/H", "/api/zip/nope"):
            self.assertEqual(self.request("GET", path)[0], 404, path)


class PreviewApiTest(ServerCase):
    def testPresets(self):
        status, body = self.call("GET", "/api/presets")
        self.assertEqual(status, 200)
        self.assertEqual([p["key"] for p in body["presets"]], ["bambu", "a1mini", "mk4", "prusamini", "ender3"])
        self.assertEqual(body["defaults"]["bed"], [256, 256, 256])

    def testPreview(self):
        status, body = self.call("POST", "/api/preview", BENCH)
        self.assertEqual((status, body["ok"], len(body["parts"])), (200, True, 37))

    def testInvalidPreview(self):
        body = self.call("POST", "/api/preview", dict(BENCH, opening_w=10))[1]
        self.assertEqual((body["ok"], body["errors"]), (False, {"opening_w": "300-3000 mm"}))

    def testIdleJob(self):
        self.assertEqual(self.call("GET", "/api/job"), (200, {"state": "idle"}))

    def testBoxStatus(self):
        status, body = self.call("GET", "/api/box")
        self.assertEqual((status, body["ok"], body["host"]), (200, True, "192.168.68.61"))

    def testOnePingAtATime(self):
        calls, results = [], []

        def ping():
            calls.append(1)
            time.sleep(0.3)
            return True

        self.app.ping = ping
        threads = [threading.Thread(target=lambda: results.append(self.call("GET", "/api/box")[1]["ok"]))
                   for _ in range(3)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(10)
        self.assertEqual((len(calls), results), (1, [True, True, True]))

    def testBatchesOfSix(self):
        self.assertEqual([len(b) for b in server.batches(list(range(14)))], [6, 6, 2])


class RenderTest(ServerCase):
    def testRenderAllThenZip(self):
        status, body = self.call("POST", "/api/render", BENCH)
        self.assertEqual((status, body["job"]["state"], body["job"]["total"]), (200, "running", 37))
        job = self.waitJob()
        self.assertEqual((job["state"], job["done"], job["error"]), ("done", 37, ""))
        self.assertEqual(set(job["parts"].values()), {"ok"})
        self.assertTrue((self.root / "params" / "t-bench.json").exists())
        self.assertTrue((self.root / "bom" / "t-bench.md").exists())
        status, headers, data = self.request("GET", "/api/zip/t-bench")
        self.assertEqual((status, headers["Content-Type"]), (200, "application/zip"))
        self.assertEqual(headers["Content-Disposition"], 'attachment; filename="t-bench-openwindow.zip"')
        names = zipfile.ZipFile(io.BytesIO(data)).namelist()
        self.assertEqual(len([n for n in names if n.startswith("stl/")]), 37)

    def testSelectionRendersInBatchesOfSix(self):
        ids = ["H", "SW", "JL", "JU", "TE", "SH", "SBE", "SV"]
        self.call("POST", "/api/render", dict(BENCH, ids=list(reversed(ids))))
        job = self.waitJob()
        self.assertEqual((job["state"], job["total"], list(job["parts"])), ("done", 8, ids))
        self.assertEqual([x for x in job["log_tail"] if x.startswith("fake render")],
                         ["fake render: 6 parts", "fake render: 2 parts"])

    def testStlEndpoint(self):
        self.call("POST", "/api/render", dict(BENCH, ids=["H"]))
        self.waitJob()
        status, headers, data = self.request("GET", "/api/stl/t-bench/H")
        self.assertEqual((status, headers["Content-Type"], len(data)), (200, "model/stl", 84 + 12 * 50))
        self.assertEqual(self.request("GET", "/api/stl/t-bench/JL")[0], 404)
        self.assertEqual(self.request("GET", "/api/stl/t-bench/ZZ")[0], 404)

    def testUnknownIdIsRejected(self):
        status, body = self.call("POST", "/api/render", dict(BENCH, ids=["ZZ"]))
        self.assertEqual((status, list(body["errors"])), (400, ["ids"]))

    def testInvalidParamsAreRejected(self):
        status, body = self.call("POST", "/api/render", dict(BENCH, opening_w=10))
        self.assertEqual((status, body["errors"]), (400, {"opening_w": "300-3000 mm"}))
        self.assertEqual(self.call("GET", "/api/job")[1], {"state": "idle"})

    def testBadNameIsRejected(self):
        status, body = self.call("POST", "/api/render", dict(BENCH, name="../x"))
        self.assertEqual((status, list(body["errors"])), (400, ["name"]))
        self.assertFalse((self.root / "params").exists())

    def testReferenceWindowIsProtected(self):
        (self.root / "params").mkdir()
        shutil.copy(api.ROOT / "params" / "bench-600.json", self.root / "params")
        status, body = self.call("POST", "/api/render", dict(BENCH, name="bench-600", opening_w=700))
        self.assertEqual(status, 400)
        self.assertIn("reference window", body["errors"]["name"])

    def testCancelWithoutAJob(self):
        self.assertEqual(self.call("POST", "/api/cancel", {})[0], 409)

    def testJobReportsItsParamsAndFinishTime(self):
        self.call("POST", "/api/render", dict(BENCH, ids=["H"]))
        job = self.waitJob()
        self.assertEqual(job["params"], api.validate(BENCH)[0])
        self.assertGreaterEqual(job["finished"], job["started"])

    def testChangedParamsClearOldStls(self):
        self.call("POST", "/api/render", BENCH)
        self.assertEqual(self.waitJob()["state"], "done")
        self.call("POST", "/api/render", dict(BENCH, glazing="twinwall", ids=["H"]))
        self.assertEqual(self.waitJob()["state"], "done")
        self.assertEqual(self.stlNames(), ["H.stl"])
        self.assertEqual(self.request("GET", "/api/zip/t-bench")[0], 409)
        self.assertEqual(self.request("GET", "/api/stl/t-bench/JL")[0], 404)
        status, _, data = self.request("GET", "/api/zip/t-bench?partial=1")
        z = zipfile.ZipFile(io.BytesIO(data))
        self.assertEqual(status, 200)
        self.assertEqual([n for n in z.namelist() if n.startswith("stl/")], ["stl/H_x2.stl"])
        self.assertEqual(json.loads(z.read("params.json"))["glazing"], "twinwall")

    def testUnchangedParamsKeepOtherStls(self):
        self.call("POST", "/api/render", BENCH)
        self.waitJob()
        self.call("POST", "/api/render", dict(BENCH, ids=["H"]))
        self.assertEqual(self.waitJob()["state"], "done")
        self.assertEqual(len(self.stlNames()), 37)
        self.assertEqual(self.request("GET", "/api/zip/t-bench")[0], 200)

    def testConcurrentRendersStartOneJob(self):
        real, order, lock = api.save_params, [], threading.Lock()

        def slow(*args):
            out = real(*args)
            with lock:
                order.append(1)
                wait = 0.3 * len(order)
            time.sleep(wait)
            return out

        barrier, results = threading.Barrier(2), {}

        def post(width):
            barrier.wait()
            results[width] = self.call("POST", "/api/render", dict(BENCH, opening_w=width))[0]

        with mock.patch.object(api, "save_params", side_effect=slow):
            threads = [threading.Thread(target=post, args=(w,)) for w in (600, 700)]
            for t in threads:
                t.start()
            for t in threads:
                t.join(10)
        self.assertEqual(sorted(results.values()), [200, 409])
        winner = next(w for w, status in results.items() if status == 200)
        self.waitJob()
        self.assertEqual(self.call("GET", "/api/job")[1]["params"]["opening_w"], winner)
        self.assertEqual(json.loads((self.root / "params" / "t-bench.json").read_text())["opening_w"], winner)

    def testVanishedZipFileIsAConflict(self):
        with mock.patch.object(api, "build_zip", side_effect=FileNotFoundError("H.stl")):
            self.assertEqual(self.request("GET", "/api/zip/t-bench")[0], 409)

    def testVanishedStlIsNotFound(self):
        self.call("POST", "/api/render", dict(BENCH, ids=["H"]))
        self.waitJob()
        real = pathlib.Path.read_bytes

        def read(path):
            if path.suffix == ".stl":
                raise FileNotFoundError(path)
            return real(path)

        with mock.patch.object(pathlib.Path, "read_bytes", autospec=True, side_effect=read):
            self.assertEqual(self.request("GET", "/api/stl/t-bench/H")[0], 404)


class SlowRenderTest(ServerCase):
    fake = ["--delay", "0.3"]

    def testBusyServerRefusesASecondJob(self):
        self.call("POST", "/api/render", BENCH)
        self.assertEqual(self.call("POST", "/api/render", BENCH)[0], 409)

    def testZipWhileRenderingIsRefused(self):
        self.call("POST", "/api/render", BENCH)
        self.assertEqual(self.request("GET", "/api/zip/t-bench")[0], 409)

    def testStlWhileRenderingIsRefused(self):
        self.call("POST", "/api/render", BENCH)
        self.assertEqual(self.request("GET", "/api/stl/t-bench/H")[0], 409)

    def testRunningJobHasNoFinishTime(self):
        self.call("POST", "/api/render", BENCH)
        self.assertIsNone(self.call("GET", "/api/job")[1]["finished"])

    def testProgressNamesTheCurrentBatch(self):
        self.call("POST", "/api/render", BENCH)
        job = self.waitJob(lambda j: j["done"] >= 6)
        self.assertLessEqual(len(job["current"]), 6)
        self.assertEqual(job["total"], 37)

    def testCancelKillsTheRunningBatch(self):
        self.call("POST", "/api/render", BENCH)
        self.waitJob(lambda j: j["current"])
        started = time.time()
        status, body = self.call("POST", "/api/cancel", {})
        self.assertEqual(status, 200)
        job = self.waitJob()
        self.assertLess(time.time() - started, 3)
        self.assertEqual(job["state"], "cancelled")
        self.assertIn("cancelled", job["parts"].values())
        self.assertIsNotNone(self.app.job.proc.poll())


class FailingRenderTest(ServerCase):
    fake = ["--fail", "H,JL"]

    def testFailedPartsAndPartialZip(self):
        self.call("POST", "/api/render", BENCH)
        job = self.waitJob()
        self.assertEqual((job["state"], job["error"]), ("failed", "2 part(s) failed: H, JL"))
        self.assertEqual((job["parts"]["H"], job["parts"]["SW"]), ("failed", "ok"))
        self.assertEqual(job["errors"]["H"], ["H: missing H.stl"])
        self.assertTrue((self.root / "bom" / "t-bench.md").exists())
        self.assertEqual(self.request("GET", "/api/zip/t-bench")[0], 409)
        status, _, data = self.request("GET", "/api/zip/t-bench?partial=1")
        z = zipfile.ZipFile(io.BytesIO(data))
        self.assertEqual(status, 200)
        self.assertNotIn("stl/H_x2.stl", z.namelist())
        self.assertTrue(z.read("README.txt").decode().startswith("PARTIAL ZIP"))


class ReferenceRenderTest(ServerCase):
    fake = ["--delay", "0.3"]

    def testCancelKeepsTheReferenceStls(self):
        before = seedReference(self.root)
        self.assertEqual(self.call("POST", "/api/render", REF)[0], 200)
        first = set(self.waitJob(lambda j: j["current"])["current"])
        self.call("POST", "/api/cancel", {})
        self.assertEqual(self.waitJob()["state"], "cancelled")
        after = {f.name: f.read_bytes() for f in api.stl_dir("bench-600", self.root).glob("*.stl")}
        self.assertEqual(sorted(after), sorted(before))
        untouched = lambda files: {n: b for n, b in files.items() if n[:-4] not in first}
        self.assertEqual(untouched(after), untouched(before))
        lay, plist = api.load("bench-600", self.root)[1:]
        self.assertEqual([pid for pid, e in api.part_status("bench-600", lay, plist, self.root).items() if e], [])


class FailingReferenceTest(ServerCase):
    fake = ["--fail", "H,JL"]

    def testFailedPartKeepsItsOldStlButIsNotOk(self):
        before = seedReference(self.root)
        self.call("POST", "/api/render", REF)
        job = self.waitJob()
        self.assertEqual((job["state"], job["parts"]["H"], job["parts"]["SW"]), ("failed", "failed", "ok"))
        self.assertEqual(job["errors"]["H"], ["H: box.sh did not write a new H.stl"])
        self.assertEqual((self.root / "cad" / "stl" / "bench-600" / "H.stl").read_bytes(), before["H.stl"])
        self.assertEqual(self.stlNames("bench-600"), sorted(before))


class UnreachableReferenceTest(ServerCase):
    fake = ["--exit", "255"]

    def testUnreachableBoxKeepsTheReferenceStls(self):
        before = seedReference(self.root)
        self.call("POST", "/api/render", REF)
        self.assertEqual(self.waitJob()["error"], UNREACHABLE)
        after = {f.name: f.read_bytes() for f in api.stl_dir("bench-600", self.root).glob("*.stl")}
        self.assertEqual(after, before)


class DroppedConnectionTest(ServerCase):
    fake = ["--drop", IDS[8]]

    def testExitOneWithConnectionTextIsUnreachable(self):
        self.call("POST", "/api/render", BENCH)
        job = self.waitJob()
        self.assertEqual((job["state"], job["error"]), ("failed", UNREACHABLE))
        self.assertEqual({job["parts"][i] for i in IDS[:6]}, {"ok"})
        self.assertEqual({job["parts"][i] for i in IDS[6:12]}, {"failed"})
        self.assertEqual({job["parts"][i] for i in IDS[12:]}, {"skipped"})
        self.assertEqual(job["errors"][IDS[6]], [UNREACHABLE])
        self.assertIn("box.sh: ssh connection failed (exit 255)", job["log_tail"])
        self.assertFalse((self.root / "bom").exists())


class GarbageOutputTest(ServerCase):
    fake = ["--garbage"]

    def testInvalidUtf8IsReplaced(self):
        self.call("POST", "/api/render", dict(BENCH, ids=["H"]))
        job = self.waitJob()
        self.assertEqual((job["state"], job["parts"]), ("done", {"H": "ok"}))
        self.assertTrue([x for x in job["log_tail"] if x.startswith("garbage: ") and "\ufffd" in x])


class ReadErrorTest(ServerCase):
    fake = ["--delay", "0.5"]

    def testErrorWhileReadingStopsTheBatch(self):
        with mock.patch.object(server.Job, "note", side_effect=RuntimeError("boom")):
            self.call("POST", "/api/render", dict(BENCH, ids=["H", "SW"]))
            job = self.waitJob()
        self.assertEqual((job["state"], job["error"]), ("failed", "RuntimeError: boom"))
        self.assertIsNotNone(self.app.job.proc.poll())
        self.assertEqual(job["parts"], {"H": "skipped", "SW": "skipped"})


class ChildProcessTest(ServerCase):
    fake = ["--child"]

    def testCancelReachesTheChild(self):
        self.call("POST", "/api/render", dict(BENCH, ids=["H"]))
        pid = self.childPid()
        self.assertEqual(self.call("POST", "/api/cancel", {})[0], 200)
        self.assertEqual(self.waitJob(timeout=5)["state"], "cancelled")
        self.assertTrue(gone(pid))


class StubbornChildTest(ServerCase):
    fake = ["--child", "--child-ignores-term"]
    kill_after = 0.5

    def testSigkillReachesTheGroupAfterTheLeaderExits(self):
        self.call("POST", "/api/render", dict(BENCH, ids=["H"]))
        pid = self.childPid()
        self.call("POST", "/api/cancel", {})
        self.assertEqual(self.waitJob(timeout=5)["state"], "cancelled")
        self.assertEqual(self.app.job.proc.returncode, -signal.SIGTERM)
        self.assertTrue(gone(pid))


class StubbornLeaderTest(ServerCase):
    fake = ["--ignore-term", "--delay", "0.3"]
    kill_after = 0.5

    def testSigkillFallback(self):
        self.call("POST", "/api/render", BENCH)
        self.waitJob(lambda j: any(x.startswith("fake render") for x in j["log_tail"]))
        self.call("POST", "/api/cancel", {})
        timers = [t for t in threading.enumerate() if isinstance(t, threading.Timer)]
        self.assertTrue(timers)
        self.assertTrue(all(t.daemon for t in timers))
        self.assertEqual(self.waitJob(timeout=5)["state"], "cancelled")
        self.assertEqual(self.app.job.proc.returncode, -signal.SIGKILL)


class SignalTest(unittest.TestCase):
    def stopWith(self, sig):
        proc = subprocess.Popen([sys.executable, str(WEB / "server.py"), "--port", "0", "--fake-render"],
                                stdout=subprocess.PIPE, text=True)
        root = None
        try:
            m = re.search(r"http://127\.0\.0\.1:(\d+)/ \(data in (.+); Ctrl-C", proc.stdout.readline())
            port, root = int(m[1]), pathlib.Path(m[2])
            req = urllib.request.Request(f"http://127.0.0.1:{port}/api/render", data=json.dumps(BENCH).encode(),
                                         method="POST", headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=10) as r:
                self.assertEqual(r.status, 200)
            fakes = lambda: subprocess.run(["pgrep", "-f", f"fake_box.py --root {root}"], capture_output=True,
                                           text=True).stdout.split()
            end = time.time() + 5
            while not fakes() and time.time() < end:
                time.sleep(0.05)
            self.assertTrue(fakes())
            proc.send_signal(sig)
            self.assertEqual(proc.wait(15), 0)
            self.assertFalse(root.exists())
            end = time.time() + 3
            while fakes() and time.time() < end:
                time.sleep(0.05)
            self.assertEqual(fakes(), [])
        finally:
            if proc.poll() is None:
                proc.kill()
                proc.wait()
            proc.stdout.close()
            if root is not None:
                subprocess.run(["pkill", "-9", "-f", f"fake_box.py --root {root}"])
                shutil.rmtree(root, ignore_errors=True)

    def testSigtermCancelsTheJobAndCleansUp(self):
        self.stopWith(signal.SIGTERM)

    def testSighupCancelsTheJobAndCleansUp(self):
        self.stopWith(signal.SIGHUP)


class UnreachableBoxTest(ServerCase):
    fake = ["--exit", "255"]

    def testJobFailsWithTheBoxMessage(self):
        self.call("POST", "/api/render", BENCH)
        job = self.waitJob()
        self.assertEqual((job["state"], job["error"]), ("failed", UNREACHABLE))
        self.assertIn("ssh: connect to host 192.168.68.61 port 22: Operation timed out", job["log_tail"])
        self.assertEqual(job["parts"]["H"], "failed")
        self.assertEqual(job["parts"]["AC"], "skipped")
        self.assertFalse((self.root / "bom").exists())

    def testBoxStatusIsDown(self):
        self.assertEqual(self.call("GET", "/api/box")[1]["ok"], False)

    def testPreviewStillWorks(self):
        self.assertTrue(self.call("POST", "/api/preview", BENCH)[1]["ok"])


class ViewerScriptTest(ServerCase):
    def testViewerScriptIsServed(self):
        status, headers, body = self.request("GET", "/viewer.js")
        self.assertEqual((status, headers["Content-Type"]), (200, "text/javascript; charset=utf-8"))
        self.assertIn(b"export class Viewer", body)
        self.assertIn(b"export function parseStl", body)


class PageTest(ServerCase):
    def testPageStyleAndScriptAreServed(self):
        status, headers, body = self.request("GET", "/")
        self.assertEqual((status, headers["Content-Type"]), (200, "text/html; charset=utf-8"))
        self.assertIn(b'<script type="module" src="app.js"></script>', body)
        self.assertEqual(self.request("GET", "/style.css")[1]["Content-Type"], "text/css; charset=utf-8")
        status, headers, body = self.request("GET", "/app.js")
        self.assertEqual((status, headers["Content-Type"]), (200, "text/javascript; charset=utf-8"))
        self.assertIn(b'import { Viewer } from "./viewer.js";', body)


class GuideTest(ServerCase):
    def testGuidePdfIsServedInline(self):
        status, headers, body = self.request("GET", "/guide.pdf")
        self.assertEqual((status, headers["Content-Type"]), (200, "application/pdf"))
        self.assertIn('inline; filename="OpenWindow-Guide.pdf"', headers["Content-Disposition"])
        self.assertTrue(body.startswith(b"%PDF-"))

    def testGuideLinkIsOnThePage(self):
        self.assertIn(b'href="/guide.pdf"', self.request("GET", "/")[2])


class BaysApiTest(ServerCase):
    def testPresetsCarryThePageMaxPane(self):
        self.assertEqual(self.call("GET", "/api/presets")[1]["max_pane"], [1200, 900])

    def testPreviewWithAMaxPane(self):
        status, body = self.call("POST", "/api/preview", dict(BENCH, opening_w=1800, opening_h=1500, awning_h=450,
                                                              max_pane=[1200, 900]))
        self.assertEqual((status, body["ok"], body["layout"]["bays"]), (200, True, 2))

    def testRenderRefusesTooFewBays(self):
        status, body = self.call("POST", "/api/render", dict(BENCH, opening_w=1800, opening_h=1500, awning_h=450,
                                                             max_pane=[1200, 900], bays=1))
        self.assertEqual((status, list(body["errors"])), (400, ["bays"]))


if __name__ == "__main__":
    unittest.main()
