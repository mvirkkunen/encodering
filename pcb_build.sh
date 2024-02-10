set -e

mkdir -p build/
mkdir -p build/led_pcb/

./led_ring.py

cat <<EOF >build/led_pcb/fp-lib-table
(fp_lib_table
  (version 7)
  (lib (name "Project")(type "KiCad")(uri "\${KIPRJMOD}/../../Project.pretty")(options "")(descr ""))
)
EOF

kicad-cli pcb export step build/led_pcb/led_pcb.kicad_pcb -o build/led_pcb.step
kicad-cli pcb export step controller_pcb/controller_pcb.kicad_pcb -o build/controller_pcb.step

#pcbnew build/led_pcb/led_pcb.kicad_pcb
#kicad-cli pcb export svg build/led_pcb.kicad_pcb -l F.Cu,B.Cu,F.SilkS,Edge.Cuts -o build/display.svg
#echo
#display -density 1000 build/display.svg
#display build/display.svg

exit 0

count=3

rm -rf build/panel/
kikit panelize \
  --layout "plugin; code: multi_grid_layout.py.Plugin; cols: 3; space: 2mm; rotation: 45deg; boards: $count * controller_pcb/controller_pcb.kicad_pcb, $count * build/led_pcb/led_pcb.pcb" \
  --tabs "fixed; width: 3mm;" \
  --cuts "mousebites; drill: 0.5mm; spacing: 1mm; offset: 0.2mm; prolong: 0.75mm" \
  --framing "railstb; width: 5mm; space: 2mm; cuts: both" \
  --post "millradius: 1mm" \
  controller_pcb/controller_pcb.kicad_pcb \
  build/panel/panel.kicad_pcb

kikit fab jlcpcb \
  --no-drc \
  --assembly \
  --schematic ../round_panel/round_panel.kicad_sch \
  --schematic /home/matti/devel/encodering/hardware/encodering.kicad_sch \
  build/panel/panel.kicad_pcb \
  build/
