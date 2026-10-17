// Node checks for web/static/viewer.js: mesh cache, invalidation, superseded views and failure reasons.
import assert from "node:assert/strict";
import { pathToFileURL } from "node:url";

globalThis.window = { addEventListener() {}, devicePixelRatio: 1 };
globalThis.ResizeObserver = class { observe() {} };
const source = process.argv[2] || new URL("../static/viewer.js", import.meta.url).pathname;
const { Viewer } = await import(pathToFileURL(source).href);

function fakeGl() {
  const gl = { live: new Set(), next: 0, deleted: 0 };
  for (const k of ["VERTEX_SHADER", "FRAGMENT_SHADER", "COMPILE_STATUS", "ARRAY_BUFFER", "STATIC_DRAW", "DEPTH_TEST",
                   "COLOR_BUFFER_BIT", "DEPTH_BUFFER_BIT", "TRIANGLES", "FLOAT"]) gl[k] = k;
  const noop = () => {};
  Object.assign(gl, {
    createShader: () => ({}), shaderSource: noop, compileShader: noop, getShaderParameter: () => true,
    createProgram: () => ({}), attachShader: noop, linkProgram: noop, getAttribLocation: () => 0,
    getUniformLocation: () => ({}), bindBuffer: noop, bufferData: noop, viewport: noop, clearColor: noop,
    enable: noop, clear: noop, useProgram: noop, uniformMatrix4fv: noop, uniformMatrix3fv: noop, uniform3fv: noop,
    enableVertexAttribArray: noop, vertexAttribPointer: noop, drawArrays: noop,
    createBuffer() { const b = { id: ++gl.next }; gl.live.add(b); return b; },
    deleteBuffer(b) { gl.live.delete(b); gl.deleted++; },
  });
  return gl;
}

function canvas(gl) {
  return { getContext: () => gl, addEventListener() {}, clientWidth: 100, clientHeight: 100, width: 0, height: 0 };
}

function cube(size) {
  const v = [[0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 1, 0], [0, 0, 1], [1, 0, 1], [1, 1, 1], [0, 1, 1]];
  const f = [[0, 2, 1], [0, 3, 2], [4, 5, 6], [4, 6, 7], [0, 1, 5], [0, 5, 4], [1, 2, 6], [1, 6, 5], [2, 3, 7],
             [2, 7, 6], [3, 0, 4], [3, 4, 7]];
  const buf = new ArrayBuffer(84 + 50 * f.length);
  const view = new DataView(buf);
  view.setUint32(80, f.length, true);
  f.forEach((tri, i) => tri.forEach((p, k) => v[p].forEach((c, a) => {
    view.setFloat32(84 + 50 * i + 12 + 12 * k + 4 * a, c * size, true);
  })));
  return buf;
}

const routes = new Map();
const calls = [];
globalThis.fetch = (url) => {
  calls.push(url);
  const route = routes.get(url);
  if (!route) return Promise.reject(new TypeError("Failed to fetch"));
  return route();
};

function stl(size) {
  return () => Promise.resolve({ ok: true, status: 200, arrayBuffer: async () => cube(size) });
}

function fail(status, error) {
  return () => Promise.resolve({ ok: false, status, json: async () => ({ error }) });
}

function gate(size) {
  let open;
  const opened = new Promise((resolve) => { open = resolve; });
  return { route: () => opened.then(() => stl(size)()), open: () => open() };
}

const checks = [];
const check = (name, fn) => checks.push([name, fn]);

check("concurrent loads of one URL fetch it once", async () => {
  const v = new Viewer(canvas(fakeGl()));
  routes.set("/a", stl(10));
  calls.length = 0;
  const [m1, m2] = await Promise.all([v.load("/a"), v.load("/a")]);
  assert.equal(calls.length, 1);
  assert.equal(m1, m2);
});

check("invalidate deletes the cached buffers and the next load fetches again", async () => {
  const gl = fakeGl();
  const v = new Viewer(canvas(gl));
  routes.set("/a", stl(10));
  await v.showPart("/a");
  assert.equal(gl.live.size, 2);
  v.invalidate();
  await new Promise((resolve) => setTimeout(resolve, 0));
  assert.equal(gl.live.size, 0);
  assert.equal(v.items.length, 0);
  routes.set("/a", stl(20));
  calls.length = 0;
  await v.showPart("/a");
  assert.equal(calls.length, 1);
  assert.equal(v.items[0].mesh.box.max[0], 20);
});

check("a load in flight during invalidate leaves no buffers behind", async () => {
  const gl = fakeGl();
  const v = new Viewer(canvas(gl));
  const g = gate(10);
  routes.set("/slow", g.route);
  const pending = v.showPart("/slow");
  v.invalidate();
  g.open();
  await assert.rejects(pending);
  assert.equal(gl.live.size, 0);
});

check("a superseded showPart does not replace the newer view", async () => {
  const v = new Viewer(canvas(fakeGl()));
  const g = gate(10);
  routes.set("/slow", g.route);
  routes.set("/fast", stl(30));
  const first = v.showPart("/slow");
  assert.equal(await v.showPart("/fast"), true);
  g.open();
  assert.equal(await first, false);
  assert.equal(v.items[0].mesh.box.max[0], 30);
});

check("a superseded assembly returns null and keeps the newer view", async () => {
  const v = new Viewer(canvas(fakeGl()));
  const g = gate(10);
  routes.set("/slow", g.route);
  routes.set("/fast", stl(30));
  const first = v.showAssembly(() => "/slow", [{ id: "H", m: [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1] }]);
  await v.showPart("/fast");
  g.open();
  assert.equal(await first, null);
  assert.equal(v.items[0].mesh.box.max[0], 30);
});

check("HTTP errors carry the status and the server's message", async () => {
  const v = new Viewer(canvas(fakeGl()));
  routes.set("/missing", fail(404, "not rendered"));
  await assert.rejects(v.showPart("/missing"), (e) => e.status === 404 && e.message === "not rendered");
  routes.set("/busy", fail(409, "a render job for this window is still running"));
  await assert.rejects(v.load("/busy"), (e) => e.status === 409 && /still running/.test(e.message));
});

check("a failed load is not cached", async () => {
  const v = new Viewer(canvas(fakeGl()));
  routes.set("/later", fail(404, "not rendered"));
  await assert.rejects(v.load("/later"));
  routes.set("/later", stl(10));
  assert.equal((await v.load("/later")).count, 36);
});

check("an unparsable file is reported as such", async () => {
  const v = new Viewer(canvas(fakeGl()));
  routes.set("/junk", () => Promise.resolve({ ok: true, status: 200, arrayBuffer: async () => new ArrayBuffer(10) }));
  await assert.rejects(v.showPart("/junk"), /not an STL file/);
});

check("a network failure says the server is not reachable", async () => {
  const v = new Viewer(canvas(fakeGl()));
  await assert.rejects(v.load("/nowhere"), /server not reachable/);
});

check("assembly failures come back with their reasons", async () => {
  const v = new Viewer(canvas(fakeGl()));
  routes.set("/H", stl(10));
  routes.set("/T", fail(404, "not rendered"));
  const m = [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1];
  const failed = await v.showAssembly((id) => `/${id}`, [{ id: "H", m }, { id: "T", m }]);
  assert.deepEqual(failed.map(([id, e]) => [id, e.status, e.message]), [["T", 404, "not rendered"]]);
  assert.equal(v.items.length, 1);
});

check("without WebGL every view fails with that reason", async () => {
  const v = new Viewer(canvas(null));
  routes.set("/a", stl(10));
  await assert.rejects(v.showPart("/a"), /WebGL is not available/);
  await assert.rejects(v.showAssembly(() => "/a", []), /WebGL is not available/);
});

let failures = 0;
for (const [name, fn] of checks) {
  try {
    await fn();
    console.log(`ok    ${name}`);
  } catch (e) {
    failures++;
    console.log(`FAIL  ${name}: ${e.message}`);
  }
}
console.log(`${checks.length - failures}/${checks.length} viewer checks passed`);
process.exit(failures ? 1 : 0);
