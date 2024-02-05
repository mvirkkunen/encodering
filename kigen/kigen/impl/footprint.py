from typing import Annotated, Optional

from ..common import BaseTransform, BaseRotate, Generator, ToProperties, Properties, Uuid, KIGEN_GENERATOR, KIGEN_VERSION
from ..node import Attr, ContainerNode, Node, NodeLoadSaveMixin, NEW_INSTANCE
from ..values import SymbolEnum, Pos2, ToVec2, Vec2

class Transform(BaseTransform):
    pass

class Rotate(BaseRotate):
    pass

class BaseLine(Node):
    start: Annotated[Vec2, Attr.Transform]
    end: Annotated[Vec2, Attr.Transform]
    layer: str
    width: float
    locked: bool

class Line(BaseLine):
    node_name = "fp_line"

    def __init__(
            self,
            start: ToVec2,
            end: ToVec2,
            layer: str,
            width: float,
            locked: bool = False,
    ) -> None:
        super().__init__(locals())

class RectFill(SymbolEnum):
    Solid = "solid"

class Rect(BaseLine):
    node_name = "fp_rect"

    fill: RectFill

    def __init__(
            self,
            start: ToVec2,
            end: ToVec2,
            layer: str,
            width: float,
            fill: Optional[RectFill] = None,
            locked: bool = False,
    ) -> None:
        super().__init__(locals())

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

GraphicsItemTypes = (Line, Rect, Transform, Rotate)
Transform.child_types = GraphicsItemTypes
Rotate.child_types = GraphicsItemTypes

class BaseFootprint(ContainerNode):
    node_name = "footprint"
    child_types = GraphicsItemTypes

    layer: str
    descr: Optional[str]
    tags: Optional[str]
    properties: Properties
    attr: Optional[FootprintAttributes]

class Footprint(BaseFootprint):
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
        properties: ToProperties = {},
        attr: Optional[FootprintAttributes] = None,
        tstamp: Uuid = NEW_INSTANCE,
        children: Optional[list] = None,
    ) -> None:
        super().__init__(locals())

class FootprintFile(BaseFootprint, NodeLoadSaveMixin):
    order_attrs = ("version", "generator")

    library_name: Annotated[str, Attr.Ignore]
    name: Annotated[str, Attr.Positional]
    version: int
    generator: Generator

    def __init__(
        self,
        library_name: str,
        name: str,
        layer: str,
        descr: Optional[str] = None,
        tags: Optional[str] = None,
        properties: ToProperties = NEW_INSTANCE,
        attr: Optional[FootprintAttributes] = None,
        version: int = KIGEN_VERSION,
        generator: Generator = KIGEN_GENERATOR,
    ) -> None:
        self.library_name = library_name

        super().__init__(locals())
