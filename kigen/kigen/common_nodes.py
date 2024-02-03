import math

from .node import *
from .values import *

class NodeGroup(ContainerNode):
    at: Pos2

    def __init__(
            self,
            at: Pos2,
            children: [Node] = None,
            parent: Node = None):
        super().__init__(locals())

    def to_sexpr(self):
        r = []
        for child in self.children:
            r += child.to_sexpr()
        return r

    def transform(self, pos: Pos2) -> Pos2:
        pos = Pos2(pos)
        at = super().transform(self.at)

        if at.r != 0:
            s = math.sin(at.r / 180 * math.pi)
            c = math.cos(at.r / 180 * math.pi)

            return Pos2(
                at.x + c * pos.x - s * pos.y,
                at.y + s * pos.x + c * pos.y,
                pos.r + at.r,
            )
        else:
            return Pos2(at.x + pos.x, at.y + pos.y, pos.r)

class PaperSize(SymbolEnum):
    A0 = "A0"
    A1 = "A1"
    A2 = "A2"
    A3 = "A3"
    A4 = "A4"
    A5 = "A5"
    A = "A"
    B = "B"
    C = "C"
    D = "D"
    E = "E"

class PageSettings(Node):
    node_name = "paper"

    width: Annotated[Optional[float], Positional]
    height: Annotated[Optional[float], Positional]
    paper_size: Annotated[Optional[PaperSize], Positional]

    def __init__(
            self,
            paper_size: PaperSize = None,
            width: float = None,
            height: float = None):
        if not (
                (width is not None and height is not None and paper_size is None)
                or (width is None and height is None and paper_size is not None)):
            raise ValueError("PageSettings must define either width and height, or paper_size, but not both.")

        super().__init__(locals())

ToProperties: TypeAlias = "Properties | dict[str, str]"

class Properties(dict, Node):
    def __init__(self, init: ToProperties):
        super().__init__(init)

    def to_sexpr(self):
        return [
            [Symbol("property"), k, v]
            for k, v
            in self.items()
        ]

