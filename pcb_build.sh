set -ex

mkdir -p build/
mkdir -p build/led_pcb/

./led_ring.py

cat <<EOF >build/led_pcb/fp-lib-table
(fp_lib_table
  (version 7)
  (lib (name "Project")(type "KiCad")(uri "\${KIPRJMOD}/../../Project.pretty")(options "")(descr ""))
)
EOF
pcbnew build/led_pcb/led_pcb.kicad_pcb

kicad-cli pcb export step build/led_pcb/led_pcb.kicad_pcb --subst-models --user-origin 50.8x50.8mm -o build/led_pcb.step
exit 0

#freecad -c "import Mesh, Part; p = Part.read('build/led_pcb.step'); m = Mesh.Mesh(); m.addFacets(p.tessellate(0.05)); m.write('build/led_pcb.3mf')"

#kicad-cli pcb export step controller_pcb/controller_pcb.kicad_pcb -o build/controller_pcb.step
#freecad -c "import Mesh, Part; p = Part.read('build/controller_pcb.step'); m = Mesh.Mesh(); m.addFacets(p.tessellate(0.05)); m.write('build/controller_pcb.3mf')"


#kicad-cli pcb export svg build/led_pcb.kicad_pcb -l F.Cu,B.Cu,F.SilkS,Edge.Cuts -o build/display.svg
#echo
#display -density 1000 build/display.svg
#display build/display.svg


count=6

rm -rf build/panel/
mkdir -p build/panel/

cp -r Project.pretty build/


  #--layout "plugin; code: ../KiKit/circle_grid_layout.py.Plugin; cols: $count; space: 3mm; rotation: 180deg; boards: $count * controller_pcb/controller_pcb.kicad_pcb, $count * build/led_pcb/led_pcb.kicad_pcb;" \
kikit panelize \
  --layout "plugin; code: ../KiKit/multi_grid_layout.py.Plugin; cols: $count; space: 3mm; rotation: 0deg; boards: $count * controller_pcb/controller_pcb.kicad_pcb, $count * build/led_pcb/led_pcb.kicad_pcb;" \
  --tabs "fixed; width: 5mm; hcount: 0; vcount: 1;" \
  --cuts "mousebites; drill: 0.5mm; spacing: 0.8mm; offset: -0.2mm;" \
  --framing "railstb; width: 5mm; space: 2mm; cuts: both;" \
  --post "millradius: 1mm;" \
  controller_pcb/controller_pcb.kicad_pcb \
  build/panel/panel.kicad_pcb

kikit fab jlcpcb \
  --no-drc \
  --assembly \
  --schematic controller_pcb/controller_pcb.kicad_sch \
  build/panel/panel.kicad_pcb \
  build/

  #--schematic build/led_pcb/led_pcb.kicad_sch \

pcbnew build/panel/panel.kicad_pcb
