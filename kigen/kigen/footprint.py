import math
from typing import Optional

from .common_nodes import *
from .values import *
from .util import reorder_dict

class GraphicsItem(Node):
    pass

class Group(NodeGroup):
    pass

Group.child_types = (GraphicsItem, Group)

class BaseLine(GraphicsItem):
    start: Annotated[Vec2, Transform]
    end: Annotated[Vec2, Transform]
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
            parent: Node = None
        ):
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
            layer: Layer,
            width: float,
            fill: RectFill = None,
            locked: bool = False,
            parent: Node = None
        ):
        super().__init__(locals())

class FootprintType(SymbolEnum):
    Smd = "smd"
    ThroughHole = "through_hole"

class FootprintAttributes(Node):
    node_name = "attr"

    type: Annotated[FootprintType, Positional]
    board_only: bool
    exclude_from_pos_files: bool
    exclude_from_bom: bool

    def __init__(
            self,
            type: FootprintType,
            board_only: bool = False,
            exclude_from_pos_files: bool = False,
            exclude_from_bom: bool = False):
        super().__init__(locals())

class BaseFootprint(ContainerNode):
    node_name = "footprint"
    child_types = (GraphicsItem, Group)

    layer: str
    descr: Optional[str]
    tags: Optional[str]
    properties: Properties
    attr: Optional[FootprintAttributes]

    def __init__(self, attrs):
        super().__init__(attrs)

class Footprint(BaseFootprint):
    library_link: Annotated[Optional[str], Positional]
    tstamp: Optional[Uuid]
    at: Annotated[Pos2, Transform]
    path: str

    def __init__(
        self,
        library_link: str,
        layer: Layer,
        at: Pos2,
        path: str,
        descr: str = None,
        tags: str = None,
        properties: ToProperties = {},
        attr: FootprintAttributes = None,
        tstamp: Uuid = Uuid(),
    ):
        super().__init__(locals())

class FootprintFile(BaseFootprint):
    order_attrs = ("version", "generator")

    name: Annotated[str, Positional]
    version: int
    generator: Generator

    def __init__(
        self,
        name: str,
        layer: str,
        descr: str = None,
        tags: str = None,
        properties: ToProperties = {},
        attr: FootprintAttributes = None,
        version: int = KIGEN_VERSION,
        generator: Generator = KIGEN_GENERATOR,
    ):
        super().__init__(locals())

