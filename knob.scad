$fn = 180;

diam = 16;
angle = 6;
height = 13;
knurls = 15;
knurl_r = 2.0;
knurl_angle = 8.0;
knurl_z = -0.3;
cap_r = 12;

shaft_d = 6.0 + 0.3;
shaft_d_t = 4.5;

d_interference = 0.2;

module knob() {
  intersection() {
    difference() {
      union() {
        difference() {
          cylinder(d1=diam, d2=diam - tan(angle) * height * 2, h=height);
          for (i = [0 : knurls]) {
            rotate([0, 0, 360/knurls * i])
              translate([diam/2 + knurl_r - -0.1, 0, knurl_z])
                rotate([0, -knurl_angle, 0]) cylinder(r=knurl_r , h=height*2);
          }
          
          translate([0, 0, -0.01]) difference() {
            cylinder(d=shaft_d, h=height - 2);
            translate([-shaft_d/2+shaft_d_t + d_interference, -shaft_d, -0.01])
              cube([shaft_d, shaft_d * 2, height]);
          }
        }
        
        translate([-shaft_d/2+shaft_d_t + 0.5, -shaft_d * 0.25, 0]) cylinder(d=1, h=height);
        translate([-shaft_d/2+shaft_d_t + 0.5, +shaft_d * 0.25, 0]) cylinder(d=1, h=height);
      }
      
      translate([0, 0, -0.1]) cylinder(d=diam - 3, h=4);
      
      translate([0, 0, height]) scale([4, 4, 1.4]) sphere(r=1);
      
      translate([0, 0, height - 0.65]) cylinder(d=diam, h=height);
    }
    hull() {
      translate([0, 0, height - cap_r]) sphere(r=cap_r);
      translate([0, 0, -height*2]) sphere(r=cap_r);
    }
  }
}

knob();

//intersection() { knob(); translate([-50, 0, -50]) cube([100, 100, 100]);  }