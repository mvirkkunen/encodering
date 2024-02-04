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

library = sym.SymbolLibFile.parse("""(kicad_symbol_lib (version 20220914) (generator kicad_symbol_editor)
  (symbol "4P2C" (pin_names (offset 1.016)) (in_bom yes) (on_board yes)
    (property "Reference" "J" (at -5.08 8.89 0)
      (effects (font (size 1.27 1.27)) (justify right))
    )
    (property "Value" "4P2C" (at 2.54 8.89 0)
      (effects (font (size 1.27 1.27)) (justify left))
    )
    (property "Footprint" "" (at 0 1.27 90)
      (effects (font (size 1.27 1.27)) hide)
    )
    (property "Datasheet" "~" (at 0 1.27 90)
      (effects (font (size 1.27 1.27)) hide)
    )
    (property "ki_keywords" "4P2C RJ socket connector" (at 0 0 0)
      (effects (font (size 1.27 1.27)) hide)
    )
    (property "ki_description" "RJ connector, 4P2C (4 positions 2 connected)" (at 0 0 0)
      (effects (font (size 1.27 1.27)) hide)
    )
    (property "ki_fp_filters" "4P2C*" (at 0 0 0)
      (effects (font (size 1.27 1.27)) hide)
    )
    (symbol "4P2C_0_1"
      (polyline
        (pts
          (xy -6.35 -0.635)
          (xy -5.08 -0.635)
          (xy -5.08 -0.635)
        )
        (stroke (width 0) (type default))
        (fill (type none))
      )
      (polyline
        (pts
          (xy -6.35 0.635)
          (xy -5.08 0.635)
          (xy -5.08 0.635)
        )
        (stroke (width 0) (type default))
        (fill (type none))
      )
      (polyline
        (pts
          (xy -6.35 1.905)
          (xy -5.08 1.905)
          (xy -5.08 1.905)
        )
        (stroke (width 0) (type default))
        (fill (type none))
      )
      (polyline
        (pts
          (xy -6.35 3.175)
          (xy -5.08 3.175)
          (xy -5.08 3.175)
        )
        (stroke (width 0) (type default))
        (fill (type none))
      )
      (polyline
        (pts
          (xy -6.35 -3.175)
          (xy -6.35 5.715)
          (xy -1.27 5.715)
          (xy 3.81 5.715)
          (xy 3.81 4.445)
          (xy 5.08 4.445)
          (xy 5.08 3.175)
          (xy 6.35 3.175)
          (xy 6.35 -0.635)
          (xy 5.08 -0.635)
          (xy 5.08 -1.905)
          (xy 3.81 -1.905)
          (xy 3.81 -3.175)
          (xy -6.35 -3.175)
          (xy -6.35 -3.175)
        )
        (stroke (width 0) (type default))
        (fill (type none))
      )
      (rectangle (start 7.62 7.62) (end -7.62 -5.08)
        (stroke (width 0.254) (type default))
        (fill (type background))
      )
    )
    (symbol "4P2C_1_1"
      (pin passive line (at 10.16 0 180) (length 2.54)
        (name "~" (effects (font (size 1.27 1.27))))
        (number "1" (effects (font (size 1.27 1.27))))
      )
      (pin passive line (at 10.16 2.54 180) (length 2.54)
        (name "~" (effects (font (size 1.27 1.27))))
        (number "2" (effects (font (size 1.27 1.27))))
      )
    )
  )
)""")

print(library.serialize())

connector = library.get("4P2C")

test = sch.SchematicFile()
test.place(
    connector,
    "J1",
    (11, 12, 90),
)

print(test.serialize())
print(Pos2((11, 12, 13)))
