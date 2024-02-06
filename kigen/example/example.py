#!/usr/bin/env python3

import sys
import os.path

root = os.path.dirname(__file__)
sys.path.append(os.path.join(root, ".."))

from kigen.values import *
import kigen.footprint as fp
import kigen.symbol as sym
import kigen.schematic as sch
import kigen.pcb as pcb

connector_lib = sym.SymbolLibrary.load("/usr/share/kicad/symbols/Connector.kicad_sym")
device_lib = sym.SymbolLibrary.load("/usr/share/kicad/symbols/Device.kicad_sym")
pin_header_sym = connector_lib.get("Conn_01x02_Pin")
resistor_sym = device_lib.get("R")

connector_pinheader_lib = fp.FootprintLibrary("/usr/share/kicad/footprints/Connector_PinHeader_2.54mm.pretty")
resistor_smd_lib = fp.FootprintLibrary("/usr/share/kicad/footprints/Resistor_SMD.pretty")
pin_header_fp = connector_pinheader_lib.load("PinHeader_1x02_P2.54mm_Vertical")
resistor_fp = resistor_smd_lib.load("R_0805_2012Metric")

schematic = sch.SchematicFile()

sch_j1 = schematic.place(pin_header_sym, "J1", (25.4, 25.4), footprint=pin_header_fp)
sch_r1 = schematic.place(resistor_sym, "R1", (50.8, 25.4), footprint=resistor_fp)

schematic.append(sch.Wire([sch_j1.get_pin_position("1"), sch_r1.get_pin_position("1")]))
schematic.append(sch.Wire([sch_j1.get_pin_position("2"), sch_r1.get_pin_position("2")]))

schematic.save(os.path.join(root, "project", "exampleproject.kicad_sch"))

board = pcb.PcbFile()
p1_net = board.add_net("P1")
p2_net = board.add_net("P2")

pcb_j1 = board.place(pin_header_fp, pcb.Layer.FCu, (25.4, 25.4), path=sch_j1)
pcb_r1 = board.place(resistor_fp, pcb.Layer.FCu, (50.8, 25.4, -90), path=sch_r1)

pcb_j1.get_pad("1").net = pcb_r1.get_pad("1").net = p1_net
pcb_j1.get_pad("2").net = pcb_r1.get_pad("2").net = p2_net

board.append(pcb.Track(start=pcb_j1.get_pad("1").position, end=pcb_r1.get_pad("1").position, width=0.5, layer=pcb.Layer.FCu, net=p1_net))
board.append(pcb.Track(start=pcb_j1.get_pad("2").position, end=pcb_r1.get_pad("2").position, width=0.5, layer=pcb.Layer.FCu, net=p2_net))

board.append(pcb.Rect(start=(0, 0), end=(76.2, 76.2), width=0.5, layer=pcb.Layer.EdgeCuts))

board.save(os.path.join(root, "project", "exampleproject.kicad_pcb"))
