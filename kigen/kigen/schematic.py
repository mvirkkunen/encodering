from .common_nodes import *

class Junction(Node):
    node_name = "junction"

    at: Vec2
    diameter: float
    color: Rgba
    uuid: Uuid

    def __init__(
            self,
            at: Vec2,
            diameter: float = 0,
            color: Rgba = Rgba(),
            uuid: Uuid = Uuid()):
        super().__init__(locals())

class NoConnect(Node):
    node_name = "no_connect"

    at: Vec2
    uuid: Uuid

    def __init__(
            self,
            at: Vec2,
            uuid: Uuid = Uuid()):
        super().__init__(locals())

class LabelShape(SymbolEnum):
    Input = "input"
    Output = "output"
    Bidirectional = "bidirectional"
    TriState = "tri_state"
    Passive = "passive"

class GlobalLabel(Node):
    name: Annotated[str, Positional]
    shape: LabelShape
    fields_autoplaced: Annotated[bool, BoolSerialization.SymbolInList]
    effects: TextEffects
    at: Pos2
    uuid: Uuid
    properties: Properties

    def __init__(
            self,
            name: str,
            at: Pos2,
            shape: LabelShape = LabelShape.Input,
            fields_autoplaced: bool = True,
            effects: TextEffects = TextEffects(),
            uuid: Uuid = Uuid(),
            properties: ToProperties = {},
    ):
        super().__init__(locals())

class SchematicFile(ContainerNode):
    node_name = "kicad_sch"
    order_attrs = ("version", "generator")

    version: int
    generator: Generator
    uuid: Uuid
    page: PageSettings

    def __init__(
        self,
        uuid: Uuid = Uuid(),
        page: PageSettings = PageSettings(PaperSize.A4),
        version: int = KIGEN_VERSION,
        generator: Generator = KIGEN_GENERATOR,
    ):
        super().__init__(locals())

