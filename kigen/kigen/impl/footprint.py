from pathlib import Path
from typing import overload, runtime_checkable, Annotated, Optional, Protocol

from ..common import BaseTransform, BaseRotate, CoordinatePointList, Generator, Net, Property, StrokeDefinition, TextEffects, ToCoordinatePointList, Uuid, KIGEN_GENERATOR, KIGEN_VERSION
from ..node import Attr, ContainerNode, Node, NodeLoadSaveMixin, NEW_INSTANCE
from ..values import SymbolEnum, Pos2, ToPos2, ToVec2, ToVec3, Vec2, Vec3
from .. import sexpr, util

class Transform(BaseTransform):
    pass

class Rotate(BaseRotate):
    pass

class TextType(SymbolEnum):
    Reference = "reference"
    Value = "value"
    User = "user"

class TextLayer(Node):
    node_name = "layer"

    layer: Annotated[str, Attr.Positional]
    knockout: bool

    def __init__(
            self,
            layer: str,
            knockout: bool = False,
    ):
        super().__init__(locals())

class Text(Node):
    node_name = "fp_text"

    type: Annotated[TextType, Attr.Positional]
    text: Annotated[str, Attr.Positional]
    at: Annotated[Pos2, Attr.Transform]
    unlocked: bool
    layer: TextLayer
    hide: bool
    effects: TextEffects
    tstamp: Uuid

    def __init__(
            self,
            type: TextType,
            text: str,
            at: ToPos2,
            layer: str | TextLayer,
            unlocked: bool = False,
            hide: bool = False,
            effects: TextEffects = NEW_INSTANCE,
            tstamp: Uuid = NEW_INSTANCE
    ):
        super().__init__(locals())

class Line(Node):
    node_name = "fp_line"

    start: Annotated[Vec2, Attr.Transform]
    end: Annotated[Vec2, Attr.Transform]
    angle: Optional[float]
    layer: str
    stroke: StrokeDefinition
    tstamp: Uuid

    def __init__(
            self,
            start: ToVec2,
            end: ToVec2,
            stroke: float | StrokeDefinition,
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
    stroke: StrokeDefinition
    fill: Optional[FillMode]
    tstamp: Uuid

    def __init__(
            self,
            start: ToVec2,
            end: ToVec2,
            stroke: float | StrokeDefinition,
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
    stroke: StrokeDefinition
    fill: Optional[FillMode]
    tstamp: Uuid

    def __init__(
            self,
            center: ToVec2,
            radius: "float | ToVec2",
            stroke: float | StrokeDefinition,
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
    stroke: StrokeDefinition
    tstamp: Uuid

    @overload
    def __init__(
            self,
            *,
            start: ToVec2,
            mid: ToVec2,
            end: ToVec2,
            stroke: float | StrokeDefinition,
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
            stroke: float | StrokeDefinition,
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
            stroke: float | StrokeDefinition,
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
    stroke: StrokeDefinition
    fill: Optional[FillMode]
    tstamp: Uuid

    def __init__(
            self,
            pts: ToCoordinatePointList,
            stroke: float | StrokeDefinition,
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
            stroke: float | StrokeDefinition,
            layer: str,
            fill: Optional[FillMode] = None,
            tstamp: Uuid = NEW_INSTANCE,
    ) -> "Polygon":
        start = Vec2(start)
        end = Vec2(end)

        return Polygon(
            [
                (start.x, start.y),
                (end.x, start.y),
                (end.x, end.y),
                (start.x, end.y),
            ],
            stroke=stroke,
            layer=layer,
            fill=fill,
            tstamp=tstamp,
        )

class Bezier(Node):
    node_name = "fp_bezier"

    pts: CoordinatePointList
    layer: str
    stroke: StrokeDefinition
    tstamp: Uuid

    def __init__(
            self,
            pts: ToCoordinatePointList,
            stroke: float | StrokeDefinition,
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
        assert isinstance(expr, list)

        return LayerRef([
            s.name if isinstance(s, sexpr.Sym) else str(s)
            for s
            in expr
        ])

    def __repr__(self):
        return f"LayerRef({repr(self.layers)})"

class DrillDefinition(Node):
    node_name = "drill"

    oval: Annotated[bool, Attr.Positional]
    diameter: Annotated[Optional[float], Attr.Positional]
    width: Annotated[Optional[float], Attr.Positional]
    offset: Annotated[Optional[Vec2], Attr.Transform]

    def __init__(
            self,
            diameter: Optional[float] = None,
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
    at: Annotated[Pos2, Attr.Transform]
    locked: Annotated[bool, Attr.Bool.SymbolInList]
    size: Vec2
    drill: Optional[DrillDefinition]
    layers: LayerRef
    roundrect_rratio: Optional[float]
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
            roundrect_rratio: Optional[float] = None,
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

class Model(Node):
    node_name = "model"

    file: Annotated[str, Attr.Positional]
    hide: bool
    offset: Vec3
    scale: Vec3
    rotate: Vec3

    def __init__(
            self,
            file: str | Path,
            offset: ToVec3 = NEW_INSTANCE,
            scale: Optional[ToVec3] = None,
            rotate: ToVec3 = NEW_INSTANCE,
            hide: bool = False,
    ):
        if isinstance(file, Path):
            file = str(file)

        if scale is None:
            scale = Vec3(1, 1, 1)

        super().__init__(locals())

GraphicsItemTypes = (Arc, Circle, Line, Pad, Polygon, Rect, Rotate, Text, Transform)
Transform.child_types = GraphicsItemTypes
Rotate.child_types = GraphicsItemTypes

def _get_layer_name(n: Node) -> Optional[str]:
    if isinstance(n, Text):
        return n.layer.layer
    elif hasattr(n, "layer") and isinstance(n.layer, str):
        return n.layer
    else:
        return None

class BaseFootprint(ContainerNode):
    node_name = "footprint"

    layer: str
    descr: Optional[str]
    tags: Optional[str]
    attr: Optional[FootprintAttributes]

    def get_pad(self, number: str) -> Pad:
        pad = self.find_one(Pad, lambda p: p.number == number, recursive = True)
        if not pad:
            raise RuntimeError(f"Footprint does not have a pad with number '{number}'")

        return pad

    def delete_layer(self, layer: str) -> None:
        for c in self.find_all(Node, lambda n: _get_layer_name(n) == layer):
            c.detach()

class Footprint(BaseFootprint):
    child_types = GraphicsItemTypes + (Model, Property)

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

    def transform_pos(self, pos: ToPos2) -> Pos2:
        # Coordinates within footprints are relative to the footprint, except for rotation for some reason, so propagate only the rotation part

        if self.parent:
            return Pos2(pos).add_rotation(self.parent.transform_pos(self.at).r)
        else:
            return Pos2(pos).add_rotation(self.at.r)

class LibraryFootprint(BaseFootprint, NodeLoadSaveMixin):
    child_types = GraphicsItemTypes + (Model,)
    order_attrs = ("version", "generator")

    library_name: Annotated[str, Attr.Ignore]
    name: Annotated[str, Attr.Positional]
    tedit: Optional[Uuid]
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
        tedit: Optional[Uuid] = None,
        version: int = KIGEN_VERSION,
        generator: Generator = KIGEN_GENERATOR,
    ) -> None:
        self.library_name = library_name

        super().__init__(locals())

    def _set_path(self, path: Path) -> None:
        self.library_name = path.parent.stem

    @property
    def library_link(self) -> Optional[str]:
        return f"{self.library_name}:{self.name}"

class FootprintLibrary:
    path: Path

    def __init__(self, path: Path | str) -> None:
        path = Path(path)

        if not path.exists():
            raise FileNotFoundError(f"Library {path} does not exist.")

        self.path = Path(path)

    def load(self, name: str) -> LibraryFootprint:
        return LibraryFootprint.load(str(self.path / f"{name}.kicad_mod"))
