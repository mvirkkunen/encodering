from enum import Flag, auto
from typing import Annotated, Iterable, Optional, Self

from . import sexpr
from .node import *
from .values import *

class Generator(SymbolEnum):
    PcbNew = "pbcnew"
    EeSchema = "eeschema"
    KicadSymbolEditor = "kicad_symbol_editor"
    Kigen = "kigen"

KIGEN_VERSION = 20230121
KIGEN_GENERATOR = Generator.Kigen

class BaseTransform(ContainerNode):
    node_name = None

    at: Pos2

    def __init__(
            self,
            at: Pos2,
            children: Optional[list[Node]] = None,
            parent: Optional[Node] = None):
        super().__init__(locals())

    def transform(self, pos: ToPos2) -> Pos2:
        pos = Pos2(pos)
        at = super().transform(self.at)
        return at + pos.rotate(at.r)

    def to_sexpr(self) -> list[list[sexpr.SExpr]]:
        r: list[list[sexpr.SExpr]] = []
        for child in iter(self):
            r += child.to_sexpr()
        return r

class BaseRotate(ContainerNode):
    node_name = None

    angle: float

    def __init__(
            self,
            angle: float,
            children: Optional[list[Node]] = None,
            parent: Optional[Node] = None):
        super().__init__(locals())

    def transform(self, pos: ToPos2) -> Pos2:
        return Pos2(pos).rotate(self.angle)

    def to_sexpr(self) -> list[list[sexpr.SExpr]]:
        r: list[list[sexpr.SExpr]] = []
        for child in iter(self):
            r += child.to_sexpr()
        return r

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

    width: Annotated[Optional[float], Attr.Positional]
    height: Annotated[Optional[float], Attr.Positional]
    paper_size: Annotated[Optional[PaperSize], Attr.Positional]

    def __init__(
            self,
            paper_size: Optional[PaperSize] = None,
            width: Optional[float] = None,
            height: Optional[float] = None
    ) -> None:
        super().__init__(locals())

    def validate(self) -> None:
        if not (
                (self.width is not None and self.height is not None and self.paper_size is None)
                or (self.width is None and self.height is None and self.paper_size is not None)):
            raise ValueError("PageSettings must define either width and height, or paper_size, but not both.")

ToProperties: TypeAlias = "Properties | dict[str, str]"

class Properties(dict[str, str], Node):
    def __init__(self, init: ToProperties):
        super().__init__(init)

    @classmethod
    def from_sexpr(self, expr: sexpr.SExpr) -> "Properties":
        assert isinstance(expr, list)

        r: dict[str, str] = {}
        for e in expr:
            assert isinstance(e, list) and isinstance(e[0], str) and isinstance(e[1], str)
            r[e[0]] = e[1]

        return Properties(r)

    def to_sexpr(self) -> list[list[sexpr.SExpr]]:
        return [
            [sexpr.Sym("property"), k, v]
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
    ) -> None:
        super().__init__(locals())

class TextJustify(Flag):
    Left = auto()
    Right = auto()
    Top = auto()
    Bottom = auto()
    Mirror = auto()

    def to_sexpr(self) -> list[sexpr.SExpr]:
        r: list[sexpr.SExpr] = []

        if TextJustify.Left in self:
            r.append(sexpr.Sym("left"))
        elif TextJustify.Right in self:
            r.append(sexpr.Sym("right"))

        if TextJustify.Top in self:
            r.append(sexpr.Sym("top"))
        elif TextJustify.Bottom in self:
            r.append(sexpr.Sym("bottom"))

        if TextJustify.Mirror in self:
            r.append(sexpr.Sym("mirror"))

        return r

    @classmethod
    def from_sexpr(cls, expr: sexpr.SExpr) -> "TextJustify":
        return TextJustify.Left # TODO

class TextEffects(Node):
    node_name = "effects"

    font: Font
    justify: Optional[TextJustify]
    hide: bool

    def __init__(
            self,
            font: Font = NEW_INSTANCE,
            justify: Optional[TextJustify] = None,
            hide: bool = False,
    ) -> None:
        super().__init__(locals())

class StrokeType(SymbolEnum):
    Default = "default"
    Dash = "dash"
    DashDot = "dash_dot"
    DashDotDot = "dash_dot_dot"
    Dot = "dot"
    Solid = "solid"

class StrokeDefinition(Node):
    node_name = "stroke"

    width: float
    type: StrokeType
    color: Optional[Rgba]

    def __init__(
            self,
            width: float = 0,
            type: StrokeType = StrokeType.Default,
            color: Optional[Rgba] = None,
    ) -> None:
        super().__init__(locals())

class FillType(SymbolEnum):
    None_ = "none"
    Outline = "outline"
    Background = "background"

class FillDefinition(Node):
    node_name = "fill"

    type: FillType

    def __init__(
            self,
            type: FillType = FillType.None_,
    ) -> None:
        super().__init__(locals())

class CoordinatePoint(Node):
    node_name = "xy"

    x: Annotated[float, Attr.Positional]
    y: Annotated[float, Attr.Positional]

    def __init__(
            self,
            x: float,
            y: float,
    ) -> None:
        super().__init__(locals())

class CoordinatePointList(ContainerNode):
    child_types = (CoordinatePoint,)
    node_name = "pts"

    def __init__(
            self,
            children: "Optional[Iterable[ToVec2 | CoordinatePoint]]" = None,
    ) -> None:
        if children:
            new_children = []
            for c in children:
                if isinstance(c, CoordinatePoint):
                    new_children.append(c)
                else:
                    vec = Vec2(c)
                    new_children.append(CoordinatePoint(vec.x, vec.y))
            children = new_children

        super().__init__(locals())
