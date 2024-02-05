from .common import *
from .symbol import Symbol, Property, SymbolLibrary

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
            uuid: Uuid = ()):
        super().__init__(locals())

class NoConnect(Node):
    node_name = "no_connect"

    at: Vec2
    uuid: Uuid

    def __init__(
            self,
            at: Vec2,
            uuid: Uuid = ()):
        super().__init__(locals())

class LabelShape(SymbolEnum):
    Input = "input"
    Output = "output"
    Bidirectional = "bidirectional"
    TriState = "tri_state"
    Passive = "passive"

class GlobalLabel(Node):
    node_name = "global_label"

    name: Annotated[str, Attr.Positional]
    shape: LabelShape
    fields_autoplaced: Annotated[bool, Attr.Bool.SymbolInList]
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
            uuid: Uuid = (),
            properties: ToProperties = {},
    ):
        super().__init__(locals())

class BaseWire(Node):
    pts: CoordinatePointList
    stroke: StrokeDefinition
    uuid: Uuid

    def __init__(
            self,
            pts: "CoordinatePointList | Iterable[ToVec2 | CoordinatePoint]" = (),
            stroke: StrokeDefinition = (),
            uuid: Uuid = (),
    ):
        super().__init__(locals())

class Wire(BaseWire):
    node_name = "wire"

class Bus(BaseWire):
    node_name = "bus"

class SchematicSymbolPin(Node):
    node_name = "pin"

    number: Annotated[str, Attr.Positional]
    uuid: Uuid

    def __init__(
            self,
            number: str,
            uuid: Uuid = ()
        ):
        super().__init__(locals())

class SchematicSymbolInstancePath(Node):
    node_name = "path"

    path: Annotated[str, Attr.Positional]
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

    name: Annotated[str, Attr.Positional]
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

class Rotate(BaseRotate):
    pass

class SchematicSymbol(TransformMixin, ContainerNode):
    child_types = (Property, Transform, SchematicSymbolPin,)
    node_name = "symbol"

    lib_id: str
    at: Annotated[Pos2, Attr.Transform]
    unit: int
    in_bom: Annotated[bool, Attr.Bool.YesNo]
    on_board: Annotated[bool, Attr.Bool.YesNo]
    dnp: Annotated[bool, Attr.Bool.YesNo]
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
            children: list[(Property | SchematicSymbolPin)] = (),
        ):
        super().__init__(locals())

    def get_pin_position(self, number: str) -> Pos2:
        schematic_file = self.closest(SchematicFile)
        if not schematic_file:
            raise RuntimeError("Cannot get pin position because there is no parent schematic")

        lib_sym: Symbol = schematic_file.lib_symbols.find_one(Symbol, lambda c: c.name == self.lib_id)
        if not lib_sym:
            raise RuntimeError(f"Could not find library symbol '{self.lib_id}' in schematic")

        pin = next((p for p in lib_sym.all_pins() if p.number.number == number), None)
        if not pin:
            raise RuntimeError(f"Symbol does not have a pin called '{number}'")

        return self.transform(pin.at.flip_y())

    @property
    def pins(self) -> Iterable[SchematicSymbolPin]:
        return self.find_all(SchematicSymbolPin)

Transform.child_types = (Property, SchematicSymbol, Transform, Rotate)
Rotate.child_types = (Property, SchematicSymbol, Transform, Rotate)

class SchematicLibrarySymbols(ContainerNode):
    node_name = "lib_symbols"
    child_types = (Symbol,)

class SchematicFile(ContainerNode):
    node_name = "kicad_sch"
    child_types = (Junction, NoConnect, Wire, Bus, GlobalLabel, SchematicSymbol, Transform, Rotate)
    order_attrs = ("version", "generator")

    version: int
    generator: Generator
    uuid: Uuid
    page: PageSettings
    lib_symbols: SchematicLibrarySymbols

    def __init__(
        self,
        uuid: Uuid = (),
        page: PageSettings = PageSettings(PaperSize.A4),
        lib_symbols: SchematicLibrarySymbols = (),
        version: int = KIGEN_VERSION,
        generator: Generator = KIGEN_GENERATOR,
    ):
        super().__init__(locals())

    def place_symbol(
            self,
            symbol: Symbol,
            reference: str,
            at: Pos2 = None,
            in_bom: bool = None,
            on_board: bool = None,
            dnp: bool = False
    ):

        lib_file = symbol.closest(SymbolLibrary)
        if not lib_file:
            raise RuntimeError("Only LibSymbols that are part of a SymbolLibFile can be imported")

        lib_id = f"{lib_file.filename}:{symbol.name}"
        if not self.lib_symbols.find_one(Symbol, lambda s: s.lib_id == lib_id):
            lsym = symbol.clone()
            lsym.name = lib_id
            self.lib_symbols.append(lsym)

        ssym = SchematicSymbol(
            lib_id=lib_id,
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
        )
        ssym.unknown = list(symbol.unknown)

        for pin in symbol.all_pins():
            ssym.append(SchematicSymbolPin(pin.number.number))

        for prop in symbol.find_all(Property):
            sprop = prop.clone()
            sprop.at = sprop.at.flip_y()
            ssym.append(sprop)

        self.append(ssym)

        return ssym

    def save(self, path):
        data = self.serialize()
        with open(path, "w") as f:
            f.write(data)
