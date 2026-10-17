# OpenWindow web configurator — Design Spec

Date: 2026-10-10
Status: Implemented (plan: docs/plans/2026-10-10-web-configurator.md). Revised 2026-10-10: local server + Windows-box OpenSCAD, replacing the in-browser WebAssembly design; revised again 2026-10-10 after code review: STL invalidation, job state, process and error handling

## 1. Goal

A local web page where the owner enters a window opening and options and gets three things:
- the resulting window, with its checks, as they type;
- every printable part, rendered by native OpenSCAD on the Windows build box;
- one zip with the STLs, cut list, glass sizes, BOM, params file and a README for that opening.

Users: the project owner, on the Mac, at home. The Windows build box must be reachable on the LAN. Not public.

## 2. Decisions

| Topic | Decision |
|---|---|
| Where it runs | `python3 web/server.py` on the Mac: stdlib `http.server`, bound to 127.0.0.1 only |
| Generator | The existing Python (`tools/window.py`, `tools/generate.py`, `bom/build_bom.py`), called in-process by the server. No JavaScript port |
| Rendering | The existing `cad/box.sh render` on the Windows box (native OpenSCAD, manifold backend) |
| Preview | Live dimensioned 2D front view (SVG), check badges and parts table, all from the Python generator, plus a built-in WebGL STL viewer (no third-party library) |
| New options | Screen on/off; printer bed size |
| Downloads and installs | None. Python 3 stdlib on the Mac, plain HTML/CSS/JS in the browser, existing SSH to the box |
| Hosting | None (local only). Making it public later would need a hosted render backend and is out of scope |

## 3. Inputs

| Field | Type | Default | Notes |
|---|---|---|---|
| `name` | text, `[a-z0-9-]+`, 1–40 chars | `my-window` | params file name, output folder name, zip name |
| `opening_w`, `opening_h` | mm, 300–3000 | 1800, 1500 | |
| `fix_gap` | mm, 0–20 | 8 | 6–10 recommended |
| `awning_h` | mm | 450 | ≥ `MIN_AWNING` |
| `glazing` | `igu` / `acrylic` / `twinwall` | `igu` | |
| `tier` | integer 1 / 2 / 3 | 3 | BOM material advice only. `2.0` is rejected, not rounded |
| `screen` | bool | true | new |
| `bed` | preset or custom `[x, y, z]` mm (each 100–500) | P1S `[256, 256, 256]` | new. Presets: Bambu P1S/P1P/X1/A1 256³; A1 mini 180³; Prusa MK4 250×210×220; Prusa Mini 180³; Ender-3 220×220×250; Custom |

The params file gains the optional keys `screen` (default `true`) and `bed` (default `[256, 256, 256]`). Existing params files keep working unchanged.

## 4. Generator changes (Python)

### 4.1 Bed size
- The maximum segment length is `max_seg(bed) = min(bed_z, max(bed_x, bed_y)) − BED_MARGIN`, with `BED_MARGIN = 16` mm (a new `dims.json` key). P1S gives 240, identical to today's `MAX_SEG`.
  - `bed` must be a list or tuple of exactly three finite numbers (no booleans, NaN or infinity), each over `BED_MARGIN`. Anything else raises `ValueError` with a message starting `bed must be`.
  - The result is floored to 0.01 mm, so segment lengths (rounded to 0.01 mm) can never exceed it. Whole-millimetre and two-decimal beds keep their exact value.
  - `layout()` returns a copy of the bed in `lay["bed"]`, never the params list or `DEFAULT_BED` itself.
- `split()` and every caller use `max_seg(bed)` in place of `D["MAX_SEG"]`.
- **Minimum segment counts.** `split(length, gap, limit, min_n=1)` uses `n = max(min_n, fewest segments under the limit)`, so a big bed can't merge parts that the hardware needs apart:
  - transom: at least 2, because the two `TE` ends carry the two cam bosses;
  - head, with the screen on: at least one `H` segment per hinge, so every hinge has its boss pair and inserts. The hinge count rule (3 hinges over a 1000 mm screen width, else 2) is `window.hinge_count()`, and `layout()` returns it as `lay["hinges"]` (0 with the screen off, which sets no minimum);
  - sash bottom rail: no minimum. With one segment, its single `SBE` carries both boss pairs, `keeper_dz` either side of the middle, and these land over the two cams, so `cam_keeper` checks it as before.
  - With the P1S bed none of these minimums changes a segment count, so the default output is unchanged.
- **New check `bed_fit`:** every part's expected bounding box must fit the bed in some rotation (sorted part dimensions ≤ sorted bed dimensions).
  - Segment-type parts: the profile envelope × length.
  - Fixed-size parts (corners, nodes, shoes, small parts): the per-part envelope table `tools/part_envelopes.json`, written from rendered STLs by a helper script.
  - Beads are keyed per glazing (`BFH/igu`, `BFH/acrylic`, `BFH/twinwall`, …), because twinwall beads are 8 mm deeper (`GLASS_T − TWINWALL_T`): 18 × 19.8 mm, not 10 × 19.8 mm. The igu and acrylic entries come from the reference renders. The twinwall entries come from a one-off box render of a temporary twinwall window's beads (`cad/box.sh render <name> BFH BFV BSH BSV`, then `python3 tools/part_envelopes.py <name> BFH BFV BSH BSV`, which merges them into the table). The temporary params file and its STLs were deleted afterwards.
  - With no arguments, the helper re-measures the reference renders and keeps the other entries. A unit test checks that the committed table matches the reference renders, and that each twinwall bead equals its igu bead deepened by `GLASS_T − TWINWALL_T`.
- The existing `cam_keeper` offset limits already depend on segment length. A bed that is too small for them fails that check, with no special handling.
- `check_stl` uses the params' bed in place of its fixed 256 mm.
- `cad/box.sh render` is unchanged. It renders whatever the generator writes.

### 4.2 Screen off
- `parts()` omits `NH`, `NV`, `CN`, `HG` and `HS`, and `H` segments get no hinge bosses (`bosses=false`).
- `layout()` omits the screen members and alu10 tubes.
- The BOM omits:
  - the screen tube, magnet strips A and B, mesh, spline and screen epoxy;
  - the 8g × 12 screen screws, the hinge M4 × 10 pan screws and the M4 × 50 pins;
  - the `H` insert pairs.
- The frame magnet channel stays in the profiles (no geometry change).
- Build and install guides: a note that screen-related steps are skipped when `screen` is false.

### 4.3 Compatibility
With no new keys, the CLI output is byte-identical to today's, and all existing Python tests pass unchanged.

- **One deliberate exception: very small openings** (up to about 373 mm wide with the default bed). The minimum-segment rule now gives these a 2-segment head and transom instead of 1. Those windows failed the cam/keeper check before and still fail it, and the two reference windows are unaffected.

## 5. Web app architecture (`web/`)

| Path | Responsibility |
|---|---|
| `server.py` | Stdlib HTTP server on 127.0.0.1 (default port 8765). Serves `static/`, and the JSON API in §6 under `/api/*`. Runs one render job at a time. Holds the job state in memory |
| `api.py` | Pure functions the server calls: validate params, `preview(params)` (layout, parts, checks, BOM, drawing geometry), `save_params(params)`, `render_job(...)`, `build_zip(name)`. Unit-tested without HTTP |
| `drawing.py` | Front-view geometry for the SVG: rectangles and dimension lines in window coordinates from `layout()` |
| `zipper.py` | Builds `<name>-openwindow.zip` with `zipfile`, plus the README.txt text (including the checks-failed block) |
| `static/index.html`, `static/style.css` | Page layout: form on the left; drawing, badges and parts table on the right; viewer panel |
| `static/app.js` | Form handling and debounced `/api/preview` calls, rendering the SVG, badges and table; starting, polling and cancelling render jobs; the download link; the "server not reachable" banner |
| `static/viewer.js` | Minimal WebGL viewer: parses binary/ASCII STL, centres and scales it, orbit/zoom with the mouse, one directional light. Single-part view, plus an "assembled" view placing frame, transom and sash instances from layout transforms returned by the API. Meshes are cached per URL (in-flight loads shared); `invalidate()` deletes every cached GPU buffer and is called whenever a job starts or ends. A view that has been superseded by a newer one never replaces it |
| `README.md` | How to run, requirements (Windows box reachable, SSH key), troubleshooting |
| `tests/test_api.py`, `tests/test_drawing.py`, `tests/test_zipper.py`, `tests/test_server.py`, `tests/test_viewer.py` | stdlib `unittest`. `test_server` starts the server on an ephemeral port and exercises the API with `urllib`/`http.client`, with the render step replaced by `fake_box.py`. `test_viewer` runs `tests/viewer_test.mjs` (plain JS, stubbed WebGL and `fetch`) under Node when Node is installed, and is skipped otherwise. No test reads the reference renders in `cad/stl/` |

## 6. HTTP API (JSON)

| Method / path | Purpose |
|---|---|
| `GET /` and static files | the page |
| `GET /api/presets` | the bed presets list |
| `POST /api/preview` | body: params → `{ok, errors:{field:msg}, layout, checks, parts:[{id,name,qty,length,role}], bom:[...], drawing:{...}}`. Pure Python and fast; no box access |
| `POST /api/render` | body: params (+ optional `ids`) → writes `params/<name>.json`, starts a job, returns `{job}`. Refuses with 409 if a job is running and with 400 on invalid params (`{errors:{field:msg}}`; a bad ID list is `{errors:{ids}}`). The busy check, the params write, the STL invalidation and the job start happen under one lock, so two concurrent requests start one job and leave that job's params on disk |
| `GET /api/job` | `{state: idle/running/done/failed/cancelled, name, params, total, done, current, parts:{id:state}, errors:{id:[msg]}, error, log_tail, started, finished, elapsed}`. `params` are the validated params the job renders; `finished` is `null` while running |
| `POST /api/cancel` | stops the running job: SIGTERM to the `box.sh` process group, then SIGKILL to the same group after 15 s, even if the leader has already exited |
| `GET /api/stl/<name>/<id>` | the rendered STL bytes, for the viewer. 409 while a job for that window is running; 404 `not rendered` when the file is missing, including one deleted while it is read |
| `GET /api/zip/<name>` | the zip of the STLs on disk that pass `check_stl`. `?partial=1` allows a zip of only the parts that passed. 409 while a job for that window is running, when a part is missing (without `partial`), or when a file vanishes while the zip is built. The params file is read once, so the zip's `params.json` always matches the STLs |
| `GET /api/box` | `{ok, host, checked}` from `box.sh ping`, cached 30 s; only one ping runs at a time and concurrent callers wait for its result |

**Render job.**
- **STL invalidation.** `save_params` reports whether it changed `params/<name>.json` (a new file counts as a change). If it did, every `cad/stl/<name>/*.stl` is deleted before the job starts, so STLs from other params (glazing or screen changes keep the same lengths, which `check_stl` cannot see) never mix into a zip, whether the job finishes, fails or is cancelled. If the params are unchanged, nothing is deleted and `box.sh` overwrites the files in place. This is what keeps the reference windows' STLs (which may be re-rendered with their own params) intact when a render is cancelled or the box fails. Params edited outside the server are not detected.
- The server runs `cad/box.sh render <name> <ids…>` in batches of up to 6 part IDs, one batch after another, so the progress has a real per-batch granularity.
- After each batch, a part is `ok` only if `box.sh` wrote a new file for it in this batch (its inode, size, mtime or ctime changed) and that file passes `check_stl`. An old file left in place is reported as `<id>: box.sh did not write a new <id>.stl`, so a failed batch never shows old STLs as freshly rendered.
- `box.sh` output is read as UTF-8 with invalid bytes replaced. If reading it fails for any other reason, the process group is stopped (SIGTERM, then SIGKILL after 15 s) and waited for before the job fails.
- When everything has rendered, it runs `bom/build_bom.py <name>`.
- `box.sh` concurrency and locking are already in place. Only one job runs at a time, by design.

## 7. User flow

1. **Type.** The page calls `/api/preview` (debounced, about 250 ms) and redraws:
   - the SVG front view with dimensions (opening, frame, transom, awning and fixed-pane sizes);
   - the check badges (transom deflection, stay, cam/keeper, bed fit);
   - the parts table (ID, name, quantity, length, interior/exterior).
2. **Render all,** or tick some rows and render the selection. The progress bar and per-row states follow `/api/job` (polled about every 1 s). Cancel is available.
3. **View.** Clicking a rendered row opens it in the viewer. "Assembled" shows frame, transom and sash in place.
4. **Download** `<name>-openwindow.zip`, containing:
   - `stl/<ID>_x<qty>.stl`;
   - `parts.csv`, `cutlist.csv`, `glass.csv`, `BOM.md`;
   - `params.json`;
   - `README.txt`: print settings summary, check results and pointers to the guide PDF and docs.

## 8. Error handling

- **Invalid input:** field errors from the API (the generator's messages) are shown inline. Render stays disabled.
- **Failed check:** a red badge with an explanation. Render and download stay allowed, and `README.txt` starts with a "CHECKS FAILED — do not print" block listing the failures.
- **Windows box unreachable:**
  - `box.sh` exits 255 (box down before the batch starts), or exits non-zero with ssh/scp connection-failure text in the batch output (box dropped mid-batch: `connect to host`, `Connection reset`, `Operation timed out`, `Broken pipe`, `ssh connection failed`, …). The job fails with "Windows build box unreachable (192.168.68.61)" and the log tail; that batch's parts fail with the same message and the remaining parts are skipped.
  - `/api/preview` keeps working.
  - The page shows a box-status indicator from `GET /api/box` (a quick SSH `echo`, cached for 30 s).
- **Server not reachable (from the page):** any failed request or non-JSON reply shows a red banner under the header. Job polling continues with backoff (2, 4, 8 … up to 30 s); when a request succeeds again the banner goes and the preview, job and box status refresh. The page also starts if the server comes up after it.
- **Render or check failure:** affected rows turn red with the log tail. The zip needs every part to be ok, unless `partial=1`, in which case `README.txt` lists the missing parts at the top. Render-request errors with no form field (`ids`, busy, network) appear in the general error line above the render buttons, without clearing the field errors.
- **Stale results:** the row states and the download link belong to the job's params. When the form differs from them, rows show `<state>, old settings` in grey and the link is replaced by "render again to download".
- **Viewer failures:** the note says why: not rendered yet, a render for that window is running, not an STL file, server not reachable, or no WebGL.
- **Server safety:** bound to 127.0.0.1 only. Requests need a `Host` of `127.0.0.1:<port>` or `localhost:<port>` (403 otherwise, including no `Host`). `Content-Length` must be a whole number from 0 to 64 KiB (400 otherwise). `name` is validated against `[a-z0-9-]+` before it touches any path, and IDs are checked against the generated part list. No shell strings are built from input: `subprocess` gets argument lists.
- **Server shutdown:** Ctrl-C, SIGTERM and SIGHUP all cancel a running job (process group SIGTERM, SIGKILL after 5 s), remove the `--fake-render` temporary folder and exit 0.

## 9. Testing

1. **Python generator:** new unit tests for `max_seg`, bed-size splitting, `bed_fit`, screen-off part lists, layout and BOM, and params defaults (all existing tests unchanged).
2. **web unit tests:**
   - `api` validation and preview contents;
   - `drawing` geometry for both reference windows;
   - `zipper` file list and README blocks (checks ok / failed / partial);
   - `server` endpoints with a fake renderer (preview, render, job polling, cancel, 409 while busy, 400 invalid, path-traversal attempts rejected), plus: changed params clear old STLs and unchanged ones keep them; cancelling or a box failure on an unchanged reference window keeps its STLs; a failed part's old STL is not reported ok; two concurrent renders start one job; invalid UTF-8 and read errors in the box output; cancel reaching a child process, SIGKILL for a leader that ignores SIGTERM and for a child left behind by an exited leader; exit 1 with connection-failure text; negative or non-numeric `Content-Length`; missing, `localhost` and foreign `Host`; one box ping at a time; SIGTERM/SIGHUP shutdown;
   - `viewer.js` under Node: shared in-flight loads, invalidation deleting buffers, superseded views, and the failure reasons.
3. **Live render:** start the server, `POST /api/render` for `bench-600`, poll to done, then download the zip and check its contents. All of it is driven from a Python script using `urllib` against the real Windows box. With `--cancel` it first starts a render and cancels it during the second batch, and checks that the job is cancelled, no generate lock is left behind and every reference STL is still there.
4. **UI:** headless-Chrome screenshots of the valid, invalid, failed-check, rendering, viewer and download states, each reviewed by eye. Nothing gets installed; Chrome is already on the Mac.

## 10. Out of scope (v1)

- Public hosting or other users
- The in-browser WebAssembly rendering
- Other layouts, slider sash, other wall types
- Inch input
