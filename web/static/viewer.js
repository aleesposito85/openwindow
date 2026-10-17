// Minimal WebGL STL viewer: binary/ASCII STL, orbit and zoom, one directional light, instanced assembly.
const VS = `
attribute vec3 position;
attribute vec3 normal;
uniform mat4 projView;
uniform mat4 model;
uniform mat3 normalMat;
varying vec3 vNormal;
void main() {
  vNormal = normalMat * normal;
  gl_Position = projView * model * vec4(position, 1.0);
}`;
const FS = `
precision mediump float;
uniform vec3 color;
uniform vec3 light;
varying vec3 vNormal;
void main() {
  float d = abs(dot(normalize(vNormal), light));
  gl_FragColor = vec4(color * (0.35 + 0.65 * d), 1.0);
}`;
const IDENTITY = [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1];
const PART_COLOUR = [0.78, 0.8, 0.83];
const GROUPS = [
  [["T", "TE", "TSL", "TSR", "TX", "MSL", "MST", "MSH", "ML", "MU"], [0.62, 0.66, 0.72]],
  [["SH", "SB", "SBE", "SV", "CS"], [0.72, 0.79, 0.86]],
];
const FOV = 0.7;
const NO_WEBGL = "WebGL is not available in this browser";

export function parseStl(buffer) {
  const view = new DataView(buffer);
  if (buffer.byteLength >= 84) {
    const n = view.getUint32(80, true);
    if (84 + 50 * n === buffer.byteLength) {
      const pos = new Float32Array(n * 9);
      for (let i = 0; i < n; i++) {
        for (let k = 0; k < 9; k++) pos[i * 9 + k] = view.getFloat32(84 + 50 * i + 12 + 4 * k, true);
      }
      return pos;
    }
  }
  const text = new TextDecoder().decode(buffer);
  const nums = [];
  const re = /vertex\s+(\S+)\s+(\S+)\s+(\S+)/g;
  let m;
  while ((m = re.exec(text))) nums.push(Number(m[1]), Number(m[2]), Number(m[3]));
  if (!nums.length || nums.length % 9) throw new Error("not an STL file");
  return new Float32Array(nums);
}

function faceNormals(pos) {
  const out = new Float32Array(pos.length);
  for (let i = 0; i < pos.length; i += 9) {
    const ux = pos[i + 3] - pos[i], uy = pos[i + 4] - pos[i + 1], uz = pos[i + 5] - pos[i + 2];
    const vx = pos[i + 6] - pos[i], vy = pos[i + 7] - pos[i + 1], vz = pos[i + 8] - pos[i + 2];
    let nx = uy * vz - uz * vy, ny = uz * vx - ux * vz, nz = ux * vy - uy * vx;
    const len = Math.hypot(nx, ny, nz) || 1;
    nx /= len; ny /= len; nz /= len;
    for (let k = 0; k < 9; k += 3) { out[i + k] = nx; out[i + k + 1] = ny; out[i + k + 2] = nz; }
  }
  return out;
}

function bounds(pos) {
  const min = [Infinity, Infinity, Infinity], max = [-Infinity, -Infinity, -Infinity];
  for (let i = 0; i < pos.length; i += 3) {
    for (let a = 0; a < 3; a++) {
      min[a] = Math.min(min[a], pos[i + a]);
      max[a] = Math.max(max[a], pos[i + a]);
    }
  }
  return { min, max };
}

function multiply(a, b) {
  const out = new Array(16).fill(0);
  for (let c = 0; c < 4; c++) for (let r = 0; r < 4; r++) for (let k = 0; k < 4; k++) out[c * 4 + r] += a[k * 4 + r] * b[c * 4 + k];
  return out;
}

function perspective(fovy, aspect, near, far) {
  const f = 1 / Math.tan(fovy / 2), nf = 1 / (near - far);
  return [f / aspect, 0, 0, 0, 0, f, 0, 0, 0, 0, (far + near) * nf, -1, 0, 0, 2 * far * near * nf, 0];
}

function normalize(v) {
  const len = Math.hypot(...v) || 1;
  return v.map((x) => x / len);
}

function cross(a, b) {
  return [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]];
}

function lookAt(eye, center, up) {
  const z = normalize(eye.map((v, i) => v - center[i]));
  const x = normalize(cross(up, z));
  const y = cross(z, x);
  const dot = (a, b) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
  return [x[0], y[0], z[0], 0, x[1], y[1], z[1], 0, x[2], y[2], z[2], 0, -dot(x, eye), -dot(y, eye), -dot(z, eye), 1];
}

function fromRows(m) {
  return [0, 1, 2, 3].flatMap((c) => [m[c], m[4 + c], m[8 + c], m[12 + c]]);
}

function apply(m, p) {
  return [0, 1, 2].map((r) => m[r] * p[0] + m[4 + r] * p[1] + m[8 + r] * p[2] + m[12 + r]);
}

function colourFor(id) {
  const group = GROUPS.find(([ids]) => ids.includes(id));
  return group ? group[1] : [0.86, 0.85, 0.82];
}

export class Viewer {
  constructor(canvas) {
    this.canvas = canvas;
    this.gl = canvas.getContext("webgl", { antialias: true, preserveDrawingBuffer: true });
    this.meshes = new Map();
    this.gen = 0;
    this.req = 0;
    this.items = [];
    this.yaw = -0.6;
    this.pitch = 0.45;
    this.dist = 1;
    this.center = [0, 0, 0];
    if (!this.gl) return;
    const gl = this.gl;
    const shader = (type, src) => {
      const s = gl.createShader(type);
      gl.shaderSource(s, src);
      gl.compileShader(s);
      if (!gl.getShaderParameter(s, gl.COMPILE_STATUS)) throw new Error(gl.getShaderInfoLog(s));
      return s;
    };
    this.prog = gl.createProgram();
    gl.attachShader(this.prog, shader(gl.VERTEX_SHADER, VS));
    gl.attachShader(this.prog, shader(gl.FRAGMENT_SHADER, FS));
    gl.linkProgram(this.prog);
    this.loc = {};
    for (const n of ["position", "normal"]) this.loc[n] = gl.getAttribLocation(this.prog, n);
    for (const n of ["projView", "model", "normalMat", "color", "light"]) this.loc[n] = gl.getUniformLocation(this.prog, n);
    let drag = null;
    canvas.addEventListener("mousedown", (e) => { drag = [e.clientX, e.clientY]; });
    window.addEventListener("mouseup", () => { drag = null; });
    window.addEventListener("mousemove", (e) => {
      if (!drag) return;
      this.yaw += (e.clientX - drag[0]) * 0.01;
      this.pitch = Math.max(-1.5, Math.min(1.5, this.pitch + (e.clientY - drag[1]) * 0.01));
      drag = [e.clientX, e.clientY];
      this.draw();
    });
    canvas.addEventListener("wheel", (e) => {
      e.preventDefault();
      this.dist *= Math.exp(e.deltaY * 0.001);
      this.draw();
    }, { passive: false });
    new ResizeObserver(() => this.draw()).observe(canvas);
  }

  load(url) {
    if (!this.gl) return Promise.reject(new Error(NO_WEBGL));
    let entry = this.meshes.get(url);
    if (!entry) {
      entry = this.fetchMesh(url, this.gen);
      this.meshes.set(url, entry);
      entry.catch(() => { if (this.meshes.get(url) === entry) this.meshes.delete(url); });
    }
    return entry;
  }

  async fetchMesh(url, gen) {
    let r;
    try {
      r = await fetch(url);
    } catch (e) {
      throw new Error("server not reachable");
    }
    if (!r.ok) {
      const body = await r.json().catch(() => ({}));
      throw Object.assign(new Error(body.error || `HTTP ${r.status}`), { status: r.status });
    }
    const pos = parseStl(await r.arrayBuffer());
    if (!pos.length) throw new Error("empty STL file");
    if (gen !== this.gen) throw new Error("superseded by a newer render");
    const gl = this.gl;
    const buf = (data) => {
      const b = gl.createBuffer();
      gl.bindBuffer(gl.ARRAY_BUFFER, b);
      gl.bufferData(gl.ARRAY_BUFFER, data, gl.STATIC_DRAW);
      return b;
    };
    return { pos: buf(pos), nrm: buf(faceNormals(pos)), count: pos.length / 3, box: bounds(pos) };
  }

  invalidate() {
    this.gen++;
    this.req++;
    for (const entry of this.meshes.values()) {
      entry.then((mesh) => { this.gl.deleteBuffer(mesh.pos); this.gl.deleteBuffer(mesh.nrm); }, () => {});
    }
    this.meshes.clear();
    this.items = [];
    this.draw();
  }

  async showPart(url) {
    const req = ++this.req;
    const mesh = await this.load(url);
    if (req !== this.req) return false;
    this.items = [{ mesh, model: IDENTITY, color: PART_COLOUR }];
    this.yaw = -0.6;
    this.pitch = 0.45;
    this.frame();
    return true;
  }

  async showAssembly(urlFor, instances) {
    const req = ++this.req;
    if (!this.gl) throw new Error(NO_WEBGL);
    const ids = [...new Set(instances.map((x) => x.id))];
    const loaded = await Promise.allSettled(ids.map((id) => this.load(urlFor(id))));
    if (req !== this.req) return null;
    const meshes = new Map();
    const failed = [];
    ids.forEach((id, i) => {
      if (loaded[i].status === "fulfilled") meshes.set(id, loaded[i].value);
      else failed.push([id, loaded[i].reason]);
    });
    this.items = instances.filter((x) => meshes.has(x.id))
      .map((x) => ({ mesh: meshes.get(x.id), model: fromRows(x.m), color: colourFor(x.id) }));
    this.yaw = 0.35;
    this.pitch = 0.3;
    this.frame();
    return failed;
  }

  clear() {
    this.req++;
    this.items = [];
    this.draw();
  }

  frame() {
    const min = [Infinity, Infinity, Infinity], max = [-Infinity, -Infinity, -Infinity];
    for (const { mesh, model } of this.items) {
      const { min: a, max: b } = mesh.box;
      for (let i = 0; i < 8; i++) {
        const p = apply(model, [i & 1 ? b[0] : a[0], i & 2 ? b[1] : a[1], i & 4 ? b[2] : a[2]]);
        for (let k = 0; k < 3; k++) { min[k] = Math.min(min[k], p[k]); max[k] = Math.max(max[k], p[k]); }
      }
    }
    if (!this.items.length) return this.draw();
    this.center = min.map((v, k) => (v + max[k]) / 2);
    const radius = Math.hypot(...max.map((v, k) => v - min[k])) / 2;
    this.dist = (radius / Math.sin(FOV / 2)) * 1.05;
    this.draw();
  }

  draw() {
    const gl = this.gl;
    if (!gl) return;
    const dpr = window.devicePixelRatio || 1;
    const w = Math.round(this.canvas.clientWidth * dpr), h = Math.round(this.canvas.clientHeight * dpr);
    if (!w || !h) return;
    if (this.canvas.width !== w || this.canvas.height !== h) { this.canvas.width = w; this.canvas.height = h; }
    gl.viewport(0, 0, w, h);
    gl.clearColor(0.914, 0.929, 0.941, 1);
    gl.enable(gl.DEPTH_TEST);
    gl.clear(gl.COLOR_BUFFER_BIT | gl.DEPTH_BUFFER_BIT);
    if (!this.items.length) return;
    const cp = Math.cos(this.pitch);
    const dir = [cp * Math.sin(this.yaw), -cp * Math.cos(this.yaw), Math.sin(this.pitch)];
    const eye = this.center.map((v, k) => v + this.dist * dir[k]);
    const projView = multiply(perspective(FOV, w / h, this.dist / 100, this.dist * 10), lookAt(eye, this.center, [0, 0, 1]));
    gl.useProgram(this.prog);
    gl.uniformMatrix4fv(this.loc.projView, false, projView);
    gl.uniform3fv(this.loc.light, normalize([dir[0] - 0.3 * dir[1], dir[1] + 0.3 * dir[0], dir[2] + 0.5]));
    gl.enableVertexAttribArray(this.loc.position);
    gl.enableVertexAttribArray(this.loc.normal);
    for (const { mesh, model, color } of this.items) {
      gl.uniformMatrix4fv(this.loc.model, false, model);
      gl.uniformMatrix3fv(this.loc.normalMat, false, [model[0], model[1], model[2], model[4], model[5], model[6], model[8], model[9], model[10]]);
      gl.uniform3fv(this.loc.color, color);
      gl.bindBuffer(gl.ARRAY_BUFFER, mesh.pos);
      gl.vertexAttribPointer(this.loc.position, 3, gl.FLOAT, false, 0, 0);
      gl.bindBuffer(gl.ARRAY_BUFFER, mesh.nrm);
      gl.vertexAttribPointer(this.loc.normal, 3, gl.FLOAT, false, 0, 0);
      gl.drawArrays(gl.TRIANGLES, 0, mesh.count);
    }
  }
}
