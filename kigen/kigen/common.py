from enum import Flag, auto
from typing import Annotated, Iterable, Optional, Self

from . import sexpr
from .node import *
from .values import *

class Generator(SymbolEnum):
    PcbNew = "pcbnew"
    EeSchema = "eeschema"
    KicadSymbolEditor = "kicad_symbol_editor"
    Kigen = "kigen"

KIGEN_VERSION = 20230121
KIGEN_GENERATOR = Generator.Kigen

class Layer:
    FCu = "F.Cu"
    In1Cu = "In1.Cu"
    In2Cu = "In2.Cu"
    In3Cu = "In3.Cu"
    In4Cu = "In4.Cu"
    In5Cu = "In5.Cu"
    In6Cu = "In6.Cu"
    In7Cu = "In7.Cu"
    In8Cu = "In8.Cu"
    In9Cu = "In9.Cu"
    In10Cu = "In10.Cu"
    In11Cu = "In11.Cu"
    In12Cu = "In12.Cu"
    In13Cu = "In13.Cu"
    In14Cu = "In14.Cu"
    In15Cu = "In15.Cu"
    In16Cu = "In16.Cu"
    In17Cu = "In17.Cu"
    In18Cu = "In18.Cu"
    In19Cu = "In19.Cu"
    In20Cu = "In20.Cu"
    In21Cu = "In21.Cu"
    In22Cu = "In22.Cu"
    In23Cu = "In23.Cu"
    In24Cu = "In24.Cu"
    In25Cu = "In25.Cu"
    In26Cu = "In26.Cu"
    In27Cu = "In27.Cu"
    In28Cu = "In28.Cu"
    In29Cu = "In29.Cu"
    In30Cu = "In30.Cu"
    BCu = "B.Cu"
    BAdhes = "B.Adhes"
    FAdhes = "F.Adhes"
    BPaste = "B.Paste"
    FPaste = "F.Paste"
    BSilkS = "B.SilkS"
    FSilkS = "F.SilkS"
    BMask = "B.Mask"
    FMask = "F.Mask"
    DwgsUser = "Dwgs.User"
    CmtsUser = "Cmts.User"
    Eco1User = "Eco1.User"
    Eco2User = "Eco2.User"
    EdgeCuts = "Edge.Cuts"
    Margin = "Margin"
    FCrtYd = "F.CrtYd"
    BCrtYd = "B.CrtYd"
    FFab = "F.Fab"
    BFab = "B.Fab"
    User1 = "User.1"
    User2 = "User.2"
    User3 = "User.3"
    User4 = "User.4"
    User5 = "User.5"
    User6 = "User.6"
    User7 = "User.7"
    User8 = "User.8"
    User9 = "User.9"

    AllCu = "*.Cu"
    AllMask = "*.Mask"

    def flip(l: str) -> str:
        if l.startswith("F."):
            return "B." + l[2:]
        elif l.startswith("B."):
            return "F." + l[2:]
        else:
            return l

class BaseTransform(ContainerNode):
    node_name = None

    at: Pos2

    def __init__(
            self,
            at: ToPos2,
            children: Optional[list[Node]] = None,
            parent: Optional[Node] = None):
        super().__init__(locals())

    def transform_pos(self, pos: ToPos2) -> Pos2:
        pos = Pos2(pos)
        at = super().transform_pos(self.at)
        return at + pos

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

    def transform_pos(self, pos: ToPos2) -> Pos2:
        pos = Pos2(pos)
        at = super().transform_pos(Pos2(0, 0, self.angle))
        return at + pos

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

class Property(Node):
    node_name = "property"

    name: Annotated[str, Attr.Positional]
    value: Annotated[str, Attr.Positional]

    def __init__(
            self,
            name: str,
            value: str,
    ) -> None:
        super().__init__(locals())

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

    at: Annotated[Vec2, Attr.Positional(2), Attr.Transform]

    def __init__(
            self,
            at: ToVec2,
    ) -> None:
        super().__init__(locals())

ToCoordinatePointList: TypeAlias = "Iterable[ToVec2 | CoordinatePoint]"

class CoordinatePointList(ContainerNode):
    child_types = (CoordinatePoint,)
    node_name = "pts"

    def __init__(
            self,
            children: Optional[ToCoordinatePointList] = None,
    ) -> None:
        if children:
            new_children = []
            for c in children:
                if isinstance(c, CoordinatePoint):
                    new_children.append(c)
                else:
                    new_children.append(CoordinatePoint(c))
            children = new_children

        super().__init__(locals())

class Net(Node):
    node_name = "net"

    ordinal: Annotated[int, Attr.Positional]
    name: Annotated[str, Attr.Positional]

    def __init__(
            self,
            ordinal: int,
            name: str
    ) -> None:
        """
        Defines a net.

        ordinal: The net ID, also defines net order
        name: Name of the net
        """

        super().__init__(locals())

    def __int__(self) -> int:
        return self.ordinal

    def __repr__(self) -> str:
        return f"Net({self.ordinal}, '{self.name}')"
