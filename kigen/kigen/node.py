import copy
import enum
from pathlib import Path

from collections.abc import Iterable, Iterator
from functools import cache
import typing
from typing import Any, Callable, ClassVar, Annotated, Optional, Protocol, Self, TypeAlias, TypeVar, Union

from . import pickle_cache, sexpr, util
from .values import Pos2, ToPos2, Uuid

class NewInstance: pass
NEW_INSTANCE: Any = NewInstance()

class Attr:
    """
    Metadata for node attributes
    """

    class Ignore:
        """
        Type annotation. Ignore for S-expression de/serialization.
        """

    class Positional:
        """
        Type annotation. Positional attributes have no name and are de/serialized by position.
        """

        count: int

        def __init__(self, count: int=1) -> None:
            self.count = count

    class Bool(enum.Enum):
        """
        Type annotation. Specify how a boolean attribute is serialized.
        """

        Symbol = 1
        SymbolInList = 2
        YesNo = 3

    class Transform:
        """
        Type annotation. Attribute is processed by Node.transform() when serializing.
        """

    Meta: TypeAlias = Ignore | Positional | Bool | Transform

    name: str
    value_type: type
    optional: bool
    meta: dict[type[Meta], Meta]

    def __init__(self, name: str, value_type: type, optional: bool, meta: dict[type[Meta], Meta]) -> None:
        self.name = name
        self.value_type = value_type
        self.optional = optional
        self.meta = meta

    _T = TypeVar("_T", Ignore, Positional, Bool, Transform)

    def get_meta(self, meta_type: type[_T]) -> Optional[_T]:
        m: Any = self.meta.get(meta_type, None)
        assert not m or isinstance(m, meta_type)
        return m

    @staticmethod
    @cache
    def _get_class_attributes(cls: type) -> "list[Attr]":
        r = []

        for name, hint in typing.get_type_hints(cls, include_extras=True).items():
            if typing.get_origin(hint) is ClassVar:
                continue

            optional = False

            if typing.get_origin(hint) is Annotated:
                hint, *meta_args = typing.get_args(hint)
                meta = dict(((m, m()) if type(m) == type else (type(m), m)) for m in meta_args)
            else:
                meta = {}

            if Attr.Ignore in meta:
                continue

            if typing.get_origin(hint) is Union:
                args = typing.get_args(hint)
                if len(args) == 2 and args[1] == type(None):
                    optional = True
                    hint = args[0]

            r.append(Attr(name, hint, optional, meta))

        order = getattr(cls, "order_attrs", [])

        r.sort(key=lambda a: (a.get_meta(Attr.Positional) is None, order.index(a.name) if a.name in order else float("inf")))

        return r

    @staticmethod
    def get_class_attributes(cls: type) -> "list[Attr]":
        return Attr._get_class_attributes(cls)

    def __repr__(self) -> str:
        return f"Attr('{self.name}', {self.value_type}, {self.optional}, {self.meta})"

class Node:
    """
    Base class for KiCad data nodes.
    """

    node_name: ClassVar[Optional[str]]
    order_attrs: ClassVar[Optional[tuple[str, ...]]]

    # Parent node.
    __parent: "Annotated[Optional[Node], Attr.Ignore]"

    # Unknown S-expression data that was encountered while deserializing. Will be retained when serializing.
    unknown: Annotated[Optional[list[sexpr.SExpr]], Attr.Ignore]

    def __init__(self, attrs: Optional[dict[str, sexpr.SExprConvert]] = None) -> None:
        self._init(attrs)

    def _init(self, attrs: Optional[dict[str, sexpr.SExprConvert]] = None) -> None:
        if not attrs:
            attrs = {}

        self.__parent = None
        self.unknown = None

        parent = attrs.pop("parent", None)
        assert parent is None or isinstance(parent, ContainerNode)

        for a in Attr.get_class_attributes(self.__class__):
            value = attrs.get(a.name, None)

            if value is None:
                if not a.optional:
                    raise ValueError(f"{self.__class__.__name__} requires attribute '{a.name}'")
            elif value is NEW_INSTANCE:
                value = a.value_type()
            elif not isinstance(value, a.value_type):
                value = a.value_type(value)

            setattr(self, a.name, value)

        if parent:
            parent.append(self)

    @property
    def parent(self) -> "Optional[Node]":
        """
        Gets the parent of the node, or None if it has none.
        """

        return self.__parent

    def _set_parent(self, parent: "Optional[Node]") -> None:
        """
        For internal use. Sets the parent reference of the node.
        """

        self.__parent = parent

    def detach(self) -> None:
        """
        Detaches node from its parent, if any.
        """

        if isinstance(self.__parent, ContainerNode):
            self.__parent.remove(self)
        else:
            self.__parent = None

    def clone(self) -> Self:
        """
        Creates a recursive clone of this node. The new node will not have a parent.
        """

        node = self.__class__.__new__(self.__class__)
        node.__parent = None
        node.unknown = copy.deepcopy(self.unknown)
        for a in Attr.get_class_attributes(self.__class__):
            if a.value_type == Uuid:
                setattr(node, a.name, Uuid())
            else:
                setattr(node, a.name, copy.deepcopy(getattr(self, a.name)))

        return node

    _T = TypeVar("_T", bound="Node")

    def closest(self, node_type: type[_T]) -> Optional[_T]:
        """
        Finds the closest parent of the specified type up the node tree, or the node itself if the node itself is the specified type.
        """

        if isinstance(self, node_type):
            return self
        elif self.__parent:
            return self.__parent.closest(node_type)
        else:
            return None

    def to_sexpr(self) -> list[list[sexpr.SExpr]]:
        self.validate()

        r: list[sexpr.SExpr] = []

        node_name = getattr(self, "node_name", None)
        if node_name:
            r.append(sexpr.Sym(node_name))

        for a in Attr.get_class_attributes(self.__class__):
            val = getattr(self, a.name, None)
            if val is None:
                continue

            if a.get_meta(Attr.Transform) and self.__parent:
                val = a.value_type(self.__parent.transform_pos(val))

            if issubclass(a.value_type, bool):
                bool_ser: Attr.Bool = typing.cast(Attr.Bool, a.get_meta(Attr.Bool) or Attr.Bool.Symbol)
                if bool_ser == Attr.Bool.Symbol:
                    if val:
                        r.append(sexpr.Sym(a.name))
                elif bool_ser == Attr.Bool.SymbolInList:
                    if val:
                        r.append([sexpr.Sym(a.name)])
                elif bool_ser == Attr.Bool.YesNo:
                    r.append([sexpr.Sym(a.name), sexpr.Sym("yes" if val else "no")])
            elif a.get_meta(Attr.Positional) or isinstance(val, Node):
                r.extend(sexpr.to_sexpr(val))
            else:
                r.append([sexpr.Sym(a.name), *sexpr.to_sexpr(val)])

        if self.unknown:
            r.extend(map(sexpr.UnknownSExpr, self.unknown))

        return [r]

    @classmethod
    def from_sexpr(cls, expr: sexpr.SExpr) -> Self:
        if not cls.node_name:
            raise TypeError(f"{cls.__name__} does not have a node name and therefore cannot be deserialized from an S-expression")

        if (not (isinstance(expr, list) and len(expr) >= 1 and expr[0] == sexpr.Sym(cls.node_name))):
            raise ValueError(f"Cannot deserialize {cls.__name__} from this S-expression because it does not start with {cls.node_name}")

        expr = list(expr[1:])

        node_name = cls.node_name
        attrs: dict[str, Any] = {}

        for a in Attr.get_class_attributes(cls):
            if issubclass(a.value_type, bool):
                bool_ser = typing.cast(Attr.Bool, a.get_meta(Attr.Bool) or Attr.Bool.Symbol)
                if bool_ser == Attr.Bool.Symbol:
                    v = util.remove_where(expr, lambda e: e == sexpr.Sym(a.name))
                    attrs[a.name] = (len(v) > 0)
                elif bool_ser == Attr.Bool.SymbolInList:
                    v = util.remove_where(expr, lambda e: e == [sexpr.Sym(a.name)])
                    attrs[a.name] = (len(v) > 0)
                elif bool_ser == Attr.Bool.YesNo:
                    v = util.remove_where(expr, lambda e: isinstance(e, list) and len(e) == 2 and e[0] == sexpr.Sym(a.name))
                    attrs[a.name] = (len(v) > 0 and isinstance(v[0], list) and v[0][1] == sexpr.Sym("yes"))
            else:
                pos = a.get_meta(Attr.Positional)
                if pos:
                    if a.optional and not (expr and isinstance(expr[0], a.value_type)):
                        continue

                    if len(expr) == 0:
                        raise ValueError(f"Not enough positional arguments in {node_name}")

                    if hasattr(a.value_type, "from_sexpr"):
                        attrs[a.name] = a.value_type.from_sexpr(expr[:pos.count])
                    else:
                        attrs[a.name] = expr[0]

                    del expr[:pos.count]
                else:
                    v = util.remove_where(expr, lambda e: isinstance(e, list) and len(e) > 0 and e[0] == sexpr.Sym(a.name))
                    if not v:
                        continue

                    if issubclass(a.value_type, Node):
                        attrs[a.name] = a.value_type.from_sexpr(v[0])
                    elif hasattr(a.value_type, "from_sexpr") and isinstance(v[0], list):
                        attrs[a.name] = a.value_type.from_sexpr(v[0][1:])
                    elif isinstance(v[0], list):
                        attrs[a.name] = v[0][1]
                    else:
                        expr.append(v)

                    expr += v[1:]

        node: Self = cls.__new__(cls)
        node._init(attrs)

        if expr:
            node.unknown = expr

        return node

    def serialize(self, show_unknown: bool=False) -> str:
        return sexpr.sexpr_serialize(self.to_sexpr()[0], show_unknown=show_unknown)

    def validate(self) -> None:
        """
        Can be overridden in a child class to validate node attributes before serialization.
        """

    def transform_pos(self, pos: ToPos2) -> Pos2:
        """
        Can be overridden in a child class to transform positioning attributes marked with Attr.Transform before serialization.
        """

        if self.__parent:
            return self.__parent.transform_pos(pos)
        else:
            return Pos2(pos)

    def __repr__(self) -> str:
        r = []
        for a in Attr.get_class_attributes(self.__class__):
            r.append(f"{a.name}={repr(getattr(self, a.name))}")
        return f"{self.__class__.__name__}({', '.join(r)})"

    @classmethod
    def parse(cls, s: str) -> Self:
        return cls.from_sexpr(sexpr.sexpr_parse(s))

class NodeLoadSaveProtocol(Protocol):
    @classmethod
    def from_sexpr(cls, expr: sexpr.SExpr) -> Any: ...

    def serialize(self) -> str: ...

    def _set_path(self, path: Path) -> None: ...

class NodeLoadSaveMixin(NodeLoadSaveProtocol):
    def save(self, path: Path | str) -> None:
        """
        Saves a node into a file.
        """

        data = self.serialize()
        with open(path, "w") as f:
            f.write(data)

    @classmethod
    def _load(cls, path: str) -> Self:
        with open(path, "r") as f:
            data = f.read()

        node = cls.from_sexpr(sexpr.sexpr_parse(data))

        if hasattr(node, "_set_path"):
            node._set_path(Path(path))

        return node

    @classmethod
    def load(cls, path: str) -> Self:
        """
        Loads a node from a file.
        """

        return pickle_cache.load(path, cls._load)

class ContainerNode(Node):
    """
    Base class for KiCad data nodes that contain children.
    """

    child_types: ClassVar[tuple[type[Node], ...]]

    __children: Annotated[list[Node], Attr.Ignore]

    def _init(self, attrs: Optional[dict[str, sexpr.SExprConvert]] = None) -> None:
        self.__children = []

        if not attrs:
            attrs = {}

        children = attrs.pop("children", None)

        super()._init(attrs)

        if children:
            assert isinstance(children, list)
            for child in children:
                self.append(child)

    def clone(self) -> Self:
        """
        Creates a recursive clone of this node. The new node will not have a parent.
        """

        node = super().clone()
        node.__children = []
        node.extend(c.clone() for c in self.__children)
        return node

    def _validate_child(self, node: Node) -> Node:
        if not isinstance(node, self.child_types):
            raise RuntimeError(f"{node.__class__.__name__} is not allowed to be a child of {self.__class__.__name__}.")

        if node.parent:
            raise RuntimeError(f"{self.__class__.__name__} already has a parent. Either .detach() it first, or use .clone() if you want a new copy.")

        node._set_parent(self)
        return node

    _T = TypeVar("_T", bound=Node)

    def append(self, node: _T) -> _T:
        """
        Adds a new child node to this container. The node type must be one of the allowed types, and it must not already have a parent.
        """

        self.__children.append(self._validate_child(node))
        return node

    def insert(self, index: int, node: Node) -> None:
        """
        Inserts a new child node to this container.
        """

        self.__children.insert(index, self._validate_child(node))

    def remove(self, node: Node) -> None:
        """
        Removes a child node from this container, detaching it.
        """

        self.__children.remove(node)
        node._set_parent(None)

    def extend(self, nodes: Iterable[Node]) -> None:
        """
        Adds multiple child nodes to this container. See append().
        """
        for n in nodes:
            self.append(n)

    def find_one(self, child_type: type[_T], predicate: Optional[Callable[[_T], bool]] = None, *, recursive: bool = False) -> Optional[_T]:
        """
        Finds the first child node of this node matching the type and optionally also a predicate. Returns None if not found.
        """

        return next(self.find_all(child_type, predicate, recursive=recursive), None)

    def find_all(self, child_type: type[_T], predicate: Optional[Callable[[_T], bool]] = None, *, recursive: bool = False) -> Iterator[_T]:
        """
        Finds all child nodes of this node matching the type and optionally also a predicate.
        """

        for c in self:
            if isinstance(c, child_type) and (not predicate or predicate(c)):
                yield c
            if recursive and isinstance(c, ContainerNode):
                yield from c.find_all(child_type, predicate=predicate, recursive=True)

        return (c for c in self if isinstance(c, child_type) and (not predicate or predicate(c)))

    def __bool__(self) -> bool:
        return True

    def __iter__(self) -> Iterator[Node]:
        return iter(self.__children)

    def __len__(self) -> int:
        return len(self.__children)

    def __getitem__(self, key: int) -> Node:
        return self.__children[key]

    def __setitem__(self, key: int, value: Node) -> None:
        old_node = self.__children[key]
        self.__children[key] = self._validate_child(value)
        old_node._set_parent(None)

    def to_sexpr(self) -> list[list[sexpr.SExpr]]:
        r = super().to_sexpr()[0]

        #for child in sorted(self.__children, key=lambda c: self.child_types.index(type(c))):
        #    r += child.to_sexpr()
        for child in self.__children:
            r += child.to_sexpr()

        return [r]

    @classmethod
    def from_sexpr(cls, expr: sexpr.SExpr) -> Self:
        if not isinstance(expr, list):
            raise ValueError(f"Cannot deserialize {cls.__name__} from this S-expression")

        children = []
        non_children = []

        for e in expr[1:]:
            if not isinstance(e, list) or not isinstance(e[0], sexpr.Sym):
                non_children.append(e)
                continue

            child_type = next((t for t in cls.child_types if t.node_name == e[0].name), None)
            if not child_type:
                non_children.append(e)
                continue

            children.append(child_type.from_sexpr(e))

        node = super().from_sexpr([expr[0], *non_children])
        node.extend(children)
        return node
