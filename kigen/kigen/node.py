import copy

from abc import ABC
from collections.abc import Iterable
from functools import cache
from typing import get_type_hints, ClassVar, Annotated, Optional, _UnionGenericAlias

from .sexpr import sexpr_parse, sexpr_serialize, SExpr, Sym, UnknownExpr
from .values import *

class BoolSerializationMeta(Enum):
    Symbol = 1
    SymbolInList = 2
    YesNo = 3

class PositionalMeta:
    pass

class TransformMeta:
    pass

class SpecialMeta:
    pass

MetaAttribute: TypeAlias = BoolSerializationMeta | PositionalMeta | TransformMeta

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

            if any(m for m in metadata if m is SpecialMeta or isinstance(m, SpecialMeta)):
                continue

            # Uhh.....
            if _UnionGenericAlias in type(hint).__mro__ and len(hint.__args__) == 2 and hint.__args__[1] == type(None):
                optional = True
                hint = hint.__args__[0]

            r.append(AttributeMeta(name, hint, optional, metadata))

        order = getattr(cls, "order_attrs", [])

        r.sort(key=lambda a: (a.get_meta(PositionalMeta) is None, order.index(a.name) if a.name in order else float("inf")))

        return r

    def __repr__(self):
        return f"AttributeMeta('{self.name}', {self.type}, {self.optional}, {self.metadata})"

def remove_where(l: list, pred):
    i = 0
    r = []
    while i < len(l):
        if pred(l[i]):
            r.append(l[i])
            del l[i]
        else:
            i += 1

    return r

class Node(ABC):
    node_name: ClassVar[Optional[str]]
    positional_attrs: ClassVar[Optional[(str)]]
    order_attrs: ClassVar[Optional[(str)]]
    transform_attrs: ClassVar[Optional[(str)]]

    parent: "Annotated[Optional[Node], SpecialMeta]"
    unknown: Annotated[Optional[list[SExpr]], SpecialMeta]

    def __init__(self, attrs=None):
        if not attrs:
            attrs = {}

        self.parent = None
        self.unknown = None

        parent = attrs.pop("parent", None)

        for a in AttributeMeta.get(self.__class__):
            value = attrs.get(a.name, None)

            if value is None:
                if not a.optional:
                    raise ValueError(f"{self.__class__.__name__} requires attribute '{a.name}'")

                setattr(self, a.name, None)
                continue
            if value == ():
                value = a.type()
            elif not isinstance(value, a.type):
                value = a.type(value)

            setattr(self, a.name, value)

        if parent:
            parent.append(self)

    def clone(self):
        node = copy.copy(self)
        node.parent = None
        return node

    def to_sexpr(self):
        r = []

        node_name = getattr(self, "node_name", None)
        if node_name:
            r.append(Sym(node_name))

        for a in AttributeMeta.get(self.__class__):
            val = getattr(self, a.name, None)
            if val is None:
                continue

            if a.get_meta(TransformMeta):
                val = a.type(self.transform(val))

            if issubclass(a.type, bool):
                bool_ser: BoolSerializationMeta = a.get_meta(BoolSerializationMeta) or BoolSerializationMeta.Symbol
                if bool_ser == BoolSerializationMeta.Symbol:
                    if val:
                        r.append(Sym(a.name))
                elif bool_ser == BoolSerializationMeta.SymbolInList:
                    if val:
                        r.append([Sym(a.name)])
                elif bool_ser == BoolSerializationMeta.YesNo:
                    r.append([Sym(a.name), Sym("yes" if val else "no")])
            elif a.get_meta(PositionalMeta) or isinstance(val, Node):
                r.append(val)
            else:
                r.append([Sym(a.name), val])

        if self.unknown:
            r.extend(map(UnknownExpr, self.unknown))

        return [r]

    @classmethod
    def from_sexpr(cls, expr) -> Self:
        if (not isinstance(expr, list) and len(expr) > 1 and expr[0] == Sym(cls.node_name)):
            raise ValueError(f"Cannot deserialize {cls.__name__} from this S-expression")

        expr = list(expr[1:])
        node_name = cls.node_name
        attrs = {}

        for a in AttributeMeta.get(cls):
            if a.get_meta(PositionalMeta):
                if len(expr) == 0:
                    raise ValueError(f"Not enough positional arguments in {node_name}")

                if hasattr(a.type, "from_sexpr"):
                    attrs[a.name] = a.type.from_sexpr([expr[0]])
                else:
                    attrs[a.name] = expr[0]
                del expr[0]
            elif a.type == bool:
                bool_ser: BoolSerializationMeta = a.get_meta(BoolSerializationMeta) or BoolSerializationMeta.Symbol
                if bool_ser == BoolSerializationMeta.Symbol:
                    v = remove_where(expr, lambda e: e == Sym(a.name))
                    attrs[a.name] = (len(v) > 0)
                elif bool_ser == BoolSerializationMeta.SymbolInList:
                    v = remove_where(expr, lambda e: e == [Sym(a.name)])
                    attrs[a.name] = (len(v) > 0)
                elif bool_ser == BoolSerializationMeta.YesNo:
                    v = remove_where(expr, lambda e: isinstance(e, list) and len(e) == 2 and e[0] == Sym(a.name))
                    attrs[a.name] = (len(v) > 0 and v[0][1] == Sym("yes"))
                    print(a, bool_ser, v, attrs[a.name])
            else:
                v = remove_where(expr, lambda e: isinstance(e, list) and len(e) > 0 and e[0] == Sym(a.name))
                if len(v) >= 1:
                    if issubclass(a.type, Node):
                        attrs[a.name] = a.type.from_sexpr(v[0])
                    elif hasattr(a.type, "from_sexpr"):
                        attrs[a.name] = a.type.from_sexpr(v[0][1:])
                    else:
                        attrs[a.name] = v[0][1]

                    expr += v[1:]

        node = cls(**attrs)
        node.unknown = expr
        return node

    def serialize(self, show_unknown=False):
        return sexpr_serialize(self.to_sexpr()[0], show_unknown=show_unknown)

    @classmethod
    def parse(cls, s):
        return cls.from_sexpr(sexpr_parse(s))

    def transform(self, pos: ToPos2) -> Pos2:
        if self.parent:
            return self.parent.transform(pos)
        else:
            return Pos2(pos)

class ContainerNode(Node):
    children: Annotated[list[Node], SpecialMeta]

    def __init__(self, attrs=None):
        if not attrs:
            attrs = {}

        children = attrs.pop("children", None)
        super().__init__(attrs)

        self.children = []

        if children:
            if not isinstance(children, Iterable):
                children = [children]

            for child in children:
                self.append(child)

    def clone(self):
        node = super().clone()
        node.children = []
        node.extend(c.clone() for c in self.children)
        return node

    def append(self, node):
        if not node:
            return

        if not isinstance(node, self.__class__.child_types):
            raise RuntimeError(f"{node.__class__.__name__} is not allowed to be a child of {self.__class__.__name__}")

        if node.parent:
            raise RuntimeError(f"{self.__class__.__name__} already has a parent")

        node.parent = self
        self.children.append(node)

    def extend(self, nodes):
        for n in nodes:
            self.append(n)

    @classmethod
    def from_sexpr(cls, expr: SExpr) -> Self:
        if (not isinstance(expr, list) and len(expr) > 1 and expr[0] == Sym(cls.node_name)):
            raise ValueError(f"Cannot deserialize {cls.__name__} from this S-expression")

        unknown = []
        children = []

        for e in expr[1:]:
            if not isinstance(e[0], Sym):
                unknown.append(e)
                continue

            child_type = next((t for t in cls.child_types if t.node_name == e[0].name), None)
            if not child_type:
                unknown.append(e)
                continue

            children.append(child_type.from_sexpr(e))

        node = super().from_sexpr([expr[0], *unknown])
        node.extend(children)
        return node

    def to_sexpr(self):
        r = super().to_sexpr()[0]
        for child in self.children:
            r += child.to_sexpr()
        return [r]
