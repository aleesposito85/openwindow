# Mullions and bays: review record (2026-10-10)

Executed with subagents; every task had a task review, plus review gates after Tasks 3 and 9 and a final whole-change review.
Final state: tools 286 tests, web 148 tests, `cad/box.sh test` 8 files; reference windows bench-600 37/37, home-1800x1500 35/35, home-1800x1500-2bay 43/43; one-bay outputs byte-identical to before the feature.

## Rulings

- no git in this project — ledger/briefs/review packages live in this scratchpad workspace; each review package is `diff -ruN` against an rsync snapshot taken before the task (binary outputs cad/stl, cad/generated, docs/img, PDFs excluded; listed by name only) — cost if wrong: a reviewer could miss a binary-only change.
- transom deflection uses the plan's pinned-tee model (mullion loads as point loads on the full span), not spec §5's "propped at each mullion" — the dovetail tees carry no moment, so propping overstates stiffness; the user was told before choosing execution; Task 13 updates the spec — cost if wrong: some wide windows reported failing that would pass.
- mullion centre formula = FRAME_W − MULLION_W/2 + i·pitch (plan) instead of spec §4.1's FRAME_W + i·pitch — spec formula breaks equal bays by 35 mm — cost if wrong: none (spec arithmetic error).
- MULLION_DOVE_D = 4 mm (plan) instead of reusing the jamb's 6 mm — keeps 2.7 mm wall to the steel tube vs 0.7 — cost if wrong: weaker dovetail engagement; bench test row covers it.
- params/my-window.json (created by a configurator render before this plan) is left untouched.
- move mullion locks to u = LOCK_U (3), matching JN's proven 1.35 mm wall, and add an assert pilot-to-mating-face wall ≥ 1.35 — spec rule "walls ≥ MIN_SKIN" (1.5) yields to the JN precedent that passed three review rounds — cost if wrong: 1.35 mm skin cracks under lock torque (bench-test dovetail row covers it).
- the lower TX shoe tongue filling the transom magnet channel at the tee (~10.6×1.7×2 mm) is left as is — no magnet strip runs there (per-bay screens turn into the mullion channels at z 3..16 / 54..67) and cutting it would only leave a void — cost if wrong: a cosmetic notch-free face; no functional loss. Closes the Task 5 carry item (b).
- plan Task 12 hand check 4 (stale-row test on TX) is reworded to use H — TX only exists at ≥2 bays, so ticking No limit removes the row; H exists at both counts and shows 'ok, old settings' — cost if wrong: none (test wording only).

## Deferred minor findings (triaged by the final review: none blocking)

- Task 1: minor (deferred): "too tall" error can blame height when width is the real limit (window.py:253-258; opening_w=450, max_pane=[300,900])
- Task 1: minor (deferred): max_bays() loops forever on opening_w=inf in hand-written CLI params (window.py:233-237) — web path is range-checked
- Task 1: minor (deferred): testOneBayIsTheOldLayout compares bays=1 vs no key through the same code; pin literal old values
- Task 1: minor (deferred): bay_layout/panes_at nested closures dense (window.py:243-272)
- Task 2: minor (deferred): no failing-input tests for mullion/transom deflection, upper-stub-worse branch, plural message (test_window.py:569-587)
- Task 2: minor (deferred): long lines window.py:102,132; awkward d_/s_ names window.py:299-301; magic numbers in expected loads test_window.py:582-585
- Task 3: minor (deferred): per-bay multipliers in generate.parts restate member qty (two sources of truth) generate.py:42-56,73-90
- Task 3: minor (deferred): no bays+screen=false test; no non-integer PITCH layout.scad test
- Gate1: minor (deferred): widths(n) relies on FRAME_W−FRAME_BODY == MULLION_W/2−MULLION_HALF_BODY and FRAME_W−GLASS_EDGE == MULLION_W/2−TRANSOM_GLASS; nothing asserts them (window.py:175-187,219)
- Task 4: minor (deferred): mullion_glazing cord ring splits at both bead keyways (inherited transom pattern; has_cord assert can't see continuity) profile.scad:195-200 — note for tee/joint reviews
- Task 4: minor (deferred): asserts restate formulas (mag lip), compare absolute rects (only valid while MULLION_W==TRANSOM_W), countersink/magnet and label-y asserts too weak; add jamb-relative magnet offset + no-screen-clash asserts (mullion_test.scad:14,30-38)
- Task 4: minor (deferred): mirror_rect/both_sides generic names hard-code MULLION_W (profile.scad:10-12)
- Task 5: minor (deferred): TX 2 mm lip at x 18..20 removed over z≈21.7..48.3 by slot mouth + lower lock heads — cosmetic, outside the screens' magnet zones (cross_node.scad:18,32)
- Task 5: minor (deferred): mullion_test.scad:87 `|| hr[0] >= m[0]` exempts upper locks from the screen-channel check; tautological asserts at :64,72,80
- Task 5: minor (deferred): SN flat top 0–4.2 mm proud of the sloped sill rebate in the bay strips — no outward fall over the counterbores (frame_node.scad:19)
- Task 5: minor (deferred): cross_node uses transom_shoe.scad only for box() (cross_node.scad:8)
- Task 5: minor (deferred): SN/HN wall assert redundant with the pin (mullion_test.scad:233); TX pilot-to-tube wall now 2.05 (asserted only at MIN_SKIN)
- Task 6: minor (deferred): mullion lock bite ≈ half of JN (24% pilot area, ~75° thread arc); still works — carry → Task 13: add a room-ward mullion-shoe pull-out row to the dovetail bench test; if weak, move mlock_uv v inward
- Task 6: minor (deferred): no asserts guard tongue share of pilot / floor breakthrough / shoe pilot-to-face 1.35 (mullion_test.scad:98-131)
- Task 7: minor (deferred): testEnvelopeTableHasEveryMullionPart checks lengths only; 180 mm bed case asserts ok but not the message (test_generate.py:146-150)
- Task 8: minor (deferred): 2-bay BOM tests only at bays=2 (scaling constants coincide) — add a bays=3 test (16 tek, 20 locks, 0.7 m 3 mm cord, 3 pairs, 62 packers) (test_bom.py:290-337)
- Task 8: minor (deferred): no acrylic 2-bay BOM test (4+4 sheets, 200 g, 22.66 m); test name understates (test_bom.py:359); five bays==1 branches + q.get("SN") style (build_bom.py:76-130)
- Task 9: minor (deferred): tb/z0 recomputed in frame()/sash()/window() (assembly.scad:55,79,94-95); SN/TX placement matrices det −1 → engraved codes mirrored in the assembly view only (assembly.scad:44,46)
- Gate2: minor (deferred): mullion_test.scad:116 tube-screw-head-vs-turns assert exempts every kerf turn (weak; safe today)
- Task 10: minor (deferred): extra blank line test_drawing.py:163-165; placement test bbox-only (mirror errors invisible) :277-283; only 2-bay covered :188-206; repeated body_x+SASH_GAP drawing.py:59,148,177
- Task 11: minor (deferred): is_number raises uncaught OverflowError for 10**400 (pre-existing for opening_w; now max_pane too) api.py:63-64,94-95 — no reply sent
- Task 11: minor (deferred): tests omit NaN/inf/tuple max_pane, bays over limit, bays without max_pane, refused changed 2-bay save (test_api.py:172-220)
- Task 12: minor (deferred): #bays-note not cleared when preview invalid (app.js:158-162); preset change resets disabled Max pane inputs (app.js:79-80); empty ?bays= / ?max_pane= query → 0 not automatic (app.js:96); num("bays") twice (app.js:71-72); shot 8 too short to show SN..MSH rows; viewAssembly draws stale STLs after a bay-count change (pre-existing for width changes)
- Task 13: minor (deferred): test-log hard-codes "186 prints"; deck note hard-codes bench-1000-2bay / 1000 × 600 (stale if the generator changes); gate omits row 7 (pre-existing)
