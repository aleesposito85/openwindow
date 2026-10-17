# OpenWindow web configurator

A local page for one window opening. Type the opening and the options, and it shows:
- the window as you type: a dimensioned front view, the checks and the parts table;
- every printable part, rendered by OpenSCAD on the Windows build box, with a 3D viewer;
- one zip with the STLs, cut list, glass sizes, BOM, params file and a README for that opening.

It runs on the Mac and is not public: the server only listens on 127.0.0.1.

## Run

    python3 web/server.py                  # then open http://127.0.0.1:8765/
    python3 web/server.py --port 9000      # another port
    python3 web/server.py --fake-render    # page work without the box: box-shaped STLs in a temporary folder, removed on Ctrl-C

Requirements:
- Python 3 on the Mac (standard library only) and a browser. Nothing gets installed or downloaded.
- For rendering: the Windows build box on the LAN, with the SSH key `cad/box.sh` already uses. Check it with `cad/box.sh ping` (prints `ok`).

## Using it

1. **Type.** The front view, check badges and parts table follow the form. A red field message means the input is invalid, and Render stays off until it is fixed. A red badge is a failed check: rendering and downloading still work, and the zip's `README.txt` then starts with "CHECKS FAILED — do not print".
2. **Glass sheet and bays.** Max pane is the largest sheet you can get, 1200 × 900 mm until you change it. Tick No limit for one bay. The window splits into the fewest equal bays that make every pane fit, and the Bays field shows that number. Type a larger number to ask for more bays.
3. **Printer.** Pick a bed preset or Custom. The generator splits every member into segments of at most min(Z, max(X, Y)) − 16 mm, and the Bed fit badge checks every part against the bed.
4. **Render all**, or tick rows and **Render selected**. The window's params are saved to `params/<name>.json`. A reference window (`bench-600`, `home-1800x1500`, `home-1800x1500-2bay`) is never overwritten: rendering it with its own values is fine, and changed values need another name (the refusal lists the fields that differ). The one-bay references `bench-600` and `home-1800x1500` have no sheet limit, so tick **No limit** before rendering them. Parts render in batches of up to six through `cad/box.sh render`, each STL is checked like `tools/check_stl.py` does, and `bom/<name>.*` is rebuilt at the end. One job runs at a time, and **Cancel** stops the running batch.
5. **View.** Click a part row to see its STL, or **Assembled** for the frame, transom, mullions and each bay's sash in place, seen from outside. Drag to orbit and scroll to zoom.
6. **Download** `<name>-openwindow.zip` once every part has passed its STL check. If some parts failed, a partial zip leaves them out and lists them at the top of its `README.txt`.

Any form field can also be preset in the address, for example `/?name=bench-600&opening_w=600&opening_h=600&awning_h=200&glazing=acrylic&tier=1&max_pane=none`. Add `view=<ID>` or `view=assembled` to open the viewer, and `max_pane=1200,900` or `max_pane=none` for the sheet limit. For acrylic glazing, `acrylic_t=3&acrylic_gap=12` sets the panel thickness and air gap; the page only sends them when they differ from 4 and 16, so the reference windows still match. `core=vslot` picks V-slot cores, and `vslot_stock=1200` sets a piece length other than 1000 mm.

## Files it writes

The same files as the command-line flow: `params/<name>.json`, `cad/generated/` (rewritten by every `box.sh` batch, as on the command line), `cad/stl/<name>/` and `bom/<name>.*`. The zip is built on request and isn't stored.

## Tests

    python3 -m unittest discover -s web/tests -p 'test_*.py'   # no box needed; the renderer is web/fake_box.py
    python3 web/tests/live_render.py --cancel                  # needs the box: cancel check, then bench-600 end to end
    python3 web/tests/ui_shots.py <folder>                     # headless-Chrome screenshots of each UI state

## Troubleshooting

- **"Windows build box unreachable (192.168.68.61)"**: the box is off, asleep or off the LAN, or the VPN is in the way. `cad/box.sh ping` must print `ok`. The preview keeps working without the box.
- **A red part row**: hover it for its STL check errors. The log under the parts table shows the output of `box.sh`.
- **"timed out waiting for the generate.py lock"**: another `generate.py` or `box.sh` is running in a terminal. If nothing is running, an interrupted run left `.generate.lock` behind: remove it with `rmdir .generate.lock`.
- **Address already in use**: another server is on that port. Use `--port`.
- **Requests answered 403 or 415**: the server only accepts the `127.0.0.1` and `localhost` host names, and JSON POST bodies. This keeps other web pages from driving it. Don't put it behind a proxy or open it to the network.
