import copy
from typing import Annotated, ClassVar, Optional

from ..node import Attr, ContainerNode, Node, NodeLoadSaveMixin, NEW_INSTANCE
from ..common import Generator, Layer, Net, PageSettings, PaperSize, Property, KIGEN_GENERATOR, KIGEN_VERSION
from ..values import SymbolEnum, Pos2, Uuid, Vec2
from .footprint import Footprint, LibraryFootprint
from .symbol import SymbolEnum, Property as SymbolProperty
from .schematic import SchematicSymbol

class GeneralSettings(Node):
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

class PcbLayer(Node):
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

class PcbLayers(ContainerNode):
    node_name = "layers"
    child_types = (PcbLayer,)

    default_non_signal_layers: ClassVar[list[tuple[str, LayerType, Optional[str]]]] = [
        (Layer.BAdhes, LayerType.User, "B.Adhesive"),
        (Layer.FAdhes, LayerType.User, "F.Adhesive"),
        (Layer.BPaste, LayerType.User, None),
        (Layer.FPaste, LayerType.User, None),
        (Layer.BSilkS, LayerType.User, "B.Silkscreen"),
        (Layer.FSilkS, LayerType.User, "F.Silkscreen"),
        (Layer.BMask, LayerType.User, None),
        (Layer.FMask, LayerType.User, None),
        (Layer.DwgsUser, LayerType.User, "User.Drawings"),
        (Layer.CmtsUser, LayerType.User, "User.Comments"),
        (Layer.Eco1User, LayerType.User, "User.Eco1"),
        (Layer.Eco2User, LayerType.User, "User.Eco2"),
        (Layer.EdgeCuts, LayerType.User, None),
        (Layer.Margin, LayerType.User, None),
        (Layer.BCrtYd, LayerType.User, "B.Courtyard"),
        (Layer.FCrtYd, LayerType.User, "F.Courtyard"),
        (Layer.BFab, LayerType.User, None),
        (Layer.FFab, LayerType.User, None),
        (Layer.User1, LayerType.User, None),
        (Layer.User2, LayerType.User, None),
        (Layer.User3, LayerType.User, None),
        (Layer.User4, LayerType.User, None),
        (Layer.User5, LayerType.User, None),
        (Layer.User6, LayerType.User, None),
        (Layer.User7, LayerType.User, None),
        (Layer.User8, LayerType.User, None),
        (Layer.User9, LayerType.User, None),
    ]

    def __init__(
            self,
            children: list[PcbLayer]
    ) -> None:
        super().__init__(locals())

    @staticmethod
    def generate_layers(num_signal_layers: int) -> "PcbLayers":
        r = []

        ordinal = 0
        if num_signal_layers > 0:
            r.append(PcbLayer(ordinal, Layer.FCu, LayerType.Signal))
            ordinal += 1

        if num_signal_layers > 2:
            for i in range(1, num_signal_layers - 1):
                r.append(PcbLayer(ordinal, f"In{i}.Cu", LayerType.Signal))
                ordinal += 1

        ordinal = max(ordinal, 31)

        if num_signal_layers > 1:
            r.append(PcbLayer(ordinal, Layer.BCu, LayerType.Signal))
            ordinal += 1

        for attrs in PcbLayers.default_non_signal_layers:
            r.append(PcbLayer(ordinal, *attrs))
            ordinal += 1

        return PcbLayers(r)

class Setup(Node):
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

class Track(Node):
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
            net: int | Net,
            tstamp: Uuid = NEW_INSTANCE
    ) -> None:
        if isinstance(net, Net):
            net = net.ordinal

        super().__init__(locals())

class Rect(Node):
    node_name = "gr_rect"

    start: Annotated[Vec2, Attr.Transform]
    end: Annotated[Vec2, Attr.Transform]
    width: float
    layer: str
    tstamp: Uuid

    def __init__(
            self,
            start: Vec2,
            end: Vec2,
            width: float,
            layer: str,
            tstamp: Uuid = NEW_INSTANCE,
    ) -> None:
        super().__init__(locals())

class PcbFile(ContainerNode, NodeLoadSaveMixin):
    child_types = (Net, Footprint, Track, Rect)
    node_name = "kicad_pcb"
    order_attrs = ("version", "generator")

    version: int
    generator: Generator
    general: GeneralSettings
    page: PageSettings
    layers: PcbLayers
    setup: Setup

    def __init__(
        self,
        layers: PcbLayers | list[PcbLayer] | int = 2,
        thickness: float = 1.6,
        page: Optional[PageSettings] = None,
        setup: Optional[Setup] = NEW_INSTANCE,
        version: int = KIGEN_VERSION,
        generator: Generator = KIGEN_GENERATOR,
    ) -> None:
        if isinstance(layers, list):
            layers = PcbLayers(layers)

        if not isinstance(layers, PcbLayers):
            layers = PcbLayers.generate_layers(layers)

        general = GeneralSettings(thickness=thickness)
        page = page or PageSettings(PaperSize.A4)

        super().__init__(locals())

        self.append(Net(0, ""))

    def add_net(self, name: str) -> None:
        if self.get_net(name):
            raise ValueError(f"Net '{name} already exists")

        net = Net(sum(1 for _ in self.find_all(Net)), name)
        self.append(net)
        return net

    def get_net(self, name: str) -> Optional[Net]:
        return self.find_one(Net, lambda n: n.name == name)

    def place(
            self,
            footprint: Footprint | LibraryFootprint,
            layer: str,
            at: Pos2,
            path: Optional[str | SchematicSymbol] = None,
            library_link: Optional[str] = None,
            parent: Optional[ContainerNode] = None,
    ) -> Footprint:
        """
        Places a footprint symbol onto the PCB.

        :param footprint: The footprint to place
        :param at: Position and rotation angle for the symbol.
        :returns: a SchematicSymbol instance
        """

        if not library_link:
            if isinstance(footprint, Footprint) and footprint.library_link is not None:
                library_link = footprint.library_link
            elif isinstance(footprint, LibraryFootprint):
                library_link = f"{footprint.library_name}:{footprint.name}"

        if not library_link:
            raise ValueError("library_link is required if footprint does not provide one")

        children = []

        if isinstance(path, SchematicSymbol):
            for prop in path.find_all(SymbolProperty, lambda p: p.name.startswith("ki_")):
                children.append(Property(prop.name, prop.value))

            path = f"/{path.uuid.value}"

        children.extend(c.clone() for c in footprint)

        fp = Footprint(
            library_link=library_link,
            layer=layer,
            at=at,
            path=path,
            descr=footprint.descr,
            tags=footprint.tags,
            children=children,
            attr=footprint.attr.clone() if footprint.attr else None
        )

        fp.unknown = copy.deepcopy(footprint.unknown)

        (parent or self).append(fp)

        return fp
