// cad/parts/test_coupon.scad
use <../lib/segment.scad>

module test_coupon(code) {
    segment("sash_rebate", 60, code, false, true);
}
