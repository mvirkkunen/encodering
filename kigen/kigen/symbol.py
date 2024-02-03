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

    name: Annotated[str, Positional]
    value: Annotated[str, Positional]
    at: Pos2
    effects: TextEffects

    def __init__(
            self,
            name: str,
            value: str,
            at: Pos2,
            effects: TextEffects = TextEffects(),
    ):
        super().__init__(locals())

class SSymbol(ContainerNode):
    node_name = "symbol"
    child_types = (SymbolProperty,)

    name: Annotated[str, Positional]
    extends: Optional[str]
    pin_numbers: Optional[PinNumberVisibility]
    pin_names: Optional[PinNames]
    in_bom: Annotated[bool, BoolSerialization.YesNo]
    on_board: Annotated[bool, BoolSerialization.YesNo]
    unit_name: Optional[str]

    def __init__(
            self,
            name: str,
            extends: Optional[str] = None,
            pin_numbers: Optional[PinNumberVisibility] = None,
            pin_names: Optional[PinNames] = None,
            in_bom: BoolSerialization.YesNo = True,
            on_board: BoolSerialization.YesNo = True,
        ):
        super().__init__(locals())

class SymbolLibFile(ContainerNode):
    node_name = "kicad_symbol_lib"
    child_types = (SSymbol,)
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
