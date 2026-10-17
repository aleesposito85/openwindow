// OpenWindow configurator page: form, live preview, render jobs, downloads.
import { Viewer } from "./viewer.js";

const $ = (sel) => document.querySelector(sel);
const form = $("#form");
const SVG = "http://www.w3.org/2000/svg";
const CHECKS = { transom_deflection: "Transom deflection", sash_weight: "Friction stay", segment_length: "Segment length",
                 cam_keeper: "Cam / keeper", pane_fit: "Pane fit", mullion_deflection: "Mullion deflection", core: "Tube cores",
                 bed_fit: "Bed fit" };
const FIELDS = ["name", "opening_w", "opening_h", "fix_gap", "awning_h", "glazing", "tier"];
const SANDWICH = { t: 4, gap: 16 };
const VSLOT_STOCK = 1000;
const state = { presets: [], maxPane: [1200, 900], preview: null, job: null, jobRev: null, selected: new Set(), seq: 0,
                timer: 0, poll: 0, pollFailures: 0, online: true, viewing: null, view: null, viewSeq: 0 };
const viewer = new Viewer($("#viewer"));
const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
const backoff = (failures) => Math.min(30000, 1000 * 2 ** failures);

async function request(path, options) {
  let r;
  try {
    r = await fetch(path, options);
  } catch (e) {
    setOnline(false, "Server not reachable: is web/server.py still running?");
    throw new Error("server not reachable");
  }
  let body;
  try {
    body = await r.json();
  } catch (e) {
    setOnline(false, `Unexpected reply from the server (HTTP ${r.status} for ${path}).`);
    throw new Error(`unexpected reply from the server (HTTP ${r.status})`);
  }
  setOnline(true);
  return { status: r.status, body };
}

async function getJson(path) {
  return (await request(path)).body;
}

function postJson(path, body) {
  return request(path, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
}

function setOnline(ok, why) {
  const recovered = ok && !state.online;
  const lost = !ok && state.online;
  state.online = ok;
  const banner = $("#offline");
  banner.hidden = ok;
  if (!ok) banner.textContent = `${why} Retrying in the background.`;
  if (lost && state.presets.length) schedulePoll(backoff(state.pollFailures + 1));
  if (recovered && state.presets.length) {
    schedulePreview();
    pollJob();
    pollBox();
  }
}

function num(name) {
  const v = form.elements[name].value.trim();
  return v === "" ? null : Number(v);
}

function readForm() {
  const preset = state.presets.find((p) => p.key === form.elements.preset.value);
  const out = {
    name: form.elements.name.value.trim(),
    opening_w: num("opening_w"), opening_h: num("opening_h"), fix_gap: num("fix_gap"), awning_h: num("awning_h"),
    glazing: form.elements.glazing.value, tier: Number(form.elements.tier.value), screen: form.elements.screen.checked,
    bed: preset ? preset.bed : [num("bed_x"), num("bed_y"), num("bed_z")],
  };
  if (!form.elements.max_none.checked) out.max_pane = [num("max_a"), num("max_b")];
  if (num("bays") !== null) out.bays = num("bays");
  if (out.glazing === "acrylic") {
    const t = num("acrylic_t");
    const gap = num("acrylic_gap");
    if (t !== null && t !== SANDWICH.t) out.acrylic_t = t;
    if (gap !== null && gap !== SANDWICH.gap) out.acrylic_gap = gap;
  }
  if (form.elements.core.value === "vslot") {
    out.core = "vslot";
    const stock = num("vslot_stock");
    if (stock !== null && stock !== VSLOT_STOCK) out.vslot_stock = stock;
  }
  return out;
}

function syncCore() {
  $("#vslot").classList.toggle("hidden", form.elements.core.value !== "vslot");
}

function syncSandwich() {
  $("#sandwich").classList.toggle("hidden", form.elements.glazing.value !== "acrylic");
}

function fillForm(p) {
  for (const k of FIELDS) form.elements[k].value = p[k];
  form.elements.screen.checked = p.screen;
  const limit = p.max_pane || state.maxPane;
  form.elements.max_none.checked = !p.max_pane;
  ["max_a", "max_b"].forEach((k, i) => { form.elements[k].value = limit[i]; form.elements[k].disabled = !p.max_pane; });
  form.elements.bays.value = p.bays === undefined ? "" : p.bays;
  form.elements.acrylic_t.value = p.acrylic_t === undefined ? SANDWICH.t : p.acrylic_t;
  form.elements.acrylic_gap.value = p.acrylic_gap === undefined ? SANDWICH.gap : p.acrylic_gap;
  syncSandwich();
  form.elements.core.value = p.core || "";
  form.elements.vslot_stock.value = p.vslot_stock === undefined ? VSLOT_STOCK : p.vslot_stock;
  syncCore();
  const preset = state.presets.find((x) => x.bed.join() === p.bed.join());
  form.elements.preset.value = preset ? preset.key : "custom";
  ["bed_x", "bed_y", "bed_z"].forEach((k, i) => { form.elements[k].value = p.bed[i]; });
  $("#custom-bed").classList.toggle("hidden", Boolean(preset));
}

function shareUrl() {
  const p = readForm();
  const q = new URLSearchParams();
  for (const k of ["name", "opening_w", "opening_h", "fix_gap", "awning_h", "glazing", "tier"]) q.set(k, p[k]);
  q.set("screen", p.screen ? "1" : "0");
  q.set("bed", p.bed.join(","));
  if (p.max_pane) q.set("max_pane", p.max_pane.join(",")); else q.set("max_pane", "none");
  if (p.bays !== undefined) q.set("bays", p.bays);
  if (p.acrylic_t !== undefined) q.set("acrylic_t", p.acrylic_t);
  if (p.acrylic_gap !== undefined) q.set("acrylic_gap", p.acrylic_gap);
  if (p.core) q.set("core", p.core);
  if (p.vslot_stock !== undefined) q.set("vslot_stock", p.vslot_stock);
  return `${location.origin}${location.pathname}?${q}`;
}

function copyLink() {
  const btn = $("#copy-link");
  const done = (ok) => {
    btn.textContent = ok ? "Copied" : "Copy failed";
    setTimeout(() => { btn.textContent = "Copy link"; }, 1500);
  };
  const url = shareUrl();
  history.replaceState(null, "", url);
  if (navigator.clipboard && navigator.clipboard.writeText) {
    navigator.clipboard.writeText(url).then(() => done(true), () => done(false));
  } else {
    const t = document.createElement("textarea");
    t.value = url;
    document.body.append(t);
    t.select();
    let ok = false;
    try { ok = document.execCommand("copy"); } catch (e) { ok = false; }
    t.remove();
    done(ok);
  }
}

function fromQuery(defaults) {
  const q = new URLSearchParams(location.search);
  const p = { ...defaults, max_pane: state.maxPane };
  for (const k of FIELDS) if (q.has(k)) p[k] = q.get(k);
  if (q.has("screen")) p.screen = !["0", "false", "no"].includes(q.get("screen"));
  if (q.has("bed")) p.bed = q.get("bed").split(",").map(Number);
  if (q.has("max_pane")) p.max_pane = q.get("max_pane") === "none" ? null : q.get("max_pane").split(",").map(Number);
  if (q.has("bays")) p.bays = Number(q.get("bays"));
  if (q.has("acrylic_t")) p.acrylic_t = Number(q.get("acrylic_t"));
  if (q.has("acrylic_gap")) p.acrylic_gap = Number(q.get("acrylic_gap"));
  if (q.has("core")) p.core = q.get("core");
  if (q.has("vslot_stock")) p.vslot_stock = Number(q.get("vslot_stock"));
  return p;
}

function currentName() {
  return form.elements.name.value.trim();
}

function previewErrors() {
  return (state.preview && state.preview.errors) || {};
}

function sameParams(values, params) {
  const keys = new Set([...Object.keys(values), ...Object.keys(params)]);
  return [...keys].every((k) => JSON.stringify(values[k]) === JSON.stringify(params[k]));
}

function jobForForm() {
  const job = state.job;
  if (!job || job.name !== currentName()) return null;
  return { job, stale: !job.params || !sameParams(readForm(), job.params) };
}

function showErrors(errors) {
  const slots = [...document.querySelectorAll(".err[data-for]")];
  const named = new Set(slots.map((el) => el.dataset.for).filter((k) => k !== "_form"));
  const general = Object.entries(errors).filter(([k]) => !named.has(k)).map(([, v]) => v);
  for (const el of slots) el.textContent = el.dataset.for === "_form" ? general.join(" ") : errors[el.dataset.for] || "";
  for (const el of form.querySelectorAll("input")) {
    const key = el.name.startsWith("bed_") ? "bed" : el.name.startsWith("max_") ? "max_pane" : el.name;
    el.classList.toggle("invalid", Boolean(errors[key]));
  }
}

function schedulePreview() {
  clearTimeout(state.timer);
  state.timer = setTimeout(runPreview, 250);
}

async function runPreview() {
  const seq = ++state.seq;
  let r;
  try {
    r = await postJson("/api/preview", readForm());
  } catch (e) {
    return;
  }
  if (seq !== state.seq) return;
  if (r.status !== 200) {
    showErrors({ _form: r.body.error || `Preview failed (HTTP ${r.status}).` });
    return;
  }
  const body = r.body;
  state.preview = body;
  showErrors(body.errors);
  const drawn = Boolean(body.drawing);
  for (const id of ["#drawing", "#badges", "#explain", "#parts"]) $(id).classList.toggle("stale", !drawn);
  if (drawn) {
    drawFront(body.drawing);
    showChecks(body.checks);
    showWeight(body.weight);
    showParts(body.parts);
    $("#maxseg").textContent = `Bed ${body.layout.bed.join(" x ")} mm: segments up to ${body.layout.max_seg} mm.`;
    const lay = body.layout;
    form.elements.bays.placeholder = `automatic: ${lay.auto_bays}`;
    $("#bays-note").textContent = lay.bays > 1
      ? `${lay.bays} bays, ${lay.bays - 1} mullion${lay.bays > 2 ? "s" : ""}, ${Math.round(lay.pitch * 10) / 10} mm apart.`
      : "One bay: no mullions.";
  }
  updateButtons();
}

function el(tag, attrs, text) {
  const node = document.createElementNS(SVG, tag);
  for (const [k, v] of Object.entries(attrs)) node.setAttribute(k, v);
  if (text !== undefined) node.textContent = text;
  return node;
}

function drawFront(d) {
  const [x0, y0, x1, y1] = d.bounds;
  const Y = (y) => y0 + y1 - y;
  const fs = d.step * 0.42;
  const t = d.step * 0.12;
  const svg = el("svg", { viewBox: `${x0} ${y0} ${x1 - x0} ${y1 - y0}`, "font-size": fs });
  for (const r of d.rects) {
    svg.append(el("rect", { class: `r-${r.kind}`, x: r.x, y: Y(r.y + r.h), width: r.w, height: r.h, "vector-effect": "non-scaling-stroke" }));
  }
  for (const m of d.dims) {
    const g = el("g", { class: "dim" });
    const line = (ax, ay, bx, by) => g.append(el("line", { x1: ax, y1: Y(ay), x2: bx, y2: Y(by), "vector-effect": "non-scaling-stroke" }));
    const mid = (m.a + m.b) / 2;
    if (m.axis === "x") {
      line(m.a, m.at, m.b, m.at);
      for (const x of [m.a, m.b]) { line(x, m.from, x, m.at - t); line(x - t, m.at - t, x + t, m.at + t); }
      g.append(el("text", { x: mid, y: Y(m.at) - fs * 0.35, "text-anchor": "middle" }, m.text));
    } else {
      line(m.at, m.a, m.at, m.b);
      for (const y of [m.a, m.b]) { line(m.from, y, m.at + (m.at > m.from ? t : -t), y); line(m.at - t, y - t, m.at + t, y + t); }
      const tx = m.at - fs * 0.35;
      g.append(el("text", { x: tx, y: Y(mid), "text-anchor": "middle", transform: `rotate(-90 ${tx} ${Y(mid)})` }, m.text));
    }
    svg.append(g);
  }
  for (const l of d.labels) svg.append(el("text", { class: "label", x: l.x, y: Y(l.y), "text-anchor": "middle", "dominant-baseline": "middle" }, l.text));
  $("#drawing").replaceChildren(svg);
}

function showWeight(w) {
  const note = $("#weight-note");
  if (!w) {
    note.textContent = "";
    return;
  }
  note.textContent = `Weight estimate: about ${w.total_kg} kg all up (${w.kg_per_m2} kg/m²): `
    + `glass ${w.glass_kg}, tube cores ${w.core_kg}, printed plastic ${w.plastic_kg}, `
    + `hardware and seals ${w.hardware_kg}. The sash alone is ${w.sash_kg} kg.`;
}

function showChecks(checks) {
  const core = checks.find((c) => c.name === "core");
  $("#core-note").textContent = core ? core.msg : "";
  $("#badges").replaceChildren(...checks.map((c) => {
    const b = document.createElement("span");
    b.className = `badge ${c.ok ? "ok" : "fail"}`;
    b.textContent = CHECKS[c.name] || c.name;
    b.title = c.msg;
    return b;
  }));
  $("#explain").replaceChildren(...checks.filter((c) => !c.ok).map((c) => {
    const p = document.createElement("p");
    p.textContent = `${CHECKS[c.name] || c.name}: ${c.msg}`;
    return p;
  }));
}

function showParts(parts) {
  const ids = new Set(parts.map((p) => p.id));
  state.selected = new Set([...state.selected].filter((id) => ids.has(id)));
  const rows = parts.map((p) => {
    const tr = document.createElement("tr");
    tr.dataset.id = p.id;
    const cells = [p.id, p.name, p.qty, p.length === null ? "" : p.length.toFixed(2), p.role, ""];
    const box = document.createElement("input");
    box.type = "checkbox";
    box.checked = state.selected.has(p.id);
    box.addEventListener("change", () => {
      if (box.checked) state.selected.add(p.id); else state.selected.delete(p.id);
      updateButtons();
    });
    const first = document.createElement("td");
    first.append(box);
    tr.append(first);
    cells.forEach((text, i) => {
      const td = document.createElement("td");
      td.textContent = text;
      td.className = ["id", "", "n", "n", "", "st"][i];
      tr.append(td);
    });
    tr.addEventListener("click", (e) => { if (e.target !== box) viewPart(p); });
    return tr;
  });
  $("#parts tbody").replaceChildren(...rows);
  const prints = parts.reduce((n, p) => n + p.qty, 0);
  $("#parts-sum").textContent = `${parts.length} types, ${prints} prints`;
  showStates();
}

function showStates() {
  const mine = jobForForm();
  for (const tr of document.querySelectorAll("#parts tbody tr")) {
    const s = mine ? mine.job.parts[tr.dataset.id] || "" : "";
    const stale = Boolean(s) && mine.stale;
    const cell = tr.lastChild;
    cell.textContent = stale ? `${s}, old settings` : s;
    cell.className = `st st-${s}${stale ? " st-stale" : ""}`;
    tr.classList.toggle("failed", s === "failed" && !stale);
    tr.classList.toggle("viewing", tr.dataset.id === state.viewing);
    tr.title = stale ? "Rendered with different settings: render again." : ((mine && mine.job.errors[tr.dataset.id]) || []).join("\n");
  }
}

function updateButtons() {
  const running = Boolean(state.job && state.job.state === "running");
  const renderable = Boolean(state.preview && state.preview.ok) && !running;
  $("#render-all").disabled = !renderable;
  $("#render-sel").disabled = !renderable || state.selected.size === 0;
  $("#render-sel").textContent = state.selected.size ? `Render selected (${state.selected.size})` : "Render selected";
  $("#cancel").disabled = !running;
  $("#select-all").checked = state.preview && state.preview.parts ? state.selected.size === state.preview.parts.length : false;
  const links = [];
  const mine = running ? null : jobForForm();
  if (mine && mine.stale) {
    const note = document.createElement("span");
    note.className = "note";
    note.textContent = `The settings differ from the last render of ${mine.job.name}: render again to download.`;
    links.push(note);
  } else if (mine) {
    const job = mine.job;
    const okCount = Object.values(job.parts).filter((s) => s === "ok").length;
    const href = `/api/zip/${encodeURIComponent(job.name)}`;
    if (job.state === "done") links.push(link(href, `Download ${job.name}-openwindow.zip`));
    else if (okCount) links.push(link(`${href}?partial=1`, `Download partial zip (${okCount} parts ok)`));
  }
  $("#downloads").replaceChildren(...links);
}

function link(href, text) {
  const a = document.createElement("a");
  a.href = href;
  a.textContent = text;
  a.setAttribute("download", "");
  return a;
}

function showJob(job) {
  state.job = job.state === "idle" ? null : job;
  const rev = state.job ? `${job.started} ${job.state}` : "";
  if (rev !== state.jobRev) {
    state.jobRev = rev;
    viewer.invalidate();
    refreshView();
  }
  const bar = $("#bar");
  if (!state.job) {
    $("#job-text").textContent = "No render in this session.";
  } else {
    bar.style.width = `${job.total ? (100 * job.done) / job.total : 0}%`;
    bar.className = job.state;
    const text = {
      running: `Rendering ${job.name}: ${job.done} of ${job.total} parts, now ${job.current.join(" ")} (${job.elapsed} s)`,
      done: `Rendered ${job.name}: ${job.total} parts ok in ${job.elapsed} s.`,
      failed: `${job.name}: ${job.error}`,
      cancelled: `Cancelled after ${job.done} of ${job.total} parts.`,
    };
    $("#job-text").textContent = text[job.state] || job.state;
    $("#log").textContent = job.state === "done" ? "" : job.log_tail.join("\n");
  }
  showStates();
  updateButtons();
}

function schedulePoll(ms) {
  clearTimeout(state.poll);
  state.poll = setTimeout(pollJob, ms);
}

async function pollJob() {
  clearTimeout(state.poll);
  let job;
  try {
    job = await getJson("/api/job");
  } catch (e) {
    schedulePoll(backoff(++state.pollFailures));
    return;
  }
  state.pollFailures = 0;
  showJob(job);
  if (job.state === "running") schedulePoll(1000);
}

async function startRender(ids) {
  const body = readForm();
  if (ids) body.ids = ids;
  let r;
  try {
    r = await postJson("/api/render", body);
  } catch (e) {
    showErrors({ ...previewErrors(), _render: `Render not started: ${e.message}.` });
    return;
  }
  if (r.status !== 200) {
    showErrors({ ...previewErrors(), ...(r.body.errors || { _render: r.body.error || `Render not started (HTTP ${r.status}).` }) });
    return;
  }
  showErrors(previewErrors());
  showJob(r.body.job);
  schedulePoll(1000);
}

async function pollBox() {
  const pill = $("#box");
  try {
    const b = await getJson("/api/box");
    pill.className = `pill ${b.ok ? "ok" : "down"}`;
    pill.textContent = `Render engine: ${b.ok ? "reachable" : "unreachable"}`;
  } catch (e) {
    pill.className = "pill";
    pill.textContent = "Render engine: unknown, server not reachable";
  }
}

function stlUrl(name, id) {
  return `/api/stl/${encodeURIComponent(name)}/${encodeURIComponent(id)}`;
}

function notRendered(e) {
  return e.status === 404 && ["not rendered", "unknown window"].includes(e.message);
}

function refreshView() {
  const v = state.view;
  if (!v) return;
  if (v.assembly) viewAssembly();
  else viewPart((state.preview && state.preview.parts || []).find((p) => p.id === v.part.id) || v.part);
}

async function viewPart(p) {
  const token = ++state.viewSeq;
  const name = currentName();
  state.view = { part: p };
  state.viewing = p.id;
  showStates();
  $("#viewer-title").textContent = `${p.id}: ${p.name}`;
  $("#viewer-note").textContent = `Loading ${p.id}...`;
  try {
    const shown = await viewer.showPart(stlUrl(name, p.id));
    if (token !== state.viewSeq || !shown) return;
    $("#viewer-note").textContent = `Print ${p.qty}. Drag to orbit, scroll to zoom.`;
  } catch (e) {
    if (token !== state.viewSeq) return;
    viewer.clear();
    $("#viewer-note").textContent = notRendered(e) ? `${p.id} is not rendered yet for ${name}.` : `Could not show ${p.id}: ${e.message}.`;
  }
}

async function viewAssembly() {
  if (!state.preview || !state.preview.assembly) return;
  const token = ++state.viewSeq;
  const name = currentName();
  state.view = { assembly: true };
  state.viewing = null;
  showStates();
  const many = state.preview.layout && state.preview.layout.bays > 1;
  $("#viewer-title").textContent = `${name}: ${many ? "frame, transom, mullions and sashes" : "frame, transom and sash"}`;
  $("#viewer-note").textContent = "Loading the assembly...";
  let failed;
  try {
    failed = await viewer.showAssembly((id) => stlUrl(name, id), state.preview.assembly);
  } catch (e) {
    if (token !== state.viewSeq) return;
    viewer.clear();
    $("#viewer-note").textContent = `Could not show the assembly: ${e.message}.`;
    return;
  }
  if (token !== state.viewSeq || failed === null) return;
  const missing = failed.filter(([, e]) => notRendered(e)).map(([id]) => id);
  const broken = failed.filter(([, e]) => !notRendered(e));
  const notes = [];
  if (broken.length) notes.push(`Could not show ${broken.map(([id]) => id).join(", ")}: ${broken[0][1].message}.`);
  if (missing.length) notes.push(`Not rendered yet: ${missing.join(", ")}.`);
  $("#viewer-note").textContent = notes.length ? notes.join(" ") : "Seen from outside. Drag to orbit, scroll to zoom.";
}

async function init() {
  let presets, defaults, maxPane;
  for (let failures = 0; ; failures++) {
    try {
      ({ presets, defaults, max_pane: maxPane } = await getJson("/api/presets"));
      break;
    } catch (e) {
      await sleep(backoff(failures));
    }
  }
  state.presets = presets;
  if (maxPane) state.maxPane = maxPane;
  const select = form.elements.preset;
  for (const p of presets) select.append(new Option(p.label, p.key));
  select.append(new Option("Custom", "custom"));
  fillForm(fromQuery(defaults));
  form.addEventListener("input", (e) => {
    if (e.target.name === "preset") {
      const preset = presets.find((p) => p.key === select.value);
      if (preset) fillForm({ ...readForm(), bed: preset.bed });
      $("#custom-bed").classList.toggle("hidden", Boolean(preset));
    }
    if (e.target.name === "max_none") ["max_a", "max_b"].forEach((k) => { form.elements[k].disabled = e.target.checked; });
    if (e.target.name === "glazing") syncSandwich();
    if (e.target.name === "core") syncCore();
    schedulePreview();
  });
  $("#render-all").addEventListener("click", () => startRender(null));
  $("#render-sel").addEventListener("click", () => startRender([...state.selected]));
  $("#cancel").addEventListener("click", () => postJson("/api/cancel", {}).catch(() => null).then(pollJob));
  $("#copy-link").addEventListener("click", copyLink);
  $("#assembled").addEventListener("click", viewAssembly);
  $("#select-all").addEventListener("change", (e) => {
    state.selected = new Set(e.target.checked && state.preview && state.preview.parts ? state.preview.parts.map((p) => p.id) : []);
    for (const box of document.querySelectorAll("#parts tbody input")) box.checked = e.target.checked;
    updateButtons();
  });
  pollBox();
  setInterval(pollBox, 30000);
  await runPreview();
  await pollJob();
  const view = new URLSearchParams(location.search).get("view");
  if (view === "assembled") viewAssembly();
  else if (view && state.preview && state.preview.parts) {
    const part = state.preview.parts.find((p) => p.id === view);
    if (part) viewPart(part);
  }
}

init();
