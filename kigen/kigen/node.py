import math

from abc import ABC
from collections.abc import Iterable
from functools import cache
from typing import get_type_hints, ClassVar, Annotated, Optional, _UnionGenericAlias

from .util import reorder_dict
from .sexpr import sexpr_serialize
from .values import *

KIGEN_VERSION = Symbol("20211014")
KIGEN_GENERATOR = Symbol("kigen")

class BoolSerialization(Enum):
    Symbol = 1
    SymbolInList = 2
    YesNo = 3

class Positional:
    pass

class Transform:
    pass

class Special:
    pass

MetaAttribute: TypeAlias = BoolSerialization | Positional | Transform

class AttributeMeta:
    name: str
    type: type
    optional: bool
    metadata: list[MetaAttribute]

    def __init__(self, name, type, optional, metadata):
        self.name = name
        self.type = type
        self.optional = optional
        self.metadata = metadata

    def get_meta(self, type: MetaAttribute) -> Optional[MetaAttribute]:
        return next((m for m in self.metadata if m is type or isinstance(m, type)), None)

    @staticmethod
    @cache
    def get(cls: type) -> "list[AttributeMeta]":
        r = []

        for name, hint in get_type_hints(cls, include_extras=True).items():
            if hint.__name__ == "ClassVar":
                continue

            optional = False
            metadata = []

            if hint.__name__ == "Annotated":
                metadata = hint.__metadata__
                hint = hint.__origin__

            if any(m for m in metadata if m is Special or isinstance(m, Special)):
                continue

            # Uhh.....
            if _UnionGenericAlias in type(hint).__mro__ and len(hint.__args__) == 2 and hint.__args__[1] == type(None):
                optional = True
                hint = hint.__args__[0]

            r.append(AttributeMeta(name, hint, optional, metadata))

        order = getattr(cls, "order_attrs", [])

        r.sort(key=lambda a: (a.get_meta(Positional) is None, order.index(a.name) if a.name in order else float("inf")))

        return r

    def __repr__(self):
        return f"AttributeMeta('{self.name}', {self.type}, {self.optional}, {self.metadata})"

class Node(ABC):
    node_name: ClassVar[Optional[str]]
    positional_attrs: ClassVar[Optional[(str)]]
    order_attrs: ClassVar[Optional[(str)]]
    transform_attrs: ClassVar[Optional[(str)]]

    parent: "Annotated[Optional[Node], Special]"

    def __init__(self, attrs):
        self.parent = None

        parent = attrs.pop("parent", None)

        for a in AttributeMeta.get(self.__class__):
            value = attrs.get(a.name, None)

            if value is None:
                if not a.optional:
                    raise ValueError(f"{self.__class__.__name__} requires attribute '{a.name}'")

                setattr(self, a.name, None)
                continue

            if not isinstance(value, a.type):
                value = a.type(value)

            setattr(self, a.name, value)

        self.parent = None
        if parent:
            parent.append(self)

    def to_sexpr(self):
        r = []

        node_name = getattr(self, "node_name", None)
        if node_name:
            r.append(Symbol(node_name))

        meta = AttributeMeta.get(self.__class__)

        attrs = {
            a.name: v
            for (a, v) in ((a, getattr(self, a.name)) for a in meta)
            if v is not None
        }

        for a in meta:
            val = attrs.get(a.name, None)
            if not val:
                continue

            if a.get_meta(Transform):
                val = a.type(self.transform(val))

            bool_ser: BoolSerialization = a.get_meta(BoolSerialization) or BoolSerialization.Symbol

            if isinstance(val, bool):
                if bool_ser == BoolSerialization.Symbol:
                    if val:
                        r.append(Symbol(a.name))
                elif bool_ser == BoolSerialization.SymbolInList:
                    if val:
                        r.append([Symbol(a.name)])
                elif bool_ser == BoolSerialization.YesNo:
                    r.append([Symbol(a.name), Symbol("yes" if val else "no")])
            elif isinstance(val, Node):
                r.append(val)
            elif a.get_meta(Positional):
                r.append(val)
            else:
                r.append([Symbol(a.name), val])

        return [r]

    def serialize(self):
        return sexpr_serialize(self.to_sexpr()[0])

    def transform(self, pos: ToPos2) -> Pos2:
        if self.parent:
            return self.parent.transform(pos)
        else:
            return Pos2(pos)

class ContainerNode(Node):
    children: Annotated[list[Node], Special]

    def __init__(self, attrs):
        children = attrs.pop("children", None)
        super().__init__(attrs)

        self.children = []

        if children:
            if not isinstance(children, Iterable):
                children = [children]

            for child in children:
                self.append(child)

    def append(self, node):
        if not node:
            return

        if not isinstance(node, getattr(self.__class__, "allowed_children")):
            raise RuntimeError(f"{node.__class__.__name__} is not allowed to be a child of {self.__class__.__name__}")

        if node.parent:
            raise RuntimeError(f"{self.__class__.__name__} already has a parent")

        node.parent = self
        self.children.append(node)

    def extend(self, nodes):
        for n in nodes:
            self.append(n)

    def to_sexpr(self):
        r = super().to_sexpr()[0]
        for child in self.children:
            r += child.to_sexpr()
        return [r]
