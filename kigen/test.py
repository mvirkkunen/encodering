#!/usr/bin/env python3

from kigen.values import *
import kigen.footprint as fp
import kigen.symbol as sym
import kigen.schematic as sch
import kigen.board as pcb

f = fp.Footprint("spöörsh", path="", layer=Layer.FCu, at=(2, 2))
f.properties["vaca"] = "pollo"
f.properties["perro"] = "cocodrilo"

f.append(fp.Line(
    start=(0, 0),
    end=(5, 10),
    layer=Layer.FCu,
    width=1,
))

xf = fp.Transform(at=Pos2(0, 0, 1), parent=f)

xf.append(fp.Line(
    start=(5, 10),
    end=(10, 10),
    layer=Layer.FCu,
    width=2,
))

#board = pcb.BoardFile(layers=2)
#print(board.serialize())

#print(fp.serialize())


connectors = sym.SymbolLibrary.load("/usr/share/kicad/symbols/Connector.kicad_sym")
connector = connectors.get("Conn_01x04_Pin")

#print(connectors.serialize())

schematic = sch.SchematicFile()

conn = schematic.place_symbol(
    connector,
    "J1",
    at=(25.4, 25.4, 90),
)

for pin in conn.pins:
    pin_pos = conn.get_pin_position(pin.number)
    label_pos = pin_pos + Pos2(25.4, 0)

    schematic.append(sch.Wire([pin_pos, label_pos]))
    schematic.append(sch.GlobalLabel(f"Conn_{pin.number}", at=label_pos, shape=sch.LabelShape.Bidirectional))

#print(schematic.serialize())

schematic.save("../testproject/testproject/testproject.kicad_sch")

import kigen
