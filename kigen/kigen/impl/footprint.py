from pathlib import Path
from typing import overload, Annotated, Optional

from ..common import BaseTransform, BaseRotate, CoordinatePointList, Generator, Net, Property, TextEffects, ToCoordinatePointList, Uuid, KIGEN_GENERATOR, KIGEN_VERSION
from ..node import Attr, ContainerNode, Node, NodeLoadSaveMixin, NEW_INSTANCE
from ..values import SymbolEnum, Pos2, ToPos2, ToVec2, Vec2
from .. import sexpr, util

class Transform(BaseTransform):
    pass

class Rotate(BaseRotate):
    pass

class TextLayer(Node):
    node_name = "layer"

    layer: str
    knockout: bool

    def __init__(
            self,
            layer: str,
            knockout: bool = False,
    ):
        super.__init__(locals())

class Text(Node):
    node_name = "fp_text"

    text: Annotated[str, Attr.Positional]
    at: Annotated[Pos2, Attr.Transform]
    effects: TextEffects
    tstamp: Uuid

    def __init__(
            self,
            text: str,
            at: ToPos2,
            layer: str | TextLayer,
            effects: TextEffects = NEW_INSTANCE,
            tstamp: Uuid = NEW_INSTANCE
    ):
        if isinstance(layer, str):
            layer = TextLayer(layer)

        super().__init__(locals())

class Line(Node):
    node_name = "fp_line"

    start: Annotated[Vec2, Attr.Transform]
    end: Annotated[Vec2, Attr.Transform]
    angle: Optional[float]
    layer: str
    width: float
    tstamp: Uuid

    def __init__(
            self,
            start: ToVec2,
            end: ToVec2,
            width: float,
            layer: str,
            angle: Optional[float] = None,
            tstamp: Uuid = NEW_INSTANCE,
    ):
        super().__init__(locals())

class FillMode(SymbolEnum):
    None_ = "none"
    Solid = "solid"

class Rect(Node):
    node_name = "fp_rect"

    start: Annotated[Vec2, Attr.Transform]
    end: Annotated[Vec2, Attr.Transform]
    layer: str
    width: float
    fill: Optional[FillMode]
    tstamp: Uuid

    def __init__(
            self,
            start: ToVec2,
            end: ToVec2,
            width: float,
            layer: str,
            fill: Optional[FillMode] = None,
            tstamp: Uuid = NEW_INSTANCE,
    ):
        super().__init__(locals())

class Circle(Node):
    node_name = "fp_circle"

    center: Annotated[Vec2, Attr.Transform]
    end: Annotated[Vec2, Attr.Transform]
    layer: str
    width: float
    fill: Optional[FillMode]
    tstamp: Uuid

    def __init__(
            self,
            center: ToVec2,
            radius: "float | ToVec2",
            width: float,
            layer: str,
            fill: Optional[FillMode] = None,
            tstamp: Uuid = NEW_INSTANCE,
    ):
        if isinstance(radius, (int, float)):
            radius = Vec2(center) + Vec2(radius, 0)

        end = radius

        super().__init__(locals())

class Arc(Node):
    node_name = "fp_arc"

    start: Annotated[Vec2, Attr.Transform]
    mid: Annotated[Vec2, Attr.Transform]
    end: Annotated[Vec2, Attr.Transform]
    layer: str
    width: float
    tstamp: Uuid

    @overload
    def __init__(
            self,
            *,
            start: ToVec2,
            mid: ToVec2,
            end: ToVec2,
            width: float,
            layer: str,
    ) -> None:
        """
        :param start: Start point of the arc.
        :param mid: Mid point of the arc.
        :param end: End point of the arc.
        :param stroke: Stroke style.
        :param fill: Fill style.
        """
        ...

    @overload
    def __init__(
            self,
            *,
            center: ToVec2,
            radius: float,
            start_angle: float,
            end_angle: float,
            width: float,
            layer: str,
    ) -> None:
        """
        :param center: Center point of the circle that defines the arc.
        :param radius: Radius of the arg.
        :param start: Start angle of the arg.
        :param end: End angle of the arg.
        :param stroke: Stroke style.
        :param fill: Fill style.
        """
        ...

    def __init__(
            self,
            *,
            start: Optional[ToVec2] = None,
            mid: Optional[ToVec2] = None,
            end: Optional[ToVec2] = None,
            center: Optional[ToVec2] = None,
            radius: Optional[float] = None,
            start_angle: Optional[float] = None,
            end_angle: Optional[float] = None,
            width: float,
            layer: str,
            tstamp: Uuid = NEW_INSTANCE,
    ) -> None:
        """
        To create a new arc, define either (start, mid, end) or (center, radius, start_angle, end_angle).

        :param start: Start point of the arc.
        :param mid: Mid point of the arc.
        :param end: End point of the arc.
        :param center: Center point of the circle that defines the arc.
        :param radius: Radius of the arg.
        :param start: Start angle of the arg.
        :param end: End angle of the arg.
        :param stroke: Stroke (outline) style.
        :param fill: Fill style.
        """

        start, mid, end = util.calculate_arc(locals())

        super().__init__(locals())

class Polygon(Node):
    node_name = "fp_poly"

    pts: CoordinatePointList
    layer: str
    width: float
    fill: Optional[FillMode]
    tstamp: Uuid

    def __init__(
            self,
            pts: ToCoordinatePointList,
            width: float,
            layer: str,
            fill: Optional[FillMode] = None,
            tstamp: Uuid = NEW_INSTANCE,
    ):
        super().__init__(locals())
        self.pts._set_parent(self)

    @staticmethod
    def rect(
            start: ToVec2,
            end: ToVec2,
            width: float,
            layer: str,
            fill: Optional[FillMode] = None,
            tstamp: Uuid = NEW_INSTANCE,
    ):
        start = Vec2(start)
        end = Vec2(end)

        return Polygon(
            [
                (start.x, start.y),
                (end.x, start.y),
                (end.x, end.y),
                (start.x, end.y),
            ],
            width=width,
            layer=layer,
            fill=fill,
            tstamp=tstamp,
        )

class Bezier(Node):
    node_name = "fp_bezier"

    pts: CoordinatePointList
    layer: str
    width: float
    tstamp: Uuid

    def __init__(
            self,
            pts: ToCoordinatePointList,
            width: float,
            layer: str,
            tstamp: Uuid = NEW_INSTANCE,
    ):
        super().__init__(locals())

    def validate(self) -> None:
        super().validate()

        if len(self.pts) != 4:
            raise ValueError("Bezier must have exactly 4 points")

class FootprintType(SymbolEnum):
    Smd = "smd"
    ThroughHole = "through_hole"

class FootprintAttributes(Node):
    node_name = "attr"

    type: Annotated[FootprintType, Attr.Positional]
    board_only: bool
    exclude_from_pos_files: bool
    exclude_from_bom: bool

    def __init__(
            self,
            type: FootprintType,
            board_only: bool = False,
            exclude_from_pos_files: bool = False,
            exclude_from_bom: bool = False
    ) -> None:
        super().__init__(locals())

class PadType(SymbolEnum):
    ThruHole = "thru_hole"
    Smd = "smd"
    Connect = "connect"
    NpThruHole = "np_thru_hole"

class PadShape(SymbolEnum):
    Circle = "circle"
    Rect = "rect"
    Oval = "oval"
    Trapezoid = "trapezoid"
    RoundRect = "roundrect"
    Custom = "custom"

class LayerRef:
    node_name = "layers"

    layers: list[str]

    def __init__(
            self,
            layers: str | list[str],
    ):
        self.layers = [layers] if isinstance(layers, str) else layers

    def to_sexpr(self) -> list[sexpr.SExpr]:
        return [sexpr.Sym(l) for l in self.layers]

    @classmethod
    def from_sexpr(cls, expr: sexpr.SExpr) -> "LayerRef":
        return LayerRef([
            s.name if isinstance(s, sexpr.Sym) else str(s)
            for s
            in expr
        ])

class DrillDefinition(Node):
    node_name = "drill"

    oval: Annotated[bool, Attr.Positional]
    diameter: Annotated[float, Attr.Positional]
    width: Annotated[Optional[float], Attr.Positional]
    offset: Annotated[Optional[Vec2], Attr.TransformRelativeRotation]

    def __init__(
            self,
            diameter: float,
            width: Optional[float] = None,
            oval: bool = False,
            offset: Optional[ToVec2] = None,
    ):
        super().__init__(locals())

class Pad(ContainerNode):
    child_types = ()
    node_name = "pad"

    number: Annotated[str, Attr.Positional]
    type: Annotated[PadType, Attr.Positional]
    shape: Annotated[PadShape, Attr.Positional]
    at: Annotated[Pos2, Attr.Transform] # TODO: Rotation when not actually transformed!!
    locked: Annotated[bool, Attr.Bool.SymbolInList]
    size: Vec2
    drill: Optional[DrillDefinition]
    layers: LayerRef
    net: Optional[Net]
    tstamp: Uuid

    def __init__(
            self,
            number: str,
            type: PadType,
            shape: PadShape,
            at: ToPos2,
            size: "ToVec2 | float | int",
            layers: LayerRef | list[str],
            drill: Optional[DrillDefinition | float | int] = None,
            net: Optional[Net] = None,
            locked: bool = False,
            tstamp: Uuid = NEW_INSTANCE,
    ):
        if isinstance(size, (float, int)):
            size = Vec2(size, size)

        if isinstance(layers, list):
            layers = LayerRef(layers)

        if isinstance(drill, (float, int)):
            drill = DrillDefinition(drill)

        super().__init__(locals())

    @property
    def position(self) -> Pos2:
        if not isinstance(self.parent, Footprint):
            return self.at

        parent_at = self.parent.transform_pos(self.parent.at)
        return parent_at + self.at.add_rotation(parent_at.r)

GraphicsItemTypes = (Arc, Circle, Line, Pad, Polygon, Rect, Rotate, Transform)
Transform.child_types = GraphicsItemTypes
Rotate.child_types = GraphicsItemTypes

class BaseFootprint(ContainerNode):
    node_name = "footprint"
    child_types = GraphicsItemTypes

    layer: str
    descr: Optional[str]
    tags: Optional[str]
    attr: Optional[FootprintAttributes]

    def get_pad(self, number: str) -> Pad:
        pad = self.find_one(Pad, lambda p: p.number == number)
        if not pad:
            raise RuntimeError(f"Footprint does not have a pad with number '{number}'")

        return pad

class Footprint(BaseFootprint):
    child_types = GraphicsItemTypes + (Property,)

    library_link: Annotated[Optional[str], Attr.Positional]
    tstamp: Optional[Uuid]
    at: Annotated[Pos2, Attr.Transform]
    path: Optional[str]

    def __init__(
        self,
        library_link: str,
        layer: str,
        at: Pos2,
        path: Optional[str] = None,
        descr: Optional[str] = None,
        tags: Optional[str] = None,
        attr: Optional[FootprintAttributes] = None,
        tstamp: Uuid = NEW_INSTANCE,
        children: Optional[list] = None,
    ) -> None:
        super().__init__(locals())

    def get_pad_position(self, number: str) -> Pos2:
        at = self.transform_pos(self.at)
        return at + self.get_pad(number).at.add_rotation(at.r)

class LibraryFootprint(BaseFootprint, NodeLoadSaveMixin):
    child_types = GraphicsItemTypes
    order_attrs = ("version", "generator")

    library_name: Annotated[str, Attr.Ignore]
    name: Annotated[str, Attr.Positional]
    tedit: Uuid
    version: int
    generator: Generator

    def __init__(
        self,
        library_name: str,
        name: str,
        layer: str,
        descr: Optional[str] = None,
        tags: Optional[str] = None,
        attr: Optional[FootprintAttributes] = None,
        tedit: Uuid = NEW_INSTANCE,
        version: int = KIGEN_VERSION,
        generator: Generator = KIGEN_GENERATOR,
    ) -> None:
        self.library_name = library_name

        super().__init__(locals())

    def _set_path(self, path: Path) -> None:
        self.library_name = path.parent.stem

class FootprintLibrary:
    path: Path

    def __init__(self, path: Path | str) -> None:
        path = Path(path)

        if not path.exists():
            raise FileNotFoundError(f"Library {path} does not exist.")

        self.path = Path(path)

    def load(self, name: str) -> LibraryFootprint:
        return LibraryFootprint.load(str(self.path / f"{name}.kicad_mod"))
