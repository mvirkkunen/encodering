$fn = $preview ? 45: 180;
E = 0.001;

module pcb_assembly() {
  color("green") translate([0, 0, -4.7 -1.6]) {
    difference() {
      rotate([0, 180, 0]) import("pcb_assembly.stl", convexity=5);
      /*translate([0, 0, -20]) union() {
        cylinder(d = 30, h=20 + 4.5+1.6);
        cylinder(d = 8, h=50);
      }*/
      translate([0, 0, 19]) cylinder(d=40, h=50);
    }
  }
  
  color("grey") translate([0, 0, 1.2]) {
    difference() {
      cylinder(d=11, h=2, $fn=6);
      translate([0, 0, -E]) cylinder(d=7.75, h=3);
    }
  }
}

leds = 30;
angle_step = 360 / leds;
outer_diam = 24 + 0.4;
hole_diam = 7.25;
ring_r = 10;
wall_t = 2;
led_h = 1.3;
knob_height = 15;
mizo_r = outer_diam * 0.5 + 0.8;

module led_separators(h) {
  for (a = [0 : angle_step : 360]) {
    rotate([0, 0, a]) translate([0, -0.3, 0]) cube([outer_diam/2, 0.6, h]);
  }
}

module plate() {
  alignment_hole_r = 6.5;
  alignment_hole_a = 30;

  difference() {
    union() {
      translate([0, 0, -1.6]) difference() {
        cylinder(d=outer_diam + wall_t * 2, h=led_h + 1.6);
        translate([0, 0, -E]) cylinder(d=outer_diam - 1, h=10);
      }
      cylinder(r=ring_r - 1.5, h=led_h);
      led_separators(led_h);
      
      rotate([0, 0, alignment_hole_a])
        translate([alignment_hole_r, 0, -1.2]) cylinder(d=1.9, h=1.2);
    }
    
    translate([0, 0, -1]) cylinder(d=hole_diam, h=10);
    
    translate([0, 0, 1.6])
      rotate_extrude()
        translate([mizo_r, 0])
          polygon([[-1, 0], [1, 0], [0, -1]]);
  }
}

module knob_envelope(d=0) {
  angle = 7.5;
  
  diam = outer_diam + wall_t * 2 + d;
  dd = tan(angle) * knob_height;
  cylinder(d1=diam, d2=diam - dd * 2, h=knob_height);
}

module knob() {
  diam = outer_diam + wall_t * 2;
  height = knob_height;
  knurls = 15;
  knurl_r = 2.0;
  knurl_angle = 5;
  knurl_z = -10.0;

  shaft_d = 6.0 + 0.3;
  shaft_d_t = 4.5;

  d_interference = 0.2;
  
  difference() {
    union() {
      difference() {
        union() {
          difference() {
            knob_envelope();
            translate([0, 0, -E]) cylinder(d=outer_diam - 1, h=$preview ? height + 1 : height - 0.24 + E);
          }
      
          led_separators(height);
          cylinder(r=ring_r - 1.5, h=height);
        }
        
        translate([0, 0, -0.01]) difference() {
          cylinder(d=shaft_d, h=height - 1);
          translate([-shaft_d/2+shaft_d_t + d_interference, -shaft_d, -0.01])
            cube([shaft_d, shaft_d * 2, height]);
        }
      }
      
      translate([-shaft_d/2+shaft_d_t + 0.5, -shaft_d * 0.25, 0]) cylinder(d=1, h=height);
      translate([-shaft_d/2+shaft_d_t + 0.5, +shaft_d * 0.25, 0]) cylinder(d=1, h=height);
      
      translate([0, 0, 0.5])
        rotate_extrude()
          translate([mizo_r, 0])
            polygon([[-1, 0], [1, 0], [0, -1]]);
    }
    
    translate([0, 0, -0.1]) cylinder(d=14, h=7);
    
    for (i = [0 : knurls]) {
      rotate([0, 0, 360/knurls * i + angle_step / 2])
        translate([diam/2 + knurl_r - -0.1, 0, knurl_z])
          rotate([0, -knurl_angle, 0]) cylinder(r=knurl_r , h=height*2);
    }
  }
}

module cutter() {
  translate([-50, 1, -50]) cube([100, 100, 100]);
}

if ($preview) {
  render() intersection() { cutter(); plate(); }
  intersection() { cutter(); translate([0, 0, 1.4]) rotate([0, 0, 180]) knob(); }

  pcb_assembly();
} else {
  //translate([outer_diam + 5, 0, led_h]) rotate([0, 180, 0]) plate();
  translate([0, 0, knob_height]) rotate([0, 180, 0]) knob();
  //translate([0, 0, knob_height]) rotate([0, 180, 0]) knob_envelope(-1);
}
