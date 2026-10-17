// cad/parts/setting_block.scad
include <../generated/dims.scad>
use <../profile.scad>
use <../lib/emboss.scad>

function setting_top(pane_t) = GLASS_Y0 + (is_undef(pane_t) ? GLASS_T : pane_t);

module setting_block(code, wedge = false, pane_t) {
    s = tan(SILL_SLOPE_DEG);
    floor_x = function(y) FRAME_BODY - (bead_seat_y() - y) * s;
    y0 = GLASS_Y0;
    y1 = setting_top(pane_t);
    pts = wedge ? [[floor_x(y0), y0], [floor_x(y1), y1], [GLASS_EDGE, y1], [GLASS_EDGE, y0]]
                : [[0, y0], [0, y1], [GLASS_CLEAR, y1], [GLASS_CLEAR, y0]];
    difference() {
        linear_extrude(SETTING_L) polygon(pts);
        engrave(code, [wedge ? floor_x(y0) + 0.2 : 0, (y0 + y1) / 2], SETTING_L / 2, 3);
    }
}
