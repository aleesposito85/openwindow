// cad/tests/corner_test.scad
include <../generated/dims.scad>
use <../profile.scad>
use <../lib/segment.scad>
use <../parts/corner_block.scad>

for (pr = [["sash_rebate", "sash_rebate"], ["sill", "glazing"], ["sash", "sash"], ["screen", "screen"]]) {
    for (q = [[pr[0], pr[1]], [pr[1], pr[0]]]) {
        a = q[0];
        b = q[1];
        e = profile_width(b);
        s = corner_screw_at(a, b);
        f = corner_fix_at(a, b);
        assert(socket_depth(a) <= socket_limit(a, b), str(a, "/", b, ": socket ", socket_depth(a), " deeper than ", socket_limit(a, b)));
        assert(s - TUBE_SCREW_D / 2 >= e - socket_depth(a) + 2 * TUBE_END_CLEAR && s + TUBE_SCREW_D / 2 <= e - 2,
               str(a, "/", b, ": tube screw lands on the tube however it sits in its end clearance"));
        if (is_perimeter(a)) {
            assert(f - FIX_D / 2 >= FRAME_BODY, str(a, "/", b, ": fixing hole exits past the other leg's body"));
            assert(f + FIX_CB_D / 2 + MIN_SKIN <= e - CORD_D / 2, str(a, "/", b, ": counterbore clears the end groove"));
            assert(fix_dz(a) == 0 || abs(f - s) - FIX_D / 2 - TUBE_SCREW_D / 2 >= MIN_SKIN, str(a, "/", b, ": fixing hole clears the tube screw"));
        }
    }
    sa = [corner_screw_at(pr[0], pr[1]), screw_x(pr[0])];
    sb = [screw_x(pr[1]), corner_screw_at(pr[1], pr[0])];
    assert(norm(sa - sb) - CSK_D >= MIN_SKIN, str(pr, ": tube-screw countersinks merge"));
}
echo("corner rules ok");
