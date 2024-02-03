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

class SchematicFile(ContainerNode):
    node_name = "kicad_sch"
    order_attrs = ("version", "generator")

    version: Symbol
    generator: Symbol
    uuid: Uuid
    page: PageSettings

    def __init__(
        self,
        uuid: Uuid = Uuid(),
        page: PageSettings = PageSettings(PaperSize.A4),
        version: Symbol = KIGEN_VERSION,
        generator: Symbol = KIGEN_GENERATOR,
    ):
        super().__init__(locals())

