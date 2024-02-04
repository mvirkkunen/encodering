from .common_nodes import *
from .symbol import SymbolProperty, LibSymbol

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
    name: Annotated[str, PositionalMeta]
    shape: LabelShape
    fields_autoplaced: Annotated[bool, BoolSerializationMeta.SymbolInList]
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


class SchematicSymbolPin(Node):
    node_name = "pin"

    name: Annotated[str, PositionalMeta]
    uuid: Uuid

    def __init__(
            self,
            name: str,
            uuid: Uuid = ()
        ):
        super().__init__(locals())

class SchematicSymbolInstancePath(Node):
    node_name = "path"

    path: Annotated[str, PositionalMeta]
    reference: str
    unit: int

    def __init__(
            self,
            path: str,
            reference: str,
            unit: int,
        ):
        super().__init__(locals())

class SchematicSymbolInstanceProject(Node):
    node_name = "project"

    name: Annotated[str, PositionalMeta]
    path: SchematicSymbolInstancePath

    def __init__(
            self,
            name: str,
            path: SchematicSymbolInstancePath = (),
        ):
        super().__init__(locals())

class SchematicSymbolInstances(ContainerNode):
    child_types = (SchematicSymbolInstanceProject,)
    node_name = "instances"

    def __init__(
            self,
            children: list[SchematicSymbolInstanceProject],
        ):
        super().__init__(locals())

class Transform(BaseTransform):
    pass

class SchematicSymbol(ContainerNode):
    child_types = (SymbolProperty, Transform, SchematicSymbolPin,)
    node_name = "symbol"

    lib_id: str
    at: Annotated[Pos2, TransformMeta]
    unit: int
    in_bom: Annotated[bool, BoolSerializationMeta.YesNo]
    on_board: Annotated[bool, BoolSerializationMeta.YesNo]
    dnp: Annotated[bool, BoolSerializationMeta.YesNo]
    uuid: Uuid
    instances: SchematicSymbolInstances

    def __init__(
            self,
            lib_id: str,
            at: Pos2,
            unit: int,
            in_bom: bool = True,
            on_board: bool = True,
            dnp: bool = False,
            uuid: Uuid = (),
            instances: SchematicSymbolInstances = (),
            children: list[(SymbolProperty | SchematicSymbolPin)] = (),
        ):
        super().__init__(locals())

Transform.child_types = (SymbolProperty, SchematicSymbol, Transform)

class SchematicLibrarySymbols(ContainerNode):
    node_name = "lib_symbols"
    child_types = (LibSymbol,)

class SchematicFile(ContainerNode):
    node_name = "kicad_sch"
    child_types = (Junction, NoConnect, GlobalLabel, SchematicSymbol, Transform)
    order_attrs = ("version", "generator")

    version: int
    generator: Generator
    uuid: Uuid
    page: PageSettings
    lib_symbols: SchematicLibrarySymbols

    def __init__(
        self,
        uuid: Uuid = Uuid(),
        page: PageSettings = PageSettings(PaperSize.A4),
        lib_symbols: SchematicLibrarySymbols = (),
        version: int = KIGEN_VERSION,
        generator: Generator = KIGEN_GENERATOR,
    ):
        super().__init__(locals())

    def place(
            self,
            symbol: LibSymbol,
            reference: str,
            at: Pos2 = None,
            in_bom: bool = None,
            on_board: bool = None,
            dnp: bool = False):

        if not any(c for c in self.lib_symbols.children if isinstance(c, LibSymbol) and c.name == symbol.name):
            self.lib_symbols.append(symbol.clone())

        ssym = SchematicSymbol(
            lib_id=symbol.name,
            at=at,
            unit=1,
            in_bom=in_bom or symbol.in_bom,
            on_board=on_board or symbol.on_board,
            dnp=dnp,
            instances=SchematicSymbolInstances(
                SchematicSymbolInstanceProject(
                    "project",
                    SchematicSymbolInstancePath(f"/{self.uuid.value}", reference, 1)
                )
            ),
            children=[
                *(SchematicSymbolPin(pin.number.number) for pin in symbol.recursive_pins()),
                *(prop.clone() for prop in symbol.children if isinstance(prop, SymbolProperty)),
            ],
        )
        ssym.unknown = list(symbol.unknown)

        if at:
            ssym = Transform(at, [ssym])

        self.append(ssym)
