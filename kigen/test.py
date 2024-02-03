from kigen import *
from kigen.footprint import *
from kigen.board import *

fp = Footprint("spöörsh", path="", layer=Layer.FCu, at=(2, 2))
fp.properties["vaca"] = "pollo"
fp.properties["perro"] = "cocodrilo"

fp.append(Line(
    start=(0, 0),
    end=(5, 10),
    layer=Layer.FCu,
    width=1,
))

gr = Group(at=Pos2(0, 0, 1), parent=fp)

gr.append(Line(
    start=(5, 10),
    end=(10, 10),
    layer=Layer.FCu,
    width=2,
))

board = BoardFile(layers=2)
print(board.serialize())

print(fp.serialize())
