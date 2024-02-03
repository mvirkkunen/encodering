import math
from enum import Flag, auto

from .node import *
from .values import *

class Generator(SymbolEnum):
    Kigen = "kigen"
    KicadSymbolEditor = "kicad_symbol_editor"

KIGEN_VERSION = 20211014
KIGEN_GENERATOR = Generator.Kigen

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

        print(at, self.at, pos.rotate(at.r))
        return at + pos.rotate(at.r)
        #if at.r != 0:
            #s = math.sin(at.r / 180 * math.pi)
            #c = math.cos(at.r / 180 * math.pi)

            #return Pos2(
            #    at.x + c * pos.x - s * pos.y,
            #    at.y + s * pos.x + c * pos.y,
            #    pos.r + at.r,
            #)
        #else:
        #    return Pos2(at.x + pos.x, at.y + pos.y, pos.r)

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

class Properties(dict[str, str], Node):
    def __init__(self, init: ToProperties):
        super().__init__(init)

    @classmethod
    def from_sexpr(self, e):
        return Properties({v[0]: v[1] for v in e})

    def to_sexpr(self):
        return [
            [Sym("property"), k, v]
            for k, v
            in self.items()
        ]

class Font(Node):
    node_name = "font"

    face: Optional[str]
    size: Vec2
    thickness: Optional[float]
    bold: bool
    italic: bool
    line_spacing: Optional[float]

    def __init__(
            self,
            face: Optional[str] = None,
            size: Vec2 = Vec2(1.27, 1.27),
            thickness: Optional[float] = None,
            bold: bool = False,
            italic: bool = False,
            line_spacing: Optional[float] = None,
    ):
        super().__init__(locals())

class TextJustify(Flag):
    Left = auto()
    Right = auto()
    Top = auto()
    Bottom = auto()
    Mirror = auto()

    def to_sexpr(self):
        r = []

        if TextJustify.Left in self:
            r.append(Sym("left"))
        elif TextJustify.Right in self:
            r.append(Sym("right"))

        if TextJustify.Top in self:
            r.append(Sym("top"))
        elif TextJustify.Bottom in self:
            r.append(Sym("bottom"))

        if TextJustify.Mirror in self:
            r.append(Sym("mirror"))

        return r

    @classmethod
    def from_sexpr(cls, e):
        return TextJustify.Left # TODO

class TextEffects(Node):
    node_name = "text_effects"

    font: Font
    justify: Optional[TextJustify]
    hide: bool

    def __init__(
            self,
            font: Font = Font(),
            justify: Optional[TextJustify] = None,
            hide: bool = False,
    ):
        super().__init__(locals())
