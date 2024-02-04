from .common_nodes import *

class PinNumberVisibility(SymbolEnum):
    Hide = "hide"

class PinNames(Node):
    node_name = "pin_names"

    offset: Optional[float]
    hide: bool

    def __init__(
            self,
            offset: Optional[float] = None,
            hide = False):
        super().__init__(locals())

class SymbolProperty(Node):
    node_name = "property"

    name: Annotated[str, PositionalMeta]
    value: Annotated[str, PositionalMeta]
    at: Annotated[Pos2, TransformMeta]
    effects: TextEffects

    def __init__(
            self,
            name: str,
            value: str,
            at: Pos2,
            effects: TextEffects = TextEffects(),
    ):
        super().__init__(locals())

class PinElectricalType(SymbolEnum):
    Input = "input"
    Output = "output"
    Bidirectional = "bidirectional"
    TriState = "tri_state"
    Passive = "passive"
    Free = "free"
    Unspecified = "unspecified"
    PowerIn = "power_in"
    PowerOut = "power_out"
    OpenCollector = "open_collector"
    OpenEmitter = "open_emitter"
    No_Connect = "no_connect"

class PinGraphicalType(SymbolEnum):
    Line = "line"
    Inverted = "inverted"
    Clock = "clock"
    InvertedClock = "inverted_clock"
    InputLow = "input_low"
    ClockLow = "clock_low"
    OutputLow = "output_low"
    EdgeClockHigh = "edge_clock_high"
    NonLogic = "non_logic"

class PinName(Node):
    node_name = "name"

    name: Annotated[str, PositionalMeta]
    effects: TextEffects

    def __init__(
            self,
            name: str,
            effects: TextEffects = (),
    ):
        super().__init__(locals())

class PinNumber(Node):
    node_name = "number"

    number: Annotated[str, PositionalMeta]
    effects: TextEffects

    def __init__(
            self,
            number: str,
            effects: TextEffects = (),
    ):
        super().__init__(locals())

class Pin(Node):
    node_name = "pin"

    electrical_type: Annotated[PinElectricalType, PositionalMeta]
    graphical_type: Annotated[PinGraphicalType, PositionalMeta]
    at: Annotated[Pos2, TransformMeta]
    length: float
    name: PinName
    number: PinNumber

    def __init__(
            self,
            electrical_type: PinElectricalType,
            graphical_type: PinGraphicalType,
            at: Pos2,
            length: float,
            name: PinName,
            number: PinNumber,
    ):
        super().__init__(locals())

class LibSymbol(ContainerNode):
    node_name = "symbol"

    name: Annotated[str, PositionalMeta]
    extends: Optional[str]
    pin_numbers: Optional[PinNumberVisibility]
    pin_names: Optional[PinNames]
    in_bom: Annotated[bool, BoolSerializationMeta.YesNo]
    on_board: Annotated[bool, BoolSerializationMeta.YesNo]
    unit_name: Optional[str]

    def __init__(
            self,
            name: str,
            extends: Optional[str] = None,
            pin_numbers: Optional[PinNumberVisibility] = None,
            pin_names: Optional[PinNames] = None,
            in_bom: BoolSerializationMeta.YesNo = True,
            on_board: BoolSerializationMeta.YesNo = True,
        ):
        super().__init__(locals())

    def recursive_pins(self) -> list[Pin]:
        r = []

        for child in self.children:
            if isinstance(child, Pin):
                r.append(child)
            elif isinstance(child, LibSymbol):
                r.extend(child.recursive_pins())

        return r

LibSymbol.child_types = (SymbolProperty, Pin, LibSymbol)

class SymbolLibFile(ContainerNode):
    node_name = "kicad_symbol_lib"
    child_types = (LibSymbol,)
    order_attrs = ("version", "generator")

    version: int
    generator: Generator

    def __init__(
        self,
        version: int = KIGEN_VERSION,
        generator: Generator = KIGEN_GENERATOR,
    ):
        super().__init__(locals())

    def get(self, name):
        return next(c for c in self.children if c.name == name)
