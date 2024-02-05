from typing import ClassVar, Sequence

from .common import *

class BoardGeneralSettings(Node):
    node_name = "general"

    thickness: float

    def __init__(
            self,
            thickness: float
    ) -> None:
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
            user_name: Optional[str] = None
    ) -> None:
        super().__init__(locals())

class BoardLayers(ContainerNode):
    node_name = "layers"
    child_types = (BoardLayer,)

    default_non_signal_layers: ClassVar[list[tuple[str, LayerType, Optional[str]]]] = [
        ("B.Adhes", LayerType.User, "B.Adhesive"),
        ("F.Adhes", LayerType.User, "F.Adhesive"),
        ("B.Paste", LayerType.User, None),
        ("F.Paste", LayerType.User, None),
        ("B.SilkS", LayerType.User, "B.Silkscreen"),
        ("F.SilkS", LayerType.User, "F.Silkscreen"),
        ("B.Mask", LayerType.User, None),
        ("F.Mask", LayerType.User, None),
        ("Dwgs.User", LayerType.User, "User.Drawings"),
        ("Cmts.User", LayerType.User, "User.Comments"),
        ("Eco1.User", LayerType.User, "User.Eco1"),
        ("Eco2.User", LayerType.User, "User.Eco2"),
        ("Edge.Cuts", LayerType.User, None),
        ("Margin", LayerType.User, None),
        ("B.CrtYd", LayerType.User, "B.Courtyard"),
        ("F.CrtYd", LayerType.User, "F.Courtyard"),
        ("B.Fab", LayerType.User, None),
        ("F.Fab", LayerType.User, None),
        ("User.1", LayerType.User, None),
        ("User.2", LayerType.User, None),
        ("User.3", LayerType.User, None),
        ("User.4", LayerType.User, None),
        ("User.5", LayerType.User, None),
        ("User.6", LayerType.User, None),
        ("User.7", LayerType.User, None),
        ("User.8", LayerType.User, None),
        ("User.9", LayerType.User, None),
    ]

    def __init__(
            self,
            children: Sequence[BoardLayer]
    ) -> None:
        super().__init__(locals())

    @staticmethod
    def generate_layers(num_signal_layers: int) -> "BoardLayers":
        r = []

        ordinal = 0
        if num_signal_layers > 0:
            r.append(BoardLayer(ordinal, "F.Cu", LayerType.Signal))
            ordinal += 1

        if num_signal_layers > 2:
            for i in range(1, num_signal_layers - 1):
                r.append(BoardLayer(ordinal, f"In{i}.Cu", LayerType.Signal))
                ordinal += 1

        ordinal = max(ordinal, 31)

        if num_signal_layers > 1:
            r.append(BoardLayer(ordinal, "B.Cu", LayerType.Signal))
            ordinal += 1

        for attrs in BoardLayers.default_non_signal_layers:
            r.append(BoardLayer(ordinal, *attrs))
            ordinal += 1

        return BoardLayers(r)

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
            solder_mask_min_width: Optional[float] = None,
            pad_to_paste_clearance: Optional[float] = None,
            pad_to_paste_clearance_ratio: Optional[float] = None,
            aux_axis_origin: Vec2 = NEW_INSTANCE,
            grid_origin: Vec2 = NEW_INSTANCE,
    ) -> None:
        super().__init__(locals())

class BoardNet(Node):
    node_name = "net"

    ordinal: int
    name: str

    def __init__(
            self,
            ordinal: int,
            name: str
    ) -> None:
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
            tstamp: Uuid = NEW_INSTANCE
    ) -> None:
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
        layers: BoardLayers | list[BoardLayer] | int,
        thickness: float,
        page: Optional[PageSettings] = None,
        setup: Optional[BoardSetup] = NEW_INSTANCE,
        version: int = KIGEN_VERSION,
        generator: Generator = KIGEN_GENERATOR,
    ) -> None:
        if isinstance(layers, list):
            layers = BoardLayers(layers)

        if not isinstance(layers, BoardLayers):
            layers = BoardLayers.generate_layers(layers)

        general = BoardGeneralSettings(thickness=thickness)
        page = page or PageSettings(PaperSize.A4)

        super().__init__(locals())
