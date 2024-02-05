from .common import *

class BoardGeneralSettings(Node):
    node_name = "general"

    thickness: float

    def __init__(
            self,
            thickness: float):
        super().__init__(locals())

class LayerType(SymbolEnum):
    Jumper = "jumper"
    Mixed = "mixed"
    Power = "power"
    Signal = "signal"
    User = "user"

class BoardLayer(Node):
    ordinal: Annotated[int, Attr.Positional]
    canonical_name: Annotated[str, Attr.Positional]
    type: Annotated[LayerType, Attr.Positional]
    user_name: Annotated[Optional[str], Attr.Positional]

    def __init__(
            self,
            ordinal: int,
            canonical_name: str,
            type: LayerType,
            user_name: str = None):
        super().__init__(locals())

    @staticmethod
    def generate_layers(signal_layers):
        r = []

        ordinal = 0
        if signal_layers > 0:
            r.append(BoardLayer(ordinal, "F.Cu", LayerType.Signal))
            ordinal += 1

        if signal_layers > 2:
            for i in range(1, signal_layers - 1):
                r.append(BoardLayer(ordinal, f"In{i}.Cu", LayerType.Signal))
                ordinal += 1

        ordinal = max(ordinal, 31)

        if signal_layers > 1:
            r.append(BoardLayer(ordinal, "B.Cu", LayerType.Signal))
            ordinal += 1

        for attrs in [
            ("B.Adhes", LayerType.User, "B.Adhesive"),
            ("F.Adhes", LayerType.User, "F.Adhesive"),
            ("B.Paste", LayerType.User),
            ("F.Paste", LayerType.User),
            ("B.SilkS", LayerType.User, "B.Silkscreen"),
            ("F.SilkS", LayerType.User, "F.Silkscreen"),
            ("B.Mask", LayerType.User),
            ("F.Mask", LayerType.User),
            ("Dwgs.User", LayerType.User, "User.Drawings"),
            ("Cmts.User", LayerType.User, "User.Comments"),
            ("Eco1.User", LayerType.User, "User.Eco1"),
            ("Eco2.User", LayerType.User, "User.Eco2"),
            ("Edge.Cuts", LayerType.User),
            ("Margin", LayerType.User),
            ("B.CrtYd", LayerType.User, "B.Courtyard"),
            ("F.CrtYd", LayerType.User, "F.Courtyard"),
            ("B.Fab", LayerType.User),
            ("F.Fab", LayerType.User),
            ("User.1", LayerType.User),
            ("User.2", LayerType.User),
            ("User.3", LayerType.User),
            ("User.4", LayerType.User),
            ("User.5", LayerType.User),
            ("User.6", LayerType.User),
            ("User.7", LayerType.User),
            ("User.8", LayerType.User),
            ("User.9", LayerType.User),
        ]:
            r.append(BoardLayer(ordinal, *attrs))
            ordinal += 1

        return r

class BoardLayers(ContainerNode):
    node_name = "layers"
    child_types = (BoardLayer,)

    def __init__(self, children):
        super().__init__(locals())

class BoardSetup(Node):
    node_name = "setup"

    pad_to_mask_clearance: float
    solder_mask_min_width: Optional[float]
    pad_to_paste_clearance: Optional[float]
    pad_to_paste_clearance_ratio: Optional[float]
    aux_axis_origin: Optional[Vec2]
    grid_origin: Optional[Vec2]

    def __init__(
            self,
            pad_to_mask_clearance: float = 0,
            solder_mask_min_width: float = None,
            pad_to_paste_clearance: float = None,
            pad_to_paste_clearance_ratio: float = None,
            aux_axis_origin: Vec2 = Vec2(),
            grid_origin: Vec2 = Vec2()):
        super().__init__(locals())

class BoardNet(Node):
    node_name = "net"

    ordinal: int
    name: str

    def __init__(
            self,
            ordinal: int,
            name: str):
        """
        Defines a net for the board.

        ordinal: the net ID, also defines net order
        name: name of the net
        """
        super().__init__(locals())

class TrackSegment(Node):
    node_name = "segment"

    start: Annotated[Vec2, Attr.Transform]
    end: Annotated[Vec2, Attr.Transform]
    width: float
    layer: str
    net: int
    tstamp: Uuid

    def __init__(
            self,
            start: Vec2,
            end: Vec2,
            width: float,
            layer: str,
            net: int,
            tstamp: Uuid = ()):
        super().__init__(locals())


class BoardFile(ContainerNode):
    node_name = "kicad_pcb"
    order_attrs = ("version", "generator")

    version: int
    generator: Generator
    general: BoardGeneralSettings
    page: PageSettings
    layers: BoardLayers
    setup: BoardSetup

    def __init__(
        self,
        layers: int | list[BoardLayer] = 2,
        general: BoardGeneralSettings = BoardGeneralSettings(thickness=1.6),
        page: PageSettings = PageSettings(PaperSize.A4),
        setup: BoardSetup = BoardSetup(),
        version: int = KIGEN_VERSION,
        generator: Generator = KIGEN_GENERATOR,
    ):
        if not isinstance(layers, list):
            layers = BoardLayer.generate_layers(layers)

        layers = BoardLayers(layers)

        super().__init__(locals())
