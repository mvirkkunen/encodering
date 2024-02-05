import copy

from abc import ABC
from collections.abc import Iterable
from functools import cache
from typing import get_type_hints, Callable, ClassVar, Annotated, Optional, _UnionGenericAlias

from .sexpr import sexpr_parse, sexpr_serialize, SExpr, Sym, UnknownSExpr
from .values import *
from . import util

class AttrBool(Enum):
    Symbol = 1
    SymbolInList = 2
    YesNo = 3

class AttrPositional:
    pass

class AttrTransform:
    pass

class AttrIgnore:
    pass

class AttributeMeta:
    MetaAttribute: TypeAlias = AttrBool | AttrPositional | AttrTransform

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

            if any(m for m in metadata if m is AttrIgnore or isinstance(m, AttrIgnore)):
                continue

            # Uhh.....
            if _UnionGenericAlias in type(hint).__mro__ and len(hint.__args__) == 2 and hint.__args__[1] == type(None):
                optional = True
                hint = hint.__args__[0]

            r.append(AttributeMeta(name, hint, optional, metadata))

        order = getattr(cls, "order_attrs", [])

        r.sort(key=lambda a: (a.get_meta(AttrPositional) is None, order.index(a.name) if a.name in order else float("inf")))

        return r

    def __repr__(self):
        return f"AttributeMeta('{self.name}', {self.type}, {self.optional}, {self.metadata})"

class Node(ABC):
    node_name: ClassVar[Optional[str]]
    positional_attrs: ClassVar[Optional[(str)]]
    order_attrs: ClassVar[Optional[(str)]]
    transform_attrs: ClassVar[Optional[(str)]]

    parent: "Annotated[Optional[ContainerNode], AttrIgnore]"
    unknown: Annotated[Optional[list[SExpr]], AttrIgnore]

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

    def clone(self) -> Self:
        node = copy.copy(self)
        node.parent = None
        return node

    def closest(self, node_type: type):
        if isinstance(self, node_type):
            return self
        elif self.parent:
            return self.parent.closest(node_type)
        else:
            return None

    def to_sexpr(self):
        self.validate()

        r = []

        node_name = getattr(self, "node_name", None)
        if node_name:
            r.append(Sym(node_name))

        for a in AttributeMeta.get(self.__class__):
            val = getattr(self, a.name, None)
            if val is None:
                continue

            if a.get_meta(AttrTransform) and self.parent:
                val = a.type(self.parent.transform(val))

            if issubclass(a.type, bool):
                bool_ser: AttrBool = a.get_meta(AttrBool) or AttrBool.Symbol
                if bool_ser == AttrBool.Symbol:
                    if val:
                        r.append(Sym(a.name))
                elif bool_ser == AttrBool.SymbolInList:
                    if val:
                        r.append([Sym(a.name)])
                elif bool_ser == AttrBool.YesNo:
                    r.append([Sym(a.name), Sym("yes" if val else "no")])
            elif a.get_meta(AttrPositional) or isinstance(val, Node):
                r.append(val)
            else:
                r.append([Sym(a.name), val])

        if self.unknown:
            r.extend(map(UnknownSExpr, self.unknown))

        return [r]

    def validate(self):
        pass

    @classmethod
    def from_sexpr(cls, expr) -> Self:
        if (not isinstance(expr, list) and len(expr) > 1 and expr[0] == Sym(cls.node_name)):
            raise ValueError(f"Cannot deserialize {cls.__name__} from this S-expression")

        expr = list(expr[1:])
        node_name = cls.node_name
        attrs = {}

        for a in AttributeMeta.get(cls):
            if a.get_meta(AttrPositional):
                if len(expr) == 0:
                    raise ValueError(f"Not enough positional arguments in {node_name}")

                if hasattr(a.type, "from_sexpr"):
                    attrs[a.name] = a.type.from_sexpr([expr[0]])
                else:
                    attrs[a.name] = expr[0]
                del expr[0]
            elif a.type == bool:
                bool_ser: AttrBool = a.get_meta(AttrBool) or AttrBool.Symbol
                if bool_ser == AttrBool.Symbol:
                    v = util.remove_where(expr, lambda e: e == Sym(a.name))
                    attrs[a.name] = (len(v) > 0)
                elif bool_ser == AttrBool.SymbolInList:
                    v = util.remove_where(expr, lambda e: e == [Sym(a.name)])
                    attrs[a.name] = (len(v) > 0)
                elif bool_ser == AttrBool.YesNo:
                    v = util.remove_where(expr, lambda e: isinstance(e, list) and len(e) == 2 and e[0] == Sym(a.name))
                    attrs[a.name] = (len(v) > 0 and v[0][1] == Sym("yes"))
            else:
                v = util.remove_where(expr, lambda e: isinstance(e, list) and len(e) > 0 and e[0] == Sym(a.name))
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
    __children: Annotated[list[Node], AttrIgnore]

    def __init__(self, attrs=None):
        self.__children = []

        if not attrs:
            attrs = {}

        children = attrs.pop("children", None)
        super().__init__(attrs)

        if children:
            if not isinstance(children, Iterable):
                children = [children]

            for child in children:
                self.append(child)

    def clone(self):
        node = super().clone()
        node.__children = []
        node.extend(c.clone() for c in self.__children)
        return node

    def append(self, node):
        if not node:
            return

        if not isinstance(node, self.child_types):
            raise RuntimeError(f"{node.__class__.__name__} is not allowed to be a child of {self.__class__.__name__}")

        if node.parent:
            raise RuntimeError(f"{self.__class__.__name__} already has a parent")

        node.parent = self
        self.__children.append(node)

    def extend(self, nodes):
        for n in nodes:
            self.append(n)

    def find_one(self, child_type: type, predicate: Callable[[Node], bool] = None):
        return next(self.find_all(child_type, predicate), None)

    def find_all(self, child_type: type, predicate: Callable[[Node], bool] = None):
        return (c for c in self if isinstance(c, child_type) and (not predicate or predicate(c)))

    def __len__(self) -> int:
        return len(self.__children)

    def __iter__(self) -> Iterable[Node]:
        return iter(self.__children)

    def __getitem__(self, key: int) -> Node:
        return self.__children[key]

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

        for child in sorted(self.__children, key=lambda c: self.child_types.index(type(c))):
            r += child.to_sexpr()

        return [r]
