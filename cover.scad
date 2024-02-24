$fn = 180;

outer_diam = 24.4;
hole_diam = 7.75;
ring_r = 10;

alignment_hole_r = 6.5;
alignment_hole_a = 30;

wall_t = 1.5;

difference() {
  union() {
    difference() {
      cylinder(d=outer_diam + wall_t * 2, h=1 + 1.6);
      translate([0, 0, 0.25]) cylinder(d=outer_diam - 1, h=10);
      translate([0, 0, 1]) cylinder(d=outer_diam, h=10);
    }
    for (a = [0 : 360/30 : 360]) {
      rotate([0, 0, a]) translate([0, -0.3, 0]) cube([outer_diam/2, 0.6, 1]);
    }
    cylinder(r=ring_r - 1.5, h=1);
    rotate([0, 0, -alignment_hole_a]) translate([alignment_hole_r, 0, 0]) cylinder(d=1.9, h=1+1);
  }
  translate([0, 0, -1]) cylinder(d=hole_diam, h=10);
}